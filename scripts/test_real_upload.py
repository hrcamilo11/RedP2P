#!/usr/bin/env python3
"""
Script para probar subidas reales de archivos
"""

import requests
import os
import tempfile

def test_real_upload():
    """Prueba la subida real de archivos"""
    
    print("🚀 Probando subida real de archivos...")
    
    # 1. Crear un archivo de prueba
    print("\n1️⃣ Creando archivo de prueba...")
    test_content = "Este es un archivo de prueba para RedP2P\nContenido de prueba\nLínea 3"
    
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
        f.write(test_content)
        test_file_path = f.name
    
    print(f"✅ Archivo creado: {test_file_path}")
    
    # 2. Verificar que el servidor esté funcionando
    print("\n2️⃣ Verificando servidor...")
    try:
        response = requests.get("http://localhost:8000/api/health", timeout=5)
        if response.status_code == 200:
            print("✅ Servidor funcionando")
        else:
            print(f"❌ Servidor no responde: {response.status_code}")
            return
    except Exception as e:
        print(f"❌ Error conectando al servidor: {e}")
        return
    
    # 3. Verificar peers disponibles
    print("\n3️⃣ Verificando peers...")
    try:
        response = requests.get("http://localhost:8000/api/peers")
        if response.status_code == 200:
            peers = response.json()
            print(f"✅ {len(peers)} peers disponibles:")
            for peer in peers:
                print(f"   - {peer['peer_id']}: {'Online' if peer['is_online'] else 'Offline'}")
        else:
            print(f"❌ Error obteniendo peers: {response.status_code}")
            return
    except Exception as e:
        print(f"❌ Error: {e}")
        return
    
    # 4. Probar subida de archivo
    print("\n4️⃣ Probando subida de archivo...")
    try:
        with open(test_file_path, 'rb') as f:
            files = {'file': ('test_upload.txt', f, 'text/plain')}
            data = {'target_peer': 'peer1'}
            
            response = requests.post(
                "http://localhost:8000/api/transfers/upload-file",
                files=files,
                data=data,
                timeout=30
            )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Archivo subido exitosamente: {result}")
        else:
            print(f"❌ Error subiendo archivo: {response.status_code}")
            print(f"   Respuesta: {response.text}")
            
    except Exception as e:
        print(f"❌ Error en subida: {e}")
    
    # 5. Verificar que el archivo aparezca en la búsqueda
    print("\n5️⃣ Verificando que el archivo aparezca en búsqueda...")
    try:
        search_data = {"filename": "test_upload"}
        response = requests.post(
            "http://localhost:8000/api/files/search",
            json=search_data,
            timeout=5
        )
        
        if response.status_code == 200:
            results = response.json()
            print(f"✅ Encontrados {len(results)} archivos con 'test_upload'")
            for file in results:
                print(f"   - {file['filename']} (hash: {file['file_hash'][:8]}...)")
        else:
            print(f"❌ Error buscando archivos: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error en búsqueda: {e}")
    
    # 6. Limpiar archivo temporal
    try:
        os.unlink(test_file_path)
        print(f"\n🧹 Archivo temporal eliminado: {test_file_path}")
    except:
        pass
    
    print("\n🎉 Prueba de subida real completada!")

if __name__ == "__main__":
    test_real_upload()
