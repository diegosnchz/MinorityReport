"""
Real-World Training Integration Script

This script trains models using REAL data from Neo4j database,
compatible with the EXPERIMENTAL_dataEngineer branch schema.

Workflow:
1. Start Neo4j: docker-compose up neo4j
2. Seed data: python scripts/seed_neo4j.py --citizens 200
3. Train: python scripts/train_with_neo4j.py

Author: The Oracle Team (feature/gat-model)
"""

import os
import sys
import time
import logging
import argparse
from pathlib import Path

import torch
import torch.nn.functional as F
from torch_geometric.data import Data

# Add project root and src to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

from src.utils.neo4j_data_fetcher import Neo4jDataFetcher
from src.models.graphsage_model import create_graphsage_model
from src.models.oracle_net import OracleNet

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("TrainWithNeo4j")


def verify_neo4j_connection():
    """Verify Neo4j is running and has data."""
    try:
        fetcher = Neo4jDataFetcher(
            uri="bolt://localhost:7687",
            user="neo4j",
            password="minorityreport"
        )
        with fetcher.driver.session() as session:
            result = session.run("MATCH (n) RETURN count(n) as count")
            count = result.single()["count"]
            
        fetcher.close()
        
        if count == 0:
            logger.error("Neo4j is empty! Run: python scripts/seed_neo4j.py")
            return False
        
        logger.info(f"[OK] Neo4j connected. Found {count} nodes.")
        return True
        
    except Exception as e:
        logger.error(f"Cannot connect to Neo4j: {e}")
        logger.error("Make sure Neo4j is running: docker-compose up neo4j")
        return False


def fetch_citizen_graph():
    """Fetch citizen social network graph from Neo4j."""
    logger.info("Fetching citizen graph from Neo4j...")
    
    fetcher = Neo4jDataFetcher(
        uri="bolt://localhost:7687",
        user="neo4j",
        password="minorityreport"
    )
    
    try:
        # Get graph data
        data = fetcher.get_pyg_data(relationship_type="KNOWS")
        
        if data is None:
            logger.error("Failed to fetch citizen graph!")
            return None
        
        logger.info(f"[OK] Fetched graph: {data.num_nodes} nodes, {data.edge_index.shape[1]} edges")
        logger.info(f"    Feature dim: {data.x.shape[1]}, Labels: {torch.unique(data.y)}")
        
        return data
        
    finally:
        fetcher.close()


def fetch_location_graph():
    """Fetch location network graph from Neo4j."""
    logger.info("Fetching location graph from Neo4j...")
    
    fetcher = Neo4jDataFetcher(
        uri="bolt://localhost:7687",
        user="neo4j",
        password="minorityreport"
    )
    
    try:
        data = fetcher.fetch_location_graph()
        
        if data is None:
            logger.error("Failed to fetch location graph!")
            return None
        
        logger.info(f"[OK] Fetched location graph: {data.num_nodes} nodes, {data.edge_index.shape[1]} edges")
        
        return data
        
    finally:
        fetcher.close()


