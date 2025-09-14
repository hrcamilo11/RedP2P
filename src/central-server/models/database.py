from sqlalchemy import create_engine, Column, String, Integer, DateTime, Boolean, Text, ForeignKey, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import os

# Configuración de la base de datos
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./central_server.db")
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class Peer(Base):
    """Modelo de Peer en la base de datos"""
    __tablename__ = "peers"
    
    id = Column(Integer, primary_key=True, index=True)
    peer_id = Column(String, unique=True, index=True, nullable=False)
    host = Column(String, nullable=False)
    port = Column(Integer, nullable=False)
    grpc_port = Column(Integer, nullable=False)
    is_online = Column(Boolean, default=True)
    last_seen = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relación con archivos
    files = relationship("File", back_populates="peer")

class File(Base):
    """Modelo de Archivo en la base de datos"""
    __tablename__ = "files"
    
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, nullable=False)
    file_hash = Column(String, index=True, nullable=False)
    size = Column(Integer, nullable=False)
    peer_id = Column(String, ForeignKey("peers.peer_id"), nullable=False)
    is_available = Column(Boolean, default=True)
    source = Column(String, default='indexed')  # 'indexed' para archivos indexados, 'upload' para archivos subidos
    last_modified = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relación con peer
    peer = relationship("Peer", back_populates="files")
    
    # Constraint único para la combinación de file_hash y peer_id
    __table_args__ = (
        UniqueConstraint('file_hash', 'peer_id', name='unique_file_per_peer'),
    )

class TransferLog(Base):
    """Modelo de Log de Transferencias"""
    __tablename__ = "transfer_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    file_hash = Column(String, nullable=False)
    source_peer_id = Column(String, nullable=False)
    target_peer_id = Column(String, nullable=False)
    transfer_type = Column(String, nullable=False)  # 'download', 'upload'
    status = Column(String, nullable=False)  # 'pending', 'completed', 'failed'
    bytes_transferred = Column(Integer, default=0)
    total_bytes = Column(Integer, nullable=False)
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    error_message = Column(Text, nullable=True)

class SearchLog(Base):
    """Modelo de Log de Búsquedas"""
    __tablename__ = "search_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    query = Column(String, nullable=False)
    peer_id = Column(String, nullable=False)
    results_count = Column(Integer, default=0)
    search_time = Column(Integer, default=0)  # en milisegundos
    created_at = Column(DateTime, default=datetime.utcnow)

def create_tables():
    """Crea todas las tablas en la base de datos"""
    Base.metadata.create_all(bind=engine)

def get_db():
    """Obtiene una sesión de base de datos"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
