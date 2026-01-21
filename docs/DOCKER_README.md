# 🐳 Docker Deployment Guide - Minority Report

Este documento describe cómo ejecutar el proyecto **Minority Report** usando Docker y Docker Compose.

## Arquitectura de Contenedores

```
┌─────────────────────────────────────────────────────┐
│  Docker Compose Network: minority-report-network    │
│                                                      │
│  ┌──────────────┐    ┌──────────────┐              │
│  │   Neo4j DB   │◄───│  OracleNet   │              │
│  │              │    │   (Robbers)  │              │
│  │  Port 7474   │    └──────────────┘              │
│  │  Port 7687   │                                   │
│  └──────┬───────┘    ┌──────────────┐              │
│         │            │  Police GAN  │              │
│         └────────────►│ (Generator+  │              │
│                      │ Discriminator)│              │
│                      └──────────────┘              │
│                                                      │
│                      ┌──────────────┐              │
│                      │    Gossip    │              │
│                      │   Protocol   │              │
│                      └──────────────┘              │
└─────────────────────────────────────────────────────┘
```

## Requisitos Previos

- Docker >= 20.10
- Docker Compose >= 2.0
- Al menos 4GB de RAM disponible
- 10GB de espacio en disco

## Inicio Rápido

### 1. Levantar todos los servicios

```bash
# Construir y levantar todos los contenedores
docker-compose up --build

# O en modo background (detached)
docker-compose up -d --build
```

### 2. Verificar que los servicios están corriendo

```bash
docker-compose ps
```

Deberías ver:
```
NAME                  STATUS              PORTS
minority-report-neo4j   running            0.0.0.0:7474->7474/tcp, 0.0.0.0:7687->7687/tcp
oracle-net              running            
police-gan              running            
gossip-network          running            
```

### 3. Acceder a Neo4j Browser

Abre tu navegador en: http://localhost:7474

- **Usuario**: `neo4j`
- **Contraseña**: `minorityreport`

### 4. Ver logs de los servicios

```bash
# Ver logs de OracleNet
docker-compose logs -f oracle-net

# Ver logs de Neo4j
docker-compose logs -f neo4j

# Ver logs de todos los servicios
docker-compose logs -f
```

## Servicios Disponibles

### Neo4j Database
- **Puerto HTTP**: 7474 (Neo4j Browser UI)
- **Puerto Bolt**: 7687 (Driver Protocol)
- **Credenciales**: neo4j/minorityreport
- **Plugins**: APOC, Graph Data Science (GDS)
- **Memoria**: 2GB heap, 1GB pagecache

### OracleNet (The Oracle)
- Entrena el modelo GCN+GAT para rutas de escape
- Se conecta automáticamente a Neo4j
- Guarda modelos entrenados en `./models/`
- Logs disponibles en `./logs/`

### Police GAN
- Entrena el GAN adversarial (Generator + Discriminator)
- Simula comportamiento de la policía predictiva

### Protocolo de Red: Gossip vs Mesh

El proyecto soporta DOS protocolos de sincronización distribuida:

#### 🔄 Gossip Protocol (Por defecto)
- **Características**:
  - Sincronización epidémica probabilística
  - Cada nodo conoce solo vecinos inmediatos
  - Excelente escalabilidad (>100 nodos)
  - Baja sobrecarga de memoria
  - Alta tolerancia a fallos

- **Usar cuando**:
  - Red grande (>100 edge nodes)
  - Ancho de banda limitado
  - Nodos entran/salen frecuentemente
  - Tolerancia a fallos es crítica

- **Ejecutar**:
  ```bash
  docker-compose up gossip-network
  ```

#### 🕸️ Mesh Network (Alternativa)
- **Características**:
  - Topología completa, cada nodo conoce todos
  - Comunicación directa optimizada
  - Convergencia rápida y determinista
  - Mayor uso de memoria (O(N))
  - Baja latencia

- **Usar cuando**:
  - Red pequeña/media (<100 nodos)
  - Latencia crítica (<100ms)
  - Actualizaciones en tiempo real
  - Ancho de banda suficiente

