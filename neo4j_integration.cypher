// 1. Project the Graph for GNN Training (Graph Data Science Library)
// This creates an in-memory graph projection named 'minorityReportGraph'
// containing Person nodes and INTERACTS_WITH relationships.
CALL gds.graph.project(
    'minorityReportGraph',
    'Person',
    {
        INTERACTS_WITH: {
            orientation: 'UNDIRECTED',
            properties: ['weight', 'timestamp']
        }
    },
    {
        nodeProperties: ['embedding', 'criminalRecord']
    }
)
YIELD graphName, nodeCount, relationshipCount, projectMillis;

// 2. Export Graph Data to Python (Concept)
// In practice, you would use the Neo4j Python Driver to stream this data.
// This query retrieves the node features and adjacency list.
MATCH (p:Person)
OPTIONAL MATCH (p)-[r:INTERACTS_WITH]-(other:Person)
RETURN p.id AS nodeId, p.embedding AS features, collect(other.id) AS neighbors;

// 3. Write Back "Pre-Crime" Risk Scores
// After the GAT Discriminator predicts the risk, we update the Neo4j graph.
// :param batch is a list of maps passed from Python: [{id: 123, risk: 0.95}, ...]
UNWIND $batch AS row
MATCH (p:Person {id: row.id})
SET p.preCrimeRiskScore = row.risk,
    p.lastAnalyzed = datetime()
RETURN count(p) as nodesUpdated;

// 4. Identify High-Risk Clusters (For Visualization)
MATCH (p:Person)
WHERE p.preCrimeRiskScore > 0.8
WITH p
MATCH (p)-[:INTERACTS_WITH]-(associate)
WHERE associate.preCrimeRiskScore > 0.5
RETURN p, associate;
