"""
Repository Port: LocationRepository
Interfaz para operaciones de persistencia de ubicaciones
"""

from abc import ABC, abstractmethod
from typing import List, Optional

from src.domain.models.location import Location, LocationId, LocationType


class LocationRepository(ABC):
    """
    Puerto para el repositorio de ubicaciones.
    Define operaciones CRUD y consultas especializadas para ubicaciones.
    """
    
    @abstractmethod
    async def find_by_id(self, location_id: LocationId) -> Optional[Location]:
        """Busca una ubicación por su ID."""
        pass
    
    @abstractmethod
    async def find_all(self, limit: int = 100) -> List[Location]:
        """Recupera todas las ubicaciones."""
        pass
    
    @abstractmethod
    async def find_by_type(self, location_type: LocationType) -> List[Location]:
        """Busca ubicaciones por tipo."""
        pass
    
    @abstractmethod
    async def find_safe_havens(self, risk_threshold: float = 0.3) -> List[Location]:
        """Busca ubicaciones seguras (bajo riesgo)."""
        pass
    
    @abstractmethod
    async def find_nearby(self, location_id: LocationId, max_distance: float) -> List[Location]:
        """Busca ubicaciones cercanas a una dada."""
        pass
    
    @abstractmethod
    async def save(self, location: Location) -> Location:
        """Guarda o actualiza una ubicación."""
        pass
    
    @abstractmethod
    async def delete(self, location_id: LocationId) -> bool:
        """Elimina una ubicación."""
        pass
    
    @abstractmethod
    async def update_risk(self, location_id: LocationId, new_risk: float) -> bool:
        """Actualiza el nivel de riesgo de una ubicación."""
        pass
