"""
Neo4j Seed Data Script - Creates sample city graph for training

This script populates Neo4j with sample data compatible with the
EXPERIMENTAL_dataEngineer branch schema:
- Citizen nodes with risk features
- Location nodes with surveillance levels
- Relationships: KNOWS, INTERACTS_WITH, CONNECTED_TO, VISITS

Run this after starting Neo4j with: docker-compose up neo4j

Author: The Oracle Team (feature/gat-model)
"""

import os
import random
import logging
from typing import List, Dict, Any

try:
    from neo4j import GraphDatabase
    NEO4J_AVAILABLE = True
except ImportError:
    NEO4J_AVAILABLE = False
    print("WARNING: neo4j not installed. Run: pip install neo4j")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("SeedData")

# Madrid city districts for realistic locations
MADRID_DISTRICTS = [
    {"name": "Sol", "lat": 40.4168, "lng": -3.7038, "type": "commercial", "police": 0.9},
    {"name": "Gran Via", "lat": 40.4203, "lng": -3.7058, "type": "commercial", "police": 0.85},
    {"name": "Malasaña", "lat": 40.4262, "lng": -3.7032, "type": "residential", "police": 0.4},
    {"name": "Chueca", "lat": 40.4225, "lng": -3.6978, "type": "commercial", "police": 0.6},
    {"name": "Lavapiés", "lat": 40.4078, "lng": -3.7003, "type": "residential", "police": 0.5},
    {"name": "La Latina", "lat": 40.4108, "lng": -3.7118, "type": "historic", "police": 0.55},
    {"name": "Retiro", "lat": 40.4153, "lng": -3.6844, "type": "park", "police": 0.3},
    {"name": "Salamanca", "lat": 40.4315, "lng": -3.6788, "type": "residential", "police": 0.7},
    {"name": "Chamberí", "lat": 40.4368, "lng": -3.6988, "type": "residential", "police": 0.45},
    {"name": "Tetuán", "lat": 40.4600, "lng": -3.6950, "type": "industrial", "police": 0.35},
    {"name": "Carabanchel", "lat": 40.3850, "lng": -3.7420, "type": "residential", "police": 0.4},
    {"name": "Vallecas", "lat": 40.3780, "lng": -3.6520, "type": "residential", "police": 0.45},
    {"name": "Hortaleza", "lat": 40.4680, "lng": -3.6400, "type": "residential", "police": 0.35},
    {"name": "Moncloa", "lat": 40.4350, "lng": -3.7200, "type": "university", "police": 0.5},
    {"name": "Atocha", "lat": 40.4065, "lng": -3.6900, "type": "transport", "police": 0.8},
    {"name": "Chamartín", "lat": 40.4720, "lng": -3.6820, "type": "transport", "police": 0.75},
    {"name": "Usera", "lat": 40.3850, "lng": -3.7050, "type": "residential", "police": 0.38},
    {"name": "Villaverde", "lat": 40.3480, "lng": -3.6980, "type": "industrial", "police": 0.32},
    {"name": "Arganzuela", "lat": 40.3920, "lng": -3.6950, "type": "commercial", "police": 0.55},
    {"name": "Centro Histórico", "lat": 40.4150, "lng": -3.7100, "type": "historic", "police": 0.65},
]

# Jobs for citizens
JOBS = [
    "engineer", "teacher", "doctor", "artist", "merchant", "unemployed",
    "student", "driver", "construction", "office_worker", "security",
    "waiter", "chef", "nurse", "lawyer", "accountant"
]

# Names pool
FIRST_NAMES = [
    "Carlos", "María", "Juan", "Ana", "Pedro", "Lucía", "Miguel", "Carmen",
    "David", "Elena", "Antonio", "Isabel", "José", "Laura", "Francisco", "Sara",
    "Pablo", "Marta", "Diego", "Sofia", "Alejandro", "Paula", "Javier", "Rosa"
]

LAST_NAMES = [
    "García", "Martínez", "López", "Sánchez", "González", "Rodríguez",
    "Fernández", "Pérez", "Gómez", "Díaz", "Ruiz", "Hernández", "Jiménez",
    "Moreno", "Muñoz", "Álvarez", "Romero", "Navarro", "Torres", "Domínguez"
]


