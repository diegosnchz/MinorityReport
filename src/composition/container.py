"""
Contenedor de Inyección de Dependencias
Configura y conecta todas las capas de la arquitectura hexagonal
"""

from typing import Optional
from src.domain.repositories.citizen_repository import CitizenRepository
from src.domain.repositories.location_repository import LocationRepository
from src.domain.repositories.vision_repository import VisionRepository
from src.domain.repositories.graph_repository import GraphRepository
from src.domain.services.ai_engine import AIPredictionEngine
from src.domain.services.routing_engine import RoutingEngine
from src.domain.services.simulation_engine import SimulationEngine

from src.infrastructure.persistence.neo4j.neo4j_citizen_repository import Neo4jCitizenRepository
from src.infrastructure.persistence.neo4j.neo4j_location_repository import Neo4jLocationRepository
from src.infrastructure.persistence.neo4j.neo4j_vision_repository import Neo4jVisionRepository
from src.infrastructure.persistence.neo4j.neo4j_graph_repository import Neo4jGraphRepository
from src.infrastructure.ai.torch_precog_engine import TorchPrecogEngine
from src.infrastructure.ai.mock_ai_engine import MockAIPredictionEngine
from src.infrastructure.config.settings import Settings


class Container:
    """
    Contenedor de Inyección de Dependencias.
    Implementa el patrón Dependency Injection para conectar adaptadores con dominio.
    """
    
    def __init__(self, settings: Optional[Settings] = None):
        self._settings = settings or Settings()
        self._repositories = {}
        self._services = {}
        self._initialized = False
    
    async def initialize(self):
        """Inicializa todas las dependencias en orden correcto."""
        if self._initialized:
            return
        
        # 1. Inicializar repositorios (adaptadores de persistencia)
        await self._init_repositories()
        
        # 2. Inicializar servicios de IA
        await self._init_ai_services()
        
        self._initialized = True
    
    async def shutdown(self):
        """Cierra todas las dependencias de forma ordenada."""
        for repo in self._repositories.values():
            if hasattr(repo, 'close'):
                await repo.close()
        self._initialized = False
    
    async def _init_repositories(self):
        """Inicializa adaptadores de persistencia basados en configuración."""
        if self._settings.demo_mode:
            # Modo demo: usar repositorios en memoria
            from src.infrastructure.persistence.memory.memory_citizen_repository import MemoryCitizenRepository
            from src.infrastructure.persistence.memory.memory_location_repository import MemoryLocationRepository
            from src.infrastructure.persistence.memory.memory_vision_repository import MemoryVisionRepository
            
            self._repositories['citizen'] = MemoryCitizenRepository()
            self._repositories['location'] = MemoryLocationRepository()
            self._repositories['vision'] = MemoryVisionRepository()
            self._repositories['graph'] = None  # No graph in demo mode
        else:
            # Modo producción: Neo4j
            neo4j_config = {
                'uri': self._settings.neo4j_uri,
                'user': self._settings.neo4j_user,
                'password': self._settings.neo4j_password
            }
            
            citizen_repo = Neo4jCitizenRepository(neo4j_config)
            location_repo = Neo4jLocationRepository(neo4j_config)
            vision_repo = Neo4jVisionRepository(neo4j_config)
            graph_repo = Neo4jGraphRepository(neo4j_config)
            
            await citizen_repo.connect()
            await location_repo.connect()
            await vision_repo.connect()
            await graph_repo.connect()
            
            self._repositories['citizen'] = citizen_repo
            self._repositories['location'] = location_repo
            self._repositories['vision'] = vision_repo
            self._repositories['graph'] = graph_repo
    
    async def _init_ai_services(self):
        """Inicializa motores de IA basados en configuración."""
        if self._settings.use_mock_ai:
            self._services['ai_engine'] = MockAIPredictionEngine()
        else:
            self._services['ai_engine'] = TorchPrecogEngine()
            await self._services['ai_engine'].load_models()
    
    # Accesos a repositorios (puertos)
    @property
    def citizen_repository(self) -> CitizenRepository:
        return self._repositories['citizen']
    
    @property
    def location_repository(self) -> LocationRepository:
        return self._repositories['location']
    
    @property
    def vision_repository(self) -> VisionRepository:
        return self._repositories['vision']
    
    @property
    def graph_repository(self) -> Optional[GraphRepository]:
        return self._repositories.get('graph')
    
    # Accesos a servicios
    @property
    def ai_engine(self) -> AIPredictionEngine:
        return self._services['ai_engine']
    
    @property
    def routing_engine(self) -> RoutingEngine:
        if 'routing' not in self._services:
            from src.infrastructure.routing.hybrid_routing_engine import HybridRoutingEngine
            self._services['routing'] = HybridRoutingEngine(self.graph_repository)
        return self._services['routing']
    
    @property
    def simulation_engine(self) -> SimulationEngine:
        if 'simulation' not in self._services:
            from src.infrastructure.simulation.graph_simulation_engine import GraphSimulationEngine
            self._services['simulation'] = GraphSimulationEngine(
                citizen_repo=self.citizen_repository,
                location_repo=self.location_repository,
                vision_repo=self.vision_repository,
                ai_engine=self.ai_engine
            )
        return self._services['simulation']
    
    @property
    def settings(self) -> Settings:
        return self._settings


# Instancia global del contenedor (Singleton)
_container: Optional[Container] = None


def get_container() -> Container:
    """Factory function para obtener el contenedor global."""
    global _container
    if _container is None:
        _container = Container()
    return _container


def reset_container():
    """Resetea el contenedor (útil para testing)."""
    global _container
    _container = None
