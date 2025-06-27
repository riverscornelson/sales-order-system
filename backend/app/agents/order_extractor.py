import re
from typing import Dict, Any, List, Optional
import asyncio
import structlog
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import PromptTemplate

logger = structlog.get_logger()

class OrderExtractionAgent:
    """Agent responsible for extracting order information from document text"""
    
    def __init__(self):
        self.llm = ChatOpenAI(
            model="gpt-4",
            temperature=0.1,
            max_tokens=2000
        )
        
        self.extraction_prompt = PromptTemplate(
            input_variables=["text"],
            template="""
            You are an expert at extracting sales order information from business documents.
            
            Extract the following information from the provided text:
            
            1. CUSTOMER INFORMATION:
               - Company name
               - Contact person name
               - Email address
               - Phone number
               - Billing/shipping address
               - Customer ID (if mentioned)
            
            2. ORDER LINE ITEMS:
               For each item, extract:
               - Part number/SKU (if available)
               - Description (detailed description of the item)
               - Quantity ordered
               - Unit price (if mentioned)
               - Line total (if calculated)
               - Any specifications (dimensions, material, grade, etc.)
            
            3. ORDER DETAILS:
               - Order date
               - Requested delivery date
               - Special instructions or notes
               - Payment terms
               - Shipping method
            
            Text to analyze:
            {text}
            
            Return the extracted information as JSON with the following structure:
            {{
                "customer_info": {{
                    "name": "string",
                    "company": "string", 
                    "email": "string",
                    "phone": "string",
                    "address": "string",
                    "customer_id": "string"
                }},
                "line_items": [
                    {{
                        "part_number": "string",
                        "description": "string",
                        "quantity": number,
                        "unit_price": number,
                        "line_total": number,
                        "specifications": {{}}
                    }}
                ],
                "order_details": {{
                    "order_date": "string",
                    "delivery_date": "string",
                    "special_instructions": "string",
                    "payment_terms": "string",
                    "shipping_method": "string"
                }},
                "confidence": {{
                    "customer_info": number,
                    "line_items": number,
                    "overall": number
                }}
            }}
            
            Important notes:
            - If information is not found, use null for that field
            - For quantities, convert text numbers to actual numbers (e.g., "five" -> 5)
            - Include confidence scores (0.0 to 1.0) for how certain you are about the extraction
            - Pay special attention to metal parts specifications (dimensions, grades, materials)
            - Look for common metal industry terms and part descriptions
            """
        )
    
    async def extract_order_data(self, text: str) -> Dict[str, Any]:
        """Extract order data from document text using LLM"""
        
        logger.info("Starting order extraction", text_length=len(text))
        
        try:
            # First, try rule-based extraction for common patterns
            structured_data = await self._rule_based_extraction(text)
            
            # Then enhance with LLM extraction
            llm_data = await self._llm_extraction(text)
            
            # Merge and validate results
            final_data = self._merge_extraction_results(structured_data, llm_data)
            
            # Post-process and validate
            final_data = self._validate_and_clean(final_data)
            
            logger.info("Order extraction completed", 
                       customer_found=bool(final_data.get("customer_info", {}).get("name")),
                       line_items_count=len(final_data.get("line_items", [])))
            
            return final_data
            
        except Exception as e:
            logger.error("Order extraction failed", error=str(e))
            raise Exception(f"Failed to extract order data: {str(e)}")
    
    async def _rule_based_extraction(self, text: str) -> Dict[str, Any]:
        """Extract data using predefined patterns and rules"""
        
        result = {
            "customer_info": {},
            "line_items": [],
            "order_details": {},
            "confidence": {"rule_based": True}
        }
        
        # Extract email addresses
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, text)
        if emails:
            result["customer_info"]["email"] = emails[0]
        
        # Extract phone numbers
        phone_pattern = r'(\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4})'
        phones = re.findall(phone_pattern, text)
        if phones:
            result["customer_info"]["phone"] = phones[0]
        
        # Extract dates (various formats)
        date_patterns = [
            r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b',
            r'\b\d{4}[/-]\d{1,2}[/-]\d{1,2}\b',
            r'\b(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2},?\s+\d{4}\b'
        ]
        
        for pattern in date_patterns:
            dates = re.findall(pattern, text, re.IGNORECASE)
            if dates:
                result["order_details"]["order_date"] = dates[0]
                break
        
        # Extract quantities and part numbers
        qty_patterns = [
            r'qty[:\s]*(\d+)',
            r'quantity[:\s]*(\d+)',
            r'(\d+)\s*(?:pcs?|pieces?|ea(?:ch)?)',
        ]
        
        part_number_patterns = [
            r'part\s*#?[:\s]*([A-Z0-9-]+)',
            r'sku[:\s]*([A-Z0-9-]+)',
            r'item[:\s]*([A-Z0-9-]+)',
        ]
        
        # Look for tabular data (simple detection)
        lines = text.split('\n')
        table_data = self._extract_table_data(lines)
        if table_data:
            result["line_items"].extend(table_data)
        
        return result
    
    async def _llm_extraction(self, text: str) -> Dict[str, Any]:
        """Extract data using LLM"""
        
        try:
            # Prepare the prompt
            formatted_prompt = self.extraction_prompt.format(text=text[:4000])  # Limit text length
            
            # Create messages
            messages = [
                SystemMessage(content="You are an expert at extracting structured data from business documents."),
                HumanMessage(content=formatted_prompt)
            ]
            
            # Get LLM response
            response = await self.llm.ainvoke(messages)
            
            # Parse JSON response
            parser = JsonOutputParser()
            parsed_data = parser.parse(response.content)
            
            return parsed_data
            
        except Exception as e:
            logger.warning("LLM extraction failed, using fallback", error=str(e))
            return {
                "customer_info": {},
                "line_items": [],
                "order_details": {},
                "confidence": {"llm_failed": True}
            }
    
    def _extract_table_data(self, lines: List[str]) -> List[Dict[str, Any]]:
        """Extract line items from table-like data"""
        
        line_items = []
        
        # Look for lines that might contain item data
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Check if line contains item-like data
            # Pattern: might have quantities, part numbers, descriptions
            if re.search(r'\d+', line) and len(line.split()) > 2:
                # Try to parse as potential line item
                parts = line.split()
                
                # Look for quantity (number at start or end)
                quantity = None
                for part in parts:
                    if part.isdigit():
                        quantity = int(part)
                        break
                
                # Look for part number (alphanumeric with dashes)
                part_number = None
                for part in parts:
                    if re.match(r'^[A-Z0-9-]{3,}$', part, re.IGNORECASE):
                        part_number = part
                        break
                
                # Look for price (decimal number with $ or currency)
                unit_price = None
                for part in parts:
                    price_match = re.search(r'\$?(\d+\.?\d*)', part)
                    if price_match:
                        try:
                            unit_price = float(price_match.group(1))
                        except ValueError:
                            pass
                
                # If we found some key data, create line item
                if quantity or part_number:
                    line_items.append({
                        "part_number": part_number,
                        "description": line,  # Use full line as description for now
                        "quantity": quantity,
                        "unit_price": unit_price,
                        "raw_line": line
                    })
        
        return line_items
    
    def _merge_extraction_results(self, rule_data: Dict[str, Any], llm_data: Dict[str, Any]) -> Dict[str, Any]:
        """Merge results from rule-based and LLM extraction"""
        
        merged = {
            "customer_info": {},
            "line_items": [],
            "order_details": {},
            "confidence": {}
        }
        
        # Merge customer info (prefer LLM if available, fallback to rules)
        for key in ["name", "company", "email", "phone", "address", "customer_id"]:
            llm_value = llm_data.get("customer_info", {}).get(key)
            rule_value = rule_data.get("customer_info", {}).get(key)
            
            if llm_value:
                merged["customer_info"][key] = llm_value
            elif rule_value:
                merged["customer_info"][key] = rule_value
        
        # Merge line items (prefer LLM, supplement with rules)
        llm_items = llm_data.get("line_items", [])
        rule_items = rule_data.get("line_items", [])
        
        if llm_items:
            merged["line_items"] = llm_items
        else:
            merged["line_items"] = rule_items
        
        # Merge order details
        for key in ["order_date", "delivery_date", "special_instructions", "payment_terms"]:
            llm_value = llm_data.get("order_details", {}).get(key)
            rule_value = rule_data.get("order_details", {}).get(key)
            
            if llm_value:
                merged["order_details"][key] = llm_value
            elif rule_value:
                merged["order_details"][key] = rule_value
        
        # Merge confidence scores
        merged["confidence"] = {
            "customer_info": llm_data.get("confidence", {}).get("customer_info", 0.5),
            "line_items": llm_data.get("confidence", {}).get("line_items", 0.5),
            "overall": llm_data.get("confidence", {}).get("overall", 0.5),
            "extraction_method": "hybrid"
        }
        
        return merged
    
    def _validate_and_clean(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and clean extracted data"""
        
        # Clean customer info
        customer_info = data.get("customer_info", {})
        
        # Validate email format
        if customer_info.get("email"):
            email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
            if not re.match(email_pattern, customer_info["email"]):
                customer_info["email"] = None
        
        # Clean phone number
        if customer_info.get("phone"):
            phone = re.sub(r'[^\d]', '', customer_info["phone"])
            if len(phone) >= 10:
                customer_info["phone"] = phone
            else:
                customer_info["phone"] = None
        
        # Validate line items
        line_items = data.get("line_items", [])
        cleaned_items = []
        
        for item in line_items:
            if isinstance(item, dict):
                # Ensure required fields
                if not item.get("description"):
                    continue
                
                # Clean quantity
                if item.get("quantity"):
                    try:
                        item["quantity"] = int(float(item["quantity"]))
                    except (ValueError, TypeError):
                        item["quantity"] = 1  # Default to 1
                
                # Clean prices
                for price_field in ["unit_price", "line_total"]:
                    if item.get(price_field):
                        try:
                            # Remove currency symbols and convert to float
                            price_str = str(item[price_field]).replace('$', '').replace(',', '')
                            item[price_field] = float(price_str)
                        except (ValueError, TypeError):
                            item[price_field] = None
                
                cleaned_items.append(item)
        
        data["line_items"] = cleaned_items
        
        # Update confidence based on data quality
        confidence = data.get("confidence", {})
        
        # Customer confidence
        customer_fields = sum(1 for v in customer_info.values() if v)
        confidence["customer_info"] = min(customer_fields / 4.0, 1.0)  # 4 key fields
        
        # Line items confidence
        if cleaned_items:
            item_completeness = sum(
                1 for item in cleaned_items 
                if item.get("description") and item.get("quantity")
            ) / len(cleaned_items)
            confidence["line_items"] = item_completeness
        else:
            confidence["line_items"] = 0.0
        
        # Overall confidence
        confidence["overall"] = (confidence["customer_info"] + confidence["line_items"]) / 2
        
        data["confidence"] = confidence
        
        return data