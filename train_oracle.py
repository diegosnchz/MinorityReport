"""
Training script for OracleNet - The Oracle's Escape Route Optimizer

Este script entrena el modelo OracleNet para predecir rutas de escape seguras
en una ciudad vigilada por policía predictiva.

Estrategia de Entrenamiento:
1. Datos sintéticos: Grafos de ciudad con niveles de peligro variables
2. Labels: Rutas conocidas como seguras/peligrosas basadas en vigilancia
3. Loss: Combinación de BCE (clasificación de aristas) y regularización
4. GPU: Optimizado para NVIDIA Quadro K4200 4GB

Author: The Oracle
"""

import torch
import torch.nn.functional as F
import torch.optim as optim
from torch_geometric.data import Data, DataLoader
from oracle_net import OracleNet, create_oracle_net
from typing import List, Tuple, Optional
import numpy as np
import time


def generate_synthetic_city_graph(
    num_nodes: int = 100,
    num_edges: int = 300,
    num_features: int = 16,
    danger_level: float = 0.5
) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
    """
    Genera un grafo sintético que simula una ciudad.
    
    Args:
        num_nodes: Número de nodos (intersecciones)
        num_edges: Número de aristas (calles)
        num_features: Features por nodo
        danger_level: Nivel base de peligro (0=seguro, 1=muy peligroso)
    
    Returns:
        x: Features de nodos [num_nodes, num_features]
        edge_index: Índices de aristas [2, num_edges]
        edge_labels: Labels de seguridad por arista [num_edges]
            1 = seguro, 0 = peligroso
    """
    # Features de nodos
    x = torch.randn((num_nodes, num_features))
    
    # Feature 0: Nivel de presencia policial (influenciado por danger_level)
    police_presence = torch.rand(num_nodes) * danger_level
    x[:, 0] = police_presence
    
    # Feature 1: Tipo de ubicación (0=calle, 1=callejón, 2=edificio, 3=parque)
    location_type = torch.randint(0, 4, (num_nodes,)).float() / 3.0
    x[:, 1] = location_type
    
    # Feature 2: Nivel de iluminación (inverso al nivel policial = más seguro de noche)
    x[:, 2] = 1.0 - torch.rand(num_nodes) * 0.5
    
    # Feature 3: Densidad de población (más gente = más fácil esconderse)
    x[:, 3] = torch.rand(num_nodes)
    
    # Generar aristas
    edge_index = torch.randint(0, num_nodes, (2, num_edges))
    
    # Generar labels de seguridad para cada arista
    # Una arista es segura si ambos nodos tienen:
    # - Baja presencia policial
    # - Buena cobertura (callejones o alta densidad)
    src_nodes = edge_index[0]
    dst_nodes = edge_index[1]
    
    src_police = x[src_nodes, 0]
    dst_police = x[dst_nodes, 0]
    src_density = x[src_nodes, 3]
    dst_density = x[dst_nodes, 3]
    
    # Score de seguridad: bajo policial + alta densidad
    safety_score = (1.0 - (src_police + dst_police) / 2.0) * ((src_density + dst_density) / 2.0)
    
    # Convertir a labels binarios (threshold = 0.5)
    edge_labels = (safety_score > 0.5).float()
    
    return x, edge_index, edge_labels


def train_epoch(
    model: OracleNet,
    optimizer: optim.Optimizer,
    x: torch.Tensor,
    edge_index: torch.Tensor,
    edge_labels: torch.Tensor,
    device: torch.device
) -> float:
    """
    Entrena el modelo por una época.
    
    Args:
        model: Modelo OracleNet
        optimizer: Optimizador
        x: Features de nodos
        edge_index: Índices de aristas
        edge_labels: Labels de seguridad
        device: Dispositivo de cómputo
    
    Returns:
        loss: Pérdida promedio de la época
    """
    model.train()
    optimizer.zero_grad()
    
    # Forward pass
    edge_predictions, _ = model(x, edge_index)
    edge_predictions = edge_predictions.squeeze()
    
    # Loss: Binary Cross Entropy
    # Predecir si una arista es segura (1) o peligrosa (0)
    loss = F.binary_cross_entropy(edge_predictions, edge_labels)
    
    # Backward pass
    loss.backward()
    optimizer.step()
    
    return loss.item()


