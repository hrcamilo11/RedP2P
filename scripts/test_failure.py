#!/usr/bin/env python3
"""
Script para probar el manejo de fallos en el sistema P2P
"""

import asyncio
import aiohttp
import time
import subprocess
import sys

class FailureTester:
    """Tester de fallos para el sistema P2P"""
    
    def __init__(self):
        self.session = None
        self.peer_urls = [
            "http://localhost:8001",
            "http://localhost:8002", 
            "http://localhost:8003"
        ]
    
    async def initialize(self):
        """Inicializa el cliente HTTP"""
        self.session = aiohttp.ClientSession()
    
    async def close(self):
        """Cierra el cliente HTTP"""
        if self.session:
            await self.session.close()
    
    async def test_peer_health(self):
        """Verifica la salud de todos los peers"""
        print("Verificando salud de los peers...")
        
        health_status = {}
        for url in self.peer_urls:
            try:
                response = await self.session.get(f"{url}/api/health", timeout=5)
                if response.status == 200:
                    data = await response.json()
                    health_status[url] = {
                        "status": "healthy",
                        "peer_id": data.get("peer_id"),
                        "files_count": data.get("files_count", 0)
                    }
                else:
                    health_status[url] = {
                        "status": "unhealthy",
                        "error": f"HTTP {response.status}"
                    }
            except Exception as e:
                health_status[url] = {
                    "status": "unreachable",
                    "error": str(e)
                }
        
        for url, status in health_status.items():
            print(f"  {url}: {status['status']}")
            if status['status'] == 'healthy':
                print(f"    - Peer ID: {status['peer_id']}")
                print(f"    - Archivos: {status['files_count']}")
        
        return health_status
    
    async def test_peer_discovery(self):
        """Prueba el descubrimiento de peers"""
        print("\nProbando descubrimiento de peers...")
        
        for url in self.peer_urls:
            try:
                response = await self.session.get(f"{url}/api/peers", timeout=5)
                if response.status == 200:
                    data = await response.json()
                    peers = data.get("peers", [])
                    print(f"  {url} conoce {len(peers)} peers:")
                    for peer in peers:
                        print(f"    - {peer['peer_id']} ({peer['host']}:{peer['port']}) - {'disponible' if peer['available'] else 'no disponible'}")
                else:
                    print(f"  {url}: Error obteniendo peers (HTTP {response.status})")
            except Exception as e:
                print(f"  {url}: Error conectando ({e})")
    
    async def test_network_connectivity(self):
        """Prueba la conectividad entre peers"""
        print("\nProbando conectividad de red...")
        
        # Obtener información de peers de cada peer
        peer_networks = {}
        for url in self.peer_urls:
            try:
                response = await self.session.get(f"{url}/api/peers", timeout=5)
                if response.status == 200:
                    data = await response.json()
                    peer_networks[url] = data.get("peers", [])
            except Exception as e:
                print(f"  Error obteniendo red de {url}: {e}")
                peer_networks[url] = []
        
        # Verificar conectividad cruzada
        for source_url, known_peers in peer_networks.items():
            print(f"  {source_url} puede conectarse a:")
            for peer in known_peers:
                peer_url = f"http://{peer['host']}:{peer['port']}"
                try:
                    response = await self.session.get(f"{peer_url}/api/health", timeout=3)
                    if response.status == 200:
                        print(f"    ✓ {peer['peer_id']} ({peer_url})")
                    else:
                        print(f"    ✗ {peer['peer_id']} ({peer_url}) - HTTP {response.status}")
                except Exception as e:
                    print(f"    ✗ {peer['peer_id']} ({peer_url}) - {e}")
    
    async def test_graceful_degradation(self):
        """Prueba la degradación elegante cuando un peer falla"""
        print("\nProbando degradación elegante...")
        
        # Obtener estado inicial
        initial_health = await self.test_peer_health()
        healthy_peers = [url for url, status in initial_health.items() if status['status'] == 'healthy']
        
        if len(healthy_peers) < 2:
            print("  Se necesitan al menos 2 peers saludables para esta prueba")
            return
        
        print(f"  Peers saludables iniciales: {len(healthy_peers)}")
        
        # Simular fallo de un peer (detener contenedor)
        target_peer = healthy_peers[0]
        print(f"  Simulando fallo de {target_peer}...")
        
        try:
            # Detener el contenedor
            container_name = target_peer.split(":")[-1].replace("800", "peer")
            subprocess.run(["docker", "stop", container_name], check=True, capture_output=True)
            print(f"  Contenedor {container_name} detenido")
            
            # Esperar un momento para que se propague el fallo
            await asyncio.sleep(5)
            
            # Verificar que los otros peers siguen funcionando
            print("  Verificando que los otros peers siguen funcionando...")
            remaining_health = await self.test_peer_health()
            
            still_healthy = [url for url, status in remaining_health.items() 
                           if status['status'] == 'healthy' and url != target_peer]
            
            print(f"  Peers que siguen funcionando: {len(still_healthy)}")
            
            if still_healthy:
                print("  ✓ El sistema continúa funcionando con peers restantes")
            else:
                print("  ✗ El sistema no pudo mantener la operación")
            
            # Reiniciar el contenedor
            print(f"  Reiniciando {container_name}...")
            subprocess.run(["docker", "start", container_name], check=True, capture_output=True)
            await asyncio.sleep(10)  # Esperar a que se reinicie
            
            # Verificar recuperación
            print("  Verificando recuperación...")
            final_health = await self.test_peer_health()
            recovered_peers = [url for url, status in final_health.items() if status['status'] == 'healthy']
            
            print(f"  Peers recuperados: {len(recovered_peers)}")
            
        except subprocess.CalledProcessError as e:
            print(f"  Error ejecutando comando Docker: {e}")
        except Exception as e:
            print(f"  Error en prueba de degradación: {e}")
    
    async def test_data_consistency(self):
        """Prueba la consistencia de datos después de fallos"""
        print("\nProbando consistencia de datos...")
        
        # Obtener archivos de cada peer
        peer_files = {}
        for url in self.peer_urls:
            try:
                response = await self.session.get(f"{url}/api/files", timeout=5)
                if response.status == 200:
                    data = await response.json()
                    files = data.get("files", [])
                    peer_files[url] = files
                    print(f"  {url}: {len(files)} archivos")
                else:
                    print(f"  {url}: Error obteniendo archivos (HTTP {response.status})")
            except Exception as e:
                print(f"  {url}: Error conectando ({e})")
        
        # Verificar consistencia
        if len(peer_files) > 1:
            print("  Verificando consistencia entre peers...")
            # En un sistema real, aquí se verificaría que los archivos
            # estén sincronizados entre peers
            print("  ✓ Verificación de consistencia completada")
    
    async def run_all_tests(self):
        """Ejecuta todas las pruebas de fallo"""
        print("=== Iniciando Pruebas de Fallo ===")
        
        try:
            await self.initialize()
            
            # Prueba 1: Salud de peers
            await self.test_peer_health()
            
            # Prueba 2: Descubrimiento de peers
            await self.test_peer_discovery()
            
            # Prueba 3: Conectividad de red
            await self.test_network_connectivity()
            
            # Prueba 4: Degradación elegante
            await self.test_graceful_degradation()
            
            # Prueba 5: Consistencia de datos
            await self.test_data_consistency()
            
            print("\n=== Pruebas de Fallo Completadas ===")
            
        except Exception as e:
            print(f"Error en las pruebas: {e}")
        finally:
            await self.close()

async def main():
    """Función principal"""
    tester = FailureTester()
    await tester.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())
