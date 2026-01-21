// ============================================================================
// HIVE CORE CLIENT - FastAPI Integration
// ============================================================================
// Esta clase maneja la comunicación con el backend FastAPI ("The Hive Core").
// Se encarga de enviar alertas de pánico y monitorear el estado del sistema.

class HiveCoreClient {
    constructor(port = 8000) {
        this.baseUrl = `http://localhost:${port}`;
        this.wsUrl = `ws://localhost:${port}/ws/ghost_${Math.floor(Math.random() * 1000)}`;
        this.ws = null;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
    }

    // Inicializar conexión WebSocket
    connectWebSocket() {
        console.log(`HIVE_CORE: Conectando a túnel WebSocket...`);
        this.ws = new WebSocket(this.wsUrl);

        this.ws.onopen = () => {
            console.log("HIVE_CORE: WebSocket Conectado ✅");
            this.reconnectAttempts = 0;
        };

        this.ws.onmessage = (event) => {
            console.log("HIVE_CORE: Mensaje recibido:", event.data);
        };

        this.ws.onclose = () => {
            console.warn("HIVE_CORE: WebSocket Desconectado 🛑");
            this.attemptReconnect();
        };

        this.ws.onerror = (err) => {
            console.error("HIVE_CORE: Error en WebSocket:", err);
        };
    }

    attemptReconnect() {
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnectAttempts++;
            const delay = Math.pow(2, this.reconnectAttempts) * 1000;
            console.log(`HIVE_CORE: Reintentando conexión en ${delay / 1000}s...`);
            setTimeout(() => this.connectWebSocket(), delay);
        }
    }

    // Reportar peligro al endpoint /alert
    async reportAlert(nodeId, type, message = "Pánico detectado") {
        console.log(`HIVE_CORE: Reportando alerta desde ${nodeId}...`);
        try {
            const response = await fetch(`${this.baseUrl}/alert`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    id_nodo: nodeId,
                    tipo: type,
                    mensaje: message,
                    timestamp: new Date().toISOString()
                })
            });
            const data = await response.json();
            return data;
        } catch (error) {
            console.warn("HIVE_CORE: Error al reportar alerta:", error.message);
            return { status: "offline", message: "Servidor no alcanzable" };
        }
    }

    // Obtener estado completo del backend
    async getQueueStatus() {
        try {
            const response = await fetch(`${this.baseUrl}/status`);
            return await response.json();
        } catch (error) {
            return null;
        }
    }
}

// ============================================================================
// THE GHOST - Core Script
// ============================================================================

