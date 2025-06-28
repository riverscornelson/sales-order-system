"""
Sales Order Intelligence Evaluation System.

This module implements the comprehensive evaluation framework for the 
Sales Order Intelligence system, focusing on ERP JSON accuracy as the
primary objective (40% of total score).
"""

import json
import logging
import time
import traceback
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from pathlib import Path

from .base_eval import BaseEval, EvalResult
from .data_structures import (
    ERPAccuracyScore, 
    ReasoningScore, 
    ComplianceScore, 
    PerformanceScore,
    EvaluationConfig
)
from ..models.schemas import OrderData, OrderLineItem, CustomerInfo
from ..core.config import settings

logger = logging.getLogger(__name__)


class SalesOrderIntelligenceEval(BaseEval):
    """
    Main evaluation class for the Sales Order Intelligence system.
    
    This evaluator focuses on ERP JSON accuracy as the PRIMARY objective,
    while also assessing reasoning quality, compliance, and performance.
    
    Scoring Breakdown:
    - ERP Accuracy: 40% (PRIMARY)
    - Reasoning Quality: 20%
    - Compliance: 20% 
    - Performance: 20%
    """
    
    def __init__(self, 
                 config: Optional[EvaluationConfig] = None,
                 erp_schema_path: Optional[str] = None):
        """
        Initialize the Sales Order Intelligence evaluator.
        
        Args:
            config: Evaluation configuration parameters
            erp_schema_path: Path to ERP JSON schema for validation
        """
        super().__init__(
            eval_name="sales_order_intelligence",
            eval_description="Comprehensive evaluation of sales order processing with ERP focus",
            config=config.to_dict() if config else {}
        )
        
        self.eval_config = config or EvaluationConfig.from_env()
        self.erp_schema_path = erp_schema_path
        self.erp_schema = self._load_erp_schema()
        
        # Validate configuration
        config_errors = self.eval_config.validate()
        if config_errors:
            raise ValueError(f"Configuration errors: {'; '.join(config_errors)}")
        
        self.logger.info(f"Initialized evaluator with ERP accuracy weight: {self.eval_config.erp_accuracy_weight}")
    
    def eval_sample(self, sample: Dict[str, Any]) -> EvalResult:
        """
        Evaluate a single sales order processing sample.
        
        Expected sample format:
        {
            "input": {
                "document_content": "...",
                "document_type": "pdf|email",
                "additional_context": {...}
            },
            "expected_output": {
                "erp_json": {...},
                "reasoning": [...],
                "metadata": {...}
            }
        }
        
        Args:
            sample: Input sample containing document and expected output
            
        Returns:
            EvalResult: Detailed evaluation result
        """
        start_time = time.time()
        
        try:
            # Extract sample components
            input_data = sample.get('input', {})
            expected_output = sample.get('expected_output', {})
            
            self.logger.debug(f"Evaluating sample with document type: {input_data.get('document_type', 'unknown')}")
            
            # Process the document through the sales order system
            actual_output = self._process_document(input_data)
            
            # Calculate all score components
            erp_score = self._evaluate_erp_accuracy(
                expected_output.get('erp_json', {}),
                actual_output.get('erp_json', {})
            )
            
            reasoning_score = self._evaluate_reasoning_quality(
                expected_output.get('reasoning', []),
                actual_output.get('reasoning', [])
            )
            
            compliance_score = self._evaluate_compliance(
                actual_output,
                input_data
            )
            
            performance_score = self._evaluate_performance(
                actual_output.get('metadata', {}),
                time.time() - start_time
            )
            
            # Calculate overall score with weights
            overall_score = (
                erp_score.overall_accuracy * self.eval_config.erp_accuracy_weight +
                reasoning_score.overall_reasoning * self.eval_config.reasoning_weight +
                compliance_score.overall_compliance * self.eval_config.compliance_weight +
                performance_score.overall_performance * self.eval_config.performance_weight
            )
            
            # Primary accuracy is ERP accuracy (the main business objective)
            primary_accuracy = erp_score.overall_accuracy
            
            # Detailed score breakdown
            detailed_scores = {
                'erp_accuracy': erp_score.overall_accuracy,
                'reasoning_quality': reasoning_score.overall_reasoning,
                'compliance': compliance_score.overall_compliance,
                'performance': performance_score.overall_performance,
                # ERP component scores
                'erp_schema_compliance': erp_score.schema_compliance,
                'erp_required_fields': erp_score.required_fields_accuracy,
                'erp_line_items': erp_score.line_items_accuracy,
                'erp_business_rules': erp_score.business_rules_compliance,
                # Performance metrics
                'processing_time_ms': (time.time() - start_time) * 1000,
                'erp_weight_contribution': erp_score.overall_accuracy * self.eval_config.erp_accuracy_weight
            }
            
            # Create result
            result = EvalResult(
                input=input_data,
                target=expected_output,
                output=actual_output,
                score=overall_score,
                accuracy=primary_accuracy,  # ERP accuracy as primary metric
                duration_ms=(time.time() - start_time) * 1000,
                model_used=self.eval_config.evaluation_model,
                detailed_scores=detailed_scores,
                metadata={
                    'erp_score_details': erp_score.to_dict(),
                    'reasoning_score_details': reasoning_score.to_dict(),
                    'compliance_score_details': compliance_score.to_dict(),
                    'performance_score_details': performance_score.to_dict(),
                    'evaluation_config': self.eval_config.to_dict()
                }
            )
            
            self.logger.debug(f"Sample evaluation completed. Overall: {overall_score:.3f}, ERP: {primary_accuracy:.3f}")
            return result
            
        except Exception as e:
            self.logger.error(f"Error evaluating sample: {e}")
            self.logger.debug(f"Traceback: {traceback.format_exc()}")
            
            return EvalResult(
                input=sample.get('input', {}),
                target=sample.get('expected_output', {}),
                duration_ms=(time.time() - start_time) * 1000,
                error=str(e),
                error_type=type(e).__name__
            )
    
    def _process_document(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process document through the sales order intelligence system.
        
        This method would integrate with the actual sales order processing
        pipeline to generate ERP JSON and reasoning chains.
        
        Args:
            input_data: Document content and metadata
            
        Returns:
            Dict containing ERP JSON, reasoning chain, and metadata
        """
        # TODO: Integration with actual sales order processing pipeline
        # For now, this is a placeholder that would call the real system
        
        document_content = input_data.get('document_content', '')
        document_type = input_data.get('document_type', 'pdf')
        
        # Placeholder - in real implementation this would:
        # 1. Call document parser
        # 2. Run through the agent pipeline
        # 3. Generate ERP JSON
        # 4. Capture reasoning chains
        # 5. Collect performance metrics
        
        self.logger.warning("Using placeholder document processing - integrate with real pipeline")
        
        return {
            'erp_json': {
                'customer': {'name': 'Placeholder Customer'},
                'line_items': [],
                'order_total': 0.0
            },
            'reasoning': ['Placeholder reasoning step'],
            'metadata': {
                'processing_time_ms': 100.0,
                'confidence_score': 0.8,
                'model_used': 'placeholder'
            }
        }
    
    def _evaluate_erp_accuracy(self, 
                             expected_erp: Dict[str, Any], 
                             actual_erp: Dict[str, Any]) -> ERPAccuracyScore:
        """
        Evaluate ERP JSON accuracy - PRIMARY evaluation metric (40% of total).
        
        This is the most critical evaluation component as ERP compatibility
        directly impacts business operations and customer satisfaction.
        
        Args:
            expected_erp: Expected ERP JSON structure
            actual_erp: Generated ERP JSON structure
            
        Returns:
            ERPAccuracyScore: Detailed ERP accuracy assessment
        """
        score = ERPAccuracyScore()
        
        try:
            # Schema compliance check
            score.schema_compliance = self._check_schema_compliance(actual_erp)
            
            # Required fields accuracy
            score.required_fields_accuracy = self._check_required_fields(expected_erp, actual_erp)
            
            # Data type accuracy
            score.data_type_accuracy = self._check_data_types(expected_erp, actual_erp)
            
            # Line items accuracy (critical for business)
            score.line_items_accuracy = self._check_line_items_accuracy(
                expected_erp.get('line_items', []),
                actual_erp.get('line_items', [])
            )
            
            # Pricing accuracy
            score.pricing_accuracy = self._check_pricing_accuracy(expected_erp, actual_erp)
            
            # Quantities accuracy
            score.quantities_accuracy = self._check_quantities_accuracy(expected_erp, actual_erp)
            
            # Part numbers accuracy
            score.part_numbers_accuracy = self._check_part_numbers_accuracy(expected_erp, actual_erp)
            
            # Business rules compliance
            score.business_rules_compliance = self._check_business_rules(actual_erp)
            
            # ERP field mapping accuracy
            score.erp_field_mapping = self._check_erp_field_mapping(expected_erp, actual_erp)
            
            # Calculate field-level scores
            score.field_level_scores = self._calculate_field_level_scores(expected_erp, actual_erp)
            
            # Identify missing and incorrect fields
            score.missing_required_fields = self._find_missing_required_fields(expected_erp, actual_erp)
            score.incorrect_fields = self._find_incorrect_fields(expected_erp, actual_erp)
            
            # Calculate counts
            score.total_fields_evaluated = len(self._get_all_fields(expected_erp))
            score.correctly_parsed_fields = sum(1 for score_val in score.field_level_scores.values() if score_val >= 0.9)
            
            # Calculate overall ERP accuracy score
            score.calculate_overall_score()
            
            self.logger.debug(f"ERP accuracy evaluation: {score.overall_accuracy:.3f}")
            
        except Exception as e:
            self.logger.error(f"Error in ERP accuracy evaluation: {e}")
            score.schema_errors.append(f"Evaluation error: {str(e)}")
        
        return score
    
    def _check_schema_compliance(self, erp_json: Dict[str, Any]) -> float:
        """Check compliance with ERP JSON schema."""
        if not self.erp_schema:
            self.logger.warning("No ERP schema loaded - skipping schema validation")
            return 1.0
        
        # TODO: Implement JSON schema validation
        # For now, basic structure check
        required_top_level = ['customer', 'line_items', 'order_total']
        present_fields = sum(1 for field in required_top_level if field in erp_json)
        return present_fields / len(required_top_level)
    
    def _check_required_fields(self, expected: Dict[str, Any], actual: Dict[str, Any]) -> float:
        """Check accuracy of required fields."""
        required_fields = ['customer', 'line_items', 'order_total', 'order_date']
        
        correct_fields = 0
        for field in required_fields:
            if field in expected and field in actual:
                if self._fields_match(expected[field], actual[field]):
                    correct_fields += 1
        
        return correct_fields / len(required_fields) if required_fields else 1.0
    
    def _check_line_items_accuracy(self, expected_items: List[Dict], actual_items: List[Dict]) -> float:
        """Check accuracy of line items parsing - critical for business operations."""
        if not expected_items and not actual_items:
            return 1.0
        
        if not expected_items or not actual_items:
            return 0.0
        
        # Match line items and calculate accuracy
        total_accuracy = 0.0
        for expected_item in expected_items:
            best_match_score = 0.0
            
            for actual_item in actual_items:
                match_score = self._calculate_line_item_match(expected_item, actual_item)
                best_match_score = max(best_match_score, match_score)
            
            total_accuracy += best_match_score
        
        return total_accuracy / len(expected_items)
    
    def _calculate_line_item_match(self, expected: Dict, actual: Dict) -> float:
        """Calculate match score between two line items."""
        weights = {
            'part_number': 0.30,
            'description': 0.25,
            'quantity': 0.20,
            'unit_price': 0.15,
            'total_price': 0.10
        }
        
        total_score = 0.0
        for field, weight in weights.items():
            if field in expected and field in actual:
                if self._fields_match(expected[field], actual[field]):
                    total_score += weight
        
        return total_score
    
    def _check_pricing_accuracy(self, expected: Dict[str, Any], actual: Dict[str, Any]) -> float:
        """Check pricing calculation accuracy."""
        # Check order total
        expected_total = expected.get('order_total', 0)
        actual_total = actual.get('order_total', 0)
        
        if expected_total == 0 and actual_total == 0:
            return 1.0
        
        if expected_total == 0 or actual_total == 0:
            return 0.0
        
        # Allow for small rounding differences
        difference_ratio = abs(expected_total - actual_total) / expected_total
        return max(0.0, 1.0 - difference_ratio)
    
    def _check_quantities_accuracy(self, expected: Dict[str, Any], actual: Dict[str, Any]) -> float:
        """Check quantity parsing accuracy."""
        expected_items = expected.get('line_items', [])
        actual_items = actual.get('line_items', [])
        
        if not expected_items:
            return 1.0
        
        correct_quantities = 0
        for expected_item in expected_items:
            expected_qty = expected_item.get('quantity', 0)
            # Find matching item in actual (simplified matching by description)
            for actual_item in actual_items:
                if self._items_similar(expected_item, actual_item):
                    actual_qty = actual_item.get('quantity', 0)
                    if expected_qty == actual_qty:
                        correct_quantities += 1
                    break
        
        return correct_quantities / len(expected_items)
    
    def _check_part_numbers_accuracy(self, expected: Dict[str, Any], actual: Dict[str, Any]) -> float:
        """Check part number identification accuracy."""
        expected_items = expected.get('line_items', [])
        actual_items = actual.get('line_items', [])
        
        if not expected_items:
            return 1.0
        
        correct_part_numbers = 0
        for expected_item in expected_items:
            expected_part = expected_item.get('part_number')
            if expected_part:
                for actual_item in actual_items:
                    if self._items_similar(expected_item, actual_item):
                        actual_part = actual_item.get('part_number')
                        if expected_part == actual_part:
                            correct_part_numbers += 1
                        break
        
        return correct_part_numbers / max(1, sum(1 for item in expected_items if item.get('part_number')))
    
    def _check_business_rules(self, erp_json: Dict[str, Any]) -> float:
        """Check compliance with business rules."""
        violations = 0
        total_rules = 0
        
        # Rule 1: Order total should equal sum of line item totals
        total_rules += 1
        order_total = erp_json.get('order_total', 0)
        line_items_total = sum(item.get('total_price', 0) for item in erp_json.get('line_items', []))
        if abs(order_total - line_items_total) > 0.01:
            violations += 1
        
        # Rule 2: All line items should have positive quantities
        total_rules += 1
        for item in erp_json.get('line_items', []):
            if item.get('quantity', 0) <= 0:
                violations += 1
                break
        
        # Rule 3: Customer information should be present
        total_rules += 1
        customer = erp_json.get('customer', {})
        if not (customer.get('name') or customer.get('company')):
            violations += 1
        
        return max(0.0, 1.0 - violations / total_rules) if total_rules > 0 else 1.0
    
    def _check_erp_field_mapping(self, expected: Dict[str, Any], actual: Dict[str, Any]) -> float:
        """Check correct mapping to ERP fields."""
        # This would check if fields are mapped to correct ERP field names
        # For now, simplified implementation
        erp_fields = ['customer', 'line_items', 'order_total', 'order_date', 'delivery_date']
        
        correct_mappings = 0
        for field in erp_fields:
            if field in expected and field in actual:
                correct_mappings += 1
        
        return correct_mappings / len(erp_fields)
    
    def _calculate_field_level_scores(self, expected: Dict[str, Any], actual: Dict[str, Any]) -> Dict[str, float]:
        """Calculate accuracy scores for individual fields."""
        field_scores = {}
        
        all_fields = set(expected.keys()) | set(actual.keys())
        for field in all_fields:
            if field in expected and field in actual:
                if self._fields_match(expected[field], actual[field]):
                    field_scores[field] = 1.0
                else:
                    field_scores[field] = 0.5  # Partial credit for presence
            elif field in expected:
                field_scores[field] = 0.0  # Missing field
            else:
                field_scores[field] = 0.8  # Extra field (not penalized heavily)
        
        return field_scores
    
    def _find_missing_required_fields(self, expected: Dict[str, Any], actual: Dict[str, Any]) -> List[str]:
        """Find required fields that are missing."""
        required_fields = ['customer', 'line_items', 'order_total']
        return [field for field in required_fields if field in expected and field not in actual]
    
    def _find_incorrect_fields(self, expected: Dict[str, Any], actual: Dict[str, Any]) -> Dict[str, str]:
        """Find fields with incorrect values."""
        incorrect = {}
        
        for field in expected:
            if field in actual and not self._fields_match(expected[field], actual[field]):
                incorrect[field] = f"Expected: {expected[field]}, Got: {actual[field]}"
        
        return incorrect
    
    def _get_all_fields(self, data: Dict[str, Any]) -> List[str]:
        """Get all fields in a nested dictionary."""
        fields = []
        for key, value in data.items():
            fields.append(key)
            if isinstance(value, dict):
                fields.extend([f"{key}.{subfield}" for subfield in self._get_all_fields(value)])
        return fields
    
    def _fields_match(self, expected: Any, actual: Any) -> bool:
        """Check if two field values match with appropriate tolerance."""
        if type(expected) != type(actual):
            return False
        
        if isinstance(expected, (int, float)):
            # Allow small numeric differences
            return abs(expected - actual) < 0.01
        elif isinstance(expected, str):
            # Case-insensitive string comparison
            return expected.lower().strip() == actual.lower().strip()
        elif isinstance(expected, list):
            # List comparison (order matters)
            return len(expected) == len(actual) and all(
                self._fields_match(e, a) for e, a in zip(expected, actual)
            )
        elif isinstance(expected, dict):
            # Dictionary comparison
            return all(
                key in actual and self._fields_match(expected[key], actual[key])
                for key in expected
            )
        else:
            return expected == actual
    
    def _items_similar(self, item1: Dict, item2: Dict) -> bool:
        """Check if two line items are similar (for matching purposes)."""
        # Simple similarity check based on description
        desc1 = item1.get('description', '').lower().strip()
        desc2 = item2.get('description', '').lower().strip()
        return desc1 == desc2 or (desc1 and desc2 and desc1 in desc2) or (desc2 in desc1)
    
    def _evaluate_reasoning_quality(self, 
                                  expected_reasoning: List[str], 
                                  actual_reasoning: List[str]) -> ReasoningScore:
        """Evaluate the quality of AI reasoning chains."""
        score = ReasoningScore()
        
        try:
            score.reasoning_chain_length = len(actual_reasoning)
            score.reasoning_steps = actual_reasoning
            
            # Basic reasoning quality checks
            if actual_reasoning:
                score.step_completeness = min(1.0, len(actual_reasoning) / max(1, len(expected_reasoning)))
                score.logical_consistency = 0.8  # Placeholder - would need more sophisticated analysis
                score.evidence_quality = 0.7    # Placeholder
                score.conclusion_validity = 0.8  # Placeholder
                score.business_logic_reasoning = 0.75  # Placeholder
            
            score.calculate_overall_score()
            
        except Exception as e:
            self.logger.error(f"Error in reasoning evaluation: {e}")
            score.reasoning_errors.append(str(e))
        
        return score
    
    def _evaluate_compliance(self, 
                           actual_output: Dict[str, Any], 
                           input_data: Dict[str, Any]) -> ComplianceScore:
        """Evaluate compliance with business rules and standards."""
        score = ComplianceScore()
        
        try:
            # Basic compliance checks
            score.business_rules_adherence = 0.9    # Placeholder
            score.data_validation_compliance = 0.85  # Placeholder
            score.workflow_compliance = 0.8         # Placeholder
            score.data_protection_compliance = 1.0  # Placeholder
            score.error_handling_compliance = 0.75  # Placeholder
            score.audit_trail_compliance = 0.9     # Placeholder
            
            score.calculate_overall_score()
            
        except Exception as e:
            self.logger.error(f"Error in compliance evaluation: {e}")
            score.violations.append(f"Evaluation error: {str(e)}")
        
        return score
    
    def _evaluate_performance(self, 
                            metadata: Dict[str, Any], 
                            total_time: float) -> PerformanceScore:
        """Evaluate system performance metrics."""
        score = PerformanceScore()
        
        try:
            score.avg_processing_time_ms = total_time * 1000
            score.calculate_speed_score()
            
            # Other performance metrics (placeholders)
            score.response_time_score = 0.8
            score.memory_efficiency_score = 0.85
            score.throughput_score = 0.75
            score.concurrent_processing_score = 0.7
            
            score.calculate_overall_score()
            
        except Exception as e:
            self.logger.error(f"Error in performance evaluation: {e}")
        
        return score
    
    def _load_erp_schema(self) -> Optional[Dict[str, Any]]:
        """Load ERP JSON schema for validation."""
        if not self.erp_schema_path:
            return None
        
        try:
            schema_path = Path(self.erp_schema_path)
            if schema_path.exists():
                with open(schema_path, 'r') as f:
                    return json.load(f)
        except Exception as e:
            self.logger.warning(f"Could not load ERP schema from {self.erp_schema_path}: {e}")
        
        return None