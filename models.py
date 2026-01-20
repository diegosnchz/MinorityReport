import torch
import torch.nn.functional as F
from torch_geometric.nn import SAGEConv, GATConv

class Generator(torch.nn.Module):
    def __init__(self, in_channels, out_channels):
        super(Generator, self).__init__()
        # GraphSAGE is inductive, allowing generation on unseen graph structures
        # We use it to transform noise (or initial state) into "criminal" feature embeddings
        self.conv1 = SAGEConv(in_channels, 64)
        self.conv2 = SAGEConv(64, 64)
        self.conv3 = SAGEConv(64, out_channels)

    def forward(self, x, edge_index):
        # x could be random noise or latent vectors
        x = self.conv1(x, edge_index)
        x = F.relu(x)
        x = F.dropout(x, p=0.2, training=self.training)
        
        x = self.conv2(x, edge_index)
        x = F.relu(x)
        x = F.dropout(x, p=0.2, training=self.training)
        
        x = self.conv3(x, edge_index)
        # Output embeddings representing likely criminal behavior patterns
        return torch.tanh(x) 

class Discriminator(torch.nn.Module):
    def __init__(self, in_channels):
        super(Discriminator, self).__init__()
        # GAT allows the model to learn which neighbors are most relevant (attention)
        # helping pinpoint the specific connections driving the "threat"
        self.conv1 = GATConv(in_channels, 64, heads=2, dropout=0.2)
        # Output of conv1 with 2 heads is 64*2 = 128
        self.conv2 = GATConv(64 * 2, 32, heads=1, dropout=0.2)
        self.linear = torch.nn.Linear(32, 1)

    def forward(self, x, edge_index):
        x = self.conv1(x, edge_index)
        x = F.elu(x)
        x = F.dropout(x, p=0.2, training=self.training)
        
        x = self.conv2(x, edge_index)
        x = F.elu(x)
        
        # Classification layer
        # Global pooling could be added here for graph-level classification, 
        # but for node-level risk (Minority Report style targeting individuals), we keep it node-level.
        x = self.linear(x)
        return torch.sigmoid(x)

if __name__ == "__main__":
    # Simple smoke test
    num_nodes = 10
    in_channels = 16
    out_channels = 16
    
    # Random graph features and edges
    x = torch.randn((num_nodes, in_channels))
    edge_index = torch.randint(0, num_nodes, (2, 20))
    
    gen = Generator(in_channels, out_channels)
    disc = Discriminator(out_channels)
    
    fake_data = gen(x, edge_index)
    print(f"Generator Output Shape: {fake_data.shape}")
    
    risk_score = disc(fake_data, edge_index)
    print(f"Discriminator Output Shape: {risk_score.shape}")
    print("Models instantiated successfully.")
