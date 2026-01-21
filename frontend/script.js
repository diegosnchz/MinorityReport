document.addEventListener('DOMContentLoaded', () => {
    // 1. Initialize Cytoscape Graph
    const cy = cytoscape({
        container: document.getElementById('cy'),
        elements: [
            // Nodes
            { data: { id: 's1', name: 'Safehouse Alpha', type: 'hideout' }, position: { x: 100, y: 100 } },
            { data: { id: 's2', name: 'Safehouse Beta', type: 'hideout' }, position: { x: 400, y: 300 } },
            { data: { id: 'b1', name: 'Central Bank', type: 'bank' }, position: { x: 250, y: 150 } },
            { data: { id: 'p1', name: 'District 4 Police', type: 'police' }, position: { x: 450, y: 100 } },
            { data: { id: 'bs1', name: 'Blind Spot 09', type: 'blindspot' }, position: { x: 200, y: 350 } },
            
            // Edges
            { data: { id: 'e1', source: 's1', target: 'b1', weight: 5 } },
            { data: { id: 'e2', source: 'b1', target: 's2', weight: 8 } },
            { data: { id: 'e3', source: 'b1', target: 'p1', weight: 2 } },
            { data: { id: 'e4', source: 's2', target: 'bs1', weight: 3 } },
            { data: { id: 'e5', source: 'bs1', target: 's1', weight: 4 } }
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
                    'width': '1px',
                    'line-color': 'rgba(0, 242, 255, 0.3)',
                    'curve-style': 'bezier',
                    'target-arrow-shape': 'triangle',
                    'target-arrow-color': 'rgba(0, 242, 255, 0.3)'
                }
            },
            {
                selector: 'edge.active-route',
                style: {
                    'width': '3px',
                    'line-color': '#00ff95',
                    'target-arrow-color': '#00ff95',
                    'line-style': 'dashed'
                }
            }
        ],
        layout: {
            name: 'grid',
            rows: 2
        },
        userZoomingEnabled: true,
        userPanningEnabled: true
    });

    // 2. Logic for State Management
    const body = document.body;
    const statusText = document.getElementById('current-status');
    const feed = document.querySelector('.feed-content');
    const panicBtn = document.getElementById('panic-btn');

    function logMessage(msg) {
        const time = new Date().toLocaleTimeString();
        feed.innerHTML += `<br>> [${time}] ${msg}`;
        feed.scrollTop = feed.scrollHeight;
    }

    function toggleStatus() {
        if (body.classList.contains('safe-state')) {
            // Switch to DETECTED
            body.classList.remove('safe-state');
            body.classList.add('detected-state');
            statusText.innerText = 'DETECTED';
            logMessage('CRITICAL ALERT: POLICE PATROL DETECTED NEAR SECTOR 4');
            logMessage('RECALCULATING EVASION ROUTE...');
            
            // Highlight a target route in the graph
            cy.edges().removeClass('active-route');
            cy.elements('#e4, #e5').addClass('active-route');
            
            setTimeout(() => {
                logMessage('GAT OPTIMIZATION COMPLETE: ROUTE UPDATED');
            }, 1000);
        } else {
            // Switch to SAFE
            body.classList.remove('detected-state');
            body.classList.add('safe-state');
            statusText.innerText = 'SAFE';
            logMessage('SYSTEM RESET: AREA CLEAR');
            cy.edges().removeClass('active-route');
        }
    }

    // 3. Panic Button Listener
    panicBtn.addEventListener('click', () => {
        logMessage('PANIC SIGNAL SENT TO HIVE ENGINE...');
        toggleStatus();
    });

    // Handle Window Resize
    window.addEventListener('resize', () => {
        cy.resize();
        cy.fit();
    });

    // Initial log
    logMessage('GHOST CLIENT INITIALIZED. STANDING BY.');
});
