# 🧠 Training Workflow Guide

## Overview

This guide explains how to train AI models using data from the **dataEngineer** branch, with support for both **GPU training** and **CPU inference** in production.

---

## 🎯 Training Objectives

### 1. **Risk Prediction** (Primary)
**What it predicts:** Individual citizen risk scores (0-1)

**Training data from dataEngineer:**
- Citizen features: age, job, criminal_degree
- Social network: KNOWS relationships
- Target: risk_seed (latent risk variable)

**Use case:** Predict which citizens are likely to commit crimes

**Backend integration:** Used by Backend AI oracle to assess danger levels

---

### 2. **Movement Prediction** (Secondary)
**What it predicts:** Next location a citizen will visit

**Training data from dataEngineer:**
- Citizen features + current location
- Location features: env_risk, type, coordinates
- Historical patterns: VISITED relationships

**Use case:** Predict escape routes and safe zones

**Backend integration:** Powers the escape route calculator

---

### 3. **Behavior Pattern Analysis** (Future)
**What it predicts:** Temporal patterns in criminal activity

**Use case:** Predict when and where crimes are likely to occur

---

## 🖥️ GPU vs CPU Strategy

### **Training Phase: GPU**
```
┌─────────────────┐
│   GPU Training  │  ← Fast training on large datasets
│   (CUDA)        │  ← Parallel computation
│                 │  ← Multiple attention heads
└────────┬────────┘
         │
         │ Export
         ▼
┌─────────────────┐
│  TorchScript    │  ← Optimized model
│  (.pt file)     │  ← CPU-friendly
└─────────────────┘
```

### **Inference Phase: CPU**
```
┌─────────────────┐
│  Backend API    │  ← FastAPI service
│  (CPU)          │  ← Lightweight inference
│                 │  ← Loaded TorchScript model
└────────┬────────┘
         │
         │ Predictions
         ▼
┌─────────────────┐
│  Frontend       │  ← Real-time updates
│  WebSocket      │  ← Escape routes
└─────────────────┘
```

**Why this approach?**
- ✅ GPU: Fast training (hours → minutes)
- ✅ CPU: Cheap deployment (no GPU servers needed)
- ✅ TorchScript: Optimized for CPU inference
- ✅ Small model size: Fast loading in Backend

---

## 🚀 Quick Start

### Step 1: Export Data from dataEngineer
```bash
# Set up Neo4j credentials
export NEO4J_URI="bolt://localhost:7687"
export NEO4J_USER="neo4j"
export NEO4J_PASSWORD="your_password"

# Export data to files
python scripts/export_data_from_neo4j.py --output data/
```

### Step 2: Train on GPU
```bash
# Train risk prediction model on GPU
python src/training/train_gat_enhanced.py \
    --data data/ \
    --gpu \
    --epochs 200 \
    --hidden 128 \
    --heads 8 \
    --export models/risk_model_production.pt
```

**Output:**
- ✅ Trained model checkpoints in `checkpoints/`
- ✅ Production-ready model in `models/risk_model_production.pt`
- ✅ Training logs in `logs/`
- ✅ Optimized for CPU inference

### Step 3: Use in Backend (CPU)
```python
# In Backend/ai_interface.py
import torch

# Load production model (CPU)
model = torch.jit.load('models/risk_model_production.pt', map_location='cpu')
model.eval()

# Make predictions
with torch.no_grad():
    risk_scores = model(citizen_features, social_network_edges)
```

---

## 📊 Training Data Flow

```
dataEngineer Branch (Neo4j)
├── Citizens (1000 nodes)
│   ├── age, job, born
│   ├── criminal_degree (calculated)
│   └── risk_seed (target)
├── Locations (50 nodes)
│   ├── type, coordinates
│   └── env_risk
└── Relationships
    ├── KNOWS (social network)
    ├── COMMITTED_CRIME
    └── VISITED

         │ Export
         ▼

Data Files (data/)
├── citizens.csv
├── features.csv
├── edges.csv
├── graph_data.pt
└── metadata.txt

         │ Load
         ▼

PyTorch Geometric
├── x: [1000, N] features
├── edge_index: [2, M] graph
└── y: [1000, 1] labels

         │ Train
         ▼

GAT Model (GPU)
├── 2 GAT layers
├── 4-8 attention heads
└── Risk prediction head

         │ Export
         ▼

Production Model (CPU)
├── TorchScript format
├── CPU-optimized
└── Ready for Backend
```

---

## 🎓 Training Examples

### Example 1: Quick Training (CPU)
```bash
# Fast test on CPU
python src/training/train_gat_enhanced.py \
    --data data/ \
    --cpu \
    --epochs 50 \
    --hidden 32 \
    --heads 2
```

### Example 2: Full Training (GPU)
```bash
# Full training on GPU with export
python src/training/train_gat_enhanced.py \
    --data data/ \
    --gpu \
    --epochs 300 \
    --hidden 128 \
    --heads 8 \
    --lr 0.01 \
    --export models/risk_model_v1.pt
```

### Example 3: Live Training (No Export)
```bash
# Train directly from Neo4j
python src/training/train_gat_enhanced.py \
    --live \
    --gpu \
    --epochs 200
```

