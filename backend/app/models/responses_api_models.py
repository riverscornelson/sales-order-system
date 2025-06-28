"""
Simplified Pydantic Models for OpenAI Responses API

These models are specifically designed to comply with the strict requirements
of the Responses API structured outputs feature:

1. No optional fields (all properties are required)
2. No complex inheritance (no allOf constructs)
3. Simple, flat object structures
4. Basic JSON Schema types only
5. additionalProperties: false everywhere
"""

from typing import List, Dict, Any
from pydantic import BaseModel, Field


# =============================================================================
# CORE BUSINESS MODELS - SIMPLIFIED FOR RESPONSES API
# =============================================================================

class SimpleCustomerInfo(BaseModel):
    """Simplified customer information for Responses API"""
    company_name: str = Field(description="Company or customer name")
    contact_name: str = Field(description="Contact person name, use 'Unknown' if not found")
    email: str = Field(description="Email address, use 'unknown@example.com' if not found")
    phone: str = Field(description="Phone number, use 'Unknown' if not found")
    customer_id: str = Field(description="Customer ID if available, use 'Unknown' if not found")


class SimpleLineItem(BaseModel):
    """Simplified line item for Responses API"""
    item_number: int = Field(description="Sequential item number starting from 1")
    description: str = Field(description="Complete item description as written")
    quantity: int = Field(description="Quantity requested, default to 1 if unclear")
    material: str = Field(description="Material type (steel, aluminum, etc.) or 'Unknown'")
    unit_price: float = Field(description="Unit price if mentioned, use 0.0 if not found")
    specifications: str = Field(description="Technical specifications as single string, use 'None' if not found")


class SimpleOrderDetails(BaseModel):
    """Simplified order details for Responses API"""
    order_date: str = Field(description="Order date if mentioned, use 'Unknown' if not found")
    delivery_date: str = Field(description="Requested delivery date, use 'Unknown' if not found")
    priority: str = Field(description="Priority level: HIGH, MEDIUM, or LOW")
    payment_terms: str = Field(description="Payment terms, use 'Unknown' if not found")
    special_instructions: str = Field(description="Special instructions, use 'None' if not found")


class SimpleERPOrder(BaseModel):
    """Simplified ERP order structure for Responses API - MAIN EVALUATION TARGET"""
    customer_info: SimpleCustomerInfo = Field(description="Customer information")
    line_items: List[SimpleLineItem] = Field(description="List of line items")
    order_details: SimpleOrderDetails = Field(description="Order metadata")
    total_amount: float = Field(description="Total order amount, use 0.0 if not calculable")
    order_id: str = Field(description="Generated order ID")


# =============================================================================
# ANALYSIS MODELS - SIMPLIFIED FOR RESPONSES API
# =============================================================================

class SimpleCustomerAnalysis(BaseModel):
    """Simplified customer context analysis for Responses API"""
    industry_sector: str = Field(description="Industry sector (manufacturing, construction, etc.)")
    company_size: str = Field(description="Company size: SMALL, MEDIUM, or LARGE")
    customer_tier: str = Field(description="Customer tier: PREMIUM, STANDARD, or BASIC")
    compliance_level: str = Field(description="Compliance requirements: HIGH, MEDIUM, or LOW")


class SimpleEmergencyAssessment(BaseModel):
    """Simplified emergency detection for Responses API"""
    urgency_level: str = Field(description="Urgency level: CRITICAL, HIGH, MEDIUM, or LOW")
    emergency_indicators: str = Field(description="Emergency keywords found, comma-separated")
    time_constraint: str = Field(description="Time constraint mentioned or 'None'")
    business_impact: str = Field(description="Potential business impact: HIGH, MEDIUM, or LOW")


class SimpleOrderAnalysis(BaseModel):
    """Simplified comprehensive order analysis for Responses API"""
    customer_analysis: SimpleCustomerAnalysis = Field(description="Customer context")
    emergency_assessment: SimpleEmergencyAssessment = Field(description="Emergency evaluation")
    complexity_level: str = Field(description="Order complexity: HIGH, MEDIUM, or LOW")
    total_line_items: int = Field(description="Number of line items found")
    confidence_score: float = Field(description="Overall confidence score 0.0-1.0")


# =============================================================================
# PART MATCHING MODELS - SIMPLIFIED FOR RESPONSES API
# =============================================================================

class SimplePartMatch(BaseModel):
    """Simplified part matching result for Responses API"""
    selected_part_number: str = Field(description="Best matching part number")
    confidence_score: float = Field(description="Match confidence 0.0-1.0")
    match_reasoning: str = Field(description="Why this part was selected")
    specification_match: float = Field(description="Specification match score 0.0-1.0")
    material_compatibility: float = Field(description="Material compatibility 0.0-1.0")
    availability_score: float = Field(description="Availability score 0.0-1.0")
    alternative_part: str = Field(description="Alternative part number or 'None'")
    risk_factors: str = Field(description="Risk factors, comma-separated or 'None'")


# =============================================================================
# ORDER EXTRACTION MODELS - SIMPLIFIED FOR RESPONSES API
# =============================================================================

