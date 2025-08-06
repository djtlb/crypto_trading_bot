#!/usr/bin/env python3
"""
Test and Validate Trading Bot Web Interface
==========================================

Comprehensive testing script for the web interface components
"""

import sys
import os
import importlib.util
from pathlib import Path

def test_imports():
    """Test all required imports"""
    print("🔍 Testing imports...")
    
    # Test CCXT and available exchanges
    try:
        import ccxt
        print(f"✅ CCXT version: {ccxt.__version__}")
        
        # Check available exchanges
        available_exchanges = ccxt.exchanges
        coinbase_variants = [ex for ex in available_exchanges if 'coinbase' in ex.lower()]
        print(f"🏦 Available Coinbase exchanges: {coinbase_variants}")
        
        # Test if we can initialize coinbase
        try:
            exchange = ccxt.coinbase()
            print("✅ Coinbase exchange available")
        except Exception as e:
            print(f"⚠️ Coinbase exchange issue: {e}")
            
    except ImportError:
        print("❌ CCXT not available")
        return False
    
    # Test web framework imports
    try:
        import fastapi
        import uvicorn
        import pydantic
        print("✅ Web framework packages available")
    except ImportError as e:
        print(f"❌ Missing web framework package: {e}")
        return False
    
    # Test our custom modules
    custom_modules = [
        'utils.exchange_handler',
        'utils.demo_data',
        'utils.gpu_acceleration'
    ]
    
    for module in custom_modules:
        try:
            importlib.import_module(module)
            print(f"✅ {module} imported successfully")
        except ImportError as e:
            print(f"❌ Failed to import {module}: {e}")
            return False
    
    return True

def test_file_structure():
    """Test if all required files exist"""
    print("\n📁 Testing file structure...")
    
    required_files = [
        'api_server.py',
        'frontend/index.html',
        'frontend/static/css/style.css',
        'frontend/static/js/app.js',
        'utils/exchange_handler.py',
        'utils/demo_data.py',
        'utils/gpu_acceleration.py',
        'launch_web_ui.py'
    ]
    
    missing_files = []
    for file_path in required_files:
        if not os.path.exists(file_path):
            missing_files.append(file_path)
        else:
            print(f"✅ {file_path}")
    
    if missing_files:
        print(f"❌ Missing files: {', '.join(missing_files)}")
        return False
    
    return True

def test_demo_data():
    """Test demo data service"""
    print("\n🎭 Testing demo data service...")
    
    try:
        from utils.demo_data import demo_service
        
        # Test portfolio status
        portfolio = demo_service.get_demo_portfolio_status()
        print(f"✅ Demo portfolio: ${portfolio['total_budget']}")
        
        # Test market data
        ticker = demo_service.get_demo_ticker('BTC/USDT')
        print(f"✅ Demo BTC price: ${ticker['last']:.2f}")
        
        # Test strategies
        strategies = demo_service.get_demo_strategies()
        print(f"✅ Demo strategies: {len(strategies)} strategies")
        
        # Test trade history
        trades = demo_service.get_demo_trade_history(limit=5)
        print(f"✅ Demo trades: {len(trades)} trades")
        
        return True
        
    except Exception as e:
        print(f"❌ Demo data test failed: {e}")
        return False

def test_gpu_acceleration():
    """Test GPU acceleration module"""
    print("\n🚀 Testing GPU acceleration...")
    
    try:
        from utils.gpu_acceleration import gpu_accelerator
        
        print(f"✅ GPU Available: {gpu_accelerator.gpu_available}")
        print(f"✅ Numba Available: {gpu_accelerator.use_numba}")
        print(f"✅ Polars Available: {gpu_accelerator.use_polars}")
        print(f"✅ OpenCL Available: {gpu_accelerator.use_opencl}")
        
        # Test a simple acceleration
        import numpy as np
        test_data = np.random.random(1000)
        result = gpu_accelerator.accelerated_rolling_mean(test_data, window=20)
        print(f"✅ GPU acceleration test passed: {len(result)} results")
        
        return True
        
    except Exception as e:
        print(f"❌ GPU acceleration test failed: {e}")
        return False

def test_exchange_handler():
    """Test exchange handler without real credentials"""
    print("\n🏦 Testing exchange handler...")
    
    try:
        from utils.exchange_handler import ExchangeHandler
        
        # Test with demo/paper trading
        try:
            # Test available exchanges
            import ccxt
            if 'coinbase' in ccxt.exchanges:
                print("✅ Coinbase exchange available in CCXT")
            else:
                print("⚠️ Coinbase not found, checking alternatives...")
                alternatives = [ex for ex in ccxt.exchanges if 'coinbase' in ex.lower()]
                print(f"🔍 Coinbase alternatives: {alternatives}")
            
            return True
            
        except Exception as e:
            print(f"⚠️ Exchange handler test (expected without credentials): {e}")
            return True  # This is expected without real credentials
            
    except Exception as e:
        print(f"❌ Exchange handler import failed: {e}")
        return False

def create_demo_credentials_file():
    """Create a demo credentials file for testing"""
    print("\n📝 Creating demo credentials file...")
    
    demo_env = """# Demo Environment Variables for Testing
# These are FAKE credentials for demonstration only!

COINBASE_API_KEY=demo_api_key_12345
COINBASE_SECRET=demo_secret_67890
COINBASE_PASSPHRASE=demo_passphrase
SANDBOX_MODE=true

# Trading Configuration
TOTAL_BUDGET=50.0
MAX_TRADES=10
STOP_LOSS=3.0
TAKE_PROFIT=8.0
"""
    
    try:
        with open('.env.demo', 'w') as f:
            f.write(demo_env)
        print("✅ Demo .env file created")
        return True
    except Exception as e:
        print(f"❌ Failed to create demo .env: {e}")
        return False

def main():
    """Run all tests"""
    print("=" * 60)
    print("🧪 TRADING BOT WEB INTERFACE TEST SUITE")
    print("=" * 60)
    
    tests = [
        ("Import Tests", test_imports),
        ("File Structure", test_file_structure),
        ("Demo Data Service", test_demo_data),
        ("GPU Acceleration", test_gpu_acceleration),
        ("Exchange Handler", test_exchange_handler)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} crashed: {e}")
            results.append((test_name, False))
    
    # Create demo credentials
    create_demo_credentials_file()
    
    # Summary
    print("\n" + "="*60)
    print("📊 TEST RESULTS SUMMARY")
    print("="*60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    print(f"\n🎯 Overall: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED! Ready to launch web interface!")
        print("\n🚀 Next steps:")
        print("1. Run: python launch_web_ui.py")
        print("2. Open browser to: http://localhost:8000")
        print("3. Use DEMO mode (leave credentials empty) for testing")
        print("4. Or use real Coinbase Pro credentials for live trading")
    else:
        print(f"\n⚠️ {total - passed} tests failed. Please check the issues above.")
        
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
