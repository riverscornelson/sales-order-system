"""
Quality Gates System for Sales Order Processing
Validates processing quality at each stage with configurable thresholds
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum
import re
import structlog

from ..models.line_item_schemas import MatchConfidence

logger = structlog.get_logger()


class QualityThreshold(str, Enum):
    """Quality threshold levels"""
    STRICT = "strict"      # 0.9+
    STANDARD = "standard"  # 0.8+
    LENIENT = "lenient"    # 0.7+
    PERMISSIVE = "permissive"  # 0.6+


@dataclass
class QualityGateResult:
    """Result of a quality gate validation"""
    passed: bool
    score: float
    threshold: float
    stage: str
    issues: List[str]
    warnings: List[str]
    recommendations: List[str]
    confidence: MatchConfidence
    
    def __post_init__(self):
        """Determine confidence level based on score"""
        if self.score >= 0.9:
            self.confidence = MatchConfidence.HIGH
        elif self.score >= 0.8:
            self.confidence = MatchConfidence.MEDIUM_HIGH
        elif self.score >= 0.7:
            self.confidence = MatchConfidence.MEDIUM
        elif self.score >= 0.6:
            self.confidence = MatchConfidence.MEDIUM_LOW
        else:
            self.confidence = MatchConfidence.LOW


class QualityGateManager:
    """
    Manages quality gates for each processing stage
    """
    
    def __init__(self, threshold_level: QualityThreshold = QualityThreshold.STANDARD):
        self.threshold_level = threshold_level
        self.thresholds = self._get_thresholds(threshold_level)
        self.validation_rules = self._initialize_validation_rules()
    
    def _get_thresholds(self, level: QualityThreshold) -> Dict[str, float]:
        """Get quality thresholds for different stages"""
        threshold_map = {
            QualityThreshold.STRICT: {
                "extraction": 0.9,
                "search": 0.85,
                "matching": 0.9,
                "validation": 0.95
            },
            QualityThreshold.STANDARD: {
                "extraction": 0.8,
                "search": 0.75,
                "matching": 0.8,
                "validation": 0.85
            },
            QualityThreshold.LENIENT: {
                "extraction": 0.7,
                "search": 0.65,
                "matching": 0.7,
                "validation": 0.75
            },
            QualityThreshold.PERMISSIVE: {
                "extraction": 0.6,
                "search": 0.55,
                "matching": 0.6,
                "validation": 0.65
            }
        }
        return threshold_map[level]
    
    def _initialize_validation_rules(self) -> Dict[str, Any]:
        """Initialize validation rules for each stage"""
        return {
            "extraction": {
                "required_fields": ["description", "quantity"],
                "optional_fields": ["material", "dimensions", "specifications"],
                "min_description_length": 10,
                "max_description_length": 500,
                "quantity_range": (1, 10000)
            },
            "search": {
                "min_results": 1,
                "max_results": 50,
                "min_similarity_score": 0.3,
                "diversity_threshold": 0.8  # Ensure results aren't too similar
            },
            "matching": {
                "min_match_confidence": 0.6,
                "require_price_info": False,
                "require_availability_info": False,
                "max_price_variance": 0.5  # 50% variance from average
            }
        }
    
    def validate_extraction(self, extraction_result: Dict[str, Any]) -> QualityGateResult:
        """Validate extraction quality"""
        logger.debug("Validating extraction quality")
        
        issues = []
        warnings = []
        recommendations = []
        score_components = []
        
        rules = self.validation_rules["extraction"]
        
        # Check required fields
        required_score = self._check_required_fields(
            extraction_result, rules["required_fields"], issues
        )
        score_components.append(("required_fields", required_score, 0.4))
        
        # Check description quality
        description_score = self._check_description_quality(
            extraction_result.get("description", ""), rules, issues, warnings
        )
        score_components.append(("description_quality", description_score, 0.3))
        
        # Check quantity validity
        quantity_score = self._check_quantity_validity(
            extraction_result.get("quantity"), rules, issues, warnings
        )
        score_components.append(("quantity_validity", quantity_score, 0.2))
        
        # Check specifications completeness
        specs_score = self._check_specifications_completeness(
            extraction_result.get("specs", {}), issues, recommendations
        )
        score_components.append(("specifications", specs_score, 0.1))
        
        # Calculate weighted score
        total_score = sum(score * weight for _, score, weight in score_components)
        threshold = self.thresholds["extraction"]
        
        return QualityGateResult(
            passed=total_score >= threshold,
            score=total_score,
            threshold=threshold,
            stage="extraction",
            issues=issues,
            warnings=warnings,
            recommendations=recommendations,
            confidence=MatchConfidence.MEDIUM  # Will be updated in __post_init__
        )
    
    def validate_search_results(self, search_result: Dict[str, Any]) -> QualityGateResult:
        """Validate search results quality"""
        logger.debug("Validating search results quality")
        
        issues = []
        warnings = []
        recommendations = []
        score_components = []
        
        rules = self.validation_rules["search"]
        matches = search_result.get("matches", [])
        
        # Check number of results
        results_score = self._check_results_count(matches, rules, issues, warnings)
        score_components.append(("results_count", results_score, 0.3))
        
        # Check similarity scores
        similarity_score = self._check_similarity_scores(matches, rules, issues, warnings)
        score_components.append(("similarity_quality", similarity_score, 0.4))
        
        # Check result diversity
        diversity_score = self._check_result_diversity(matches, rules, warnings, recommendations)
        score_components.append(("diversity", diversity_score, 0.2))
        
        # Check metadata completeness
        metadata_score = self._check_search_metadata(matches, issues, recommendations)
        score_components.append(("metadata", metadata_score, 0.1))
        
        # Calculate weighted score
        total_score = sum(score * weight for _, score, weight in score_components)
        threshold = self.thresholds["search"]
        
        return QualityGateResult(
            passed=total_score >= threshold,
            score=total_score,
            threshold=threshold,
            stage="search",
            issues=issues,
            warnings=warnings,
            recommendations=recommendations,
            confidence=MatchConfidence.MEDIUM
        )
    
    def validate_match_selection(self, match_result: Dict[str, Any]) -> QualityGateResult:
        """Validate match selection quality"""
        logger.debug("Validating match selection quality")
        
        issues = []
        warnings = []
        recommendations = []
        score_components = []
        
        rules = self.validation_rules["matching"]
        selected_match = match_result.get("selected_match", {})
        
        # Check match confidence
        confidence_score = self._check_match_confidence(selected_match, rules, issues)
        score_components.append(("match_confidence", confidence_score, 0.4))
        
        # Check business data completeness
        business_score = self._check_business_data(selected_match, rules, warnings, recommendations)
        score_components.append(("business_data", business_score, 0.3))
        
        # Check selection reasoning
        reasoning_score = self._check_selection_reasoning(match_result, issues, recommendations)
        score_components.append(("reasoning", reasoning_score, 0.2))
        
        # Check price reasonableness
        price_score = self._check_price_reasonableness(selected_match, rules, warnings)
        score_components.append(("price_check", price_score, 0.1))
        
        # Calculate weighted score
        total_score = sum(score * weight for _, score, weight in score_components)
        threshold = self.thresholds["matching"]
        
        return QualityGateResult(
            passed=total_score >= threshold,
            score=total_score,
            threshold=threshold,
            stage="matching",
            issues=issues,
            warnings=warnings,
            recommendations=recommendations,
            confidence=MatchConfidence.MEDIUM
        )
    
    # Phase 1: Contextual Intelligence Enhancement
    def validate_with_context(self, stage: str, data: Dict[str, Any], 
                             contextual_insights: Optional[Dict[str, Any]] = None) -> QualityGateResult:
        """
        Enhanced validation that considers contextual intelligence
        Adjusts validation criteria based on business context and complexity
        """
        logger.debug(f"Running context-aware validation for stage: {stage}")
        
        # Apply contextual adjustments
        if contextual_insights:
            self._apply_contextual_adjustments(stage, contextual_insights)
        
        # Run standard validation based on stage
        if stage == "extraction":
            result = self.validate_extraction(data)
        elif stage == "search":
            result = self.validate_search_results(data)
        elif stage == "matching":
            result = self.validate_match_selection(data)
        else:
            # Generic validation
            result = self._generic_validation(stage, data)
        
        # Enhance result with contextual information
        if contextual_insights:
            result = self._enhance_result_with_context(result, contextual_insights)
        
        return result
    
    def _apply_contextual_adjustments(self, stage: str, insights: Dict[str, Any]):
        """Apply contextual adjustments to validation thresholds"""
        
        complexity = insights.get('overall_complexity', 'simple')
        business_context = insights.get('primary_business_context', 'routine')
        urgency = insights.get('urgency_level', 'medium')
        
        # Store original thresholds for restoration
        if not hasattr(self, '_original_thresholds'):
            self._original_thresholds = self.thresholds.copy()
        
        # Adjust thresholds based on context
        adjustment_factor = 1.0
        
        # Business context adjustments
        if business_context == 'production_down':
            adjustment_factor *= 0.8  # Lower thresholds for emergency
            logger.info("Applied production emergency threshold adjustment")
        elif business_context == 'emergency':
            adjustment_factor *= 0.85  # Slightly lower for emergencies
            logger.info("Applied emergency threshold adjustment")
        
        # Complexity adjustments
        if complexity == 'critical':
            adjustment_factor *= 0.9  # Lower thresholds for critical complexity
            logger.info("Applied critical complexity threshold adjustment")
        elif complexity == 'complex':
            adjustment_factor *= 0.95  # Slightly lower for complex items
            logger.info("Applied complex item threshold adjustment")
        
        # Urgency adjustments
        if urgency == 'critical':
            adjustment_factor *= 0.85  # Lower thresholds for critical urgency
            logger.info("Applied critical urgency threshold adjustment")
        elif urgency == 'high':
            adjustment_factor *= 0.9  # Slightly lower for high urgency
            logger.info("Applied high urgency threshold adjustment")
        
        # Apply adjustments
        if stage in self.thresholds:
            original_threshold = self._original_thresholds[stage]
            adjusted_threshold = original_threshold * adjustment_factor
            self.thresholds[stage] = max(adjusted_threshold, 0.5)  # Minimum threshold
            
            logger.info(f"Contextual adjustment for {stage}: {original_threshold:.3f} → {self.thresholds[stage]:.3f}")
    
    def _enhance_result_with_context(self, result: QualityGateResult, insights: Dict[str, Any]) -> QualityGateResult:
        """Enhance validation result with contextual information"""
        
        # Add contextual recommendations
        complexity = insights.get('overall_complexity', 'simple')
        business_context = insights.get('primary_business_context', 'routine')
        
        contextual_recommendations = []
        
        if business_context == 'production_down':
            contextual_recommendations.append("Production emergency: Prioritize speed and availability over perfect matches")
            contextual_recommendations.append("Consider expedited sourcing options")
        elif business_context == 'emergency':
            contextual_recommendations.append("Emergency context: Balance speed with quality requirements")
        
        if complexity == 'critical':
            contextual_recommendations.append("Critical complexity detected: Enhanced validation may be needed")
            contextual_recommendations.append("Consider expert review for this item")
        elif complexity == 'complex':
            contextual_recommendations.append("Complex item: Verify technical specifications carefully")
        
        # Add contextual warnings
        contextual_warnings = []
        
        if result.score < result.threshold and business_context in ['production_down', 'emergency']:
            contextual_warnings.append(f"Quality below standard but acceptable for {business_context} context")
        
        # Create enhanced result
        enhanced_result = QualityGateResult(
            passed=result.passed,
            score=result.score,
            threshold=result.threshold,
            stage=result.stage,
            issues=result.issues,
            warnings=result.warnings + contextual_warnings,
            recommendations=result.recommendations + contextual_recommendations,
            confidence=result.confidence
        )
        
        return enhanced_result
    
    def _generic_validation(self, stage: str, data: Dict[str, Any]) -> QualityGateResult:
        """Generic validation for unknown stages"""
        return QualityGateResult(
            passed=True,
            score=0.8,
            threshold=self.thresholds.get(stage, 0.8),
            stage=stage,
            issues=[],
            warnings=[],
            recommendations=[],
            confidence=MatchConfidence.MEDIUM
        )
    
    def restore_original_thresholds(self):
        """Restore original thresholds after contextual adjustments"""
        if hasattr(self, '_original_thresholds'):
            self.thresholds = self._original_thresholds.copy()
            logger.debug("Restored original quality thresholds")

    # Helper methods for validation checks
    
    def _check_required_fields(self, data: Dict[str, Any], required: List[str], issues: List[str]) -> float:
        """Check if required fields are present and valid"""
        present_fields = 0
        for field in required:
            value = data.get(field)
            if value is not None and str(value).strip():
                present_fields += 1
            else:
                issues.append(f"Missing or empty required field: {field}")
        
        return present_fields / len(required) if required else 1.0
    
    def _check_description_quality(self, description: str, rules: Dict[str, Any], 
                                 issues: List[str], warnings: List[str]) -> float:
        """Check description quality"""
        if not description:
            issues.append("Empty description")
            return 0.0
        
        score = 0.0
        
        # Length check
        min_len = rules.get("min_description_length", 10)
        max_len = rules.get("max_description_length", 500)
        
        if len(description) < min_len:
            issues.append(f"Description too short (minimum {min_len} characters)")
        elif len(description) > max_len:
            warnings.append(f"Description very long (maximum {max_len} characters)")
            score += 0.5
        else:
            score += 0.7
        
        # Content quality indicators
        if re.search(r'\d+', description):  # Contains numbers
            score += 0.1
        if re.search(r'[a-zA-Z]{3,}', description):  # Contains words
            score += 0.1
        if any(keyword in description.lower() for keyword in ['steel', 'aluminum', 'plastic', 'metal']):
            score += 0.1
        
        return min(score, 1.0)
    
    def _check_quantity_validity(self, quantity: Any, rules: Dict[str, Any], 
                               issues: List[str], warnings: List[str]) -> float:
        """Check quantity validity"""
        if quantity is None:
            issues.append("Missing quantity")
            return 0.0
        
        try:
            qty = float(quantity)
            min_qty, max_qty = rules.get("quantity_range", (1, 10000))
            
            if qty <= 0:
                issues.append("Quantity must be positive")
                return 0.0
            elif qty < min_qty:
                warnings.append(f"Quantity seems low: {qty}")
                return 0.7
            elif qty > max_qty:
                warnings.append(f"Quantity seems high: {qty}")
                return 0.8
            else:
                return 1.0
                
        except (ValueError, TypeError):
            issues.append("Invalid quantity format")
            return 0.0
    
    def _check_specifications_completeness(self, specs: Dict[str, Any], 
                                         issues: List[str], recommendations: List[str]) -> float:
        """Check specifications completeness"""
        if not specs:
            recommendations.append("Consider extracting material and dimension specifications")
            return 0.5
        
        score = 0.0
        spec_count = 0
        
        important_specs = ['material_grade', 'dimensions', 'form', 'surface_finish']
        
        for spec in important_specs:
            if spec in specs and specs[spec]:
                spec_count += 1
        
        score = spec_count / len(important_specs)
        
        if score < 0.5:
            recommendations.append("Try to extract more specific material and dimension information")
        
        return score
    
    def _check_results_count(self, matches: List[Dict[str, Any]], rules: Dict[str, Any], 
                           issues: List[str], warnings: List[str]) -> float:
        """Check if we have appropriate number of search results"""
        count = len(matches)
        min_results = rules.get("min_results", 1)
        max_results = rules.get("max_results", 50)
        
        if count < min_results:
            issues.append(f"Too few search results: {count} (minimum {min_results})")
            return 0.0
        elif count > max_results:
            warnings.append(f"Many search results: {count} (maximum {max_results})")
            return 0.8
        elif count < 3:
            warnings.append("Few search results, consider broadening search criteria")
            return 0.7
        else:
            return 1.0
    
    def _check_similarity_scores(self, matches: List[Dict[str, Any]], rules: Dict[str, Any], 
                               issues: List[str], warnings: List[str]) -> float:
        """Check similarity score quality"""
        if not matches:
            return 0.0
        
        scores = [match.get("similarity_score", 0) for match in matches]
        min_score = rules.get("min_similarity_score", 0.3)
        
        # Check if best match meets minimum threshold
        best_score = max(scores) if scores else 0
        if best_score < min_score:
            issues.append(f"Best similarity score too low: {best_score:.3f} (minimum {min_score})")
            return 0.0
        
        # Check overall quality of matches
        avg_score = sum(scores) / len(scores)
        if avg_score < 0.5:
            warnings.append(f"Average similarity scores are low: {avg_score:.3f}")
            return 0.6
        
        return min(best_score, 1.0)
    
    def _check_result_diversity(self, matches: List[Dict[str, Any]], rules: Dict[str, Any], 
                              warnings: List[str], recommendations: List[str]) -> float:
        """Check diversity of search results"""
        if len(matches) <= 1:
            return 1.0
        
        # Simple diversity check based on part numbers
        part_numbers = [match.get("part_number", "") for match in matches]
        unique_prefixes = set()
        
        for pn in part_numbers:
            if len(pn) >= 4:
                unique_prefixes.add(pn[:4])
        
        diversity_ratio = len(unique_prefixes) / len(matches)
        threshold = rules.get("diversity_threshold", 0.8)
        
        if diversity_ratio < 0.3:
            warnings.append("Search results may be too similar")
            recommendations.append("Consider using different search strategies")
            return 0.6
        
        return min(diversity_ratio / threshold, 1.0)
    
    def _check_search_metadata(self, matches: List[Dict[str, Any]], 
                             issues: List[str], recommendations: List[str]) -> float:
        """Check completeness of search result metadata"""
        if not matches:
            return 0.0
        
        metadata_score = 0.0
        required_fields = ["part_number", "description"]
        optional_fields = ["price", "availability", "supplier"]
        
        for match in matches:
            match_score = 0.0
            
            # Required fields
            for field in required_fields:
                if field in match and match[field]:
                    match_score += 0.4
            
            # Optional fields
            for field in optional_fields:
                if field in match and match[field]:
                    match_score += 0.2
            
            metadata_score += min(match_score, 1.0)
        
        avg_metadata_score = metadata_score / len(matches)
        
        if avg_metadata_score < 0.6:
            recommendations.append("Search results missing some metadata (price, availability)")
        
        return avg_metadata_score
    
    def _check_match_confidence(self, selected_match: Dict[str, Any], rules: Dict[str, Any], 
                               issues: List[str]) -> float:
        """Check match confidence level"""
        confidence = selected_match.get("confidence_score", 0)
        min_confidence = rules.get("min_match_confidence", 0.6)
        
        if confidence < min_confidence:
            issues.append(f"Match confidence too low: {confidence:.3f} (minimum {min_confidence})")
            return 0.0
        
        return min(confidence, 1.0)
    
    def _check_business_data(self, selected_match: Dict[str, Any], rules: Dict[str, Any], 
                           warnings: List[str], recommendations: List[str]) -> float:
        """Check business data completeness"""
        score = 0.0
        
        # Check price information
        if "price" in selected_match and selected_match["price"]:
            score += 0.4
        elif rules.get("require_price_info", False):
            warnings.append("Selected match missing price information")
        else:
            score += 0.2
        
        # Check availability information
        if "availability" in selected_match and selected_match["availability"]:
            score += 0.4
        elif rules.get("require_availability_info", False):
            warnings.append("Selected match missing availability information")
        else:
            score += 0.2
        
        # Check supplier information
        if "supplier" in selected_match and selected_match["supplier"]:
            score += 0.2
        else:
            recommendations.append("Consider including supplier information")
        
        return score
    
    def _check_selection_reasoning(self, match_result: Dict[str, Any], 
                                 issues: List[str], recommendations: List[str]) -> float:
        """Check quality of selection reasoning"""
        reasoning = match_result.get("reasoning", "")
        
        if not reasoning:
            issues.append("Missing selection reasoning")
            return 0.0
        
        score = 0.5  # Base score for having reasoning
        
        # Check for quality indicators in reasoning
        reasoning_lower = reasoning.lower()
        
        if any(keyword in reasoning_lower for keyword in ['confidence', 'similarity', 'match']):
            score += 0.2
        
        if any(keyword in reasoning_lower for keyword in ['price', 'cost', 'availability']):
            score += 0.2
        
        if len(reasoning) > 50:  # Detailed reasoning
            score += 0.1
        
        return min(score, 1.0)
    
    def _check_price_reasonableness(self, selected_match: Dict[str, Any], rules: Dict[str, Any], 
                                  warnings: List[str]) -> float:
        """Check if price is reasonable"""
        price = selected_match.get("price")
        
        if not price:
            return 0.5  # Neutral score if no price
        
        try:
            price_val = float(price)
            
            # Basic sanity checks
            if price_val <= 0:
                warnings.append("Price appears to be invalid")
                return 0.3
            elif price_val > 10000:
                warnings.append("Price seems very high, verify accuracy")
                return 0.7
            else:
                return 1.0
                
        except (ValueError, TypeError):
            warnings.append("Price format appears invalid")
            return 0.4
    
    def adjust_thresholds(self, stage: str, new_threshold: float):
        """Dynamically adjust quality thresholds"""
        if stage in self.thresholds:
            self.thresholds[stage] = new_threshold
            logger.info(f"Adjusted {stage} threshold to {new_threshold}")
    
    def get_stage_statistics(self) -> Dict[str, Any]:
        """Get statistics about quality gate performance"""
        return {
            "current_thresholds": self.thresholds,
            "threshold_level": self.threshold_level,
            "validation_rules": self.validation_rules
        }