class SimpleOrderData(BaseModel):
    """Simplified order extraction result for Responses API"""
    customer_company: str = Field(description="Customer company name")
    customer_email: str = Field(description="Customer email address")
    customer_phone: str = Field(description="Customer phone number")
    line_item_1_desc: str = Field(description="First line item description or 'None'")
    line_item_1_qty: int = Field(description="First line item quantity or 0")
    line_item_1_material: str = Field(description="First line item material or 'Unknown'")
    line_item_2_desc: str = Field(description="Second line item description or 'None'")
    line_item_2_qty: int = Field(description="Second line item quantity or 0")
    line_item_2_material: str = Field(description="Second line item material or 'Unknown'")
    line_item_3_desc: str = Field(description="Third line item description or 'None'")
    line_item_3_qty: int = Field(description="Third line item quantity or 0")
    line_item_3_material: str = Field(description="Third line item material or 'Unknown'")
    order_date: str = Field(description="Order date")
    delivery_date: str = Field(description="Delivery date")
    total_items: int = Field(description="Total number of line items found")
    confidence_score: float = Field(description="Extraction confidence 0.0-1.0")


# =============================================================================
# METADATA EXTRACTION MODELS - SIMPLIFIED FOR RESPONSES API
# =============================================================================

class SimpleOrderMetadata(BaseModel):
    """Simplified order metadata for Responses API"""
    customer_name: str = Field(description="Customer or company name")
    contact_person: str = Field(description="Contact person name")
    contact_email: str = Field(description="Contact email")
    contact_phone: str = Field(description="Contact phone")
    po_number: str = Field(description="Purchase order number")
    priority_level: str = Field(description="Priority: HIGH, MEDIUM, or LOW")
    delivery_date: str = Field(description="Delivery date")
    project_name: str = Field(description="Project name")
    payment_terms: str = Field(description="Payment terms")
    credit_approved: str = Field(description="Credit approval status: YES or NO")


class SimpleDeliveryInstructions(BaseModel):
    """Simplified delivery instructions for Responses API"""
    delivery_address: str = Field(description="Delivery address")
    special_instructions: str = Field(description="Special delivery instructions")
    delivery_date: str = Field(description="Requested delivery date")
    delivery_method: str = Field(description="Delivery method")
    contact_person: str = Field(description="Contact for delivery")


# =============================================================================
# HELPER FUNCTIONS FOR MODEL CONVERSION
# =============================================================================

def convert_simple_to_complex_erp(simple_order: SimpleERPOrder) -> Dict[str, Any]:
    """Convert simplified ERP model to complex model format"""
    return {
        "customer_info": {
            "company_name": simple_order.customer_info.company_name,
            "contact_name": simple_order.customer_info.contact_name,
            "email": simple_order.customer_info.email,
            "phone": simple_order.customer_info.phone,
            "customer_id": simple_order.customer_info.customer_id
        },
        "line_items": [
            {
                "item_number": item.item_number,
                "description": item.description,
                "quantity": item.quantity,
                "material": item.material,
                "unit_price": item.unit_price,
                "specifications": {"raw": item.specifications} if item.specifications != "None" else {}
            }
            for item in simple_order.line_items
        ],
        "order_details": {
            "order_date": simple_order.order_details.order_date,
            "delivery_date": simple_order.order_details.delivery_date,
            "priority": simple_order.order_details.priority,
            "payment_terms": simple_order.order_details.payment_terms,
            "special_instructions": simple_order.order_details.special_instructions
        },
        "total_amount": simple_order.total_amount,
        "order_id": simple_order.order_id
    }


def convert_simple_order_data_to_dict(simple_data: SimpleOrderData) -> Dict[str, Any]:
    """Convert simplified order data to standard extraction format"""
    line_items = []
    
    # Convert flattened line items back to list
    for i in range(1, 4):  # Support up to 3 line items
        desc_key = f"line_item_{i}_desc"
        qty_key = f"line_item_{i}_qty"
        mat_key = f"line_item_{i}_material"
        
        desc = getattr(simple_data, desc_key)
        qty = getattr(simple_data, qty_key)
        material = getattr(simple_data, mat_key)
        
        if desc and desc != "None" and qty > 0:
            line_items.append({
                "description": desc,
                "quantity": qty,
                "material": material if material != "Unknown" else None
            })
    
    return {
        "customer_info": {
            "company": simple_data.customer_company,
            "email": simple_data.customer_email,
            "phone": simple_data.customer_phone
        },
        "line_items": line_items,
        "order_details": {
            "order_date": simple_data.order_date,
            "delivery_date": simple_data.delivery_date
        },
        "confidence": {
            "overall": simple_data.confidence_score,
            "model": "gpt-4.1",
            "api": "responses_api"
        }
    }


# =============================================================================
# MODEL REGISTRY FOR EASY ACCESS
# =============================================================================

SIMPLE_STRUCTURED_OUTPUT_MODELS = {
    "SimpleERPOrder": SimpleERPOrder,
    "SimpleOrderAnalysis": SimpleOrderAnalysis,
    "SimplePartMatch": SimplePartMatch,
    "SimpleOrderData": SimpleOrderData,
    "SimpleOrderMetadata": SimpleOrderMetadata,
    "SimpleDeliveryInstructions": SimpleDeliveryInstructions,
    "SimpleCustomerInfo": SimpleCustomerInfo,
    "SimpleLineItem": SimpleLineItem
}


def get_simple_model(model_name: str) -> type:
    """Get simplified model by name"""
    if model_name not in SIMPLE_STRUCTURED_OUTPUT_MODELS:
        raise ValueError(f"Unknown simple model: {model_name}. Available: {list(SIMPLE_STRUCTURED_OUTPUT_MODELS.keys())}")
    return SIMPLE_STRUCTURED_OUTPUT_MODELS[model_name]