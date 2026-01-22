from fastapi import APIRouter
from app.repositories.analytics_repo import analytics_repo

router = APIRouter(prefix="/analytics", tags=["Analytics & KPIs"])

@router.get("/spatial")
async def get_spatial_kpis():
    """Devuelve hotspots por tipo y ubicación."""
    return await analytics_repo.get_spatial_hotspots()

@router.get("/social")
async def get_social_kpis():
    """Devuelve datos de correlación Social (Degree) vs Riesgo."""
    return await analytics_repo.get_social_influence()

@router.get("/temporal")
async def get_temporal_kpis():
    """Devuelve distribución horaria de las visiones."""
    return await analytics_repo.get_hourly_patterns()

@router.get("/headline")
async def get_headline_stats():
    """Devuelve KPIs estilo 'Marcador' para el header."""
    return await analytics_repo.get_headline_stats()

@router.get("/system")
async def get_system_kpis():
    """Devuelve métricas globales de rendimiento."""
    return await analytics_repo.get_system_stats()
