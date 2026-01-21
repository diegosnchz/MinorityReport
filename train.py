import torch
import logging
from models import CrimeGenerator, PoliceDiscriminator
from src.database.neo4j_client import db

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Device configuration
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

def train_precrime_gan(data, epochs=50):
    """
    Min-Max Game Training Loop.
    The Generator creates fake links, the Discriminator tries to catch them.
    """
    # Initialization
    in_dim = data.num_features
    hidden_dim = 64
    out_dim = 32 # Embedding dimension
    
    generator = CrimeGenerator(in_dim, hidden_dim, out_dim).to(device)
    discriminator = PoliceDiscriminator(out_dim, hidden_dim, 1).to(device) # Output 1 (Probability)

    # Separate Optimizers
    optimizer_G = torch.optim.Adam(generator.parameters(), lr=0.01)
    optimizer_D = torch.optim.Adam(discriminator.parameters(), lr=0.01)

    logger.info("🥊 Starting Adversarial Training...")

    # Simulation Loop
    for epoch in range(epochs):
        # ---------------------
        # 1. Train Police (Discriminator)
        # ---------------------
        optimizer_D.zero_grad()
        
        # Generate "potential crimes" (embeddings)
        fake_node_embeddings = generator(data.x.to(device), data.edge_index.to(device))
        
        # Discriminator evaluates real data vs generated
        # Note: In a real implementation we would sample positive/negative edges here.
        # For this demo architecture we pass node embeddings directly as simplified input
        real_pred = discriminator(data.x.to(device), data.edge_index.to(device)) 
        fake_pred = discriminator(fake_node_embeddings.detach(), data.edge_index.to(device))
        
        # Loss: Maximize accuracy on real and detection of fakes
        loss_D = -torch.mean(torch.log(real_pred + 1e-9) + torch.log(1 - fake_pred + 1e-9))
        loss_D.backward()
        optimizer_D.step()

        # ---------------------
        # 2. Train Criminal (Generator)
        # ---------------------
        optimizer_G.zero_grad()
        
        # Generator wants Discriminator to be wrong (classify fake as real)
        fake_node_embeddings = generator(data.x.to(device), data.edge_index.to(device))
        fake_pred = discriminator(fake_node_embeddings, data.edge_index.to(device))
        
        loss_G = -torch.mean(torch.log(fake_pred + 1e-9))
        loss_G.backward()
        optimizer_G.step()

        if epoch % 10 == 0:
            logger.info(f"Epoch {epoch} | Loss Police: {loss_D.item():.4f} | Loss Criminal: {loss_G.item():.4f}")

    return generator, discriminator

if __name__ == "__main__":
    from torch_geometric.data import Data
    
    # 1. Create Dummy Data for testing (Simulating Citizens/Locations)
    # 100 Nodes, 16 features each
    x = torch.randn((100, 16), device=device)
    # Random connections
    edge_index = torch.randint(0, 100, (2, 300), device=device)
    
    data = Data(x=x, edge_index=edge_index)
    
    logger.info("🔮 Initializing Pre-Crime System...")
    gen, disc = train_precrime_gan(data)
    
    # 2. Simulate export to Neo4j (Requires active database)
    # fake_predictions = [{'source': 1, 'target': 5, 'risk': 0.98}] 
    # db.update_predictions(fake_predictions)
    
    logger.info("✅ Training finished. Precogs ready.")
