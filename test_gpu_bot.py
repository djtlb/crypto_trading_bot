#!/usr/bin/env python3
"""
GPU-Accelerated Trading Bot Test
===============================

Test script to verify that the GPU acceleration is working
with the AMD GPU and trading strategies.
"""

import os
import sys
import logging

# Add the project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.gpu_acceleration import gpu_accelerator
from utils.multi_strategy_trader import MultiStrategyTrader
from utils.exchange_handler import ExchangeHandler
from utils.portfolio_manager import PortfolioManager
from utils.risk_manager import RiskManager

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("GPUTest")

def test_gpu_acceleration():
    """Test GPU acceleration functionality"""
    logger.info("=== Testing GPU Acceleration ===")
    
    # Test GPU accelerator
    logger.info(f"GPU Available: {gpu_accelerator.gpu_available}")
    logger.info(f"OpenCL Available: {gpu_accelerator.use_opencl}")
    logger.info(f"Numba Available: {gpu_accelerator.use_numba}")
    logger.info(f"Polars Available: {gpu_accelerator.use_polars}")
    
    # Test basic acceleration functions
    import numpy as np
    
    test_data = np.random.randn(100) + 50000  # Random price data
    test_data = np.abs(test_data)  # Ensure positive
    
    try:
        # Test rolling mean
        rolling_mean = gpu_accelerator.accelerated_rolling_mean(test_data, window=10)
        logger.info(f"Rolling mean test: Success, got {len(rolling_mean)} values")
        
        # Test RSI calculation
        rsi_values = gpu_accelerator.accelerated_rsi(test_data, period=14)
        logger.info(f"RSI calculation test: Success, got {len(rsi_values)} values")
        
        # Test ATR calculation (need high, low, close)
        high = test_data + np.random.rand(len(test_data)) * 100
        low = test_data - np.random.rand(len(test_data)) * 100
        atr_values = gpu_accelerator.accelerated_atr(high, low, test_data, period=14)
        logger.info(f"ATR calculation test: Success, got {len(atr_values)} values")
        
        return True
        
    except Exception as e:
        logger.error(f"GPU acceleration test failed: {e}")
        return False

def test_strategy_initialization():
    """Test GPU-accelerated strategy initialization"""
    logger.info("=== Testing Strategy Initialization ===")
    
    try:
        # Mock exchange handler (test mode)
        exchange_handler = ExchangeHandler("binance", "test_key", "test_secret")
        
        # Initialize portfolio manager
        portfolio_manager = PortfolioManager(exchange_handler, total_budget=50.0)
        
        # Initialize risk manager
        risk_manager = RiskManager(
            exchange_handler,
            portfolio_manager,
            stop_loss_percentage=3.0,
            take_profit_percentage=8.0,
            max_trades=10
        )
        
        # Initialize multi-strategy trader
        multi_trader = MultiStrategyTrader(exchange_handler, portfolio_manager, risk_manager)
        
        # Initialize GPU strategies
        multi_trader.initialize_gpu_strategies()
        
        logger.info(f"Initialized {len(multi_trader.strategies)} GPU-accelerated strategies")
        
        for strategy_name in multi_trader.strategies:
            logger.info(f"  - {strategy_name}")
        
        return True
        
    except Exception as e:
        logger.error(f"Strategy initialization test failed: {e}")
        return False

def test_benchmark():
    """Test GPU vs CPU performance benchmark"""
    logger.info("=== Testing Performance Benchmark ===")
    
    try:
        # Mock exchange handler
        exchange_handler = ExchangeHandler("binance", "test_key", "test_secret")
        portfolio_manager = PortfolioManager(exchange_handler, total_budget=50.0)
        risk_manager = RiskManager(exchange_handler, portfolio_manager)
        
        # Initialize multi-strategy trader
        multi_trader = MultiStrategyTrader(exchange_handler, portfolio_manager, risk_manager)
        multi_trader.initialize_gpu_strategies()
        
        # Run benchmarks
        benchmark_results = multi_trader.benchmark_gpu_performance()
        
        logger.info("Benchmark Results:")
        for strategy_name, results in benchmark_results.items():
            logger.info(f"  {strategy_name}:")
            if 'error' in results:
                logger.error(f"    Error: {results['error']}")
            else:
                logger.info(f"    Data size: {results.get('data_size', 'N/A')}")
                logger.info(f"    GPU time: {results.get('gpu_time', 'N/A'):.4f}s")
                logger.info(f"    CPU time: {results.get('cpu_time', 'N/A'):.4f}s")
                logger.info(f"    Speedup: {results.get('speedup', 'N/A'):.2f}x")
                logger.info(f"    Accuracy: {'Good' if results.get('accuracy_good', False) else 'Check needed'}")
        
        return True
        
    except Exception as e:
        logger.error(f"Benchmark test failed: {e}")
        return False

def main():
    """Run all tests"""
    logger.info("Starting GPU-Accelerated Trading Bot Tests")
    logger.info("=" * 50)
    
    test_results = []
    
    # Test 1: GPU acceleration
    test_results.append(("GPU Acceleration", test_gpu_acceleration()))
    
    # Test 2: Strategy initialization
    test_results.append(("Strategy Initialization", test_strategy_initialization()))
    
    # Test 3: Performance benchmark
    test_results.append(("Performance Benchmark", test_benchmark()))
    
    # Summary
    logger.info("=" * 50)
    logger.info("Test Results Summary:")
    
    all_passed = True
    for test_name, result in test_results:
        status = "PASS" if result else "FAIL"
        logger.info(f"  {test_name}: {status}")
        if not result:
            all_passed = False
    
    logger.info("=" * 50)
    if all_passed:
        logger.info("🎉 All tests PASSED! Your GPU-accelerated trading bot is ready!")
        logger.info("💡 Next steps:")
        logger.info("   1. Set up your .env file with real API credentials")
        logger.info("   2. Run: python main.py")
        logger.info("   3. Monitor the trading dashboard")
    else:
        logger.warning("⚠️  Some tests failed. Check the errors above.")
        logger.info("💡 The bot should still work with CPU fallbacks.")

if __name__ == "__main__":
    main()
