# database.py
from neo4j import GraphDatabase
import os

class Neo4jProvider:
    def __init__(self):
        # En producción usar variables de entorno
        uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
        user = os.getenv("NEO4J_USER", "neo4j")
        password = os.getenv("NEO4J_PASSWORD", "secret_password")
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

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