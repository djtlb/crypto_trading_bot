#!/usr/bin/env python3
"""
Bot Runner with Dashboard
========================

Runs the trading bot and generates a monitoring dashboard.
"""

import os
import sys
import time
import threading
import argparse
from datetime import datetime

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from main import initialize
from utils.dashboard import TradingDashboard

def run_bot_with_dashboard():
    """Run the bot with dashboard monitoring"""
    print("Starting Crypto Trading Bot with Dashboard...")
    
    try:
        # Initialize the bot components
        multi_trader, portfolio_manager = initialize()
        
        # Create dashboard
        dashboard = TradingDashboard(portfolio_manager, multi_trader)
        
        # Start the multi-strategy trader
        multi_trader.start_trading()
        
        print("Bot started successfully!")
        print("Dashboard will be updated every 30 seconds...")
        print("Press Ctrl+C to stop the bot")
        
        # Dashboard update loop
        def update_dashboard():
            while True:
                try:
                    # Print status to console
                    dashboard.print_status()
                    
                    # Save data to JSON
                    dashboard.save_dashboard_data('logs/dashboard_data.json')
                    
                    # Create HTML dashboard
                    dashboard.create_simple_html_dashboard('logs/dashboard.html')
                    
                    # Wait 30 seconds
                    time.sleep(30)
                    
                except Exception as e:
                    print(f"Dashboard update error: {e}")
                    time.sleep(60)  # Wait longer on error
        
        # Start dashboard in a separate thread
        dashboard_thread = threading.Thread(target=update_dashboard, daemon=True)
        dashboard_thread.start()
        
        # Keep main thread alive
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nShutting down bot...")
            multi_trader.stop_trading()
            
            # Print final summary
            print("\n" + "="*50)
            print("FINAL TRADING SUMMARY")
            print("="*50)
            summary = multi_trader.get_trading_summary()
            
            portfolio = summary['portfolio_status']
            print(f"Final Budget: ${portfolio['total_budget']:.2f}")
            print(f"Total Return: ${portfolio['total_budget'] - 50:.2f}")
            print(f"Return Percentage: {((portfolio['total_budget'] - 50) / 50) * 100:.2f}%")
            print(f"Total Trades: {summary['overall_stats']['total_trades']}")
            print(f"Success Rate: {summary['overall_stats']['success_rate']:.1f}%")
            print("="*50)
            
    except Exception as e:
        print(f"Error running bot: {e}")
        sys.exit(1)

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Crypto Trading Bot with Dashboard")
    parser.add_argument("--dashboard-only", action="store_true", 
                       help="Only show dashboard without trading")
    parser.add_argument("--check-config", action="store_true",
                       help="Check configuration and exit")
    
    args = parser.parse_args()
    
    # Create logs directory
    os.makedirs("logs", exist_ok=True)
    
    if args.check_config:
        print("Checking configuration...")
        try:
            from dotenv import load_dotenv
            load_dotenv()
            
            required_vars = ['EXCHANGE', 'TRADING_SYMBOL', 'TRADE_AMOUNT', 'TOTAL_BUDGET']
            missing_vars = []
            
            for var in required_vars:
                if not os.getenv(var):
                    missing_vars.append(var)
            
            if missing_vars:
                print(f"Missing required environment variables: {missing_vars}")
                print("Please check your .env file")
                sys.exit(1)
            else:
                print("Configuration check passed!")
                print(f"Exchange: {os.getenv('EXCHANGE')}")
                print(f"Symbol: {os.getenv('TRADING_SYMBOL')}")
                print(f"Trade Amount: ${os.getenv('TRADE_AMOUNT')}")
                print(f"Total Budget: ${os.getenv('TOTAL_BUDGET')}")
                
        except Exception as e:
            print(f"Configuration check failed: {e}")
            sys.exit(1)
    
    elif args.dashboard_only:
        print("Dashboard-only mode not implemented yet")
        print("Use the main bot to generate dashboard data")
    
    else:
        run_bot_with_dashboard()

if __name__ == "__main__":
    main()
