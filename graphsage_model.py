"""
GraphSAGE Model with Multiple Aggregation Methods

This module implements GraphSAGE (Graph Sample and Aggregate) with support for:
- Mini-batch gradient descent
- Neighbor sampling
- Multiple aggregation methods: Mean, LSTM, Pooling
- Clustering support

Based on: https://mlabonne.github.io/blog/posts/2022-04-06-GraphSAGE.html

Author: The Oracle Team
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch_geometric.nn import SAGEConv, global_mean_pool
from typing import Optional, Literal


class GraphSAGEAggregator(nn.Module):
    """
    GraphSAGE with configurable aggregation methods.
    
    Supports three aggregation strategies:
    1. Mean: Simple average of neighbor features (GCN-like)
    2. LSTM: Sequential aggregation using LSTM
    3. Pooling: Element-wise max pooling
    
    Args:
        in_channels: Number of input features per node
        hidden_channels: Number of hidden units
        out_channels: Number of output features
        num_layers: Number of GraphSAGE layers
        aggregator: Type of aggregation ('mean', 'lstm', 'pool')
        dropout: Dropout rate for regularization
    """
    
    def __init__(
        self,
        in_channels: int,
        hidden_channels: int = 64,
        out_channels: int = 32,
        num_layers: int = 2,
        aggregator: Literal['mean', 'lstm', 'pool'] = 'mean',
        dropout: float = 0.3
    ):
        super(GraphSAGEAggregator, self).__init__()
        
        self.in_channels = in_channels
        self.hidden_channels = hidden_channels
        self.out_channels = out_channels
        self.num_layers = num_layers
        self.aggregator = aggregator
        self.dropout = dropout
        
        self.convs = nn.ModuleList()
        self.batch_norms = nn.ModuleList()
        
        # Build GraphSAGE layers
        for i in range(num_layers):
            in_ch = in_channels if i == 0 else hidden_channels
            out_ch = out_channels if i == num_layers - 1 else hidden_channels
            
            # SAGEConv with specified aggregator
            self.convs.append(
                SAGEConv(in_ch, out_ch, aggr=aggregator)
            )
            self.batch_norms.append(nn.BatchNorm1d(out_ch))
        
        # For LSTM aggregation, add additional LSTM layer
        if aggregator == 'lstm':
            self.lstm = nn.LSTM(
                input_size=hidden_channels,
                hidden_size=hidden_channels,
                num_layers=1,
                batch_first=True
            )
    
    def forward(self, x: torch.Tensor, edge_index: torch.Tensor) -> torch.Tensor:
        """
        Forward pass through GraphSAGE layers.
        
        Args:
            x: Node features [num_nodes, in_channels]
            edge_index: Edge indices [2, num_edges]
        
        Returns:
            Node embeddings [num_nodes, out_channels]
        """
        for i, (conv, bn) in enumerate(zip(self.convs, self.batch_norms)):
            x = conv(x, edge_index)
            x = bn(x)
            
            # Apply activation except for last layer
            if i < self.num_layers - 1:
                x = F.relu(x)
                x = F.dropout(x, p=self.dropout, training=self.training)
        
        return x


class GraphSAGEWithClustering(nn.Module):
    """
    GraphSAGE model with clustering support.
    
    This model extends GraphSAGE with hierarchical graph clustering
    for better scalability and structure learning.
    
    Args:
        in_channels: Number of input features per node
        hidden_channels: Number of hidden units
        out_channels: Number of output features
        num_layers: Number of GraphSAGE layers
        aggregator: Type of aggregation ('mean', 'lstm', 'pool')
        num_clusters: Number of clusters for graph pooling
        dropout: Dropout rate
    """
    
    def __init__(
        self,
        in_channels: int,
        hidden_channels: int = 64,
        out_channels: int = 32,
        num_layers: int = 2,
        aggregator: Literal['mean', 'lstm', 'pool'] = 'mean',
        num_clusters: int = 10,
        dropout: float = 0.3
    ):
        super(GraphSAGEWithClustering, self).__init__()
        
        self.num_clusters = num_clusters
        
        # GraphSAGE backbone
        self.sage = GraphSAGEAggregator(
            in_channels=in_channels,
            hidden_channels=hidden_channels,
            out_channels=out_channels,
            num_layers=num_layers,
            aggregator=aggregator,
            dropout=dropout
        )
        
        # Clustering layer: assigns nodes to clusters
        self.cluster_assignment = nn.Sequential(
            nn.Linear(out_channels, hidden_channels),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_channels, num_clusters),
            nn.Softmax(dim=1)
        )
        
        # Cluster embedding layer
        self.cluster_embedding = nn.Linear(out_channels, out_channels)
    
    def forward(
        self, 
        x: torch.Tensor, 
        edge_index: torch.Tensor,
        batch: Optional[torch.Tensor] = None,
        return_clusters: bool = False
    ):
        """
        Forward pass with optional clustering.
        
        Args:
            x: Node features [num_nodes, in_channels]
            edge_index: Edge indices [2, num_edges]
            batch: Batch assignment for nodes [num_nodes]
            return_clusters: If True, return cluster assignments
        
        Returns:
            Node embeddings and optionally cluster assignments
        """
        # Get node embeddings from GraphSAGE
        node_embeddings = self.sage(x, edge_index)
        
        # Compute cluster assignments (soft clustering)
        cluster_probs = self.cluster_assignment(node_embeddings)
        
        # Compute cluster representations
        # cluster_repr[i] = weighted sum of nodes assigned to cluster i
        cluster_repr = torch.matmul(
            cluster_probs.t(),  # [num_clusters, num_nodes]
            node_embeddings     # [num_nodes, out_channels]
        )  # [num_clusters, out_channels]
        
        cluster_repr = self.cluster_embedding(cluster_repr)
        
        if return_clusters:
            return node_embeddings, cluster_repr, cluster_probs
        
        return node_embeddings, cluster_repr


class GraphSAGEMiniBatch(nn.Module):
    """
    GraphSAGE model optimized for mini-batch training with neighbor sampling.
    
    This model is designed to work with PyTorch Geometric's NeighborLoader
    for efficient mini-batch gradient descent on large graphs.
    
    Features:
    - Efficient neighbor sampling
    - Mini-batch training support
    - Multiple aggregation methods
    - Edge-level predictions (for link prediction tasks)
    
    Args:
        in_channels: Number of input features per node
        hidden_channels: Number of hidden units
        out_channels: Number of output features
        num_layers: Number of GraphSAGE layers
        aggregator: Type of aggregation ('mean', 'lstm', 'pool')
        dropout: Dropout rate
        task: Task type ('node', 'edge', 'graph')
    """
    
    def __init__(
        self,
        in_channels: int,
        hidden_channels: int = 64,
        out_channels: int = 32,
        num_layers: int = 2,
        aggregator: Literal['mean', 'lstm', 'pool'] = 'mean',
        dropout: float = 0.3,
        task: Literal['node', 'edge', 'graph'] = 'node'
    ):
        super(GraphSAGEMiniBatch, self).__init__()
        
        self.task = task
        
        # GraphSAGE backbone
        self.sage = GraphSAGEAggregator(
            in_channels=in_channels,
            hidden_channels=hidden_channels,
            out_channels=out_channels,
            num_layers=num_layers,
            aggregator=aggregator,
            dropout=dropout
        )
        
        # Task-specific heads
        if task == 'edge':
            # Edge prediction head
            self.edge_predictor = nn.Sequential(
                nn.Linear(out_channels * 2, hidden_channels),
                nn.ReLU(),
                nn.Dropout(dropout),
                nn.Linear(hidden_channels, 1),
                nn.Sigmoid()
            )
        elif task == 'graph':
            # Graph-level prediction head
            self.graph_predictor = nn.Sequential(
                nn.Linear(out_channels, hidden_channels),
                nn.ReLU(),
                nn.Dropout(dropout),
                nn.Linear(hidden_channels, 1),
                nn.Sigmoid()
            )
        else:  # node task
            # Node-level prediction head
            self.node_predictor = nn.Sequential(
                nn.Linear(out_channels, hidden_channels),
                nn.ReLU(),
                nn.Dropout(dropout),
                nn.Linear(hidden_channels, 1),
                nn.Sigmoid()
            )
    
    def forward(
        self, 
        x: torch.Tensor, 
        edge_index: torch.Tensor,
        edge_label_index: Optional[torch.Tensor] = None,
        batch: Optional[torch.Tensor] = None
    ):
        """
        Forward pass for mini-batch training.
        
        Args:
            x: Node features [num_nodes, in_channels]
            edge_index: Edge indices for message passing [2, num_edges]
            edge_label_index: Edge indices for prediction [2, num_pred_edges]
            batch: Batch assignment for graph-level tasks [num_nodes]
        
        Returns:
            Predictions based on task type
        """
        # Get node embeddings
        node_embeddings = self.sage(x, edge_index)
        
        if self.task == 'edge':
            # Edge prediction
            if edge_label_index is None:
                edge_label_index = edge_index
            
            src_nodes = edge_label_index[0]
            dst_nodes = edge_label_index[1]
            
            src_embeddings = node_embeddings[src_nodes]
            dst_embeddings = node_embeddings[dst_nodes]
            
            edge_features = torch.cat([src_embeddings, dst_embeddings], dim=1)
            predictions = self.edge_predictor(edge_features)
            
            return predictions
        
        elif self.task == 'graph':
            # Graph-level prediction
            if batch is None:
                # Single graph: use mean pooling
                graph_embedding = global_mean_pool(node_embeddings, 
                                                   torch.zeros(node_embeddings.size(0), 
                                                             dtype=torch.long, 
                                                             device=node_embeddings.device))
            else:
                # Multiple graphs: pool by batch
                graph_embedding = global_mean_pool(node_embeddings, batch)
            
            predictions = self.graph_predictor(graph_embedding)
            return predictions
        
        else:  # node task
            # Node-level prediction
            predictions = self.node_predictor(node_embeddings)
            return predictions
    
    def get_embeddings(self, x: torch.Tensor, edge_index: torch.Tensor) -> torch.Tensor:
        """
        Get node embeddings without task-specific predictions.
        
        Args:
            x: Node features
            edge_index: Edge indices
        
        Returns:
            Node embeddings
        """
        return self.sage(x, edge_index)


def create_graphsage_model(
    in_channels: int = 16,
    aggregator: Literal['mean', 'lstm', 'pool'] = 'mean',
    use_clustering: bool = False,
    task: Literal['node', 'edge', 'graph'] = 'edge',
    device: Optional[str] = None
) -> nn.Module:
    """
    Factory function to create a GraphSAGE model with specified configuration.
    
    Args:
        in_channels: Number of input features
        aggregator: Type of aggregation ('mean', 'lstm', 'pool')
        use_clustering: Whether to use clustering
        task: Task type for mini-batch model
        device: Device to place model on
    
    Returns:
        Configured GraphSAGE model
    """
    if device is None:
        device = 'cuda' if torch.cuda.is_available() else 'cpu'
    
    if use_clustering:
        model = GraphSAGEWithClustering(
            in_channels=in_channels,
            hidden_channels=64,
            out_channels=32,
            num_layers=2,
            aggregator=aggregator,
            num_clusters=10,
            dropout=0.3
        )
    else:
        model = GraphSAGEMiniBatch(
            in_channels=in_channels,
            hidden_channels=64,
            out_channels=32,
            num_layers=2,
            aggregator=aggregator,
            dropout=0.3,
            task=task
        )
    
    return model.to(device)


if __name__ == "__main__":
    """
    Smoke test for GraphSAGE models.
    """
    print("=" * 70)
    print("GraphSAGE Model Test - Multiple Aggregation Methods")
    print("=" * 70)
    
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    print(f"\n🖥️  Device: {device}")
    
    # Test parameters
    num_nodes = 100
    num_edges = 300
    in_channels = 16
    
    # Generate test data
    x = torch.randn(num_nodes, in_channels, device=device)
    edge_index = torch.randint(0, num_nodes, (2, num_edges), device=device)
    
    print(f"\n📊 Test Graph:")
    print(f"   Nodes: {num_nodes}")
    print(f"   Edges: {num_edges}")
    print(f"   Features: {in_channels}")
    
    # Test all aggregation methods
    aggregators = ['mean', 'lstm', 'pool']
    
    for aggr in aggregators:
        print(f"\n{'='*70}")
        print(f"Testing Aggregator: {aggr.upper()}")
        print(f"{'='*70}")
        
        # Test standard GraphSAGE
        print(f"\n1. GraphSAGEMiniBatch (Edge Prediction):")
        model = create_graphsage_model(
            in_channels=in_channels,
            aggregator=aggr,
            use_clustering=False,
            task='edge',
            device=device
        )
        
        model.eval()
        with torch.no_grad():
            predictions = model(x, edge_index)
        
        print(f"   Parameters: {sum(p.numel() for p in model.parameters()):,}")
        print(f"   Output shape: {predictions.shape}")
        print(f"   Mean prediction: {predictions.mean():.4f}")
        
        # Test GraphSAGE with clustering
        print(f"\n2. GraphSAGEWithClustering:")
        model_cluster = create_graphsage_model(
            in_channels=in_channels,
            aggregator=aggr,
            use_clustering=True,
            device=device
        )
        
        model_cluster.eval()
        with torch.no_grad():
            node_emb, cluster_emb, cluster_probs = model_cluster(
                x, edge_index, return_clusters=True
            )
        
        print(f"   Parameters: {sum(p.numel() for p in model_cluster.parameters()):,}")
        print(f"   Node embeddings: {node_emb.shape}")
        print(f"   Cluster embeddings: {cluster_emb.shape}")
        print(f"   Cluster probabilities: {cluster_probs.shape}")
        
        # Show cluster assignment distribution
        cluster_assignments = cluster_probs.argmax(dim=1)
        unique_clusters, counts = torch.unique(cluster_assignments, return_counts=True)
        print(f"   Active clusters: {len(unique_clusters)}/10")
    
    print(f"\n{'='*70}")
    print("✨ All GraphSAGE models tested successfully!")
    print(f"{'='*70}")
