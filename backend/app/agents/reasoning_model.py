"""
Line Item Reasoning Model
Provides intelligent analysis and retry strategies for difficult line items
"""

import asyncio
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import re
import structlog
from datetime import datetime

from ..models.line_item_schemas import LineItem, LineItemStatus, ProcessingStage
from .quality_gates import QualityGateResult

logger = structlog.get_logger()


class FailureCategory(str, Enum):
    """Categories of processing failures"""
    EXTRACTION_UNCLEAR = "extraction_unclear"
    EXTRACTION_INCOMPLETE = "extraction_incomplete"
    SEARCH_NO_RESULTS = "search_no_results"
    SEARCH_POOR_MATCHES = "search_poor_matches"
    MATCHING_LOW_CONFIDENCE = "matching_low_confidence"
    MATCHING_CONFLICTING = "matching_conflicting"
    DATA_QUALITY = "data_quality"
    TECHNICAL_ERROR = "technical_error"


class RetryStrategy(str, Enum):
    """Available retry strategies"""
    ENHANCED_EXTRACTION = "enhanced_extraction"
    BROADENED_SEARCH = "broadened_search"
    ALTERNATIVE_SEARCH = "alternative_search"
    FUZZY_MATCHING = "fuzzy_matching"
    HUMAN_GUIDED = "human_guided"
    MULTI_STRATEGY = "multi_strategy"


@dataclass
class FailureAnalysis:
    """Analysis of why a line item failed processing"""
    category: FailureCategory
    confidence: float  # How confident we are in this analysis
    root_causes: List[str]
    contributing_factors: List[str]
    complexity_score: float  # 0-1, how complex/difficult this item is
    suggested_strategies: List[RetryStrategy]


@dataclass
class RetryRecommendation:
    """Recommendation for retrying a failed line item"""
    should_retry: bool
    strategy_name: str
    strategy: RetryStrategy
    modifications: Dict[str, Any]
    expected_success_probability: float
    estimated_processing_time: float
    reasoning: str
    
    def apply_modifications(self, processors: Dict[str, Any]) -> Dict[str, Any]:
        """Apply strategy modifications to processors"""
        modified_processors = processors.copy()
        
        for processor_name, modifications in self.modifications.items():
            if processor_name in modified_processors:
                # Apply modifications to the processor
                processor = modified_processors[processor_name]
                for key, value in modifications.items():
                    if hasattr(processor, key):
                        setattr(processor, key, value)
                    elif hasattr(processor, 'config'):
                        processor.config[key] = value
        
        return modified_processors