- **Ejecutar**:
  ```bash
  # Editar docker-compose.yml, descomentar sección mesh-network
  docker-compose up mesh-network
  ```

#### 📊 Benchmark: ¿Cuál usar?

Para decidir qué protocolo es mejor para tu caso:

```bash
# Ejecutar benchmark comparativo
docker-compose run --rm benchmark

# Verás un análisis como:
# ┌─────────────────────┬──────────────────────┬──────────────────────┐
# │ Característica      │ Mesh Network         │ Gossip Protocol      │
# ├─────────────────────┼──────────────────────┼──────────────────────┤
# │ Convergencia        │ Rápida (determinista)│ Lenta (probabilística│
# │ Escalabilidad       │ Limitada (<1000)     │ Excelente (>10k)     │
# │ Latencia            │ Baja (directa)       │ Media (multi-hop)    │
# └─────────────────────┴──────────────────────┴──────────────────────┘
```

#### 💡 Enfoque Híbrido (Recomendado)

Para **Minority Report**, recomendamos una arquitectura híbrida:

```
Ciudad dividida en zonas:

┌─────────────────────────────────────────┐
│  Centro (Alta Prioridad) - MESH         │
│  • 50 nodos edge                        │
│  • Latencia <50ms                       │
│  • Tracking policial en tiempo real     │
│                                          │
│  ┌──────────────────────────┐           │
│  │    Puentes Mesh↔Gossip   │           │
│  └──────────────────────────┘           │
│                                          │
│  Periferia (Escalabilidad) - GOSSIP    │
│  • 200+ nodos edge                      │
│  • Sincronización eventual              │
│  • Monitoreo de largo alcance           │
└─────────────────────────────────────────┘
```

Para implementar híbrido:
1. Levantar ambos servicios
2. Configurar nodos puente que traducen entre protocolos
3. Asignar zonas geográficas a cada protocolo

```bash
# Levantar ambos
docker-compose up gossip-network mesh-network
```

## Comandos Útiles

### Detener todos los servicios
```bash
docker-compose down
```

### Detener y eliminar volúmenes (⚠️ elimina datos de Neo4j)
```bash
docker-compose down -v
```

### Reconstruir un servicio específico
```bash
docker-compose up --build oracle-net
```

### Ejecutar comandos dentro de un contenedor
```bash
# Entrar a una shell en el contenedor de OracleNet
docker-compose exec oracle-net bash

# Ejecutar el smoke test
docker-compose exec oracle-net python oracle_net.py

# Entrenar el modelo manualmente
docker-compose exec oracle-net python train_oracle.py
```

### Escalar servicios
```bash
# Ejecutar múltiples instancias del Gossip Network
docker-compose up -d --scale gossip-network=3
```

## Configuración de GPU (Opcional)

Si tienes una GPU NVIDIA (como la Quadro K4200) y quieres usarla:

### 1. Instalar NVIDIA Container Toolkit
```bash
# Ubuntu/Debian
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | \
  sudo tee /etc/apt/sources.list.d/nvidia-docker.list

sudo apt-get update && sudo apt-get install -y nvidia-docker2
sudo systemctl restart docker
```

### 2. Modificar docker-compose.yml

Agregar para el servicio `oracle-net`:
```yaml
oracle-net:
  # ... otras configuraciones
  deploy:
    resources:
      reservations:
        devices:
          - driver: nvidia
            count: 1
            capabilities: [gpu]
  environment:
    - CUDA_VISIBLE_DEVICES=0  # Cambiar de -1 a 0
```

### 3. Reconstruir y levantar
```bash
docker-compose up --build oracle-net
```

## Estructura de Volúmenes

```
MinorityReport/
├── models/              # Modelos entrenados (.pth files)
│   └── oracle_net_best.pth
├── logs/                # Logs de entrenamiento
│   └── training.log
└── (Neo4j volumes gestionados por Docker)
```

## Integración con Neo4j

### Inicialización Automática

El script `scripts/init-neo4j.sh` se ejecuta automáticamente al iniciar Neo4j y crea:
- 5 ubicaciones de ejemplo (Downtown Plaza, Back Alley, Metro Station, etc.)
- 6 conexiones (calles) entre ubicaciones
- Propiedades de vigilancia y seguridad

