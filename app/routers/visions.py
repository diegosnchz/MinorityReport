from fastapi import APIRouter, HTTPException, Query
from typing import List
from app.models.schemas_vision import VisionCreate, VisionRead
from app.repositories.vision_repo import vision_repo
from app.services.vision_service import vision_service

router = APIRouter(prefix="/visions", tags=["Pre-Crime Visions"])

@router.get("/graph")
async def get_graph(limit: int = Query(100, le=500)):
    """
    Endpoint para el Frontend (D3.js).
    Devuelve la topología de la red criminal.
    """
    # El router solo valida (limit <= 500) y delega.
    return await vision_service.get_dashboard_graph(limit)

@router.get("/search")
async def search_visions(q: str):
    """
    Buscador para el dashboard.
    Ej: /visions/search?q=Anderton
    """
    return await vision_service.search_visions(q)

@router.post("/", response_model=VisionRead)
async def generate_prediction(vision_data: VisionCreate):
    """
    Input para la Red Neuronal (RedGAN).
    Cuando la IA detecta un riesgo, llama a este endpoint.
    """
    # Aquí podríamos añadir lógica extra (ej. notificar a patrullas)
    # The repository returns the full read model dict/object
    new_vision = await vision_repo.create_vision(vision_data)
    
    if not new_vision:
        raise HTTPException(status_code=404, detail="Citizen or Location not found")
        
    return new_vision

@router.get("/active", response_model=List[VisionRead])
async def get_dashboard():
    """
    La pantalla de John Anderton.
    Muestra solo las amenazas activas.
    """
    return await vision_repo.find_active_visions()

@router.put("/{vision_id}/resolve")
async def intervene_vision(vision_id: str, outcome: str):
    """
    Registra la acción policial.
    """
    if outcome not in ["INTERVENED", "FALSE_ALARM"]:
        raise HTTPException(status_code=400, detail="Invalid outcome")
        
    await vision_repo.resolve_vision(vision_id, outcome)
    return {"msg": f"Vision {vision_id} resolved as {outcome}"}
