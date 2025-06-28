"""
Part Matching Agent - Responses API Only

This agent selects the best part match from search results using OpenAI Responses API
with gpt-4.1 and structured outputs exclusively.
"""

import json
import asyncio
from typing import List, Dict, Any, Optional
import structlog
from pydantic import BaseModel, Field

from app.core.responses_client import ResponsesAPIClient
from app.models.flat_responses_models import FlatPartMatch

logger = structlog.get_logger()


# Using FlatPartMatch from flat_responses_models for Responses API compatibility


class PartMatchingAgent:
    """AI-powered agent that selects the best part match using Responses API with gpt-4.1"""
    
    def __init__(self):
        self.model = "gpt-4.1"  # Fixed model
        self.responses_client = ResponsesAPIClient(temperature=0.1, max_tokens=2000)
        logger.info("Initialized PartMatchingAgent with Responses API", model=self.model)
    
    async def select_best_match(self, line_item: LineItem, 
                              search_results: List[SearchResult]) -> MatchSelection:
        """Use AI to select the best part match for a line item"""
        
        logger.info("Starting part matching for line item",
                   line_id=line_item.line_id,
                   candidates=len(search_results))
        
        try:
            if not search_results:
                return self._create_no_match_result(line_item)
            
            # Filter to top candidates for AI analysis
            top_candidates = search_results[:5]
            
            # Use Responses API to make intelligent selection
            ai_selection = await self._responses_api_match_selection(line_item, top_candidates)
            
            # Validate and enhance the selection
            validated_selection = self._validate_selection(ai_selection, top_candidates)
            
            logger.info("Part matching completed",
                       line_id=line_item.line_id,
                       selected_part=validated_selection.selected_part_number,
                       confidence=validated_selection.confidence.overall_confidence)
            
            return validated_selection
            
        except Exception as e:
            logger.error("Part matching failed",
                        line_id=line_item.line_id,
                        error=str(e))
            return self._create_error_result(line_item, str(e))
    
    async def _responses_api_match_selection(self, line_item: LineItem, 
                                           candidates: List[SearchResult]) -> PartMatchAnalysis:
        """Use Responses API to analyze and select the best part match"""
        
        system_message = """
        You are an expert parts specialist for a metals manufacturing company.
        Analyze the customer's line item requirements against available parts
        and select the best match based on:
        
        1. Technical specifications (dimensions, material grade, etc.)
        2. Material compatibility and suitability
        3. Availability and lead times
        4. Price considerations
        5. Quality and reliability factors
        
        Consider both exact matches and suitable alternatives.
        Always explain your reasoning clearly.
        """
        
        # Format candidate parts for analysis
        candidates_text = self._format_candidates_for_prompt(candidates)
        
        prompt = f"""
        CUSTOMER REQUIREMENT:
        Line Item: {line_item.description}
        Quantity: {line_item.quantity}
        Raw Text: {line_item.raw_text}
        
        AVAILABLE PARTS:
        {candidates_text}
        
        Analyze these candidates and select the best match for the customer's requirement.
        Consider all factors including specifications, material compatibility, availability, and price.
        
        Provide:
        1. Selected part number with confidence score
        2. Detailed reasoning for the selection
        3. Individual scores for specification match, material compatibility, dimensions, and availability
        4. Alternative recommendations if applicable
        5. Any risk factors or concerns
        6. Price considerations
        """
        
        try:
            result = await self.responses_client.get_structured_response(
                input_messages=prompt,
                output_model=PartMatchAnalysis,
                system_message=system_message,
                store=True
            )
            
            if result.success:
                return result.data
            else:
                logger.warning("AI match selection failed", error=result.error)
                return self._get_fallback_analysis(candidates)
                
        except Exception as e:
            logger.error("Responses API match selection error", error=str(e))
            return self._get_fallback_analysis(candidates)
    
    def _format_candidates_for_prompt(self, candidates: List[SearchResult]) -> str:
        """Format candidate parts for the AI prompt"""
        
        formatted_parts = []
        
        for i, candidate in enumerate(candidates, 1):
            part_info = f"""
            {i}. PART NUMBER: {candidate.part_number}
               DESCRIPTION: {candidate.description}
               MATERIAL: {candidate.material or 'Not specified'}
               SPECIFICATIONS: {json.dumps(candidate.specifications) if candidate.specifications else 'None'}
               PRICE: ${candidate.unit_price:.2f} if candidate.unit_price else 'Not available'
               AVAILABILITY: {candidate.availability or 'Unknown'} units
               SUPPLIER: {candidate.supplier or 'Unknown'}
               SIMILARITY SCORE: {candidate.similarity_score:.3f}
            """
            formatted_parts.append(part_info)
        
        return "\n".join(formatted_parts)
    
    def _get_fallback_analysis(self, candidates: List[SearchResult]) -> PartMatchAnalysis:
        """Provide fallback analysis when AI selection fails"""
        
        if not candidates:
            return {
                "selected_part_number": "NO_MATCH",
                "confidence_score": 0.0,
                "match_reasoning": "No candidates available for matching",
                "specification_match": 0.0,
                "material_compatibility": 0.0,
                "availability_score": 0.0,
                "alternative_part": "None",
                "risk_factors": "No candidates"
            }
        
        # Select the highest similarity score candidate as fallback
        best_candidate = max(candidates, key=lambda x: x.similarity_score)
        
        return {
            "selected_part_number": best_candidate.part_number,
            "confidence_score": best_candidate.similarity_score,
            "match_reasoning": "Fallback selection based on highest similarity score",
            "specification_match": best_candidate.similarity_score,
            "material_compatibility": 0.7,  # Assume reasonable compatibility
            "availability_score": 0.8 if best_candidate.availability and best_candidate.availability > 0 else 0.3,
            "alternative_part": candidates[1].part_number if len(candidates) > 1 else "None",
            "risk_factors": "Fallback selection - manual review recommended"
        }
    
    def _validate_selection(self, analysis: PartMatchAnalysis, 
                          candidates: List[SearchResult]) -> MatchSelection:
        """Validate AI selection and create MatchSelection object"""
        
        # Find the selected candidate
        selected_candidate = None
        for candidate in candidates:
            if candidate.part_number == analysis.selected_part_number:
                selected_candidate = candidate
                break
        
        if not selected_candidate:
            logger.warning("Selected part not found in candidates", 
                         selected=analysis.selected_part_number)
            # Fall back to first candidate
            selected_candidate = candidates[0]
            analysis.selected_part_number = selected_candidate.part_number
        
        # Create confidence object
        confidence = MatchConfidence(
            overall_confidence=analysis.confidence_score,
            specification_match=analysis.specification_match,
            material_compatibility=analysis.material_compatibility,
            availability_confidence=analysis.availability_score,
            price_confidence=0.8,  # Default reasonable price confidence
            source_reliability=0.9  # High reliability for our catalog
        )
        
        # Create match selection
        match_selection = MatchSelection(
            line_item_id=selected_candidate.line_item_id,
            selected_part_number=analysis.selected_part_number,
            selected_description=selected_candidate.description,
            selected_material=selected_candidate.material,
            selected_specifications=selected_candidate.specifications or {},
            unit_price=selected_candidate.unit_price,
            availability=selected_candidate.availability,
            supplier=selected_candidate.supplier,
            confidence=confidence,
            reasoning=analysis.match_reasoning,
            alternatives=[
                {"part_number": alt, "reason": "AI recommended alternative"}
                for alt in analysis.alternative_recommendations
            ],
            risk_factors=analysis.risk_factors,
            match_timestamp=None,  # Will be set automatically
            ai_model=self.model
        )
        
        return match_selection
    
    def _create_no_match_result(self, line_item: LineItem) -> MatchSelection:
        """Create result when no candidates are available"""
        
        confidence = MatchConfidence(
            overall_confidence=0.0,
            specification_match=0.0,
            material_compatibility=0.0,
            availability_confidence=0.0,
            price_confidence=0.0,
            source_reliability=1.0
        )
        
        return MatchSelection(
            line_item_id=line_item.line_id,
            selected_part_number="NO_MATCH",
            selected_description="No matching parts found",
            confidence=confidence,
            reasoning="No search results available for matching",
            alternatives=[],
            risk_factors=["No parts available in catalog"],
            ai_model=self.model
        )
    
    def _create_error_result(self, line_item: LineItem, error_msg: str) -> MatchSelection:
        """Create result when matching process fails"""
        
        confidence = MatchConfidence(
            overall_confidence=0.0,
            specification_match=0.0,
            material_compatibility=0.0,
            availability_confidence=0.0,
            price_confidence=0.0,
            source_reliability=0.0
        )
        
        return MatchSelection(
            line_item_id=line_item.line_id,
            selected_part_number="ERROR",
            selected_description="Matching process failed",
            confidence=confidence,
            reasoning=f"Part matching failed: {error_msg}",
            alternatives=[],
            risk_factors=["Matching process error"],
            ai_model=self.model
        )


# Factory function for easy instantiation
def create_part_matching_agent() -> PartMatchingAgent:
    """Factory function for creating PartMatchingAgent with Responses API"""
    return PartMatchingAgent()