@echo off
SETLOCAL EnableDelayedExpansion

echo ==========================================
echo    Minority Report - Project Starter   
echo ==========================================
echo.

:: 1. Verificar si Docker está instalado
where docker >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Docker no está instalado o no está en el PATH.
    echo Por favor, instala Docker Desktop primero: https://www.docker.com/products/docker-desktop
    pause
    exit /b 1
)

:: 2. Levantar los contenedores
echo [1/3] Levantando contenedores con Docker Compose...
docker-compose up -d
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Hubo un problema al arrancar Docker Compose.
    echo Asegúrate de que Docker Desktop está abierto.
    pause
    exit /b 1
)

:: 3. Esperar a que Neo4j esté listo (aprox 20 seg)
echo [2/3] Esperando a que Neo4j termine de arrancar (20 segundos)...
timeout /t 20 /nobreak >nul

:: 4. Poblar la base de datos
echo [3/3] Inicializando el grafo de la ciudad...
python src/scripts/init_city_graph.py
if %ERRORLEVEL% neq 0 (
    echo [AVISO] El script de inicialización falló o ya estaba inicializado.
    echo Revisa si tienes Python instalado y las dependencias (pip install -r requirements.txt).
)

echo.
echo ==========================================
echo PROYECTO LISTO PARA USAR!
echo ==========================================
echo.
echo - Neo4j Browser: http://localhost:7474
echo - API Docs:      http://localhost:8000/docs
echo - Dashboard 3D:  http://localhost:8000/static/map.html
echo.
echo Presiona cualquier tecla para salir...
pause >nul
