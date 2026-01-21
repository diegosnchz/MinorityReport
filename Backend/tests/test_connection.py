from neo4j import GraphDatabase
import os

# --- CONFIGURACIÓN ---
# Si ya editaste database.py con tus datos, puedes intentar importarlo.
# Pero para esta prueba, es mejor pegar aquí tus credenciales de AuraDB
# para asegurarnos de que no hay errores de código externos.

URI = "neo4j+ssc://6ffb75ca.databases.neo4j.io"  # <--- PEGA TU URI AQUÍ
AUTH = ("neo4j", "eJcc40rfUud7IbOLvgX87dsRyT-uhV1FG81v6OnOL7s")          # <--- PEGA TU CONTRASEÑA AQUÍ

def probar_conexion():
    print("⏳ Intentando conectar a Neo4j AuraDB...")
    
    try:
        # 1. Intentamos crear el driver
        with GraphDatabase.driver(URI, auth=AUTH) as driver:
            # 2. Verificamos conectividad básica
            driver.verify_connectivity()
            print("✅ ¡Conexión establecida con el servidor!")

            # 3. Ejecutamos una consulta de prueba real (Leer/Escribir)
            with driver.session() as session:
                result = session.run("RETURN 'Hola desde Python' AS mensaje")
                msg = result.single()["mensaje"]
                print(f"🎉 La base de datos responde: {msg}")
                
    except Exception as e:
        print("\n❌ HUBO UN ERROR:")
        print(e)
        print("\n💡 Pista: Revisa que la URI empiece por 'neo4j+s://' y que la contraseña sea exacta.")

if __name__ == "__main__":
    probar_conexion()