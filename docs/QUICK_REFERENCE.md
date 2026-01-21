# 🎯 MinorityReport - Quick Reference Card

**Keep this handy for common tasks!**

---

## 🚀 Essential Commands

### Activate Environment
```powershell
cd c:\Users\Techie3\Documents\GitHub\MinorityReport
.\venv311\Scripts\Activate.ps1
```

### Run Smoke Test
```powershell
python oracle_net.py
```
✅ Output: "OracleNet initialized successfully!"

### Train Model
```powershell
python train_oracle.py
```
✅ Expected: ~2 minutes, 69.67% final accuracy

### Check Device Status
```powershell
python -c "from device_utils import print_device_info; print_device_info()"
```

### Run All Tests
```powershell
python oracle_net.py
python train_oracle.py
python test_graphsage.py
```

---

## 📚 Documentation Quick Links

| Need | Document | Time |
|------|----------|------|
| Get Started | [QUICKSTART.md](QUICKSTART.md) | 5 min |
| Model Details | [README_ORACLE.md](README_ORACLE.md) | 30 min |
| GPU/CPU Help | [DEVICE_GUIDE.md](DEVICE_GUIDE.md) | 10 min |
| Deployment | [DEPLOYMENT.md](DEPLOYMENT.md) | 15 min |
| Docker | [DOCKER_README.md](DOCKER_README.md) | 15 min |
| Status | [DEPLOYMENT_STATUS.md](DEPLOYMENT_STATUS.md) | 15 min |
| All Docs | [INDEX.md](INDEX.md) | 5 min (index) |

---

## 🔧 Common Tasks

### Force CPU (for debugging)
```powershell
$env:FORCE_CPU = 'true'
python oracle_net.py
```

### Use UTF-8 Encoding (Windows emoji support)
```powershell
$env:PYTHONIOENCODING = 'utf-8'
python train_oracle.py
```

### Install New Dependency
```powershell
.\venv311\Scripts\pip install package-name
```

### List Installed Packages
```powershell
.\venv311\Scripts\pip list
```

### Verify PyTorch Installation
```powershell
python -c "import torch; print(f'PyTorch: {torch.__version__}'); print(f'CUDA: {torch.cuda.is_available()}')"
```

---

## 🐛 Troubleshooting

### "Module not found" Error
```powershell
# Ensure environment is activated
.\venv311\Scripts\Activate.ps1

# Verify you're in the right directory
cd c:\Users\Techie3\Documents\GitHub\MinorityReport

# Run the command again
python oracle_net.py
```

### Training is Very Slow
```powershell
# Check if using CPU (normal for this hardware)
python -c "from device_utils import get_device; print(get_device())"

# If CPU: training takes ~2 min for 200 epochs (expected)
# Upgrade GPU hardware for faster training
```

### GPU Not Detected
```powershell
# Check NVIDIA drivers
nvidia-smi

# Update drivers if needed from nvidia.com
# Note: Current GPU (Quadro K4200) incompatible with PyTorch 2.0+
# Will use CPU fallback (automatic)
```

### Import Error "No module named 'device_utils'"
```powershell
# Verify file exists
dir device_utils.py

# Check you're in correct directory
pwd  # Should show: ...\MinorityReport

# Re-activate environment
.\venv311\Scripts\Activate.ps1
```

---

## 📊 Performance Reference

| Task | Time | Notes |
|------|------|-------|
| Smoke test (oracle_net.py) | ~1 sec | Full model initialization |
| Training 200 epochs | ~2 min | CPU, 50 graphs/epoch |
| GraphSAGE training | ~5 min | Larger graphs, mini-batch |
| Device detection | <100ms | Automatic |

---

## 🎓 Learning Path

### 5 Minutes
1. Activate environment
2. Run `python oracle_net.py`
3. See "OracleNet initialized successfully!"

### 15 Minutes
1. Read [QUICKSTART.md](QUICKSTART.md)
2. Run `python train_oracle.py`
3. Watch training progress (200 epochs)

### 30 Minutes
1. Read [README_ORACLE.md](README_ORACLE.md)
2. Understand OracleNet architecture
3. Review training results

### 1 Hour
1. Read [architecture_design.md](architecture_design.md)
2. Explore code in `oracle_net.py`
3. Try modifying hyperparameters

### 2 Hours
1. Read [DEVICE_GUIDE.md](DEVICE_GUIDE.md)
2. Understand GPU/CPU selection
3. Learn Docker deployment ([DOCKER_README.md](DOCKER_README.md))

