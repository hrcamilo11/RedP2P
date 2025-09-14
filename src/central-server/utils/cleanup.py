"""
Utilidades para limpieza de archivos temporales
"""

import os
import time
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

def cleanup_temp_files(temp_dir: str = "/tmp/redp2p_uploads", max_age_hours: int = 24):
    """
    Limpia archivos temporales más antiguos que max_age_hours
    
    Args:
        temp_dir: Directorio temporal a limpiar
        max_age_hours: Edad máxima en horas para mantener archivos
    """
    try:
        if not os.path.exists(temp_dir):
            logger.info(f"Directorio temporal {temp_dir} no existe")
            return
        
        current_time = time.time()
        max_age_seconds = max_age_hours * 3600
        cleaned_count = 0
        total_size = 0
        
        for file_path in Path(temp_dir).iterdir():
            if file_path.is_file():
                file_age = current_time - file_path.stat().st_mtime
                
                if file_age > max_age_seconds:
                    file_size = file_path.stat().st_size
                    try:
                        file_path.unlink()
                        cleaned_count += 1
                        total_size += file_size
                        logger.info(f"Archivo temporal eliminado: {file_path}")
                    except Exception as e:
                        logger.warning(f"Error eliminando archivo {file_path}: {e}")
        
        if cleaned_count > 0:
            logger.info(f"Limpieza completada: {cleaned_count} archivos, {total_size} bytes liberados")
        else:
            logger.info("No hay archivos temporales para limpiar")
            
    except Exception as e:
        logger.error(f"Error en limpieza de archivos temporales: {e}")

def safe_remove_file(file_path: str) -> bool:
    """
    Elimina un archivo de forma segura
    
    Args:
        file_path: Ruta del archivo a eliminar
        
    Returns:
        True si se eliminó correctamente, False en caso contrario
    """
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            logger.info(f"Archivo eliminado: {file_path}")
            return True
        return False
    except Exception as e:
        logger.warning(f"Error eliminando archivo {file_path}: {e}")
        return False
