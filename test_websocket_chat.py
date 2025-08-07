#!/usr/bin/env python3
"""
Test WebSocket Chat Functionality
"""

import asyncio
import websockets
import json

async def test_chat():
    """Test the WebSocket chat connection"""
    try:
        print("🔌 Connecting to WebSocket chat...")
        
        # Connect to chat WebSocket
        uri = "ws://localhost:8001/ws/chat"
        async with websockets.connect(uri) as websocket:
            print("✅ Connected to chat!")
            
            # Send a test message
            test_message = "Hello trader! What's the status?"
            print(f"📤 Sending: {test_message}")
            await websocket.send(test_message)
            
            # Receive response
            response = await websocket.recv()
            print(f"📥 Received: {response}")
            
            # Send another message
            test_message2 = "gas prices"
            print(f"📤 Sending: {test_message2}")
            await websocket.send(test_message2)
            
            # Receive response
            response2 = await websocket.recv()
            print(f"📥 Received: {response2}")
            
            print("✅ WebSocket chat test completed!")
            
    except Exception as e:
        print(f"❌ WebSocket test failed: {e}")

if __name__ == "__main__":
    print("🧪 Testing WebSocket Chat Connection")
    print("===================================")
    asyncio.run(test_chat())
