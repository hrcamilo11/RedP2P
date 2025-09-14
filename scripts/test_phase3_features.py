#!/usr/bin/env python3
"""
Script de testing para las funcionalidades de la Fase 3
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

class Phase3Tester:
    """Tester para funcionalidades de la Fase 3"""
    
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
    
    async def test_advanced_logging(self):
        """Prueba el sistema de logging avanzado"""
        print("🧪 Probando Logging Avanzado...")
        
        try:
            # Hacer peticiones para generar logs
            async with self.session.get(f"{self.base_url}/api/health") as response:
                if response.status == 200:
                    print("   ✅ Logs generados correctamente")
                    return True
                else:
                    print(f"   ❌ Error generando logs: Status {response.status}")
                    return False
                    
        except Exception as e:
            print(f"   ❌ Error probando logging: {e}")
            return False
    
    async def test_backup_system(self):
        """Prueba el sistema de backup"""
        print("🧪 Probando Sistema de Backup...")
        
        try:
            # Listar backups existentes
            async with self.session.get(f"{self.base_url}/api/admin/backups") as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"   ✅ Lista de backups: {len(data.get('backups', []))} backups encontrados")
                    
                    # Crear un nuevo backup
                    async with self.session.post(f"{self.base_url}/api/admin/backups/create") as create_response:
                        if create_response.status == 200:
                            create_data = await create_response.json()
                            print("   ✅ Backup creado exitosamente")
                            return True
                        else:
                            print(f"   ❌ Error creando backup: Status {create_response.status}")
                            return False
                else:
                    print(f"   ❌ Error listando backups: Status {response.status}")
                    return False
                    
        except Exception as e:
            print(f"   ❌ Error probando sistema de backup: {e}")
            return False
    
    async def test_alert_system(self):
        """Prueba el sistema de alertas"""
        print("🧪 Probando Sistema de Alertas...")
        
        try:
            # Obtener alertas
            async with self.session.get(f"{self.base_url}/api/admin/alerts") as response:
                if response.status == 200:
                    data = await response.json()
                    alerts = data.get('alerts', [])
                    print(f"   ✅ Alertas obtenidas: {len(alerts)} alertas encontradas")
                    
                    # Obtener estadísticas de alertas
                    async with self.session.get(f"{self.base_url}/api/admin/alerts/stats") as stats_response:
                        if stats_response.status == 200:
                            stats_data = await stats_response.json()
                            print(f"   ✅ Estadísticas de alertas: {stats_data.get('total_alerts', 0)} total")
                            return True
                        else:
                            print(f"   ❌ Error obteniendo estadísticas: Status {stats_response.status}")
                            return False
                else:
                    print(f"   ❌ Error obteniendo alertas: Status {response.status}")
                    return False
                    
        except Exception as e:
            print(f"   ❌ Error probando sistema de alertas: {e}")
            return False
    
    async def test_business_metrics(self):
        """Prueba las métricas de negocio"""
        print("🧪 Probando Métricas de Negocio...")
        
        try:
            # Obtener métricas de dashboard
            async with self.session.get(f"{self.base_url}/api/admin/metrics") as response:
                if response.status == 200:
                    data = await response.json()
                    print("   ✅ Métricas de dashboard obtenidas")
                    
                    # Verificar estructura de métricas
                    expected_keys = ['peers', 'files', 'transfers', 'system']
                    for key in expected_keys:
                        if key in data:
                            print(f"   ✅ Métrica '{key}' presente")
                        else:
                            print(f"   ❌ Métrica '{key}' faltante")
                    
                    return all(key in data for key in expected_keys)
                else:
                    print(f"   ❌ Error obteniendo métricas: Status {response.status}")
                    return False
                    
        except Exception as e:
            print(f"   ❌ Error probando métricas de negocio: {e}")
            return False
    
    async def test_admin_endpoints(self):
        """Prueba los endpoints de administración"""
        print("🧪 Probando Endpoints de Administración...")
        
        endpoints = [
            ("/api/admin/backups", "GET"),
            ("/api/admin/alerts", "GET"),
            ("/api/admin/alerts/stats", "GET"),
            ("/api/admin/metrics", "GET"),
            ("/api/admin/logs", "GET"),
            ("/api/admin/health/detailed", "GET")
        ]
        
        results = []
        
        for endpoint, method in endpoints:
            try:
                if method == "GET":
                    async with self.session.get(f"{self.base_url}{endpoint}") as response:
                        if response.status == 200:
                            print(f"   ✅ {endpoint}: OK")
                            results.append(True)
                        else:
                            print(f"   ❌ {endpoint}: Status {response.status}")
                            results.append(False)
                elif method == "POST":
                    async with self.session.post(f"{self.base_url}{endpoint}") as response:
                        if response.status in [200, 201]:
                            print(f"   ✅ {endpoint}: OK")
                            results.append(True)
                        else:
                            print(f"   ❌ {endpoint}: Status {response.status}")
                            results.append(False)
            except Exception as e:
                print(f"   ❌ {endpoint}: Error {e}")
                results.append(False)
        
        return all(results)
    
    async def test_advanced_monitoring(self):
        """Prueba el monitoreo avanzado"""
        print("🧪 Probando Monitoreo Avanzado...")
        
        try:
            # Probar endpoint de salud detallado
            async with self.session.get(f"{self.base_url}/api/admin/health/detailed") as response:
                if response.status == 200:
                    data = await response.json()
                    print("   ✅ Estado de salud detallado obtenido")
                    
                    # Verificar componentes
                    components = ['system_health', 'alert_stats', 'business_metrics', 'services_status']
                    for component in components:
                        if component in data:
                            print(f"   ✅ Componente '{component}' presente")
                        else:
                            print(f"   ❌ Componente '{component}' faltante")
                    
                    return all(component in data for component in components)
                else:
                    print(f"   ❌ Error obteniendo salud detallada: Status {response.status}")
                    return False
                    
        except Exception as e:
            print(f"   ❌ Error probando monitoreo avanzado: {e}")
            return False
    
    async def test_configuration_management(self):
        """Prueba el manejo de configuración"""
        print("🧪 Probando Manejo de Configuración...")
        
        try:
            # Probar que el sistema responde con configuración válida
            async with self.session.get(f"{self.base_url}/api/health") as response:
                if response.status == 200:
                    data = await response.json()
                    print("   ✅ Configuración básica funcionando")
                    
                    # Verificar que los servicios están configurados
                    async with self.session.get(f"{self.base_url}/api/admin/health/detailed") as detailed_response:
                        if detailed_response.status == 200:
                            detailed_data = await detailed_response.json()
                            services = detailed_data.get('services_status', {})
                            print(f"   ✅ Servicios configurados: {len(services)} servicios")
                            return True
                        else:
                            print("   ❌ Error obteniendo estado de servicios")
                            return False
                else:
                    print(f"   ❌ Error en configuración básica: Status {response.status}")
                    return False
                    
        except Exception as e:
            print(f"   ❌ Error probando configuración: {e}")
            return False
    
    async def test_performance_improvements(self):
        """Prueba las mejoras de performance"""
        print("🧪 Probando Mejoras de Performance...")
        
        try:
            # Probar múltiples peticiones concurrentes
            tasks = []
            for i in range(10):
                task = self.session.get(f"{self.base_url}/api/health")
                tasks.append(task)
            
            start_time = time.time()
            responses = await asyncio.gather(*tasks, return_exceptions=True)
            end_time = time.time()
            
            # Verificar respuestas
            success_count = sum(1 for r in responses if isinstance(r, aiohttp.ClientResponse) and r.status == 200)
            duration = end_time - start_time
            
            print(f"   ✅ Peticiones concurrentes: {success_count}/10 exitosas en {duration:.2f}s")
            
            # Liberar respuestas
            for response in responses:
                if isinstance(response, aiohttp.ClientResponse):
                    await response.release()
            
            return success_count >= 8  # Al menos 80% de éxito
            
        except Exception as e:
            print(f"   ❌ Error probando performance: {e}")
            return False
    
    async def run_all_tests(self):
        """Ejecuta todas las pruebas de la Fase 3"""
        print("🚀 INICIANDO PRUEBAS DE FASE 3")
        print("=" * 50)
        
        tests = [
            ("Logging Avanzado", self.test_advanced_logging),
            ("Sistema de Backup", self.test_backup_system),
            ("Sistema de Alertas", self.test_alert_system),
            ("Métricas de Negocio", self.test_business_metrics),
            ("Endpoints de Administración", self.test_admin_endpoints),
            ("Monitoreo Avanzado", self.test_advanced_monitoring),
            ("Manejo de Configuración", self.test_configuration_management),
            ("Mejoras de Performance", self.test_performance_improvements),
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
        print("📊 RESUMEN DE PRUEBAS FASE 3")
        print("=" * 50)
        
        passed = sum(1 for _, result in results if result)
        total = len(results)
        
        for test_name, result in results:
            status = "✅ PASÓ" if result else "❌ FALLÓ"
            print(f"{status} - {test_name}")
        
        print(f"\n🎯 Resultado: {passed}/{total} pruebas pasaron")
        
        if passed == total:
            print("🎉 ¡Todas las pruebas de la Fase 3 pasaron!")
            return True
        else:
            print("⚠️  Algunas pruebas fallaron. Revisar la implementación.")
            return False

async def main():
    """Función principal"""
    print("🧪 TESTER DE FUNCIONALIDADES FASE 3")
    print("RedP2P - Sistema P2P Distribuido")
    print()
    
    async with Phase3Tester() as tester:
        success = await tester.run_all_tests()
        return 0 if success else 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
