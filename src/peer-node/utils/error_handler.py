"""
Manejo de errores para el sistema P2P
"""

import logging
import traceback
from typing import Optional, Dict, Any
from enum import Enum

class ErrorType(Enum):
    """Tipos de errores del sistema"""
    PEER_UNAVAILABLE = "peer_unavailable"
    FILE_NOT_FOUND = "file_not_found"
    NETWORK_ERROR = "network_error"
    CONFIGURATION_ERROR = "configuration_error"
    CONCURRENCY_ERROR = "concurrency_error"
    UNKNOWN_ERROR = "unknown_error"

class P2PError(Exception):
    """Excepción base para errores del sistema P2P"""
    
    def __init__(self, message: str, error_type: ErrorType = ErrorType.UNKNOWN_ERROR, 
                 details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.error_type = error_type
        self.details = details or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte el error a diccionario"""
        return {
            "error": self.message,
            "type": self.error_type.value,
            "details": self.details
        }

class PeerUnavailableError(P2PError):
    """Error cuando un peer no está disponible"""
    
    def __init__(self, peer_id: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            f"Peer {peer_id} no está disponible",
            ErrorType.PEER_UNAVAILABLE,
            {"peer_id": peer_id, **(details or {})}
        )

class FileNotFoundError(P2PError):
    """Error cuando un archivo no se encuentra"""
    
    def __init__(self, file_hash: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            f"Archivo con hash {file_hash} no encontrado",
            ErrorType.FILE_NOT_FOUND,
            {"file_hash": file_hash, **(details or {})}
        )

class NetworkError(P2PError):
    """Error de red"""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            f"Error de red: {message}",
            ErrorType.NETWORK_ERROR,
            details or {}
        )

class ConfigurationError(P2PError):
    """Error de configuración"""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            f"Error de configuración: {message}",
            ErrorType.CONFIGURATION_ERROR,
            details or {}
        )

class ConcurrencyError(P2PError):
    """Error de concurrencia"""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            f"Error de concurrencia: {message}",
            ErrorType.CONCURRENCY_ERROR,
            details or {}
        )

class ErrorHandler:
    """Manejador de errores del sistema"""
    
    def __init__(self, logger_name: str = "p2p_error"):
        self.logger = logging.getLogger(logger_name)
        self.setup_logging()
    
    def setup_logging(self):
        """Configura el logging"""
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)
    
    def handle_error(self, error: Exception, context: str = "") -> Dict[str, Any]:
        """Maneja un error y retorna información estructurada"""
        error_info = {
            "context": context,
            "timestamp": None,
            "error": str(error),
            "type": "unknown",
            "details": {}
        }
        
        if isinstance(error, P2PError):
            error_info.update(error.to_dict())
        else:
            error_info["error"] = str(error)
            error_info["type"] = ErrorType.UNKNOWN_ERROR.value
            error_info["details"] = {
                "exception_type": type(error).__name__,
                "traceback": traceback.format_exc()
            }
        
        # Log del error
        self.logger.error(f"Error en {context}: {error_info}")
        
        return error_info
    
    def handle_peer_error(self, peer_id: str, error: Exception, operation: str = "") -> Dict[str, Any]:
        """Maneja errores específicos de peers"""
        context = f"Peer {peer_id}"
        if operation:
            context += f" - {operation}"
        
        if isinstance(error, aiohttp.ClientError):
            return self.handle_error(
                NetworkError(f"Error de conexión con peer {peer_id}: {error}"),
                context
            )
        elif isinstance(error, asyncio.TimeoutError):
            return self.handle_error(
                PeerUnavailableError(peer_id, {"operation": operation}),
                context
            )
        else:
            return self.handle_error(error, context)
    
    def handle_file_error(self, file_hash: str, error: Exception, operation: str = "") -> Dict[str, Any]:
        """Maneja errores específicos de archivos"""
        context = f"Archivo {file_hash[:8]}..."
        if operation:
            context += f" - {operation}"
        
        if isinstance(error, FileNotFoundError):
            return self.handle_error(error, context)
        elif isinstance(error, PermissionError):
            return self.handle_error(
                FileNotFoundError(file_hash, {"reason": "permission_denied"}),
                context
            )
        else:
            return self.handle_error(error, context)
    
    def create_error_response(self, error_info: Dict[str, Any], status_code: int = 500) -> Dict[str, Any]:
        """Crea una respuesta de error para APIs"""
        return {
            "success": False,
            "error": error_info["error"],
            "error_type": error_info["type"],
            "details": error_info["details"],
            "status_code": status_code
        }
    
    def log_operation(self, operation: str, peer_id: str = "", details: Dict[str, Any] = None):
        """Registra una operación exitosa"""
        message = f"Operación exitosa: {operation}"
        if peer_id:
            message += f" - Peer: {peer_id}"
        if details:
            message += f" - Detalles: {details}"
        
        self.logger.info(message)

# Instancia global del manejador de errores
error_handler = ErrorHandler()
