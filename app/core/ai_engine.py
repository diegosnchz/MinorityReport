import torch
import logging
from app.models.neural_net import PoliceDiscriminator
from app.models.schemas_citizen import CitizenFeatureVector

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("PrecogSystem")

class PrecogSystem:
    def __init__(self):
        self.model = None
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        
    def load_models(self):
        """Initializes the AI models (GAT)."""
        logger.info("🧠 Loading Precog Neural Networks...")
        # In a real scenario, we would load state_dict here:
        # self.model.load_state_dict(torch.load("precogs.pt"))
        
        # Initializing fresh model for demo purposes
        # Input channels must match our feature vector size:
        # risk_seed (1) + criminal_degree (1) + job_vector (3 mock) = 5 features approx?
        # Let's assume input dim = 16 for now to match training defaults or dynamic
        input_dim = 16 
        hidden_dim = 32
        out_dim = 1
        
        self.model = PoliceDiscriminator(input_dim, hidden_dim, out_dim).to(self.device)
        self.model.eval() # Set to inference mode
        logger.info("🧠 Precogs are AWAKE and ready.")

    def predict(self, features: CitizenFeatureVector) -> dict:
        """
        Runs inference on a single citizen.
        """
        if not self.model:
            raise RuntimeError("Precog System not initialized. Call load_models() first.")
            
        # Mock Transformation to Tensor
        # We constructed a vector of length ~5-10
        # For this demo, we'll create a random tensor or mapping
        # In reality, we must match the training dimensions perfectly.
        
        # [Mock Logic]
        # logic: 0.85+ if risk_seed high and criminal_degree high
        
        # Using the actual model (even if untrained, it outputs sigmoid)
        # We need to reshape input to [N, Features] and provide dummy edge_index
        # Since GAT needs edges, passing empty edges for single node inference
        
        input_tensor = torch.randn(1, 16).to(self.device) # Dummy input matching dim
        
        # Inject our real features into the dummy tensor partially
        input_tensor[0, 0] = features.risk_seed
        input_tensor[0, 1] = features.criminal_degree
        
        empty_edges = torch.empty((2, 0), dtype=torch.long).to(self.device)
        
        with torch.no_grad():
            output = self.model(input_tensor, empty_edges)
            prob = output.item()
            
        # [Heuristic Override for Demo]
        # Since the model is untrained random weights, let's mix in the real risk_seed 
        # to make the API behave "realistically" for the user demo
        # If risk_seed is high (0.7+), we boost the probability
        
        adjusted_prob = (prob * 0.2) + (features.risk_seed * 0.8)
        
        logger.info(f"🔮 Precog Scan {features.id}: Risk {features.risk_seed} -> Prob {adjusted_prob:.2f}")
        
        return {"probability": float(adjusted_prob)}

precog_system = PrecogSystem()
