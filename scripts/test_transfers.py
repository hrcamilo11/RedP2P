#!/usr/bin/env python3
"""
Script de prueba para el sistema de transferencias RedP2P
"""

import requests
import json
import time
import sys

def test_transfer_system():
    """Prueba el sistema de transferencias completo"""
    
    print("🚀 Iniciando pruebas del sistema de transferencias...")
    
    # 1. Verificar que el servidor central esté funcionando
    print("\n1️⃣ Verificando servidor central...")
    try:
        response = requests.get("http://localhost:8000/api/health", timeout=5)
        if response.status_code == 200:
            print("✅ Servidor central funcionando")
        else:
            print(f"❌ Servidor central no responde: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error conectando al servidor central: {e}")
        return False
    
    # 2. Registrar peers
    print("\n2️⃣ Registrando peers...")
    peers = [
        {"peer_id": "peer1", "host": "localhost", "port": 8001, "grpc_port": 9001},
        {"peer_id": "peer2", "host": "localhost", "port": 8002, "grpc_port": 9002},
        {"peer_id": "peer3", "host": "localhost", "port": 8003, "grpc_port": 9003}
    ]
    
    for peer in peers:
        try:
            response = requests.post(
                "http://localhost:8000/api/peers/register",
                json=peer,
                timeout=5
            )
            if response.status_code == 200:
                print(f"✅ Peer {peer['peer_id']} registrado")
            else:
                print(f"❌ Error registrando peer {peer['peer_id']}: {response.status_code}")
        except Exception as e:
            print(f"❌ Error registrando peer {peer['peer_id']}: {e}")
    
    # 3. Indexar archivos
    print("\n3️⃣ Indexando archivos...")
    try:
        response = requests.post("http://localhost:8000/api/files/index-all", timeout=10)
        if response.status_code == 200:
            print("✅ Archivos indexados")
        else:
            print(f"❌ Error indexando archivos: {response.status_code}")
    except Exception as e:
        print(f"❌ Error indexando archivos: {e}")
    
    # 4. Verificar estadísticas
    print("\n4️⃣ Verificando estadísticas...")
    try:
        response = requests.get("http://localhost:8000/api/stats", timeout=5)
        if response.status_code == 200:
            stats = response.json()
            print(f"✅ Estadísticas: {stats['total_peers']} peers, {stats['total_files']} archivos")
        else:
            print(f"❌ Error obteniendo estadísticas: {response.status_code}")
    except Exception as e:
        print(f"❌ Error obteniendo estadísticas: {e}")
    
    # 5. Buscar archivos
    print("\n5️⃣ Buscando archivos...")
    try:
        search_data = {"filename": "test"}
        response = requests.post(
            "http://localhost:8000/api/files/search",
            json=search_data,
            timeout=5
        )
        if response.status_code == 200:
            results = response.json()
            print(f"✅ Encontrados {len(results)} archivos")
            
            if results:
                # 6. Probar descarga
                print("\n6️⃣ Probando descarga...")
                file_hash = results[0]['file_hash']
                download_data = {
                    "file_hash": file_hash,
                    "requesting_peer_id": "test-peer"
                }
                
                response = requests.post(
                    "http://localhost:8000/api/transfers/download",
                    json=download_data,
                    timeout=5
                )
                if response.status_code == 200:
                    download_info = response.json()
                    print(f"✅ Descarga iniciada: {download_info['download_url']}")
                    
                    # 7. Verificar estado de transferencia
                    print("\n7️⃣ Verificando estado de transferencia...")
                    time.sleep(2)
                    
                    response = requests.get("http://localhost:8000/api/transfers/active", timeout=5)
                    if response.status_code == 200:
                        transfers = response.json()
                        print(f"✅ Transferencias activas: {len(transfers)}")
                        for transfer in transfers:
                            print(f"   - {transfer['file_hash'][:8]}... - {transfer['status']} - {transfer['progress']*100:.1f}%")
                    else:
                        print(f"❌ Error obteniendo transferencias activas: {response.status_code}")
                else:
                    print(f"❌ Error iniciando descarga: {response.status_code}")
                    print(f"   Respuesta: {response.text}")
            else:
                print("⚠️ No hay archivos para probar descarga")
        else:
            print(f"❌ Error buscando archivos: {response.status_code}")
    except Exception as e:
        print(f"❌ Error en búsqueda/descarga: {e}")
    
    print("\n🎉 Pruebas completadas!")

if __name__ == "__main__":
    test_transfer_system()
