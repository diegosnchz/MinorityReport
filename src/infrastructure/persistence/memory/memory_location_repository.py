"""
Infrastructure: Memory Location Repository
Implementación en memoria para testing y modo demo
"""

from typing import List, Optional

from src.domain.models.location import Location, LocationId, LocationType, Coordinates, Connection
from src.domain.repositories.location_repository import LocationRepository


class MemoryLocationRepository(LocationRepository):
    """Repositorio en memoria para ubicaciones."""
    
    def __init__(self):
        self._locations: dict = {}
        self._seed_data()
    
    def _seed_data(self):
        """Carga datos de ejemplo."""
        sample_locations = [
            Location(
                LocationId("loc_001"),
                "Banco Central",
                LocationType.BANK,
                Coordinates(40.4168, -3.7038),
                env_risk=0.8
            ),
            Location(
                LocationId("loc_002"),
                "Escondite Sótano",
                LocationType.HIDEOUT,
                Coordinates(40.4150, -3.7100),
                env_risk=0.2
            ),
            Location(
                LocationId("loc_003"),
                "Comisaría Principal",
                LocationType.POLICE_STATION,
                Coordinates(40.4180, -3.7000),
                env_risk=1.0
            ),
            Location(
                LocationId("loc_004"),
                "Callejón Oscuro",
                LocationType.BLIND_SPOT,
                Coordinates(40.4140, -3.7050),
                env_risk=0.4
            ),
            Location(
                LocationId("loc_005"),
                "Centro Comercial",
                LocationType.COMMERCIAL,
                Coordinates(40.4170, -3.7020),
                env_risk=0.5
            ),
        ]
        
        # Añadir conexiones
        sample_locations[0].add_connection(LocationId("loc_004"), 100, 0.3)
        sample_locations[0].add_connection(LocationId("loc_005"), 150, 0.4)
        sample_locations[1].add_connection(LocationId("loc_004"), 50, 0.2)
        sample_locations[3].add_connection(LocationId("loc_002"), 50, 0.1)
        
        for loc in sample_locations:
            self._locations[loc.id.value] = loc
    
    async def find_by_id(self, location_id: LocationId) -> Optional[Location]:
        return self._locations.get(location_id.value)
    
    async def find_all(self, limit: int = 100) -> List[Location]:
        return list(self._locations.values())[:limit]
    
    async def find_by_type(self, location_type: LocationType) -> List[Location]:
        return [l for l in self._locations.values() if l.location_type == location_type]
    
    async def find_safe_havens(self, risk_threshold: float = 0.3) -> List[Location]:
        return [l for l in self._locations.values() if l.get_risk_score() <= risk_threshold]
    
    async def find_nearby(self, location_id: LocationId, max_distance: float) -> List[Location]:
        location = self._locations.get(location_id.value)
        if not location:
            return []
        return [
            self._locations.get(conn.target.value)
            for conn in location.connections
            if conn.distance <= max_distance and conn.target.value in self._locations
        ]
    
    async def save(self, location: Location) -> Location:
        self._locations[location.id.value] = location
        return location
    
    async def delete(self, location_id: LocationId) -> bool:
        if location_id.value in self._locations:
            del self._locations[location_id.value]
            return True
        return False
    
    async def update_risk(self, location_id: LocationId, new_risk: float) -> bool:
        location = self._locations.get(location_id.value)
        if location:
            location.env_risk = new_risk
            return True
        return False