@torch.no_grad()
def evaluate(
    model: OracleNet,
    x: torch.Tensor,
    edge_index: torch.Tensor,
    edge_labels: torch.Tensor,
    device: torch.device
) -> Tuple[float, float]:
    """
    Evalúa el modelo en un conjunto de validación.
    
    Returns:
        loss: Pérdida
        accuracy: Precisión en clasificación de aristas
    """
    model.eval()
    
    # Forward pass
    edge_predictions, _ = model(x, edge_index)
    edge_predictions = edge_predictions.squeeze()
    
    # Loss
    loss = F.binary_cross_entropy(edge_predictions, edge_labels)
    
    # Accuracy (threshold = 0.5)
    predictions_binary = (edge_predictions > 0.5).float()
    accuracy = (predictions_binary == edge_labels).float().mean()
    
    return loss.item(), accuracy.item()


def train_oracle_net(
    num_epochs: int = 200,
    num_graphs: int = 50,
    learning_rate: float = 0.001,
    device: Optional[str] = None
):
    """
    Función principal de entrenamiento para OracleNet.
    
    Args:
        num_epochs: Número de épocas de entrenamiento
        num_graphs: Número de grafos sintéticos a generar por época
        learning_rate: Tasa de aprendizaje
        device: Dispositivo ('cuda' o 'cpu')
    """
    print("=" * 70)
    print("🔮 OracleNet Training - The Robber's Escape Route Optimizer")
    print("=" * 70)
    
    # Configurar dispositivo
    if device is None:
        device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    else:
        device = torch.device(device)
    
    print(f"\n🖥️  Device Configuration:")
    print(f"   Device: {device}")
    
    if device.type == 'cuda':
        gpu_name = torch.cuda.get_device_name(0)
        gpu_memory = torch.cuda.get_device_properties(0).total_memory / 1e9
        print(f"   GPU: {gpu_name}")
        print(f"   Memory: {gpu_memory:.2f} GB")
        
        # Nota sobre NVIDIA Quadro K4200
        if "K4200" in gpu_name or "Quadro" in gpu_name:
            print(f"\n   ⚡ NVIDIA Quadro K4200 detectada!")
            print(f"   Esta GPU es excelente para entrenar modelos GNN de tamaño medio.")
            print(f"   Con 4GB VRAM, podemos procesar grafos de hasta ~200-300 nodos eficientemente.")
    else:
        print(f"   ⚠️  GPU no disponible. Entrenando en CPU.")
        print(f"   Para grafos grandes, recomendamos usar GPU.")
    
    # Crear modelo
    print(f"\n🏗️  Building OracleNet...")
    model = create_oracle_net(num_features=16, device=device)
    
    total_params = sum(p.numel() for p in model.parameters())
    print(f"   Total parameters: {total_params:,}")
    
    # Optimizador
    optimizer = optim.Adam(model.parameters(), lr=learning_rate)
    
    # Learning rate scheduler para convergencia más estable
    scheduler = optim.lr_scheduler.ReduceLROnPlateau(
        optimizer, mode='min', factor=0.5, patience=10, verbose=True
    )
    
    print(f"\n🎯 Training Configuration:")
    print(f"   Epochs: {num_epochs}")
    print(f"   Graphs per epoch: {num_graphs}")
    print(f"   Learning rate: {learning_rate}")
    print(f"   Optimizer: Adam")
    
    print("\n" + "=" * 70)
    print("🚀 Starting Training...")
    print("=" * 70)
    
    best_val_loss = float('inf')
    training_history = {
        'train_loss': [],
        'val_loss': [],
        'val_accuracy': []
    }
    
    start_time = time.time()
    
    for epoch in range(num_epochs):
        epoch_start = time.time()
        
        # Entrenar en múltiples grafos sintéticos
        train_losses = []
        
        for graph_idx in range(num_graphs):
            # Generar grafo de entrenamiento
            # Variar el nivel de peligro para diversidad
            danger_level = np.random.uniform(0.3, 0.8)
            x_train, edge_index_train, edge_labels_train = generate_synthetic_city_graph(
                num_nodes=100,
                num_edges=300,
                num_features=16,
                danger_level=danger_level
            )
            
            x_train = x_train.to(device)
            edge_index_train = edge_index_train.to(device)
            edge_labels_train = edge_labels_train.to(device)
            
            # Entrenar
            loss = train_epoch(
                model, optimizer, x_train, edge_index_train, edge_labels_train, device
            )
            train_losses.append(loss)
        
        avg_train_loss = np.mean(train_losses)
        training_history['train_loss'].append(avg_train_loss)
        
        # Validación en un grafo separado
        x_val, edge_index_val, edge_labels_val = generate_synthetic_city_graph(
            num_nodes=100,
            num_edges=300,
            num_features=16,
            danger_level=0.5
        )
        x_val = x_val.to(device)
        edge_index_val = edge_index_val.to(device)
        edge_labels_val = edge_labels_val.to(device)
        
        val_loss, val_accuracy = evaluate(
            model, x_val, edge_index_val, edge_labels_val, device
        )
        training_history['val_loss'].append(val_loss)
        training_history['val_accuracy'].append(val_accuracy)
        
        # Update learning rate
        scheduler.step(val_loss)
        
        # Guardar mejor modelo
        if val_loss < best_val_loss:
            best_val_loss = val_loss
            torch.save({
                'epoch': epoch,
                'model_state_dict': model.state_dict(),
                'optimizer_state_dict': optimizer.state_dict(),
                'val_loss': val_loss,
                'val_accuracy': val_accuracy,
            }, 'oracle_net_best.pth')
        
        epoch_time = time.time() - epoch_start
        
        # Logging
        if (epoch + 1) % 10 == 0 or epoch == 0:
            print(f"Epoch [{epoch+1:3d}/{num_epochs}] | "
                  f"Train Loss: {avg_train_loss:.4f} | "
                  f"Val Loss: {val_loss:.4f} | "
                  f"Val Acc: {val_accuracy:.4f} | "
                  f"Time: {epoch_time:.2f}s")
    
    total_time = time.time() - start_time
    
    print("\n" + "=" * 70)
    print("✅ Training Completed!")
    print("=" * 70)
    print(f"Total training time: {total_time/60:.2f} minutes")
    print(f"Best validation loss: {best_val_loss:.4f}")
    print(f"Final validation accuracy: {training_history['val_accuracy'][-1]:.4f}")
    print(f"\n💾 Best model saved to: oracle_net_best.pth")
    
    return model, training_history


