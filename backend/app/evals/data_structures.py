"""
Data structures for evaluation scoring and configuration.

This module defines the detailed scoring components used in the 
Sales Order Intelligence evaluation system.
"""

import json
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Union
from pathlib import Path

from ..core.config import settings


@dataclass
class ERPAccuracyScore:
    """
    ERP JSON accuracy scoring - PRIMARY evaluation metric (40% of total score).
    
    This evaluates how accurately the system generates ERP-compatible JSON
    from sales order documents, which is the core business objective.
    """
    
    # Overall ERP accuracy (0.0 to 1.0)
    overall_accuracy: float = 0.0
    
    # Structural accuracy - JSON schema compliance
    schema_compliance: float = 0.0
    schema_errors: List[str] = field(default_factory=list)
    
    # Field-level accuracy scores
    required_fields_accuracy: float = 0.0  # Essential fields present and correct
    optional_fields_accuracy: float = 0.0  # Optional fields when present
    data_type_accuracy: float = 0.0       # Correct data types
    
    # Business logic accuracy
    line_items_accuracy: float = 0.0       # Line item parsing accuracy
    pricing_accuracy: float = 0.0          # Price calculations
    quantities_accuracy: float = 0.0       # Quantity parsing
    part_numbers_accuracy: float = 0.0     # Part number identification
    
    # ERP-specific requirements
    erp_field_mapping: float = 0.0         # Correct mapping to ERP fields
    business_rules_compliance: float = 0.0  # Business rules adherence
    
    # Detailed breakdowns for analysis
    field_level_scores: Dict[str, float] = field(default_factory=dict)
    missing_required_fields: List[str] = field(default_factory=list)
    incorrect_fields: Dict[str, str] = field(default_factory=dict)  # field -> error description
    
    # Metadata
    total_fields_evaluated: int = 0
    correctly_parsed_fields: int = 0
    
    def calculate_overall_score(self) -> float:
        """Calculate the overall ERP accuracy score with weighted components."""
        weights = {
            'schema_compliance': 0.20,
            'required_fields_accuracy': 0.25,
            'line_items_accuracy': 0.20,
            'business_rules_compliance': 0.15,
            'data_type_accuracy': 0.10,
            'part_numbers_accuracy': 0.10
        }
        
        score = (
            self.schema_compliance * weights['schema_compliance'] +
            self.required_fields_accuracy * weights['required_fields_accuracy'] +
            self.line_items_accuracy * weights['line_items_accuracy'] +
            self.business_rules_compliance * weights['business_rules_compliance'] +
            self.data_type_accuracy * weights['data_type_accuracy'] +
            self.part_numbers_accuracy * weights['part_numbers_accuracy']
        )
        
        self.overall_accuracy = score
        return score
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for reporting."""
        return {
            'overall_accuracy': self.overall_accuracy,
            'schema_compliance': self.schema_compliance,
            'required_fields_accuracy': self.required_fields_accuracy,
            'optional_fields_accuracy': self.optional_fields_accuracy,
            'data_type_accuracy': self.data_type_accuracy,
            'line_items_accuracy': self.line_items_accuracy,
            'pricing_accuracy': self.pricing_accuracy,
            'quantities_accuracy': self.quantities_accuracy,
            'part_numbers_accuracy': self.part_numbers_accuracy,
            'erp_field_mapping': self.erp_field_mapping,
            'business_rules_compliance': self.business_rules_compliance,
            'field_level_scores': self.field_level_scores,
            'missing_required_fields': self.missing_required_fields,
            'incorrect_fields': self.incorrect_fields,
            'total_fields_evaluated': self.total_fields_evaluated,
            'correctly_parsed_fields': self.correctly_parsed_fields,
            'schema_errors': self.schema_errors
        }


@dataclass
class ReasoningScore:
    """
    Reasoning quality evaluation (20% of total score).
    
    Evaluates the quality of AI reasoning chains and decision-making
    processes in the sales order intelligence system.
    """
    
    # Overall reasoning quality
    overall_reasoning: float = 0.0
    
    # Reasoning components
    logical_consistency: float = 0.0       # Internal consistency of reasoning
    evidence_quality: float = 0.0          # Quality of supporting evidence
    step_completeness: float = 0.0         # Completeness of reasoning steps
    conclusion_validity: float = 0.0       # Validity of final conclusions
    
    # Domain-specific reasoning
    business_logic_reasoning: float = 0.0   # Understanding of business rules
    technical_reasoning: float = 0.0       # Technical decision quality
    edge_case_handling: float = 0.0        # Handling of unusual scenarios
    
    # Reasoning artifacts
    reasoning_chain_length: int = 0
    reasoning_steps: List[str] = field(default_factory=list)
    confidence_scores: List[float] = field(default_factory=list)
    
    # Error analysis
    reasoning_errors: List[str] = field(default_factory=list)
    logical_fallacies: List[str] = field(default_factory=list)
    
    def calculate_overall_score(self) -> float:
        """Calculate overall reasoning score."""
        weights = {
            'logical_consistency': 0.25,
            'evidence_quality': 0.20,
            'step_completeness': 0.20,
            'conclusion_validity': 0.15,
            'business_logic_reasoning': 0.15,
            'edge_case_handling': 0.05
        }
        
        score = (
            self.logical_consistency * weights['logical_consistency'] +
            self.evidence_quality * weights['evidence_quality'] +
            self.step_completeness * weights['step_completeness'] +
            self.conclusion_validity * weights['conclusion_validity'] +
            self.business_logic_reasoning * weights['business_logic_reasoning'] +
            self.edge_case_handling * weights['edge_case_handling']
        )
        
        self.overall_reasoning = score
        return score
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for reporting."""
        return {
            'overall_reasoning': self.overall_reasoning,
            'logical_consistency': self.logical_consistency,
            'evidence_quality': self.evidence_quality,
            'step_completeness': self.step_completeness,
            'conclusion_validity': self.conclusion_validity,
            'business_logic_reasoning': self.business_logic_reasoning,
            'technical_reasoning': self.technical_reasoning,
            'edge_case_handling': self.edge_case_handling,
            'reasoning_chain_length': self.reasoning_chain_length,
            'reasoning_steps': self.reasoning_steps,
            'confidence_scores': self.confidence_scores,
            'reasoning_errors': self.reasoning_errors,
            'logical_fallacies': self.logical_fallacies
        }


