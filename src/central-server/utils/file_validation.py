"""
Utilidades para validación de archivos
"""

import os
import hashlib
from typing import List, Tuple
from fastapi import HTTPException

# Configuración de validación
ALLOWED_EXTENSIONS = {
    '.pdf', '.txt', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx',
    '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg',
    '.mp3', '.mp4', '.avi', '.mov', '.wav',
    '.zip', '.rar', '.7z', '.tar', '.gz',
    '.py', '.js', '.html', '.css', '.json', '.xml'
}

MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB
MIN_FILE_SIZE = 1  # 1 byte

def validate_file_extension(filename: str) -> bool:
    """Valida la extensión del archivo"""
    if not filename:
        return False
    
    _, ext = os.path.splitext(filename.lower())
    return ext in ALLOWED_EXTENSIONS

def validate_file_size(size: int) -> bool:
    """Valida el tamaño del archivo"""
    return MIN_FILE_SIZE <= size <= MAX_FILE_SIZE

def validate_filename(filename: str) -> bool:
    """Valida el nombre del archivo"""
    if not filename or len(filename) == 0:
        return False
    
    # Verificar caracteres peligrosos
    dangerous_chars = ['..', '/', '\\', ':', '*', '?', '"', '<', '>', '|']
    for char in dangerous_chars:
        if char in filename:
            return False
    
    # Verificar longitud máxima
    if len(filename) > 255:
        return False
    
    return True

def validate_file_content(content: bytes) -> Tuple[bool, str]:
    """Valida el contenido del archivo"""
    if not content:
        return False, "Archivo vacío"
    
    # Verificar tamaño
    if len(content) > MAX_FILE_SIZE:
        return False, f"Archivo demasiado grande. Máximo: {MAX_FILE_SIZE} bytes"
    
    if len(content) < MIN_FILE_SIZE:
        return False, f"Archivo demasiado pequeño. Mínimo: {MIN_FILE_SIZE} bytes"
    
    return True, ""

def calculate_file_hash(content: bytes) -> str:
    """Calcula el hash SHA256 del archivo"""
    return hashlib.sha256(content).hexdigest()

def validate_upload_file(filename: str, content: bytes) -> Tuple[bool, str, str]:
    """
    Valida completamente un archivo para subida
    Retorna: (es_válido, mensaje_error, hash_archivo)
    """
    # Validar nombre
    if not validate_filename(filename):
        return False, "Nombre de archivo inválido", ""
    
    # Validar extensión
    if not validate_file_extension(filename):
        allowed_exts = ", ".join(sorted(ALLOWED_EXTENSIONS))
        return False, f"Extensión no permitida. Permitidas: {allowed_exts}", ""
    
    # Validar contenido
    is_valid_content, content_error = validate_file_content(content)
    if not is_valid_content:
        return False, content_error, ""
    
    # Calcular hash
    file_hash = calculate_file_hash(content)
    
    return True, "", file_hash

def get_safe_temp_path(filename: str, file_hash: str) -> str:
    """Genera una ruta temporal segura para el archivo"""
    # Crear directorio temporal seguro
    temp_dir = "/tmp/redp2p_uploads"
    os.makedirs(temp_dir, exist_ok=True)
    
    # Generar nombre seguro
    safe_filename = f"{file_hash}_{filename}"
    
    return os.path.join(temp_dir, safe_filename)