---

## 🔑 Key Files

### Essential
- `oracle_net.py` - Main OracleNet model
- `train_oracle.py` - Training script
- `device_utils.py` - GPU/CPU management
- `requirements.txt` - Dependencies

### Important
- `graphsage_model.py` - Graph embeddings
- `models.py` - GAN for police simulation
- `train.py` - GAN training

### Configuration
- `Dockerfile` - Container image
- `docker-compose.yml` - Multi-service setup
- `neo4j_integration.cypher` - Database queries

---

## 💡 Tips & Tricks

### Faster Iteration
```powershell
# During development, skip full training
# Modify train_oracle.py:
#   num_epochs = 10  # Instead of 200
#   num_graphs_per_epoch = 10  # Instead of 50

python train_oracle.py  # Runs in ~5 seconds
```

### Save Memory
```powershell
# Force CPU if GPU memory issues
$env:FORCE_CPU = 'true'
python train_oracle.py
```

### Performance Tuning
```powershell
# Benchmark your system
python benchmark_protocols.py

# See performance metrics
# Useful for understanding training speed
```

### Debug Information
```python
# In your code, add:
from device_utils import get_device, get_device_info

device = get_device()
info = get_device_info()
print(f"Device: {info['device_name']}")
print(f"GPU: {info['is_gpu']}")
```

---

## ❓ FAQ

**Q: Will it use my GPU?**  
A: Yes, automatically if available. Current system uses CPU (Quadro K4200 incompatible with PyTorch 2.0+). Will switch to GPU if hardware upgraded (no code changes needed).

**Q: How long does training take?**  
A: ~2 minutes for 200 epochs on CPU. Will be ~30-60 seconds on a modern GPU.

**Q: Can I use a different Python version?**  
A: Not recommended. Python 3.11 has best PyTorch support. Python 3.14 lacks CUDA wheels.

**Q: How do I update dependencies?**  
A: Run `.\venv311\Scripts\pip install --upgrade package-name`

**Q: What's the minimum RAM needed?**  
A: 8 GB is comfortable. 4 GB minimum for basic usage.

**Q: Can I run this on Mac/Linux?**  
A: Yes! The code is platform-independent. Follow same setup steps (adjust paths).

---

## 🚨 When Something Goes Wrong

### Step 1: Check Environment
```powershell
.\venv311\Scripts\Activate.ps1
python --version  # Should be 3.11.x
```

### Step 2: Check Installation
```powershell
python -c "import torch; print(torch.__version__)"
python -c "import torch_geometric; print('OK')"
```

### Step 3: Run Diagnostics
```powershell
python device_utils.py
```

### Step 4: Check Documentation
- GPU/CPU issues → [DEVICE_GUIDE.md](DEVICE_GUIDE.md)
- Model issues → [README_ORACLE.md](README_ORACLE.md)
- Deployment issues → [DEPLOYMENT.md](DEPLOYMENT.md)
- General → [DEPLOYMENT_STATUS.md](DEPLOYMENT_STATUS.md)

### Step 5: Nuclear Option (Last Resort)
```powershell
# Recreate environment from scratch
rmdir venv311 -Force -Recurse
py -3.11 -m venv venv311
.\venv311\Scripts\Activate.ps1
pip install -r requirements.txt
```

---

## ✅ Verification Checklist

Run this to verify everything works:

```powershell
# 1. Activate
.\venv311\Scripts\Activate.ps1

# 2. Check Python
python --version

# 3. Check PyTorch
python -c "import torch; print(f'PyTorch {torch.__version__}')"

# 4. Check device
python device_utils.py

# 5. Run smoke test
python oracle_net.py

# 6. All good if you see: "OracleNet initialized successfully!"
```

---

## 📞 Documentation Hub

```
Need help?

Quick Start        → QUICKSTART.md
Model Details      → README_ORACLE.md
GPU/CPU Issues     → DEVICE_GUIDE.md
Deployment         → DEPLOYMENT.md
System Status      → DEPLOYMENT_STATUS.md
All Documents      → INDEX.md
Verification       → FINAL_VERIFICATION.md
```

---

## 🎉 Ready to Go!

```
✅ Environment: Ready
✅ Models: Ready
✅ Documentation: Ready
✅ Testing: Passed

You're all set! Pick a task and start coding.
```

---

**Last Updated**: December 2024  
**Version**: 1.0  
**Status**: ✅ OPERATIONAL

*Print this page or save it for quick reference!*
