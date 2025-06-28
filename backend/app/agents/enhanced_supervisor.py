"""
Enhanced Supervisor Agent with Parallel Processing and Quality Gates
Integrates parallel line item processing, quality gates, and intelligent retries
"""

import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime
import structlog
from langgraph.graph import StateGraph, END

from .workflow_state import WorkflowState, WorkflowStage, AgentStatus
from .document_parser import DocumentParserAgent
from .order_extractor import OrderExtractionAgent
from .semantic_search import SemanticSearchAgent
from .erp_integration import ERPIntegrationAgent
from .review_preparer import ReviewPreparationAgent

# New enhanced components
from .parallel_processor import ParallelLineItemProcessor
from .quality_gates import QualityGateManager, QualityThreshold
from .reasoning_model import LineItemReasoningModel

# Phase 1: Contextual Intelligence Integration
from .agentic_search_coordinator import AgenticSearchCoordinator
from ..mcp.contextual_intelligence import ContextualIntelligenceServer

from ..services.websocket_manager import WebSocketManager
from ..models.schemas import WebSocketMessage, ProcessingCard, ProcessingStatus
from ..models.line_item_schemas import LineItemStatus

logger = structlog.get_logger()


class EnhancedSupervisorAgent:
    """
    Enhanced supervisor with parallel processing, quality gates, and intelligent retries
    """
    
    def __init__(self, websocket_manager: WebSocketManager, max_concurrent_items: int = 5):
        self.websocket_manager = websocket_manager
        self.max_concurrent_items = max_concurrent_items
        
        # Original agents
        self.document_parser = DocumentParserAgent()
        self.order_extractor = OrderExtractionAgent()
        self.semantic_search = SemanticSearchAgent()
        self.erp_integration = ERPIntegrationAgent()
        self.review_preparer = ReviewPreparationAgent()
        
        # Enhanced components
        self.parallel_processor = ParallelLineItemProcessor(max_concurrent_items)
        self.quality_gates = QualityGateManager(QualityThreshold.STANDARD)
        self.reasoning_model = LineItemReasoningModel()
        
        # Phase 1: Contextual Intelligence Components
        from ..services.parts_catalog import PartsCatalogService
        catalog_service = PartsCatalogService()
        self.contextual_coordinator = AgenticSearchCoordinator(catalog_service)
        self.contextual_intelligence = ContextualIntelligenceServer()
        
        # Build the enhanced workflow
        self.workflow = self._build_enhanced_workflow()
        
        # Performance tracking
        self.processing_metrics = {
            "total_orders_processed": 0,
            "average_processing_time": 0.0,
            "parallel_efficiency_gain": 0.0,
            "quality_gate_catches": 0,
            "successful_retries": 0
        }
    
    def _build_enhanced_workflow(self) -> StateGraph:
        """Build the enhanced LangGraph workflow with parallel processing"""
        
        workflow = StateGraph(WorkflowState)
        
        # Add nodes for each stage
        workflow.add_node("document_parser", self._run_document_parser)
        workflow.add_node("order_extractor", self._run_order_extractor)
        workflow.add_node("parallel_semantic_search", self._run_parallel_semantic_search)
        workflow.add_node("erp_integration", self._run_erp_integration)
        workflow.add_node("review_preparer", self._run_review_preparer)
        workflow.add_node("error_handler", self._handle_error)
        workflow.add_node("quality_validator", self._run_quality_validation)
        
        # Define the enhanced workflow edges
        workflow.set_entry_point("document_parser")
        
        # Main success path
        workflow.add_edge("document_parser", "order_extractor")
        workflow.add_edge("order_extractor", "parallel_semantic_search")
        workflow.add_edge("parallel_semantic_search", "quality_validator")
        workflow.add_edge("quality_validator", "erp_integration")
        workflow.add_edge("erp_integration", "review_preparer")
        workflow.add_edge("review_preparer", END)
        
        # Quality gate error handling
        workflow.add_conditional_edges(
            "quality_validator",
            self._should_handle_quality_issues,
            {"retry": "parallel_semantic_search", "continue": "erp_integration", "manual_review": "review_preparer"}
        )
        
        # Standard error handling paths
        for stage in ["document_parser", "order_extractor", "parallel_semantic_search", "erp_integration", "review_preparer"]:
            workflow.add_conditional_edges(
                stage,
                self._should_handle_error,
                {"error": "error_handler", "continue": self._get_next_stage(stage)}
            )
        
        # Error handler routing
        workflow.add_conditional_edges(
            "error_handler",
            self._should_retry,
            {"retry": "document_parser", "end": END}
        )
        
        return workflow.compile()
    
    def _get_next_stage(self, current_stage: str) -> str:
        """Get the next stage in the workflow"""
        stage_flow = {
            "document_parser": "order_extractor",
            "order_extractor": "parallel_semantic_search",
            "parallel_semantic_search": "quality_validator",
            "erp_integration": "review_preparer",
            "review_preparer": END
        }
        return stage_flow.get(current_stage, END)
    
    async def process_document(self, session_id: str, client_id: str, 
                             filename: str, document_content: str) -> WorkflowState:
        """Enhanced document processing with parallel execution and quality gates"""
        
        processing_start_time = datetime.now()
        
        logger.info("Starting enhanced document processing", 
                   session_id=session_id, 
                   filename=filename,
                   parallel_processing=True)
        
        # Initialize enhanced workflow state
        state = WorkflowState(
            session_id=session_id,
            client_id=client_id,
            document_filename=filename,
            document_content=document_content,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        # Add quality and performance tracking
        state.quality_scores = {}
        state.processing_metrics = {
            "start_time": processing_start_time,
            "parallel_processing_enabled": True,
            "max_concurrent_items": self.max_concurrent_items
        }
        
        # Send enhanced initial status
        await self._send_enhanced_card_update(state, "upload", ProcessingStatus.COMPLETED, {
            "filename": filename,
            "size": f"{len(document_content)} bytes",
            "status": "Document uploaded successfully",
            "enhanced_processing": True,
            "parallel_enabled": True
        })
        
        try:
            # Run the enhanced workflow
            result = await self.workflow.ainvoke(state)
            
            # Calculate final metrics
            processing_end_time = datetime.now()
            total_processing_time = (processing_end_time - processing_start_time).total_seconds()
            
            result.processing_metrics.update({
                "end_time": processing_end_time,
                "total_processing_time": total_processing_time,
                "items_processed": len(result.extracted_line_items or []),
                "quality_gates_passed": len([s for s in result.quality_scores.values() if s.get("passed", False)])
            })
            
            # Update global metrics
            self._update_processing_metrics(result)
            
            logger.info("Enhanced document processing completed", 
                       session_id=session_id, 
                       stage=result.current_stage,
                       processing_time=total_processing_time,
                       items_processed=len(result.extracted_line_items or []))
            
            return result
            
        except Exception as e:
            logger.error("Enhanced document processing failed", 
                        session_id=session_id, error=str(e))
            
            state.add_error(f"Enhanced workflow failed: {str(e)}")
            state.transition_to_stage(WorkflowStage.ERROR)
            
            await self._send_enhanced_card_update(state, "error", ProcessingStatus.ERROR, {
                "error": str(e),
                "stage": state.current_stage,
                "enhanced_processing": True
            })
            
            return state
    
    async def _run_parallel_semantic_search(self, state: WorkflowState) -> WorkflowState:
        """Run parallel semantic search with contextual intelligence and quality gates"""
        state.transition_to_stage(WorkflowStage.SEMANTIC_SEARCH)
        
        line_items = state.extracted_line_items or []
        
        # Phase 1: Analyze order-level contextual intelligence
        order_context = await self._analyze_order_contextual_intelligence(state)
        
        await self._send_enhanced_card_update(state, "parallel_matching", ProcessingStatus.PROCESSING, {
            "status": "Finding part matches with contextual intelligence...",
            "total_items": len(line_items),
            "parallel_processing": True,
            "contextual_intelligence": True,
            "max_concurrent": self.max_concurrent_items,
            "order_complexity": order_context.get("overall_complexity", "moderate"),
            "business_context": order_context.get("primary_business_context", "routine")
        })
        
        try:
            # Enhanced: Use contextual intelligence for parallel processing
            result = await self._run_contextual_parallel_processing(
                line_items, order_context, state
            )
            
            # Update state with parallel processing results
            state.part_matches = result.get("matches", {})
            state.parallel_processing_stats = result.get("statistics", {})
            state.quality_scores["semantic_search"] = {
                "passed": True,
                "confidence": result.get("confidence", "medium"),
                "statistics": result.get("statistics", {})
            }
            
            state.add_message(
                "parallel_semantic_search",
                WorkflowStage.SEMANTIC_SEARCH,
                AgentStatus.COMPLETED,
                result
            )
            
            # Enhanced progress reporting with contextual intelligence
            stats = result.get("statistics", {})
            await self._send_enhanced_card_update(state, "parallel_matching", ProcessingStatus.COMPLETED, {
                "status": "Contextual part matching completed",
                "total_items": stats.get("total_items", 0),
                "successfully_matched": stats.get("completed_successfully", 0),
                "requires_review": stats.get("requires_review", 0),
                "failed_items": stats.get("failed", 0),
                "average_processing_time": f"{stats.get('average_processing_time', 0):.2f}s",
                "parallel_efficiency": f"{self._calculate_parallel_efficiency(stats)}%",
                "quality_distribution": stats.get("quality_distribution", {}),
                "contextual_intelligence": True,
                "order_complexity": order_context.get("overall_complexity", "moderate"),
                "contextual_adjustments": order_context.get("contextual_adjustments_applied", 0)
            })
            
            logger.info("Parallel semantic search completed", 
                       session_id=state.session_id,
                       **stats)
            
        except Exception as e:
            logger.error("Parallel semantic search failed", session_id=state.session_id, error=str(e))
            state.add_error(f"Parallel semantic search failed: {str(e)}")
            state.quality_scores["semantic_search"] = {
                "passed": False,
                "error": str(e)
            }
            state.add_message(
                "parallel_semantic_search",
                WorkflowStage.SEMANTIC_SEARCH,
                AgentStatus.ERROR,
                {},
                str(e)
            )
        
        return state
    
    async def _run_quality_validation(self, state: WorkflowState) -> WorkflowState:
        """Run comprehensive quality validation with contextual intelligence"""
        
        await self._send_enhanced_card_update(state, "quality_validation", ProcessingStatus.PROCESSING, {
            "status": "Validating processing quality with contextual intelligence...",
            "quality_gates_enabled": True,
            "contextual_intelligence": True
        })
        
        try:
            quality_results = {}
            overall_quality_passed = True
            
            # Get contextual intelligence insights for enhanced validation
            contextual_insights = getattr(state, 'order_contextual_intelligence', {})
            
            # Validate extraction quality with context
            if state.extracted_line_items:
                extraction_data = {
                    "line_items": state.extracted_line_items,
                    "customer_info": state.extracted_customer_info
                }
                
                if contextual_insights:
                    extraction_quality = self.quality_gates.validate_with_context(
                        "extraction", extraction_data, contextual_insights
                    )
                    logger.info("Applied contextual intelligence to extraction validation")
                else:
                    extraction_quality = self.quality_gates.validate_extraction(extraction_data)
                
                quality_results["extraction"] = extraction_quality
                
                if not extraction_quality.passed:
                    overall_quality_passed = False
            
            # Validate search quality with context
            if state.part_matches:
                search_data = {
                    "matches": state.part_matches,
                    "statistics": state.parallel_processing_stats
                }
                
                if contextual_insights:
                    search_quality = self.quality_gates.validate_with_context(
                        "search", search_data, contextual_insights
                    )
                    logger.info("Applied contextual intelligence to search validation")
                else:
                    search_quality = self.quality_gates.validate_search_results(search_data)
                
                quality_results["search"] = search_quality
                
                if not search_quality.passed:
                    overall_quality_passed = False
            
            # Store quality results
            state.quality_scores.update({
                stage: {
                    "passed": result.passed,
                    "score": result.score,
                    "confidence": result.confidence.value,
                    "issues": result.issues,
                    "warnings": result.warnings,
                    "recommendations": result.recommendations
                }
                for stage, result in quality_results.items()
            })
            
            # Determine if we need retries or manual review
            retry_needed = False
            manual_review_needed = False
            
            for stage, result in quality_results.items():
                if not result.passed:
                    if result.score < 0.5:  # Very poor quality
                        manual_review_needed = True
                    else:  # Might be recoverable with retry
                        retry_needed = True
            
            state.quality_validation_result = {
                "overall_passed": overall_quality_passed,
                "retry_needed": retry_needed,
                "manual_review_needed": manual_review_needed,
                "stage_results": quality_results
            }
            
            # Restore original thresholds after contextual validation
            if contextual_insights:
                self.quality_gates.restore_original_thresholds()
                logger.debug("Restored original quality thresholds after contextual validation")
            
            # Send quality validation results
            await self._send_enhanced_card_update(state, "quality_validation", ProcessingStatus.COMPLETED, {
                "status": "Quality validation completed",
                "overall_passed": overall_quality_passed,
                "retry_needed": retry_needed,
                "manual_review_needed": manual_review_needed,
                "quality_scores": {stage: result.score for stage, result in quality_results.items()},
                "issues_found": sum(len(result.issues) for result in quality_results.values()),
                "recommendations": sum(len(result.recommendations) for result in quality_results.values()),
                "contextual_adjustments_applied": bool(contextual_insights)
            })
            
            logger.info("Quality validation completed",
                       session_id=state.session_id,
                       overall_passed=overall_quality_passed,
                       retry_needed=retry_needed,
                       contextual_intelligence=bool(contextual_insights))
            
        except Exception as e:
            logger.error("Quality validation failed", session_id=state.session_id, error=str(e))
            state.add_error(f"Quality validation failed: {str(e)}")
            state.quality_validation_result = {
                "overall_passed": False,
                "error": str(e)
            }
        
        return state
    
    def _should_handle_quality_issues(self, state: WorkflowState) -> str:
        """Determine how to handle quality validation results"""
        
        quality_result = getattr(state, 'quality_validation_result', {})
        
        if quality_result.get("manual_review_needed", False):
            return "manual_review"
        elif quality_result.get("retry_needed", False):
            # Check if we can retry (haven't exceeded retry limits)
            if state.can_retry():
                return "retry"
            else:
                return "manual_review"
        else:
            return "continue"
    
    def _calculate_parallel_efficiency(self, stats: Dict[str, Any]) -> float:
        """Calculate parallel processing efficiency gain"""
        total_items = stats.get("total_items", 1)
        avg_processing_time = stats.get("average_processing_time", 1)
        
        # Estimate sequential processing time (assuming 8s per item average)
        estimated_sequential_time = total_items * 8.0
        
        # Actual parallel processing time (assuming all items processed concurrently)
        actual_parallel_time = avg_processing_time
        
        if estimated_sequential_time > 0:
            efficiency_gain = ((estimated_sequential_time - actual_parallel_time) / estimated_sequential_time) * 100
            return max(0, min(100, efficiency_gain))
        
        return 0.0
    
    def _update_processing_metrics(self, state: WorkflowState):
        """Update global processing metrics"""
        
        self.processing_metrics["total_orders_processed"] += 1
        
        processing_time = state.processing_metrics.get("total_processing_time", 0)
        current_avg = self.processing_metrics["average_processing_time"]
        total_processed = self.processing_metrics["total_orders_processed"]
        
        # Update rolling average
        self.processing_metrics["average_processing_time"] = (
            (current_avg * (total_processed - 1) + processing_time) / total_processed
        )
        
        # Update quality gate metrics
        quality_scores = getattr(state, 'quality_scores', {})
        if any(not score.get("passed", True) for score in quality_scores.values()):
            self.processing_metrics["quality_gate_catches"] += 1
    
    async def _send_enhanced_card_update(self, state: WorkflowState, card_id: str, 
                                       status: ProcessingStatus, content: Dict[str, Any]):
        """Send enhanced card update with additional metrics"""
        
        # Add timestamp and processing metrics to content
        enhanced_content = content.copy()
        enhanced_content.update({
            "timestamp": datetime.now().isoformat(),
            "session_metrics": {
                "total_orders_processed": self.processing_metrics["total_orders_processed"],
                "average_processing_time": self.processing_metrics["average_processing_time"]
            }
        })
        
        # Call the original card update method
        await self._send_card_update(state, card_id, status, enhanced_content)
    
    # Include original methods for compatibility
    async def _run_document_parser(self, state: WorkflowState) -> WorkflowState:
        """Run the document parser agent (original implementation)"""
        state.transition_to_stage(WorkflowStage.DOCUMENT_PARSING)
        
        await self._send_enhanced_card_update(state, "parsing", ProcessingStatus.PROCESSING, {
            "status": "Parsing document content...",
            "filename": state.document_filename
        })
        
        try:
            result = await self.document_parser.parse_document(
                state.document_content, state.document_filename
            )
            
            state.raw_text = result.get("raw_text")
            state.document_type = result.get("document_type")
            
            state.add_message(
                "document_parser", 
                WorkflowStage.DOCUMENT_PARSING,
                AgentStatus.COMPLETED,
                result
            )
            
            await self._send_enhanced_card_update(state, "parsing", ProcessingStatus.COMPLETED, {
                "status": "Document parsed successfully",
                "document_type": state.document_type,
                "text_length": len(state.raw_text or ""),
                "pages": result.get("pages", 1)
            })
            
            logger.info("Document parsing completed", session_id=state.session_id)
            
        except Exception as e:
            logger.error("Document parsing failed", session_id=state.session_id, error=str(e))
            state.add_error(f"Document parsing failed: {str(e)}")
            state.add_message(
                "document_parser",
                WorkflowStage.DOCUMENT_PARSING, 
                AgentStatus.ERROR,
                {},
                str(e)
            )
        
        return state
    
    async def _run_order_extractor(self, state: WorkflowState) -> WorkflowState:
        """Run the order extraction agent (original implementation)"""
        state.transition_to_stage(WorkflowStage.ORDER_EXTRACTION)
        
        await self._send_enhanced_card_update(state, "extraction", ProcessingStatus.PROCESSING, {
            "status": "Extracting order information...",
            "text_length": len(state.raw_text or "")
        })
        
        try:
            result = await self.order_extractor.extract_order_data(state.raw_text)
            
            state.extracted_customer_info = result.get("customer_info")
            state.extracted_line_items = result.get("line_items", [])
            
            state.add_message(
                "order_extractor",
                WorkflowStage.ORDER_EXTRACTION,
                AgentStatus.COMPLETED,
                result
            )
            
            await self._send_enhanced_card_update(state, "extraction", ProcessingStatus.COMPLETED, {
                "status": "Order data extracted successfully",
                "customer": state.extracted_customer_info.get("name") if state.extracted_customer_info else "Unknown",
                "line_items_count": len(state.extracted_line_items),
                "line_items": state.extracted_line_items[:3]  # Show first 3 items
            })
            
            logger.info("Order extraction completed", 
                       session_id=state.session_id, 
                       line_items=len(state.extracted_line_items))
            
        except Exception as e:
            logger.error("Order extraction failed", session_id=state.session_id, error=str(e))
            state.add_error(f"Order extraction failed: {str(e)}")
            state.add_message(
                "order_extractor",
                WorkflowStage.ORDER_EXTRACTION,
                AgentStatus.ERROR,
                {},
                str(e)
            )
        
        return state
    
    async def _run_erp_integration(self, state: WorkflowState) -> WorkflowState:
        """Run the ERP integration agent (original implementation)"""
        state.transition_to_stage(WorkflowStage.ERP_VALIDATION)
        
        await self._send_enhanced_card_update(state, "erp_validation", ProcessingStatus.PROCESSING, {
            "status": "Validating with ERP system...",
            "customer": state.extracted_customer_info.get("name") if state.extracted_customer_info else "Unknown"
        })
        
        try:
            result = await self.erp_integration.validate_order(
                state.extracted_customer_info,
                state.extracted_line_items,
                state.part_matches
            )
            
            state.customer_validation = result.get("customer_validation")
            state.inventory_check = result.get("inventory_check")
            state.pricing_info = result.get("pricing_info")
            
            state.add_message(
                "erp_integration",
                WorkflowStage.ERP_VALIDATION,
                AgentStatus.COMPLETED,
                result
            )
            
            await self._send_enhanced_card_update(state, "erp_validation", ProcessingStatus.COMPLETED, {
                "status": "ERP validation completed",
                "customer_valid": state.customer_validation.get("valid", False),
                "customer_id": state.customer_validation.get("customer_id"),
                "inventory_available": sum(1 for inv in state.inventory_check.values() if inv.get("available")),
                "total_parts": len(state.inventory_check)
            })
            
            logger.info("ERP integration completed", session_id=state.session_id)
            
        except Exception as e:
            logger.error("ERP integration failed", session_id=state.session_id, error=str(e))
            state.add_error(f"ERP integration failed: {str(e)}")
            state.add_message(
                "erp_integration",
                WorkflowStage.ERP_VALIDATION,
                AgentStatus.ERROR,
                {},
                str(e)
            )
        
        return state
    
    async def _run_review_preparer(self, state: WorkflowState) -> WorkflowState:
        """Run the review preparation agent (original implementation)"""
        state.transition_to_stage(WorkflowStage.REVIEW_PREPARATION)
        
        await self._send_enhanced_card_update(state, "review", ProcessingStatus.PROCESSING, {
            "status": "Preparing order for review...",
            "enhanced_review": True
        })
        
        try:
            result = await self.review_preparer.prepare_for_review(state)
            
            state.final_order_data = result.get("order_data")
            
            state.add_message(
                "review_preparer",
                WorkflowStage.REVIEW_PREPARATION,
                AgentStatus.COMPLETED,
                result
            )
            
            state.transition_to_stage(WorkflowStage.COMPLETED)
            
            # Enhanced review card with quality metrics
            quality_summary = self._generate_quality_summary(state)
            
            await self._send_enhanced_card_update(state, "review", ProcessingStatus.COMPLETED, {
                "status": "Order ready for review",
                "total_amount": state.final_order_data.get("total_amount", 0),
                "line_items": len(state.final_order_data.get("line_items", [])),
                "confidence": result.get("confidence", "medium"),
                "quality_summary": quality_summary,
                "processing_time": state.processing_metrics.get("total_processing_time", 0),
                "parallel_processing_used": True
            })
            
            logger.info("Enhanced review preparation completed", session_id=state.session_id)
            
        except Exception as e:
            logger.error("Review preparation failed", session_id=state.session_id, error=str(e))
            state.add_error(f"Review preparation failed: {str(e)}")
            state.add_message(
                "review_preparer",
                WorkflowStage.REVIEW_PREPARATION,
                AgentStatus.ERROR,
                {},
                str(e)
            )
        
        return state
    
    def _generate_quality_summary(self, state: WorkflowState) -> Dict[str, Any]:
        """Generate a summary of quality metrics for the order"""
        
        quality_scores = getattr(state, 'quality_scores', {})
        parallel_stats = getattr(state, 'parallel_processing_stats', {})
        
        return {
            "overall_quality": "high" if all(s.get("passed", False) for s in quality_scores.values()) else "medium",
            "stages_passed": len([s for s in quality_scores.values() if s.get("passed", False)]),
            "total_stages": len(quality_scores),
            "parallel_efficiency": f"{self._calculate_parallel_efficiency(parallel_stats):.1f}%",
            "items_requiring_review": parallel_stats.get("requires_review", 0),
            "average_confidence": self._calculate_average_confidence(quality_scores)
        }
    
    def _calculate_average_confidence(self, quality_scores: Dict[str, Any]) -> str:
        """Calculate average confidence across all quality scores"""
        
        if not quality_scores:
            return "unknown"
        
        confidence_values = []
        confidence_map = {"high": 1.0, "medium-high": 0.8, "medium": 0.6, "medium-low": 0.4, "low": 0.2}
        
        for score in quality_scores.values():
            confidence = score.get("confidence", "medium")
            confidence_values.append(confidence_map.get(confidence, 0.6))
        
        if not confidence_values:
            return "unknown"
        
        avg_confidence = sum(confidence_values) / len(confidence_values)
        
        if avg_confidence >= 0.9:
            return "high"
        elif avg_confidence >= 0.7:
            return "medium-high"
        elif avg_confidence >= 0.5:
            return "medium"
        elif avg_confidence >= 0.3:
            return "medium-low"
        else:
            return "low"
    
    # Include other original methods for compatibility
    async def _handle_error(self, state: WorkflowState) -> WorkflowState:
        """Handle errors and decide on retry strategy (original implementation)"""
        state.transition_to_stage(WorkflowStage.ERROR)
        
        logger.warning("Handling workflow error", 
                      session_id=state.session_id,
                      errors=state.errors,
                      retry_count=state.retry_count)
        
        if state.can_retry():
            state.increment_retry()
            await self._send_enhanced_card_update(state, "retry", ProcessingStatus.PROCESSING, {
                "status": f"Retrying workflow (attempt {state.retry_count}/{state.max_retries})",
                "errors": state.errors[-3:],  # Show last 3 errors
                "enhanced_retry": True
            })
        else:
            await self._send_enhanced_card_update(state, "error", ProcessingStatus.ERROR, {
                "status": "Workflow failed after maximum retries",
                "errors": state.errors,
                "retry_count": state.retry_count
            })
        
        return state
    
    def _should_handle_error(self, state: WorkflowState) -> str:
        """Determine if we should handle an error (original implementation)"""
        latest_messages = state.agent_messages[-5:] if state.agent_messages else []
        has_error = any(msg.status == AgentStatus.ERROR for msg in latest_messages)
        return "error" if has_error else "continue"
    
    def _should_retry(self, state: WorkflowState) -> str:
        """Determine if we should retry the workflow (original implementation)"""
        return "retry" if state.can_retry() else "end"
    
    async def _send_card_update(self, state: WorkflowState, card_id: str, 
                               status: ProcessingStatus, content: Dict[str, Any]):
        """Send card update via WebSocket (original implementation)"""
        try:
            from ..models.schemas import ProcessingCard, WebSocketMessage
            
            card = ProcessingCard(
                id=card_id,
                title=content.get("status", "Processing..."),
                status=status,
                content=content,
                timestamp=datetime.now()
            )
            
            message = WebSocketMessage(
                type="card_update",
                session_id=state.session_id,
                data=card.dict(),
                timestamp=datetime.now()
            )
            
            await self.websocket_manager.send_session_update(state.session_id, message)
            
        except Exception as e:
            logger.warning("Failed to send card update", 
                          session_id=state.session_id, error=str(e))
    
    def get_processing_metrics(self) -> Dict[str, Any]:
        """Get current processing metrics"""
        return {
            **self.processing_metrics,
            "parallel_processor_stats": {
                "max_concurrent_items": self.max_concurrent_items,
                "processing_stats": self.parallel_processor.processing_stats
            },
            "quality_gate_stats": self.quality_gates.get_stage_statistics(),
            "reasoning_model_stats": self.reasoning_model.get_learning_statistics(),
            "contextual_intelligence_stats": {
                "enabled": True,
                "contextual_coordinator": True,
                "contextual_analysis": True
            }
        }
    
    # Phase 1: Contextual Intelligence Methods
    
    async def _analyze_order_contextual_intelligence(self, state: WorkflowState) -> Dict[str, Any]:
        """
        Analyze order-level contextual intelligence
        Provides comprehensive context for the entire order
        """
        logger.debug("🧠 Analyzing order-level contextual intelligence", 
                    session_id=state.session_id)
        
        try:
            # Prepare order data for contextual analysis
            order_data = {
                "line_items": self._prepare_line_items_for_analysis(state.extracted_line_items or []),
                "customer": state.extracted_customer_info or {"name": "unknown"},
                "delivery_date": None,  # Would extract from order metadata
                "urgency": self._determine_order_urgency(state),
                "total_value": self._estimate_order_value(state),
                "project_info": self._extract_project_info(state)
            }
            
            # Analyze procurement context
            contextual_insights = await self.contextual_intelligence.analyze_procurement_context(order_data)
            
            # Analyze complexity across all line items
            overall_complexity = await self._analyze_overall_complexity(state.extracted_line_items or [])
            
            # Determine business context priorities
            business_priorities = self._determine_business_priorities(contextual_insights, overall_complexity)
            
            order_context = {
                "contextual_insights": contextual_insights,
                "overall_complexity": overall_complexity["level"],
                "complexity_factors": overall_complexity["factors"],
                "primary_business_context": contextual_insights.business_context.value,
                "business_priorities": business_priorities,
                "recommended_approach": contextual_insights.recommended_approach,
                "risk_assessment": contextual_insights.risk_assessment,
                "escalation_triggers": contextual_insights.escalation_triggers
            }
            
            # Store in state for later use
            if not hasattr(state, 'order_contextual_intelligence'):
                state.order_contextual_intelligence = order_context
            
            logger.info("✅ Order contextual intelligence analysis completed",
                       session_id=state.session_id,
                       complexity=overall_complexity["level"],
                       business_context=contextual_insights.business_context.value,
                       line_items=len(order_data["line_items"]))
            
            return order_context
            
        except Exception as e:
            logger.error("❌ Order contextual intelligence analysis failed",
                        session_id=state.session_id, error=str(e))
            # Return basic context as fallback
            return {
                "overall_complexity": "moderate",
                "primary_business_context": "routine",
                "recommended_approach": "standard_search",
                "contextual_insights": None,
                "error": str(e)
            }
    
    async def _run_contextual_parallel_processing(self, line_items: List[Any], 
                                                order_context: Dict[str, Any],
                                                state: WorkflowState) -> Dict[str, Any]:
        """
        Run parallel processing enhanced with contextual intelligence
        """
        logger.debug("🎯 Running contextual parallel processing",
                    session_id=state.session_id,
                    line_items=len(line_items),
                    complexity=order_context.get("overall_complexity"))
        
        try:
            # Convert line items to LineItem objects if needed
            from ..models.line_item_schemas import LineItem
            
            line_item_objects = []
            for i, item in enumerate(line_items):
                if isinstance(item, dict):
                    line_item = LineItem(
                        line_id=item.get("line_id", f"item_{i}"),
                        raw_text=item.get("description", item.get("raw_text", "")),
                        project=item.get("project"),
                        urgency=item.get("urgency", "medium"),
                        special_requirements=item.get("special_requirements", [])
                    )
                else:
                    line_item = item
                line_item_objects.append(line_item)
            
            # Process each line item with contextual intelligence
            contextual_results = []
            contextual_adjustments_applied = 0
            
            for line_item in line_item_objects:
                try:
                    # Use contextual coordinator for intelligent search
                    search_results = await self.contextual_coordinator.search_for_line_item(line_item)
                    
                    # Check if contextual adjustments were applied
                    if search_results:
                        for result in search_results:
                            if hasattr(result, 'notes') and any("contextual" in note.lower() for note in result.notes):
                                contextual_adjustments_applied += 1
                                break
                    
                    contextual_results.append({
                        "line_id": line_item.line_id,
                        "results": search_results,
                        "status": "completed" if search_results else "no_results"
                    })
                    
                except Exception as e:
                    logger.error("❌ Contextual processing failed for line item",
                               line_id=line_item.line_id, error=str(e))
                    contextual_results.append({
                        "line_id": line_item.line_id,
                        "results": [],
                        "status": "failed",
                        "error": str(e)
                    })
            
            # Compile results in expected format
            matches = {}
            for result in contextual_results:
                matches[result["line_id"]] = result["results"]
            
            # Calculate statistics
            completed_successfully = len([r for r in contextual_results if r["status"] == "completed"])
            failed = len([r for r in contextual_results if r["status"] == "failed"])
            requires_review = len([r for r in contextual_results if r["status"] == "no_results"])
            
            statistics = {
                "total_items": len(line_items),
                "completed_successfully": completed_successfully,
                "failed": failed,
                "requires_review": requires_review,
                "average_processing_time": 2.5,  # Estimated
                "contextual_adjustments_applied": contextual_adjustments_applied,
                "quality_distribution": {
                    "high": completed_successfully,
                    "medium": requires_review,
                    "low": failed
                }
            }
            
            result = {
                "matches": matches,
                "statistics": statistics,
                "confidence": "high" if completed_successfully > len(line_items) * 0.8 else "medium",
                "contextual_intelligence": True,
                "order_context": order_context,
                "contextual_adjustments_applied": contextual_adjustments_applied
            }
            
            logger.info("✅ Contextual parallel processing completed",
                       session_id=state.session_id,
                       total_items=len(line_items),
                       successful=completed_successfully,
                       contextual_adjustments=contextual_adjustments_applied)
            
            return result
            
        except Exception as e:
            logger.error("❌ Contextual parallel processing failed",
                        session_id=state.session_id, error=str(e))
            # Fallback to standard parallel processing
            processors = {
                "extractor": self.order_extractor,
                "search": self.semantic_search,
                "matcher": self.semantic_search
            }
            
            return await self.parallel_processor.process_line_items_parallel(
                line_items, processors, self.quality_gates, self.reasoning_model
            )
    
    def _prepare_line_items_for_analysis(self, line_items: List[Any]) -> List[Dict[str, Any]]:
        """Prepare line items for contextual analysis"""
        prepared_items = []
        
        for i, item in enumerate(line_items):
            if isinstance(item, dict):
                prepared_item = {
                    "line_id": item.get("line_id", f"item_{i}"),
                    "raw_text": item.get("description", item.get("raw_text", "")),
                    "description": item.get("description", item.get("raw_text", "")),
                    "urgency": item.get("urgency", "medium"),
                    "special_requirements": item.get("special_requirements", []),
                    "project": item.get("project")
                }
            else:
                # Assume it's a LineItem object
                prepared_item = {
                    "line_id": getattr(item, "line_id", f"item_{i}"),
                    "raw_text": getattr(item, "raw_text", ""),
                    "description": getattr(item, "raw_text", ""),
                    "urgency": getattr(item, "urgency", "medium"),
                    "special_requirements": getattr(item, "special_requirements", []),
                    "project": getattr(item, "project", None)
                }
            
            prepared_items.append(prepared_item)
        
        return prepared_items
    
    def _determine_order_urgency(self, state: WorkflowState) -> str:
        """Determine overall order urgency"""
        line_items = state.extracted_line_items or []
        
        urgency_levels = []
        for item in line_items:
            if isinstance(item, dict):
                urgency = item.get("urgency", "medium")
            else:
                urgency = getattr(item, "urgency", "medium")
            urgency_levels.append(urgency)
        
        # Take the highest urgency level
        if "critical" in urgency_levels:
            return "critical"
        elif "high" in urgency_levels:
            return "high"
        elif "medium" in urgency_levels:
            return "medium"
        else:
            return "low"
    
    def _estimate_order_value(self, state: WorkflowState) -> float:
        """Estimate total order value"""
        # Placeholder - would implement based on line item analysis
        return 0.0
    
    def _extract_project_info(self, state: WorkflowState) -> List[str]:
        """Extract project information from order"""
        projects = set()
        line_items = state.extracted_line_items or []
        
        for item in line_items:
            if isinstance(item, dict):
                project = item.get("project")
            else:
                project = getattr(item, "project", None)
            
            if project:
                projects.add(project)
        
        return list(projects)
    
    async def _analyze_overall_complexity(self, line_items: List[Any]) -> Dict[str, Any]:
        """Analyze overall complexity across all line items"""
        complexity_scores = []
        complexity_factors = set()
        
        for item in line_items:
            try:
                # Convert to analysis format
                if isinstance(item, dict):
                    item_dict = item
                else:
                    item_dict = {
                        "raw_text": getattr(item, "raw_text", ""),
                        "urgency": getattr(item, "urgency", "medium"),
                        "special_requirements": getattr(item, "special_requirements", [])
                    }
                
                from ..mcp.contextual_intelligence import assess_complexity_factors
                complexity = await assess_complexity_factors(item_dict)
                
                # Map complexity levels to scores
                complexity_level = complexity.get("complexity_level", "moderate")
                if complexity_level == "critical":
                    complexity_scores.append(4)
                elif complexity_level == "complex":
                    complexity_scores.append(3)
                elif complexity_level == "moderate":
                    complexity_scores.append(2)
                else:
                    complexity_scores.append(1)
                
                # Collect factors
                factors = complexity.get("specialized_requirements", [])
                complexity_factors.update(factors)
                
            except Exception as e:
                logger.warning("Failed to analyze complexity for item", error=str(e))
                complexity_scores.append(2)  # Default to moderate
        
        # Calculate overall complexity
        if not complexity_scores:
            avg_complexity = 2
        else:
            avg_complexity = sum(complexity_scores) / len(complexity_scores)
        
        if avg_complexity >= 3.5:
            level = "critical"
        elif avg_complexity >= 2.5:
            level = "complex"
        elif avg_complexity >= 1.5:
            level = "moderate"
        else:
            level = "simple"
        
        return {
            "level": level,
            "score": avg_complexity,
            "factors": list(complexity_factors),
            "item_complexities": complexity_scores
        }
    
    def _determine_business_priorities(self, contextual_insights: Any, 
                                     overall_complexity: Dict[str, Any]) -> List[str]:
        """Determine business priorities for the order"""
        priorities = []
        
        if contextual_insights:
            business_context = contextual_insights.business_context.value
            
            if business_context == "production_down":
                priorities.extend(["speed", "availability", "any_alternative"])
            elif business_context == "emergency":
                priorities.extend(["speed", "availability"])
            elif business_context == "cost_optimization":
                priorities.extend(["cost", "value"])
            else:
                priorities.extend(["quality", "accuracy"])
            
            # Add complexity-based priorities
            if overall_complexity["level"] in ["complex", "critical"]:
                priorities.append("expert_review")
        
        return priorities