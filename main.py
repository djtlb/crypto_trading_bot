#!/usr/bin/env python3
"""
Crypto Trading Bot - Main Module
===============================

This bot attempts to make profitable trades on cryptocurrency exchanges.
IMPORTANT: This is for educational purposes only. Trading cryptocurrencies 
involves significant risk of loss. Use at your own risk.
"""

import os
import time
import logging
import schedule
from dotenv import load_dotenv

from utils.exchange_handler import ExchangeHandler
from utils.risk_manager import RiskManager
from utils.portfolio_manager import PortfolioManager
from utils.multi_strategy_trader import MultiStrategyTrader
from strategies.strategy_factory import StrategyFactory

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/trading_bot.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("TradingBot")

def initialize():
    """Initialize the trading bot with configurations from .env file"""
    load_dotenv()
    
    exchange_id = os.getenv("EXCHANGE", "binance")
    api_key = os.getenv("API_KEY")
    api_secret = os.getenv("API_SECRET")
    
    # Trading parameters
    symbol = os.getenv("TRADING_SYMBOL", "BTC/USDT")
    trade_amount = float(os.getenv("TRADE_AMOUNT", "5"))
    use_percentage = float(os.getenv("USE_PERCENTAGE", "95"))
    total_budget = float(os.getenv("TOTAL_BUDGET", "50"))
    
    # Initialize exchange handler
    exchange_handler = ExchangeHandler(exchange_id, api_key, api_secret)
    
    # Initialize portfolio manager
    portfolio_manager = PortfolioManager(exchange_handler, total_budget)
    
    # Initialize risk manager
    stop_loss = float(os.getenv("STOP_LOSS_PERCENTAGE", "3"))
    take_profit = float(os.getenv("TAKE_PROFIT_PERCENTAGE", "8"))
    max_trades = int(os.getenv("MAX_TRADES", "10"))
    
    risk_manager = RiskManager(
        exchange_handler,
        portfolio_manager,
        stop_loss_percentage=stop_loss,
        take_profit_percentage=take_profit,
        max_trades=max_trades
    )
    
    # Initialize GPU-accelerated multi-strategy trader
    multi_trader = MultiStrategyTrader(exchange_handler, portfolio_manager, risk_manager)
    
    # Initialize GPU-accelerated strategies
    logger.info("Initializing GPU-accelerated trading strategies...")
    multi_trader.initialize_gpu_strategies()
    
    # Benchmark GPU performance
    logger.info("Benchmarking GPU performance...")
    benchmark_results = multi_trader.benchmark_gpu_performance()
    logger.info(f"GPU Benchmark Results: {benchmark_results}")
    
    return multi_trader, portfolio_manager

def execute_trading_cycle(multi_trader, portfolio_manager):
    """Execute one complete trading cycle"""
    try:
        logger.info("Checking trading opportunities...")
        
        # Get portfolio status
        status = portfolio_manager.get_portfolio_status()
        
        if status['available_budget'] < 3:
            logger.info("Insufficient budget for new trades")
            return
        
        if status['active_trades'] >= status['max_concurrent_trades']:
            logger.info("Maximum concurrent trades reached")
            return
        
        # The multi-trader handles strategy execution automatically
        # This cycle just logs status
        logger.info(f"Portfolio: ${status['available_budget']:.2f} available, "
                   f"{status['active_trades']} active trades")
        
    except Exception as e:
        logger.error(f"Error during trading cycle: {str(e)}")

def run_bot():
    """Run the bot continuously with multi-strategy trading"""
    multi_trader, portfolio_manager = initialize()
    
    # Start the multi-strategy trader
    multi_trader.start_trading()
    
    # Schedule periodic status checks
    schedule.every(5).minutes.do(execute_trading_cycle, multi_trader, portfolio_manager)
    
    logger.info("Multi-strategy bot started. Press Ctrl+C to stop.")
    
    try:
        while True:
            schedule.run_pending()
            time.sleep(30)  # Check every 30 seconds
    except KeyboardInterrupt:
        logger.info("Bot stopping...")
        multi_trader.stop_trading()
        
        # Print final summary
        summary = multi_trader.get_trading_summary()
        logger.info(f"Final Summary: {summary}")

