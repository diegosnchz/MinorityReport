from typing import List, Dict, Any
from app.repositories.vision_repo import vision_repo
from app.repositories.citizen_repo import citizen_repo

class VisionService:
    """
    Capa de Lógica de Negocio.
    Transforma datos crudos de la BD en estructuras útiles para la UI.
    """
    async def get_dashboard_graph(self, limit: int = 100) -> Dict[str, Any]:
        """
        Orquesta la obtención de datos y el formateo para D3.js / ForceGraph.
        """
        # 1. Obtener datos crudos del repositorio (Tuplas de Nodos)
        raw_data = await vision_repo.get_graph_visualization(limit)
        
        # 2. Transformación (La lógica que antes estaba dispersa)
        # El frontend espera: { "nodes": [...], "links": [...] }
        formatted_graph = self._to_d3_format(raw_data)
        return formatted_graph

    async def search_visions(self, query: str) -> List[dict]:
        """
        Búsqueda difusa: Permite buscar por nombre de criminal o lugar.
        """
        return await vision_repo.search_by_text(query)

    def _to_d3_format(self, raw_data: dict) -> Dict[str, Any]:
        """
        Transforma la salida de Neo4j en el JSON que D3.js necesita.
        Asigna colores (grupos) y tamaños basados en riesgo.
        """
        nodes = []
        links = []
        seen_nodes = set()
        
        # Procesar Nodos (raw_data['nodes'] viene del repo)
        for node in raw_data['nodes']:
            if node['id'] in seen_nodes:
                continue
            
            # Lógica de Visualización:
            # - Visiones (Rojo) son grandes si la probabilidad es alta
            # - Ciudadanos (Azul)
            # - Lugares (Amarillo)
            val = 1 # Tamaño por defecto
            if node['group'] == 'red': # Vision
                val = 10 * node.get('prob', 0.5)
            
            nodes.append({
                "id": node['id'],
                "group": node['group'],
                "label": node.get('label') or node.get('name'),
                "val": val, # Tamaño del nodo en la UI
                "in_analysis": node.get('in_analysis', True),
                "info": node # Metadatos extra para el tooltip
            })
            seen_nodes.add(node['id'])

        # Procesar Enlaces
        for link in raw_data['links']:
            links.append({
                "source": link['source'],
                "target": link['target'],
                "type": link['type'],
                "color": "#999" # Color por defecto
            })
            
        return {"nodes": nodes, "links": links}

# Singleton
vision_service = VisionService()
