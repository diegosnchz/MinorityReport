"""
Model package for MinorityReport AI system.

This package contains all neural network models for:
- OracleNet (GCN + GAT hybrid for escape route optimization)
- GraphSAGE (scalable graph embeddings with mini-batch training)
- Risk prediction (GAT-based)
- Movement prediction
- Behavior pattern analysis

Models are designed to:
1. Train on GPU for speed
2. Export for CPU inference in production
3. Integrate with Backend FastAPI services
4. Use dataEngineer graph data efficiently
"""

from .oracle_net import OracleNet, create_oracle_net
from .graphsage_model import (
    GraphSAGEMiniBatch,
    GraphSAGEWithClustering,
    GraphSAGEAggregator,
    create_graphsage_model
)

__all__ = [
    # OracleNet
    'OracleNet',
    'create_oracle_net',
    # GraphSAGE
    'GraphSAGEMiniBatch',
    'GraphSAGEWithClustering',
    'GraphSAGEAggregator',
    'create_graphsage_model',
    # Legacy
    'RiskPredictionGAT',
    'MovementPredictionModel',
    'BehaviorPatternModel',
    'create_risk_model',
    'create_movement_model',
]
