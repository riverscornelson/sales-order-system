import re
import json
import asyncio
from typing import List, Dict, Any, Optional
import structlog
from langchain_openai import ChatOpenAI
from datetime import datetime

from ..models.line_item_schemas import (
    EnhancedOrder, OrderMetadata, LineItem, ExtractedSpecs, 
    DeliveryInstructions, LineItemStatus
)

logger = structlog.get_logger()

class EnhancedOrderExtractor:
    """Enhanced order extractor that extracts individual line items with detailed specifications"""
    
    def __init__(self, llm: ChatOpenAI):
        self.llm = llm
        
    async def extract_order_with_line_items(self, document_content: str, 
                                          session_id: str) -> EnhancedOrder:
        """Extract order with individual line items from document"""
        
        logger.info("Starting enhanced order extraction", 
                   session_id=session_id,
                   content_length=len(document_content))
        
        try:
            # Step 1: Extract order metadata
            order_metadata = await self._extract_order_metadata(document_content)
            
            # Step 2: Extract individual line items with raw text
            line_items = await self._extract_line_items(document_content)
            
            # Step 3: Extract delivery instructions
            delivery_instructions = await self._extract_delivery_instructions(document_content)
            
            # Step 4: Create enhanced order object
            enhanced_order = EnhancedOrder(
                order_id=f"ORD-{session_id[:8]}",
                session_id=session_id,
                order_metadata=order_metadata,
                line_items=line_items,
                delivery_instructions=delivery_instructions,
                total_line_items=len(line_items),
                overall_status="extracted"
            )
            
            logger.info("Enhanced order extraction completed",
                       session_id=session_id,
                       line_items_count=len(line_items),
                       customer=order_metadata.customer)
            
            return enhanced_order
            
        except Exception as e:
            logger.error("Enhanced order extraction failed",
                        session_id=session_id,
                        error=str(e))
            raise
    
    async def _extract_order_metadata(self, document_content: str) -> OrderMetadata:
        """Extract order-level metadata using AI"""
        
        metadata_prompt = f"""
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
        
        Return as JSON:
        {{
            "customer": "string",
            "contact_person": "string",
            "contact_email": "string", 
            "contact_phone": "string",
            "po_number": "string",
            "priority": "HIGH/MEDIUM/LOW",
            "delivery_date": "string",
            "projects": ["project1", "project2"],
            "payment_terms": "string",
            "credit_approval": "string"
        }}
        """
        
        try:
            response = await asyncio.to_thread(self.llm.invoke, metadata_prompt)
            metadata_data = json.loads(response.content)
            return OrderMetadata(**metadata_data)
        except Exception as e:
            logger.warning("AI metadata extraction failed, using fallback", error=str(e))
            return OrderMetadata(
                customer="Unknown Customer",
                priority="MEDIUM"
            )
    
    async def _extract_line_items(self, document_content: str) -> List[LineItem]:
        """Extract individual line items with raw text and specifications"""
        
        line_items_prompt = f"""
        Carefully analyze this document and extract EVERY individual material/part line item mentioned.
        
        Document:
        {document_content}
        
        For each line item, extract:
        1. The EXACT raw text as it appears in the document
        2. Structured specifications (material, dimensions, quantity, etc.)
        3. Any special requirements or certifications
        4. Project association if mentioned
        5. Urgency indicators
        
        Be very thorough - capture ALL materials mentioned, even if they're in different sections or projects.
        
        Return as JSON array:
        [
            {{
                "line_id": "L001",
                "project": "PROJECT PHOENIX",
                "raw_text": "Titanium Grade 5 (6Al-4V) sheets - Thickness: 0.125\" (±0.005\") - Dimensions: 24\" x 36\" - Quantity: 12 pieces - Surface finish: Mill finish acceptable - Material cert required (DFARS compliant)",
                "extracted_specs": {{
                    "material_grade": "Titanium Grade 5 (6Al-4V)",
                    "form": "sheets",
                    "dimensions": {{
                        "length": "24",
                        "width": "36", 
                        "thickness": "0.125"
                    }},
                    "quantity": 12,
                    "units": "inches",
                    "tolerances": {{
                        "thickness": "±0.005"
                    }},
                    "surface_finish": "Mill finish",
                    "certifications": ["DFARS compliant", "Material cert required"]
                }},
                "urgency": "HIGH",
                "special_requirements": ["DFARS compliant", "Material cert required"]
            }}
        ]
        
        Extract ALL line items found in the document. If there are multiple projects, make sure to capture items from each project.
        """
        
        try:
            response = await asyncio.to_thread(self.llm.invoke, line_items_prompt)
            line_items_data = json.loads(response.content)
            
            line_items = []
            for i, item_data in enumerate(line_items_data):
                # Ensure line_id is present
                if "line_id" not in item_data:
                    item_data["line_id"] = f"L{i+1:03d}"
                
                # Create ExtractedSpecs object
                specs_data = item_data.get("extracted_specs", {})
                extracted_specs = ExtractedSpecs(**specs_data) if specs_data else None
                
                # Create LineItem object
                line_item = LineItem(
                    line_id=item_data["line_id"],
                    project=item_data.get("project"),
                    raw_text=item_data["raw_text"],
                    extracted_specs=extracted_specs,
                    urgency=item_data.get("urgency"),
                    special_requirements=item_data.get("special_requirements", []),
                    status=LineItemStatus.PENDING
                )
                
                line_items.append(line_item)
            
            logger.info("AI line item extraction successful", 
                       line_items_count=len(line_items))
            return line_items
            
        except Exception as e:
            logger.error("AI line item extraction failed", error=str(e))
            # Fallback: basic text parsing
            return self._fallback_line_item_extraction(document_content)
    
    def _fallback_line_item_extraction(self, document_content: str) -> List[LineItem]:
        """Fallback line item extraction using basic text parsing"""
        
        logger.warning("Using fallback line item extraction")
        
        # Look for numbered lists, bullet points, or material mentions
        lines = document_content.split('\n')
        line_items = []
        line_counter = 1
        
        # Common material keywords
        material_keywords = [
            'titanium', 'aluminum', 'steel', 'stainless', 'carbon', 'alloy',
            'brass', 'copper', 'bronze', 'inconel', 'hastelloy'
        ]
        
        # Common form keywords
        form_keywords = [
            'sheet', 'plate', 'bar', 'rod', 'tube', 'pipe', 'angle', 'beam',
            'channel', 'wire', 'foil'
        ]
        
        for line in lines:
            line_lower = line.lower().strip()
            
            # Skip empty lines or headers
            if not line_lower or len(line_lower) < 10:
                continue
            
            # Check if line contains material and form keywords
            has_material = any(keyword in line_lower for keyword in material_keywords)
            has_form = any(keyword in line_lower for keyword in form_keywords)
            
            # Look for quantity indicators
            has_quantity = bool(re.search(r'\d+\s*(piece|pcs|ea|each|qty|quantity)', line_lower))
            
            # Look for dimension patterns
            has_dimensions = bool(re.search(r'\d+[\.\d]*\s*[x×]\s*\d+[\.\d]*', line_lower))
            
            # If it looks like a material specification
            if (has_material and has_form) or (has_material and has_quantity) or (has_material and has_dimensions):
                line_item = LineItem(
                    line_id=f"L{line_counter:03d}",
                    raw_text=line.strip(),
                    extracted_specs=ExtractedSpecs(),
                    status=LineItemStatus.PENDING
                )
                line_items.append(line_item)
                line_counter += 1
        
        logger.info("Fallback line item extraction completed", 
                   line_items_count=len(line_items))
        return line_items
    
    async def _extract_delivery_instructions(self, document_content: str) -> Optional[DeliveryInstructions]:
        """Extract delivery and shipping instructions"""
        
        delivery_prompt = f"""
        Extract delivery and shipping information from this document:
        
        {document_content[-1000:]}
        
        Look for:
        1. Default shipping address
        2. Special shipping instructions for different projects
        3. Delivery requirements or notes
        4. Shipping preferences
        
        Return as JSON:
        {{
            "default_address": "string",
            "special_shipping": {{
                "project_name": "address"
            }},
            "shipping_notes": ["note1", "note2"],
            "delivery_requirements": ["req1", "req2"]
        }}
        """
        
        try:
            response = await asyncio.to_thread(self.llm.invoke, delivery_prompt)
            delivery_data = json.loads(response.content)
            return DeliveryInstructions(**delivery_data)
        except Exception as e:
            logger.warning("Delivery instruction extraction failed", error=str(e))
            return None
    
    async def enhance_line_item_specs(self, line_item: LineItem) -> LineItem:
        """Use AI to enhance extracted specifications for a single line item"""
        
        enhancement_prompt = f"""
        Analyze this line item and enhance the extracted specifications:
        
        Raw Text: {line_item.raw_text}
        Current Specs: {line_item.extracted_specs.dict() if line_item.extracted_specs else {}}
        
        Provide enhanced specifications with better parsing of:
        1. Material grades and equivalents
        2. Dimensional information and tolerances
        3. Form factors and shapes
        4. Quantities and units
        5. Special requirements
        6. Alternative acceptable specifications
        
        Return enhanced specs as JSON:
        {{
            "material_grade": "string",
            "form": "string",
            "dimensions": {{
                "length": "value",
                "width": "value",
                "thickness": "value",
                "diameter": "value"
            }},
            "quantity": number,
            "units": "string",
            "tolerances": {{
                "field": "tolerance"
            }},
            "surface_finish": "string",
            "heat_treatment": "string",
            "certifications": ["cert1", "cert2"],
            "special_requirements": ["req1", "req2"],
            "grade_equivalents": ["alt1", "alt2"]
        }}
        """
        
        try:
            response = await asyncio.to_thread(self.llm.invoke, enhancement_prompt)
            enhanced_data = json.loads(response.content)
            
            # Update the line item with enhanced specs
            line_item.extracted_specs = ExtractedSpecs(**enhanced_data)
            
            logger.debug("Enhanced line item specifications", 
                        line_id=line_item.line_id)
            return line_item
            
        except Exception as e:
            logger.warning("Specification enhancement failed", 
                          line_id=line_item.line_id,
                          error=str(e))
            return line_item