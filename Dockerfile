# Usamos una imagen ligera de Python 3.9
FROM python:3.9-slim

# Evita que Python genere archivos .pyc y buffer de salida
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Directorio de trabajo dentro del contenedor
WORKDIR /code

# Instalamos dependencias del sistema (necesarias para algunas libs de grafos)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copiamos los requerimientos e instalamos
COPY requirements.txt /code/
RUN pip install --no-cache-dir --upgrade -r requirements.txt

# Copiamos todo el código del proyecto
COPY ./app /code/app

# Exponemos el puerto
EXPOSE 8000

# Comando de inicio
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
