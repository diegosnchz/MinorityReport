"""
Infrastructure: Memory Vision Repository
Implementación en memoria para testing y modo demo
"""

from typing import List, Optional
from datetime import datetime, timedelta
import uuid

from src.domain.models.vision import Vision, VisionId, VisionStatus
from src.domain.models.citizen import CitizenId
from src.domain.models.location import LocationId
from src.domain.repositories.vision_repository import VisionRepository


class MemoryVisionRepository(VisionRepository):
    """Repositorio en memoria para visiones/predicciones."""
    
    def __init__(self):
        self._visions: dict = {}
        self._seed_data()
    
    def _seed_data(self):
        """Carga datos de ejemplo."""
        now = datetime.now()
        sample_visions = [
            Vision(
                VisionId(str(uuid.uuid4())),
                CitizenId(2),
                LocationId("loc_001"),
                0.75,
                now + timedelta(hours=12),
                VisionStatus.PENDING,
                "Sim_v1",
                now
            ),
            Vision(
                VisionId(str(uuid.uuid4())),
                CitizenId(4),
                LocationId("loc_003"),
                0.92,
                now + timedelta(hours=6),
                VisionStatus.PENDING,
                "Sim_v1",
                now
            ),
        ]
        for v in sample_visions:
            self._visions[v.id.value] = v
    
    async def find_by_id(self, vision_id: VisionId) -> Optional[Vision]:
        return self._visions.get(vision_id.value)
    
    async def find_all(self, limit: int = 100) -> List[Vision]:
        return list(self._visions.values())[:limit]
    
    async def find_by_citizen(self, citizen_id: CitizenId) -> List[Vision]:
        return [v for v in self._visions.values() if v.citizen_id.value == citizen_id.value]
    
    async def find_by_location(self, location_id: LocationId) -> List[Vision]:
        return [v for v in self._visions.values() if v.location_id.value == location_id.value]
    
    async def find_by_status(self, status: VisionStatus) -> List[Vision]:
        return [v for v in self._visions.values() if v.status == status]
    
    async def find_critical(self, threshold: float = 0.8) -> List[Vision]:
        return [v for v in self._visions.values() if v.probability >= threshold]
    
    async def find_pending_before(self, date: datetime) -> List[Vision]:
        return [
            v for v in self._visions.values()
            if v.status == VisionStatus.PENDING and v.predicted_date < date
        ]
    
    async def save(self, vision: Vision) -> Vision:
        self._visions[vision.id.value] = vision
        return vision
    
    async def update_status(self, vision_id: VisionId, new_status: VisionStatus) -> bool:
        vision = self._visions.get(vision_id.value)
        if vision:
            updated = vision.confirm() if new_status == VisionStatus.CONFIRMED else \
                     vision.prevent() if new_status == VisionStatus.PREVENTED else \
                     Vision(
                         id=vision.id,
                         citizen_id=vision.citizen_id,
                         location_id=vision.location_id,
                         probability=vision.probability,
                         predicted_date=vision.predicted_date,
                         status=new_status,
                         ai_model_version=vision.ai_model_version,
                         created_at=vision.created_at
                     )
            self._visions[vision_id.value] = updated
            return True
        return False
    
    async def add_explanation(self, vision_id: VisionId, explanation: dict) -> bool:
        vision = self._visions.get(vision_id.value)
        if vision:
            updated = vision.add_explanation(explanation)
            self._visions[vision_id.value] = updated
            return True
        return False
    
    async def delete(self, vision_id: VisionId) -> bool:
        if vision_id.value in self._visions:
            del self._visions[vision_id.value]
            return True
        return False
