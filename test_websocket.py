#!/usr/bin/env python3
"""
Test WebSocket client to see real-time agent updates
"""
import asyncio
import websockets
import json

async def test_websocket():
    client_id = "client-51453ede-83c4-429a-b292-2db05b1be87f"
    uri = f"ws://localhost:8000/ws/{client_id}"
    
    print(f"🔗 Connecting to WebSocket: {uri}")
    
    try:
        async with websockets.connect(uri) as websocket:
            print("✅ WebSocket connected! Listening for agent updates...")
            
            while True:
                try:
                    message = await asyncio.wait_for(websocket.recv(), timeout=30.0)
                    data = json.loads(message)
                    
                    print(f"\n📨 Received message:")
                    print(f"   Type: {data.get('type', 'unknown')}")
                    
                    if data.get('type') == 'card_update':
                        card = data.get('data', {})
                        print(f"   🤖 Agent: {card.get('id', 'unknown')}")
                        print(f"   📋 Title: {card.get('title', 'unknown')}")
                        print(f"   🔄 Status: {card.get('status', 'unknown')}")
                        print(f"   📊 Content: {json.dumps(card.get('content', {}), indent=2)}")
                    else:
                        print(f"   📄 Data: {json.dumps(data, indent=2)}")
                        
                except asyncio.TimeoutError:
                    print("⏰ No messages received in 30 seconds, closing...")
                    break
                except websockets.exceptions.ConnectionClosed:
                    print("🔌 WebSocket connection closed")
                    break
                    
    except Exception as e:
        print(f"❌ WebSocket error: {e}")

if __name__ == "__main__":
    print("🚀 Starting WebSocket test client...")
    asyncio.run(test_websocket())