"""
Model package for MinorityReport AI system.

This package contains all neural network models for:
- Risk prediction (GAT-based)
- Movement prediction
- Behavior pattern analysis
- Crime prediction

Models are designed to:
1. Train on GPU for speed
2. Export for CPU inference in production
3. Integrate with Backend FastAPI services
4. Use dataEngineer graph data efficiently
"""

__all__ = [
    'RiskPredictionGAT',
    'MovementPredictionModel',
    'BehaviorPatternModel',
    'create_risk_model',
    'create_movement_model',
]
