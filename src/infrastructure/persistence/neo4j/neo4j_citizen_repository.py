"""
Infrastructure Adapter: Neo4j Citizen Repository
Implementación concreta del puerto CitizenRepository usando Neo4j
"""

from typing import List, Optional
from neo4j import AsyncGraphDatabase

from src.domain.models.citizen import Citizen, CitizenId, CitizenStatus
from src.domain.repositories.citizen_repository import CitizenRepository


class Neo4jCitizenRepository(CitizenRepository):
    """
    Adaptador de Infraestructura: Implementa CitizenRepository con Neo4j.
    
    Esta clase adapta las operaciones de dominio a queries Cypher de Neo4j.
    Es un ADAPTER en la arquitectura hexagonal.
    """
    
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
    
    def _to_domain(self, record: dict) -> Citizen:
        """Mapea un registro Neo4j a entidad de dominio."""
        return Citizen(
            id=CitizenId(record['id']),
            name=record['name'],
            born=record['born'],
            status=CitizenStatus(record.get('status', 'active')),
            risk_seed=record.get('risk_seed', 0.0),
            criminal_degree=record.get('criminal_degree', 0)
        )
    
    async def find_by_id(self, citizen_id: CitizenId) -> Optional[Citizen]:
        query = """
        MATCH (c:Citizen {id: $cid})
        OPTIONAL MATCH (c)-[:KNOWS]-(friend)
        WITH c, count(friend) as social_score
        RETURN c.id as id, c.name as name, c.born as born,
               c.status as status, c.risk_seed as risk_seed,
               c.criminal_degree as criminal_degree
        """
        results = await self._execute_query(query, {"cid": citizen_id.value})
        return self._to_domain(results[0]) if results else None
    
    async def find_all(self, limit: int = 100) -> List[Citizen]:
        query = """
        MATCH (c:Citizen)
        RETURN c.id as id, c.name as name, c.born as born, 
               c.status as status, c.risk_seed as risk_seed,
               c.criminal_degree as criminal_degree
        LIMIT $limit
        """
        results = await self._execute_query(query, {"limit": limit})
        return [self._to_domain(r) for r in results]
    
    async def find_high_risk(self, threshold: float = 0.7) -> List[Citizen]:
        query = """
        MATCH (c:Citizen)
        WHERE c.risk_seed > $thresh
        RETURN c.id as id, c.name as name, c.born as born, 
               c.status as status, c.risk_seed as risk_seed,
               c.criminal_degree as criminal_degree
        """
        results = await self._execute_query(query, {"thresh": threshold})
        return [self._to_domain(r) for r in results]
    
    async def save(self, citizen: Citizen) -> Citizen:
        query = """
        MERGE (c:Citizen {id: $id})
        SET c.name = $name,
            c.born = $born,
            c.status = $status,
            c.risk_seed = $risk_seed,
            c.criminal_degree = $criminal_degree
        RETURN c.id as id, c.name as name, c.born as born,
               c.status as status, c.risk_seed as risk_seed,
               c.criminal_degree as criminal_degree
        """
        params = {
            "id": citizen.id.value,
            "name": citizen.name,
            "born": citizen.born,
            "status": citizen.status.value,
            "risk_seed": citizen.risk_seed,
            "criminal_degree": citizen.criminal_degree
        }
        results = await self._execute_query(query, params)
        return self._to_domain(results[0])
    
    async def delete(self, citizen_id: CitizenId) -> bool:
        query = """
        MATCH (c:Citizen {id: $cid})
        DELETE c
        RETURN count(c) as deleted
        """
        results = await self._execute_query(query, {"cid": citizen_id.value})
        return results[0]['deleted'] > 0 if results else False
    
    async def find_with_criminal_connections(self, min_connections: int = 1) -> List[Citizen]:
        query = """
        MATCH (c:Citizen)
        WHERE c.risk_seed > 0.5
        MATCH (c)-[:KNOWS]-(associate)
        WHERE (associate)-[:COMMITTED_CRIME]->()
        WITH c, count(associate) as criminal_friends
        WHERE criminal_friends >= $min
        RETURN DISTINCT c.id as id, c.name as name, c.born as born, 
               c.status as status, c.risk_seed as risk_seed,
               c.criminal_degree as criminal_degree
        ORDER BY c.risk_seed DESC
        """
        results = await self._execute_query(query, {"min": min_connections})
        return [self._to_domain(r) for r in results]
    
    async def _execute_query(self, query: str, parameters: dict) -> List[dict]:
        """Ejecuta una query Cypher y retorna resultados."""
        if not self._driver:
            raise ConnectionError("Repository not connected")
        
        async with self._driver.session() as session:
            result = await session.run(query, parameters)
            return [record.data() async for record in result]
