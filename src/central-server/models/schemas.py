from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class PeerInfo(BaseModel):
    peer_id: str
    host: str
    port: int
    grpc_port: int
    is_online: bool
    last_seen: datetime
    files_count: int = 0

class FileInfo(BaseModel):
    id: int
    filename: str
    file_hash: str
    size: int
    peer_id: str
    is_available: bool
    last_modified: datetime
    peer_info: Optional[PeerInfo] = None

class SearchRequest(BaseModel):
    filename: Optional[str] = None
    file_hash: Optional[str] = None
    min_size: Optional[int] = None
    max_size: Optional[int] = None
    peer_id: Optional[str] = None

class SearchResponse(BaseModel):
    files: List[FileInfo]
    total_found: int
    search_time: float
    searched_peers: List[str]

class DownloadRequest(BaseModel):
    file_hash: str
    requesting_peer_id: str

class DownloadResponse(BaseModel):
    success: bool
    file_info: Optional[FileInfo] = None
    download_url: Optional[str] = None
    error_message: Optional[str] = None

class UploadRequest(BaseModel):
    filename: str
    file_size: int
    file_hash: str
    uploading_peer_id: str

class UploadResponse(BaseModel):
    success: bool
    file_id: Optional[str] = None
    error_message: Optional[str] = None

class PeerRegistration(BaseModel):
    peer_id: str
    host: str
    port: int
    grpc_port: int

class PeerStatus(BaseModel):
    peer_id: str
    is_online: bool
    last_seen: datetime
    files_count: int
    total_size: int

class TransferRequest(BaseModel):
    file_hash: str
    source_peer_id: str
    target_peer_id: str
    transfer_type: str  # 'download', 'upload'

class TransferStatus(BaseModel):
    transfer_id: int
    file_hash: str
    source_peer_id: str
    target_peer_id: str
    status: str
    progress: float  # 0.0 a 1.0
    bytes_transferred: int
    total_bytes: int
    started_at: datetime
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None

class SystemStats(BaseModel):
    total_peers: int
    online_peers: int
    total_files: int
    total_size: int
    active_transfers: int
    completed_transfers_today: int
