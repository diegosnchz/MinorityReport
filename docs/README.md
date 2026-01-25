# MinorityReport - Documentación Principal

Bienvenido a MinorityReport. Esta carpeta contiene toda la documentación necesaria.

## 📚 Documentación Principal (Lee Esto Primero)

### 1. [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) - Guía Definitiva ⭐
**Lee esto para**: 
- Requerimientos del sistema (hardware/software)
- Instalación inicial
- Deployment paso a paso
- Uso de modelos entrenados
- Integración con backend
- Testing y verificación

**Secciones principales**:
- Requerimientos Hardware/Software
- Instalación de Python + Dependencias
- 3 opciones de Deployment (automatizado, manual, CPU-only)
- Uso detallado de Neo4j
- Parámetros de entrenamiento
- Verificación completa del sistema

---

### 2. [TROUBLESHOOTING.md](TROUBLESHOOTING.md) - Solución de Problemas ⭐
**Lee esto si**: 
- Algo no funciona
- Necesitas solucionar un error específico
- Quieres entender por qué algo falló

**Contiene 20 errores comunes con soluciones**:
1. Errores de Instalación
2. Errores de Docker y Neo4j
3. Errores de Python y PyTorch
4. Errores de Entrenamiento
5. Errores de Datos y Cypher
6. Errores de CUDA y GPU
7. Errores de Performance

---

## 🚀 Inicio Rápido (5 minutos)

```powershell
# 1. Ir a directorio del proyecto
cd "D:\Repositorios Github\MinorityReport"

# 2. Ejecutar deployment automático
.\deploy_real_environment.ps1 -Citizens 200 -Epochs 100

# ¡Listo! Los modelos estarán entrenados en ~5 minutos
```

---

## 📖 Flujo Recomendado de Lectura

**Si eres nuevo**:
1. Lee DEPLOYMENT_GUIDE.md → Sección "Requerimientos del Sistema"
2. Lee DEPLOYMENT_GUIDE.md → Sección "Instalación Inicial"
3. Lee DEPLOYMENT_GUIDE.md → Sección "Deployment Rápido"
4. Ejecuta `.\deploy_real_environment.ps1`

**Si algo falla**:
1. Lee el error completo
2. Busca en TROUBLESHOOTING.md
3. Ejecuta la solución propuesta

**Si necesitas entrenar con tus datos**:
1. Lee DEPLOYMENT_GUIDE.md → "Entrenamiento de Modelos"
2. Modifica `scripts/seed_neo4j.py` para tu dataset
3. Ejecuta `python scripts/train_with_neo4j.py`

**Si necesitas integrar con tu API**:
1. Lee DEPLOYMENT_GUIDE.md → "Uso Detallado" → "Integración con API Backend"
2. Copia el código ejemplo
3. Adapta a tu framework (FastAPI, Flask, Django, etc)

---

## 🎯 Paths de Archivos Importantes

```
MinorityReport/
├── docs/
│   ├── DEPLOYMENT_GUIDE.md         ← Guía principal (EMPIEZA AQUÍ)
│   └── TROUBLESHOOTING.md          ← Errores y soluciones
├── scripts/
│   ├── seed_neo4j.py               ← Generar datos
│   └── train_with_neo4j.py         ← Entrenar modelos
├── src/
│   ├── models/
│   │   ├── graphsage_model.py      ← Crime Prediction
│   │   └── oracle_net.py           ← Escape Routes
│   └── utils/
│       └── neo4j_data_fetcher.py   ← Obtener datos
├── models/
│   ├── crime_prediction_best.pt    ← Modelo entrenado
│   └── escape_route_best.pt        ← Modelo entrenado
├── docker-compose.yml              ← Configuración Docker
└── deploy_real_environment.ps1     ← Deployment automatizado
```

---

## 🔗 Accesos Rápidos

| Componente | URL/Comando | Credenciales |
|-----------|-----------|--------------|
| **Neo4j Browser** | http://localhost:7474 | neo4j / minorityreport |
| **Neo4j Bolt** | bolt://localhost:7687 | neo4j / minorityreport |
| **Python venv** | `.\venv311\Scripts\Activate.ps1` | - |
| **Training** | `python scripts/train_with_neo4j.py` | - |
| **Seed Data** | `python scripts/seed_neo4j.py` | - |

---

## ✅ Checklist Pre-Deployment

- [ ] Python 3.11.0+  instalado
- [ ] Docker Desktop instalado y corriendo
- [ ] 8 GB RAM disponible
- [ ] 20 GB espacio en disco
- [ ] Git instalado
- [ ] Repository clonado

Si todo está ✅, ejecuta:
```powershell
.\deploy_real_environment.ps1
```

---

## 📊 Estructura de Documentos Deprecados

Otros documentos en esta carpeta son **históricos/de referencia** y no son necesarios para el deployment. Se mantienen por:
- Histórico de decisiones de arquitectura
- Referencia para desarrolladores
- Contexto del proyecto

Para desarrollo/troubleshooting, solo necesitas:
- **DEPLOYMENT_GUIDE.md**
- **TROUBLESHOOTING.md**

---

## 🆘 Si Algo Aún No Funciona

1. **Revisa TROUBLESHOOTING.md** → Busca tu error
2. **Si tu error no está**:
   - Obtén el stack trace completo
   - Ejecuta: `python -c "import torch; print(torch.__version__)"`
   - Ejecuta: `docker ps`
   - Ejecuta: `python scripts/seed_neo4j.py --citizens 10` (test rápido)
3. **Abre un issue** en GitHub con la información anterior

---

## 📞 Información de Soporte

- **Repositorio**: https://github.com/diegosnchz/MinorityReport
- **Issues**: https://github.com/diegosnchz/MinorityReport/issues
- **Rama principal**: feature/gat-model
- **Última actualización**: 25 Enero 2026

---

**¡Bienvenido! Comienza con DEPLOYMENT_GUIDE.md →**
