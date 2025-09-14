#!/usr/bin/env python3
"""
Script para probar el servidor central del sistema P2P
"""

import asyncio
import aiohttp
import time
import json
from typing import List, Dict

class CentralServerTester:
    """Tester para el servidor central P2P"""
    
    def __init__(self):
        self.central_url = "http://localhost:8000"
        self.peer_urls = [
            "http://localhost:8001",
            "http://localhost:8002",
            "http://localhost:8003"
        ]
        self.session = None
    
    async def initialize(self):
        """Inicializa el cliente HTTP"""
        self.session = aiohttp.ClientSession()
    
    async def close(self):
        """Cierra el cliente HTTP"""
        if self.session:
            await self.session.close()
    
    async def test_central_server_health(self):
        """Prueba la salud del servidor central"""
        print("=== Prueba: Salud del Servidor Central ===")
        
        try:
            response = await self.session.get(f"{self.central_url}/api/health", timeout=5)
            if response.status == 200:
                data = await response.json()
                print(f"✓ Servidor central está funcionando")
                print(f"  - Servicio: {data['service']}")
                print(f"  - Versión: {data['version']}")
                return True
            else:
                print(f"✗ Servidor central no responde (HTTP {response.status})")
                return False
        except Exception as e:
            print(f"✗ Error conectando con servidor central: {e}")
            return False
    
    async def test_peer_registration(self):
        """Prueba el registro de peers"""
        print("\n=== Prueba: Registro de Peers ===")
        
        try:
            response = await self.session.get(f"{self.central_url}/api/peers", timeout=10)
            if response.status == 200:
                peers = await response.json()
                print(f"Peers registrados: {len(peers)}")
                
                online_count = 0
                for peer in peers:
                    status = "en línea" if peer['is_online'] else "desconectado"
                    if peer['is_online']:
                        online_count += 1
                    print(f"  - {peer['peer_id']}: {status} ({peer['files_count']} archivos)")
                
                print(f"Peers en línea: {online_count}/{len(peers)}")
                return online_count > 0
            else:
                print(f"Error obteniendo peers: HTTP {response.status}")
                return False
        except Exception as e:
            print(f"Error obteniendo peers: {e}")
            return False
    
    async def test_central_file_search(self):
        """Prueba la búsqueda centralizada de archivos"""
        print("\n=== Prueba: Búsqueda Centralizada de Archivos ===")
        
        search_queries = ["test", "document", "image", "video", "file"]
        total_found = 0
        
        for query in search_queries:
            try:
                search_data = {"filename": query}
                response = await self.session.post(
                    f"{self.central_url}/api/files/search",
                    json=search_data,
                    timeout=15
                )
                
                if response.status == 200:
                    data = await response.json()
                    files_found = data['total_found']
                    total_found += files_found
                    print(f"  '{query}': {files_found} archivos encontrados")
                else:
                    print(f"  '{query}': Error en búsqueda (HTTP {response.status})")
            
            except Exception as e:
                print(f"  '{query}': Error en búsqueda ({e})")
        
        print(f"Total de archivos encontrados: {total_found}")
        return total_found > 0
    
    async def test_system_statistics(self):
        """Prueba las estadísticas del sistema"""
        print("\n=== Prueba: Estadísticas del Sistema ===")
        
        try:
            response = await self.session.get(f"{self.central_url}/api/stats", timeout=10)
            if response.status == 200:
                stats = await response.json()
                print(f"Estadísticas del sistema:")
                print(f"  - Total peers: {stats['total_peers']}")
                print(f"  - Peers en línea: {stats['online_peers']}")
                print(f"  - Total archivos: {stats['total_files']}")
                print(f"  - Tamaño total: {stats['total_size']} bytes")
                print(f"  - Transferencias activas: {stats['active_transfers']}")
                
                # Verificar que las estadísticas sean consistentes
                if stats['total_peers'] > 0 and stats['online_peers'] <= stats['total_peers']:
                    print("✓ Estadísticas consistentes")
                    return True
                else:
                    print("✗ Estadísticas inconsistentes")
                    return False
            else:
                print(f"Error obteniendo estadísticas: HTTP {response.status}")
                return False
        except Exception as e:
            print(f"Error obteniendo estadísticas: {e}")
            return False
    
    async def test_file_download_coordination(self):
        """Prueba la coordinación de descargas"""
        print("\n=== Prueba: Coordinación de Descargas ===")
        
        try:
            # Obtener archivos disponibles
            response = await self.session.get(f"{self.central_url}/api/files/peer/peer1", timeout=10)
            if response.status == 200:
                files = await response.json()
                
                if files:
                    file_info = files[0]  # Tomar el primer archivo
                    print(f"Probando descarga de: {file_info['filename']}")
                    
                    # Simular solicitud de descarga
                    download_request = {
                        "file_hash": file_info['file_hash'],
                        "requesting_peer_id": "test_client"
                    }
                    
                    download_response = await self.session.post(
                        f"{self.central_url}/api/transfers/download",
                        json=download_request,
                        timeout=10
                    )
                    
                    if download_response.status == 200:
                        download_data = await download_response.json()
                        if download_data['success']:
                            print(f"  ✓ Descarga coordinada exitosamente")
                            print(f"  - URL: {download_data['download_url']}")
                            return True
                        else:
                            print(f"  ✗ Error en descarga: {download_data['error_message']}")
                            return False
                    else:
                        print(f"  ✗ Error HTTP: {download_response.status}")
                        return False
                else:
                    print("  No hay archivos disponibles para descarga")
                    return False
            else:
                print(f"Error obteniendo archivos: HTTP {response.status}")
                return False
        except Exception as e:
            print(f"Error en prueba de descarga: {e}")
            return False
    
    async def test_concurrent_searches(self, num_requests: int = 10):
        """Prueba búsquedas concurrentes en el servidor central"""
        print(f"\n=== Prueba: Búsquedas Concurrentes ({num_requests} solicitudes) ===")
        
        start_time = time.time()
        
        # Crear tareas concurrentes
        tasks = []
        for i in range(num_requests):
            query = f"test{i % 5}"  # Rotar entre 5 consultas diferentes
            task = self._search_central(query)
            tasks.append(task)
        
        # Ejecutar todas las tareas concurrentemente
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Analizar resultados
        successful = sum(1 for r in results if not isinstance(r, Exception) and r > 0)
        failed = len(results) - successful
        total_files = sum(r for r in results if not isinstance(r, Exception) and isinstance(r, int))
        
        print(f"Resultados:")
        print(f"  - Exitosas: {successful}")
        print(f"  - Fallidas: {failed}")
        print(f"  - Tiempo total: {total_time:.2f}s")
        print(f"  - Tiempo promedio: {total_time/num_requests:.2f}s")
        print(f"  - Archivos encontrados: {total_files}")
        
        return successful > num_requests * 0.8  # 80% de éxito
    
    async def _search_central(self, query: str) -> int:
        """Realiza una búsqueda en el servidor central"""
        try:
            search_data = {"filename": query}
            response = await self.session.post(
                f"{self.central_url}/api/files/search",
                json=search_data,
                timeout=10
            )
            
            if response.status == 200:
                data = await response.json()
                return data.get('total_found', 0)
            else:
                return 0
        except Exception as e:
            print(f"Error en búsqueda '{query}': {e}")
            return 0
    
    async def test_peer_health_monitoring(self):
        """Prueba el monitoreo de salud de peers"""
        print("\n=== Prueba: Monitoreo de Salud de Peers ===")
        
        try:
            response = await self.session.get(f"{self.central_url}/api/peers/online", timeout=10)
            if response.status == 200:
                online_peers = await response.json()
                print(f"Peers en línea: {len(online_peers)}")
                
                for peer in online_peers:
                    print(f"  - {peer['peer_id']}: {peer['files_count']} archivos")
                
                # Verificar que los peers estén realmente en línea
                health_checks = []
                for peer in online_peers:
                    peer_url = f"http://{peer['host']}:{peer['port']}"
                    health_check = await self._check_peer_health(peer_url)
                    health_checks.append(health_check)
                
                healthy_peers = sum(health_checks)
                print(f"Peers realmente saludables: {healthy_peers}/{len(online_peers)}")
                
                return healthy_peers > 0
            else:
                print(f"Error obteniendo peers en línea: HTTP {response.status}")
                return False
        except Exception as e:
            print(f"Error en monitoreo de salud: {e}")
            return False
    
    async def _check_peer_health(self, peer_url: str) -> bool:
        """Verifica la salud de un peer específico"""
        try:
            response = await self.session.get(f"{peer_url}/api/health", timeout=5)
            return response.status == 200
        except Exception:
            return False
    
    async def run_all_tests(self):
        """Ejecuta todas las pruebas del servidor central"""
        print("🧪 Iniciando Pruebas del Servidor Central P2P")
        print("=" * 60)
        
        try:
            await self.initialize()
            
            # Ejecutar pruebas
            tests = [
                ("Salud del Servidor Central", self.test_central_server_health()),
                ("Registro de Peers", self.test_peer_registration()),
                ("Búsqueda Centralizada", self.test_central_file_search()),
                ("Estadísticas del Sistema", self.test_system_statistics()),
                ("Coordinación de Descargas", self.test_file_download_coordination()),
                ("Búsquedas Concurrentes", self.test_concurrent_searches(20)),
                ("Monitoreo de Salud", self.test_peer_health_monitoring())
            ]
            
            results = []
            for test_name, test_coro in tests:
                print(f"\n--- Ejecutando: {test_name} ---")
                try:
                    result = await test_coro
                    results.append((test_name, result))
                    status = "✓ PASS" if result else "✗ FAIL"
                    print(f"Resultado: {status}")
                except Exception as e:
                    print(f"Error en {test_name}: {e}")
                    results.append((test_name, False))
            
            # Resumen de resultados
            print("\n" + "=" * 60)
            print("📊 RESUMEN DE PRUEBAS")
            print("=" * 60)
            
            passed = sum(1 for _, result in results if result)
            total = len(results)
            
            for test_name, result in results:
                status = "✓ PASS" if result else "✗ FAIL"
                print(f"{status} - {test_name}")
            
            print(f"\nTotal: {passed}/{total} pruebas pasaron")
            
            if passed == total:
                print("🎉 ¡Todas las pruebas pasaron!")
            elif passed >= total * 0.8:
                print("⚠️  La mayoría de las pruebas pasaron")
            else:
                print("❌ Muchas pruebas fallaron")
            
        except Exception as e:
            print(f"❌ Error en las pruebas: {e}")
        finally:
            await self.close()

async def main():
    """Función principal"""
    tester = CentralServerTester()
    await tester.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())
