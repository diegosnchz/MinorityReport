from app.core.database import db_manager
from typing import List

class LocationRepository:
    async def find_all(self, limit: int = 100) -> List[dict]:
        query = """
        MATCH (l:Location)
        RETURN l.id as id, l.name as name, l.type as type, 
               l.env_risk as env_risk, 
               l.coord.latitude as latitude, l.coord.longitude as longitude
        LIMIT $limit
        """
        return await db_manager.query(query, {"limit": limit})

    async def find_hotspots(self) -> List[dict]:
        """
        Identifica zonas de alto riesgo basándose en crímenes pasados.
        Vital para asignar patrullas preventivas.
        """
        query = """
        MATCH (l:Location)<-[:COMMITTED_CRIME]-(c)
        RETURN l.id as id, l.name as name, l.type as type,
               l.env_risk as env_risk,
               l.coord.latitude as latitude, l.coord.longitude as longitude,
               count(c) as historical_crime_count
        ORDER BY historical_crime_count DESC
        LIMIT 10
        """
        # Note: Added fields to return to match Schema
        return await db_manager.query(query)

location_repo = LocationRepository()
