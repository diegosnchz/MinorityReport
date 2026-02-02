# 🧠 Minority Report - Precog Engine v2.0

Sistema de monitoreo predictivo con Motor Precog Zero-Latency. Interfaz diseñada con el **Vercel Design System (Geist)** - minimalista, limpia y profesional.

## 🎨 Design System: Vercel Geist

La interfaz sigue estrictamente el sistema de diseño de Vercel:

- **Filosofía**: Minimalismo extremo, orientado al contenido, "Industrial Clean"
- **Colores**: 
  - Fondo: Blanco puro (#FFFFFF)
  - Texto: Negro (#000000) y grises (#666666)
  - Acento: Vercel Blue (#0070F3) solo para CTAs
  - Bordes: Gris muy sutil (#EAEAEA)
- **Tipografía**: Inter / System fonts con tracking-tight
- **Componentes**: Bordes casi cuadrados (border-radius: 6px), sombras sutiles

## 📦 Librerías Necesarias

```bash
cd frontend
npm install
```

### Dependencias Principales

- **React 18** + **TypeScript** - UI Framework
- **Axios** - HTTP Client para prefetching
- **Leaflet + React-Leaflet** - Mapas interactivos
- **Lucide React** - Iconos modernos
- **Zustand** - State management

### Dev Dependencies

- **Vite** - Build tool y dev server
- **TailwindCSS** - Utility-first CSS
- **TypeScript** - Type checking
- **ESLint** - Linting

## 🚀 Inicio Rápido

### 1. Instalar Dependencias

```bash
cd frontend
npm install
```

### 2. Configurar Variables de Entorno

```bash
cp .env.example .env
```

Edita `.env`:
```env
VITE_API_URL=http://localhost:8000/api/v2
```

### 3. Iniciar el Servidor

```bash
npm run dev
```

Abre `http://localhost:3000`

## 🎯 Características

### 1. Mapa Interactivo Real
- Visualización geográfica con Leaflet
- Marcadores de riesgo por ubicación
- Datos reales del backend (con fallback a demo)
- Popup con información detallada

### 2. Tabla de Ciudadanos
- Datos reales de la API
- Indicadores de riesgo visuales
- Estados: Activo, Vigilado, Intervenir, Detenido
- Fotos de avatar generadas por nombre

### 3. Motor Precog (Invisible)
- Funciona en segundo plano
- Precarga datos cuando detecta intención > 60%
- Indicador sutil en esquina inferior derecha
- Sin invadir la UI con gráficos

### 4. Diseño Vercel
- Layout limpio con mucho whitespace
- Cards minimalistas con bordes sutiles
- Header sticky con blur effect
- Tipografía legible y profesional

## 📁 Estructura

```
frontend/
├── src/
│   ├── components/
│   │   ├── Dashboard.tsx      # Vista principal
│   │   ├── MapView.tsx        # Mapa con Leaflet
│   │   └── CitizenTable.tsx   # Tabla de datos
│   ├── contexts/
│   │   └── PrecogContext.tsx  # Motor predictivo
│   ├── services/
│   │   └── api.ts             # API + prefetching
│   ├── App.tsx                # App con toggle
│   └── index.css              # Estilos Geist
└── README.md
```

## 🎮 Uso

### Vista Normal
Dashboard estándar con mapa y tabla de datos.

### Activar Precog
1. Haz clic en **"Activar Precog"** (esquina superior derecha)
2. El motor comenzará a trackear el mouse
3. Verás un indicador sutil en la esquina inferior derecha cuando esté precargando

### Indicador Precog
- **Gris**: Monitoreando
- **Azul**: Analizando patrones
- **Azul oscuro**: Precargando datos

## ⚙️ Configuración Precog

```tsx
<PrecogProvider
  config={{
    confidenceThreshold: 0.6,    // Umbral para prefetch
    maxTrajectoryLength: 30,     // Puntos de trayectoria
    predictionInterval: 100,     // ms entre análisis
    cacheTTL: 300000,            // 5 min caché
    enableWebWorker: true        // Usar Worker
  }}
>
  <App />
</PrecogProvider>
```

## 🔧 Personalización

### Cambiar colores
Edita las variables CSS en `index.css`:

```css
:root {
  --geist-accent: #0070f3;  /* Tu color */
}
```

### Agregar nuevos endpoints
En `services/api.ts`:

```typescript
preloadCustomData(): void {
  this.prefetch('/mi-endpoint', 'high');
}
```

## 📊 Datos

La app intenta conectar con el backend Python en `localhost:8000`. Si no está disponible, usa datos demo.

Para usar datos reales:
1. Asegúrate de que el backend Python esté corriendo
2. Verifica `VITE_API_URL` apunte a tu API

## 🐛 Troubleshooting

**Mapa no carga**: Recarga la página (Leaflet a veces necesita recarga)
**Datos no aparecen**: Verifica que el backend esté en `localhost:8000`
**Precog no funciona**: Activa el toggle y espera 2-3 segundos

---

**Diseño limpio, datos reales, predicciones invisibles.** 🎯
