"""
Structured LLM Output Integration Layer

This module provides utilities for integrating Pydantic structured outputs
with LLM agents, solving the JSON consistency issues from OpenAI evaluations.

Key Features:
- OpenAI structured outputs integration
- LangChain Pydantic output parser integration  
- Automatic schema generation for prompts
- Validation and error handling
- Migration utilities for existing agents
"""

import json
from typing import Type, TypeVar, Dict, Any, Optional, Union, List
from pydantic import BaseModel, ValidationError
from openai import OpenAI
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage

from app.models.structured_outputs import (
    ERPOrderOutput, SalesOrderAnalysis, SalesOrderReasoning,
    CustomerContextAnalysis, EmergencyDetection, ProductRequirement,
    StructuredOutputResponse, STRUCTURED_OUTPUT_MODELS
)

T = TypeVar('T', bound=BaseModel)


class StructuredLLMClient:
    """
    Enhanced LLM client with structured output support
    
    Provides multiple methods for getting structured outputs:
    1. OpenAI native structured outputs (beta)
    2. LangChain Pydantic parsers (stable)
    3. Manual JSON parsing with validation
    """
    
    def __init__(self, model: str = "gpt-4.1", temperature: float = 0.1):
        self.model = model
        self.temperature = temperature
        self.openai_client = OpenAI()
        self.langchain_client = ChatOpenAI(
            model=model, 
            temperature=temperature
        )
    
    async def get_structured_output(
        self,
        prompt: str,
        output_model: Type[T],
        system_message: Optional[str] = None,
        method: str = "openai_structured"
    ) -> StructuredOutputResponse:
        """
        Get structured output using specified method
        
        Args:
            prompt: User prompt
            output_model: Pydantic model class for output structure
            system_message: Optional system message
            method: "openai_structured", "langchain_parser", or "manual_parse"
        """
        
        try:
            if method == "openai_structured":
                result = await self._openai_structured_output(
                    prompt, output_model, system_message
                )
            elif method == "langchain_parser":
                result = await self._langchain_pydantic_output(
                    prompt, output_model, system_message
                )
            elif method == "manual_parse":
                result = await self._manual_json_parse(
                    prompt, output_model, system_message
                )
            else:
                raise ValueError(f"Unknown method: {method}")
            
            return StructuredOutputResponse(
                success=True,
                data=result,
                metadata={"method": method, "model": self.model}
            )
            
        except Exception as e:
            return StructuredOutputResponse(
                success=False,
                data={},
                error=str(e),
                metadata={"method": method, "model": self.model}
            )
    
    async def _openai_structured_output(
        self,
        prompt: str,
        output_model: Type[T],
        system_message: Optional[str] = None
    ) -> T:
        """Use OpenAI's native structured outputs (beta feature)"""
        
        messages = []
        if system_message:
            messages.append({"role": "system", "content": system_message})
        messages.append({"role": "user", "content": prompt})
        
        # Convert Pydantic model to OpenAI function schema
        function_schema = {
            "name": f"generate_{output_model.__name__.lower()}",
            "description": f"Generate structured {output_model.__name__}",
            "parameters": output_model.model_json_schema()
        }
        
        response = self.openai_client.chat.completions.create(
            model=self.model,
            messages=messages,
            functions=[function_schema],
            function_call={"name": function_schema["name"]},
            temperature=self.temperature
        )
        
        # Extract function call arguments and validate
        function_call = response.choices[0].message.function_call
        if not function_call:
            raise ValueError("No function call in response")
        
        arguments = json.loads(function_call.arguments)
        return output_model(**arguments)
    
    async def _langchain_pydantic_output(
        self,
        prompt: str,
        output_model: Type[T],
        system_message: Optional[str] = None
    ) -> T:
        """Use LangChain's Pydantic output parser"""
        
        parser = PydanticOutputParser(pydantic_object=output_model)
        
        # Create prompt with format instructions
        format_instructions = parser.get_format_instructions()
        
        full_prompt = f"{prompt}\n\n{format_instructions}"
        
        messages = []
        if system_message:
            messages.append(SystemMessage(content=system_message))
        messages.append(HumanMessage(content=full_prompt))
        
        response = await self.langchain_client.ainvoke(messages)
        return parser.parse(response.content)
    
    async def _manual_json_parse(
        self,
        prompt: str,
        output_model: Type[T],
        system_message: Optional[str] = None
    ) -> T:
        """Manual JSON parsing with validation"""
        
        # Enhanced system message with schema
        schema_str = json.dumps(output_model.model_json_schema(), indent=2)
        
        enhanced_system = f"""
        {system_message or 'You are a helpful assistant.'}
        
        CRITICAL: Return ONLY valid JSON that matches this exact schema:
        
        {schema_str}
        
        Do not include any explanations, markdown formatting, or additional text.
        Return only the JSON object.
        """
        
        messages = [
            {"role": "system", "content": enhanced_system},
            {"role": "user", "content": prompt}
        ]
        
        response = self.openai_client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=self.temperature
        )
        
        content = response.choices[0].message.content.strip()
        
        # Extract JSON from response (handle markdown wrapping)
        if content.startswith("```json"):
            content = content[7:]
        if content.endswith("```"):
            content = content[:-3]
        
        # Find JSON boundaries
        start = content.find('{')
        end = content.rfind('}') + 1
        
        if start == -1 or end == 0:
            raise ValueError("No JSON found in response")
        
        json_str = content[start:end]
        data = json.loads(json_str)
        return output_model(**data)


