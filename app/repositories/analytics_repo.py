from app.core.database import db_manager
from typing import List, Dict, Any

class AnalyticsRepository:
    async def get_spatial_hotspots(self) -> List[Dict[str, Any]]:
        """
        KPI 1 & 2: Análisis Espacial.
        Devuelve el conteo de visiones por tipo de lugar y las top 5 ubicaciones específicas.
        """
        # Agrupado por Tipo de Lugar (Ej. Bank, Park)
        query_type = """
        MATCH (v:Vision)-[:TARGETS]->(l:Location)
        RETURN l.type as type, 
               count(v) as count, 
               avg(v.probability) as avg_risk
        ORDER BY count DESC
        """
        by_type = await db_manager.query(query_type)
        
        # Top 5 Ubicaciones Específicas
        query_loc = """
        MATCH (v:Vision)-[:TARGETS]->(l:Location)
        RETURN l.name as name, l.type as type, count(v) as count
        ORDER BY count DESC LIMIT 5
        """
        top_locations = await db_manager.query(query_loc)
        
        return {
            "by_type": by_type,
            "top_locations": top_locations
        }

    async def get_social_influence(self) -> List[Dict[str, Any]]:
        """
        KPI 3 & 4: Análisis Social.
        Devuelve datos para correlacionar popularidad (grado conexiones) vs riesgo.
        """
        # Extraemos una muestra de ciudadanos para scatter plot: Risk vs Degree
        query = """
        MATCH (c:Citizen)
        // Contar conexiones KNOWS
        OPTIONAL MATCH (c)-[r:KNOWS]-()
        WITH c, count(r) as degree
        WHERE c.risk_seed IS NOT NULL
        RETURN degree, c.risk_seed as risk
        LIMIT 200
        """
        return await db_manager.query(query)

    async def get_hourly_patterns(self) -> List[Dict[str, Any]]:
        """
        KPI 5: Análisis Temporal.
        Distribución de visiones por hora del día.
        """
        # Nota: En Neo4j Community, datetime access puede variar.
        # Asumimos que timestamp es Neo4j DateTime.
        query = """
        MATCH (v:Vision)
        RETURN v.timestamp.hour as hour, count(*) as count
        ORDER BY hour ASC
        """
        return await db_manager.query(query)

    async def get_headline_stats(self) -> Dict[str, Any]:
        """
        NUEVO: Estadísticas tipo 'Marcador de Fútbol' para dashboard profesional.
        Devuelve un resumen de alto nivel del estado de la ciudad.
        """
        query = """
        MATCH (v:Vision)
        WITH count(v) as total_visions,
             sum(CASE WHEN v.status = 'OPEN' THEN 1 ELSE 0 END) as active_cases,
             sum(CASE WHEN v.status = 'INTERVENED' THEN 1 ELSE 0 END) as prevented_crimes,
             avg(v.probability) as avg_risk_level
        
        // Subquery para encontrar el lugar más peligroso
        CALL {
            MATCH (v2:Vision)-[:TARGETS]->(l:Location)
            RETURN l.name as dangerous_district, count(v2) as district_incidents
            ORDER BY district_incidents DESC LIMIT 1
        }
        
        RETURN total_visions, active_cases, prevented_crimes, avg_risk_level, 
               dangerous_district, district_incidents
        """
        results = await db_manager.query(query)
        if not results:
             return {
                 "active_cases": 0,
                 "prevented_crimes": 0,
                 "avg_risk_level": 0.0,
                 "most_dangerous_district": "N/A"
             }
             
        row = results[0]
        return {
            "active_cases": row['active_cases'],
            "prevented_crimes": row['prevented_crimes'],
            "avg_risk_level": row['avg_risk_level'],
            "most_dangerous_district": row['dangerous_district']
        }

    async def get_system_stats(self) -> Dict[str, Any]:
        """
        KPI 7 & 8: Rendimiento Global.
        """
        query = """
        MATCH (v:Vision)
        RETURN count(v) as total,
               sum(CASE WHEN v.status = 'INTERVENED' THEN 1 ELSE 0 END) as intervened,
               avg(v.probability) as avg_confidence
        """
        results = await db_manager.query(query)
        if not results:
            return {"total": 0, "intervened": 0, "avg_confidence": 0}
            
        data = results[0]
        total = data['total'] or 0
        intervened = data['intervened'] or 0
        rate = (intervened / total * 100) if total > 0 else 0.0
        
        return {
            "total_visions": total,
            "intervened_count": intervened,
            "intervention_rate": rate,
            "avg_confidence": data['avg_confidence'] or 0.0
        }

analytics_repo = AnalyticsRepository()