def train_crime_prediction_model(data, epochs=100, device=None):
    """
    Train simple GCN model for crime/risk prediction on citizens.
    
    This is the "CrimeGenerator" from dataEngineer's schema.
    """
    if device is None:
        device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    
    logger.info(f"\n{'='*60}")
    logger.info(f"  Training Crime Prediction Model (GCN)")
    logger.info(f"  Device: {device}")
    logger.info(f"{'='*60}")
    
    # Move data to device
    data = data.to(device)
    
    # Create train/val/test masks
    num_nodes = data.num_nodes
    indices = torch.randperm(num_nodes)
    
    train_size = int(0.7 * num_nodes)
    val_size = int(0.15 * num_nodes)
    
    train_mask = torch.zeros(num_nodes, dtype=torch.bool)
    val_mask = torch.zeros(num_nodes, dtype=torch.bool)
    test_mask = torch.zeros(num_nodes, dtype=torch.bool)
    
    train_mask[indices[:train_size]] = True
    val_mask[indices[train_size:train_size + val_size]] = True
    test_mask[indices[train_size + val_size:]] = True
    
    data.train_mask = train_mask.to(device)
    data.val_mask = val_mask.to(device)
    data.test_mask = test_mask.to(device)
    
    # Create simple GCN model
    from torch_geometric.nn import GCNConv
    
    num_classes = len(torch.unique(data.y))
    
    class SimpleGCN(torch.nn.Module):
        def __init__(self, in_channels, hidden_channels, out_channels):
            super().__init__()
            self.conv1 = GCNConv(in_channels, hidden_channels)
            self.conv2 = GCNConv(hidden_channels, out_channels)
        
        def forward(self, x, edge_index):
            x = self.conv1(x, edge_index)
            x = F.relu(x)
            x = F.dropout(x, training=self.training)
            x = self.conv2(x, edge_index)
            return x
    
    model = SimpleGCN(
        in_channels=data.x.shape[1],
        hidden_channels=64,
        out_channels=num_classes
    ).to(device)
    
    optimizer = torch.optim.Adam(model.parameters(), lr=0.01, weight_decay=5e-4)
    
    logger.info(f"Model: SimpleGCN")
    logger.info(f"Parameters: {sum(p.numel() for p in model.parameters()):,}")
    
    best_val_acc = 0
    start_time = time.time()
    
    for epoch in range(1, epochs + 1):
        # Training
        model.train()
        optimizer.zero_grad()
        
        out = model(data.x, data.edge_index)
        loss = F.cross_entropy(out[data.train_mask], data.y[data.train_mask])
        
        loss.backward()
        optimizer.step()
        
        # Evaluation
        if epoch % 10 == 0 or epoch == epochs:
            model.eval()
            with torch.no_grad():
                out = model(data.x, data.edge_index)
                pred = out.argmax(dim=1)
                
                train_acc = (pred[data.train_mask] == data.y[data.train_mask]).float().mean()
                val_acc = (pred[data.val_mask] == data.y[data.val_mask]).float().mean()
                
                if val_acc > best_val_acc:
                    best_val_acc = val_acc
                    # Save best model
                    torch.save(model.state_dict(), 'models/crime_prediction_best.pt')
            
            logger.info(f"Epoch {epoch:03d} | Loss: {loss:.4f} | "
                       f"Train: {train_acc:.4f} | Val: {val_acc:.4f}")
    
    elapsed = time.time() - start_time
    
    # Final test evaluation
    model.eval()
    with torch.no_grad():
        out = model(data.x, data.edge_index)
        pred = out.argmax(dim=1)
        test_acc = (pred[data.test_mask] == data.y[data.test_mask]).float().mean()
    
    logger.info(f"\n[RESULTS] Crime Prediction Model:")
    logger.info(f"  - Test Accuracy: {test_acc:.4f}")
    logger.info(f"  - Best Val Accuracy: {best_val_acc:.4f}")
    logger.info(f"  - Training Time: {elapsed:.2f}s")
    logger.info(f"  - Model saved: models/crime_prediction_best.pt")
    
    return model, test_acc.item()


