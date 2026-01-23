
import time
import timeit
import numpy as np
import pandas as pd
import os
import sys

# Add project root to path to import app modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.evasion.math.heuristics import batch_cost_processing, calculate_heuristic_cost

def benchmark_numba():
    print("\n--- Numba Benchmark (Vectorized/JIT Loop vs Pure Python Loop) ---")
    
    # Pure Python logic applied in a loop
    def python_batch_process(distances, risks, fatigues, multipliers):
        n = len(distances)
        out = [0.0] * n
        for i in range(n):
            out[i] = (distances[i] * multipliers[i]) + (risks[i] * 100.0) + (fatigues[i] * 5.0)
        return out

    # Prepare data
    n = 1_000_000
    print(f"Generating {n} elements for Numba benchmark...")
    distances = np.random.rand(n)
    risks = np.random.rand(n)
    fatigues = np.random.rand(n)
    multipliers = np.random.rand(n)

    # Warmup Numba
    batch_cost_processing(distances[:10], risks[:10], fatigues[:10], multipliers[:10])

    print(f"Running processing on {n} items...")

    # Python time
    start_py = time.perf_counter()
    _ = python_batch_process(distances, risks, fatigues, multipliers)
    end_py = time.perf_counter()
    time_py = end_py - start_py

    # Numba time
    start_numba = time.perf_counter()
    _ = batch_cost_processing(distances, risks, fatigues, multipliers)
    end_numba = time.perf_counter()
    time_numba = end_numba - start_numba

    print(f"Pure Python Loop Time: {time_py:.4f}s")
    print(f"Numba @jit Loop Time:  {time_numba:.4f}s")
    if time_numba > 0:
        print(f"Speedup Factor:        {time_py / time_numba:.2f}x")
    else:
        print("Speedup Factor:        Infinite")

def benchmark_arrow():
    print("\n--- Arrow/Parquet Benchmark (Pandas CSV vs PyArrow Parquet) ---")
    
    rows = 5_000_000
    print(f"Generating {rows} rows of synthetic data (approx 200MB)...")
    df = pd.DataFrame({
        'id': np.arange(rows, dtype=np.int32),
        'value': np.random.rand(rows).astype(np.float32),
        'category': np.random.choice(['A', 'B', 'C', 'D'], rows),
        'timestamp': pd.date_range('2024-01-01', periods=rows, freq='s')
    })
    
    csv_file = 'temp_benchmark.csv'
    parquet_file = 'temp_benchmark.parquet'
    
    print("Saving files...")
    # writing csv can be slow, but we are benchmarking READ
    df.to_csv(csv_file, index=False)
    df.to_parquet(parquet_file, engine='pyarrow')
    
    # Measure CSV read
    print("Reading CSV with Pandas...")
    start_csv = time.perf_counter()
    _ = pd.read_csv(csv_file)
    end_csv = time.perf_counter()
    time_csv = end_csv - start_csv
    
    # Measure Parquet read
    print("Reading Parquet with Pandas (engine='pyarrow')...")
    start_pq = time.perf_counter()
    _ = pd.read_parquet(parquet_file, engine='pyarrow')
    end_pq = time.perf_counter()
    time_pq = end_pq - start_pq
    
    print(f"Pandas CSV Read Time:      {time_csv:.4f}s")
    print(f"Pandas Parquet Read Time:  {time_pq:.4f}s")
    if time_pq > 0:
        print(f"Speedup Factor:            {time_csv / time_pq:.2f}x")
    else:
        print("Speedup Factor:            Infinite")

    # Cleanup
    os.remove(csv_file)
    os.remove(parquet_file)
    print("Temporary files cleaned up.")

if __name__ == "__main__":
    benchmark_numba()
    benchmark_arrow()
