"""
Utilidades de validación de entrada para APIs
"""

import re
import ipaddress
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, validator
import logging

logger = logging.getLogger(__name__)

class ValidationError(Exception):
    """Excepción personalizada para errores de validación"""
    pass

class InputValidator:
    """Validador de entradas para APIs"""
    
    # Patrones de validación
    PATTERNS = {
        'peer_id': r'^[a-zA-Z0-9_-]{3,50}$',
        'file_hash': r'^[a-f0-9]{64}$',  # SHA256
        'filename': r'^[^<>:"/\\|?*]{1,255}$',
        'ip_address': r'^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$',
        'port': r'^(?:[0-9]{1,4}|[1-5][0-9]{4}|6[0-4][0-9]{3}|65[0-4][0-9]{2}|655[0-2][0-9]|6553[0-5])$',
        'search_query': r'^[a-zA-Z0-9\s._-]{1,100}$'
    }
    
    # Límites de validación
    LIMITS = {
        'max_filename_length': 255,
        'max_search_query_length': 100,
        'max_peer_id_length': 50,
        'min_peer_id_length': 3,
        'max_file_size_mb': 100,
        'max_page_size': 100,
        'min_page_size': 1,
        'max_search_results': 1000
    }
    
    @classmethod
    def validate_peer_id(cls, peer_id: str) -> bool:
        """Valida un ID de peer"""
        if not peer_id or not isinstance(peer_id, str):
            return False
        
        if not (cls.LIMITS['min_peer_id_length'] <= len(peer_id) <= cls.LIMITS['max_peer_id_length']):
            return False
        
        return bool(re.match(cls.PATTERNS['peer_id'], peer_id))
    
    @classmethod
    def validate_file_hash(cls, file_hash: str) -> bool:
        """Valida un hash de archivo SHA256"""
        if not file_hash or not isinstance(file_hash, str):
            return False
        
        return bool(re.match(cls.PATTERNS['file_hash'], file_hash))
    
    @classmethod
    def validate_filename(cls, filename: str) -> bool:
        """Valida un nombre de archivo"""
        if not filename or not isinstance(filename, str):
            return False
        
        if len(filename) > cls.LIMITS['max_filename_length']:
            return False
        
        # Verificar caracteres no permitidos
        if not re.match(cls.PATTERNS['filename'], filename):
            return False
        
        # Verificar que no sea solo puntos o espacios
        if filename.strip('. ').strip() == '':
            return False
        
        return True
    
    @classmethod
    def validate_ip_address(cls, ip: str) -> bool:
        """Valida una dirección IP"""
        if not ip or not isinstance(ip, str):
            return False
        
        try:
            ipaddress.ip_address(ip)
            return True
        except ValueError:
            return False
    
    @classmethod
    def validate_port(cls, port: Union[int, str]) -> bool:
        """Valida un puerto"""
        try:
            port_int = int(port)
            return 1 <= port_int <= 65535
        except (ValueError, TypeError):
            return False
    
    @classmethod
    def validate_search_query(cls, query: str) -> bool:
        """Valida una consulta de búsqueda"""
        if not query or not isinstance(query, str):
            return False
        
        if len(query.strip()) < 1:
            return False
        
        if len(query) > cls.LIMITS['max_search_query_length']:
            return False
        
        # Verificar caracteres permitidos
        return bool(re.match(cls.PATTERNS['search_query'], query.strip()))
    
    @classmethod
    def validate_pagination(cls, page: int, limit: int) -> bool:
        """Valida parámetros de paginación"""
        if not isinstance(page, int) or not isinstance(limit, int):
            return False
        
        if page < 1:
            return False
        
        if not (cls.LIMITS['min_page_size'] <= limit <= cls.LIMITS['max_page_size']):
            return False
        
        return True
    
    @classmethod
    def validate_file_size(cls, size_bytes: int) -> bool:
        """Valida el tamaño de un archivo"""
        if not isinstance(size_bytes, int):
            return False
        
        max_size_bytes = cls.LIMITS['max_file_size_mb'] * 1024 * 1024
        return 0 < size_bytes <= max_size_bytes
    
    @classmethod
    def sanitize_string(cls, text: str, max_length: int = 255) -> str:
        """Sanitiza una cadena de texto"""
        if not text or not isinstance(text, str):
            return ""
        
        # Remover caracteres de control y espacios extra
        sanitized = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', text.strip())
        
        # Limitar longitud
        if len(sanitized) > max_length:
            sanitized = sanitized[:max_length]
        
        return sanitized
    
    @classmethod
    def validate_peer_registration(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        """Valida datos de registro de peer"""
        errors = []
        
        # Validar peer_id
        if 'peer_id' not in data or not cls.validate_peer_id(data['peer_id']):
            errors.append("peer_id inválido")
        
        # Validar host
        if 'host' not in data or not cls.validate_ip_address(data['host']):
            errors.append("host inválido")
        
        # Validar puerto
        if 'port' not in data or not cls.validate_port(data['port']):
            errors.append("port inválido")
        
        # Validar puerto gRPC si existe
        if 'grpc_port' in data and not cls.validate_port(data['grpc_port']):
            errors.append("grpc_port inválido")
        
        # Validar shared_directory
        if 'shared_directory' in data:
            shared_dir = data['shared_directory']
            if not isinstance(shared_dir, str) or len(shared_dir.strip()) == 0:
                errors.append("shared_directory inválido")
        
        if errors:
            raise ValidationError(f"Errores de validación: {', '.join(errors)}")
        
        return data
    
    @classmethod
    def validate_search_request(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        """Valida datos de búsqueda"""
        errors = []
        
        # Validar query
        if 'query' not in data or not cls.validate_search_query(data['query']):
            errors.append("query de búsqueda inválida")
        
        # Validar paginación
        page = data.get('page', 1)
        limit = data.get('limit', 50)
        
        if not cls.validate_pagination(page, limit):
            errors.append("parámetros de paginación inválidos")
        
        # Validar peer_id si existe
        if 'peer_id' in data and data['peer_id'] and not cls.validate_peer_id(data['peer_id']):
            errors.append("peer_id inválido")
        
        if errors:
            raise ValidationError(f"Errores de validación: {', '.join(errors)}")
        
        return data
    
    @classmethod
    def validate_download_request(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        """Valida datos de descarga"""
        errors = []
        
        # Validar file_hash
        if 'file_hash' not in data or not cls.validate_file_hash(data['file_hash']):
            errors.append("file_hash inválido")
        
        # Validar target_peer si existe
        if 'target_peer' in data and data['target_peer'] and not cls.validate_peer_id(data['target_peer']):
            errors.append("target_peer inválido")
        
        if errors:
            raise ValidationError(f"Errores de validación: {', '.join(errors)}")
        
        return data

# Instancia global del validador
input_validator = InputValidator()
