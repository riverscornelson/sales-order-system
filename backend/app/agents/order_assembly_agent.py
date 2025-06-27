import json
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime
import structlog
from langchain_openai import ChatOpenAI

from ..models.line_item_schemas import (
    EnhancedOrder, LineItem, MatchSelection, AssembledOrder, 
    LineItemStatus, MatchConfidence
)

logger = structlog.get_logger()

class OrderAssemblyAgent:
    """Agent responsible for combining all processed line items into a final order"""
    
    def __init__(self, llm: Optional[ChatOpenAI] = None):
        self.llm = llm
    
    async def assemble_order(self, enhanced_order: EnhancedOrder, 
                           line_item_matches: Dict[str, MatchSelection]) -> AssembledOrder:
        """Assemble final order from processed line items"""
        
        logger.info("Starting order assembly",
                   order_id=enhanced_order.order_id,
                   total_line_items=len(enhanced_order.line_items))
        
        try:
            # Process each line item with its match
            assembled_line_items = []
            issues_requiring_review = []
            
            for line_item in enhanced_order.line_items:
                match_selection = line_item_matches.get(line_item.line_id)
                
                if match_selection:
                    assembled_item, issues = self._process_line_item_match(
                        line_item, match_selection
                    )
                    assembled_line_items.append(assembled_item)
                    issues_requiring_review.extend(issues)
                else:
                    # Line item wasn't processed - create issue
                    issue = self._create_processing_issue(line_item)
                    issues_requiring_review.append(issue)
            
            # Calculate totals
            totals = self._calculate_order_totals(assembled_line_items)
            
            # Generate order summary
            order_summary = self._create_order_summary(
                enhanced_order, assembled_line_items, issues_requiring_review
            )
            
            # Determine next steps
            next_steps = self._determine_next_steps(
                assembled_line_items, issues_requiring_review
            )
            
            # Calculate overall confidence
            confidence_score = self._calculate_overall_confidence(assembled_line_items)
            
            # Create assembled order
            assembled_order = AssembledOrder(
                order_summary=order_summary,
                line_items=assembled_line_items,
                issues_requiring_review=issues_requiring_review,
                totals=totals,
                next_steps=next_steps,
                approval_required=len(issues_requiring_review) > 0,
                confidence_score=confidence_score
            )
            
            # Use AI to enhance the assembly if available
            if self.llm:
                assembled_order = await self._ai_enhance_assembly(
                    enhanced_order, assembled_order
                )
            
            logger.info("Order assembly completed",
                       order_id=enhanced_order.order_id,
                       total_items=len(assembled_line_items),
                       issues=len(issues_requiring_review),
                       approval_required=assembled_order.approval_required)
            
            return assembled_order
            
        except Exception as e:
            logger.error("Order assembly failed",
                        order_id=enhanced_order.order_id,
                        error=str(e))
            raise
    
    def _process_line_item_match(self, line_item: LineItem, 
                               match_selection: MatchSelection) -> tuple:
        """Process a single line item with its match selection"""
        
        issues = []
        
        # Create assembled line item
        assembled_item = {
            "line_id": line_item.line_id,
            "project": line_item.project,
            "original_request": line_item.raw_text,
            "extracted_specifications": line_item.extracted_specs.dict() if line_item.extracted_specs else {},
            "urgency": line_item.urgency,
            "special_requirements": line_item.special_requirements or []
        }
        
        # Handle different match outcomes
        if match_selection.selected_part_number == "NO_MATCH":
            assembled_item["status"] = "no_match_found"
            assembled_item["match_result"] = {
                "outcome": "no_suitable_match",
                "reasoning": match_selection.reasoning,
                "recommendations": match_selection.selection_metadata.get("recommendations", [])
            }
            
            # Create issue for manual review
            issues.append({
                "line_id": line_item.line_id,
                "issue_type": "no_suitable_match",
                "description": f"No suitable parts found for: {line_item.raw_text[:100]}...",
                "reasoning": match_selection.reasoning,
                "suggestions": match_selection.selection_metadata.get("recommendations", []),
                "priority": "high" if line_item.urgency == "HIGH" else "medium"
            })
            
        elif match_selection.selected_part_number == "ERROR":
            assembled_item["status"] = "processing_error"
            assembled_item["match_result"] = {
                "outcome": "processing_error",
                "error": match_selection.reasoning
            }
            
            # Create issue for technical error
            issues.append({
                "line_id": line_item.line_id,
                "issue_type": "processing_error",
                "description": f"Technical error processing: {line_item.raw_text[:100]}...",
                "error_details": match_selection.reasoning,
                "priority": "high"
            })
            
        else:
            # Successful match
            assembled_item["status"] = "matched"
            assembled_item["matched_part"] = self._create_matched_part_info(match_selection)
            assembled_item["match_confidence"] = match_selection.confidence
            assembled_item["match_reasoning"] = match_selection.reasoning
            
            # Check if requires approval
            if match_selection.requires_approval or match_selection.concerns:
                assembled_item["requires_approval"] = True
                
                issues.append({
                    "line_id": line_item.line_id,
                    "issue_type": "requires_approval",
                    "description": f"Match found but requires approval: {match_selection.selected_part_number}",
                    "concerns": match_selection.concerns,
                    "alternatives": match_selection.alternatives,
                    "confidence": match_selection.confidence,
                    "priority": "medium"
                })
        
        return assembled_item, issues
    
    def _create_matched_part_info(self, match_selection: MatchSelection) -> Dict[str, Any]:
        """Create matched part information from selection"""
        
        # This would typically fetch additional part details from catalog
        # For now, we'll use the information available in the match selection
        
        matched_part = {
            "part_number": match_selection.selected_part_number,
            "confidence": match_selection.confidence,
            "match_score": match_selection.match_score,
            "selection_reasoning": match_selection.reasoning,
            "concerns": match_selection.concerns,
            "alternatives": match_selection.alternatives
        }
        
        # Add metadata if available
        if match_selection.selection_metadata:
            matched_part.update({
                "specification_analysis": match_selection.selection_metadata.get("specification_analysis", {}),
                "risk_assessment": match_selection.selection_metadata.get("risk_assessment", {}),
                "recommendations": match_selection.selection_metadata.get("recommendations", [])
            })
        
        return matched_part
    
    def _create_processing_issue(self, line_item: LineItem) -> Dict[str, Any]:
        """Create an issue for unprocessed line item"""
        
        return {
            "line_id": line_item.line_id,
            "issue_type": "not_processed",
            "description": f"Line item was not processed: {line_item.raw_text[:100]}...",
            "original_text": line_item.raw_text,
            "priority": "high"
        }
    
    def _calculate_order_totals(self, assembled_line_items: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate order totals from assembled line items"""
        
        totals = {
            "total_line_items": len(assembled_line_items),
            "matched_items": 0,
            "pending_approval": 0,
            "no_match_items": 0,
            "error_items": 0,
            "estimated_total_value": 0.0,
            "currency": "USD"
        }
        
        for item in assembled_line_items:
            status = item.get("status", "unknown")
            
            if status == "matched":
                totals["matched_items"] += 1
                
                if item.get("requires_approval"):
                    totals["pending_approval"] += 1
                
                # Add to total value if price information available
                matched_part = item.get("matched_part", {})
                unit_price = matched_part.get("unit_price")
                quantity = 1  # Default quantity
                
                # Try to get quantity from original specs
                if item.get("extracted_specifications", {}).get("quantity"):
                    quantity = item["extracted_specifications"]["quantity"]
                
                if unit_price and isinstance(unit_price, (int, float)):
                    totals["estimated_total_value"] += unit_price * quantity
                    
            elif status == "no_match_found":
                totals["no_match_items"] += 1
            elif status == "processing_error":
                totals["error_items"] += 1
        
        # Round monetary values
        totals["estimated_total_value"] = round(totals["estimated_total_value"], 2)
        
        return totals
    
    def _create_order_summary(self, enhanced_order: EnhancedOrder,
                            assembled_line_items: List[Dict[str, Any]],
                            issues: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Create order summary information"""
        
        return {
            "order_id": enhanced_order.order_id,
            "customer": enhanced_order.order_metadata.customer,
            "contact_person": enhanced_order.order_metadata.contact_person,
            "po_number": enhanced_order.order_metadata.po_number,
            "priority": enhanced_order.order_metadata.priority,
            "projects": enhanced_order.order_metadata.projects or [],
            "delivery_date": enhanced_order.order_metadata.delivery_date,
            "processing_completed_at": datetime.now().isoformat(),
            "total_line_items": len(assembled_line_items),
            "successful_matches": sum(1 for item in assembled_line_items if item.get("status") == "matched"),
            "items_requiring_review": len(issues),
            "overall_status": "ready_for_review" if issues else "ready_for_processing"
        }
    
    def _determine_next_steps(self, assembled_line_items: List[Dict[str, Any]],
                            issues: List[Dict[str, Any]]) -> List[str]:
        """Determine recommended next steps based on assembly results"""
        
        next_steps = []
        
        # Count different types of issues
        high_priority_issues = sum(1 for issue in issues if issue.get("priority") == "high")
        approval_required = sum(1 for item in assembled_line_items if item.get("requires_approval"))
        no_matches = sum(1 for item in assembled_line_items if item.get("status") == "no_match_found")
        
        if high_priority_issues > 0:
            next_steps.append(f"Address {high_priority_issues} high-priority issues requiring immediate attention")
        
        if no_matches > 0:
            next_steps.append(f"Review {no_matches} line items with no suitable matches - consider alternatives or custom sourcing")
        
        if approval_required > 0:
            next_steps.append(f"Obtain approval for {approval_required} matched items with concerns")
        
        # Determine processing path
        if not issues:
            next_steps.extend([
                "Validate pricing and availability with suppliers",
                "Submit to ERP system for inventory check", 
                "Prepare final quote for customer approval"
            ])
        elif len(issues) <= 2:
            next_steps.extend([
                "Resolve outstanding issues",
                "Reprocess problematic line items",
                "Proceed with ERP validation for approved items"
            ])
        else:
            next_steps.extend([
                "Comprehensive manual review required",
                "Contact customer for specification clarification",
                "Consider splitting order into multiple phases"
            ])
        
        return next_steps
    
    def _calculate_overall_confidence(self, assembled_line_items: List[Dict[str, Any]]) -> float:
        """Calculate overall confidence score for the order"""
        
        if not assembled_line_items:
            return 0.0
        
        total_score = 0.0
        scored_items = 0
        
        for item in assembled_line_items:
            if item.get("status") == "matched":
                match_score = item.get("matched_part", {}).get("match_score", 0.0)
                
                # Reduce score if requires approval
                if item.get("requires_approval"):
                    match_score *= 0.8
                
                total_score += match_score
                scored_items += 1
        
        # Items with no match or errors get 0 score
        # Overall confidence is average of all items
        overall_confidence = total_score / len(assembled_line_items) if assembled_line_items else 0.0
        
        return round(overall_confidence, 3)
    
    async def _ai_enhance_assembly(self, enhanced_order: EnhancedOrder,
                                 assembled_order: AssembledOrder) -> AssembledOrder:
        """Use AI to enhance the assembled order with insights"""
        
        try:
            enhancement_prompt = f"""
            Review this assembled sales order and provide insights and recommendations:
            
            ORIGINAL ORDER:
            Customer: {enhanced_order.order_metadata.customer}
            Priority: {enhanced_order.order_metadata.priority}
            Projects: {enhanced_order.order_metadata.projects}
            
            ASSEMBLY RESULTS:
            {json.dumps(assembled_order.order_summary, indent=2)}
            
            ISSUES:
            {json.dumps(assembled_order.issues_requiring_review, indent=2)}
            
            Provide enhanced insights:
            1. Risk analysis for this order
            2. Recommendations for issue resolution
            3. Suggested customer communication points
            4. Process optimization suggestions
            
            Return as JSON:
            {{
                "risk_analysis": {{
                    "delivery_risk": "assessment",
                    "pricing_risk": "assessment", 
                    "technical_risk": "assessment"
                }},
                "recommendations": ["rec1", "rec2"],
                "customer_communication": ["point1", "point2"],
                "process_insights": ["insight1", "insight2"]
            }}
            """
            
            response = await asyncio.to_thread(self.llm.invoke, enhancement_prompt)
            ai_insights = json.loads(response.content)
            
            # Add AI insights to the assembled order
            assembled_order.order_summary["ai_insights"] = ai_insights
            
            logger.info("AI enhancement completed", 
                       order_id=enhanced_order.order_id)
            
        except Exception as e:
            logger.warning("AI enhancement failed", 
                          order_id=enhanced_order.order_id,
                          error=str(e))
        
        return assembled_order