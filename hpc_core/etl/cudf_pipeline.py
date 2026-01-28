# hpc_core/etl/cudf_pipeline.py
import pyarrow as pa
import io
from app.core import hardware_switch as hw

# We wrap RAPIDS imports to avoid crashing if run on a non-GPU dev machine.
# But for PRODUCTION, this code assumes `cudf` is available.
# Hardware Switch handles fallback logging.
cudf = hw.cudf

def ingest_arrow_stream_to_gpu(arrow_bytes):
    """
    HPC Core Ingestor.
    
    Responsibilities:
    1. Receive Arrow IPC Stream (Bytes) from Kafka/Nuclio.
    2. ZERO-COPY LOAD: Read directly into GPU Memory (VRAM) using RAPIDS.
    3. VERIFICATION: Perform GPU-accelerated aggregation.
    """
    print(f"DEBUG: Receiving {len(arrow_bytes)} bytes of Arrow Stream...")
    
    # 1. Read Arrow Buffer (CPU Side metadata)
    # Even with cuDF, we might need to parse the IPC stream header first tailored to the source.
    # However, cudf.read_feather/orc/parquet is more common for files.
    # For IPC Stream in memory, we often bridge via PyArrow Table -> cuDF DataFrame
    # This is still highly efficient/zero-copy if configured correctly.
    
    source_stream = io.BytesIO(arrow_bytes)
    
    if hw.HAS_GPU:
        # --- GPU PATH (PRODUCTION) ---
        print("INFO: Loading directly to GPU via RAPIDS...")
        
        # Option A: Direct read if supported by version (cudf.read_ipc is not always standard for streams)
        # Option B: Bridge via PyArrow (Very fast, negligible overhead vs parsing JSON)
        # We use Option B for maximum compatibility with Nuclio's output.
        
        # Open Stream via PyArrow
        reader = pa.ipc.open_stream(source_stream)
        pa_table = reader.read_all()
        
        # Move to GPU implementation
        # cudf.DataFrame.from_arrow is zero-copy where possible
        gdf = hw.cudf.DataFrame.from_arrow(pa_table)
        
        print(f"INFO: Data Loaded to VRAM. Shape: {gdf.shape}")
        
        # 2. GPU Verification Aggregation
        # Let's group by sector (simulated by rounding lat/lon) to prove we have data
        # We create a 'sector_id' on the fly on the GPU
        gdf['sector_lat'] = (gdf['lat'] * 10).astype('int32')
        gdf['sector_lon'] = (gdf['lon'] * 10).astype('int32')
        
        # GroupBy on GPU
        result = gdf.groupby(['sector_lat', 'sector_lon']).agg({'hash_id': 'count'})
        result.columns = ['sensor_count']
        
        print("\n--- GPU AGGREGATION RESULT (Sectors) ---")
        print(result)
        
        return gdf
        
    else:
        # --- CPU MOCK PATH (DEV/CI) ---
        print("INFO: CPU Fallback Mode")
        import pandas as pd
        reader = pa.ipc.open_stream(source_stream)
        pa_table = reader.read_all()
        pdf = pa_table.to_pandas()
        
        pdf['sector_lat'] = (pdf['lat'] * 10).astype('int32')
        pdf['sector_lon'] = (pdf['lon'] * 10).astype('int32')
        result = pdf.groupby(['sector_lat', 'sector_lon']).agg({'hash_id': 'count'})
        
        print("\n--- CPU AGGREGATION RESULT (Sectors) ---")
        print(result)
        return pdf

# --- Test Harness (Simulate pipeline) ---
if __name__ == "__main__":
    # Simulate the Nuclio output
    print("Testing Pipeline...")
    
    # Create a dummy batch to mimic what comes from Nuclio
    schema = pa.schema([
        ('timestamp', pa.float64()),
        ('hash_id', pa.string()),
        ('lat', pa.float64()),
        ('lon', pa.float64()),
        ('sensor_type', pa.string())
    ])
    
    data = [
        pa.array([167888.0, 167899.0]),
        pa.array(["hash1", "hash2"]),
        pa.array([40.45, 40.42]),
        pa.array([-3.69, -3.71]),
        pa.array(["camera", "lidar"])
    ]
    batch = pa.RecordBatch.from_arrays(data, schema=schema)
    sink = io.BytesIO()
    with pa.ipc.new_stream(sink, schema) as writer:
        writer.write_batch(batch)
    
    buffer = sink.getvalue()
    
    # Run Ingest
    ingest_arrow_stream_to_gpu(buffer)
