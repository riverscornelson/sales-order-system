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

from app.core.structured_llm import SalesOrderStructuredOutputs, StructuredOutputResponse
from app.models.structured_outputs import (
    ERPOrderOutput, ERPCustomerInfo, ERPLineItem, ERPOrderMetadata,
    ERPMaterialSpecification, SalesOrderAnalysis
)

logger = structlog.get_logger()


class StructuredERPAgent:
    """
    ERP Integration Agent with structured outputs
    
    Replaces manual dictionary construction with validated Pydantic models,
    solving the JSON consistency issues from OpenAI evaluations.
    """
    
    def __init__(self):
        self.structured_llm = SalesOrderStructuredOutputs()
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
            # Step 1: Generate structured ERP JSON
            erp_response = await self.structured_llm.generate_erp_json(
                customer_email=customer_email,
                customer_name=customer_name
            )
            
            if not erp_response.success:
                self.logger.error(
                    "Failed to generate ERP JSON",
                    error=erp_response.error
                )
                return erp_response
            
            # Step 2: Validate and enhance the output
            erp_output = erp_response.data
            enhanced_output = await self._enhance_erp_output(
                erp_output, customer_email, order_id
            )
            
            # Step 3: Perform final validation
            validation_result = self._validate_erp_output(enhanced_output)
            
            if not validation_result.success:
                return validation_result
            
            self.logger.info(
                "Successfully generated structured ERP JSON",
                order_id=enhanced_output.order_metadata.order_id,
                line_items_count=len(enhanced_output.line_items)
            )
            
            return StructuredOutputResponse(
                success=True,
                data=enhanced_output,
                metadata={
                    "processing_method": "structured_output",
                    "validation_passed": True,
                    "line_items_count": len(enhanced_output.line_items),
                    "customer_tier": enhanced_output.customer.tier,
                    "order_priority": enhanced_output.order_metadata.priority
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
        erp_output: ERPOrderOutput,
        customer_email: str,
        order_id: Optional[str] = None
    ) -> ERPOrderOutput:
        """Enhance ERP output with additional business logic"""
        
        # Generate order ID if not provided
        if order_id:
            erp_output.order_metadata.order_id = order_id
        elif not erp_output.order_metadata.order_id:
            erp_output.order_metadata.order_id = self._generate_order_id(
                erp_output.customer.name
            )
        
        # Enhance line items with business rules
        for i, line_item in enumerate(erp_output.line_items):
            if not line_item.line_id:
                line_item.line_id = f"L{i+1:03d}"
            
            # Apply urgency rules based on email content
            if any(keyword in customer_email.lower() for keyword in 
                   ["urgent", "emergency", "asap", "critical", "rush"]):
                line_item.urgency = "emergency"
                erp_output.order_metadata.priority = "emergency"
        
        return erp_output
    
    def _validate_erp_output(self, erp_output: ERPOrderOutput) -> StructuredOutputResponse:
        """Comprehensive validation of ERP output"""
        
        errors = []
        
        # Validate customer information
        if not erp_output.customer.name.strip():
            errors.append("Customer name cannot be empty")
        
        # Validate line items
        if not erp_output.line_items:
            errors.append("Order must have at least one line item")
        
        for i, line_item in enumerate(erp_output.line_items):
            # Critical: Ensure 'material' field is present and valid
            if not line_item.material or not line_item.material.strip():
                errors.append(f"Line item {i+1}: Material field is required and cannot be empty")
            
            if line_item.quantity <= 0:
                errors.append(f"Line item {i+1}: Quantity must be greater than zero")
            
            if not line_item.specifications.material_grade:
                errors.append(f"Line item {i+1}: Material grade is required")
        
        # Validate order metadata
        if not erp_output.order_metadata.order_id:
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
        
        return await self.structured_llm.extract_sales_order_analysis(
            customer_email=customer_email,
            customer_name=customer_name
        )
    
    async def detect_emergency_requirements(
        self,
        customer_email: str,
        customer_name: str
    ) -> StructuredOutputResponse:
        """Detect emergency situations for priority processing"""
        
        return await self.structured_llm.detect_emergency_situation(
            customer_email=customer_email,
            customer_name=customer_name
        )
    
    def convert_to_legacy_format(self, erp_output: ERPOrderOutput) -> Dict[str, Any]:
        """
        Convert structured output to legacy format for backward compatibility
        
        This allows gradual migration from the old system.
        """
        
        return {
            "customer_validation": {
                "valid": True,
                "customer_name": erp_output.customer.name,
                "customer_id": erp_output.customer.customer_id,
                "tier": erp_output.customer.tier,
                "industry": erp_output.customer.industry
            },
            "inventory_check": {
                "status": "completed",
                "parts": {
                    item.line_id: {
                        "material": item.material,  # CONSISTENT FIELD NAME
                        "quantity": item.quantity,
                        "availability": item.availability,
                        "part_number": item.part_number
                    }
                    for item in erp_output.line_items
                },
                "available_count": len([
                    item for item in erp_output.line_items 
                    if item.availability == "in_stock"
                ]),
                "total_parts_checked": len(erp_output.line_items)
            },
            "order_totals": {
                "line_count": len(erp_output.line_items),
                "total_quantity": sum(item.quantity for item in erp_output.line_items),
                "priority": erp_output.order_metadata.priority,
                "complexity": erp_output.order_metadata.complexity_level
            },
            "business_rules": {
                "emergency_processing": erp_output.order_metadata.priority in ["emergency", "critical"],
                "special_handling": bool(erp_output.order_metadata.special_instructions),
                "certifications_required": any(
                    item.specifications.certifications 
                    for item in erp_output.line_items
                )
            },
            "erp_json": erp_output.model_dump()  # Full structured output
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
        ERPOrderOutput(**json_data)
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