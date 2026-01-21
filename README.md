# MinorityReport - The Oracle's Escape Route Optimizer

[SUCCESS] AI-powered Graph Neural Network for optimal escape route prediction in urban surveillance networks.

## Quick Start

```powershell
# Clone and setup
git clone <repository-url>
cd MinorityReport

# Install dependencies
pip install -r config/requirements.txt

# Run training
python run_oracle_training.py
```

## Project Overview

MinorityReport implements advanced Graph Neural Networks to optimize escape routes in surveillance-heavy urban environments. The system uses:

- **OracleNet**: Custom GCN + GAT hybrid model for route optimization
- **GraphSAGE**: Scalable graph embeddings with mini-batch training
- **GAN Models**: Adversarial training for robustness
- **Neo4j Integration**: Real-time graph database connectivity
- **Distributed Protocols**: Gossip and Mesh network synchronization

## Architecture

The project follows a modular Python package structure:

```
MinorityReport/
├── src/                 # Source code
│   ├── models/         # Neural network models
│   ├── training/       # Training scripts
│   ├── utils/          # Utility functions
│   └── protocols/      # Communication protocols
├── tests/              # Unit tests
├── docs/               # Documentation
├── config/             # Configuration files
├── data/               # Training data
└── saved_models/       # Model checkpoints
```

See [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md) for detailed structure documentation.

## Usage

### Training Models

```powershell
# Train OracleNet (GCN + GAT hybrid)
python run_oracle_training.py

# Train GraphSAGE model
python run_graphsage_training.py
```

### Using as a Package

```python
from src.models.oracle_net import create_oracle_net
from src.utils.device_utils import get_device

# Create model
device = get_device()
model = create_oracle_net(num_features=16, device=device)

# Train
from src.training.train_oracle import train_oracle_net
model, history = train_oracle_net(num_epochs=50)
```

### Docker Deployment

```bash
# Start all services (Neo4j + OracleNet)
docker-compose up --build

# Start only OracleNet training
docker-compose up oracle-net

# Start only Neo4j database
docker-compose up neo4j
```

## Requirements

### Software Requirements
- Python 3.11+
- PyTorch 2.0.1+ (CUDA 11.8 for GPU)
- torch-geometric 2.7.0+
- Neo4j 5.15+ (optional, for production)

### Hardware Requirements
- **Minimum**: CPU with 4GB RAM
- **Recommended**: NVIDIA GPU with 6GB+ VRAM
- **GPU Support**: CUDA 11.8 compatible GPU

### Installation

```powershell
# CPU version
pip install -r config/requirements.txt

# GPU version (CUDA 11.8)
pip install -r config/requirements_cuda.txt
```

## Model Performance

### OracleNet (GCN + GAT Hybrid)
- **Parameters**: 18,401
- **Architecture**: 
  - GCN Layer 1: 16 → 32 features
  - GCN Layer 2: 32 → 16 features  
  - GAT Layer: 16 → 8 features (4 heads)
- **Training Speed**: ~2-3 sec/epoch (GPU) | ~5-8 sec/epoch (CPU)
- **Use Case**: Small to medium graphs (<10,000 nodes)

### GraphSAGE
- **Parameters**: Configurable
- **Aggregators**: Mean, LSTM, Pooling
- **Training**: Mini-batch with neighbor sampling
- **Use Case**: Large graphs (100,000+ nodes)

## Features

### [SUCCESS] Core Features
- **Multi-Model Support**: OracleNet, GraphSAGE, GAN
- **Auto Device Detection**: Automatic GPU/CPU selection
- **Mini-batch Training**: Scalable to large graphs
- **Neighbor Sampling**: Memory-efficient for massive graphs
- **Attention Mechanisms**: GAT for important edge detection
- **Adversarial Training**: GAN for robustness

### [Building] Advanced Features
- **Neo4j Integration**: Real-time graph database connectivity
- **Distributed Training**: Gossip and Mesh protocols
- **Protocol Benchmarking**: Performance comparison tools
- **Docker Support**: Full containerization with GPU support

## Documentation

- [Oracle README](docs/README_ORACLE.md) - OracleNet architecture and training
- [GraphSAGE Guide](docs/GRAPHSAGE_README.md) - GraphSAGE implementation details
- [Docker Guide](docs/DOCKER_README.md) - Container deployment
- [Quick Start](docs/QUICKSTART.md) - Getting started tutorial
- [Architecture Design](docs/architecture_design.md) - System architecture
- [Project Structure](PROJECT_STRUCTURE.md) - Code organization

## Development

### Running Tests

```powershell
# Run all tests
python -m pytest tests/

# Run specific test
python tests/test_graphsage.py
```

### Project Configuration

The project uses environment variables for configuration:

```powershell
# Set Python path
$env:PYTHONPATH = "$PWD"

# Neo4j configuration (optional)
$env:NEO4J_URI = "bolt://localhost:7687"
$env:NEO4J_USER = "neo4j"
$env:NEO4J_PASSWORD = "minorityreport"
```

### Code Style

- Type hints for all functions
- Docstrings for all modules and classes
- No emojis in output (Windows PowerShell compatibility)
- Text-based status indicators: `[SUCCESS]`, `[WARNING]`, `[Building]`

## Troubleshooting

### Import Errors

If you get import errors, set the PYTHONPATH:

```powershell
# Windows PowerShell
$env:PYTHONPATH = "c:\path\to\MinorityReport"

# Or add to scripts
cd c:\path\to\MinorityReport
python run_oracle_training.py
```

### GPU Issues

```python
# Check GPU availability
from src.utils.device_utils import print_device_info
print_device_info()
```

### Docker Issues

```bash
# Check logs
docker-compose logs oracle-net

# Rebuild containers
docker-compose down
docker-compose up --build
```

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make changes with type hints and docstrings
4. Test your changes
5. Submit a pull request

## License

[Specify your license here]

## Authors

**The Oracle Team**
- OracleNet Architecture
- GraphSAGE Implementation  
- Distributed Protocol Design

## Acknowledgments

- PyTorch Geometric team for the amazing GNN library
- Hamilton et al. for the GraphSAGE paper
- Neo4j for graph database capabilities

## Citation

```bibtex
@software{minorityreport2024,
  title={MinorityReport: Neural Networks for Escape Route Optimization},
  author={The Oracle Team},
  year={2024},
  url={https://github.com/yourusername/MinorityReport}
}
```

---

[SUCCESS] Built with PyTorch, torch-geometric, and determination to outsmart surveillance systems.
