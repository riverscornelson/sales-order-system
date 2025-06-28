"""
Base evaluation class compatible with OpenAI Evals API structure.

This module provides the foundational evaluation framework that follows
OpenAI's Evals patterns for consistency and compatibility with analysis tools.
"""

import json
import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class EvalResult:
    """Single evaluation result following OpenAI Evals format."""
    
    # Core fields matching OpenAI Evals structure
    input: Dict[str, Any]
    target: Optional[Dict[str, Any]] = None
    output: Optional[Dict[str, Any]] = None
    
    # Scoring components
    score: float = 0.0  # Overall score [0.0, 1.0]
    accuracy: float = 0.0  # Primary accuracy metric
    
    # Metadata
    timestamp: datetime = field(default_factory=datetime.now)
    duration_ms: float = 0.0
    model_used: Optional[str] = None
    
    # Detailed scoring breakdown
    detailed_scores: Dict[str, float] = field(default_factory=dict)
    
    # Error tracking
    error: Optional[str] = None
    error_type: Optional[str] = None
    
    # Additional metadata for analysis
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format compatible with OpenAI Evals."""
        return {
            'input': self.input,
            'target': self.target,
            'output': self.output,
            'score': self.score,
            'accuracy': self.accuracy,
            'timestamp': self.timestamp.isoformat(),
            'duration_ms': self.duration_ms,
            'model_used': self.model_used,
            'detailed_scores': self.detailed_scores,
            'error': self.error,
            'error_type': self.error_type,
            'metadata': self.metadata
        }


@dataclass
class EvalMetrics:
    """Aggregate metrics across all evaluation samples."""
    
    # Core aggregate metrics
    total_samples: int = 0
    successful_samples: int = 0
    failed_samples: int = 0
    
    # Primary metrics
    mean_score: float = 0.0
    mean_accuracy: float = 0.0
    
    # Distribution metrics
    score_distribution: Dict[str, float] = field(default_factory=dict)
    accuracy_distribution: Dict[str, float] = field(default_factory=dict)
    
    # Performance metrics
    mean_duration_ms: float = 0.0
    total_duration_ms: float = 0.0
    
    # Detailed component metrics
    component_metrics: Dict[str, float] = field(default_factory=dict)
    
    # Error analysis
    error_breakdown: Dict[str, int] = field(default_factory=dict)
    
    # Evaluation metadata
    evaluation_id: str = ""
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format for reporting."""
        return {
            'total_samples': self.total_samples,
            'successful_samples': self.successful_samples,
            'failed_samples': self.failed_samples,
            'success_rate': self.successful_samples / max(self.total_samples, 1),
            'mean_score': self.mean_score,
            'mean_accuracy': self.mean_accuracy,
            'score_distribution': self.score_distribution,
            'accuracy_distribution': self.accuracy_distribution,
            'mean_duration_ms': self.mean_duration_ms,
            'total_duration_ms': self.total_duration_ms,
            'component_metrics': self.component_metrics,
            'error_breakdown': self.error_breakdown,
            'evaluation_id': self.evaluation_id,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None
        }


