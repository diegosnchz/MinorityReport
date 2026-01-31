"""
Infrastructure Adapter: Neo4j Graph Repository
Implementación de operaciones avanzadas de grafo usando Neo4j
"""

from typing import List, Dict, Optional
from neo4j import AsyncGraphDatabase

from src.domain.models.location import LocationId
from src.domain.repositories.graph_repository import GraphRepository


class Neo4jGraphRepository(GraphRepository):
    """
    Adaptador de Infraestructura: Operaciones avanzadas de grafo con Neo4j.
    
    Implementa algoritmos de análisis de grafos usando Cypher y GDS.
    """
    
    def __init__(self, config: dict):
        self._uri = config.get('uri', 'bolt://localhost:7687')
        self._user = config.get('user', 'neo4j')
        self._password = config.get('password', 'password')
        self._driver = None
    
    async def connect(self) -> None:
        """Establece conexión con Neo4j."""
        if self._driver is None:
            self._driver = AsyncGraphDatabase.driver(
                self._uri,
                auth=(self._user, self._password)
            )
            await self._driver.verify_connectivity()
    
    async def close(self) -> None:
        """Cierra la conexión."""
        if self._driver:
            await self._driver.close()
            self._driver = None
    
    async def find_shortest_path(self, 
                                origin: LocationId, 
                                destination: LocationId,
                                weight_property: str = "distance") -> List[LocationId]:
        """Encuentra camino más corto usando Dijkstra."""
        query = """
        MATCH (start:Location {id: $origin}), (end:Location {id: $destination})
        CALL apoc.algo.dijkstra(start, end, 'CONNECTS_WITH', $weight) YIELD path, weight
        RETURN [node in nodes(path) | node.id] as path_ids
        """
        results = await self._execute_query(query, {
            "origin": origin.value,
            "destination": destination.value,
            "weight": weight_property
        })
        
        if results:
            return [LocationId(pid) for pid in results[0].get('path_ids', [])]
        return []
    
    async def calculate_centrality(self, location_id: LocationId) -> float:
        """Calcula betweenness centrality."""
        query = """
        MATCH (l:Location {id: $loc_id})
        RETURN l.centrality as centrality
        """
        results = await self._execute_query(query, {"loc_id": location_id.value})
        return results[0].get('centrality', 0.0) if results else 0.0
    
    async def find_communities(self) -> List[List[LocationId]]:
        """Detecta comunidades usando Louvain."""
        query = """
        CALL gds.louvain.stream('location-graph')
        YIELD nodeId, communityId
        RETURN communityId, collect(gds.util.asNode(nodeId).id) as members
        """
        results = await self._execute_query(query)
        return [
            [LocationId(mid) for mid in r.get('members', [])]
            for r in results
        ]
    
    async def get_neighbors(self, location_id: LocationId, 
                          relationship_type: Optional[str] = None) -> List[LocationId]:
        """Obtiene vecinos de una ubicación."""
        rel_type = relationship_type or "CONNECTS_WITH"
        query = f"""
        MATCH (l:Location {{id: $loc_id}})-[:{rel_type}]-(neighbor:Location)
        RETURN collect(neighbor.id) as neighbors
        """
        results = await self._execute_query(query, {"loc_id": location_id.value})
        
        if results:
            return [LocationId(nid) for nid in results[0].get('neighbors', [])]
        return []
    
    async def update_edge_weight(self, 
                               origin: LocationId, 
                               destination: LocationId,
                               weight: float,
                               property_name: str = "risk") -> bool:
        """Actualiza peso de arista."""
        query = f"""
        MATCH (a:Location {{id: $origin}})-[r:CONECTA_WITH]->(b:Location {{id: $dest}})
        SET r.{property_name} = $weight
        RETURN count(r) as updated
        """
        results = await self._execute_query(query, {
            "origin": origin.value,
            "dest": destination.value,
            "weight": weight
        })
        return results[0].get('updated', 0) > 0 if results else False
    
    async def get_subgraph(self, 
                         center: LocationId, 
                         radius: int) -> Dict:
        """Obtiene subgrafo en un radio determinado."""
        query = """
        MATCH path = (center:Location {id: $center})-[:CONNECTS_WITH*1..$radius]-(neighbor:Location)
        WITH center, neighbor, relationships(path) as rels
        RETURN center.id as center_id,
               collect(DISTINCT neighbor.id) as neighbors,
               count(DISTINCT neighbor) as node_count
        """
        results = await self._execute_query(query, {
            "center": center.value,
            "radius": radius
        })
        
        if results:
            return {
                "center": results[0].get('center_id'),
                "neighbors": results[0].get('neighbors', []),
                "node_count": results[0].get('node_count', 0)
            }
        return {"center": center.value, "neighbors": [], "node_count": 0}
    
    async def _execute_query(self, query: str, parameters: dict = None) -> List[dict]:
        """Ejecuta query Cypher."""
        if not self._driver:
            raise ConnectionError("Repository not connected")
        
        async with self._driver.session() as session:
            result = await session.run(query, parameters or {})
            return [record.data() async for record in result]
