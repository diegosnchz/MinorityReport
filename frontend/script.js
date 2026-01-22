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

document.addEventListener('DOMContentLoaded', async () => {

    const hiveClient = new HiveCoreClient();
    hiveClient.connectWebSocket();

    // ========================================================================
    // 1. CARGA DE DATOS (JSON EXTERNO)
    // ========================================================================
    // Cargamos la topología de la ciudad desde un archivo separado para despliegue

    let graphData;
    try {
        const dataResponse = await fetch('data.json');
        graphData = await dataResponse.json();
        console.log("THE GHOST: Topología cargada desde data.json");
    } catch (error) {
        console.error("THE GHOST: Error cargando data.json. Usando datos de emergencia.", error);
        graphData = { nodes: [{ id: 's1', name: 'Emergency Hideout', type: 'hideout', x: 0, y: 0, z: 0 }], links: [] };
    }

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
            if (node.id === currentNodeId) return '#00ff95'; // Agente actual

            const typeColors = {
                hideout: '#00ff95',   // Verde (Seguro)
                bank: '#ffd700',      // Oro (Objetivo)
                police: '#ff3e3e',    // Rojo (Peligro)
                blindspot: '#bb00ff', // Púrpura (Invisibilidad)
                junction: '#4dabf7'   // Azul (Tránsito)
            };

            const baseColor = typeColors[node.type] || '#ff8c42';

            if (visitedNodes.has(node.id)) {
                return baseColor; // Mantener color para nodos visitados (táctico)
            }
            return baseColor;
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

            // Si el Oráculo (GAT) nos da una ruta, la usamos. Si no, calculamos localmente.
            if (response.path && response.path.length > 0) {
                panicRoute = response.path;
                logMessage('🧠 GAT MODEL: OPTIMAL ROUTE RECEIVED');
            } else {
                logMessage('🧠 GAT MODEL: NO ROUTE PROVIDED. CALCULATING LOCAL FALLBACK...');
                panicRoute = findSafestPath(currentNodeId, 'hideout');
            }
        } else {
            if (response.status === "offline") {
                logMessage('📡 BACKEND: OFFLINE (Running local evasion)');
            }
            panicRoute = findSafestPath(currentNodeId, 'hideout');
        }

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
