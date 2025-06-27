export type ProcessingStatus = 'pending' | 'processing' | 'completed' | 'error';

export interface ProcessingCard {
  id: string;
  title: string;
  status: ProcessingStatus;
  content?: Record<string, unknown> | string | null;
  timestamp?: string;
}

export interface WebSocketMessage {
  type: 'status_update' | 'agent_update' | 'final_results' | 'error' | string;
  data: {
    id?: string;
    step?: string;
    status?: ProcessingStatus;
    message?: string;
    [key: string]: unknown;
  };
  timestamp?: string;
}

export interface UploadResponse {
  session_id: string;
  client_id: string;
  filename: string;
  content_type: string;
}

export interface HealthStatus {
  status: string;
  timestamp: string;
  version?: string;
}

export interface SessionData {
  session_id: string;
  status: string;
  created_at: string;
  updated_at: string;
  results?: Record<string, unknown>;
}