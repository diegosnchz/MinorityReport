from pydantic import BaseModel
from typing import List, Optional

class Alerta(BaseModel):
    ladron_id: str
    ubicacion_actual_id: str
    amenaza_detectada: str # Ej: "PATRULLA", "DRONE"
    nivel_riesgo: float

class RutaEscape(BaseModel):
    destino_seguro: str
    camino_nodos: List[str]
    probabilidad_exito: float

