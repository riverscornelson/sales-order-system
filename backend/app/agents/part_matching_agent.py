import json
import asyncio
from typing import List, Dict, Any, Optional
import structlog
from langchain_openai import ChatOpenAI

from ..models.line_item_schemas import (
    LineItem, SearchResult, MatchSelection, MatchConfidence
)

logger = structlog.get_logger()

class PartMatchingAgent:
    """AI-powered agent that selects the best part match from search results"""
    
    def __init__(self, llm: ChatOpenAI):
        self.llm = llm
    
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
            
            # Use AI to make intelligent selection
            ai_selection = await self._ai_match_selection(line_item, top_candidates)
            
            # Validate and enhance the selection
            validated_selection = self._validate_selection(ai_selection, top_candidates)
            
            logger.info("Part matching completed",
                       line_id=line_item.line_id,
                       selected_part=validated_selection.selected_part_number,
                       confidence=validated_selection.confidence)
            
            return validated_selection
            
        except Exception as e:
            logger.error("Part matching failed",
                        line_id=line_item.line_id,
                        error=str(e))
            return self._create_error_result(line_item, str(e))
    
    async def _ai_match_selection(self, line_item: LineItem, 
                                candidates: List[SearchResult]) -> Dict[str, Any]:
        """Use AI to intelligently select the best match"""
        
        # Prepare detailed context for AI analysis
        line_item_context = {
            "line_id": line_item.line_id,
            "raw_text": line_item.raw_text,
            "project": line_item.project,
            "urgency": line_item.urgency,
            "special_requirements": line_item.special_requirements or [],
            "extracted_specs": line_item.extracted_specs.dict() if line_item.extracted_specs else {}
        }
        
        candidates_context = []
        for candidate in candidates:
            candidates_context.append({
                "rank": candidate.rank,
                "part_number": candidate.part_number,
                "description": candidate.description,
                "similarity_score": candidate.similarity_score,
                "spec_match": candidate.spec_match,
                "availability": candidate.availability,
                "unit_price": candidate.unit_price,
                "supplier": candidate.supplier,
                "match_confidence": candidate.match_confidence,
                "notes": candidate.notes
            })
        
        matching_prompt = f"""
        You are an expert procurement specialist analyzing part matches for a sales order line item.
        
        LINE ITEM TO MATCH:
        {json.dumps(line_item_context, indent=2)}
        
        CANDIDATE PARTS:
        {json.dumps(candidates_context, indent=2)}
        
        ANALYSIS CRITERIA:
        1. **Specification Accuracy**: How well do the material grade, dimensions, and form factor match?
        2. **Availability vs Demand**: Is there sufficient inventory for the requested quantity?
        3. **Price Reasonableness**: Is the price within expected range for this material type?
        4. **Special Requirements**: Does the part meet certifications, compliance, or special needs?
        5. **Supplier Reliability**: Consider supplier track record and capabilities
        6. **Form Factor Compatibility**: Are there any form factor issues (sheet vs plate, etc.)?
        7. **Alternative Considerations**: Are there acceptable alternatives if primary choice has issues?
        
        DECISION MAKING:
        - Prioritize exact specification matches over close alternatives
        - Consider availability constraints seriously
        - Flag any compliance or certification gaps
        - Identify potential issues that might require customer approval
        - Suggest alternatives for risk mitigation
        
        CONFIDENCE LEVELS:
        - **high**: Exact match, good availability, meets all requirements
        - **medium-high**: Very close match, minor specification differences
        - **medium**: Good match but has some concerns (availability, price, specs)
        - **medium-low**: Acceptable but requires customer approval
        - **low**: Significant concerns, requires engineering review
        
        Return your analysis as JSON:
        {{
            "selected_part_number": "string",
            "confidence": "high|medium-high|medium|medium-low|low",
            "reasoning": "Detailed explanation of why this part was selected",
            "specification_analysis": {{
                "material_match": "exact|close|acceptable|poor",
                "dimension_match": "exact|close|acceptable|poor", 
                "form_factor_match": "exact|equivalent|different",
                "grade_compatibility": "identical|equivalent|acceptable|questionable"
            }},
            "concerns": [
                "List any concerns about this selection"
            ],
            "alternatives": [
                "List backup part numbers in order of preference"
            ],
            "requires_approval": true/false,
            "match_score": 0.0-1.0,
            "risk_assessment": {{
                "availability_risk": "low|medium|high",
                "specification_risk": "low|medium|high",
                "price_risk": "low|medium|high",
                "compliance_risk": "low|medium|high"
            }},
            "recommendations": [
                "Specific recommendations for this selection"
            ]
        }}
        
        Be thorough in your analysis and provide clear reasoning for your decision.
        """
        
        try:
            if self.llm is None:
                raise Exception("AI model not available")
            
            response = await asyncio.to_thread(self.llm.invoke, matching_prompt)
            ai_result = json.loads(response.content)
            
            logger.info("AI matching analysis completed",
                       line_id=line_item.line_id,
                       selected_part=ai_result.get("selected_part_number"),
                       confidence=ai_result.get("confidence"))
            
            return ai_result
            
        except Exception as e:
            logger.error("AI matching analysis failed",
                        line_id=line_item.line_id,
                        error=str(e))
            
            # Fallback to rule-based selection
            return self._fallback_selection(line_item, candidates)
    
    def _fallback_selection(self, line_item: LineItem, 
                          candidates: List[SearchResult]) -> Dict[str, Any]:
        """Fallback rule-based selection when AI fails"""
        
        logger.warning("Using fallback matching logic", line_id=line_item.line_id)
        
        if not candidates:
            return {
                "selected_part_number": None,
                "confidence": "low",
                "reasoning": "No suitable candidates found",
                "concerns": ["No matching parts in catalog"],
                "alternatives": [],
                "requires_approval": True,
                "match_score": 0.0
            }
        
        # Simple rule-based selection
        best_candidate = candidates[0]  # Highest ranked by search
        
        # Basic confidence assessment
        if best_candidate.similarity_score >= 0.8:
            confidence = "medium-high"
        elif best_candidate.similarity_score >= 0.6:
            confidence = "medium"
        else:
            confidence = "medium-low"
        
        # Check availability vs quantity needed
        concerns = []
        if line_item.extracted_specs and line_item.extracted_specs.quantity:
            needed_qty = line_item.extracted_specs.quantity
            available_qty = best_candidate.availability or 0
            
            if available_qty < needed_qty:
                concerns.append(f"Insufficient inventory: need {needed_qty}, available {available_qty}")
                confidence = "medium-low"
        
        # Check for special requirements
        if line_item.special_requirements:
            concerns.append("Special requirements need manual verification")
        
        return {
            "selected_part_number": best_candidate.part_number,
            "confidence": confidence,
            "reasoning": f"Selected highest-ranked candidate with {best_candidate.similarity_score:.2f} similarity score",
            "concerns": concerns,
            "alternatives": [c.part_number for c in candidates[1:4]],
            "requires_approval": len(concerns) > 0 or confidence in ["medium-low", "low"],
            "match_score": best_candidate.similarity_score
        }
    
    def _validate_selection(self, ai_result: Dict[str, Any], 
                          candidates: List[SearchResult]) -> MatchSelection:
        """Validate and enhance AI selection"""
        
        selected_part = ai_result.get("selected_part_number")
        
        # Ensure selected part is in candidates
        if selected_part:
            found_candidate = None
            for candidate in candidates:
                if candidate.part_number == selected_part:
                    found_candidate = candidate
                    break
            
            if not found_candidate:
                logger.warning("AI selected part not in candidates, using top candidate")
                selected_part = candidates[0].part_number if candidates else None
        
        # Validate confidence level
        confidence_str = ai_result.get("confidence", "medium")
        try:
            confidence = MatchConfidence(confidence_str)
        except ValueError:
            confidence = MatchConfidence.MEDIUM
            logger.warning("Invalid confidence level from AI", confidence=confidence_str)
        
        # Create MatchSelection object
        return MatchSelection(
            selected_part_number=selected_part or "NO_MATCH",
            confidence=confidence,
            reasoning=ai_result.get("reasoning", "AI analysis completed"),
            concerns=ai_result.get("concerns", []),
            alternatives=ai_result.get("alternatives", []),
            requires_approval=ai_result.get("requires_approval", False),
            match_score=float(ai_result.get("match_score", 0.0)),
            selection_metadata={
                "specification_analysis": ai_result.get("specification_analysis", {}),
                "risk_assessment": ai_result.get("risk_assessment", {}),
                "recommendations": ai_result.get("recommendations", []),
                "selection_method": "ai_analysis"
            }
        )
    
    def _create_no_match_result(self, line_item: LineItem) -> MatchSelection:
        """Create result when no candidates found"""
        
        return MatchSelection(
            selected_part_number="NO_MATCH",
            confidence=MatchConfidence.LOW,
            reasoning="No suitable parts found in catalog for this specification",
            concerns=["No matching parts in inventory"],
            alternatives=[],
            requires_approval=True,
            match_score=0.0,
            selection_metadata={
                "selection_method": "no_candidates",
                "recommendations": [
                    "Contact engineering for specification review",
                    "Consider alternative materials or suppliers",
                    "Check if custom fabrication is needed"
                ]
            }
        )
    
    def _create_error_result(self, line_item: LineItem, error_msg: str) -> MatchSelection:
        """Create result when matching process fails"""
        
        return MatchSelection(
            selected_part_number="ERROR",
            confidence=MatchConfidence.LOW,
            reasoning=f"Matching process failed: {error_msg}",
            concerns=["Technical error during matching process"],
            alternatives=[],
            requires_approval=True,
            match_score=0.0,
            selection_metadata={
                "selection_method": "error",
                "error_message": error_msg,
                "recommendations": ["Manual review required due to technical error"]
            }
        )
    
    async def batch_match_line_items(self, line_items_with_results: List[tuple]) -> List[MatchSelection]:
        """Process multiple line items in batch for efficiency"""
        
        logger.info("Starting batch matching", total_items=len(line_items_with_results))
        
        # Process items in parallel
        matching_tasks = []
        for line_item, search_results in line_items_with_results:
            task = self.select_best_match(line_item, search_results)
            matching_tasks.append(task)
        
        # Wait for all matches to complete
        match_results = await asyncio.gather(*matching_tasks, return_exceptions=True)
        
        # Handle any exceptions
        validated_results = []
        for i, result in enumerate(match_results):
            if isinstance(result, Exception):
                line_item, _ = line_items_with_results[i]
                error_result = self._create_error_result(line_item, str(result))
                validated_results.append(error_result)
            else:
                validated_results.append(result)
        
        logger.info("Batch matching completed", 
                   total_items=len(validated_results),
                   successful_matches=sum(1 for r in validated_results if r.selected_part_number not in ["NO_MATCH", "ERROR"]))
        
        return validated_results