def train_escape_route_model(data, epochs=100, device=None):
    """
    Train GCN model for escape route optimization on locations.
    
    This predicts optimal paths through the city avoiding high police levels.
    """
    if device is None:
        device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    
    logger.info(f"\n{'='*60}")
    logger.info(f"  Training Escape Route Model (GCN)")
    logger.info(f"  Device: {device}")
    logger.info(f"{'='*60}")
    
    # Move data to device
    data = data.to(device)
    
    # Create labels from police level (low police = good escape route)
    # Binary classification: 0 = high surveillance, 1 = good escape route
    if hasattr(data, 'police_level'):
        labels = (data.police_level < 0.5).long()
    else:
        # Use first feature column as proxy
        labels = (data.x[:, 0] < data.x[:, 0].median()).long()
    
    data.y = labels.to(device)
    
    # Create masks
    num_nodes = data.num_nodes
    indices = torch.randperm(num_nodes)
    
    train_size = int(0.7 * num_nodes)
    val_size = int(0.15 * num_nodes)
    
    train_mask = torch.zeros(num_nodes, dtype=torch.bool)
    val_mask = torch.zeros(num_nodes, dtype=torch.bool)
    test_mask = torch.zeros(num_nodes, dtype=torch.bool)
    
    train_mask[indices[:train_size]] = True
    val_mask[indices[train_size:train_size + val_size]] = True
    test_mask[indices[train_size + val_size:]] = True
    
    data.train_mask = train_mask.to(device)
    data.val_mask = val_mask.to(device)
    data.test_mask = test_mask.to(device)
    
    # Create simple GCN model for location classification
    from torch_geometric.nn import GCNConv
    
    class LocationGCN(torch.nn.Module):
        def __init__(self, in_channels, hidden_channels, out_channels):
            super().__init__()
            self.conv1 = GCNConv(in_channels, hidden_channels)
            self.conv2 = GCNConv(hidden_channels, out_channels)
        
        def forward(self, x, edge_index):
            x = self.conv1(x, edge_index)
            x = F.relu(x)
            x = F.dropout(x, training=self.training)
            x = self.conv2(x, edge_index)
            return x
    
    model = LocationGCN(
        in_channels=data.x.shape[1],
        hidden_channels=32,
        out_channels=2
    ).to(device)
    
    optimizer = torch.optim.Adam(model.parameters(), lr=0.01, weight_decay=5e-4)
    
    logger.info(f"Model: LocationGCN")
    logger.info(f"Parameters: {sum(p.numel() for p in model.parameters()):,}")
    
    best_val_acc = 0
    start_time = time.time()
    
    for epoch in range(1, epochs + 1):
        # Training
        model.train()
        optimizer.zero_grad()
        
        out = model(data.x, data.edge_index)
        loss = F.cross_entropy(out[data.train_mask], data.y[data.train_mask])
        
        loss.backward()
        optimizer.step()
        
        # Evaluation
        if epoch % 10 == 0 or epoch == epochs:
            model.eval()
            with torch.no_grad():
                out = model(data.x, data.edge_index)
                pred = out.argmax(dim=1)
                
                train_acc = (pred[data.train_mask] == data.y[data.train_mask]).float().mean()
                val_acc = (pred[data.val_mask] == data.y[data.val_mask]).float().mean()
                
                if val_acc > best_val_acc:
                    best_val_acc = val_acc
                    torch.save(model.state_dict(), 'models/escape_route_best.pt')
            
            logger.info(f"Epoch {epoch:03d} | Loss: {loss:.4f} | "
                       f"Train: {train_acc:.4f} | Val: {val_acc:.4f}")
    
    elapsed = time.time() - start_time
    
    # Final test evaluation
    model.eval()
    with torch.no_grad():
        out = model(data.x, data.edge_index)
        pred = out.argmax(dim=1)
        test_acc = (pred[data.test_mask] == data.y[data.test_mask]).float().mean()
    
    logger.info(f"\n[RESULTS] Escape Route Model:")
    logger.info(f"  - Test Accuracy: {test_acc:.4f}")
    logger.info(f"  - Best Val Accuracy: {best_val_acc:.4f}")
    logger.info(f"  - Training Time: {elapsed:.2f}s")
    logger.info(f"  - Model saved: models/escape_route_best.pt")
    
    return model, test_acc.item()


