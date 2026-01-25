"""
Main entry point for training OracleNet

This script provides a simple way to run the Oracle training process
without needing to navigate into the src folder structure.

Usage:
    python run_oracle_training.py
"""

import sys
import os

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Import and run the training
from src.training.train_oracle import train_oracle_net

if __name__ == "__main__":
    print("[Starting OracleNet Training]")
    print("=" * 60)
    
    # Run training with default parameters
    model, history = train_oracle_net(
        num_epochs=50,
        num_graphs=100
    )
    
    print("=" * 60)
    print("[Training Complete]")
    print(f"Final train loss: {history['train_loss'][-1]:.4f}")
    print(f"Model saved to: saved_models/oracle_net_best.pth")
