from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks, UploadFile, File, Request, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List, Optional
from middleware.rate_limiter import rate_limit_middleware
from monitoring.resource_monitor import resource_monitor
from services.backup_manager import backup_manager
from services.alert_manager import alert_manager, AlertLevel, AlertType
from services.business_metrics import business_metrics
from utils.advanced_logging import business_logger, performance_logger
from datetime import datetime
import logging

from models.database import get_db, create_tables
from models.schemas import (
    PeerRegistration, PeerInfo, PeerStatus, FileInfo, SearchRequest, SearchResponse,
    DownloadRequest, DownloadResponse, UploadRequest, UploadResponse,
    TransferStatus, SystemStats
)
from services.peer_manager import PeerManager
from services.file_indexer import CentralFileIndexer
from services.transfer_manager import TransferManager

logger = logging.getLogger(__name__)

class CentralServerAPI:
    """API REST del servidor central"""
    
    def __init__(self):
        self.peer_manager = PeerManager()
        self.file_indexer = CentralFileIndexer(self.peer_manager)
        self.transfer_manager = TransferManager(self.peer_manager)
        self.app = FastAPI(
            title="Servidor Central P2P",
            description="Servidor central para coordinación de red P2P",
            version="1.0.0"
        )
        self._setup_middleware()
        self._setup_routes()
    
    def _setup_middleware(self):
        """Configura middleware de la aplicación"""
        # Configuración CORS más restrictiva
        allowed_origins = [
            "http://localhost:8000",
            "http://localhost:3000",
            "http://127.0.0.1:8000",
            "http://127.0.0.1:3000"
        ]
        
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=allowed_origins,
            allow_credentials=True,
            allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            allow_headers=["*"],
            expose_headers=["*"],
        )
        
        # Agregar rate limiting
        @self.app.middleware("http")
        async def rate_limit_middleware_wrapper(request: Request, call_next):
            return await rate_limit_middleware(request, call_next)
        
        # Servir archivos estáticos
        self.app.mount("/static", StaticFiles(directory="static"), name="static")
    
    def _setup_routes(self):
        """Configura las rutas de la API"""
        
        @self.app.on_event("startup")
        async def startup_event():
            """Evento de inicio de la aplicación"""
            create_tables()
            logger.info("Servidor central iniciado")
        
        @self.app.on_event("shutdown")
        async def shutdown_event():
            """Evento de cierre de la aplicación"""
            await self.peer_manager.close()
            await self.file_indexer.close()
            await self.transfer_manager.close()
            logger.info("Servidor central detenido")
        
        # === RUTA PRINCIPAL ===
        
        @self.app.get("/")
        async def root():
            """Página principal de la interfaz web"""
            return FileResponse("static/index.html")
        
        # === RUTAS DE PEERS ===
        
        @self.app.post("/api/peers/register", response_model=dict)
        async def register_peer(
            peer_registration: PeerRegistration,
            background_tasks: BackgroundTasks,
            db: Session = Depends(get_db)
        ):
            """Registra un nuevo peer en el sistema"""
            try:
                success = await self.peer_manager.register_peer(peer_registration, db)
                if success:
                    # Indexar archivos del peer en segundo plano
                    background_tasks.add_task(
                        self.file_indexer.index_peer_files,
                        peer_registration.peer_id,
                        db
                    )
                    return {"success": True, "message": "Peer registrado correctamente"}
                else:
                    raise HTTPException(status_code=400, detail="Error registrando peer")
            except Exception as e:
                logger.error(f"Error en registro de peer: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.delete("/api/peers/{peer_id}")
        async def unregister_peer(peer_id: str, db: Session = Depends(get_db)):
            """Desregistra un peer del sistema"""
            try:
                success = await self.peer_manager.unregister_peer(peer_id, db)
                if success:
                    return {"success": True, "message": f"Peer {peer_id} desregistrado"}
                else:
                    raise HTTPException(status_code=404, detail="Peer no encontrado")
            except Exception as e:
                logger.error(f"Error desregistrando peer {peer_id}: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/api/peers", response_model=List[PeerInfo])
        async def get_all_peers(db: Session = Depends(get_db)):
            """Obtiene todos los peers registrados"""
            try:
                return await self.peer_manager.get_all_peers(db)
            except Exception as e:
                logger.error(f"Error obteniendo peers: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/api/peers/online", response_model=List[PeerInfo])
        async def get_online_peers(db: Session = Depends(get_db)):
            """Obtiene solo los peers en línea"""
            try:
                return await self.peer_manager.get_online_peers(db)
            except Exception as e:
                logger.error(f"Error obteniendo peers en línea: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/api/peers/{peer_id}/status", response_model=PeerStatus)
        async def get_peer_status(peer_id: str, db: Session = Depends(get_db)):
            """Obtiene el estado de un peer específico"""
            try:
                status = await self.peer_manager.get_peer_status(peer_id, db)
                if not status:
                    raise HTTPException(status_code=404, detail="Peer no encontrado")
                return status
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Error obteniendo estado del peer {peer_id}: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        # === RUTAS DE ARCHIVOS ===
        
        @self.app.post("/api/files/index/{peer_id}")
        async def index_peer_files(peer_id: str, db: Session = Depends(get_db)):
            """Indexa archivos de un peer específico"""
            try:
                success = await self.file_indexer.index_peer_files(peer_id, db)
                if success:
                    return {"success": True, "message": f"Archivos del peer {peer_id} indexados"}
                else:
                    raise HTTPException(status_code=400, detail="Error indexando archivos")
            except Exception as e:
                logger.error(f"Error indexando archivos del peer {peer_id}: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/api/files/index-all")
        async def index_all_peers(background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
            """Indexa archivos de todos los peers en línea"""
            try:
                results = await self.file_indexer.index_all_peers(db)
                return {
                    "success": True,
                    "message": "Indexación iniciada",
                    "results": results
                }
            except Exception as e:
                logger.error(f"Error indexando todos los peers: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/api/files/search", response_model=SearchResponse)
        async def search_files(search_request: SearchRequest, db: Session = Depends(get_db)):
            """Busca archivos en el índice central"""
            try:
                return await self.file_indexer.search_files(search_request, db)
            except Exception as e:
                logger.error(f"Error buscando archivos: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/api/files/{file_hash}", response_model=FileInfo)
        async def get_file_info(file_hash: str, db: Session = Depends(get_db)):
            """Obtiene información de un archivo específico"""
            try:
                file_info = await self.file_indexer.get_file_info(file_hash, db)
                if not file_info:
                    raise HTTPException(status_code=404, detail="Archivo no encontrado")
                return file_info
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Error obteniendo información del archivo {file_hash}: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/api/files/peer/{peer_id}", response_model=List[FileInfo])
        async def get_peer_files(
            peer_id: str, 
            page: int = 1, 
            limit: int = 50, 
            db: Session = Depends(get_db)
        ):
            """Obtiene todos los archivos de un peer específico con paginación"""
            try:
                # Validar parámetros de paginación
                if page < 1:
                    page = 1
                if limit < 1 or limit > 100:
                    limit = 50
                
                return await self.file_indexer.get_peer_files(peer_id, db, page, limit)
            except Exception as e:
                logger.error(f"Error obteniendo archivos del peer {peer_id}: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        # === RUTAS DE TRANSFERENCIAS ===
        
        @self.app.post("/api/transfers/download", response_model=DownloadResponse)
        async def initiate_download(download_request: DownloadRequest, db: Session = Depends(get_db)):
            """Inicia una descarga de archivo"""
            try:
                return await self.transfer_manager.initiate_download(download_request, db)
            except Exception as e:
                logger.error(f"Error iniciando descarga: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/api/transfers/upload", response_model=UploadResponse)
        async def initiate_upload(upload_request: UploadRequest, db: Session = Depends(get_db)):
            """Inicia una subida de archivo"""
            try:
                return await self.transfer_manager.initiate_upload(upload_request, db)
            except Exception as e:
                logger.error(f"Error iniciando subida: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/api/transfers/upload-file")
        async def upload_file(file: UploadFile = File(...), target_peer: str = Form(...), db: Session = Depends(get_db)):
            """Sube un archivo real al sistema"""
            try:
                from utils.file_validation import validate_upload_file, get_safe_temp_path
                
                # Leer contenido del archivo
                content = await file.read()
                
                # Validar archivo
                is_valid, error_message, file_hash = validate_upload_file(file.filename, content)
                if not is_valid:
                    raise HTTPException(status_code=400, detail=error_message)
                
                # Validar que se especifique un peer destino
                if not target_peer or target_peer.strip() == "":
                    raise HTTPException(status_code=400, detail="Debe especificar un peer destino")
                
                # Crear request de subida
                upload_request = UploadRequest(
                    filename=file.filename,
                    file_hash=file_hash,
                    file_size=len(content),
                    uploading_peer_id=target_peer
                )
                
                # Iniciar subida
                result = await self.transfer_manager.initiate_upload(upload_request, db)
                
                if result.success:
                    # Guardar archivo temporalmente para la subida usando ruta segura
                    temp_path = get_safe_temp_path(file.filename, file_hash)
                    
                    with open(temp_path, 'wb') as f:
                        f.write(content)
                    
                    # Realizar subida real
                    await self.transfer_manager._real_upload_with_file(result.file_id, upload_request, temp_path, db)
                    
                    # Limpiar archivo temporal
                    from utils.cleanup import safe_remove_file
                    safe_remove_file(temp_path)
                
                return result
                
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Error subiendo archivo: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/api/transfers/{transfer_id}/status", response_model=TransferStatus)
        async def get_transfer_status(transfer_id: int, db: Session = Depends(get_db)):
            """Obtiene el estado de una transferencia"""
            try:
                status = await self.transfer_manager.get_transfer_status(transfer_id, db)
                if not status:
                    raise HTTPException(status_code=404, detail="Transferencia no encontrada")
                return status
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Error obteniendo estado de transferencia {transfer_id}: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/api/transfers/active", response_model=List[TransferStatus])
        async def get_active_transfers(db: Session = Depends(get_db)):
            """Obtiene todas las transferencias activas"""
            try:
                return await self.transfer_manager.get_active_transfers(db)
            except Exception as e:
                logger.error(f"Error obteniendo transferencias activas: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/api/transfers/history", response_model=List[TransferStatus])
        async def get_transfer_history(
            peer_id: Optional[str] = None,
            limit: int = 100,
            db: Session = Depends(get_db)
        ):
            """Obtiene el historial de transferencias"""
            try:
                return await self.transfer_manager.get_transfer_history(peer_id, limit, db)
            except Exception as e:
                logger.error(f"Error obteniendo historial de transferencias: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        # === RUTAS DE SISTEMA ===
        
        @self.app.get("/api/health")
        async def health_check():
            """Verificación de salud del servidor central"""
            return {
                "status": "healthy",
                "service": "central_server",
                "version": "1.0.0"
            }
        
        @self.app.options("/api/{path:path}")
        async def options_handler(path: str):
            """Maneja peticiones OPTIONS para CORS"""
            from fastapi.responses import Response
            response = Response()
            response.headers["Access-Control-Allow-Origin"] = "*"
            response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
            response.headers["Access-Control-Allow-Headers"] = "*"
            response.headers["Access-Control-Allow-Credentials"] = "true"
            return response
        
        @self.app.get("/api/stats", response_model=SystemStats)
        async def get_system_stats(db: Session = Depends(get_db)):
            """Obtiene estadísticas del sistema"""
            try:
                stats = await self.file_indexer.get_system_stats(db)
                return SystemStats(**stats)
            except Exception as e:
                logger.error(f"Error obteniendo estadísticas del sistema: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/api/peers/{peer_id}/files", response_model=List[FileInfo])
        async def get_peer_files_detailed(peer_id: str, db: Session = Depends(get_db)):
            """Obtiene archivos detallados de un peer"""
            try:
                return await self.file_indexer.get_peer_files(peer_id, db)
            except Exception as e:
                logger.error(f"Error obteniendo archivos detallados del peer {peer_id}: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        # === RUTAS DE MONITOREO ===
        
        @self.app.get("/api/monitoring/health")
        async def get_health_status():
            """Obtiene el estado de salud del sistema"""
            try:
                return resource_monitor.get_health_status()
            except Exception as e:
                logger.error(f"Error obteniendo estado de salud: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/api/monitoring/metrics")
        async def get_system_metrics():
            """Obtiene métricas actuales del sistema"""
            try:
                return resource_monitor.get_system_metrics()
            except Exception as e:
                logger.error(f"Error obteniendo métricas del sistema: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/api/monitoring/history")
        async def get_metrics_history(limit: int = 10):
            """Obtiene el historial de métricas"""
            try:
                if limit < 1 or limit > 100:
                    limit = 10
                return resource_monitor.get_metrics_history(limit)
            except Exception as e:
                logger.error(f"Error obteniendo historial de métricas: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/api/monitoring/averages")
        async def get_average_metrics(minutes: int = 5):
            """Obtiene métricas promedio de los últimos N minutos"""
            try:
                if minutes < 1 or minutes > 60:
                    minutes = 5
                return resource_monitor.get_average_metrics(minutes)
            except Exception as e:
                logger.error(f"Error obteniendo métricas promedio: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        # === RUTAS DE ADMINISTRACIÓN ===
        
        @self.app.get("/api/admin/backups")
        async def list_backups():
            """Lista todos los backups disponibles"""
            try:
                backups = await backup_manager.list_backups()
                return {"backups": backups}
            except Exception as e:
                logger.error(f"Error listando backups: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/api/admin/backups/create")
        async def create_backup():
            """Crea un nuevo backup"""
            try:
                backup_info = await backup_manager.create_backup()
                return {"message": "Backup creado exitosamente", "backup": backup_info}
            except Exception as e:
                logger.error(f"Error creando backup: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/api/admin/backups/{backup_name}/restore")
        async def restore_backup(backup_name: str):
            """Restaura un backup específico"""
            try:
                success = await backup_manager.restore_backup(backup_name)
                if success:
                    return {"message": f"Backup {backup_name} restaurado exitosamente"}
                else:
                    raise HTTPException(status_code=404, detail="Backup no encontrado")
            except Exception as e:
                logger.error(f"Error restaurando backup: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/api/admin/alerts")
        async def get_alerts(level: str = None, type: str = None, resolved: bool = None):
            """Obtiene alertas del sistema"""
            try:
                alert_level = AlertLevel(level) if level else None
                alert_type = AlertType(type) if type else None
                
                alerts = alert_manager.get_alerts(level=alert_level, type=alert_type, resolved=resolved)
                
                # Convertir a dict para serialización
                alerts_data = []
                for alert in alerts:
                    alerts_data.append({
                        "id": alert.id,
                        "level": alert.level.value,
                        "type": alert.type.value,
                        "title": alert.title,
                        "message": alert.message,
                        "timestamp": alert.timestamp.isoformat(),
                        "source": alert.source,
                        "resolved": alert.resolved,
                        "resolved_at": alert.resolved_at.isoformat() if alert.resolved_at else None,
                        "data": alert.data
                    })
                
                return {"alerts": alerts_data}
            except Exception as e:
                logger.error(f"Error obteniendo alertas: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/api/admin/alerts/{alert_id}/resolve")
        async def resolve_alert(alert_id: str):
            """Resuelve una alerta específica"""
            try:
                success = await alert_manager.resolve_alert(alert_id)
                if success:
                    return {"message": f"Alerta {alert_id} resuelta exitosamente"}
                else:
                    raise HTTPException(status_code=404, detail="Alerta no encontrada")
            except Exception as e:
                logger.error(f"Error resolviendo alerta: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/api/admin/alerts/stats")
        async def get_alert_stats():
            """Obtiene estadísticas de alertas"""
            try:
                stats = alert_manager.get_alert_stats()
                return stats
            except Exception as e:
                logger.error(f"Error obteniendo estadísticas de alertas: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/api/admin/metrics")
        async def get_business_metrics(name: str = None, hours: int = 24):
            """Obtiene métricas de negocio"""
            try:
                if name:
                    metrics = business_metrics.get_metrics(name=name)
                    summary = business_metrics.get_metric_summary(name, hours)
                    return {"metrics": metrics, "summary": summary}
                else:
                    dashboard_metrics = business_metrics.get_dashboard_metrics()
                    return dashboard_metrics
            except Exception as e:
                logger.error(f"Error obteniendo métricas de negocio: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/api/admin/logs")
        async def get_system_logs(level: str = "INFO", limit: int = 100):
            """Obtiene logs del sistema"""
            try:
                # Esta es una implementación básica
                # En producción, se integraría con un sistema de logging más robusto
                return {
                    "message": "Endpoint de logs implementado",
                    "level": level,
                    "limit": limit,
                    "note": "Integrar con sistema de logging avanzado"
                }
            except Exception as e:
                logger.error(f"Error obteniendo logs: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/api/admin/health/detailed")
        async def get_detailed_health():
            """Obtiene estado de salud detallado del sistema"""
            try:
                # Estado de salud del sistema
                system_health = resource_monitor.get_health_status()
                
                # Estado de alertas
                alert_stats = alert_manager.get_alert_stats()
                
                # Métricas de negocio
                business_metrics_data = business_metrics.get_dashboard_metrics()
                
                # Estado de servicios
                services_status = {
                    "backup_manager": backup_manager.running,
                    "alert_manager": alert_manager.running,
                    "business_metrics": business_metrics.running,
                    "resource_monitor": True  # Siempre activo
                }
                
                return {
                    "system_health": system_health,
                    "alert_stats": alert_stats,
                    "business_metrics": business_metrics_data,
                    "services_status": services_status,
                    "timestamp": datetime.utcnow().isoformat()
                }
            except Exception as e:
                logger.error(f"Error obteniendo estado de salud detallado: {e}")
                raise HTTPException(status_code=500, detail=str(e))
    
    def get_app(self):
        """Retorna la aplicación FastAPI"""
        return self.app