# =============================================================================
# SALES ORDER SPECIFIC STRUCTURED OUTPUT FUNCTIONS
# =============================================================================

class SalesOrderStructuredOutputs:
    """
    Sales order specific structured output functions
    
    These functions solve the specific issues identified in the OpenAI evaluations
    by ensuring consistent field names and validated JSON structures.
    """
    
    def __init__(self, llm_client: Optional[StructuredLLMClient] = None):
        self.llm_client = llm_client or StructuredLLMClient()
    
    async def extract_sales_order_analysis(
        self,
        customer_email: str,
        customer_name: str
    ) -> StructuredOutputResponse:
        """
        Extract structured sales order analysis - FIXES EVAL ISSUES
        
        This replaces the inconsistent JSON generation that caused
        OpenAI evaluation failures.
        """
        
        system_message = """
        You are a sales order analysis expert for a metals manufacturing company.
        Analyze customer emails and extract structured information for order processing.
        
        Focus on:
        - Customer context and industry classification
        - Emergency situation detection  
        - Product requirements extraction
        - Complexity assessment
        """
        
        prompt = f"""
        Analyze this sales order request:
        
        Customer: {customer_name}
        Email: {customer_email}
        
        Extract complete structured analysis including customer context, 
        emergency assessment, product requirements, and complexity level.
        """
        
        return await self.llm_client.get_structured_output(
            prompt=prompt,
            output_model=SalesOrderAnalysis,
            system_message=system_message,
            method="langchain_parser"  # Most stable for complex structures
        )
    
    async def generate_erp_json(
        self,
        customer_email: str,
        customer_name: str,
        order_analysis: Optional[SalesOrderAnalysis] = None
    ) -> StructuredOutputResponse:
        """
        Generate ERP JSON with consistent structure - SOLVES OPENAI EVAL FAILURES
        
        This ensures the 'material' field is always present and consistent,
        fixing the exact issue that caused our evaluations to fail.
        """
        
        system_message = """
        You are an ERP data conversion specialist. Convert sales orders into 
        structured JSON for ERP system import.
        
        CRITICAL REQUIREMENTS:
        - Always use 'material' field (never 'product' or other variants)
        - Include complete customer information
        - Structure line items with consistent field names
        - Include order metadata for processing
        
        The output must be valid for direct ERP import.
        """
        
        # Include analysis context if available
        analysis_context = ""
        if order_analysis:
            analysis_context = f"""
            
        Previous Analysis Context:
        - Industry: {order_analysis.customer_context.industry_sector}
        - Urgency: {order_analysis.emergency_assessment.urgency_level}
        - Complexity: {order_analysis.complexity_assessment}
        """
        
        prompt = f"""
        Convert this sales order to ERP JSON format:
        
        Customer: {customer_name}
        Email: {customer_email}{analysis_context}
        
        Generate complete ERP order structure with customer info, line items, and metadata.
        Ensure all material specifications use 'material' field consistently.
        """
        
        return await self.llm_client.get_structured_output(
            prompt=prompt,
            output_model=ERPOrderOutput,
            system_message=system_message,
            method="openai_structured"  # Best for strict schema compliance
        )
    
    async def detect_emergency_situation(
        self,
        customer_email: str,
        customer_name: str
    ) -> StructuredOutputResponse:
        """Extract structured emergency detection"""
        
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
        
        return await self.llm_client.get_structured_output(
            prompt=prompt,
            output_model=EmergencyDetection,
            system_message=system_message
        )
    
    async def extract_customer_context(
        self,
        customer_email: str,
        customer_name: str
    ) -> StructuredOutputResponse:
        """Extract structured customer context analysis"""
        
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
        
        return await self.llm_client.get_structured_output(
            prompt=prompt,
            output_model=CustomerContextAnalysis,
            system_message=system_message
        )


