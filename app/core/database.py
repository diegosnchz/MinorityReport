# app/core/database.py
import os
from neo4j import AsyncGraphDatabase
from dotenv import load_dotenv
import logging

# Cargar variables de entorno (.env)
load_dotenv()

# Configuración básica de logs
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("PreCrimeDB")

class Neo4jManager:
    def __init__(self):
        self._driver = None
        self._uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
        self._user = os.getenv("NEO4J_USER", "neo4j")
        self._password = os.getenv("NEO4J_PASSWORD", "secret_password_123") # Default matching docker

    def connect(self):
        """Inicializa el driver asíncrono."""
        if self._driver is None:
            try:
                self._driver = AsyncGraphDatabase.driver(
                    self._uri,
                    auth=(self._user, self._password)
                )
                logger.info(f"Conectado a Neo4j en {self._uri}")
            except Exception as e:
                logger.error(f"Fallo al conectar con Neo4j: {e}")
                raise e

    async def close(self):
        """Cierra el pool de conexiones de manera limpia."""
        if self._driver:
            await self._driver.close()
            logger.info("Conexión a Neo4j cerrada.")

    async def check_connection(self):
        """Verifica que la base de datos responde (Health check)."""
        if self._driver:
            try:
                await self._driver.verify_connectivity()
                return True
            except Exception:
                return False
        return False

    async def query(self, cypher_query: str, parameters: dict = None):
        """
        Ejecuta una consulta Cypher y devuelve los resultados como lista de diccionarios.
        Maneja la sesión automáticamente.
        """
        if self._driver is None:
            raise ConnectionError("El driver de Neo4j no está inicializado.")
        
        async with self._driver.session() as session:
            result = await session.run(cypher_query, parameters)
            # Convertimos los registros a diccionarios nativos de Python
            data = [record.data() for record in await result.values()]
            return data

# Instancia global para ser importada en el resto de la app
db_manager = Neo4jManager()
