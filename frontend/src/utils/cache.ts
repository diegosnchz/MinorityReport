import { CacheEntry, PrefetchRequest } from '../types/precog';

export class PrecogCache {
  private cache: Map<string, CacheEntry<unknown>>;
  private maxSize: number;
  private defaultTTL: number;

  constructor(maxSize: number = 100, defaultTTL: number = 300000) {
    this.cache = new Map();
    this.maxSize = maxSize;
    this.defaultTTL = defaultTTL;
  }

  set<T>(key: string, data: T, customTTL?: number): void {
    const now = Date.now();
    const ttl = customTTL ?? this.defaultTTL;
    
    // Eviction strategy: LRU (Least Recently Used)
    if (this.cache.size >= this.maxSize && !this.cache.has(key)) {
      this.evictLRU();
    }

    this.cache.set(key, {
      data,
      timestamp: now,
      expiresAt: now + ttl,
      accessCount: 1
    });
  }

  get<T>(key: string): T | null {
    const entry = this.cache.get(key);
    
    if (!entry) {
      return null;
    }

    // Check if expired
    if (Date.now() > entry.expiresAt) {
      this.cache.delete(key);
      return null;
    }

    // Update access count
    entry.accessCount++;
    
    return entry.data as T;
  }

  has(key: string): boolean {
    const entry = this.cache.get(key);
    
    if (!entry) {
      return false;
    }

    // Check if expired
    if (Date.now() > entry.expiresAt) {
      this.cache.delete(key);
      return false;
    }

    return true;
  }

  delete(key: string): boolean {
    return this.cache.delete(key);
  }

  clear(): void {
    this.cache.clear();
  }

  getStats(): {
    size: number;
    hitRate: number;
    avgAccessCount: number;
    oldestEntry: number;
  } {
    const entries = Array.from(this.cache.values());
    const now = Date.now();
    
    return {
      size: this.cache.size,
      hitRate: this.calculateHitRate(),
      avgAccessCount: entries.reduce((sum, e) => sum + e.accessCount, 0) / Math.max(entries.length, 1),
      oldestEntry: entries.length > 0 
        ? Math.min(...entries.map(e => e.timestamp))
        : now
    };
  }

  private evictLRU(): void {
    let oldestKey: string | null = null;
    let oldestAccessCount = Infinity;
    let oldestTimestamp = Infinity;

    for (const [key, entry] of this.cache.entries()) {
      // Prioritize by access count, then by timestamp
      if (entry.accessCount < oldestAccessCount || 
          (entry.accessCount === oldestAccessCount && entry.timestamp < oldestTimestamp)) {
        oldestKey = key;
        oldestAccessCount = entry.accessCount;
        oldestTimestamp = entry.timestamp;
      }
    }

    if (oldestKey) {
      this.cache.delete(oldestKey);
    }
  }

  private hitCount = 0;
  private missCount = 0;

  recordHit(): void {
    this.hitCount++;
  }

  recordMiss(): void {
    this.missCount++;
  }

  private calculateHitRate(): number {
    const total = this.hitCount + this.missCount;
    return total > 0 ? this.hitCount / total : 0;
  }

  cleanup(): void {
    const now = Date.now();
    for (const [key, entry] of this.cache.entries()) {
      if (now > entry.expiresAt) {
        this.cache.delete(key);
      }
    }
  }
}

// Prefetch Queue Manager
export class PrefetchQueue {
  private queue: PrefetchRequest[];
  private processing: Set<string>;
  private maxConcurrent: number;
  private onPrefetch: (request: PrefetchRequest) => Promise<unknown>;

  constructor(
    maxConcurrent: number = 3,
    onPrefetch: (request: PrefetchRequest) => Promise<unknown>
  ) {
    this.queue = [];
    this.processing = new Set();
    this.maxConcurrent = maxConcurrent;
    this.onPrefetch = onPrefetch;
  }

  enqueue(request: PrefetchRequest): void {
    // Avoid duplicates
    if (this.queue.some(r => r.id === request.id) || this.processing.has(request.id)) {
      return;
    }

    // Insert based on priority
    const priorityOrder = { high: 0, medium: 1, low: 2 };
    const insertIndex = this.queue.findIndex(
      r => priorityOrder[r.priority] > priorityOrder[request.priority]
    );
    
    if (insertIndex === -1) {
      this.queue.push(request);
    } else {
      this.queue.splice(insertIndex, 0, request);
    }

    this.processQueue();
  }

  cancel(requestId: string): void {
    const index = this.queue.findIndex(r => r.id === requestId);
    if (index !== -1) {
      this.queue.splice(index, 1);
    }
  }

  private async processQueue(): Promise<void> {
    if (this.processing.size >= this.maxConcurrent || this.queue.length === 0) {
      return;
    }

    const request = this.queue.shift();
    if (!request) return;

    this.processing.add(request.id);

    try {
      await this.onPrefetch(request);
    } catch (error) {
      console.warn(`[Precog] Prefetch failed for ${request.id}:`, error);
    } finally {
      this.processing.delete(request.id);
      this.processQueue();
    }
  }

  clear(): void {
    this.queue = [];
  }

  getStats(): {
    queueLength: number;
    processingCount: number;
  } {
    return {
      queueLength: this.queue.length,
      processingCount: this.processing.size
    };
  }
}
