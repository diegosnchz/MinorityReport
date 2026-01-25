import torch

class TemporalDataBatcher:
    """
    Convierte nuestros datos de Neo4j en lotes temporales para TGN.
    """
    def prepare_batch(self, events):
        """
        Prepara un lote de eventos para el entrenamiento/inferencia de TGN.
        Args:
            events (list): Lista de diccionarios traída de Neo4j ordenada por timestamp.
                           Cada evento debe tener keys: 'source_id', 'target_id', 'timestamp'.
        """
        if not events:
            return None

        # Extraemos listas de los eventos
        src_ids = [e['source_id'] for e in events]
        dst_ids = [e['target_id'] for e in events]
        timestamps = [int(e['timestamp']) for e in events] # UNIX timestamps convertidos a int
        
        # Generamos mensajes crudos (raw features) para cada interacción.
        # En un caso real, esto vendría de propiedades de la relación (ej. tipo de transacción).
        # Aquí usamos ruido aleatorio como placeholder de la feature "interacción".
        raw_msg_dim = 16
        raw_msgs = torch.randn(len(events), raw_msg_dim)

        # TGN espera Tensores
        return {
            'src': torch.tensor(src_ids, dtype=torch.long),
            'dst': torch.tensor(dst_ids, dtype=torch.long),
            't': torch.tensor(timestamps, dtype=torch.long),
            'msg': raw_msgs
        }