---

## 🔧 Model Architecture

### Risk Prediction GAT
```
Input: Citizen Features [1000, 16]
         │
         ▼
    ┌─────────────┐
    │  GAT Layer 1│  ← 4 attention heads
    │  (64 hidden)│  ← Learns neighbor importance
    └──────┬──────┘
         │ ELU
         ▼
    ┌─────────────┐
    │  GAT Layer 2│  ← Single head
    │  (1 output) │  ← Risk score
    └──────┬──────┘
         │ Sigmoid
         ▼
Output: Risk Scores [1000, 1]
```

**Key Features:**
- **Attention Mechanism:** Learns which neighbors matter most
- **Graph Awareness:** Uses social network structure
- **Dropout:** Prevents overfitting (0.6)
- **Small Size:** ~200KB model file

---

## 📈 Monitoring Training

### Training Logs
```
Epoch   1 | train_loss: 0.245612 | train_mae: 0.378421 | eval_loss: 0.234567 | eval_mae: 0.367891 |
Epoch  10 | train_loss: 0.156789 | train_mae: 0.289012 | eval_loss: 0.145678 | eval_mae: 0.276543 |
Epoch  20 | train_loss: 0.098765 | train_mae: 0.198765 | eval_loss: 0.089012 | eval_mae: 0.187654 |
```

### Checkpoints
- `checkpoints/gat_risk_model_latest.pt` - Latest epoch
- `checkpoints/gat_risk_model_best.pt` - Best validation loss
- `logs/training_history.json` - Full history

---

## 🔌 Backend Integration

### Loading the Model
```python
# Backend/ai_interface.py
import torch
import asyncio

class AIOracle:
    def __init__(self):
        # Load CPU-optimized model
        self.model = torch.jit.load(
            'models/risk_model_production.pt',
            map_location='cpu'
        )
        self.model.eval()
    
    async def predict_risk(self, citizen_features, social_network):
        """Predict risk scores for citizens."""
        # Run on CPU in thread pool (non-blocking)
        return await asyncio.to_thread(
            self._predict_sync,
            citizen_features,
            social_network
        )
    
    def _predict_sync(self, features, edges):
        with torch.no_grad():
            scores = self.model(features, edges)
        return scores.numpy()
```

### API Endpoint
```python
# Backend/main.py
@app.get("/predict/risk/{citizen_id}")
async def predict_citizen_risk(citizen_id: str):
    # Get citizen data from Neo4j
    features, network = db.get_citizen_graph(citizen_id)
    
    # Predict with AI
    risk_score = await ai_oracle.predict_risk(features, network)
    
    return {
        "citizen_id": citizen_id,
        "risk_score": float(risk_score),
        "timestamp": datetime.now()
    }
```

---

## 🎯 Training Best Practices

### 1. **Data Quality**
- ✅ Ensure Neo4j has data (run init_city_graph.py)
- ✅ Check for missing features
- ✅ Verify edge connectivity

### 2. **Hyperparameters**
- **Hidden size:** 64-128 for risk prediction
- **Attention heads:** 4-8 (more = better but slower)
- **Learning rate:** 0.005-0.01
- **Epochs:** 100-300 depending on data size

### 3. **GPU Memory**
- Monitor with `nvidia-smi`
- Reduce batch size if OOM
- Reduce hidden channels if needed

### 4. **Export for Production**
- Always use `--export` flag
- Test exported model on CPU before deployment
- Verify model size (<10MB ideal)

---

## 🐛 Troubleshooting

### "GPU not available"
```bash
# Check CUDA
python -c "import torch; print(torch.cuda.is_available())"

# Use CPU if GPU not available
python src/training/train_gat_enhanced.py --cpu --data data/
```

### "No data found"
```bash
# Export data first
python scripts/export_data_from_neo4j.py --output data/

# Verify data exists
ls -lh data/
```

### "Model too large"
```python
# Reduce model size
python src/training/train_gat_enhanced.py \
    --hidden 32 \    # Smaller hidden size
    --heads 2 \      # Fewer attention heads
    --export models/small_model.pt
```

---

## 📚 Next Steps

1. ✅ Train risk prediction model
2. ⏳ Add validation/test splits
3. ⏳ Implement movement prediction training
4. ⏳ Create evaluation metrics
5. ⏳ Deploy to Backend
6. ⏳ Integrate with Frontend

---

## 🔗 Related Files

- `src/models/risk_prediction.py` - GAT model definitions
- `src/models/movement_prediction.py` - Movement models
- `src/utils/device_manager.py` - GPU/CPU utilities
- `src/training/train_gat_enhanced.py` - Main training script
- `scripts/export_data_from_neo4j.py` - Data export
- `src/utils/data_loader.py` - Data loading

---

## 💡 Key Takeaways

1. **Train on GPU** → Fast, efficient training
2. **Export to TorchScript** → CPU-optimized model
3. **Use in Backend on CPU** → Cheap, scalable inference
4. **Small models** → Fast loading, low latency
5. **dataEngineer data** → Realistic training data

**This workflow ensures models trained on GPU can run efficiently on CPU in production!**
