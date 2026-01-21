import os
import logging
import time
from typing import Optional, Any, List
from neo4j import GraphDatabase, Driver, Session, Transaction
from neo4j.exceptions import ServiceUnavailable, AuthError

# Configure Logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Neo4jClient:
    """
    Singleton class to manage Neo4j connection.
    Implements robust error handling, retries, and context management.
    """
    _instance: Optional['Neo4jClient'] = None
    _driver: Optional[Driver] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Neo4jClient, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        # Avoid re-initialization if already initialized
        if self._driver is not None:
            return

        self.uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
        user = os.getenv("NEO4J_USER", "neo4j")
        password = os.getenv("NEO4J_PASSWORD", "secret_password_123")
        
        # Parse AUTH if provided in single var (docker-compose style)
        auth_env = os.getenv("NEO4J_AUTH")
        if auth_env and "/" in auth_env:
            user, password = auth_env.split("/", 1)

        self.auth = (user, password)
        self.connect()

    def connect(self) -> None:
        """Establishes the driver connection with retry logic."""
        max_retries = 5
        retry_delay = 2

        for attempt in range(max_retries):
            try:
                self._driver = GraphDatabase.driver(self.uri, auth=self.auth)
                self.verify_connection()
                logger.info("✅ Connected to Neo4j successfully.")
                return
            except (ServiceUnavailable, AuthError, Exception) as e:
                logger.warning(f"Connection attempt {attempt + 1}/{max_retries} failed: {e}")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                else:
                    logger.error("❌ Failed to connect to Neo4j after multiple attempts.")
                    raise e

    def verify_connection(self) -> None:
        """Health check for the database connection."""
        try:
            with self._driver.session() as session:
                session.run("RETURN 1")
        except Exception as e:
            logger.error("Health check failed.")
            raise e

    def close(self) -> None:
        """Closes the driver connection."""
        if self._driver:
            self._driver.close()
            logger.info("Neo4j connection closed.")

    def get_driver(self) -> Driver:
        """Returns the active driver."""
        if self._driver is None:
            self.connect()
        return self._driver

    def execute_query(self, query: str, parameters: Optional[dict] = None, db: str = "neo4j") -> List[Any]:
        """
        Executes a Cypher query and returns the results.
        Uses explicit session management to ensure ACID compliance.
        """
        if self._driver is None:
            self.connect()

        try:
            with self._driver.session(database=db) as session:
                result = session.run(query, parameters or {})
                return [record for record in result]
        except Exception as e:
            logger.error(f"Query execution error: {e}")
            raise e

    def update_predictions(self, predictions_list: List[Dict[str, Any]]):
        """
        Receives a list of dictionaries: [{'source': ID, 'target': ID, 'risk': 0.95}, ...]
        Creates WILL_COMMIT relationships marked in RED.
        """
        if self._driver is None:
            self.connect()
            
        query = """
        UNWIND $batch as row
        MATCH (p:Citizen {id: row.source})
        MATCH (l:Location {id: row.target})
        MERGE (p)-[r:WILL_COMMIT]->(l)
        SET r.risk_score = row.risk,
            r.color = '#FF0000',  // Rojo "Minority Report"
            r.timestamp = timestamp()
        """
        try:
            with self._driver.session() as session:
                session.run(query, batch=predictions_list)
                logger.info(f"⚡ {len(predictions_list)} prediction(s) inserted into Neo4j.")
        except Exception as e:
            logger.error(f"Failed to insert predictions: {e}")
            raise

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

# Global Client Instance
# Usage:
# from src.database.neo4j_client import db
# results = db.execute_query("MATCH (n) RETURN n")
db = Neo4jClient()
