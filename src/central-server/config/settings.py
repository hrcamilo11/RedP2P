"""
Configuración centralizada del servidor central
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List, Optional, Dict, Any
from enum import Enum
import os

class LogLevel(str, Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"

class Environment(str, Enum):
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', extra='ignore')

    # Environment
    ENVIRONMENT: Environment = Environment.DEVELOPMENT
    DEBUG: bool = False
    
    # Server Configuration
    DATABASE_URL: str = "sqlite:///./data/central_server.db"
    CENTRAL_SERVER_HOST: str = "0.0.0.0"
    CENTRAL_SERVER_PORT: int = 8000
    
    # Logging
    LOG_LEVEL: LogLevel = LogLevel.INFO
    LOG_FILE: Optional[str] = None
    LOG_FORMAT: str = "json"  # json or text
    LOG_ROTATION: bool = True
    LOG_MAX_SIZE_MB: int = 100
    LOG_BACKUP_COUNT: int = 5

    # CORS
    CORS_ALLOW_ORIGINS: List[str] = ["http://localhost:8000", "http://localhost:3000", "http://127.0.0.1:8000", "http://127.0.0.1:3000"]
    CORS_ALLOW_METHODS: List[str] = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
    CORS_ALLOW_HEADERS: List[str] = ["*"]
    CORS_ALLOW_CREDENTIALS: bool = True

    # File Validation
    FILE_ALLOWED_EXTENSIONS: List[str] = ['.txt', '.pdf', '.jpg', '.jpeg', '.png', '.gif', '.zip', '.rar', '.mp3', '.mp4', '.doc', '.docx', '.xls', '.xlsx']
    FILE_MAX_SIZE_MB: int = 100
    TEMP_UPLOAD_DIR: str = "/tmp/redp2p_uploads"
    FILE_SCAN_ENABLED: bool = True
    FILE_QUARANTINE_DIR: str = "/tmp/redp2p_quarantine"

    # Peer Discovery
    PEER_DISCOVERY_TIMEOUT_SECONDS: int = 30
    PEER_HEALTH_CHECK_INTERVAL: int = 60
    PEER_MAX_RETRIES: int = 5
    PEER_RETRY_INTERVAL: int = 30

    # Transfer Manager
    TRANSFER_MAX_RETRIES: int = 3
    TRANSFER_TIMEOUT_SECONDS: int = 60
    TRANSFER_CHUNK_SIZE: int = 8192
    TRANSFER_MAX_CONCURRENT: int = 10

    # Rate Limiting
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_MAX_REQUESTS: int = 100
    RATE_LIMIT_WINDOW_SECONDS: int = 60
    RATE_LIMIT_BURST: int = 20

    # Cache
    REDIS_ENABLED: bool = True
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: Optional[str] = None
    CACHE_TTL_DEFAULT: int = 300
    CACHE_TTL_PEER_INFO: int = 600
    CACHE_TTL_FILE_SEARCH: int = 60

    # Monitoring
    MONITORING_ENABLED: bool = True
    METRICS_RETENTION_DAYS: int = 7
    HEALTH_CHECK_INTERVAL: int = 30
    ALERT_CPU_THRESHOLD: float = 80.0
    ALERT_MEMORY_THRESHOLD: float = 85.0
    ALERT_DISK_THRESHOLD: float = 90.0

    # Security
    SECRET_KEY: str = "your-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_HOURS: int = 24
    PASSWORD_MIN_LENGTH: int = 8
    MAX_LOGIN_ATTEMPTS: int = 5
    LOCKOUT_DURATION_MINUTES: int = 15

    # Performance
    WORKER_PROCESSES: int = 1
    MAX_CONNECTIONS: int = 1000
    KEEPALIVE_TIMEOUT: int = 5
    GRACEFUL_TIMEOUT: int = 30

    # Compression
    COMPRESSION_ENABLED: bool = True
    COMPRESSION_MIN_SIZE_MB: int = 1
    COMPRESSION_LEVEL: int = 6
    COMPRESSION_ALGORITHM: str = "gzip"

    # Backup
    BACKUP_ENABLED: bool = True
    BACKUP_INTERVAL_HOURS: int = 24
    BACKUP_RETENTION_DAYS: int = 30
    BACKUP_DIR: str = "./backups"

    def get_database_url(self) -> str:
        """Obtiene la URL de base de datos con configuración de entorno"""
        if self.ENVIRONMENT == Environment.PRODUCTION:
            return self.DATABASE_URL.replace("sqlite://", "postgresql://")
        return self.DATABASE_URL

    def is_production(self) -> bool:
        """Verifica si está en modo producción"""
        return self.ENVIRONMENT == Environment.PRODUCTION

    def is_development(self) -> bool:
        """Verifica si está en modo desarrollo"""
        return self.ENVIRONMENT == Environment.DEVELOPMENT

    def get_cors_origins(self) -> List[str]:
        """Obtiene orígenes CORS según el entorno"""
        if self.is_production():
            return ["https://yourdomain.com"]
        return self.CORS_ALLOW_ORIGINS

    def get_log_config(self) -> Dict[str, Any]:
        """Obtiene configuración de logging"""
        return {
            "level": self.LOG_LEVEL.value,
            "format": self.LOG_FORMAT,
            "file": self.LOG_FILE,
            "rotation": self.LOG_ROTATION,
            "max_size_mb": self.LOG_MAX_SIZE_MB,
            "backup_count": self.LOG_BACKUP_COUNT
        }

    def get_redis_config(self) -> Dict[str, Any]:
        """Obtiene configuración de Redis"""
        return {
            "enabled": self.REDIS_ENABLED,
            "host": self.REDIS_HOST,
            "port": self.REDIS_PORT,
            "db": self.REDIS_DB,
            "password": self.REDIS_PASSWORD
        }

    def get_rate_limit_config(self) -> Dict[str, Any]:
        """Obtiene configuración de rate limiting"""
        return {
            "enabled": self.RATE_LIMIT_ENABLED,
            "max_requests": self.RATE_LIMIT_MAX_REQUESTS,
            "window_seconds": self.RATE_LIMIT_WINDOW_SECONDS,
            "burst": self.RATE_LIMIT_BURST
        }

    def get_monitoring_config(self) -> Dict[str, Any]:
        """Obtiene configuración de monitoreo"""
        return {
            "enabled": self.MONITORING_ENABLED,
            "retention_days": self.METRICS_RETENTION_DAYS,
            "health_check_interval": self.HEALTH_CHECK_INTERVAL,
            "alert_thresholds": {
                "cpu": self.ALERT_CPU_THRESHOLD,
                "memory": self.ALERT_MEMORY_THRESHOLD,
                "disk": self.ALERT_DISK_THRESHOLD
            }
        }

settings = Settings()