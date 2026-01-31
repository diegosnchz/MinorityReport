"""
Domain Entity: Evasion
Representa una operación de evasión/emergency routing
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Dict
from enum import Enum

from src.domain.models.citizen import CitizenId
from src.domain.models.location import LocationId, Coordinates


class EvasionStatus(Enum):
    PLANNING = "planning"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    COMPROMISED = "compromised"
    ABORTED = "aborted"


class ThreatLevel(Enum):
    GREEN = "green"      # Seguro
    YELLOW = "yellow"    # Precaución
    RED = "red"          # Peligro inminente
    BLACK = "black"      # Crítico - evacuación inmediata


@dataclass(frozen=True)
class EvasionId:
    """Value Object para identificador de operación de evasión."""
    value: str


@dataclass
class Waypoint:
    """Punto de ruta en una operación de evasión."""
    location_id: LocationId
    coordinates: Coordinates
    estimated_arrival: Optional[datetime] = None
    risk_at_moment: float = 0.0
    instructions: str = ""


@dataclass
class EvasionRoute:
    """
    Agregado: Ruta de evasión calculada
    
    Representa un plan de escape desde origen hasta destino seguro.
    """
    id: EvasionId
    citizen_id: CitizenId
    origin: LocationId
    destination: LocationId
    waypoints: List[Waypoint]
    total_distance: float = 0.0
    estimated_duration_minutes: int = 0
    calculated_at: datetime = field(default_factory=datetime.now)
    expires_at: Optional[datetime] = None
    
    @property
    def waypoint_count(self) -> int:
        return len(self.waypoints)
    
    @property
    def average_risk(self) -> float:
        """Riesgo promedio a lo largo de la ruta."""
        if not self.waypoints:
            return 1.0
        return sum(wp.risk_at_moment for wp in self.waypoints) / len(self.waypoints)
    
    @property
    def safety_score(self) -> float:
        """Score de seguridad (0-1)."""
        return max(0, 1.0 - self.average_risk)
    
    def is_expired(self) -> bool:
        """Verifica si la ruta ha expirado."""
        if self.expires_at is None:
            return False
        return datetime.now() > self.expires_at
    
    def recalculate_risk(self, current_threat_data: Dict[LocationId, float]) -> 'EvasionRoute':
        """Recalcula riesgos basado en datos actuales."""
        updated_waypoints = []
        for wp in self.waypoints:
            new_risk = current_threat_data.get(wp.location_id, wp.risk_at_moment)
            updated_wp = Waypoint(
                location_id=wp.location_id,
                coordinates=wp.coordinates,
                estimated_arrival=wp.estimated_arrival,
                risk_at_moment=new_risk,
                instructions=wp.instructions
            )
            updated_waypoints.append(updated_wp)
        
        return EvasionRoute(
            id=self.id,
            citizen_id=self.citizen_id,
            origin=self.origin,
            destination=self.destination,
            waypoints=updated_waypoints,
            total_distance=self.total_distance,
            estimated_duration_minutes=self.estimated_duration_minutes,
            calculated_at=self.calculated_at,
            expires_at=self.expires_at
        )


@dataclass
class EmergencyAlert:
    """Alerta de emergencia que activa el protocolo de evasión."""
    id: str
    citizen_id: CitizenId
    location_id: LocationId
    threat_level: ThreatLevel
    detected_at: datetime
    description: str = ""
    
    def requires_immediate_evacuation(self) -> bool:
        """Determina si requiere evacuación inmediata."""
        return self.threat_level in [ThreatLevel.RED, ThreatLevel.BLACK]


@dataclass
class RouteRequest:
    """Solicitud de cálculo de ruta."""
    citizen_id: CitizenId
    origin_id: LocationId
    destination_id: LocationId
    preferences: Dict = field(default_factory=dict)
    avoid_high_risk: bool = True
    max_distance: Optional[float] = None
