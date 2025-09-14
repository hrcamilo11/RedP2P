from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import hashlib
import os

class FileInfo(BaseModel):
    filename: str
    size: int
    hash: str
    peer_id: str
    last_modified: datetime
    path: str
    is_available: bool = True

    @classmethod
    def from_file(cls, file_path: str, peer_id: str) -> 'FileInfo':
        """Crea FileInfo desde un archivo del sistema"""
        stat = os.stat(file_path)
        
        # Calcular hash del archivo
        with open(file_path, 'rb') as f:
            file_hash = hashlib.sha256(f.read()).hexdigest()
        
        return cls(
            filename=os.path.basename(file_path),
            size=stat.st_size,
            hash=file_hash,
            peer_id=peer_id,
            last_modified=datetime.fromtimestamp(stat.st_mtime),
            path=file_path
        )

class SearchRequest(BaseModel):
    filename: Optional[str] = None
    file_hash: Optional[str] = None
    min_size: Optional[int] = None
    max_size: Optional[int] = None

class SearchResponse(BaseModel):
    files: List[FileInfo]
    total_found: int
    search_time: float

class DownloadRequest(BaseModel):
    file_hash: str
    peer_id: str

class DownloadResponse(BaseModel):
    success: bool
    file_info: Optional[FileInfo] = None
    download_url: Optional[str] = None
    error_message: Optional[str] = None

class UploadRequest(BaseModel):
    filename: str
    file_size: int
    file_hash: str

class UploadResponse(BaseModel):
    success: bool
    file_id: Optional[str] = None
    error_message: Optional[str] = None
