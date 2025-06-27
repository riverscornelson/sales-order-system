import axios from 'axios';
import { UploadResponse, OrderProcessingSession, OrderData } from '../types/api';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
});

export const apiService = {
  // Upload document
  uploadDocument: async (file: File): Promise<UploadResponse> => {
    const formData = new FormData();
    formData.append('file', file);
    
    const response = await api.post<UploadResponse>('/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    
    return response.data;
  },

  // Get session status
  getSessionStatus: async (sessionId: string): Promise<OrderProcessingSession> => {
    const response = await api.get<OrderProcessingSession>(`/sessions/${sessionId}`);
    return response.data;
  },

  // Submit order to ERP
  submitOrder: async (sessionId: string, orderData: OrderData): Promise<any> => {
    const response = await api.post(`/orders/${sessionId}/submit`, orderData);
    return response.data;
  },

  // Health check
  healthCheck: async (): Promise<any> => {
    const response = await api.get('/health');
    return response.data;
  },
};