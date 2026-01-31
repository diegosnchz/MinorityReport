"""
Web Router: Evasion API
Expone endpoints REST para protocolo de evasión
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
from pydantic import BaseModel, Field

from src.composition.container import get_container, Container
from src.domain.models.location import LocationId
from src.domain.models.citizen import CitizenId
from src.domain.models.evasion import RouteRequest, EvasionId, ThreatLevel

router = APIRouter(prefix="/evasion", tags=["Evasion Protocol"])


# DTOs
class RouteRequestDTO(BaseModel):
    citizen_id: int
    origin_id: str
    destination_id: str
    avoid_high_risk: bool = True


class WaypointDTO(BaseModel):
    location_id: str
    latitude: float
    longitude: float
    risk_at_moment: float
    instructions: str


class EvasionRouteResponse(BaseModel):
    id: str
    citizen_id: int
    origin_id: str
    destination_id: str
    waypoints: List[WaypointDTO]
    waypoint_count: int
    total_distance: float
    estimated_duration_minutes: int
    safety_score: float
    average_risk: float


class RiskExplanationRequest(BaseModel):
    hour: int = Field(..., ge=0, le=23)
    weather: str
    patrols: float


class RiskExplanationResponse(BaseModel):
    base_risk: float
    top_factors: List[str]
    shap_summary: str


def get_routing_engine(container: Container = Depends(get_container)):
    return container.routing_engine


@router.post("/route", response_model=EvasionRouteResponse)
async def calculate_escape_route(
    request: RouteRequestDTO,
    container: Container = Depends(get_container)
):
    """Calcula una ruta de escape táctica."""
    routing_engine = container.routing_engine
    
    route_request = RouteRequest(
        citizen_id=CitizenId(request.citizen_id),
        origin_id=LocationId(request.origin_id),
        destination_id=LocationId(request.destination_id),
        avoid_high_risk=request.avoid_high_risk
    )
    
    route = await routing_engine.calculate_optimal_route(route_request)
    
    if not route:
        raise HTTPException(status_code=404, detail="Could not calculate route")
    
    return EvasionRouteResponse(
        id=route.id.value,
        citizen_id=route.citizen_id.value,
        origin_id=route.origin.value,
        destination_id=route.destination.value,
        waypoints=[
            WaypointDTO(
                location_id=wp.location_id.value,
                latitude=wp.coordinates.latitude,
                longitude=wp.coordinates.longitude,
                risk_at_moment=wp.risk_at_moment,
                instructions=wp.instructions
            )
            for wp in route.waypoints
        ],
        waypoint_count=route.waypoint_count,
        total_distance=route.total_distance,
        estimated_duration_minutes=route.estimated_duration_minutes,
        safety_score=route.safety_score,
        average_risk=route.average_risk
    )


@router.get("/route/{route_id}/alternatives", response_model=List[EvasionRouteResponse])
async def get_alternative_routes(
    route_id: str,
    count: int = 3,
    container: Container = Depends(get_container)
):
    """Obtiene rutas alternativas de escape."""
    # Esta funcionalidad requeriría almacenar la solicitud original
    # Por ahora retornamos lista vacía
    return []


@router.post("/explain-risk", response_model=RiskExplanationResponse)
async def explain_node_risk(
    request: RiskExplanationRequest,
    container: Container = Depends(get_container)
):
    """
    XAI: Explica por qué una zona es riesgosa.
    """
    ai_engine = container.ai_engine
    
    if not ai_engine.is_ready():
        raise HTTPException(status_code=503, detail="AI engine not ready")
    
    # Calcular riesgo base basado en factores
    base_risk = 0.3 + (request.patrols * 0.1)
    if request.weather.lower() == "rain":
        base_risk += 0.2
    if request.hour < 6 or request.hour > 22:
        base_risk += 0.15
    
    base_risk = min(base_risk, 0.99)
    
    top_factors = ["Patrol Density"]
    if request.weather.lower() == "rain":
        top_factors.append("Weather Conditions")
    if request.hour < 6 or request.hour > 22:
        top_factors.append("Time of Day (Night)")
    
    return RiskExplanationResponse(
        base_risk=base_risk,
        top_factors=top_factors,
        shap_summary="Risk calculated based on environmental factors and patrol density"
    )


@router.get("/nearest-safe-haven")
async def find_nearest_safe_haven(
    current_location_id: str,
    citizen_id: int,
    container: Container = Depends(get_container)
):
    """Encuentra el refugio seguro más cercano."""
    routing_engine = container.routing_engine
    
    safe_haven = await routing_engine.find_nearest_safe_haven(
        LocationId(current_location_id),
        CitizenId(citizen_id)
    )
    
    if not safe_haven:
        raise HTTPException(status_code=404, detail="No safe haven found")
    
    return {"safe_haven_id": safe_haven.value}


@router.get("/threat-map")
async def get_threat_map(
    center_location_id: str,
    radius: float = 1000.0,
    container: Container = Depends(get_container)
):
    """Obtiene mapa de riesgo en tiempo real."""
    routing_engine = container.routing_engine
    
    risk_map = await routing_engine.get_realtime_risk_map(
        LocationId(center_location_id),
        radius
    )
    
    return risk_map
