# Dockerfile para OracleNet - The Oracle's Escape Route Optimizer
# Versión GPU-enabled con CUDA 11.8
FROM nvidia/cuda:11.8.0-cudnn8-runtime-ubuntu22.04

# Metadata
LABEL maintainer="The Oracle <oracle@minorityreport.ai>"
LABEL description="OracleNet: GCN+GAT model for robber's escape route optimization with GPU support"

# Evitar prompts durante instalación
ENV DEBIAN_FRONTEND=noninteractive

# Establecer directorio de trabajo
WORKDIR /app

# Instalar Python 3.11 y dependencias del sistema
RUN apt-get update && apt-get install -y \
    software-properties-common \
    && add-apt-repository ppa:deadsnakes/ppa \
    && apt-get update && apt-get install -y \
    python3.11 \
    python3.11-venv \
    python3.11-dev \
    python3-pip \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Crear symlink para python
RUN update-alternatives --install /usr/bin/python python /usr/bin/python3.11 1
RUN update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.11 1

# Actualizar pip
RUN python -m pip install --upgrade pip

# Copiar requirements primero para aprovechar cache de Docker
COPY config/requirements.txt .
COPY config/requirements_cuda.txt .

# Instalar PyTorch con CUDA 11.8
RUN pip install --no-cache-dir torch==2.0.1 torchvision==0.15.2 torchaudio==0.2.0 \
    --index-url https://download.pytorch.org/whl/cu118

# Instalar PyTorch Geometric y extensiones
RUN pip install --no-cache-dir torch-geometric
RUN pip install --no-cache-dir torch-scatter torch-sparse \
    -f https://data.pyg.org/whl/torch-2.0.1+cu118.html

# Instalar dependencias restantes
RUN pip install --no-cache-dir neo4j networkx numpy pandas matplotlib seaborn tqdm

# Copiar código fuente con la nueva estructura
COPY src/ ./src/
COPY run_oracle_training.py .
COPY run_graphsage_training.py .
COPY docs/ ./docs/

# Crear directorio para modelos entrenados
RUN mkdir -p /app/saved_models

# Variables de entorno
ENV PYTHONUNBUFFERED=1
ENV NEO4J_URI=bolt://neo4j:7687
ENV NEO4J_USER=neo4j
ENV NEO4J_PASSWORD=minorityreport
ENV PYTHONPATH=/app

# Puerto para API (si se implementa en el futuro)
EXPOSE 8080

# Comando por defecto: entrenar OracleNet
CMD ["python", "run_oracle_training.py"]
