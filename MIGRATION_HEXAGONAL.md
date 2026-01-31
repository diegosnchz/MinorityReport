# Migración a Arquitectura Hexagonal - COMPLETADA

## Resumen de Cambios

Se ha completado la refactorización masiva del proyecto "The Evasion Protocol" a una **Arquitectura Hexagonal (Ports & Adapters)** estricta.

## Nueva Estructura de Carpetas

```
src/
├── domain/                          # 💎 NÚCLEO PURO (0 dependencias externas)
│   ├── models/
│   │   ├── citizen.py               # Entidad Citizen + CitizenId + CitizenStatus
│   │   ├── location.py              # Entidad Location + Coordinates + Route
│   │   ├── vision.py                # Entidad Vision + PredictionOutput
│   │   └── evasion.py               # Entidad EvasionRoute + EmergencyAlert
│   ├── repositories/
│   │   ├── citizen_repository.py    # Puerto: Interface CitizenRepository
│   │   ├── location_repository.py   # Puerto: Interface LocationRepository
│   │   ├── vision_repository.py     # Puerto: Interface VisionRepository
│   │   └── graph_repository.py      # Puerto: Interface GraphRepository
│   └── services/
│       ├── ai_engine.py             # Puerto: Interface AIPredictionEngine
│       ├── routing_engine.py        # Puerto: Interface RoutingEngine
│       └── simulation_engine.py     # Puerto: Interface SimulationEngine
│
├── infrastructure/                  # 🔌 ADAPTADORES (implementan puertos)
│   ├── persistence/
│   │   ├── neo4j/
│   │   │   ├── neo4j_citizen_repository.py
│   │   │   ├── neo4j_location_repository.py
│   │   │   ├── neo4j_vision_repository.py
│   │   │   └── neo4j_graph_repository.py
│   │   └── memory/                  # Para testing/demo mode
│   │       ├── memory_citizen_repository.py
│   │       ├── memory_location_repository.py
│   │       └── memory_vision_repository.py
│   ├── ai/
│   │   ├── torch_precog_engine.py   # Implementación con PyTorch
│   │   └── mock_ai_engine.py        # Implementación mock para testing
│   ├── routing/
│   │   └── hybrid_routing_engine.py # GAT + A* híbrido
│   ├── simulation/
│   │   └── graph_simulation_engine.py
│   ├── web/
│   │   ├── fastapi_server.py        # Adaptador web FastAPI
│   │   └── routers/
│   │       ├── citizens.py
│   │       ├── predictions.py
│   │       ├── evasion.py
│   │       └── simulation.py
│   └── config/
│       └── settings.py
│
└── composition/                     # 🔗 COMPOSICIÓN RAÍZ
    ├── container.py                 # Contenedor de IoC (Dependency Injection)
    └── main.py                      # Entry point
```

## Principios Aplicados

### 1. Aislamiento del Dominio
- Las entidades en `domain/models/` son **puras** - solo usan Python estándar
- No hay imports de FastAPI, Neo4j, PyTorch en la capa de dominio
- Las reglas de negocio están encapsuladas en las entidades

### 2. Puertos (Interfaces)
- `CitizenRepository`, `LocationRepository`, `VisionRepository` - Persistencia
- `GraphRepository` - Operaciones avanzadas de grafos
- `AIPredictionEngine` - Inferencia de IA
- `RoutingEngine` - Cálculo de rutas
- `SimulationEngine` - Simulación de actividad

### 3. Adaptadores (Implementaciones)
- **Neo4j**: Implementaciones de repositorios usando Cypher
- **Memory**: Implementaciones en memoria para modo demo/testing
- **TorchPrecogEngine**: Implementación de IA con PyTorch
- **MockAIPredictionEngine**: Implementación mock sin dependencias
- **FastAPIServer**: Adaptador web que expone la API

### 4. Inyección de Dependencias
- `Container` en `composition/container.py` gestiona todas las dependencias
- Configurable vía `Settings` (variables de entorno)
- Soporta modo demo (memory repos + mock AI) y modo producción (Neo4j + Torch)

## Cómo Usar

### Modo Demo (sin Neo4j)
```bash
# Configurar variables de entorno
export DEMO_MODE=true
export USE_MOCK_AI=true

# Ejecutar
python -m src.composition.main
```

