import random
import time
import threading

class EdgeNode:
    def __init__(self, node_id, neighbors, local_graph_view):
        self.node_id = node_id
        self.neighbors = neighbors # List of directly connected Edge Nodes
        self.local_graph_view = local_graph_view # Dictionary or Subgraph object
        self.lock = threading.Lock()
        
    def select_peer(self):
        """Select a random neighbor to gossip with."""
        if not self.neighbors:
            return None
        return random.choice(self.neighbors)

    def prepare_digest(self):
        """Prepare a summary of local knowledge (e.g., hash of embeddings or timestamp of last update)."""
        with self.lock:
            # Simplification: sending a version number or checksum
            return {
                'node_id': self.node_id,
                'version': self.local_graph_view.get('version', 0),
                'top_updates': self.local_graph_view.get('recent_embeddings', [])
            }

    def reconcile(self, peer_digest):
        """Compare peer knowledge with local knowledge and fetch missing pieces."""
        # IF peer has newer version of a subgraph component:
        #   Request update from peer
        #   Merge update into self.local_graph_view
        pass

    def start_gossip_loop(self):
        """Main loop: The heartbeat of the decentralized network."""
        while True:
            # 1. Select Peer
            peer = self.select_peer()
            if peer:
                # 2. Push/Pull Sync
                # Simulating an exchange of "Graph Diffs" (random vector updates)
                digest = self.prepare_digest()
                print(f"[Node {self.node_id}] 📡 Contacting [Node {peer.node_id}] | My Version: {digest['version']}")
                
                # Simulate receiving an update that increases our knowledge (version)
                if random.random() > 0.5:
                     with self.lock:
                         self.local_graph_view['version'] += 1
                         print(f"   ↳ [Node {self.node_id}] ✅ Synced with {peer.node_id}. New Version: {self.local_graph_view['version']}")
                else:
                     print(f"   ↳ [Node {self.node_id}] ➖ No updates needed.")
            
            # 3. Wait (e.g., 100ms)
            time.sleep(0.1)

# Simulation
if __name__ == "__main__":
    # Setup a small cluster of edge nodes
    nodes = []
    for i in range(5):
        nodes.append(EdgeNode(id=i, neighbors=[], local_graph_view={'version': 0}))

    # Connect them randomly (Small World Network)
    for node in nodes:
        potential = [n for n in nodes if n != node]
        node.neighbors = random.sample(potential, 2)

    print("--- 🕵️ Minority Report: Distributed Edge Gossip Network Started ---")
    print("Nodes are exchanging local graph embeddings to synchronize criminal patterns...")
    
    # Start Gossip Threads
    threads = [threading.Thread(target=n.start_gossip_loop, daemon=True) for n in nodes]
    for t in threads: 
        t.start()
    
    # Run simulation for 5 seconds then stop
    time.sleep(5)
    print("--- Simulation Ended ---")
