import random
import time
import logging
from datetime import datetime, timedelta
from neo4j import GraphDatabase
from faker import Faker
from tqdm import tqdm  # Progress bar

# --- CONFIGURACIÓN ---
# These are loaded from environment in a real app, but hardcoded here as per script provided
URI = "bolt://localhost:7687"
AUTH = ("neo4j", "secret_password_123")  # Updated to match our docker-compose config
NUM_CITIZENS = 1000
NUM_LOCATIONS = 50
CRIME_RATE = 0.05  # 5% de la población son criminales activos

fake = Faker()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PreCrimeCityGenerator:
    def __init__(self, uri, auth):
        self.driver = GraphDatabase.driver(uri, auth=auth)
    
    def close(self):
        self.driver.close()

    def clear_database(self):
        """Limpia la base de datos para empezar de cero."""
        logger.info("🧹 Limpiando la ciudad (Base de datos)...")
        with self.driver.session() as session:
            session.run("MATCH (n) DETACH DELETE n")

    def create_constraints(self):
        """Crea índices para que la inserción sea rápida."""
        logger.info("🛡️ Estableciendo leyes físicas (Indices)...")
        queries = [
            "CREATE CONSTRAINT citizen_id IF NOT EXISTS FOR (c:Citizen) REQUIRE c.id IS UNIQUE",
            "CREATE CONSTRAINT location_id IF NOT EXISTS FOR (l:Location) REQUIRE l.id IS UNIQUE",
            "CREATE INDEX risk_index IF NOT EXISTS FOR (c:Citizen) ON (c.risk_seed)"
        ]
        with self.driver.session() as session:
            for q in queries:
                session.run(q)

    def generate_locations(self):
        """Genera el escenario (Bancos, Callejones, Parques)."""
        logger.info(f"buildings Construyendo {NUM_LOCATIONS} ubicaciones...")
        loc_types = ["Bank", "Jewelry Store", "Subway Station", "Dark Alley", "Park", "Cafe", "Apartment Block"]
        
        locations = []
        for i in range(NUM_LOCATIONS):
            l_type = random.choice(loc_types)
            # Los callejones tienen un factor de riesgo ambiental más alto
            env_risk = 0.9 if l_type == "Dark Alley" else 0.1
            
            locations.append({
                "id": f"LOC_{i}",
                "name": f"{fake.street_name()} {l_type}",
                "type": l_type,
                "env_risk": env_risk,
                "coord_x": float(fake.latitude()), # Ensure float for Neo4j point
                "coord_y": float(fake.longitude())
            })

        query = """
        UNWIND $batch as row
        MERGE (l:Location {id: row.id})
        SET l.name = row.name, l.type = row.type, 
            l.env_risk = row.env_risk, l.coord = point({latitude: toFloat(row.coord_x), longitude: toFloat(row.coord_y)})
        """
        self._batch_insert(query, locations)

    def generate_citizens(self):
        """
        Genera ciudadanos con una 'Semilla de Riesgo'.
        Esta semilla es la variable latente que la IA intentará descubrir.
        """
        logger.info(f"👥 Poblando la ciudad con {NUM_CITIZENS} ciudadanos...")
        citizens = []
        for i in range(NUM_CITIZENS):
            # Distribución Beta: La mayoría es buena gente (riesgo bajo), pocos son muy peligrosos
            risk_seed = random.betavariate(2, 10) 
            
            citizens.append({
                "id": i,
                "name": fake.name(),
                "born": fake.year(),
                "risk_seed": risk_seed, # <--- EL SECRETO
                "job": fake.job()
            })

        query = """
        UNWIND $batch as row
        CREATE (c:Citizen {id: row.id})
        SET c.name = row.name, c.born = row.born, 
            c.risk_seed = row.risk_seed, c.job = row.job
        """
        self._batch_insert(query, citizens)

    def generate_social_graph(self):
        """
        Crea la red social (:KNOWS).
        Usa lógica de 'Homofilia': Criminales conocen criminales.
        """
        logger.info("🕸️ Tejiendo la red social...")
        
        # Recuperamos los IDs y sus riesgos para calcular lógica en Python
        with self.driver.session() as session:
            result = session.run("MATCH (c:Citizen) RETURN c.id as id, c.risk_seed as risk")
            population = [{"id": r["id"], "risk": r["risk"]} for r in result]

        relationships = []
        
        # Using simple loop with tqdm manually if verifying local execution, but standard tqdm wrapper is fine
        for person in tqdm(population, desc="Social Links"):
            # Lógica 1: Vecinos (IDs cercanos simulan vecindario físico)
            # Lógica 2: Afinidad de riesgo (Pandillas)
            
            # num_friends = random.randint(3, 15) # Original
            # Reduced slightly for faster demo execution if needed, but keeping close to original
            num_friends = random.randint(2, 10)
            potential_friends = random.sample(population, 20) # Muestreo para no comparar con todos
            
            for friend in potential_friends:
                if person["id"] == friend["id"]: continue
                
                # Probabilidad base de conexión
                prob = 0.1 
                
                # Si ambos tienen alto riesgo, es muy probable que se conozcan (Cómplices)
                if person["risk"] > 0.6 and friend["risk"] > 0.6:
                    prob += 0.5
                
                if random.random() < prob:
                    relationships.append({"p1": person["id"], "p2": friend["id"]})

        query = """
        UNWIND $batch as row
        MATCH (a:Citizen {id: row.p1}), (b:Citizen {id: row.p2})
        MERGE (a)-[:KNOWS]->(b)
        """
        self._batch_insert(query, relationships, batch_size=1000)

    def generate_crimes(self):
        """
        Genera el 'Ground Truth' (:COMMITTED_CRIME).
        Solo ciudadanos con alto risk_seed cometen crímenes.
        """
        logger.info("🚨 Generando historial criminal...")
        crimes = []
        
        # Recuperar ciudadanos de alto riesgo y ubicaciones
        with self.driver.session() as session:
            # Note: The original script used .value() which returns a list of single values (ids)
            high_risk_citizens = session.run("MATCH (c:Citizen) WHERE c.risk_seed > 0.6 RETURN c.id as id").value()
            locations = session.run("MATCH (l:Location) RETURN l.id as id, l.type as type").data()

        if not high_risk_citizens:
            logger.info("⚠️ No hay ciudadanos de alto riesgo generados.")
            return

        for criminal_id in high_risk_citizens:
            # Cuantos más crímenes cometa, más fácil será para GraphSAGE detectarlo
            num_crimes = random.randint(1, 4) 
            
            for _ in range(num_crimes):
                target = random.choice(locations)
                
                # Lógica: Roban Bancos, Asaltan en Callejones
                crime_type = "Robbery" if target["type"] == "Bank" else "Assault"
                if target["type"] == "Park": crime_type = "Vandalism"
                
                crimes.append({
                    "cid": criminal_id,
                    "lid": target["id"],
                    "type": crime_type,
                    "date": fake.date_between(start_date='-2y', end_date='today').isoformat()
                })

        query = """
        UNWIND $batch as row
        MATCH (c:Citizen {id: row.cid})
        MATCH (l:Location {id: row.lid})
        MERGE (c)-[:COMMITTED_CRIME {date: row.date, type: row.type}]->(l)
        """
        self._batch_insert(query, crimes)

    def _batch_insert(self, query, data, batch_size=500):
        """Helper para insertar datos en bloques y no saturar la RAM."""
        with self.driver.session() as session:
            total = len(data)
            # Use TQDM for batch writing visualisation
            for i in range(0, total, batch_size):
                batch = data[i:i+batch_size]
                session.run(query, batch=batch)

# --- EJECUCIÓN PRINCIPAL ---
if __name__ == "__main__":
    generator = PreCrimeCityGenerator(URI, AUTH)
    
    try:
        generator.create_constraints()
        generator.clear_database()
        
        generator.generate_locations()
        generator.generate_citizens()
        generator.generate_social_graph()
        generator.generate_crimes()
        
        print("\n✅ CIUDAD GENERADA EXITOSAMENTE.")
        print("Ahora tienes datos para entrenar a tus Precogs.")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
    finally:
        generator.close()
