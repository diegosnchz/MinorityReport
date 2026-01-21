"""
Main entry point for training GraphSAGE models

This script provides a simple way to run GraphSAGE training
without needing to navigate into the src folder structure.

Usage:
    python run_graphsage_training.py
"""

import sys
import os

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Import and run the training
from src.training.train_graphsage_minibatch import train_graphsage_minibatch

if __name__ == "__main__":
    print("[Starting GraphSAGE Training]")
    print("=" * 60)
    
    # Run training with default parameters
    model, history = train_graphsage_minibatch(
        num_epochs=20,
        num_nodes=1000,
        batch_size=32,
        aggregator_type='mean'
    )
    
    print("=" * 60)
    print("[Training Complete]")
    print(f"Final train loss: {history['train_loss'][-1]:.4f}")
    print(f"Final train accuracy: {history['train_accuracy'][-1]:.4f}")
