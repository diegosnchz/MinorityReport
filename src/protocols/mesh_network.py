"""
Mesh Networking Implementation for Minority Report
Protocolo alternativo al Gossip para sincronización distribuida de grafos

Mesh vs Gossip:
- Mesh: Cada nodo conoce toda la topología, comunicación directa optimizada
- Gossip: Cada nodo solo conoce vecinos, comunicación epidémica probabilística

Author: The Oracle
"""

import random
import time
import threading
import numpy as np
from typing import Dict, List, Set, Optional
from dataclasses import dataclass, field
from enum import Enum
import queue


class SyncStrategy(Enum):
    """Estrategias de sincronización en la red Mesh."""
    BROADCAST = "broadcast"      # Broadcast a todos los nodos
    MULTICAST = "multicast"      # Solo a nodos relevantes
    UNICAST = "unicast"          # Punto a punto optimizado


@dataclass
class GraphUpdate:
    """Representa una actualización del grafo de ciudad."""
    update_id: str
    source_node_id: int
    timestamp: float
    node_updates: Dict[int, Dict] = field(default_factory=dict)
    edge_updates: Dict[tuple, Dict] = field(default_factory=dict)
    priority: int = 0  # 0=normal, 1=high (alerta policial), 2=critical


@dataclass
class MeshNode:
    """
    Nodo en la red Mesh - Edge device con conocimiento global de topología.
    """
    node_id: int
    position: tuple  # (lat, lon) para optimización geográfica
    
    # Routing table: conoce TODOS los nodos de la red
    routing_table: Dict[int, 'MeshNode'] = field(default_factory=dict)
    
    # Local graph view (parcial)
    local_graph_view: Dict = field(default_factory=dict)
    
    # Message queue para procesamiento asíncrono
    message_queue: queue.PriorityQueue = field(default_factory=queue.PriorityQueue)
    
    # Estadísticas
    messages_sent: int = 0
    messages_received: int = 0
    bytes_transmitted: int = 0
    
    lock: threading.Lock = field(default_factory=threading.Lock)
    
    def __post_init__(self):
        """Inicialización después de crear el objeto."""
        self.local_graph_view.setdefault('version', 0)
        self.local_graph_view.setdefault('nodes', {})
        self.local_graph_view.setdefault('edges', {})
    
    def connect_to_network(self, all_nodes: List['MeshNode']):
        """
        Conecta este nodo a la red Mesh completa.
        
        En Mesh, cada nodo conoce la topología completa de la red,
        a diferencia de Gossip donde solo conoce vecinos inmediatos.
        
        Args:
            all_nodes: Lista de todos los nodos en la red
        """
        with self.lock:
            for node in all_nodes:
                if node.node_id != self.node_id:
                    self.routing_table[node.node_id] = node
            
            print(f"[Mesh Node {self.node_id}] Connected to network. "
                  f"Routing table size: {len(self.routing_table)}")
    
    def calculate_optimal_route(
        self, 
        target_id: int, 
        strategy: SyncStrategy = SyncStrategy.UNICAST
    ) -> List[int]:
        """
        Calcula la ruta óptima hacia un nodo objetivo.
        
        Mesh permite routing inteligente basado en:
        - Proximidad geográfica
        - Latencia de red
        - Carga del nodo
        
        Args:
            target_id: ID del nodo destino
            strategy: Estrategia de sincronización
        
        Returns:
            Lista de IDs de nodos en la ruta óptima
        """
        if target_id not in self.routing_table:
            return []
        
        # En esta implementación simple, comunicación directa
        # En producción, usarías algoritmos como Dijkstra o A*
        return [self.node_id, target_id]
    
    def broadcast_update(
        self, 
        update: GraphUpdate, 
        strategy: SyncStrategy = SyncStrategy.MULTICAST
    ):
        """
        Difunde una actualización a la red.
        
        Args:
            update: Actualización del grafo
            strategy: Estrategia de difusión
        """
        if strategy == SyncStrategy.BROADCAST:
            # Enviar a TODOS los nodos
            targets = list(self.routing_table.keys())
        
        elif strategy == SyncStrategy.MULTICAST:
            # Enviar solo a nodos en área geográfica relevante
            targets = self._select_relevant_nodes(update)
        
        else:  # UNICAST
            # Enviar solo al nodo más cercano al área de interés
            targets = [self._find_closest_node(update)]
        
        # Enviar mensajes
        for target_id in targets:
            if target_id in self.routing_table:
                self._send_message(target_id, update)
    
    def _select_relevant_nodes(self, update: GraphUpdate) -> List[int]:
        """
        Selecciona nodos relevantes basándose en proximidad geográfica.
        
        Multicast inteligente: solo notificar a nodos que podrían
        verse afectados por la actualización.
        """
        # Si la actualización tiene información de ubicación
        if 'location' in update.node_updates:
            update_location = update.node_updates['location']
            
            # Calcular distancia a cada nodo
            relevant = []
            for node_id, node in self.routing_table.items():
                distance = self._calculate_distance(self.position, node.position)
                # Solo notificar a nodos dentro de radio de 5 unidades
                if distance < 5.0:
                    relevant.append(node_id)
            
            return relevant if relevant else list(self.routing_table.keys())[:3]
        
        # Por defecto, seleccionar nodos aleatorios (similar a Gossip)
        num_targets = min(3, len(self.routing_table))
        return random.sample(list(self.routing_table.keys()), num_targets)
    
    def _find_closest_node(self, update: GraphUpdate) -> int:
        """Encuentra el nodo más cercano para unicast."""
        if not self.routing_table:
            return None
        
        # Seleccionar nodo con menor distancia
        closest_id = None
        min_distance = float('inf')
        
        for node_id, node in self.routing_table.items():
            distance = self._calculate_distance(self.position, node.position)
            if distance < min_distance:
                min_distance = distance
                closest_id = node_id
        
        return closest_id
    
    def _calculate_distance(self, pos1: tuple, pos2: tuple) -> float:
        """Calcula distancia euclidiana entre dos posiciones."""
        return np.sqrt((pos1[0] - pos2[0])**2 + (pos1[1] - pos2[1])**2)
    
    def _send_message(self, target_id: int, update: GraphUpdate):
        """
        Envía un mensaje a un nodo específico.
        
        En Mesh, la comunicación es directa y garantizada,
        a diferencia de Gossip que es probabilística.
        """
        target_node = self.routing_table.get(target_id)
        if target_node:
            # Simular tamaño del mensaje
            message_size = len(str(update))
            
            # Encolar mensaje en el nodo destino
            target_node.receive_message(update)
            
            # Actualizar estadísticas
            with self.lock:
                self.messages_sent += 1
                self.bytes_transmitted += message_size
    
    def receive_message(self, update: GraphUpdate):
        """
        Recibe un mensaje de otro nodo.
        
        Args:
            update: Actualización recibida
        """
        # Encolar con prioridad
        priority = -update.priority  # Negativo porque PriorityQueue es min-heap
        self.message_queue.put((priority, update.timestamp, update))
        
        with self.lock:
            self.messages_received += 1
    
    def process_message_queue(self):
        """
        Procesa mensajes en la cola (ejecutar en thread separado).
        """
        while True:
            try:
                # Obtener mensaje con mayor prioridad
                priority, timestamp, update = self.message_queue.get(timeout=0.1)
                
                # Procesar actualización
                with self.lock:
                    self._apply_update(update)
                
            except queue.Empty:
                time.sleep(0.01)
    
    def _apply_update(self, update: GraphUpdate):
        """
        Aplica una actualización al grafo local.
        
        Args:
            update: Actualización a aplicar
        """
        # Actualizar nodos
        for node_id, node_data in update.node_updates.items():
            self.local_graph_view['nodes'][node_id] = node_data
        
        # Actualizar aristas
        for edge_key, edge_data in update.edge_updates.items():
            self.local_graph_view['edges'][edge_key] = edge_data
        
        # Incrementar versión
        self.local_graph_view['version'] += 1
    
    def get_statistics(self) -> Dict:
        """Retorna estadísticas del nodo."""
        with self.lock:
            return {
                'node_id': self.node_id,
                'version': self.local_graph_view['version'],
                'messages_sent': self.messages_sent,
                'messages_received': self.messages_received,
                'bytes_transmitted': self.bytes_transmitted,
                'routing_table_size': len(self.routing_table),
                'queue_size': self.message_queue.qsize()
            }


