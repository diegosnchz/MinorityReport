# app/routers/citizens.py
from fastapi import APIRouter, HTTPException
from typing import List
from app.models.schemas_citizen import Citizen
from app.repositories.citizen_repo import citizen_repo

router = APIRouter(
    prefix="/citizens",
    tags=["Citizens"]
)

@router.get("/", response_model=List[Citizen])
async def get_all_citizens(limit: int = 50):
    """
    Equivalente a @GetMapping
    Devuelve la lista de ciudadanos.
    """
    return await citizen_repo.find_all(limit)

@router.get("/risk/analysis") # Placed before /{citizen_id} to avoid conflict
async def get_high_risk_list():
    """
    Endpoint administrativo para ver amenazas potenciales.
    """
    return await citizen_repo.find_high_risk_suspects()

@router.get("/{citizen_id}", response_model=Citizen)
async def get_citizen_details(citizen_id: int):
    """
    Busca un ciudadano por ID. Lanza 404 si no existe.
    """
    citizen = await citizen_repo.find_by_id(citizen_id)
    if not citizen:
        raise HTTPException(status_code=404, detail="Ciudadano no encontrado")
    return citizen
