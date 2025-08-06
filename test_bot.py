#!/usr/bin/env python3
"""
Trading Bot Test Script
======================

Test script to validate all components are working correctly.
"""

import os
import sys
import traceback
from dotenv import load_dotenv

def test_imports():
    """Test that all required modules can be imported"""
    print("Testing imports...")
    
    try:
        from utils.exchange_handler import ExchangeHandler
        print("✓ ExchangeHandler import OK")
    except Exception as e:
        print(f"✗ ExchangeHandler import failed: {e}")
        return False
    
    try:
        from utils.risk_manager import RiskManager
        print("✓ RiskManager import OK")
    except Exception as e:
        print(f"✗ RiskManager import failed: {e}")
        return False
    
    try:
        from utils.portfolio_manager import PortfolioManager
        print("✓ PortfolioManager import OK")
    except Exception as e:
        print(f"✗ PortfolioManager import failed: {e}")
        return False
    
    try:
        from utils.multi_strategy_trader import MultiStrategyTrader
        print("✓ MultiStrategyTrader import OK")
    except Exception as e:
        print(f"✗ MultiStrategyTrader import failed: {e}")
        return False
    
    try:
        from strategies.strategy_factory import StrategyFactory
        print("✓ StrategyFactory import OK")
    except Exception as e:
        print(f"✗ StrategyFactory import failed: {e}")
        return False
    
    try:
        from utils.dashboard import TradingDashboard
        print("✓ TradingDashboard import OK")
    except Exception as e:
        print(f"✗ TradingDashboard import failed: {e}")
        return False
    
    return True

def test_configuration():
    """Test configuration loading"""
    print("\nTesting configuration...")
    
    load_dotenv()
    
    required_vars = [
        'EXCHANGE', 'TRADING_SYMBOL', 'TRADE_AMOUNT', 
        'TOTAL_BUDGET', 'STOP_LOSS_PERCENTAGE', 'TAKE_PROFIT_PERCENTAGE'
    ]
    
    missing_vars = []
    for var in required_vars:
        value = os.getenv(var)
        if value:
            print(f"✓ {var}: {value}")
        else:
            print(f"✗ {var}: Missing")
            missing_vars.append(var)
    
    if missing_vars:
        print(f"\nMissing required variables: {missing_vars}")
        return False
    
    return True

def test_strategy_creation():
    """Test strategy creation"""
    print("\nTesting strategy creation...")
    
    try:
        from utils.exchange_handler import ExchangeHandler
        from utils.risk_manager import RiskManager
        from utils.portfolio_manager import PortfolioManager
        from strategies.strategy_factory import StrategyFactory
        
        # Create mock components (without API keys for testing)
        exchange_handler = ExchangeHandler('binance')
        portfolio_manager = PortfolioManager(exchange_handler, 50.0)
        risk_manager = RiskManager(exchange_handler, portfolio_manager)
        
        # Test strategy factory
        factory = StrategyFactory()
        
        # Test creating strategies
        strategies_to_test = ['volatility_breakout', 'rsi_strategy', 'moving_average_cross']
        
        for strategy_name in strategies_to_test:
            try:
                strategy = factory.create_strategy(
                    strategy_name,
                    exchange_handler,
                    risk_manager,
                    symbol='BTC/USDT',
                    trade_amount=5.0
                )
                if strategy:
                    print(f"✓ {strategy_name} strategy created OK")
                else:
                    print(f"✗ {strategy_name} strategy creation returned None")
            except Exception as e:
                print(f"✗ {strategy_name} strategy creation failed: {e}")
                return False
        
        return True
        
    except Exception as e:
        print(f"✗ Strategy creation test failed: {e}")
        traceback.print_exc()
        return False

def test_portfolio_manager():
    """Test portfolio manager functionality"""
    print("\nTesting portfolio manager...")
    
    try:
        from utils.exchange_handler import ExchangeHandler
        from utils.portfolio_manager import PortfolioManager
        
        # Create mock exchange handler
        exchange_handler = ExchangeHandler('binance')
        
        # Create portfolio manager
        portfolio_manager = PortfolioManager(exchange_handler, 50.0)
        
        # Test portfolio status
        status = portfolio_manager.get_portfolio_status()
        print(f"✓ Portfolio status: {status}")
        
        # Test recommended trade size
        trade_size = portfolio_manager.get_recommended_trade_size()
        print(f"✓ Recommended trade size: ${trade_size}")
        
        # Test trade allocation
        can_trade = portfolio_manager.can_open_trade('BTC/USDT', 5.0)
        print(f"✓ Can open trade: {can_trade}")
        
        return True
        
    except Exception as e:
        print(f"✗ Portfolio manager test failed: {e}")
        traceback.print_exc()
        return False

def test_dashboard():
    """Test dashboard functionality"""
    print("\nTesting dashboard...")
    
    try:
        from utils.exchange_handler import ExchangeHandler
        from utils.portfolio_manager import PortfolioManager
        from utils.dashboard import TradingDashboard
        
        # Create mock components
        exchange_handler = ExchangeHandler('binance')
        portfolio_manager = PortfolioManager(exchange_handler, 50.0)
        
        # Create dashboard
        dashboard = TradingDashboard(portfolio_manager)
        
        # Test dashboard data
        data = dashboard.get_dashboard_data()
        print(f"✓ Dashboard data keys: {list(data.keys())}")
        
        # Test console output
        print("✓ Testing console dashboard output:")
        dashboard.print_status()
        
        return True
        
    except Exception as e:
        print(f"✗ Dashboard test failed: {e}")
        traceback.print_exc()
        return False

def main():
    """Run all tests"""
    print("="*50)
    print("CRYPTO TRADING BOT - COMPONENT TESTS")
    print("="*50)
    
    tests = [
        test_imports,
        test_configuration,
        test_strategy_creation,
        test_portfolio_manager,
        test_dashboard
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                print(f"\n❌ {test.__name__} FAILED")
        except Exception as e:
            print(f"\n❌ {test.__name__} CRASHED: {e}")
            traceback.print_exc()
    
    print("\n" + "="*50)
    print(f"TEST RESULTS: {passed}/{total} PASSED")
    print("="*50)
    
    if passed == total:
        print("🎉 ALL TESTS PASSED! Your trading bot is ready to run.")
        print("\nNext steps:")
        print("1. Set up your API keys in .env file")
        print("2. Run: python run_bot.py --check-config")
        print("3. Run: python run_bot.py")
    else:
        print("⚠️  Some tests failed. Please check the errors above.")
        sys.exit(1)

if __name__ == "__main__":
    main()
