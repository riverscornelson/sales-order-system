from typing import Dict, Any, List, Optional
import asyncio
import structlog
from datetime import datetime

from .workflow_state import WorkflowState

logger = structlog.get_logger()

class ReviewPreparationAgent:
    """Agent responsible for preparing order data for human review"""
    
    def __init__(self):
        self.confidence_thresholds = {
            "high": 0.8,
            "medium": 0.6,
            "low": 0.4
        }
    
    async def prepare_for_review(self, workflow_state: WorkflowState) -> Dict[str, Any]:
        """Prepare order data for human review and approval"""
        
        logger.info("Preparing order for review", 
                   session_id=workflow_state.session_id)
        
        try:
            # Compile all data from workflow state
            order_data = self._compile_order_data(workflow_state)
            
            # Generate review summary
            review_summary = self._generate_review_summary(workflow_state)
            
            # Identify items requiring attention
            attention_items = self._identify_attention_items(workflow_state)
            
            # Calculate confidence scores
            confidence_analysis = self._calculate_confidence_analysis(workflow_state)
            
            # Generate recommendations
            recommendations = self._generate_recommendations(workflow_state, confidence_analysis)
            
            # Prepare alternative options
            alternatives = self._prepare_alternatives(workflow_state)
            
            result = {
                "order_data": order_data,
                "review_summary": review_summary,
                "attention_items": attention_items,
                "confidence_analysis": confidence_analysis,
                "recommendations": recommendations,
                "alternatives": alternatives,
                "review_timestamp": datetime.now().isoformat(),
                "agent": "review_preparer"
            }
            
            logger.info("Review preparation completed", 
                       session_id=workflow_state.session_id,
                       confidence=confidence_analysis.get("overall_confidence"),
                       attention_items_count=len(attention_items))
            
            return result
            
        except Exception as e:
            logger.error("Review preparation failed", 
                        session_id=workflow_state.session_id,
                        error=str(e))
            raise Exception(f"Review preparation failed: {str(e)}")
    
    def _compile_order_data(self, workflow_state: WorkflowState) -> Dict[str, Any]:
        """Compile final order data from all workflow stages"""
        
        # Base customer information
        customer_info = workflow_state.extracted_customer_info or {}
        
        # Enhanced with ERP validation
        if workflow_state.customer_validation:
            erp_customer = workflow_state.customer_validation.get("customer_data", {})
            customer_info.update({
                "customer_id": erp_customer.get("id") or erp_customer.get("customer_id"),
                "credit_limit": erp_customer.get("credit_limit"),
                "payment_terms": erp_customer.get("payment_terms"),
                "is_validated": workflow_state.customer_validation.get("valid", False)
            })
        
        # Compile line items with matching and pricing information
        line_items = []
        
        for i, extracted_item in enumerate(workflow_state.extracted_line_items):
            item_id = f"item_{i}"
            
            # Get matches for this item
            item_matches = workflow_state.part_matches.get(item_id, [])
            best_match = item_matches[0] if item_matches else None
            
            # Get inventory and pricing info
            inventory_info = None
            unit_price = None
            
            if best_match:
                part_number = best_match.get("part_number")
                if part_number and workflow_state.inventory_check:
                    inventory_info = workflow_state.inventory_check.get("parts", {}).get(part_number)
                
                if part_number and workflow_state.pricing_info:
                    unit_price = workflow_state.pricing_info.get("pricing", {}).get(part_number)
            
            # Compile line item
            line_item = {
                "line_number": i + 1,
                "original_description": extracted_item.get("description"),
                "extracted_quantity": extracted_item.get("quantity"),
                "extracted_part_number": extracted_item.get("part_number"),
                
                # Matched part information
                "matched_part_number": best_match.get("part_number") if best_match else None,
                "matched_description": best_match.get("description") if best_match else None,
                "match_confidence": best_match.get("scores", {}).get("combined_score", 0) if best_match else 0,
                "match_explanation": best_match.get("match_explanation") if best_match else None,
                
                # Pricing and availability
                "unit_price": unit_price,
                "available_quantity": inventory_info.get("available_quantity") if inventory_info else 0,
                "is_available": inventory_info.get("available", False) if inventory_info else False,
                "lead_time_days": inventory_info.get("lead_time_days") if inventory_info else None,
                
                # Calculated totals
                "line_total": (unit_price * extracted_item.get("quantity", 1)) if unit_price else None,
                
                # Alternative matches
                "alternatives": item_matches[1:4] if len(item_matches) > 1 else [],
                
                # Status flags
                "requires_review": self._item_requires_review(extracted_item, best_match, inventory_info),
                "has_issues": self._item_has_issues(extracted_item, best_match, inventory_info)
            }
            
            line_items.append(line_item)
        
        # Calculate order totals
        order_totals = workflow_state.erp_integration.get("order_totals", {}) if hasattr(workflow_state, 'erp_integration') else {}
        
        order_data = {
            "customer_info": customer_info,
            "line_items": line_items,
            "order_totals": order_totals,
            "document_info": {
                "filename": workflow_state.document_filename,
                "document_type": workflow_state.document_type,
                "processed_at": workflow_state.created_at
            },
            "processing_summary": {
                "total_items": len(line_items),
                "matched_items": len([item for item in line_items if item["matched_part_number"]]),
                "available_items": len([item for item in line_items if item["is_available"]]),
                "items_requiring_review": len([item for item in line_items if item["requires_review"]])
            }
        }
        
        return order_data
    
    def _generate_review_summary(self, workflow_state: WorkflowState) -> Dict[str, Any]:
        """Generate high-level summary for review"""
        
        summary = {
            "processing_status": "completed",
            "customer_status": "unknown",
            "inventory_status": "unknown",
            "pricing_status": "unknown",
            "ready_to_submit": False,
            "key_metrics": {}
        }
        
        # Customer status
        if workflow_state.customer_validation:
            if workflow_state.customer_validation.get("valid"):
                summary["customer_status"] = "validated"
            else:
                summary["customer_status"] = "validation_failed"
        
        # Inventory status
        if workflow_state.inventory_check:
            available_count = workflow_state.inventory_check.get("available_count", 0)
            total_count = workflow_state.inventory_check.get("total_parts_checked", 1)
            
            if available_count == total_count:
                summary["inventory_status"] = "all_available"
            elif available_count > 0:
                summary["inventory_status"] = "partial_available"
            else:
                summary["inventory_status"] = "none_available"
        
        # Pricing status
        if workflow_state.pricing_info:
            pricing_data = workflow_state.pricing_info.get("pricing", {})
            if pricing_data:
                summary["pricing_status"] = "available"
            else:
                summary["pricing_status"] = "unavailable"
        
        # Overall readiness
        summary["ready_to_submit"] = (
            summary["customer_status"] == "validated" and
            summary["inventory_status"] in ["all_available", "partial_available"] and
            summary["pricing_status"] == "available"
        )
        
        # Key metrics
        order_totals = getattr(workflow_state, 'erp_integration', {}).get("order_totals", {})
        summary["key_metrics"] = {
            "total_amount": order_totals.get("total_amount", 0),
            "line_items_count": len(workflow_state.extracted_line_items),
            "processing_time": self._calculate_processing_time(workflow_state),
            "confidence_score": self._calculate_overall_confidence_simple(workflow_state)
        }
        
        return summary
    
    def _identify_attention_items(self, workflow_state: WorkflowState) -> List[Dict[str, Any]]:
        """Identify items that require human attention"""
        
        attention_items = []
        
        # Check customer validation issues
        if workflow_state.customer_validation and not workflow_state.customer_validation.get("valid"):
            attention_items.append({
                "type": "customer_validation",
                "severity": "high",
                "title": "Customer Validation Failed",
                "description": workflow_state.customer_validation.get("error", "Customer could not be validated"),
                "action_required": "Verify customer information or create new customer account"
            })
        
        # Check for low-confidence part matches
        for i, item_matches in workflow_state.part_matches.items():
            if item_matches:
                best_match = item_matches[0]
                confidence = best_match.get("scores", {}).get("combined_score", 0)
                
                if confidence < self.confidence_thresholds["medium"]:
                    line_num = int(i.split("_")[1]) + 1
                    attention_items.append({
                        "type": "low_confidence_match",
                        "severity": "medium",
                        "title": f"Low Confidence Match - Line {line_num}",
                        "description": f"Part match confidence is {confidence:.2f}, below threshold of {self.confidence_thresholds['medium']}",
                        "action_required": "Review and confirm part selection",
                        "line_number": line_num,
                        "original_description": workflow_state.extracted_line_items[int(i.split("_")[1])].get("description")
                    })
        
        # Check for unavailable items
        if workflow_state.inventory_check:
            parts_data = workflow_state.inventory_check.get("parts", {})
            for part_number, part_info in parts_data.items():
                if not part_info.get("available"):
                    attention_items.append({
                        "type": "inventory_unavailable",
                        "severity": "medium",
                        "title": f"Item Unavailable - {part_number}",
                        "description": f"Part {part_number} is not available in inventory",
                        "action_required": "Find alternative part or check lead time",
                        "part_number": part_number
                    })
        
        # Check for business rule violations
        if hasattr(workflow_state, 'business_rules'):
            business_rules = workflow_state.business_rules.get("rules", [])
            for rule in business_rules:
                if rule.get("status") in ["failed", "requires_approval"]:
                    severity = "high" if rule["status"] == "failed" else "medium"
                    attention_items.append({
                        "type": "business_rule_violation",
                        "severity": severity,
                        "title": f"Business Rule: {rule.get('rule', 'Unknown')}",
                        "description": rule.get("message", "Business rule check failed"),
                        "action_required": "Review and address business rule violation"
                    })
        
        # Sort by severity
        severity_order = {"high": 0, "medium": 1, "low": 2}
        attention_items.sort(key=lambda x: severity_order.get(x["severity"], 3))
        
        return attention_items
    
    def _calculate_confidence_analysis(self, workflow_state: WorkflowState) -> Dict[str, Any]:
        """Calculate detailed confidence analysis"""
        
        # Document extraction confidence
        extraction_confidence = 0.8  # Default, could be calculated from extraction agent
        if workflow_state.extracted_customer_info and workflow_state.extracted_line_items:
            extraction_confidence = 0.9
        
        # Part matching confidence
        match_confidences = []
        for item_matches in workflow_state.part_matches.values():
            if item_matches:
                best_match_confidence = item_matches[0].get("scores", {}).get("combined_score", 0)
                match_confidences.append(best_match_confidence)
            else:
                match_confidences.append(0.0)
        
        matching_confidence = sum(match_confidences) / len(match_confidences) if match_confidences else 0.0
        
        # ERP validation confidence
        erp_confidence = 0.5  # Default
        if workflow_state.customer_validation and workflow_state.customer_validation.get("valid"):
            erp_confidence = 0.9
        elif workflow_state.customer_validation:
            erp_confidence = 0.3
        
        # Overall confidence (weighted average)
        overall_confidence = (
            extraction_confidence * 0.3 +
            matching_confidence * 0.4 +
            erp_confidence * 0.3
        )
        
        confidence_level = "high"
        if overall_confidence < self.confidence_thresholds["medium"]:
            confidence_level = "low"
        elif overall_confidence < self.confidence_thresholds["high"]:
            confidence_level = "medium"
        
        return {
            "overall_confidence": round(overall_confidence, 3),
            "confidence_level": confidence_level,
            "component_confidences": {
                "extraction": round(extraction_confidence, 3),
                "matching": round(matching_confidence, 3),
                "erp_validation": round(erp_confidence, 3)
            },
            "match_distribution": {
                "high_confidence": len([c for c in match_confidences if c >= self.confidence_thresholds["high"]]),
                "medium_confidence": len([c for c in match_confidences if self.confidence_thresholds["medium"] <= c < self.confidence_thresholds["high"]]),
                "low_confidence": len([c for c in match_confidences if c < self.confidence_thresholds["medium"]])
            }
        }
    
    def _generate_recommendations(self, workflow_state: WorkflowState, 
                                confidence_analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate actionable recommendations"""
        
        recommendations = []
        
        overall_confidence = confidence_analysis.get("overall_confidence", 0)
        
        # High confidence - ready to proceed
        if overall_confidence >= self.confidence_thresholds["high"]:
            recommendations.append({
                "type": "proceed",
                "priority": "high",
                "title": "Ready to Submit",
                "description": "Order processing completed with high confidence. Ready for submission to ERP.",
                "action": "submit_order"
            })
        
        # Medium confidence - review recommended
        elif overall_confidence >= self.confidence_thresholds["medium"]:
            recommendations.append({
                "type": "review",
                "priority": "medium",
                "title": "Review Recommended",
                "description": "Order processing completed with medium confidence. Quick review recommended before submission.",
                "action": "review_and_submit"
            })
        
        # Low confidence - detailed review required
        else:
            recommendations.append({
                "type": "detailed_review",
                "priority": "high",
                "title": "Detailed Review Required",
                "description": "Order processing completed with low confidence. Detailed review and corrections needed.",
                "action": "detailed_review"
            })
        
        # Specific recommendations based on issues
        match_distribution = confidence_analysis.get("match_distribution", {})
        
        if match_distribution.get("low_confidence", 0) > 0:
            recommendations.append({
                "type": "part_verification",
                "priority": "medium",
                "title": "Verify Part Matches",
                "description": f"{match_distribution['low_confidence']} part matches have low confidence and should be verified.",
                "action": "verify_parts"
            })
        
        if workflow_state.inventory_check and workflow_state.inventory_check.get("unavailable_count", 0) > 0:
            recommendations.append({
                "type": "inventory_alternatives",
                "priority": "medium",
                "title": "Find Alternative Parts",
                "description": f"{workflow_state.inventory_check['unavailable_count']} parts are unavailable. Consider alternatives or check lead times.",
                "action": "find_alternatives"
            })
        
        return recommendations
    
    def _prepare_alternatives(self, workflow_state: WorkflowState) -> Dict[str, Any]:
        """Prepare alternative options for problematic items"""
        
        alternatives = {
            "part_alternatives": {},
            "pricing_options": {},
            "delivery_options": {}
        }
        
        # Part alternatives for low-confidence matches
        for item_id, item_matches in workflow_state.part_matches.items():
            if item_matches and len(item_matches) > 1:
                best_match = item_matches[0]
                if best_match.get("scores", {}).get("combined_score", 0) < self.confidence_thresholds["high"]:
                    alternatives["part_alternatives"][item_id] = {
                        "primary": best_match,
                        "alternatives": item_matches[1:4],  # Top 3 alternatives
                        "recommendation": "Consider alternatives for better match"
                    }
        
        return alternatives
    
    def _item_requires_review(self, extracted_item: Dict[str, Any], 
                            best_match: Optional[Dict[str, Any]], 
                            inventory_info: Optional[Dict[str, Any]]) -> bool:
        """Determine if an item requires human review"""
        
        # No match found
        if not best_match:
            return True
        
        # Low confidence match
        confidence = best_match.get("scores", {}).get("combined_score", 0)
        if confidence < self.confidence_thresholds["medium"]:
            return True
        
        # Not available in inventory
        if inventory_info and not inventory_info.get("available", False):
            return True
        
        # Large quantity without explicit part number
        if extracted_item.get("quantity", 1) > 100 and not extracted_item.get("part_number"):
            return True
        
        return False
    
    def _item_has_issues(self, extracted_item: Dict[str, Any], 
                        best_match: Optional[Dict[str, Any]], 
                        inventory_info: Optional[Dict[str, Any]]) -> bool:
        """Determine if an item has issues that prevent processing"""
        
        # No match at all
        if not best_match:
            return True
        
        # Very low confidence
        confidence = best_match.get("scores", {}).get("combined_score", 0)
        if confidence < self.confidence_thresholds["low"]:
            return True
        
        # Not available and no lead time info
        if inventory_info and not inventory_info.get("available", False) and not inventory_info.get("lead_time_days"):
            return True
        
        return False
    
    def _calculate_processing_time(self, workflow_state: WorkflowState) -> float:
        """Calculate total processing time in seconds"""
        
        if workflow_state.created_at and workflow_state.updated_at:
            created = datetime.fromisoformat(workflow_state.created_at.replace('Z', '+00:00'))
            updated = datetime.fromisoformat(workflow_state.updated_at.replace('Z', '+00:00'))
            return (updated - created).total_seconds()
        
        return 0.0
    
    def _calculate_overall_confidence_simple(self, workflow_state: WorkflowState) -> float:
        """Simple overall confidence calculation"""
        
        # Count successful components
        components = 0
        successful = 0
        
        # Document extraction
        components += 1
        if workflow_state.extracted_line_items:
            successful += 1
        
        # Customer validation
        components += 1
        if workflow_state.customer_validation and workflow_state.customer_validation.get("valid"):
            successful += 1
        
        # Part matching
        components += 1
        if workflow_state.part_matches:
            successful += 1
        
        # Inventory check
        components += 1
        if workflow_state.inventory_check and workflow_state.inventory_check.get("available_count", 0) > 0:
            successful += 1
        
        return successful / components if components > 0 else 0.0