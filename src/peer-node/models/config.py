from pydantic import BaseModel
from typing import Optional, Dict, Any
import json
import os

class NetworkPeer(BaseModel):
    peer_id: str
    host: str
    port: int
    grpc_port: int

class ServerConfig(BaseModel):
    host: str
    port: int
    grpc_port: int

class NetworkConfig(BaseModel):
    primary_friend: NetworkPeer
    backup_friend: NetworkPeer

class PeerConfig(BaseModel):
    peer_id: str
    server: ServerConfig
    shared_directory: str
    network: NetworkConfig
    max_concurrent_connections: int
    file_chunk_size: int
    discovery_timeout: int

    @classmethod
    def load_from_file(cls, config_file: str) -> 'PeerConfig':
        """Carga la configuración desde un archivo JSON"""
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            return cls(**config_data)
        except Exception as e:
            raise Exception(f"Error cargando configuración: {e}")

    @classmethod
    def load_from_env(cls) -> 'PeerConfig':
        """Carga la configuración desde variables de entorno"""
        config_file = os.getenv('CONFIG_FILE', '/app/config.json')
        return cls.load_from_file(config_file)
