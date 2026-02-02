export interface Point2D {
  x: number;
  y: number;
  timestamp: number;
}

export interface TrajectoryVector {
  dx: number;
  dy: number;
  speed: number;
  angle: number;
  timestamp: number;
}

export interface PredictedAction {
  id: string;
  type: 'route' | 'data' | 'api' | 'component';
  target: string;
  confidence: number;
  intent: 'navigation' | 'selection' | 'hover' | 'exit' | 'exploration';
  timestamp: number;
  payload?: unknown;
}

export interface MousePattern {
  acceleration: number;
  deceleration: number;
  hoverTime: number;
  directionChanges: number;
  straightness: number;
}

export interface PrecogState {
  isTracking: boolean;
  trajectory: Point2D[];
  lastPrediction: PredictedAction | null;
  confidence: number;
  cachedActions: Map<string, unknown>;
}

export interface PrecogConfig {
  confidenceThreshold: number;
  maxTrajectoryLength: number;
  predictionInterval: number;
  cacheTTL: number;
  enableWebWorker: boolean;
}

export interface CacheEntry<T> {
  data: T;
  timestamp: number;
  expiresAt: number;
  accessCount: number;
}

export interface PrefetchRequest {
  id: string;
  url: string;
  method: 'GET' | 'POST';
  priority: 'high' | 'medium' | 'low';
  timestamp: number;
}

export type IntentType = 'navigation' | 'selection' | 'hover' | 'exit' | 'exploration';