# =============================================================================
# MIGRATION UTILITIES FOR EXISTING AGENTS
# =============================================================================

class AgentMigrationUtils:
    """Utilities for migrating existing agents to structured outputs"""
    
    @staticmethod
    def create_structured_prompt_template(
        base_template: str,
        output_model: Type[BaseModel]
    ) -> PromptTemplate:
        """Convert existing prompt template to use structured outputs"""
        
        parser = PydanticOutputParser(pydantic_object=output_model)
        format_instructions = parser.get_format_instructions()
        
        enhanced_template = f"""
        {base_template}
        
        RESPONSE FORMAT:
        {format_instructions}
        """
        
        return PromptTemplate(
            template=enhanced_template,
            input_variables=["customer_email", "customer_name"]
        )
    
    @staticmethod
    def validate_legacy_json_output(
        json_output: Dict[str, Any],
        target_model: Type[T]
    ) -> Union[T, ValidationError]:
        """Validate legacy JSON output against new structured model"""
        
        try:
            return target_model(**json_output)
        except ValidationError as e:
            return e
    
    @staticmethod
    def convert_legacy_agent_response(
        response: str,
        target_model: Type[T]
    ) -> StructuredOutputResponse:
        """Convert legacy agent string response to structured output"""
        
        try:
            # Try to extract JSON from response
            if response.strip().startswith('{'):
                data = json.loads(response)
            else:
                # Look for JSON within text
                start = response.find('{')
                end = response.rfind('}') + 1
                if start == -1 or end == 0:
                    raise ValueError("No JSON found in response")
                json_str = response[start:end]
                data = json.loads(json_str)
            
            # Validate against model
            validated_data = target_model(**data)
            
            return StructuredOutputResponse(
                success=True,
                data=validated_data,
                metadata={"converted_from_legacy": True}
            )
            
        except Exception as e:
            return StructuredOutputResponse(
                success=False,
                data={},
                error=f"Legacy conversion failed: {str(e)}",
                metadata={"converted_from_legacy": True}
            )


# =============================================================================
# FACTORY FUNCTIONS FOR COMMON USE CASES
# =============================================================================

def create_sales_order_analyzer() -> SalesOrderStructuredOutputs:
    """Factory function for sales order structured outputs"""
    return SalesOrderStructuredOutputs()

def get_structured_model(model_name: str) -> Type[BaseModel]:
    """Get structured output model by name"""
    if model_name not in STRUCTURED_OUTPUT_MODELS:
        raise ValueError(f"Unknown model: {model_name}")
    return STRUCTURED_OUTPUT_MODELS[model_name]

def create_erp_json_generator(model: str = "gpt-4.1") -> SalesOrderStructuredOutputs:
    """Factory function specifically for ERP JSON generation"""
    client = StructuredLLMClient(model=model, temperature=0.0)  # Zero temp for consistency
    return SalesOrderStructuredOutputs(llm_client=client)