import { UploadResponse, SessionData } from '../types';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

export class ApiService {
  private baseUrl: string;

  constructor(baseUrl: string = API_BASE_URL) {
    this.baseUrl = baseUrl;
  }

  async uploadFile(file: File): Promise<UploadResponse> {
    const formData = new FormData();
    formData.append('file', file);

    const response = await fetch(`${this.baseUrl}/api/v1/upload`, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      throw new Error(`Upload failed: ${response.statusText}`);
    }

    return response.json();
  }

  async getSession(sessionId: string): Promise<SessionData> {
    const response = await fetch(`${this.baseUrl}/api/v1/sessions/${sessionId}`);
    
    if (!response.ok) {
      throw new Error(`Failed to fetch session: ${response.statusText}`);
    }

    return response.json();
  }

  async checkHealth() {
    const response = await fetch(`${this.baseUrl}/api/v1/health`);
    return response.json();
  }

  getWebSocketUrl(clientId: string): string {
    const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsHost = this.baseUrl.replace(/^https?:/, wsProtocol);
    return `${wsHost}/ws/${clientId}`;
  }
}

export const apiService = new ApiService();