import { useEffect, useRef, useState } from 'react';

interface PerformanceMetrics {
  renderTime: number;
  memoryUsage?: number;
  renderCount: number;
}

export function usePerformance(componentName: string) {
  const renderCountRef = useRef(0);
  const renderStartRef = useRef<number>(0);
  const [metrics, setMetrics] = useState<PerformanceMetrics>({
    renderTime: 0,
    renderCount: 0
  });

  useEffect(() => {
    renderCountRef.current += 1;
    renderStartRef.current = performance.now();
  });

  useEffect(() => {
    const renderTime = performance.now() - renderStartRef.current;
    
    // Update metrics
    setMetrics(prev => ({
      renderTime,
      memoryUsage: (performance as any).memory?.usedJSHeapSize,
      renderCount: renderCountRef.current
    }));

    // Log slow renders in development
    if (renderTime > 16) {
      console.warn(`Slow render detected in ${componentName}: ${renderTime.toFixed(2)}ms`);
    }
  });

  return metrics;
}

export function useRenderCount() {
  const renderCount = useRef(0);
  renderCount.current += 1;
  return renderCount.current;
}