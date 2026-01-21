# test_full_flow.py
import asyncio
import websockets
import requests
import json
import threading
import time

# Datos del ladrón de prueba
LADRON_ID = "Lupin_III"
URI_SOCKET = f"ws://127.0.0.1:8000/ws/{LADRON_ID}"
URL_ALERTA = "http://127.0.0.1:8000/alert"

def enviar_alerta_http():
    """Simula pulsar el botón de pánico 2 segundos después de conectar"""
    time.sleep(2) 
    print(f"\n[HTTP] 🚨 Enviando alerta de pánico para {LADRON_ID}...")
    
    payload = {
        "ladron_id": LADRON_ID,
        "ubicacion_actual_id": "Banco_Central",
        "amenaza_detectada": "POLICIA",
        "nivel_riesgo": 0.9
    }
    
    try:
        response = requests.post(URL_ALERTA, json=payload)
        print(f"[HTTP] ✅ Servidor respondió: {response.json()}")
    except Exception as e:
        print(f"[HTTP] ❌ Error enviando alerta: {e}")

async def escuchar_websocket():
    print(f"[WS] ⏳ Conectando al canal seguro de {LADRON_ID}...")
    
    async with websockets.connect(URI_SOCKET) as websocket:
        print("[WS] ✅ CONECTADO. Esperando instrucciones de escape...")
        
        # Lanzamos el hilo que enviará la alerta HTTP mientras nosotros escuchamos
        threading.Thread(target=enviar_alerta_http).start()
        
        # Bucle infinito escuchando mensajes del servidor
        while True:
            mensaje = await websocket.recv()
            datos = json.loads(mensaje)
            
            print("\n" + "="*40)
            print("📡 [WEBSOCKET] ¡MENSAJE RECIBIDO DEL HIVE!")
            print("="*40)
            print(f"Tipo: {datos.get('tipo')}")
            print(f"🏃 Destino Seguro: {datos.get('destino')}")
            print(f"🗺️ Ruta: {datos.get('nodos')}")
            print(f"🎲 Probabilidad Éxito: {datos.get('probabilidad')}")
            print("="*40 + "\n")
            
            # Rompemos el bucle para terminar la prueba tras recibir el mensaje
            break

if __name__ == "__main__":
    # Necesitas instalar: pip install websockets requests
    try:
        asyncio.run(escuchar_websocket())
    except KeyboardInterrupt:
        print("Prueba finalizada.")