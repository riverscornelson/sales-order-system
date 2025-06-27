#!/usr/bin/env python3
"""
Test the agents directly without FastAPI
"""
import asyncio
import os
import sys
sys.path.append('/Users/riverscornelson/PycharmProjects/sales-order-system/backend')

# Set OpenAI API key from environment
if 'OPENAI_API_KEY' not in os.environ:
    print("❌ OPENAI_API_KEY environment variable not set")
    print("Please set your OpenAI API key: export OPENAI_API_KEY='your-key-here'")
    sys.exit(1)

async def test_agents():
    print("🚀 Testing agents directly...")
    
    try:
        from app.agents.supervisor import SupervisorAgent
        from app.services.websocket_manager import WebSocketManager
        
        print("✅ Imports successful")
        
        # Create WebSocket manager and supervisor
        websocket_manager = WebSocketManager()
        supervisor = SupervisorAgent(websocket_manager)
        
        print("✅ Supervisor created")
        
        # Test content
        test_content = """
        Customer Order Request
        Customer: John Doe  
        Email: john@example.com
        Items:
        - Widget A (Qty: 5)
        - Widget B (Qty: 10)  
        Total: $150.00
        """
        
        print("🤖 Starting agent processing...")
        
        # Process document
        result = await supervisor.process_document(
            session_id="test-session-123",
            client_id="test-client-123", 
            filename="test.txt",
            document_content=test_content
        )
        
        print("✅ Agent processing completed!")
        print(f"📊 Result: {result}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_agents())