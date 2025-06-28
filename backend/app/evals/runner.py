"""
Evaluation runner utilities for the Sales Order Intelligence system.

This module provides high-level functions for running evaluations,
handling error cases, and generating comprehensive reports.
"""

import logging
import json
import traceback
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from .base_eval import EvalMetrics, EvalResult
from .sales_order_eval import SalesOrderIntelligenceEval
from .config import load_evaluation_config
from .data_structures import EvaluationConfig

logger = logging.getLogger(__name__)


class EvaluationRunner:
    """
    High-level evaluation runner with comprehensive error handling and reporting.
    
    This class provides a robust interface for running evaluations with
    proper error handling, logging, and result management.
    """
    
    def __init__(self, 
                 config: Optional[EvaluationConfig] = None,
                 output_dir: Optional[Union[str, Path]] = None):
        """
        Initialize evaluation runner.
        
        Args:
            config: Evaluation configuration
            output_dir: Directory for output files
        """
        self.config = config or load_evaluation_config()
        self.output_dir = Path(output_dir) if output_dir else Path(self.config.output_results_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Setup evaluation-specific logging
        self._setup_logging()
        
        logger.info(f"Initialized evaluation runner with output dir: {self.output_dir}")
    
    def run_evaluation_from_jsonl(self, 
                                 jsonl_path: Union[str, Path],
                                 evaluation_id: Optional[str] = None) -> EvalMetrics:
        """
        Run evaluation from JSONL file with comprehensive error handling.
        
        Args:
            jsonl_path: Path to JSONL file containing evaluation samples
            evaluation_id: Optional unique identifier for this evaluation run
            
        Returns:
            EvalMetrics: Comprehensive evaluation results
        """
        jsonl_path = Path(jsonl_path)
        evaluation_id = evaluation_id or f"eval_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        logger.info(f"Starting evaluation run '{evaluation_id}' from {jsonl_path}")
        
        try:
            # Validate input file
            if not jsonl_path.exists():
                raise FileNotFoundError(f"Evaluation file not found: {jsonl_path}")
            
            # Create evaluator
            evaluator = SalesOrderIntelligenceEval(
                config=self.config,
                erp_schema_path=self._get_erp_schema_path()
            )
            
            # Setup output directory for this run
            run_output_dir = self.output_dir / evaluation_id
            run_output_dir.mkdir(parents=True, exist_ok=True)
            
            # Run evaluation
            logger.info("Running evaluation...")
            metrics = evaluator.run_from_jsonl(jsonl_path, run_output_dir)
            
            # Generate comprehensive report
            report_path = self._generate_evaluation_report(metrics, evaluator, run_output_dir)
            
            # Log summary
            self._log_evaluation_summary(metrics, evaluation_id)
            
            logger.info(f"Evaluation completed successfully. Report: {report_path}")
            return metrics
            
        except Exception as e:
            logger.error(f"Evaluation failed: {e}")
            logger.debug(f"Traceback: {traceback.format_exc()}")
            
            # Create error report
            self._create_error_report(e, evaluation_id, jsonl_path)
            raise
    
    async def evaluate_single_sample(self, 
                                   sample: Dict[str, Any],
                                   sample_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Evaluate a single sample and return simplified result dict.
        
        Args:
            sample: Single evaluation sample
            sample_id: Optional identifier for the sample
            
        Returns:
            Dict with evaluation results
        """
        sample_id = sample_id or sample.get('id', f"sample_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}")
        
        logger.info(f"Evaluating single sample: {sample_id}")
        
        try:
            evaluator = SalesOrderIntelligenceEval(
                config=self.config,
                erp_schema_path=self._get_erp_schema_path()
            )
            
            result = await evaluator.eval_sample(sample)
            
            # Convert to simplified dict
            result_dict = {
                'sample_id': sample_id,
                'overall_score': result.score,
                'erp_accuracy': result.accuracy,
                'processing_time_ms': result.processing_time_ms,
                'detailed_scores': result.detailed_scores,
                'success': result.error is None,
                'error': result.error
            }
            
            # Save single result
            result_file = self.output_dir / f"{sample_id}_result.json"
            with open(result_file, 'w') as f:
                json.dump(result_dict, f, indent=2)
            
            logger.info(f"Sample evaluation completed. Score: {result.score:.3f}, ERP Accuracy: {result.accuracy:.3f}")
            return result_dict
            
        except Exception as e:
            logger.error(f"Single sample evaluation failed: {e}")
            logger.debug(f"Traceback: {traceback.format_exc()}")
            raise

    def run_single_sample_evaluation(self, 
                                   sample: Dict[str, Any],
                                   sample_id: Optional[str] = None) -> EvalResult:
        """
        Run evaluation on a single sample with error handling.
        
        Args:
            sample: Single evaluation sample
            sample_id: Optional identifier for the sample
            
        Returns:
            EvalResult: Detailed result for the sample
        """
        sample_id = sample_id or f"sample_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
        
        logger.info(f"Evaluating single sample: {sample_id}")
        
        try:
            evaluator = SalesOrderIntelligenceEval(
                config=self.config,
                erp_schema_path=self._get_erp_schema_path()
            )
            
            result = evaluator.eval_sample(sample)
            
            # Save single result
            result_file = self.output_dir / f"{sample_id}_result.json"
            with open(result_file, 'w') as f:
                json.dump(result.to_dict(), f, indent=2)
            
            logger.info(f"Sample evaluation completed. Score: {result.score:.3f}, ERP Accuracy: {result.accuracy:.3f}")
            return result
            
        except Exception as e:
            logger.error(f"Single sample evaluation failed: {e}")
            logger.debug(f"Traceback: {traceback.format_exc()}")
            raise
    
    def validate_evaluation_data(self, jsonl_path: Union[str, Path]) -> Dict[str, Any]:
        """
        Validate evaluation data file and return summary.
        
        Args:
            jsonl_path: Path to JSONL evaluation file
            
        Returns:
            Dict containing validation results and data summary
        """
        jsonl_path = Path(jsonl_path)
        
        validation_result = {
            'file_exists': jsonl_path.exists(),
            'total_samples': 0,
            'valid_samples': 0,
            'invalid_samples': 0,
            'validation_errors': [],
            'sample_types': {},
            'has_expected_outputs': 0,
            'missing_fields': []
        }
        
        if not validation_result['file_exists']:
            validation_result['validation_errors'].append(f"File not found: {jsonl_path}")
            return validation_result
        
        try:
            with open(jsonl_path, 'r') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if not line:
                        continue
                    
                    validation_result['total_samples'] += 1
                    
                    try:
                        sample = json.loads(line)
                        
                        # Validate sample structure
                        errors = self._validate_sample_structure(sample)
                        if errors:
                            validation_result['invalid_samples'] += 1
                            validation_result['validation_errors'].extend([f"Line {line_num}: {error}" for error in errors])
                        else:
                            validation_result['valid_samples'] += 1
                        
                        # Track sample characteristics
                        if 'input' in sample:
                            doc_type = sample['input'].get('document_type', 'unknown')
                            validation_result['sample_types'][doc_type] = validation_result['sample_types'].get(doc_type, 0) + 1
                        
                        if 'expected_output' in sample:
                            validation_result['has_expected_outputs'] += 1
                        
                    except json.JSONDecodeError as e:
                        validation_result['invalid_samples'] += 1
                        validation_result['validation_errors'].append(f"Line {line_num}: Invalid JSON - {e}")
            
            # Summary validation
            if validation_result['valid_samples'] == 0:
                validation_result['validation_errors'].append("No valid samples found")
            
            logger.info(f"Validation completed: {validation_result['valid_samples']}/{validation_result['total_samples']} valid samples")
            
        except Exception as e:
            validation_result['validation_errors'].append(f"Error reading file: {e}")
        
        return validation_result
    
    def _validate_sample_structure(self, sample: Dict[str, Any]) -> List[str]:
        """Validate the structure of a single sample."""
        errors = []
        
        # Check required top-level fields
        if 'input' not in sample:
            errors.append("Missing 'input' field")
        
        if 'expected_output' not in sample:
            errors.append("Missing 'expected_output' field")
        
        # Validate input structure
        if 'input' in sample:
            input_data = sample['input']
            if not isinstance(input_data, dict):
                errors.append("'input' must be a dictionary")
            else:
                if 'document_content' not in input_data:
                    errors.append("Missing 'document_content' in input")
                if 'document_type' not in input_data:
                    errors.append("Missing 'document_type' in input")
        
        # Validate expected_output structure
        if 'expected_output' in sample:
            expected = sample['expected_output']
            if not isinstance(expected, dict):
                errors.append("'expected_output' must be a dictionary")
            else:
                if 'erp_json' not in expected:
                    errors.append("Missing 'erp_json' in expected_output")
        
        return errors
    
    def _setup_logging(self):
        """Setup evaluation-specific logging."""
        if self.config.detailed_logging:
            # Create evaluation log file
            log_file = self.output_dir / "evaluation.log"
            
            # Create file handler
            file_handler = logging.FileHandler(log_file)
            file_handler.setLevel(logging.DEBUG)
            
            # Create formatter
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            file_handler.setFormatter(formatter)
            
            # Add handler to evaluation loggers
            eval_logger = logging.getLogger('eval')
            eval_logger.addHandler(file_handler)
            eval_logger.setLevel(logging.DEBUG)
    
    def _get_erp_schema_path(self) -> Optional[str]:
        """Get path to ERP schema file."""
        schema_path = Path(self.config.reference_data_dir) / "erp_schema.json"
        return str(schema_path) if schema_path.exists() else None
    
    def _generate_evaluation_report(self, 
                                  metrics: EvalMetrics, 
                                  evaluator: SalesOrderIntelligenceEval,
                                  output_dir: Path) -> Path:
        """Generate comprehensive evaluation report."""
        report_data = {
            'evaluation_summary': metrics.to_dict(),
            'configuration': self.config.to_dict(),
            'detailed_analysis': self._analyze_results(evaluator.results),
            'recommendations': self._generate_recommendations(metrics),
            'generated_at': datetime.now().isoformat()
        }
        
        report_file = output_dir / "evaluation_report.json"
        with open(report_file, 'w') as f:
            json.dump(report_data, f, indent=2)
        
        # Also create a human-readable summary
        self._create_human_readable_report(report_data, output_dir)
        
        return report_file
    
    def _analyze_results(self, results: List[EvalResult]) -> Dict[str, Any]:
        """Analyze evaluation results for insights."""
        analysis = {
            'score_distribution': {},
            'common_errors': {},
            'performance_patterns': {},
            'erp_accuracy_insights': {}
        }
        
        if not results:
            return analysis
        
        # Score distribution analysis
        successful_results = [r for r in results if r.error is None]
        if successful_results:
            scores = [r.score for r in successful_results]
            accuracies = [r.accuracy for r in successful_results]
            
            analysis['score_distribution'] = {
                'mean_score': sum(scores) / len(scores),
                'mean_accuracy': sum(accuracies) / len(accuracies),
                'score_std': self._calculate_std(scores),
                'accuracy_std': self._calculate_std(accuracies)
            }
        
        # Error analysis
        error_counts = {}
        for result in results:
            if result.error:
                error_type = result.error_type or 'Unknown'
                error_counts[error_type] = error_counts.get(error_type, 0) + 1
        
        analysis['common_errors'] = error_counts
        
        # ERP accuracy specific insights
        erp_scores = []
        for result in successful_results:
            if 'erp_accuracy' in result.detailed_scores:
                erp_scores.append(result.detailed_scores['erp_accuracy'])
        
        if erp_scores:
            analysis['erp_accuracy_insights'] = {
                'mean_erp_accuracy': sum(erp_scores) / len(erp_scores),
                'below_threshold_count': sum(1 for score in erp_scores if score < self.config.min_erp_accuracy_threshold),
                'excellent_count': sum(1 for score in erp_scores if score >= self.config.target_erp_accuracy)
            }
        
        return analysis
    
    def _calculate_std(self, values: List[float]) -> float:
        """Calculate standard deviation."""
        if len(values) < 2:
            return 0.0
        
        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / (len(values) - 1)
        return variance ** 0.5
    
    def _generate_recommendations(self, metrics: EvalMetrics) -> List[str]:
        """Generate recommendations based on evaluation results."""
        recommendations = []
        
        if metrics.mean_accuracy < self.config.min_erp_accuracy_threshold:
            recommendations.append(
                f"ERP accuracy ({metrics.mean_accuracy:.3f}) is below minimum threshold "
                f"({self.config.min_erp_accuracy_threshold}). Focus on improving document parsing and field extraction."
            )
        
        if metrics.failed_samples > 0:
            failure_rate = metrics.failed_samples / metrics.total_samples
            if failure_rate > 0.1:
                recommendations.append(
                    f"High failure rate ({failure_rate:.1%}). Review error handling and input validation."
                )
        
        if metrics.mean_duration_ms > self.config.max_processing_time_ms:
            recommendations.append(
                f"Processing time ({metrics.mean_duration_ms:.0f}ms) exceeds maximum threshold "
                f"({self.config.max_processing_time_ms:.0f}ms). Consider performance optimization."
            )
        
        if metrics.mean_accuracy >= self.config.target_erp_accuracy:
            recommendations.append(
                "Excellent ERP accuracy achieved! Consider increasing target thresholds or focusing on edge cases."
            )
        
        return recommendations
    
    def _create_human_readable_report(self, report_data: Dict[str, Any], output_dir: Path):
        """Create a human-readable evaluation report."""
        summary = report_data['evaluation_summary']
        
        report_lines = [
            "# Sales Order Intelligence Evaluation Report",
            f"Generated: {report_data['generated_at']}",
            "",
            "## Summary",
            f"- Total Samples: {summary['total_samples']}",
            f"- Successful: {summary['successful_samples']}",
            f"- Failed: {summary['failed_samples']}",
            f"- Success Rate: {summary.get('success_rate', 0):.1%}",
            "",
            "## Scores",
            f"- Overall Score: {summary['mean_score']:.3f}",
            f"- ERP Accuracy (PRIMARY): {summary['mean_accuracy']:.3f}",
            f"- Processing Time: {summary['mean_duration_ms']:.0f}ms",
            "",
            "## Component Scores"
        ]
        
        # Add component scores if available
        if 'component_metrics' in summary:
            for component, score in summary['component_metrics'].items():
                if component.endswith('_mean'):
                    component_name = component.replace('_mean', '').replace('_', ' ').title()
                    report_lines.append(f"- {component_name}: {score:.3f}")
        
        # Add recommendations
        if 'recommendations' in report_data and report_data['recommendations']:
            report_lines.extend([
                "",
                "## Recommendations"
            ])
            for i, rec in enumerate(report_data['recommendations'], 1):
                report_lines.append(f"{i}. {rec}")
        
        # Save human-readable report
        report_file = output_dir / "evaluation_summary.md"
        with open(report_file, 'w') as f:
            f.write('\n'.join(report_lines))
    
    def _log_evaluation_summary(self, metrics: EvalMetrics, evaluation_id: str):
        """Log evaluation summary."""
        logger.info(f"=== Evaluation Summary: {evaluation_id} ===")
        logger.info(f"Total Samples: {metrics.total_samples}")
        logger.info(f"Successful: {metrics.successful_samples}")
        logger.info(f"Failed: {metrics.failed_samples}")
        logger.info(f"Success Rate: {metrics.successful_samples / max(metrics.total_samples, 1):.1%}")
        logger.info(f"Mean Overall Score: {metrics.mean_score:.3f}")
        logger.info(f"Mean ERP Accuracy: {metrics.mean_accuracy:.3f}")
        logger.info(f"Mean Processing Time: {metrics.mean_duration_ms:.0f}ms")
        
        if metrics.mean_accuracy < self.config.min_erp_accuracy_threshold:
            logger.warning(f"ERP accuracy below threshold ({self.config.min_erp_accuracy_threshold})")
        
        logger.info("=" * 50)
    
    def _create_error_report(self, error: Exception, evaluation_id: str, input_file: Path):
        """Create error report for failed evaluations."""
        error_report = {
            'evaluation_id': evaluation_id,
            'input_file': str(input_file),
            'error_type': type(error).__name__,
            'error_message': str(error),
            'traceback': traceback.format_exc(),
            'timestamp': datetime.now().isoformat(),
            'configuration': self.config.to_dict()
        }
        
        error_file = self.output_dir / f"{evaluation_id}_error.json"
        try:
            with open(error_file, 'w') as f:
                json.dump(error_report, f, indent=2)
            logger.info(f"Error report saved: {error_file}")
        except Exception as e:
            logger.error(f"Failed to save error report: {e}")


def run_evaluation(jsonl_path: Union[str, Path], 
                  config: Optional[EvaluationConfig] = None,
                  output_dir: Optional[Union[str, Path]] = None,
                  evaluation_id: Optional[str] = None) -> EvalMetrics:
    """
    Convenience function to run evaluation with default settings.
    
    Args:
        jsonl_path: Path to evaluation data file
        config: Optional evaluation configuration
        output_dir: Optional output directory
        evaluation_id: Optional evaluation identifier
        
    Returns:
        EvalMetrics: Evaluation results
    """
    runner = EvaluationRunner(config=config, output_dir=output_dir)
    return runner.run_evaluation_from_jsonl(jsonl_path, evaluation_id)