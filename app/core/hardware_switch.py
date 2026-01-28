import os
import logging

# Configure logger
logger = logging.getLogger("HardwareSwitch")

# Chequear variable de entorno
DEMO_MODE = os.getenv("DEMO_MODE", "False").lower() == "true"

HAS_GPU = False
cudf = None
cupy = None
cuml = None

if not DEMO_MODE:
    try:
        import cudf
        import cupy
        import cuml
        HAS_GPU = True
        logger.info("⚡ NVIDIA RAPIDS Detected. GPU Acceleration ENABLED.")
    except ImportError:
        logger.warning("⚠️ RAPIDS not found. Falling back to CPU Mode.")
        HAS_GPU = False
else:
    logger.info("ℹ️ DEMO MODE Activated. Forcing CPU Execution.")

# Expose libraries (aliases)
if HAS_GPU:
    import cudf
    import cupy
    import cuml
    
    # Alias standard names to GPU versions where API is compatible
    pd = cudf
    np = cupy
else:
    import pandas as pd
    import numpy as np
    
    # Mocks or aliases for compatibility if needed, 
    # but usually we just import pandas as pd in the consuming code.
    # Here we expose 'cudf' as pandas so accidental calls might work if simple API
    cudf = pd 
    cupy = np
    cuml = None # scikit-learn replacement handled in logic usually

def get_xgboost_params(base_params=None):
    """
    Returns appropriate XGBoost parameters based on hardware availability.
    """
    if base_params is None:
        base_params = {}
    
    params = base_params.copy()
    
    if HAS_GPU:
        params['tree_method'] = 'gpu_hist'
        params['gpu_id'] = 0
    else:
        params['tree_method'] = 'hist' # Efficient CPU method
        # Remove gpu_id if present
        params.pop('gpu_id', None)
        
    return params

def to_cpu(df):
    """
    Ensures safe conversion to Pandas DataFrame (CPU).
    """
    if HAS_GPU and hasattr(df, 'to_pandas'):
        return df.to_pandas()
    return df

def to_gpu_if_possible(df):
    """
    Attempts to convert Pandas DF to cuDF if GPU is available.
    """
    if HAS_GPU:
        try:
             # If it's already cuDF, ignore
            if hasattr(df, 'device'): 
                return df
            return cudf.DataFrame.from_pandas(df)
        except Exception as e:
            logger.warning(f"Failed to move data to GPU: {e}")
            return df
    return df
