import { useState, useEffect, useCallback } from 'react';

export interface JobStatus {
  id: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  progress?: number;
  step?: string;
  message?: string;
  results?: any;
  error?: string;
  timestamp: string;
}

interface UseJobPollingOptions {
  interval?: number; // Polling interval in ms (default: 2000)
  maxRetries?: number; // Max retry attempts on error (default: 3)
  onStatusChange?: (status: JobStatus) => void;
  onComplete?: (results: any) => void;
  onError?: (error: string) => void;
}

export const useJobPolling = (
  jobId: string | null,
  options: UseJobPollingOptions = {}
) => {
  const {
    interval = 2000,
    maxRetries = 3,
    onStatusChange,
    onComplete,
    onError
  } = options;

  const [status, setStatus] = useState<JobStatus | null>(null);
  const [isPolling, setIsPolling] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [retryCount, setRetryCount] = useState(0);

  const fetchStatus = useCallback(async () => {
    if (!jobId) return;

    try {
      // Call your backend API to get job status
      const response = await fetch(`/api/jobs/${jobId}/status`);
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const jobStatus: JobStatus = await response.json();
      
      setStatus(jobStatus);
      setError(null);
      setRetryCount(0);

      // Trigger callbacks
      onStatusChange?.(jobStatus);

      if (jobStatus.status === 'completed') {
        setIsPolling(false);
        onComplete?.(jobStatus.results);
      } else if (jobStatus.status === 'failed') {
        setIsPolling(false);
        const errorMsg = jobStatus.error || 'Job failed';
        setError(errorMsg);
        onError?.(errorMsg);
      }

    } catch (err) {
      console.error('Polling error:', err);
      const errorMessage = err instanceof Error ? err.message : 'Unknown error';
      
      if (retryCount < maxRetries) {
        setRetryCount(prev => prev + 1);
        // Continue polling with exponential backoff
        setTimeout(() => {}, Math.min(interval * Math.pow(2, retryCount), 10000));
      } else {
        setError(errorMessage);
        setIsPolling(false);
        onError?.(errorMessage);
      }
    }
  }, [jobId, retryCount, maxRetries, interval, onStatusChange, onComplete, onError]);

  // Start/stop polling based on jobId and job status
  useEffect(() => {
    if (!jobId) {
      setIsPolling(false);
      setStatus(null);
      setError(null);
      setRetryCount(0);
      return;
    }

    // Don't poll if job is already completed or failed
    if (status?.status === 'completed' || status?.status === 'failed') {
      setIsPolling(false);
      return;
    }

    setIsPolling(true);
    
    // Initial fetch
    fetchStatus();

    // Set up polling interval
    const intervalId = setInterval(fetchStatus, interval);

    return () => {
      clearInterval(intervalId);
      setIsPolling(false);
    };
  }, [jobId, fetchStatus, interval, status?.status]);

  // Manual refresh function
  const refresh = useCallback(() => {
    if (jobId) {
      setRetryCount(0);
      setError(null);
      fetchStatus();
    }
  }, [jobId, fetchStatus]);

  return {
    status,
    isPolling,
    error,
    refresh,
    retryCount
  };
};