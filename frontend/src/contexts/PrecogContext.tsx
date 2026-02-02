import React, { createContext, useContext, useCallback, useRef, useState, useEffect, useMemo } from 'react';
import { Point2D, PredictedAction, PrecogConfig, IntentType } from '../types/precog';
import { TrajectoryAnalyzer, generateActionId, throttle } from '../utils/trajectory';
import { precogApi } from '../services/api';

interface PrecogContextType {
  isTracking: boolean;
  trajectory: Point2D[];
  lastPrediction: PredictedAction | null;
  confidence: number;
  startTracking: () => void;
  stopTracking: () => void;
  registerElement: (id: string, element: HTMLElement) => void;
  unregisterElement: (id: string) => void;
  clearTrajectory: () => void;
  getStats: () => {
    trajectoryLength: number;
    predictionAccuracy: number;
    cacheHitRate: number;
    activeElements: number;
  };
}

const PrecogContext = createContext<PrecogContextType | null>(null);

interface PrecogProviderProps {
  children: React.ReactNode;
  config?: Partial<PrecogConfig>;
}

const defaultConfig: PrecogConfig = {
  confidenceThreshold: 0.7,
  maxTrajectoryLength: 50,
  predictionInterval: 50,
  cacheTTL: 300000,
  enableWebWorker: true
};

