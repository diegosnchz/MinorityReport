# app/models/schemas.py
from pydantic import BaseModel, Field
from typing import Optional, List

# --- CLASE BASE ---
class CitizenBase(BaseModel):
    """La definición pública básica de un ciudadano."""
    name: str = Field(..., example="John Anderton")
    status: str = Field(..., example="ACTIVE")

# --- LECTURA (Lo que devolvemos al usuario) ---
class Citizen(CitizenBase):
    id: int
    born: int  # Added to match schema
    # En Spring usaríamos @Transient, aquí simplemente lo declaramos opcional
    criminal_degree: Optional[int] = 0
    risk_seed: Optional[float] = None  # Solo visible para admins/precogs

    class Config:
        from_attributes = True

# --- ESCRITURA (Para crear nuevos ciudadanos manualmente) ---
class CitizenCreate(CitizenBase):
    born: int
    job: str

# --- IA MODELS (Compatibility with Part 4) ---
class CitizenFeatureVector(Citizen):
    """Extends Citizen to include AI-specific vectors not usually exposed."""
    job_vector: List[float]  # Vector One-Hot del trabajo

# La "Bola Roja" (Keep from Part 4)
class PredictionOutput(BaseModel):
    subject_id: int
    target_location_id: str
    probability: float   # 0.0 a 1.0
    verdict: str         # "SAFE" | "WATCHLIST" | "INTERVENE"
