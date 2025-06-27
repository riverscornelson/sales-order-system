import { useEffect, useRef, useCallback } from 'react';
import { WebSocketService } from '../services/websocket';
import { WebSocketMessage } from '../types/api';

interface UseWebSocketOptions {
  onMessage?: (message: WebSocketMessage) => void;
  onConnect?: () => void;
  onDisconnect?: () => void;
  onError?: (error: Event) => void;
  reconnectAttempts?: number;
  reconnectDelay?: number;
}

export const useWebSocket = (
  clientId: string,
  options: UseWebSocketOptions = {}
) => {
  const {
    onMessage,
    onConnect,
    onDisconnect,
    onError,
    reconnectAttempts = 5,
    reconnectDelay = 1000
  } = options;

  const wsRef = useRef<WebSocketService | null>(null);
  const reconnectCountRef = useRef(0);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  const connect = useCallback(async () => {
    try {
      if (wsRef.current) {
        wsRef.current.disconnect();
      }

      const ws = new WebSocketService(clientId);
      wsRef.current = ws;

      await ws.connect();
      reconnectCountRef.current = 0;
      onConnect?.();

      // Set up message listener
      if (onMessage) {
        ws.subscribe('', onMessage);
      }

    } catch (error) {
      console.error('WebSocket connection failed:', error);
      onError?.(error as Event);
      
      // Attempt reconnection
      if (reconnectCountRef.current < reconnectAttempts) {
        reconnectCountRef.current++;
        reconnectTimeoutRef.current = setTimeout(() => {
          connect();
        }, reconnectDelay * reconnectCountRef.current);
      }
    }
  }, [clientId, onMessage, onConnect, onError, reconnectAttempts, reconnectDelay]);

  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }

    if (wsRef.current) {
      wsRef.current.disconnect();
      wsRef.current = null;
    }

    onDisconnect?.();
  }, [onDisconnect]);

  const sendMessage = useCallback((message: WebSocketMessage) => {
    if (wsRef.current) {
      wsRef.current.send(message);
    } else {
      console.warn('WebSocket not connected');
    }
  }, []);

  const subscribeToSession = useCallback((sessionId: string, callback: (message: WebSocketMessage) => void) => {
    if (wsRef.current) {
      return wsRef.current.subscribe(sessionId, callback);
    }
    return () => {};
  }, []);

  useEffect(() => {
    connect();

    return () => {
      disconnect();
    };
  }, [connect, disconnect]);

  return {
    connect,
    disconnect,
    sendMessage,
    subscribeToSession,
    isConnected: wsRef.current !== null,
    reconnectCount: reconnectCountRef.current
  };
};