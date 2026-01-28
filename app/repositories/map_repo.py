from app.core.database import db_manager
from typing import List, Dict, Any
import app.core.hardware_switch as hw
import numpy as np

class MapRepository:
    async def get_crime_heatmap(self) -> List[Dict[str, Any]]:
        """
        Devuelve ubicaciones de crímenes recientes para el Heatmap (HexagonLayer).
        Retorna [ {pos: [lon, lat], weight: float}, ... ]
        """
        if hw.DEMO_MODE:
            # Generate synthetic heatmap data for Madrid
            data = []
            # Create hotspots around key Madrid locations
            hotspots = [
                {"lat": 40.4168, "lon": -3.7038, "base_weight": 0.8},  # Puerta del Sol
                {"lat": 40.4073, "lon": -3.6937, "base_weight": 0.7},  # Atocha
                {"lat": 40.4200, "lon": -3.7050, "base_weight": 0.6},  # Gran Via
                {"lat": 40.4150, "lon": -3.6840, "base_weight": 0.5},  # Retiro
                {"lat": 40.4300, "lon": -3.7100, "base_weight": 0.65}, # Tetuan
            ]
            
            for hotspot in hotspots:
                # Create cluster of points around each hotspot
                for _ in range(15):
                    lat_offset = np.random.normal(0, 0.005)
                    lon_offset = np.random.normal(0, 0.005)
                    weight = hotspot["base_weight"] + np.random.uniform(-0.2, 0.2)
                    data.append({
                        "coordinates": [
                            hotspot["lon"] + lon_offset,
                            hotspot["lat"] + lat_offset
                        ],
                        "weight": max(0.1, min(1.0, weight))
                    })
            return data
        
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
        if hw.DEMO_MODE:
            # Generate synthetic vision markers for Madrid
            visions = []
            locations = [
                {"name": "Puerta del Sol", "lat": 40.4168, "lon": -3.7038},
                {"name": "Plaza Mayor", "lat": 40.4155, "lon": -3.7074},
                {"name": "Atocha Station", "lat": 40.4073, "lon": -3.6937},
                {"name": "Gran Via", "lat": 40.4200, "lon": -3.7050},
                {"name": "Retiro Park", "lat": 40.4150, "lon": -3.6840},
                {"name": "Lavapies", "lat": 40.4088, "lon": -3.7008},
            ]
            
            for i, loc in enumerate(locations):
                visions.append({
                    "id": f"VIS_DEMO_{i:03d}",
                    "probability": float(np.random.uniform(0.7, 0.95)),
                    "lon": loc["lon"] + np.random.normal(0, 0.001),
                    "lat": loc["lat"] + np.random.normal(0, 0.001),
                    "location_name": loc["name"]
                })
            return visions
        
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