class MeshNetwork:
    """
    Red Mesh completa para sincronización de grafos distribuidos.
    """
    
    def __init__(self, num_nodes: int = 10):
        """
        Inicializa una red Mesh con N nodos.
        
        Args:
            num_nodes: Número de nodos en la red
        """
        self.nodes: List[MeshNode] = []
        self.running = False
        
        # Crear nodos con posiciones geográficas aleatorias
        for i in range(num_nodes):
            position = (random.uniform(0, 100), random.uniform(0, 100))
            node = MeshNode(node_id=i, position=position)
            self.nodes.append(node)
        
        # Conectar todos los nodos (topología completa)
        for node in self.nodes:
            node.connect_to_network(self.nodes)
    
    def start(self):
        """Inicia la red Mesh."""
        self.running = True
        
        # Iniciar threads de procesamiento para cada nodo
        for node in self.nodes:
            thread = threading.Thread(
                target=node.process_message_queue, 
                daemon=True
            )
            thread.start()
        
        print(f"🕸️  Mesh Network started with {len(self.nodes)} nodes")
    
    def stop(self):
        """Detiene la red Mesh."""
        self.running = False
        print("🕸️  Mesh Network stopped")
    
    def simulate_city_update(self, num_updates: int = 10):
        """
        Simula actualizaciones aleatorias del grafo de ciudad.
        
        Args:
            num_updates: Número de actualizaciones a simular
        """
        for i in range(num_updates):
            # Seleccionar nodo aleatorio como origen
            source_node = random.choice(self.nodes)
            
            # Crear actualización simulada
            update = GraphUpdate(
                update_id=f"update_{i}",
                source_node_id=source_node.node_id,
                timestamp=time.time(),
                node_updates={
                    random.randint(0, 100): {
                        'police_level': random.random(),
                        'location': source_node.position
                    }
                },
                priority=random.randint(0, 2)
            )
            
            # Seleccionar estrategia aleatoria
            strategy = random.choice(list(SyncStrategy))
            
            # Difundir actualización
            source_node.broadcast_update(update, strategy)
            
            print(f"[Update {i}] Node {source_node.node_id} -> "
                  f"Strategy: {strategy.value} | "
                  f"Priority: {update.priority}")
            
            time.sleep(0.1)
    
    def get_network_statistics(self) -> Dict:
        """Retorna estadísticas agregadas de la red."""
        stats = {
            'num_nodes': len(self.nodes),
            'total_messages_sent': sum(n.messages_sent for n in self.nodes),
            'total_messages_received': sum(n.messages_received for n in self.nodes),
            'total_bytes_transmitted': sum(n.bytes_transmitted for n in self.nodes),
            'avg_version': np.mean([n.local_graph_view['version'] for n in self.nodes]),
            'nodes': [n.get_statistics() for n in self.nodes]
        }
        return stats


