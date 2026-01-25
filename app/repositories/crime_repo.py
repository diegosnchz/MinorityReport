from app.core.database import db_manager
from typing import List

class CrimeRepository:
    async def find_recent_activity(self, limit: int = 50) -> List[dict]:
        """
        Reporte de actividad reciente para el dashboard policial.
        """
        query = """
        MATCH (c:Citizen)-[r:COMMITTED_CRIME]->(l:Location)
        RETURN r.date as date, r.type as type, r.severity as severity,
               c.name as perpetrator_name, l.name as location_name
        ORDER BY r.date DESC
        LIMIT $limit
        """
        return await db_manager.query(query, {"limit": limit})

crime_repo = CrimeRepository()
