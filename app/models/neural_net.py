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

# --- TGN IMPLEMENTATION (PART 10) ---
from torch_geometric.nn import TGNMemory, TransformerConv
from torch_geometric.nn.models.tgn import (LastNeighborLoader, IdentityMessage,
                                           LastAggregator)

class PrecogTGN(torch.nn.Module):
    def __init__(self, num_nodes, raw_msg_dim, memory_dim, time_dim, embedding_dim):
        super().__init__()
        # 1. EL LÓBULO TEMPORAL (Memoria)
        # Almacena el estado oculto (S) de cada ciudadano y ubicación.
        # Evoluciona con cada interacción.
        self.memory = TGNMemory(
            num_nodes=num_nodes,
            raw_msg_dim=raw_msg_dim,
            memory_dim=memory_dim,
            time_dim=time_dim,
            message_module=IdentityMessage(raw_msg_dim, memory_dim, time_dim),
            aggregator_module=LastAggregator(),
        )

        # 2. EL LÓBULO DE RAZONAMIENTO (Embedding)
        # Usa Graph Attention (Transformer) sobre la memoria actual + vecinos
        self.embedding_gnn = TransformerConv(
            in_channels=memory_dim,
            out_channels=embedding_dim,
            heads=2,
            dropout=0.1
        )

        # 3. EL PRECOG (Clasificador)
        # Decide si el enlace (src -> dst) es un crimen futuro
        self.predictor = torch.nn.Linear(embedding_dim * 2, 1)

    def forward(self, n_id, edge_index, edge_time):
        """
        n_id: IDs de los nodos involucrados en el evento actual
        """
        # A. Recuperar la memoria actualizada hasta este milisegundo
        # (El TGNMemory se actualiza externamente antes del forward)
        memory = self.memory(n_id)

        # B. Generar Embeddings Espaciales
        # Combinamos la memoria histórica con la estructura actual del grafo
        emb = self.embedding_gnn(memory, edge_index)
        return emb

    def predict_link(self, src_emb, dst_emb):
        # Concatenar embedding de Ciudadano + Ubicación para predecir riesgo
        h = torch.cat([src_emb, dst_emb], dim=1)
        return torch.sigmoid(self.predictor(h))
