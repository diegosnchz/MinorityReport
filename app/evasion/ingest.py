
import json
import hashlib
import random
import io
import pyarrow as pa
import logging

# Simulamos el entorno de Nuclio si no estamos en el container real
try:
    import nuclio_sdk
except ImportError:
    class MockContext:
        logger = logging.getLogger("nuclio")
    nuclio_sdk = None

def handler(context, event):
    """
    Nuclio Handler: Ingesta de Datos del Edge.
    
    Flujo:
    1. Recibe JSON del sensor (simulado o real).
    2. Aplica Privacidad (Hashing + Jitter).
    3. Serializa a Apache Arrow (Zero-Copy para RAPIDS).
    """
    
    # 1. Parsear Evento
    if isinstance(event.body, bytes):
        body = json.loads(event.body.decode('utf-8'))
    else:
        body = event.body
        
    context.logger.info(f"Received event from sensor: {body.get('sensor_id')}")

    # 2. Privacidad y Seguridad (GDPR Compliance)
    # Ofuscar ID del Ciudadano
    raw_id = body.get('citizen_id', 'unknown')
    hashed_id = hashlib.sha256(raw_id.encode()).hexdigest()
    
    # Jitter Espacial (Ruido a las coordenadas para evitar triangulación exacta)
    # ~10-50 metros de ruido aleatorio
    lat = float(body.get('lat', 40.4168))
    lon = float(body.get('lon', -3.7038))
    
    lat_jitter = lat + random.uniform(-0.0005, 0.0005)
    lon_jitter = lon + random.uniform(-0.0005, 0.0005)

    # 3. Empaquetado High-Performance (Apache Arrow)
    # Schema Definido
    schema = pa.schema([
        ('timestamp', pa.float64()),
        ('citizen_hash', pa.string()),
        ('lat', pa.float64()),
        ('lon', pa.float64()),
        ('heart_rate', pa.int32()),
        ('stress_level', pa.float32())
    ])

    # Columnas
    data = [
        pa.array([float(body.get('timestamp', 0))]),
        pa.array([hashed_id]),
        pa.array([lat_jitter]),
        pa.array([lon_jitter]),
        pa.array([int(body.get('heart_rate', 70))]),
        pa.array([float(body.get('stress_level', 0.1))])
    ]

    batch = pa.RecordBatch.from_arrays(data, schema=schema)
    
    # Escribir a Buffer en Memoria (Zero-Copy ready)
    sink = io.BytesIO()
    writer = pa.RecordBatchFileWriter(sink, schema)
    writer.write_batch(batch)
    writer.close()
    
    arrow_buffer = sink.getvalue()
    
    # 4. Retorno (En producción iría a Kafka/Redpanda)
    return context.Response(
        body=arrow_buffer,
        headers={"Content-Type": "application/vnd.apache.arrow.file"},
        status_code=200
    )

# --- Simulation Hook for Testing ---
if __name__ == "__main__":
    # Simula un evento para pruebas locales
    import time
    
    print("Testing Ingest Function locally...")
    
    mock_event = type('Event', (), {})()
    mock_event.body = {
        "sensor_id": "SENS-001",
        "timestamp": time.time(),
        "citizen_id": "ID_12345_SECRET",
        "lat": 40.41,
        "lon": -3.70,
        "heart_rate": 120,
        "stress_level": 0.85
    }
    
    mock_context = type('Context', (), {})()
    mock_context.logger = logging.getLogger("test")
    mock_context.logger.setLevel(logging.INFO)
    mock_context.Response = lambda body, headers, status_code: \
        f"[Response {status_code}] Bytes: {len(body)} Content-Type: {headers['Content-Type']}"

    result = handler(mock_context, mock_event)
    print(result)
