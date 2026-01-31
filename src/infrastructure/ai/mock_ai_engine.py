"""
Infrastructure: Mock AI Prediction Engine
Implementación mock para testing sin dependencias de PyTorch
"""

from typing import List, Dict
import random
import logging

from src.domain.models.citizen import Citizen
from src.domain.models.location import Location
from src.domain.models.vision import PredictionOutput, Vision, RiskLevel
from src.domain.services.ai_engine import AIPredictionEngine

logger = logging.getLogger("MockAIPredictionEngine")


class MockAIPredictionEngine(AIPredictionEngine):
    """
    Adaptador Mock: Implementación de AIPredictionEngine sin PyTorch.
    
    Usado para testing y modo demo cuando no se requiere inferencia real.
    Calcula probabilidades basadas en heurísticas simples.
    """
    
    def __init__(self):
        self._ready = True
        self._model_version = "mock_v1.0"
    
    async def load_models(self) -> None:
        """No requiere cargar modelos (es mock)."""
        logger.info("Mock AI Engine initialized")
        self._ready = True
    
    async def predict_single(self, citizen: Citizen, location: Location) -> PredictionOutput:
        """Predice usando heurísticas simples."""
        # Calcular probabilidad basada en atributos
        base_prob = citizen.calculate_base_risk()
        location_factor = location.get_risk_score()
        
        # Combinar factores
        probability = (base_prob * 0.6) + (location_factor * 0.3)
        probability += random.uniform(-0.05, 0.05)  # Ruido
        probability = max(0.0, min(0.99, probability))
        
        # Determinar verdict
        if probability >= 0.9:
            verdict = RiskLevel.CRITICAL
        elif probability >= 0.7:
            verdict = RiskLevel.INTERVENE
        elif probability >= 0.4:
            verdict = RiskLevel.WATCHLIST
        else:
            verdict = RiskLevel.SAFE
        
        return PredictionOutput(
            citizen_id=citizen.id,
            location_id=location.id,
            probability=probability,
            verdict=verdict,
            confidence_score=0.7 + random.uniform(0, 0.2)
        )
    
    async def predict_batch(self, 
                          citizens: List[Citizen], 
                          locations: List[Location]) -> List[PredictionOutput]:
        """Predicción en batch."""
        results = []
        for citizen in citizens[:5]:  # Limitar para demo
            for location in locations[:3]:
                prediction = await self.predict_single(citizen, location)
                results.append(prediction)
        return results
    
    async def calculate_risk_score(self, citizen: Citizen) -> float:
        """Calcula score de riesgo."""
        return citizen.calculate_base_risk()
    
    async def explain_prediction(self, vision: Vision) -> Dict:
        """Genera explicación mock."""
        return {
            "model_version": self._model_version,
            "top_factors": [
                {"factor": "citizen_risk_seed", "importance": 0.5},
                {"factor": "location_env_risk", "importance": 0.3},
                {"factor": "time_of_day", "importance": 0.2}
            ],
            "confidence": 0.75,
            "method": "mock_explainer"
        }
    
    def is_ready(self) -> bool:
        return self._ready
    
    async def get_model_version(self) -> str:
        return self._model_version
