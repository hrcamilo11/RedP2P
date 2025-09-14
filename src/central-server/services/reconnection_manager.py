"""
Gestor de reconexión automática para peers
"""

import asyncio
import logging
from typing import Dict, List, Optional, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class ConnectionStatus(Enum):
    """Estados de conexión de un peer"""
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    RECONNECTING = "reconnecting"
    FAILED = "failed"

@dataclass
class PeerConnectionInfo:
    """Información de conexión de un peer"""
    peer_id: str
    host: str
    port: int
    status: ConnectionStatus
    last_seen: datetime
    reconnect_attempts: int = 0
    max_reconnect_attempts: int = 5
    reconnect_interval: int = 30  # segundos
    next_reconnect: Optional[datetime] = None

class ReconnectionManager:
    """Gestor de reconexión automática para peers"""
    
    def __init__(self):
        self.peer_connections: Dict[str, PeerConnectionInfo] = {}
        self.reconnect_callbacks: List[Callable] = []
        self.status_callbacks: List[Callable] = []
        self._running = False
        self._task: Optional[asyncio.Task] = None
        self._lock = asyncio.Lock()
    
    async def start(self):
        """Inicia el gestor de reconexión"""
        if self._running:
            return
        
        self._running = True
        self._task = asyncio.create_task(self._reconnection_loop())
        logger.info("Gestor de reconexión iniciado")
    
    async def stop(self):
        """Detiene el gestor de reconexión"""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("Gestor de reconexión detenido")
    
    async def register_peer(self, peer_id: str, host: str, port: int, 
                           max_attempts: int = 5, interval: int = 30):
        """Registra un peer para monitoreo de reconexión"""
        async with self._lock:
            self.peer_connections[peer_id] = PeerConnectionInfo(
                peer_id=peer_id,
                host=host,
                port=port,
                status=ConnectionStatus.CONNECTED,
                last_seen=datetime.utcnow(),
                max_reconnect_attempts=max_attempts,
                reconnect_interval=interval
            )
            logger.info(f"Peer {peer_id} registrado para reconexión")
    
    async def unregister_peer(self, peer_id: str):
        """Desregistra un peer del monitoreo"""
        async with self._lock:
            if peer_id in self.peer_connections:
                del self.peer_connections[peer_id]
                logger.info(f"Peer {peer_id} desregistrado del monitoreo")
    
    async def update_peer_status(self, peer_id: str, is_online: bool):
        """Actualiza el estado de conexión de un peer"""
        async with self._lock:
            if peer_id not in self.peer_connections:
                return
            
            peer_info = self.peer_connections[peer_id]
            
            if is_online:
                if peer_info.status != ConnectionStatus.CONNECTED:
                    logger.info(f"Peer {peer_id} se reconectó exitosamente")
                    peer_info.status = ConnectionStatus.CONNECTED
                    peer_info.reconnect_attempts = 0
                    peer_info.next_reconnect = None
                    await self._notify_status_change(peer_id, ConnectionStatus.CONNECTED)
            else:
                if peer_info.status == ConnectionStatus.CONNECTED:
                    logger.warning(f"Peer {peer_id} se desconectó")
                    peer_info.status = ConnectionStatus.DISCONNECTED
                    peer_info.next_reconnect = datetime.utcnow() + timedelta(seconds=peer_info.reconnect_interval)
                    await self._notify_status_change(peer_id, ConnectionStatus.DISCONNECTED)
            
            peer_info.last_seen = datetime.utcnow()
    
    async def _reconnection_loop(self):
        """Loop principal de reconexión"""
        while self._running:
            try:
                await self._check_reconnections()
                await asyncio.sleep(10)  # Verificar cada 10 segundos
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error en loop de reconexión: {e}")
                await asyncio.sleep(30)  # Esperar más tiempo en caso de error
    
    async def _check_reconnections(self):
        """Verifica qué peers necesitan reconexión"""
        current_time = datetime.utcnow()
        peers_to_reconnect = []
        
        async with self._lock:
            for peer_id, peer_info in self.peer_connections.items():
                if (peer_info.status == ConnectionStatus.DISCONNECTED and 
                    peer_info.next_reconnect and 
                    current_time >= peer_info.next_reconnect and
                    peer_info.reconnect_attempts < peer_info.max_reconnect_attempts):
                    peers_to_reconnect.append(peer_id)
        
        # Procesar reconexiones
        for peer_id in peers_to_reconnect:
            await self._attempt_reconnection(peer_id)
    
    async def _attempt_reconnection(self, peer_id: str):
        """Intenta reconectar un peer"""
        async with self._lock:
            if peer_id not in self.peer_connections:
                return
            
            peer_info = self.peer_connections[peer_id]
            peer_info.status = ConnectionStatus.RECONNECTING
            peer_info.reconnect_attempts += 1
        
        logger.info(f"Intentando reconectar peer {peer_id} (intento {peer_info.reconnect_attempts})")
        
        try:
            # Notificar que se está intentando reconectar
            await self._notify_status_change(peer_id, ConnectionStatus.RECONNECTING)
            
            # Ejecutar callbacks de reconexión
            for callback in self.reconnect_callbacks:
                try:
                    await callback(peer_id, peer_info.host, peer_info.port)
                except Exception as e:
                    logger.error(f"Error en callback de reconexión: {e}")
            
            # Simular verificación de conexión (en implementación real, harías ping)
            await asyncio.sleep(2)
            
            # Por ahora, asumimos que la reconexión fue exitosa
            # En implementación real, verificarías la conexión
            async with self._lock:
                peer_info.status = ConnectionStatus.CONNECTED
                peer_info.reconnect_attempts = 0
                peer_info.next_reconnect = None
            
            logger.info(f"Peer {peer_id} reconectado exitosamente")
            await self._notify_status_change(peer_id, ConnectionStatus.CONNECTED)
            
        except Exception as e:
            logger.error(f"Error reconectando peer {peer_id}: {e}")
            
            async with self._lock:
                peer_info.status = ConnectionStatus.DISCONNECTED
                peer_info.next_reconnect = datetime.utcnow() + timedelta(seconds=peer_info.reconnect_interval)
            
            # Si se agotaron los intentos, marcar como fallido
            if peer_info.reconnect_attempts >= peer_info.max_reconnect_attempts:
                peer_info.status = ConnectionStatus.FAILED
                logger.error(f"Peer {peer_id} falló después de {peer_info.max_reconnect_attempts} intentos")
                await self._notify_status_change(peer_id, ConnectionStatus.FAILED)
    
    async def _notify_status_change(self, peer_id: str, status: ConnectionStatus):
        """Notifica cambios de estado"""
        for callback in self.status_callbacks:
            try:
                await callback(peer_id, status)
            except Exception as e:
                logger.error(f"Error en callback de estado: {e}")
    
    def add_reconnect_callback(self, callback: Callable):
        """Agrega un callback para reconexión"""
        self.reconnect_callbacks.append(callback)
    
    def add_status_callback(self, callback: Callable):
        """Agrega un callback para cambios de estado"""
        self.status_callbacks.append(callback)
    
    async def get_peer_status(self, peer_id: str) -> Optional[ConnectionStatus]:
        """Obtiene el estado de un peer"""
        async with self._lock:
            if peer_id in self.peer_connections:
                return self.peer_connections[peer_id].status
            return None
    
    async def get_all_peer_statuses(self) -> Dict[str, ConnectionStatus]:
        """Obtiene el estado de todos los peers"""
        async with self._lock:
            return {peer_id: info.status for peer_id, info in self.peer_connections.items()}
    
    async def get_disconnected_peers(self) -> List[str]:
        """Obtiene lista de peers desconectados"""
        async with self._lock:
            return [
                peer_id for peer_id, info in self.peer_connections.items()
                if info.status in [ConnectionStatus.DISCONNECTED, ConnectionStatus.RECONNECTING, ConnectionStatus.FAILED]
            ]
    
    async def reset_peer_attempts(self, peer_id: str):
        """Reinicia los intentos de reconexión de un peer"""
        async with self._lock:
            if peer_id in self.peer_connections:
                peer_info = self.peer_connections[peer_id]
                peer_info.reconnect_attempts = 0
                peer_info.next_reconnect = None
                logger.info(f"Intentos de reconexión reiniciados para peer {peer_id}")

# Instancia global del gestor de reconexión
reconnection_manager = ReconnectionManager()
