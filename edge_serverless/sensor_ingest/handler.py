
# edge_serverless/sensor_ingest/handler.py
import json
import hashlib
import random
import io
import pyarrow as pa
import logging

def handler(context, event):
    """
    Nuclio Handler for The Evasion Protocol - Edge Ingest.
    
    Responsibilities:
    1. Receive Raw Sensor JSON.
    2. PRIVACY: Hash User IDs and apply geospatial jitter to coordinates.
    3. PERFORMANCE: Serialize to Apache Arrow (IPC Stream) for Zero-Copy transfer.
    """
    
    # 1. Parse Input
    try:
        body = event.body
        if isinstance(body, bytes):
            body = json.loads(body.decode('utf-8'))
        elif isinstance(body, str):
            body = json.loads(body)
    except Exception as e:
        context.logger.error(f"Failed to parse event: {e}")
        return context.Response(body="Invalid JSON", status_code=400)

    # 2. Privacy Layer (Obfuscation)
    # Hashing the User ID (SHA-256)
    raw_user_id = str(body.get('user_id', 'unknown'))
    hashed_id = hashlib.sha256(raw_user_id.encode('utf-8')).hexdigest()
    
    # Geospatial Jitter (~50m randomization)
    # 0.0005 degrees is roughly 55 meters at 40 deg latitude
    # This prevents precise triangulation of "Safe Nodes"
    raw_lat = float(body.get('lat', 0.0))
    raw_lon = float(body.get('lon', 0.0))
    
    jitter_lat = raw_lat + random.uniform(-0.0005, 0.0005)
    jitter_lon = raw_lon + random.uniform(-0.0005, 0.0005)
    
    timestamp = float(body.get('timestamp', 0.0))
    
    # 3. Arrow Serialization (Zero-Copy Pipeline)
    # Define rigid schema for the High Performance Core
    schema = pa.schema([
        ('timestamp', pa.float64()),
        ('hash_id', pa.string()),
        ('lat', pa.float64()),
        ('lon', pa.float64()),
        ('sensor_type', pa.string())
    ])
    
    # Create Columns (Arrays)
    # Note: Nuclio typically handles single requests, but we could batch here if needed.
    # We construct a 1-row batch for this stream event.
    data = [
        pa.array([timestamp]),
        pa.array([hashed_id]),
        pa.array([jitter_lat]),
        pa.array([jitter_lon]),
        pa.array([str(body.get('sensor_type', 'generic'))])
    ]
    
    batch = pa.RecordBatch.from_arrays(data, schema=schema)
    
    # Serialize to Byte Stream (IPC Format)
    sink = io.BytesIO()
    with pa.ipc.new_stream(sink, schema) as writer:
        writer.write_batch(batch)
        
    arrow_buffer = sink.getvalue()
    
    # 4. Return Binary Response
    # This buffer goes directly to Kafka/Redpanda and then to RAPIDS
    return context.Response(
        body=arrow_buffer,
        headers={"Content-Type": "application/vnd.apache.arrow.stream"},
        status_code=200
    )
