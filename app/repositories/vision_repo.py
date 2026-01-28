from app.core.database import db_manager
from typing import List, Optional
import uuid
import os
import pandas as pd
import numpy as np
import app.core.hardware_switch as hw

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
               {id: c.id, name: c.name, status: c.status} as perpetrator,
               {id: l.id, name: l.name, type: l.type, env_risk: l.env_risk,
                latitude: l.coord.latitude, longitude: l.coord.longitude} as target
        """
        results = await db_manager.query(query, {"vid": vision_id})
        if not results:
            return None
            
        row = results[0]
        # Fix types for Pydantic
        if hasattr(row['timestamp'], 'to_native'):
            row['timestamp'] = row['timestamp'].to_native()
            
        if row['perpetrator'] and row['perpetrator'].get('status') is None:
            row['perpetrator']['status'] = "UNKNOWN"
            
        return row


    async def find_active_visions(self) -> List[dict]:
        """
        Dashboard principal: Muestra crímenes que AÚN no han ocurrido.
        """
        if hw.DEMO_MODE:
            try:
                # Load demo data
                data_path = os.path.join("app", "data", "hpc", "demo_data.parquet")
                if os.path.exists(data_path):
                    df = hw.pd.read_parquet(data_path)
                    # Filter high risk for "active visions"
                    high_risk = df[df['risk_seed'] > 0.85].head(15)
                    
                    results = []
                    for _, row in high_risk.iterrows():
                        results.append({
                            "id": f"VIS_{row['node_id']}",
                            "probability": float(row['risk_seed']),
                            "timestamp": pd.Timestamp.now().isoformat(), # Live feel
                            "status": "OPEN",
                            "perpetrator": {"id": row['node_id'], "name": f"Suspect {row['node_id'][-4:]}", "status": "WANTED"},
                            "target": {
                                "id": f"LOC_{row['node_id']}", 
                                "name": f"Sector {row['node_id'][-2:]}", 
                                "type": "PUBLIC_SQUARE",
                                "env_risk": 0.9,
                                "latitude": float(row['lat']), 
                                "longitude": float(row['lon'])
                            }
                        })
                    return results
            except Exception as e:
                print(f"Error loading demo data for active visions: {e}")
                return []

        query = """
        MATCH (c:Citizen)-[:APPEARS_IN]->(v:Vision)-[:TARGETS]->(l:Location)
        WHERE v.status = 'OPEN'
        RETURN v.id as id, v.probability as probability, 
               v.timestamp as timestamp, v.status as status,
               {id: c.id, name: c.name, status: c.status} as perpetrator,
               {id: l.id, name: l.name, type: l.type, env_risk: l.env_risk,
                latitude: l.coord.latitude, longitude: l.coord.longitude} as target
        ORDER BY v.probability DESC
        """
        results = await db_manager.query(query)
        
        # Fix types for Pydantic
        for row in results:
            if hasattr(row['timestamp'], 'to_native'):
                row['timestamp'] = row['timestamp'].to_native()
            
            if row['perpetrator'] and row['perpetrator'].get('status') is None:
                row['perpetrator']['status'] = "UNKNOWN"
                
        return results

    async def resolve_vision(self, vision_id: str, outcome: str):
        """
        La Policía interviene. Cambiamos el estado de la visión.
        outcome: 'INTERVENED' o 'FALSE_ALARM'
        """
        if hw.DEMO_MODE:
            return # Mock action
            
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
        if hw.DEMO_MODE:
            return [] # Search not implemented in demo yet

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
        Combina la RED SOCIAL (Citizens) con las VISIONES (Predictions).
        """
        if hw.DEMO_MODE:
            try:
                data_path = os.path.join("app", "data", "hpc", "demo_data.parquet")
                if os.path.exists(data_path):
                    df = hw.pd.read_parquet(data_path).head(limit)
                    nodes = []
                    links = []
                    
                    # Create sector hubs (distributed centers instead of single Precog_Center)
                    sectors = ["Sector_Centro", "Sector_Norte", "Sector_Sur", "Sector_Este", "Sector_Oeste"]
                    for i, sector in enumerate(sectors):
                        nodes.append({
                            "id": sector, 
                            "group": "purple", 
                            "label": sector.replace("_", " "), 
                            "val": 15
                        })
                    
                    # Connect sectors to each other (hub network)
                    for i in range(len(sectors)):
                        for j in range(i + 1, len(sectors)):
                            if np.random.random() > 0.3:  # 70% chance of connection
                                links.append({"source": sectors[i], "target": sectors[j], "type": "CONNECTED"})
                    
                    # Assign each node to a sector based on its index
                    for idx, (_, row) in enumerate(df.iterrows()):
                        nid = row['node_id']
                        risk = row['risk_seed']
                        
                        # Node Grouping based on Risk
                        group = "blue"  # Citizen
                        if risk > 0.85: 
                            group = "red"  # Threat
                        elif risk > 0.6: 
                            group = "yellow"  # Suspicious
                        
                        nodes.append({
                            "id": nid,
                            "label": f"Entity {nid[-4:]}",
                            "group": group,
                            "prob": risk,
                            "in_analysis": True if risk > 0.5 else False,
                            "val": 5 + (risk * 10)
                        })
                        
                        # Link to assigned sector (distribute nodes across sectors)
                        assigned_sector = sectors[idx % len(sectors)]
                        if risk > 0.5:
                            links.append({"source": nid, "target": assigned_sector, "type": "MONITORED"})
                        
                        # Create MANY more peer links for dense network
                        num_peers = int(np.random.randint(2, 6))  # 2-5 peer connections per node
                        peer_indices = np.random.choice(len(df), size=min(num_peers, len(df)), replace=False)
                        for peer_idx in peer_indices:
                            target_peer = df.iloc[peer_idx]['node_id']
                            if target_peer != nid:
                                links.append({"source": nid, "target": target_peer, "type": "KNOWS"})
                    
                    return {"nodes": nodes, "links": links}
            except Exception as e:
                print(f"Error generating demo graph: {e}")
                return {"nodes": [], "links": []}

        nodes = {}
        links = []

        # 1. Fetch Visions (The "Red Balls")
        vision_query = """
        MATCH (v:Vision)-[:APPEARS_IN]-(c:Citizen)
        MATCH (v)-[:TARGETS]-(l:Location)
        RETURN v, c, l
        LIMIT $limit
        """
        vision_results = await db_manager.query(vision_query, {"limit": limit})
        
        for row in vision_results:
            v, c, l = row['v'], row['c'], row['l']
            
            nodes[v['id']] = {"id": v['id'], "label": "Vision", "group": "red", "prob": v.get('probability', 0), "in_analysis": True}
            nodes[c['id']] = {"id": c['id'], "label": "Citizen", "group": "blue", "name": c.get('name', 'Unknown'), "in_analysis": True}
            nodes[l['id']] = {"id": l['id'], "label": "Location", "group": "yellow", "name": l.get('name', 'Unknown'), "in_analysis": True}
            
            links.append({"source": c['id'], "target": v['id'], "type": "APPEARS_IN"})
            links.append({"source": v['id'], "target": l['id'], "type": "TARGETS"})

        # 2. Fetch Social Background (The "City Web") - To populate graph when no visions exist
        # We increase the limit to ensure background nodes are present for context
        social_limit = 300 
        social_query = """
        MATCH (c1:Citizen)-[:KNOWS]->(c2:Citizen)
        RETURN c1, c2
        LIMIT $limit
        """
        social_results = await db_manager.query(social_query, {"limit": social_limit})
            
        for row in social_results:
            c1, c2 = row['c1'], row['c2']
            
            # Add nodes if they don't exist yet
            if c1['id'] not in nodes:
                nodes[c1['id']] = {"id": c1['id'], "label": "Citizen", "group": "blue", "name": c1.get('name', 'Unknown'), "in_analysis": False}
            if c2['id'] not in nodes:
                nodes[c2['id']] = {"id": c2['id'], "label": "Citizen", "group": "blue", "name": c2.get('name', 'Unknown'), "in_analysis": False}
            
            links.append({"source": c1['id'], "target": c2['id'], "type": "KNOWS"})

        return {
            "nodes": list(nodes.values()),
            "links": links
        }

vision_repo = VisionRepository()

