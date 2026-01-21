from pydantic import BaseModel
from datetime import date

class CrimeEvent(BaseModel):
    date: date
    type: str     # Robbery, Assault...
    severity: int # 1-10
    # Enriquecemos el evento con quién y dónde
    perpetrator_name: str
    location_name: str
