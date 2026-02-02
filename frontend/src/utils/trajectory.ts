import { Point2D, TrajectoryVector, MousePattern, IntentType, PredictedAction } from '../types/precog';

export class TrajectoryAnalyzer {
  private static readonly MIN_POINTS = 5;
  private static readonly HOVER_THRESHOLD = 200; // ms
  private static readonly SPEED_THRESHOLD = 500; // pixels/second
  private static readonly ANGLE_THRESHOLD = Math.PI / 4; // 45 degrees

  static calculateVectors(trajectory: Point2D[]): TrajectoryVector[] {
    if (trajectory.length < 2) return [];

    const vectors: TrajectoryVector[] = [];
    
    for (let i = 1; i < trajectory.length; i++) {
      const current = trajectory[i];
      const previous = trajectory[i - 1];
      
      const dx = current.x - previous.x;
      const dy = current.y - previous.y;
      const dt = current.timestamp - previous.timestamp;
      
      if (dt <= 0) continue;
      
      const distance = Math.sqrt(dx * dx + dy * dy);
      const speed = (distance / dt) * 1000; // Convert to pixels/second
      const angle = Math.atan2(dy, dx);
      
      vectors.push({
        dx,
        dy,
        speed,
        angle,
        timestamp: current.timestamp
      });
    }
    
    return vectors;
  }

  static analyzePattern(trajectory: Point2D[]): MousePattern {
    const vectors = this.calculateVectors(trajectory);
    
    if (vectors.length === 0) {
      return {
        acceleration: 0,
        deceleration: 0,
        hoverTime: 0,
        directionChanges: 0,
        straightness: 0
      };
    }

    // Calculate accelerations
    let totalAccel = 0;
    let totalDecel = 0;
    let accelCount = 0;
    let decelCount = 0;

    for (let i = 1; i < vectors.length; i++) {
      const speedDiff = vectors[i].speed - vectors[i - 1].speed;
      if (speedDiff > 0) {
        totalAccel += speedDiff;
        accelCount++;
      } else {
        totalDecel += Math.abs(speedDiff);
        decelCount++;
      }
    }

    // Calculate direction changes
    let directionChanges = 0;
    for (let i = 1; i < vectors.length; i++) {
      const angleDiff = Math.abs(vectors[i].angle - vectors[i - 1].angle);
      if (angleDiff > this.ANGLE_THRESHOLD) {
        directionChanges++;
      }
    }

    // Calculate hover time (low speed periods)
    let hoverTime = 0;
    let hoverStart: number | null = null;
    
    for (const vector of vectors) {
      if (vector.speed < this.SPEED_THRESHOLD) {
        if (hoverStart === null) {
          hoverStart = vector.timestamp;
        }
      } else if (hoverStart !== null) {
        hoverTime += vector.timestamp - hoverStart;
        hoverStart = null;
      }
    }

    // Calculate straightness (average alignment of vectors)
    let straightness = 1;
    if (vectors.length > 1) {
      const firstAngle = vectors[0].angle;
      let angleVariance = 0;
      
      for (const vector of vectors) {
        let angleDiff = Math.abs(vector.angle - firstAngle);
        if (angleDiff > Math.PI) {
          angleDiff = 2 * Math.PI - angleDiff;
        }
        angleVariance += angleDiff;
      }
      
      straightness = 1 - (angleVariance / (vectors.length * Math.PI));
    }

    return {
      acceleration: accelCount > 0 ? totalAccel / accelCount : 0,
      deceleration: decelCount > 0 ? totalDecel / decelCount : 0,
      hoverTime,
      directionChanges,
      straightness: Math.max(0, straightness)
    };
  }

