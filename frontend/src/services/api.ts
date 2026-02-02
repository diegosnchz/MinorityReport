import axios, { AxiosRequestConfig } from 'axios';
import { PrecogCache, PrefetchQueue } from '../utils/cache';
import { PrefetchRequest } from '../types/precog';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v2';

class PrecogApiService {
  private cache: PrecogCache;
  private prefetchQueue: PrefetchQueue;
  private axiosInstance;

  constructor() {
    this.cache = new PrecogCache(100, 300000); // 100 items, 5 min TTL
    this.axiosInstance = axios.create({
      baseURL: API_BASE_URL,
      timeout: 10000,
      headers: {
        'Content-Type': 'application/json'
      }
    });

    // Initialize prefetch queue
    this.prefetchQueue = new PrefetchQueue(3, this.executePrefetch.bind(this));

    // Periodic cleanup
    setInterval(() => {
      this.cache.cleanup();
    }, 60000); // Every minute
  }

  // Main fetch method with cache check
  async fetch<T>(endpoint: string, config?: AxiosRequestConfig): Promise<T> {
    const cacheKey = this.generateCacheKey(endpoint, config);
    
    // Check cache first
    const cached = this.cache.get<T>(cacheKey);
    if (cached !== null) {
      this.cache.recordHit();
      return cached;
    }

    this.cache.recordMiss();

    // Fetch from API
    try {
      const response = await this.axiosInstance.get<T>(endpoint, config);
      const data = response.data;

      // Store in cache
      this.cache.set(cacheKey, data);

      return data;
    } catch (error) {
      console.error(`[Precog API] Error fetching ${endpoint}:`, error);
      throw error;
    }
  }

  // Prefetch method (called by prediction engine)
  prefetch(endpoint: string, priority: 'high' | 'medium' | 'low' = 'medium'): void {
    const cacheKey = this.generateCacheKey(endpoint, {});
    
    // Skip if already cached or being processed
    if (this.cache.has(cacheKey)) {
      return;
    }

    const request: PrefetchRequest = {
      id: cacheKey,
      url: endpoint,
      method: 'GET',
      priority,
      timestamp: Date.now()
    };

    this.prefetchQueue.enqueue(request);
  }

  // Batch prefetch multiple endpoints
  prefetchBatch(endpoints: string[], priority: 'high' | 'medium' | 'low' = 'low'): void {
    endpoints.forEach((endpoint, index) => {
      // Stagger requests to avoid overwhelming the server
      setTimeout(() => {
        this.prefetch(endpoint, priority);
      }, index * 100);
    });
  }

  // Execute actual prefetch
  private async executePrefetch(request: PrefetchRequest): Promise<unknown> {
    try {
      const response = await this.axiosInstance.request({
        method: request.method,
        url: request.url,
        timeout: 5000 // Shorter timeout for prefetches
      });

      // Store in cache
      this.cache.set(request.id, response.data);

      return response.data;
    } catch (error) {
      // Silently fail for prefetches - don't disrupt user experience
      console.warn(`[Precog] Prefetch failed for ${request.url}`);
      throw error;
    }
  }

  // Invalidate cache for specific endpoint pattern
  invalidate(pattern: string): void {
    const keysToDelete: string[] = [];
    
    // Note: In a real implementation, you'd iterate over the cache keys
    // For now, we'll just clear the whole cache for simplicity
    this.cache.clear();
  }

  // Get cache statistics
  getCacheStats() {
    return this.cache.getStats();
  }

  // Get prefetch queue stats
  getQueueStats() {
    return this.prefetchQueue.getStats();
  }

  // Preload citizen data
  preloadCitizen(citizenId: number): void {
    this.prefetch(`/citizens/${citizenId}`, 'high');
    this.prefetch(`/citizens/${citizenId}/risk`, 'medium');
    this.prefetch(`/precogs/scan/${citizenId}`, 'low');
  }

  // Preload dashboard data
  preloadDashboard(): void {
    this.prefetchBatch([
      '/citizens?limit=20',
      '/locations',
      '/precogs/stats'
    ], 'medium');
  }

  // Preload evasion route data
  preloadEvasionData(): void {
    this.prefetchBatch([
      '/evasion/routes',
      '/evasion/predictions'
    ], 'low');
  }

  private generateCacheKey(endpoint: string, config?: AxiosRequestConfig): string {
    const params = config?.params ? JSON.stringify(config.params) : '';
    return `${endpoint}${params}`;
  }
}

// Singleton instance
export const precogApi = new PrecogApiService();

// React hook for using the API service
export function usePrecogApi() {
  return precogApi;
}
