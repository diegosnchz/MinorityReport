"""
Training script for GraphSAGE with Mini-batch Gradient Descent and Neighbor Sampling

This script implements:
1. Mini-batch training with very small batches
2. Neighbor sampling for scalability
3. Multiple aggregation methods (mean, LSTM, pooling)
4. Clustering support

Based on the requirements from:
https://mlabonne.github.io/blog/posts/2022-04-06-GraphSAGE.html

Author: The Oracle Team
"""

import torch
import torch.nn.functional as F
import torch.optim as optim
from torch_geometric.data import Data
from torch_geometric.loader import NeighborLoader
from src.models.graphsage_model import create_graphsage_model, GraphSAGEMiniBatch, GraphSAGEWithClustering
from typing import Optional, Literal, Tuple
import time


def generate_synthetic_graph(
    num_nodes: int = 1000,
    avg_degree: int = 10,
    num_features: int = 16
) -> Data:
    """
    Generate a synthetic graph for training.
    
    Args:
        num_nodes: Number of nodes in the graph
        avg_degree: Average degree per node
        num_features: Number of features per node
    
    Returns:
        PyTorch Geometric Data object
    """
    # Generate node features
    x = torch.randn(num_nodes, num_features)
    
    # Generate edges with approximate average degree
    num_edges = num_nodes * avg_degree // 2
    edge_index = torch.randint(0, num_nodes, (2, num_edges))
    
    # Generate edge labels (for edge prediction task)
    # Simulate safety scores: edges are safe if both nodes have low risk
    node_risk = torch.rand(num_nodes)
    x[:, 0] = node_risk  # Feature 0 is risk level
    
    src_risk = node_risk[edge_index[0]]
    dst_risk = node_risk[edge_index[1]]
    edge_labels = ((src_risk + dst_risk) / 2 < 0.5).float()
    
    return Data(x=x, edge_index=edge_index, edge_attr=edge_labels)


def train_minibatch_epoch(
    model: GraphSAGEMiniBatch,
    loader: NeighborLoader,
    optimizer: optim.Optimizer,
    device: torch.device
) -> float:
    """
    Train for one epoch using mini-batch gradient descent.
    
    Args:
        model: GraphSAGE model
        loader: NeighborLoader for mini-batch sampling
        optimizer: Optimizer
        device: Device for computation
    
    Returns:
        Average loss for the epoch
    """
    model.train()
    total_loss = 0
    total_batches = 0
    
    for batch in loader:
        batch = batch.to(device)
        optimizer.zero_grad()
        
        # Forward pass
        if model.task == 'edge':
            # Edge prediction task
            predictions = model(batch.x, batch.edge_index)
            
            # Get labels for the edges
            edge_labels = batch.edge_attr
            if edge_labels is None:
                # Generate synthetic labels if not provided
                src_risk = batch.x[batch.edge_index[0], 0]
                dst_risk = batch.x[batch.edge_index[1], 0]
                edge_labels = ((src_risk + dst_risk) / 2 < 0.5).float().unsqueeze(1)
            
            loss = F.binary_cross_entropy(predictions, edge_labels)
        
        elif model.task == 'node':
            # Node prediction task
            predictions = model(batch.x, batch.edge_index)
            node_labels = (batch.x[:, 0] < 0.5).float().unsqueeze(1)
            loss = F.binary_cross_entropy(predictions, node_labels)
        
        else:  # graph task
            predictions = model(batch.x, batch.edge_index, batch.batch)
            # Graph-level label (mean of node risks)
            if hasattr(batch, 'y'):
                graph_label = batch.y
            else:
                graph_label = (batch.x[:, 0].mean() < 0.5).float().unsqueeze(0).unsqueeze(1)
            loss = F.binary_cross_entropy(predictions, graph_label)
        
        # Backward pass
        loss.backward()
        optimizer.step()
        
        total_loss += loss.item()
        total_batches += 1
    
    return total_loss / total_batches if total_batches > 0 else 0


def train_with_clustering(
    model: GraphSAGEWithClustering,
    data: Data,
    optimizer: optim.Optimizer,
    device: torch.device,
    cluster_loss_weight: float = 0.1
) -> float:
    """
    Train GraphSAGE with clustering for one step.
    
    Args:
        model: GraphSAGE model with clustering
        data: Full graph data
        optimizer: Optimizer
        device: Device
        cluster_loss_weight: Weight for clustering loss
    
    Returns:
        Total loss
    """
    model.train()
    optimizer.zero_grad()
    
    data = data.to(device)
    
    # Forward pass
    node_embeddings, cluster_repr, cluster_probs = model(
        data.x, data.edge_index, return_clusters=True
    )
    
    # Node-level loss (edge prediction)
    src_embeddings = node_embeddings[data.edge_index[0]]
    dst_embeddings = node_embeddings[data.edge_index[1]]
    
    # Simple edge predictor using dot product
    edge_scores = torch.sigmoid(
        (src_embeddings * dst_embeddings).sum(dim=1, keepdim=True)
    )
    
    edge_labels = data.edge_attr
    if edge_labels is None:
        src_risk = data.x[data.edge_index[0], 0]
        dst_risk = data.x[data.edge_index[1], 0]
        edge_labels = ((src_risk + dst_risk) / 2 < 0.5).float().unsqueeze(1)
    
    main_loss = F.binary_cross_entropy(edge_scores, edge_labels)
    
    # Clustering loss: encourage diversity in cluster assignments
    # Use entropy regularization to prevent collapse
    cluster_dist = cluster_probs.mean(dim=0)  # [num_clusters]
    uniform_dist = torch.ones_like(cluster_dist) / model.num_clusters
    clustering_loss = F.kl_div(
        cluster_dist.log(), 
        uniform_dist, 
        reduction='batchmean'
    )
    
    # Total loss
    loss = main_loss + cluster_loss_weight * clustering_loss
    
    loss.backward()
    optimizer.step()
    
    return loss.item()


