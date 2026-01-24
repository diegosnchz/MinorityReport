# database.py
from neo4j import GraphDatabase
import os
from dotenv import load_dotenv  # <--- IMPORTANTE
load_dotenv()

uri = os.getenv("NEO4J_URI")
print(f"👀 OJO: La URI que estoy leyendo es: '{uri}'")  # <--- AÑADE ESTO
class Neo4jProvider:
    def __init__(self):
        # 1. URI: Cambia 'bolt' por 'neo4j+s' y pon la dirección de tu nube
        uri = os.getenv("NEO4J_URI")
        
        # 2. USER: Normalmente sigue siendo 'neo4j' en AuraDB
        user = os.getenv("NEO4J_USER")
        
        # 3. PASSWORD: Pega aquí la contraseña larga que te dio AuraDB al crear la cuenta
        password = os.getenv("NEO4J_PASSWORD")
        
        try:
            self.driver = GraphDatabase.driver(uri, auth=(user, password))
            # Añadimos un verify para que sepas al instante si conecta
            self.driver.verify_connectivity()
            print("✅ Conectado a Neo4j AuraDB correctamente")
        except Exception as e:
            print(f"❌ Error conectando a Neo4j: {e}")

    def close(self):
        self.driver.close()

    def actualizar_riesgo_nodo(self, nodo_id, riesgo_adicional):
        """
        Consulta Cypher para aumentar el riesgo de un nodo y sus vecinos
        """
        query = """
        MATCH (n:Escondite {name: $id})
        SET n.riesgo = n.riesgo + $riesgo
        WITH n
        MATCH (n)-[r:CONECTA_CON]-(vecino)
        SET vecino.riesgo = vecino.riesgo + ($riesgo * 0.5)
        RETURN n, vecino
        """
        with self.driver.session() as session:
            session.run(query, id=nodo_id, riesgo=riesgo_adicional)
            print(f"⚠️ Neo4j: Riesgo actualizado en zona {nodo_id}")

db = Neo4jProvider()