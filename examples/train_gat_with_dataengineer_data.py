"""
Example: Train GAT Model with Data from dataEngineer Branch

This script demonstrates how to:
1. Load data exported from Neo4j (dataEngineer branch)
2. Train a Graph Attention Network (GAT) model
3. Evaluate the model's performance

Usage:
    # Using exported data:
    python examples/train_gat_with_dataengineer_data.py --data data/ --epochs 100
    
    # Using live Neo4j connection:
    python examples/train_gat_with_dataengineer_data.py --live --epochs 100
"""

import argparse
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import torch
import torch.nn.functional as F
from torch_geometric.nn import GATConv
from torch_geometric.data import Data
import logging

from src.utils.data_loader import load_exported_data
from src.utils.neo4j_data_fetcher import fetch_graph_data

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SimpleGAT(torch.nn.Module):
    """
    Simple Graph Attention Network for risk prediction.
    
    This is a basic GAT implementation for demonstration.
    You can enhance it with:
    - More layers
    - Different attention heads
    - Dropout for regularization
    - Batch normalization
    """
    
    def __init__(self, in_channels, hidden_channels, out_channels, heads=4):
        super(SimpleGAT, self).__init__()
        
        # First GAT layer with multiple attention heads
        self.conv1 = GATConv(in_channels, hidden_channels, heads=heads, dropout=0.6)
        
        # Second GAT layer (reduce to single head)
        self.conv2 = GATConv(hidden_channels * heads, out_channels, heads=1, 
                            concat=False, dropout=0.6)
    
    def forward(self, x, edge_index):
        """
        Forward pass through the GAT network.
        
        Args:
            x: Node features [num_nodes, in_channels]
            edge_index: Graph connectivity [2, num_edges]
        
        Returns:
            predictions: Node predictions [num_nodes, out_channels]
        """
        # First GAT layer + ELU activation
        x = F.dropout(x, p=0.6, training=self.training)
        x = self.conv1(x, edge_index)
        x = F.elu(x)
        
        # Second GAT layer
        x = F.dropout(x, p=0.6, training=self.training)
        x = self.conv2(x, edge_index)
        
        return x


def train_epoch(model, data, optimizer, criterion, device):
    """
    Train for one epoch.
    
    Args:
        model: GAT model
        data: PyTorch Geometric Data object
        optimizer: Optimizer
        criterion: Loss function
        device: torch device
    
    Returns:
        loss: Training loss
    """
    model.train()
    optimizer.zero_grad()
    
    # Forward pass
    out = model(data.x.to(device), data.edge_index.to(device))
    loss = criterion(out, data.y.to(device))
    
    # Backward pass
    loss.backward()
    optimizer.step()
    
    return loss.item()


@torch.no_grad()
def evaluate(model, data, criterion, device):
    """
    Evaluate model on the data.
    
    Args:
        model: GAT model
        data: PyTorch Geometric Data object
        criterion: Loss function
        device: torch device
    
    Returns:
        loss: Evaluation loss
        mae: Mean Absolute Error
    """
    model.eval()
    
    out = model(data.x.to(device), data.edge_index.to(device))
    loss = criterion(out, data.y.to(device))
    mae = F.l1_loss(out, data.y.to(device))
    
    return loss.item(), mae.item()


def train_gat_model(data: Data, epochs: int = 100, lr: float = 0.005, 
                    hidden_channels: int = 64, heads: int = 4):
    """
    Train a GAT model on the graph data.
    
    Args:
        data: PyTorch Geometric Data object
        epochs: Number of training epochs
        lr: Learning rate
        hidden_channels: Hidden layer size
        heads: Number of attention heads
    
    Returns:
        model: Trained GAT model
    """
    # Setup device
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    logger.info(f"🖥️  Using device: {device}")
    
    # Create model
    model = SimpleGAT(
        in_channels=data.num_features,
        hidden_channels=hidden_channels,
        out_channels=1,  # Single output for risk prediction
        heads=heads
    ).to(device)
    
    logger.info(f"🧠 Model: {sum(p.numel() for p in model.parameters())} parameters")
    
    # Setup training
    optimizer = torch.optim.Adam(model.parameters(), lr=lr, weight_decay=5e-4)
    criterion = torch.nn.MSELoss()
    
    # Training loop
    logger.info(f"🚀 Starting training for {epochs} epochs...")
    best_loss = float('inf')
    
    for epoch in range(1, epochs + 1):
        # Train
        train_loss = train_epoch(model, data, optimizer, criterion, device)
        
        # Evaluate
        eval_loss, mae = evaluate(model, data, criterion, device)
        
        # Track best model
        if eval_loss < best_loss:
            best_loss = eval_loss
            best_epoch = epoch
        
        # Log progress
        if epoch % 10 == 0 or epoch == 1:
            logger.info(f"Epoch {epoch:3d} | Train Loss: {train_loss:.6f} | "
                       f"Eval Loss: {eval_loss:.6f} | MAE: {mae:.6f}")
    
    logger.info(f"✅ Training complete! Best loss: {best_loss:.6f} at epoch {best_epoch}")
    
    return model


def main():
    parser = argparse.ArgumentParser(
        description="Train GAT model with data from dataEngineer branch"
    )
    parser.add_argument(
        "--data", "-d",
        type=str,
        default="data",
        help="Directory with exported data (default: data/)"
    )
    parser.add_argument(
        "--live",
        action="store_true",
        help="Use live Neo4j connection instead of exported data"
    )
    parser.add_argument(
        "--epochs", "-e",
        type=int,
        default=100,
        help="Number of training epochs (default: 100)"
    )
    parser.add_argument(
        "--lr",
        type=float,
        default=0.005,
        help="Learning rate (default: 0.005)"
    )
    parser.add_argument(
        "--hidden",
        type=int,
        default=64,
        help="Hidden layer size (default: 64)"
    )
    parser.add_argument(
        "--heads",
        type=int,
        default=4,
        help="Number of attention heads (default: 4)"
    )
    parser.add_argument(
        "--save",
        type=str,
        help="Path to save trained model"
    )
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("GAT Training with dataEngineer Data")
    print("=" * 60)
    
    # Load data
    if args.live:
        logger.info("🔌 Loading data from live Neo4j connection...")
        data = fetch_graph_data()
    else:
        logger.info(f"📂 Loading data from {args.data}...")
        data = load_exported_data(args.data)
    
    if data is None:
        logger.error("❌ Failed to load data!")
        if not args.live:
            logger.error("   Run: python scripts/export_data_from_neo4j.py")
        return
    
    logger.info(f"✅ Loaded: {data.num_nodes} nodes, {data.num_edges} edges, "
               f"{data.num_features} features")
    
    # Train model
    model = train_gat_model(
        data,
        epochs=args.epochs,
        lr=args.lr,
        hidden_channels=args.hidden,
        heads=args.heads
    )
    
    # Save model if requested
    if args.save:
        torch.save({
            'model_state_dict': model.state_dict(),
            'num_features': data.num_features,
            'hidden_channels': args.hidden,
            'heads': args.heads
        }, args.save)
        logger.info(f"💾 Model saved to {args.save}")
    
    print("\n" + "=" * 60)
    print("✅ Training completed successfully!")
    print("=" * 60)
    print(f"\nModel trained on:")
    print(f"  Nodes:    {data.num_nodes}")
    print(f"  Edges:    {data.num_edges}")
    print(f"  Features: {data.num_features}")
    print(f"\nArchitecture:")
    print(f"  Hidden:   {args.hidden}")
    print(f"  Heads:    {args.heads}")
    print(f"  Epochs:   {args.epochs}")


if __name__ == "__main__":
    main()
