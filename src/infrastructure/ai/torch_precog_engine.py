"""
Infrastructure Adapter: Torch Precog Engine
Implementación concreta del motor de IA usando PyTorch
"""

import torch
import logging
from typing import List, Dict

from src.domain.models.citizen import Citizen
from src.domain.models.location import Location
from src.domain.models.vision import PredictionOutput, Vision, RiskLevel
from src.domain.services.ai_engine import AIPredictionEngine

logger = logging.getLogger("TorchPrecogEngine")


class TorchPrecogEngine(AIPredictionEngine):
    """
    Adaptador de Infraestructura: Implementa AIPredictionEngine con PyTorch.
    
    Carga y ejecuta modelos GAT/GCN para predicción criminal.
    """
    
    def __init__(self):
        self._model = None
        self._device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self._model_version = "v1.0.0"
        self._ready = False
    
    async def load_models(self) -> None:
        """Carga los modelos de IA."""
        logger.info("Loading Precog Neural Networks...")
        
        try:
            # Importar aquí para evitar dependencia circular
            from app.models.neural_net import PoliceDiscriminator
            
            input_dim = 16
            hidden_dim = 32
            out_dim = 1
            
            self._model = PoliceDiscriminator(input_dim, hidden_dim, out_dim).to(self._device)
            self._model.eval()
            self._ready = True
            
            logger.info("Precogs are AWAKE and ready.")
        except Exception as e:
            logger.error(f"Failed to load models: {e}")
            raise
    
    async def predict_single(self, citizen: Citizen, location: Location) -> PredictionOutput:
        """Predice probabilidad de crimen para ciudadano-ubicación."""
        if not self._ready:
            raise RuntimeError("Engine not initialized")
        
        # Preparar features
        citizen_features = citizen.to_feature_vector()
        location_risk = location.get_risk_score()
        
        # Crear tensor de input
        input_tensor = torch.randn(1, 16).to(self._device)
        input_tensor[0, 0] = citizen.risk_seed
        input_tensor[0, 1] = float(citizen.criminal_degree) / 10.0
        input_tensor[0, 2] = location_risk
        
        # Inferencia
        empty_edges = torch.empty((2, 0), dtype=torch.long).to(self._device)
        
        with torch.no_grad():
            output = self._model(input_tensor, empty_edges)
            prob = output.item()
        
        # Ajustar con heurísticas
        adjusted_prob = (prob * 0.2) + (citizen.risk_seed * 0.6) + (location_risk * 0.2)
        adjusted_prob = min(adjusted_prob, 0.99)
        
        # Determinar verdict
        if adjusted_prob >= 0.9:
            verdict = RiskLevel.CRITICAL
        elif adjusted_prob >= 0.7:
            verdict = RiskLevel.INTERVENE
        elif adjusted_prob >= 0.4:
            verdict = RiskLevel.WATCHLIST
        else:
            verdict = RiskLevel.SAFE
        
        return PredictionOutput(
            citizen_id=citizen.id,
            location_id=location.id,
            probability=adjusted_prob,
            verdict=verdict,
            confidence_score=0.85
        )
    
    async def predict_batch(self, 
                          citizens: List[Citizen], 
                          locations: List[Location]) -> List[PredictionOutput]:
        """Predicción en batch."""
        results = []
        for citizen in citizens:
            for location in locations:
                prediction = await self.predict_single(citizen, location)
                results.append(prediction)
        return results
    
    async def calculate_risk_score(self, citizen: Citizen) -> float:
        """Calcula score de riesgo general."""
        base_risk = citizen.calculate_base_risk()
        # Añadir complejidad del modelo
        return min(base_risk * 1.1, 1.0)
    
    async def explain_prediction(self, vision: Vision) -> Dict:
        """Genera explicación XAI."""
        return {
            "model_version": self._model_version,
            "top_factors": [
                {"factor": "risk_seed", "importance": 0.6},
                {"factor": "location_risk", "importance": 0.3},
                {"factor": "social_connections", "importance": 0.1}
            ],
            "confidence": 0.85,
            "method": "GNNExplainer-compatible"
        }
    
    def is_ready(self) -> bool:
        return self._ready
    
    async def get_model_version(self) -> str:
        return self._model_version
