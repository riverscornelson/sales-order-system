"""
Structured LLM Output Integration Layer - Responses API Only

This module provides utilities for integrating Pydantic structured outputs
with LLM agents using the OpenAI Responses API and gpt-4.1 exclusively.

Key Features:
- OpenAI Responses API with structured outputs only
- Always uses gpt-4.1 model for consistency
- Conversation state management with previous_response_id
- Comprehensive error handling and validation
- Clean, simple interface without legacy baggage
"""

import json
from typing import Type, TypeVar, Dict, Any, Optional, Union, List
from pydantic import BaseModel, ValidationError
import structlog

from app.core.responses_client import (
    ResponsesAPIClient, SalesOrderResponsesClient,
    create_responses_client, get_global_responses_client
)
from app.models.structured_outputs import StructuredOutputResponse
from app.models.flat_responses_models import (
    FlatERPOrder, FlatOrderAnalysis, FlatPartMatch, FlatOrderData,
    FLAT_STRUCTURED_OUTPUT_MODELS
)

T = TypeVar('T', bound=BaseModel)

logger = structlog.get_logger()


class StructuredLLMClient:
    """
    Enhanced LLM client using only OpenAI Responses API with gpt-4.1
    
    Simple, clean interface focused on structured outputs using the latest
    OpenAI technology. No legacy methods or backwards compatibility.
    """
    
    def __init__(self, temperature: float = 0.1, max_tokens: Optional[int] = None):
        self.model = "gpt-4.1"  # Fixed model for consistency
        self.temperature = temperature
        self.max_tokens = max_tokens
        
        # Use new Responses API client exclusively
        self.responses_client = ResponsesAPIClient(
            temperature=temperature, 
            max_tokens=max_tokens
        )
        
        logger.info("Initialized StructuredLLMClient with Responses API only", 
                   model=self.model, temperature=temperature)
    
    async def get_structured_output(
        self,
        prompt: str,
        flat_model_name: str,
        system_message: Optional[str] = None,
        previous_response_id: Optional[str] = None,
        store: bool = True
    ) -> StructuredOutputResponse:
        """
        Get structured output using flat models and Responses API exclusively
        
        Args:
            prompt: User prompt
            flat_model_name: Name of flat model to use
            system_message: Optional system message
            previous_response_id: For conversation continuity
            store: Whether to store the response
        """
        
        logger.debug("Getting structured output via Responses API", 
                   model=flat_model_name)
        
        return await self.responses_client.get_flat_structured_response(
            input_messages=prompt,
            flat_model_name=flat_model_name,
            system_message=system_message,
            previous_response_id=previous_response_id,
            store=store
        )
    
    async def get_structured_output_from_messages(
        self,
        messages: List[Dict[str, str]],
        flat_model_name: str,
        previous_response_id: Optional[str] = None,
        store: bool = True
    ) -> StructuredOutputResponse:
        """
        Get structured output from pre-formatted message list using flat models
        
        Args:
            messages: List of messages in OpenAI format
            flat_model_name: Name of flat model to use
            previous_response_id: For conversation continuity
            store: Whether to store the response
        """
        
        logger.debug("Getting structured output from messages via Responses API", 
                   model=flat_model_name, message_count=len(messages))
        
        return await self.responses_client.get_flat_structured_response(
            input_messages=messages,
            flat_model_name=flat_model_name,
            previous_response_id=previous_response_id,
            store=store
        )
    
    async def simple_text_response(
        self,
        prompt: str,
        system_message: Optional[str] = None,
        previous_response_id: Optional[str] = None,
        store: bool = True
    ) -> str:
        """
        Get simple text response without structured output
        
        Args:
            prompt: User prompt
            system_message: Optional system message
            previous_response_id: For conversation continuity
            store: Whether to store the response
        """
        
        logger.debug("Getting simple text response via Responses API")
        
        return await self.responses_client.simple_text_response(
            input_messages=prompt,
            system_message=system_message,
            previous_response_id=previous_response_id,
            store=store
        )


