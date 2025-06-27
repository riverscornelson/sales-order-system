"""
Enhanced supervisor for line-item level order processing
"""
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime
import structlog
from langchain_openai import ChatOpenAI
import json

from .workflow_state import WorkflowState, WorkflowStage, AgentStatus
from ..services.websocket_manager import WebSocketManager
from ..models.schemas import ProcessingCard, ProcessingStatus
from ..models.line_item_schemas import (
    OrderProcessingState, LineItemProcessingState, LineItemStatus, ProcessingStage
)
from .enhanced_order_extractor import EnhancedOrderExtractor
from .agentic_search_coordinator import AgenticSearchCoordinator
from .part_matching_agent import PartMatchingAgent
from .order_assembly_agent import OrderAssemblyAgent
from ..services.parts_catalog import PartsCatalogService

logger = structlog.get_logger()

class LocalSupervisorAgent:
    """Enhanced supervisor that processes orders at line item level"""
    
    def __init__(self, websocket_manager: WebSocketManager):
        self.websocket_manager = websocket_manager
        
        # Get OpenAI API key from settings
        from ..core.config import settings
        
        if not settings.openai_api_key:
            logger.warning("⚠️ OpenAI API key not found. Please set OPENAI_API_KEY environment variable.")
            self.llm = None
        else:
            self.llm = ChatOpenAI(
                model="gpt-4.1", 
                temperature=0,
                openai_api_key=settings.openai_api_key
            )
        
        # Initialize specialized agents
        self.order_extractor = EnhancedOrderExtractor(self.llm) if self.llm else None
        self.catalog_service = PartsCatalogService()
        self.search_coordinator = AgenticSearchCoordinator(self.catalog_service, self.llm)
        self.matching_agent = PartMatchingAgent(self.llm) if self.llm else None
        self.assembly_agent = OrderAssemblyAgent(self.llm)
        
        logger.info("✅ Enhanced supervisor initialized successfully")
    
    async def _send_card_update(self, client_id: str, card_id: str, 
                               status: ProcessingStatus, content: Dict[str, Any],
                               title: str = None):
        """Send card update via WebSocket"""
        card = ProcessingCard(
            id=card_id,
            title=title or card_id.replace('_', ' ').title(),
            status=status,
            content=content,
            timestamp=datetime.now()
        )
        
        # Convert to dict and handle datetime serialization
        card_dict = card.dict()
        if 'timestamp' in card_dict and hasattr(card_dict['timestamp'], 'isoformat'):
            card_dict['timestamp'] = card_dict['timestamp'].isoformat()
        
        message = {
            "type": "card_update",
            "data": card_dict
        }
        
        logger.info(f"📤 Sending card update", 
                   client_id=client_id, 
                   card_id=card_id, 
                   status=status.value)
        
        import json
        await self.websocket_manager.send_personal_message(
            message=json.dumps(message),
            client_id=client_id
        )
    
    async def process_document(self, session_id: str, client_id: str, 
                             filename: str, document_content: str) -> Dict[str, Any]:
        """Process document through enhanced line item workflow"""
        
        logger.info("🚀 Starting enhanced agent workflow", 
                   session_id=session_id, 
                   filename=filename,
                   content_length=len(document_content))
        
        # Initialize processing state
        processing_state = OrderProcessingState(
            order_id=f"ORD-{session_id[:8]}",
            session_id=session_id,
            client_id=client_id,
            started_at=datetime.now()
        )
        
        # Send initial test message
        test_message = {
            "type": "test_message",
            "data": {"message": "Enhanced WebSocket system active!"}
        }
        await self.websocket_manager.send_personal_message(
            message=json.dumps(test_message),
            client_id=client_id
        )
        
        try:
            # Step 1: Document Analysis
            await self._send_card_update(
                client_id, "document_parser", ProcessingStatus.PROCESSING,
                {"message": "Analyzing document structure..."},
                "🔍 Document Parser"
            )
            
            processing_state.current_stage = ProcessingStage.EXTRACTION
            
            # Basic document analysis (keeping it simple for now)
            doc_analysis = {
                "document_type": "email",
                "filename": filename,
                "content_length": len(document_content),
                "preview": document_content[:200] + "..." if len(document_content) > 200 else document_content
            }
            
            await self._send_card_update(
                client_id, "document_parser", ProcessingStatus.COMPLETED,
                {
                    "message": "Document structure analyzed",
                    "document_type": doc_analysis["document_type"],
                    "content_length": doc_analysis["content_length"]
                },
                "🔍 Document Parser"
            )
            
            # Step 2: Enhanced Order Extraction
            await self._send_card_update(
                client_id, "order_extractor", ProcessingStatus.PROCESSING,
                {"message": "Extracting line items with AI..."},
                "📝 Order Extractor"
            )
            
            # Extract order with line items
            if self.order_extractor and self.llm:
                enhanced_order = await self.order_extractor.extract_order_with_line_items(
                    document_content, session_id
                )
            else:
                # Fallback extraction
                from ..models.line_item_schemas import EnhancedOrder, OrderMetadata, LineItem, ExtractedSpecs
                enhanced_order = EnhancedOrder(
                    order_id=f"ORD-{session_id[:8]}",
                    session_id=session_id,
                    order_metadata=OrderMetadata(customer="Unknown Customer"),
                    line_items=[LineItem(
                        line_id="L001",
                        raw_text="Materials from uploaded document",
                        extracted_specs=ExtractedSpecs()
                    )]
                )
            
            # Update processing state with line items
            processing_state.total_items = len(enhanced_order.line_items)
            for line_item in enhanced_order.line_items:
                line_state = LineItemProcessingState(
                    line_id=line_item.line_id,
                    status=LineItemStatus.PENDING
                )
                processing_state.line_item_states[line_item.line_id] = line_state
            
            await self._send_card_update(
                client_id, "order_extractor", ProcessingStatus.COMPLETED,
                {
                    "message": "Line items extracted successfully",
                    "customer": enhanced_order.order_metadata.customer,
                    "total_line_items": len(enhanced_order.line_items),
                    "line_items_preview": [
                        {
                            "line_id": item.line_id,
                            "preview": item.raw_text[:100] + "..." if len(item.raw_text) > 100 else item.raw_text
                        }
                        for item in enhanced_order.line_items[:3]
                    ]
                },
                "📝 Order Extractor"
            )
            
            # Step 3: Line Item Processing
            await self._send_card_update(
                client_id, "line_item_processing", ProcessingStatus.PROCESSING,
                {"message": f"Processing {len(enhanced_order.line_items)} line items..."},
                "⚙️ Line Item Processing"
            )
            
            # Initialize catalog
            try:
                import os
                sample_catalog_path = os.path.join(os.path.dirname(__file__), "../../data/parts_catalog_sample.csv")
                if os.path.exists(sample_catalog_path):
                    logger.info("🔍 Loading catalog from CSV", path=sample_catalog_path)
                    success = await self.catalog_service.load_catalog_from_csv(sample_catalog_path)
                    if success:
                        logger.info("📦 Loaded sample parts catalog successfully")
                        # Get catalog stats to verify
                        stats = await self.catalog_service.get_catalog_stats()
                        logger.info("📊 Catalog stats", total_parts=stats.get("total_parts", 0))
                    else:
                        logger.error("❌ Failed to load catalog from CSV")
                else:
                    logger.error("❌ Catalog file not found", path=sample_catalog_path)
            except Exception as e:
                logger.error("⚠️ Could not load catalog", error=str(e))
            
            # Process each line item
            line_item_matches = {}
            processing_results = []
            
            print(f"🔄 DEBUG: Starting line item processing loop with {len(enhanced_order.line_items)} items")
            logger.info("🔄 Starting line item processing loop", 
                       total_line_items=len(enhanced_order.line_items))
            
            for i, line_item in enumerate(enhanced_order.line_items):
                print(f"🔄 DEBUG: Processing line item {i+1}: {line_item.line_id}")
                logger.info("🔄 Processing line item", 
                           item_number=i+1, 
                           line_id=line_item.line_id,
                           raw_text_preview=line_item.raw_text[:50])
                try:
                    # Update line item status
                    await self._send_line_item_update(
                        client_id, line_item.line_id, "searching", 
                        f"Searching for: {line_item.raw_text[:50]}..."
                    )
                    
                    # Search for parts
                    print(f"🔍 DEBUG: Starting search for {line_item.line_id}")
                    logger.info("🔍 Starting search for line item", 
                               line_id=line_item.line_id, 
                               raw_text=line_item.raw_text[:100])
                    search_results = await self.search_coordinator.search_for_line_item(line_item)
                    print(f"🔍 DEBUG: Search completed for {line_item.line_id}, found {len(search_results)} results")
                    logger.info("🔍 Search completed", 
                               line_id=line_item.line_id,
                               results_count=len(search_results))
                    
                    # Select best match using AI
                    print(f"🤖 DEBUG: Checking matching - agent exists: {self.matching_agent is not None}, results: {len(search_results)}")
                    if self.matching_agent and search_results:
                        print(f"🤖 DEBUG: Starting AI matching for {line_item.line_id}")
                        await self._send_line_item_update(
                            client_id, line_item.line_id, "matching",
                            f"AI selecting best match from {len(search_results)} candidates..."
                        )
                        
                        match_selection = await self.matching_agent.select_best_match(
                            line_item, search_results
                        )
                        line_item_matches[line_item.line_id] = match_selection
                        print(f"🤖 DEBUG: Matching completed for {line_item.line_id}, selected: {match_selection.selected_part_number}")
                        
                        # Update with final result
                        if match_selection.selected_part_number not in ["NO_MATCH", "ERROR"]:
                            await self._send_line_item_update(
                                client_id, line_item.line_id, "matched",
                                f"Matched: {match_selection.selected_part_number}"
                            )
                        else:
                            await self._send_line_item_update(
                                client_id, line_item.line_id, "manual_review",
                                "Requires manual review"
                            )
                    else:
                        print(f"🤖 DEBUG: Skipping matching - no agent or no results")
                        # No matches found
                        await self._send_line_item_update(
                            client_id, line_item.line_id, "manual_review",
                            "No suitable matches found"
                        )
                    
                    processing_results.append({
                        "line_id": line_item.line_id,
                        "search_results_count": len(search_results),
                        "match_found": line_item.line_id in line_item_matches
                    })
                    
                except Exception as e:
                    logger.error(f"Failed to process line item {line_item.line_id}", error=str(e))
                    await self._send_line_item_update(
                        client_id, line_item.line_id, "failed",
                        f"Processing error: {str(e)}"
                    )
            
            await self._send_card_update(
                client_id, "line_item_processing", ProcessingStatus.COMPLETED,
                {
                    "message": "Line item processing completed",
                    "total_items": len(enhanced_order.line_items),
                    "successful_matches": len(line_item_matches),
                    "processing_summary": processing_results
                },
                "⚙️ Line Item Processing"
            )
            
            # Step 4: Order Assembly
            await self._send_card_update(
                client_id, "assembly", ProcessingStatus.PROCESSING,
                {"message": "Assembling final order..."},
                "🔧 Order Assembly"
            )
            
            # Assemble the final order
            assembled_order = await self.assembly_agent.assemble_order(
                enhanced_order, line_item_matches
            )
            
            await self._send_card_update(
                client_id, "assembly", ProcessingStatus.COMPLETED,
                {
                    "message": "Order assembly completed",
                    "total_value": assembled_order.totals.get("estimated_total_value", 0),
                    "approval_required": assembled_order.approval_required,
                    "confidence_score": assembled_order.confidence_score,
                    "issues_count": len(assembled_order.issues_requiring_review)
                },
                "🔧 Order Assembly"
            )
            
            # Step 5: ERP Integration (mock)
            await self._send_card_update(
                client_id, "erp_integration", ProcessingStatus.PROCESSING,
                {"message": "Validating with ERP system..."},
                "🏢 ERP Integration"
            )
            await asyncio.sleep(1)
            
            await self._send_card_update(
                client_id, "erp_integration", ProcessingStatus.COMPLETED,
                {
                    "message": "ERP validation complete",
                    "customer_verified": True,
                    "inventory_status": "Items checked",
                    "credit_status": "Approved"
                },
                "🏢 ERP Integration"
            )
            
            # Step 6: Final Review
            await self._send_card_update(
                client_id, "review", ProcessingStatus.PROCESSING,
                {"message": "Preparing comprehensive order review..."},
                "📋 Review Preparation"
            )
            
            # Finalize processing state
            processing_state.completed_at = datetime.now()
            processing_state.overall_status = "completed"
            processing_state.final_order = assembled_order.dict()
            
            await self._send_card_update(
                client_id, "review", ProcessingStatus.COMPLETED,
                {
                    "message": "Enhanced order processing completed",
                    "order_summary": assembled_order.order_summary,
                    "total_line_items": assembled_order.totals.get("total_line_items", 0),
                    "matched_items": assembled_order.totals.get("matched_items", 0),
                    "approval_required": assembled_order.approval_required,
                    "confidence_score": assembled_order.confidence_score,
                    "next_steps": assembled_order.next_steps[:3] if assembled_order.next_steps else []
                },
                "📋 Review Preparation"
            )
            
            logger.info("✅ Enhanced agent workflow completed successfully", 
                       session_id=session_id,
                       total_line_items=len(enhanced_order.line_items),
                       successful_matches=len(line_item_matches))
            
            return {
                "status": "success",
                "enhanced_order": enhanced_order.dict(),
                "assembled_order": assembled_order.dict(),
                "processing_state": processing_state.dict(),
                "session_id": session_id
            }
            
        except Exception as e:
            logger.error("❌ Local agent workflow failed", 
                        session_id=session_id, 
                        error=str(e),
                        exc_info=True)
            
            # Send error card
            await self._send_card_update(
                client_id, "error", ProcessingStatus.ERROR,
                {
                    "message": "Processing failed",
                    "error": str(e)
                },
                "❌ Error"
            )
            
            raise
    
    async def _send_line_item_update(self, client_id: str, line_id: str, 
                                    status: str, message: str):
        """Send line item status update via WebSocket"""
        
        update_message = {
            "type": "line_item_update",
            "data": {
                "line_id": line_id,
                "status": status,
                "message": message,
                "timestamp": datetime.now().isoformat()
            }
        }
        
        logger.debug("📤 Sending line item update", 
                   client_id=client_id, 
                   line_id=line_id, 
                   status=status)
        
        await self.websocket_manager.send_personal_message(
            message=json.dumps(update_message),
            client_id=client_id
        )