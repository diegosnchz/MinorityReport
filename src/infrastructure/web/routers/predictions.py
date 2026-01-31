"""
Web Router: Predictions API
Expone endpoints REST para predicciones y visiones
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime

from src.composition.container import get_container, Container
from src.domain.models.citizen import CitizenId
from src.domain.models.location import LocationId
from src.domain.models.vision import Vision, VisionId, VisionStatus, RiskLevel

router = APIRouter(prefix="/predictions", tags=["Predictions"])


# DTOs
class PredictionRequest(BaseModel):
    citizen_id: int
    location_id: str


class PredictionResponse(BaseModel):
    citizen_id: int
    location_id: str
    probability: float
    verdict: str
    confidence_score: float


class VisionResponse(BaseModel):
    id: str
    citizen_id: int
    location_id: str
    probability: float
    predicted_date: datetime
    status: str
    risk_level: str
    ai_model_version: str
    is_critical: bool


class VisionExplanationResponse(BaseModel):
    vision_id: str
    top_factors: List[dict]
    confidence: float
    method: str


def get_vision_repository(container: Container = Depends(get_container)):
    return container.vision_repository


def get_ai_engine(container: Container = Depends(get_container)):
    return container.ai_engine


@router.post("/assess", response_model=PredictionResponse)
async def assess_risk(
    request: PredictionRequest,
    container: Container = Depends(get_container)
):
    """Evalúa el riesgo de un ciudadano en una ubicación específica."""
    citizen_repo = container.citizen_repository
    location_repo = container.location_repository
    ai_engine = container.ai_engine
    
    citizen = await citizen_repo.find_by_id(CitizenId(request.citizen_id))
    if not citizen:
        raise HTTPException(status_code=404, detail="Citizen not found")
    
    location = await location_repo.find_by_id(LocationId(request.location_id))
    if not location:
        raise HTTPException(status_code=404, detail="Location not found")
    
    if not ai_engine.is_ready():
        raise HTTPException(status_code=503, detail="AI engine not ready")
    
    prediction = await ai_engine.predict_single(citizen, location)
    
    return PredictionResponse(
        citizen_id=prediction.citizen_id.value,
        location_id=prediction.location_id.value,
        probability=prediction.probability,
        verdict=prediction.verdict.value,
        confidence_score=prediction.confidence_score
    )


@router.get("/visions", response_model=List[VisionResponse])
async def list_visions(
    status: Optional[str] = None,
    limit: int = 100,
    repo=Depends(get_vision_repository)
):
    """Lista todas las visiones/predicciones."""
    if status:
        visions = await repo.find_by_status(VisionStatus(status))
    else:
        visions = await repo.find_all(limit=limit)
    
    return [
        VisionResponse(
            id=v.id.value,
            citizen_id=v.citizen_id.value,
            location_id=v.location_id.value,
            probability=v.probability,
            predicted_date=v.predicted_date,
            status=v.status.value,
            risk_level=v.risk_level.value,
            ai_model_version=v.ai_model_version,
            is_critical=v.is_critical
        )
        for v in visions
    ]


@router.get("/visions/critical", response_model=List[VisionResponse])
async def list_critical_visions(
    threshold: float = 0.8,
    repo=Depends(get_vision_repository)
):
    """Lista visiones críticas (alta probabilidad)."""
    visions = await repo.find_critical(threshold=threshold)
    
    return [
        VisionResponse(
            id=v.id.value,
            citizen_id=v.citizen_id.value,
            location_id=v.location_id.value,
            probability=v.probability,
            predicted_date=v.predicted_date,
            status=v.status.value,
            risk_level=v.risk_level.value,
            ai_model_version=v.ai_model_version,
            is_critical=v.is_critical
        )
        for v in visions
    ]


@router.get("/visions/{vision_id}", response_model=VisionResponse)
async def get_vision(
    vision_id: str,
    repo=Depends(get_vision_repository)
):
    """Obtiene una visión específica."""
    vision = await repo.find_by_id(VisionId(vision_id))
    if not vision:
        raise HTTPException(status_code=404, detail="Vision not found")
    
    return VisionResponse(
        id=vision.id.value,
        citizen_id=vision.citizen_id.value,
        location_id=vision.location_id.value,
        probability=vision.probability,
        predicted_date=vision.predicted_date,
        status=vision.status.value,
        risk_level=vision.risk_level.value,
        ai_model_version=vision.ai_model_version,
        is_critical=vision.is_critical
    )


@router.get("/visions/{vision_id}/explain", response_model=VisionExplanationResponse)
async def explain_vision(
    vision_id: str,
    container: Container = Depends(get_container)
):
    """Explica por qué se generó una visión (XAI)."""
    vision_repo = container.vision_repository
    ai_engine = container.ai_engine
    
    vision = await vision_repo.find_by_id(VisionId(vision_id))
    if not vision:
        raise HTTPException(status_code=404, detail="Vision not found")
    
    if not ai_engine.is_ready():
        raise HTTPException(status_code=503, detail="AI engine not ready")
    
    explanation = await ai_engine.explain_prediction(vision)
    
    return VisionExplanationResponse(
        vision_id=vision_id,
        top_factors=explanation.get("top_factors", []),
        confidence=explanation.get("confidence", 0.0),
        method=explanation.get("method", "unknown")
    )


@router.get("/citizens/{citizen_id}/visions", response_model=List[VisionResponse])
async def get_citizen_visions(
    citizen_id: int,
    repo=Depends(get_vision_repository)
):
    """Obtiene todas las visiones de un ciudadano."""
    visions = await repo.find_by_citizen(CitizenId(citizen_id))
    
    return [
        VisionResponse(
            id=v.id.value,
            citizen_id=v.citizen_id.value,
            location_id=v.location_id.value,
            probability=v.probability,
            predicted_date=v.predicted_date,
            status=v.status.value,
            risk_level=v.risk_level.value,
            ai_model_version=v.ai_model_version,
            is_critical=v.is_critical
        )
        for v in visions
    ]