  static predictIntent(
    trajectory: Point2D[],
    pattern: MousePattern,
    interactiveElements: Map<string, DOMRect>
  ): { intent: IntentType; confidence: number; target?: string } {
    if (trajectory.length < this.MIN_POINTS) {
      return { intent: 'exploration', confidence: 0.3 };
    }

    const lastPoint = trajectory[trajectory.length - 1];
    const vectors = this.calculateVectors(trajectory);
    const avgSpeed = vectors.reduce((sum, v) => sum + v.speed, 0) / vectors.length;
    const lastVector = vectors[vectors.length - 1];

    // Check if moving toward a specific target
    let bestTarget: string | undefined;
    let bestScore = 0;

    for (const [id, rect] of interactiveElements) {
      const centerX = rect.left + rect.width / 2;
      const centerY = rect.top + rect.height / 2;
      
      const targetAngle = Math.atan2(centerY - lastPoint.y, centerX - lastPoint.x);
      const distance = Math.sqrt(
        Math.pow(centerX - lastPoint.x, 2) + 
        Math.pow(centerY - lastPoint.y, 2)
      );

      // Calculate alignment score
      let angleDiff = Math.abs(lastVector.angle - targetAngle);
      if (angleDiff > Math.PI) {
        angleDiff = 2 * Math.PI - angleDiff;
      }
      
      const alignmentScore = 1 - (angleDiff / Math.PI);
      const distanceScore = Math.max(0, 1 - distance / 500); // 500px max distance
      
      // Hover detection
      const isHovering = 
        lastPoint.x >= rect.left && 
        lastPoint.x <= rect.right && 
        lastPoint.y >= rect.top && 
        lastPoint.y <= rect.bottom;

      let score = alignmentScore * 0.5 + distanceScore * 0.3;
      
      if (isHovering && pattern.hoverTime > this.HOVER_THRESHOLD) {
        score += 0.4; // Bonus for hovering
      }

      if (score > bestScore) {
        bestScore = score;
        bestTarget = id;
      }
    }

    // Determine intent based on pattern
    let intent: IntentType;
    let confidence: number;

    if (pattern.hoverTime > 300 && bestScore > 0.6) {
      intent = 'selection';
      confidence = 0.6 + bestScore * 0.3;
    } else if (pattern.straightness > 0.8 && avgSpeed > 300) {
      intent = 'navigation';
      confidence = 0.5 + pattern.straightness * 0.4;
    } else if (pattern.directionChanges > 3 && avgSpeed < 200) {
      intent = 'exploration';
      confidence = 0.4;
    } else if (bestScore > 0.5) {
      intent = 'hover';
      confidence = 0.5 + bestScore * 0.3;
    } else {
      intent = 'exploration';
      confidence = 0.3;
    }

    return { intent, confidence: Math.min(confidence, 1), target: bestTarget };
  }

  static calculatePredictionProbability(
    pattern: MousePattern,
    historicalAccuracy: number,
    timeOfDay: number
  ): number {
    // Weight different factors
    const weights = {
      straightness: 0.3,
      speed: 0.2,
      history: 0.3,
      time: 0.2
    };

    // Straightness score (higher is better)
    const straightnessScore = pattern.straightness;

    // Speed score (optimal speed is 200-800 px/s)
    const speedScore = Math.max(0, 1 - Math.abs(pattern.acceleration - 500) / 500);

    // Historical accuracy score
    const historyScore = historicalAccuracy;

    // Time score (users are more predictable during work hours 9-17)
    const hour = timeOfDay / 3600000; // Convert ms to hours
    const timeScore = (hour >= 9 && hour <= 17) ? 0.8 : 0.6;

    return (
      straightnessScore * weights.straightness +
      speedScore * weights.speed +
      historyScore * weights.history +
      timeScore * weights.time
    );
  }
}

export function generateActionId(): string {
  return `precog-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
}

export function debounce<T extends (...args: unknown[]) => unknown>(
  func: T,
  wait: number
): (...args: Parameters<T>) => void {
  let timeout: NodeJS.Timeout | null = null;
  
  return (...args: Parameters<T>) => {
    if (timeout) {
      clearTimeout(timeout);
    }
    
    timeout = setTimeout(() => {
      func(...args);
    }, wait);
  };
}

export function throttle<T extends (...args: unknown[]) => unknown>(
  func: T,
  limit: number
): (...args: Parameters<T>) => void {
  let inThrottle = false;
  
  return (...args: Parameters<T>) => {
    if (!inThrottle) {
      func(...args);
      inThrottle = true;
      setTimeout(() => {
        inThrottle = false;
      }, limit);
    }
  };
}
