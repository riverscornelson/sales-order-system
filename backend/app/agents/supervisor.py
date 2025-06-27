import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime
import structlog
from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage

from .workflow_state import WorkflowState, WorkflowStage, AgentStatus
from .document_parser import DocumentParserAgent
from .order_extractor import OrderExtractionAgent
from .semantic_search import SemanticSearchAgent
from .erp_integration import ERPIntegrationAgent
from .review_preparer import ReviewPreparationAgent
from ..services.websocket_manager import WebSocketManager
from ..models.schemas import WebSocketMessage, ProcessingCard, ProcessingStatus

logger = structlog.get_logger()

class SupervisorAgent:
    """Main supervisor agent that orchestrates the entire workflow"""
    
    def __init__(self, websocket_manager: WebSocketManager):
        self.websocket_manager = websocket_manager
        self.document_parser = DocumentParserAgent()
        self.order_extractor = OrderExtractionAgent()
        self.semantic_search = SemanticSearchAgent()
        self.erp_integration = ERPIntegrationAgent()
        self.review_preparer = ReviewPreparationAgent()
        
        # Build the workflow graph
        self.workflow = self._build_workflow()
    
    def _build_workflow(self) -> StateGraph:
        """Build the LangGraph workflow"""
        
        # Define the workflow nodes
        workflow = StateGraph(WorkflowState)
        
        # Add nodes for each agent
        workflow.add_node("document_parser", self._run_document_parser)
        workflow.add_node("order_extractor", self._run_order_extractor)
        workflow.add_node("semantic_search", self._run_semantic_search)
        workflow.add_node("erp_integration", self._run_erp_integration)
        workflow.add_node("review_preparer", self._run_review_preparer)
        workflow.add_node("error_handler", self._handle_error)
        
        # Define the workflow edges
        workflow.set_entry_point("document_parser")
        
        # Success path
        workflow.add_edge("document_parser", "order_extractor")
        workflow.add_edge("order_extractor", "semantic_search")
        workflow.add_edge("semantic_search", "erp_integration")
        workflow.add_edge("erp_integration", "review_preparer")
        workflow.add_edge("review_preparer", END)
        
        # Error handling paths
        workflow.add_conditional_edges(
            "document_parser",
            self._should_handle_error,
            {"error": "error_handler", "continue": "order_extractor"}
        )
        
        workflow.add_conditional_edges(
            "order_extractor", 
            self._should_handle_error,
            {"error": "error_handler", "continue": "semantic_search"}
        )
        
        workflow.add_conditional_edges(
            "semantic_search",
            self._should_handle_error,
            {"error": "error_handler", "continue": "erp_integration"}
        )
        
        workflow.add_conditional_edges(
            "erp_integration",
            self._should_handle_error,
            {"error": "error_handler", "continue": "review_preparer"}
        )
        
        workflow.add_conditional_edges(
            "review_preparer",
            self._should_handle_error,
            {"error": "error_handler", "continue": END}
        )
        
        # Error handler can either retry or end
        workflow.add_conditional_edges(
            "error_handler",
            self._should_retry,
            {"retry": "document_parser", "end": END}
        )
        
        return workflow.compile()
    
    async def process_document(self, session_id: str, client_id: str, 
                             filename: str, document_content: str) -> WorkflowState:
        """Main entry point to process a document through the workflow"""
        
        logger.info("Starting document processing", 
                   session_id=session_id, filename=filename)
        
        # Initialize workflow state
        state = WorkflowState(
            session_id=session_id,
            client_id=client_id,
            document_filename=filename,
            document_content=document_content,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        # Send initial status
        await self._send_card_update(state, "upload", ProcessingStatus.COMPLETED, {
            "filename": filename,
            "size": f"{len(document_content)} bytes",
            "status": "Document uploaded successfully"
        })
        
        try:
            # Run the workflow
            result = await self.workflow.ainvoke(state)
            
            logger.info("Document processing completed", 
                       session_id=session_id, stage=result.current_stage)
            
            return result
            
        except Exception as e:
            logger.error("Document processing failed", 
                        session_id=session_id, error=str(e))
            
            state.add_error(f"Workflow failed: {str(e)}")
            state.transition_to_stage(WorkflowStage.ERROR)
            
            await self._send_card_update(state, "error", ProcessingStatus.ERROR, {
                "error": str(e),
                "stage": state.current_stage
            })
            
            return state
    
    async def _run_document_parser(self, state: WorkflowState) -> WorkflowState:
        """Run the document parser agent"""
        state.transition_to_stage(WorkflowStage.DOCUMENT_PARSING)
        
        await self._send_card_update(state, "parsing", ProcessingStatus.PROCESSING, {
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
            
            await self._send_card_update(state, "parsing", ProcessingStatus.COMPLETED, {
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
        """Run the order extraction agent"""
        state.transition_to_stage(WorkflowStage.ORDER_EXTRACTION)
        
        await self._send_card_update(state, "extraction", ProcessingStatus.PROCESSING, {
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
            
            await self._send_card_update(state, "extraction", ProcessingStatus.COMPLETED, {
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
    
    async def _run_semantic_search(self, state: WorkflowState) -> WorkflowState:
        """Run the semantic search agent"""
        state.transition_to_stage(WorkflowStage.SEMANTIC_SEARCH)
        
        await self._send_card_update(state, "matching", ProcessingStatus.PROCESSING, {
            "status": "Finding part matches...",
            "parts_to_match": len(state.extracted_line_items)
        })
        
        try:
            result = await self.semantic_search.find_part_matches(state.extracted_line_items)
            
            state.part_matches = result.get("matches", {})
            
            state.add_message(
                "semantic_search",
                WorkflowStage.SEMANTIC_SEARCH,
                AgentStatus.COMPLETED,
                result
            )
            
            # Calculate match statistics
            total_parts = len(state.extracted_line_items)
            matched_parts = len([m for m in state.part_matches.values() if m])
            match_rate = (matched_parts / total_parts * 100) if total_parts > 0 else 0
            
            await self._send_card_update(state, "matching", ProcessingStatus.COMPLETED, {
                "status": "Part matching completed",
                "total_parts": total_parts,
                "matched_parts": matched_parts,
                "match_rate": f"{match_rate:.1f}%",
                "top_matches": list(state.part_matches.items())[:3]
            })
            
            logger.info("Semantic search completed", 
                       session_id=state.session_id,
                       match_rate=match_rate)
            
        except Exception as e:
            logger.error("Semantic search failed", session_id=state.session_id, error=str(e))
            state.add_error(f"Semantic search failed: {str(e)}")
            state.add_message(
                "semantic_search",
                WorkflowStage.SEMANTIC_SEARCH,
                AgentStatus.ERROR,
                {},
                str(e)
            )
        
        return state
    
    async def _run_erp_integration(self, state: WorkflowState) -> WorkflowState:
        """Run the ERP integration agent"""
        state.transition_to_stage(WorkflowStage.ERP_VALIDATION)
        
        await self._send_card_update(state, "erp_validation", ProcessingStatus.PROCESSING, {
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
            
            await self._send_card_update(state, "erp_validation", ProcessingStatus.COMPLETED, {
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
        """Run the review preparation agent"""
        state.transition_to_stage(WorkflowStage.REVIEW_PREPARATION)
        
        await self._send_card_update(state, "review", ProcessingStatus.PROCESSING, {
            "status": "Preparing order for review..."
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
            
            await self._send_card_update(state, "review", ProcessingStatus.COMPLETED, {
                "status": "Order ready for review",
                "total_amount": state.final_order_data.get("total_amount", 0),
                "line_items": len(state.final_order_data.get("line_items", [])),
                "confidence": result.get("confidence", "medium")
            })
            
            logger.info("Review preparation completed", session_id=state.session_id)
            
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
    
    async def _handle_error(self, state: WorkflowState) -> WorkflowState:
        """Handle errors and decide on retry strategy"""
        state.transition_to_stage(WorkflowStage.ERROR)
        
        logger.warning("Handling workflow error", 
                      session_id=state.session_id,
                      errors=state.errors,
                      retry_count=state.retry_count)
        
        if state.can_retry():
            state.increment_retry()
            await self._send_card_update(state, "retry", ProcessingStatus.PROCESSING, {
                "status": f"Retrying workflow (attempt {state.retry_count}/{state.max_retries})",
                "errors": state.errors[-3:]  # Show last 3 errors
            })
        else:
            await self._send_card_update(state, "error", ProcessingStatus.ERROR, {
                "status": "Workflow failed after maximum retries",
                "errors": state.errors,
                "retry_count": state.retry_count
            })
        
        return state
    
    def _should_handle_error(self, state: WorkflowState) -> str:
        """Determine if we should handle an error"""
        latest_messages = state.agent_messages[-5:] if state.agent_messages else []
        has_error = any(msg.status == AgentStatus.ERROR for msg in latest_messages)
        return "error" if has_error else "continue"
    
    def _should_retry(self, state: WorkflowState) -> str:
        """Determine if we should retry the workflow"""
        return "retry" if state.can_retry() else "end"
    
    async def _send_card_update(self, state: WorkflowState, card_id: str, 
                               status: ProcessingStatus, content: Dict[str, Any]):
        """Send card update via WebSocket"""
        try:
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