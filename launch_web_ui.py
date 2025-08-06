#!/usr/bin/env python3
"""
Web Interface Launcher for GPU-Accelerated Crypto Trading Bot
===========================================================

Launch script for the trading bot web interface
"""

import os
import sys
import subprocess
import webbrowser
import time
from pathlib import Path

def check_requirements():
    """Check if required packages are installed"""
    try:
        import fastapi
        import uvicorn
        import pydantic
        print("✅ All required packages are installed")
        return True
    except ImportError as e:
        print(f"❌ Missing required package: {e}")
        print("Installing required packages...")
        try:
            subprocess.run([sys.executable, "-m", "pip", "install", "fastapi", "uvicorn", "pydantic", "python-multipart"], check=True)
            print("✅ Packages installed successfully")
            return True
        except subprocess.CalledProcessError:
            print("❌ Failed to install packages")
            return False

def check_project_structure():
    """Check if project structure is correct"""
    required_dirs = [
        "frontend",
        "frontend/static",
        "frontend/static/css",
        "frontend/static/js",
        "utils"
    ]
    
    required_files = [
        "frontend/index.html",
        "frontend/static/css/style.css", 
        "frontend/static/js/app.js",
        "api_server.py",
        "utils/exchange_handler.py"
    ]
    
    missing_dirs = []
    missing_files = []
    
    for dir_path in required_dirs:
        if not os.path.exists(dir_path):
            missing_dirs.append(dir_path)
    
    for file_path in required_files:
        if not os.path.exists(file_path):
            missing_files.append(file_path)
    
    if missing_dirs:
        print(f"❌ Missing directories: {', '.join(missing_dirs)}")
        return False
    
    if missing_files:
        print(f"❌ Missing files: {', '.join(missing_files)}")
        return False
    
    print("✅ Project structure is correct")
    return True

def start_server():
    """Start the FastAPI server"""
    print("🚀 Starting GPU-Accelerated Trading Bot Web Interface...")
    print("📡 Server will be available at: http://localhost:8000")
    print("🛑 Press Ctrl+C to stop the server")
    print("-" * 60)
    
    try:
        # Start the server
        subprocess.run([
            sys.executable, "-m", "uvicorn", 
            "api_server:app", 
            "--host", "0.0.0.0", 
            "--port", "8000",
            "--reload"
        ], check=True)
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to start server: {e}")
        return False
    
    return True

def open_browser():
    """Open web browser to the application"""
    url = "http://localhost:8000"
    print(f"🌐 Opening browser to {url}")
    try:
        webbrowser.open(url)
    except Exception as e:
        print(f"⚠️ Could not open browser automatically: {e}")
        print(f"Please manually open: {url}")

def main():
    """Main launcher function"""
    print("=" * 60)
    print("🤖 GPU-Accelerated Crypto Trading Bot Web Interface")
    print("=" * 60)
    
    # Check if we're in the right directory
    if not os.path.exists("api_server.py"):
        print("❌ Please run this script from the crypto_trading_bot directory")
        sys.exit(1)
    
    # Check requirements
    if not check_requirements():
        sys.exit(1)
    
    # Check project structure
    if not check_project_structure():
        print("❌ Project structure is incomplete. Please ensure all files are present.")
        sys.exit(1)
    
    print("✅ All checks passed!")
    print()
    
    # Give user information
    print("📋 Getting Started:")
    print("1. The web interface will open in your browser")
    print("2. Connect to Coinbase Pro with your API credentials")
    print("3. Use sandbox mode for testing (recommended)")
    print("4. Start automated trading or place manual trades")
    print("5. Monitor GPU acceleration and performance")
    print()
    
    # Ask user if they want to continue
    try:
        response = input("🚀 Ready to start? (y/n): ").lower().strip()
        if response not in ['y', 'yes']:
            print("👋 Goodbye!")
            sys.exit(0)
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
        sys.exit(0)
    
    # Open browser after a delay
    import threading
    def delayed_browser_open():
        time.sleep(3)  # Wait for server to start
        open_browser()
    
    browser_thread = threading.Thread(target=delayed_browser_open)
    browser_thread.daemon = True
    browser_thread.start()
    
    # Start the server
    start_server()

if __name__ == "__main__":
    main()
