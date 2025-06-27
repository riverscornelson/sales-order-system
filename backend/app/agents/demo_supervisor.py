"""
Demo supervisor agent to show refactored agents working with controlled WebSocket messages
"""
import asyncio
from typing import Dict, Any
from datetime import datetime
import structlog
import json

from ..services.websocket_manager import WebSocketManager
from ..models.schemas import ProcessingCard, ProcessingStatus
from .semantic_search import SemanticSearchAgent

logger = structlog.get_logger()


class DemoSupervisorAgent:
    """Simplified supervisor to demonstrate refactored agents working"""
    
    def __init__(self, websocket_manager: WebSocketManager):
        self.websocket_manager = websocket_manager
        
        # Initialize our refactored semantic search agent
        self.semantic_search_agent = SemanticSearchAgent()
        
        logger.info("✅ Demo supervisor initialized with refactored agents")
    
    async def _send_card_update(self, client_id: str, card_id: str, 
                               status: ProcessingStatus, content: Dict[str, Any],
                               title: str = None):
        """Send controlled card update via WebSocket"""
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
            "type": "agent_update",
            "data": card_dict
        }
        
        logger.info(f"📤 Demo: Sending card update", 
                   client_id=client_id, 
                   card_id=card_id, 
                   status=status.value)
        
        await self.websocket_manager.send_personal_message(
            message=json.dumps(message),
            client_id=client_id
        )
        
        # Add delay to prevent message flooding
        await asyncio.sleep(1)
    
    async def process_document(self, session_id: str, client_id: str, 
                             filename: str, document_content: str) -> Dict[str, Any]:
        """Demo processing workflow showing refactored agents in action"""
        
        logger.info("🚀 Starting DEMO agent workflow", 
                   session_id=session_id, 
                   filename=filename)
        
        try:
            # Step 1: Document Analysis (Simulated)
            await self._send_card_update(
                client_id, "demo_parser", ProcessingStatus.PROCESSING,
                {"message": "Analyzing document with refactored architecture..."},
                "🔍 Demo Document Parser"
            )
            
            # Simulate document analysis
            await asyncio.sleep(2)
            
            # Simple line item extraction from content
            line_items = []
            if "steel" in document_content.lower():
                line_items.append({
                    "description": "Steel bolts M8",
                    "quantity": 5,
                    "extracted_from": "document analysis"
                })
            if "aluminum" in document_content.lower():
                line_items.append({
                    "description": "Aluminum washers",
                    "quantity": 10,
                    "extracted_from": "document analysis"
                })
            
            if not line_items:
                line_items = [{"description": "Generic industrial part", "quantity": 1}]
            
            await self._send_card_update(
                client_id, "demo_parser", ProcessingStatus.COMPLETED,
                {
                    "message": f"Found {len(line_items)} line items",
                    "line_items": line_items
                },
                "🔍 Demo Document Parser"
            )
            
            # Step 2: Semantic Search with Refactored Agent
            await self._send_card_update(
                client_id, "semantic_search", ProcessingStatus.PROCESSING,
                {"message": "Using refactored semantic search strategies..."},
                "🔎 Refactored Semantic Search"
            )
            
            # Use our refactored semantic search agent
            search_results = await self.semantic_search_agent.find_part_matches(line_items)
            
            await self._send_card_update(
                client_id, "semantic_search", ProcessingStatus.COMPLETED,
                {
                    "message": "Semantic search completed with refactored agent",
                    "statistics": search_results.get("statistics", {}),
                    "agent_type": search_results.get("agent", "semantic_search"),
                    "confidence": search_results.get("confidence", 0)
                },
                "🔎 Refactored Semantic Search"
            )
            
            # Step 3: Results Summary
            await self._send_card_update(
                client_id, "demo_results", ProcessingStatus.PROCESSING,
                {"message": "Compiling results from refactored components..."},
                "📊 Demo Results"
            )
            
            await asyncio.sleep(1)
            
            # Count matches found
            total_matches = 0
            for item_matches in search_results.get("matches", {}).values():
                total_matches += len(item_matches)
            
            final_results = {
                "session_id": session_id,
                "line_items_processed": len(line_items),
                "total_matches_found": total_matches,
                "processing_time": "~5 seconds",
                "architecture": "Refactored with Strategy Pattern",
                "security": "SQL injection protected",
                "performance": "Optimized with memoization",
                "agents_used": [
                    "DemoSupervisorAgent (new)",
                    "SemanticSearchAgent (refactored)",
                    "Strategy pattern search components"
                ]
            }
            
            await self._send_card_update(
                client_id, "demo_results", ProcessingStatus.COMPLETED,
                {
                    "message": "✅ Demo completed - Refactored agents working!",
                    "results": final_results
                },
                "📊 Demo Results"
            )
            
            logger.info("✅ Demo workflow completed successfully", session_id=session_id)
            return final_results
            
        except Exception as e:
            logger.error("❌ Demo workflow failed", session_id=session_id, error=str(e))
            
            await self._send_card_update(
                client_id, "demo_error", ProcessingStatus.ERROR,
                {
                    "message": f"Demo workflow failed: {str(e)}",
                    "error_type": type(e).__name__
                },
                "❌ Demo Error"
            )
            
            raise e