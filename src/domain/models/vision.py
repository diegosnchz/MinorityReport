"""
Domain Entity: Vision
Representa una predicción de crimen futuro ("bola roja")
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from enum import Enum

from src.domain.models.citizen import CitizenId
from src.domain.models.location import LocationId


class VisionStatus(Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    PREVENTED = "prevented"
    EXPIRED = "expired"


class RiskLevel(Enum):
    SAFE = "safe"
    WATCHLIST = "watchlist"
    INTERVENE = "intervene"
    CRITICAL = "critical"


@dataclass(frozen=True)
class VisionId:
    """Value Object para identificador de visión."""
    value: str
    
    def __post_init__(self):
        if not self.value:
            raise ValueError("VisionId cannot be empty")


@dataclass
class Vision:
    """
    Entidad de Dominio: Visión (Predicción de crimen)
    
    Representa una predicción de la red neuronal Precog sobre
    un posible crimen futuro.
    """
    id: VisionId
    citizen_id: CitizenId
    location_id: LocationId
    probability: float
    predicted_date: datetime
    status: VisionStatus
    ai_model_version: str
    created_at: datetime
    explained: bool = False
    explanation_data: Optional[dict] = None
    
    def __post_init__(self):
        if not (0 <= self.probability <= 1):
            raise ValueError(f"Probability must be between 0 and 1: {self.probability}")
    
    @property
    def risk_level(self) -> RiskLevel:
        """Determina el nivel de riesgo basado en probabilidad."""
        if self.probability >= 0.9:
            return RiskLevel.CRITICAL
        elif self.probability >= 0.7:
            return RiskLevel.INTERVENE
        elif self.probability >= 0.4:
            return RiskLevel.WATCHLIST
        return RiskLevel.SAFE
    
    @property
    def is_critical(self) -> bool:
        """Indica si es una visión crítica que requiere acción inmediata."""
        return self.probability >= 0.8
    
    def confirm(self) -> 'Vision':
        """Marca la visión como confirmada (el crimen ocurrió)."""
        return Vision(
            id=self.id,
            citizen_id=self.citizen_id,
            location_id=self.location_id,
            probability=self.probability,
            predicted_date=self.predicted_date,
            status=VisionStatus.CONFIRMED,
            ai_model_version=self.ai_model_version,
            created_at=self.created_at,
            explained=self.explained,
            explanation_data=self.explanation_data
        )
    
    def prevent(self) -> 'Vision':
        """Marca la visión como prevenida (se evitó el crimen)."""
        return Vision(
            id=self.id,
            citizen_id=self.citizen_id,
            location_id=self.location_id,
            probability=self.probability,
            predicted_date=self.predicted_date,
            status=VisionStatus.PREVENTED,
            ai_model_version=self.ai_model_version,
            created_at=self.created_at,
            explained=self.explained,
            explanation_data=self.explanation_data
        )
    
    def add_explanation(self, explanation: dict) -> 'Vision':
        """Añade explicación XAI a la visión."""
        return Vision(
            id=self.id,
            citizen_id=self.citizen_id,
            location_id=self.location_id,
            probability=self.probability,
            predicted_date=self.predicted_date,
            status=self.status,
            ai_model_version=self.ai_model_version,
            created_at=self.created_at,
            explained=True,
            explanation_data=explanation
        )


@dataclass
class PredictionInput:
    """Input para generar una predicción."""
    citizen_id: CitizenId
    location_id: LocationId
    current_risk_factors: dict


@dataclass
class PredictionOutput:
    """Output de una predicción generada."""
    citizen_id: CitizenId
    location_id: LocationId
    probability: float
    verdict: RiskLevel
    confidence_score: float