### Queries de Ejemplo

Una vez que Neo4j esté corriendo, puedes ejecutar estas queries en el Browser:

```cypher
// Ver todas las ubicaciones
MATCH (n:Location) RETURN n

// Ver todas las conexiones
MATCH (a)-[r:CONNECTED_TO]->(b) RETURN a, r, b

// Encontrar ubicaciones con baja vigilancia
MATCH (n:Location)
WHERE n.policeLevel < 0.4
RETURN n.name, n.policeLevel
ORDER BY n.policeLevel ASC

// Calcular ruta más corta (por distancia)
MATCH (start:Location {name: 'Downtown Plaza'}), 
      (end:Location {name: 'Warehouse District'}),
      path = shortestPath((start)-[:CONNECTED_TO*]-(end))
RETURN path
```

### Ejecutar OracleNet con Neo4j

```bash
# Asegúrate de que Neo4j esté corriendo
docker-compose up -d neo4j

# Espera a que esté saludable (health check)
docker-compose ps neo4j

# Ejecuta el script de integración
docker-compose exec oracle-net python neo4j_oracle_integration.py
```

## Variables de Entorno

Puedes personalizar la configuración mediante variables de entorno:

```bash
# Crear archivo .env
cat > .env <<EOF
NEO4J_URI=bolt://neo4j:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=tu_password_seguro
CUDA_VISIBLE_DEVICES=-1
EOF

# Docker Compose cargará automáticamente este archivo
docker-compose up -d
```

## Troubleshooting

### Neo4j no inicia
```bash
# Ver logs detallados
docker-compose logs neo4j

# Verificar que los puertos no estén en uso
sudo netstat -tulpn | grep -E '7474|7687'

# Reiniciar el servicio
docker-compose restart neo4j
```

### OracleNet no puede conectarse a Neo4j
```bash
# Verificar conectividad de red
docker-compose exec oracle-net ping neo4j

# Verificar que Neo4j esté saludable
docker-compose ps neo4j

# Ver variables de entorno
docker-compose exec oracle-net env | grep NEO4J
```

### Error de memoria en Neo4j
```bash
# Ajustar límites de memoria en docker-compose.yml
# Reducir NEO4J_dbms_memory_heap_max__size a 1G
# Reducir NEO4J_dbms_memory_pagecache_size a 512m
```

### GPU no detectada
```bash
# Verificar que nvidia-docker esté instalado
docker run --rm --gpus all nvidia/cuda:11.8.0-base-ubuntu22.04 nvidia-smi

# Si falla, reinstalar nvidia-container-toolkit
```

## Integración con Otras Branches

Este setup de Docker está diseñado para integrarse fácilmente con otras branches que estén trabajando en:
- API REST/GraphQL para OracleNet
- Frontend de visualización
- Simulación de ciudad en tiempo real
- Dashboard de análisis

### Para integrar tu branch:

1. **Agrega tu servicio al docker-compose.yml**:
```yaml
  tu-servicio:
    build:
      context: ./tu-directorio
      dockerfile: Dockerfile
    depends_on:
      - neo4j
      - oracle-net
    networks:
      - minority-report-network
```

2. **Usa las variables de entorno existentes** para conectarte a Neo4j

3. **Prueba la integración**:
```bash
docker-compose up --build
```

## Producción

Para deployment en producción, considera:

1. **Usar secretos de Docker** en lugar de passwords en texto plano
2. **Configurar backup automático** de Neo4j
3. **Usar imágenes multi-stage** para reducir tamaño
4. **Implementar health checks** para todos los servicios
5. **Agregar reverse proxy** (nginx/traefik)
6. **Monitoreo con Prometheus + Grafana**

## Referencias

- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [Neo4j Docker Documentation](https://neo4j.com/docs/operations-manual/current/docker/)
- [NVIDIA Container Toolkit](https://github.com/NVIDIA/nvidia-docker)

---

**Autor**: The Oracle  
**Proyecto**: Minority Report - Robbers Side  
**Última actualización**: 2026-01-21
