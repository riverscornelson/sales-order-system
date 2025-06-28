"""
OpenAI Responses API Client with Structured Outputs
This module provides a unified client for the Responses API using gpt-4.1 
with structured outputs across the entire sales order system.
"""

import json
import asyncio
from typing import Type, TypeVar, Dict, Any, Optional, Union, List
from pydantic import BaseModel, ValidationError
from openai import OpenAI, AsyncOpenAI
import structlog

from app.models.structured_outputs import (
    ERPOrderOutput, SalesOrderAnalysis, SalesOrderReasoning,
    CustomerContextAnalysis, EmergencyDetection, ProductRequirement,
    StructuredOutputResponse, STRUCTURED_OUTPUT_MODELS
)
from app.models.responses_api_models import (
    SimpleERPOrder, SimpleOrderAnalysis, SimplePartMatch, SimpleOrderData,
    SimpleOrderMetadata, SimpleDeliveryInstructions, SimpleCustomerInfo,
    SIMPLE_STRUCTURED_OUTPUT_MODELS, get_simple_model,
    convert_simple_to_complex_erp, convert_simple_order_data_to_dict
)
from app.models.flat_responses_models import (
    FlatERPOrder, FlatOrderAnalysis, FlatPartMatch, FlatOrderData,
    FlatOrderMetadata, FLAT_STRUCTURED_OUTPUT_MODELS, get_flat_model,
    convert_flat_erp_to_standard, convert_flat_order_data_to_standard
)

logger = structlog.get_logger()

T = TypeVar('T', bound=BaseModel)

