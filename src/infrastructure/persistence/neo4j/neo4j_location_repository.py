"""
Infrastructure Adapter: Neo4j Location Repository
Implementación del repositorio de ubicaciones usando Neo4j
"""

from typing import List, Optional
from neo4j import AsyncGraphDatabase

from src.domain.models.location import Location, LocationId, LocationType, Coordinates, Connection
from src.domain.repositories.location_repository import LocationRepository


class Neo4jLocationRepository(LocationRepository):
    """Adaptador de Infraestructura: Repositorio de ubicaciones con Neo4j."""
    
    def __init__(self, config: dict):
        self._uri = config.get('uri', 'bolt://localhost:7687')
        self._user = config.get('user', 'neo4j')
        self._password = config.get('password', 'password')
        self._driver = None
    
    async def connect(self):
        """Establece conexión con Neo4j."""
        if self._driver is None:
            self._driver = AsyncGraphDatabase.driver(
                self._uri,
                auth=(self._user, self._password)
            )
            await self._driver.verify_connectivity()
    
    async def close(self):
        """Cierra la conexión."""
        if self._driver:
            await self._driver.close()
            self._driver = None
    
    def _to_domain(self, record: dict) -> Location:
        """Mapea registro Neo4j a entidad de dominio."""
        location = Location(
            id=LocationId(record['id']),
            name=record['name'],
            location_type=LocationType(record.get('type', 'residential')),
            coordinates=Coordinates(
                latitude=record.get('lat', 0.0),
                longitude=record.get('lon', 0.0)
            ),
            env_risk=record.get('env_risk', 0.0)
        )
        
        # Cargar conexiones si existen
        if 'connections' in record:
            for conn in record['connections']:
                location.add_connection(
                    target=LocationId(conn['target']),
                    distance=conn.get('distance', 0),
                    risk_factor=conn.get('risk_factor', 0.0)
                )
        
        return location
    
    async def find_by_id(self, location_id: LocationId) -> Optional[Location]:
        query = """
        MATCH (l:Location {id: $lid})
        OPTIONAL MATCH (l)-[r:CONECTA_WITH]->(target:Location)
        WITH l, collect({target: target.id, distance: r.distancia, risk_factor: r.riesgo}) as connections
        RETURN l.id as id, l.name as name, l.type as type, 
               l.lat as lat, l.lon as lon, l.env_risk as env_risk,
               connections
        """
        results = await self._execute_query(query, {"lid": location_id.value})
        return self._to_domain(results[0]) if results else None
    
    async def find_all(self, limit: int = 100) -> List[Location]:
        query = """
        MATCH (l:Location)
        RETURN l.id as id, l.name as name, l.type as type,
               l.lat as lat, l.lon as lon, l.env_risk as env_risk
        LIMIT $limit
        """
        results = await self._execute_query(query, {"limit": limit})
        return [self._to_domain(r) for r in results]
    
    async def find_by_type(self, location_type: LocationType) -> List[Location]:
        query = """
        MATCH (l:Location {type: $type})
        RETURN l.id as id, l.name as name, l.type as type,
               l.lat as lat, l.lon as lon, l.env_risk as env_risk
        """
        results = await self._execute_query(query, {"type": location_type.value})
        return [self._to_domain(r) for r in results]
    
    async def find_safe_havens(self, risk_threshold: float = 0.3) -> List[Location]:
        query = """
        MATCH (l:Location)
        WHERE l.env_risk <= $threshold
        RETURN l.id as id, l.name as name, l.type as type,
               l.lat as lat, l.lon as lon, l.env_risk as env_risk
        """
        results = await self._execute_query(query, {"threshold": risk_threshold})
        return [self._to_domain(r) for r in results]
    
    async def find_nearby(self, location_id: LocationId, max_distance: float) -> List[Location]:
        query = """
        MATCH (l:Location {id: $lid})-[r:CONECTA_WITH]->(nearby:Location)
        WHERE r.distancia <= $max_dist
        RETURN nearby.id as id, nearby.name as name, nearby.type as type,
               nearby.lat as lat, nearby.lon as lon, nearby.env_risk as env_risk
        """
        results = await self._execute_query(query, {
            "lid": location_id.value,
            "max_dist": max_distance
        })
        return [self._to_domain(r) for r in results]
    
    async def save(self, location: Location) -> Location:
        query = """
        MERGE (l:Location {id: $id})
        SET l.name = $name,
            l.type = $type,
            l.lat = $lat,
            l.lon = $lon,
            l.env_risk = $env_risk
        RETURN l.id as id, l.name as name, l.type as type,
               l.lat as lat, l.lon as lon, l.env_risk as env_risk
        """
        params = {
            "id": location.id.value,
            "name": location.name,
            "type": location.location_type.value,
            "lat": location.coordinates.latitude,
            "lon": location.coordinates.longitude,
            "env_risk": location.env_risk
        }
        results = await self._execute_query(query, params)
        return self._to_domain(results[0])
    
    async def delete(self, location_id: LocationId) -> bool:
        query = """
        MATCH (l:Location {id: $lid})
        DETACH DELETE l
        RETURN count(l) as deleted
        """
        results = await self._execute_query(query, {"lid": location_id.value})
        return results[0].get('deleted', 0) > 0 if results else False
    
    async def update_risk(self, location_id: LocationId, new_risk: float) -> bool:
        query = """
        MATCH (l:Location {id: $lid})
        SET l.env_risk = $risk
        RETURN count(l) as updated
        """
        results = await self._execute_query(query, {
            "lid": location_id.value,
            "risk": new_risk
        })
        return results[0].get('updated', 0) > 0 if results else False
    
    async def _execute_query(self, query: str, parameters: dict) -> List[dict]:
        """Ejecuta query Cypher."""
        if not self._driver:
            raise ConnectionError("Repository not connected")
        
        async with self._driver.session() as session:
            result = await session.run(query, parameters)
            return [record.data() async for record in result]
