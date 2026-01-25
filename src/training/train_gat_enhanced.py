"""
Enhanced Training Script for GAT Models with dataEngineer Data

This script provides GPU-accelerated training with:
- Automatic GPU/CPU detection
- Model checkpointing
- Export for production use
- Integration with dataEngineer Neo4j data

Usage:
    # Train on GPU with exported data
    python src/training/train_gat_enhanced.py --data data/ --gpu --epochs 200
    
    # Train on CPU with live Neo4j
    python src/training/train_gat_enhanced.py --live --epochs 100
    
    # Train and export for production
    python src/training/train_gat_enhanced.py --data data/ --export models/risk_model.pt
"""

import argparse
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import torch
import torch.nn.functional as F
from torch_geometric.data import Data

from src.models.risk_prediction import create_risk_model
from src.utils.device_manager import (
    get_device, move_to_device, ModelCheckpoint, 
    TrainingLogger, export_for_production
)
from src.utils.data_loader import load_exported_data
from src.utils.neo4j_data_fetcher import fetch_graph_data


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
        mae: Mean Absolute Error
    """
    model.train()
    data = move_to_device(data, device)
    
    optimizer.zero_grad()
    
    # Forward pass
    out = model(data.x, data.edge_index)
    loss = criterion(out, data.y)
    mae = F.l1_loss(out, data.y)
    
    # Backward pass
    loss.backward()
    optimizer.step()
    
    return loss.item(), mae.item()


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
    data = move_to_device(data, device)
    
    out = model(data.x, data.edge_index)
    loss = criterion(out, data.y)
    mae = F.l1_loss(out, data.y)
    
    return loss.item(), mae.item()


def train_gat_model(data, epochs=100, lr=0.005, hidden_channels=64, 
                    heads=4, use_gpu=True, checkpoint_dir='checkpoints',
                    export_path=None):
    """
    Train a GAT model on the graph data with GPU/CPU support.
    
    Args:
        data: PyTorch Geometric Data object
        epochs: Number of training epochs
        lr: Learning rate
        hidden_channels: Hidden layer size
        heads: Number of attention heads
        use_gpu: Whether to use GPU if available
        checkpoint_dir: Directory to save checkpoints
        export_path: Path to export final model for production
    
    Returns:
        model: Trained GAT model
        history: Training history
    """
    # Setup device
    device = get_device(prefer_gpu=use_gpu, verbose=True)
    
    # Create model
    model = create_risk_model(
        num_features=data.num_features,
        hidden_channels=hidden_channels,
        heads=heads,
        deep=False,
        device=device
    )
    
    print(f"\n🧠 Model Architecture:")
    print(f"   Parameters: {sum(p.numel() for p in model.parameters()):,}")
    print(f"   Input features: {data.num_features}")
    print(f"   Hidden channels: {hidden_channels}")
    print(f"   Attention heads: {heads}")
    
    # Setup training
    optimizer = torch.optim.Adam(model.parameters(), lr=lr, weight_decay=5e-4)
    criterion = torch.nn.MSELoss()
    
    # Setup logging and checkpointing
    logger = TrainingLogger(log_dir='logs')
    checkpoint = ModelCheckpoint(
        save_dir=checkpoint_dir,
        model_name='gat_risk_model',
        monitor='loss',
        mode='min'
    )
    
    # Training loop
    print(f"\n🚀 Starting training for {epochs} epochs...")
    print("=" * 80)
    
    best_loss = float('inf')
    best_epoch = 0
    
    for epoch in range(1, epochs + 1):
        # Train
        train_loss, train_mae = train_epoch(model, data, optimizer, criterion, device)
        
        # Evaluate (on same data for now - in production use validation set)
        eval_loss, eval_mae = evaluate(model, data, criterion, device)
        
        # Track best model
        if eval_loss < best_loss:
            best_loss = eval_loss
            best_epoch = epoch
        
        # Log metrics
        metrics = {
            'train_loss': train_loss,
            'train_mae': train_mae,
            'eval_loss': eval_loss,
            'eval_mae': eval_mae
        }
        
        # Log every 10 epochs or at the end
        if epoch % 10 == 0 or epoch == epochs:
            logger.log(epoch, metrics, print_console=True)
        
        # Save checkpoint every 20 epochs
        if epoch % 20 == 0 or epoch == epochs:
            checkpoint.save(model, optimizer, epoch, metrics)
    
    print("=" * 80)
    print(f"✅ Training complete!")
    print(f"   Best loss: {best_loss:.6f} at epoch {best_epoch}")
    
    # Save training history
    logger.save_history()
    
    # Export for production if requested
    if export_path:
        print(f"\n📦 Exporting model for production...")
        export_for_production(
            model=model,
            example_data=(data.x.cpu(), data.edge_index.cpu()),
            save_path=export_path,
            optimize_for_cpu=True,
            verbose=True
        )
        print(f"✅ Model ready for Backend integration!")
    
    return model, logger.history


def main():
    parser = argparse.ArgumentParser(
        description="Train GAT model with dataEngineer data (GPU/CPU optimized)"
    )
    
    # Data source
    data_group = parser.add_mutually_exclusive_group(required=True)
    data_group.add_argument(
        "--data", "-d",
        type=str,
        help="Directory with exported data"
    )
    data_group.add_argument(
        "--live",
        action="store_true",
        help="Use live Neo4j connection"
    )
    
    # Training parameters
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
    
    # Device selection
    parser.add_argument(
        "--gpu",
        action="store_true",
        help="Use GPU if available (default: auto-detect)"
    )
    parser.add_argument(
        "--cpu",
        action="store_true",
        help="Force CPU usage (for testing)"
    )
    
    # Output
    parser.add_argument(
        "--checkpoint-dir",
        type=str,
        default="checkpoints",
        help="Directory to save checkpoints (default: checkpoints/)"
    )
    parser.add_argument(
        "--export",
        type=str,
        help="Export trained model to this path for production use"
    )
    
    args = parser.parse_args()
    
    print("=" * 80)
    print("GAT Training with dataEngineer Data (GPU/CPU Optimized)")
    print("=" * 80)
    
    # Load data
    if args.live:
        print("\n🔌 Loading data from live Neo4j connection...")
        data = fetch_graph_data()
    else:
        print(f"\n📂 Loading data from {args.data}...")
        data = load_exported_data(args.data)
    
    if data is None:
        print("\n❌ Failed to load data!")
        if not args.live:
            print("   Run: python scripts/export_data_from_neo4j.py")
        return 1
    
    print(f"✅ Loaded: {data.num_nodes} nodes, {data.num_edges} edges, "
          f"{data.num_features} features")
    
    # Determine device preference
    use_gpu = not args.cpu  # Use GPU unless explicitly told to use CPU
    
    # Train model
    model, history = train_gat_model(
        data,
        epochs=args.epochs,
        lr=args.lr,
        hidden_channels=args.hidden,
        heads=args.heads,
        use_gpu=use_gpu,
        checkpoint_dir=args.checkpoint_dir,
        export_path=args.export
    )
    
    print("\n" + "=" * 80)
    print("✅ Training completed successfully!")
    print("=" * 80)
    print(f"\n📊 Final Metrics:")
    print(f"   Epochs:   {args.epochs}")
    print(f"   Hidden:   {args.hidden}")
    print(f"   Heads:    {args.heads}")
    print(f"   Nodes:    {data.num_nodes}")
    print(f"   Features: {data.num_features}")
    
    if args.export:
        print(f"\n💡 To use in Backend:")
        print(f"   model = torch.jit.load('{args.export}')")
        print(f"   model.eval()")
        print(f"   predictions = model(citizen_features, social_network)")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
