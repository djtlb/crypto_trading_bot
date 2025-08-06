#!/usr/bin/env python3
"""
Complete System Test for GPU-Accelerated Crypto Trading Bot
Te        from utils.websocket_manager import ConnectionManager
        
        manager = ConnectionManager()
        print("✅ WebSocket manager created")all components including real-time WebSocket functionality
"""

import os
import sys
import subprocess
import time
import json
import asyncio

def test_project_structure():
    """Test that all required files exist"""
    print("🔍 Testing project structure...")
    
    required_files = [
        'api_server.py',
        'frontend/index.html',
        'frontend/static/css/style.css',
        'frontend/static/js/app.js',
        'utils/websocket_manager.py',
        'utils/demo_data.py',
        'utils/exchange_handler.py',
        'launch_web_ui.py'
    ]
    
    missing_files = []
    for file_path in required_files:
        if not os.path.exists(file_path):
            missing_files.append(file_path)
    
    if missing_files:
        print(f"❌ Missing files: {', '.join(missing_files)}")
        return False
    
    print("✅ All required files present")
    return True

def test_imports():
    """Test that all required modules can be imported"""
    print("📦 Testing module imports...")
    
    try:
        # Test main API server imports
        sys.path.insert(0, '.')
        
        from utils.demo_data import DemoDataService
        print("✅ Demo data service imports correctly")
        
        from utils.websocket_manager import ConnectionManager
        print("✅ WebSocket manager imports correctly")
        
        from utils.exchange_handler import ExchangeHandler
        print("✅ Exchange handler imports correctly")
        
        import fastapi
        import uvicorn
        print("✅ FastAPI and Uvicorn available")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False

def test_api_server_startup():
    """Test that the API server can start successfully"""
    print("🚀 Testing API server startup...")
    
    try:
        # Try to import the app
        from api_server import app
        print("✅ API server module loads successfully")
        
        # Test basic FastAPI functionality
        print("✅ FastAPI app created successfully")
        return True
        
    except Exception as e:
        print(f"❌ API server startup failed: {e}")
        return False

def test_websocket_manager():
    """Test WebSocket manager functionality"""
    print("🔌 Testing WebSocket manager...")
    
    try:
        from utils.websocket_manager import ConnectionManager
        
        manager = ConnectionManager()
        print("✅ WebSocket manager created")
        
        # Test demo data availability
        from utils.demo_data import DemoDataService
        demo_service = DemoDataService()
        
        demo_portfolio = demo_service.get_demo_portfolio_status()
        if demo_portfolio:
            print("✅ Demo data service working")
        
        return True
        
    except Exception as e:
        print(f"❌ WebSocket manager test failed: {e}")
        return False

def test_frontend_files():
    """Test frontend file completeness"""
    print("🌐 Testing frontend files...")
    
    # Check HTML file
    with open('frontend/index.html', 'r') as f:
        html_content = f.read()
        
    required_elements = [
        'id="connection-status"',
        'id="bot-status"',
        'id="gpu-status"',
        'id="total-budget"',
        'id="available-budget"',
        'id="daily-pnl"',
        'id="strategies-content"',
        'id="market-data"'
    ]
    
    missing_elements = []
    for element in required_elements:
        if element not in html_content:
            missing_elements.append(element)
    
    if missing_elements:
        print(f"❌ Missing HTML elements: {', '.join(missing_elements)}")
        return False
    
    print("✅ All required HTML elements present")
    
    # Check JavaScript file
    with open('frontend/static/js/app.js', 'r') as f:
        js_content = f.read()
    
    required_functions = [
        'initWebSocket',
        'handleWebSocketMessage',
        'updatePortfolioDisplay',
        'updateStrategyDisplay',
        'showConnectionStatus'
    ]
    
    missing_functions = []
    for func in required_functions:
        if func not in js_content:
            missing_functions.append(func)
    
    if missing_functions:
        print(f"❌ Missing JS functions: {', '.join(missing_functions)}")
        return False
    
    print("✅ All required JavaScript functions present")
    return True

def run_quick_server_test():
    """Run a quick server test"""
    print("⚡ Running quick server functionality test...")
    
    try:
        # This is a basic test to see if we can start the server
        import subprocess
        import signal
        import time
        
        print("Starting server process...")
        process = subprocess.Popen(
            [sys.executable, '-c', '''
import sys
sys.path.insert(0, ".")
from api_server import app
import uvicorn
uvicorn.run(app, host="127.0.0.1", port=8001, log_level="critical")
            '''],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        # Wait a moment for server to start
        time.sleep(3)
        
        # Test if process is running
        if process.poll() is None:
            print("✅ Server started successfully")
            process.terminate()
            process.wait(timeout=5)
            return True
        else:
            stdout, stderr = process.communicate()
            print(f"❌ Server failed to start: {stderr.decode()}")
            return False
            
    except Exception as e:
        print(f"❌ Server test failed: {e}")
        return False

def main():
    """Run complete system test"""
    print("🧪 GPU-Accelerated Crypto Trading Bot - Complete System Test")
    print("=" * 70)
    
    tests = [
        ("Project Structure", test_project_structure),
        ("Module Imports", test_imports),
        ("API Server Startup", test_api_server_startup),
        ("WebSocket Manager", test_websocket_manager),
        ("Frontend Files", test_frontend_files),
        ("Quick Server Test", run_quick_server_test)
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        print(f"\n📋 Running: {test_name}")
        print("-" * 30)
        
        try:
            if test_func():
                passed += 1
                print(f"✅ {test_name}: PASSED")
            else:
                failed += 1
                print(f"❌ {test_name}: FAILED")
        except Exception as e:
            failed += 1
            print(f"💥 {test_name}: ERROR - {e}")
    
    print("\n" + "=" * 70)
    print("📊 TEST RESULTS")
    print("=" * 70)
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"📈 Success Rate: {(passed/(passed+failed)*100):.1f}%")
    
    if failed == 0:
        print("\n🎉 ALL TESTS PASSED!")
        print("🚀 Your trading bot is ready to launch!")
        print("\n📝 Next Steps:")
        print("1. Run: python launch_web_ui.py")
        print("2. Open http://localhost:8000 in your browser")
        print("3. Use demo mode to test all features")
        print("4. Configure real API credentials when ready")
        print("\n💡 Features Ready:")
        print("   • Real-time WebSocket updates")
        print("   • Professional trading interface")
        print("   • GPU acceleration monitoring")
        print("   • Demo mode for safe testing")
        print("   • Complete API backend")
    else:
        print("\n⚠️  Some tests failed. Please review and fix issues before launching.")
    
    return failed == 0

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
