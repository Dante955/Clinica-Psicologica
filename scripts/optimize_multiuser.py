"""
Script de Optimización de SQLite para Multi-Usuario

Este script optimiza la base de datos SQLite para permitir
acceso simultáneo de múltiples usuarios.

Ejecuta este script UNA SOLA VEZ después de configurar la red compartida.
"""

import sqlite3
import os
import sys

def optimize_database(db_path='clinic.db'):
    """
    Optimiza la base de datos SQLite para acceso multi-usuario.
    
    Args:
        db_path: Ruta a la base de datos (puede ser ruta de red como Z:/clinic.db)
    """
    print("="*60)
    print("🔧 Optimizador de Base de Datos Multi-Usuario")
    print("="*60)
    print()
    
    # Verificar que existe la base de datos
    if not os.path.exists(db_path):
        print(f"❌ Error: No se encontró la base de datos en: {db_path}")
        print()
        print("Por favor, verifica la ruta y vuelve a intentar.")
        input("\nPresiona Enter para salir...")
        sys.exit(1)
    
    try:
        print(f"📁 Conectando a: {db_path}")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("\n⚙️  Aplicando optimizaciones...")
        print()
        
        # 1. Habilitar WAL mode (Write-Ahead Logging)
        print("1️⃣  Habilitando WAL mode...")
        cursor.execute('PRAGMA journal_mode=WAL;')
        result = cursor.fetchone()
        print(f"   ✅ Journal mode: {result[0]}")
        
        # 2. Configurar sincronización normal (balance entre seguridad y velocidad)
        print("2️⃣  Configurando sincronización...")
        cursor.execute('PRAGMA synchronous=NORMAL;')
        print("   ✅ Synchronous: NORMAL")
        
        # 3. Usar memoria para archivos temporales
        print("3️⃣  Optimizando almacenamiento temporal...")
        cursor.execute('PRAGMA temp_store=MEMORY;')
        print("   ✅ Temp store: MEMORY")
        
        # 4. Habilitar memory-mapped I/O (30GB)
        print("4️⃣  Habilitando memory-mapped I/O...")
        cursor.execute('PRAGMA mmap_size=30000000000;')
        print("   ✅ MMAP size: 30GB")
        
        # 5. Configurar timeout para bloqueos (5 segundos)
        print("5️⃣  Configurando timeout de bloqueo...")
        conn.execute('PRAGMA busy_timeout=5000;')
        print("   ✅ Busy timeout: 5000ms")
        
        # 6. Optimizar cache
        print("6️⃣  Optimizando cache...")
        cursor.execute('PRAGMA cache_size=-64000;')  # 64MB
        print("   ✅ Cache size: 64MB")
        
        conn.commit()
        
        # Verificar configuración
        print("\n📊 Verificando configuración final...")
        print()
        
        cursor.execute('PRAGMA journal_mode;')
        journal = cursor.fetchone()[0]
        print(f"   Journal mode: {journal}")
        
        cursor.execute('PRAGMA synchronous;')
        sync = cursor.fetchone()[0]
        print(f"   Synchronous: {sync}")
        
        cursor.execute('PRAGMA temp_store;')
        temp = cursor.fetchone()[0]
        print(f"   Temp store: {temp}")
        
        conn.close()
        
        print()
        print("="*60)
        print("✅ ¡Base de datos optimizada exitosamente!")
        print("="*60)
        print()
        print("📝 Notas importantes:")
        print("   • La base de datos ahora soporta múltiples usuarios simultáneos")
        print("   • Se crearon archivos adicionales (-wal y -shm) - NO los borres")
        print("   • Asegúrate de que todos los usuarios tengan permisos de lectura/escritura")
        print()
        print("🚀 Puedes iniciar la aplicación en múltiples computadoras")
        print()
        
    except sqlite3.Error as e:
        print()
        print(f"❌ Error al optimizar la base de datos: {e}")
        print()
        print("Posibles causas:")
        print("   • La base de datos está siendo usada por otra aplicación")
        print("   • No tienes permisos de escritura")
        print("   • La ruta de red no es accesible")
        print()
    except Exception as e:
        print()
        print(f"❌ Error inesperado: {e}")
        print()
    
    input("\nPresiona Enter para salir...")


if __name__ == "__main__":
    print()
    print("Este script optimizará la base de datos para uso multi-usuario.")
    print()
    
    # Preguntar por la ruta de la base de datos
    print("Opciones:")
    print("1. Base de datos local (clinic.db)")
    print("2. Base de datos en red (ejemplo: Z:/clinic.db)")
    print()
    
    opcion = input("Selecciona una opción (1 o 2): ").strip()
    
    if opcion == "1":
        db_path = "clinic.db"
    elif opcion == "2":
        db_path = input("\nIngresa la ruta completa (ejemplo: Z:/clinic.db): ").strip()
    else:
        print("\n❌ Opción inválida")
        input("\nPresiona Enter para salir...")
        sys.exit(1)
    
    print()
    optimize_database(db_path)
