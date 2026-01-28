import pyarrow as pa
import pyarrow.parquet as pq
import pandas as pd
import logging
import os
from app.core import hardware_switch as hw

# Alias for convenience
HAS_GPU = hw.HAS_GPU
cudf = hw.cudf

class EvasionDataLoader:
    """
    Orquestador de carga de datos Zero-Copy usando Apache Arrow.
    Mueve datos del disco a la GPU sin serialización redundante.
    """
    
    def __init__(self, data_dir="data/hpc"):
        self.data_dir = data_dir
        os.makedirs(data_dir, exist_ok=True)

    def save_to_parquet(self, df: pd.DataFrame, filename: str):
        """Guarda un DataFrame en formato Parquet usando Arrow."""
        path = os.path.join(self.data_dir, filename)
        table = pa.Table.from_pandas(df)
        pq.write_table(table, path)
        return path

    def load_zero_copy(self, filename: str):
        """
        Carga datos usando Zero-Copy.
        Si hay GPU, usa cuDF para leer el buffer de Arrow directamente.
        """
        if hw.DEMO_MODE:
            logging.info("DEMO MODE: Loading synthetic data instead of production dataset.")
            filename = "demo_data.parquet"
            
        path = os.path.join(self.data_dir, filename)
        if not os.path.exists(path):
            raise FileNotFoundError(f"Data file not found: {path}")

        # 1. Leer Parquet a tabla Arrow (en memoria RAM)
        table = pq.read_table(path)
        
        if HAS_GPU:
            # 2. Transferencia Zero-Copy a VRAM de la GPU
            # RAPIDS cuDF puede consumir buffers de Arrow directamente
            gpu_df = cudf.DataFrame.from_arrow(table)
            logging.info("Data loaded to GPU via Zero-Copy.")
            return gpu_df
        else:
            # Fallback a Pandas
            return table.to_pandas()

# Singleton
data_loader = EvasionDataLoader()