class BaseEval(ABC):
    """
    Base evaluation class following OpenAI Evals API structure.
    
    This class provides the foundational framework for evaluation that's
    compatible with OpenAI's evaluation tools and analysis pipeline.
    """
    
    def __init__(self, 
                 eval_name: str,
                 eval_description: str = "",
                 config: Optional[Dict[str, Any]] = None):
        """
        Initialize the base evaluation.
        
        Args:
            eval_name: Unique name for this evaluation
            eval_description: Human-readable description
            config: Optional configuration parameters
        """
        self.eval_name = eval_name
        self.eval_description = eval_description
        self.config = config or {}
        
        # Track evaluation state
        self.results: List[EvalResult] = []
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None
        
        # Setup logging
        self.logger = logging.getLogger(f"eval.{eval_name}")
        
    @abstractmethod
    def eval_sample(self, sample: Dict[str, Any]) -> EvalResult:
        """
        Evaluate a single sample.
        
        This is the core method that must be implemented by subclasses.
        It should take a sample input and return an EvalResult.
        
        Args:
            sample: Input sample containing the data to evaluate
            
        Returns:
            EvalResult: Detailed evaluation result for this sample
        """
        pass
    
    def run_evaluation(self, 
                      samples: List[Dict[str, Any]],
                      output_path: Optional[Union[str, Path]] = None) -> EvalMetrics:
        """
        Run evaluation on a list of samples.
        
        Args:
            samples: List of input samples to evaluate
            output_path: Optional path to save detailed results
            
        Returns:
            EvalMetrics: Aggregate metrics across all samples
        """
        self.logger.info(f"Starting evaluation '{self.eval_name}' with {len(samples)} samples")
        self.start_time = datetime.now()
        self.results = []
        
        try:
            for i, sample in enumerate(samples):
                try:
                    self.logger.debug(f"Evaluating sample {i + 1}/{len(samples)}")
                    result = self.eval_sample(sample)
                    self.results.append(result)
                    
                except Exception as e:
                    self.logger.error(f"Error evaluating sample {i + 1}: {e}")
                    # Create error result
                    error_result = EvalResult(
                        input=sample,
                        error=str(e),
                        error_type=type(e).__name__
                    )
                    self.results.append(error_result)
            
            self.end_time = datetime.now()
            
            # Calculate aggregate metrics
            metrics = self.get_metrics()
            
            # Save results if path provided
            if output_path:
                self._save_results(output_path, metrics)
            
            self.logger.info(f"Evaluation completed. Success rate: {metrics.successful_samples}/{metrics.total_samples}")
            return metrics
            
        except Exception as e:
            self.logger.error(f"Evaluation failed: {e}")
            raise
    
    def run_from_jsonl(self, 
                      jsonl_path: Union[str, Path],
                      output_path: Optional[Union[str, Path]] = None) -> EvalMetrics:
        """
        Run evaluation from JSONL file format (compatible with OpenAI Evals).
        
        Args:
            jsonl_path: Path to JSONL file containing samples
            output_path: Optional path to save results
            
        Returns:
            EvalMetrics: Aggregate evaluation metrics
        """
        samples = []
        jsonl_path = Path(jsonl_path)
        
        if not jsonl_path.exists():
            raise FileNotFoundError(f"JSONL file not found: {jsonl_path}")
        
        try:
            with open(jsonl_path, 'r') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if line:
                        try:
                            sample = json.loads(line)
                            samples.append(sample)
                        except json.JSONDecodeError as e:
                            self.logger.warning(f"Invalid JSON on line {line_num}: {e}")
            
            self.logger.info(f"Loaded {len(samples)} samples from {jsonl_path}")
            return self.run_evaluation(samples, output_path)
            
        except Exception as e:
            self.logger.error(f"Error reading JSONL file {jsonl_path}: {e}")
            raise
    
    def get_metrics(self) -> EvalMetrics:
        """
        Calculate aggregate metrics from evaluation results.
        
        Returns:
            EvalMetrics: Comprehensive metrics across all results
        """
        if not self.results:
            return EvalMetrics(evaluation_id=self.eval_name)
        
        # Basic counts
        total_samples = len(self.results)
        successful_samples = sum(1 for r in self.results if r.error is None)
        failed_samples = total_samples - successful_samples
        
        # Get successful results for metric calculation
        successful_results = [r for r in self.results if r.error is None]
        
        if not successful_results:
            return EvalMetrics(
                total_samples=total_samples,
                successful_samples=0,
                failed_samples=failed_samples,
                evaluation_id=self.eval_name,
                start_time=self.start_time,
                end_time=self.end_time,
                error_breakdown=self._get_error_breakdown()
            )
        
        # Calculate means
        mean_score = sum(r.score for r in successful_results) / len(successful_results)
        mean_accuracy = sum(r.accuracy for r in successful_results) / len(successful_results)
        mean_duration = sum(r.duration_ms for r in successful_results) / len(successful_results)
        total_duration = sum(r.duration_ms for r in self.results)
        
        # Calculate distributions
        score_distribution = self._calculate_distribution([r.score for r in successful_results])
        accuracy_distribution = self._calculate_distribution([r.accuracy for r in successful_results])
        
        # Calculate component metrics
        component_metrics = self._calculate_component_metrics(successful_results)
        
        return EvalMetrics(
            total_samples=total_samples,
            successful_samples=successful_samples,
            failed_samples=failed_samples,
            mean_score=mean_score,
            mean_accuracy=mean_accuracy,
            score_distribution=score_distribution,
            accuracy_distribution=accuracy_distribution,
            mean_duration_ms=mean_duration,
            total_duration_ms=total_duration,
            component_metrics=component_metrics,
            error_breakdown=self._get_error_breakdown(),
            evaluation_id=self.eval_name,
            start_time=self.start_time,
            end_time=self.end_time
        )
    
    def _calculate_distribution(self, values: List[float]) -> Dict[str, float]:
        """Calculate distribution statistics for a list of values."""
        if not values:
            return {}
        
        values_sorted = sorted(values)
        n = len(values_sorted)
        
        return {
            'min': min(values_sorted),
            'max': max(values_sorted),
            'median': values_sorted[n // 2] if n % 2 == 1 else (values_sorted[n // 2 - 1] + values_sorted[n // 2]) / 2,
            'p25': values_sorted[n // 4],
            'p75': values_sorted[3 * n // 4],
            'std': self._calculate_std(values_sorted)
        }
    
    def _calculate_std(self, values: List[float]) -> float:
        """Calculate standard deviation."""
        if len(values) < 2:
            return 0.0
        
        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / (len(values) - 1)
        return variance ** 0.5
    
    def _calculate_component_metrics(self, results: List[EvalResult]) -> Dict[str, float]:
        """Calculate metrics for individual score components."""
        if not results:
            return {}
        
        # Collect all component keys
        all_components = set()
        for result in results:
            all_components.update(result.detailed_scores.keys())
        
        # Calculate mean for each component
        component_metrics = {}
        for component in all_components:
            component_scores = [
                result.detailed_scores.get(component, 0.0) 
                for result in results 
                if component in result.detailed_scores
            ]
            if component_scores:
                component_metrics[f"{component}_mean"] = sum(component_scores) / len(component_scores)
        
        return component_metrics
    
    def _get_error_breakdown(self) -> Dict[str, int]:
        """Get breakdown of errors by type."""
        error_breakdown = {}
        for result in self.results:
            if result.error_type:
                error_breakdown[result.error_type] = error_breakdown.get(result.error_type, 0) + 1
        return error_breakdown
    
    def _save_results(self, output_path: Union[str, Path], metrics: EvalMetrics):
        """Save evaluation results and metrics to files."""
        output_path = Path(output_path)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Save detailed results as JSONL
        results_file = output_path / f"{self.eval_name}_results.jsonl"
        with open(results_file, 'w') as f:
            for result in self.results:
                f.write(json.dumps(result.to_dict()) + '\n')
        
        # Save aggregate metrics as JSON
        metrics_file = output_path / f"{self.eval_name}_metrics.json"
        with open(metrics_file, 'w') as f:
            json.dump(metrics.to_dict(), f, indent=2)
        
        self.logger.info(f"Results saved to {results_file}")
        self.logger.info(f"Metrics saved to {metrics_file}")