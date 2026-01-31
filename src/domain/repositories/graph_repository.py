"""
Repository Port: GraphRepository
Interfaz para operaciones de grafo y análisis de red
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Tuple

from src.domain.models.citizen import CitizenId
from src.domain.models.location import LocationId


class GraphRepository(ABC):
    """
    Puerto para operaciones avanzadas de grafo.
    
    Define operaciones de análisis de grafos que van más allá
    de las operaciones CRUD básicas (centrality, shortest paths, etc.)
    """
    
    @abstractmethod
    async def find_shortest_path(self, 
                                origin: LocationId, 
                                destination: LocationId,
                                weight_property: str = "distance") -> List[LocationId]:
        """Encuentra el camino más corto entre dos ubicaciones."""
        pass
    
    @abstractmethod
    async def calculate_centrality(self, location_id: LocationId) -> float:
        """Calcula la centralidad de una ubicación en el grafo."""
        pass
    
    @abstractmethod
    async def find_communities(self) -> List[List[LocationId]]:
        """Detecta comunidades en el grafo de ubicaciones."""
        pass
    
    @abstractmethod
    async def get_neighbors(self, location_id: LocationId, 
                          relationship_type: Optional[str] = None) -> List[LocationId]:
        """Obtiene vecinos de una ubicación."""
        pass
    
    @abstractmethod
    async def update_edge_weight(self, 
                               origin: LocationId, 
                               destination: LocationId,
                               weight: float,
                               property_name: str = "risk") -> bool:
        """Actualiza el peso de una arista."""
        pass
    
    @abstractmethod
    async def get_subgraph(self, 
                         center: LocationId, 
                         radius: int) -> Dict:
        """Obtiene un subgrafo centrado en una ubicación."""
        pass
    
    @abstractmethod
    async def connect(self) -> None:
        """Establece conexión con la base de datos de grafos."""
        pass
    
    @abstractmethod
    async def close(self) -> None:
        """Cierra la conexión."""
        pass
