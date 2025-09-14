"""
Sistema de backup automático para la base de datos y archivos
"""

import asyncio
import shutil
import sqlite3
import gzip
import os
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any, Optional
from config.settings import settings

logger = logging.getLogger(__name__)

class BackupManager:
    """Gestor de backups automáticos"""
    
    def __init__(self):
        self.backup_dir = Path(settings.BACKUP_DIR)
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        self.running = False
        self._task: Optional[asyncio.Task] = None
    
    async def start(self):
        """Inicia el gestor de backup"""
        if self.running:
            return
        
        self.running = True
        self._task = asyncio.create_task(self._backup_loop())
        logger.info("Gestor de backup iniciado")
    
    async def stop(self):
        """Detiene el gestor de backup"""
        self.running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("Gestor de backup detenido")
    
    async def _backup_loop(self):
        """Loop principal de backup"""
        while self.running:
            try:
                if settings.BACKUP_ENABLED:
                    await self.create_backup()
                
                # Esperar hasta el próximo backup
                await asyncio.sleep(settings.BACKUP_INTERVAL_HOURS * 3600)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error en loop de backup: {e}")
                await asyncio.sleep(3600)  # Esperar 1 hora en caso de error
    
    async def create_backup(self) -> Dict[str, Any]:
        """Crea un backup completo del sistema"""
        try:
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            backup_name = f"redp2p_backup_{timestamp}"
            backup_path = self.backup_dir / backup_name
            backup_path.mkdir(exist_ok=True)
            
            logger.info(f"Iniciando backup: {backup_name}")
            
            # Backup de base de datos
            db_backup = await self._backup_database(backup_path)
            
            # Backup de archivos compartidos
            files_backup = await self._backup_shared_files(backup_path)
            
            # Backup de configuración
            config_backup = await self._backup_configuration(backup_path)
            
            # Crear archivo de metadatos
            metadata = {
                "timestamp": timestamp,
                "backup_name": backup_name,
                "database": db_backup,
                "files": files_backup,
                "configuration": config_backup,
                "total_size": self._calculate_backup_size(backup_path)
            }
            
            metadata_file = backup_path / "backup_metadata.json"
            with open(metadata_file, 'w') as f:
                import json
                json.dump(metadata, f, indent=2)
            
            # Comprimir backup
            compressed_backup = await self._compress_backup(backup_path)
            
            # Limpiar backups antiguos
            await self._cleanup_old_backups()
            
            logger.info(f"Backup completado: {compressed_backup}")
            return metadata
            
        except Exception as e:
            logger.error(f"Error creando backup: {e}")
            raise e
    
    async def _backup_database(self, backup_path: Path) -> Dict[str, Any]:
        """Crea backup de la base de datos"""
        try:
            db_path = settings.DATABASE_URL.replace("sqlite:///", "")
            backup_db_path = backup_path / "central_server.db"
            
            # Copiar base de datos
            shutil.copy2(db_path, backup_db_path)
            
            # Obtener información de la base de datos
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Obtener estadísticas
            cursor.execute("SELECT COUNT(*) FROM peers")
            peer_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM files")
            file_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM transfer_logs")
            transfer_count = cursor.fetchone()[0]
            
            conn.close()
            
            return {
                "file": str(backup_db_path),
                "size": backup_db_path.stat().st_size,
                "peer_count": peer_count,
                "file_count": file_count,
                "transfer_count": transfer_count
            }
            
        except Exception as e:
            logger.error(f"Error en backup de base de datos: {e}")
            return {"error": str(e)}
    
    async def _backup_shared_files(self, backup_path: Path) -> Dict[str, Any]:
        """Crea backup de archivos compartidos"""
        try:
            shared_files_dir = Path("data/shared-files")
            backup_files_dir = backup_path / "shared-files"
            
            if not shared_files_dir.exists():
                return {"error": "Directorio de archivos compartidos no encontrado"}
            
            # Copiar archivos compartidos
            shutil.copytree(shared_files_dir, backup_files_dir)
            
            # Obtener estadísticas
            total_files = 0
            total_size = 0
            
            for root, dirs, files in os.walk(backup_files_dir):
                for file in files:
                    file_path = Path(root) / file
                    total_files += 1
                    total_size += file_path.stat().st_size
            
            return {
                "directory": str(backup_files_dir),
                "file_count": total_files,
                "total_size": total_size
            }
            
        except Exception as e:
            logger.error(f"Error en backup de archivos compartidos: {e}")
            return {"error": str(e)}
    
    async def _backup_configuration(self, backup_path: Path) -> Dict[str, Any]:
        """Crea backup de configuración"""
        try:
            config_backup_dir = backup_path / "config"
            config_backup_dir.mkdir(exist_ok=True)
            
            # Copiar archivos de configuración
            config_files = [
                "config/peer1.json",
                "config/peer2.json", 
                "config/peer3.json",
                "docker-compose.yml",
                "requirements.txt"
            ]
            
            copied_files = []
            for config_file in config_files:
                if os.path.exists(config_file):
                    dest_file = config_backup_dir / os.path.basename(config_file)
                    shutil.copy2(config_file, dest_file)
                    copied_files.append(str(dest_file))
            
            return {
                "directory": str(config_backup_dir),
                "files": copied_files
            }
            
        except Exception as e:
            logger.error(f"Error en backup de configuración: {e}")
            return {"error": str(e)}
    
    async def _compress_backup(self, backup_path: Path) -> str:
        """Comprime el directorio de backup"""
        try:
            compressed_file = f"{backup_path}.tar.gz"
            
            # Crear archivo comprimido
            import tarfile
            with tarfile.open(compressed_file, "w:gz") as tar:
                tar.add(backup_path, arcname=backup_path.name)
            
            # Eliminar directorio original
            shutil.rmtree(backup_path)
            
            return compressed_file
            
        except Exception as e:
            logger.error(f"Error comprimiendo backup: {e}")
            return str(backup_path)
    
    def _calculate_backup_size(self, backup_path: Path) -> int:
        """Calcula el tamaño total del backup"""
        total_size = 0
        for root, dirs, files in os.walk(backup_path):
            for file in files:
                file_path = Path(root) / file
                total_size += file_path.stat().st_size
        return total_size
    
    async def _cleanup_old_backups(self):
        """Elimina backups antiguos según la política de retención"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=settings.BACKUP_RETENTION_DAYS)
            
            for backup_file in self.backup_dir.glob("redp2p_backup_*.tar.gz"):
                file_time = datetime.fromtimestamp(backup_file.stat().st_mtime)
                if file_time < cutoff_date:
                    backup_file.unlink()
                    logger.info(f"Backup antiguo eliminado: {backup_file.name}")
            
        except Exception as e:
            logger.error(f"Error limpiando backups antiguos: {e}")
    
    async def list_backups(self) -> List[Dict[str, Any]]:
        """Lista todos los backups disponibles"""
        try:
            backups = []
            
            for backup_file in self.backup_dir.glob("redp2p_backup_*.tar.gz"):
                file_stat = backup_file.stat()
                backups.append({
                    "name": backup_file.name,
                    "path": str(backup_file),
                    "size": file_stat.st_size,
                    "created": datetime.fromtimestamp(file_stat.st_mtime).isoformat(),
                    "size_mb": round(file_stat.st_size / 1024 / 1024, 2)
                })
            
            # Ordenar por fecha de creación (más reciente primero)
            backups.sort(key=lambda x: x["created"], reverse=True)
            
            return backups
            
        except Exception as e:
            logger.error(f"Error listando backups: {e}")
            return []
    
    async def restore_backup(self, backup_name: str, restore_path: str = None) -> bool:
        """Restaura un backup específico"""
        try:
            backup_file = self.backup_dir / backup_name
            
            if not backup_file.exists():
                logger.error(f"Backup no encontrado: {backup_name}")
                return False
            
            # Crear directorio temporal para extraer
            temp_dir = Path(f"/tmp/restore_{backup_name.replace('.tar.gz', '')}")
            temp_dir.mkdir(exist_ok=True)
            
            # Extraer backup
            import tarfile
            with tarfile.open(backup_file, "r:gz") as tar:
                tar.extractall(temp_dir)
            
            # Restaurar archivos
            extracted_backup = temp_dir / backup_name.replace('.tar.gz', '')
            
            if restore_path:
                restore_path = Path(restore_path)
            else:
                restore_path = Path(".")
            
            # Restaurar base de datos
            db_backup = extracted_backup / "central_server.db"
            if db_backup.exists():
                shutil.copy2(db_backup, restore_path / "data/central_server.db")
            
            # Restaurar archivos compartidos
            shared_files_backup = extracted_backup / "shared-files"
            if shared_files_backup.exists():
                shutil.copytree(shared_files_backup, restore_path / "data/shared-files", dirs_exist_ok=True)
            
            # Limpiar directorio temporal
            shutil.rmtree(temp_dir)
            
            logger.info(f"Backup restaurado exitosamente: {backup_name}")
            return True
            
        except Exception as e:
            logger.error(f"Error restaurando backup: {e}")
            return False

# Instancia global del gestor de backup
backup_manager = BackupManager()
