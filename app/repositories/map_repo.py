from app.core.database import db_manager
from typing import List, Dict, Any
import app.core.hardware_switch as hw
import numpy as np

class MapRepository:
    async def get_crime_heatmap(self) -> List[Dict[str, Any]]:
        """
        Devuelve ubicaciones de crímenes recientes para el Heatmap (HexagonLayer).
        Retorna [ {pos: [lon, lat], weight: float}, ... ]
        Data is regenerated stochastically on each call.
        """
        if hw.DEMO_MODE:
            # Generate synthetic heatmap data spread across Madrid
            # Randomized on each call for dynamic visualization
            data = []
            # Create hotspots across different areas of Madrid with random weights
            hotspots = [
                {"lat": 40.4168, "lon": -3.7038, "name": "Sol"},
                {"lat": 40.4073, "lon": -3.6937, "name": "Atocha"},
                {"lat": 40.4200, "lon": -3.7050, "name": "Gran Via"},
                {"lat": 40.4150, "lon": -3.6840, "name": "Retiro"},
                {"lat": 40.4300, "lon": -3.7100, "name": "Tetuan"},
                {"lat": 40.4500, "lon": -3.6900, "name": "Chamartin"},
                {"lat": 40.3900, "lon": -3.7000, "name": "Usera"},
                {"lat": 40.4100, "lon": -3.7400, "name": "Casa de Campo"},
                {"lat": 40.4250, "lon": -3.6600, "name": "Salamanca"},
                {"lat": 40.4400, "lon": -3.7200, "name": "Cuatro Caminos"},
            ]
            
            for hotspot in hotspots:
                # Random base weight for each hotspot (changes each call)
                base_weight = np.random.uniform(0.3, 0.9)
                # Random number of points per hotspot (5-12)
                num_points = np.random.randint(5, 13)
                
                for _ in range(num_points):
                    lat_offset = np.random.normal(0, 0.012)
                    lon_offset = np.random.normal(0, 0.012)
                    weight = base_weight + np.random.uniform(-0.25, 0.25)
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
               l.env_risk as base_risk,
               past_crimes
        """
        results = await db_manager.query(query)
        
        # Formato Deck.gl - ADD RANDOMNESS so bars change on each call
        data = []
        for row in results:
            # Base weight from database + random variation
            base_weight = row.get('base_risk', 0.3) + (row.get('past_crimes', 0) * 0.1)
            # Add stochastic variation (-0.3 to +0.3)
            random_variation = np.random.uniform(-0.3, 0.3)
            final_weight = max(0.1, min(1.0, base_weight + random_variation))
            
            # Add random coordinate offset so bars MOVE to new positions
            lat_offset = np.random.uniform(-0.02, 0.02)
            lon_offset = np.random.uniform(-0.02, 0.02)
            
            data.append({
                "coordinates": [row['lon'] + lon_offset, row['lat'] + lat_offset],
                "weight": final_weight
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
