"""
Structured ERP Integration Agent

This replaces the problematic manual dictionary construction in erp_integration.py
that was causing inconsistent JSON outputs in OpenAI evaluations.

Key Fixes:
- Consistent field names (always 'material', never 'product')
- Validated Pydantic models for all outputs
- Schema-enforced JSON generation
- Comprehensive error handling
"""

from typing import Dict, Any, List, Optional
import structlog
from datetime import datetime

from app.core.responses_client import ResponsesAPIClient, create_sales_order_client
from app.models.structured_outputs import StructuredOutputResponse
from app.models.flat_responses_models import (
    FlatERPOrder, convert_flat_erp_to_standard
)

logger = structlog.get_logger()


class StructuredERPAgent:
    """
    ERP Integration Agent with structured outputs
    
    Replaces manual dictionary construction with validated Pydantic models,
    solving the JSON consistency issues from OpenAI evaluations.
    """
    
    def __init__(self):
        self.sales_client = create_sales_order_client()
        self.logger = logger.bind(agent="structured_erp")
    
    async def process_sales_order_to_erp(
        self,
        customer_email: str,
        customer_name: str,
        order_id: Optional[str] = None
    ) -> StructuredOutputResponse:
        """
        Convert sales order to validated ERP JSON
        
        This is the main function that replaces the problematic
        manual dictionary construction from the original system.
        """
        
        self.logger.info(
            "Processing sales order to ERP JSON",
            customer=customer_name,
            order_id=order_id
        )
        
        try:
            # Step 1: Generate structured ERP JSON using flat model
            erp_response = await self.sales_client.generate_erp_json(
                customer_email=customer_email,
                customer_name=customer_name
            )
            
            if not erp_response.success:
                self.logger.error(
                    "Failed to generate ERP JSON",
                    error=erp_response.error
                )
                return erp_response
            
            # Step 2: Convert flat model to standard format for processing
            flat_erp_data = erp_response.data
            standard_format = convert_flat_erp_to_standard(flat_erp_data)
            enhanced_output = await self._enhance_erp_output(
                standard_format, customer_email, order_id
            )
            
            # Step 3: Perform final validation
            validation_result = self._validate_erp_output(enhanced_output)
            
            if not validation_result.success:
                return validation_result
            
            self.logger.info(
                "Successfully generated structured ERP JSON",
                order_id=enhanced_output.get("order_id"),
                line_items_count=len(enhanced_output.get("line_items", []))
            )
            
            return StructuredOutputResponse(
                success=True,
                data=enhanced_output,
                metadata={
                    "processing_method": "flat_responses_api",
                    "validation_passed": True,
                    "line_items_count": len(enhanced_output.get("line_items", [])),
                    "model": "gpt-4.1",
                    "api": "responses_api"
                }
            )
            
        except Exception as e:
            self.logger.error(
                "Exception in ERP processing",
                error=str(e),
                customer=customer_name
            )
            return StructuredOutputResponse(
                success=False,
                data={},
                error=f"ERP processing failed: {str(e)}"
            )
    
    async def _enhance_erp_output(
        self,
        erp_output: Dict[str, Any],
        customer_email: str,
        order_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Enhance ERP output with additional business logic"""
        
        # Generate order ID if not provided
        if order_id:
            erp_output["order_id"] = order_id
        elif not erp_output.get("order_id"):
            erp_output["order_id"] = self._generate_order_id(
                erp_output.get("customer_info", {}).get("company_name", "Unknown")
            )
        
        # Enhance line items with business rules
        line_items = erp_output.get("line_items", [])
        for i, line_item in enumerate(line_items):
            # Apply urgency rules based on email content
            if any(keyword in customer_email.lower() for keyword in 
                   ["urgent", "emergency", "asap", "critical", "rush"]):
                erp_output["priority"] = "HIGH"
        
        return erp_output
    
    def _validate_erp_output(self, erp_output: Dict[str, Any]) -> StructuredOutputResponse:
        """Comprehensive validation of ERP output"""
        
        errors = []
        
        # Validate customer information
        customer_info = erp_output.get("customer_info", {})
        if not customer_info.get("company_name", "").strip():
            errors.append("Customer name cannot be empty")
        
        # Validate line items
        line_items = erp_output.get("line_items", [])
        if not line_items:
            errors.append("Order must have at least one line item")
        
        for i, line_item in enumerate(line_items):
            # Critical: Ensure 'material' field is present and valid
            if not line_item.get("material", "").strip():
                errors.append(f"Line item {i+1}: Material field is required and cannot be empty")
            
            if line_item.get("quantity", 0) <= 0:
                errors.append(f"Line item {i+1}: Quantity must be greater than zero")
        
        # Validate order metadata
        if not erp_output.get("order_id"):
            errors.append("Order ID is required")
        
        if errors:
            return StructuredOutputResponse(
                success=False,
                data={},
                error=f"Validation failed: {'; '.join(errors)}"
            )
        
        return StructuredOutputResponse(success=True, data=erp_output)
    
    def _generate_order_id(self, customer_name: str) -> str:
        """Generate unique order ID"""
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        customer_prefix = ''.join(c.upper() for c in customer_name if c.isalpha())[:4]
        return f"ORD-{customer_prefix}-{timestamp}"
    
    async def extract_customer_analysis(
        self,
        customer_email: str,
        customer_name: str
    ) -> StructuredOutputResponse:
        """Extract structured customer analysis for ERP processing"""
        
        return await self.sales_client.extract_sales_order_analysis(
            customer_email=customer_email,
            customer_name=customer_name
        )
    
    async def detect_emergency_requirements(
        self,
        customer_email: str,
        customer_name: str
    ) -> StructuredOutputResponse:
        """Detect emergency situations for priority processing"""
        
        return await self.sales_client.detect_emergency_situation(
            customer_email=customer_email,
            customer_name=customer_name
        )
    
    def convert_to_legacy_format(self, erp_output: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert structured output to legacy format for backward compatibility
        
        This allows gradual migration from the old system.
        """
        
        customer_info = erp_output.get("customer_info", {})
        line_items = erp_output.get("line_items", [])
        
        return {
            "customer_validation": {
                "valid": True,
                "customer_name": customer_info.get("company_name", "Unknown"),
                "customer_id": customer_info.get("customer_id"),
                "tier": "standard",  # Default for flat model
                "industry": "unknown"  # Default for flat model
            },
            "inventory_check": {
                "status": "completed",
                "parts": {
                    f"L{i+1:03d}": {
                        "material": item.get("material", "Unknown"),  # CONSISTENT FIELD NAME
                        "quantity": item.get("quantity", 1),
                        "availability": "unknown",
                        "part_number": item.get("part_number")
                    }
                    for i, item in enumerate(line_items)
                },
                "available_count": 0,  # Not tracked in flat model
                "total_parts_checked": len(line_items)
            },
            "order_totals": {
                "line_count": len(line_items),
                "total_quantity": sum(item.get("quantity", 1) for item in line_items),
                "priority": erp_output.get("priority", "MEDIUM"),
                "complexity": "MEDIUM"  # Default for flat model
            },
            "business_rules": {
                "emergency_processing": erp_output.get("priority") == "HIGH",
                "special_handling": bool(erp_output.get("special_instructions")),
                "certifications_required": False  # Not tracked in flat model
            },
            "erp_json": erp_output  # Full structured output
        }


# =============================================================================
# FACTORY AND UTILITY FUNCTIONS
# =============================================================================

def create_structured_erp_agent() -> StructuredERPAgent:
    """Factory function for creating structured ERP agent"""
    return StructuredERPAgent()

async def process_sales_order_structured(
    customer_email: str,
    customer_name: str,
    order_id: Optional[str] = None
) -> StructuredOutputResponse:
    """
    Convenience function for processing sales orders with structured outputs
    
    This is a drop-in replacement for the old manual JSON generation.
    """
    agent = create_structured_erp_agent()
    return await agent.process_sales_order_to_erp(
        customer_email=customer_email,
        customer_name=customer_name,
        order_id=order_id
    )

def validate_erp_json_structure(json_data: Dict[str, Any]) -> bool:
    """
    Validate JSON structure against ERP requirements
    
    This can be used to check if existing JSON meets the new standards.
    """
    try:
        FlatERPOrder(**json_data)
        return True
    except Exception:
        return False


# =============================================================================
# MIGRATION HELPER FOR EXISTING AGENTS
# =============================================================================

class ERPAgentMigrationHelper:
    """Helper class for migrating existing ERP agents to structured outputs"""
    
    @staticmethod
    def migrate_legacy_response(legacy_response: Dict[str, Any]) -> StructuredOutputResponse:
        """
        Migrate legacy ERP response to structured format
        
        This helps transition from the old manual dictionary approach.
        """
        try:
            # Extract components from legacy response
            customer_validation = legacy_response.get("customer_validation", {})
            inventory_check = legacy_response.get("inventory_check", {})
            
            # Build structured customer info
            customer_info = ERPCustomerInfo(
                name=customer_validation.get("customer_name", "Unknown"),
                customer_id=customer_validation.get("customer_id"),
                tier=customer_validation.get("tier"),
                industry=customer_validation.get("industry")
            )
            
            # Build structured line items
            line_items = []
            parts_data = inventory_check.get("parts", {})
            for line_id, part_data in parts_data.items():
                line_item = ERPLineItem(
                    line_id=line_id,
                    material=part_data.get("material", "Unknown"),
                    quantity=part_data.get("quantity", 1),
                    specifications=ERPMaterialSpecification(
                        material_grade=part_data.get("material", "Unknown"),
                        form="unknown"
                    ),
                    part_number=part_data.get("part_number"),
                    availability=part_data.get("availability", "unknown")
                )
                line_items.append(line_item)
            
            # Build structured order metadata
            order_metadata = ERPOrderMetadata(
                order_id=f"MIGRATED-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                priority=legacy_response.get("order_totals", {}).get("priority", "standard"),
                complexity_level=legacy_response.get("order_totals", {}).get("complexity", "simple")
            )
            
            # Create structured output
            erp_output = ERPOrderOutput(
                customer=customer_info,
                line_items=line_items,
                order_metadata=order_metadata
            )
            
            return StructuredOutputResponse(
                success=True,
                data=erp_output,
                metadata={"migrated_from_legacy": True}
            )
            
        except Exception as e:
            return StructuredOutputResponse(
                success=False,
                data={},
                error=f"Migration failed: {str(e)}",
                metadata={"migrated_from_legacy": True, "migration_error": True}
            )