def run_single_strategy():
    """Run with a single strategy (legacy mode)"""
    load_dotenv()
    
    exchange_id = os.getenv("EXCHANGE", "binance")
    api_key = os.getenv("API_KEY")
    api_secret = os.getenv("API_SECRET")
    
    symbol = os.getenv("TRADING_SYMBOL", "BTC/USDT")
    trade_amount = float(os.getenv("TRADE_AMOUNT", "5"))
    use_percentage = float(os.getenv("USE_PERCENTAGE", "95"))
    strategy_name = os.getenv("STRATEGY", "volatility_breakout")
    total_budget = float(os.getenv("TOTAL_BUDGET", "50"))
    
    # Initialize components
    exchange_handler = ExchangeHandler(exchange_id, api_key, api_secret)
    portfolio_manager = PortfolioManager(exchange_handler, total_budget)
    
    stop_loss = float(os.getenv("STOP_LOSS_PERCENTAGE", "3"))
    take_profit = float(os.getenv("TAKE_PROFIT_PERCENTAGE", "8"))
    max_trades = int(os.getenv("MAX_TRADES", "10"))
    
    risk_manager = RiskManager(
        exchange_handler,
        portfolio_manager,
        stop_loss_percentage=stop_loss,
        take_profit_percentage=take_profit,
        max_trades=max_trades
    )
    
    # Initialize strategy
    strategy_factory = StrategyFactory()
    strategy = strategy_factory.create_strategy(
        strategy_name, 
        exchange_handler,
        risk_manager,
        symbol=symbol,
        trade_amount=trade_amount,
        use_percentage=use_percentage
    )
    
    if not strategy:
        logger.error(f"Failed to create strategy: {strategy_name}")
        return
    
    # Single strategy execution loop
    schedule.every(2).minutes.do(lambda: strategy.execute())
    
    logger.info(f"Single strategy bot started with {strategy_name}. Press Ctrl+C to stop.")
    
    try:
        while True:
            schedule.run_pending()
            time.sleep(30)
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")

def backtest():
    """Run backtest mode instead of live trading"""
    from utils.backtester import Backtester
    
    load_dotenv()
    
    exchange_id = os.getenv("EXCHANGE", "binance")
    api_key = os.getenv("API_KEY")
    api_secret = os.getenv("API_SECRET")
    
    symbol = os.getenv("TRADING_SYMBOL", "BTC/USDT")
    trade_amount = float(os.getenv("TRADE_AMOUNT", "5"))
    use_percentage = float(os.getenv("USE_PERCENTAGE", "95"))
    strategy_name = os.getenv("STRATEGY", "volatility_breakout")
    total_budget = float(os.getenv("TOTAL_BUDGET", "50"))
    
    # Initialize components for backtesting
    exchange_handler = ExchangeHandler(exchange_id, api_key, api_secret)
    portfolio_manager = PortfolioManager(exchange_handler, total_budget)
    
    stop_loss = float(os.getenv("STOP_LOSS_PERCENTAGE", "3"))
    take_profit = float(os.getenv("TAKE_PROFIT_PERCENTAGE", "8"))
    max_trades = int(os.getenv("MAX_TRADES", "10"))
    
    risk_manager = RiskManager(
        exchange_handler,
        portfolio_manager,
        stop_loss_percentage=stop_loss,
        take_profit_percentage=take_profit,
        max_trades=max_trades
    )
    
    strategy_factory = StrategyFactory()
    strategy = strategy_factory.create_strategy(
        strategy_name, 
        exchange_handler,
        risk_manager,
        symbol=symbol,
        trade_amount=trade_amount,
        use_percentage=use_percentage
    )
    
    if not strategy:
        logger.error(f"Failed to create strategy for backtesting: {strategy_name}")
        return
    
    # Create backtester with 30 days of historical data
    backtester = Backtester(strategy, symbol, days=30)
    results = backtester.run()
    
    logger.info(f"Backtest results: {results}")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Crypto Trading Bot")
    parser.add_argument("--backtest", action="store_true", help="Run in backtest mode")
    parser.add_argument("--single", action="store_true", help="Run single strategy mode")
    args = parser.parse_args()
    
    # Create logs directory if it doesn't exist
    os.makedirs("logs", exist_ok=True)
    
    if args.backtest:
        backtest()
    elif args.single:
        run_single_strategy()
    else:
        run_bot()
