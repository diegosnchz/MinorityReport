import os
import sys

# Force DEMO_MODE to true for testing
os.environ["DEMO_MODE"] = "True"

try:
    from app.core import hardware_switch as hw
    print(f"Hardware Switch Loaded. HAS_GPU={hw.HAS_GPU}")
    
    from app.evasion.models import hybrid_engine
    print("Hybrid Engine Imported.")
    
    from app.evasion.etl.data_loader import data_loader
    print("Data Loader Imported.")
    
    # Test Data Load
    df = data_loader.load_zero_copy("ignored_in_demo_mode.parquet")
    print(f"Data Loaded: {len(df)} rows.")
    
except Exception as e:
    print(f"CRITICAL ERROR: {e}")
    sys.exit(1)
