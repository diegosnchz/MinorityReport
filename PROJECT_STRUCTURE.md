# MinorityReport Project Structure

## Overview

This project has been reorganized into a professional Python package structure for better maintainability and scalability.

## Directory Structure

```
MinorityReport/
├── src/                          # Source code package
│   ├── __init__.py              # Main package initialization
│   ├── models/                  # Neural network models
│   │   ├── __init__.py         
│   │   ├── oracle_net.py       # OracleNet (GCN + GAT)
│   │   ├── graphsage_model.py  # GraphSAGE implementations
│   │   └── models.py           # GAN models (Generator/Discriminator)
│   ├── training/                # Training scripts
│   │   ├── __init__.py
│   │   ├── train_oracle.py     # OracleNet training
│   │   ├── train_graphsage_minibatch.py  # GraphSAGE training
│   │   └── train.py            # GAN training
│   ├── utils/                   # Utility modules
│   │   ├── __init__.py
│   │   ├── device_utils.py     # GPU/CPU detection
│   │   ├── neo4j_oracle_integration.py  # Neo4j integration
│   │   └── benchmark_protocols.py       # Protocol benchmarking
│   └── protocols/               # Communication protocols
│       ├── __init__.py
│       ├── gossip_protocol.py  # Gossip protocol implementation
│       └── mesh_network.py     # Mesh network protocol
├── tests/                       # Test files
│   ├── __init__.py
│   └── test_graphsage.py
├── docs/                        # Documentation
│   ├── README_ORACLE.md
│   ├── GRAPHSAGE_README.md
│   ├── DOCKER_README.md
│   ├── QUICKSTART.md
│   └── architecture_design.md
├── config/                      # Configuration files
│   ├── requirements.txt
│   ├── requirements_cuda.txt
│   ├── neo4j_integration.cypher
│   └── setup_environment.ps1
├── data/                        # Data directory (graphs, datasets)
├── saved_models/                # Trained model checkpoints
│   └── oracle_net_best.pth
├── scripts/                     # Utility scripts
│   └── init-neo4j.sh
├── run_oracle_training.py       # Entry point for OracleNet training
├── run_graphsage_training.py    # Entry point for GraphSAGE training
├── Dockerfile                   # Docker configuration
└── docker-compose.yml           # Multi-service orchestration
```

## Usage

### Running Training Scripts

From the project root directory:

```powershell
# Train OracleNet
python run_oracle_training.py

# Train GraphSAGE
python run_graphsage_training.py
```

### Using as a Package

```python
# Import models
from src.models.oracle_net import OracleNet, create_oracle_net
from src.models.graphsage_model import GraphSAGEMiniBatch

# Import utilities
from src.utils.device_utils import get_device, print_device_info

# Import training functions
from src.training.train_oracle import train_oracle_net
```

### Docker Usage

```bash
# Build and run with docker-compose
docker-compose up --build

# Run specific service
docker-compose up oracle-net
```

## Key Changes

1. **Package Structure**: All source code is now in the `src/` directory with proper `__init__.py` files
2. **Import Paths**: All imports updated to use `src.` prefix (e.g., `from src.models.oracle_net import ...`)
3. **Entry Points**: Created `run_oracle_training.py` and `run_graphsage_training.py` for easy execution
4. **Docker Updates**: Updated Dockerfile and docker-compose.yml to work with new structure
5. **Clean Output**: Removed all emojis for Windows PowerShell compatibility

## Configuration

Set Python path if needed:

```powershell
# Windows PowerShell
$env:PYTHONPATH = "$PWD"

# Linux/Mac
export PYTHONPATH=$(pwd)
```

## Documentation

See the `docs/` folder for detailed documentation:
- [Oracle README](docs/README_ORACLE.md) - OracleNet model details
- [GraphSAGE README](docs/GRAPHSAGE_README.md) - GraphSAGE implementation
- [Docker README](docs/DOCKER_README.md) - Docker setup guide
- [Quick Start](docs/QUICKSTART.md) - Getting started guide
- [Architecture](docs/architecture_design.md) - System architecture

## Requirements

Install dependencies from the config folder:

```powershell
# CPU only
pip install -r config/requirements.txt

# GPU with CUDA 11.8
pip install -r config/requirements_cuda.txt
```
