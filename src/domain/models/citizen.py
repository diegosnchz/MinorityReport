"""
Domain Entity: Citizen
Entidad pura de dominio - NO depende de frameworks externos
"""

from dataclasses import dataclass
from typing import Optional, List
from enum import Enum


class CitizenStatus(Enum):
    ACTIVE = "active"
    WATCHLIST = "watchlist"
    INTERVENE = "intervene"
    DETAINED = "detained"


@dataclass(frozen=True)
class CitizenId:
    """Value Object para identificador de ciudadano."""
    value: int
    
    def __post_init__(self):
        if self.value <= 0:
            raise ValueError("CitizenId must be positive")


@dataclass
class Citizen:
    """
    Entidad de Dominio: Ciudadano
    
    Representa a un ciudadano en el sistema Pre-Crime.
    Contiene solo datos y comportamiento de negocio puro.
    """
    id: CitizenId
    name: str
    born: int
    status: CitizenStatus
    risk_seed: float = 0.0
    criminal_degree: int = 0
    
    def calculate_base_risk(self) -> float:
        """Calcula el riesgo base basado en atributos internos."""
        risk = self.risk_seed * 0.6
        risk += (self.criminal_degree / 10) * 0.4
        return min(risk, 1.0)
    
    def update_status(self, new_status: CitizenStatus) -> 'Citizen':
        """Retorna nueva instancia con estado actualizado (inmutabilidad)."""
        return Citizen(
            id=self.id,
            name=self.name,
            born=self.born,
            status=new_status,
            risk_seed=self.risk_seed,
            criminal_degree=self.criminal_degree
        )
    
    def is_high_risk(self, threshold: float = 0.7) -> bool:
        """Determina si el ciudadano es de alto riesgo."""
        return self.calculate_base_risk() >= threshold
    
    def to_feature_vector(self) -> List[float]:
        """Convierte a vector de características para IA."""
        return [
            self.risk_seed,
            float(self.criminal_degree) / 10.0,
            1.0 if self.status == CitizenStatus.WATCHLIST else 0.0,
            1.0 if self.status == CitizenStatus.INTERVENE else 0.0,
        ]


@dataclass
class CitizenFeatureVector:
    """Vector de características para procesamiento por IA."""
    citizen_id: CitizenId
    base_features: List[float]
    job_vector: Optional[List[float]] = None
    
    def combine_features(self) -> List[float]:
        """Combina todas las características en un solo vector."""
        combined = self.base_features.copy()
        if self.job_vector:
            combined.extend(self.job_vector)
        return combined
