#!/usr/bin/env python3
"""
Test CCXT Exchange Availability
==============================

Check which exchanges are available in the current CCXT installation
"""

import ccxt
import sys

def test_exchanges():
    """Test which exchanges are available"""
    
    print("🔍 Testing CCXT Exchange Availability...")
    print("=" * 50)
    
    # Test basic CCXT functionality
    try:
        print(f"✅ CCXT Version: {ccxt.__version__}")
    except:
        print("❌ CCXT version not available")
    
    # List of exchanges to test
    test_exchanges = [
        'coinbase',
        'coinbasepro', 
        'coinbaseadvanced',
        'binance',
        'kraken',
        'bitfinex',
        'okx',
        'bybit'
    ]
    
    available_exchanges = []
    unavailable_exchanges = []
    
    print("\n🏦 Testing Exchange Availability:")
    print("-" * 50)
    
    for exchange_name in test_exchanges:
        try:
            if hasattr(ccxt, exchange_name):
                exchange_class = getattr(ccxt, exchange_name)
                # Try to create an instance
                exchange = exchange_class({'enableRateLimit': True})
                available_exchanges.append(exchange_name)
                print(f"✅ {exchange_name:<20} - Available")
            else:
                unavailable_exchanges.append(exchange_name)
                print(f"❌ {exchange_name:<20} - Not available")
        except Exception as e:
            unavailable_exchanges.append(exchange_name)
            print(f"❌ {exchange_name:<20} - Error: {str(e)[:50]}")
    
    print("\n📊 Summary:")
    print("-" * 50)
    print(f"✅ Available exchanges: {len(available_exchanges)}")
    print(f"❌ Unavailable exchanges: {len(unavailable_exchanges)}")
    
    if available_exchanges:
        print(f"\n🎯 Recommended exchange for testing: {available_exchanges[0]}")
        
        # Test market loading for the first available exchange
        try:
            test_exchange = getattr(ccxt, available_exchanges[0])({'enableRateLimit': True})
            markets = test_exchange.load_markets()
            print(f"✅ {available_exchanges[0]} markets loaded: {len(markets)} symbols")
            
            # Show some popular symbols
            popular_symbols = ['BTC/USDT', 'ETH/USDT', 'BNB/USDT', 'ADA/USDT', 'SOL/USDT']
            available_symbols = []
            for symbol in popular_symbols:
                if symbol in markets:
                    available_symbols.append(symbol)
            
            if available_symbols:
                print(f"📈 Available symbols: {', '.join(available_symbols)}")
            
        except Exception as e:
            print(f"⚠️ Could not load markets for {available_exchanges[0]}: {str(e)}")
    
    return available_exchanges

def test_demo_mode():
    """Test demo mode functionality"""
    print("\n🎮 Testing Demo Mode:")
    print("-" * 50)
    
    try:
        from utils.demo_data import demo_service
        
        # Test demo balance
        balance = demo_service.get_demo_balance()
        print(f"✅ Demo balance loaded: {len(balance)} currencies")
        
        # Test demo ticker
        ticker = demo_service.get_demo_ticker('BTC/USDT')
        print(f"✅ Demo ticker: BTC/USDT = ${ticker['last']:.2f}")
        
        # Test demo portfolio
        portfolio = demo_service.get_demo_portfolio_status()
        print(f"✅ Demo portfolio: ${portfolio['total_budget']:.2f} total budget")
        
        # Test demo strategies
        strategies = demo_service.get_demo_strategies()
        print(f"✅ Demo strategies: {len(strategies)} strategies loaded")
        
        print("✅ Demo mode fully functional!")
        return True
        
    except Exception as e:
        print(f"❌ Demo mode error: {str(e)}")
        return False

def main():
    """Main test function"""
    print("🚀 GPU-Accelerated Trading Bot - System Check")
    print("=" * 60)
    
    # Test exchanges
    available_exchanges = test_exchanges()
    
    # Test demo mode
    demo_working = test_demo_mode()
    
    print("\n🎯 Recommendations:")
    print("=" * 60)
    
    if demo_working:
        print("✅ Demo mode is working - you can test the interface safely")
        print("   🎮 Start the web interface and leave API credentials empty")
    
    if available_exchanges:
        print(f"✅ Real trading available with: {', '.join(available_exchanges)}")
        print("   🔑 Get API credentials from your preferred exchange")
    else:
        print("❌ No exchanges available for real trading")
        print("   📦 Try: pip install --upgrade ccxt")
    
    print("\n🌐 To start the web interface:")
    print("   python launch_web_ui.py")
    print("   or")
    print("   python -m uvicorn api_server:app --host 0.0.0.0 --port 8000")

if __name__ == "__main__":
    main()
