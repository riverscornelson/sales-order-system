#!/usr/bin/env python3

import asyncio
import os
import sys
import structlog

# Add the backend directory to Python path
sys.path.insert(0, '/Users/riverscornelson/PycharmProjects/sales-order-system/backend')

from app.agents.supervisor_local import LocalSupervisorAgent
from app.services.websocket_manager import WebSocketManager

# Configure structlog for better output
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.dev.ConsoleRenderer()
    ],
    wrapper_class=structlog.stdlib.BoundLogger,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

async def test_urgent_order():
    """Test the urgent rush order processing with debug logging"""
    
    # Read the urgent rush order file
    urgent_order_path = "/Users/riverscornelson/PycharmProjects/sales-order-system/backend/data/test_emails/urgent_rush_order.txt"
    
    with open(urgent_order_path, 'r') as f:
        document_content = f.read()
    
    print(f"Document length: {len(document_content)} characters")
    print(f"Document preview: {document_content[:200]}...")
    
    # Create a mock WebSocket manager
    websocket_manager = WebSocketManager()
    
    # Create supervisor
    supervisor = LocalSupervisorAgent(websocket_manager)
    
    # Process the document
    try:
        result = await supervisor.process_document(
            session_id="test-session-123",
            client_id="test-client-456", 
            filename="urgent_rush_order.txt",
            document_content=document_content
        )
        
        print("\n" + "="*80)
        print("PROCESSING COMPLETED SUCCESSFULLY")
        print("="*80)
        print(f"Result keys: {list(result.keys())}")
        
        if 'enhanced_order' in result:
            enhanced_order = result['enhanced_order']
            print(f"\nExtracted {len(enhanced_order.get('line_items', []))} line items:")
            for i, item in enumerate(enhanced_order.get('line_items', [])[:3]):  # Show first 3
                print(f"  {i+1}. {item.get('raw_text', '')[:100]}...")
        
        if 'assembled_order' in result:
            assembled = result['assembled_order']
            totals = assembled.get('totals', {})
            print(f"\nAssembly Results:")
            print(f"  Total items: {totals.get('total_line_items', 0)}")
            print(f"  Matched items: {totals.get('matched_items', 0)}")
            print(f"  No match items: {totals.get('no_match_items', 0)}")
            print(f"  Error items: {totals.get('error_items', 0)}")
            
    except Exception as e:
        print(f"\n❌ Processing failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_urgent_order())