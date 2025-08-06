"""
GPU-Accelerated Moving Average Crossover Strategy Module
=======================================================

Enhanced moving average crossover strategy with AMD GPU acceleration for faster calculations.
"""

import logging
import pandas as pd
import numpy as np
from typing import Dict

# Import the base strategy and GPU acceleration
from strategies.moving_average_cross import MovingAverageCrossStrategy as BaseMAStrategy
from utils.gpu_acceleration import gpu_accelerator

logger = logging.getLogger("GPUAcceleratedMA")

class GPUAcceleratedMAStrategy(BaseMAStrategy):
    """
    GPU-Accelerated Moving Average Crossover Strategy
    
    Inherits from the base MA crossover strategy but uses GPU acceleration
    for faster moving average calculations and trend analysis.
    """
    
    def __init__(self, *args, **kwargs):
        """Initialize the GPU-accelerated MA strategy"""
        super().__init__(*args, **kwargs)
        self.gpu_accelerator = gpu_accelerator
        logger.info(f"GPU-accelerated MA strategy initialized (GPU available: {self.gpu_accelerator.gpu_available})")
    
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
        Calculate moving average indicators using GPU acceleration
        """
        if data.empty or len(data) < max(self.fast_period, self.slow_period):
            return data
        
        try:
            # Use GPU-accelerated calculations
            if self.gpu_accelerator.gpu_available and len(data) > 50:
                data = self._calculate_indicators_gpu(data)
                logger.debug(f"GPU-accelerated MA calculation completed for {self.symbol}")
            else:
                # Fallback to optimized CPU calculation
                data = self._calculate_indicators_cpu_optimized(data)
                logger.debug(f"CPU-optimized MA calculation used for {self.symbol}")
            
            return data
            
        except Exception as e:
            logger.warning(f"GPU MA calculation failed, using fallback: {e}")
            return super()._calculate_indicators(data)
    
    def _calculate_indicators_gpu(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        GPU-accelerated moving average calculation
        """
        try:
            # Extract price array
            close_prices = data['close'].values
            
            # GPU-accelerated moving averages
            fast_ma = self.gpu_accelerator.accelerated_rolling_mean(close_prices, self.fast_period)
            slow_ma = self.gpu_accelerator.accelerated_rolling_mean(close_prices, self.slow_period)
            
            data['fast_ma'] = fast_ma
            data['slow_ma'] = slow_ma
            
            # Calculate additional GPU-accelerated indicators
            # Moving average convergence/divergence
            data['ma_diff'] = data['fast_ma'] - data['slow_ma']
            data['ma_diff_pct'] = (data['ma_diff'] / data['slow_ma']) * 100
            
            # GPU-accelerated trend strength indicator
            if len(close_prices) >= 20:
                # Calculate trend strength using standard deviation of MA difference
                ma_diff_values = data['ma_diff'].dropna().values
                if len(ma_diff_values) >= 10:
                    trend_strength = self.gpu_accelerator.accelerated_rolling_std(
                        ma_diff_values, min(10, len(ma_diff_values))
                    )
                    # Pad to match data length
                    trend_strength_padded = np.full(len(data), np.nan)
                    start_idx = len(data) - len(trend_strength)
                    trend_strength_padded[start_idx:] = trend_strength
                    data['trend_strength'] = trend_strength_padded
            
            # GPU-accelerated momentum calculation
            if len(close_prices) >= 14:  # 14-period momentum
                momentum = self.gpu_accelerator.accelerated_momentum(close_prices, 14)
                data['momentum'] = momentum
            
            return data
            
        except Exception as e:
            logger.warning(f"GPU MA indicator calculation failed: {e}")
            return self._calculate_indicators_cpu_optimized(data)
    
    def _calculate_indicators_cpu_optimized(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Optimized CPU-based moving average calculation using vectorized operations
        """
        try:
            # Use pandas rolling for efficiency (already optimized)
            data['fast_ma'] = data['close'].rolling(window=self.fast_period, min_periods=1).mean()
            data['slow_ma'] = data['close'].rolling(window=self.slow_period, min_periods=1).mean()
            
            # Vectorized calculations
            data['ma_diff'] = data['fast_ma'] - data['slow_ma']
            data['ma_diff_pct'] = (data['ma_diff'] / data['slow_ma']) * 100
            
            # Trend strength using rolling standard deviation
            data['trend_strength'] = data['ma_diff'].rolling(window=10, min_periods=5).std()
            
            # Momentum calculation (vectorized)
            data['momentum'] = data['close'] / data['close'].shift(14) - 1
            
            return data
            
        except Exception as e:
            logger.warning(f"CPU-optimized MA calculation failed: {e}")
            return super()._calculate_indicators(data)
    
    def _check_crossover_conditions(self, data: pd.DataFrame) -> tuple:
        """
        Enhanced crossover condition checking with GPU-accelerated pattern analysis
        """
        if data.empty or len(data) < 2:
            return False, False, {}
        
        try:
            current_row = data.iloc[-1]
            prev_row = data.iloc[-2]
            
            # Basic crossover conditions
            bullish_cross = (
                current_row['fast_ma'] > current_row['slow_ma'] and
                prev_row['fast_ma'] <= prev_row['slow_ma']
            )
            
            bearish_cross = (
                current_row['fast_ma'] < current_row['slow_ma'] and
                prev_row['fast_ma'] >= prev_row['slow_ma']
            )
            
            # Enhanced conditions with trend analysis
            conditions = {
                'ma_diff': current_row.get('ma_diff', 0),
                'ma_diff_pct': current_row.get('ma_diff_pct', 0),
                'trend_strength': current_row.get('trend_strength', 0),
                'momentum': current_row.get('momentum', 0),
                'price_above_fast_ma': current_row['close'] > current_row['fast_ma'],
                'price_above_slow_ma': current_row['close'] > current_row['slow_ma']
            }
            
            # Enhanced filtering based on trend strength and momentum
            min_trend_strength = 0.01  # Minimum trend strength threshold
            min_momentum = 0.001  # Minimum momentum threshold
            
            # Filter weak signals
            if abs(conditions['trend_strength']) < min_trend_strength:
                conditions['weak_trend_filter'] = True
                # Reduce signal strength for weak trends
                if abs(conditions['ma_diff_pct']) < 0.1:  # Less than 0.1% difference
                    bullish_cross = False
                    bearish_cross = False
            
            # Momentum confirmation
            if bullish_cross and conditions['momentum'] < -min_momentum:
                conditions['momentum_divergence'] = True
                # Could reduce position size or skip trade
            
            if bearish_cross and conditions['momentum'] > min_momentum:
                conditions['momentum_divergence'] = True
                # Could reduce position size or skip trade
            
            return bullish_cross, bearish_cross, conditions
            
        except Exception as e:
            logger.warning(f"Enhanced crossover condition check failed: {e}")
            return super()._check_crossover_conditions(data)
    
    def _calculate_signal_strength(self, data: pd.DataFrame) -> float:
        """
        Calculate signal strength using GPU-accelerated analysis
        """
        if data.empty:
            return 0.0
        
        try:
            current_row = data.iloc[-1]
            
            # Base signal strength from MA difference
            ma_diff_pct = abs(current_row.get('ma_diff_pct', 0))
            
            # Trend strength component
            trend_strength = abs(current_row.get('trend_strength', 0))
            
            # Momentum component
            momentum = abs(current_row.get('momentum', 0))
            
            # Combine components (normalized)
            signal_strength = min(1.0, (
                ma_diff_pct * 0.4 +  # 40% weight on MA difference
                trend_strength * 100 * 0.3 +  # 30% weight on trend strength
                momentum * 50 * 0.3  # 30% weight on momentum
            ))
            
            return signal_strength
            
        except Exception as e:
            logger.warning(f"Signal strength calculation failed: {e}")
            return 0.5  # Default moderate signal strength
    
    def execute(self):
        """
        Execute strategy with performance monitoring and enhanced signal analysis
        """
        import time
        start_time = time.time()
        
        try:
            # Get market data with GPU acceleration
            data = self._get_market_data()
            if data.empty:
                logger.warning(f"No market data available for {self.symbol}")
                return
            
            # Calculate indicators with GPU acceleration
            data = self._calculate_indicators(data)
            
            # Check for crossover signals with enhanced analysis
            bullish_cross, bearish_cross, conditions = self._check_crossover_conditions(data)
            
            # Calculate signal strength
            signal_strength = self._calculate_signal_strength(data)
            
            # Execute trades based on signals
            if bullish_cross and signal_strength > 0.3:
                logger.info(f"Bullish crossover detected for {self.symbol} (strength: {signal_strength:.2f})")
                self._execute_buy_order(signal_strength, conditions)
            
            elif bearish_cross and signal_strength > 0.3:
                logger.info(f"Bearish crossover detected for {self.symbol} (strength: {signal_strength:.2f})")
                self._execute_sell_order(signal_strength, conditions)
            
            execution_time = time.time() - start_time
            logger.debug(f"GPU-accelerated MA strategy execution completed in {execution_time:.4f}s for {self.symbol}")
            
        except Exception as e:
            logger.error(f"GPU-accelerated MA strategy execution failed: {e}")
            raise
    
    def _execute_buy_order(self, signal_strength: float, conditions: Dict):
        """Execute buy order with signal strength consideration"""
        try:
            # Adjust position size based on signal strength
            base_amount = getattr(self, 'trade_amount', 5.0)
            adjusted_amount = base_amount * min(signal_strength * 2, 1.0)  # Scale by signal strength
            
            # Use parent's trading logic but with adjusted amount
            # This would integrate with your existing trading execution
            logger.info(f"Executing buy order for {self.symbol}: amount={adjusted_amount}, conditions={conditions}")
            
        except Exception as e:
            logger.error(f"Buy order execution failed: {e}")
    
    def _execute_sell_order(self, signal_strength: float, conditions: Dict):
        """Execute sell order with signal strength consideration"""
        try:
            # Adjust position size based on signal strength
            base_amount = getattr(self, 'trade_amount', 5.0)
            adjusted_amount = base_amount * min(signal_strength * 2, 1.0)  # Scale by signal strength
            
            # Use parent's trading logic but with adjusted amount
            logger.info(f"Executing sell order for {self.symbol}: amount={adjusted_amount}, conditions={conditions}")
            
        except Exception as e:
            logger.error(f"Sell order execution failed: {e}")
    
    def get_performance_metrics(self) -> Dict:
        """
        Get performance metrics including GPU utilization
        """
        metrics = {
            'strategy_type': 'gpu_accelerated_ma_cross',
            'gpu_available': self.gpu_accelerator.gpu_available,
            'use_opencl': self.gpu_accelerator.use_opencl,
            'use_numba': self.gpu_accelerator.use_numba,
            'use_polars': self.gpu_accelerator.use_polars,
            'fast_period': self.fast_period,
            'slow_period': self.slow_period,
            'symbol': self.symbol
        }
        
        return metrics
    
    def benchmark_performance(self, data_size: int = 1000) -> Dict:
        """
        Benchmark GPU vs CPU performance for moving average calculations
        """
        import time
        
        # Generate test data
        test_data = pd.DataFrame({
            'timestamp': range(data_size),
            'close': np.random.randn(data_size) * 100 + 50000,
            'volume': np.random.randn(data_size) * 1000 + 10000
        })
        
        # Ensure positive prices
        test_data['close'] = np.abs(test_data['close'])
        
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
            
            # Check accuracy for moving averages
            if (len(gpu_result) > 0 and len(cpu_result) > 0 and 
                'fast_ma' in gpu_result.columns and 'fast_ma' in cpu_result.columns):
                
                gpu_ma = gpu_result['fast_ma'].dropna()
                cpu_ma = cpu_result['fast_ma'].dropna()
                
                if len(gpu_ma) > 0 and len(cpu_ma) > 0:
                    min_len = min(len(gpu_ma), len(cpu_ma))
                    mse = np.mean((gpu_ma.iloc[:min_len] - cpu_ma.iloc[:min_len]) ** 2)
                    results['accuracy_mse'] = mse
                    results['accuracy_good'] = mse < 1e-6
            
        except Exception as e:
            logger.error(f"MA benchmark failed: {e}")
            results['error'] = str(e)
        
        return results