class Neo4jSeeder:
    """Seeds Neo4j with sample data for MinorityReport training."""
    
    def __init__(
        self,
        uri: str = None,
        user: str = None,
        password: str = None
    ):
        if not NEO4J_AVAILABLE:
            raise ImportError("neo4j package not installed")
        
        self.uri = uri or os.getenv("NEO4J_URI", "bolt://localhost:7687")
        self.user = user or os.getenv("NEO4J_USER", "neo4j")
        self.password = password or os.getenv("NEO4J_PASSWORD", "minorityreport")
        
        self.driver = GraphDatabase.driver(self.uri, auth=(self.user, self.password))
        
    def close(self):
        if self.driver:
            self.driver.close()
    
    def clear_database(self):
        """Remove all existing data."""
        logger.info("Clearing existing data...")
        with self.driver.session() as session:
            session.run("MATCH (n) DETACH DELETE n")
        logger.info("[OK] Database cleared")
    
    def create_constraints(self):
        """Create unique constraints for nodes."""
        logger.info("Creating constraints...")
        
        constraints = [
            "CREATE CONSTRAINT citizen_id IF NOT EXISTS FOR (c:Citizen) REQUIRE c.id IS UNIQUE",
            "CREATE CONSTRAINT location_id IF NOT EXISTS FOR (l:Location) REQUIRE l.id IS UNIQUE",
            "CREATE CONSTRAINT person_id IF NOT EXISTS FOR (p:Person) REQUIRE p.id IS UNIQUE",
        ]
        
        with self.driver.session() as session:
            for constraint in constraints:
                try:
                    session.run(constraint)
                except Exception as e:
                    logger.warning(f"Constraint may already exist: {e}")
        
        logger.info("[OK] Constraints created")
    
    def create_locations(self) -> List[Dict]:
        """Create Location nodes based on Madrid districts."""
        logger.info("Creating Location nodes...")
        
        locations = []
        for idx, district in enumerate(MADRID_DISTRICTS):
            location = {
                "id": idx,
                "name": district["name"],
                "latitude": district["lat"],
                "longitude": district["lng"],
                "locationType": ["commercial", "residential", "historic", "park", 
                                 "transport", "industrial", "university"].index(district["type"]) 
                               if district["type"] in ["commercial", "residential", "historic", "park", 
                                                       "transport", "industrial", "university"] else 0,
                "policeLevel": district["police"],
                "illumination": random.uniform(0.4, 0.9),
                "density": random.uniform(0.3, 0.8),
                "envRisk": district["police"] * 0.5 + random.uniform(0, 0.3)
            }
            locations.append(location)
        
        query = """
        UNWIND $locations AS loc
        CREATE (l:Location {
            id: loc.id,
            name: loc.name,
            latitude: loc.latitude,
            longitude: loc.longitude,
            locationType: loc.locationType,
            policeLevel: loc.policeLevel,
            illumination: loc.illumination,
            density: loc.density,
            envRisk: loc.envRisk
        })
        """
        
        with self.driver.session() as session:
            session.run(query, locations=locations)
        
        logger.info(f"[OK] Created {len(locations)} locations")
        return locations
    
    def create_location_connections(self, locations: List[Dict]):
        """Create CONNECTED_TO relationships between adjacent locations."""
        logger.info("Creating location connections...")
        
        # Connect locations that are geographically close
        connections = []
        for i, loc1 in enumerate(locations):
            for j, loc2 in enumerate(locations):
                if i >= j:
                    continue
                
                # Calculate distance
                dist = ((loc1["latitude"] - loc2["latitude"])**2 + 
                        (loc1["longitude"] - loc2["longitude"])**2)**0.5
                
                # Connect if close enough (within ~2km in lat/lng terms)
                if dist < 0.03:
                    surveillance = (loc1["policeLevel"] + loc2["policeLevel"]) / 2
                    connections.append({
                        "source": loc1["id"],
                        "target": loc2["id"],
                        "distance": dist * 100,  # Convert to approximate km
                        "surveillanceLevel": surveillance
                    })
        
        query = """
        UNWIND $connections AS conn
        MATCH (l1:Location {id: conn.source}), (l2:Location {id: conn.target})
        CREATE (l1)-[:CONNECTED_TO {
            distance: conn.distance,
            surveillanceLevel: conn.surveillanceLevel
        }]->(l2)
        CREATE (l2)-[:CONNECTED_TO {
            distance: conn.distance,
            surveillanceLevel: conn.surveillanceLevel
        }]->(l1)
        """
        
        with self.driver.session() as session:
            session.run(query, connections=connections)
        
        logger.info(f"[OK] Created {len(connections) * 2} location connections")
    
    def create_citizens(self, num_citizens: int = 100) -> List[Dict]:
        """Create Citizen/Person nodes."""
        logger.info(f"Creating {num_citizens} citizens...")
        
        citizens = []
        for i in range(num_citizens):
            # Generate realistic risk distribution (most people low risk)
            risk_seed = random.betavariate(2, 8)  # Skewed towards low values
            
            citizen = {
                "id": i,
                "name": f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}",
                "born": random.randint(1950, 2005),
                "job": random.choice(JOBS),
                "riskSeed": risk_seed,
                "criminalRecord": 1 if risk_seed > 0.7 else 0,
                "preCrimeRiskScore": risk_seed,
                "embedding": [random.gauss(0, 0.5) for _ in range(16)]
            }
            citizens.append(citizen)
        
        query = """
        UNWIND $citizens AS cit
        CREATE (c:Citizen:Person {
            id: cit.id,
            name: cit.name,
            born: cit.born,
            job: cit.job,
            riskSeed: cit.riskSeed,
            criminalRecord: cit.criminalRecord,
            preCrimeRiskScore: cit.preCrimeRiskScore,
            embedding: cit.embedding
        })
        """
        
        with self.driver.session() as session:
            session.run(query, citizens=citizens)
        
        logger.info(f"[OK] Created {num_citizens} citizens")
        return citizens
    
    def create_social_network(self, citizens: List[Dict], avg_connections: int = 5):
        """Create KNOWS/INTERACTS_WITH relationships between citizens."""
        logger.info("Creating social network...")
        
        edges = []
        seen = set()
        
        for citizen in citizens:
            # Number of connections follows power law
            num_connections = int(random.paretovariate(2.5) * avg_connections / 2)
            num_connections = min(num_connections, len(citizens) - 1, 15)
            
            targets = random.sample(
                [c["id"] for c in citizens if c["id"] != citizen["id"]],
                num_connections
            )
            
            for target in targets:
                edge_key = tuple(sorted([citizen["id"], target]))
                if edge_key not in seen:
                    seen.add(edge_key)
                    edges.append({
                        "source": citizen["id"],
                        "target": target,
                        "weight": random.uniform(0.1, 1.0),
                        "timestamp": random.randint(1609459200, 1735689600)  # 2021-2025
                    })
        
        # Create KNOWS relationships
        query_knows = """
        UNWIND $edges AS edge
        MATCH (c1:Citizen {id: edge.source}), (c2:Citizen {id: edge.target})
        CREATE (c1)-[:KNOWS {weight: edge.weight, since: edge.timestamp}]->(c2)
        """
        
        # Create INTERACTS_WITH relationships (bidirectional as two directed edges)
        query_interacts = """
        UNWIND $edges AS edge
        MATCH (c1:Citizen {id: edge.source}), (c2:Citizen {id: edge.target})
        CREATE (c1)-[:INTERACTS_WITH {weight: edge.weight, timestamp: edge.timestamp}]->(c2)
        CREATE (c2)-[:INTERACTS_WITH {weight: edge.weight, timestamp: edge.timestamp}]->(c1)
        """
        
        with self.driver.session() as session:
            session.run(query_knows, edges=edges)
            session.run(query_interacts, edges=edges)
        
        logger.info(f"[OK] Created {len(edges)} social connections")
    
    def create_citizen_location_visits(self, citizens: List[Dict], locations: List[Dict]):
        """Create VISITS relationships between citizens and locations."""
        logger.info("Creating citizen-location visits...")
        
        visits = []
        for citizen in citizens:
            # Each citizen visits 2-5 locations regularly
            num_visits = random.randint(2, 5)
            visited_locations = random.sample(locations, num_visits)
            
            for loc in visited_locations:
                visits.append({
                    "citizen_id": citizen["id"],
                    "location_id": loc["id"],
                    "frequency": random.uniform(0.1, 1.0)
                })
        
        query = """
        UNWIND $visits AS visit
        MATCH (c:Citizen {id: visit.citizen_id}), (l:Location {id: visit.location_id})
        CREATE (c)-[:VISITS {frequency: visit.frequency}]->(l)
        """
        
        with self.driver.session() as session:
            session.run(query, visits=visits)
        
        logger.info(f"[OK] Created {len(visits)} citizen-location visits")
    
    def calculate_criminal_influence(self):
        """Calculate and update criminal_degree for all citizens."""
        logger.info("Calculating criminal influence...")
        
        query = """
        MATCH (c:Citizen)
        OPTIONAL MATCH (c)-[:KNOWS|INTERACTS_WITH]-(friend)
        WHERE friend.criminalRecord = 1
        WITH c, count(distinct friend) as criminal_friends
        SET c.criminalDegree = criminal_friends,
            c.preCrimeRiskScore = c.riskSeed + (criminal_friends * 0.1)
        RETURN count(c) as updated
        """
        
        with self.driver.session() as session:
            result = session.run(query)
            count = result.single()["updated"]
        
        logger.info(f"[OK] Updated criminal influence for {count} citizens")
    
    def get_stats(self) -> Dict[str, int]:
        """Get database statistics."""
        stats = {}
        
        queries = {
            "citizens": "MATCH (c:Citizen) RETURN count(c) as count",
            "locations": "MATCH (l:Location) RETURN count(l) as count",
            "knows_relations": "MATCH ()-[r:KNOWS]->() RETURN count(r) as count",
            "interacts_relations": "MATCH ()-[r:INTERACTS_WITH]-() RETURN count(r) as count",
            "location_connections": "MATCH ()-[r:CONNECTED_TO]->() RETURN count(r) as count",
            "visits": "MATCH ()-[r:VISITS]->() RETURN count(r) as count"
        }
        
        with self.driver.session() as session:
            for name, query in queries.items():
                result = session.run(query)
                stats[name] = result.single()["count"]
        
        return stats
    
    def seed_all(self, num_citizens: int = 100, clear_first: bool = True):
        """
        Run complete seeding process.
        
        Args:
            num_citizens: Number of citizens to create
            clear_first: Whether to clear existing data first
        """
        logger.info("=" * 60)
        logger.info("  MinorityReport - Neo4j Seed Data")
        logger.info("=" * 60)
        
        try:
            if clear_first:
                self.clear_database()
            
            self.create_constraints()
            locations = self.create_locations()
            self.create_location_connections(locations)
            citizens = self.create_citizens(num_citizens)
            self.create_social_network(citizens)
            self.create_citizen_location_visits(citizens, locations)
            self.calculate_criminal_influence()
            
            logger.info("\n" + "=" * 60)
            logger.info("  Database Statistics")
            logger.info("=" * 60)
            
            stats = self.get_stats()
            for name, count in stats.items():
                logger.info(f"  {name}: {count}")
            
            logger.info("\n[SUCCESS] Database seeded successfully!")
            logger.info("You can now run training with real data.")
            
        except Exception as e:
            logger.error(f"Seeding failed: {e}")
            raise
        finally:
            self.close()


def seed_neo4j(
    num_citizens: int = 100,
    clear_first: bool = True,
    uri: str = None,
    user: str = None,
    password: str = None
) -> bool:
    """
    Convenience function to seed Neo4j.
    
    Args:
        num_citizens: Number of citizens to create
        clear_first: Clear existing data first
        uri, user, password: Neo4j connection parameters
        
    Returns:
        True if successful
    """
    try:
        seeder = Neo4jSeeder(uri, user, password)
        seeder.seed_all(num_citizens, clear_first)
        return True
    except Exception as e:
        logger.error(f"Failed to seed database: {e}")
        return False


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Seed Neo4j with sample data")
    parser.add_argument("--citizens", type=int, default=100, help="Number of citizens")
    parser.add_argument("--no-clear", action="store_true", help="Don't clear existing data")
    parser.add_argument("--uri", type=str, help="Neo4j URI")
    parser.add_argument("--user", type=str, help="Neo4j username")
    parser.add_argument("--password", type=str, help="Neo4j password")
    
    args = parser.parse_args()
    
    success = seed_neo4j(
        num_citizens=args.citizens,
        clear_first=not args.no_clear,
        uri=args.uri,
        user=args.user,
        password=args.password
    )
    
    exit(0 if success else 1)