class ResponsesAPIClient:
    """
    Unified client for OpenAI Responses API with structured outputs
    
    Features:
    - Always uses gpt-4.1 model
    - Structured outputs using text.format with json_schema
    - Async and sync support
    - Comprehensive error handling
    - Conversation state management
    """
    
    def __init__(self, temperature: float = 0.1, max_tokens: Optional[int] = None):
        self.model = "gpt-4.1"  # Fixed model for consistency
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.sync_client = OpenAI()
        self.async_client = AsyncOpenAI()
        logger.info("Initialized ResponsesAPIClient", model=self.model, temperature=temperature)
    
    def _prepare_schema_for_responses_api(self, schema: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare Pydantic schema for Responses API requirements"""
        # Responses API has strict requirements:
        # 1. additionalProperties: false everywhere
        # 2. required array must include ALL properties (no optional fields)
        
        if isinstance(schema, dict):
            schema_copy = schema.copy()
            schema_copy["additionalProperties"] = False
            
            # Make all properties required for Responses API
            if "properties" in schema_copy:
                schema_copy["required"] = list(schema_copy["properties"].keys())
            
            # Recursively process nested objects
            def process_schema(obj):
                if isinstance(obj, dict):
                    # Add additionalProperties: false to all objects
                    if obj.get("type") == "object" or "properties" in obj:
                        obj["additionalProperties"] = False
                        # Make all properties required
                        if "properties" in obj:
                            obj["required"] = list(obj["properties"].keys())
                    
                    # Process all nested values
                    for key, value in obj.items():
                        if key != "required":  # Don't process the required array itself
                            process_schema(value)
                            
                elif isinstance(obj, list):
                    for item in obj:
                        process_schema(item)
            
            process_schema(schema_copy)
            return schema_copy
        return schema
    
    async def get_structured_response(
        self,
        input_messages: Union[str, List[Dict[str, str]]],
        output_model: Type[T],
        system_message: Optional[str] = None,
        previous_response_id: Optional[str] = None,
        store: bool = True
    ) -> StructuredOutputResponse:
        """
        Get structured response using Responses API
        
        Args:
            input_messages: String or list of messages
            output_model: Pydantic model for structured output
            system_message: Optional system message
            previous_response_id: For conversation continuity
            store: Whether to store the response
        """
        
        try:
            # Prepare input
            if isinstance(input_messages, str):
                input_data = []
                if system_message:
                    input_data.append({"role": "system", "content": system_message})
                input_data.append({"role": "user", "content": input_messages})
            else:
                input_data = input_messages
                if system_message and not any(msg.get("role") == "system" for msg in input_data):
                    input_data.insert(0, {"role": "system", "content": system_message})
            
            # Prepare request parameters
            request_params = {
                "model": self.model,
                "input": input_data,
                "text": {
                    "format": {
                        "type": "json_schema",
                        "name": f"{output_model.__name__}Output",
                        "description": f"Structured output for {output_model.__name__}",
                        "schema": self._prepare_schema_for_responses_api(output_model.model_json_schema())
                    }
                },
                "temperature": self.temperature,
                "store": store
            }
            
            # Note: Responses API doesn't support max_tokens parameter
            # if self.max_tokens:
            #     request_params["max_tokens"] = self.max_tokens
            if previous_response_id:
                request_params["previous_response_id"] = previous_response_id
            
            # Make API call
            logger.debug("Making Responses API call", 
                        model=self.model,
                        output_model=output_model.__name__,
                        has_previous_response=bool(previous_response_id))
            
            response = await self.async_client.responses.create(**request_params)
            
            # Parse and validate structured output
            output_text = response.output_text
            
            try:
                # Parse JSON from response
                parsed_data = json.loads(output_text)
                
                # Validate against Pydantic model
                validated_output = output_model(**parsed_data)
                
                return StructuredOutputResponse(
                    success=True,
                    data=validated_output,
                    metadata={
                        "response_id": response.id,
                        "model": self.model,
                        "method": "responses_api",
                        "previous_response_id": previous_response_id,
                        "token_usage": getattr(response, 'usage', None)
                    }
                )
                
            except json.JSONDecodeError as e:
                logger.error("Failed to parse JSON from response", 
                           output_text=output_text[:200],
                           error=str(e))
                return StructuredOutputResponse(
                    success=False,
                    data={},
                    error=f"JSON parsing failed: {str(e)}",
                    metadata={"response_id": response.id, "raw_output": output_text}
                )
                
            except ValidationError as e:
                logger.error("Pydantic validation failed", 
                           model=output_model.__name__,
                           error=str(e))
                return StructuredOutputResponse(
                    success=False,
                    data={},
                    error=f"Validation failed: {str(e)}",
                    metadata={"response_id": response.id, "parsed_data": parsed_data}
                )
            
        except Exception as e:
            logger.error("Responses API call failed", 
                        model=self.model,
                        error=str(e))
            return StructuredOutputResponse(
                success=False,
                data={},
                error=f"API call failed: {str(e)}",
                metadata={"model": self.model}
            )
    
    def get_structured_response_sync(
        self,
        input_messages: Union[str, List[Dict[str, str]]],
        output_model: Type[T],
        system_message: Optional[str] = None,
        previous_response_id: Optional[str] = None,
        store: bool = True
    ) -> StructuredOutputResponse:
        """Synchronous version of get_structured_response"""
        
        try:
            # Prepare input (same logic as async)
            if isinstance(input_messages, str):
                input_data = []
                if system_message:
                    input_data.append({"role": "system", "content": system_message})
                input_data.append({"role": "user", "content": input_messages})
            else:
                input_data = input_messages
                if system_message and not any(msg.get("role") == "system" for msg in input_data):
                    input_data.insert(0, {"role": "system", "content": system_message})
            
            # Prepare request parameters
            request_params = {
                "model": self.model,
                "input": input_data,
                "text": {
                    "format": {
                        "type": "json_schema",
                        "name": f"{output_model.__name__}Output",
                        "description": f"Structured output for {output_model.__name__}",
                        "schema": self._prepare_schema_for_responses_api(output_model.model_json_schema())
                    }
                },
                "temperature": self.temperature,
                "store": store
            }
            
            # Note: Responses API doesn't support max_tokens parameter
            # if self.max_tokens:
            #     request_params["max_tokens"] = self.max_tokens
            if previous_response_id:
                request_params["previous_response_id"] = previous_response_id
            
            # Make synchronous API call
            response = self.sync_client.responses.create(**request_params)
            
            # Parse and validate (same logic as async)
            output_text = response.output_text
            parsed_data = json.loads(output_text)
            validated_output = output_model(**parsed_data)
            
            return StructuredOutputResponse(
                success=True,
                data=validated_output,
                metadata={
                    "response_id": response.id,
                    "model": self.model,
                    "method": "responses_api_sync",
                    "previous_response_id": previous_response_id,
                    "token_usage": getattr(response, 'usage', None)
                }
            )
            
        except Exception as e:
            logger.error("Sync Responses API call failed", error=str(e))
            return StructuredOutputResponse(
                success=False,
                data={},
                error=f"Sync API call failed: {str(e)}",
                metadata={"model": self.model}
            )
    
    async def simple_text_response(
        self,
        input_messages: Union[str, List[Dict[str, str]]],
        system_message: Optional[str] = None,
        previous_response_id: Optional[str] = None,
        store: bool = True
    ) -> str:
        """
        Get simple text response without structured output
        Useful for basic text generation tasks
        """
        
        try:
            # Prepare input
            if isinstance(input_messages, str):
                input_data = []
                if system_message:
                    input_data.append({"role": "system", "content": system_message})
                input_data.append({"role": "user", "content": input_messages})
            else:
                input_data = input_messages
                if system_message and not any(msg.get("role") == "system" for msg in input_data):
                    input_data.insert(0, {"role": "system", "content": system_message})
            
            request_params = {
                "model": self.model,
                "input": input_data,
                "temperature": self.temperature,
                "store": store
            }
            
            # Note: Responses API doesn't support max_tokens parameter
            # if self.max_tokens:
            #     request_params["max_tokens"] = self.max_tokens
            if previous_response_id:
                request_params["previous_response_id"] = previous_response_id
            
            response = await self.async_client.responses.create(**request_params)
            return response.output_text
            
        except Exception as e:
            logger.error("Simple text response failed", error=str(e))
            raise Exception(f"Text response failed: {str(e)}")
    
    async def get_simple_structured_response(
        self,
        input_messages: Union[str, List[Dict[str, str]]],
        simple_model_name: str,
        system_message: Optional[str] = None,
        previous_response_id: Optional[str] = None,
        store: bool = True
    ) -> StructuredOutputResponse:
        """
        Get structured response using simplified models optimized for Responses API
        
        Args:
            input_messages: String or list of messages
            simple_model_name: Name of the simplified model to use
            system_message: Optional system message
            previous_response_id: For conversation continuity
            store: Whether to store the response
        """
        
        try:
            # Get the simplified model
            simple_model = get_simple_model(simple_model_name)
            
            logger.debug("Using simplified model for Responses API", 
                        model=simple_model_name)
            
            # Use the existing structured response method
            result = await self.get_structured_response(
                input_messages=input_messages,
                output_model=simple_model,
                system_message=system_message,
                previous_response_id=previous_response_id,
                store=store
            )
            
            # Add simplified model metadata
            if result.success and result.metadata:
                result.metadata["simplified_model"] = simple_model_name
                result.metadata["responses_api_optimized"] = True
            
            return result
            
        except Exception as e:
            logger.error("Simple structured response failed", 
                        simple_model=simple_model_name, error=str(e))
            return StructuredOutputResponse(
                success=False,
                data={},
                error=f"Simple structured response failed: {str(e)}",
                metadata={"simple_model": simple_model_name}
            )
    
    async def get_flat_structured_response(
        self,
        input_messages: Union[str, List[Dict[str, str]]],
        flat_model_name: str,
        system_message: Optional[str] = None,
        previous_response_id: Optional[str] = None,
        store: bool = True
    ) -> StructuredOutputResponse:
        """
        Get structured response using completely flat models optimized for Responses API
        
        These models have no nested objects and should work perfectly with Responses API.
        
        Args:
            input_messages: String or list of messages
            flat_model_name: Name of the flat model to use
            system_message: Optional system message
            previous_response_id: For conversation continuity
            store: Whether to store the response
        """
        
        try:
            # Get the flat model
            flat_model = get_flat_model(flat_model_name)
            
            logger.debug("Using flat model for Responses API", 
                        model=flat_model_name)
            
            # Use the existing structured response method
            result = await self.get_structured_response(
                input_messages=input_messages,
                output_model=flat_model,
                system_message=system_message,
                previous_response_id=previous_response_id,
                store=store
            )
            
            # Add flat model metadata
            if result.success and result.metadata:
                result.metadata["flat_model"] = flat_model_name
                result.metadata["responses_api_optimized"] = True
                result.metadata["completely_flat"] = True
            
            return result
            
        except Exception as e:
            logger.error("Flat structured response failed", 
                        flat_model=flat_model_name, error=str(e))
            return StructuredOutputResponse(
                success=False,
                data={},
                error=f"Flat structured response failed: {str(e)}",
                metadata={"flat_model": flat_model_name}
            )


class SalesOrderResponsesClient:
    """
    Sales order specific client built on ResponsesAPIClient
    Provides domain-specific methods for sales order processing
    """
    
    def __init__(self, responses_client: Optional[ResponsesAPIClient] = None):
        self.client = responses_client or ResponsesAPIClient()
    
    async def extract_sales_order_analysis(
        self,
        customer_email: str,
        customer_name: str,
        previous_response_id: Optional[str] = None
    ) -> StructuredOutputResponse:
        """Extract structured sales order analysis using simplified Responses API models"""
        
        system_message = """
        You are a sales order analysis expert for a metals manufacturing company.
        Analyze customer emails and extract structured information for order processing.
        
        Focus on:
        - Customer context and industry classification
        - Emergency situation detection  
        - Product requirements extraction
        - Complexity assessment
        
        Use specific values like SMALL/MEDIUM/LARGE for company size,
        HIGH/MEDIUM/LOW for urgency and complexity levels.
        """
        
        prompt = f"""
        Analyze this sales order request:
        
        Customer: {customer_name}
        Email: {customer_email}
        
        Extract complete structured analysis including customer context, 
        emergency assessment, product requirements, and complexity level.
        
        For any field you cannot determine, use appropriate default values:
        - Industry: Use best guess based on content
        - Company size: MEDIUM if unknown
        - Urgency: LOW if no urgency indicators
        - Complexity: MEDIUM if unclear
        """
        
        return await self.client.get_simple_structured_response(
            input_messages=prompt,
            simple_model_name="SimpleOrderAnalysis",
            system_message=system_message,
            previous_response_id=previous_response_id
        )
    
    async def generate_erp_json(
        self,
        customer_email: str,
        customer_name: str,
        order_analysis: Optional[SimpleOrderAnalysis] = None,
        previous_response_id: Optional[str] = None
    ) -> StructuredOutputResponse:
        """Generate ERP JSON with consistent structure using simplified Responses API models"""
        
        system_message = """
        You are an ERP data conversion specialist. Convert sales orders into 
        structured JSON for ERP system import.
        
        CRITICAL REQUIREMENTS:
        - Always use 'material' field (never 'product' or other variants)
        - Include complete customer information
        - Structure line items with consistent field names
        - Include order metadata for processing
        - Generate a unique order ID
        - Calculate total amount if possible
        
        The output must be valid for direct ERP import.
        """
        
        # Include analysis context if available
        analysis_context = ""
        if order_analysis:
            analysis_context = f"""
            
        Previous Analysis Context:
        - Industry: {order_analysis.customer_analysis.industry_sector}
        - Urgency: {order_analysis.emergency_assessment.urgency_level}
        - Complexity: {order_analysis.complexity_level}
        """
        
        prompt = f"""
        Convert this sales order to ERP JSON format:
        
        Customer: {customer_name}
        Email: {customer_email}{analysis_context}
        
        Generate complete ERP order structure with customer info, line items, and metadata.
        Ensure all material specifications use 'material' field consistently.
        
        Requirements:
        - Generate order ID in format: ORD-YYYY-NNNN
        - Calculate total_amount if line items have prices
        - Use 'Unknown' for missing information rather than leaving empty
        - Priority should be HIGH, MEDIUM, or LOW
        """
        
        return await self.client.get_simple_structured_response(
            input_messages=prompt,
            simple_model_name="SimpleERPOrder",
            system_message=system_message,
            previous_response_id=previous_response_id
        )
    
    async def detect_emergency_situation(
        self,
        customer_email: str,
        customer_name: str,
        previous_response_id: Optional[str] = None
    ) -> StructuredOutputResponse:
        """Extract structured emergency detection using Responses API"""
        
        system_message = """
        You are an emergency situation detection specialist for a manufacturing company.
        Analyze customer communications for urgent situations requiring immediate response.
        """
        
        prompt = f"""
        Analyze this customer communication for emergency indicators:
        
        Customer: {customer_name}
        Message: {customer_email}
        
        Detect any emergency situations, assess urgency level, and identify
        time constraints or business impact.
        """
        
        return await self.client.get_structured_response(
            input_messages=prompt,
            output_model=EmergencyDetection,
            system_message=system_message,
            previous_response_id=previous_response_id
        )
    
    async def extract_customer_context(
        self,
        customer_email: str,
        customer_name: str,
        previous_response_id: Optional[str] = None
    ) -> StructuredOutputResponse:
        """Extract structured customer context analysis using Responses API"""
        
        system_message = """
        You are a customer intelligence analyst. Analyze customer communications
        to understand their business context, industry, and requirements.
        """
        
        prompt = f"""
        Analyze this customer communication for business context:
        
        Customer: {customer_name}
        Message: {customer_email}
        
        Determine industry sector, business size, compliance requirements,
        and customer tier classification.
        """
        
        return await self.client.get_structured_response(
            input_messages=prompt,
            output_model=CustomerContextAnalysis,
            system_message=system_message,
            previous_response_id=previous_response_id
        )


# Factory functions for easy instantiation
def create_responses_client() -> ResponsesAPIClient:
    """Factory function for creating ResponsesAPIClient"""
    return ResponsesAPIClient()

def create_sales_order_client() -> SalesOrderResponsesClient:
    """Factory function for creating SalesOrderResponsesClient"""
    return SalesOrderResponsesClient()

def get_structured_model(model_name: str) -> Type[BaseModel]:
    """Get structured output model by name"""
    if model_name not in STRUCTURED_OUTPUT_MODELS:
        raise ValueError(f"Unknown model: {model_name}")
    return STRUCTURED_OUTPUT_MODELS[model_name]

# Global client instance for reuse
_global_responses_client = None

def get_global_responses_client() -> ResponsesAPIClient:
    """Get or create global ResponsesAPIClient instance"""
    global _global_responses_client
    if _global_responses_client is None:
        _global_responses_client = ResponsesAPIClient()
    return _global_responses_client