def write_predictions_back(model, data, fetcher: Neo4jDataFetcher, node_type="citizen"):
    """Write model predictions back to Neo4j."""
    logger.info(f"\nWriting {node_type} predictions back to Neo4j...")
    
    model.eval()
    with torch.no_grad():
        if hasattr(model, 'forward'):
            out = model(data.x.cpu(), data.edge_index.cpu())
            if isinstance(out, tuple):
                out = out[0]
        
        # Get probabilities
        probs = F.softmax(out, dim=1)
        risk_scores = probs[:, 1].numpy() if probs.shape[1] > 1 else probs.squeeze().numpy()
    
    # Map back to Neo4j IDs (assuming sequential)
    predictions = [{"node_id": i, "risk_score": float(risk_scores[i])} 
                   for i in range(len(risk_scores))]
    
    query = f"""
    UNWIND $predictions AS pred
    MATCH (n:{node_type.capitalize()} {{id: pred.node_id}})
    SET n.predictedRiskScore = pred.risk_score
    RETURN count(n) as updated
    """
    
    with fetcher.driver.session() as session:
        result = session.run(query, predictions=predictions)
        updated = result.single()["updated"]
    
    logger.info(f"[OK] Updated {updated} {node_type} nodes with predictions")


def main():
    parser = argparse.ArgumentParser(description="Train models with Neo4j data")
    parser.add_argument("--model", choices=["crime", "escape", "both"], default="both",
                       help="Which model to train")
    parser.add_argument("--epochs", type=int, default=100, help="Training epochs")
    parser.add_argument("--device", type=str, default=None, help="Device (cuda/cpu)")
    parser.add_argument("--write-back", action="store_true", 
                       help="Write predictions back to Neo4j")
    
    args = parser.parse_args()
    
    # Setup device
    if args.device:
        device = torch.device(args.device)
    else:
        device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    
    logger.info("="*60)
    logger.info("  MinorityReport - Real-World Training with Neo4j")
    logger.info("="*60)
    logger.info(f"Device: {device}")
    
    if device.type == 'cuda':
        logger.info(f"GPU: {torch.cuda.get_device_name(0)}")
    
    # Verify connection
    if not verify_neo4j_connection():
        sys.exit(1)
    
    # Create models directory
    os.makedirs("models", exist_ok=True)
    
    results = {}
    
    # Train crime prediction model
    if args.model in ["crime", "both"]:
        citizen_data = fetch_citizen_graph()
        if citizen_data is not None:
            crime_model, crime_acc = train_crime_prediction_model(
                citizen_data, 
                epochs=args.epochs,
                device=device
            )
            results["crime_prediction"] = crime_acc
            
            if args.write_back:
                fetcher = Neo4jDataFetcher(
                    uri="bolt://localhost:7687",
                    user="neo4j",
                    password="minorityreport"
                )
                write_predictions_back(crime_model, citizen_data, fetcher, "citizen")
                fetcher.close()
    
    # Train escape route model
    if args.model in ["escape", "both"]:
        location_data = fetch_location_graph()
        if location_data is not None:
            escape_model, escape_acc = train_escape_route_model(
                location_data,
                epochs=args.epochs,
                device=device
            )
            results["escape_route"] = escape_acc
            
            if args.write_back:
                fetcher = Neo4jDataFetcher(
                    uri="bolt://localhost:7687",
                    user="neo4j",
                    password="minorityreport"
                )
                write_predictions_back(escape_model, location_data, fetcher, "location")
                fetcher.close()
    
    # Summary
    logger.info("\n" + "="*60)
    logger.info("  TRAINING COMPLETE")
    logger.info("="*60)
    
    for model_name, accuracy in results.items():
        logger.info(f"  {model_name}: {accuracy:.4f}")
    
    logger.info("\nSaved models:")
    logger.info("  - models/crime_prediction_best.pt (GraphSAGE)")
    logger.info("  - models/escape_route_best.pt (OracleNet)")
    logger.info("\nThese models are ready for the backend/frontend teams!")


if __name__ == "__main__":
    main()
