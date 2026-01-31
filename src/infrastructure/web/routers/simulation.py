"""
Web Router: Simulation API
Expone endpoints REST para simulación de actividad criminal
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Dict

from src.composition.container import get_container, Container

router = APIRouter(prefix="/simulation", tags=["Simulation"])


# DTOs
class SimulationStepResponse(BaseModel):
    processed: int
    crimes_detected: int
    visions_created: int
    status: str


class SimulationStatusResponse(BaseModel):
    running: bool
    total_steps: int
    total_visions_created: int
    demo_mode: bool


class CrimePattern(BaseModel):
    location_type: str
    frequency: float
    average_risk: float


def get_simulation_engine(container: Container = Depends(get_container)):
    return container.simulation_engine


@router.post("/step", response_model=SimulationStepResponse)
async def run_simulation_step(
    container: Container = Depends(get_container)
):
    """
    Ejecuta un 'tick' de la simulación.
    Genera actividad criminal y visiones basadas en probabilidades.
    """
    simulation_engine = container.simulation_engine
    settings = container.settings
    
    try:
        result = await simulation_engine.run_step()
        
        return SimulationStepResponse(
            processed=result.get("processed", 0),
            crimes_detected=result.get("crimes_detected", 0),
            visions_created=result.get("visions_created", 0),
            status="demo_mode" if settings.demo_mode else "active"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Simulation error: {str(e)}")


@router.post("/run/{steps}")
async def run_multiple_steps(
    steps: int,
    container: Container = Depends(get_container)
):
    """Ejecuta múltiples pasos de simulación."""
    simulation_engine = container.simulation_engine
    
    total_visions = 0
    total_processed = 0
    
    for _ in range(steps):
        try:
            result = await simulation_engine.run_step()
            total_visions += result.get("visions_created", 0)
            total_processed += result.get("processed", 0)
        except Exception as e:
            break
    
    return {
        "steps_executed": steps,
        "total_visions_created": total_visions,
        "total_processed": total_processed
    }


@router.get("/status", response_model=SimulationStatusResponse)
async def get_simulation_status(
    container: Container = Depends(get_container)
):
    """Obtiene el estado actual de la simulación."""
    settings = container.settings
    simulation_engine = container.simulation_engine
    
    return SimulationStatusResponse(
        running=simulation_engine.is_running() if hasattr(simulation_engine, 'is_running') else False,
        total_steps=getattr(simulation_engine, 'total_steps', 0),
        total_visions_created=getattr(simulation_engine, 'total_visions', 0),
        demo_mode=settings.demo_mode
    )


@router.get("/patterns", response_model=List[CrimePattern])
async def get_crime_patterns(
    container: Container = Depends(get_container)
):
    """Obtiene patrones de crimen detectados."""
    # Datos simulados de patrones
    return [
        CrimePattern(
            location_type="bank",
            frequency=0.35,
            average_risk=0.75
        ),
        CrimePattern(
            location_type="residential",
            frequency=0.25,
            average_risk=0.45
        ),
        CrimePattern(
            location_type="commercial",
            frequency=0.40,
            average_risk=0.60
        )
    ]


@router.post("/reset")
async def reset_simulation(
    container: Container = Depends(get_container)
):
    """Reinicia la simulación."""
    simulation_engine = container.simulation_engine
    
    if hasattr(simulation_engine, 'reset'):
        await simulation_engine.reset()
    
    return {"status": "reset_complete"}
