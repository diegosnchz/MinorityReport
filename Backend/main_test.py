import asyncio
from models import Alerta
from executor import executor
from database import db # Para cerrar la conexión al final

async def main():
    # 1. Arrancar el worker en segundo plano
    # create_task lanza la función sin bloquear el programa principal
    worker_task = asyncio.create_task(executor.run_worker())

    print("🚀 SISTEMA INICIADO. Simulando llegada de alertas...\n")

    # 2. Simular que la API recibe peticiones (Productor)
    alertas_prueba = [
        Alerta(
            ladron_id="Lupin", 
            ubicacion_actual_id="Banco_Central", 
            nivel_riesgo=80, 
            amenaza_detectada="Robo de diamantes"  # <--- AÑADIDO
        ),
        Alerta(
            ladron_id="Catwoman", 
            ubicacion_actual_id="Joyeria", 
            nivel_riesgo=40, 
            amenaza_detectada="Allanamiento silencioso" # <--- AÑADIDO
        ),
        Alerta(
            ladron_id="Joker", 
            ubicacion_actual_id="Comisaria", 
            nivel_riesgo=95, 
            amenaza_detectada="Caos generalizado" # <--- AÑADIDO
        )
    ]

    for alerta in alertas_prueba:
        print(f"📲 API: Enviando alerta de {alerta.ladron_id}...")
        await executor.add_alert(alerta)
        # Esperamos un poquito entre alertas para ver los logs ordenados
        await asyncio.sleep(0.5)

    # 3. Esperar a que la cola se vacíe (que el worker termine su trabajo)
    print("\n⏳ Esperando a que el executor termine de procesar...")
    await executor.queue.join()

    # 4. Parar todo limpiamente
    executor.is_running = False
    worker_task.cancel()
    db.close()
    print("\n✅ PRUEBA FINALIZADA CON ÉXITO")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Apagando...")