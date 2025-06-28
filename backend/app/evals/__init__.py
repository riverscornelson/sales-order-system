"""
Evaluation infrastructure for the Sales Order Intelligence System.

This module provides OpenAI Evals compatible evaluation framework for:
- ERP JSON accuracy assessment (primary metric - 40% of total score)
- Reasoning quality evaluation (20%)
- Business compliance validation (20%)
- Performance benchmarking (20%)

Key Features:
- OpenAI Evals API compatibility
- Comprehensive ERP JSON accuracy scoring
- Standardized JSONL input/output format
- Detailed error handling and logging
- Flexible configuration management
- Human-readable and machine-readable reports

Usage Example:
    from app.evals import run_evaluation, EvaluationConfig
    
    # Load configuration
    config = EvaluationConfig.from_env()
    
    # Run evaluation
    metrics = run_evaluation(
        jsonl_path="data/evaluation/test_samples.jsonl",
        config=config,
        evaluation_id="production_test_v1"
    )
    
    print(f"ERP Accuracy: {metrics.mean_accuracy:.3f}")
    print(f"Overall Score: {metrics.mean_score:.3f}")
"""

from .base_eval import BaseEval, EvalResult, EvalMetrics
from .sales_order_eval import SalesOrderIntelligenceEval
from .data_structures import (
    ERPAccuracyScore,
    ReasoningScore,
    ComplianceScore,
    PerformanceScore,
    EvaluationConfig
)
from .config import (
    EvaluationConfigManager,
    load_evaluation_config,
    create_config_template
)
from .runner import EvaluationRunner, run_evaluation

__all__ = [
    # Core evaluation classes
    'BaseEval',
    'EvalResult', 
    'EvalMetrics',
    'SalesOrderIntelligenceEval',
    
    # Scoring components
    'ERPAccuracyScore',
    'ReasoningScore',
    'ComplianceScore',
    'PerformanceScore',
    
    # Configuration
    'EvaluationConfig',
    'EvaluationConfigManager',
    'load_evaluation_config',
    'create_config_template',
    
    # High-level interface
    'EvaluationRunner',
    'run_evaluation'
]

# Version info
__version__ = "1.0.0"
__author__ = "Sales Order Intelligence Team"
__description__ = "OpenAI Evals compatible evaluation framework with ERP JSON focus"