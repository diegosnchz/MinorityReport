from app.core.database import db_manager
from typing import List, Dict, Any

class MapRepository:
    async def get_crime_heatmap(self) -> List[Dict[str, Any]]:
        """
        Devuelve ubicaciones de crímenes recientes para el Heatmap (HexagonLayer).
        Retorna [ {pos: [lon, lat], weight: float}, ... ]
        """
        # Consulta: Ubicaciones donde han ocurrido crímenes (:COMMITTED_CRIME)
        # O donde hay una Vision activa (:TARGETS)
        query = """
        MATCH (l:Location)
        WHERE l.coord IS NOT NULL
        
        // Calcular peso basado en riesgo ambiental y crímenes históricos
        OPTIONAL MATCH ()-[r:COMMITTED_CRIME]->(l)
        WITH l, count(r) as past_crimes
        
        RETURN l.coord.longitude as lon, 
               l.coord.latitude as lat, 
               (l.env_risk + (past_crimes * 0.1)) as weight
        """
        results = await db_manager.query(query)
        
        # Formato Deck.gl
        data = []
        for row in results:
            data.append({
                "coordinates": [row['lon'], row['lat']],
                "weight": row['weight']
            })
        return data

    async def get_active_visions_geo(self) -> List[Dict[str, Any]]:
        """
        Devuelve Visiones activas con coordenadas para ScatterplotLayer.
        """
        query = """
        MATCH (v:Vision {status: 'OPEN'})-[:TARGETS]->(l:Location)
        WHERE l.coord IS NOT NULL
        RETURN v.id as id, 
               v.probability as probability,
               l.coord.longitude as lon, 
               l.coord.latitude as lat,
               l.name as location_name
        """
        return await db_manager.query(query)

map_repo = MapRepository()
