document.addEventListener('DOMContentLoaded', () => {
    // 1. Initialize Cytoscape Graph with metadata
    const cy = cytoscape({
        container: document.getElementById('cy'),
        elements: [
            // Nodes with features
            { data: { id: 's1', name: 'Safehouse Alpha', type: 'hideout', risk: 0.1, hidden: 0.9 }, position: { x: 100, y: 150 } },
            { data: { id: 's2', name: 'Safehouse Beta', type: 'hideout', risk: 0.1, hidden: 0.8 }, position: { x: 500, y: 350 } },
            { data: { id: 'b1', name: 'Central Bank', type: 'bank', risk: 0.4, hidden: 0.2 }, position: { x: 300, y: 250 } },
            { data: { id: 'p1', name: 'District 4 Police', type: 'police', risk: 0.9, hidden: 0.05 }, position: { x: 500, y: 150 } },
            { data: { id: 'bs1', name: 'Blind Spot 09', type: 'blindspot', risk: 0.05, hidden: 0.95 }, position: { x: 100, y: 350 } },

            // Edges with distancia and base_riesgo
            { data: { id: 'e1', source: 's1', target: 'b1', dist: 10, riesgo: 0.2, alpha: 0.7 } },
            { data: { id: 'e2', source: 'b1', target: 's2', dist: 15, riesgo: 0.5, alpha: 0.4 } },
            { data: { id: 'e3', source: 'b1', target: 'p1', dist: 5, riesgo: 0.9, alpha: 0.1 } },
            { data: { id: 'e4', source: 's2', target: 'bs1', dist: 8, riesgo: 0.1, alpha: 0.9 } },
            { data: { id: 'e5', source: 'bs1', target: 's1', dist: 12, riesgo: 0.05, alpha: 0.95 } }
        ],
        style: [
            {
                selector: 'node',
                style: {
                    'label': 'data(name)',
                    'color': '#fff',
                    'font-size': '10px',
                    'text-valign': 'bottom',
                    'text-margin-y': '5px',
                    'background-color': '#00f2ff',
                    'width': '20px',
                    'height': '20px',
                    'border-width': '2px',
                    'border-color': '#00f2ff',
                    'overlay-padding': '4px'
                }
            },
            {
                selector: 'node[type="hideout"]',
                style: { 'background-color': '#00ff95', 'border-color': '#00ff95' }
            },
            {
                selector: 'node[type="bank"]',
                style: { 'background-color': '#ffd700', 'border-color': '#ffd700', 'shape': 'diamond' }
            },
            {
                selector: 'node[type="police"]',
                style: { 'background-color': '#ff3e3e', 'border-color': '#ff3e3e', 'shape': 'triangle' }
            },
            {
                selector: 'node[type="blindspot"]',
                style: { 'background-color': '#bb00ff', 'border-color': '#bb00ff', 'shape': 'octagon' }
            },
            {
                selector: 'edge',
                style: {
                    'width': 'mapData(alpha, 0, 1, 0.5, 4)', // Visualizing GAT Alpha
                    'line-color': 'rgba(0, 242, 255, 0.3)',
                    'curve-style': 'bezier',
                    'target-arrow-shape': 'triangle',
                    'target-arrow-color': 'rgba(0, 242, 255, 0.3)',
                    'label': (ele) => `R: ${ele.data('riesgo')}`,
                    'font-size': '10px',
                    'font-weight': 'bold',
                    'color': '#00f2ff',
                    'text-rotation': 'autorotate',
                    'text-background-color': '#0a0e14',
                    'text-background-opacity': 1,
                    'text-background-padding': '4px',
                    'text-margin-y': '-2px'
                }
            },
            {
                selector: 'edge.active-route',
                style: {
                    'width': '4px',
                    'line-color': '#00ff95',
                    'target-arrow-color': '#00ff95',
                    'line-style': 'dashed',
                    'label': (ele) => `α: ${ele.data('alpha')}`
                }
            },
            {
                selector: 'node.scanning',
                style: {
                    'border-width': '6px',
                    'border-color': '#00f2ff',
                    'border-opacity': 0.5
                }
            }
        ],
        layout: { name: 'preset' },
        userZoomingEnabled: true,
        userPanningEnabled: true
    });

    const body = document.body;
    const statusText = document.getElementById('current-status');
    const feed = document.querySelector('.feed-content');
    const panicBtn = document.getElementById('panic-btn');

    // 2. GCN Simulation: Calculate neighborhood risk context
    function applyGCNContext() {
        cy.nodes().forEach(node => {
            const neighbors = node.neighborhood('node');
            if (neighbors.length > 0) {
                const avgRisk = neighbors.reduce((acc, n) => acc + (n.data('risk') || 0), 0) / neighbors.length;
                node.data('contextualRisk', avgRisk);

                // Visual feedback of contextual risk (GCN)
                if (avgRisk > 0.6) node.style('border-color', '#ff3e3e');
                else if (avgRisk > 0.3) node.style('border-color', '#ffd700');
            }
        });
        logMessage('GCN CONTEXT CALCULATED: NEIGHBORHOOD RISK AGGREGATED.');
    }

    // 3. Gossip Protocol Simulation
    function runGossipSim() {
        setInterval(() => {
            const edges = cy.edges();
            const randomEdge = edges[Math.floor(Math.random() * edges.length)];

            // Simulating a packet jump
            const sourcePos = randomEdge.source().position();
            const targetPos = randomEdge.target().position();

            logMessage(`MESH GOSSIP: NODE ${randomEdge.source().id()} SYNCING WITH ${randomEdge.target().id()}`);
        }, 15000);
    }

    // 4. Enhanced Panic Sequence (AI Scanning)
    async function runPanicSequence() {
        logMessage('PANIC SIGNAL SENT TO HIVE ENGINE...');
        body.classList.add('detected-state');
        body.classList.remove('safe-state');
        statusText.innerText = 'DETECTED';

        // Animated Scanning effect (Recursive Scan simulation)
        const nodes = cy.nodes();
        for (let i = 0; i < nodes.length; i++) {
            nodes[i].addClass('scanning');
            await new Promise(r => setTimeout(r, 200));
            nodes[i].removeClass('scanning');
        }

        // recalculate GAT Attention (simulated)
        logMessage('RECALCULATING GAT ATTENTION COEFFICIENTS (α)...');
        cy.edges().forEach(e => {
            if (e.data('riesgo') > 0.5) {
                e.data('alpha', 0.05);
                e.style('line-color', '#ff3e3e');
            } else {
                e.data('alpha', 0.98);
                e.style('line-color', '#00ff95');
                e.addClass('active-route');
            }
        });

        logMessage('EVASIÓN PROTOCOL: OPTIMAL ROUTE SECURED.');
    }

    function logMessage(msg) {
        const time = new Date().toLocaleTimeString();
        feed.innerHTML = `> [${time}] ${msg}<br>` + feed.innerHTML;
        // Keep only last 10 messages for performance
        const lines = feed.innerHTML.split('<br>');
        if (lines.length > 10) feed.innerHTML = lines.slice(0, 10).join('<br>');
    }

    // Initialize logic
    cy.ready(() => {
        applyGCNContext();
        runGossipSim();
        logMessage('GHOST CLIENT INITIALIZED. STANDING BY.');
    });

    // Panic Button Listener
    panicBtn.addEventListener('click', () => {
        if (body.classList.contains('safe-state')) {
            runPanicSequence();
        } else {
            // Reset state
            body.classList.remove('detected-state');
            body.classList.add('safe-state');
            statusText.innerText = 'SAFE';
            cy.edges().removeClass('active-route').style('line-color', 'rgba(0, 242, 255, 0.3)');
            logMessage('SYSTEM RESET: AREA CLEAR');
        }
    });

    window.addEventListener('resize', () => {
        cy.resize();
        cy.fit();
    });
});
