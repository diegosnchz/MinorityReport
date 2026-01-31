"""
Infrastructure: Memory Repositories (Demo Mode)
Implementaciones en memoria para testing y modo demo
"""

from typing import List, Optional
import random

from src.domain.models.citizen import Citizen, CitizenId, CitizenStatus
from src.domain.repositories.citizen_repository import CitizenRepository


class MemoryCitizenRepository(CitizenRepository):
    """
    Adaptador de Infraestructura: Repositorio en memoria para ciudadanos.
    
    Usado en modo demo cuando no hay conexión a Neo4j.
    """
    
    def __init__(self):
        self._citizens: dict = {}
        self._seed_data()
    
    def _seed_data(self):
        """Carga datos de ejemplo."""
        sample_citizens = [
            Citizen(CitizenId(1), "John Anderton", 1980, CitizenStatus.ACTIVE, 0.2, 0),
            Citizen(CitizenId(2), "Agatha", 1990, CitizenStatus.WATCHLIST, 0.6, 1),
            Citizen(CitizenId(3), "Arthur", 1985, CitizenStatus.ACTIVE, 0.3, 0),
            Citizen(CitizenId(4), "Dash", 1992, CitizenStatus.INTERVENE, 0.85, 3),
            Citizen(CitizenId(5), "Tom Cruise", 1962, CitizenStatus.ACTIVE, 0.15, 0),
        ]
        for c in sample_citizens:
            self._citizens[c.id.value] = c
    
    async def find_by_id(self, citizen_id: CitizenId) -> Optional[Citizen]:
        return self._citizens.get(citizen_id.value)
    
    async def find_all(self, limit: int = 100) -> List[Citizen]:
        return list(self._citizens.values())[:limit]
    
    async def find_high_risk(self, threshold: float = 0.7) -> List[Citizen]:
        return [c for c in self._citizens.values() if c.risk_seed >= threshold]
    
    async def save(self, citizen: Citizen) -> Citizen:
        self._citizens[citizen.id.value] = citizen
        return citizen
    
    async def delete(self, citizen_id: CitizenId) -> bool:
        if citizen_id.value in self._citizens:
            del self._citizens[citizen_id.value]
            return True
        return False
    
    async def find_with_criminal_connections(self, min_connections: int = 1) -> List[Citizen]:
        # Simulación: ciudadanos con criminal_degree > 0
        return [c for c in self._citizens.values() if c.criminal_degree >= min_connections]
