import React, { useMemo } from 'react';
import { usePrecog } from '../contexts/PrecogContext';
import { Activity, Zap, Target, MousePointer, TrendingUp, Brain } from 'lucide-react';

export function PrecogDebugger() {
  const { 
    isTracking, 
    trajectory, 
    lastPrediction, 
    confidence,
    startTracking,
    stopTracking,
    getStats
  } = usePrecog();

  const stats = useMemo(() => getStats(), [getStats, trajectory.length, lastPrediction]);

  return (
    <div className="precog-debugger">
      <div className="debugger-header">
        <Brain className="w-5 h-5" />
        <h3>Precog Engine v2.0</h3>
        <div className={`status-badge ${isTracking ? 'active' : 'inactive'}`}>
          {isTracking ? 'TRACKING' : 'STANDBY'}
        </div>
      </div>

      <div className="debugger-controls">
        <button
          onClick={isTracking ? stopTracking : startTracking}
          className={`control-btn ${isTracking ? 'stop' : 'start'}`}
        >
          {isTracking ? 'Detener' : 'Iniciar'} Tracking
        </button>
      </div>

      <div className="debugger-stats">
        <StatCard
          icon={<MousePointer className="w-4 h-4" />}
          label="Puntos de Trayectoria"
          value={stats.trajectoryLength}
          max={50}
        />
        <StatCard
          icon={<Target className="w-4 h-4" />}
          label="Precisión Predicción"
          value={`${(stats.predictionAccuracy * 100).toFixed(1)}%`}
        />
        <StatCard
          icon={<Zap className="w-4 h-4" />}
          label="Cache Hit Rate"
          value={`${(stats.cacheHitRate * 100).toFixed(1)}%`}
        />
        <StatCard
          icon={<Activity className="w-4 h-4" />}
          label="Elementos Activos"
          value={stats.activeElements}
        />
      </div>

      <div className="confidence-meter">
        <div className="meter-label">
          <TrendingUp className="w-4 h-4" />
          <span>Confianza Actual</span>
        </div>
        <div className="meter-bar">
          <div 
            className="meter-fill"
            style={{ 
              width: `${confidence * 100}%`,
              backgroundColor: confidence >= 0.7 ? '#00ff88' : confidence >= 0.5 ? '#ffaa00' : '#ff4444'
            }}
          />
        </div>
        <span className="meter-value">{(confidence * 100).toFixed(1)}%</span>
      </div>

      {lastPrediction && (
        <div className="last-prediction">
          <h4>Última Predicción</h4>
          <div className="prediction-details">
            <span className="prediction-intent">{lastPrediction.intent}</span>
            <span className="prediction-target">→ {lastPrediction.target}</span>
            <span className="prediction-confidence">
              {(lastPrediction.confidence * 100).toFixed(1)}%
            </span>
          </div>
          <div className="prediction-type">
            Tipo: <strong>{lastPrediction.type}</strong>
          </div>
        </div>
      )}

      <TrajectoryVisualizer trajectory={trajectory} />

      <style>{`
        .precog-debugger {
          position: fixed;
          top: 20px;
          right: 20px;
          width: 320px;
          background: rgba(10, 10, 20, 0.95);
          border: 1px solid rgba(0, 255, 136, 0.3);
          border-radius: 12px;
          padding: 16px;
          color: #fff;
          font-family: 'JetBrains Mono', monospace;
          font-size: 12px;
          z-index: 9999;
          backdrop-filter: blur(10px);
          box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4);
        }

        .debugger-header {
          display: flex;
          align-items: center;
          gap: 8px;
          margin-bottom: 16px;
          padding-bottom: 12px;
          border-bottom: 1px solid rgba(255, 255, 255, 0.1);
        }

        .debugger-header h3 {
          margin: 0;
          font-size: 14px;
          font-weight: 600;
          color: #00ff88;
          text-transform: uppercase;
          letter-spacing: 1px;
        }

        .status-badge {
          margin-left: auto;
          padding: 4px 8px;
          border-radius: 4px;
          font-size: 10px;
          font-weight: 700;
        }

        .status-badge.active {
          background: rgba(0, 255, 136, 0.2);
          color: #00ff88;
        }

        .status-badge.inactive {
          background: rgba(255, 68, 68, 0.2);
          color: #ff4444;
        }

        .debugger-controls {
          margin-bottom: 16px;
        }

        .control-btn {
          width: 100%;
          padding: 8px 16px;
          border: none;
          border-radius: 6px;
          font-family: inherit;
          font-size: 12px;
          font-weight: 600;
          cursor: pointer;
          transition: all 0.2s;
          text-transform: uppercase;
          letter-spacing: 1px;
        }

        .control-btn.start {
          background: linear-gradient(135deg, #00ff88, #00cc6a);
          color: #000;
        }

        .control-btn.stop {
          background: linear-gradient(135deg, #ff4444, #cc3333);
          color: #fff;
        }

        .control-btn:hover {
          transform: translateY(-1px);
          box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
        }

        .debugger-stats {
          display: grid;
          grid-template-columns: 1fr 1fr;
          gap: 8px;
          margin-bottom: 16px;
        }

        .stat-card {
          background: rgba(255, 255, 255, 0.05);
          border-radius: 8px;
          padding: 10px;
          border: 1px solid rgba(255, 255, 255, 0.1);
        }

        .stat-icon {
          color: #00ff88;
          margin-bottom: 4px;
        }

        .stat-label {
          font-size: 10px;
          color: rgba(255, 255, 255, 0.6);
          margin-bottom: 4px;
        }

        .stat-value {
          font-size: 16px;
          font-weight: 700;
          color: #fff;
        }

        .stat-max {
          font-size: 10px;
          color: rgba(255, 255, 255, 0.4);
        }

        .confidence-meter {
          margin-bottom: 16px;
        }

        .meter-label {
          display: flex;
          align-items: center;
          gap: 6px;
          margin-bottom: 8px;
          color: rgba(255, 255, 255, 0.8);
        }

        .meter-bar {
          height: 8px;
          background: rgba(255, 255, 255, 0.1);
          border-radius: 4px;
          overflow: hidden;
          margin-bottom: 4px;
        }

        .meter-fill {
          height: 100%;
          border-radius: 4px;
          transition: width 0.3s ease, background-color 0.3s ease;
        }

        .meter-value {
          display: block;
          text-align: right;
          font-size: 11px;
          color: rgba(255, 255, 255, 0.6);
        }

        .last-prediction {
          background: rgba(0, 255, 136, 0.1);
          border: 1px solid rgba(0, 255, 136, 0.3);
          border-radius: 8px;
          padding: 12px;
          margin-bottom: 16px;
        }

        .last-prediction h4 {
          margin: 0 0 8px 0;
          font-size: 11px;
          color: #00ff88;
          text-transform: uppercase;
          letter-spacing: 1px;
        }

        .prediction-details {
          display: flex;
          flex-wrap: wrap;
          gap: 8px;
          margin-bottom: 8px;
        }

        .prediction-intent {
          background: rgba(0, 255, 136, 0.2);
          color: #00ff88;
          padding: 2px 8px;
          border-radius: 4px;
          font-size: 10px;
          text-transform: uppercase;
        }

        .prediction-target {
          color: rgba(255, 255, 255, 0.8);
          font-size: 11px;
        }

        .prediction-confidence {
          margin-left: auto;
          font-weight: 700;
          color: #00ff88;
        }

        .prediction-type {
          font-size: 10px;
          color: rgba(255, 255, 255, 0.6);
        }

        .trajectory-viz {
          background: rgba(0, 0, 0, 0.5);
          border-radius: 8px;
          padding: 8px;
        }

        .trajectory-viz h4 {
          margin: 0 0 8px 0;
          font-size: 11px;
          color: rgba(255, 255, 255, 0.6);
          text-transform: uppercase;
        }

        .trajectory-canvas {
          width: 100%;
          height: 100px;
          background: rgba(0, 0, 0, 0.3);
          border-radius: 4px;
        }
      `}</style>
    </div>
  );
}

