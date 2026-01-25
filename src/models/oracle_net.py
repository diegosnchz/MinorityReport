"""
OracleNet - GCN + GAT Hybrid Model for Escape Route Optimization

This module implements OracleNet, a hybrid Graph Neural Network that combines:
- Graph Convolutional Networks (GCN) for structural feature extraction
- Graph Attention Networks (GAT) for attention-weighted message passing

The model predicts safe escape routes in surveillance-heavy urban environments.

Author: The Oracle Team
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch_geometric.nn import GCNConv, GATConv
from typing import Optional, Tuple


class OracleNet(nn.Module):
    """
    Hybrid GCN + GAT model for escape route optimization.
    
    Architecture:
        - GCN Layer 1: Extract local structural features
        - GCN Layer 2: Aggregate neighborhood information
        - GAT Layer: Apply attention to identify critical paths
        - Edge Predictor: Predict safety scores for edges
    
    Args:
        num_features: Number of input node features
        hidden_channels: Hidden layer dimension (default: 32)
        num_heads: Number of attention heads for GAT (default: 4)
        dropout: Dropout rate (default: 0.1)
    """
    
    def __init__(
        self,
        num_features: int = 16,
        hidden_channels: int = 32,
        num_heads: int = 4,
        dropout: float = 0.1
    ):
        super(OracleNet, self).__init__()
        
        self.num_features = num_features
        self.hidden_channels = hidden_channels
        self.num_heads = num_heads
        self.dropout = dropout
        
        # GCN Layers for structural feature extraction
        self.gcn1 = GCNConv(num_features, hidden_channels)
        self.gcn2 = GCNConv(hidden_channels, hidden_channels // 2)
        
        # GAT Layer for attention-based aggregation
        # Output: hidden_channels // 2 * num_heads -> hidden_channels // 2
        self.gat = GATConv(
            hidden_channels // 2,
            hidden_channels // num_heads,
            heads=num_heads,
            concat=True,
            dropout=dropout
        )
        
        # Edge predictor MLP
        # Takes concatenated source and destination embeddings
        self.edge_predictor = nn.Sequential(
            nn.Linear(hidden_channels * 2, hidden_channels),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_channels, 1),
            nn.Sigmoid()
        )
        
        # Batch normalization
        self.bn1 = nn.BatchNorm1d(hidden_channels)
        self.bn2 = nn.BatchNorm1d(hidden_channels // 2)
        
    def forward(
        self,
        x: torch.Tensor,
        edge_index: torch.Tensor,
        return_attention: bool = False
    ) -> Tuple[torch.Tensor, Optional[torch.Tensor]]:
        """
        Forward pass of OracleNet.
        
        Args:
            x: Node features [num_nodes, num_features]
            edge_index: Edge indices [2, num_edges]
            return_attention: Whether to return attention weights
            
        Returns:
            edge_predictions: Safety scores for each edge [num_edges, 1]
            attention_weights: GAT attention weights (if return_attention=True)
        """
        # GCN layers
        h = self.gcn1(x, edge_index)
        h = self.bn1(h)
        h = F.relu(h)
        h = F.dropout(h, p=self.dropout, training=self.training)
        
        h = self.gcn2(h, edge_index)
        h = self.bn2(h)
        h = F.relu(h)
        h = F.dropout(h, p=self.dropout, training=self.training)
        
        # GAT layer with optional attention weights
        if return_attention:
            h, (edge_index_att, attention_weights) = self.gat(
                h, edge_index, return_attention_weights=True
            )
        else:
            h = self.gat(h, edge_index)
            attention_weights = None
        
        h = F.elu(h)
        
        # Edge prediction
        # Concatenate source and destination node embeddings
        src_embeddings = h[edge_index[0]]
        dst_embeddings = h[edge_index[1]]
        edge_embeddings = torch.cat([src_embeddings, dst_embeddings], dim=1)
        
        # Predict edge safety scores
        edge_predictions = self.edge_predictor(edge_embeddings)
        
        return edge_predictions, attention_weights
    
    def get_node_embeddings(
        self,
        x: torch.Tensor,
        edge_index: torch.Tensor
    ) -> torch.Tensor:
        """
        Get node embeddings without edge prediction.
        
        Args:
            x: Node features
            edge_index: Edge indices
            
        Returns:
            Node embeddings after GCN+GAT processing
        """
        h = self.gcn1(x, edge_index)
        h = self.bn1(h)
        h = F.relu(h)
        h = F.dropout(h, p=self.dropout, training=self.training)
        
        h = self.gcn2(h, edge_index)
        h = self.bn2(h)
        h = F.relu(h)
        h = F.dropout(h, p=self.dropout, training=self.training)
        
        h = self.gat(h, edge_index)
        h = F.elu(h)
        
        return h


def create_oracle_net(
    num_features: int = 16,
    hidden_channels: int = 32,
    num_heads: int = 4,
    dropout: float = 0.1,
    device: Optional[torch.device] = None
) -> OracleNet:
    """
    Factory function to create and initialize OracleNet.
    
    Args:
        num_features: Number of input features
        hidden_channels: Hidden dimension
        num_heads: Number of GAT attention heads
        dropout: Dropout rate
        device: Target device (cuda/cpu)
        
    Returns:
        Initialized OracleNet model on specified device
    """
    if device is None:
        device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    
    model = OracleNet(
        num_features=num_features,
        hidden_channels=hidden_channels,
        num_heads=num_heads,
        dropout=dropout
    )
    
    model = model.to(device)
    
    return model


if __name__ == "__main__":
    # Quick test
    print("[Testing OracleNet]")
    
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    print(f"Device: {device}")
    
    # Create model
    model = create_oracle_net(num_features=16, device=device)
    print(f"Parameters: {sum(p.numel() for p in model.parameters()):,}")
    
    # Test forward pass
    num_nodes = 100
    num_edges = 300
    x = torch.randn(num_nodes, 16, device=device)
    edge_index = torch.randint(0, num_nodes, (2, num_edges), device=device)
    
    edge_pred, attn = model(x, edge_index, return_attention=True)
    print(f"Edge predictions shape: {edge_pred.shape}")
    print(f"Attention weights shape: {attn.shape if attn is not None else 'None'}")
    
    print("[SUCCESS] OracleNet test passed!")
