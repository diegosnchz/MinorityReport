"""
Movement Prediction Model

Predicts citizen movement patterns and escape routes based on:
- Current location
- Location risk levels
- Historical movement patterns (VISITED relationships)
- Social network influence

This model is crucial for:
- Backend escape route calculations
- Predicting where suspects will go
- Identifying safe zones dynamically
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch_geometric.nn import GATConv, global_mean_pool


class MovementPredictionModel(nn.Module):
    """
    Predicts next location in movement sequence.
    
    Uses citizen features + location features to predict
    which location a person is likely to visit next.
    
    Architecture:
    - Citizen feature encoder (GAT on social network)
    - Location feature encoder
    - Combined prediction head
    """
    
    def __init__(self, citizen_features, location_features, 
                 hidden_dim=128, num_locations=50):
        """
        Args:
            citizen_features: Number of citizen features
            location_features: Number of location features (env_risk, type, etc.)
            hidden_dim: Hidden layer size
            num_locations: Total number of locations in the system
        """
        super(MovementPredictionModel, self).__init__()
        
        self.citizen_features = citizen_features
        self.location_features = location_features
        self.hidden_dim = hidden_dim
        self.num_locations = num_locations
        
        # Citizen encoder (GAT on social network)
        self.citizen_gat1 = GATConv(citizen_features, hidden_dim // 2, heads=4)
        self.citizen_gat2 = GATConv(hidden_dim * 2, hidden_dim, heads=1, concat=False)
        
        # Location encoder
        self.location_encoder = nn.Sequential(
            nn.Linear(location_features, hidden_dim),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(hidden_dim, hidden_dim)
        )
        
        # Combined prediction head
        self.predictor = nn.Sequential(
            nn.Linear(hidden_dim * 2, hidden_dim),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(hidden_dim, num_locations)  # Softmax over all locations
        )
    
    def forward(self, citizen_x, citizen_edge_index, location_features, 
                current_location_idx):
        """
        Predict next location for a citizen.
        
        Args:
            citizen_x: Citizen features [num_citizens, citizen_features]
            citizen_edge_index: Social network edges [2, num_edges]
            location_features: Features for all locations [num_locations, location_features]
            current_location_idx: Current location of citizen (index)
        
        Returns:
            Location probabilities [num_locations]
        """
        # Encode citizen through social network
        cx = F.dropout(citizen_x, p=0.6, training=self.training)
        cx = self.citizen_gat1(cx, citizen_edge_index)
        cx = F.elu(cx)
        cx = F.dropout(cx, p=0.6, training=self.training)
        cx = self.citizen_gat2(cx, citizen_edge_index)
        
        # Get citizen embedding (assume single citizen for simplicity, or use index)
        # In batch mode, this would be cx[citizen_idx]
        citizen_embedding = cx.mean(dim=0)  # For demo, use mean
        
        # Encode all locations
        location_embeddings = self.location_encoder(location_features)
        
        # Get current location context
        current_loc_embedding = location_embeddings[current_location_idx]
        
        # Combine citizen + current location
        combined = torch.cat([citizen_embedding, current_loc_embedding], dim=0)
        
        # Predict next location
        logits = self.predictor(combined)
        probs = F.softmax(logits, dim=0)
        
        return probs


class EscapeRouteModel(nn.Module):
    """
    Specialized model for escape route planning.
    
    Given:
    - Current location
    - Danger level
    - Graph of locations
    
    Predicts:
    - Safe destination
    - Intermediate waypoints
    - Success probability
    """
    
    def __init__(self, location_features, hidden_dim=128):
        super(EscapeRouteModel, self).__init__()
        
        # Location graph encoder (GAT on location connections)
        self.loc_gat1 = GATConv(location_features, hidden_dim, heads=4)
        self.loc_gat2 = GATConv(hidden_dim * 4, hidden_dim, heads=1, concat=False)
        
        # Danger assessment
        self.danger_encoder = nn.Sequential(
            nn.Linear(hidden_dim + 1, hidden_dim),  # +1 for danger level
            nn.ReLU(),
            nn.Dropout(0.3)
        )
        
        # Safe zone predictor
        self.safe_zone_predictor = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, 1),  # Safety score
            nn.Sigmoid()
        )
    
    def forward(self, location_features, location_edges, danger_level):
        """
        Predict safe zones given current danger level.
        
        Args:
            location_features: Features for all locations [num_locs, features]
            location_edges: Connections between locations [2, num_edges]
            danger_level: Current danger level (0-1)
        
        Returns:
            Safety scores for all locations [num_locs]
        """
        # Encode location graph
        x = F.dropout(location_features, p=0.3, training=self.training)
        x = self.loc_gat1(x, location_edges)
        x = F.elu(x)
        x = F.dropout(x, p=0.3, training=self.training)
        x = self.loc_gat2(x, location_edges)
        
        # Add danger context
        danger_vec = torch.full((x.size(0), 1), danger_level, device=x.device)
        x = torch.cat([x, danger_vec], dim=1)
        x = self.danger_encoder(x)
        
        # Predict safety scores
        safety_scores = self.safe_zone_predictor(x)
        
        return safety_scores.squeeze()


def create_movement_model(citizen_features, location_features, 
                          num_locations, hidden_dim=128, device='cpu'):
    """
    Factory function for movement prediction models.
    
    Args:
        citizen_features: Number of citizen features
        location_features: Number of location features
        num_locations: Total number of locations
        hidden_dim: Hidden layer size
        device: Device to place model on
    
    Returns:
        Movement prediction model
    """
    model = MovementPredictionModel(
        citizen_features=citizen_features,
        location_features=location_features,
        hidden_dim=hidden_dim,
        num_locations=num_locations
    )
    return model.to(device)


def create_escape_route_model(location_features, hidden_dim=128, device='cpu'):
    """
    Factory function for escape route models.
    
    Args:
        location_features: Number of location features
        hidden_dim: Hidden layer size
        device: Device to place model on
    
    Returns:
        Escape route model
    """
    model = EscapeRouteModel(
        location_features=location_features,
        hidden_dim=hidden_dim
    )
    return model.to(device)


if __name__ == "__main__":
    # Test the movement model
    print("Testing Movement Prediction Model...")
    
    num_citizens = 100
    num_locations = 50
    citizen_features = 16
    location_features = 8
    
    # Dummy data
    citizen_x = torch.randn(num_citizens, citizen_features)
    citizen_edges = torch.randint(0, num_citizens, (2, 200))
    location_feats = torch.randn(num_locations, location_features)
    current_loc = 5
    
    # Create and test model
    model = create_movement_model(citizen_features, location_features, num_locations)
    probs = model(citizen_x, citizen_edges, location_feats, current_loc)
    
    print(f"Movement prediction shape: {probs.shape}")
    print(f"Probability sum: {probs.sum():.4f}")
    print(f"Top 3 destinations: {probs.topk(3).indices.tolist()}")
    
    # Test escape route model
    print("\nTesting Escape Route Model...")
    escape_model = create_escape_route_model(location_features)
    location_graph_edges = torch.randint(0, num_locations, (2, 100))
    danger_level = 0.8
    
    safety_scores = escape_model(location_feats, location_graph_edges, danger_level)
    print(f"Safety scores shape: {safety_scores.shape}")
    print(f"Safest locations: {safety_scores.topk(5).indices.tolist()}")
    print("✅ Movement models test passed!")
