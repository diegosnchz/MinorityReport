# Dockerfile para OracleNet - The Oracle's Escape Route Optimizer
FROM python:3.11-slim

# Metadata
LABEL maintainer="The Oracle <oracle@minorityreport.ai>"
LABEL description="OracleNet: GCN+GAT model for robber's escape route optimization"

# Establecer directorio de trabajo
WORKDIR /app

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements primero para aprovechar cache de Docker
COPY requirements.txt .

# Instalar dependencias de Python
RUN pip install --no-cache-dir -r requirements.txt

# Instalar driver de Neo4j
RUN pip install --no-cache-dir neo4j

# Copiar código fuente
COPY oracle_net.py .
COPY train_oracle.py .
COPY neo4j_oracle_integration.py .
COPY models.py .
COPY train.py .
COPY gossip_protocol.py .
COPY mesh_network.py .
COPY benchmark_protocols.py .
COPY architecture_design.md .
COPY README_ORACLE.md .

# Crear directorio para modelos entrenados
RUN mkdir -p /app/models

# Variables de entorno
ENV PYTHONUNBUFFERED=1
ENV NEO4J_URI=bolt://neo4j:7687
ENV NEO4J_USER=neo4j
ENV NEO4J_PASSWORD=minorityreport

# Puerto para API (si se implementa en el futuro)
EXPOSE 8080

# Comando por defecto: smoke test
CMD ["python", "oracle_net.py"]
