from fastapi import WebSocket
import logging

logging.basicConfig(level=logging.INFO)

class ConnectionManager:
    def __init__(self):
        # ladron_id -> WebSocket
        self.active_connections: dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, client_id: str):
        await websocket.accept()
        self.active_connections[client_id] = websocket
        logging.info(f"🔌 Cliente conectado: {client_id}")

    def disconnect(self, client_id: str):
        if client_id in self.active_connections:
            del self.active_connections[client_id]
            logging.info(f"🔌 Cliente desconectado: {client_id}")

    async def send_personal_message(self, message: dict, client_id: str):
        """
        Envía un JSON a un cliente concreto.
        Si el socket está caído, lo elimina de conexiones activas.
        """
        ws = self.active_connections.get(client_id)
        if not ws:
            logging.warning(f"⚠️ No existe conexión WS para: {client_id}")
            return

        try:
            await ws.send_json(message)
        except Exception as e:
            logging.warning(f"⚠️ Error enviando WS a {client_id}: {e}. Desconectando...")
            self.disconnect(client_id)

# Instancia compartida
manager = ConnectionManager()