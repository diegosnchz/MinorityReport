import { useEffect, useState } from 'react';
import { precogApi } from '../services/api';
import { usePrecogElement } from '../contexts/PrecogContext';
import { Users, AlertTriangle, CheckCircle, Clock } from 'lucide-react';

interface Citizen {
  id: number;
  name: string;
  born: number;
  status: 'active' | 'watchlist' | 'intervene' | 'detained';
  risk_seed: number;
  criminal_degree: number;
  last_location?: string;
}

export function CitizenTable() {
  const [citizens, setCitizens] = useState<Citizen[]>([]);
  const [loading, setLoading] = useState(true);
  const tableRef = usePrecogElement('citizen-table');

  useEffect(() => {
    const fetchCitizens = async () => {
      try {
        const response = await precogApi.fetch<Citizen[]>('/citizens?limit=50');
        if (response && response.length > 0) {
          setCitizens(response);
        } else {
          setCitizens(getDemoCitizens());
        }
      } catch (error) {
        console.warn('Using demo citizens:', error);
        setCitizens(getDemoCitizens());
      } finally {
        setLoading(false);
      }
    };

    fetchCitizens();
  }, []);

  if (loading) {
    return (
      <div className="geist-card" style={{ padding: '48px', textAlign: 'center' }}>
        <span style={{ color: 'var(--geist-gray-400)' }}>Cargando ciudadanos...</span>
      </div>
    );
  }

  return (
    <div 
      ref={tableRef as React.RefObject<HTMLDivElement>} 
      className="geist-card"
      data-precog-id="citizen-table"
      style={{ overflow: 'hidden' }}
    >
      <div style={{ 
        padding: '16px 20px', 
        borderBottom: '1px solid var(--geist-gray-200)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Users size={18} style={{ color: 'var(--geist-gray-400)' }} />
          <span style={{ fontWeight: 600, fontSize: '14px' }}>Ciudadanos Monitoreados</span>
        </div>
        <span style={{ fontSize: '13px', color: 'var(--geist-gray-400)' }}>
          {citizens.length} registros
        </span>
      </div>
      
      <div style={{ overflowX: 'auto' }}>
        <table className="geist-table">
          <thead>
            <tr>
              <th>ID</th>
              <th>Nombre</th>
              <th>Estado</th>
              <th>Nivel de Riesgo</th>
              <th>Conexiones</th>
              <th>Última Ubicación</th>
            </tr>
          </thead>
          <tbody>
            {citizens.slice(0, 20).map((citizen) => (
              <tr key={citizen.id} data-precog-id={`citizen-row-${citizen.id}`}>
                <td>
                  <span style={{ fontFamily: 'monospace', fontSize: '13px', color: 'var(--geist-gray-400)' }}>
                    #{citizen.id.toString().padStart(4, '0')}
                  </span>
                </td>
                <td>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                    <div style={{
                      width: '32px',
                      height: '32px',
                      borderRadius: '50%',
                      background: getAvatarColor(citizen.name),
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      fontSize: '13px',
                      fontWeight: 600,
                      color: 'white'
                    }}>
                      {citizen.name.charAt(0)}
                    </div>
                    <div>
                      <div style={{ fontWeight: 500 }}>{citizen.name}</div>
                      <div style={{ fontSize: '12px', color: 'var(--geist-gray-400)' }}>
                        Nac. {citizen.born}
                      </div>
                    </div>
                  </div>
                </td>
                <td>
                  <StatusBadge status={citizen.status} />
                </td>
                <td>
                  <RiskIndicator risk={citizen.risk_seed} />
                </td>
                <td>
                  <span style={{ fontSize: '13px', color: 'var(--geist-gray-400)' }}>
                    {citizen.criminal_degree} contactos
                  </span>
                </td>
                <td>
                  <span style={{ fontSize: '13px', color: 'var(--geist-gray-400)', display: 'flex', alignItems: 'center', gap: '4px' }}>
                    <Clock size={12} />
                    {citizen.last_location || 'Desconocida'}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function StatusBadge({ status }: { status: Citizen['status'] }) {
  const config = {
    active: { label: 'Activo', color: 'var(--geist-gray-400)', bg: 'var(--geist-gray-100)' },
    watchlist: { label: 'Vigilado', color: 'var(--geist-warning)', bg: 'rgba(245, 166, 35, 0.1)' },
    intervene: { label: 'Intervenir', color: 'var(--geist-accent)', bg: 'rgba(0, 112, 243, 0.1)' },
    detained: { label: 'Detenido', color: 'var(--geist-error)', bg: 'rgba(224, 0, 0, 0.1)' },
  };

  const { label, color, bg } = config[status];

  return (
    <span style={{
      display: 'inline-flex',
      alignItems: 'center',
      gap: '4px',
      padding: '2px 8px',
      fontSize: '12px',
      fontWeight: 500,
      borderRadius: '4px',
      color,
      background: bg,
    }}>
      {status === 'active' && <CheckCircle size={12} />}
      {status === 'watchlist' && <Clock size={12} />}
      {status === 'intervene' && <AlertTriangle size={12} />}
      {label}
    </span>
  );
}

function RiskIndicator({ risk }: { risk: number }) {
  const percentage = Math.round(risk * 100);
  let color = 'var(--geist-success)';
  let label = 'Bajo';
  
  if (risk > 0.7) {
    color = 'var(--geist-error)';
    label = 'Crítico';
  } else if (risk > 0.4) {
    color = 'var(--geist-warning)';
    label = 'Medio';
  }

  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
      <div style={{
        width: '60px',
        height: '4px',
        background: 'var(--geist-gray-200)',
        borderRadius: '2px',
        overflow: 'hidden'
      }}>
        <div style={{
          width: `${percentage}%`,
          height: '100%',
          background: color,
          borderRadius: '2px',
          transition: 'width 0.3s ease'
        }} />
      </div>
      <span style={{ fontSize: '12px', color: 'var(--geist-gray-400)', fontWeight: 500 }}>
        {percentage}%
      </span>
    </div>
  );
}

function getAvatarColor(name: string): string {
  const colors = [
    '#0070f3', '#7928ca', '#ff0080', '#f5a623', '#e00', '#50e3c2'
  ];
  const index = name.charCodeAt(0) % colors.length;
  return colors[index];
}

function getDemoCitizens(): Citizen[] {
  return [
    { id: 1, name: 'John Anderton', born: 1975, status: 'active', risk_seed: 0.15, criminal_degree: 2, last_location: 'Centro Madrid' },
    { id: 2, name: 'Lamar Burgess', born: 1960, status: 'watchlist', risk_seed: 0.45, criminal_degree: 8, last_location: 'Barrio Salamanca' },
    { id: 3, name: 'Agatha Lively', born: 1995, status: 'intervene', risk_seed: 0.82, criminal_degree: 15, last_location: 'Usera' },
    { id: 4, name: 'Danny Witwer', born: 1982, status: 'active', risk_seed: 0.25, criminal_degree: 0, last_location: 'Chamberí' },
    { id: 5, name: 'Tom Cruise', born: 1962, status: 'detained', risk_seed: 0.95, criminal_degree: 23, last_location: 'Villaverde' },
    { id: 6, name: 'Sarah Connor', born: 1965, status: 'watchlist', risk_seed: 0.55, criminal_degree: 12, last_location: 'Retiro' },
    { id: 7, name: 'Kyle Reese', born: 2004, status: 'active', risk_seed: 0.12, criminal_degree: 1, last_location: 'Chamartín' },
    { id: 8, name: 'T-800', born: 2029, status: 'intervene', risk_seed: 0.88, criminal_degree: 45, last_location: 'Carabanchel' },
    { id: 9, name: 'Rick Deckard', born: 1985, status: 'active', risk_seed: 0.22, criminal_degree: 3, last_location: 'Centro Madrid' },
    { id: 10, name: 'Roy Batty', born: 2016, status: 'detained', risk_seed: 0.78, criminal_degree: 19, last_location: 'Usera' },
    { id: 11, name: 'Pris Stratton', born: 2018, status: 'watchlist', risk_seed: 0.48, criminal_degree: 9, last_location: 'Chamberí' },
    { id: 12, name: 'Gaff', born: 1970, status: 'active', risk_seed: 0.18, criminal_degree: 4, last_location: 'Retiro' },
  ];
}
