"""
Ejemplo de integración de OracleNet con Neo4j
Este script demuestra cómo usar OracleNet con datos reales de Neo4j

Requiere:
- Neo4j running en localhost:7687
- Base de datos con nodos Person/Location y relaciones INTERACTS_WITH/CONNECTED_TO
"""

from neo4j import GraphDatabase
import torch
import numpy as np
from src.models.oracle_net import create_oracle_net
from typing import Dict, List, Tuple
import networkx as nx


class Neo4jOracleIntegration:
    """
    Integración entre Neo4j y OracleNet para calcular rutas de escape.
    """
    
    def __init__(self, uri: str = "bolt://localhost:7687", user: str = "neo4j", password: str = "password"):
        """
        Inicializa la conexión con Neo4j.
        
        Args:
            uri: URI de conexión a Neo4j
            user: Usuario de Neo4j
            password: Contraseña de Neo4j
        """
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.model = None
        
    def close(self):
        """Cierra la conexión con Neo4j."""
        self.driver.close()
    
    def fetch_city_graph(self, session) -> Tuple[Dict, List]:
        """
        Extrae el grafo de la ciudad desde Neo4j.
        
        Returns:
            nodes: Diccionario {node_id: features}
            edges: Lista de tuplas (source, target, properties)
        """
        # Query para obtener nodos con sus propiedades
        nodes_query = """
        MATCH (n:Location)
        RETURN 
            id(n) as node_id,
            n.policeLevel as police_level,
            n.locationType as location_type,
            n.illumination as illumination,
            n.density as density,
            n.latitude as lat,
            n.longitude as lon
        """
        
        # Query para obtener aristas (calles)
        edges_query = """
        MATCH (a:Location)-[r:CONNECTED_TO]->(b:Location)
        RETURN 
            id(a) as source,
            id(b) as target,
            r.distance as distance,
            r.surveillanceLevel as surveillance
        """
        
        # Ejecutar queries
        nodes_result = session.run(nodes_query)
        edges_result = session.run(edges_query)
        
        # Procesar nodos
        nodes = {}
        for record in nodes_result:
            node_id = record["node_id"]
            nodes[node_id] = {
                'police_level': record.get("police_level", 0.5),
                'location_type': record.get("location_type", 0),
                'illumination': record.get("illumination", 0.5),
                'density': record.get("density", 0.5),
                'lat': record.get("lat", 0.0),
                'lon': record.get("lon", 0.0)
            }
        
        # Procesar aristas
        edges = []
        for record in edges_result:
            edges.append((
                record["source"],
                record["target"],
                {
                    'distance': record.get("distance", 1.0),
                    'surveillance': record.get("surveillance", 0.5)
                }
            ))
        
        return nodes, edges
    
    def prepare_graph_data(self, nodes: Dict, edges: List) -> Tuple[torch.Tensor, torch.Tensor, Dict]:
        """
        Convierte datos de Neo4j al formato requerido por PyTorch Geometric.
        
        Args:
            nodes: Diccionario de nodos con features
            edges: Lista de aristas
        
        Returns:
            x: Tensor de features de nodos [num_nodes, num_features]
            edge_index: Tensor de índices de aristas [2, num_edges]
            node_mapping: Mapeo de node_id de Neo4j a índice del tensor
        """
        # Crear mapeo de IDs de Neo4j a índices consecutivos
        node_ids = sorted(nodes.keys())
        node_mapping = {neo4j_id: idx for idx, neo4j_id in enumerate(node_ids)}
        
        num_nodes = len(node_ids)
        num_features = 16  # Features de OracleNet
        
        # Crear tensor de features
        x = torch.zeros((num_nodes, num_features))
        
        for neo4j_id, idx in node_mapping.items():
            node_data = nodes[neo4j_id]
            
            # Feature 0: Nivel policial
            x[idx, 0] = node_data['police_level']
            
            # Feature 1: Tipo de ubicación (normalizado)
            x[idx, 1] = node_data['location_type'] / 3.0
            
            # Feature 2: Iluminación
            x[idx, 2] = node_data['illumination']
            
            # Feature 3: Densidad
            x[idx, 3] = node_data['density']
            
            # Features 4-5: Coordenadas geográficas (normalizadas)
            x[idx, 4] = node_data['lat']
            x[idx, 5] = node_data['lon']
            
            # Features 6-15: Rellenadas con características derivadas o ceros
            # Estas podrían ser: hora del día, día de la semana, eventos especiales, etc.
            x[idx, 6:] = torch.randn(10) * 0.1  # Placeholder
        
        # Crear tensor de aristas
        edge_list = []
        for source_id, target_id, props in edges:
            if source_id in node_mapping and target_id in node_mapping:
                src_idx = node_mapping[source_id]
                dst_idx = node_mapping[target_id]
                edge_list.append([src_idx, dst_idx])
        
        edge_index = torch.tensor(edge_list, dtype=torch.long).t().contiguous()
        
        return x, edge_index, node_mapping
    
    def calculate_escape_routes(
        self, 
        start_location: str,
        end_location: str,
        top_k: int = 5
    ) -> List[Tuple[List[int], float]]:
        """
        Calcula las mejores rutas de escape desde start hasta end.
        
        Args:
            start_location: Nombre o ID de la ubicación de inicio
            end_location: Nombre o ID de la ubicación de destino
            top_k: Número de rutas alternativas
        
        Returns:
            Lista de tuplas (ruta, safety_score)
        """
        with self.driver.session() as session:
            # 1. Extraer grafo de Neo4j
            print("📡 Fetching city graph from Neo4j...")
            nodes, edges = self.fetch_city_graph(session)
            print(f"   Found {len(nodes)} locations and {len(edges)} streets")
            
            # 2. Preparar datos para PyTorch
            print("🔧 Converting to PyTorch format...")
            x, edge_index, node_mapping = self.prepare_graph_data(nodes, edges)
            x = x.to(self.device)
            edge_index = edge_index.to(self.device)
            
            # 3. Crear y cargar modelo
            if self.model is None:
                print("🏗️  Loading OracleNet...")
                self.model = create_oracle_net(num_features=16, device=self.device)
                
                # Intentar cargar modelo entrenado
                try:
                    checkpoint = torch.load('oracle_net_best.pth', map_location=self.device)
                    self.model.load_state_dict(checkpoint['model_state_dict'])
                    print(f"   ✅ Loaded trained model (Val Loss: {checkpoint['val_loss']:.4f})")
                except FileNotFoundError:
                    print("   ⚠️  Using untrained model")
            
            # 4. Calcular scores de seguridad
            print("🔮 Computing safety scores...")
            self.model.eval()
            with torch.no_grad():
                edge_safety_scores, attention_weights = self.model(
                    x, edge_index, return_attention=True
                )
            
            # 5. Construir grafo de NetworkX con pesos de seguridad
            G = nx.DiGraph()
            
            for i in range(edge_index.shape[1]):
                src = edge_index[0, i].item()
                dst = edge_index[1, i].item()
                safety = edge_safety_scores[i].item()
                
                # Peso para pathfinding: menor es mejor
                # Convertimos safety (0-1) a peso (1/safety para que rutas seguras tengan menor peso)
                weight = 1.0 / (safety + 0.01)  # +0.01 para evitar división por cero
                
                G.add_edge(src, dst, weight=weight, safety=safety)
            
            # 6. Encontrar ubicaciones de inicio y fin
            # TODO: Implementar búsqueda por nombre de ubicación en Neo4j
            # Query ejemplo:
            # MATCH (n:Location {name: $location_name}) RETURN id(n)
            
            # Por ahora, convertimos start_location y end_location a enteros
            # si son IDs, o usamos nodos aleatorios como fallback
            try:
                start_node_id = int(start_location)
                start_node = node_mapping.get(start_node_id, 0)
            except (ValueError, KeyError):
                start_node = 0  # Fallback a primer nodo
                print(f"   ⚠️  Could not find start location '{start_location}', using node 0")
            
            try:
                end_node_id = int(end_location)
                end_node = node_mapping.get(end_node_id, len(nodes) - 1)
            except (ValueError, KeyError):
                end_node = len(nodes) - 1  # Fallback a último nodo
                print(f"   ⚠️  Could not find end location '{end_location}', using node {end_node}")
            
            print(f"🎯 Finding routes from node {start_node} to {end_node}...")
            
            # 7. Calcular las K mejores rutas usando A*
            routes = []
            
            try:
                # Ruta más corta (óptima por seguridad)
                path = nx.shortest_path(G, start_node, end_node, weight='weight')
                
                # Calcular score de seguridad promedio de la ruta
                total_safety = 0
                for i in range(len(path) - 1):
                    edge_data = G[path[i]][path[i+1]]
                    total_safety += edge_data['safety']
                avg_safety = total_safety / (len(path) - 1) if len(path) > 1 else 0
                
                routes.append((path, avg_safety))
                
                print(f"   ✅ Found optimal route with {len(path)} hops")
                print(f"   🛡️  Average safety score: {avg_safety:.4f}")
                
            except nx.NetworkXNoPath:
                print("   ⚠️  No path found between start and end locations")
            
            return routes
    
    def write_safety_scores_to_neo4j(
        self,
        edge_safety_scores: torch.Tensor,
        edge_index: torch.Tensor,
        node_mapping: Dict
    ):
        """
        Escribe los scores de seguridad de vuelta a Neo4j.
        
        Args:
            edge_safety_scores: Scores de seguridad calculados
            edge_index: Índices de aristas
            node_mapping: Mapeo de índices a IDs de Neo4j
        """
        # Invertir el mapeo
        idx_to_neo4j = {idx: neo4j_id for neo4j_id, idx in node_mapping.items()}
        
        with self.driver.session() as session:
            for i in range(edge_index.shape[1]):
                src_idx = edge_index[0, i].item()
                dst_idx = edge_index[1, i].item()
                safety = edge_safety_scores[i].item()
                
                src_neo4j = idx_to_neo4j[src_idx]
                dst_neo4j = idx_to_neo4j[dst_idx]
                
                # Actualizar la arista en Neo4j
                query = """
                MATCH (a:Location)-[r:CONNECTED_TO]->(b:Location)
                WHERE id(a) = $src_id AND id(b) = $dst_id
                SET r.oracleSafetyScore = $safety,
                    r.lastAnalyzed = datetime()
                """
                
                session.run(query, src_id=src_neo4j, dst_id=dst_neo4j, safety=safety)
            
            print(f"✅ Updated {edge_index.shape[1]} edges with safety scores in Neo4j")


def example_usage():
    """
    Ejemplo de uso de la integración Neo4j-OracleNet.
    """
    print("=" * 70)
    print("🔮 Neo4j + OracleNet Integration Example")
    print("=" * 70)
    
    # Nota: Este ejemplo requiere Neo4j corriendo localmente
    print("\n⚠️  Note: This example requires Neo4j running at bolt://localhost:7687")
    print("   If Neo4j is not available, this is just a demonstration.")
    print()
    
    try:
        # Crear integración
        integration = Neo4jOracleIntegration(
            uri="bolt://localhost:7687",
            user="neo4j",
            password="password"
        )
        
        # Calcular rutas de escape
        routes = integration.calculate_escape_routes(
            start_location="LocationA",
            end_location="LocationB",
            top_k=5
        )
        
        # Mostrar resultados
        print("\n🛡️  ESCAPE ROUTES:")
        for i, (path, safety) in enumerate(routes, 1):
            print(f"\nRoute {i}:")
            print(f"  Path: {' → '.join(map(str, path))}")
            print(f"  Safety Score: {safety:.4f}")
        
        integration.close()
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nThis is expected if Neo4j is not running.")
        print("The OracleNet model itself works independently of Neo4j.")


if __name__ == "__main__":
    example_usage()
