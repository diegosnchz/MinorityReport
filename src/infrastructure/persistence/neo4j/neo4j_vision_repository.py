"""
Infrastructure Adapter: Neo4j Vision Repository
Implementación del repositorio de visiones usando Neo4j
"""

from typing import List, Optional
from datetime import datetime
from neo4j import AsyncGraphDatabase

from src.domain.models.vision import Vision, VisionId, VisionStatus
from src.domain.models.citizen import CitizenId
from src.domain.models.location import LocationId
from src.domain.repositories.vision_repository import VisionRepository


class Neo4jVisionRepository(VisionRepository):
    """Adaptador de Infraestructura: Repositorio de visiones con Neo4j."""
    
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
    
    def _to_domain(self, record: dict) -> Vision:
        """Mapea registro Neo4j a entidad de dominio."""
        return Vision(
            id=VisionId(record['id']),
            citizen_id=CitizenId(record['citizen_id']),
            location_id=LocationId(record['location_id']),
            probability=record['probability'],
            predicted_date=record['predicted_date'],
            status=VisionStatus(record['status']),
            ai_model_version=record.get('ai_model_version', 'unknown'),
            created_at=record.get('created_at', datetime.now()),
            explained=record.get('explained', False),
            explanation_data=record.get('explanation_data')
        )
    
    async def find_by_id(self, vision_id: VisionId) -> Optional[Vision]:
        query = """
        MATCH (v:Vision {id: $vid})
        RETURN v.id as id, v.probability as probability,
               v.predicted_date as predicted_date, v.status as status,
               v.ai_model_version as ai_model_version, v.created_at as created_at,
               v.explained as explained, v.explanation_data as explanation_data,
               v.citizen_id as citizen_id, v.location_id as location_id
        """
        results = await self._execute_query(query, {"vid": vision_id.value})
        return self._to_domain(results[0]) if results else None
    
    async def find_all(self, limit: int = 100) -> List[Vision]:
        query = """
        MATCH (v:Vision)
        RETURN v.id as id, v.probability as probability,
               v.predicted_date as predicted_date, v.status as status,
               v.ai_model_version as ai_model_version, v.created_at as created_at,
               v.explained as explained, v.explanation_data as explanation_data,
               v.citizen_id as citizen_id, v.location_id as location_id
        LIMIT $limit
        """
        results = await self._execute_query(query, {"limit": limit})
        return [self._to_domain(r) for r in results]
    
    async def find_by_citizen(self, citizen_id: CitizenId) -> List[Vision]:
        query = """
        MATCH (v:Vision {citizen_id: $cid})
        RETURN v.id as id, v.probability as probability,
               v.predicted_date as predicted_date, v.status as status,
               v.ai_model_version as ai_model_version, v.created_at as created_at,
               v.explained as explained, v.explanation_data as explanation_data,
               v.citizen_id as citizen_id, v.location_id as location_id
        """
        results = await self._execute_query(query, {"cid": citizen_id.value})
        return [self._to_domain(r) for r in results]
    
    async def find_by_location(self, location_id: LocationId) -> List[Vision]:
        query = """
        MATCH (v:Vision {location_id: $lid})
        RETURN v.id as id, v.probability as probability,
               v.predicted_date as predicted_date, v.status as status,
               v.ai_model_version as ai_model_version, v.created_at as created_at,
               v.explained as explained, v.explanation_data as explanation_data,
               v.citizen_id as citizen_id, v.location_id as location_id
        """
        results = await self._execute_query(query, {"lid": location_id.value})
        return [self._to_domain(r) for r in results]
    
    async def find_by_status(self, status: VisionStatus) -> List[Vision]:
        query = """
        MATCH (v:Vision {status: $status})
        RETURN v.id as id, v.probability as probability,
               v.predicted_date as predicted_date, v.status as status,
               v.ai_model_version as ai_model_version, v.created_at as created_at,
               v.explained as explained, v.explanation_data as explanation_data,
               v.citizen_id as citizen_id, v.location_id as location_id
        """
        results = await self._execute_query(query, {"status": status.value})
        return [self._to_domain(r) for r in results]
    
    async def find_critical(self, threshold: float = 0.8) -> List[Vision]:
        query = """
        MATCH (v:Vision)
        WHERE v.probability >= $threshold
        RETURN v.id as id, v.probability as probability,
               v.predicted_date as predicted_date, v.status as status,
               v.ai_model_version as ai_model_version, v.created_at as created_at,
               v.explained as explained, v.explanation_data as explanation_data,
               v.citizen_id as citizen_id, v.location_id as location_id
        ORDER BY v.probability DESC
        """
        results = await self._execute_query(query, {"threshold": threshold})
        return [self._to_domain(r) for r in results]
    
    async def find_pending_before(self, date: datetime) -> List[Vision]:
        query = """
        MATCH (v:Vision {status: 'pending'})
        WHERE v.predicted_date < $date
        RETURN v.id as id, v.probability as probability,
               v.predicted_date as predicted_date, v.status as status,
               v.ai_model_version as ai_model_version, v.created_at as created_at,
               v.explained as explained, v.explanation_data as explanation_data,
               v.citizen_id as citizen_id, v.location_id as location_id
        """
        results = await self._execute_query(query, {"date": date})
        return [self._to_domain(r) for r in results]
    
    async def save(self, vision: Vision) -> Vision:
        query = """
        MERGE (v:Vision {id: $id})
        SET v.probability = $probability,
            v.predicted_date = $predicted_date,
            v.status = $status,
            v.ai_model_version = $ai_model_version,
            v.created_at = $created_at,
            v.citizen_id = $citizen_id,
            v.location_id = $location_id,
            v.explained = $explained
        RETURN v.id as id, v.probability as probability,
               v.predicted_date as predicted_date, v.status as status,
               v.ai_model_version as ai_model_version, v.created_at as created_at,
               v.explained as explained, v.explanation_data as explanation_data,
               v.citizen_id as citizen_id, v.location_id as location_id
        """
        params = {
            "id": vision.id.value,
            "probability": vision.probability,
            "predicted_date": vision.predicted_date,
            "status": vision.status.value,
            "ai_model_version": vision.ai_model_version,
            "created_at": vision.created_at,
            "citizen_id": vision.citizen_id.value,
            "location_id": vision.location_id.value,
            "explained": vision.explained
        }
        results = await self._execute_query(query, params)
        return self._to_domain(results[0])
    
    async def update_status(self, vision_id: VisionId, new_status: VisionStatus) -> bool:
        query = """
        MATCH (v:Vision {id: $vid})
        SET v.status = $status
        RETURN count(v) as updated
        """
        results = await self._execute_query(query, {
            "vid": vision_id.value,
            "status": new_status.value
        })
        return results[0].get('updated', 0) > 0 if results else False
    
    async def add_explanation(self, vision_id: VisionId, explanation: dict) -> bool:
        query = """
        MATCH (v:Vision {id: $vid})
        SET v.explained = true,
            v.explanation_data = $explanation
        RETURN count(v) as updated
        """
        import json
        results = await self._execute_query(query, {
            "vid": vision_id.value,
            "explanation": json.dumps(explanation)
        })
        return results[0].get('updated', 0) > 0 if results else False
    
    async def delete(self, vision_id: VisionId) -> bool:
        query = """
        MATCH (v:Vision {id: $vid})
        DELETE v
        RETURN count(v) as deleted
        """
        results = await self._execute_query(query, {"vid": vision_id.value})
        return results[0].get('deleted', 0) > 0 if results else False
    
    async def _execute_query(self, query: str, parameters: dict) -> List[dict]:
        """Ejecuta query Cypher."""
        if not self._driver:
            raise ConnectionError("Repository not connected")
        
        async with self._driver.session() as session:
            result = await session.run(query, parameters)
            return [record.data() async for record in result]
