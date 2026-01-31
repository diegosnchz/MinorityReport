"""
Domain Entity: Location
Entidad pura de dominio para ubicaciones/puntos de interés
"""

from dataclasses import dataclass
from typing import Optional, List
from enum import Enum


class LocationType(Enum):
    BANK = "bank"
    HIDEOUT = "hideout"
    POLICE_STATION = "police_station"
    BLIND_SPOT = "blind_spot"
    RESIDENTIAL = "residential"
    COMMERCIAL = "commercial"


@dataclass(frozen=True)
class LocationId:
    """Value Object para identificador de ubicación."""
    value: str
    
    def __post_init__(self):
        if not self.value:
            raise ValueError("LocationId cannot be empty")


@dataclass
class Coordinates:
    """Value Object para coordenadas geográficas."""
    latitude: float
    longitude: float
    altitude: Optional[float] = None
    
    def __post_init__(self):
        if not (-90 <= self.latitude <= 90):
            raise ValueError(f"Invalid latitude: {self.latitude}")
        if not (-180 <= self.longitude <= 180):
            raise ValueError(f"Invalid longitude: {self.longitude}")


@dataclass
class Location:
    """
    Entidad de Dominio: Ubicación
    
    Representa un punto en el mapa (banco, escondite, comisaría, etc.)
    """
    id: LocationId
    name: str
    location_type: LocationType
    coordinates: Coordinates
    env_risk: float = 0.0
    connections: List['Connection'] = None
    
    def __post_init__(self):
        if self.connections is None:
            self.connections = []
        if not (0 <= self.env_risk <= 1):
            raise ValueError(f"env_risk must be between 0 and 1: {self.env_risk}")
    
    def add_connection(self, target: LocationId, distance: float, risk_factor: float = 0.0):
        """Añade una conexión a otra ubicación."""
        connection = Connection(target=target, distance=distance, risk_factor=risk_factor)
        self.connections.append(connection)
    
    def get_risk_score(self) -> float:
        """Calcula el score de riesgo de la ubicación."""
        base_risk = self.env_risk
        if self.location_type == LocationType.POLICE_STATION:
            base_risk = 1.0
        elif self.location_type == LocationType.BLIND_SPOT:
            base_risk = min(base_risk * 0.5, 0.3)
        return base_risk
    
    def is_safe_haven(self, risk_threshold: float = 0.3) -> bool:
        """Determina si es un lugar seguro para esconderse."""
        return self.get_risk_score() <= risk_threshold


@dataclass
class Connection:
    """Value Object para conexiones entre ubicaciones."""
    target: LocationId
    distance: float
    risk_factor: float = 0.0
    
    def __post_init__(self):
        if self.distance < 0:
            raise ValueError("Distance cannot be negative")
        if not (0 <= self.risk_factor <= 1):
            raise ValueError(f"risk_factor must be between 0 and 1: {self.risk_factor}")


@dataclass
class Route:
    """Agregado: Ruta entre dos ubicaciones."""
    origin: LocationId
    destination: LocationId
    path: List[LocationId]
    total_distance: float
    total_risk: float
    estimated_time: Optional[float] = None
    
    @property
    def safety_score(self) -> float:
        """Score de seguridad (0-1, mayor es más seguro)."""
        if self.total_risk == 0:
            return 1.0
        return max(0, 1.0 - self.total_risk)
