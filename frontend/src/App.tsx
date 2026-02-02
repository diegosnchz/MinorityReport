import { useState } from 'react';
import { PrecogProvider } from './contexts/PrecogContext';
import { Dashboard } from './components/Dashboard';
import { Zap } from 'lucide-react';

function App() {
  const [precogEnabled, setPrecogEnabled] = useState(false);

  return (
    <div style={{ minHeight: '100vh', background: 'var(--geist-background)' }}>
      {/* Header con Toggle */}
      <header style={{
        position: 'sticky',
        top: 0,
        zIndex: 100,
        background: 'rgba(255, 255, 255, 0.8)',
        backdropFilter: 'blur(12px)',
        borderBottom: '1px solid var(--geist-gray-200)'
      }}>
        <div className="container-vercel" style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          height: '64px'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span style={{ 
              fontSize: '14px', 
              fontWeight: 600,
              color: 'var(--geist-foreground)'
            }}>
              Minority Report
            </span>
            <span style={{
              fontSize: '11px',
              padding: '2px 6px',
              background: 'var(--geist-gray-100)',
              color: 'var(--geist-gray-500)',
              borderRadius: '4px',
              fontWeight: 500
            }}>
              v2.0
            </span>
          </div>

          <button
            onClick={() => setPrecogEnabled(!precogEnabled)}
            className="geist-button"
            style={{
              background: precogEnabled ? 'var(--geist-foreground)' : 'transparent',
              color: precogEnabled ? 'var(--geist-background)' : 'var(--geist-gray-600)',
              borderColor: precogEnabled ? 'var(--geist-foreground)' : 'var(--geist-gray-200)',
              fontSize: '13px',
              height: '32px',
              padding: '0 12px'
            }}
          >
            <Zap size={14} style={{ 
              color: precogEnabled ? 'var(--geist-accent)' : 'inherit',
              fill: precogEnabled ? 'var(--geist-accent)' : 'none'
            }} />
            <span>{precogEnabled ? 'Precog On' : 'Activar Precog'}</span>
          </button>
        </div>
      </header>

      {/* Main Content */}
      <main>
        {precogEnabled ? (
          <PrecogProvider
            config={{
              confidenceThreshold: 0.6,
              maxTrajectoryLength: 30,
              predictionInterval: 100,
              cacheTTL: 300000,
              enableWebWorker: true
            }}
          >
            <Dashboard />
          </PrecogProvider>
        ) : (
          <Dashboard />
        )}
      </main>
    </div>
  );
}

export default App;
