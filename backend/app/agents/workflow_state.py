from typing import Dict, List, Optional, Any
from pydantic import BaseModel
from enum import Enum
from datetime import datetime

class WorkflowStage(str, Enum):
    UPLOAD = "upload"
    DOCUMENT_PARSING = "document_parsing"
    ORDER_EXTRACTION = "order_extraction"
    SEMANTIC_SEARCH = "semantic_search"
    ERP_VALIDATION = "erp_validation"
    REVIEW_PREPARATION = "review_preparation"
    COMPLETED = "completed"
    ERROR = "error"

class AgentStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    ERROR = "error"

class AgentMessage(BaseModel):
    agent_name: str
    stage: WorkflowStage
    status: AgentStatus
    data: Dict[str, Any]
    timestamp: datetime
    error: Optional[str] = None

class WorkflowState(BaseModel):
    """Shared state across all agents in the workflow"""
    
    # Session metadata
    session_id: str
    client_id: str
    
    # Current workflow status
    current_stage: WorkflowStage = WorkflowStage.UPLOAD
    stage_history: List[WorkflowStage] = []
    
    # Document information
    document_filename: Optional[str] = None
    document_type: Optional[str] = None
    document_content: Optional[str] = None
    
    # Extracted data
    raw_text: Optional[str] = None
    extracted_customer_info: Optional[Dict[str, Any]] = None
    extracted_line_items: List[Dict[str, Any]] = []
    
    # Semantic search results
    part_matches: Dict[str, List[Dict[str, Any]]] = {}
    
    # ERP validation results
    customer_validation: Optional[Dict[str, Any]] = None
    inventory_check: Optional[Dict[str, Any]] = None
    pricing_info: Optional[Dict[str, Any]] = None
    
    # Final order data
    final_order_data: Optional[Dict[str, Any]] = None
    draft_order_id: Optional[str] = None
    
    # Agent communication
    agent_messages: List[AgentMessage] = []
    
    # Error handling
    errors: List[str] = []
    retry_count: int = 0
    max_retries: int = 3
    
    # Timestamps
    created_at: datetime
    updated_at: datetime
    
    def add_message(self, agent_name: str, stage: WorkflowStage, status: AgentStatus, 
                   data: Dict[str, Any], error: Optional[str] = None):
        """Add a message from an agent"""
        message = AgentMessage(
            agent_name=agent_name,
            stage=stage,
            status=status,
            data=data,
            timestamp=datetime.now(),
            error=error
        )
        self.agent_messages.append(message)
        self.updated_at = datetime.now()
    
    def transition_to_stage(self, stage: WorkflowStage):
        """Transition to a new workflow stage"""
        if self.current_stage != stage:
            self.stage_history.append(self.current_stage)
            self.current_stage = stage
            self.updated_at = datetime.now()
    
    def add_error(self, error: str):
        """Add an error to the workflow"""
        self.errors.append(error)
        self.updated_at = datetime.now()
    
    def can_retry(self) -> bool:
        """Check if the workflow can be retried"""
        return self.retry_count < self.max_retries
    
    def increment_retry(self):
        """Increment the retry counter"""
        self.retry_count += 1
        self.updated_at = datetime.now()
    
    def get_latest_message_by_agent(self, agent_name: str) -> Optional[AgentMessage]:
        """Get the latest message from a specific agent"""
        for message in reversed(self.agent_messages):
            if message.agent_name == agent_name:
                return message
        return None
    
    def get_messages_by_stage(self, stage: WorkflowStage) -> List[AgentMessage]:
        """Get all messages for a specific stage"""
        return [msg for msg in self.agent_messages if msg.stage == stage]