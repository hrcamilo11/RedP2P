"""
Sistema de alertas y notificaciones
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable
from enum import Enum
from dataclasses import dataclass
from config.settings import settings

logger = logging.getLogger(__name__)

class AlertLevel(str, Enum):
    """Niveles de alerta"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

class AlertType(str, Enum):
    """Tipos de alerta"""
    SYSTEM = "system"
    PEER = "peer"
    TRANSFER = "transfer"
    SECURITY = "security"
    PERFORMANCE = "performance"
    STORAGE = "storage"

@dataclass
class Alert:
    """Estructura de una alerta"""
    id: str
    level: AlertLevel
    type: AlertType
    title: str
    message: str
    timestamp: datetime
    source: str
    data: Dict[str, Any] = None
    resolved: bool = False
    resolved_at: Optional[datetime] = None

class AlertManager:
    """Gestor de alertas y notificaciones"""
    
    def __init__(self):
        self.alerts: Dict[str, Alert] = {}
        self.alert_callbacks: List[Callable] = []
        self.running = False
        self._task: Optional[asyncio.Task] = None
        self._alert_counter = 0
    
    async def start(self):
        """Inicia el gestor de alertas"""
        if self.running:
            return
        
        self.running = True
        self._task = asyncio.create_task(self._alert_loop())
        logger.info("Gestor de alertas iniciado")
    
    async def stop(self):
        """Detiene el gestor de alertas"""
        self.running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("Gestor de alertas detenido")
    
    async def _alert_loop(self):
        """Loop principal de monitoreo de alertas"""
        while self.running:
            try:
                # Verificar alertas del sistema
                await self._check_system_alerts()
                
                # Verificar alertas de peers
                await self._check_peer_alerts()
                
                # Verificar alertas de transferencias
                await self._check_transfer_alerts()
                
                # Limpiar alertas antiguas
                await self._cleanup_old_alerts()
                
                # Esperar antes de la siguiente verificación
                await asyncio.sleep(30)  # Verificar cada 30 segundos
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error en loop de alertas: {e}")
                await asyncio.sleep(60)  # Esperar más tiempo en caso de error
    
    async def create_alert(self, level: AlertLevel, type: AlertType, title: str, 
                          message: str, source: str, data: Dict[str, Any] = None) -> str:
        """Crea una nueva alerta"""
        try:
            self._alert_counter += 1
            alert_id = f"alert_{self._alert_counter}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
            
            alert = Alert(
                id=alert_id,
                level=level,
                type=type,
                title=title,
                message=message,
                timestamp=datetime.utcnow(),
                source=source,
                data=data or {}
            )
            
            self.alerts[alert_id] = alert
            
            # Notificar a callbacks
            await self._notify_alert(alert)
            
            logger.info(f"Alerta creada: {alert_id} - {title}")
            return alert_id
            
        except Exception as e:
            logger.error(f"Error creando alerta: {e}")
            return None
    
    async def resolve_alert(self, alert_id: str) -> bool:
        """Resuelve una alerta"""
        try:
            if alert_id in self.alerts:
                self.alerts[alert_id].resolved = True
                self.alerts[alert_id].resolved_at = datetime.utcnow()
                logger.info(f"Alerta resuelta: {alert_id}")
                return True
            return False
            
        except Exception as e:
            logger.error(f"Error resolviendo alerta: {e}")
            return False
    
    async def _check_system_alerts(self):
        """Verifica alertas del sistema"""
        try:
            # Verificar uso de CPU
            import psutil
            cpu_percent = psutil.cpu_percent(interval=1)
            if cpu_percent > settings.ALERT_CPU_THRESHOLD:
                await self.create_alert(
                    level=AlertLevel.WARNING,
                    type=AlertType.SYSTEM,
                    title="Alto uso de CPU",
                    message=f"Uso de CPU: {cpu_percent:.1f}% (límite: {settings.ALERT_CPU_THRESHOLD}%)",
                    source="system_monitor",
                    data={"cpu_percent": cpu_percent, "threshold": settings.ALERT_CPU_THRESHOLD}
                )
            
            # Verificar uso de memoria
            memory = psutil.virtual_memory()
            if memory.percent > settings.ALERT_MEMORY_THRESHOLD:
                await self.create_alert(
                    level=AlertLevel.WARNING,
                    type=AlertType.SYSTEM,
                    title="Alto uso de memoria",
                    message=f"Uso de memoria: {memory.percent:.1f}% (límite: {settings.ALERT_MEMORY_THRESHOLD}%)",
                    source="system_monitor",
                    data={"memory_percent": memory.percent, "threshold": settings.ALERT_MEMORY_THRESHOLD}
                )
            
            # Verificar uso de disco
            disk = psutil.disk_usage('/')
            if disk.percent > settings.ALERT_DISK_THRESHOLD:
                await self.create_alert(
                    level=AlertLevel.CRITICAL,
                    type=AlertType.STORAGE,
                    title="Alto uso de disco",
                    message=f"Uso de disco: {disk.percent:.1f}% (límite: {settings.ALERT_DISK_THRESHOLD}%)",
                    source="system_monitor",
                    data={"disk_percent": disk.percent, "threshold": settings.ALERT_DISK_THRESHOLD}
                )
            
        except Exception as e:
            logger.error(f"Error verificando alertas del sistema: {e}")
    
    async def _check_peer_alerts(self):
        """Verifica alertas de peers"""
        try:
            # Esta función se integraría con el PeerManager
            # Por ahora, solo un ejemplo de implementación
            pass
            
        except Exception as e:
            logger.error(f"Error verificando alertas de peers: {e}")
    
    async def _check_transfer_alerts(self):
        """Verifica alertas de transferencias"""
        try:
            # Esta función se integraría con el TransferManager
            # Por ahora, solo un ejemplo de implementación
            pass
            
        except Exception as e:
            logger.error(f"Error verificando alertas de transferencias: {e}")
    
    async def _cleanup_old_alerts(self):
        """Limpia alertas antiguas"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=7)  # Mantener 7 días
            
            alerts_to_remove = []
            for alert_id, alert in self.alerts.items():
                if alert.timestamp < cutoff_date and alert.resolved:
                    alerts_to_remove.append(alert_id)
            
            for alert_id in alerts_to_remove:
                del self.alerts[alert_id]
            
            if alerts_to_remove:
                logger.info(f"Limpiadas {len(alerts_to_remove)} alertas antiguas")
                
        except Exception as e:
            logger.error(f"Error limpiando alertas antiguas: {e}")
    
    async def _notify_alert(self, alert: Alert):
        """Notifica una alerta a los callbacks registrados"""
        for callback in self.alert_callbacks:
            try:
                await callback(alert)
            except Exception as e:
                logger.error(f"Error en callback de alerta: {e}")
    
    def add_alert_callback(self, callback: Callable):
        """Agrega un callback para notificaciones de alertas"""
        self.alert_callbacks.append(callback)
    
    def get_alerts(self, level: AlertLevel = None, type: AlertType = None, 
                   resolved: bool = None) -> List[Alert]:
        """Obtiene alertas filtradas"""
        filtered_alerts = []
        
        for alert in self.alerts.values():
            if level and alert.level != level:
                continue
            if type and alert.type != type:
                continue
            if resolved is not None and alert.resolved != resolved:
                continue
            
            filtered_alerts.append(alert)
        
        # Ordenar por timestamp (más reciente primero)
        filtered_alerts.sort(key=lambda x: x.timestamp, reverse=True)
        
        return filtered_alerts
    
    def get_alert_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas de alertas"""
        total_alerts = len(self.alerts)
        resolved_alerts = sum(1 for alert in self.alerts.values() if alert.resolved)
        active_alerts = total_alerts - resolved_alerts
        
        # Contar por nivel
        level_counts = {}
        for alert in self.alerts.values():
            level_counts[alert.level] = level_counts.get(alert.level, 0) + 1
        
        # Contar por tipo
        type_counts = {}
        for alert in self.alerts.values():
            type_counts[alert.type] = type_counts.get(alert.type, 0) + 1
        
        return {
            "total_alerts": total_alerts,
            "active_alerts": active_alerts,
            "resolved_alerts": resolved_alerts,
            "level_counts": level_counts,
            "type_counts": type_counts
        }

# Instancia global del gestor de alertas
alert_manager = AlertManager()
