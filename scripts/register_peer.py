#!/usr/bin/env python3
import requests
import json

def register_peer():
    """Registra un peer manualmente para probar"""
    base_url = "http://localhost:8000"
    
    # Datos del peer
    peer_data = {
        "peer_id": "peer1",
        "host": "localhost",
        "port": 8001,
        "grpc_port": 9001
    }
    
    try:
        response = requests.post(f"{base_url}/api/peers/register", json=peer_data)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            print("✅ Peer registrado exitosamente")
        else:
            print("❌ Error registrando peer")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    register_peer()
