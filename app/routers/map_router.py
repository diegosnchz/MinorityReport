from fastapi import APIRouter
from app.repositories.map_repo import map_repo

router = APIRouter(prefix="/map", tags=["Geospatial Intelligence"])

@router.get("/heatmap")
async def get_heatmap_data():
    """Data for Deck.gl HexagonLayer (Crime Density)"""
    return await map_repo.get_crime_heatmap()

@router.get("/visions")
async def get_geo_visions():
    """Data for Deck.gl ScatterplotLayer (Active Threats)"""
    return await map_repo.get_active_visions_geo()
