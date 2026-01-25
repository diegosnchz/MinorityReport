"""
GPU/CPU Training Utilities

Provides automatic GPU detection and fallback to CPU,
plus utilities for exporting models for production use.

Key Features:
- Automatic device selection
- Model checkpointing
- Export to TorchScript for CPU inference
- Training progress tracking
"""

import torch
import os
from datetime import datetime
from pathlib import Path


def get_device(prefer_gpu=True, verbose=True):
    """
    Automatically detect and return the best available device.
    
    Args:
        prefer_gpu: Whether to prefer GPU if available
        verbose: Print device information
    
    Returns:
        torch.device
    """
    if prefer_gpu and torch.cuda.is_available():
        device = torch.device('cuda')
        if verbose:
            print(f"🖥️  Using GPU: {torch.cuda.get_device_name(0)}")
            print(f"    Memory: {torch.cuda.get_device_properties(0).total_memory / 1e9:.2f} GB")
    else:
        device = torch.device('cpu')
        if verbose:
            if prefer_gpu:
                print("⚠️  GPU not available, using CPU")
            else:
                print("🖥️  Using CPU (as requested)")
    
    return device


def get_device_info():
    """
    Get detailed device information.
    
    Returns:
        Dictionary with device info
    """
    info = {
        'cuda_available': torch.cuda.is_available(),
        'device_count': torch.cuda.device_count() if torch.cuda.is_available() else 0,
        'current_device': None,
        'device_name': None,
        'memory_gb': None
    }
    
    if torch.cuda.is_available():
        info['current_device'] = torch.cuda.current_device()
        info['device_name'] = torch.cuda.get_device_name(0)
        info['memory_gb'] = torch.cuda.get_device_properties(0).total_memory / 1e9
    
    return info


def move_to_device(data, device):
    """
    Move PyTorch Geometric Data to device.
    
    Args:
        data: PyTorch Geometric Data object
        device: Target device
    
    Returns:
        Data on target device
    """
    data.x = data.x.to(device)
    data.edge_index = data.edge_index.to(device)
    if hasattr(data, 'y') and data.y is not None:
        data.y = data.y.to(device)
    if hasattr(data, 'batch') and data.batch is not None:
        data.batch = data.batch.to(device)
    
    return data


class ModelCheckpoint:
    """
    Save model checkpoints during training.
    
    Automatically saves:
    - Best model (based on metric)
    - Latest model
    - Training metadata
    """
    
    def __init__(self, save_dir, model_name='model', monitor='loss', mode='min'):
        """
        Args:
            save_dir: Directory to save checkpoints
            model_name: Base name for saved models
            monitor: Metric to monitor ('loss' or 'accuracy')
            mode: 'min' (lower is better) or 'max' (higher is better)
        """
        self.save_dir = Path(save_dir)
        self.save_dir.mkdir(parents=True, exist_ok=True)
        
        self.model_name = model_name
        self.monitor = monitor
        self.mode = mode
        
        self.best_value = float('inf') if mode == 'min' else float('-inf')
        self.best_epoch = 0
    
    def is_better(self, value):
        """Check if current value is better than best."""
        if self.mode == 'min':
            return value < self.best_value
        else:
            return value > self.best_value
    
    def save(self, model, optimizer, epoch, metrics):
        """
        Save checkpoint.
        
        Args:
            model: PyTorch model
            optimizer: Optimizer
            epoch: Current epoch
            metrics: Dictionary of metrics
        """
        # Always save latest
        latest_path = self.save_dir / f"{self.model_name}_latest.pt"
        torch.save({
            'epoch': epoch,
            'model_state_dict': model.state_dict(),
            'optimizer_state_dict': optimizer.state_dict(),
            'metrics': metrics
        }, latest_path)
        
        # Check if this is the best model
        current_value = metrics.get(self.monitor)
        if current_value is not None and self.is_better(current_value):
            self.best_value = current_value
            self.best_epoch = epoch
            
            best_path = self.save_dir / f"{self.model_name}_best.pt"
            torch.save({
                'epoch': epoch,
                'model_state_dict': model.state_dict(),
                'optimizer_state_dict': optimizer.state_dict(),
                'metrics': metrics,
                'best_value': self.best_value
            }, best_path)
            
            print(f"💾 New best model saved! {self.monitor}={self.best_value:.6f} at epoch {epoch}")
    
    def load_best(self, model, optimizer=None):
        """Load the best saved model."""
        best_path = self.save_dir / f"{self.model_name}_best.pt"
        if not best_path.exists():
            raise FileNotFoundError(f"No best model found at {best_path}")
        
        checkpoint = torch.load(best_path)
        model.load_state_dict(checkpoint['model_state_dict'])
        
        if optimizer is not None:
            optimizer.load_state_dict(checkpoint['optimizer_state_dict'])
        
        print(f"✅ Loaded best model from epoch {checkpoint['epoch']}")
        return checkpoint


