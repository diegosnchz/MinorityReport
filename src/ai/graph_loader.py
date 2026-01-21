import torch
from torch_geometric.data import Data
from src.database.neo4j_client import db
from src.database.schema_models import NodeLabel, RelationshipType, EdgeProperty, NodeProperty
import logging

logger = logging.getLogger(__name__)

def load_graph_from_neo4j():
    """
    Fetches the entire city topology from Neo4j and converts it into a 
    PyTorch Geometric Data object for GNN processing.
    """
    logger.info("⚡ Fetching graph data from Neo4j...")
    
    # 1. Fetch All Location Nodes
    # We map UID strings to Integer Indices (0, 1, 2...) for PyTorch
    query_nodes = f"""
    MATCH (n:{NodeLabel.LOCATION.value})
    RETURN n.{NodeProperty.ID.value} as uid, 
           n.{NodeProperty.X.value} as x, 
           n.{NodeProperty.Y.value} as y,
           labels(n) as labels
    """
    nodes_result = db.execute_query(query_nodes)
    
    node_to_idx = {}
    features = []
    
    for idx, record in enumerate(nodes_result):
        uid = record['uid']
        node_to_idx[uid] = idx
        
        # Feature Engineering: [X, Y, IsHideout]
        # In a real scenario, we might normalize coordinates.
        is_hideout = 1.0 if NodeLabel.HIDEOUT.value in record['labels'] else 0.0
        x_coord = float(record['x'])
        y_coord = float(record['y'])
        
        features.append([x_coord, y_coord, is_hideout])
    
    x = torch.tensor(features, dtype=torch.float)
    
    # 2. Fetch All Edges
    query_edges = f"""
    MATCH (a:{NodeLabel.LOCATION.value})-[r:{RelationshipType.CONNECTED_TO.value}]->(b:{NodeLabel.LOCATION.value})
    RETURN a.{NodeProperty.ID.value} as source, 
           b.{NodeProperty.ID.value} as target, 
           r.{EdgeProperty.RISK_LEVEL.value} as risk,
           r.{EdgeProperty.DISTANCE.value} as dist
    """
    edges_result = db.execute_query(query_edges)
    
    edge_sources = []
    edge_targets = []
    edge_attrs = []
    
    for record in edges_result:
        u = record['source']
        v = record['target']
        
        if u in node_to_idx and v in node_to_idx:
            edge_sources.append(node_to_idx[u])
            edge_targets.append(node_to_idx[v])
            
            # Edge Features: [Risk, Distance]
            edge_attrs.append([float(record['risk']), float(record['dist'])])
            
    edge_index = torch.tensor([edge_sources, edge_targets], dtype=torch.long)
    edge_attr = torch.tensor(edge_attrs, dtype=torch.float)
    
    data = Data(x=x, edge_index=edge_index, edge_attr=edge_attr)
    data.node_map = {idx: uid for uid, idx in node_to_idx.items()} # Save mapping to reverse lookup later
    
    logger.info(f"✅ Graph Loaded: {data.num_nodes} Nodes, {data.num_edges} Edges.")
    return data
