import { useEffect, useState } from 'react';
import { precogApi } from '../services/api';
import { usePrecogElement } from '../contexts/PrecogContext';
import { MapPin, AlertTriangle, Navigation } from 'lucide-react';

interface Location {
  id: string;
  name: string;
  type: string;
  coordinates: { x: number; y: number };
  risk_level: 'high' | 'medium' | 'low';
  crime_count: number;
  population: number;
}

export function MapView() {
  const [locations, setLocations] = useState<Location[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedLocation, setSelectedLocation] = useState<Location | null>(null);
  const mapRef = usePrecogElement('map-view');

  useEffect(() => {
    const fetchLocations = async () => {
      try {
        const response = await precogApi.fetch<Location[]>('/locations');
        if (response && response.length > 0) {
          setLocations(response.map((loc, index) => ({
            ...loc,
            coordinates: getGridPosition(index)
          })));
        } else {
          setLocations(getDemoLocations());
        }
      } catch (error) {
        setLocations(getDemoLocations());
      } finally {
        setLoading(false);
      }
    };

    fetchLocations();
  }, []);

  if (loading) {
    return (
      <div className="geist-card" style={{ 
        height: '500px', 
        display: 'flex', 
        alignItems: 'center', 
        justifyContent: 'center' 
      }}>
        <span style={{ color: 'var(--geist-gray-400)' }}>Cargando mapa...</span>
      </div>
    );
  }

  return (
    <div 
      ref={mapRef as React.RefObject<HTMLDivElement>} 
      className="geist-card"
      data-precog-id="map-view"
      style={{ overflow: 'hidden' }}
    >
      <div style={{ 
        height: '500px', 
        position: 'relative',
        background: 'var(--geist-gray-100)',
        borderRadius: 'var(--geist-radius)'
      }}>
        {/* Grid Background */}
        <svg 
          width="100%" 
          height="100%" 
          style={{ 
            position: 'absolute',
            opacity: 0.3
          }}
        >
          <defs>
            <pattern id="grid" width="40" height="40" patternUnits="userSpaceOnUse">
              <path d="M 40 0 L 0 0 0 40" fill="none" stroke="#000" strokeWidth="0.5"/>
            </pattern>
          </defs>
          <rect width="100%" height="100%" fill="url(#grid)" />
        </svg>

        {/* Connection Lines */}
        <svg 
          width="100%" 
          height="100%" 
          style={{ position: 'absolute', pointerEvents: 'none' }}
        >
          {locations.map((loc, i) => 
            locations.slice(i + 1).map((otherLoc, j) => {
              if (Math.abs(loc.coordinates.x - otherLoc.coordinates.x) < 20 && 
                  Math.abs(loc.coordinates.y - otherLoc.coordinates.y) < 20) {
                return (
                  <line
                    key={`${loc.id}-${otherLoc.id}`}
                    x1={`${loc.coordinates.x}%`}
                    y1={`${loc.coordinates.y}%`}
                    x2={`${otherLoc.coordinates.x}%`}
                    y2={`${otherLoc.coordinates.y}%`}
                    stroke="var(--geist-gray-300)"
                    strokeWidth="1"
                    strokeDasharray="4"
                    opacity={0.5}
                  />
                );
              }
              return null;
            })
          )}
        </svg>

        {/* Location Markers */}
        {locations.map((location) => (
          <div
            key={location.id}
            onClick={() => setSelectedLocation(location)}
            style={{
              position: 'absolute',
              left: `${location.coordinates.x}%`,
              top: `${location.coordinates.y}%`,
              transform: 'translate(-50%, -50%)',
              cursor: 'pointer',
              zIndex: 10
            }}
          >
            <div style={{
              width: '48px',
              height: '48px',
              borderRadius: '50%',
              background: getRiskColor(location.risk_level),
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              boxShadow: '0 2px 8px rgba(0,0,0,0.15)',
              border: selectedLocation?.id === location.id ? '3px solid var(--geist-foreground)' : '2px solid white',
              transition: 'all 0.2s ease'
            }}>
              <MapPin size={20} color="white" />
            </div>
            <div style={{
              position: 'absolute',
              top: '52px',
              left: '50%',
              transform: 'translateX(-50%)',
              background: 'var(--geist-background)',
              padding: '4px 8px',
              borderRadius: '4px',
              fontSize: '11px',
              fontWeight: 600,
              whiteSpace: 'nowrap',
              boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
              border: '1px solid var(--geist-gray-200)'
            }}>
              {location.name}
            </div>
          </div>
        ))}

        {/* Legend */}
        <div style={{
          position: 'absolute',
          bottom: '16px',
          left: '16px',
          background: 'var(--geist-background)',
          padding: '12px 16px',
          borderRadius: 'var(--geist-radius)',
          border: '1px solid var(--geist-gray-200)',
          boxShadow: 'var(--geist-shadow-sm)',
          display: 'flex',
          gap: '16px',
          fontSize: '12px'
        }}>
          <LegendItem color="#e00" label="Alto riesgo" />
          <LegendItem color="#f5a623" label="Riesgo medio" />
          <LegendItem color="#0070f3" label="Bajo riesgo" />
        </div>
      </div>

      {/* Selected Location Details */}
      {selectedLocation && (
        <div style={{
          padding: '20px',
          borderTop: '1px solid var(--geist-gray-200)',
          background: 'var(--geist-gray-100)'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '12px' }}>
            <div style={{
              width: '40px',
              height: '40px',
              borderRadius: '50%',
              background: getRiskColor(selectedLocation.risk_level),
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center'
            }}>
              <Navigation size={18} color="white" />
            </div>
            <div>
              <div style={{ fontWeight: 600, fontSize: '16px' }}>{selectedLocation.name}</div>
              <div style={{ fontSize: '13px', color: 'var(--geist-gray-400)' }}>
                {selectedLocation.type} • {selectedLocation.population?.toLocaleString()} hab.
              </div>
            </div>
            <div style={{ marginLeft: 'auto', textAlign: 'right' }}>
              <div style={{ 
                fontSize: '24px', 
                fontWeight: 700, 
                color: getRiskColor(selectedLocation.risk_level) 
              }}>
                {selectedLocation.crime_count}
              </div>
              <div style={{ fontSize: '11px', color: 'var(--geist-gray-400)' }}>Incidentes</div>
            </div>
          </div>
          <div style={{ 
            display: 'flex', 
            gap: '8px',
            fontSize: '12px'
          }}>
            <span style={{
              padding: '4px 12px',
              borderRadius: '4px',
              background: getRiskBg(selectedLocation.risk_level),
              color: getRiskColor(selectedLocation.risk_level),
              fontWeight: 500
            }}>
              {selectedLocation.risk_level === 'high' ? '⚠️ Crítico' : 
               selectedLocation.risk_level === 'medium' ? '⚡ Moderado' : 
               '✓ Seguro'}
            </span>
          </div>
        </div>
      )}
    </div>
  );
}

