from app.core.database import db_manager
from typing import List, Optional
import uuid

class VisionRepository:
    async def create_vision(self, data: dict) -> dict:
        """
        El núcleo del sistema.
        Crea el nodo (:Vision) y lo conecta con (:Citizen) y (:Location).
        """
        vision_id = f"VIS_{uuid.uuid4().hex[:8]}"
        query = """
        MATCH (c:Citizen {id: $cid})
        MATCH (l:Location {id: $lid})
        // Crear el Nodo Visión
        CREATE (v:Vision {
            id: $vid,
            probability: $prob,
            timestamp: datetime($date),
            model: $model,
            status: 'OPEN'
        })
        // Crear las relaciones (El pegamento)
        MERGE (c)-[:APPEARS_IN]->(v)
        MERGE (v)-[:TARGETS]->(l)
        RETURN v.id as id
        """
        
        # Ensure data is dict or object access
        # The service passes pydantic model, so we might need access via attributes or dict
        # Assuming input 'data' is Pydantic model here based on usage in router
        params = {
            "cid": data.citizen_id,
            "lid": data.location_id,
            "vid": vision_id,
            "prob": data.probability,
            "date": data.predicted_date.isoformat(),
            "model": data.ai_model_version
        }
        await db_manager.query(query, params)
        
        # Devolvemos la visión completa recuperándola
        return await self.find_by_id(vision_id)

    async def find_by_id(self, vision_id: str) -> Optional[dict]:
        """Helper to fetch full vision details."""
        query = """
        MATCH (c:Citizen)-[:APPEARS_IN]->(v:Vision {id: $vid})-[:TARGETS]->(l:Location)
        RETURN v.id as id, v.probability as probability, 
               v.timestamp as timestamp, v.status as status,
               {name: c.name, status: c.status} as perpetrator,
               {name: l.name, type: l.type, env_risk: l.env_risk} as target
        """
        results = await db_manager.query(query, {"vid": vision_id})
        return results[0] if results else None

    async def find_active_visions(self) -> List[dict]:
        """
        Dashboard principal: Muestra crímenes que AÚN no han ocurrido.
        """
        query = """
        MATCH (c:Citizen)-[:APPEARS_IN]->(v:Vision)-[:TARGETS]->(l:Location)
        WHERE v.status = 'OPEN'
        RETURN v.id as id, v.probability as probability, 
               v.timestamp as timestamp, v.status as status,
               {name: c.name, status: c.status} as perpetrator,
               {name: l.name, type: l.type, env_risk: l.env_risk} as target
        ORDER BY v.probability DESC
        """
        return await db_manager.query(query)

    async def resolve_vision(self, vision_id: str, outcome: str):
        """
        La Policía interviene. Cambiamos el estado de la visión.
        outcome: 'INTERVENED' o 'FALSE_ALARM'
        """
        query = """
        MATCH (v:Vision {id: $vid})
        SET v.status = $outcome, v.resolved_at = datetime()
        RETURN v.id
        """
        await db_manager.query(query, {"vid": vision_id, "outcome": outcome})

    async def search_by_text(self, text: str) -> List[dict]:
        """
        Busca visiones donde el nombre del ciudadano o del lugar coincida con el texto.
        """
        query = """
        MATCH (v:Vision)<-[:APPEARS_IN]-(c:Citizen)
        MATCH (v)-[:TARGETS]->(l:Location)
        WHERE toLower(c.name) CONTAINS toLower($text) 
           OR toLower(l.name) CONTAINS toLower($text)
        RETURN v.id as id, v.probability as probability, 
               v.timestamp as timestamp, v.status as status,
               {name: c.name, status: c.status} as perpetrator,
               {name: l.name, type: l.type, env_risk: l.env_risk} as target
        LIMIT 20
        """
        return await db_manager.query(query, {"text": text})

    async def get_graph_visualization(self, limit: int = 50) -> dict:
        """
        Devuelve datos formateados para librerías de visualización (D3.js / Cytoscape).
        Estructura: {nodes: [], links: []}
        """
        query = """
        MATCH (v:Vision)-[:APPEARS_IN]-(c:Citizen)
        MATCH (v)-[:TARGETS]-(l:Location)
        RETURN v, c, l
        LIMIT $limit
        """
        results = await db_manager.query(query, {"limit": limit})
        
        nodes = {}
        links = []
        
        for row in results:
            # Extraer nodos (evitando duplicados usando diccionarios)
            v, c, l = row['v'], row['c'], row['l']
            
            nodes[v['id']] = {"id": v['id'], "label": "Vision", "group": "red", "prob": v.get('probability', 0)}
            nodes[c['id']] = {"id": c['id'], "label": "Citizen", "group": "blue", "name": c.get('name', 'Unknown')}
            nodes[l['id']] = {"id": l['id'], "label": "Location", "group": "yellow", "name": l.get('name', 'Unknown')}
            
            # Crear enlaces (Aristas)
            links.append({"source": c['id'], "target": v['id'], "type": "APPEARS_IN"})
            links.append({"source": v['id'], "target": l['id'], "type": "TARGETS"})
            
        return {
            "nodes": list(nodes.values()),
            "links": links
        }

vision_repo = VisionRepository()
