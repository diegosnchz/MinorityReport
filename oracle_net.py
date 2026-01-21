"""
OracleNet: The Oracle - AI Model for Robber's Escape Route Optimization

Este módulo implementa el modelo de IA para el lado de los ladrones en 
"Minority Report - Robbers Side". El objetivo es calcular rutas de escape 
óptimas evitando la vigilancia policial predictiva.

Arquitectura:
- GCN (Graph Convolutional Network): Comprende el nivel de peligro del vecindario
- GAT (Graph Attention Network): Pondera aristas basándose en seguridad de ruta

Author: The Oracle
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch_geometric.nn import GCNConv, GATConv
from typing import Tuple, Optional
import numpy as np


class OracleNet(nn.Module):
    """
    OracleNet: Modelo híbrido GCN + GAT para optimización de rutas de escape.
    
    El modelo procesa un grafo de ciudad donde:
    - Nodos: Ubicaciones/intersecciones con features [nivel_policial, tipo_nodo, ...]
    - Aristas: Calles/conexiones con pesos de peligro
    
    Output: Probabilidad de seguridad para cada arista (0=peligroso, 1=seguro)
    
    Args:
        in_channels (int): Número de features de entrada por nodo
        hidden_channels (int): Dimensión de la representación oculta
        out_channels (int): Dimensión de la salida por nodo
        num_heads (int): Número de cabezas de atención para GAT
        dropout (float): Tasa de dropout para regularización
    """
    
    def __init__(
        self, 
        in_channels: int = 16,
        hidden_channels: int = 64,
        out_channels: int = 32,
        num_heads: int = 4,
        dropout: float = 0.3
    ):
        super(OracleNet, self).__init__()
        
        self.in_channels = in_channels
        self.hidden_channels = hidden_channels
        self.out_channels = out_channels
        self.num_heads = num_heads
        self.dropout = dropout
        
        # =================================================================
        # CAPA 1: GCN - Comprensión del Contexto del Vecindario
        # =================================================================
        # La GCN agrega información de los vecinos para que cada nodo
        # entienda el nivel de peligro en su área local.
        # Transformación: h^(l+1) = σ(D^(-1/2) A D^(-1/2) h^(l) W^(l))
        
        self.gcn1 = GCNConv(in_channels, hidden_channels)
        self.gcn2 = GCNConv(hidden_channels, hidden_channels)
        
        # Batch Normalization para estabilidad de entrenamiento
        self.bn1 = nn.BatchNorm1d(hidden_channels)
        self.bn2 = nn.BatchNorm1d(hidden_channels)
        
        # =================================================================
        # CAPA 2: GAT - Mecanismo de Atención para Ponderación de Rutas
        # =================================================================
        # GAT usa atención para ponderar la importancia de cada vecino.
        # Esto permite identificar qué calles/conexiones son más seguras.
        #
        # Mecanismo de Atención (α):
        # 1. e_ij = LeakyReLU(a^T [W h_i || W h_j])  -- Score de atención
        # 2. α_ij = softmax_j(e_ij)                   -- Normalización
        # 3. h'_i = σ(Σ_j α_ij W h_j)                -- Agregación ponderada
        #
        # Donde:
        # - h_i, h_j: Features de nodo i y vecino j
        # - W: Matriz de transformación lineal
        # - a: Vector de parámetros de atención
        # - ||: Concatenación
        # - α_ij: Coeficiente de atención (importancia de j para i)
        #
        # En nuestro contexto:
        # - α_ij alto: La calle de i a j es SEGURA (bajo riesgo policial)
        # - α_ij bajo: La calle de i a j es PELIGROSA (alto riesgo)
        
        self.gat1 = GATConv(
            hidden_channels, 
            hidden_channels // num_heads,
            heads=num_heads,
            dropout=dropout,
            concat=True  # Concatenar las salidas de múltiples cabezas
        )
        
        # Segunda capa GAT con una sola cabeza para consolidación
        self.gat2 = GATConv(
            hidden_channels,
            out_channels,
            heads=1,
            dropout=dropout,
            concat=False
        )
        
        # Batch Normalization para capas GAT
        self.bn3 = nn.BatchNorm1d(hidden_channels)
        self.bn4 = nn.BatchNorm1d(out_channels)
        
        # =================================================================
        # CAPA 3: Edge Scoring - Cálculo de Seguridad de Aristas
        # =================================================================
        # Esta capa toma los embeddings de nodos y calcula un score
        # de seguridad para cada arista (calle).
        # Score alto = Ruta segura, Score bajo = Ruta peligrosa
        
        self.edge_scorer = nn.Sequential(
            nn.Linear(out_channels * 2, hidden_channels),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_channels, 32),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(32, 1),
            nn.Sigmoid()  # Output entre 0 y 1 (probabilidad de seguridad)
        )
    
    def forward(
        self, 
        x: torch.Tensor, 
        edge_index: torch.Tensor,
        return_attention: bool = False
    ) -> Tuple[torch.Tensor, Optional[torch.Tensor]]:
        """
        Forward pass del modelo.
        
        Args:
            x (torch.Tensor): Features de nodos [num_nodes, in_channels]
                - Columna 0: Nivel de presencia policial (0-1)
                - Columna 1: Tipo de nodo (0=calle, 1=callejón, 2=edificio, etc.)
                - Columnas 2+: Otras features (densidad, iluminación, etc.)
            edge_index (torch.Tensor): Índices de aristas [2, num_edges]
            return_attention (bool): Si True, retorna también los pesos de atención
        
        Returns:
            edge_safety_scores (torch.Tensor): Probabilidad de seguridad por arista [num_edges, 1]
            attention_weights (torch.Tensor, optional): Pesos de atención de GAT
        """
        
        # =================================================================
        # FASE 1: GCN - Agregación de Contexto Local
        # =================================================================
        # Cada nodo agrega información de sus vecinos para entender
        # el nivel de peligro en su vecindario
        
        # Primera capa GCN
        x = self.gcn1(x, edge_index)
        x = self.bn1(x)
        x = F.relu(x)
        x = F.dropout(x, p=self.dropout, training=self.training)
        
        # Segunda capa GCN
        x = self.gcn2(x, edge_index)
        x = self.bn2(x)
        x = F.relu(x)
        x = F.dropout(x, p=self.dropout, training=self.training)
        
        # =================================================================
        # FASE 2: GAT - Atención sobre Vecinos (Ponderación de Rutas)
        # =================================================================
        # GAT aprende a dar más peso a vecinos "seguros" y menos a "peligrosos"
        
        # Primera capa GAT con múltiples cabezas
        # Cada cabeza aprende diferentes aspectos de la seguridad
        x, attention_weights_1 = self.gat1(x, edge_index, return_attention_weights=True)
        x = self.bn3(x)
        x = F.elu(x)  # ELU funciona mejor que ReLU en GAT
        x = F.dropout(x, p=self.dropout, training=self.training)
        
        # Segunda capa GAT para consolidación
        x, attention_weights_2 = self.gat2(x, edge_index, return_attention_weights=True)
        x = self.bn4(x)
        x = F.elu(x)
        
        # x ahora contiene embeddings de nodos que capturan:
        # - Contexto del vecindario (vía GCN)
        # - Importancia relativa de cada conexión (vía GAT)
        
        # =================================================================
        # FASE 3: Edge Scoring - Cálculo de Seguridad por Arista
        # =================================================================
        # Para cada arista (i, j), concatenamos los embeddings de 
        # los nodos fuente y destino, y predecimos la seguridad
        
        # Extraer índices de nodos para cada arista
        src_nodes = edge_index[0]  # Nodos fuente
        dst_nodes = edge_index[1]  # Nodos destino
        
        # Obtener embeddings de nodos fuente y destino
        src_embeddings = x[src_nodes]  # [num_edges, out_channels]
        dst_embeddings = x[dst_nodes]  # [num_edges, out_channels]
        
        # Concatenar embeddings de ambos extremos de cada arista
        edge_features = torch.cat([src_embeddings, dst_embeddings], dim=1)
        # [num_edges, out_channels * 2]
        
        # Calcular score de seguridad para cada arista
        edge_safety_scores = self.edge_scorer(edge_features)
        # [num_edges, 1] donde cada valor está en [0, 1]
        # 0 = Ruta muy peligrosa (alta presencia policial)
        # 1 = Ruta muy segura (baja presencia policial, buena cobertura)
        
        if return_attention:
            # Retornar también los pesos de atención para análisis
            return edge_safety_scores, attention_weights_2
        
        return edge_safety_scores, None
    
    def get_safe_route(
        self,
        x: torch.Tensor,
        edge_index: torch.Tensor,
        start_node: int,
        end_node: int,
        top_k: int = 5
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Calcula las K rutas más seguras desde start_node hasta end_node.
        
        Args:
            x: Features de nodos
            edge_index: Índices de aristas
            start_node: Nodo de inicio
            end_node: Nodo de destino
            top_k: Número de rutas alternativas a retornar
        
        Returns:
            routes: Las K mejores rutas [k, max_route_length]
            safety_scores: Score de seguridad de cada ruta [k]
        
        Raises:
            NotImplementedError: Este método aún no está implementado
        """
        # TODO: Implementar algoritmo de pathfinding (e.g., A* modificado)
        # que use edge_safety_scores como pesos inversos
        # Ver neo4j_oracle_integration.py para un ejemplo de implementación
        # usando NetworkX
        raise NotImplementedError(
            "Pathfinding algorithm not yet implemented. "
            "See neo4j_oracle_integration.py for an example using NetworkX."
        )


