"""
Parallel Line Item Processing Engine
Handles concurrent processing of line items with quality gates and intelligent routing
"""

import asyncio
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass
from enum import Enum
import structlog

from ..models.line_item_schemas import (
    LineItem, LineItemStatus, ProcessingStage, MatchConfidence,
    ExtractedSpecs, SearchResult, MatchSelection
)

logger = structlog.get_logger()


class ProcessingPriority(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class ProcessingTask:
    """Individual processing task for a line item"""
    line_item: LineItem
    priority: ProcessingPriority
    retry_count: int = 0
    max_retries: int = 3
    created_at: datetime = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()


class ParallelLineItemProcessor:
    """
    Parallel processor for line items with quality gates and intelligent routing
    """
    
    def __init__(self, max_concurrent_tasks: int = 5):
        self.max_concurrent_tasks = max_concurrent_tasks
        self.semaphore = asyncio.Semaphore(max_concurrent_tasks)
        self.processing_stats = {
            "total_items": 0,
            "completed_items": 0,
            "failed_items": 0,
            "retried_items": 0,
            "avg_processing_time": 0.0
        }
    
    async def process_line_items_parallel(
        self, 
        line_items: List[Dict[str, Any]], 
        processors: Dict[str, Any],
        quality_gates: 'QualityGateManager',
        reasoning_model: 'LineItemReasoningModel'
    ) -> Dict[str, Any]:
        """
        Process multiple line items in parallel with quality gates
        
        Args:
            line_items: List of extracted line items
            processors: Dictionary of processing agents
            quality_gates: Quality gate manager for validation
            reasoning_model: Reasoning model for intelligent retries
            
        Returns:
            Processing results with matches, stats, and quality metrics
        """
        logger.info("Starting parallel line item processing", 
                   total_items=len(line_items))
        
        # Convert to processing tasks
        tasks = self._create_processing_tasks(line_items)
        
        # Process tasks in parallel batches
        results = await self._process_tasks_in_batches(
            tasks, processors, quality_gates, reasoning_model
        )
        
        # Compile final results
        return self._compile_results(results, tasks)
    
    def _create_processing_tasks(self, line_items: List[Dict[str, Any]]) -> List[ProcessingTask]:
        """Create processing tasks from line items with priority assignment"""
        tasks = []
        
        for i, item_data in enumerate(line_items):
            # Create LineItem object
            line_item = LineItem(
                line_id=f"item_{i}",
                raw_text=item_data.get("description", ""),
                extracted_specs=self._extract_specs_from_item(item_data)
            )
            
            # Assign priority based on item characteristics
            priority = self._determine_priority(line_item)
            
            task = ProcessingTask(
                line_item=line_item,
                priority=priority
            )
            tasks.append(task)
        
        # Sort by priority (high first)
        tasks.sort(key=lambda t: (t.priority.value, t.created_at))
        return tasks
    
    def _determine_priority(self, line_item: LineItem) -> ProcessingPriority:
        """Determine processing priority based on line item characteristics"""
        # High priority for items with clear part numbers or urgent delivery
        if line_item.urgency == "HIGH":
            return ProcessingPriority.HIGH
        
        # Check for clear part number patterns
        text = line_item.raw_text.upper()
        if any(pattern in text for pattern in ["PN:", "PART#", "P/N", "ITEM#"]):
            return ProcessingPriority.HIGH
        
        # Medium priority for standard items
        if len(line_item.raw_text.split()) >= 3:
            return ProcessingPriority.MEDIUM
        
        # Low priority for unclear or short descriptions
        return ProcessingPriority.LOW
    
    def _extract_specs_from_item(self, item_data: Dict[str, Any]) -> Optional[ExtractedSpecs]:
        """Extract structured specifications from item data"""
        try:
            return ExtractedSpecs(
                quantity=item_data.get("quantity"),
                units=item_data.get("units"),
                material_grade=item_data.get("material"),
                dimensions=item_data.get("dimensions")
            )
        except Exception as e:
            logger.warning("Failed to extract specs", error=str(e))
            return None
    
    async def _process_tasks_in_batches(
        self,
        tasks: List[ProcessingTask],
        processors: Dict[str, Any],
        quality_gates: 'QualityGateManager',
        reasoning_model: 'LineItemReasoningModel'
    ) -> List[Tuple[ProcessingTask, Dict[str, Any]]]:
        """Process tasks in parallel batches with concurrency control"""
        
        # Create semaphore-controlled processing coroutines
        async def process_single_task(task: ProcessingTask) -> Tuple[ProcessingTask, Dict[str, Any]]:
            async with self.semaphore:
                return await self._process_single_line_item(
                    task, processors, quality_gates, reasoning_model
                )
        
        # Execute all tasks concurrently
        coroutines = [process_single_task(task) for task in tasks]
        results = await asyncio.gather(*coroutines, return_exceptions=True)
        
        # Handle exceptions
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Task {i} failed with exception", error=str(result))
                error_result = (tasks[i], {"error": str(result), "matches": []})
                processed_results.append(error_result)
            else:
                processed_results.append(result)
        
        return processed_results
    
    async def _process_single_line_item(
        self,
        task: ProcessingTask,
        processors: Dict[str, Any],
        quality_gates: 'QualityGateManager',
        reasoning_model: 'LineItemReasoningModel'
    ) -> Tuple[ProcessingTask, Dict[str, Any]]:
        """Process a single line item through the full pipeline"""
        task.started_at = datetime.now()
        line_item = task.line_item
        
        logger.debug("Processing line item", 
                    line_id=line_item.line_id,
                    priority=task.priority,
                    retry_count=task.retry_count)
        
        try:
            # Stage 1: Enhanced Extraction
            line_item.status = LineItemStatus.EXTRACTING
            line_item.current_stage = ProcessingStage.EXTRACTION
            
            extraction_result = await processors['extractor'].extract_line_item_specs(
                line_item.raw_text
            )
            
            # Quality Gate 1: Extraction Quality
            extraction_quality = quality_gates.validate_extraction(extraction_result)
            if not extraction_quality.passed:
                return await self._handle_quality_failure(
                    task, "extraction", extraction_quality, 
                    processors, quality_gates, reasoning_model
                )
            
            # Update line item with extracted data
            line_item.extracted_specs = extraction_result.get("specs")
            line_item.status = LineItemStatus.SEARCHING
            line_item.current_stage = ProcessingStage.SEMANTIC_SEARCH
            
            # Stage 2: Semantic Search
            search_result = await processors['search'].find_matches_for_single_item(
                line_item.raw_text, line_item.extracted_specs
            )
            
            # Quality Gate 2: Search Quality
            search_quality = quality_gates.validate_search_results(search_result)
            if not search_quality.passed:
                return await self._handle_quality_failure(
                    task, "search", search_quality,
                    processors, quality_gates, reasoning_model
                )
            
            # Stage 3: Match Selection
            line_item.status = LineItemStatus.MATCHING
            line_item.current_stage = ProcessingStage.MATCHING
            
            match_result = await processors['matcher'].select_best_match(
                line_item, search_result.get("matches", [])
            )
            
            # Quality Gate 3: Match Quality
            match_quality = quality_gates.validate_match_selection(match_result)
            if not match_quality.passed:
                return await self._handle_quality_failure(
                    task, "matching", match_quality,
                    processors, quality_gates, reasoning_model
                )
            
            # Success - update final status
            line_item.status = LineItemStatus.MATCHED
            line_item.selected_match = match_result.get("selected_match")
            line_item.match_confidence = match_result.get("confidence")
            line_item.processing_end_time = datetime.now()
            
            task.completed_at = datetime.now()
            
            return task, {
                "line_item": line_item,
                "matches": search_result.get("matches", []),
                "selected_match": match_result.get("selected_match"),
                "confidence": match_result.get("confidence"),
                "processing_time": (task.completed_at - task.started_at).total_seconds(),
                "retry_count": task.retry_count,
                "quality_scores": {
                    "extraction": extraction_quality.score,
                    "search": search_quality.score,
                    "matching": match_quality.score
                }
            }
            
        except Exception as e:
            logger.error("Line item processing failed", 
                        line_id=line_item.line_id, 
                        error=str(e))
            
            line_item.status = LineItemStatus.FAILED
            line_item.issues.append(f"Processing failed: {str(e)}")
            
            return task, {
                "line_item": line_item,
                "error": str(e),
                "matches": [],
                "retry_count": task.retry_count
            }
    
    async def _handle_quality_failure(
        self,
        task: ProcessingTask,
        stage: str,
        quality_result: 'QualityGateResult',
        processors: Dict[str, Any],
        quality_gates: 'QualityGateManager',
        reasoning_model: 'LineItemReasoningModel'
    ) -> Tuple[ProcessingTask, Dict[str, Any]]:
        """Handle quality gate failures with intelligent retry logic"""
        
        logger.warning("Quality gate failure", 
                      line_id=task.line_item.line_id,
                      stage=stage,
                      score=quality_result.score,
                      issues=quality_result.issues)
        
        # Check if we should retry
        if task.retry_count < task.max_retries:
            # Use reasoning model to determine retry strategy
            retry_strategy = await reasoning_model.analyze_failure_and_suggest_retry(
                task.line_item, stage, quality_result
            )
            
            if retry_strategy.should_retry:
                logger.info("Retrying with modified strategy",
                           line_id=task.line_item.line_id,
                           strategy=retry_strategy.strategy_name)
                
                task.retry_count += 1
                # Apply the suggested modifications and retry
                return await self._retry_with_strategy(
                    task, retry_strategy, processors, quality_gates, reasoning_model
                )
        
        # No retry or max retries reached - mark for manual review
        task.line_item.status = LineItemStatus.MANUAL_REVIEW
        task.line_item.requires_approval = True
        task.line_item.issues.extend(quality_result.issues)
        
        return task, {
            "line_item": task.line_item,
            "quality_failure": {
                "stage": stage,
                "score": quality_result.score,
                "issues": quality_result.issues
            },
            "requires_manual_review": True,
            "retry_count": task.retry_count
        }
    
    async def _retry_with_strategy(
        self,
        task: ProcessingTask,
        retry_recommendation: 'RetryRecommendation',
        processors: Dict[str, Any],
        quality_gates: 'QualityGateManager',
        reasoning_model: 'LineItemReasoningModel'
    ) -> Tuple[ProcessingTask, Dict[str, Any]]:
        """Retry processing with modified strategy"""
        
        # Apply strategy modifications to processors
        modified_processors = retry_recommendation.apply_modifications(processors)
        
        # Reset line item status for retry
        task.line_item.status = LineItemStatus.PENDING
        task.line_item.issues.append(f"Retry #{task.retry_count} with {retry_recommendation.strategy_name}")
        
        # Recursive call with modified processors
        return await self._process_single_line_item(
            task, modified_processors, quality_gates, reasoning_model
        )
    
    def _compile_results(
        self, 
        results: List[Tuple[ProcessingTask, Dict[str, Any]]], 
        original_tasks: List[ProcessingTask]
    ) -> Dict[str, Any]:
        """Compile final processing results with statistics"""
        
        compiled_matches = {}
        quality_stats = {
            "high_confidence": 0,
            "medium_confidence": 0,
            "low_confidence": 0,
            "manual_review_required": 0,
            "failed": 0
        }
        
        processing_times = []
        
        for task, result in results:
            line_id = task.line_item.line_id
            compiled_matches[line_id] = result
            
            # Update quality statistics
            if result.get("requires_manual_review"):
                quality_stats["manual_review_required"] += 1
            elif result.get("error"):
                quality_stats["failed"] += 1
            else:
                confidence = result.get("confidence", MatchConfidence.LOW)
                if confidence == MatchConfidence.HIGH:
                    quality_stats["high_confidence"] += 1
                elif confidence in [MatchConfidence.MEDIUM_HIGH, MatchConfidence.MEDIUM]:
                    quality_stats["medium_confidence"] += 1
                else:
                    quality_stats["low_confidence"] += 1
            
            # Track processing times
            if "processing_time" in result:
                processing_times.append(result["processing_time"])
        
        # Calculate overall statistics
        total_items = len(original_tasks)
        avg_processing_time = sum(processing_times) / len(processing_times) if processing_times else 0
        
        return {
            "matches": compiled_matches,
            "statistics": {
                "total_items": total_items,
                "completed_successfully": quality_stats["high_confidence"] + quality_stats["medium_confidence"],
                "requires_review": quality_stats["manual_review_required"] + quality_stats["low_confidence"],
                "failed": quality_stats["failed"],
                "average_processing_time": avg_processing_time,
                "quality_distribution": quality_stats
            },
            "confidence": self._calculate_overall_confidence(quality_stats, total_items),
            "parallel_processing_enabled": True,
            "max_concurrent_tasks": self.max_concurrent_tasks
        }
    
    def _calculate_overall_confidence(self, quality_stats: Dict[str, int], total_items: int) -> str:
        """Calculate overall processing confidence"""
        if total_items == 0:
            return "unknown"
        
        high_rate = quality_stats["high_confidence"] / total_items
        success_rate = (quality_stats["high_confidence"] + quality_stats["medium_confidence"]) / total_items
        
        if high_rate >= 0.8:
            return "high"
        elif success_rate >= 0.7:
            return "medium-high"
        elif success_rate >= 0.5:
            return "medium"
        else:
            return "low"