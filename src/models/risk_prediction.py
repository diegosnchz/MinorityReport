"""
Risk Prediction Model using Graph Attention Networks (GAT)

This model predicts citizen risk scores based on:
- Personal features (age, job, etc.)
- Social network (KNOWS relationships)
- Criminal influence (friends' criminal activity)

Designed for:
- GPU training
- CPU inference in production
- Integration with Backend API
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch_geometric.nn import GATConv


class RiskPredictionGAT(nn.Module):
    """
    Graph Attention Network for predicting citizen risk scores.
    
    Architecture:
    - Input: Node features (age, job encodings, criminal_degree)
    - GAT Layer 1: Multi-head attention (4 heads)
    - GAT Layer 2: Single-head attention
    - Output: Risk score (0-1)
    
    This model learns to:
    1. Attend to influential neighbors in social network
    2. Aggregate risk factors from connected citizens
    3. Predict individual risk propensity
    """
    
    def __init__(self, in_channels, hidden_channels=64, out_channels=1, 
                 heads=4, dropout=0.6):
        """
        Initialize the GAT model.
        
        Args:
            in_channels: Number of input features per node
            hidden_channels: Hidden layer size
            out_channels: Output size (1 for risk score)
            heads: Number of attention heads in first layer
            dropout: Dropout probability for regularization
        """
        super(RiskPredictionGAT, self).__init__()
        
        self.in_channels = in_channels
        self.hidden_channels = hidden_channels
        self.out_channels = out_channels
        self.heads = heads
        self.dropout = dropout
        
        # First GAT layer with multiple attention heads
        self.conv1 = GATConv(
            in_channels, 
            hidden_channels, 
            heads=heads, 
            dropout=dropout
        )
        
        # Second GAT layer (single head output)
        self.conv2 = GATConv(
            hidden_channels * heads, 
            out_channels, 
            heads=1, 
            concat=False, 
            dropout=dropout
        )
    
    def forward(self, x, edge_index):
        """
        Forward pass through the GAT network.
        
        Args:
            x: Node features [num_nodes, in_channels]
            edge_index: Graph connectivity [2, num_edges]
        
        Returns:
            Risk predictions [num_nodes, out_channels]
        """
        # First GAT layer + activation
        x = F.dropout(x, p=self.dropout, training=self.training)
        x = self.conv1(x, edge_index)
        x = F.elu(x)
        
        # Second GAT layer
        x = F.dropout(x, p=self.dropout, training=self.training)
        x = self.conv2(x, edge_index)
        
        # Sigmoid to get probability (0-1)
        x = torch.sigmoid(x)
        
        return x
    
    def get_attention_weights(self, x, edge_index, layer=1):
        """
        Extract attention weights for visualization.
        
        Args:
            x: Node features
            edge_index: Graph connectivity
            layer: Which layer's attention to extract (1 or 2)
        
        Returns:
            Attention weights and edge indices
        """
        self.eval()
        with torch.no_grad():
            x = F.dropout(x, p=self.dropout, training=False)
            if layer == 1:
                _, attention_weights = self.conv1(x, edge_index, return_attention_weights=True)
                return attention_weights
            else:
                x = self.conv1(x, edge_index)
                x = F.elu(x)
                x = F.dropout(x, p=self.dropout, training=False)
                _, attention_weights = self.conv2(x, edge_index, return_attention_weights=True)
                return attention_weights


class RiskPredictionDeepGAT(nn.Module):
    """
    Deeper GAT architecture for complex risk patterns.
    
    Uses 3 GAT layers with residual connections for better
    information flow through the network.
    """
    
    def __init__(self, in_channels, hidden_channels=64, out_channels=1,
                 heads=4, dropout=0.6):
        super(RiskPredictionDeepGAT, self).__init__()
        
        self.in_channels = in_channels
        self.hidden_channels = hidden_channels
        self.heads = heads
        self.dropout = dropout
        
        # Input projection
        self.input_proj = nn.Linear(in_channels, hidden_channels)
        
        # GAT layers
        self.conv1 = GATConv(hidden_channels, hidden_channels, heads=heads, dropout=dropout)
        self.conv2 = GATConv(hidden_channels * heads, hidden_channels, heads=heads, dropout=dropout)
        self.conv3 = GATConv(hidden_channels * heads, hidden_channels, heads=1, concat=False, dropout=dropout)
        
        # Output layer
        self.output = nn.Linear(hidden_channels, out_channels)
        
    def forward(self, x, edge_index):
        # Project input
        x = self.input_proj(x)
        identity = x
        
        # Layer 1
        x = F.dropout(x, p=self.dropout, training=self.training)
        x = self.conv1(x, edge_index)
        x = F.elu(x)
        
        # Layer 2
        x = F.dropout(x, p=self.dropout, training=self.training)
        x = self.conv2(x, edge_index)
        x = F.elu(x)
        
        # Layer 3
        x = F.dropout(x, p=self.dropout, training=self.training)
        x = self.conv3(x, edge_index)
        
        # Add residual connection
        x = x + identity
        x = F.elu(x)
        
        # Output
        x = self.output(x)
        x = torch.sigmoid(x)
        
        return x


def create_risk_model(num_features, hidden_channels=64, heads=4, 
                     deep=False, device='cpu'):
    """
    Factory function to create risk prediction models.
    
    Args:
        num_features: Number of input features
        hidden_channels: Hidden layer size
        heads: Number of attention heads
        deep: Whether to use deep architecture
        device: Device to place model on ('cpu' or 'cuda')
    
    Returns:
        Risk prediction model
    """
    if deep:
        model = RiskPredictionDeepGAT(
            in_channels=num_features,
            hidden_channels=hidden_channels,
            out_channels=1,
            heads=heads
        )
    else:
        model = RiskPredictionGAT(
            in_channels=num_features,
            hidden_channels=hidden_channels,
            out_channels=1,
            heads=heads
        )
    
    return model.to(device)


def export_risk_model_for_production(model, example_input, save_path):
    """
    Export model for CPU inference in production.
    
    Converts to TorchScript for optimized CPU inference in Backend.
    
    Args:
        model: Trained GAT model
        example_input: Example (x, edge_index) tuple for tracing
        save_path: Where to save the exported model
    """
    model.eval()
    model.cpu()
    
    # Convert to TorchScript via tracing
    x, edge_index = example_input
    traced_model = torch.jit.trace(model, (x, edge_index))
    
    # Optimize for inference
    traced_model = torch.jit.optimize_for_inference(traced_model)
    
    # Save
    torch.jit.save(traced_model, save_path)
    print(f"✅ Model exported to {save_path} (optimized for CPU)")
    
    return traced_model


if __name__ == "__main__":
    # Test the model
    print("Testing Risk Prediction GAT...")
    
    # Create dummy data
    num_nodes = 100
    num_features = 16
    num_edges = 300
    
    x = torch.randn(num_nodes, num_features)
    edge_index = torch.randint(0, num_nodes, (2, num_edges))
    
    # Create model
    model = create_risk_model(num_features, hidden_channels=32, heads=4)
    
    # Forward pass
    output = model(x, edge_index)
    
    print(f"Input shape: {x.shape}")
    print(f"Edge index shape: {edge_index.shape}")
    print(f"Output shape: {output.shape}")
    print(f"Output range: [{output.min():.4f}, {output.max():.4f}]")
    print(f"Model parameters: {sum(p.numel() for p in model.parameters())}")
    print("✅ Model test passed!")