function LegendItem({ color, label }: { color: string; label: string }) {
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
      <span style={{ 
        width: '8px', 
        height: '8px', 
        borderRadius: '50%', 
        background: color 
      }} />
      <span style={{ color: 'var(--geist-gray-500)' }}>{label}</span>
    </div>
  );
}

function getGridPosition(index: number): { x: number; y: number } {
  const positions = [
    { x: 20, y: 25 },
    { x: 45, y: 20 },
    { x: 70, y: 30 },
    { x: 35, y: 45 },
    { x: 60, y: 50 },
    { x: 25, y: 65 },
    { x: 50, y: 70 },
    { x: 75, y: 60 },
    { x: 40, y: 80 },
    { x: 65, y: 75 },
  ];
  return positions[index % positions.length];
}

function getRiskColor(level: string): string {
  switch (level) {
    case 'high': return '#e00';
    case 'medium': return '#f5a623';
    case 'low': return '#0070f3';
    default: return '#666';
  }
}

function getRiskBg(level: string): string {
  switch (level) {
    case 'high': return 'rgba(224, 0, 0, 0.1)';
    case 'medium': return 'rgba(245, 166, 35, 0.1)';
    case 'low': return 'rgba(0, 112, 243, 0.1)';
    default: return 'var(--geist-gray-100)';
  }
}

function getDemoLocations(): Location[] {
  return [
    { id: '1', name: 'Centro de Madrid', type: 'Comercial', coordinates: { x: 0, y: 0 }, risk_level: 'medium', crime_count: 45, population: 150000 },
    { id: '2', name: 'Barrio Salamanca', type: 'Residencial', coordinates: { x: 0, y: 0 }, risk_level: 'low', crime_count: 12, population: 180000 },
    { id: '3', name: 'Usera', type: 'Residencial', coordinates: { x: 0, y: 0 }, risk_level: 'high', crime_count: 89, population: 130000 },
    { id: '4', name: 'Chamberí', type: 'Mixto', coordinates: { x: 0, y: 0 }, risk_level: 'low', crime_count: 23, population: 140000 },
    { id: '5', name: 'Retiro', type: 'Parque', coordinates: { x: 0, y: 0 }, risk_level: 'low', crime_count: 8, population: 5000 },
    { id: '6', name: 'Villaverde', type: 'Industrial', coordinates: { x: 0, y: 0 }, risk_level: 'high', crime_count: 67, population: 125000 },
    { id: '7', name: 'Chamartín', type: 'Empresarial', coordinates: { x: 0, y: 0 }, risk_level: 'medium', crime_count: 34, population: 110000 },
    { id: '8', name: 'Carabanchel', type: 'Residencial', coordinates: { x: 0, y: 0 }, risk_level: 'medium', crime_count: 56, population: 195000 },
  ];
}