def create_oracle_net(
    num_features: int = 16,
    device: Optional[str] = None
) -> OracleNet:
    """
    Factory function para crear una instancia de OracleNet configurada.
    
    Args:
        num_features: Número de features de entrada por nodo
        device: Dispositivo para el modelo ('cuda' o 'cpu')
    
    Returns:
        modelo OracleNet configurado
    """
    if device is None:
        device = 'cuda' if torch.cuda.is_available() else 'cpu'
    
    model = OracleNet(
        in_channels=num_features,
        hidden_channels=64,
        out_channels=32,
        num_heads=4,
        dropout=0.3
    )
    
    return model.to(device)


if __name__ == "__main__":
    """
    Smoke test para verificar que el modelo funciona correctamente.
    """
    print("=" * 70)
    print("OracleNet - The Oracle: Robber's Escape Route Optimizer")
    print("=" * 70)
    
    # Configuración del dispositivo
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    print(f"\n🖥️  Device: {device}")
    
    if device.type == 'cuda':
        print(f"   GPU: {torch.cuda.get_device_name(0)}")
        print(f"   Memory: {torch.cuda.get_device_properties(0).total_memory / 1e9:.2f} GB")
    
    # Crear un grafo de prueba simulando una ciudad pequeña
    num_nodes = 50  # 50 intersecciones
    num_edges = 150  # 150 calles
    num_features = 16  # Features por nodo
    
    print(f"\n📊 Graph Stats:")
    print(f"   Nodes (intersections): {num_nodes}")
    print(f"   Edges (streets): {num_edges}")
    print(f"   Features per node: {num_features}")
    
    # Generar features de nodos aleatorios
    # Feature 0: Nivel policial (0-1)
    # Feature 1: Tipo de nodo (normalizado)
    # Features 2+: Otras características (iluminación, densidad, etc.)
    x = torch.randn((num_nodes, num_features), device=device)
    x[:, 0] = torch.rand(num_nodes, device=device)  # Nivel policial
    x[:, 1] = torch.randint(0, 4, (num_nodes,), device=device).float() / 3.0  # Tipo normalizado
    
    # Generar aristas aleatorias (grafo conectado)
    edge_index = torch.randint(0, num_nodes, (2, num_edges), device=device)
    
    # Crear modelo
    print("\n🏗️  Building OracleNet...")
    model = create_oracle_net(num_features=num_features, device=device)
    
    # Contar parámetros
    total_params = sum(p.numel() for p in model.parameters())
    trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
    print(f"   Total parameters: {total_params:,}")
    print(f"   Trainable parameters: {trainable_params:,}")
    
    # Forward pass
    print("\n🔄 Running forward pass...")
    model.eval()
    with torch.no_grad():
        edge_safety_scores, attention_weights = model(x, edge_index, return_attention=True)
    
    print(f"   Input shape: {x.shape}")
    print(f"   Edge index shape: {edge_index.shape}")
    print(f"   Output (safety scores) shape: {edge_safety_scores.shape}")
    print(f"   Attention weights shape: {attention_weights[1].shape}")
    
    # Análisis de resultados
    print("\n📈 Safety Analysis:")
    safety_scores = edge_safety_scores.squeeze().cpu().numpy()
    print(f"   Mean safety: {np.mean(safety_scores):.4f}")
    print(f"   Std safety: {np.std(safety_scores):.4f}")
    print(f"   Min safety (most dangerous): {np.min(safety_scores):.4f}")
    print(f"   Max safety (safest route): {np.max(safety_scores):.4f}")
    
    # Identificar las 5 rutas más seguras y más peligrosas
    top_safe_indices = np.argsort(safety_scores)[-5:][::-1]
    top_dangerous_indices = np.argsort(safety_scores)[:5]
    
    print("\n✅ Top 5 SAFEST routes:")
    for i, idx in enumerate(top_safe_indices, 1):
        src, dst = edge_index[0, idx].item(), edge_index[1, idx].item()
        score = safety_scores[idx]
        print(f"   {i}. Route {src} → {dst}: Safety = {score:.4f}")
    
    print("\n⚠️  Top 5 MOST DANGEROUS routes:")
    for i, idx in enumerate(top_dangerous_indices, 1):
        src, dst = edge_index[0, idx].item(), edge_index[1, idx].item()
        score = safety_scores[idx]
        print(f"   {i}. Route {src} → {dst}: Safety = {score:.4f}")
    
    print("\n" + "=" * 70)
    print("✨ OracleNet initialized successfully!")
    print("=" * 70)
