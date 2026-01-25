"""
Data Loader for Exported Graph Data

This module provides functions to load graph data that was exported
from Neo4j using the export_data_from_neo4j.py script.

Usage:
    # Load from PyTorch files
    data = load_pytorch_data("data/")
    
    # Load from CSV files
    data = load_csv_data("data/")
"""

import os
import torch
import pandas as pd
import logging
from typing import Optional, Tuple
from torch_geometric.data import Data
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def load_pytorch_data(data_dir: str) -> Optional[Data]:
    """
    Load PyTorch Geometric Data from exported .pt files.
    
    Args:
        data_dir: Directory containing exported PyTorch files
    
    Returns:
        PyTorch Geometric Data object or None if failed
    """
    data_dir = Path(data_dir)
    
    # Try to load complete data object first
    graph_data_file = data_dir / "graph_data.pt"
    if graph_data_file.exists():
        logger.info(f"📂 Loading PyTorch Geometric Data from {graph_data_file}")
        try:
            data = torch.load(graph_data_file)
            logger.info(f"✅ Loaded: {data.num_nodes} nodes, {data.num_edges} edges, "
                       f"{data.num_features} features")
            return data
        except Exception as e:
            logger.error(f"Failed to load {graph_data_file}: {e}")
    
    # If complete file not found, load individual components
    x_file = data_dir / "node_features.pt"
    edge_index_file = data_dir / "edge_index.pt"
    y_file = data_dir / "labels.pt"
    
    if not (x_file.exists() and edge_index_file.exists() and y_file.exists()):
        logger.error(f"❌ Missing PyTorch data files in {data_dir}")
        logger.error(f"   Expected: graph_data.pt OR (node_features.pt, edge_index.pt, labels.pt)")
        return None
    
    try:
        logger.info(f"📂 Loading PyTorch data from individual files in {data_dir}")
        x = torch.load(x_file)
        edge_index = torch.load(edge_index_file)
        y = torch.load(y_file)
        
        data = Data(x=x, edge_index=edge_index, y=y)
        logger.info(f"✅ Loaded: {data.num_nodes} nodes, {data.num_edges} edges, "
                   f"{data.num_features} features")
        return data
    except Exception as e:
        logger.error(f"Failed to load PyTorch data: {e}")
        return None


def load_csv_data(data_dir: str) -> Optional[Data]:
    """
    Load graph data from exported CSV files and convert to PyTorch Geometric Data.
    
    Args:
        data_dir: Directory containing exported CSV files
    
    Returns:
        PyTorch Geometric Data object or None if failed
    """
    data_dir = Path(data_dir)
    
    citizens_file = data_dir / "citizens.csv"
    features_file = data_dir / "features.csv"
    edges_file = data_dir / "edges.csv"
    
    if not (citizens_file.exists() and features_file.exists() and edges_file.exists()):
        logger.error(f"❌ Missing CSV files in {data_dir}")
        logger.error(f"   Expected: citizens.csv, features.csv, edges.csv")
        return None
    
    try:
        logger.info(f"📂 Loading graph data from CSV files in {data_dir}")
        
        # Load data
        citizens_df = pd.read_csv(citizens_file)
        features_df = pd.read_csv(features_file)
        edges_df = pd.read_csv(edges_file)
        
        # Convert to tensors
        x = torch.tensor(features_df.values, dtype=torch.float)
        y = torch.tensor(citizens_df['target'].values, dtype=torch.float).view(-1, 1)
        
        # Build edge index
        if edges_df.empty:
            logger.warning("⚠️  No edges found!")
            edge_index = torch.empty((2, 0), dtype=torch.long)
        else:
            # Create node ID to index mapping
            node_ids = sorted(citizens_df['id'].unique())
            id_to_idx = {node_id: idx for idx, node_id in enumerate(node_ids)}
            
            # Map edge IDs to indices
            source_indices = edges_df['source'].map(id_to_idx)
            target_indices = edges_df['target'].map(id_to_idx)
            
            # Create bidirectional edges
            edge_index = torch.tensor([
                list(source_indices) + list(target_indices),
                list(target_indices) + list(source_indices)
            ], dtype=torch.long)
        
        data = Data(x=x, edge_index=edge_index, y=y)
        
        logger.info(f"✅ Loaded: {data.num_nodes} nodes, {data.num_edges} edges, "
                   f"{data.num_features} features")
        return data
    
    except Exception as e:
        logger.error(f"Failed to load CSV data: {e}")
        import traceback
        traceback.print_exc()
        return None


