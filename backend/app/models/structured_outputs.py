"""
Legacy Structured Output Models for Sales Order Intelligence

⚠️  DEPRECATED: These complex models have been replaced with flat models
for compatibility with OpenAI Responses API. See flat_responses_models.py

These models are maintained for:
- Legacy compatibility during transition
- Reference implementations
- Complex data structures that may be needed for specific ERP formats

For new development, use the flat models in flat_responses_models.py
"""

from typing import Dict, List, Optional, Union, Literal, Any
from pydantic import BaseModel, Field, validator, root_validator
from datetime import datetime
from enum import Enum
from decimal import Decimal


# =============================================================================
# PRIORITY 1: ERP JSON STRUCTURED OUTPUTS (Fixes OpenAI Eval Issues)
# =============================================================================

class ERPCustomerInfo(BaseModel):
    """Structured customer information for ERP import"""
    name: str = Field(..., description="Customer company name")
    customer_id: Optional[str] = Field(None, description="ERP customer ID if known")
    contact_person: Optional[str] = Field(None, description="Primary contact name")
    email: Optional[str] = Field(None, description="Contact email")
    phone: Optional[str] = Field(None, description="Contact phone")
    industry: Optional[str] = Field(None, description="Customer industry")
    tier: Optional[Literal["key_account", "preferred", "small_business", "unknown"]] = Field(
        None, description="Customer tier classification"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "Ford Motor Company - Dearborn Plant",
                "customer_id": "FORD-001",
                "contact_person": "Mike Rodriguez",
                "email": "mrodriguez@ford.com",
                "phone": "313-555-0147",
                "industry": "automotive",
                "tier": "key_account"
            }
        }


class ERPMaterialSpecification(BaseModel):
    """Structured material specifications for ERP line items"""
    material_grade: str = Field(..., description="Material grade (e.g., 316L, 1018, 6061-T6)")
    form: str = Field(..., description="Material form (e.g., plate, rod, tube, sheet)")
    dimensions: Dict[str, Union[float, str]] = Field(
        default_factory=dict, 
        description="Dimensions (diameter, length, thickness, etc.)"
    )
    finish: Optional[str] = Field(None, description="Surface finish requirements")
    certifications: List[str] = Field(
        default_factory=list, 
        description="Required certifications (mill_cert, AS9100, etc.)"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "material_grade": "316L",
                "form": "seamless tubing",
                "dimensions": {
                    "outer_diameter": 2.5,
                    "wall_thickness": 0.065,
                    "length": 48,
                    "units": "inches"
                },
                "finish": "mill_finish",
                "certifications": ["mill_cert"]
            }
        }


class ERPLineItem(BaseModel):
    """Structured line item for ERP import - FIXES FIELD NAME INCONSISTENCY"""
    line_id: str = Field(..., description="Unique line item identifier")
    material: str = Field(..., description="Material type/grade - CONSISTENT FIELD NAME")
    quantity: float = Field(..., gt=0, description="Quantity requested")
    unit: str = Field(default="pieces", description="Unit of measure")
    specifications: ERPMaterialSpecification = Field(
        ..., description="Detailed material specifications"
    )
    part_number: Optional[str] = Field(None, description="Matched part number from inventory")
    unit_price: Optional[Decimal] = Field(None, description="Unit price if available")
    total_price: Optional[Decimal] = Field(None, description="Total line price")
    availability: Optional[Literal["in_stock", "special_order", "unavailable"]] = Field(
        None, description="Inventory availability status"
    )
    urgency: Optional[Literal["standard", "expedited", "emergency", "critical"]] = Field(
        "standard", description="Delivery urgency level"
    )
    
    @validator('material')
    def material_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('Material field cannot be empty')
        return v.strip()
    
    class Config:
        json_schema_extra = {
            "example": {
                "line_id": "L001",
                "material": "316L Stainless Steel",  # CONSISTENT FIELD NAME
                "quantity": 6,
                "unit": "pieces",
                "specifications": {
                    "material_grade": "316L",
                    "form": "seamless tubing",
                    "dimensions": {
                        "outer_diameter": 2.5,
                        "wall_thickness": 0.065,
                        "length": 48
                    }
                },
                "part_number": "SS316L-TUBE-2.5-0.065",
                "availability": "in_stock",
                "urgency": "critical"
            }
        }


