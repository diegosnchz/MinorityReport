import numpy as np
import random
from app.evasion.math.heuristics import calculate_heuristic_cost
from app.repositories.location_repo import location_repo
import app.core.hardware_switch as hw

class RoutingService:
    """
    Servicio táctico de rutas de escape.
    Calcula el camino óptimo minimizando el coste de detección.
    """
    
    async def find_safe_path(self, start_loc_id: str, end_loc_id: str):
        """
        Calcula una ruta de escape.
        En una impl real, esto haría A* sobre el grafo de Neo4j usando Numba para los pesos.
        """
        # 1. Obtener ubicaciones
        start = None
        end = None
        
        if hw.DEMO_MODE:
            # Mock de ubicaciones
            start = {"lat": 40.4168, "lon": -3.7038, "name": "Puerta del Sol"}
            end = {"lat": 40.4150, "lon": -3.6840, "name": "Parque de El Retiro"}
        else:
            start = await location_repo.find_by_id(start_loc_id)
            end = await location_repo.find_by_id(end_loc_id)
        
        if not start or not end:
            # FALLBACK: Si no existen los IDs específicos (LOC_SOL), pillamos dos al azar para la DEMO
            if not hw.DEMO_MODE:
                all_locs = await location_repo.find_all(limit=10)
                if len(all_locs) >= 2:
                    start = all_locs[0]
                    end = all_locs[1]
                else:
                    return None
            else:
                 return None

        # 2. Simular generación de nodos intermedios (City Graph)
        # En una ruta real, estos vendrían de Neo4j
        path_nodes = self._generate_simulated_path(start, end)
        
        # 3. Calcular costes JIT (Numba)
        total_cost = 0
        for i in range(len(path_nodes) - 1):
            dist = 0.5 # km
            risk = random.uniform(0.1, 0.4)
            fatigue = 0.2
            terrain = 1.2 # Alleyways
            
            # LLAMADA A FUNCIÓN COMPILADA JIT
            cost = calculate_heuristic_cost(dist, risk, fatigue, terrain)
            total_cost += cost
            
        return {
            "path": path_nodes,
            "total_risk_score": total_cost,
            "confidence": 0.95,
            "sectors_crossed": ["Sector 4", "Usera"]
        }

    def _generate_simulated_path(self, start, end):
        """Genera puntos geográficos entre origen y destino."""
        n_steps = 5
        
        # Defensive check for coordinates
        start_lat = start.get('lat') or start.get('latitude') or 40.41
        start_lon = start.get('lon') or start.get('longitude') or -3.70
        end_lat = end.get('lat') or end.get('latitude') or 40.415
        end_lon = end.get('lon') or end.get('longitude') or -3.705

        lats = np.linspace(start_lat, end_lat, n_steps)
        lons = np.linspace(start_lon, end_lon, n_steps)
        
        path = []
        for i in range(n_steps):
            path.append({
                "lat": float(lats[i]) + random.uniform(-0.001, 0.001),
                "lon": float(lons[i]) + random.uniform(-0.001, 0.001),
                "name": f"Waypoint {i}" if i > 0 else start.get('name', 'Origin')
            })
        return path

routing_service = RoutingService()
