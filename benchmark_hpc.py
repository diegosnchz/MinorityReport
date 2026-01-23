import time
import pandas as pd
import numpy as np
import pyarrow.parquet as pq
import pyarrow as pa
import os
from app.evasion.math.heuristics import calculate_heuristic_cost

def legacy_cost_function(distance, risk_score, agent_fatigue, terrain_multiplier):
    """Pure Python implementation (Slow)"""
    return (distance * terrain_multiplier) + (risk_score * 100.0) + (agent_fatigue * 5.0)

def benchmark_compute():
    iterations = 1_000_000
    
    # Data for benchmark
    dist = 0.5
    risk = 0.4
    fatigue = 0.2
    terrain = 1.2

    print(f"Running Compute Benchmark ({iterations} iterations)...")

    # Round 1: Legacy (Python)
    start_legacy = time.perf_counter()
    for _ in range(iterations):
        legacy_cost_function(dist, risk, fatigue, terrain)
    end_legacy = time.perf_counter()
    time_legacy = end_legacy - start_legacy

    # Round 2: HPC (Numba JIT)
    # Warmup JIT
    calculate_heuristic_cost(dist, risk, fatigue, terrain)
    
    start_hpc = time.perf_counter()
    for _ in range(iterations):
        calculate_heuristic_cost(dist, risk, fatigue, terrain)
    end_hpc = time.perf_counter()
    time_hpc = end_hpc - start_hpc

    return time_legacy, time_hpc

def benchmark_io():
    rows = 100_000
    print(f"Running I/O Benchmark ({rows} rows)...")
    
    # Generate dummy data
    df = pd.DataFrame(np.random.randint(0, 100, size=(rows, 4)), columns=list('ABCD'))
    csv_file = "benchmark_data.csv"
    parquet_file = "benchmark_data.parquet"
    
    df.to_csv(csv_file, index=False)
    df.to_parquet(parquet_file)

    # Round 3: I/O
    # Pandas CSV
    start_pandas = time.perf_counter()
    _ = pd.read_csv(csv_file)
    end_pandas = time.perf_counter()
    time_pandas = end_pandas - start_pandas

    # Arrow Parquet
    start_arrow = time.perf_counter()
    _ = pq.read_table(parquet_file)
    end_arrow = time.perf_counter()
    time_arrow = end_arrow - start_arrow

    # Cleanup
    if os.path.exists(csv_file): os.remove(csv_file)
    if os.path.exists(parquet_file): os.remove(parquet_file)

    return time_pandas, time_arrow

def print_results(t_legacy, t_hpc, t_pandas, t_arrow):
    speedup_compute = t_legacy / t_hpc if t_hpc > 0 else 0
    speedup_io = t_pandas / t_arrow if t_arrow > 0 else 0

    output = []
    output.append("\n" + "="*60)
    output.append(f"{'BENCHMARK RESULTS':^60}")
    output.append("="*60)
    output.append(f"{'TEST CASE':<25} | {'LEGACY (s)':<12} | {'HPC (s)':<12} | {'SPEEDUP':<10}")
    output.append("-" * 60)
    output.append(f"{'Compute (1M ops)':<25} | {t_legacy:<12.5f} | {t_hpc:<12.5f} | {speedup_compute:>8.1f}x")
    output.append(f"{'I/O (100k rows)':<25} | {t_pandas:<12.5f} | {t_arrow:<12.5f} | {speedup_io:>8.1f}x")
    output.append("="*60)
    output.append("\nVERDICT:")
    if speedup_compute > 10 and speedup_io > 5:
        output.append("HPC Architecture VALIDATED. System is ready for production.")
    else:
        output.append("HPC optimization failed. Check Numba/Arrow configuration.")
    
    report = "\n".join(output)
    print(report)
    
    with open("benchmark_results.txt", "w", encoding="utf-8") as f:
        f.write(report)

if __name__ == "__main__":
    t_leg, t_hpc = benchmark_compute()
    t_pd, t_arr = benchmark_io()
    print_results(t_leg, t_hpc, t_pd, t_arr)
