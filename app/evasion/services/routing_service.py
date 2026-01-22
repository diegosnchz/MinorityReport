import numpy as np
import random
from app.evasion.math.heuristics import calculate_heuristic_cost
from app.repositories.location_repo import location_repo

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
        start = await location_repo.find_by_id(start_loc_id)
        end = await location_repo.find_by_id(end_loc_id)
        
        if not start or not end:
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
        lats = np.linspace(start['lat'], end['lat'], n_steps)
        lons = np.linspace(start['lon'], end['lon'], n_steps)
        
        path = []
        for i in range(n_steps):
            path.append({
                "lat": lats[i] + random.uniform(-0.001, 0.001),
                "lon": lons[i] + random.uniform(-0.001, 0.001),
                "name": f"Waypoint {i}" if i > 0 else start['name']
            })
        return path

routing_service = RoutingService()