@torch.no_grad()
def evaluate_minibatch(
    model: GraphSAGEMiniBatch,
    loader: NeighborLoader,
    device: torch.device
) -> Tuple[float, float]:
    """
    Evaluate model on validation set.
    
    Returns:
        loss, accuracy
    """
    model.eval()
    total_loss = 0
    total_correct = 0
    total_samples = 0
    total_batches = 0
    
    for batch in loader:
        batch = batch.to(device)
        
        # Forward pass
        if model.task == 'edge':
            predictions = model(batch.x, batch.edge_index)
            edge_labels = batch.edge_attr
            if edge_labels is None:
                src_risk = batch.x[batch.edge_index[0], 0]
                dst_risk = batch.x[batch.edge_index[1], 0]
                edge_labels = ((src_risk + dst_risk) / 2 < 0.5).float().unsqueeze(1)
            
            loss = F.binary_cross_entropy(predictions, edge_labels)
            pred_binary = (predictions > 0.5).float()
            correct = (pred_binary == edge_labels).sum().item()
            samples = edge_labels.size(0)
        
        elif model.task == 'node':
            predictions = model(batch.x, batch.edge_index)
            node_labels = (batch.x[:, 0] < 0.5).float().unsqueeze(1)
            loss = F.binary_cross_entropy(predictions, node_labels)
            pred_binary = (predictions > 0.5).float()
            correct = (pred_binary == node_labels).sum().item()
            samples = node_labels.size(0)
        
        else:  # graph task
            predictions = model(batch.x, batch.edge_index, batch.batch)
            if hasattr(batch, 'y'):
                graph_label = batch.y
            else:
                graph_label = (batch.x[:, 0].mean() < 0.5).float().unsqueeze(0).unsqueeze(1)
            loss = F.binary_cross_entropy(predictions, graph_label)
            pred_binary = (predictions > 0.5).float()
            correct = (pred_binary == graph_label).sum().item()
            samples = graph_label.size(0)
        
        total_loss += loss.item()
        total_correct += correct
        total_samples += samples
        total_batches += 1
    
    avg_loss = total_loss / total_batches if total_batches > 0 else 0
    accuracy = total_correct / total_samples if total_samples > 0 else 0
    
    return avg_loss, accuracy


