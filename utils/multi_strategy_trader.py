"""
Multi-Strategy Trader Module with Pump Detection
===============================================

Manages trading strategies including the pump detection strategy.
"""

import logging
import time
import threading
from typing import Dict, List, Optional
from datetime import datetime, timedelta

# Import trading strategies
from strategies.pump_detection_strategy import PumpDetectionStrategy

logger = logging.getLogger("MultiStrategyTrader")

class MultiStrategyTrader:
    """Manages multiple trading strategies for diversified trading"""
    
    def __init__(self, exchange_handler, portfolio_manager, risk_manager):
        """
        Initialize the multi-strategy trader
        
        Args:
            exchange_handler: Exchange handler instance
            portfolio_manager: Portfolio manager instance
            risk_manager: Risk manager instance
        """
        self.exchange_handler = exchange_handler
        self.portfolio_manager = portfolio_manager
        self.risk_manager = risk_manager
        self.strategies = {}
        self.active = False
        self.execution_threads = {}
        
        # Trading symbols to monitor
        self.symbols = ['BTC-USD', 'ETH-USD', 'LTC-USD']
        
        # Strategy execution interval (in seconds)
        self.execution_interval = 10  # Check every 10 seconds
        
    def add_strategy(self, strategy_name: str, strategy_instance, symbols: List[str] = None):
        """
        Add a trading strategy
        
        Args:
            strategy_name: Name of the strategy
            strategy_instance: Strategy instance
            symbols: Trading symbols for this strategy
        """
        self.strategies[strategy_name] = {
            "instance": strategy_instance,
            "symbols": symbols or self.symbols,
            "active": True,
            "trade_count": 0,
            "successful_trades": 0,
            "failed_trades": 0,
            "last_execution": {}
        }
        logger.info(f"Added strategy: {strategy_name}")
    
    def start_trading(self):
        """Start the multi-strategy trading"""
        self.active = True
        
        # Start execution thread for pump detection
        thread = threading.Thread(
            target=self._strategy_execution_loop,
            daemon=True
        )
        thread.start()
        self.execution_threads['pump_detection'] = thread
        logger.info("Started pump detection strategy thread")
        
        logger.info("Multi-strategy trading started")
    
    def initialize_gpu_strategies(self):
        """Initialize the pump detection strategy (simplified from GPU strategies)"""
        try:
            # Initialize pump detection strategy with config from config.py
            from config import TRADING_PAIR, TRADE_AMOUNT_USD, TAKE_PROFIT_PERCENT, STOP_LOSS_PERCENT
            
            pump_config = {
                'trading_pair': TRADING_PAIR,
                'trade_amount_usd': TRADE_AMOUNT_USD,
                'take_profit_percent': TAKE_PROFIT_PERCENT,
                'stop_loss_percent': STOP_LOSS_PERCENT,
                'pump_threshold': 0.8,  # 0.8% price increase threshold
                'volume_multiplier': 1.5  # 1.5x volume spike
            }
            
            pump_strategy = PumpDetectionStrategy(
                exchange_handler=self.exchange_handler,
                portfolio_manager=self.portfolio_manager,
                config=pump_config
            )
            
            self.add_strategy("pump_detection", pump_strategy, [TRADING_PAIR])
            
            logger.info("Pump detection strategy initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize pump detection strategy: {e}")
            # Fallback: create a basic strategy
            pump_strategy = PumpDetectionStrategy(
                exchange_handler=self.exchange_handler,
                portfolio_manager=self.portfolio_manager,
                config={
                    'trading_pair': 'BTC-USD',
                    'trade_amount_usd': 20,
                    'take_profit_percent': 1.5,
                    'stop_loss_percent': 1.0
                }
            )
            self.add_strategy("pump_detection", pump_strategy, ['BTC-USD'])
            logger.info("Pump detection strategy initialized with default config")
    
    def _strategy_execution_loop(self):
        """Main execution loop for strategies"""
        logger.info("Strategy execution loop started")
        
        while self.active:
            try:
                for strategy_name, strategy_info in self.strategies.items():
                    if not strategy_info["active"]:
                        continue
                        
                    try:
                        # Execute strategy
                        result = strategy_info["instance"].execute_strategy()
                        
                        # Update strategy stats
                        strategy_info["last_execution"] = {
                            "timestamp": datetime.now().isoformat(),
                            "result": result
                        }
                        
                        # Update trade counts based on result
                        if result.get("action") in ["buy", "sell"]:
                            strategy_info["trade_count"] += 1
                            
                        if result.get("action") == "sell":
                            if result.get("profit_usd", 0) > 0:
                                strategy_info["successful_trades"] += 1
                            else:
                                strategy_info["failed_trades"] += 1
                        
                        # Log important actions
                        if result.get("action") not in ["none", "error"]:
                            logger.info(f"Strategy {strategy_name}: {result.get('message', 'Action taken')}")
                            
                    except Exception as e:
                        logger.error(f"Error executing strategy {strategy_name}: {e}")
                        strategy_info["last_execution"] = {
                            "timestamp": datetime.now().isoformat(),
                            "error": str(e)
                        }
                
                # Wait before next execution
                time.sleep(self.execution_interval)
                
            except Exception as e:
                logger.error(f"Error in strategy execution loop: {e}")
                time.sleep(self.execution_interval)
        
        logger.info("Strategy execution loop stopped")
    
    def stop_trading(self):
        """Stop all trading strategies"""
        self.active = False
        logger.info("Multi-strategy trading stopped")
    
    def get_strategy_performance(self, strategy_name: str = None) -> Dict:
        """
        Get performance metrics for strategies
        
        Args:
            strategy_name: Specific strategy name, or None for all
            
        Returns:
            Dict with performance data
        """
        if strategy_name and strategy_name in self.strategies:
            strategy_info = self.strategies[strategy_name]
            performance = strategy_info["instance"].get_performance_metrics()
            performance.update({
                "active": strategy_info["active"],
                "last_execution": strategy_info["last_execution"]
            })
            return {strategy_name: performance}
        
        # Return all strategies
        all_performance = {}
        for name, strategy_info in self.strategies.items():
            try:
                performance = strategy_info["instance"].get_performance_metrics()
                performance.update({
                    "active": strategy_info["active"],
                    "last_execution": strategy_info["last_execution"]
                })
                all_performance[name] = performance
            except Exception as e:
                all_performance[name] = {
                    "error": str(e),
                    "active": strategy_info["active"]
                }
        
        return all_performance
    
    def benchmark_gpu_performance(self) -> Dict:
        """Return pump detection strategy performance instead of GPU benchmark"""
        try:
            performance = self.get_strategy_performance()
            return {
                "pump_detection_performance": performance,
                "benchmark_type": "trading_strategy_performance",
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            return {
                "error": str(e),
                "benchmark_type": "trading_strategy_performance",
                "timestamp": datetime.now().isoformat()
            }

    def get_trading_summary(self) -> Dict:
        """
        Get a summary of trading activities
        
        Returns:
            Dictionary with trading summary
        """
        portfolio_status = self.portfolio_manager.get_portfolio_status()
        
        strategy_stats = {}
        total_trades = 0
        total_successful = 0
        
        for strategy_name, strategy_info in self.strategies.items():
            trades = strategy_info['trade_count']
            successful = strategy_info['successful_trades']
            success_rate = (successful / trades * 100) if trades > 0 else 0
            
            strategy_stats[strategy_name] = {
                'total_trades': trades,
                'successful_trades': successful,
                'success_rate': success_rate
            }
            
            total_trades += trades
            total_successful += successful
        
        overall_success_rate = (total_successful / total_trades * 100) if total_trades > 0 else 0
        
        return {
            'portfolio_status': portfolio_status,
            'strategy_performance': strategy_stats,
            'overall_stats': {
                'total_trades': total_trades,
                'successful_trades': total_successful,
                'success_rate': overall_success_rate
            }
        }