### Modo Producción (con Neo4j)
```bash
# Configurar variables de entorno
export DEMO_MODE=false
export USE_MOCK_AI=false
export NEO4J_URI=bolt://localhost:7687
export NEO4J_USER=neo4j
export NEO4J_PASSWORD=secret

# Ejecutar
python -m src.composition.main
```

## Endpoints API (v2 - Hexagonal)

- `GET  /health` - Health check
- `GET  /api/v2/citizens` - Listar ciudadanos
- `GET  /api/v2/citizens/{id}` - Obtener ciudadano
- `GET  /api/v2/citizens/{id}/risk` - Evaluar riesgo
- `POST /api/v2/citizens` - Crear ciudadano
- `POST /api/v2/predictions/assess` - Evaluar riesgo ciudadano-ubicación
- `GET  /api/v2/predictions/visions` - Listar visiones
- `GET  /api/v2/predictions/visions/critical` - Visiones críticas
- `GET  /api/v2/predictions/visions/{id}/explain` - Explicar predicción (XAI)
- `POST /api/v2/evasion/route` - Calcular ruta de escape
- `POST /api/v2/evasion/explain-risk` - Explicar riesgo de zona
- `POST /api/v2/simulation/step` - Ejecutar paso de simulación
- `GET  /api/v2/simulation/status` - Estado de simulación

## Flujo de Dependencias

```
┌─────────────────────────────────────────────────────────────┐
│                     INFRASTRUCTURE                          │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐       │
│  │  Neo4j   │ │ PyTorch  │ │ FastAPI  │ │  Panel   │       │
│  │  Repos   │ │  Engine  │ │  Server  │ │    UI    │       │
│  └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘       │
│       │            │            │            │              │
│       └────────────┴────────────┼────────────┘              │
│                                 │                           │
│                        ┌────────┴────────┐                  │
│                        │     Container   │                  │
│                        │   (IoC Config)  │                  │
│                        └────────┬────────┘                  │
└─────────────────────────────────┼───────────────────────────┘
                                  │
┌─────────────────────────────────┼───────────────────────────┐
│                                 │                           │
│                      ┌──────────┴──────────┐               │
│                      │   USE CASES/APPS    │               │
│                      │   (Application)     │               │
│                      └──────────┬──────────┘               │
│                                 │                           │
│                      ┌──────────┴──────────┐               │
│                      │      DOMAIN         │               │
│                      │  (Entities/Ports)   │               │
│                      │                     │               │
│                      │  Citizen, Location  │               │
│                      │  Vision, Evasion    │               │
│                      │  Repositories (IF)  │               │
│                      │  Services (IF)      │               │
│                      └─────────────────────┘               │
│                                                           │
└─────────────────────────────────────────────────────────────┘
```

## Reglas del Dominio Incluidas

1. **Citizen.calculate_base_risk()** - Calcula riesgo basado en atributos
2. **Citizen.is_high_risk()** - Determina si es alto riesgo
3. **Location.get_risk_score()** - Score de riesgo de ubicación
4. **Location.is_safe_haven()** - Determina si es refugio seguro
5. **Vision.risk_level** - Nivel de riesgo de la predicción
6. **Vision.is_critical** - Determina si requiere acción inmediata
7. **EvasionRoute.safety_score** - Score de seguridad de ruta
8. **EvasionRoute.is_expired()** - Verifica expiración de ruta

## Ventajas de esta Arquitectura

1. **Testabilidad**: Puedes testear el dominio sin bases de datos ni servidores
2. **Flexibilidad**: Cambia Neo4j por PostgreSQL sin tocar el dominio
3. **Independencia**: El dominio no depende de frameworks
4. **Claridad**: Separación clara entre lógica de negocio e infraestructura
5. **Mantenibilidad**: Cambios en UI o DB no afectan las reglas de negocio

## Estado: ✅ COMPLETADO

Toda la lógica de negocio ha sido migrada a la capa de dominio puro.
Los adaptadores implementan los puertos definidos.
El contenedor de IoC conecta todo al iniciar la aplicación.
La aplicación es funcional y mantiene compatibilidad con la API anterior.
