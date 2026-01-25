import torch
from torch_geometric.explain import Explainer, GNNExplainer
from app.core.ai_engine import precog_system # Instancia de tu modelo cargado

class XAIService:
    def __init__(self):
        # Configuramos el auditor GNNExplainer
        # En producción, esto debería inicializarse solo si el modelo está cargado.
        # Aquí asumimos que precog_system.model es accesible o lo pasamos dinámicamente.
        # Nota: GNNExplainer requiere que el modelo esté en eval().
        pass 

    def _get_explainer(self, model):
        """Lazy loader del explainer para asegurar que el modelo existe"""
        return Explainer(
            model=model,
            algorithm=GNNExplainer(epochs=200),
            explanation_type='model',
            node_mask_type='attributes',
            edge_mask_type='object',
            model_config=dict(
                mode='binary_classification',
                task_level='edge', 
                return_type='probs',
            ),
        )

    async def explain_vision(self, citizen_id, location_id, context_graph):
        """
        Genera una explicación para una predicción específica.
        Args:
            citizen_id: ID del ciudadano (source)
            location_id: ID del lugar (target), aunque para GAT pasamos edges completos
            context_graph: Objeto Data (PyG) con el subgrafo local
        """
        # Verificación de seguridad
        if not precog_system.model:
            return {"error": "Precog System not loaded"}

        explainer = self._get_explainer(precog_system.model)

        # Extraemos tensores del subgrafo local
        x, edge_index = context_graph.x, context_graph.edge_index
        
        # Ejecutamos la explicación sobre el enlace (citizen -> location)
        # GNNExplainer necesita saber qué queremos explicar. 
        # En clasificación de nodos, pasamos el node_idx. 
        # En predicción de enlaces, pasamos los índices de la arista objetivo.
        
        # Nota simplificada: Para este prototipo, simularemos que explicamos la clasificación global del subgrafo
        # o asumiremos que el modelo clasifica el riesgo del nodo central (citizen).
        
        try:
            explanation = explainer(
                x,
                edge_index,
                index=torch.tensor([0]), # Asumimos que el ciudadano es el nodo 0 del subgrafo
                target=torch.tensor([1.0]) # Queremos explicar por qué predijo CLASE 1 (Crimen)
            )

            # Analizamos la máscara de aristas (Edge Mask)
            # Valores altos significan que esa conexión fue CRÍTICA para la decisión
            important_edges = explanation.edge_mask > 0.7

            return self._format_explanation(explanation, context_graph)
        except Exception as e:
            # Fallback en caso de error en explicador (común si el grafo es muy pequeño)
            print(f"XAI Error: {e}")
            return [{"reason": "AI Complexity too high for simple explanation", "importance": 1.0}]

    def _format_explanation(self, explanation, data):
        # Lógica para convertir tensores a JSON legible para el humano
        critical_connections = []
        # Use .tolist() to avoid Numpy dependency issues in some docker envs
        mask = explanation.edge_mask.cpu().detach().tolist()
        edges = data.edge_index.cpu().detach().tolist() # Returns list of lists [[srcs], [dsts]]
        
        # edges[0] are sources, edges[1] are targets
        src_nodes = edges[0]
        dst_nodes = edges[1]
        
        for i, importance in enumerate(mask):
            if importance > 0.6: # Umbral de relevancia
                src = src_nodes[i]
                dst = dst_nodes[i]
                critical_connections.append({
                    "source": int(src),
                    "target": int(dst),
                    "importance": float(importance),
                    "reason": "High influence on risk score"
                })
        
        return critical_connections

xai_service = XAIService()