def export_for_production(model, example_data, save_path, 
                          optimize_for_cpu=True, verbose=True):
    """
    Export model for production use (Backend integration).
    
    Converts to TorchScript and optimizes for CPU inference.
    
    Args:
        model: Trained PyTorch model
        example_data: Example (x, edge_index) for tracing
        save_path: Where to save the exported model
        optimize_for_cpu: Whether to optimize for CPU
        verbose: Print progress
    
    Returns:
        Path to saved model
    """
    if verbose:
        print(f"📦 Exporting model for production...")
    
    # Set to eval mode and move to CPU
    model.eval()
    if optimize_for_cpu:
        model.cpu()
    
    # Unpack example data
    if isinstance(example_data, tuple):
        x, edge_index = example_data
    else:
        x = example_data.x
        edge_index = example_data.edge_index
    
    # Move example data to CPU if optimizing for CPU
    if optimize_for_cpu:
        x = x.cpu()
        edge_index = edge_index.cpu()
    
    # Trace the model
    try:
        traced_model = torch.jit.trace(model, (x, edge_index))
        
        # Optimize for inference
        if optimize_for_cpu:
            traced_model = torch.jit.optimize_for_inference(traced_model)
        
        # Save
        save_path = Path(save_path)
        save_path.parent.mkdir(parents=True, exist_ok=True)
        torch.jit.save(traced_model, str(save_path))
        
        if verbose:
            print(f"✅ Model exported to {save_path}")
            if optimize_for_cpu:
                print("   Optimized for CPU inference")
            
            # Get model size
            size_mb = save_path.stat().st_size / (1024 * 1024)
            print(f"   Model size: {size_mb:.2f} MB")
        
        return save_path
    
    except Exception as e:
        print(f"❌ Export failed: {e}")
        raise


def load_production_model(model_path, device='cpu'):
    """
    Load a production model (TorchScript).
    
    Args:
        model_path: Path to the exported model
        device: Device to load model on
    
    Returns:
        Loaded model
    """
    model = torch.jit.load(model_path, map_location=device)
    model.eval()
    return model


class TrainingLogger:
    """
    Log training progress and metrics.
    """
    
    def __init__(self, log_dir='logs'):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        self.log_file = self.log_dir / f"training_{timestamp}.log"
        
        self.history = {
            'train_loss': [],
            'val_loss': [],
            'train_acc': [],
            'val_acc': [],
            'epochs': []
        }
    
    def log(self, epoch, metrics, print_console=True):
        """
        Log metrics for an epoch.
        
        Args:
            epoch: Current epoch number
            metrics: Dictionary of metrics
            print_console: Whether to print to console
        """
        # Update history
        self.history['epochs'].append(epoch)
        for key, value in metrics.items():
            if key not in self.history:
                self.history[key] = []
            self.history[key].append(value)
        
        # Format log message
        msg = f"Epoch {epoch:3d} |"
        for key, value in metrics.items():
            msg += f" {key}: {value:.6f} |"
        
        # Write to file
        with open(self.log_file, 'a') as f:
            f.write(msg + '\n')
        
        # Print to console
        if print_console:
            print(msg)
    
    def save_history(self, save_path=None):
        """Save training history to file."""
        if save_path is None:
            save_path = self.log_dir / "training_history.json"
        
        import json
        with open(save_path, 'w') as f:
            json.dump(self.history, f, indent=2)
        
        print(f"💾 Training history saved to {save_path}")


if __name__ == "__main__":
    # Test device detection
    print("Testing Device Utilities...")
    print("=" * 60)
    
    device = get_device()
    print(f"\nSelected device: {device}")
    
    info = get_device_info()
    print(f"\nDevice info:")
    for key, value in info.items():
        print(f"  {key}: {value}")
    
    print("\n✅ Device utilities test passed!")
