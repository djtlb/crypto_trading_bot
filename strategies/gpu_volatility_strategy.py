"""
GPU-Accelerated Volatility Breakout Strategy Module
==================================================

Enhanced volatility breakout strategy with AMD GPU acceleration for faster calculations.
"""

import logging
import pandas as pd
import numpy as np
from typing import Dict

# Import the base strategy and GPU acceleration
from strategies.volatility_breakout import VolatilityBreakoutStrategy as BaseVolatilityStrategy
from utils.gpu_acceleration import gpu_accelerator

logger = logging.getLogger("GPUAcceleratedVolatility")

class GPUAcceleratedVolatilityStrategy(BaseVolatilityStrategy):
    """
    GPU-Accelerated Volatility Breakout Strategy
    
    Inherits from the base volatility strategy but uses GPU acceleration
    for faster ATR calculations and volatility analysis.
    """
    
    def __init__(self, *args, **kwargs):
        """Initialize the GPU-accelerated volatility strategy"""
        super().__init__(*args, **kwargs)
        self.gpu_accelerator = gpu_accelerator
        logger.info(f"GPU-accelerated volatility strategy initialized (GPU available: {self.gpu_accelerator.gpu_available})")
    
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
        Calculate volatility indicators using GPU acceleration
        """
        if data.empty or len(data) < max(self.atr_period, self.lookback_period):
            return data
        
        try:
            # Use GPU-accelerated calculations
            if self.gpu_accelerator.gpu_available and len(data) > 50:
                data = self._calculate_indicators_gpu(data)
                logger.debug(f"GPU-accelerated volatility calculation completed for {self.symbol}")
            else:
                # Fallback to optimized CPU calculation
                data = self._calculate_indicators_cpu_optimized(data)
                logger.debug(f"CPU-optimized volatility calculation used for {self.symbol}")
            
            return data
            
        except Exception as e:
            logger.warning(f"GPU volatility calculation failed, using fallback: {e}")
            return super()._calculate_indicators(data)
    
    def _calculate_indicators_gpu(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        GPU-accelerated volatility indicator calculation
        """
        try:
            # Extract price arrays
            high_prices = data['high'].values
            low_prices = data['low'].values
            close_prices = data['close'].values
            
            # GPU-accelerated ATR calculation
            atr_values = self.gpu_accelerator.accelerated_atr(
                high_prices, low_prices, close_prices, self.atr_period
            )
            data['atr'] = atr_values
            
            # GPU-accelerated rolling calculations for breakout levels
            if len(close_prices) >= self.lookback_period:
                # Calculate rolling max/min using GPU
                rolling_high = self.gpu_accelerator.accelerated_rolling_max(
                    high_prices, self.lookback_period
                )
                rolling_low = self.gpu_accelerator.accelerated_rolling_min(
                    low_prices, self.lookback_period
                )
                
                data['rolling_high'] = rolling_high
                data['rolling_low'] = rolling_low
                
                # Calculate breakout levels
                data['upper_breakout'] = data['rolling_high'] + (data['atr'] * self.breakout_multiplier)
                data['lower_breakout'] = data['rolling_low'] - (data['atr'] * self.breakout_multiplier)
            
            # GPU-accelerated volatility percentile calculation
            if len(atr_values) >= 20:  # Need enough data for percentile
                volatility_percentile = self.gpu_accelerator.accelerated_percentile(
                    atr_values[-50:] if len(atr_values) > 50 else atr_values,  # Last 50 periods
                    50  # 50th percentile (median)
                )
                data['volatility_percentile'] = volatility_percentile
            
            return data
            
        except Exception as e:
            logger.warning(f"GPU volatility indicator calculation failed: {e}")
            return self._calculate_indicators_cpu_optimized(data)
    
    def _calculate_indicators_cpu_optimized(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Optimized CPU-based volatility calculation using vectorized operations
        """
        try:
            # Vectorized True Range calculation
            high_low = data['high'] - data['low']
            high_close_prev = np.abs(data['high'] - data['close'].shift(1))
            low_close_prev = np.abs(data['low'] - data['close'].shift(1))
            
            # True Range is the maximum of the three
            true_range = np.maximum(high_low, np.maximum(high_close_prev, low_close_prev))
            data['true_range'] = true_range
            
            # ATR using exponential weighted mean for efficiency
            alpha = 1.0 / self.atr_period
            data['atr'] = data['true_range'].ewm(alpha=alpha, adjust=False).mean()
            
            # Rolling calculations using pandas (optimized)
            data['rolling_high'] = data['high'].rolling(window=self.lookback_period, min_periods=1).max()
            data['rolling_low'] = data['low'].rolling(window=self.lookback_period, min_periods=1).min()
            
            # Breakout levels
            data['upper_breakout'] = data['rolling_high'] + (data['atr'] * self.breakout_multiplier)
            data['lower_breakout'] = data['rolling_low'] - (data['atr'] * self.breakout_multiplier)
            
            # Volatility percentile using rolling quantile
            data['volatility_percentile'] = data['atr'].rolling(window=50, min_periods=20).quantile(0.5)
            
            return data
            
        except Exception as e:
            logger.warning(f"CPU-optimized volatility calculation failed: {e}")
            return super()._calculate_indicators(data)
    
    def _check_breakout_conditions(self, data: pd.DataFrame) -> tuple:
        """
        Enhanced breakout condition checking with GPU-accelerated pattern recognition
        """
        if data.empty or len(data) < 2:
            return False, False, {}
        
        try:
            current_row = data.iloc[-1]
            prev_row = data.iloc[-2]
            
            # Basic breakout conditions
            bullish_breakout = (
                current_row['close'] > current_row['upper_breakout'] and
                prev_row['close'] <= prev_row['upper_breakout']
            )
            
            bearish_breakout = (
                current_row['close'] < current_row['lower_breakout'] and
                prev_row['close'] >= prev_row['lower_breakout']
            )
            
            # Enhanced conditions with volatility analysis
            conditions = {
                'atr': current_row.get('atr', 0),
                'volatility_percentile': current_row.get('volatility_percentile', 50),
                'price_range': current_row['high'] - current_row['low'],
                'volume_surge': False  # Could be enhanced with volume analysis
            }
            
            # Filter based on volatility - avoid trading in extremely low volatility periods
            if conditions['volatility_percentile'] < 20:
                bullish_breakout = False
                bearish_breakout = False
                conditions['low_volatility_filter'] = True
            
            return bullish_breakout, bearish_breakout, conditions
            
        except Exception as e:
            logger.warning(f"Enhanced breakout condition check failed: {e}")
            return super()._check_breakout_conditions(data)
    
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
            logger.debug(f"GPU-accelerated volatility strategy execution completed in {execution_time:.4f}s for {self.symbol}")
            
        except Exception as e:
            logger.error(f"GPU-accelerated volatility strategy execution failed: {e}")
            raise
    
    def get_performance_metrics(self) -> Dict:
        """
        Get performance metrics including GPU utilization
        """
        metrics = {
            'strategy_type': 'gpu_accelerated_volatility',
            'gpu_available': self.gpu_accelerator.gpu_available,
            'use_opencl': self.gpu_accelerator.use_opencl,
            'use_numba': self.gpu_accelerator.use_numba,
            'use_polars': self.gpu_accelerator.use_polars,
            'atr_period': self.atr_period,
            'lookback_period': self.lookback_period,
            'breakout_multiplier': self.breakout_multiplier,
            'symbol': self.symbol
        }
        
        return metrics
    
    def benchmark_performance(self, data_size: int = 1000) -> Dict:
        """
        Benchmark GPU vs CPU performance for volatility calculations
        """
        import time
        
        # Generate test data with realistic OHLCV structure
        test_data = pd.DataFrame({
            'timestamp': range(data_size),
            'open': np.random.randn(data_size) * 100 + 50000,
            'high': np.random.randn(data_size) * 100 + 50100,
            'low': np.random.randn(data_size) * 100 + 49900,
            'close': np.random.randn(data_size) * 100 + 50000,
            'volume': np.random.randn(data_size) * 1000 + 10000
        })
        
        # Ensure realistic price relationships
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
            
            # Check accuracy for ATR values
            if len(gpu_result) > 0 and len(cpu_result) > 0 and 'atr' in gpu_result.columns and 'atr' in cpu_result.columns:
                gpu_atr = gpu_result['atr'].dropna()
                cpu_atr = cpu_result['atr'].dropna()
                
                if len(gpu_atr) > 0 and len(cpu_atr) > 0:
                    min_len = min(len(gpu_atr), len(cpu_atr))
                    mse = np.mean((gpu_atr.iloc[:min_len] - cpu_atr.iloc[:min_len]) ** 2)
                    results['accuracy_mse'] = mse
                    results['accuracy_good'] = mse < 1e-6
            
        except Exception as e:
            logger.error(f"Volatility benchmark failed: {e}")
            results['error'] = str(e)
        
        return results
