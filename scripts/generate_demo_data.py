import pandas as pd
import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq
import os

# Configuration
NUM_NODES = 5000
MADRID_LAT = 40.4168
MADRID_LON = -3.7038
# Spread in degrees (roughly 5-10km radius)
SPREAD = 0.05 
OUTPUT_DIR = "app/data/hpc"
OUTPUT_FILE = "demo_data.parquet"

def generate_madrid_nodes():
    print(f"Generating {NUM_NODES} synthetic nodes for Madrid Demo...")
    
    # 1. Generate Coordinates (Gaussian distribution around Madrid center)
    lats = np.random.normal(MADRID_LAT, SPREAD, NUM_NODES)
    lons = np.random.normal(MADRID_LON, SPREAD, NUM_NODES)
    
    # 2. Generate Metadata
    ids = [f"node_{i:05d}" for i in range(NUM_NODES)]
    risk_seeds = np.random.uniform(0, 1, NUM_NODES) # 0.0 to 1.0
    
    # 3. Create DataFrame
    df = pd.DataFrame({
        'node_id': ids,
        'lat': lats,
        'lon': lons,
        'risk_seed': risk_seeds,
        'timestamp': pd.Timestamp.now().timestamp(),
        'sensor_type': np.random.choice(['camera', 'lidar', 'acoustic'], NUM_NODES)
    })
    
    # Ensure directory exists
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # 4. Save to Parquet
    full_path = os.path.join(OUTPUT_DIR, OUTPUT_FILE)
    table = pa.Table.from_pandas(df)
    pq.write_table(table, full_path)
    
    print(f"✅ Success! Data saved to: {full_path}")
    print(df.head())

if __name__ == "__main__":
    generate_madrid_nodes()
