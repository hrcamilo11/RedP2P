#!/usr/bin/env python3
"""
Script para probar el estado de los peers
"""

import requests
import json

def test_peer_status():
    """Prueba el estado de los peers"""
    
    print("🔍 Probando estado de los peers...")
    
    # 1. Verificar peers registrados
    print("\n1️⃣ Peers registrados:")
    try:
        response = requests.get("http://localhost:8000/api/peers")
        if response.status_code == 200:
            peers = response.json()
            for peer in peers:
                print(f"   - {peer['peer_id']}: {peer['is_online']} (última vez: {peer['last_seen']})")
        else:
            print(f"❌ Error obteniendo peers: {response.status_code}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # 2. Verificar estado individual de peer1
    print("\n2️⃣ Estado de peer1:")
    try:
        response = requests.get("http://localhost:8000/api/peers/peer1/status")
        if response.status_code == 200:
            status = response.json()
            print(f"   - Online: {status['is_online']}")
            print(f"   - Archivos: {status['files_count']}")
            print(f"   - Última vez: {status['last_seen']}")
        else:
            print(f"❌ Error obteniendo estado: {response.status_code}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # 3. Verificar conectividad directa a peer1
    print("\n3️⃣ Conectividad directa a peer1:")
    try:
        response = requests.get("http://localhost:8001/api/health", timeout=5)
        print(f"   - Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   - Respuesta: {data}")
        else:
            print(f"   - Error: {response.text}")
    except Exception as e:
        print(f"❌ Error conectando directamente: {e}")
    
    # 4. Verificar conectividad desde el servidor central
    print("\n4️⃣ Conectividad desde servidor central:")
    try:
        # Simular la misma URL que usaría el servidor central
        response = requests.get("http://p2p-peer-1:8001/api/health", timeout=5)
        print(f"   - Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   - Respuesta: {data}")
        else:
            print(f"   - Error: {response.text}")
    except Exception as e:
        print(f"❌ Error conectando desde servidor central: {e}")

if __name__ == "__main__":
    test_peer_status()
