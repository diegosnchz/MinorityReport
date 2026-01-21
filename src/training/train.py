import torch
import torch.nn.functional as F
from src.models.models import Generator, Discriminator
from torch_geometric.data import Data

def train_gan(num_epochs=100, num_nodes=100, feature_dim=16):
    # Setup Device
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    print(f"Using device: {device}")

    # Hyperparameters
    lr = 0.001
    
    # Initialize Models
    generator = Generator(in_channels=feature_dim, out_channels=feature_dim).to(device)
    discriminator = Discriminator(in_channels=feature_dim).to(device)
    
    # Optimizers
    g_optimizer = torch.optim.Adam(generator.parameters(), lr=lr)
    d_optimizer = torch.optim.Adam(discriminator.parameters(), lr=lr)
    
    # Dummy Graph Data (In a real scenario, this comes from Neo4j)
    # 100 nodes, with random connections
    edge_index = torch.randint(0, num_nodes, (2, 300)).to(device)
    
    # Real data (Normal behavior patterns)
    real_data = torch.randn((num_nodes, feature_dim)).to(device)
    
    # Labels
    real_labels = torch.ones((num_nodes, 1)).to(device)
    fake_labels = torch.zeros((num_nodes, 1)).to(device)

    print("Starting adversarial training (Pre-Crime Simulation)...")

    for epoch in range(num_epochs):
        # ==================================================================
        # 1. Train Discriminator (The Police)
        # ==================================================================
        # Goal: Maximize log(D(x)) + log(1 - D(G(z)))
        
        # Train on Real Data
        d_optimizer.zero_grad()
        real_output = discriminator(real_data, edge_index)
        d_loss_real = F.binary_cross_entropy(real_output, real_labels)
        
        # Train on Fake Data (Generated "Crimes")
        # Noise input for Generator
        z = torch.randn((num_nodes, feature_dim)).to(device)
        fake_data = generator(z, edge_index)
        
        # We detach fake_data so we don't backpropagate through the Generator yet
        fake_output = discriminator(fake_data.detach(), edge_index)
        d_loss_fake = F.binary_cross_entropy(fake_output, fake_labels)
        
        d_loss = d_loss_real + d_loss_fake
        d_loss.backward()
        d_optimizer.step()
        
        # ==================================================================
        # 2. Train Generator (The Crime/Pre-Crime Simulator)
        # ==================================================================
        # Goal: Maximize log(D(G(z))) -> Trick the discriminator
        
        g_optimizer.zero_grad()
        
        # We want the discriminator to classify these as REAL (1)
        # This forces the generator to create plausible criminal patterns
        fake_output_for_gen = discriminator(fake_data, edge_index)
        g_loss = F.binary_cross_entropy(fake_output_for_gen, real_labels)
        
        g_loss.backward()
        g_optimizer.step()
        
        # Logging
        if (epoch + 1) % 10 == 0:
            print(f"Epoch [{epoch+1}/{num_epochs}] | "
                  f"D Loss: {d_loss.item():.4f} | "
                  f"G Loss: {g_loss.item():.4f}")

    print("Training finished.")
    return generator, discriminator

if __name__ == "__main__":
    train_gan()