class ERPOrderMetadata(BaseModel):
    """Structured order metadata for ERP processing"""
    order_id: str = Field(..., description="Generated order identifier")
    priority: Literal["standard", "expedited", "emergency", "critical"] = Field(
        "standard", description="Overall order priority"
    )
    requested_delivery: Optional[datetime] = Field(None, description="Requested delivery date")
    project_reference: Optional[str] = Field(None, description="Customer project reference")
    special_instructions: List[str] = Field(
        default_factory=list, description="Special handling instructions"
    )
    processing_strategy: Literal[
        "exact_match", "alternative_products", "split_shipment", 
        "expedited_restock", "custom_solution"
    ] = Field("exact_match", description="Fulfillment strategy")
    complexity_level: Literal["simple", "moderate", "complex", "critical"] = Field(
        "simple", description="Order complexity assessment"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "order_id": "ORD-FORD-20240628-001",
                "priority": "emergency",
                "requested_delivery": "2024-06-29T14:00:00Z",
                "project_reference": "F-150 production schedule",
                "special_instructions": ["mill_cert_required", "immediate_delivery"],
                "processing_strategy": "exact_match",
                "complexity_level": "critical"
            }
        }


class ERPOrderOutput(BaseModel):
    """Complete structured ERP order output - SOLVES OPENAI EVAL ISSUES"""
    customer: ERPCustomerInfo = Field(..., description="Customer information")
    line_items: List[ERPLineItem] = Field(..., description="Order line items")
    order_metadata: ERPOrderMetadata = Field(..., description="Order processing metadata")
    
    @validator('line_items')
    def line_items_not_empty(cls, v):
        if not v:
            raise ValueError('Order must have at least one line item')
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "customer": {
                    "name": "Ford Motor Company - Dearborn Plant",
                    "customer_id": "FORD-001",
                    "tier": "key_account",
                    "industry": "automotive"
                },
                "line_items": [{
                    "line_id": "L001",
                    "material": "316L Stainless Steel",
                    "quantity": 6,
                    "specifications": {
                        "material_grade": "316L",
                        "form": "seamless tubing"
                    }
                }],
                "order_metadata": {
                    "order_id": "ORD-FORD-20240628-001",
                    "priority": "emergency",
                    "complexity_level": "critical"
                }
            }
        }


# =============================================================================
# PRIORITY 2: LLM AGENT STRUCTURED OUTPUTS
# =============================================================================

class CustomerContextAnalysis(BaseModel):
    """Structured customer context analysis output"""
    industry_sector: str = Field(..., description="Identified industry sector")
    customer_tier: Literal["key_account", "preferred", "small_business", "unknown"] = Field(
        ..., description="Customer tier classification"
    )
    business_size: Literal["enterprise", "mid_market", "small_business", "individual"] = Field(
        ..., description="Business size classification"
    )
    flexibility_score: float = Field(
        ..., ge=0, le=1, description="Customer flexibility score (0-1)"
    )
    payment_terms: Optional[str] = Field(None, description="Preferred payment terms")
    compliance_requirements: List[str] = Field(
        default_factory=list, description="Industry compliance requirements"
    )
    confidence_score: float = Field(
        ..., ge=0, le=1, description="Analysis confidence (0-1)"
    )


class EmergencyDetection(BaseModel):
    """Structured emergency situation detection"""
    emergency_detected: bool = Field(..., description="Whether emergency situation detected")
    emergency_type: Optional[Literal[
        "production_down", "equipment_failure", "supply_shortage", 
        "deadline_critical", "safety_issue", "regulatory_deadline"
    ]] = Field(None, description="Type of emergency if detected")
    urgency_level: Literal["low", "medium", "high", "critical"] = Field(
        ..., description="Urgency level assessment"
    )
    impact_assessment: Optional[str] = Field(None, description="Business impact description")
    time_constraint: Optional[str] = Field(None, description="Time constraint description")
    financial_impact: Optional[str] = Field(None, description="Financial impact if known")
    emergency_indicators: List[str] = Field(
        default_factory=list, description="Text indicators that triggered emergency detection"
    )


class ProductRequirement(BaseModel):
    """Structured product requirement extraction"""
    requirement_id: str = Field(..., description="Unique requirement identifier")
    material_type: str = Field(..., description="Material type (e.g., steel, aluminum)")
    material_grade: Optional[str] = Field(None, description="Specific grade if specified")
    form_factor: str = Field(..., description="Form (plate, rod, tube, etc.)")
    quantity: float = Field(..., gt=0, description="Requested quantity")
    unit: str = Field(..., description="Unit of measure")
    dimensions: Dict[str, Any] = Field(
        default_factory=dict, description="Dimensional requirements"
    )
    tolerances: Dict[str, Any] = Field(
        default_factory=dict, description="Tolerance specifications"
    )
    surface_finish: Optional[str] = Field(None, description="Surface finish requirements")
    certifications: List[str] = Field(
        default_factory=list, description="Required certifications"
    )
    applications: List[str] = Field(
        default_factory=list, description="Intended applications"
    )
    priority: Literal["low", "medium", "high", "critical"] = Field(
        "medium", description="Requirement priority"
    )


