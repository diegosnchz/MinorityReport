from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from app.models.schemas_citizen import CitizenBase # Reutilizamos partes del Ciudadano
from app.models.schemas_location import LocationBase # Reutilizamos Ubicación

# --- INPUT: Lo que la IA nos envía ---
class VisionCreate(BaseModel):
    citizen_id: int
    location_id: str
    probability: float = Field(..., ge=0.0, le=1.0)
    ai_model_version: str = "RedGAN_v1.0"
    predicted_date: datetime

# --- OUTPUT: Lo que el policía ve en la pantalla ---
class VisionRead(BaseModel):
    id: str # ID único de la visión (La "Bola Roja")
    probability: float
    status: str # "OPEN", "INTERVENED", "FALSE_ALARM"
    timestamp: datetime
    # Datos enriquecidos (Join)
    perpetrator: CitizenBase
    target: LocationBase

    class Config:
        from_attributes = True
