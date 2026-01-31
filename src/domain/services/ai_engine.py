"""
Service Port: AIPredictionEngine
Interfaz para motores de IA de predicción criminal
"""

from abc import ABC, abstractmethod
from typing import List, Dict

from src.domain.models.citizen import Citizen, CitizenFeatureVector
from src.domain.models.location import Location
from src.domain.models.vision import PredictionOutput, Vision


class AIPredictionEngine(ABC):
    """
    Puerto para el motor de IA de predicción.
    
    El dominio define qué necesita de la IA, pero no cómo se implementa.
    Puede ser PyTorch, TensorFlow, o incluso un mock para testing.
    """
    
    @abstractmethod
    async def load_models(self) -> None:
        """Carga los modelos de IA en memoria."""
        pass
    
    @abstractmethod
    async def predict_single(self, citizen: Citizen, location: Location) -> PredictionOutput:
        """
        Predice la probabilidad de crimen para un ciudadano en una ubicación.
        """
        pass
    
    @abstractmethod
    async def predict_batch(self, 
                          citizens: List[Citizen], 
                          locations: List[Location]) -> List[PredictionOutput]:
        """
        Predice probabilidades para múltiples combinaciones ciudadano-ubicación.
        """
        pass
    
    @abstractmethod
    async def calculate_risk_score(self, citizen: Citizen) -> float:
        """Calcula un score de riesgo general para un ciudadano."""
        pass
    
    @abstractmethod
    async def explain_prediction(self, vision: Vision) -> Dict:
        """
        Genera explicación XAI de por qué se hizo una predicción.
        Retorna factores de importancia (SHAP values, attention weights, etc.)
        """
        pass
    
    @abstractmethod
    def is_ready(self) -> bool:
        """Verifica si el motor está listo para hacer predicciones."""
        pass
    
    @abstractmethod
    async def get_model_version(self) -> str:
        """Retorna la versión del modelo cargado."""
        pass
