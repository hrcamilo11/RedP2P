"""
Sistema de logging avanzado y estructurado
"""

import logging
import json
import sys
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path
import traceback

class StructuredFormatter(logging.Formatter):
    """Formateador de logs estructurados en JSON"""
    
    def format(self, record):
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
            "thread": record.thread,
            "process": record.process
        }
        
        # Agregar información adicional si existe
        if hasattr(record, 'extra_data'):
            log_entry["extra_data"] = record.extra_data
        
        if hasattr(record, 'user_id'):
            log_entry["user_id"] = record.user_id
        
        if hasattr(record, 'request_id'):
            log_entry["request_id"] = record.request_id
        
        if hasattr(record, 'peer_id'):
            log_entry["peer_id"] = record.peer_id
        
        if hasattr(record, 'file_hash'):
            log_entry["file_hash"] = record.file_hash
        
        # Agregar excepción si existe
        if record.exc_info:
            log_entry["exception"] = {
                "type": record.exc_info[0].__name__,
                "message": str(record.exc_info[1]),
                "traceback": traceback.format_exception(*record.exc_info)
            }
        
        return json.dumps(log_entry, ensure_ascii=False)

class BusinessMetricsLogger:
    """Logger para métricas de negocio"""
    
    def __init__(self, logger_name: str = "business_metrics"):
        self.logger = logging.getLogger(logger_name)
        self.logger.setLevel(logging.INFO)
        
        # Configurar handler para métricas
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(StructuredFormatter())
        self.logger.addHandler(handler)
    
    def log_peer_activity(self, peer_id: str, action: str, details: Dict[str, Any] = None):
        """Registra actividad de peer"""
        self.logger.info(
            f"Peer activity: {action}",
            extra={
                "peer_id": peer_id,
                "action": action,
                "extra_data": details or {}
            }
        )
    
    def log_file_operation(self, file_hash: str, operation: str, peer_id: str = None, details: Dict[str, Any] = None):
        """Registra operación de archivo"""
        self.logger.info(
            f"File operation: {operation}",
            extra={
                "file_hash": file_hash,
                "operation": operation,
                "peer_id": peer_id,
                "extra_data": details or {}
            }
        )
    
    def log_transfer_event(self, transfer_id: str, event: str, details: Dict[str, Any] = None):
        """Registra evento de transferencia"""
        self.logger.info(
            f"Transfer event: {event}",
            extra={
                "transfer_id": transfer_id,
                "event": event,
                "extra_data": details or {}
            }
        )
    
    def log_system_event(self, event: str, details: Dict[str, Any] = None):
        """Registra evento del sistema"""
        self.logger.info(
            f"System event: {event}",
            extra={
                "event": event,
                "extra_data": details or {}
            }
        )

class PerformanceLogger:
    """Logger para métricas de performance"""
    
    def __init__(self, logger_name: str = "performance"):
        self.logger = logging.getLogger(logger_name)
        self.logger.setLevel(logging.INFO)
        
        # Configurar handler para performance
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(StructuredFormatter())
        self.logger.addHandler(handler)
    
    def log_api_request(self, method: str, path: str, duration_ms: float, status_code: int, user_id: str = None):
        """Registra petición API"""
        self.logger.info(
            f"API request: {method} {path}",
            extra={
                "method": method,
                "path": path,
                "duration_ms": duration_ms,
                "status_code": status_code,
                "user_id": user_id,
                "extra_data": {
                    "request_type": "api"
                }
            }
        )
    
    def log_database_query(self, query_type: str, duration_ms: float, rows_affected: int = None):
        """Registra consulta de base de datos"""
        self.logger.info(
            f"Database query: {query_type}",
            extra={
                "query_type": query_type,
                "duration_ms": duration_ms,
                "rows_affected": rows_affected,
                "extra_data": {
                    "request_type": "database"
                }
            }
        )
    
    def log_cache_operation(self, operation: str, key: str, hit: bool, duration_ms: float = None):
        """Registra operación de cache"""
        self.logger.info(
            f"Cache operation: {operation}",
            extra={
                "operation": operation,
                "key": key,
                "hit": hit,
                "duration_ms": duration_ms,
                "extra_data": {
                    "request_type": "cache"
                }
            }
        )

def setup_advanced_logging(log_level: str = "INFO", log_file: str = None):
    """Configura el sistema de logging avanzado"""
    
    # Crear directorio de logs si no existe
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # Configurar logger raíz
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))
    
    # Limpiar handlers existentes
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Handler para consola
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(StructuredFormatter())
    root_logger.addHandler(console_handler)
    
    # Handler para archivo si se especifica
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(StructuredFormatter())
        root_logger.addHandler(file_handler)
    
    # Configurar loggers específicos
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.error").setLevel(logging.INFO)
    
    return root_logger

# Instancias globales
business_logger = BusinessMetricsLogger()
performance_logger = PerformanceLogger()

# Decorador para logging de performance
def log_performance(operation_name: str):
    """Decorador para logging automático de performance"""
    def decorator(func):
        async def async_wrapper(*args, **kwargs):
            start_time = datetime.utcnow()
            try:
                result = await func(*args, **kwargs)
                duration = (datetime.utcnow() - start_time).total_seconds() * 1000
                performance_logger.log_api_request(
                    method=operation_name,
                    path=func.__name__,
                    duration_ms=duration,
                    status_code=200
                )
                return result
            except Exception as e:
                duration = (datetime.utcnow() - start_time).total_seconds() * 1000
                performance_logger.log_api_request(
                    method=operation_name,
                    path=func.__name__,
                    duration_ms=duration,
                    status_code=500
                )
                raise e
        
        def sync_wrapper(*args, **kwargs):
            start_time = datetime.utcnow()
            try:
                result = func(*args, **kwargs)
                duration = (datetime.utcnow() - start_time).total_seconds() * 1000
                performance_logger.log_api_request(
                    method=operation_name,
                    path=func.__name__,
                    duration_ms=duration,
                    status_code=200
                )
                return result
            except Exception as e:
                duration = (datetime.utcnow() - start_time).total_seconds() * 1000
                performance_logger.log_api_request(
                    method=operation_name,
                    path=func.__name__,
                    duration_ms=duration,
                    status_code=500
                )
                raise e
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator
