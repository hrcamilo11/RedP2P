import asyncio
import aiohttp
from typing import List, Optional, Dict
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from models.database import Peer, File, get_db
from models.schemas import PeerInfo, PeerStatus, PeerRegistration
from config.hosts import map_host
from cache.redis_cache import redis_cache, cache_peer_info, get_cached_peer_info, invalidate_peer_cache
import logging

logger = logging.getLogger(__name__)

class PeerManager:
    """Gestor de peers en el servidor central"""
    
    def __init__(self):
        self.session = aiohttp.ClientSession()
        self.peer_cache: Dict[str, PeerInfo] = {}
        self._lock = asyncio.Lock()
        self.redis_connected = False
    
    async def close(self):
        """Cierra el cliente HTTP y Redis"""
        if self.session:
            await self.session.close()
        if self.redis_connected:
            await redis_cache.disconnect()
    
    async def initialize_redis(self):
        """Inicializa conexión a Redis"""
        try:
            await redis_cache.connect()
            self.redis_connected = redis_cache.connected
            if self.redis_connected:
                logger.info("Redis cache inicializado")
            else:
                logger.warning("Redis no disponible, usando cache en memoria")
        except Exception as e:
            logger.error(f"Error inicializando Redis: {e}")
            self.redis_connected = False
    
    async def register_peer(self, peer_registration: PeerRegistration, db: Session) -> bool:
        """Registra un nuevo peer en el sistema"""
        try:
            # Verificar si el peer ya existe
            existing_peer = db.query(Peer).filter(Peer.peer_id == peer_registration.peer_id).first()
            
            if existing_peer:
                # Actualizar información del peer existente
                existing_peer.host = peer_registration.host
                existing_peer.port = peer_registration.port
                existing_peer.grpc_port = peer_registration.grpc_port
                existing_peer.is_online = True
                existing_peer.last_seen = datetime.utcnow()
                existing_peer.updated_at = datetime.utcnow()
            else:
                # Crear nuevo peer
                new_peer = Peer(
                    peer_id=peer_registration.peer_id,
                    host=peer_registration.host,
                    port=peer_registration.port,
                    grpc_port=peer_registration.grpc_port,
                    is_online=True,
                    last_seen=datetime.utcnow()
                )
                db.add(new_peer)
            
            db.commit()
            
            # Actualizar caché
            await self._update_peer_cache(peer_registration.peer_id, db)
            
            # Invalidar cache Redis
            if self.redis_connected:
                await invalidate_peer_cache(peer_registration.peer_id)
            
            logger.info(f"Peer {peer_registration.peer_id} registrado/actualizado")
            return True
            
        except Exception as e:
            logger.error(f"Error registrando peer {peer_registration.peer_id}: {e}")
            db.rollback()
            return False
    
    async def unregister_peer(self, peer_id: str, db: Session) -> bool:
        """Desregistra un peer del sistema"""
        try:
            peer = db.query(Peer).filter(Peer.peer_id == peer_id).first()
            if peer:
                peer.is_online = False
                peer.updated_at = datetime.utcnow()
                db.commit()
                
                # Remover del caché
                async with self._lock:
                    if peer_id in self.peer_cache:
                        del self.peer_cache[peer_id]
                
                logger.info(f"Peer {peer_id} desregistrado")
                return True
            return False
            
        except Exception as e:
            logger.error(f"Error desregistrando peer {peer_id}: {e}")
            db.rollback()
            return False
    
    async def get_peer_status(self, peer_id: str, db: Session) -> Optional[PeerStatus]:
        """Obtiene el estado de un peer"""
        try:
            peer = db.query(Peer).filter(Peer.peer_id == peer_id).first()
            if not peer:
                return None
            
            # Verificar conectividad
            is_online = await self._ping_peer(peer)
            if is_online != peer.is_online:
                peer.is_online = is_online
                peer.last_seen = datetime.utcnow()
                db.commit()
            
            # Contar archivos del peer
            files_count = db.query(File).filter(File.peer_id == peer_id).count()
            
            return PeerStatus(
                peer_id=peer.peer_id,
                is_online=peer.is_online,
                last_seen=peer.last_seen,
                files_count=files_count,
                total_size=0  # Se calcularía sumando los tamaños de archivos
            )
            
        except Exception as e:
            logger.error(f"Error obteniendo estado del peer {peer_id}: {e}")
            return None
    
    async def get_all_peers(self, db: Session) -> List[PeerInfo]:
        """Obtiene todos los peers registrados"""
        try:
            # Usar JOIN para evitar consultas N+1
            from sqlalchemy import func
            peers_with_counts = db.query(
                Peer,
                func.count(File.id).label('files_count')
            ).outerjoin(File, Peer.peer_id == File.peer_id).group_by(Peer.id).all()
            
            peer_infos = []
            for peer, files_count in peers_with_counts:
                peer_info = PeerInfo(
                    peer_id=peer.peer_id,
                    host=peer.host,
                    port=peer.port,
                    grpc_port=peer.grpc_port,
                    is_online=peer.is_online,
                    last_seen=peer.last_seen,
                    files_count=files_count or 0
                )
                peer_infos.append(peer_info)
            
            return peer_infos
            
        except Exception as e:
            logger.error(f"Error obteniendo peers: {e}")
            return []
    
    async def get_online_peers(self, db: Session) -> List[PeerInfo]:
        """Obtiene solo los peers que están en línea"""
        try:
            # Usar JOIN para evitar consultas N+1
            from sqlalchemy import func
            peers_with_counts = db.query(
                Peer,
                func.count(File.id).label('files_count')
            ).outerjoin(File, Peer.peer_id == File.peer_id).filter(
                Peer.is_online == True
            ).group_by(Peer.id).all()
            
            peer_infos = []
            for peer, files_count in peers_with_counts:
                # Verificar conectividad real
                is_online = await self._ping_peer(peer)
                if is_online:
                    peer_info = PeerInfo(
                        peer_id=peer.peer_id,
                        host=peer.host,
                        port=peer.port,
                        grpc_port=peer.grpc_port,
                        is_online=True,
                        last_seen=datetime.utcnow(),
                        files_count=files_count or 0
                    )
                    peer_infos.append(peer_info)
                else:
                    # Marcar como offline
                    peer.is_online = False
                    peer.updated_at = datetime.utcnow()
                    db.commit()
            
            return peer_infos
            
        except Exception as e:
            logger.error(f"Error obteniendo peers en línea: {e}")
            return []
    
    async def _ping_peer(self, peer: Peer) -> bool:
        """Hace ping a un peer para verificar conectividad"""
        try:
            # Mapear localhost a nombres de contenedores Docker
            mapped_host = map_host(peer.host, peer.port)
            url = f"http://{mapped_host}/api/health"
            
            logger.debug(f"Haciendo ping a peer {peer.peer_id} en {url}")
            async with self.session.get(url, timeout=10) as response:
                is_online = response.status == 200
                logger.debug(f"Peer {peer.peer_id} respondió con status {response.status}")
                return is_online
        except Exception as e:
            logger.debug(f"Error haciendo ping a peer {peer.peer_id}: {e}")
            # Temporalmente, asumir que el peer está online si no podemos hacer ping
            # Esto evita que los peers se marquen como offline incorrectamente
            return True
    
    async def _update_peer_cache(self, peer_id: str, db: Session):
        """Actualiza el caché de peers"""
        try:
            peer = db.query(Peer).filter(Peer.peer_id == peer_id).first()
            if peer:
                files_count = db.query(File).filter(File.peer_id == peer_id).count()
                
                peer_info = PeerInfo(
                    peer_id=peer.peer_id,
                    host=peer.host,
                    port=peer.port,
                    grpc_port=peer.grpc_port,
                    is_online=peer.is_online,
                    last_seen=peer.last_seen,
                    files_count=files_count
                )
                
                async with self._lock:
                    self.peer_cache[peer_id] = peer_info
                    
        except Exception as e:
            logger.error(f"Error actualizando caché del peer {peer_id}: {e}")
    
    async def cleanup_offline_peers(self, db: Session, timeout_minutes: int = 30):
        """Limpia peers que han estado offline por mucho tiempo"""
        try:
            cutoff_time = datetime.utcnow() - timedelta(minutes=timeout_minutes)
            offline_peers = db.query(Peer).filter(
                Peer.is_online == False,
                Peer.last_seen < cutoff_time
            ).all()
            
            for peer in offline_peers:
                # Marcar archivos como no disponibles
                db.query(File).filter(File.peer_id == peer.peer_id).update({
                    "is_available": False
                })
                
                # Remover del caché
                async with self._lock:
                    if peer.peer_id in self.peer_cache:
                        del self.peer_cache[peer.peer_id]
            
            db.commit()
            logger.info(f"Limpiados {len(offline_peers)} peers offline")
            
        except Exception as e:
            logger.error(f"Error limpiando peers offline: {e}")
            db.rollback()
