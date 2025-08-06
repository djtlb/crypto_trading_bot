#!/usr/bin/env python3
"""
Test Real Coinbase API Connection
Test the real Coinbase API with provided credentials
"""

import asyncio
import sys
import os
from config import API_KEY, API_SECRET, API_PASSPHRASE, SANDBOX_MODE

# Add the current directory to Python path
sys.path.insert(0, '.')

async def test_real_coinbase_connection():
    """Test connection to real Coinbase API"""
    print("🔐 Testing Real Coinbase API Connection...")
    print(f"API Key: {API_KEY[:20]}...")
    print(f"Sandbox Mode: {SANDBOX_MODE}")
    print("-" * 50)
    
    try:
        from utils.exchange_handler import ExchangeHandler
        
        # Initialize exchange handler with your credentials
        exchange_handler = ExchangeHandler(
            exchange_id="coinbase",
            api_key=API_KEY,
            api_secret=API_SECRET,
            sandbox=SANDBOX_MODE,
            passphrase=API_PASSPHRASE
        )
        
        print("✅ Exchange handler created")
        
        # Test 1: Get account balance
        print("\n📊 Testing account balance...")
        balance = await asyncio.to_thread(exchange_handler.get_balance)
        print("✅ Account balance retrieved:")
        for currency, bal in balance.items():
            if bal.get('total', 0) > 0.001:  # Only show currencies with balance
                print(f"   {currency}: {bal}")
        
        # Test 2: Get market data
        print("\n📈 Testing market data...")
        ticker = await asyncio.to_thread(exchange_handler.exchange.fetch_ticker, 'BTC-USD')
        print(f"✅ BTC-USD Price: ${ticker.get('last', 'N/A')}")
        print(f"   Bid: ${ticker.get('bid', 'N/A')}")
        print(f"   Ask: ${ticker.get('ask', 'N/A')}")
        print(f"   Volume: {ticker.get('baseVolume', 'N/A')}")
        
        # Test 3: Get recent trades (if any)
        print("\n📋 Testing trade history...")
        try:
            trades = await asyncio.to_thread(exchange_handler.get_trade_history, limit=5)
            print(f"✅ Retrieved {len(trades)} recent trades")
            for trade in trades[:3]:  # Show first 3
                print(f"   {trade.get('datetime', 'N/A')}: {trade.get('side', 'N/A')} {trade.get('amount', 'N/A')} {trade.get('symbol', 'N/A')}")
        except Exception as e:
            print(f"⚠️  Trade history: {e}")
        
        # Test 4: Check available markets
        print("\n🏪 Testing available markets...")
        try:
            markets = await asyncio.to_thread(exchange_handler.exchange.fetch_markets)
            btc_markets = [m for m in markets if 'BTC' in m['symbol']][:5]
            print(f"✅ Available markets (showing 5 BTC pairs):")
            for market in btc_markets:
                print(f"   {market['symbol']}")
        except Exception as e:
            print(f"⚠️  Markets: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Connection test failed: {e}")
        print("\n🔧 Troubleshooting tips:")
        print("1. Verify your API credentials are correct")
        print("2. Make sure your Coinbase Pro account has API access enabled")
        print("3. Check if you're using sandbox vs live credentials")
        print("4. Ensure your IP is whitelisted (if required)")
        return False

async def test_login_endpoint():
    """Test the API server login endpoint with real credentials"""
    print("\n🌐 Testing API Server Login Endpoint...")
    
    try:
        import aiohttp
        
        async with aiohttp.ClientSession() as session:
            login_data = {
                "api_key": API_KEY,
                "api_secret": API_SECRET,
                "api_passphrase": API_PASSPHRASE,
                "sandbox": SANDBOX_MODE
            }
            
            async with session.post("http://localhost:8000/api/auth/login", json=login_data) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    print("✅ API Server login successful!")
                    print(f"   Exchange: {data.get('exchange', 'N/A')}")
                    print(f"   Demo Mode: {data.get('demo_mode', 'N/A')}")
                    print(f"   Message: {data.get('message', 'N/A')}")
                    return True
                else:
                    error_text = await resp.text()
                    print(f"❌ API Server login failed: {resp.status}")
                    print(f"   Error: {error_text}")
                    return False
                    
    except Exception as e:
        print(f"❌ API Server test failed: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Real Coinbase API Connection Test")
    print("=" * 50)
    
    asyncio.run(test_real_coinbase_connection())
    asyncio.run(test_login_endpoint())
    
    print("\n✨ Test completed!")
    print("If successful, your credentials are working and you can use real trading!")
