#!/usr/bin/env python3
"""
Test WebSocket Real-time Updates
Test the real-time WebSocket functionality of the trading bot
"""

import asyncio
import websockets
import json
import time

async def test_websocket():
    """Test WebSocket connection and real-time updates"""
    uri = "ws://localhost:8000/ws"
    
    print("Testing WebSocket Real-time Connection...")
    print(f"Connecting to: {uri}")
    
    try:
        async with websockets.connect(uri) as websocket:
            print("✅ WebSocket connected successfully!")
            
            # Send ping
            ping_message = json.dumps({"type": "ping"})
            await websocket.send(ping_message)
            print("📤 Sent ping message")
            
            # Request immediate update
            update_message = json.dumps({"type": "request_update"})
            await websocket.send(update_message)
            print("📤 Requested immediate update")
            
            # Listen for messages for 30 seconds
            print("🔄 Listening for real-time updates...")
            start_time = time.time()
            message_count = 0
            
            while time.time() - start_time < 30:  # Listen for 30 seconds
                try:
                    # Wait for message with timeout
                    message = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                    message_count += 1
                    
                    try:
                        data = json.loads(message)
                        print(f"📥 Message #{message_count}: {data.get('type', 'unknown')} at {data.get('timestamp', 'no-timestamp')}")
                        
                        if data.get('type') == 'immediate_update':
                            print("   └─ Contains: ", ', '.join(data.get('data', {}).keys()))
                        elif data.get('type') == 'portfolio_update':
                            portfolio = data.get('data', {})
                            print(f"   └─ Portfolio: ${portfolio.get('total_value', 0):.2f} total, ${portfolio.get('available_budget', 0):.2f} available")
                        elif data.get('type') == 'market_update':
                            market_data = data.get('data', [])
                            print(f"   └─ Market data for {len(market_data)} symbols")
                        
                    except json.JSONDecodeError:
                        print(f"📥 Raw message #{message_count}: {message[:100]}...")
                        
                except asyncio.TimeoutError:
                    print("⏰ No message received in last 5 seconds")
                    
            print(f"\n📊 Test completed! Received {message_count} messages in 30 seconds")
            
    except ConnectionRefusedError:
        print("❌ Connection refused. Is the server running on localhost:8000?")
        print("   Run: python api_server.py")
    except Exception as e:
        print(f"❌ WebSocket test failed: {e}")

async def test_api_endpoints():
    """Test API endpoints that should trigger WebSocket updates"""
    import aiohttp
    
    print("\n🔧 Testing API endpoints...")
    
    async with aiohttp.ClientSession() as session:
        try:
            # Test demo login
            async with session.post("http://localhost:8000/api/auth/demo") as resp:
                if resp.status == 200:
                    print("✅ Demo login successful")
                else:
                    print(f"❌ Demo login failed: {resp.status}")
            
            # Test status endpoint
            async with session.get("http://localhost:8000/api/status") as resp:
                if resp.status == 200:
                    data = await resp.json()
                    print(f"✅ Status endpoint working - Demo mode: {data.get('demo_mode')}")
                else:
                    print(f"❌ Status endpoint failed: {resp.status}")
                    
            # Test realtime status
            async with session.get("http://localhost:8000/api/realtime/status") as resp:
                if resp.status == 200:
                    data = await resp.json()
                    print(f"✅ Realtime status: {data.get('connections')} connections, Active: {data.get('updates_active')}")
                else:
                    print(f"❌ Realtime status failed: {resp.status}")
                    
        except Exception as e:
            print(f"❌ API test failed: {e}")

if __name__ == "__main__":
    print("🚀 WebSocket Real-time System Test")
    print("=" * 50)
    
    # Test API endpoints first
    asyncio.run(test_api_endpoints())
    
    # Test WebSocket
    asyncio.run(test_websocket())
    
    print("\n✨ Test completed!")
    print("If you see real-time updates, your WebSocket system is working!")