def train_graphsage_minibatch(
    aggregator: Literal['mean', 'lstm', 'pool'] = 'mean',
    num_epochs: int = 100,
    batch_size: int = 32,
    num_neighbors: list = [10, 5],
    learning_rate: float = 0.01,
    use_clustering: bool = False,
    device: Optional[str] = None
):
    """
    Main training function for GraphSAGE with mini-batch gradient descent.
    
    Args:
        aggregator: Type of aggregation ('mean', 'lstm', 'pool')
        num_epochs: Number of training epochs
        batch_size: Batch size (number of nodes per batch)
        num_neighbors: Number of neighbors to sample per layer [layer1, layer2, ...]
        learning_rate: Learning rate
        use_clustering: Whether to use clustering
        device: Device for computation
    """
    print("=" * 70)
    print("🚀 GraphSAGE Training with Mini-batch Gradient Descent")
    print("=" * 70)
    
    # Setup device
    if device is None:
        device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    else:
        device = torch.device(device)
    
    print(f"\n🖥️  Configuration:")
    print(f"   Device: {device}")
    print(f"   Aggregator: {aggregator}")
    print(f"   Batch size: {batch_size}")
    print(f"   Neighbor samples: {num_neighbors}")
    print(f"   Learning rate: {learning_rate}")
    print(f"   Use clustering: {use_clustering}")
    
    # Generate synthetic graph
    print(f"\n📊 Generating synthetic graph...")
    data = generate_synthetic_graph(num_nodes=1000, avg_degree=10, num_features=16)
    print(f"   Nodes: {data.num_nodes}")
    print(f"   Edges: {data.num_edges}")
    print(f"   Features: {data.num_node_features}")
    
    if use_clustering:
        # Use full-batch training with clustering
        print(f"\n🏗️  Building GraphSAGE with Clustering...")
        model = create_graphsage_model(
            in_channels=data.num_node_features,
            aggregator=aggregator,
            use_clustering=True,
            device=device
        )
        
        optimizer = optim.Adam(model.parameters(), lr=learning_rate)
        
        print(f"   Parameters: {sum(p.numel() for p in model.parameters()):,}")
        
        print(f"\n{'='*70}")
        print("🎯 Training with Clustering...")
        print(f"{'='*70}")
        
        start_time = time.time()
        
        for epoch in range(num_epochs):
            loss = train_with_clustering(model, data, optimizer, device)
            
            if (epoch + 1) % 10 == 0 or epoch == 0:
                print(f"Epoch [{epoch+1:3d}/{num_epochs}] | Loss: {loss:.4f}")
        
        total_time = time.time() - start_time
        
    else:
        # Use mini-batch training with neighbor sampling
        print(f"\n🏗️  Building GraphSAGE for Mini-batch Training...")
        model = create_graphsage_model(
            in_channels=data.num_node_features,
            aggregator=aggregator,
            use_clustering=False,
            task='edge',
            device=device
        )
        
        print(f"   Parameters: {sum(p.numel() for p in model.parameters()):,}")
        
        # Create data loaders with neighbor sampling
        # NeighborLoader samples a fixed number of neighbors per layer
        train_loader = NeighborLoader(
            data,
            num_neighbors=num_neighbors,
            batch_size=batch_size,
            shuffle=True,
            num_workers=0
        )
        
        val_loader = NeighborLoader(
            data,
            num_neighbors=num_neighbors,
            batch_size=batch_size,
            shuffle=False,
            num_workers=0
        )
        
        optimizer = optim.Adam(model.parameters(), lr=learning_rate)
        scheduler = optim.lr_scheduler.ReduceLROnPlateau(
            optimizer, mode='min', factor=0.5, patience=10
        )
        
        print(f"\n{'='*70}")
        print("🎯 Training with Mini-batch Gradient Descent...")
        print(f"{'='*70}")
        
        best_val_loss = float('inf')
        start_time = time.time()
        
        for epoch in range(num_epochs):
            # Training
            train_loss = train_minibatch_epoch(model, train_loader, optimizer, device)
            
            # Validation
            val_loss, val_acc = evaluate_minibatch(model, val_loader, device)
            
            # Update learning rate
            scheduler.step(val_loss)
            
            # Save best model
            if val_loss < best_val_loss:
                best_val_loss = val_loss
                torch.save({
                    'epoch': epoch,
                    'model_state_dict': model.state_dict(),
                    'optimizer_state_dict': optimizer.state_dict(),
                    'val_loss': val_loss,
                    'val_accuracy': val_acc,
                }, f'graphsage_{aggregator}_best.pth')
            
            # Logging
            if (epoch + 1) % 10 == 0 or epoch == 0:
                print(f"Epoch [{epoch+1:3d}/{num_epochs}] | "
                      f"Train Loss: {train_loss:.4f} | "
                      f"Val Loss: {val_loss:.4f} | "
                      f"Val Acc: {val_acc:.4f}")
        
        total_time = time.time() - start_time
    
    print(f"\n{'='*70}")
    print("✅ Training Completed!")
    print(f"{'='*70}")
    print(f"Total time: {total_time:.2f}s ({total_time/60:.2f} min)")
    print(f"Average time per epoch: {total_time/num_epochs:.2f}s")
    
    if not use_clustering:
        print(f"Best validation loss: {best_val_loss:.4f}")
        print(f"Model saved to: graphsage_{aggregator}_best.pth")
    
    return model


def compare_aggregators():
    """
    Compare different aggregation methods.
    """
    print("=" * 70)
    print("📊 Comparing GraphSAGE Aggregation Methods")
    print("=" * 70)
    
    aggregators = ['mean', 'lstm', 'pool']
    results = {}
    
    for aggr in aggregators:
        print(f"\n\n{'='*70}")
        print(f"Training with {aggr.upper()} aggregator")
        print(f"{'='*70}")
        
        model = train_graphsage_minibatch(
            aggregator=aggr,
            num_epochs=50,
            batch_size=32,
            num_neighbors=[10, 5],
            learning_rate=0.01,
            use_clustering=False
        )
        
        results[aggr] = model
    
    print(f"\n\n{'='*70}")
    print("✨ All aggregators trained successfully!")
    print(f"{'='*70}")
    
    return results


if __name__ == "__main__":
    # Test mini-batch training with mean aggregation
    print("Test 1: Mini-batch training with MEAN aggregation")
    train_graphsage_minibatch(
        aggregator='mean',
        num_epochs=50,
        batch_size=32,
        num_neighbors=[10, 5],
        use_clustering=False
    )
    
    print("\n\n")
    
    # Test clustering
    print("Test 2: Full-batch training with clustering")
    train_graphsage_minibatch(
        aggregator='mean',
        num_epochs=50,
        use_clustering=True
    )
    
    print("\n\n")
    
    # Compare all aggregators
    print("Test 3: Compare all aggregation methods")
    compare_aggregators()
