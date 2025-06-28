"""
Enhanced Order Extractor - Responses API Only

This agent extracts individual line items with detailed specifications using
OpenAI Responses API with gpt-4.1 and structured outputs exclusively.
"""

import re
import json
import asyncio
from typing import List, Dict, Any, Optional
import structlog
from datetime import datetime
from pydantic import BaseModel, Field

from app.core.responses_client import ResponsesAPIClient
from app.models.flat_responses_models import FlatOrderData, FlatOrderMetadata

logger = structlog.get_logger()


# Using FlatOrderMetadata from flat_responses_models for Responses API compatibility


# Using FlatOrderData from flat_responses_models for Responses API compatibility


class DeliveryInstructionsOutput(BaseModel):
    """Structured output for delivery instructions"""
    delivery_address: Optional[str] = Field(description="Delivery address")
    special_instructions: Optional[str] = Field(description="Special delivery instructions")
    delivery_date: Optional[str] = Field(description="Requested delivery date")
    delivery_method: Optional[str] = Field(description="Preferred delivery method")
    contact_for_delivery: Optional[str] = Field(description="Contact person for delivery")


class EnhancedOrderExtractor:
    """Enhanced order extractor using Responses API with gpt-4.1 exclusively"""
    
    def __init__(self):
        self.model = "gpt-4.1"  # Fixed model
        self.responses_client = ResponsesAPIClient(temperature=0.1, max_tokens=3000)
        logger.info("Initialized EnhancedOrderExtractor with Responses API", model=self.model)
        
    async def extract_order_with_line_items(self, document_content: str, 
                                          session_id: str) -> Dict[str, Any]:
        """Extract order with individual line items from document"""
        
        logger.info("Starting enhanced order extraction", 
                   session_id=session_id,
                   content_length=len(document_content))
        
        try:
            # Step 1: Extract order metadata using Responses API
            order_metadata = await self._extract_order_metadata(document_content)
            
            # Step 2: Extract individual line items with raw text using Responses API
            line_items = await self._extract_line_items(document_content)
            
            # Step 3: Extract delivery instructions using Responses API
            delivery_instructions = await self._extract_delivery_instructions(document_content)
            
            # Step 4: Create enhanced order object
            enhanced_order = {
                "order_id": f"ORD-{session_id[:8]}",
                "session_id": session_id,
                "order_metadata": order_metadata,
                "line_items": line_items,
                "delivery_instructions": delivery_instructions,
                "total_line_items": len(line_items),
                "overall_status": "extracted"
            }
            
            logger.info("Enhanced order extraction completed",
                       session_id=session_id,
                       line_items_count=len(line_items),
                       customer=order_metadata.get("customer", "Unknown"))
            
            return enhanced_order
            
        except Exception as e:
            logger.error("Enhanced order extraction failed",
                        session_id=session_id,
                        error=str(e))
            raise
    
    async def _extract_order_metadata(self, document_content: str) -> Dict[str, Any]:
        """Extract order-level metadata using Responses API"""
        
        system_message = """
        You are an expert at extracting order metadata from business documents.
        Focus on customer information, contact details, purchase order numbers,
        priority levels, and payment terms.
        """
        
        prompt = f"""
        Extract order metadata from this document:
        
        {document_content[:2000]}...
        
        Extract the following information:
        1. Customer/company name
        2. Contact person details (name, email, phone)
        3. PO number or reference number
        4. Priority level (HIGH/MEDIUM/LOW)
        5. Overall delivery date
        6. Project names mentioned
        7. Payment terms
        8. Credit approval information
        
        Return structured metadata for order processing.
        """
        
        try:
            result = await self.responses_client.get_flat_structured_response(
                input_messages=prompt,
                flat_model_name="FlatOrderMetadata",
                system_message=system_message,
                store=True
            )
            
            if result.success:
                data = result.data
                return {
                    "customer": data.customer_name,
                    "contact_name": data.contact_person,
                    "contact_email": data.contact_email,
                    "contact_phone": data.contact_phone,
                    "po_number": data.po_number,
                    "priority": data.priority_level,
                    "delivery_date": data.delivery_date,
                    "project_name": data.project_name,
                    "payment_terms": data.payment_terms,
                    "credit_approved": data.credit_approved == "YES",
                    "extracted_at": datetime.now().isoformat()
                }
            else:
                logger.warning("Metadata extraction failed", error=result.error)
                return self._get_default_metadata()
                
        except Exception as e:
            logger.error("Metadata extraction error", error=str(e))
            return self._get_default_metadata()
    
    def _get_default_metadata(self) -> Dict[str, Any]:
        """Return default metadata when extraction fails"""
        return {
            "customer": "Unknown Customer",
            "priority": "MEDIUM",
            "extracted_at": datetime.now().isoformat()
        }
    
    async def _extract_line_items(self, document_content: str) -> List[Dict[str, Any]]:
        """Extract individual line items using Responses API"""
        
        system_message = """
        You are an expert at extracting individual line items from order documents.
        Focus on identifying each distinct product or material requested, with
        quantities, specifications, and technical details.
        
        Pay special attention to:
        - Material types (steel, aluminum, stainless, etc.)
        - Dimensions and specifications
        - Quantities and units
        - Urgency indicators
        - Lead time requirements
        """
        
        prompt = f"""
        Extract individual line items from this document:
        
        {document_content}
        
        For each line item, extract:
        1. Line number (sequential)
        2. Raw description as written
        3. Quantity and unit
        4. Material type
        5. Technical specifications (dimensions, grades, etc.)
        6. Any urgency indicators or special requirements
        7. Estimated lead time if mentioned
        
        Return a structured list of all line items found.
        """
        
        try:
            # Since we need a list of line items, we'll extract them as a group
            # and then process into individual LineItem objects
            result = await self.responses_client.simple_text_response(
                input_messages=prompt,
                system_message=system_message,
                store=True
            )
            
            # Parse the response and convert to LineItem objects
            line_items = await self._parse_line_items_response(result)
            
            logger.info("Extracted line items", count=len(line_items))
            return line_items
            
        except Exception as e:
            logger.error("Line items extraction error", error=str(e))
            return []
    
    async def _parse_line_items_response(self, response_text: str) -> List[Dict[str, Any]]:
        """Parse line items response and convert to LineItem objects"""
        
        line_items = []
        
        # Simple parsing - look for numbered items or bullet points
        lines = response_text.split('\n')
        current_line_number = 1
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Look for patterns that indicate line items
            if (re.match(r'^\d+\.?\s+', line) or 
                re.match(r'^[-*]\s+', line) or
                any(keyword in line.lower() for keyword in ['qty', 'quantity', 'steel', 'aluminum', 'material'])):
                
                # Extract basic information from the line
                description = re.sub(r'^\d+\.?\s*', '', line)
                description = re.sub(r'^[-*]\s*', '', description)
                
                # Simple quantity extraction
                quantity = 1
                qty_match = re.search(r'qty:?\s*(\d+)|quantity:?\s*(\d+)|(\d+)\s*(?:pcs?|pieces?|ea)', line.lower())
                if qty_match:
                    quantity = int(qty_match.group(1) or qty_match.group(2) or qty_match.group(3))
                
                # Create line item dictionary
                line_item = {
                    "line_id": f"line_{current_line_number}",
                    "line_number": current_line_number,
                    "description": description,
                    "quantity": quantity,
                    "raw_text": line,
                    "status": "EXTRACTED"
                }
                
                line_items.append(line_item)
                current_line_number += 1
        
        return line_items
    
    async def _extract_delivery_instructions(self, document_content: str) -> Dict[str, Any]:
        """Extract delivery instructions using Responses API"""
        
        system_message = """
        You are an expert at extracting delivery and shipping instructions
        from business documents. Focus on addresses, special requirements,
        delivery dates, and contact information.
        """
        
        prompt = f"""
        Extract delivery instructions from this document:
        
        {document_content[:2000]}...
        
        Extract:
        1. Delivery address
        2. Special delivery instructions
        3. Requested delivery date
        4. Preferred delivery method
        5. Contact person for delivery
        
        Return structured delivery information.
        """
        
        try:
            result = await self.responses_client.get_structured_response(
                input_messages=prompt,
                output_model=DeliveryInstructionsOutput,
                system_message=system_message,
                store=True
            )
            
            if result.success:
                data = result.data
                return {
                    "delivery_address": data.delivery_address,
                    "special_instructions": data.special_instructions,
                    "delivery_date": data.delivery_date,
                    "delivery_method": data.delivery_method,
                    "contact_for_delivery": data.contact_for_delivery
                }
            else:
                logger.warning("Delivery instructions extraction failed", error=result.error)
                return {}
                
        except Exception as e:
            logger.error("Delivery instructions extraction error", error=str(e))
            return {}

    async def extract_order_data(self, document_content: str) -> Dict[str, Any]:
        """Alias for extract_order_with_line_items for compatibility"""
        session_id = f"test_{int(datetime.now().timestamp())}"
        return await self.extract_order_with_line_items(document_content, session_id)


# Factory function for easy instantiation
def create_enhanced_order_extractor() -> EnhancedOrderExtractor:
    """Factory function for creating EnhancedOrderExtractor with Responses API"""
    return EnhancedOrderExtractor()