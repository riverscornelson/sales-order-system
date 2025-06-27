from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

class ProcessingStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    ERROR = "error"

class ConfidenceLevel(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

class DocumentType(str, Enum):
    PDF = "pdf"
    EMAIL = "email"

class OrderLineItem(BaseModel):
    part_number: Optional[str] = None
    description: str
    quantity: int
    unit_price: Optional[float] = None
    total_price: Optional[float] = None
    matched_part_id: Optional[str] = None
    confidence_score: Optional[float] = None
    alternatives: List[Dict[str, Any]] = []

class CustomerInfo(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    company: Optional[str] = None
    address: Optional[str] = None
    customer_id: Optional[str] = None

class OrderData(BaseModel):
    customer_info: CustomerInfo
    line_items: List[OrderLineItem]
    order_date: Optional[datetime] = None
    delivery_date: Optional[datetime] = None
    special_instructions: Optional[str] = None
    total_amount: Optional[float] = None

class ProcessingCard(BaseModel):
    id: str
    title: str
    status: ProcessingStatus
    content: Dict[str, Any]
    timestamp: datetime = Field(default_factory=datetime.now)
    confidence: Optional[ConfidenceLevel] = None

class OrderProcessingSession(BaseModel):
    session_id: str
    document_type: DocumentType
    filename: str
    status: ProcessingStatus
    cards: List[ProcessingCard] = []
    order_data: Optional[OrderData] = None
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

class PartMatch(BaseModel):
    part_id: str
    part_number: str
    description: str
    confidence_score: float
    unit_price: Optional[float] = None
    availability: Optional[int] = None
    specifications: Dict[str, Any] = {}

class WebSocketMessage(BaseModel):
    type: str
    session_id: str
    data: Dict[str, Any]
    timestamp: datetime = Field(default_factory=datetime.now)