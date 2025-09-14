"""
Configuración centralizada de mapeo de hosts para el sistema P2P
"""

import os
from typing import Dict

# Mapeo de hosts para diferentes entornos
HOST_MAPPINGS = {
    "development": {
        "localhost:8001": "p2p-peer-1:8001",
        "localhost:8002": "p2p-peer-2:8002", 
        "localhost:8003": "p2p-peer-3:8003"
    },
    "production": {
        "localhost:8001": "p2p-peer-1:8001",
        "localhost:8002": "p2p-peer-2:8002", 
        "localhost:8003": "p2p-peer-3:8003"
    },
    "docker": {
        "localhost:8001": "p2p-peer-1:8001",
        "localhost:8002": "p2p-peer-2:8002", 
        "localhost:8003": "p2p-peer-3:8003"
    }
}

def get_host_mapping() -> Dict[str, str]:
    """Obtiene el mapeo de hosts según el entorno actual"""
    env = os.getenv("ENVIRONMENT", "development")
    return HOST_MAPPINGS.get(env, HOST_MAPPINGS["development"])

def map_host(host: str, port: int) -> str:
    """Mapea un host:puerto a su equivalente en Docker"""
    host_port = f"{host}:{port}"
    mapping = get_host_mapping()
    return mapping.get(host_port, host_port)
