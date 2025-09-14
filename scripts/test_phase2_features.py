#!/usr/bin/env python3
"""
Script de testing para las funcionalidades de la Fase 2
"""

import asyncio
import aiohttp
import json
import time
import sys
import os
from typing import Dict, Any

# Agregar el directorio src al path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src', 'central-server'))

class Phase2Tester:
    """Tester para funcionalidades de la Fase 2"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session = None
        self.results = []
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def test_rate_limiting(self):
        """Prueba el rate limiting"""
        print("🧪 Probando Rate Limiting...")
        
        try:
            # Hacer muchas peticiones rápidas
            tasks = []
            for i in range(150):  # Más del límite de 100
                task = self.session.get(f"{self.base_url}/api/health")
                tasks.append(task)
            
            responses = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Contar respuestas exitosas vs rate limited
            success_count = 0
            rate_limited_count = 0
            
            for response in responses:
                if isinstance(response, aiohttp.ClientResponse):
                    if response.status == 200:
                        success_count += 1
                    elif response.status == 429:
                        rate_limited_count += 1
                    await response.release()
            
            print(f"   ✅ Respuestas exitosas: {success_count}")
            print(f"   ⚠️  Rate limited: {rate_limited_count}")
            
            if rate_limited_count > 0:
                print("   ✅ Rate limiting funcionando correctamente")
                return True
            else:
                print("   ❌ Rate limiting no está funcionando")
                return False
                
        except Exception as e:
            print(f"   ❌ Error probando rate limiting: {e}")
            return False
    
    async def test_monitoring_endpoints(self):
        """Prueba los endpoints de monitoreo"""
        print("🧪 Probando Endpoints de Monitoreo...")
        
        endpoints = [
            "/api/monitoring/health",
            "/api/monitoring/metrics",
            "/api/monitoring/history",
            "/api/monitoring/averages"
        ]
        
        results = []
        
        for endpoint in endpoints:
            try:
                async with self.session.get(f"{self.base_url}{endpoint}") as response:
                    if response.status == 200:
                        data = await response.json()
                        print(f"   ✅ {endpoint}: OK")
                        results.append(True)
                    else:
                        print(f"   ❌ {endpoint}: Status {response.status}")
                        results.append(False)
            except Exception as e:
                print(f"   ❌ {endpoint}: Error {e}")
                results.append(False)
        
        return all(results)
    
    async def test_file_validation(self):
        """Prueba la validación de archivos"""
        print("🧪 Probando Validación de Archivos...")
        
        # Crear archivo de prueba
        test_file_content = b"Test file content for validation"
        
        try:
            # Crear archivo temporal
            import tempfile
            with tempfile.NamedTemporaryFile(delete=False, suffix=".txt") as f:
                f.write(test_file_content)
                temp_file_path = f.name
            
            # Probar subida de archivo válido
            data = aiohttp.FormData()
            data.add_field('file', open(temp_file_path, 'rb'), filename='test.txt')
            data.add_field('target_peer', 'peer1')
            
            async with self.session.post(f"{self.base_url}/api/transfers/upload-file", data=data) as response:
                if response.status == 200:
                    print("   ✅ Subida de archivo válido: OK")
                    valid_upload = True
                else:
                    print(f"   ❌ Subida de archivo válido: Status {response.status}")
                    valid_upload = False
            
            # Probar subida de archivo inválido (extensión no permitida)
            data = aiohttp.FormData()
            data.add_field('file', open(temp_file_path, 'rb'), filename='test.exe')
            data.add_field('target_peer', 'peer1')
            
            async with self.session.post(f"{self.base_url}/api/transfers/upload-file", data=data) as response:
                if response.status == 400:
                    print("   ✅ Validación de extensión: OK")
                    validation_working = True
                else:
                    print(f"   ❌ Validación de extensión: Status {response.status}")
                    validation_working = False
            
            # Limpiar archivo temporal
            os.unlink(temp_file_path)
            
            return valid_upload and validation_working
            
        except Exception as e:
            print(f"   ❌ Error probando validación de archivos: {e}")
            return False
    
    async def test_pagination(self):
        """Prueba la paginación"""
        print("🧪 Probando Paginación...")
        
        try:
            # Probar paginación en archivos de peer
            async with self.session.get(f"{self.base_url}/api/files/peer/peer1?page=1&limit=10") as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"   ✅ Paginación básica: OK (obtenidos {len(data)} archivos)")
                    pagination_working = True
                else:
                    print(f"   ❌ Paginación básica: Status {response.status}")
                    pagination_working = False
            
            # Probar parámetros inválidos
            async with self.session.get(f"{self.base_url}/api/files/peer/peer1?page=0&limit=200") as response:
                if response.status == 200:
                    data = await response.json()
                    # Debería usar valores por defecto
                    print(f"   ✅ Validación de parámetros: OK")
                    validation_working = True
                else:
                    print(f"   ❌ Validación de parámetros: Status {response.status}")
                    validation_working = False
            
            return pagination_working and validation_working
            
        except Exception as e:
            print(f"   ❌ Error probando paginación: {e}")
            return False
    
    async def test_cors_headers(self):
        """Prueba los headers CORS"""
        print("🧪 Probando Headers CORS...")
        
        try:
            # Hacer petición OPTIONS para probar CORS
            async with self.session.options(f"{self.base_url}/api/health") as response:
                headers = response.headers
                
                # Verificar headers CORS
                cors_headers = [
                    'Access-Control-Allow-Origin',
                    'Access-Control-Allow-Methods',
                    'Access-Control-Allow-Headers'
                ]
                
                missing_headers = []
                for header in cors_headers:
                    if header not in headers:
                        missing_headers.append(header)
                
                if not missing_headers:
                    print("   ✅ Headers CORS: OK")
                    return True
                else:
                    print(f"   ❌ Headers CORS faltantes: {missing_headers}")
                    return False
                    
        except Exception as e:
            print(f"   ❌ Error probando CORS: {e}")
            return False
    
    async def test_system_health(self):
        """Prueba la salud general del sistema"""
        print("🧪 Probando Salud del Sistema...")
        
        try:
            # Probar endpoint de salud
            async with self.session.get(f"{self.base_url}/api/health") as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"   ✅ Health check: OK - {data.get('status', 'unknown')}")
                    health_ok = True
                else:
                    print(f"   ❌ Health check: Status {response.status}")
                    health_ok = False
            
            # Probar estadísticas
            async with self.session.get(f"{self.base_url}/api/stats") as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"   ✅ Stats: OK - {data.get('total_peers', 0)} peers, {data.get('total_files', 0)} files")
                    stats_ok = True
                else:
                    print(f"   ❌ Stats: Status {response.status}")
                    stats_ok = False
            
            return health_ok and stats_ok
            
        except Exception as e:
            print(f"   ❌ Error probando salud del sistema: {e}")
            return False
    
    async def run_all_tests(self):
        """Ejecuta todas las pruebas"""
        print("🚀 INICIANDO PRUEBAS DE FASE 2")
        print("=" * 50)
        
        tests = [
            ("Salud del Sistema", self.test_system_health),
            ("Headers CORS", self.test_cors_headers),
            ("Paginación", self.test_pagination),
            ("Validación de Archivos", self.test_file_validation),
            ("Endpoints de Monitoreo", self.test_monitoring_endpoints),
            ("Rate Limiting", self.test_rate_limiting),
        ]
        
        results = []
        
        for test_name, test_func in tests:
            print(f"\n📋 {test_name}")
            print("-" * 30)
            
            try:
                result = await test_func()
                results.append((test_name, result))
                
                if result:
                    print(f"✅ {test_name}: PASÓ")
                else:
                    print(f"❌ {test_name}: FALLÓ")
                    
            except Exception as e:
                print(f"❌ {test_name}: ERROR - {e}")
                results.append((test_name, False))
        
        # Resumen
        print("\n" + "=" * 50)
        print("📊 RESUMEN DE PRUEBAS")
        print("=" * 50)
        
        passed = sum(1 for _, result in results if result)
        total = len(results)
        
        for test_name, result in results:
            status = "✅ PASÓ" if result else "❌ FALLÓ"
            print(f"{status} - {test_name}")
        
        print(f"\n🎯 Resultado: {passed}/{total} pruebas pasaron")
        
        if passed == total:
            print("🎉 ¡Todas las pruebas de la Fase 2 pasaron!")
            return True
        else:
            print("⚠️  Algunas pruebas fallaron. Revisar la implementación.")
            return False

async def main():
    """Función principal"""
    print("🧪 TESTER DE FUNCIONALIDADES FASE 2")
    print("RedP2P - Sistema P2P Distribuido")
    print()
    
    async with Phase2Tester() as tester:
        success = await tester.run_all_tests()
        return 0 if success else 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
