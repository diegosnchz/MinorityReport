from pydantic import BaseModel, Field
from typing import Optional

class LocationBase(BaseModel):
    name: str
    type: str = Field(..., example="Bank") # Bank, Alley, Park...
    env_risk: float = Field(..., ge=0.0, le=1.0) # Factor de riesgo ambiental

class Location(LocationBase):
    id: str
    # Note: Using float for lat/long matching database
    latitude: float 
    longitude: float
    # Campo calculado: ¿Cuántos crímenes han ocurrido aquí?
    historical_crime_count: Optional[int] = 0

    class Config:
        from_attributes = True
