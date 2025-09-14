"""
Sistema de métricas de negocio y analytics
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from collections import defaultdict
from sqlalchemy.orm import Session
from models.database import Peer, File, TransferLog, get_db

logger = logging.getLogger(__name__)

@dataclass
class BusinessMetric:
    """Estructura de una métrica de negocio"""
    name: str
    value: float
    timestamp: datetime
    tags: Dict[str, str] = None
    metadata: Dict[str, Any] = None

class BusinessMetricsCollector:
    """Recolector de métricas de negocio"""
    
    def __init__(self):
        self.metrics: List[BusinessMetric] = []
        self.running = False
        self._task: Optional[asyncio.Task] = None
        self._retention_days = 30
    
    async def start(self):
        """Inicia el recolector de métricas"""
        if self.running:
            return
        
        self.running = True
        self._task = asyncio.create_task(self._collection_loop())
        logger.info("Recolector de métricas de negocio iniciado")
    
    async def stop(self):
        """Detiene el recolector de métricas"""
        self.running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("Recolector de métricas de negocio detenido")
    
    async def _collection_loop(self):
        """Loop principal de recolección de métricas"""
        while self.running:
            try:
                # Recolectar métricas
                await self._collect_peer_metrics()
                await self._collect_file_metrics()
                await self._collect_transfer_metrics()
                await self._collect_system_metrics()
                
                # Limpiar métricas antiguas
                await self._cleanup_old_metrics()
                
                # Esperar antes de la siguiente recolección
                await asyncio.sleep(300)  # Recolectar cada 5 minutos
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error en loop de recolección de métricas: {e}")
                await asyncio.sleep(600)  # Esperar más tiempo en caso de error
    
    async def _collect_peer_metrics(self):
        """Recolecta métricas de peers"""
        try:
            from utils.database import get_db_session
            async with get_db_session() as db:
                # Total de peers registrados
                total_peers = db.query(Peer).count()
                self._add_metric("peers.total", total_peers, {"type": "count"})
                
                # Peers online (asumiendo que los que están en la DB están online)
                online_peers = db.query(Peer).filter(Peer.is_online == True).count()
                self._add_metric("peers.online", online_peers, {"type": "count"})
                
                # Tasa de peers online
                if total_peers > 0:
                    online_rate = (online_peers / total_peers) * 100
                    self._add_metric("peers.online_rate", online_rate, {"type": "percentage"})
                
                # Peers por región (simulado)
                self._add_metric("peers.by_region", total_peers, {"region": "global", "type": "count"})
                
        except Exception as e:
            logger.error(f"Error recolectando métricas de peers: {e}")
    
    async def _collect_file_metrics(self):
        """Recolecta métricas de archivos"""
        try:
            from utils.database import get_db_session
            async with get_db_session() as db:
                # Total de archivos
                total_files = db.query(File).count()
                self._add_metric("files.total", total_files, {"type": "count"})
                
                # Tamaño total de archivos
                files = db.query(File).all()
                total_size = sum(file.file_size for file in files if file.file_size)
                self._add_metric("files.total_size", total_size, {"type": "bytes"})
                
                # Archivos por tipo
                file_types = defaultdict(int)
                for file in files:
                    if file.file_name:
                        ext = file.file_name.split('.')[-1].lower()
                        file_types[ext] += 1
                
                for ext, count in file_types.items():
                    self._add_metric("files.by_type", count, {"file_type": ext, "type": "count"})
                
                # Archivos por peer
                files_per_peer = db.query(File.peer_id, db.func.count(File.id)).group_by(File.peer_id).all()
                for peer_id, count in files_per_peer:
                    self._add_metric("files.per_peer", count, {"peer_id": peer_id, "type": "count"})
                
        except Exception as e:
            logger.error(f"Error recolectando métricas de archivos: {e}")
    
    async def _collect_transfer_metrics(self):
        """Recolecta métricas de transferencias"""
        try:
            from utils.database import get_db_session
            async with get_db_session() as db:
                # Transferencias totales
                total_transfers = db.query(TransferLog).count()
                self._add_metric("transfers.total", total_transfers, {"type": "count"})
                
                # Transferencias exitosas
                successful_transfers = db.query(TransferLog).filter(TransferLog.status == "completed").count()
                self._add_metric("transfers.successful", successful_transfers, {"type": "count"})
                
                # Tasa de éxito
                if total_transfers > 0:
                    success_rate = (successful_transfers / total_transfers) * 100
                    self._add_metric("transfers.success_rate", success_rate, {"type": "percentage"})
                
                # Transferencias por día (últimos 7 días)
                week_ago = datetime.utcnow() - timedelta(days=7)
                recent_transfers = db.query(TransferLog).filter(TransferLog.created_at >= week_ago).count()
                self._add_metric("transfers.last_7_days", recent_transfers, {"type": "count"})
                
                # Tamaño total transferido
                transfers = db.query(TransferLog).filter(TransferLog.status == "completed").all()
                total_transferred = sum(transfer.file_size for transfer in transfers if transfer.file_size)
                self._add_metric("transfers.total_size", total_transferred, {"type": "bytes"})
                
        except Exception as e:
            logger.error(f"Error recolectando métricas de transferencias: {e}")
    
    async def _collect_system_metrics(self):
        """Recolecta métricas del sistema"""
        try:
            import psutil
            
            # Uso de CPU
            cpu_percent = psutil.cpu_percent(interval=1)
            self._add_metric("system.cpu_usage", cpu_percent, {"type": "percentage"})
            
            # Uso de memoria
            memory = psutil.virtual_memory()
            self._add_metric("system.memory_usage", memory.percent, {"type": "percentage"})
            self._add_metric("system.memory_used", memory.used, {"type": "bytes"})
            self._add_metric("system.memory_total", memory.total, {"type": "bytes"})
            
            # Uso de disco
            disk = psutil.disk_usage('/')
            self._add_metric("system.disk_usage", disk.percent, {"type": "percentage"})
            self._add_metric("system.disk_used", disk.used, {"type": "bytes"})
            self._add_metric("system.disk_total", disk.total, {"type": "bytes"})
            
            # Red
            network = psutil.net_io_counters()
            self._add_metric("system.network_bytes_sent", network.bytes_sent, {"type": "bytes"})
            self._add_metric("system.network_bytes_recv", network.bytes_recv, {"type": "bytes"})
            
        except Exception as e:
            logger.error(f"Error recolectando métricas del sistema: {e}")
    
    def _add_metric(self, name: str, value: float, tags: Dict[str, str] = None, metadata: Dict[str, Any] = None):
        """Agrega una métrica"""
        metric = BusinessMetric(
            name=name,
            value=value,
            timestamp=datetime.utcnow(),
            tags=tags or {},
            metadata=metadata or {}
        )
        self.metrics.append(metric)
    
    async def _cleanup_old_metrics(self):
        """Limpia métricas antiguas"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=self._retention_days)
            self.metrics = [m for m in self.metrics if m.timestamp >= cutoff_date]
        except Exception as e:
            logger.error(f"Error limpiando métricas antiguas: {e}")
    
    def get_metrics(self, name: str = None, tags: Dict[str, str] = None, 
                   start_time: datetime = None, end_time: datetime = None) -> List[BusinessMetric]:
        """Obtiene métricas filtradas"""
        filtered_metrics = []
        
        for metric in self.metrics:
            if name and metric.name != name:
                continue
            
            if tags:
                if not all(metric.tags.get(k) == v for k, v in tags.items()):
                    continue
            
            if start_time and metric.timestamp < start_time:
                continue
            
            if end_time and metric.timestamp > end_time:
                continue
            
            filtered_metrics.append(metric)
        
        return filtered_metrics
    
    def get_metric_summary(self, name: str, hours: int = 24) -> Dict[str, Any]:
        """Obtiene resumen de una métrica"""
        try:
            start_time = datetime.utcnow() - timedelta(hours=hours)
            metrics = self.get_metrics(name=name, start_time=start_time)
            
            if not metrics:
                return {"error": "No metrics found"}
            
            values = [m.value for m in metrics]
            
            return {
                "name": name,
                "count": len(values),
                "min": min(values),
                "max": max(values),
                "avg": sum(values) / len(values),
                "latest": values[-1] if values else None,
                "period_hours": hours
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo resumen de métrica: {e}")
            return {"error": str(e)}
    
    def get_dashboard_metrics(self) -> Dict[str, Any]:
        """Obtiene métricas para dashboard"""
        try:
            # Métricas de peers
            peer_metrics = self.get_metrics(name="peers.total")
            total_peers = peer_metrics[-1].value if peer_metrics else 0
            
            online_metrics = self.get_metrics(name="peers.online")
            online_peers = online_metrics[-1].value if online_metrics else 0
            
            # Métricas de archivos
            file_metrics = self.get_metrics(name="files.total")
            total_files = file_metrics[-1].value if file_metrics else 0
            
            size_metrics = self.get_metrics(name="files.total_size")
            total_size = size_metrics[-1].value if size_metrics else 0
            
            # Métricas de transferencias
            transfer_metrics = self.get_metrics(name="transfers.total")
            total_transfers = transfer_metrics[-1].value if transfer_metrics else 0
            
            success_metrics = self.get_metrics(name="transfers.successful")
            successful_transfers = success_metrics[-1].value if success_metrics else 0
            
            # Métricas del sistema
            cpu_metrics = self.get_metrics(name="system.cpu_usage")
            cpu_usage = cpu_metrics[-1].value if cpu_metrics else 0
            
            memory_metrics = self.get_metrics(name="system.memory_usage")
            memory_usage = memory_metrics[-1].value if memory_metrics else 0
            
            return {
                "peers": {
                    "total": total_peers,
                    "online": online_peers,
                    "online_rate": (online_peers / total_peers * 100) if total_peers > 0 else 0
                },
                "files": {
                    "total": total_files,
                    "total_size": total_size,
                    "total_size_mb": total_size / 1024 / 1024 if total_size else 0
                },
                "transfers": {
                    "total": total_transfers,
                    "successful": successful_transfers,
                    "success_rate": (successful_transfers / total_transfers * 100) if total_transfers > 0 else 0
                },
                "system": {
                    "cpu_usage": cpu_usage,
                    "memory_usage": memory_usage
                }
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo métricas de dashboard: {e}")
            return {"error": str(e)}

# Instancia global del recolector de métricas
business_metrics = BusinessMetricsCollector()