function StatCard({ 
  icon, 
  label, 
  value, 
  max 
}: { 
  icon: React.ReactNode; 
  label: string; 
  value: string | number;
  max?: number;
}) {
  return (
    <div className="stat-card">
      <div className="stat-icon">{icon}</div>
      <div className="stat-label">{label}</div>
      <div className="stat-value">
        {value}
        {max !== undefined && <span className="stat-max"> / {max}</span>}
      </div>
    </div>
  );
}

function TrajectoryVisualizer({ trajectory }: { trajectory: Array<{ x: number; y: number }> }) {
  const canvasRef = React.useRef<HTMLCanvasElement>(null);

  React.useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas || trajectory.length < 2) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    // Clear canvas
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    // Draw trajectory
    ctx.strokeStyle = '#00ff88';
    ctx.lineWidth = 2;
    ctx.lineCap = 'round';
    ctx.lineJoin = 'round';

    // Scale points to canvas
    const minX = Math.min(...trajectory.map(p => p.x));
    const maxX = Math.max(...trajectory.map(p => p.x));
    const minY = Math.min(...trajectory.map(p => p.y));
    const maxY = Math.max(...trajectory.map(p => p.y));

    const scaleX = canvas.width / Math.max(maxX - minX, 1);
    const scaleY = canvas.height / Math.max(maxY - minY, 1);
    const scale = Math.min(scaleX, scaleY) * 0.8;

    const offsetX = (canvas.width - (maxX - minX) * scale) / 2;
    const offsetY = (canvas.height - (maxY - minY) * scale) / 2;

    ctx.beginPath();
    trajectory.forEach((point, index) => {
      const x = (point.x - minX) * scale + offsetX;
      const y = (point.y - minY) * scale + offsetY;
      
      if (index === 0) {
        ctx.moveTo(x, y);
      } else {
        ctx.lineTo(x, y);
      }
    });
    ctx.stroke();

    // Draw gradient effect
    const gradient = ctx.createLinearGradient(0, 0, canvas.width, 0);
    gradient.addColorStop(0, 'rgba(0, 255, 136, 0)');
    gradient.addColorStop(1, 'rgba(0, 255, 136, 0.3)');
    ctx.strokeStyle = gradient;
    ctx.lineWidth = 4;
    ctx.stroke();

  }, [trajectory]);

  return (
    <div className="trajectory-viz">
      <h4>Trayectoria del Mouse</h4>
      <canvas
        ref={canvasRef}
        width={280}
        height={100}
        className="trajectory-canvas"
      />
    </div>
  );
}
