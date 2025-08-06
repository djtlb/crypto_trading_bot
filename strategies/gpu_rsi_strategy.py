"""
GPU-Accelerated RSI Strategy Module
=================================

Enhanced RSI strategy with AMD GPU acceleration for faster calculations.
"""

import logging
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple

# Import the base strategy and GPU acceleration
from strategies.rsi_strategy import RSIStrategy as BaseRSIStrategy
from utils.gpu_acceleration import gpu_accelerator

logger = logging.getLogger("GPUAcceleratedRSI")

class GPUAcceleratedRSIStrategy(BaseRSIStrategy):
    """
    GPU-Accelerated RSI Strategy
    
    Inherits from the base RSI strategy but uses GPU acceleration
    for faster indicator calculations and data processing.
    """
    
    def __init__(self, *args, **kwargs):
        """Initialize the GPU-accelerated RSI strategy"""
        super().__init__(*args, **kwargs)
        self.gpu_accelerator = gpu_accelerator
        logger.info(f"GPU-accelerated RSI strategy initialized (GPU available: {self.gpu_accelerator.gpu_available})")
    
    def _get_market_data(self) -> pd.DataFrame:
        """
        Get market data with GPU acceleration for DataFrame operations
        """
        # Get data using parent method
        data = super()._get_market_data()
        
        if data.empty:
            return data
        
        # Apply GPU acceleration to DataFrame operations if available
        if self.gpu_accelerator.use_polars and len(data) > 50:
            try:
                data = self.gpu_accelerator.accelerated_dataframe_ops(data)
                logger.debug(f"Applied GPU acceleration to market data for {self.symbol}")
            except Exception as e:
                logger.warning(f"GPU DataFrame acceleration failed: {e}")
        
        return data
    
    def _calculate_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate RSI indicators using GPU acceleration
        """
        if data.empty or len(data) < self.rsi_period:
            return data
        
        try:
            # Use GPU-accelerated RSI calculation
            prices = data['close'].values
            
            if self.gpu_accelerator.gpu_available and len(prices) > 50:
                # GPU-accelerated RSI calculation
                rsi_values = self.gpu_accelerator.accelerated_rsi(prices, self.rsi_period)
                data['rsi'] = rsi_values
                logger.debug(f"GPU-accelerated RSI calculation completed for {self.symbol}")
            else:
                # Fallback to optimized CPU calculation
                data = self._calculate_indicators_cpu_optimized(data)
                logger.debug(f"CPU-optimized RSI calculation used for {self.symbol}")
            
            return data
            
        except Exception as e:
            logger.warning(f"GPU RSI calculation failed, using fallback: {e}")
            return super()._calculate_indicators(data)
    
    def _calculate_indicators_cpu_optimized(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Optimized CPU-based RSI calculation using vectorized operations
        """
        try:
            # Vectorized price change calculation
            price_changes = data['close'].diff().values
            
            # Vectorized gains and losses
            gains = np.where(price_changes > 0, price_changes, 0.0)
            losses = np.where(price_changes < 0, -price_changes, 0.0)
            
            # Use pandas rolling for efficiency
            data['gain'] = pd.Series(gains, index=data.index)
            data['loss'] = pd.Series(losses, index=data.index)
            
            # Calculate averages using exponential weighted mean for efficiency
            alpha = 1.0 / self.rsi_period
            data['avg_gain'] = data['gain'].ewm(alpha=alpha, adjust=False).mean()
            data['avg_loss'] = data['loss'].ewm(alpha=alpha, adjust=False).mean()
            
            # Avoid division by zero
            rs = data['avg_gain'] / (data['avg_loss'] + 1e-10)
            data['rsi'] = 100 - (100 / (1 + rs))
            
            return data
            
        except Exception as e:
            logger.warning(f"CPU-optimized RSI calculation failed: {e}")
            return super()._calculate_indicators(data)
    
    def execute(self):
        """
        Execute strategy with performance monitoring
        """
        import time
        start_time = time.time()
        
        try:
            # Execute using parent method but with our GPU-accelerated calculations
            super().execute()
            
            execution_time = time.time() - start_time
            logger.debug(f"GPU-accelerated RSI strategy execution completed in {execution_time:.4f}s for {self.symbol}")
            
        except Exception as e:
            logger.error(f"GPU-accelerated RSI strategy execution failed: {e}")
            raise
    
    def get_performance_metrics(self) -> Dict:
        """
        Get performance metrics including GPU utilization
        """
        metrics = {
            'strategy_type': 'gpu_accelerated_rsi',
            'gpu_available': self.gpu_accelerator.gpu_available,
            'use_opencl': self.gpu_accelerator.use_opencl,
            'use_numba': self.gpu_accelerator.use_numba,
            'use_polars': self.gpu_accelerator.use_polars,
            'rsi_period': self.rsi_period,
            'symbol': self.symbol
        }
        
        return metrics
    
    def benchmark_performance(self, data_size: int = 1000) -> Dict:
        """
        Benchmark GPU vs CPU performance for this strategy
        """
        import time
        
        # Generate test data
        test_data = pd.DataFrame({
            'timestamp': range(data_size),
            'open': np.random.randn(data_size) * 100 + 50000,
            'high': np.random.randn(data_size) * 100 + 50100,
            'low': np.random.randn(data_size) * 100 + 49900,
            'close': np.random.randn(data_size) * 100 + 50000,
            'volume': np.random.randn(data_size) * 1000 + 10000
        })
        
        # Ensure positive prices
        test_data['close'] = np.abs(test_data['close'])
        test_data['high'] = test_data['close'] + np.abs(test_data['high'] - test_data['close'])
        test_data['low'] = test_data['close'] - np.abs(test_data['close'] - test_data['low'])
        test_data['open'] = test_data['low'] + (test_data['high'] - test_data['low']) * np.random.rand(data_size)
        
        results = {
            'data_size': data_size,
            'gpu_available': self.gpu_accelerator.gpu_available
        }
        
        try:
            # Test GPU-accelerated calculation
            start_time = time.time()
            gpu_result = self._calculate_indicators(test_data.copy())
            gpu_time = time.time() - start_time
            
            # Test original CPU calculation
            start_time = time.time()
            cpu_result = super()._calculate_indicators(test_data.copy())
            cpu_time = time.time() - start_time
            
            results.update({
                'gpu_time': gpu_time,
                'cpu_time': cpu_time,
                'speedup': cpu_time / gpu_time if gpu_time > 0 else 1.0,
                'gpu_success': len(gpu_result) > 0,
                'cpu_success': len(cpu_result) > 0
            })
            
            # Check accuracy
            if len(gpu_result) > 0 and len(cpu_result) > 0 and 'rsi' in gpu_result.columns and 'rsi' in cpu_result.columns:
                # Compare RSI values (allowing for small numerical differences)
                gpu_rsi = gpu_result['rsi'].dropna()
                cpu_rsi = cpu_result['rsi'].dropna()
                
                if len(gpu_rsi) > 0 and len(cpu_rsi) > 0:
                    min_len = min(len(gpu_rsi), len(cpu_rsi))
                    mse = np.mean((gpu_rsi.iloc[:min_len] - cpu_rsi.iloc[:min_len]) ** 2)
                    results['accuracy_mse'] = mse
                    results['accuracy_good'] = mse < 1e-6
            
        except Exception as e:
            logger.error(f"Benchmark failed: {e}")
            results['error'] = str(e)
        
        return results
