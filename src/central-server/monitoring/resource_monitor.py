"""
Sistema de monitoreo de recursos del servidor
"""

import psutil
import asyncio
import logging
from typing import Dict, Any
from datetime import datetime
import os

logger = logging.getLogger(__name__)

class ResourceMonitor:
    """Monitor de recursos del sistema"""
    
    def __init__(self):
        self.start_time = datetime.utcnow()
        self.metrics_history = []
        self.max_history = 100
    
    def get_system_metrics(self) -> Dict[str, Any]:
        """Obtiene métricas del sistema"""
        try:
            # CPU
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_count = psutil.cpu_count()
            
            # Memoria
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            memory_used = memory.used
            memory_total = memory.total
            memory_available = memory.available
            
            # Disco
            disk = psutil.disk_usage('/')
            disk_percent = disk.percent
            disk_used = disk.used
            disk_total = disk.total
            disk_free = disk.free
            
            # Red
            network = psutil.net_io_counters()
            bytes_sent = network.bytes_sent
            bytes_recv = network.bytes_recv
            packets_sent = network.packets_sent
            packets_recv = network.packets_recv
            
            # Procesos
            process = psutil.Process()
            process_cpu = process.cpu_percent()
            process_memory = process.memory_info()
            process_memory_mb = process_memory.rss / 1024 / 1024
            
            # Tiempo de actividad
            uptime = (datetime.utcnow() - self.start_time).total_seconds()
            
            metrics = {
                "timestamp": datetime.utcnow().isoformat(),
                "uptime_seconds": uptime,
                "cpu": {
                    "percent": cpu_percent,
                    "count": cpu_count
                },
                "memory": {
                    "percent": memory_percent,
                    "used_bytes": memory_used,
                    "total_bytes": memory_total,
                    "available_bytes": memory_available,
                    "used_mb": round(memory_used / 1024 / 1024, 2),
                    "total_mb": round(memory_total / 1024 / 1024, 2),
                    "available_mb": round(memory_available / 1024 / 1024, 2)
                },
                "disk": {
                    "percent": disk_percent,
                    "used_bytes": disk_used,
                    "total_bytes": disk_total,
                    "free_bytes": disk_free,
                    "used_gb": round(disk_used / 1024 / 1024 / 1024, 2),
                    "total_gb": round(disk_total / 1024 / 1024 / 1024, 2),
                    "free_gb": round(disk_free / 1024 / 1024 / 1024, 2)
                },
                "network": {
                    "bytes_sent": bytes_sent,
                    "bytes_recv": bytes_recv,
                    "packets_sent": packets_sent,
                    "packets_recv": packets_recv
                },
                "process": {
                    "cpu_percent": process_cpu,
                    "memory_mb": round(process_memory_mb, 2),
                    "pid": process.pid
                }
            }
            
            # Agregar a historial
            self.metrics_history.append(metrics)
            if len(self.metrics_history) > self.max_history:
                self.metrics_history.pop(0)
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error obteniendo métricas del sistema: {e}")
            return {
                "timestamp": datetime.utcnow().isoformat(),
                "error": str(e)
            }
    
    def get_health_status(self) -> Dict[str, Any]:
        """Obtiene el estado de salud del sistema"""
        try:
            metrics = self.get_system_metrics()
            
            # Definir umbrales de alerta
            cpu_threshold = 80
            memory_threshold = 85
            disk_threshold = 90
            
            alerts = []
            status = "healthy"
            
            # Verificar CPU
            if metrics.get("cpu", {}).get("percent", 0) > cpu_threshold:
                alerts.append(f"CPU usage high: {metrics['cpu']['percent']}%")
                status = "warning"
            
            # Verificar memoria
            if metrics.get("memory", {}).get("percent", 0) > memory_threshold:
                alerts.append(f"Memory usage high: {metrics['memory']['percent']}%")
                status = "warning"
            
            # Verificar disco
            if metrics.get("disk", {}).get("percent", 0) > disk_threshold:
                alerts.append(f"Disk usage high: {metrics['disk']['percent']}%")
                status = "critical"
            
            return {
                "status": status,
                "alerts": alerts,
                "metrics": metrics,
                "thresholds": {
                    "cpu": cpu_threshold,
                    "memory": memory_threshold,
                    "disk": disk_threshold
                }
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo estado de salud: {e}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    def get_metrics_history(self, limit: int = 10) -> list:
        """Obtiene el historial de métricas"""
        return self.metrics_history[-limit:]
    
    def get_average_metrics(self, minutes: int = 5) -> Dict[str, Any]:
        """Obtiene métricas promedio de los últimos N minutos"""
        try:
            cutoff_time = datetime.utcnow().timestamp() - (minutes * 60)
            
            recent_metrics = [
                m for m in self.metrics_history 
                if datetime.fromisoformat(m["timestamp"]).timestamp() > cutoff_time
            ]
            
            if not recent_metrics:
                return {"error": "No data available"}
            
            # Calcular promedios
            avg_cpu = sum(m.get("cpu", {}).get("percent", 0) for m in recent_metrics) / len(recent_metrics)
            avg_memory = sum(m.get("memory", {}).get("percent", 0) for m in recent_metrics) / len(recent_metrics)
            avg_disk = sum(m.get("disk", {}).get("percent", 0) for m in recent_metrics) / len(recent_metrics)
            
            return {
                "period_minutes": minutes,
                "samples": len(recent_metrics),
                "averages": {
                    "cpu_percent": round(avg_cpu, 2),
                    "memory_percent": round(avg_memory, 2),
                    "disk_percent": round(avg_disk, 2)
                },
                "current": recent_metrics[-1] if recent_metrics else None
            }
            
        except Exception as e:
            logger.error(f"Error calculando métricas promedio: {e}")
            return {"error": str(e)}

# Instancia global del monitor
resource_monitor = ResourceMonitor()
