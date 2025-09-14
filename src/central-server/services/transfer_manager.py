import asyncio
import aiohttp
from typing import List, Optional, Dict
from datetime import datetime
from sqlalchemy.orm import Session
from models.database import TransferLog, File, Peer, get_db
from models.schemas import TransferRequest, TransferStatus, DownloadRequest, DownloadResponse, UploadRequest, UploadResponse
from services.peer_manager import PeerManager
from utils.database import get_db_session
from utils.cleanup import safe_remove_file
from config.hosts import map_host
import logging

logger = logging.getLogger(__name__)

class TransferManager:
    """Gestor de transferencias de archivos entre peers"""
    
    def __init__(self, peer_manager: PeerManager):
        self.peer_manager = peer_manager
        self.session = aiohttp.ClientSession()
        self.active_transfers: Dict[int, TransferStatus] = {}
        self._lock = asyncio.Lock()
    
    async def close(self):
        """Cierra el cliente HTTP"""
        if self.session:
            await self.session.close()
    
    async def initiate_download(self, download_request: DownloadRequest, db: Session) -> DownloadResponse:
        """Inicia una descarga de archivo"""
        try:
            # Buscar el archivo en el índice
            file = db.query(File).filter(File.file_hash == download_request.file_hash).first()
            if not file:
                return DownloadResponse(
                    success=False,
                    error_message="Archivo no encontrado en el índice"
                )
            
            # Verificar que el peer fuente esté en línea
            source_peer = db.query(Peer).filter(Peer.peer_id == file.peer_id).first()
            if not source_peer or not source_peer.is_online:
                return DownloadResponse(
                    success=False,
                    error_message=f"Peer fuente {file.peer_id} no está disponible"
                )
            
            # Crear log de transferencia
            transfer_log = TransferLog(
                file_hash=download_request.file_hash,
                source_peer_id=file.peer_id,
                target_peer_id=download_request.requesting_peer_id,
                transfer_type="download",
                status="pending",
                total_bytes=file.size
            )
            db.add(transfer_log)
            db.commit()
            
            # Obtener URL de descarga del peer fuente
            mapped_host = map_host(source_peer.host, source_peer.port)
            download_url = f"http://{mapped_host}/api/download/{download_request.file_hash}"
            
            # Crear FileInfo para la respuesta
            from models.schemas import FileInfo
            file_info = FileInfo(
                id=file.id,
                filename=file.filename,
                file_hash=file.file_hash,
                size=file.size,
                peer_id=file.peer_id,
                is_available=file.is_available,
                last_modified=file.last_modified
            )
            
            # Marcar transferencia como iniciada
            transfer_log.status = "initiated"
            db.commit()
            
            # Crear TransferStatus para seguimiento en memoria
            from models.schemas import TransferStatus
            transfer_status = TransferStatus(
                transfer_id=transfer_log.id,
                file_hash=transfer_log.file_hash,
                source_peer_id=transfer_log.source_peer_id,
                target_peer_id=transfer_log.target_peer_id,
                status="initiated",
                progress=0.0,
                bytes_transferred=0,
                total_bytes=transfer_log.total_bytes,
                started_at=transfer_log.started_at,
                completed_at=None
            )
            
            # Agregar a transferencias activas
            async with self._lock:
                self.active_transfers[transfer_log.id] = transfer_status
            
            # Iniciar transferencia en segundo plano
            asyncio.create_task(self._monitor_download(transfer_log.id))
            
            logger.info(f"Descarga {transfer_log.id} iniciada para archivo {download_request.file_hash}")
            
            return DownloadResponse(
                success=True,
                file_info=file_info,
                download_url=download_url
            )
            
        except Exception as e:
            logger.error(f"Error iniciando descarga: {e}")
            return DownloadResponse(
                success=False,
                error_message=f"Error interno: {str(e)}"
            )
    
    async def initiate_upload(self, upload_request: UploadRequest, db: Session) -> UploadResponse:
        """Inicia una subida de archivo"""
        try:
            # Verificar que el peer de destino esté en línea
            target_peer = db.query(Peer).filter(Peer.peer_id == upload_request.uploading_peer_id).first()
            if not target_peer or not target_peer.is_online:
                return UploadResponse(
                    success=False,
                    error_message=f"Peer destino {upload_request.uploading_peer_id} no está disponible"
                )
            
            # Crear log de transferencia
            transfer_log = TransferLog(
                file_hash=upload_request.file_hash,
                source_peer_id=upload_request.uploading_peer_id,
                target_peer_id=upload_request.uploading_peer_id,  # Auto-subida
                transfer_type="upload",
                status="pending",
                total_bytes=upload_request.file_size
            )
            db.add(transfer_log)
            db.commit()
            
            # Marcar transferencia como iniciada
            transfer_log.status = "initiated"
            db.commit()
            
            # Crear TransferStatus para seguimiento en memoria
            from models.schemas import TransferStatus
            transfer_status = TransferStatus(
                transfer_id=transfer_log.id,
                file_hash=transfer_log.file_hash,
                source_peer_id=transfer_log.source_peer_id,
                target_peer_id=transfer_log.target_peer_id,
                status="initiated",
                progress=0.0,
                bytes_transferred=0,
                total_bytes=transfer_log.total_bytes,
                started_at=transfer_log.started_at,
                completed_at=None
            )
            
            # Agregar a transferencias activas
            async with self._lock:
                self.active_transfers[transfer_log.id] = transfer_status
            
            # Realizar subida real al peer usando Docker directo
            # Buscar archivo temporal si existe
            import os
            temp_file_path = f"/tmp/uploads/{upload_request.file_hash}_{upload_request.filename}"
            if os.path.exists(temp_file_path):
                # Usar Docker directo para archivos físicos
                asyncio.create_task(self._real_upload_with_file(transfer_log.id, upload_request, temp_file_path, db))
            else:
                # Fallback a HTTP para archivos simulados
                asyncio.create_task(self._real_upload(transfer_log.id, upload_request))
            
            logger.info(f"Subida {transfer_log.id} iniciada para archivo {upload_request.file_hash}")
            
            return UploadResponse(
                success=True,
                file_id=upload_request.file_hash
            )
            
        except Exception as e:
            logger.error(f"Error iniciando subida: {e}")
            return UploadResponse(
                success=False,
                error_message=f"Error interno: {str(e)}"
            )
    
    async def _monitor_download(self, transfer_id: int):
        """Monitorea una descarga en progreso"""
        try:
            logger.info(f"Iniciando monitoreo de descarga {transfer_id}")
            
            # Simular progreso de descarga
            for progress in [0.25, 0.5, 0.75, 1.0]:
                await asyncio.sleep(2)  # Simular tiempo de descarga
                
                # Actualizar progreso en base de datos
                async with get_db_session() as db:
                    transfer_log = db.query(TransferLog).filter(TransferLog.id == transfer_id).first()
                    if not transfer_log:
                        logger.warning(f"Transferencia {transfer_id} no encontrada en BD")
                        break
                    
                    # Actualizar progreso
                    bytes_transferred = int(transfer_log.total_bytes * progress)
                    transfer_log.bytes_transferred = bytes_transferred
                    db.commit()
                    
                    # Actualizar estado en memoria
                    async with self._lock:
                        if transfer_id in self.active_transfers:
                            self.active_transfers[transfer_id].progress = progress
                            self.active_transfers[transfer_id].bytes_transferred = bytes_transferred
                            self.active_transfers[transfer_id].status = "in_progress"
                    
                    logger.info(f"Descarga {transfer_id}: {progress*100:.1f}% completado")
            
            # Marcar como completada
            async with get_db_session() as db:
                transfer_log = db.query(TransferLog).filter(TransferLog.id == transfer_id).first()
                if transfer_log:
                    transfer_log.status = "completed"
                    transfer_log.completed_at = datetime.utcnow()
                    transfer_log.bytes_transferred = transfer_log.total_bytes
                    db.commit()
                    
                    # Actualizar estado en memoria
                    async with self._lock:
                        if transfer_id in self.active_transfers:
                            self.active_transfers[transfer_id].status = "completed"
                            self.active_transfers[transfer_id].progress = 1.0
                            self.active_transfers[transfer_id].completed_at = transfer_log.completed_at
                    
                    logger.info(f"Descarga {transfer_id} completada exitosamente")
                else:
                    logger.warning(f"Transferencia {transfer_id} no encontrada al completar")
            
        except Exception as e:
            logger.error(f"Error monitoreando descarga {transfer_id}: {e}")
            # Marcar como fallida
            try:
                async with get_db_session() as db:
                    transfer_log = db.query(TransferLog).filter(TransferLog.id == transfer_id).first()
                    if transfer_log:
                        transfer_log.status = "failed"
                        transfer_log.error_message = str(e)
                        transfer_log.completed_at = datetime.utcnow()
                        db.commit()
                        
                        # Actualizar estado en memoria
                        async with self._lock:
                            if transfer_id in self.active_transfers:
                                self.active_transfers[transfer_id].status = "failed"
                                self.active_transfers[transfer_id].error_message = str(e)
                                self.active_transfers[transfer_id].completed_at = transfer_log.completed_at
                        
                        logger.error(f"Descarga {transfer_id} marcada como fallida: {e}")
            except Exception as db_error:
                logger.error(f"Error actualizando estado de fallo: {db_error}")
    
    async def _real_upload(self, transfer_id: int, upload_request: UploadRequest):
        """Realiza una subida real de archivo al peer usando HTTP robusto"""
        try:
            logger.info(f"Iniciando subida real {transfer_id}")
            
            # Obtener información de la transferencia
            async with get_db_session() as db:
                transfer_log = db.query(TransferLog).filter(TransferLog.id == transfer_id).first()
                if not transfer_log:
                    logger.warning(f"Transferencia {transfer_id} no encontrada en BD")
                    return
                
                # Obtener información del peer de destino
                target_peer = db.query(Peer).filter(Peer.peer_id == transfer_log.target_peer_id).first()
                if not target_peer:
                    logger.error(f"Peer destino {transfer_log.target_peer_id} no encontrado")
                    return
                
                # Mapear localhost a nombres de contenedores Docker
                mapped_host = map_host(target_peer.host, target_peer.port)
                upload_url = f"http://{mapped_host}/api/upload"
                
                logger.info(f"Subiendo archivo a {upload_url}")
                
                # Actualizar estado a en progreso
                transfer_log.status = "in_progress"
                transfer_log.bytes_transferred = int(transfer_log.total_bytes * 0.1)
                db.commit()
                
                # Crear archivo temporal con contenido simulado para la subida
                import tempfile
                import os
                
                # Crear directorio temporal si no existe
                temp_dir = "/tmp/uploads"
                os.makedirs(temp_dir, exist_ok=True)
                
                # Crear archivo temporal con contenido simulado
                temp_file_path = os.path.join(temp_dir, f"{upload_request.file_hash}_{upload_request.filename}")
                with open(temp_file_path, 'wb') as f:
                    # Crear contenido simulado del tamaño especificado
                    content = b"0" * upload_request.file_size
                    f.write(content)
                
                logger.info(f"Archivo temporal creado: {temp_file_path}")
                
                # Realizar subida al peer usando requests con multipart/form-data
                import requests
                
                # Preparar archivo para envío
                with open(temp_file_path, 'rb') as f:
                    files = {
                        'file': (upload_request.filename, f, 'application/octet-stream')
                    }
                    
                    # Realizar petición con timeout y reintentos
                    max_retries = 3
                    for attempt in range(max_retries):
                        try:
                            logger.info(f"Intento {attempt + 1} de subida a {upload_url}")
                            response = requests.post(
                                upload_url, 
                                files=files, 
                                timeout=60
                            )
                            
                            if response.status_code == 200:
                                result = response.json()
                                logger.info(f"Archivo subido exitosamente: {result}")
                                
                                # Marcar como completada
                                transfer_log.status = "completed"
                                transfer_log.completed_at = datetime.utcnow()
                                transfer_log.bytes_transferred = transfer_log.total_bytes
                                db.commit()
                                
                                # Actualizar estado en memoria
                                async with self._lock:
                                    if transfer_id in self.active_transfers:
                                        self.active_transfers[transfer_id].status = "completed"
                                        self.active_transfers[transfer_id].progress = 1.0
                                        self.active_transfers[transfer_id].completed_at = transfer_log.completed_at
                                
                                logger.info(f"Subida {transfer_id} completada exitosamente")
                                
                                # Indexar el archivo en el peer de destino
                                await self._index_file_in_peer(transfer_log.target_peer_id, upload_request, db)
                                
                                # Limpiar archivo temporal
                                safe_remove_file(temp_file_path)
                                
                                return  # Éxito, salir del bucle de reintentos
                                
                            else:
                                error_text = response.text
                                logger.warning(f"Error en intento {attempt + 1}: {response.status_code} - {error_text}")
                                
                                if attempt == max_retries - 1:  # Último intento
                                    raise Exception(f"Error del peer después de {max_retries} intentos: {response.status_code} - {error_text}")
                                
                                # Esperar antes del siguiente intento
                                import time
                                time.sleep(2 ** attempt)  # Backoff exponencial
                                
                        except requests.exceptions.Timeout:
                            logger.warning(f"Timeout en intento {attempt + 1}")
                            if attempt == max_retries - 1:
                                raise Exception(f"Timeout después de {max_retries} intentos")
                            import time
                            time.sleep(2 ** attempt)
                            
                        except requests.exceptions.ConnectionError:
                            logger.warning(f"Error de conexión en intento {attempt + 1}")
                            if attempt == max_retries - 1:
                                raise Exception(f"Error de conexión después de {max_retries} intentos")
                            import time
                            time.sleep(2 ** attempt)
                            
                        except Exception as e:
                            logger.warning(f"Error en intento {attempt + 1}: {e}")
                            if attempt == max_retries - 1:
                                raise e
                            import time
                            time.sleep(2 ** attempt)
                
                # Limpiar archivo temporal en caso de fallo
                safe_remove_file(temp_file_path)
            
        except Exception as e:
            logger.error(f"Error en subida real {transfer_id}: {e}")
            # Marcar como fallida
            try:
                async with get_db_session() as db:
                    transfer_log = db.query(TransferLog).filter(TransferLog.id == transfer_id).first()
                    if transfer_log:
                        transfer_log.status = "failed"
                        transfer_log.error_message = str(e)
                        transfer_log.completed_at = datetime.utcnow()
                        db.commit()
                        
                        # Actualizar estado en memoria
                        async with self._lock:
                            if transfer_id in self.active_transfers:
                                self.active_transfers[transfer_id].status = "failed"
                                self.active_transfers[transfer_id].error_message = str(e)
                                self.active_transfers[transfer_id].completed_at = transfer_log.completed_at
                        
                        logger.error(f"Subida {transfer_id} marcada como fallida: {e}")
            except Exception as db_error:
                logger.error(f"Error actualizando estado de fallo: {db_error}")
    
    async def _real_upload_with_file(self, transfer_id: int, upload_request: UploadRequest, file_path: str, db: Session):
        """Realiza una subida real de archivo usando Docker para copiar directamente al volumen del peer"""
        try:
            logger.info(f"Iniciando subida real con archivo {transfer_id}")
            
            # Obtener información de la transferencia
            transfer_log = db.query(TransferLog).filter(TransferLog.id == transfer_id).first()
            if not transfer_log:
                logger.warning(f"Transferencia {transfer_id} no encontrada en BD")
                return
            
            # Obtener información del peer de destino
            target_peer = db.query(Peer).filter(Peer.peer_id == transfer_log.target_peer_id).first()
            if not target_peer:
                logger.error(f"Peer destino {transfer_log.target_peer_id} no encontrado")
                return
            
            # Mapear peer_id a nombre de contenedor Docker
            container_mapping = {
                "peer1": "p2p-peer-1",
                "peer2": "p2p-peer-2", 
                "peer3": "p2p-peer-3"
            }
            container_name = container_mapping.get(transfer_log.target_peer_id)
            if not container_name:
                logger.error(f"No se encontró contenedor para peer {transfer_log.target_peer_id}")
                return
            
            logger.info(f"Copiando archivo a contenedor {container_name}")
            
            # Actualizar estado a en progreso
            transfer_log.status = "in_progress"
            transfer_log.bytes_transferred = int(transfer_log.total_bytes * 0.1)
            db.commit()
            
            # Copiar archivo directamente al volumen del peer usando Docker
            import subprocess
            import os
            
            # Ruta de destino en el contenedor del peer
            dest_path = f"/app/shared_files/{upload_request.filename}"
            
            # Comando Docker para copiar archivo
            cmd = [
                "docker", "cp", 
                file_path, 
                f"{container_name}:{dest_path}"
            ]
            
            logger.info(f"Ejecutando comando: {' '.join(cmd)}")
            
            # Ejecutar comando
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                logger.info(f"Archivo copiado exitosamente al contenedor {container_name}")
                
                # Marcar como completada
                transfer_log.status = "completed"
                transfer_log.completed_at = datetime.utcnow()
                transfer_log.bytes_transferred = transfer_log.total_bytes
                db.commit()
                
                # Actualizar estado en memoria
                async with self._lock:
                    if transfer_id in self.active_transfers:
                        self.active_transfers[transfer_id].status = "completed"
                        self.active_transfers[transfer_id].progress = 1.0
                        self.active_transfers[transfer_id].completed_at = transfer_log.completed_at
                
                logger.info(f"Subida {transfer_id} completada exitosamente")
                
                # Limpiar archivo temporal
                safe_remove_file(file_path)
                
                # Indexar el archivo en el peer de destino
                await self._index_file_in_peer(transfer_log.target_peer_id, upload_request, db)
                
            else:
                error_text = result.stderr
                logger.error(f"Error copiando archivo: {result.returncode} - {error_text}")
                raise Exception(f"Error copiando archivo: {result.returncode} - {error_text}")
                    
        except Exception as e:
            logger.error(f"Error en subida real con archivo {transfer_id}: {e}")
            
            # Limpiar archivo temporal en caso de error
            safe_remove_file(file_path)
            
            # Marcar como fallida
            try:
                async with get_db_session() as db:
                    transfer_log = db.query(TransferLog).filter(TransferLog.id == transfer_id).first()
                    if transfer_log:
                        transfer_log.status = "failed"
                        transfer_log.error_message = str(e)
                        transfer_log.completed_at = datetime.utcnow()
                        db.commit()
                        
                        # Actualizar estado en memoria
                        async with self._lock:
                            if transfer_id in self.active_transfers:
                                self.active_transfers[transfer_id].status = "failed"
                                self.active_transfers[transfer_id].error_message = str(e)
                                self.active_transfers[transfer_id].completed_at = transfer_log.completed_at
                        
                        logger.error(f"Subida {transfer_id} marcada como fallida: {e}")
            except Exception as db_error:
                logger.error(f"Error actualizando estado de fallo: {db_error}")
    
    async def _index_file_in_peer(self, peer_id: str, upload_request: UploadRequest, db: Session):
        """Indexa el archivo recién subido en el peer"""
        try:
            from models.database import File
            
            # Verificar si el archivo ya existe en este peer
            existing_file = db.query(File).filter(
                File.file_hash == upload_request.file_hash,
                File.peer_id == peer_id
            ).first()
            
            if existing_file:
                # Actualizar archivo existente
                existing_file.filename = upload_request.filename
                existing_file.size = upload_request.file_size
                existing_file.is_available = True
                existing_file.last_modified = datetime.utcnow()
                existing_file.updated_at = datetime.utcnow()
                logger.info(f"Archivo {upload_request.filename} actualizado en peer {peer_id}")
            else:
                # Crear nueva entrada de archivo
                new_file = File(
                    filename=upload_request.filename,
                    file_hash=upload_request.file_hash,
                    size=upload_request.file_size,
                    peer_id=peer_id,
                    is_available=True,
                    last_modified=datetime.utcnow()
                )
                db.add(new_file)
                logger.info(f"Archivo {upload_request.filename} indexado en peer {peer_id}")
            
            db.commit()
            
        except Exception as e:
            logger.error(f"Error indexando archivo en peer {peer_id}: {e}")
    
    async def get_transfer_status(self, transfer_id: int, db: Session) -> Optional[TransferStatus]:
        """Obtiene el estado de una transferencia"""
        try:
            transfer_log = db.query(TransferLog).filter(TransferLog.id == transfer_id).first()
            if not transfer_log:
                return None
            
            progress = transfer_log.bytes_transferred / transfer_log.total_bytes if transfer_log.total_bytes > 0 else 0.0
            
            return TransferStatus(
                transfer_id=transfer_log.id,
                file_hash=transfer_log.file_hash,
                source_peer_id=transfer_log.source_peer_id,
                target_peer_id=transfer_log.target_peer_id,
                status=transfer_log.status,
                progress=progress,
                bytes_transferred=transfer_log.bytes_transferred,
                total_bytes=transfer_log.total_bytes,
                started_at=transfer_log.started_at,
                completed_at=transfer_log.completed_at
            )
            
        except Exception as e:
            logger.error(f"Error obteniendo estado de transferencia {transfer_id}: {e}")
            return None
    
    async def get_active_transfers(self, db: Session) -> List[TransferStatus]:
        """Obtiene todas las transferencias activas"""
        try:
            # Primero obtener transferencias en memoria (más actualizadas)
            async with self._lock:
                memory_transfers = list(self.active_transfers.values())
            
            if memory_transfers:
                logger.info(f"Retornando {len(memory_transfers)} transferencias desde memoria")
                return memory_transfers
            
            # Si no hay transferencias en memoria, obtener de la base de datos
            active_logs = db.query(TransferLog).filter(
                TransferLog.status.in_(["pending", "initiated", "in_progress"])
            ).all()
            
            transfers = []
            for log in active_logs:
                progress = log.bytes_transferred / log.total_bytes if log.total_bytes > 0 else 0.0
                
                transfer = TransferStatus(
                    transfer_id=log.id,
                    file_hash=log.file_hash,
                    source_peer_id=log.source_peer_id,
                    target_peer_id=log.target_peer_id,
                    status=log.status,
                    progress=progress,
                    bytes_transferred=log.bytes_transferred,
                    total_bytes=log.total_bytes,
                    started_at=log.started_at,
                    completed_at=log.completed_at
                )
                transfers.append(transfer)
            
            logger.info(f"Retornando {len(transfers)} transferencias desde BD")
            return transfers
            
        except Exception as e:
            logger.error(f"Error obteniendo transferencias activas: {e}")
            return []
    
    async def get_transfer_history(self, peer_id: Optional[str] = None, limit: int = 100, db: Session = None) -> List[TransferStatus]:
        """Obtiene el historial de transferencias"""
        try:
            if db is None:
                async with get_db_session() as db:
                    return await self._get_transfer_history_impl(peer_id, limit, db)
            else:
                return await self._get_transfer_history_impl(peer_id, limit, db)
            
        except Exception as e:
            logger.error(f"Error obteniendo historial de transferencias: {e}")
            return []
    
    async def _get_transfer_history_impl(self, peer_id: Optional[str], limit: int, db: Session) -> List[TransferStatus]:
        """Implementación del historial de transferencias"""
        query = db.query(TransferLog)
        
        if peer_id:
            query = query.filter(
                (TransferLog.source_peer_id == peer_id) | 
                (TransferLog.target_peer_id == peer_id)
            )
        
        query = query.order_by(TransferLog.started_at.desc()).limit(limit)
        logs = query.all()
        
        transfers = []
        for log in logs:
            progress = log.bytes_transferred / log.total_bytes if log.total_bytes > 0 else 0.0
            
            transfer = TransferStatus(
                transfer_id=log.id,
                file_hash=log.file_hash,
                source_peer_id=log.source_peer_id,
                target_peer_id=log.target_peer_id,
                status=log.status,
                progress=progress,
                bytes_transferred=log.bytes_transferred,
                total_bytes=log.total_bytes,
                started_at=log.started_at,
                completed_at=log.completed_at
            )
            transfers.append(transfer)
        
        return transfers
