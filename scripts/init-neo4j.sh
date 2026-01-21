#!/bin/bash
# Script de inicialización para Neo4j
# Este script se ejecuta cuando el contenedor de Neo4j inicia por primera vez

echo "🔮 Minority Report - Initializing Neo4j database..."

# Esperar a que Neo4j esté completamente iniciado
sleep 20

# Ejecutar queries de inicialización usando cypher-shell
# Nota: Este script asume que neo4j_integration.cypher está en /var/lib/neo4j/import/

if [ -f "/var/lib/neo4j/import/init.cypher" ]; then
    echo "📊 Creating initial graph structure..."
    
    # Ejecutar el archivo Cypher de inicialización
    cypher-shell -u neo4j -p minorityreport -f /var/lib/neo4j/import/init.cypher
    
    echo "✅ Neo4j initialization completed!"
else
    echo "⚠️  No init.cypher file found. Skipping initialization."
fi

# Crear datos de prueba para la ciudad
echo "🏙️  Creating sample city graph..."

cypher-shell -u neo4j -p minorityreport <<EOF
// Crear nodos de ubicación de muestra
CREATE (l1:Location {
    name: 'Downtown Plaza',
    policeLevel: 0.8,
    locationType: 0,
    illumination: 0.9,
    density: 0.7,
    latitude: 40.7128,
    longitude: -74.0060
})

CREATE (l2:Location {
    name: 'Back Alley 5th',
    policeLevel: 0.2,
    locationType: 1,
    illumination: 0.3,
    density: 0.4,
    latitude: 40.7138,
    longitude: -74.0050
})

CREATE (l3:Location {
    name: 'Metro Station',
    policeLevel: 0.6,
    locationType: 2,
    illumination: 0.8,
    density: 0.9,
    latitude: 40.7148,
    longitude: -74.0040
})

CREATE (l4:Location {
    name: 'Central Park',
    policeLevel: 0.3,
    locationType: 3,
    illumination: 0.5,
    density: 0.5,
    latitude: 40.7829,
    longitude: -73.9654
})

CREATE (l5:Location {
    name: 'Warehouse District',
    policeLevel: 0.4,
    locationType: 2,
    illumination: 0.4,
    density: 0.3,
    latitude: 40.7158,
    longitude: -74.0030
})

// Crear conexiones (calles)
MATCH (l1:Location {name: 'Downtown Plaza'}), (l2:Location {name: 'Back Alley 5th'})
CREATE (l1)-[:CONNECTED_TO {distance: 0.5, surveillanceLevel: 0.7}]->(l2)

MATCH (l2:Location {name: 'Back Alley 5th'}), (l3:Location {name: 'Metro Station'})
CREATE (l2)-[:CONNECTED_TO {distance: 0.3, surveillanceLevel: 0.4}]->(l3)

MATCH (l3:Location {name: 'Metro Station'}), (l4:Location {name: 'Central Park'})
CREATE (l3)-[:CONNECTED_TO {distance: 1.2, surveillanceLevel: 0.5}]->(l4)

MATCH (l4:Location {name: 'Central Park'}), (l5:Location {name: 'Warehouse District'})
CREATE (l4)-[:CONNECTED_TO {distance: 0.8, surveillanceLevel: 0.3}]->(l5)

MATCH (l1:Location {name: 'Downtown Plaza'}), (l3:Location {name: 'Metro Station'})
CREATE (l1)-[:CONNECTED_TO {distance: 0.6, surveillanceLevel: 0.8}]->(l3)

MATCH (l2:Location {name: 'Back Alley 5th'}), (l5:Location {name: 'Warehouse District'})
CREATE (l2)-[:CONNECTED_TO {distance: 0.9, surveillanceLevel: 0.2}]->(l5)

// Verificar creación
MATCH (n:Location) RETURN count(n) as totalLocations;
MATCH ()-[r:CONNECTED_TO]->() RETURN count(r) as totalConnections;
EOF

echo "✅ Sample city graph created!"
echo "🌐 Neo4j is ready at http://localhost:7474"
echo "🔐 Username: neo4j, Password: minorityreport"
