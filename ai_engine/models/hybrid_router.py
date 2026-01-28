
# ai_engine/models/hybrid_router.py
import torch
import torch.nn.functional as F
from torch_geometric.nn import GATConv
import xgboost as xgb
import numpy as np

# Check for GPU availability for XGBoost
try:
    import cudf
    TREE_METHOD = 'gpu_hist'
except ImportError:
    TREE_METHOD = 'hist'

class HybridRouter(torch.nn.Module):
    """
    The Core of the Hybrid Intelligence.
    Combines:
    1. XGBoost: Handling tabular risk factors (Weather, Time, Patrol Density).
    2. GAT (Graph Attention Network): Handling topological risk (Escape Routes).
    """
    def __init__(self, in_channels, out_channels, xgb_params=None):
        super(HybridRouter, self).__init__()
        
        # --- 1. Toplogical Brain (PyTorch Geometric) ---
        # GAT Layer 1: Captures immediate neighborhood influence
        self.gat1 = GATConv(in_channels, 16, heads=8, dropout=0.6)
        # GAT Layer 2: Aggregates multi-hop risk
        self.gat2 = GATConv(16 * 8, out_channels, heads=1, concat=False, dropout=0.6)
        
        # --- 2. Tabular Brain (XGBoost) ---
        # This sits "outside" the autograd graph usually, but we integrate the flow.
        self.xgb_params = xgb_params or {
            'objective': 'binary:logistic',
            'tree_method': TREE_METHOD,
            'eval_metric': 'logloss',
            'max_depth': 6,
            'eta': 0.1
        }
        self.xgb_model = None

    def train_xgboost(self, X_tabular, y):
        """
        Trains the Tabular Brain.
        X_tabular: cuDF DataFrame or Numpy array.
        """
        dtrain = xgb.DMatrix(X_tabular, label=y)
        self.xgb_model = xgb.train(self.xgb_params, dtrain, num_boost_round=100)
        print(f"XGBoost Trained. Tree Method: {self.xgb_params['tree_method']}")

    def _predict_tabular(self, x_tabular):
        if self.xgb_model is None:
            return None
        if hasattr(self.xgb_model, "inplace_predict"):
            return self.xgb_model.inplace_predict(x_tabular)
        dmatrix = xgb.DMatrix(x_tabular)
        return self.xgb_model.predict(dmatrix)

    def forward(self, x, edge_index, x_tabular):
        """
        The Hybrid Forward Pass.
        
        Args:
            x (Tensor): Node feature matrix (initial embeddings).
            edge_index (LongTensor): Graph connectivity.
            x_tabular (Array/DataFrame): Tabular features for the same nodes.
        
        Returns:
            Tensor: Final Risk Probability per Node.
        """
        # --- Step 1: Query Tabular Brain ---
        # We get the "Base Risk" from XGBoost
        if self.xgb_model:
            xgb_risk_score = self._predict_tabular(x_tabular)
            
            # Convert to Tensor and Inject into Graph
            # We treat the XGB score as a "Super Feature"
            xgb_risk_tensor = torch.as_tensor(xgb_risk_score, dtype=torch.float32, device=x.device).unsqueeze(1)
            
            # Concatenate XGB output to Node Features
            # New shape: [num_nodes, in_channels + 1]
            x = torch.cat([x, xgb_risk_tensor], dim=1)
        else:
            # Fallback for untrained state or pure GAT mode
            # Padding with zeros if XGB not ready
            zero_pad = torch.zeros((x.size(0), 1), device=x.device)
            x = torch.cat([x, zero_pad], dim=1)

        # --- Step 2: Query Topological Brain (GAT) ---
        # Now the GAT sees not just the node features, but also the XGBoost risk assessment
        x = F.dropout(x, p=0.6, training=self.training)
        
        # Convolution 1
        x = F.elu(self.gat1(x, edge_index))
        x = F.dropout(x, p=0.6, training=self.training)
        
        # Convolution 2
        x = self.gat2(x, edge_index)
        
        # Final Activation (Probability)
        return torch.sigmoid(x)
