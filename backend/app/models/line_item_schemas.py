from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum

class LineItemStatus(str, Enum):
    PENDING = "pending"
    EXTRACTING = "extracting"
    SEARCHING = "searching"
    MATCHING = "matching"
    MATCHED = "matched"
    MANUAL_REVIEW = "manual_review"
    FAILED = "failed"
    COMPLETED = "completed"

class MatchConfidence(str, Enum):
    HIGH = "high"
    MEDIUM_HIGH = "medium-high"
    MEDIUM = "medium"
    MEDIUM_LOW = "medium-low"
    LOW = "low"

class ProcessingStage(str, Enum):
    EXTRACTION = "extraction"
    SEMANTIC_SEARCH = "semantic_search"
    MATCHING = "matching"
    ASSEMBLY = "assembly"
    ERP_VALIDATION = "erp_validation"
    REVIEW = "review"

class ExtractedSpecs(BaseModel):
    """Structured specifications extracted from line item text"""
    material_grade: Optional[str] = None
    form: Optional[str] = None  # sheet, plate, bar, tube, etc.
    dimensions: Optional[Dict[str, Any]] = None  # length, width, thickness, diameter, etc.
    quantity: Optional[int] = None
    units: Optional[str] = None  # inches, mm, feet, etc.
    tolerances: Optional[Dict[str, str]] = None
    surface_finish: Optional[str] = None
    heat_treatment: Optional[str] = None
    certifications: Optional[List[str]] = None
    special_requirements: Optional[List[str]] = None
    grade_equivalents: Optional[List[str]] = None  # Alternative acceptable grades

class LineItem(BaseModel):
    """Individual line item from sales order"""
    line_id: str = Field(..., description="Unique identifier for line item")
    project: Optional[str] = None
    raw_text: str = Field(..., description="Exact text from original document")
    extracted_specs: Optional[ExtractedSpecs] = None
    urgency: Optional[str] = None  # HIGH, MEDIUM, LOW
    special_requirements: Optional[List[str]] = None
    delivery_date: Optional[str] = None
    shipping_address: Optional[str] = None
    
    # Processing state
    status: LineItemStatus = LineItemStatus.PENDING
    current_stage: Optional[ProcessingStage] = None
    processing_start_time: Optional[datetime] = None
    processing_end_time: Optional[datetime] = None
    
    # Search results
    search_results: Optional[List[Dict[str, Any]]] = None
    selected_match: Optional[Dict[str, Any]] = None
    match_confidence: Optional[MatchConfidence] = None
    
    # Issues and notes
    issues: List[str] = []
    notes: List[str] = []
    requires_approval: bool = False

class OrderMetadata(BaseModel):
    """Order-level metadata"""
    customer: Optional[str] = None
    contact_person: Optional[str] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    po_number: Optional[str] = None
    priority: Optional[str] = None  # HIGH, MEDIUM, LOW
    delivery_date: Optional[str] = None
    projects: Optional[List[str]] = None
    payment_terms: Optional[str] = None
    credit_approval: Optional[str] = None

class DeliveryInstructions(BaseModel):
    """Delivery and shipping information"""
    default_address: Optional[str] = None
    special_shipping: Optional[Dict[str, str]] = None  # project -> address
    shipping_notes: Optional[List[str]] = None
    delivery_requirements: Optional[List[str]] = None

class EnhancedOrder(BaseModel):
    """Complete order with line items and metadata"""
    order_id: str
    session_id: str
    created_at: datetime = Field(default_factory=datetime.now)
    
    # Order information
    order_metadata: OrderMetadata
    line_items: List[LineItem]
    delivery_instructions: Optional[DeliveryInstructions] = None
    
    # Processing status
    overall_status: str = "pending"
    total_line_items: int = 0
    processed_items: int = 0
    matched_items: int = 0
    review_required_items: int = 0
    
    # Totals (calculated after matching)
    estimated_total: Optional[float] = None
    currency: str = "USD"

class SearchResult(BaseModel):
    """Individual search result for a line item"""
    rank: int
    part_number: str
    description: str
    similarity_score: float
    spec_match: Dict[str, str]  # field -> match_type (exact, similar, missing)
    availability: Optional[int] = None
    unit_price: Optional[float] = None
    supplier: Optional[str] = None
    lead_time: Optional[str] = None
    match_confidence: MatchConfidence
    notes: Optional[List[str]] = None

class MatchSelection(BaseModel):
    """Selected match for a line item"""
    selected_part_number: str
    confidence: MatchConfidence
    reasoning: str
    concerns: List[str] = []
    alternatives: List[str] = []
    requires_approval: bool = False
    match_score: float
    selection_metadata: Dict[str, Any] = {}

class LineItemProcessingState(BaseModel):
    """Processing state for individual line item"""
    line_id: str
    status: LineItemStatus
    current_stage: Optional[ProcessingStage] = None
    progress: float = 0.0  # 0.0 to 1.0
    message: Optional[str] = None
    search_results: Optional[List[SearchResult]] = None
    selected_match: Optional[MatchSelection] = None
    processing_time: float = 0.0
    error_message: Optional[str] = None

class OrderProcessingState(BaseModel):
    """Overall order processing state"""
    order_id: str
    session_id: str
    client_id: str
    overall_status: str = "pending"
    current_stage: Optional[ProcessingStage] = None
    
    # Line item states
    line_item_states: Dict[str, LineItemProcessingState] = {}
    
    # Progress tracking
    total_items: int = 0
    completed_items: int = 0
    progress: float = 0.0
    
    # Timing
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    # Results
    final_order: Optional[Dict[str, Any]] = None
    issues: List[str] = []

class AssembledOrder(BaseModel):
    """Final assembled order ready for ERP/Review"""
    order_summary: Dict[str, Any]
    line_items: List[Dict[str, Any]]
    issues_requiring_review: List[Dict[str, Any]] = []
    totals: Dict[str, Any] = {}
    next_steps: List[str] = []
    approval_required: bool = False
    confidence_score: float = 0.0