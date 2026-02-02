import { useEffect, useState } from 'react';
import { usePrecog } from '../contexts/PrecogContext';
import { precogApi } from '../services/api';
import { MapView } from './MapView';
import { CitizenTable } from './CitizenTable';
import { Users, MapPin, Activity, AlertTriangle, Brain, Shield } from 'lucide-react';

interface Stats {
  totalCitizens: number;
  highRiskCount: number;
  activePredictions: number;
  totalLocations: number;
  crimesToday: number;
  interventionRate: number;
}

export function Dashboard() {
  const { isTracking, getStats, confidence } = usePrecog();
  const [stats, setStats] = useState<Stats>({
    totalCitizens: 0,
    highRiskCount: 0,
    activePredictions: 0,
    totalLocations: 0,
    crimesToday: 0,
    interventionRate: 0
  });
  const [precogStats, setPrecogStats] = useState({
    trajectoryLength: 0,
    predictionAccuracy: 0,
    cacheHitRate: 0,
    activeElements: 0
  });

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const [citizens, locations] = await Promise.all([
          precogApi.fetch<Array<{ risk_seed: number }>>('/citizens?limit=1000'),
          precogApi.fetch<Array<unknown>>('/locations')
        ]);

        const highRisk = citizens.filter(c => c.risk_seed > 0.7).length;
        
        setStats({
          totalCitizens: citizens.length,
          highRiskCount: highRisk,
          activePredictions: Math.floor(Math.random() * 30) + 10,
          totalLocations: locations.length,
          crimesToday: Math.floor(Math.random() * 15) + 5,
          interventionRate: Math.round((highRisk / citizens.length) * 100)
        });
      } catch (error) {
        console.warn('Using demo stats:', error);
        setStats({
          totalCitizens: 1247,
          highRiskCount: 89,
          activePredictions: 24,
          totalLocations: 156,
          crimesToday: 12,
          interventionRate: 7
        });
      }
    };

    fetchStats();
    
    const interval = setInterval(() => {
      setPrecogStats(getStats());
    }, 1000);

    return () => clearInterval(interval);
  }, [getStats]);

  return (
    <div className="container-vercel" style={{ paddingTop: '24px', paddingBottom: '48px' }}>
      {/* Header */}
      <header style={{ marginBottom: '32px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '8px' }}>
          <Shield size={24} style={{ color: 'var(--geist-foreground)' }} />
          <h1 style={{ fontSize: '24px', fontWeight: 700, letterSpacing: '-0.02em' }}>
            Minority Report
          </h1>
          {isTracking && (
            <span style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '4px',
              padding: '2px 8px',
              fontSize: '11px',
              fontWeight: 500,
              borderRadius: '4px',
              background: 'rgba(0, 112, 243, 0.1)',
              color: 'var(--geist-accent)',
            }}>
              <Brain size={12} />
              Precog Activo
            </span>
          )}
        </div>
        <p style={{ color: 'var(--geist-gray-400)', fontSize: '14px', margin: 0 }}>
          Sistema de predicción y monitoreo de comportamiento criminal en tiempo real
        </p>
      </header>

      {/* Stats Grid */}
      <div style={{ 
        display: 'grid', 
        gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', 
        gap: '16px',
        marginBottom: '32px'
      }}>
        <StatCard 
          icon={<Users size={18} />}
          label="Ciudadanos"
          value={stats.totalCitizens.toLocaleString()}
          trend="+12 esta semana"
        />
        <StatCard 
          icon={<AlertTriangle size={18} />}
          label="Alto Riesgo"
          value={stats.highRiskCount.toString()}
          valueColor="var(--geist-error)"
          trend={`${stats.interventionRate}% del total`}
        />
        <StatCard 
          icon={<MapPin size={18} />}
          label="Ubicaciones"
          value={stats.totalLocations.toString()}
          trend="8 zonas críticas"
        />
        <StatCard 
          icon={<Activity size={18} />}
          label="Predicciones Hoy"
          value={stats.activePredictions.toString()}
          trend="3 requieren atención"
        />
      </div>

      {/* Main Content */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr', gap: '32px' }}>
        {/* Map Section */}
        <div>
          <SectionHeader 
            icon={<MapPin size={18} />}
            title="Mapa de Riesgo"
            subtitle="Visualización geográfica de incidentes y niveles de riesgo por zona"
          />
          <MapView />
        </div>

        {/* Citizens Table */}
        <div>
          <SectionHeader 
            icon={<Users size={18} />}
            title="Ciudadanos Monitoreados"
            subtitle="Listado de individuos bajo vigilancia activa"
          />
          <CitizenTable />
        </div>
      </div>

      {/* Precog Minimal Indicator */}
      {isTracking && (
        <div className={`precog-indicator ${confidence > 0.7 ? 'active' : ''}`}>
          <div className="precog-indicator-dot"></div>
          <span>
            {confidence > 0.7 
              ? 'Precargando datos...' 
              : confidence > 0.4 
                ? 'Analizando patrones...'
                : 'Monitoreando...'}
          </span>
          {precogStats.cacheHitRate > 0 && (
            <span style={{ color: 'var(--geist-gray-300)', marginLeft: '4px' }}>
              ({Math.round(precogStats.cacheHitRate * 100)}% cache hit)
            </span>
          )}
        </div>
      )}
    </div>
  );
}

function StatCard({ 
  icon, 
  label, 
  value, 
  trend,
  valueColor = 'var(--geist-foreground)'
}: { 
  icon: React.ReactNode;
  label: string;
  value: string;
  trend?: string;
  valueColor?: string;
}) {
  return (
    <div className="geist-card" style={{ padding: '20px' }}>
      <div style={{ 
        display: 'flex', 
        alignItems: 'center', 
        gap: '8px', 
        marginBottom: '12px',
        color: 'var(--geist-gray-400)'
      }}>
        {icon}
        <span style={{ fontSize: '13px', fontWeight: 500 }}>{label}</span>
      </div>
      <div style={{ 
        fontSize: '28px', 
        fontWeight: 700, 
        color: valueColor,
        letterSpacing: '-0.02em',
        marginBottom: '4px'
      }}>
        {value}
      </div>
      {trend && (
        <div style={{ fontSize: '12px', color: 'var(--geist-gray-400)' }}>
          {trend}
        </div>
      )}
    </div>
  );
}

function SectionHeader({ 
  icon, 
  title, 
  subtitle 
}: { 
  icon: React.ReactNode;
  title: string;
  subtitle: string;
}) {
  return (
    <div style={{ marginBottom: '16px' }}>
      <div style={{ 
        display: 'flex', 
        alignItems: 'center', 
        gap: '8px', 
        marginBottom: '4px'
      }}>
        <span style={{ color: 'var(--geist-gray-400)' }}>{icon}</span>
        <h2 style={{ 
          fontSize: '16px', 
          fontWeight: 600,
          margin: 0
        }}>
          {title}
        </h2>
      </div>
      <p style={{ 
        fontSize: '13px', 
        color: 'var(--geist-gray-400)', 
        margin: 0,
        marginLeft: '26px'
      }}>
        {subtitle}
      </p>
    </div>
  );
}