class SalesOrderAnalysis(BaseModel):
    """Complete structured sales order analysis output"""
    order_id: str = Field(..., description="Generated order analysis ID")
    customer_context: CustomerContextAnalysis = Field(..., description="Customer analysis")
    emergency_assessment: EmergencyDetection = Field(..., description="Emergency detection")
    product_requirements: List[ProductRequirement] = Field(
        ..., description="Extracted product requirements"
    )
    complexity_assessment: Literal["simple", "moderate", "complex", "critical"] = Field(
        ..., description="Overall order complexity"
    )
    processing_notes: List[str] = Field(
        default_factory=list, description="Additional processing notes"
    )
    confidence_score: float = Field(
        ..., ge=0, le=1, description="Overall analysis confidence"
    )
    analysis_timestamp: datetime = Field(
        default_factory=datetime.now, description="Analysis timestamp"
    )


# =============================================================================
# PRIORITY 3: REASONING FRAMEWORK STRUCTURED OUTPUTS
# =============================================================================

class FulfillmentStrategy(BaseModel):
    """Structured fulfillment strategy"""
    strategy_id: str = Field(..., description="Unique strategy identifier")
    strategy_type: Literal[
        "exact_match", "alternative_products", "split_shipment", 
        "expedited_restock", "custom_solution"
    ] = Field(..., description="Strategy type")
    description: str = Field(..., description="Strategy description")
    confidence_score: float = Field(..., ge=0, le=1, description="Confidence in strategy")
    estimated_fulfillment_time: Optional[str] = Field(
        None, description="Estimated fulfillment time"
    )
    cost_impact: Optional[Literal["lower", "same", "higher", "significantly_higher"]] = Field(
        None, description="Cost impact relative to standard"
    )
    risk_factors: List[str] = Field(
        default_factory=list, description="Associated risk factors"
    )
    advantages: List[str] = Field(
        default_factory=list, description="Strategy advantages"
    )
    requirements: List[str] = Field(
        default_factory=list, description="Requirements for this strategy"
    )


class ReasoningChainStep(BaseModel):
    """Individual step in reasoning chain"""
    step_id: str = Field(..., description="Step identifier")
    step_type: Literal[
        "analysis", "decomposition", "hypothesis", "validation", "synthesis"
    ] = Field(..., description="Type of reasoning step")
    input_data: Dict[str, Any] = Field(..., description="Input data for this step")
    reasoning_process: str = Field(..., description="Description of reasoning process")
    output_data: Dict[str, Any] = Field(..., description="Output data from this step")
    confidence_score: float = Field(..., ge=0, le=1, description="Step confidence")
    dependencies: List[str] = Field(
        default_factory=list, description="IDs of dependent steps"
    )


class SalesOrderReasoning(BaseModel):
    """Complete structured reasoning output"""
    reasoning_id: str = Field(..., description="Unique reasoning session ID")
    order_analysis: SalesOrderAnalysis = Field(..., description="Order analysis results")
    fulfillment_strategies: List[FulfillmentStrategy] = Field(
        ..., description="Generated fulfillment strategies"
    )
    recommended_strategy: str = Field(..., description="ID of recommended strategy")
    reasoning_chain: List[ReasoningChainStep] = Field(
        ..., description="Complete reasoning chain"
    )
    business_intelligence: Dict[str, Any] = Field(
        default_factory=dict, description="Business intelligence insights"
    )
    final_recommendations: List[str] = Field(
        ..., description="Final actionable recommendations"
    )
    overall_confidence: float = Field(
        ..., ge=0, le=1, description="Overall reasoning confidence"
    )
    processing_time_ms: float = Field(..., description="Total processing time")
    created_at: datetime = Field(default_factory=datetime.now)


# =============================================================================
# STRUCTURED OUTPUT UTILITIES
# =============================================================================

class StructuredOutputResponse(BaseModel):
    """Generic wrapper for all structured outputs"""
    success: bool = Field(..., description="Whether operation was successful")
    data: Union[
        ERPOrderOutput, 
        SalesOrderAnalysis, 
        SalesOrderReasoning,
        Any,  # Support flat models and any Pydantic BaseModel
        Dict[str, Any]
    ] = Field(..., description="The structured output data")
    error: Optional[str] = Field(None, description="Error message if failed")
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata"
    )
    
    @validator('data')
    def data_required_when_success(cls, v, values):
        if values.get('success') and v is None:
            raise ValueError('Data is required when success is True')
        return v


# Model registry for dynamic access
STRUCTURED_OUTPUT_MODELS = {
    "erp_order": ERPOrderOutput,
    "sales_analysis": SalesOrderAnalysis,
    "sales_reasoning": SalesOrderReasoning,
    "customer_context": CustomerContextAnalysis,
    "emergency_detection": EmergencyDetection,
    "product_requirement": ProductRequirement,
    "fulfillment_strategy": FulfillmentStrategy,
    "reasoning_step": ReasoningChainStep,
}