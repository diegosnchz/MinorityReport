import { Point2D, TrajectoryVector, MousePattern, IntentType } from '../types/precog';

// Web Worker for Precog calculations
// Runs trajectory analysis off the main thread

const ANGLE_THRESHOLD = Math.PI / 4; // 45 degrees
const SPEED_THRESHOLD = 500; // pixels/second
const HOVER_THRESHOLD = 200; // ms

function calculateVectors(trajectory: Point2D[]): TrajectoryVector[] {
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
    const speed = (distance / dt) * 1000;
    const angle = Math.atan2(dy, dx);
    
    vectors.push({ dx, dy, speed, angle, timestamp: current.timestamp });
  }
  
  return vectors;
}

function analyzePattern(trajectory: Point2D[]): MousePattern {
  const vectors = calculateVectors(trajectory);
  
  if (vectors.length === 0) {
    return {
      acceleration: 0,
      deceleration: 0,
      hoverTime: 0,
      directionChanges: 0,
      straightness: 0
    };
  }

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

  let directionChanges = 0;
  for (let i = 1; i < vectors.length; i++) {
    const angleDiff = Math.abs(vectors[i].angle - vectors[i - 1].angle);
    if (angleDiff > ANGLE_THRESHOLD) {
      directionChanges++;
    }
  }

  let hoverTime = 0;
  let hoverStart: number | null = null;
  
  for (const vector of vectors) {
    if (vector.speed < SPEED_THRESHOLD) {
      if (hoverStart === null) {
        hoverStart = vector.timestamp;
      }
    } else if (hoverStart !== null) {
      hoverTime += vector.timestamp - hoverStart;
      hoverStart = null;
    }
  }

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

function predictIntent(
  trajectory: Point2D[],
  pattern: MousePattern,
  elements: Array<[string, { left: number; top: number; width: number; height: number }]>
): { intent: IntentType; confidence: number; target?: string } {
  if (trajectory.length < 5) {
    return { intent: 'exploration', confidence: 0.3 };
  }

  const lastPoint = trajectory[trajectory.length - 1];
  const vectors = calculateVectors(trajectory);
  const avgSpeed = vectors.reduce((sum, v) => sum + v.speed, 0) / vectors.length;
  const lastVector = vectors[vectors.length - 1];

  let bestTarget: string | undefined;
  let bestScore = 0;

  for (const [id, rect] of elements) {
    const centerX = rect.left + rect.width / 2;
    const centerY = rect.top + rect.height / 2;
    
    const targetAngle = Math.atan2(centerY - lastPoint.y, centerX - lastPoint.x);
    const distance = Math.sqrt(
      Math.pow(centerX - lastPoint.x, 2) + 
      Math.pow(centerY - lastPoint.y, 2)
    );

    let angleDiff = Math.abs(lastVector.angle - targetAngle);
    if (angleDiff > Math.PI) {
      angleDiff = 2 * Math.PI - angleDiff;
    }
    
    const alignmentScore = 1 - (angleDiff / Math.PI);
    const distanceScore = Math.max(0, 1 - distance / 500);
    
    const isHovering = 
      lastPoint.x >= rect.left && 
      lastPoint.x <= rect.left + rect.width && 
      lastPoint.y >= rect.top && 
      lastPoint.y <= rect.top + rect.height;

    let score = alignmentScore * 0.5 + distanceScore * 0.3;
    
    if (isHovering && pattern.hoverTime > HOVER_THRESHOLD) {
      score += 0.4;
    }

    if (score > bestScore) {
      bestScore = score;
      bestTarget = id;
    }
  }

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

// Worker message handler
self.onmessage = (event) => {
  const { type, payload } = event.data;
  
  if (type === 'ANALYZE') {
    const { trajectory, elements } = payload;
    
    const pattern = analyzePattern(trajectory);
    const prediction = predictIntent(trajectory, pattern, elements);
    
    self.postMessage({
      type: 'PREDICTION',
      payload: prediction
    });
  }
};
