import asyncio
import uvicorn
import os
import signal
import sys
from contextlib import asynccontextmanager

from models.config import PeerConfig
from services.file_indexer import FileIndexer
from services.file_locator import FileLocator
from services.file_transfer import FileTransfer
from services.pclient import PClient
from services.central_client import CentralClient
from api.rest_api import RESTAPI
from api.grpc_api import GRPCServer

class PeerNode:
    """Nodo principal del peer P2P"""
    
    def __init__(self):
        self.config: PeerConfig = None
        self.file_indexer: FileIndexer = None
        self.file_locator: FileLocator = None
        self.file_transfer: FileTransfer = None
        self.pclient: PClient = None
        self.central_client: CentralClient = None
        self.rest_api: RESTAPI = None
        self.grpc_server: GRPCServer = None
        self.running = False
    
    async def initialize(self):
        """Inicializa todos los componentes del peer"""
        try:
            # Cargar configuración
            self.config = PeerConfig.load_from_env()
            print(f"Inicializando peer {self.config.peer_id}")
            
            # Crear directorio compartido si no existe
            os.makedirs(self.config.shared_directory, exist_ok=True)
            
            # Inicializar servicios
            self.file_indexer = FileIndexer(
                self.config.shared_directory, 
                self.config.peer_id
            )
            
            self.file_locator = FileLocator(
                self.file_indexer, 
                self.config.network
            )
            
            self.file_transfer = FileTransfer(
                self.file_indexer,
                self.config.shared_directory,
                self.config.peer_id
            )
            
            self.pclient = PClient(
                self.config.peer_id,
                self.file_locator,
                self.file_transfer
            )
            
            # Inicializar cliente central
            # Usar el nombre del contenedor Docker para conectarse al servidor central
            central_server_url = "http://p2p-central-server:8000"
            self.central_client = CentralClient(
                central_server_url,
                self.config.peer_id,
                self.config.server.host,
                self.config.server.port,
                self.config.server.grpc_port
            )
            
            # Inicializar APIs
            self.rest_api = RESTAPI(
                self.config.peer_id,
                self.config,
                self.file_indexer,
                self.file_locator,
                self.file_transfer,
                self.pclient,
                self.central_client
            )
            
            self.grpc_server = GRPCServer(
                self.config.peer_id,
                self.config.server.grpc_port,
                self.file_indexer,
                self.file_locator,
                self.file_transfer
            )
            
            # Inicializar servicios
            await self.file_locator.initialize()
            await self.file_transfer.initialize()
            await self.pclient.initialize()
            await self.central_client.initialize()
            
            print("Peer inicializado correctamente")
            
        except Exception as e:
            print(f"Error inicializando peer: {e}")
            raise
    
    async def start(self):
        """Inicia el peer"""
        try:
            self.running = True
            
            # Escanear directorio inicial
            print("Escaneando directorio compartido...")
            files = await self.file_indexer.scan_directory()
            print(f"Encontrados {len(files)} archivos")
            
            # Sincronizar con servidor central
            print("Sincronizando con servidor central...")
            await self.central_client.sync_files_with_central(files)
            
            # Iniciar servidor gRPC
            await self.grpc_server.start()
            
            # Iniciar tareas en segundo plano
            asyncio.create_task(self._background_tasks())
            
            print(f"Peer {self.config.peer_id} iniciado")
            print(f"API REST disponible en puerto {self.config.server.port}")
            print(f"API gRPC disponible en puerto {self.config.server.grpc_port}")
            
        except Exception as e:
            print(f"Error iniciando peer: {e}")
            raise
    
    async def stop(self):
        """Detiene el peer"""
        try:
            self.running = False
            
            # Detener servidor gRPC
            if self.grpc_server:
                await self.grpc_server.stop()
            
            # Cerrar servicios
            if self.pclient:
                await self.pclient.close()
            
            if self.central_client:
                await self.central_client.unregister_from_central()
                await self.central_client.close()
            
            if self.file_locator:
                await self.file_locator.close()
            
            if self.file_transfer:
                await self.file_transfer.close()
            
            print("Peer detenido correctamente")
            
        except Exception as e:
            print(f"Error deteniendo peer: {e}")
    
    async def _background_tasks(self):
        """Tareas que se ejecutan en segundo plano"""
        while self.running:
            try:
                # Descubrir nuevos peers cada 30 segundos
                await asyncio.sleep(30)
                if self.running:
                    discovered = await self.pclient.discover_network()
                    if discovered:
                        print(f"Descubiertos nuevos peers: {discovered}")
                
                # Sincronizar con peers conocidos cada 60 segundos
                await asyncio.sleep(30)
                if self.running:
                    # Sincronizar con servidor central
                    files = await self.file_indexer.get_all_files()
                    await self.central_client.sync_files_with_central(files)
                    
                    # Sincronizar con peers conocidos
                    for peer_id in self.file_locator.known_peers.keys():
                        await self.pclient.sync_with_peer(peer_id)
                
            except Exception as e:
                print(f"Error en tareas en segundo plano: {e}")
                await asyncio.sleep(10)

# Instancia global del peer
peer_node = PeerNode()

def signal_handler(signum, frame):
    """Maneja señales del sistema"""
    print(f"\nRecibida señal {signum}, deteniendo peer...")
    asyncio.create_task(peer_node.stop())
    sys.exit(0)

async def main():
    """Función principal"""
    # Configurar manejadores de señales
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # Inicializar peer
        await peer_node.initialize()
        
        # Iniciar peer
        await peer_node.start()
        
        # Iniciar servidor REST
        app = peer_node.rest_api.get_app()
        config = uvicorn.Config(
            app, 
            host=peer_node.config.server.host, 
            port=peer_node.config.server.port,
            log_level="info"
        )
        server = uvicorn.Server(config)
        
        # Ejecutar servidor REST
        await server.serve()
        
    except KeyboardInterrupt:
        print("Interrumpido por el usuario")
    except Exception as e:
        print(f"Error en main: {e}")
    finally:
        await peer_node.stop()

if __name__ == "__main__":
    asyncio.run(main())
