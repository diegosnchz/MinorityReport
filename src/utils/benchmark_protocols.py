"""
Benchmark: Gossip Protocol vs Mesh Network
Comparación de rendimiento para decidir cuál usar en Minority Report

Este script ejecuta ambos protocolos bajo las mismas condiciones
y compara métricas clave de rendimiento.

Author: The Oracle
"""

import time
import statistics
from typing import Dict, List
import matplotlib
matplotlib.use('Agg')  # Para generar gráficos sin display
import matplotlib.pyplot as plt

# Importar ambas implementaciones
from gossip_protocol import EdgeNode as GossipNode
from mesh_network import MeshNetwork, GraphUpdate, SyncStrategy
import random
import threading


class BenchmarkRunner:
    """
    Ejecuta benchmarks comparativos entre Gossip y Mesh.
    """
    
    def __init__(self):
        self.results = {
            'gossip': {},
            'mesh': {}
        }
    
    def benchmark_gossip(self, num_nodes: int, num_updates: int, duration: int) -> Dict:
        """
        Benchmark del protocolo Gossip.
        
        Args:
            num_nodes: Número de nodos
            num_updates: Número de actualizaciones a propagar
            duration: Duración en segundos
        
        Returns:
            Diccionario con métricas
        """
        print(f"\n🔄 Benchmarking Gossip Protocol...")
        print(f"   Nodes: {num_nodes}, Updates: {num_updates}, Duration: {duration}s")
        
        start_time = time.time()
        
        # Crear nodos Gossip
        nodes = []
        for i in range(num_nodes):
            node = GossipNode(
                node_id=i,
                neighbors=[],
                local_graph_view={'version': 0}
            )
            nodes.append(node)
        
        # Conectar nodos aleatoriamente (grafo aleatorio)
        for node in nodes:
            potential = [n for n in nodes if n != node]
            num_neighbors = min(3, len(potential))  # 3 vecinos por nodo
            node.neighbors = random.sample(potential, num_neighbors)
        
        # Flag para detener threads
        stop_flag = {'stop': False}
        
        # Versión modificada del gossip loop con condición de parada
        def gossip_loop_with_timeout(node, stop_flag, duration):
            """Gossip loop que se detiene después de duration segundos."""
            end_time = time.time() + duration
            while time.time() < end_time and not stop_flag['stop']:
                peer = node.select_peer()
                if peer:
                    digest = node.prepare_digest()
                    if random.random() > 0.5:
                        with node.lock:
                            node.local_graph_view['version'] += 1
                time.sleep(0.1)
        
        # Iniciar threads de gossip con timeout
        threads = []
        for node in nodes:
            thread = threading.Thread(
                target=gossip_loop_with_timeout, 
                args=(node, stop_flag, duration),
                daemon=True
            )
            thread.start()
            threads.append(thread)
        
        # Esperar a que terminen los threads
        for thread in threads:
            thread.join(timeout=duration + 1)
        
        # Asegurar que todos se detengan
        stop_flag['stop'] = True
        
        # Recopilar métricas
        versions = [node.local_graph_view.get('version', 0) for node in nodes]
        
        end_time = time.time()
        elapsed = end_time - start_time
        
        metrics = {
            'nodes': num_nodes,
            'elapsed_time': elapsed,
            'avg_version': statistics.mean(versions),
            'std_version': statistics.stdev(versions) if len(versions) > 1 else 0,
            'min_version': min(versions),
            'max_version': max(versions),
            'convergence_ratio': min(versions) / max(versions) if max(versions) > 0 else 0,
            'updates_per_second': sum(versions) / elapsed
        }
        
        print(f"   ✅ Completed: Avg version={metrics['avg_version']:.2f}, "
              f"Convergence={metrics['convergence_ratio']:.2%}")
        
        return metrics
    
    def benchmark_mesh(self, num_nodes: int, num_updates: int, duration: int) -> Dict:
        """
        Benchmark de Mesh Network.
        
        Args:
            num_nodes: Número de nodos
            num_updates: Número de actualizaciones a propagar
            duration: Duración en segundos
        
        Returns:
            Diccionario con métricas
        """
        print(f"\n🕸️  Benchmarking Mesh Network...")
        print(f"   Nodes: {num_nodes}, Updates: {num_updates}, Duration: {duration}s")
        
        start_time = time.time()
        
        # Crear red Mesh
        network = MeshNetwork(num_nodes=num_nodes)
        network.start()
        
        # Simular actualizaciones
        for i in range(num_updates):
            source_node = random.choice(network.nodes)
            update = GraphUpdate(
                update_id=f"update_{i}",
                source_node_id=source_node.node_id,
                timestamp=time.time(),
                node_updates={random.randint(0, 100): {'police_level': random.random()}},
                priority=random.randint(0, 2)
            )
            strategy = random.choice(list(SyncStrategy))
            source_node.broadcast_update(update, strategy)
            time.sleep(0.01)  # Pequeño delay entre updates
        
        # Esperar a que se procesen todos los mensajes
        time.sleep(max(1, duration - (time.time() - start_time)))
        
        # Recopilar métricas
        stats = network.get_network_statistics()
        versions = [node.local_graph_view['version'] for node in network.nodes]
        
        end_time = time.time()
        elapsed = end_time - start_time
        
        network.stop()
        
        metrics = {
            'nodes': num_nodes,
            'elapsed_time': elapsed,
            'avg_version': stats['avg_version'],
            'std_version': statistics.stdev(versions) if len(versions) > 1 else 0,
            'min_version': min(versions),
            'max_version': max(versions),
            'convergence_ratio': min(versions) / max(versions) if max(versions) > 0 else 0,
            'total_messages': stats['total_messages_sent'],
            'total_bytes': stats['total_bytes_transmitted'],
            'updates_per_second': stats['total_messages_sent'] / elapsed
        }
        
        print(f"   ✅ Completed: Avg version={metrics['avg_version']:.2f}, "
              f"Messages={metrics['total_messages']}, "
              f"Convergence={metrics['convergence_ratio']:.2%}")
        
        return metrics
    
    def run_comparison(self, scenarios: List[Dict]):
        """
        Ejecuta comparación en múltiples escenarios.
        
        Args:
            scenarios: Lista de configuraciones a probar
        """
        print("=" * 70)
        print("📊 GOSSIP vs MESH - Performance Benchmark")
        print("=" * 70)
        
        for i, scenario in enumerate(scenarios, 1):
            print(f"\n{'='*70}")
            print(f"Scenario {i}: {scenario['name']}")
            print(f"{'='*70}")
            
            # Benchmark Gossip
            gossip_metrics = self.benchmark_gossip(
                num_nodes=scenario['num_nodes'],
                num_updates=scenario['num_updates'],
                duration=scenario['duration']
            )
            
            # Benchmark Mesh
            mesh_metrics = self.benchmark_mesh(
                num_nodes=scenario['num_nodes'],
                num_updates=scenario['num_updates'],
                duration=scenario['duration']
            )
            
            # Guardar resultados
            self.results['gossip'][scenario['name']] = gossip_metrics
            self.results['mesh'][scenario['name']] = mesh_metrics
            
            # Comparar
            self._compare_metrics(scenario['name'], gossip_metrics, mesh_metrics)
    
    def _compare_metrics(self, scenario_name: str, gossip: Dict, mesh: Dict):
        """
        Compara métricas entre Gossip y Mesh.
        """
        print(f"\n📊 Comparison for {scenario_name}:")
        print(f"   {'Metric':<30} {'Gossip':<15} {'Mesh':<15} {'Winner':<10}")
        print(f"   {'-'*70}")
        
        # Convergencia (mayor es mejor)
        g_conv = gossip['convergence_ratio']
        m_conv = mesh['convergence_ratio']
        conv_winner = "Mesh" if m_conv > g_conv else "Gossip"
        print(f"   {'Convergence Ratio':<30} {g_conv:<15.2%} {m_conv:<15.2%} {conv_winner:<10}")
        
        # Consistencia (menor std es mejor)
        g_std = gossip['std_version']
        m_std = mesh['std_version']
        std_winner = "Mesh" if m_std < g_std else "Gossip"
        print(f"   {'Version Std Dev':<30} {g_std:<15.2f} {m_std:<15.2f} {std_winner:<10}")
        
        # Throughput (mayor es mejor)
        g_tput = gossip['updates_per_second']
        m_tput = mesh['updates_per_second']
        tput_winner = "Mesh" if m_tput > g_tput else "Gossip"
        print(f"   {'Updates/sec':<30} {g_tput:<15.2f} {m_tput:<15.2f} {tput_winner:<10}")
        
        # Latencia (menor es mejor) - aproximado por tiempo de convergencia
        g_time = gossip['elapsed_time']
        m_time = mesh['elapsed_time']
        time_winner = "Mesh" if m_time < g_time else "Gossip"
        print(f"   {'Elapsed Time (s)':<30} {g_time:<15.2f} {m_time:<15.2f} {time_winner:<10}")
        
        # Ancho de banda (solo Mesh lo reporta)
        if 'total_bytes' in mesh:
            print(f"   {'Total Bytes (Mesh only)':<30} {'-':<15} {mesh['total_bytes']:<15}")
    
    def generate_report(self):
        """
        Genera un reporte final con recomendaciones.
        """
        print("\n" + "=" * 70)
        print("📋 FINAL REPORT & RECOMMENDATIONS")
        print("=" * 70)
        
        # Calcular promedios
        gossip_avg_conv = statistics.mean(
            [r['convergence_ratio'] for r in self.results['gossip'].values()]
        )
        mesh_avg_conv = statistics.mean(
            [r['convergence_ratio'] for r in self.results['mesh'].values()]
        )
        
        gossip_avg_tput = statistics.mean(
            [r['updates_per_second'] for r in self.results['gossip'].values()]
        )
        mesh_avg_tput = statistics.mean(
            [r['updates_per_second'] for r in self.results['mesh'].values()]
        )
        
        print(f"\n📊 Average Performance:")
        print(f"   Gossip - Convergence: {gossip_avg_conv:.2%}, Throughput: {gossip_avg_tput:.2f} ups")
        print(f"   Mesh   - Convergence: {mesh_avg_conv:.2%}, Throughput: {mesh_avg_tput:.2f} ups")
        
        print(f"\n🎯 RECOMMENDATION FOR MINORITY REPORT:")
        
        if mesh_avg_conv > gossip_avg_conv * 1.2:
            print(f"   ✅ MESH NETWORK is recommended")
            print(f"      - {((mesh_avg_conv/gossip_avg_conv - 1) * 100):.1f}% better convergence")
            print(f"      - Suitable for <100 edge nodes")
            print(f"      - Best for real-time police tracking")
        elif gossip_avg_tput > mesh_avg_tput * 1.2:
            print(f"   ✅ GOSSIP PROTOCOL is recommended")
            print(f"      - {((gossip_avg_tput/mesh_avg_tput - 1) * 100):.1f}% better throughput")
            print(f"      - Suitable for >100 edge nodes")
            print(f"      - Best for large-scale deployment")
        else:
            print(f"   ✅ HYBRID APPROACH is recommended")
            print(f"      - Use Mesh for critical zones (downtown, ~50 nodes)")
            print(f"      - Use Gossip for peripheral zones (~200+ nodes)")
            print(f"      - Best overall performance/scalability balance")
        
        print(f"\n💡 Implementation Priority:")
        print(f"   1. Start with Gossip (already implemented)")
        print(f"   2. Add Mesh for high-priority zones (future sprint)")
        print(f"   3. Implement hybrid bridges (optimization phase)")


def main():
    """
    Función principal de benchmark.
    """
    benchmark = BenchmarkRunner()
    
    # Definir escenarios de prueba
    scenarios = [
        {
            'name': 'Small Network (10 nodes)',
            'num_nodes': 10,
            'num_updates': 20,
            'duration': 3
        },
        {
            'name': 'Medium Network (25 nodes)',
            'num_nodes': 25,
            'num_updates': 50,
            'duration': 5
        },
        {
            'name': 'Large Network (50 nodes)',
            'num_nodes': 50,
            'num_updates': 100,
            'duration': 8
        }
    ]
    
    # Ejecutar comparación
    benchmark.run_comparison(scenarios)
    
    # Generar reporte final
    benchmark.generate_report()
    
    print("\n" + "=" * 70)
    print("✨ Benchmark completed!")
    print("=" * 70)


if __name__ == "__main__":
    main()
