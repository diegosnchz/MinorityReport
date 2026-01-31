"""
Repository Port: VisionRepository
Interfaz para operaciones de persistencia de visiones/predicciones
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Optional

from src.domain.models.vision import Vision, VisionId, VisionStatus
from src.domain.models.citizen import CitizenId
from src.domain.models.location import LocationId


class VisionRepository(ABC):
    """
    Puerto para el repositorio de visiones (predicciones).
    Gestiona el almacenamiento de predicciones de crímenes futuros.
    """
    
    @abstractmethod
    async def find_by_id(self, vision_id: VisionId) -> Optional[Vision]:
        """Busca una visión por su ID."""
        pass
    
    @abstractmethod
    async def find_all(self, limit: int = 100) -> List[Vision]:
        """Recupera todas las visiones."""
        pass
    
    @abstractmethod
    async def find_by_citizen(self, citizen_id: CitizenId) -> List[Vision]:
        """Busca visiones de un ciudadano específico."""
        pass
    
    @abstractmethod
    async def find_by_location(self, location_id: LocationId) -> List[Vision]:
        """Busca visiones en una ubicación específica."""
        pass
    
    @abstractmethod
    async def find_by_status(self, status: VisionStatus) -> List[Vision]:
        """Busca visiones por estado."""
        pass
    
    @abstractmethod
    async def find_critical(self, threshold: float = 0.8) -> List[Vision]:
        """Busca visiones críticas (alta probabilidad)."""
        pass
    
    @abstractmethod
    async def find_pending_before(self, date: datetime) -> List[Vision]:
        """Busca visiones pendientes que expiran antes de una fecha."""
        pass
    
    @abstractmethod
    async def save(self, vision: Vision) -> Vision:
        """Guarda o actualiza una visión."""
        pass
    
    @abstractmethod
    async def update_status(self, vision_id: VisionId, new_status: VisionStatus) -> bool:
        """Actualiza el estado de una visión."""
        pass
    
    @abstractmethod
    async def add_explanation(self, vision_id: VisionId, explanation: dict) -> bool:
        """Añade datos explicativos XAI a una visión."""
        pass
    
    @abstractmethod
    async def delete(self, vision_id: VisionId) -> bool:
        """Elimina una visión."""
        pass