class LineItemReasoningModel:
    """
    AI-powered reasoning model for analyzing line item processing failures
    and suggesting intelligent retry strategies
    """
    
    def __init__(self):
        self.failure_patterns = self._initialize_failure_patterns()
        self.strategy_effectiveness = self._initialize_strategy_effectiveness()
        self.complexity_indicators = self._initialize_complexity_indicators()
        
        # Learning metrics
        self.retry_history = []
        self.success_rates = {}
    
    def _initialize_failure_patterns(self) -> Dict[str, Any]:
        """Initialize patterns for recognizing failure types"""
        return {
            "extraction_unclear": {
                "indicators": [
                    "description too short",
                    "missing key information",
                    "ambiguous specifications",
                    "unclear material type"
                ],
                "text_patterns": [
                    r"^.{1,20}$",  # Very short description
                    r"misc|various|assorted|other",  # Vague terms
                    r"^[^a-zA-Z]*$"  # No letters (just numbers/symbols)
                ]
            },
            "extraction_incomplete": {
                "indicators": [
                    "missing quantity",
                    "missing material",
                    "incomplete specifications",
                    "partial extraction"
                ],
                "required_fields": ["quantity", "description", "material"]
            },
            "search_no_results": {
                "indicators": [
                    "no search results",
                    "empty result set",
                    "zero matches found"
                ]
            },
            "search_poor_matches": {
                "indicators": [
                    "low similarity scores",
                    "poor quality matches",
                    "irrelevant results"
                ],
                "thresholds": {
                    "max_similarity": 0.4,
                    "avg_similarity": 0.3
                }
            },
            "matching_low_confidence": {
                "indicators": [
                    "low match confidence",
                    "uncertain selection",
                    "close alternatives"
                ],
                "thresholds": {
                    "confidence": 0.6
                }
            }
        }
    
    def _initialize_strategy_effectiveness(self) -> Dict[RetryStrategy, Dict[str, float]]:
        """Initialize expected effectiveness of different retry strategies"""
        return {
            RetryStrategy.ENHANCED_EXTRACTION: {
                "extraction_unclear": 0.8,
                "extraction_incomplete": 0.9,
                "data_quality": 0.7,
                "default": 0.3
            },
            RetryStrategy.BROADENED_SEARCH: {
                "search_no_results": 0.9,
                "search_poor_matches": 0.7,
                "extraction_unclear": 0.6,
                "default": 0.4
            },
            RetryStrategy.ALTERNATIVE_SEARCH: {
                "search_poor_matches": 0.8,
                "matching_low_confidence": 0.7,
                "search_no_results": 0.6,
                "default": 0.5
            },
            RetryStrategy.FUZZY_MATCHING: {
                "matching_low_confidence": 0.8,
                "extraction_unclear": 0.7,
                "search_poor_matches": 0.6,
                "default": 0.4
            },
            RetryStrategy.MULTI_STRATEGY: {
                "matching_conflicting": 0.9,
                "search_poor_matches": 0.8,
                "extraction_incomplete": 0.7,
                "default": 0.6
            },
            RetryStrategy.HUMAN_GUIDED: {
                "extraction_unclear": 0.95,
                "extraction_incomplete": 0.9,
                "matching_low_confidence": 0.8,
                "search_poor_matches": 0.7,
                "default": 0.8
            }
        }
    
    def _initialize_complexity_indicators(self) -> Dict[str, float]:
        """Initialize indicators for measuring line item complexity"""
        return {
            "technical_specifications": 0.8,
            "multiple_materials": 0.7,
            "custom_dimensions": 0.6,
            "special_requirements": 0.9,
            "industry_jargon": 0.5,
            "abbreviations": 0.4,
            "numbers_only": 0.3
        }
    
    async def analyze_failure_and_suggest_retry(
        self, 
        line_item: LineItem, 
        failed_stage: str, 
        quality_result: QualityGateResult
    ) -> RetryRecommendation:
        """
        Analyze why a line item failed and suggest an intelligent retry strategy
        """
        logger.info("Analyzing failure for retry strategy", 
                   line_id=line_item.line_id, 
                   stage=failed_stage,
                   score=quality_result.score)
        
        # Step 1: Analyze the failure
        failure_analysis = await self._analyze_failure(line_item, failed_stage, quality_result)
        
        # Step 2: Calculate complexity score
        complexity_score = self._calculate_complexity_score(line_item)
        
        # Step 3: Select best retry strategy
        retry_strategy = self._select_retry_strategy(failure_analysis, complexity_score, line_item)
        
        # Step 4: Generate specific modifications
        modifications = self._generate_strategy_modifications(retry_strategy, failure_analysis, line_item)
        
        # Step 5: Estimate success probability
        success_probability = self._estimate_success_probability(
            retry_strategy, failure_analysis, complexity_score, line_item
        )
        
        # Step 6: Generate reasoning explanation
        reasoning = self._generate_reasoning(failure_analysis, retry_strategy, success_probability)
        
        # Decision: Should we retry?
        should_retry = self._should_attempt_retry(
            success_probability, complexity_score, line_item.status, quality_result
        )
        
        recommendation = RetryRecommendation(
            should_retry=should_retry,
            strategy_name=retry_strategy.value,
            strategy=retry_strategy,
            modifications=modifications,
            expected_success_probability=success_probability,
            estimated_processing_time=self._estimate_processing_time(retry_strategy, complexity_score),
            reasoning=reasoning
        )
        
        # Log the recommendation for learning
        self._log_retry_recommendation(line_item, failure_analysis, recommendation)
        
        return recommendation
    
    async def _analyze_failure(
        self, 
        line_item: LineItem, 
        failed_stage: str, 
        quality_result: QualityGateResult
    ) -> FailureAnalysis:
        """Analyze the specific failure to categorize it"""
        
        # Combine all available information
        issues = quality_result.issues + line_item.issues
        text = line_item.raw_text
        
        # Pattern matching for failure categories
        category_scores = {}
        
        for category, patterns in self.failure_patterns.items():
            score = 0.0
            
            # Check issue indicators
            for indicator in patterns.get("indicators", []):
                if any(indicator in issue.lower() for issue in issues):
                    score += 0.3
            
            # Check text patterns
            for pattern in patterns.get("text_patterns", []):
                if re.search(pattern, text, re.IGNORECASE):
                    score += 0.2
            
            # Check thresholds
            thresholds = patterns.get("thresholds", {})
            if failed_stage == "search" and "max_similarity" in thresholds:
                # This would require access to actual search results
                # For now, we'll use the quality score as a proxy
                if quality_result.score < thresholds["max_similarity"]:
                    score += 0.4
            
            category_scores[category] = score
        
        # Find the most likely category
        best_category = max(category_scores, key=category_scores.get)
        confidence = category_scores[best_category]
        
        # Analyze root causes
        root_causes = self._identify_root_causes(line_item, failed_stage, quality_result)
        contributing_factors = self._identify_contributing_factors(line_item, issues)
        
        # Calculate complexity
        complexity_score = self._calculate_complexity_score(line_item)
        
        # Suggest strategies based on category
        suggested_strategies = self._suggest_strategies_for_category(
            FailureCategory(best_category), complexity_score
        )
        
        return FailureAnalysis(
            category=FailureCategory(best_category),
            confidence=min(confidence, 1.0),
            root_causes=root_causes,
            contributing_factors=contributing_factors,
            complexity_score=complexity_score,
            suggested_strategies=suggested_strategies
        )
    
    def _calculate_complexity_score(self, line_item: LineItem) -> float:
        """Calculate how complex/difficult this line item is to process"""
        text = line_item.raw_text.lower()
        score = 0.0
        
        # Length-based complexity
        if len(text) < 20:
            score += 0.3  # Very short descriptions are complex
        elif len(text) > 200:
            score += 0.2  # Very long descriptions can be complex
        
        # Content-based complexity indicators
        complexity_patterns = {
            r'\d+x\d+x\d+': 0.1,  # Dimensions
            r'grade\s+\w+': 0.2,  # Material grades
            r'spec\w*\s+\w+': 0.2,  # Specifications
            r'custom|special|modified': 0.3,  # Custom requirements
            r'tolerance|±|precision': 0.4,  # Precision requirements
            r'certified|approved|qualified': 0.2,  # Certifications
            r'[A-Z]{2,}\d+': 0.1,  # Part numbers or codes
        }
        
        for pattern, weight in complexity_patterns.items():
            if re.search(pattern, text, re.IGNORECASE):
                score += weight
        
        # Word complexity
        words = text.split()
        technical_words = 0
        for word in words:
            if len(word) > 8:  # Long technical terms
                technical_words += 1
        
        if technical_words > 0:
            score += min(technical_words * 0.05, 0.2)
        
        return min(score, 1.0)
    
    def _select_retry_strategy(
        self, 
        failure_analysis: FailureAnalysis, 
        complexity_score: float, 
        line_item: LineItem
    ) -> RetryStrategy:
        """Select the best retry strategy based on failure analysis"""
        
        category = failure_analysis.category.value
        suggested_strategies = failure_analysis.suggested_strategies
        
        # Calculate effectiveness scores for each suggested strategy
        strategy_scores = {}
        
        for strategy in suggested_strategies:
            effectiveness = self.strategy_effectiveness[strategy]
            base_score = effectiveness.get(category, effectiveness["default"])
            
            # Adjust based on complexity
            if complexity_score > 0.7:
                # High complexity items benefit from multi-strategy approach
                if strategy == RetryStrategy.MULTI_STRATEGY:
                    base_score += 0.2
                elif strategy in [RetryStrategy.HUMAN_GUIDED, RetryStrategy.ENHANCED_EXTRACTION]:
                    base_score += 0.1
            
            # Adjust based on retry count
            retry_count = getattr(line_item, 'retry_count', 0)
            if retry_count > 0:
                # Prefer different strategies on subsequent retries
                if strategy == RetryStrategy.MULTI_STRATEGY:
                    base_score += 0.15
                elif strategy == RetryStrategy.ALTERNATIVE_SEARCH:
                    base_score += 0.1
            
            strategy_scores[strategy] = base_score
        
        # Select the strategy with highest score
        best_strategy = max(strategy_scores, key=strategy_scores.get)
        
        logger.debug("Selected retry strategy", 
                    strategy=best_strategy.value,
                    score=strategy_scores[best_strategy],
                    category=category)
        
        return best_strategy
    
    def _generate_strategy_modifications(
        self, 
        strategy: RetryStrategy, 
        failure_analysis: FailureAnalysis, 
        line_item: LineItem
    ) -> Dict[str, Any]:
        """Generate specific modifications for the retry strategy"""
        
        modifications = {}
        
        if strategy == RetryStrategy.ENHANCED_EXTRACTION:
            modifications["extractor"] = {
                "use_advanced_parsing": True,
                "enable_context_expansion": True,
                "apply_domain_knowledge": True,
                "extraction_confidence_threshold": 0.6
            }
        
        elif strategy == RetryStrategy.BROADENED_SEARCH:
            modifications["search"] = {
                "similarity_threshold": 0.3,  # Lower threshold
                "max_results": 20,  # More results
                "enable_fuzzy_search": True,
                "search_synonyms": True,
                "expand_query_terms": True
            }
        
        elif strategy == RetryStrategy.ALTERNATIVE_SEARCH:
            modifications["search"] = {
                "use_alternative_embedding_model": True,
                "enable_semantic_expansion": True,
                "try_categorical_search": True,
                "use_keyword_fallback": True
            }
        
        elif strategy == RetryStrategy.FUZZY_MATCHING:
            modifications["matcher"] = {
                "enable_fuzzy_matching": True,
                "fuzzy_threshold": 0.7,
                "allow_partial_matches": True,
                "confidence_adjustment": -0.1  # Lower confidence threshold
            }
        
        elif strategy == RetryStrategy.MULTI_STRATEGY:
            # Combine multiple approaches
            modifications.update({
                "extractor": {
                    "use_multiple_extraction_methods": True,
                    "consensus_threshold": 0.6
                },
                "search": {
                    "use_multiple_search_strategies": True,
                    "combine_results": True,
                    "diversity_boost": True
                },
                "matcher": {
                    "use_ensemble_matching": True,
                    "multiple_confidence_metrics": True
                }
            })
        
        elif strategy == RetryStrategy.HUMAN_GUIDED:
            modifications["workflow"] = {
                "request_human_input": True,
                "highlight_ambiguities": True,
                "suggest_clarifications": True,
                "partial_automation": True
            }
        
        return modifications
    
    def _estimate_success_probability(
        self, 
        strategy: RetryStrategy, 
        failure_analysis: FailureAnalysis, 
        complexity_score: float, 
        line_item: LineItem
    ) -> float:
        """Estimate probability of success with the selected strategy"""
        
        # Base effectiveness for this failure category
        category = failure_analysis.category.value
        effectiveness = self.strategy_effectiveness[strategy]
        base_probability = effectiveness.get(category, effectiveness["default"])
        
        # Adjust for failure analysis confidence
        if failure_analysis.confidence > 0.8:
            base_probability += 0.1  # We understand the failure well
        elif failure_analysis.confidence < 0.5:
            base_probability -= 0.1  # Uncertain about the failure
        
        # Adjust for complexity
        complexity_penalty = complexity_score * 0.2
        base_probability -= complexity_penalty
        
        # Adjust for retry count
        retry_count = getattr(line_item, 'retry_count', 0)
        if retry_count > 0:
            base_probability -= retry_count * 0.1  # Diminishing returns
        
        # Historical performance adjustment
        if strategy.value in self.success_rates:
            historical_rate = self.success_rates[strategy.value]
            base_probability = (base_probability + historical_rate) / 2
        
        return max(0.1, min(0.95, base_probability))
    
    def _should_attempt_retry(
        self, 
        success_probability: float, 
        complexity_score: float, 
        current_status: LineItemStatus,
        quality_result: QualityGateResult
    ) -> bool:
        """Decide whether to attempt a retry"""
        
        # Don't retry if probability is too low
        if success_probability < 0.3:
            return False
        
        # Don't retry if item is already in manual review
        if current_status == LineItemStatus.MANUAL_REVIEW:
            return False
        
        # Always retry if probability is high
        if success_probability > 0.7:
            return True
        
        # Consider quality score - retry if close to threshold
        score_gap = quality_result.threshold - quality_result.score
        if score_gap < 0.1:  # Very close to passing
            return True
        
        # Consider complexity - retry simpler items more readily
        if complexity_score < 0.5 and success_probability > 0.5:
            return True
        
        # Default decision based on probability
        return success_probability > 0.5
    
    def _estimate_processing_time(self, strategy: RetryStrategy, complexity_score: float) -> float:
        """Estimate additional processing time for the retry strategy"""
        
        base_times = {
            RetryStrategy.ENHANCED_EXTRACTION: 3.0,
            RetryStrategy.BROADENED_SEARCH: 2.0,
            RetryStrategy.ALTERNATIVE_SEARCH: 4.0,
            RetryStrategy.FUZZY_MATCHING: 1.5,
            RetryStrategy.MULTI_STRATEGY: 6.0,
            RetryStrategy.HUMAN_GUIDED: 30.0  # Includes human wait time
        }
        
        base_time = base_times.get(strategy, 3.0)
        complexity_multiplier = 1.0 + (complexity_score * 0.5)
        
        return base_time * complexity_multiplier
    
    def _generate_reasoning(
        self, 
        failure_analysis: FailureAnalysis, 
        strategy: RetryStrategy, 
        success_probability: float
    ) -> str:
        """Generate human-readable reasoning for the retry decision"""
        
        category_descriptions = {
            FailureCategory.EXTRACTION_UNCLEAR: "unclear or incomplete extraction",
            FailureCategory.SEARCH_NO_RESULTS: "no suitable matches found",
            FailureCategory.SEARCH_POOR_MATCHES: "poor quality search results",
            FailureCategory.MATCHING_LOW_CONFIDENCE: "low confidence in match selection"
        }
        
        strategy_descriptions = {
            RetryStrategy.ENHANCED_EXTRACTION: "enhanced extraction with advanced parsing",
            RetryStrategy.BROADENED_SEARCH: "broadened search with relaxed criteria",
            RetryStrategy.ALTERNATIVE_SEARCH: "alternative search using different methods",
            RetryStrategy.FUZZY_MATCHING: "fuzzy matching with partial matches allowed",
            RetryStrategy.MULTI_STRATEGY: "multi-strategy approach combining techniques",
            RetryStrategy.HUMAN_GUIDED: "human-guided processing with operator input"
        }
        
        category_desc = category_descriptions.get(
            failure_analysis.category, "processing difficulties"
        )
        strategy_desc = strategy_descriptions.get(strategy, "alternative processing")
        
        reasoning = f"Analysis identified {category_desc} as the primary issue. "
        reasoning += f"Recommending {strategy_desc} "
        reasoning += f"with {success_probability:.1%} estimated success probability. "
        
        if failure_analysis.complexity_score > 0.7:
            reasoning += "Item complexity is high, may require manual review if retry fails. "
        
        if len(failure_analysis.root_causes) > 0:
            reasoning += f"Key issues: {', '.join(failure_analysis.root_causes[:2])}."
        
        return reasoning
    
    def _identify_root_causes(
        self, 
        line_item: LineItem, 
        failed_stage: str, 
        quality_result: QualityGateResult
    ) -> List[str]:
        """Identify root causes of the failure"""
        causes = []
        
        # Extract causes from quality result issues
        for issue in quality_result.issues:
            if "missing" in issue.lower():
                causes.append("incomplete_data")
            elif "invalid" in issue.lower():
                causes.append("data_format_error")
            elif "too short" in issue.lower():
                causes.append("insufficient_description")
            elif "low" in issue.lower() and "score" in issue.lower():
                causes.append("poor_similarity_match")
        
        # Analyze line item text for additional causes
        text = line_item.raw_text.lower()
        if len(text) < 15:
            causes.append("minimal_description")
        if not re.search(r'\d', text):
            causes.append("missing_specifications")
        if re.search(r'misc|various|other|tbd|unknown', text):
            causes.append("vague_description")
        
        return list(set(causes))  # Remove duplicates
    
    def _identify_contributing_factors(self, line_item: LineItem, issues: List[str]) -> List[str]:
        """Identify factors that contributed to the failure"""
        factors = []
        
        # Analyze urgency
        if hasattr(line_item, 'urgency') and line_item.urgency == "HIGH":
            factors.append("high_urgency_pressure")
        
        # Analyze special requirements
        if hasattr(line_item, 'special_requirements') and line_item.special_requirements:
            factors.append("special_requirements_complexity")
        
        # Analyze previous attempts
        if len(line_item.issues) > 1:
            factors.append("multiple_processing_attempts")
        
        return factors
    
    def _suggest_strategies_for_category(
        self, 
        category: FailureCategory, 
        complexity_score: float
    ) -> List[RetryStrategy]:
        """Suggest appropriate strategies for a failure category"""
        
        strategy_map = {
            FailureCategory.EXTRACTION_UNCLEAR: [
                RetryStrategy.ENHANCED_EXTRACTION, 
                RetryStrategy.HUMAN_GUIDED
            ],
            FailureCategory.EXTRACTION_INCOMPLETE: [
                RetryStrategy.ENHANCED_EXTRACTION, 
                RetryStrategy.MULTI_STRATEGY
            ],
            FailureCategory.SEARCH_NO_RESULTS: [
                RetryStrategy.BROADENED_SEARCH, 
                RetryStrategy.ALTERNATIVE_SEARCH
            ],
            FailureCategory.SEARCH_POOR_MATCHES: [
                RetryStrategy.ALTERNATIVE_SEARCH, 
                RetryStrategy.BROADENED_SEARCH, 
                RetryStrategy.FUZZY_MATCHING
            ],
            FailureCategory.MATCHING_LOW_CONFIDENCE: [
                RetryStrategy.FUZZY_MATCHING, 
                RetryStrategy.MULTI_STRATEGY
            ]
        }
        
        strategies = strategy_map.get(category, [RetryStrategy.MULTI_STRATEGY])
        
        # Add multi-strategy for complex items
        if complexity_score > 0.7 and RetryStrategy.MULTI_STRATEGY not in strategies:
            strategies.append(RetryStrategy.MULTI_STRATEGY)
        
        return strategies
    
    def _log_retry_recommendation(
        self, 
        line_item: LineItem, 
        failure_analysis: FailureAnalysis, 
        recommendation: RetryRecommendation
    ):
        """Log retry recommendation for learning and improvement"""
        
        log_entry = {
            "timestamp": datetime.now(),
            "line_id": line_item.line_id,
            "failure_category": failure_analysis.category.value,
            "complexity_score": failure_analysis.complexity_score,
            "recommended_strategy": recommendation.strategy.value,
            "success_probability": recommendation.expected_success_probability,
            "should_retry": recommendation.should_retry
        }
        
        self.retry_history.append(log_entry)
        
        # Keep only recent history
        if len(self.retry_history) > 1000:
            self.retry_history = self.retry_history[-1000:]
    
    def update_success_rate(self, strategy: RetryStrategy, success: bool):
        """Update success rate tracking for a strategy"""
        if strategy.value not in self.success_rates:
            self.success_rates[strategy.value] = 0.5  # Start neutral
        
        current_rate = self.success_rates[strategy.value]
        # Exponential moving average
        self.success_rates[strategy.value] = current_rate * 0.9 + (1.0 if success else 0.0) * 0.1
    
    def get_learning_statistics(self) -> Dict[str, Any]:
        """Get statistics about the reasoning model's performance"""
        return {
            "total_recommendations": len(self.retry_history),
            "success_rates": self.success_rates,
            "recent_recommendations": self.retry_history[-10:] if self.retry_history else []
        }