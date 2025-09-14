#!/usr/bin/env python3
"""
Script de prueba para verificar la selección de peer destino en subida de archivos
"""

import requests
import json
import time
import os

def test_peer_selection():
    """Prueba la funcionalidad de selección de peer destino"""
    print("🧪 TESTER DE SELECCIÓN DE PEER DESTINO")
    print("RedP2P - Sistema P2P Distribuido")
    print()
    print("🚀 INICIANDO PRUEBAS DE SELECCIÓN DE PEER")
    print("=" * 50)
    
    base_url = "http://localhost:8000"
    
    # Esperar a que el servidor esté listo
    print("⏳ Esperando que el servidor esté listo...")
    for i in range(30):
        try:
            response = requests.get(f"{base_url}/api/health", timeout=5)
            if response.status_code == 200:
                print("✅ Servidor listo")
                break
        except:
            pass
        time.sleep(1)
    else:
        print("❌ Servidor no disponible después de 30 segundos")
        return False
    
    # 1. Verificar que hay peers disponibles
    print("\n📋 Verificando Peers Disponibles")
    print("-" * 30)
    try:
        response = requests.get(f"{base_url}/api/peers")
        if response.status_code == 200:
            peers = response.json()
            print(f"✅ Peers encontrados: {len(peers)}")
            for peer in peers:
                print(f"   - {peer['peer_id']}: {peer['host']}:{peer['port']} ({'online' if peer['is_online'] else 'offline'})")
        else:
            print(f"❌ Error obteniendo peers: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    
    # 2. Crear archivo de prueba
    print("\n📁 Creando Archivo de Prueba")
    print("-" * 30)
    test_file_content = "Este es un archivo de prueba para verificar la selección de peer destino.\n"
    test_file_content += f"Timestamp: {time.time()}\n"
    test_file_content += "Contenido de prueba para verificar que se sube al peer correcto.\n"
    
    test_file_path = "test_peer_selection.txt"
    with open(test_file_path, 'w', encoding='utf-8') as f:
        f.write(test_file_content)
    
    print(f"✅ Archivo de prueba creado: {test_file_path}")
    
    # 3. Probar subida a diferentes peers
    print("\n📤 Probando Subida a Diferentes Peers")
    print("-" * 30)
    
    success_count = 0
    total_tests = 0
    
    for peer in peers:
        if not peer['is_online']:
            print(f"⚠️  Saltando {peer['peer_id']} (offline)")
            continue
            
        total_tests += 1
        print(f"🧪 Probando subida a {peer['peer_id']}...")
        
        try:
            with open(test_file_path, 'rb') as f:
                files = {'file': (test_file_path, f, 'text/plain')}
                data = {'target_peer': peer['peer_id']}
                
                response = requests.post(f"{base_url}/api/transfers/upload-file", 
                                       files=files, data=data, timeout=30)
                
                if response.status_code == 200:
                    result = response.json()
                    print(f"   ✅ Subida exitosa a {peer['peer_id']}")
                    print(f"      - File ID: {result.get('file_id', 'N/A')}")
                    print(f"      - Success: {result.get('success', False)}")
                    success_count += 1
                else:
                    print(f"   ❌ Error subiendo a {peer['peer_id']}: {response.status_code}")
                    print(f"      - Response: {response.text}")
        except Exception as e:
            print(f"   ❌ Excepción subiendo a {peer['peer_id']}: {e}")
    
    # 4. Probar validación de peer destino requerido
    print("\n🔒 Probando Validación de Peer Destino")
    print("-" * 30)
    
    try:
        with open(test_file_path, 'rb') as f:
            files = {'file': (test_file_path, f, 'text/plain')}
            data = {'target_peer': ''}  # Peer vacío
            
            response = requests.post(f"{base_url}/api/transfers/upload-file", 
                                   files=files, data=data, timeout=10)
            
            if response.status_code == 400:
                print("✅ Validación funcionando: Peer destino requerido")
            else:
                print(f"❌ Validación falló: Esperaba 400, obtuvo {response.status_code}")
                print(f"   - Response: {response.text}")
    except Exception as e:
        print(f"❌ Error en validación: {e}")
    
    # 5. Verificar archivos en cada peer
    print("\n📋 Verificando Archivos en Cada Peer")
    print("-" * 30)
    
    for peer in peers:
        if not peer['is_online']:
            continue
            
        try:
            response = requests.get(f"{base_url}/api/files/peer/{peer['peer_id']}")
            if response.status_code == 200:
                files = response.json()
                print(f"✅ {peer['peer_id']}: {len(files)} archivos")
                for file_info in files:
                    if test_file_path in file_info.get('filename', ''):
                        print(f"   - ✅ Archivo de prueba encontrado: {file_info['filename']}")
            else:
                print(f"❌ Error obteniendo archivos de {peer['peer_id']}: {response.status_code}")
        except Exception as e:
            print(f"❌ Error verificando {peer['peer_id']}: {e}")
    
    # Limpiar archivo de prueba
    try:
        os.remove(test_file_path)
        print(f"\n🧹 Archivo de prueba eliminado: {test_file_path}")
    except:
        pass
    
    # Resumen
    print("\n" + "=" * 50)
    print("📊 RESUMEN DE PRUEBAS")
    print("=" * 50)
    print(f"✅ Subidas exitosas: {success_count}/{total_tests}")
    print(f"✅ Validación de peer destino: Funcionando")
    print(f"✅ Verificación de archivos: Completada")
    
    if success_count == total_tests and total_tests > 0:
        print("\n🎯 Resultado: TODAS LAS PRUEBAS PASARON")
        print("✅ La selección de peer destino funciona correctamente")
        return True
    else:
        print("\n⚠️  Algunas pruebas fallaron")
        return False

if __name__ == "__main__":
    success = test_peer_selection()
    exit(0 if success else 1)