def compare_mesh_vs_gossip():
    """
    Comparación teórica entre Mesh y Gossip.
    """
    print("=" * 70)
    print("📊 MESH vs GOSSIP - Comparative Analysis")
    print("=" * 70)
    
    comparison = """
    ┌─────────────────────┬──────────────────────┬──────────────────────┐
    │     Característica  │    Mesh Network      │   Gossip Protocol    │
    ├─────────────────────┼──────────────────────┼──────────────────────┤
    │ Conocimiento de Red │ Global (todos)       │ Local (vecinos)      │
    │ Convergencia        │ Rápida (determinista)│ Lenta (probabilística│
    │ Overhead de Memoria │ Alto (O(N))          │ Bajo (O(k))          │
    │ Tráfico de Red      │ Medio (optimizable)  │ Bajo (epidémico)     │
    │ Tolerancia a Fallos │ Media                │ Alta (redundancia)   │
    │ Escalabilidad       │ Limitada (<1000)     │ Excelente (>10k)     │
    │ Latencia            │ Baja (directa)       │ Media (multi-hop)    │
    │ Complejidad Impl.   │ Media                │ Baja                 │
    └─────────────────────┴──────────────────────┴──────────────────────┘
    
    🎯 RECOMENDACIONES:
    
    ✅ USA MESH si:
       - Tienes <100 nodos edge
       - Necesitas latencia mínima (<100ms)
       - Actualizaciones críticas (policía en tiempo real)
       - Red controlada (todos nodos confiables)
       - Ancho de banda suficiente
    
    ✅ USA GOSSIP si:
       - Tienes >100 nodos edge
       - Escalabilidad es prioridad
       - Tolerancia a fallos crítica
       - Red heterogénea (nodos entran/salen)
       - Ancho de banda limitado
    
    💡 HÍBRIDO (Mejor opción para Minority Report):
       - Mesh para zona crítica (centro ciudad, ~50 nodos)
       - Gossip para periferia (suburbios, ~200+ nodos)
       - Mesh-to-Gossip bridges en los límites
    """
    
    print(comparison)


# Simulación de ejemplo
if __name__ == "__main__":
    print("=" * 70)
    print("🕸️  Mesh Network Simulation - Minority Report")
    print("=" * 70)
    
    # Crear red Mesh
    network = MeshNetwork(num_nodes=5)
    
    # Iniciar red
    network.start()
    
    # Simular actualizaciones
    print("\n🎬 Simulating city graph updates...")
    network.simulate_city_update(num_updates=10)
    
    # Esperar a que se procesen mensajes
    time.sleep(2)
    
    # Mostrar estadísticas
    print("\n📊 Network Statistics:")
    stats = network.get_network_statistics()
    print(f"   Total messages sent: {stats['total_messages_sent']}")
    print(f"   Total messages received: {stats['total_messages_received']}")
    print(f"   Total bytes transmitted: {stats['total_bytes_transmitted']}")
    print(f"   Average graph version: {stats['avg_version']:.2f}")
    
    print("\n📈 Per-node statistics:")
    for node_stats in stats['nodes']:
        print(f"   Node {node_stats['node_id']}: "
              f"Sent={node_stats['messages_sent']}, "
              f"Received={node_stats['messages_received']}, "
              f"Version={node_stats['version']}")
    
    # Detener red
    network.stop()
    
    # Mostrar comparación
    print("\n")
    compare_mesh_vs_gossip()
