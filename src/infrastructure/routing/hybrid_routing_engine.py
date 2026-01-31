"""
Infrastructure: Hybrid Routing Engine
Implementación del motor de routing usando GAT + A* híbrido
"""

from typing import List, Optional, Dict
import uuid
from datetime import datetime, timedelta

from src.domain.models.location import LocationId, Location, Coordinates
from src.domain.models.citizen import CitizenId
from src.domain.models.evasion import (
    EvasionRoute, RouteRequest, EmergencyAlert, 
    Waypoint, EvasionId, ThreatLevel
)
from src.domain.repositories.graph_repository import GraphRepository
from src.domain.services.routing_engine import RoutingEngine


class HybridRoutingEngine(RoutingEngine):
    """
    Adaptador de Infraestructura: Motor de routing híbrido.
    
    Combina GAT (Graph Attention) para evaluación de riesgo
    con A* para pathfinding óptimo.
    """
    
    def __init__(self, graph_repo: Optional[GraphRepository] = None):
        self._graph_repo = graph_repo
        self._risk_cache: Dict[str, float] = {}
    
    async def calculate_optimal_route(self, request: RouteRequest) -> Optional[EvasionRoute]:
        """Calcula la ruta óptima de evasión."""
        # En una implementación real, usaríamos A* con heurística de riesgo
        # Aquí simulamos el resultado
        
        route_id = EvasionId(f"route_{uuid.uuid4().hex[:8]}")
        
        # Simular waypoints
        waypoints = [
            Waypoint(
                location_id=request.origin_id,
                coordinates=Coordinates(40.4168, -3.7038),
                risk_at_moment=0.2,
                instructions="Start here, move quickly but calmly"
            ),
            Waypoint(
                location_id=LocationId("wp_001"),
                coordinates=Coordinates(40.4155, -3.7050),
                risk_at_moment=0.15,
                instructions="Turn left into alley"
            ),
            Waypoint(
                location_id=request.destination_id,
                coordinates=Coordinates(40.4150, -3.7100),
                risk_at_moment=0.1,
                instructions="Arrive at safe haven"
            )
        ]
        
        total_distance = 500.0  # metros
        estimated_duration = 8  # minutos
        
        return EvasionRoute(
            id=route_id,
            citizen_id=request.citizen_id,
            origin=request.origin_id,
            destination=request.destination_id,
            waypoints=waypoints,
            total_distance=total_distance,
            estimated_duration_minutes=estimated_duration,
            calculated_at=datetime.now(),
            expires_at=datetime.now() + timedelta(minutes=30)
        )
    
    async def calculate_alternative_routes(self, 
                                         request: RouteRequest, 
                                         count: int = 3) -> List[EvasionRoute]:
        """Calcula múltiples rutas alternativas."""
        routes = []
        for i in range(count):
            route = await self.calculate_optimal_route(request)
            if route:
                # Modificar ligeramente para crear alternativas
                route.id = EvasionId(f"route_alt_{i}_{uuid.uuid4().hex[:6]}")
                route.total_distance *= (1 + i * 0.1)
                routes.append(route)
        return routes
    
    async def update_route_with_threats(self, 
                                      route: EvasionRoute, 
                                      threats: List[EmergencyAlert]) -> EvasionRoute:
        """Actualiza ruta considerando nuevas amenazas."""
        # Recalcular riesgos de waypoints basado en threats
        threat_map = {}
        for threat in threats:
            threat_map[threat.location_id] = 0.9 if threat.threat_level == ThreatLevel.RED else 0.6
        
        return route.recalculate_risk(threat_map)
    
    async def find_nearest_safe_haven(self, 
                                    current_location: LocationId,
                                    citizen_id: CitizenId) -> Optional[LocationId]:
        """Encuentra el refugio seguro más cercano."""
        # Simulación: retornar un ID fijo
        return LocationId("loc_002")  # Escondite Sótano
    
    async def is_route_still_safe(self, route: EvasionRoute, 
                                 max_risk_threshold: float = 0.5) -> bool:
        """Verifica si la ruta sigue siendo segura."""
        if route.is_expired():
            return False
        return route.average_risk <= max_risk_threshold
    
    async def get_realtime_risk_map(self, area_center: LocationId, 
                                   radius: float) -> dict:
        """Obtiene mapa de riesgo en tiempo real."""
        return {
            "center": area_center.value,
            "radius_meters": radius,
            "risk_zones": [
                {"location": "loc_001", "risk": 0.8, "type": "high"},
                {"location": "loc_002", "risk": 0.2, "type": "low"},
                {"location": "loc_003", "risk": 1.0, "type": "extreme"},
            ],
            "timestamp": datetime.now().isoformat()
        }
