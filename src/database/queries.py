from typing import List, Dict, Any
from .neo4j_client import db
from .schema_models import NodeLabel, RelationshipType, EdgeProperty, NodeProperty

def get_neighborhood(node_id: str, hops: int = 2) -> List[Dict[str, Any]]:
    """
    Retrieves the neighborhood of a node up to 'hops' distance.
    Useful for GCN (Graph Convolutional Networks) context aggregation.
    
    Args:
        node_id: The UID of the center node.
        hops: Number of hops to traverse.
    
    Returns:
        List of paths or subgraph data.
    """
    query = f"""
    MATCH path = (start:{NodeLabel.LOCATION} {{ {NodeProperty.ID}: $node_id }})-[*1..{hops}]-(neighbor)
    RETURN path
    """
    params = {"node_id": node_id}
    return db.execute_query(query, params)

def find_safe_path(start_id: str, end_id: str) -> List[Dict[str, Any]]:
    """
    Finds the path with the minimal accumulated risk using Dijkstra-like logic 
    (via APOC or standard Cypher reduction if APOC not available, though we configured APOC).
    
    This implementation uses standard Cypher's `shortestPath` weighted by risk 
    simulated by filtering or creating a custom reduction if complexity is high.
    
    For GAT, we ideally want to extract the subgraph and let the Python model decide,
    but this provides a baseline 'heuristically safe' path from DB.
    """
    
    # Using APOC for weighted shortest path if available is best.
    # Here we use a standard approach finding multiple paths and sorting by total risk.
    query = f"""
    MATCH p = (start:{NodeLabel.LOCATION} {{ {NodeProperty.ID}: $start_id }})-[:{RelationshipType.CONNECTED_TO}*..10]-(end:{NodeLabel.LOCATION} {{ {NodeProperty.ID}: $end_id }})
    WITH p, 
         reduce(risk = 0.0, r IN relationships(p) | risk + COALESCE(r.{EdgeProperty.RISK_LEVEL}, 0)) AS total_risk
    ORDER BY total_risk ASC
    LIMIT 1
    RETURN p, total_risk
    """
    params = {"start_id": start_id, "end_id": end_id}
    return db.execute_query(query, params)

def clear_database():
    """Danger: Clears the entire database."""
    query = "MATCH (n) DETACH DELETE n"
    return db.execute_query(query)
