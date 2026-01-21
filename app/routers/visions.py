from fastapi import APIRouter, HTTPException, Query
from typing import List
from app.models.schemas_vision import VisionCreate, VisionRead
from app.repositories.vision_repo import vision_repo
from app.services.xai_service import xai_service
from app.repositories.citizen_repo import citizen_repo # Necesario para obtener subgrafofrom app.services.vision_service import vision_service

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

@router.get("/{vision_id}/explain")
async def explain_prediction(vision_id: str):
    """
    Endpoint de Transparencia (XAI).
    Devuelve el subgrafo que causó la alerta.
    """
    # 1. Recuperar datos
    vision = await vision_repo.find_by_id(vision_id)
    if not vision:
        raise HTTPException(status_code=404, detail="Vision not found")

    # 2. Recuperar el subgrafo del perpetrador para alimentar al explainer
    # (NOTA: Asumimos que citizen_repo tiene un método get_pyg_subgraph simulado o real)
    # Como fallback para este demo, construiremos un objeto Data dummy si el repo no lo tiene.
    
    try:
        # Intento de llamada real si existiera
        # subgraph = await citizen_repo.get_pyg_subgraph(vision['perpetrator']['id'])
        pass
    except:
        pass
        
    # --- MOCK DATA PARA DEMO ---
    # Para que el endpoint funcione sin reescribir todo citizen_repo ahora mismo:
    from torch_geometric.data import Data
    import torch
    # Simulamos un subgrafo pequeño alrededor del sospechoso
    subgraph = Data(
        x=torch.randn(10, 16), # 10 nodos, 16 features
        edge_index=torch.randint(0, 10, (2, 20)) # 20 aristas
    )
    # ---------------------------

    # 3. Ejecutar XAI
    explanation = await xai_service.explain_vision(
        vision['perpetrator']['id'],
        vision['target']['id'],
        subgraph
    )
    
    return {
        "vision_id": vision_id,
        "verdict": "INTERVENE",
        "explanation": explanation
        # Frontend: Resaltar estas aristas en amarillo brillante en el grafo 3D
    }
