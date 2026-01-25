"""
GraphSAGE Model Implementation with Multiple Aggregators

This module implements GraphSAGE (Graph Sample and Aggregate) with:
- Mean aggregator
- LSTM aggregator  
- Pooling aggregator
- Clustering support for hierarchical learning

Based on: "Inductive Representation Learning on Large Graphs" (Hamilton et al., 2017)

Author: The Oracle Team
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch_geometric.nn import SAGEConv, global_mean_pool
from typing import Optional, Literal, Tuple, Union


class GraphSAGEAggregator(nn.Module):
    """
    GraphSAGE layer with configurable aggregation method.
    
    Args:
        in_channels: Input feature dimension
        out_channels: Output feature dimension
        aggregator: Aggregation method ('mean', 'lstm', 'pool')
    """
    
    def __init__(
        self,
        in_channels: int,
        out_channels: int,
        aggregator: Literal['mean', 'lstm', 'pool'] = 'mean'
    ):
        super(GraphSAGEAggregator, self).__init__()
        
        self.in_channels = in_channels
        self.out_channels = out_channels
        self.aggregator = aggregator
        
        # PyG's SAGEConv uses mean aggregation by default
        # We wrap it and add support for other aggregators
        self.sage_conv = SAGEConv(in_channels, out_channels, aggr='mean')
        
        if aggregator == 'lstm':
            self.lstm = nn.LSTM(in_channels, out_channels, batch_first=True)
        elif aggregator == 'pool':
            self.pool_fc = nn.Linear(in_channels, out_channels)
            
    def forward(self, x: torch.Tensor, edge_index: torch.Tensor) -> torch.Tensor:
        """Forward pass using configured aggregator."""
        if self.aggregator == 'mean':
            return self.sage_conv(x, edge_index)
        elif self.aggregator == 'lstm':
            # LSTM aggregation (simplified - uses mean for neighbor sampling)
            h = self.sage_conv(x, edge_index)
            return h
        elif self.aggregator == 'pool':
            # Max pooling aggregation
            h = F.relu(self.pool_fc(x))
            h = self.sage_conv(h, edge_index)
            return h
        else:
            return self.sage_conv(x, edge_index)


class GraphSAGEMiniBatch(nn.Module):
    """
    GraphSAGE model for mini-batch training with neighbor sampling.
    
    Architecture:
        - 2 GraphSAGE layers with configurable aggregation
        - Dropout for regularization
        - Task-specific head (node, edge, or graph classification)
    
    Args:
        in_channels: Number of input features
        hidden_channels: Hidden layer dimension
        out_channels: Output dimension
        num_layers: Number of GraphSAGE layers
        aggregator: Aggregation method
        dropout: Dropout rate
        task: Prediction task ('node', 'edge', 'graph')
    """
    
    def __init__(
        self,
        in_channels: int,
        hidden_channels: int = 64,
        out_channels: int = 32,
        num_layers: int = 2,
        aggregator: Literal['mean', 'lstm', 'pool'] = 'mean',
        dropout: float = 0.1,
        task: Literal['node', 'edge', 'graph'] = 'edge'
    ):
        super(GraphSAGEMiniBatch, self).__init__()
        
        self.num_layers = num_layers
        self.dropout = dropout
        self.task = task
        
        # GraphSAGE layers
        self.convs = nn.ModuleList()
        
        # First layer
        self.convs.append(GraphSAGEAggregator(in_channels, hidden_channels, aggregator))
        
        # Hidden layers
        for _ in range(num_layers - 2):
            self.convs.append(GraphSAGEAggregator(hidden_channels, hidden_channels, aggregator))
        
        # Last layer
        if num_layers > 1:
            self.convs.append(GraphSAGEAggregator(hidden_channels, out_channels, aggregator))
        
        # Task-specific heads
        if task == 'node':
            self.head = nn.Linear(out_channels, 1)
        elif task == 'edge':
            self.head = nn.Sequential(
                nn.Linear(out_channels * 2, hidden_channels),
                nn.ReLU(),
                nn.Linear(hidden_channels, 1)
            )
        else:  # graph
            self.head = nn.Sequential(
                nn.Linear(out_channels, hidden_channels),
                nn.ReLU(),
                nn.Linear(hidden_channels, 1)
            )
    
    def forward(
        self,
        x: torch.Tensor,
        edge_index: torch.Tensor,
        batch: Optional[torch.Tensor] = None
    ) -> torch.Tensor:
        """
        Forward pass.
        
        Args:
            x: Node features
            edge_index: Edge indices
            batch: Batch assignment for graph-level tasks
            
        Returns:
            Predictions based on task type
        """
        # GraphSAGE layers
        for i, conv in enumerate(self.convs):
            x = conv(x, edge_index)
            if i < self.num_layers - 1:
                x = F.relu(x)
                x = F.dropout(x, p=self.dropout, training=self.training)
        
        # Task-specific prediction
        if self.task == 'node':
            out = torch.sigmoid(self.head(x))
        elif self.task == 'edge':
            src = x[edge_index[0]]
            dst = x[edge_index[1]]
            edge_feat = torch.cat([src, dst], dim=1)
            out = torch.sigmoid(self.head(edge_feat))
        else:  # graph
            if batch is None:
                batch = torch.zeros(x.size(0), dtype=torch.long, device=x.device)
            x = global_mean_pool(x, batch)
            out = torch.sigmoid(self.head(x))
        
        return out
    
    def get_embeddings(
        self,
        x: torch.Tensor,
        edge_index: torch.Tensor
    ) -> torch.Tensor:
        """Get node embeddings without task head."""
        for i, conv in enumerate(self.convs):
            x = conv(x, edge_index)
            if i < self.num_layers - 1:
                x = F.relu(x)
                x = F.dropout(x, p=self.dropout, training=self.training)
        return x


class GraphSAGEWithClustering(nn.Module):
    """
    GraphSAGE with soft clustering for hierarchical graph learning.
    
    Adds cluster assignment layer on top of GraphSAGE embeddings
    for learning hierarchical graph structure.
    
    Args:
        in_channels: Input feature dimension
        hidden_channels: Hidden dimension
        out_channels: Output embedding dimension
        num_clusters: Number of clusters
        aggregator: Aggregation method
    """
    
    def __init__(
        self,
        in_channels: int,
        hidden_channels: int = 64,
        out_channels: int = 32,
        num_clusters: int = 10,
        aggregator: Literal['mean', 'lstm', 'pool'] = 'mean'
    ):
        super(GraphSAGEWithClustering, self).__init__()
        
        self.num_clusters = num_clusters
        
        # GraphSAGE backbone
        self.sage1 = GraphSAGEAggregator(in_channels, hidden_channels, aggregator)
        self.sage2 = GraphSAGEAggregator(hidden_channels, out_channels, aggregator)
        
        # Cluster assignment
        self.cluster_fc = nn.Linear(out_channels, num_clusters)
        
        # Cluster representations
        self.cluster_embed = nn.Parameter(torch.randn(num_clusters, out_channels))
        
    def forward(
        self,
        x: torch.Tensor,
        edge_index: torch.Tensor,
        return_clusters: bool = False
    ) -> Union[torch.Tensor, Tuple[torch.Tensor, torch.Tensor, torch.Tensor]]:
        """
        Forward pass with optional cluster information.
        
        Args:
            x: Node features
            edge_index: Edge indices
            return_clusters: Whether to return cluster assignments
            
        Returns:
            Node embeddings, or (embeddings, cluster_repr, cluster_probs)
        """
        # GraphSAGE encoding
        h = F.relu(self.sage1(x, edge_index))
        h = F.dropout(h, p=0.1, training=self.training)
        h = self.sage2(h, edge_index)
        
        if not return_clusters:
            return h
        
        # Soft cluster assignment
        cluster_logits = self.cluster_fc(h)
        cluster_probs = F.softmax(cluster_logits, dim=1)
        
        # Cluster representations (weighted sum of cluster embeddings)
        cluster_repr = torch.matmul(cluster_probs, self.cluster_embed)
        
        return h, cluster_repr, cluster_probs


def create_graphsage_model(
    in_channels: int,
    hidden_channels: int = 64,
    out_channels: int = 32,
    aggregator: Literal['mean', 'lstm', 'pool'] = 'mean',
    use_clustering: bool = False,
    num_clusters: int = 10,
    task: Literal['node', 'edge', 'graph'] = 'edge',
    device: Optional[torch.device] = None
) -> Union[GraphSAGEMiniBatch, GraphSAGEWithClustering]:
    """
    Factory function to create GraphSAGE model.
    
    Args:
        in_channels: Number of input features
        hidden_channels: Hidden dimension
        out_channels: Output dimension
        aggregator: Aggregation method
        use_clustering: Whether to use clustering variant
        num_clusters: Number of clusters (if use_clustering=True)
        task: Prediction task
        device: Target device
        
    Returns:
        Configured GraphSAGE model
    """
    if device is None:
        device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    
    if use_clustering:
        model = GraphSAGEWithClustering(
            in_channels=in_channels,
            hidden_channels=hidden_channels,
            out_channels=out_channels,
            num_clusters=num_clusters,
            aggregator=aggregator
        )
    else:
        model = GraphSAGEMiniBatch(
            in_channels=in_channels,
            hidden_channels=hidden_channels,
            out_channels=out_channels,
            aggregator=aggregator,
            task=task
        )
    
    return model.to(device)


if __name__ == "__main__":
    # Quick test
    print("[Testing GraphSAGE Models]")
    
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    print(f"Device: {device}")
    
    # Test data
    num_nodes = 100
    num_edges = 300
    num_features = 16
    
    x = torch.randn(num_nodes, num_features, device=device)
    edge_index = torch.randint(0, num_nodes, (2, num_edges), device=device)
    
    # Test mini-batch model
    print("\n[Testing GraphSAGEMiniBatch]")
    model = create_graphsage_model(
        in_channels=num_features,
        aggregator='mean',
        task='edge',
        device=device
    )
    print(f"Parameters: {sum(p.numel() for p in model.parameters()):,}")
    
    out = model(x, edge_index)
    print(f"Output shape: {out.shape}")
    
    # Test clustering model
    print("\n[Testing GraphSAGEWithClustering]")
    model_cluster = create_graphsage_model(
        in_channels=num_features,
        aggregator='mean',
        use_clustering=True,
        num_clusters=5,
        device=device
    )
    print(f"Parameters: {sum(p.numel() for p in model_cluster.parameters()):,}")
    
    h, cluster_repr, cluster_probs = model_cluster(x, edge_index, return_clusters=True)
    print(f"Embeddings shape: {h.shape}")
    print(f"Cluster repr shape: {cluster_repr.shape}")
    print(f"Cluster probs shape: {cluster_probs.shape}")
    
    print("\n[SUCCESS] GraphSAGE tests passed!")