def test_trained_model():
    """
    Prueba el modelo entrenado en un escenario de escape.
    """
    print("\n" + "=" * 70)
    print("🎬 Testing Trained OracleNet - Escape Scenario Simulation")
    print("=" * 70)
    
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    
    # Cargar modelo entrenado
    model = create_oracle_net(num_features=16, device=device)
    
    try:
        checkpoint = torch.load('oracle_net_best.pth', map_location=device)
        model.load_state_dict(checkpoint['model_state_dict'])
        print(f"\n✅ Loaded trained model (Epoch {checkpoint['epoch']}, "
              f"Val Loss: {checkpoint['val_loss']:.4f})")
    except FileNotFoundError:
        print("\n⚠️  No trained model found. Using untrained model.")
    
    # Generar escenario de prueba: Ciudad con alta vigilancia
    print("\n🌆 Generating high-surveillance city scenario...")
    x_test, edge_index_test, true_labels = generate_synthetic_city_graph(
        num_nodes=50,
        num_edges=150,
        num_features=16,
        danger_level=0.7  # Alta vigilancia
    )
    
    x_test = x_test.to(device)
    edge_index_test = edge_index_test.to(device)
    
    # Predicción
    model.eval()
    with torch.no_grad():
        safety_predictions, attention_weights = model(
            x_test, edge_index_test, return_attention=True
        )
    
    safety_scores = safety_predictions.squeeze().cpu().numpy()
    
    print(f"\n📊 Escape Route Analysis:")
    print(f"   Total routes evaluated: {len(safety_scores)}")
    print(f"   Safe routes (>0.7): {np.sum(safety_scores > 0.7)}")
    print(f"   Risky routes (0.3-0.7): {np.sum((safety_scores >= 0.3) & (safety_scores <= 0.7))}")
    print(f"   Dangerous routes (<0.3): {np.sum(safety_scores < 0.3)}")
    
    # Top 5 rutas más seguras
    top_indices = np.argsort(safety_scores)[-5:][::-1]
    
    print(f"\n🛡️  RECOMMENDED ESCAPE ROUTES (Top 5):")
    for i, idx in enumerate(top_indices, 1):
        src = edge_index_test[0, idx].item()
        dst = edge_index_test[1, idx].item()
        score = safety_scores[idx]
        police_src = x_test[src, 0].item()
        police_dst = x_test[dst, 0].item()
        
        print(f"   {i}. Route {src:2d} → {dst:2d}: "
              f"Safety={score:.3f} | "
              f"Police: {police_src:.2f}→{police_dst:.2f}")
    
    print("\n" + "=" * 70)


if __name__ == "__main__":
    # Entrenar el modelo
    model, history = train_oracle_net(
        num_epochs=200,
        num_graphs=50,
        learning_rate=0.001
    )
    
    # Probar el modelo entrenado
    test_trained_model()
