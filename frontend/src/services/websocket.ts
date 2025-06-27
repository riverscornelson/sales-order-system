import { WebSocketMessage } from '../types/api';

export class WebSocketService {
  private ws: WebSocket | null = null;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 1000;
  private clientId: string;
  private listeners: Map<string, (message: WebSocketMessage) => void> = new Map();

  constructor(clientId: string) {
    this.clientId = clientId;
  }

  connect(): Promise<void> {
    return new Promise((resolve, reject) => {
      const wsUrl = `${import.meta.env.VITE_WS_BASE_URL || 'ws://localhost:8000'}/ws/${this.clientId}`;
      
      this.ws = new WebSocket(wsUrl);

      this.ws.onopen = () => {
        console.log('WebSocket connected');
        this.reconnectAttempts = 0;
        resolve();
      };

      this.ws.onmessage = (event) => {
        try {
          const message: WebSocketMessage = JSON.parse(event.data);
          this.handleMessage(message);
        } catch (error) {
          console.error('Failed to parse WebSocket message:', error);
        }
      };

      this.ws.onclose = () => {
        console.log('WebSocket disconnected');
        this.attemptReconnect();
      };

      this.ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        reject(error);
      };
    });
  }

  private handleMessage(message: WebSocketMessage): void {
    // Notify all listeners
    this.listeners.forEach((callback) => {
      callback(message);
    });
  }

  private attemptReconnect(): void {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++;
      console.log(`Attempting to reconnect (${this.reconnectAttempts}/${this.maxReconnectAttempts})`);
      
      setTimeout(() => {
        this.connect().catch(console.error);
      }, this.reconnectDelay * this.reconnectAttempts);
    }
  }

  subscribe(sessionId: string, callback: (message: WebSocketMessage) => void): () => void {
    const listenerId = `${sessionId}-${Date.now()}`;
    this.listeners.set(listenerId, callback);

    // Send subscription message
    this.send({
      type: 'subscribe',
      session_id: sessionId,
      data: {},
      timestamp: new Date().toISOString(),
    });

    // Return unsubscribe function
    return () => {
      this.listeners.delete(listenerId);
    };
  }

  send(message: WebSocketMessage): void {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(message));
    } else {
      console.warn('WebSocket is not connected');
    }
  }

  disconnect(): void {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
    this.listeners.clear();
  }
}