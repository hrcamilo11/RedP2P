#!/usr/bin/env python3
"""
Script para recrear la base de datos con los nuevos constraints
"""

import os
import sys
import sqlite3

def recreate_database():
    """Recrea la base de datos con los nuevos constraints"""
    print("🗄️ RECREANDO BASE DE DATOS")
    print("=" * 40)
    
    # Ruta de la base de datos
    db_path = "data/central-server/central_server.db"
    
    # Backup de la base de datos existente
    if os.path.exists(db_path):
        backup_path = f"{db_path}.backup"
        print(f"📦 Creando backup: {backup_path}")
        os.rename(db_path, backup_path)
    
    # Crear directorio si no existe
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    
    # Crear nueva base de datos
    print("🆕 Creando nueva base de datos...")
    
    # Importar y crear tablas
    sys.path.append('src/central-server')
    from models.database import create_tables
    
    create_tables()
    
    print("✅ Base de datos recreada exitosamente")
    print(f"📁 Ubicación: {db_path}")
    
    # Verificar constraints
    print("\n🔍 Verificando constraints...")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Verificar constraint único
    cursor.execute("PRAGMA table_info(files)")
    columns = cursor.fetchall()
    print("📋 Columnas de la tabla files:")
    for col in columns:
        print(f"   - {col[1]} ({col[2]})")
    
    # Verificar índices
    cursor.execute("PRAGMA index_list(files)")
    indexes = cursor.fetchall()
    print("\n📊 Índices de la tabla files:")
    for idx in indexes:
        print(f"   - {idx[1]} ({'UNIQUE' if idx[2] else 'INDEX'})")
    
    conn.close()
    print("\n🎯 Base de datos lista para usar")

if __name__ == "__main__":
    recreate_database()
