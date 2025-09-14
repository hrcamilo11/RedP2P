#!/usr/bin/env python3
"""
Script para probar la concurrencia del sistema P2P
"""

import asyncio
import aiohttp
import time
import json
from typing import List

class ConcurrencyTester:
    """Tester de concurrencia para el sistema P2P"""
    
    def __init__(self, peer_urls: List[str]):
        self.peer_urls = peer_urls
        self.session = None
    
    async def initialize(self):
        """Inicializa el cliente HTTP"""
        self.session = aiohttp.ClientSession()
    
    async def close(self):
        """Cierra el cliente HTTP"""
        if self.session:
            await self.session.close()
    
    async def test_concurrent_searches(self, num_requests: int = 10):
        """Prueba búsquedas concurrentes"""
        print(f"Probando {num_requests} búsquedas concurrentes...")
        
        start_time = time.time()
        
        # Crear tareas concurrentes
        tasks = []
        for i in range(num_requests):
            task = self._search_files(f"test{i}")
            tasks.append(task)
        
        # Ejecutar todas las tareas concurrentemente
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Analizar resultados
        successful = sum(1 for r in results if not isinstance(r, Exception))
        failed = len(results) - successful
        
        print(f"Resultados:")
        print(f"  - Exitosas: {successful}")
        print(f"  - Fallidas: {failed}")
        print(f"  - Tiempo total: {total_time:.2f}s")
        print(f"  - Tiempo promedio: {total_time/num_requests:.2f}s")
        
        return results
    
    async def _search_files(self, query: str):
        """Realiza una búsqueda en todos los peers"""
        tasks = []
        for url in self.peer_urls:
            task = self._search_peer(url, query)
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        return results
    
    async def _search_peer(self, base_url: str, query: str):
        """Busca archivos en un peer específico"""
        try:
            url = f"{base_url}/api/search"
            params = {"filename": query}
            
            async with self.session.get(url, params=params, timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    return {
                        "peer": base_url,
                        "query": query,
                        "files_found": data.get("total_found", 0),
                        "search_time": data.get("search_time", 0)
                    }
                else:
                    return {
                        "peer": base_url,
                        "query": query,
                        "error": f"HTTP {response.status}"
                    }
        
        except Exception as e:
            return {
                "peer": base_url,
                "query": query,
                "error": str(e)
            }
    
    async def test_concurrent_downloads(self, file_hashes: List[str]):
        """Prueba descargas concurrentes"""
        print(f"Probando descargas concurrentes de {len(file_hashes)} archivos...")
        
        start_time = time.time()
        
        tasks = []
        for file_hash in file_hashes:
            task = self._download_file(file_hash)
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        end_time = time.time()
        total_time = end_time - start_time
        
        successful = sum(1 for r in results if not isinstance(r, Exception) and r.get("success", False))
        failed = len(results) - successful
        
        print(f"Resultados de descarga:")
        print(f"  - Exitosas: {successful}")
        print(f"  - Fallidas: {failed}")
        print(f"  - Tiempo total: {total_time:.2f}s")
        
        return results
    
    async def _download_file(self, file_hash: str):
        """Simula la descarga de un archivo"""
        try:
            # Buscar el archivo en todos los peers
            for url in self.peer_urls:
                file_url = f"{url}/api/file/{file_hash}"
                async with self.session.get(file_url, timeout=5) as response:
                    if response.status == 200:
                        data = await response.json()
                        return {
                            "file_hash": file_hash,
                            "success": True,
                            "file_info": data
                        }
            
            return {
                "file_hash": file_hash,
                "success": False,
                "error": "Archivo no encontrado en ningún peer"
            }
        
        except Exception as e:
            return {
                "file_hash": file_hash,
                "success": False,
                "error": str(e)
            }
    
    async def test_peer_failure(self, target_peer: str):
        """Prueba el comportamiento cuando un peer falla"""
        print(f"Probando fallo del peer {target_peer}...")
        
        # Obtener estado inicial
        initial_status = await self._get_peer_status(target_peer)
        print(f"Estado inicial del peer: {initial_status}")
        
        # Simular fallo (en un escenario real, esto sería detener el contenedor)
        print("Simulando fallo del peer...")
        
        # Intentar operaciones con el peer fallido
        tasks = []
        for i in range(5):
            task = self._search_peer(target_peer, f"test{i}")
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Analizar resultados
        failures = sum(1 for r in results if isinstance(r, Exception) or r.get("error"))
        print(f"Operaciones fallidas: {failures}/5")
        
        return results
    
    async def _get_peer_status(self, peer_url: str):
        """Obtiene el estado de un peer"""
        try:
            url = f"{peer_url}/api/health"
            async with self.session.get(url, timeout=5) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    return {"status": "error", "code": response.status}
        except Exception as e:
            return {"status": "error", "message": str(e)}

async def main():
    """Función principal de pruebas"""
    # URLs de los peers
    peer_urls = [
        "http://localhost:8001",
        "http://localhost:8002",
        "http://localhost:8003"
    ]
    
    tester = ConcurrencyTester(peer_urls)
    
    try:
        await tester.initialize()
        
        print("=== Iniciando Pruebas de Concurrencia ===")
        
        # Prueba 1: Búsquedas concurrentes
        print("\n1. Prueba de búsquedas concurrentes")
        await tester.test_concurrent_searches(20)
        
        # Prueba 2: Descargas concurrentes
        print("\n2. Prueba de descargas concurrentes")
        file_hashes = ["hash1", "hash2", "hash3", "hash4", "hash5"]
        await tester.test_concurrent_downloads(file_hashes)
        
        # Prueba 3: Fallo de peer
        print("\n3. Prueba de fallo de peer")
        await tester.test_peer_failure("http://localhost:8002")
        
        print("\n=== Pruebas completadas ===")
        
    except Exception as e:
        print(f"Error en las pruebas: {e}")
    finally:
        await tester.close()

if __name__ == "__main__":
    asyncio.run(main())
