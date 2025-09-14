#!/usr/bin/env python3
"""
Script para probar la conectividad entre el servidor central y los peers
"""

import requests
import asyncio
import aiohttp

async def test_peer_connectivity():
    """Prueba la conectividad entre servidor central y peers"""
    
    print("🔍 Probando conectividad entre servidor central y peers...")
    
    # URLs de los peers usando nombres de contenedor
    peer_urls = {
        "peer1": "http://p2p-peer-1:8001/api/health",
        "peer2": "http://p2p-peer-2:8002/api/health", 
        "peer3": "http://p2p-peer-3:8003/api/health"
    }
    
    # URLs usando localhost
    localhost_urls = {
        "peer1": "http://localhost:8001/api/health",
        "peer2": "http://localhost:8002/api/health",
        "peer3": "http://localhost:8003/api/health"
    }
    
    print("\n1️⃣ Probando conectividad desde localhost...")
    for peer_id, url in localhost_urls.items():
        try:
            response = requests.get(url, timeout=5)
            print(f"   ✅ {peer_id}: {response.status_code} - {response.json()}")
        except Exception as e:
            print(f"   ❌ {peer_id}: Error - {e}")
    
    print("\n2️⃣ Probando conectividad desde servidor central (simulado)...")
    async with aiohttp.ClientSession() as session:
        for peer_id, url in peer_urls.items():
            try:
                async with session.get(url, timeout=5) as response:
                    data = await response.json()
                    print(f"   ✅ {peer_id}: {response.status} - {data}")
            except Exception as e:
                print(f"   ❌ {peer_id}: Error - {e}")
    
    print("\n3️⃣ Probando indexación de archivos...")
    try:
        # Probar indexación de un peer específico
        response = requests.post("http://localhost:8000/api/files/index/peer1", timeout=10)
        if response.status_code == 200:
            print("   ✅ Indexación de peer1 exitosa")
        else:
            print(f"   ❌ Error indexando peer1: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"   ❌ Error en indexación: {e}")
    
    print("\n4️⃣ Verificando estado de peers después de indexación...")
    try:
        response = requests.get("http://localhost:8000/api/peers")
        if response.status_code == 200:
            peers = response.json()
            print(f"   📊 Estado de {len(peers)} peers:")
            for peer in peers:
                status = "🟢 Online" if peer['is_online'] else "🔴 Offline"
                print(f"      - {peer['peer_id']}: {status} (archivos: {peer['files_count']})")
        else:
            print(f"   ❌ Error obteniendo peers: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_peer_connectivity())
