import torch
import torch.nn.functional as F
from torch_geometric.nn import SAGEConv, GATConv

# Device configuration
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

class CrimeGenerator(torch.nn.Module):
    """
    THE CRIMINAL (GraphSAGE):
    Attempts to generate node embeddings that suggest new connections (crimes)
    based on local structure.
    """
    def __init__(self, in_channels, hidden_channels, out_channels):
        super(CrimeGenerator, self).__init__()
        # SAGEConv is inductive: learns to recognize neighborhood patterns
        self.conv1 = SAGEConv(in_channels, hidden_channels)
        self.conv2 = SAGEConv(hidden_channels, out_channels)

    def forward(self, x, edge_index):
        # x: Node features (history, base risk)
        # edge_index: Current connections
        x = self.conv1(x, edge_index)
        x = F.relu(x)
        x = F.dropout(x, p=0.2, training=self.training)
        x = self.conv2(x, edge_index)
        # Returns latent embeddings representing "criminal intent"
        return x

class PoliceDiscriminator(torch.nn.Module):
    """
    THE PRECOGS (GAT - Graph Attention Network):
    Evaluates if a link (connection between nodes) is a real crime or noise.
    Uses attention to decide which neighbors are important accomplices.
    """
    def __init__(self, in_channels, hidden_channels, out_channels):
        super(PoliceDiscriminator, self).__init__()
        # GAT uses 'heads' to look at different aspects of the relationship simultaneously
        self.conv1 = GATConv(in_channels, hidden_channels, heads=2, dropout=0.3)
        # Output of conv1 with 2 heads -> hidden_channels * 2
        self.conv2 = GATConv(hidden_channels * 2, out_channels, heads=1, concat=False, dropout=0.3)

    def forward(self, x, edge_index):
        x = F.dropout(x, p=0.3, training=self.training)
        x = self.conv1(x, edge_index)
        x = F.elu(x)
        x = F.dropout(x, p=0.3, training=self.training)
        x = self.conv2(x, edge_index)
        return torch.sigmoid(x) # Probability: 0 (Noise) to 1 (Real Crime/Risk)
