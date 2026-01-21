# app/repositories/citizen_repo.py
from app.core.database import db_manager
from typing import List, Optional

class CitizenRepository:
    """
    Encapsula toda la lógica de acceso a datos para Ciudadanos.
    Equivalente a CharacterRepo en Spring, pero con Cypher explícito.
    """
    async def find_all(self, limit: int = 100) -> List[dict]:
        """Recupera todos los ciudadanos (con límite de seguridad)."""
        query = """
        MATCH (c:Citizen)
        RETURN c.id as id, c.name as name, c.born as born, 
               c.status as status, c.risk_seed as risk_seed
        LIMIT $limit
        """
        return await db_manager.query(query, {"limit": limit})

    async def find_by_id(self, citizen_id: int) -> Optional[dict]:
        """Busca un ciudadano específico y calcula sus métricas al vuelo."""
        query = """
        MATCH (c:Citizen {id: $cid})
        // Subquery para enriquecer el dato al vuelo
        OPTIONAL MATCH (c)-[:KNOWS]-(friend)
        WITH c, count(friend) as social_score
        RETURN c.id as id, c.name as name, c.born as born,
               c.status as status, social_score, c.risk_seed as risk_seed
        """
        # Note: Added risk_seed to return to map to Citizen schema comfortably
        results = await db_manager.query(query, {"cid": citizen_id})
        return results[0] if results else None

    async def find_high_risk_suspects(self, threshold: float = 0.8) -> List[dict]:
        """
        Una query que Spring Data tendría dificultades para generar automáticamente.
        Buscamos ciudadanos conectados a criminales.
        """
        query = """
        MATCH (c:Citizen)
        WHERE c.risk_seed > $thresh
        MATCH (c)-[:KNOWS]-(associate)
        WHERE (associate)-[:COMMITTED_CRIME]->()
        RETURN DISTINCT c.id as id, c.name as name, c.born as born, c.status as status,
                        c.risk_seed as risk_seed, 
                        count(associate) as criminal_friends
        ORDER BY risk_seed DESC
        """
        # Updated return to match Citizen schema fields largely, though this might need custom response model if strictly typed
        return await db_manager.query(query, {"thresh": threshold})

# Instancia Singleton
citizen_repo = CitizenRepository()
