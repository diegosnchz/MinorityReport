import xarray as xr
import numpy as np
import zarr
import os

class RiskDataCube:
    """
    Motor Tensors-Temporal para Minority Report.
    Usa Zarr para almacenamiento en chunks y Xarray para slicing.
    """
    
    def __init__(self, storage_path="data/tensors/risk_cube.zarr"):
        self.path = storage_path
        os.makedirs(os.path.dirname(storage_path), exist_ok=True)

    def create_mock_cube(self):
        """Genera un cubo de datos de riesgo (Lat, Lon, Time)."""
        times = xr.date_range("2024-01-01", periods=24, freq="H")
        lats = np.linspace(40.35, 40.50, 50)
        lons = np.linspace(-3.75, -3.55, 50)
        
        # Generar ruido de riesgo
        data = np.random.rand(len(times), len(lats), len(lons))
        
        ds = xr.Dataset(
            {"risk_level": (["time", "lat", "lon"], data)},
            coords={
                "time": times,
                "lat": lats,
                "lon": lons,
            }
        )
        
        # Guardar en formato Zarr (Eficiente para lecturas parciales)
        ds.to_zarr(self.path, mode="w")
        return ds

    def get_risk_at(self, time_slice, lat_range, lon_range):
        """
        Slicing ultrarrápido usando Xarray.
        Ej: 'Dame el riesgo en Usera durante la última hora'.
        """
        ds = xr.open_zarr(self.path)
        return ds.sel(
            time=time_slice, 
            lat=slice(lat_range[0], lat_range[1]),
            lon=slice(lon_range[0], lon_range[1])
        ).risk_level.mean().values

# Singleton
risk_cube = RiskDataCube()
