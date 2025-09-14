"""
Utilidades de compresión para archivos
"""

import gzip
import os
import tempfile
import logging
from typing import Tuple, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

class FileCompressor:
    """Compresor de archivos para optimizar transferencias"""
    
    def __init__(self, min_size_mb: int = 1, compression_level: int = 6):
        self.min_size_mb = min_size_mb * 1024 * 1024  # Convertir a bytes
        self.compression_level = compression_level
    
    def should_compress(self, file_size: int) -> bool:
        """Determina si un archivo debe ser comprimido"""
        return file_size >= self.min_size_mb
    
    def compress_file(self, input_path: str, output_path: Optional[str] = None) -> Tuple[str, int, float]:
        """
        Comprime un archivo
        
        Args:
            input_path: Ruta del archivo a comprimir
            output_path: Ruta de salida (opcional)
            
        Returns:
            Tuple[ruta_archivo_comprimido, tamaño_original, ratio_compresión]
        """
        try:
            if not os.path.exists(input_path):
                raise FileNotFoundError(f"Archivo no encontrado: {input_path}")
            
            file_size = os.path.getsize(input_path)
            
            # Si el archivo es muy pequeño, no comprimir
            if not self.should_compress(file_size):
                logger.info(f"Archivo {input_path} es muy pequeño para comprimir")
                return input_path, file_size, 1.0
            
            # Generar ruta de salida si no se proporciona
            if not output_path:
                output_path = f"{input_path}.gz"
            
            # Comprimir archivo
            with open(input_path, 'rb') as f_in:
                with gzip.open(output_path, 'wb', compresslevel=self.compression_level) as f_out:
                    f_out.write(f_in.read())
            
            compressed_size = os.path.getsize(output_path)
            compression_ratio = compressed_size / file_size if file_size > 0 else 1.0
            
            logger.info(f"Archivo comprimido: {input_path} -> {output_path}")
            logger.info(f"Tamaño original: {file_size} bytes, comprimido: {compressed_size} bytes")
            logger.info(f"Ratio de compresión: {compression_ratio:.2f}")
            
            return output_path, file_size, compression_ratio
            
        except Exception as e:
            logger.error(f"Error comprimiendo archivo {input_path}: {e}")
            raise e
    
    def decompress_file(self, input_path: str, output_path: Optional[str] = None) -> str:
        """
        Descomprime un archivo
        
        Args:
            input_path: Ruta del archivo comprimido
            output_path: Ruta de salida (opcional)
            
        Returns:
            Ruta del archivo descomprimido
        """
        try:
            if not os.path.exists(input_path):
                raise FileNotFoundError(f"Archivo comprimido no encontrado: {input_path}")
            
            # Generar ruta de salida si no se proporciona
            if not output_path:
                if input_path.endswith('.gz'):
                    output_path = input_path[:-3]  # Quitar .gz
                else:
                    output_path = f"{input_path}.decompressed"
            
            # Descomprimir archivo
            with gzip.open(input_path, 'rb') as f_in:
                with open(output_path, 'wb') as f_out:
                    f_out.write(f_in.read())
            
            logger.info(f"Archivo descomprimido: {input_path} -> {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Error descomprimiendo archivo {input_path}: {e}")
            raise e
    
    def get_compression_info(self, file_path: str) -> dict:
        """Obtiene información sobre la compresión de un archivo"""
        try:
            if not os.path.exists(file_path):
                return {"error": "Archivo no encontrado"}
            
            file_size = os.path.getsize(file_path)
            is_compressed = file_path.endswith('.gz')
            
            info = {
                "file_path": file_path,
                "file_size": file_size,
                "file_size_mb": round(file_size / 1024 / 1024, 2),
                "is_compressed": is_compressed,
                "should_compress": self.should_compress(file_size),
                "compression_level": self.compression_level
            }
            
            # Si está comprimido, intentar obtener tamaño descomprimido
            if is_compressed:
                try:
                    with gzip.open(file_path, 'rb') as f:
                        f.read(1)  # Leer un byte para verificar que es válido
                        # Obtener tamaño descomprimido aproximado
                        with gzip.open(file_path, 'rb') as f:
                            decompressed_size = len(f.read())
                        info["decompressed_size"] = decompressed_size
                        info["compression_ratio"] = file_size / decompressed_size if decompressed_size > 0 else 1.0
                except Exception as e:
                    info["decompression_error"] = str(e)
            
            return info
            
        except Exception as e:
            logger.error(f"Error obteniendo información de compresión: {e}")
            return {"error": str(e)}

# Instancia global del compresor
file_compressor = FileCompressor(min_size_mb=1, compression_level=6)
