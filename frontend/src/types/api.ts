export enum ProcessingStatus {
  PENDING = "pending",
  PROCESSING = "processing", 
  COMPLETED = "completed",
  ERROR = "error"
}

export enum ConfidenceLevel {
  HIGH = "high",
  MEDIUM = "medium",
  LOW = "low"
}

export enum DocumentType {
  PDF = "pdf",
  EMAIL = "email"
}

export interface OrderLineItem {
  part_number?: string;
  description: string;
  quantity: number;
  unit_price?: number;
  total_price?: number;
  matched_part_id?: string;
  confidence_score?: number;
  alternatives: PartMatch[];
}

export interface CustomerInfo {
  name?: string;
  email?: string;
  phone?: string;
  company?: string;
  address?: string;
  customer_id?: string;
}

export interface OrderData {
  customer_info: CustomerInfo;
  line_items: OrderLineItem[];
  order_date?: string;
  delivery_date?: string;
  special_instructions?: string;
  total_amount?: number;
}

export interface ProcessingCard {
  id: string;
  title: string;
  status: ProcessingStatus;
  content: Record<string, any>;
  timestamp: string;
  confidence?: ConfidenceLevel;
}

export interface OrderProcessingSession {
  session_id: string;
  document_type: DocumentType;
  filename: string;
  status: ProcessingStatus;
  cards: ProcessingCard[];
  order_data?: OrderData;
  created_at: string;
  updated_at: string;
}

export interface PartMatch {
  part_id: string;
  part_number: string;
  description: string;
  confidence_score: number;
  unit_price?: number;
  availability?: number;
  specifications: Record<string, any>;
}

export interface WebSocketMessage {
  type: string;
  session_id: string;
  data: Record<string, any>;
  timestamp: string;
}

export interface UploadResponse {
  session_id: string;
  status: string;
  message: string;
}