@dataclass  
class ComplianceScore:
    """
    Compliance and safety evaluation (20% of total score).
    
    Evaluates adherence to business rules, data protection requirements,
    and operational compliance standards.
    """
    
    # Overall compliance
    overall_compliance: float = 0.0
    
    # Business compliance
    business_rules_adherence: float = 0.0   # Following business rules
    data_validation_compliance: float = 0.0 # Data validation requirements
    workflow_compliance: float = 0.0       # Proper workflow execution
    
    # Security and privacy
    data_protection_compliance: float = 0.0 # Data protection standards
    pii_handling_compliance: float = 0.0   # PII handling correctness
    access_control_compliance: float = 0.0  # Access control adherence
    
    # Operational compliance
    error_handling_compliance: float = 0.0  # Proper error handling
    logging_compliance: float = 0.0        # Adequate logging
    audit_trail_compliance: float = 0.0    # Audit trail completeness
    
    # Compliance violations
    violations: List[str] = field(default_factory=list)
    severity_breakdown: Dict[str, int] = field(default_factory=dict)  # critical, high, medium, low
    
    def calculate_overall_score(self) -> float:
        """Calculate overall compliance score."""
        weights = {
            'business_rules_adherence': 0.30,
            'data_validation_compliance': 0.20,
            'data_protection_compliance': 0.20,
            'workflow_compliance': 0.15,
            'error_handling_compliance': 0.10,
            'audit_trail_compliance': 0.05
        }
        
        score = (
            self.business_rules_adherence * weights['business_rules_adherence'] +
            self.data_validation_compliance * weights['data_validation_compliance'] +
            self.data_protection_compliance * weights['data_protection_compliance'] +
            self.workflow_compliance * weights['workflow_compliance'] +
            self.error_handling_compliance * weights['error_handling_compliance'] +
            self.audit_trail_compliance * weights['audit_trail_compliance']
        )
        
        self.overall_compliance = score
        return score
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for reporting."""
        return {
            'overall_compliance': self.overall_compliance,
            'business_rules_adherence': self.business_rules_adherence,
            'data_validation_compliance': self.data_validation_compliance,
            'workflow_compliance': self.workflow_compliance,
            'data_protection_compliance': self.data_protection_compliance,
            'pii_handling_compliance': self.pii_handling_compliance,
            'access_control_compliance': self.access_control_compliance,
            'error_handling_compliance': self.error_handling_compliance,
            'logging_compliance': self.logging_compliance,
            'audit_trail_compliance': self.audit_trail_compliance,
            'violations': self.violations,
            'severity_breakdown': self.severity_breakdown
        }


@dataclass
class PerformanceScore:
    """
    Performance evaluation (20% of total score).
    
    Evaluates system performance including processing speed,
    resource utilization, and scalability characteristics.
    """
    
    # Overall performance
    overall_performance: float = 0.0
    
    # Speed metrics
    processing_speed_score: float = 0.0    # Processing time relative to baseline
    response_time_score: float = 0.0       # API response times
    throughput_score: float = 0.0          # Requests per second capability
    
    # Resource utilization
    memory_efficiency_score: float = 0.0   # Memory usage efficiency
    cpu_efficiency_score: float = 0.0      # CPU usage efficiency
    
    # Scalability
    concurrent_processing_score: float = 0.0  # Concurrent request handling
    load_handling_score: float = 0.0       # Performance under load
    
    # Raw performance metrics
    avg_processing_time_ms: float = 0.0
    max_processing_time_ms: float = 0.0
    min_processing_time_ms: float = 0.0
    memory_peak_mb: float = 0.0
    cpu_peak_percent: float = 0.0
    
    # Performance benchmarks
    baseline_processing_time_ms: float = 1000.0  # Expected baseline
    target_processing_time_ms: float = 500.0     # Performance target
    
    def calculate_overall_score(self) -> float:
        """Calculate overall performance score."""
        weights = {
            'processing_speed_score': 0.35,
            'response_time_score': 0.25,
            'memory_efficiency_score': 0.20,
            'throughput_score': 0.15,
            'concurrent_processing_score': 0.05
        }
        
        score = (
            self.processing_speed_score * weights['processing_speed_score'] +
            self.response_time_score * weights['response_time_score'] +
            self.memory_efficiency_score * weights['memory_efficiency_score'] +
            self.throughput_score * weights['throughput_score'] +
            self.concurrent_processing_score * weights['concurrent_processing_score']
        )
        
        self.overall_performance = score
        return score
    
    def calculate_speed_score(self) -> float:
        """Calculate speed score based on processing time vs baseline."""
        if self.avg_processing_time_ms <= 0:
            return 0.0
        
        # Score based on how much faster/slower than baseline
        if self.avg_processing_time_ms <= self.target_processing_time_ms:
            # Excellent performance
            self.processing_speed_score = 1.0
        elif self.avg_processing_time_ms <= self.baseline_processing_time_ms:
            # Good performance - linear scale between target and baseline
            ratio = (self.baseline_processing_time_ms - self.avg_processing_time_ms) / \
                   (self.baseline_processing_time_ms - self.target_processing_time_ms)
            self.processing_speed_score = 0.7 + (0.3 * ratio)
        else:
            # Below baseline - diminishing returns
            ratio = self.baseline_processing_time_ms / self.avg_processing_time_ms
            self.processing_speed_score = max(0.0, 0.7 * ratio)
        
        return self.processing_speed_score
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for reporting."""
        return {
            'overall_performance': self.overall_performance,
            'processing_speed_score': self.processing_speed_score,
            'response_time_score': self.response_time_score,
            'throughput_score': self.throughput_score,
            'memory_efficiency_score': self.memory_efficiency_score,
            'cpu_efficiency_score': self.cpu_efficiency_score,
            'concurrent_processing_score': self.concurrent_processing_score,
            'load_handling_score': self.load_handling_score,
            'avg_processing_time_ms': self.avg_processing_time_ms,
            'max_processing_time_ms': self.max_processing_time_ms,
            'min_processing_time_ms': self.min_processing_time_ms,
            'memory_peak_mb': self.memory_peak_mb,
            'cpu_peak_percent': self.cpu_peak_percent,
            'baseline_processing_time_ms': self.baseline_processing_time_ms,
            'target_processing_time_ms': self.target_processing_time_ms
        }


