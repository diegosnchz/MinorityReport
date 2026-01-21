import torch
import pandas as pd
import logging
from typing import Tuple
from neo4j import Driver
from torch_geometric.data import Data
from src.database.neo4j_client import Neo4jClient

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_driver() -> Driver:
    """Retrieves the driver from the Singleton Neo4jClient."""
    client = Neo4jClient()
    client.verify_connection()
    return client._driver

def calculate_criminal_influence(driver: Driver):
    """
    Step 1: Metric Calculation (In-Graph).
    Updates Citizen nodes with 'criminal_degree'.
    """
    logger.info("💧 Hydrating: Calculating criminal influence from environment...")
    query = """
    MATCH (c:Citizen)
    OPTIONAL MATCH (c)-[:KNOWS]-(friend)-[:COMMITTED_CRIME]->()
    WITH c, count(distinct friend) as criminal_friends
    SET c.criminal_degree = criminal_friends
    RETURN count(c) as count
    """
    try:
        with driver.session() as session:
            result = session.run(query)
            count = result.single()["count"]
            logger.info(f"✅ {count} nodes updated with 'criminal_degree'.")
    except Exception as e:
        logger.error(f"Failed to calculate criminal influence: {e}")
        raise

def extract_features_to_pandas(driver: Driver) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Step 2: Vectorization (Python/Pandas).
    Extracts raw data and performs One-Hot Encoding and Normalization.
    """
    logger.info("📊 Extracting data for vectorization...")
    query = """
    MATCH (c:Citizen)
    RETURN c.id as id, c.born as born, c.job as job, c.criminal_degree as crim_deg, 
           c.risk_seed as target
    ORDER BY c.id ASC
    """
    # Note: ORDER BY c.id ASC is crucial to ensure consistent improved mapping later if IDs are integers
    
    with driver.session() as session:
        result = session.run(query)
        data = [r.data() for r in result]
    
    if not data:
        logger.warning("No data found in Neo4j!")
        return pd.DataFrame(), pd.DataFrame()

    df = pd.DataFrame(data)
    
    # Age Normalization
    current_year = 2026
    # Handle possible strings or ints in 'born'
    df['born'] = pd.to_numeric(df['born'], errors='coerce').fillna(current_year)
    df['age'] = (current_year - df['born']) / 100.0
    
    # One-Hot Encoding of Jobs
    job_dummies = pd.get_dummies(df['job'], prefix='job')
    # Handle boolean columns from get_dummies if any (modern pandas) - ensure 0/1 ints
    job_dummies = job_dummies.astype(int)
    
    df_processed = pd.concat([df, job_dummies], axis=1)
    
    # Cleanup: Drop non-numeric/raw columns to keep only features
    # Keeping 'crim_deg', 'age', and all 'job_*' columns
    drop_cols = ['born', 'job', 'target', 'id']
    features = df_processed.drop(columns=drop_cols)
    
    logger.info(f"✅ Features processed. Tensor dimensions: {features.shape}")
    return df, features

def load_graph_to_pyg(driver: Driver, features_df: pd.DataFrame, full_df: pd.DataFrame) -> Data:
    """
    Step 3: PyTorch Geometric Assembly.
    Constructs the Data object.
    """
    logger.info("🚀 Building PyTorch Geometric object...")
    
    if features_df.empty:
        raise ValueError("Features DataFrame is empty. Cannot build graph.")

    # 1. Create Feature Tensor (X)
    x = torch.tensor(features_df.values, dtype=torch.float)
    
    # 2. Create Label Tensor (Y) - risk_seed
    y = torch.tensor(full_df['target'].values, dtype=torch.float).view(-1, 1)
    
    # 3. Extract Topology (Edge Index)
    # We need to map Neo4j IDs to 0..N indices.
    # Since we sorted by c.id ASC in extract_features and assuming c.id are 0..999 from seed script:
    # We can perform a direct mapping if IDs are contiguous integers from 0. 
    # But to be safe, we should create a mapping.
    
    id_to_index = {uid: idx for idx, uid in enumerate(full_df['id'])}
    
    edge_query = """
    MATCH (c1:Citizen)-[:KNOWS]->(c2:Citizen)
    RETURN c1.id as source, c2.id as target
    """
    
    with driver.session() as session:
        result = session.run(edge_query)
        # Verify IDs exist in our mapping (loaded set)
        edges = []
        for r in result:
            src, tgt = r['source'], r['target']
            if src in id_to_index and tgt in id_to_index:
                edges.append((id_to_index[src], id_to_index[tgt]))
    
    if not edges:
        logger.warning("No relationships found! Creating graph with empty edges.")
        edge_index = torch.empty((2, 0), dtype=torch.long)
    else:
        # PyG requires shape [2, num_edges]
        edge_index = torch.tensor(edges, dtype=torch.long).t().contiguous()
    
    # 4. Assembly
    data = Data(x=x, edge_index=edge_index, y=y)
    
    logger.info(f"✨ Graph loaded into memory:")
    logger.info(f" - Nodes: {data.num_nodes}")
    logger.info(f" - Edges: {data.num_edges}")
    logger.info(f" - Features per node: {data.num_node_features}")
    
    return data

def main():
    """Main execution function for standalone testing."""
    try:
        driver = get_driver()
        
        # Step 1
        calculate_criminal_influence(driver)
        
        # Step 2
        df_full, df_features = extract_features_to_pandas(driver)
        
        # Step 3
        if not df_full.empty:
            graph_data = load_graph_to_pyg(driver, df_features, df_full)
            print("Graph Data Object Created Successfully.")
            print(graph_data)
        
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")

if __name__ == "__main__":
    main()
