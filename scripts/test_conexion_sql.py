"""
Script de prueba de conexion SQL Server
Prueba diferentes configuraciones para identificar el problema
"""

import pyodbc
import sys

def test_connection(host, port, database, user, password, driver="ODBC Driver 17 for SQL Server"):
    """Prueba una conexion a SQL Server"""
    
    # Construir connection string
    if port:
        server_part = f"{host},{port}"
    else:
        server_part = host
    
    conn_str = (
        f"DRIVER={{{driver}}};"
        f"SERVER={server_part};"
        f"DATABASE={database};"
        f"UID={user};PWD={password};"
        f"Connection Timeout=5;"
        f"TrustServerCertificate=yes;"
    )
    
    print(f"\nProbando conexion a: {server_part}")
    print(f"Base de datos: {database}")
    print(f"Usuario: {user}")
    print("-" * 50)
    
    try:
        print("Conectando...")
        conn = pyodbc.connect(conn_str, timeout=5)
        cursor = conn.cursor()
        
        # Probar query simple
        cursor.execute("SELECT @@VERSION")
        version = cursor.fetchone()[0]
        
        print("✅ CONEXION EXITOSA!")
        print(f"\nVersion de SQL Server:")
        print(version[:100] + "...")
        
        # Probar query a la base de datos
        cursor.execute("SELECT DB_NAME()")
        db_name = cursor.fetchone()[0]
        print(f"\nBase de datos actual: {db_name}")
        
        cursor.close()
        conn.close()
        return True
        
    except pyodbc.Error as e:
        print("❌ ERROR DE CONEXION:")
        error_msg = str(e)
        
        # Analizar el error
        if "Login timeout expired" in error_msg or "Tiempo de espera" in error_msg:
            print("\n🔍 DIAGNOSTICO:")
            print("- El servidor no responde en el tiempo esperado")
            print("- Posibles causas:")
            print("  1. SQL Server Browser no esta corriendo")
            print("  2. Firewall bloqueando la conexion")
            print("  3. IP o puerto incorrectos")
            
        elif "Login failed" in error_msg:
            print("\n🔍 DIAGNOSTICO:")
            print("- El servidor responde pero rechaza las credenciales")
            print("- Posibles causas:")
            print("  1. Usuario o contraseña incorrectos")
            print("  2. Usuario 'sa' deshabilitado")
            print("  3. Modo de autenticacion mixta no habilitado")
            print("  4. Base de datos no existe")
            
        elif "Cannot open database" in error_msg:
            print("\n🔍 DIAGNOSTICO:")
            print("- Credenciales correctas pero la base de datos no existe")
            print("- Solucion: Crear la base de datos o usar 'master'")
        
        print(f"\nError completo:\n{error_msg}")
        return False
    
    except Exception as e:
        print(f"❌ ERROR INESPERADO: {e}")
        return False


if __name__ == "__main__":
    print("=" * 50)
    print("PRUEBA DE CONEXION SQL SERVER")
    print("=" * 50)
    
    # Configuracion desde el usuario
    HOST = "192.168.0.9"
    PORT = "1433"
    DATABASE = "clinic_db"
    USER = "sa"
    PASSWORD = input("Ingresa la contraseña de 'sa': ")
    
    # Prueba 1: Con IP y puerto
    print("\n\n=== PRUEBA 1: IP + Puerto ===")
    success1 = test_connection(HOST, PORT, DATABASE, USER, PASSWORD)
    
    # Prueba 2: Con IP y puerto, base de datos 'master'
    if not success1:
        print("\n\n=== PRUEBA 2: IP + Puerto + Base de datos 'master' ===")
        success2 = test_connection(HOST, PORT, "master", USER, PASSWORD)
        
        if success2:
            print("\n✅ La conexion funciona con 'master'")
            print("❌ La base de datos 'clinic_db' no existe")
            print("\n💡 SOLUCION: Crear la base de datos 'clinic_db'")
    
    # Prueba 3: Con instancia nombrada
    if not success1:
        print("\n\n=== PRUEBA 3: Con instancia nombrada SQLEXPRESS ===")
        success3 = test_connection(f"{HOST}\\SQLEXPRESS", "", DATABASE, USER, PASSWORD)
    
    print("\n" + "=" * 50)
    print("FIN DE PRUEBAS")
    print("=" * 50)
