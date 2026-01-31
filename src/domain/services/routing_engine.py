"""
Service Port: RoutingEngine
Interfaz para motores de cálculo de rutas de evasión
"""

from abc import ABC, abstractmethod
from typing import List, Optional

from src.domain.models.location import LocationId, Route
from src.domain.models.evasion import EvasionRoute, RouteRequest, EmergencyAlert
from src.domain.models.citizen import CitizenId


class RoutingEngine(ABC):
    """
    Puerto para el motor de cálculo de rutas de evasión.
    
    Define las operaciones necesarias para calcular rutas seguras
    de escape sin depender de la implementación específica (A*, GAT, etc.)
    """
    
    @abstractmethod
    async def calculate_optimal_route(self, request: RouteRequest) -> Optional[EvasionRoute]:
        """
        Calcula la ruta de evasión óptima entre dos puntos.
        """
        pass
    
    @abstractmethod
    async def calculate_alternative_routes(self, 
                                         request: RouteRequest, 
                                         count: int = 3) -> List[EvasionRoute]:
        """
        Calcula múltiples rutas alternativas para tener opciones.
        """
        pass
    
    @abstractmethod
    async def update_route_with_threats(self, 
                                      route: EvasionRoute, 
                                      threats: List[EmergencyAlert]) -> EvasionRoute:
        """
        Recalcula una ruta considerando nuevas amenazas en tiempo real.
        """
        pass
    
    @abstractmethod
    async def find_nearest_safe_haven(self, 
                                    current_location: LocationId,
                                    citizen_id: CitizenId) -> Optional[LocationId]:
        """
        Encuentra el refugio seguro más cercano desde una posición.
        """
        pass
    
    @abstractmethod
    async def is_route_still_safe(self, route: EvasionRoute, 
                                 max_risk_threshold: float = 0.5) -> bool:
        """
        Verifica si una ruta previamente calculada sigue siendo segura.
        """
        pass
    
    @abstractmethod
    async def get_realtime_risk_map(self, area_center: LocationId, 
                                   radius: float) -> dict:
        """
        Obtiene un mapa de riesgo en tiempo real para un área.
        """
        pass
