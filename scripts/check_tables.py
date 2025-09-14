#!/usr/bin/env python3
import sqlite3

conn = sqlite3.connect('data/central-server/central_server.db')
cursor = conn.cursor()
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [row[0] for row in cursor.fetchall()]
print("Tablas en la base de datos:", tables)
conn.close()
