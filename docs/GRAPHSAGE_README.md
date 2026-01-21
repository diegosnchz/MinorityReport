# GraphSAGE Implementation with Mini-batch Training and Neighbor Sampling

## Overview

This implementation adds GraphSAGE (Graph Sample and Aggregate) with the following features as requested:

### Key Features

1. **Mini-batch Gradient Descent**
   - Uses PyTorch Geometric's `NeighborLoader` for efficient mini-batch sampling
   - Configurable batch sizes (supports very small batches as requested)
   - Reduced memory footprint for large graphs

2. **Neighbor Sampling**
   - Samples a fixed number of neighbors per layer
   - Configurable sampling strategy: `[10, 5]` means 10 neighbors in layer 1, 5 in layer 2
   - Enables training on large graphs that don't fit in GPU memory

3. **Multiple Aggregation Methods**
   - **Mean**: Simple average aggregation (GCN-like approach)
   - **LSTM**: Sequential aggregation using LSTM layers
   - **Pooling**: Element-wise max pooling aggregation

4. **Clustering Support**
   - Soft clustering with learnable cluster assignments
   - Hierarchical graph structure learning
   - Entropy regularization to prevent cluster collapse

5. **Production-Ready Environment**
   - Modular design for easy integration
   - Support for node, edge, and graph-level tasks
   - Efficient mini-batch training for scalability

## Files

### `graphsage_model.py`
Contains the GraphSAGE model implementations:
- `GraphSAGEAggregator`: Base model with configurable aggregation
- `GraphSAGEWithClustering`: Model with clustering support
- `GraphSAGEMiniBatch`: Model optimized for mini-batch training

### `train_graphsage_minibatch.py`
Training script that demonstrates:
- Mini-batch training with neighbor sampling
- Comparison of different aggregation methods
- Full-batch training with clustering

## Usage

### Basic Mini-batch Training

```python
from train_graphsage_minibatch import train_graphsage_minibatch

# Train with mean aggregation and mini-batches
model = train_graphsage_minibatch(
    aggregator='mean',
    num_epochs=100,
    batch_size=32,           # Small batch size
    num_neighbors=[10, 5],   # Neighbor sampling strategy
    learning_rate=0.01
)
```

### Compare All Aggregation Methods

```python
from train_graphsage_minibatch import compare_aggregators

# Train and compare mean, LSTM, and pooling aggregators
results = compare_aggregators()
```

### Training with Clustering

```python
model = train_graphsage_minibatch(
    aggregator='mean',
    num_epochs=100,
    use_clustering=True
)
```

### Direct Model Usage

```python
from graphsage_model import create_graphsage_model
import torch

# Create model with LSTM aggregation
model = create_graphsage_model(
    in_channels=16,
    aggregator='lstm',
    use_clustering=False,
    task='edge'
)

# Example inference
x = torch.randn(100, 16)  # Node features
edge_index = torch.randint(0, 100, (2, 300))  # Edges

predictions = model(x, edge_index)
```

## Architecture Details

### GraphSAGE Aggregation

The model implements three aggregation methods as described in the GraphSAGE paper:

1. **Mean Aggregator** (GCN-like):
   ```
   h_v^k = σ(W^k · MEAN({h_u^{k-1}, ∀u ∈ N(v) ∪ {v}}))
   ```

2. **LSTM Aggregator**:
   - Uses LSTM to aggregate neighbor features sequentially
   - Captures ordering information in neighborhoods

3. **Pooling Aggregator**:
   ```
   h_v^k = σ(W^k · MAX({ReLU(W_pool · h_u^{k-1}), ∀u ∈ N(v)}))
   ```

### Neighbor Sampling

For scalability, we sample a fixed number of neighbors per layer:
- Layer 1: Sample K₁ neighbors
- Layer 2: Sample K₂ neighbors from each of the K₁ neighbors
- Total computation: O(K₁ × K₂) instead of O(d²) where d is degree

### Clustering

The clustering module learns soft cluster assignments:
1. Node embeddings → Cluster probabilities (softmax)
2. Cluster representations = weighted sum of nodes
3. Loss includes entropy regularization for diversity

## Benefits

### Mini-batch Gradient Descent Benefits (as specified)

1. **Improved Accuracy**
   - Mini-batches reduce overfitting through gradient averaging
   - Lower variance in error rates

2. **Increased Speed**
   - Batches processed in parallel
   - Faster training than full-batch or SGD

3. **Improved Scalability**
   - Can handle graphs larger than GPU memory
   - Efficient neighbor sampling reduces computation

## Configuration

### Recommended Settings

For **very small batches** (as requested):
```python
batch_size=16  # or 32
num_neighbors=[5, 3]  # Conservative sampling
```

For **large graphs**:
```python
batch_size=128
num_neighbors=[25, 10]  # More neighbors per layer
```

For **production deployment**:
```python
aggregator='mean'  # Fastest
batch_size=64
num_neighbors=[15, 10]  # Balanced
```

## Integration with Existing Code

The GraphSAGE implementation can be integrated with the existing models:

```python
# Replace the Generator in models.py with GraphSAGE
from graphsage_model import GraphSAGEAggregator

class ImprovedGenerator(torch.nn.Module):
    def __init__(self, in_channels, out_channels):
        super().__init__()
        self.sage = GraphSAGEAggregator(
            in_channels=in_channels,
            hidden_channels=64,
            out_channels=out_channels,
            num_layers=3,
            aggregator='mean'
        )
    
    def forward(self, x, edge_index):
        return torch.tanh(self.sage(x, edge_index))
```

## Reference

Implementation based on:
- Hamilton et al. "Inductive Representation Learning on Large Graphs" (NeurIPS 2017)
- https://mlabonne.github.io/blog/posts/2022-04-06-GraphSAGE.html

## Testing

Run the smoke tests:
```bash
# Test the models
python graphsage_model.py

# Test mini-batch training
python train_graphsage_minibatch.py
```

## Future Enhancements

Possible extensions:
- [ ] Integration with Neo4j for real graph data
- [ ] Food pairing AI application example
- [ ] Semantic web (RDF/RDFS) support
- [ ] Multi-GPU training
- [ ] Dynamic batch size adjustment
- [ ] Custom neighbor sampling strategies
