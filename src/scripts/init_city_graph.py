import random
import uuid
import logging
from src.database.neo4j_client import db
from src.database.schema_models import NodeLabel, RelationshipType, EdgeProperty, NodeProperty
from src.database.queries import clear_database

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def generate_city_grid(rows: int = 5, cols: int = 5):
    """
    Generates a grid-based city topology.
    - Creates Location nodes.
    - Connects adjacent nodes with CONNECTED_TO relationships.
    - Assigns random risk levels.
    """
    logger.info("🌱 Starting City Seeding...")
    
    try:
        # 1. Clear existing data
        clear_database()
        logger.info("🧹 Database cleared.")

        locations = {}
        
        # 2. Create Nodes
        query_create_node = f"""
        CREATE (n:{NodeLabel.LOCATION.value} {{
            {NodeProperty.ID.value}: $uid,
            {NodeProperty.X.value}: $x,
            {NodeProperty.Y.value}: $y,
            {NodeProperty.NAME.value}: $name
        }})
        """
        
        for r in range(rows):
            for c in range(cols):
                uid = str(uuid.uuid4())
                name = f"Street-{r}-{c}"
                
                # Check for special locations (Hideouts)
                if (r, c) in [(0, 0), (rows-1, cols-1)]:
                    # Create Hideout instead of simple Location just for marking or add secondary label
                    # For simplicity, we add a generic Location but could add extra label later.
                    pass 

                db.execute_query(query_create_node, {
                    "uid": uid,
                    "x": r,
                    "y": c,
                    "name": name
                })
                locations[(r, c)] = uid
        
        logger.info(f"✅ Created {rows*cols} locations.")

        # 3. Create Relationships (Grid Edges)
        query_create_edge = f"""
        MATCH (a:{NodeLabel.LOCATION.value} {{ {NodeProperty.ID.value}: $id_a }})
        MATCH (b:{NodeLabel.LOCATION.value} {{ {NodeProperty.ID.value}: $id_b }})
        CREATE (a)-[:{RelationshipType.CONNECTED_TO.value} {{
            {EdgeProperty.DISTANCE.value}: 1,
            {EdgeProperty.RISK_LEVEL.value}: $risk
        }}]->(b)
        """
        
        edges_count = 0
        for r in range(rows):
            for c in range(cols):
                current_id = locations[(r, c)]
                
                # Check neighbors (Right and Down to avoid duplicates in undirected grid)
                neighbors = []
                if c + 1 < cols: neighbors.append((r, c + 1)) # Right
                if r + 1 < rows: neighbors.append((r + 1, c)) # Down
                
                for nr, nc in neighbors:
                    neighbor_id = locations[(nr, nc)]
                    
                    # Random Risk: 10% chance of high risk (Police Checkpoint)
                    risk = round(random.uniform(0.7, 0.9), 2) if random.random() < 0.1 else round(random.uniform(0.0, 0.2), 2)
                    
                    db.execute_query(query_create_edge, {
                        "id_a": current_id,
                        "id_b": neighbor_id,
                        "risk": risk
                    })
                    edges_count += 1
        
        logger.info(f"✅ Created {edges_count} connections.")
        
        # 4. Create Special Nodes (Hideouts)
        # Convert some existing random nodes to Hideouts or create new ones linked
        hideout_query = f"""
        MATCH (n:{NodeLabel.LOCATION.value}) 
        WITH n ORDER BY rand() LIMIT 2
        SET n:{NodeLabel.HIDEOUT.value}
        RETURN n.{NodeProperty.NAME.value} as name
        """
        hideouts = db.execute_query(hideout_query)
        logger.info(f"🕵️ Designated Hideouts: {[h['name'] for h in hideouts]}")
        
    except Exception as e:
        logger.error(f"❌ Seeding failed: {e}")
        raise

if __name__ == "__main__":
    # Wait for DB to be ready if running immediately after docker-compose up
    try:
        generate_city_grid()
    except Exception:
        logger.info("Waiting for DB...")
        import time
        time.sleep(5)
        # Retry once
        generate_city_grid()
