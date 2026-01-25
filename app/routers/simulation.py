from fastapi import APIRouter, BackgroundTasks
from app.services.simulation_service import simulation_service
from app.repositories.vision_repo import vision_repo

router = APIRouter(prefix="/simulation", tags=["Simulation Engine"])

@router.post("/step")
async def trigger_simulation_step():
    """Fuerza un paso de la simulación (Genera visiones aleatorias)."""
    await simulation_service.run_step()
    return {"message": "Simulation step executed"}

@router.get("/graph-data")
async def get_graph_for_frontend():
    """Devuelve el JSON para pintar el grafo."""
    return await vision_repo.get_graph_visualization()