class SalesOrderStructuredOutputs:
    """
    Sales order specific structured output functions using Responses API
    
    These functions solve the specific issues identified in the OpenAI evaluations
    by ensuring consistent field names and validated JSON structures.
    """
    
    def __init__(self, llm_client: Optional[StructuredLLMClient] = None):
        self.llm_client = llm_client or StructuredLLMClient()
        self.sales_client = SalesOrderResponsesClient(self.llm_client.responses_client)
    
    async def extract_sales_order_analysis(
        self,
        customer_email: str,
        customer_name: str,
        previous_response_id: Optional[str] = None
    ) -> StructuredOutputResponse:
        """
        Extract structured sales order analysis - USES RESPONSES API
        
        This replaces the inconsistent JSON generation that caused
        OpenAI evaluation failures.
        """
        
        return await self.sales_client.extract_sales_order_analysis(
            customer_email=customer_email,
            customer_name=customer_name,
            previous_response_id=previous_response_id
        )
    
    async def generate_erp_json(
        self,
        customer_email: str,
        customer_name: str,
        order_analysis: Optional[Any] = None,
        previous_response_id: Optional[str] = None
    ) -> StructuredOutputResponse:
        """
        Generate ERP JSON with consistent structure - USES RESPONSES API
        
        This ensures the 'material' field is always present and consistent,
        fixing the exact issue that caused our evaluations to fail.
        """
        
        return await self.sales_client.generate_erp_json(
            customer_email=customer_email,
            customer_name=customer_name,
            order_analysis=order_analysis,
            previous_response_id=previous_response_id
        )
    
    async def detect_emergency_situation(
        self,
        customer_email: str,
        customer_name: str,
        previous_response_id: Optional[str] = None
    ) -> StructuredOutputResponse:
        """Extract structured emergency detection using Responses API"""
        
        return await self.sales_client.detect_emergency_situation(
            customer_email=customer_email,
            customer_name=customer_name,
            previous_response_id=previous_response_id
        )
    
    async def extract_customer_context(
        self,
        customer_email: str,
        customer_name: str,
        previous_response_id: Optional[str] = None
    ) -> StructuredOutputResponse:
        """Extract structured customer context analysis using Responses API"""
        
        return await self.sales_client.extract_customer_context(
            customer_email=customer_email,
            customer_name=customer_name,
            previous_response_id=previous_response_id
        )


# =============================================================================
# FACTORY FUNCTIONS FOR EASY INSTANTIATION
# =============================================================================

def create_sales_order_analyzer() -> SalesOrderStructuredOutputs:
    """Factory function for sales order structured outputs using Responses API"""
    return SalesOrderStructuredOutputs()

def get_flat_model(model_name: str) -> Type[BaseModel]:
    """Get flat model by name"""
    if model_name not in FLAT_STRUCTURED_OUTPUT_MODELS:
        raise ValueError(f"Unknown flat model: {model_name}")
    return FLAT_STRUCTURED_OUTPUT_MODELS[model_name]

def create_erp_json_generator() -> SalesOrderStructuredOutputs:
    """Factory function specifically for ERP JSON generation using Responses API"""
    client = StructuredLLMClient(temperature=0.0)  # Zero temp for consistency
    return SalesOrderStructuredOutputs(llm_client=client)

def create_structured_llm_client(temperature: float = 0.1) -> StructuredLLMClient:
    """Factory function for creating StructuredLLMClient with Responses API"""
    return StructuredLLMClient(temperature=temperature)

# Global client instance for reuse
_global_structured_client = None

def get_global_structured_client() -> StructuredLLMClient:
    """Get or create global StructuredLLMClient instance"""
    global _global_structured_client
    if _global_structured_client is None:
        _global_structured_client = StructuredLLMClient()
    return _global_structured_client