@dataclass
class EvaluationConfig:
    """
    Configuration for evaluation parameters and thresholds.
    
    This class manages all configurable aspects of the evaluation system,
    allowing for flexible tuning of evaluation criteria and benchmarks.
    """
    
    # Score weights (must sum to 1.0)
    erp_accuracy_weight: float = 0.40      # PRIMARY metric
    reasoning_weight: float = 0.20
    compliance_weight: float = 0.20
    performance_weight: float = 0.20
    
    # ERP accuracy thresholds
    min_erp_accuracy_threshold: float = 0.70  # Minimum acceptable ERP accuracy
    target_erp_accuracy: float = 0.90        # Target ERP accuracy
    
    # Performance thresholds
    max_processing_time_ms: float = 2000.0   # Maximum acceptable processing time
    target_processing_time_ms: float = 500.0 # Target processing time
    
    # Reasoning thresholds
    min_reasoning_steps: int = 3             # Minimum reasoning chain length
    max_reasoning_steps: int = 15            # Maximum useful reasoning chain length
    
    # Compliance thresholds
    max_critical_violations: int = 0         # No critical violations allowed
    max_high_violations: int = 2            # Maximum high-severity violations
    
    # Evaluation behavior
    fail_on_critical_errors: bool = True     # Fail evaluation on critical errors
    detailed_logging: bool = True            # Enable detailed logging
    save_intermediate_results: bool = True   # Save step-by-step results
    
    # Model configuration
    evaluation_model: str = "gpt-4"          # Model for evaluation tasks
    temperature: float = 0.1                 # Low temperature for consistency
    max_tokens: int = 4000                   # Maximum tokens per evaluation
    
    # File paths and directories
    input_data_dir: str = "data/evaluation"
    output_results_dir: str = "results/evaluation"
    reference_data_dir: str = "data/reference"
    
    @classmethod
    def from_file(cls, config_path: Union[str, Path]) -> 'EvaluationConfig':
        """Load configuration from JSON file."""
        config_path = Path(config_path)
        if not config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")
        
        with open(config_path, 'r') as f:
            config_data = json.load(f)
        
        return cls(**config_data)
    
    @classmethod
    def from_env(cls) -> 'EvaluationConfig':
        """Create configuration from environment variables and defaults."""
        # Use settings from the app config plus evaluation-specific defaults
        return cls(
            evaluation_model=getattr(settings, 'evaluation_model', 'gpt-4'),
            detailed_logging=getattr(settings, 'debug', True),
            input_data_dir=getattr(settings, 'input_data_dir', 'data/evaluation'),
            output_results_dir=getattr(settings, 'output_results_dir', 'results/evaluation')
        )
    
    def validate(self) -> List[str]:
        """Validate configuration parameters."""
        errors = []
        
        # Check weight sum
        total_weight = (self.erp_accuracy_weight + self.reasoning_weight + 
                       self.compliance_weight + self.performance_weight)
        if abs(total_weight - 1.0) > 0.001:
            errors.append(f"Score weights must sum to 1.0, got {total_weight}")
        
        # Check thresholds
        if not 0 <= self.min_erp_accuracy_threshold <= 1:
            errors.append("min_erp_accuracy_threshold must be between 0 and 1")
        
        if not 0 <= self.target_erp_accuracy <= 1:
            errors.append("target_erp_accuracy must be between 0 and 1")
        
        if self.max_processing_time_ms <= 0:
            errors.append("max_processing_time_ms must be positive")
        
        if self.target_processing_time_ms <= 0:
            errors.append("target_processing_time_ms must be positive")
        
        if self.min_reasoning_steps < 1:
            errors.append("min_reasoning_steps must be at least 1")
        
        if self.max_reasoning_steps < self.min_reasoning_steps:
            errors.append("max_reasoning_steps must be >= min_reasoning_steps")
        
        return errors
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'erp_accuracy_weight': self.erp_accuracy_weight,
            'reasoning_weight': self.reasoning_weight,
            'compliance_weight': self.compliance_weight,
            'performance_weight': self.performance_weight,
            'min_erp_accuracy_threshold': self.min_erp_accuracy_threshold,
            'target_erp_accuracy': self.target_erp_accuracy,
            'max_processing_time_ms': self.max_processing_time_ms,
            'target_processing_time_ms': self.target_processing_time_ms,
            'min_reasoning_steps': self.min_reasoning_steps,
            'max_reasoning_steps': self.max_reasoning_steps,
            'max_critical_violations': self.max_critical_violations,
            'max_high_violations': self.max_high_violations,
            'fail_on_critical_errors': self.fail_on_critical_errors,
            'detailed_logging': self.detailed_logging,
            'save_intermediate_results': self.save_intermediate_results,
            'evaluation_model': self.evaluation_model,
            'temperature': self.temperature,
            'max_tokens': self.max_tokens,
            'input_data_dir': self.input_data_dir,
            'output_results_dir': self.output_results_dir,
            'reference_data_dir': self.reference_data_dir
        }