def load_exported_data(data_dir: str, format: str = "auto") -> Optional[Data]:
    """
    Load exported graph data automatically detecting the format.
    
    Args:
        data_dir: Directory containing exported data files
        format: Format to load ("pytorch", "csv", or "auto")
    
    Returns:
        PyTorch Geometric Data object or None if failed
    """
    data_dir = Path(data_dir)
    
    if not data_dir.exists():
        logger.error(f"❌ Data directory not found: {data_dir}")
        logger.error(f"   Run: python scripts/export_data_from_neo4j.py --output {data_dir}")
        return None
    
    if format == "auto":
        # Try PyTorch first (faster)
        if (data_dir / "graph_data.pt").exists() or (data_dir / "node_features.pt").exists():
            logger.info("🔍 Auto-detected PyTorch format")
            return load_pytorch_data(data_dir)
        elif (data_dir / "citizens.csv").exists():
            logger.info("🔍 Auto-detected CSV format")
            return load_csv_data(data_dir)
        else:
            logger.error(f"❌ No recognized data files in {data_dir}")
            return None
    elif format == "pytorch":
        return load_pytorch_data(data_dir)
    elif format == "csv":
        return load_csv_data(data_dir)
    else:
        logger.error(f"❌ Unknown format: {format}. Use 'pytorch', 'csv', or 'auto'")
        return None


def load_feature_names(data_dir: str) -> Optional[list]:
    """
    Load feature names from exported data.
    
    Args:
        data_dir: Directory containing exported data files
    
    Returns:
        List of feature names or None if not found
    """
    data_dir = Path(data_dir)
    feature_names_file = data_dir / "feature_names.txt"
    
    if not feature_names_file.exists():
        logger.warning(f"⚠️  Feature names file not found: {feature_names_file}")
        return None
    
    try:
        with open(feature_names_file, 'r') as f:
            feature_names = [line.strip() for line in f.readlines()]
        logger.info(f"✅ Loaded {len(feature_names)} feature names")
        return feature_names
    except Exception as e:
        logger.error(f"Failed to load feature names: {e}")
        return None


def print_data_info(data: Data, feature_names: Optional[list] = None):
    """
    Print detailed information about loaded data.
    
    Args:
        data: PyTorch Geometric Data object
        feature_names: Optional list of feature names
    """
    print("\n" + "=" * 60)
    print("Graph Data Information")
    print("=" * 60)
    print(f"\nStructure:")
    print(f"  Nodes:           {data.num_nodes}")
    print(f"  Edges:           {data.num_edges}")
    print(f"  Features:        {data.num_features}")
    print(f"  Undirected:      {data.is_undirected()}")
    
    if feature_names:
        print(f"\nFeature names ({len(feature_names)}):")
        for i, name in enumerate(feature_names):
            print(f"  [{i}] {name}")
    
    print(f"\nTensor shapes:")
    print(f"  x (features):    {data.x.shape}")
    print(f"  edge_index:      {data.edge_index.shape}")
    print(f"  y (labels):      {data.y.shape}")
    
    print(f"\nFeature statistics:")
    print(f"  Mean: {data.x.mean(dim=0)}")
    print(f"  Std:  {data.x.std(dim=0)}")
    
    print(f"\nLabel statistics:")
    print(f"  Min:  {data.y.min().item():.6f}")
    print(f"  Max:  {data.y.max().item():.6f}")
    print(f"  Mean: {data.y.mean().item():.6f}")
    print(f"  Std:  {data.y.std().item():.6f}")
    
    print(f"\nGraph statistics:")
    density = data.num_edges / (data.num_nodes * (data.num_nodes - 1))
    avg_degree = data.num_edges / data.num_nodes
    print(f"  Density:         {density:.6f}")
    print(f"  Average degree:  {avg_degree:.2f}")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Load and inspect exported graph data")
    parser.add_argument("data_dir", type=str, help="Directory containing exported data")
    parser.add_argument("--format", type=str, default="auto", 
                       choices=["auto", "pytorch", "csv"],
                       help="Data format to load (default: auto)")
    
    args = parser.parse_args()
    
    # Load data
    data = load_exported_data(args.data_dir, args.format)
    
    if data:
        # Load feature names
        feature_names = load_feature_names(args.data_dir)
        
        # Print info
        print_data_info(data, feature_names)
        
        print("✅ Data loaded successfully!")
        print(f"\nYou can use this data for GAT model training:")
        print(f"  from src.utils.data_loader import load_exported_data")
        print(f"  data = load_exported_data('{args.data_dir}')")
    else:
        print("❌ Failed to load data")
