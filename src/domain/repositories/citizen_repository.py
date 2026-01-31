"""
Repository Port: CitizenRepository
Interfaz que define las operaciones de persistencia para ciudadanos
"""

from abc import ABC, abstractmethod
from typing import List, Optional

from src.domain.models.citizen import Citizen, CitizenId


class CitizenRepository(ABC):
    """
    Puerto (Interface) para el repositorio de ciudadanos.
    
    Esta interfaz define el contrato que cualquier adaptador de persistencia
    debe implementar. El dominio NO sabe/cares si usa Neo4j, SQL, o memoria.
    """
    
    @abstractmethod
    async def find_by_id(self, citizen_id: CitizenId) -> Optional[Citizen]:
        """Busca un ciudadano por su ID."""
        pass
    
    @abstractmethod
    async def find_all(self, limit: int = 100) -> List[Citizen]:
        """Recupera todos los ciudadanos con límite."""
        pass
    
    @abstractmethod
    async def find_high_risk(self, threshold: float = 0.7) -> List[Citizen]:
        """Busca ciudadanos de alto riesgo."""
        pass
    
    @abstractmethod
    async def save(self, citizen: Citizen) -> Citizen:
        """Guarda o actualiza un ciudadano."""
        pass
    
    @abstractmethod
    async def delete(self, citizen_id: CitizenId) -> bool:
        """Elimina un ciudadano por ID."""
        pass
    
    @abstractmethod
    async def find_with_criminal_connections(self, min_connections: int = 1) -> List[Citizen]:
        """Busca ciudadanos conectados a criminales."""
        pass
