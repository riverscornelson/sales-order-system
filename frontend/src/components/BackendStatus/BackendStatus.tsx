import { useEffect, useState, memo, useCallback } from 'react';
import type { HealthStatus } from '../../types';

interface BackendStatusProps {
  apiUrl?: string;
}

export const BackendStatus: React.FC<BackendStatusProps> = memo(({ 
  apiUrl = 'http://localhost:8000' 
}) => {
  const [status, setStatus] = useState<string>('Unknown');
  const [isLoading, setIsLoading] = useState(true);

  const checkStatus = useCallback(async () => {
    try {
      const response = await fetch(`${apiUrl}/api/v1/health`);
      const health: HealthStatus = await response.json();
      setStatus(`✅ ${health.status} (${health.timestamp})`);
    } catch (error) {
      setStatus(`❌ Disconnected: ${error}`);
    } finally {
      setIsLoading(false);
    }
  }, [apiUrl]);

  useEffect(() => {
    checkStatus();
    const interval = setInterval(checkStatus, 30000); // Check every 30s
    return () => clearInterval(interval);
  }, [checkStatus]);

  return (
    <div style={{
      position: 'fixed',
      top: 10,
      right: 10,
      padding: '8px 12px',
      backgroundColor: '#f3f4f6',
      borderRadius: '6px',
      fontSize: '12px',
      fontFamily: 'monospace',
      boxShadow: '0 1px 3px rgba(0,0,0,0.1)'
    }}>
      <strong>Backend:</strong> {isLoading ? '⏳ Checking...' : status}
    </div>
  );
});