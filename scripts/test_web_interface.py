#!/usr/bin/env python3
"""
Script de prueba para la interfaz web del servidor central RedP2P
"""

import requests
import json
import time
import sys
from datetime import datetime

class WebInterfaceTester:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.session = requests.Session()
    
    def test_health_check(self):
        """Prueba el endpoint de salud del servidor"""
        print("🔍 Probando health check...")
        try:
            response = self.session.get(f"{self.api_url}/health")
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Servidor saludable: {data['status']}")
                return True
            else:
                print(f"❌ Error en health check: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Error conectando al servidor: {e}")
            return False
    
    def test_static_files(self):
        """Prueba que los archivos estáticos se sirvan correctamente"""
        print("\n🔍 Probando archivos estáticos...")
        static_files = [
            "/",
            "/static/index.html",
            "/static/styles.css",
            "/static/app.js"
        ]
        
        for file_path in static_files:
            try:
                response = self.session.get(f"{self.base_url}{file_path}")
                if response.status_code == 200:
                    print(f"✅ {file_path} - OK")
                else:
                    print(f"❌ {file_path} - Error {response.status_code}")
            except Exception as e:
                print(f"❌ {file_path} - Error: {e}")
    
    def test_api_endpoints(self):
        """Prueba los endpoints de la API"""
        print("\n🔍 Probando endpoints de la API...")
        
        endpoints = [
            ("GET", "/stats", "Estadísticas del sistema"),
            ("GET", "/peers", "Lista de peers"),
            ("GET", "/peers/online", "Peers online"),
            ("GET", "/transfers/active", "Transferencias activas"),
            ("GET", "/transfers/history", "Historial de transferencias")
        ]
        
        for method, endpoint, description in endpoints:
            try:
                if method == "GET":
                    response = self.session.get(f"{self.api_url}{endpoint}")
                else:
                    response = self.session.post(f"{self.api_url}{endpoint}")
                
                if response.status_code == 200:
                    data = response.json()
                    print(f"✅ {description} - OK")
                    if isinstance(data, list):
                        print(f"   📊 {len(data)} elementos encontrados")
                    elif isinstance(data, dict) and 'total_peers' in data:
                        print(f"   📊 Peers: {data.get('total_peers', 0)}, Archivos: {data.get('total_files', 0)}")
                else:
                    print(f"❌ {description} - Error {response.status_code}")
            except Exception as e:
                print(f"❌ {description} - Error: {e}")
    
    def test_file_search(self):
        """Prueba la funcionalidad de búsqueda de archivos"""
        print("\n🔍 Probando búsqueda de archivos...")
        
        search_queries = [
            {"filename": "test"},
            {"min_size": 1000},
            {"max_size": 1000000}
        ]
        
        for query in search_queries:
            try:
                response = self.session.post(
                    f"{self.api_url}/files/search",
                    json=query,
                    headers={"Content-Type": "application/json"}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    print(f"✅ Búsqueda '{query}' - {data.get('total_found', 0)} archivos encontrados")
                else:
                    print(f"❌ Búsqueda '{query}' - Error {response.status_code}")
            except Exception as e:
                print(f"❌ Búsqueda '{query}' - Error: {e}")
    
    def test_peer_management(self):
        """Prueba la gestión de peers"""
        print("\n🔍 Probando gestión de peers...")
        
        # Simular registro de un peer de prueba
        test_peer = {
            "peer_id": "test-peer-web",
            "host": "localhost",
            "port": 8001,
            "grpc_port": 9001
        }
        
        try:
            # Registrar peer
            response = self.session.post(
                f"{self.api_url}/peers/register",
                json=test_peer,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                print("✅ Peer de prueba registrado")
                
                # Verificar que aparece en la lista
                response = self.session.get(f"{self.api_url}/peers")
                if response.status_code == 200:
                    peers = response.json()
                    test_peer_found = any(p['peer_id'] == 'test-peer-web' for p in peers)
                    if test_peer_found:
                        print("✅ Peer encontrado en la lista")
                    else:
                        print("❌ Peer no encontrado en la lista")
                
                # Desregistrar peer
                response = self.session.delete(f"{self.api_url}/peers/test-peer-web")
                if response.status_code == 200:
                    print("✅ Peer de prueba desregistrado")
                else:
                    print(f"❌ Error desregistrando peer: {response.status_code}")
            else:
                print(f"❌ Error registrando peer: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Error en gestión de peers: {e}")
    
    def test_transfer_simulation(self):
        """Simula una transferencia de archivo"""
        print("\n🔍 Probando simulación de transferencia...")
        
        # Crear una solicitud de descarga simulada
        download_request = {
            "file_hash": "test-hash-123",
            "requesting_peer_id": "test-peer"
        }
        
        try:
            response = self.session.post(
                f"{self.api_url}/transfers/download",
                json=download_request,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    print("✅ Transferencia simulada iniciada")
                else:
                    print(f"⚠️ Transferencia falló: {data.get('error_message', 'Error desconocido')}")
            else:
                print(f"❌ Error iniciando transferencia: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Error en simulación de transferencia: {e}")
    
    def run_all_tests(self):
        """Ejecuta todas las pruebas"""
        print("🚀 Iniciando pruebas de la interfaz web RedP2P")
        print("=" * 50)
        
        start_time = time.time()
        
        # Ejecutar pruebas
        tests = [
            self.test_health_check,
            self.test_static_files,
            self.test_api_endpoints,
            self.test_file_search,
            self.test_peer_management,
            self.test_transfer_simulation
        ]
        
        passed = 0
        total = len(tests)
        
        for test in tests:
            try:
                if test():
                    passed += 1
            except Exception as e:
                print(f"❌ Error ejecutando prueba: {e}")
        
        # Resumen
        end_time = time.time()
        duration = end_time - start_time
        
        print("\n" + "=" * 50)
        print(f"📊 Resumen de pruebas:")
        print(f"   ✅ Exitosas: {passed}/{total}")
        print(f"   ❌ Fallidas: {total - passed}/{total}")
        print(f"   ⏱️ Tiempo total: {duration:.2f} segundos")
        
        if passed == total:
            print("🎉 ¡Todas las pruebas pasaron!")
            return True
        else:
            print("⚠️ Algunas pruebas fallaron")
            return False

def main():
    """Función principal"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Prueba la interfaz web de RedP2P")
    parser.add_argument("--url", default="http://localhost:8000", 
                       help="URL base del servidor (default: http://localhost:8000)")
    parser.add_argument("--timeout", type=int, default=10,
                       help="Timeout para las peticiones (default: 10 segundos)")
    
    args = parser.parse_args()
    
    # Configurar timeout
    requests.adapters.DEFAULT_RETRIES = 1
    
    # Crear tester
    tester = WebInterfaceTester(args.url)
    tester.session.timeout = args.timeout
    
    # Ejecutar pruebas
    success = tester.run_all_tests()
    
    # Código de salida
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
