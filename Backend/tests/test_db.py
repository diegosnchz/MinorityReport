# test_db.py
from database import db

def probar_conexion():
    print("1. Intentando conectar...")
    try:
        # Vamos a crear un nodo de prueba
        with db.driver.session() as session:
            session.run("CREATE (n:TestNode {name: 'Prueba', riesgo: 0.0})")
        print("✅ Conexión ÉXITOSA: Nodo creado.")
        
        # Vamos a probar tu función de actualizar riesgo
        print("2. Probando función actualizar_riesgo_nodo...")
        db.actualizar_riesgo_nodo('Prueba', 0.5)
        print("✅ Función ejecutada sin errores.")
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    probar_conexion()