export function PrecogProvider({ children, config: userConfig }: PrecogProviderProps) {
  const config = useMemo(() => ({ ...defaultConfig, ...userConfig }), [userConfig]);
  
  const [isTracking, setIsTracking] = useState(false);
  const [trajectory, setTrajectory] = useState<Point2D[]>([]);
  const [lastPrediction, setLastPrediction] = useState<PredictedAction | null>(null);
  const [confidence, setConfidence] = useState(0);

  const trajectoryRef = useRef<Point2D[]>([]);
  const interactiveElements = useRef<Map<string, DOMRect>>(new Map());
  const predictionHistory = useRef<{ prediction: string; actual: string; timestamp: number }[]>([]);
  const rafId = useRef<number | null>(null);
  const webWorker = useRef<Worker | null>(null);

  // Initialize Web Worker if enabled
  useEffect(() => {
    if (config.enableWebWorker && typeof Worker !== 'undefined') {
      try {
        webWorker.current = new Worker(new URL('../workers/precog.worker.ts', import.meta.url), {
          type: 'module'
        });

        webWorker.current.onmessage = (event) => {
          const { type, payload } = event.data;
          
          if (type === 'PREDICTION') {
            handleWorkerPrediction(payload);
          }
        };
      } catch (error) {
        console.warn('[Precog] Web Worker initialization failed, falling back to main thread:', error);
      }
    }

    return () => {
      webWorker.current?.terminate();
    };
  }, [config.enableWebWorker]);

  // Update trajectory ref when state changes
  useEffect(() => {
    trajectoryRef.current = trajectory;
  }, [trajectory]);

  // Mouse tracking handler
  const handleMouseMove = useCallback(
    throttle((event: MouseEvent) => {
      if (!isTracking) return;

      const point: Point2D = {
        x: event.clientX,
        y: event.clientY,
        timestamp: Date.now()
      };

      // Add to trajectory
      const newTrajectory = [...trajectoryRef.current, point];
      
      // Keep only last N points
      if (newTrajectory.length > config.maxTrajectoryLength) {
        newTrajectory.shift();
      }

      trajectoryRef.current = newTrajectory;
      setTrajectory(newTrajectory);

      // Trigger prediction analysis
      analyzeTrajectory();
    }, config.predictionInterval),
    [isTracking, config]
  );

  // Click tracking
  const handleClick = useCallback((event: MouseEvent) => {
    // Record actual action for accuracy tracking
    const target = event.target as HTMLElement;
    const elementId = target.dataset.precogId;
    
    if (elementId && lastPrediction?.target === elementId) {
      predictionHistory.current.push({
        prediction: lastPrediction.target,
        actual: elementId,
        timestamp: Date.now()
      });
    }
  }, [lastPrediction]);

  // Start/stop tracking
  const startTracking = useCallback(() => {
    setIsTracking(true);
    document.addEventListener('mousemove', handleMouseMove);
    document.addEventListener('click', handleClick);
  }, [handleMouseMove, handleClick]);

  const stopTracking = useCallback(() => {
    setIsTracking(false);
    document.removeEventListener('mousemove', handleMouseMove);
    document.removeEventListener('click', handleClick);
    
    if (rafId.current) {
      cancelAnimationFrame(rafId.current);
    }
  }, [handleMouseMove, handleClick]);

  // Register interactive elements
  const registerElement = useCallback((id: string, element: HTMLElement) => {
    const rect = element.getBoundingClientRect();
    interactiveElements.current.set(id, rect);

    // Store ID on element for click tracking
    element.dataset.precogId = id;
  }, []);

  const unregisterElement = useCallback((id: string) => {
    interactiveElements.current.delete(id);
  }, []);

  // Clear trajectory
  const clearTrajectory = useCallback(() => {
    trajectoryRef.current = [];
    setTrajectory([]);
    setLastPrediction(null);
    setConfidence(0);
  }, []);

  // Main trajectory analysis
  const analyzeTrajectory = useCallback(() => {
    const currentTrajectory = trajectoryRef.current;
    
    if (currentTrajectory.length < 5) return;

    // Use Web Worker if available
    if (webWorker.current) {
      webWorker.current.postMessage({
        type: 'ANALYZE',
        payload: {
          trajectory: currentTrajectory,
          elements: Array.from(interactiveElements.current.entries())
        }
      });
      return;
    }

    // Fallback: Analyze in main thread
    performAnalysis(currentTrajectory);
  }, []);

  // Perform analysis (called from main thread or worker callback)
  const performAnalysis = useCallback((currentTrajectory: Point2D[]) => {
    const pattern = TrajectoryAnalyzer.analyzePattern(currentTrajectory);
    const { intent, confidence: intentConfidence, target } = TrajectoryAnalyzer.predictIntent(
      currentTrajectory,
      pattern,
      interactiveElements.current
    );

    // Calculate overall prediction probability
    const historicalAccuracy = calculateHistoricalAccuracy();
    const probability = TrajectoryAnalyzer.calculatePredictionProbability(
      pattern,
      historicalAccuracy,
      Date.now()
    );

    const finalConfidence = (intentConfidence + probability) / 2;
    setConfidence(finalConfidence);

    // Trigger action if confidence exceeds threshold
    if (finalConfidence >= config.confidenceThreshold && target) {
      triggerPrediction(intent, finalConfidence, target);
    }
  }, [config.confidenceThreshold]);

  // Handle worker prediction
  const handleWorkerPrediction = useCallback((payload: {
    intent: IntentType;
    confidence: number;
    target?: string;
  }) => {
    if (payload.confidence >= config.confidenceThreshold && payload.target) {
      triggerPrediction(payload.intent, payload.confidence, payload.target);
    }
    setConfidence(payload.confidence);
  }, [config.confidenceThreshold]);

  // Trigger prediction action
  const triggerPrediction = useCallback((intent: IntentType, conf: number, target: string) => {
    // Avoid duplicate predictions
    if (lastPrediction?.target === target && Date.now() - (lastPrediction?.timestamp || 0) < 1000) {
      return;
    }

    const action: PredictedAction = {
      id: generateActionId(),
      type: determineActionType(intent, target),
      target,
      confidence: conf,
      intent,
      timestamp: Date.now()
    };

    setLastPrediction(action);
    executePrefetch(action);
  }, [lastPrediction]);

  // Execute prefetch based on action
  const executePrefetch = useCallback((action: PredictedAction) => {
    switch (action.type) {
      case 'route':
        // Prefetch route data
        if (action.target.includes('citizen')) {
          const citizenId = extractIdFromTarget(action.target);
          if (citizenId) {
            precogApi.preloadCitizen(citizenId);
          }
        } else if (action.target === 'dashboard') {
          precogApi.preloadDashboard();
        } else if (action.target === 'evasion') {
          precogApi.preloadEvasionData();
        }
        break;

      case 'data':
        // Prefetch specific data
        precogApi.prefetch(action.target, 'high');
        break;

      case 'api':
        // Prefetch API endpoint
        precogApi.prefetch(action.target, 'medium');
        break;

      default:
        break;
    }
  }, []);

  // Calculate historical accuracy
  const calculateHistoricalAccuracy = useCallback((): number => {
    const recent = predictionHistory.current.filter(
      h => Date.now() - h.timestamp < 300000 // Last 5 minutes
    );

    if (recent.length === 0) return 0.5;

    const correct = recent.filter(h => h.prediction === h.actual).length;
    return correct / recent.length;
  }, []);

  // Get stats
  const getStats = useCallback(() => {
    const cacheStats = precogApi.getCacheStats();
    const recentPredictions = predictionHistory.current.filter(
      h => Date.now() - h.timestamp < 300000
    );
    
    const accuracy = recentPredictions.length > 0
      ? recentPredictions.filter(h => h.prediction === h.actual).length / recentPredictions.length
      : 0;

    return {
      trajectoryLength: trajectory.length,
      predictionAccuracy: accuracy,
      cacheHitRate: cacheStats.hitRate,
      activeElements: interactiveElements.current.size
    };
  }, [trajectory.length]);

  // Update element positions on resize/scroll
  useEffect(() => {
    const updatePositions = () => {
      interactiveElements.current.forEach((_, id) => {
        const element = document.querySelector(`[data-precog-id="${id}"]`) as HTMLElement;
        if (element) {
          const rect = element.getBoundingClientRect();
          interactiveElements.current.set(id, rect);
        }
      });
    };

    window.addEventListener('resize', updatePositions);
    window.addEventListener('scroll', updatePositions);

    return () => {
      window.removeEventListener('resize', updatePositions);
      window.removeEventListener('scroll', updatePositions);
    };
  }, []);

  const value = useMemo(() => ({
    isTracking,
    trajectory,
    lastPrediction,
    confidence,
    startTracking,
    stopTracking,
    registerElement,
    unregisterElement,
    clearTrajectory,
    getStats
  }), [
    isTracking,
    trajectory,
    lastPrediction,
    confidence,
    startTracking,
    stopTracking,
    registerElement,
    unregisterElement,
    clearTrajectory,
    getStats
  ]);

  return (
    <PrecogContext.Provider value={value}>
      {children}
    </PrecogContext.Provider>
  );
}

// Helper functions
function determineActionType(intent: IntentType, target: string): 'route' | 'data' | 'api' | 'component' {
  if (target.includes('citizen') || target.includes('dashboard') || target.includes('evasion')) {
    return 'route';
  }
  if (target.includes('/api/') || target.startsWith('/')) {
    return 'api';
  }
  return 'data';
}

function extractIdFromTarget(target: string): number | null {
  const match = target.match(/\d+/);
  return match ? parseInt(match[0], 10) : null;
}

// Custom hook
export function usePrecog() {
  const context = useContext(PrecogContext);
  if (!context) {
    throw new Error('usePrecog must be used within a PrecogProvider');
  }
  return context;
}

// Hook for registering elements
export function usePrecogElement(id: string) {
  const { registerElement, unregisterElement } = usePrecog();
  const elementRef = useRef<HTMLElement>(null);

  useEffect(() => {
    if (elementRef.current) {
      registerElement(id, elementRef.current);
      
      return () => {
        unregisterElement(id);
      };
    }
  }, [id, registerElement, unregisterElement]);

  return elementRef;
}
