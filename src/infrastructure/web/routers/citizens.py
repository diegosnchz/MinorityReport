"""
Web Router: Citizens API
Expone endpoints REST para gestión de ciudadanos
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
from pydantic import BaseModel, Field

from src.composition.container import get_container, Container
from src.domain.models.citizen import Citizen, CitizenId, CitizenStatus

router = APIRouter(prefix="/citizens", tags=["Citizens"])


# DTOs para API
class CitizenResponse(BaseModel):
    id: int
    name: str
    born: int
    status: str
    risk_seed: Optional[float] = None
    criminal_degree: int = 0
    
    class Config:
        from_attributes = True


class CitizenCreateRequest(BaseModel):
    name: str = Field(..., example="John Anderton")
    born: int = Field(..., example=1980)
    status: str = Field(default="active")


class RiskAssessmentResponse(BaseModel):
    citizen_id: int
    base_risk: float
    is_high_risk: bool


def get_citizen_repository(container: Container = Depends(get_container)):
    """Dependency injection para repositorio."""
    return container.citizen_repository


@router.get("", response_model=List[CitizenResponse])
async def list_citizens(
    limit: int = 100,
    repo=Depends(get_citizen_repository)
):
    """Lista todos los ciudadanos."""
    citizens = await repo.find_all(limit=limit)
    return [
        CitizenResponse(
            id=c.id.value,
            name=c.name,
            born=c.born,
            status=c.status.value,
            risk_seed=c.risk_seed,
            criminal_degree=c.criminal_degree
        )
        for c in citizens
    ]


@router.get("/{citizen_id}", response_model=CitizenResponse)
async def get_citizen(
    citizen_id: int,
    repo=Depends(get_citizen_repository)
):
    """Obtiene un ciudadano por ID."""
    citizen = await repo.find_by_id(CitizenId(citizen_id))
    if not citizen:
        raise HTTPException(status_code=404, detail="Citizen not found")
    
    return CitizenResponse(
        id=citizen.id.value,
        name=citizen.name,
        born=citizen.born,
        status=citizen.status.value,
        risk_seed=citizen.risk_seed,
        criminal_degree=citizen.criminal_degree
    )


@router.get("/{citizen_id}/risk", response_model=RiskAssessmentResponse)
async def assess_citizen_risk(
    citizen_id: int,
    repo=Depends(get_citizen_repository)
):
    """Evalúa el riesgo de un ciudadano."""
    citizen = await repo.find_by_id(CitizenId(citizen_id))
    if not citizen:
        raise HTTPException(status_code=404, detail="Citizen not found")
    
    return RiskAssessmentResponse(
        citizen_id=citizen.id.value,
        base_risk=citizen.calculate_base_risk(),
        is_high_risk=citizen.is_high_risk()
    )


@router.get("/high-risk/list", response_model=List[CitizenResponse])
async def list_high_risk_citizens(
    threshold: float = 0.7,
    repo=Depends(get_citizen_repository)
):
    """Lista ciudadanos de alto riesgo."""
    citizens = await repo.find_high_risk(threshold=threshold)
    return [
        CitizenResponse(
            id=c.id.value,
            name=c.name,
            born=c.born,
            status=c.status.value,
            risk_seed=c.risk_seed,
            criminal_degree=c.criminal_degree
        )
        for c in citizens
    ]


@router.post("", response_model=CitizenResponse)
async def create_citizen(
    request: CitizenCreateRequest,
    repo=Depends(get_citizen_repository)
):
    """Crea un nuevo ciudadano."""
    # Generar ID (en producción sería autoincremental)
    import random
    new_id = CitizenId(random.randint(1000, 9999))
    
    citizen = Citizen(
        id=new_id,
        name=request.name,
        born=request.born,
        status=CitizenStatus(request.status),
        risk_seed=0.0,
        criminal_degree=0
    )
    
    saved = await repo.save(citizen)
    
    return CitizenResponse(
        id=saved.id.value,
        name=saved.name,
        born=saved.born,
        status=saved.status.value,
        risk_seed=saved.risk_seed,
        criminal_degree=saved.criminal_degree
    )
