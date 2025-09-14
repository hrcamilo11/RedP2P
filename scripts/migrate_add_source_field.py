#!/usr/bin/env python3
"""
Script de migración para agregar el campo 'source' a la tabla de archivos
"""

import sqlite3
import os
import sys

def migrate_database():
    """Migra la base de datos para agregar el campo source"""
    
    # Ruta a la base de datos
    db_path = "data/central-server/central_server.db"
    
    if not os.path.exists(db_path):
        print(f"❌ Base de datos no encontrada en {db_path}")
        return False
    
    try:
        # Conectar a la base de datos
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Verificar si el campo source ya existe
        cursor.execute("PRAGMA table_info(files)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'source' in columns:
            print("✅ Campo 'source' ya existe en la tabla files")
            return True
        
        # Agregar el campo source con valor por defecto 'indexed'
        print("🔄 Agregando campo 'source' a la tabla files...")
        cursor.execute("ALTER TABLE files ADD COLUMN source VARCHAR DEFAULT 'indexed'")
        
        # Actualizar archivos existentes para marcar como indexados
        cursor.execute("UPDATE files SET source = 'indexed' WHERE source IS NULL")
        
        # Confirmar cambios
        conn.commit()
        
        print("✅ Campo 'source' agregado exitosamente")
        print("✅ Todos los archivos existentes marcados como 'indexed'")
        
        return True
        
    except Exception as e:
        print(f"❌ Error migrando base de datos: {e}")
        return False
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    print("🚀 Iniciando migración de base de datos...")
    success = migrate_database()
    
    if success:
        print("✅ Migración completada exitosamente")
        sys.exit(0)
    else:
        print("❌ Migración falló")
        sys.exit(1)