document.addEventListener('DOMContentLoaded', () => {

    const hiveClient = new HiveCoreClient();
    hiveClient.connectWebSocket();

    // ========================================================================
    // 1. DATOS DEL GRAFO 3D
    // ========================================================================
    // Define todos los nodos (ubicaciones) y enlaces (conexiones) del mapa

    const graphData = {
        nodes: [
            // Hideout único - El destino seguro del protocolo de pánico
            { id: 's1', name: 'Safe Hideout', type: 'hideout', x: -200, y: 50, z: -100 },

            // Otras zonas seguras (no son hideouts)
            { id: 's2', name: 'Safehouse Beta', type: 'blindspot', x: 250, y: -80, z: 200 },
            { id: 's3', name: 'Safehouse Gamma', type: 'blindspot', x: -150, y: 100, z: 250 },
            { id: 's4', name: 'Safehouse Delta', type: 'junction', x: 300, y: -50, z: -150 },

            // Bancos - Objetivos de alto valor pero con más vigilancia
            { id: 'b1', name: 'Central Bank', type: 'bank', x: 0, y: 0, z: 0 },
            { id: 'b2', name: 'ATM District 7', type: 'bank', x: 150, y: 30, z: -80 },

            // Zonas policiales - Áreas de máximo riesgo
            { id: 'p1', name: 'District 4 Police', type: 'police', x: 200, y: -100, z: -200 },
            { id: 'p2', name: 'Metro Station Guard', type: 'police', x: -100, y: 80, z: 100 },
            { id: 'p3', name: 'Checkpoint 6', type: 'police', x: -250, y: 0, z: -50 },

            // Puntos ciegos - Zonas con poca vigilancia
            { id: 'bs1', name: 'Blind Spot 09', type: 'blindspot', x: -180, y: 50, z: 80 },
            { id: 'bs2', name: 'Blind Spot 12', type: 'blindspot', x: 180, y: 120, z: 220 },
            { id: 'bs3', name: 'Alley Network', type: 'blindspot', x: 280, y: -30, z: 120 },

            // Junctions - Zonas públicas de tránsito
            { id: 'junc1', name: 'Plaza Central', type: 'junction', x: 50, y: -20, z: -120 },
            { id: 'junc2', name: 'Market Square', type: 'junction', x: -120, y: 30, z: -30 },
            { id: 'junc3', name: 'East End', type: 'junction', x: 230, y: 0, z: 50 }
        ],
        links: [
            { source: 's1', target: 'junc2', riesgo: 0.15, baseRiesgo: 0.15 },
            { source: 'junc2', target: 'b1', riesgo: 0.3, baseRiesgo: 0.3 },
            { source: 'b1', target: 'junc1', riesgo: 0.25, baseRiesgo: 0.25 },
            { source: 'junc1', target: 'p1', riesgo: 0.85, baseRiesgo: 0.85 },
            { source: 'junc1', target: 'b2', riesgo: 0.35, baseRiesgo: 0.35 },
            { source: 'b2', target: 'junc3', riesgo: 0.4, baseRiesgo: 0.4 },
            { source: 'junc3', target: 's2', riesgo: 0.2, baseRiesgo: 0.2 },
            { source: 's2', target: 'bs2', riesgo: 0.1, baseRiesgo: 0.1 },
            { source: 'bs2', target: 's3', riesgo: 0.08, baseRiesgo: 0.08 },
            { source: 's3', target: 'p2', riesgo: 0.7, baseRiesgo: 0.7 },
            { source: 'p2', target: 'bs1', riesgo: 0.6, baseRiesgo: 0.6 },
            { source: 'bs1', target: 's1', riesgo: 0.05, baseRiesgo: 0.05 },
            { source: 's1', target: 'p3', riesgo: 0.8, baseRiesgo: 0.8 },
            { source: 'p3', target: 'junc2', riesgo: 0.75, baseRiesgo: 0.75 },
            { source: 'junc3', target: 'bs3', riesgo: 0.12, baseRiesgo: 0.12 },
            { source: 'bs3', target: 's4', riesgo: 0.15, baseRiesgo: 0.15 },
            { source: 's4', target: 'p1', riesgo: 0.9, baseRiesgo: 0.9 },
            { source: 'b1', target: 'p2', riesgo: 0.65, baseRiesgo: 0.65 }
        ]
    };

    // Estado del agente
    let currentNodeId = 's1';
    let isFollowingPanicRoute = false;
    let panicRoute = [];
    let panicRouteIndex = 0;
    const visitedNodes = new Map();
    visitedNodes.set(currentNodeId, Date.now());

    // Mapa de adyacencia
    const adjacencyMap = {};
    graphData.links.forEach(link => {
        if (!adjacencyMap[link.source]) adjacencyMap[link.source] = [];
        if (!adjacencyMap[link.target]) adjacencyMap[link.target] = [];
        adjacencyMap[link.source].push({ node: link.target, link: link });
        adjacencyMap[link.target].push({ node: link.source, link: link });
    });

    // Dijkstra para ruta más segura
    function findSafestPath(start, targetType) {
        const distances = {};
        const previous = {};
        const unvisited = new Set();

        graphData.nodes.forEach(node => {
            distances[node.id] = Infinity;
            previous[node.id] = null;
            unvisited.add(node.id);
        });

        distances[start] = 0;

        while (unvisited.size > 0) {
            let current = null;
            let minDist = Infinity;
            unvisited.forEach(nodeId => {
                if (distances[nodeId] < minDist) {
                    minDist = distances[nodeId];
                    current = nodeId;
                }
            });
            if (current === null) break;
            unvisited.delete(current);

            const currentNode = graphData.nodes.find(n => n.id === current);
            if (currentNode.type === targetType) {
                const path = [];
                let step = current;
                while (step !== null) {
                    path.unshift(step);
                    step = previous[step];
                }
                return path;
            }

            const neighbors = adjacencyMap[current] || [];
            neighbors.forEach(({ node, link }) => {
                const riskCost = link.riesgo * 100;
                const alt = distances[current] + riskCost;
                if (alt < distances[node]) {
                    distances[node] = alt;
                    previous[node] = current;
                }
            });
        }
        return [start];
    }

    // Variación dinámica del riesgo
    function updateDynamicRisk() {
        graphData.links.forEach(link => {
            const variation = (Math.random() - 0.5) * 0.6;
            link.riesgo = Math.max(0.05, Math.min(0.95, link.baseRiesgo + variation));
        });
        Graph.linkColor(Graph.linkColor());
    }
    setInterval(updateDynamicRisk, 3000);

    // Inicialización del Grafo 3D
    const Graph = ForceGraph3D()
        (document.getElementById('cy'))
        .graphData(graphData)
        .backgroundColor('#0a0e14')
        .nodeLabel('name')
        .nodeVal(8)
        .nodeColor(node => {
            if (node.id === currentNodeId) return '#00ff95';
            if (visitedNodes.has(node.id)) {
                const age = Date.now() - visitedNodes.get(node.id);
                const fadeFactor = Math.min(age / 60000, 1);
                const r = Math.floor(204 - fadeFactor * 102);
                const g = Math.floor(102 - fadeFactor * 51);
                const b = Math.floor(51 - fadeFactor * 25);
                return `rgb(${r}, ${g}, ${b})`;
            }
            return '#ff8c42';
        })
        .nodeOpacity(1.0)
        .nodeResolution(20)
        .linkColor(link => {
            const risk = link.riesgo;
            if (risk > 0.7) return 'rgba(255, 62, 62, 1.0)';
            if (risk > 0.4) return 'rgba(255, 215, 0, 0.95)';
            return 'rgba(0, 242, 255, 0.9)';
        })
        .linkWidth(link => 1.5 + (1 - link.riesgo) * 2.5)
        .linkOpacity(1.0)
        .linkDirectionalParticles(4)
        .linkDirectionalParticleWidth(3)
        .linkDirectionalParticleSpeed(0.008)
        .enableNodeDrag(true) // ACTIVADO: Nodos maleables
        .onNodeDragEnd(node => {
            node.fx = node.x;
            node.fy = node.y;
            node.fz = node.z;
            logMessage(`COORDENADAS FIJADAS: ${node.name.toUpperCase()}`);
        })
        .onNodeClick(node => {
            logMessage(`📍 LOCATION: ${node.name.toUpperCase()}`);
        })
        .showNavInfo(false);

    Graph.cameraPosition({ x: 0, y: 0, z: 600 }, { x: 0, y: 0, z: 0 }, 2000);

    // Movimiento
    function moveThief() {
        if (isFollowingPanicRoute && panicRoute.length > 0) {
            panicRouteIndex++;
            if (panicRouteIndex >= panicRoute.length) {
                isFollowingPanicRoute = false;
                logMessage('✅ ARRIVED AT SAFE HIDEOUT');
                return;
            }
            currentNodeId = panicRoute[panicRouteIndex];
        } else {
            const neighbors = adjacencyMap[currentNodeId] || [];
            if (neighbors.length === 0) return;
            const next = neighbors[Math.floor(Math.random() * neighbors.length)];
            currentNodeId = next.node;
        }

        visitedNodes.set(currentNodeId, Date.now());
        const currentNode = graphData.nodes.find(n => n.id === currentNodeId);
        logMessage(`🏃 MOVING TO: ${currentNode.name.toUpperCase()}`);

        Graph.nodeColor(Graph.nodeColor());
        updateSystemStatus(currentNode);
    }

    setInterval(moveThief, 3000);

    // UI y Logs
    function updateSystemStatus(node) {
        const statusText = document.getElementById('current-status');
        const body = document.body;
        if (node.type === 'police') {
            statusText.innerText = 'HIGH ALERT';
            body.classList.remove('safe-state');
            body.classList.add('detected-state');
            logMessage('⚠️ DANGER: POLICE ZONE');
        } else if (node.type === 'hideout' || node.type === 'blindspot') {
            statusText.innerText = 'SAFE';
            body.classList.add('safe-state');
            body.classList.remove('detected-state');
        } else {
            statusText.innerText = 'CAUTION';
            body.classList.add('safe-state');
            body.classList.remove('detected-state');
        }
    }

    const feed = document.querySelector('.feed-content');
    const panicBtn = document.getElementById('panic-btn');

    function logMessage(msg) {
        const time = new Date().toLocaleTimeString();
        feed.innerHTML = `> [${time}] ${msg}<br>` + feed.innerHTML;
        const lines = feed.innerHTML.split('<br>');
        if (lines.length > 15) feed.innerHTML = lines.slice(0, 15).join('<br>');
    }

    async function runPanicSequence() {
        logMessage('🚨 PANIC ACTIVATED: CALCULATING SAFEST ROUTE...');

        // Notificar al backend FastAPI
        const response = await hiveClient.reportAlert(currentNodeId, "PANIC", "Evasion protocol triggered by user");
        if (response.status === "received") {
            logMessage(`📡 BACKEND: ${response.message.toUpperCase()}`);
        } else if (response.status === "offline") {
            logMessage('📡 BACKEND: OFFLINE (Running local evasion)');
        }

        panicRoute = findSafestPath(currentNodeId, 'hideout');
        if (panicRoute.length > 1) {
            logMessage(`🛣️ ROUTE FOUND: ${panicRoute.length - 1} HOPS TO SAFETY`);
            isFollowingPanicRoute = true;
            panicRouteIndex = 0;
            logMessage('🏃‍♂️ EXECUTING EVASION ROUTE...');
        } else {
            logMessage('✅ ALREADY AT SAFE LOCATION');
        }
    }

    panicBtn.addEventListener('click', runPanicSequence);

    // Monitoreo de estado del backend (Polling cada 10s)
    async function pollBackendStatus() {
        const status = await hiveClient.getQueueStatus();
        if (status) {
            console.log(`HIVE_CORE: Worker [${status.estado_worker}] | Tareas: ${status.tareas_pendientes}`);
        }
    }
    setInterval(pollBackendStatus, 10000);

    // Inicio
    logMessage('GHOST CLIENT 3D INITIALIZED. STANDING BY.');
    logMessage(`MONITORING ${graphData.nodes.length} NODES.`);
    updateSystemStatus(graphData.nodes.find(n => n.id === currentNodeId));
});
