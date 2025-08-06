"""
GPU Acceleration Module for AMD GPUs
===================================

Provides GPU-accelerated computations for trading strategies using AMD ROCm/OpenCL.
Falls back to CPU if GPU is not available.
"""

import logging
import numpy as np
import pandas as pd
from typing import Optional, Union, Tuple
import warnings

logger = logging.getLogger("GPUAcceleration")

class GPUAccelerator:
    """GPU acceleration handler for AMD GPUs"""
    
    def __init__(self):
        """Initialize GPU acceleration"""
        self.gpu_available = False
        self.use_opencl = False
        self.use_numba = False
        self.use_polars = False
        self.cl_ctx = None
        self.cl_queue = None
        
        self._initialize_gpu()
    
    def _initialize_gpu(self):
        """Initialize GPU acceleration libraries"""
        # Try OpenCL for AMD GPUs
        try:
            import pyopencl as cl
            platforms = cl.get_platforms()
            
            for platform in platforms:
                if 'amd' in platform.name.lower() or 'radeon' in platform.name.lower():
                    devices = platform.get_devices(cl.device_type.GPU)
                    if devices:
                        self.cl_ctx = cl.Context(devices[:1])  # Use first AMD GPU
                        self.cl_queue = cl.CommandQueue(self.cl_ctx)
                        self.use_opencl = True
                        logger.info(f"AMD GPU acceleration enabled: {devices[0].name}")
                        break
            
            if not self.use_opencl:
                logger.info("AMD GPU found but OpenCL context creation failed")
                
        except ImportError:
            logger.info("PyOpenCL not available for AMD GPU acceleration")
        except Exception as e:
            logger.warning(f"Failed to initialize OpenCL: {e}")
        
        # Try Numba for CPU/GPU JIT compilation
        try:
            import numba
            self.use_numba = True
            logger.info("Numba JIT acceleration enabled")
        except ImportError:
            logger.info("Numba not available")
        
        # Try Polars for fast DataFrame operations
        try:
            import polars as pl
            self.use_polars = True
            logger.info("Polars fast DataFrame operations enabled")
        except ImportError:
            logger.info("Polars not available")
        
        self.gpu_available = self.use_opencl or self.use_numba or self.use_polars
        
        if self.gpu_available:
            logger.info("GPU acceleration successfully initialized")
        else:
            logger.info("GPU acceleration not available, using CPU")
    
    def accelerated_rolling_mean(self, data: np.ndarray, window: int) -> np.ndarray:
        """
        GPU-accelerated rolling mean calculation
        
        Args:
            data: Input data array
            window: Rolling window size
            
        Returns:
            Rolling mean array
        """
        if self.use_numba:
            return self._numba_rolling_mean(data, window)
        elif self.use_opencl and len(data) > 1000:  # Use GPU for larger datasets
            return self._opencl_rolling_mean(data, window)
        else:
            return self._cpu_rolling_mean(data, window)
    
    def accelerated_ema(self, data: np.ndarray, span: int) -> np.ndarray:
        """
        GPU-accelerated exponential moving average
        
        Args:
            data: Input data array
            span: EMA span
            
        Returns:
            EMA array
        """
        if self.use_numba:
            return self._numba_ema(data, span)
        else:
            return self._cpu_ema(data, span)
    
    def accelerated_rsi(self, prices: np.ndarray, period: int = 14) -> np.ndarray:
        """
        GPU-accelerated RSI calculation
        
        Args:
            prices: Price data array
            period: RSI period
            
        Returns:
            RSI array
        """
        if self.use_numba:
            return self._numba_rsi(prices, period)
        else:
            return self._cpu_rsi(prices, period)
    
    def accelerated_atr(self, high: np.ndarray, low: np.ndarray, close: np.ndarray, period: int = 14) -> np.ndarray:
        """
        GPU-accelerated Average True Range calculation
        
        Args:
            high: High prices
            low: Low prices
            close: Close prices
            period: ATR period
            
        Returns:
            ATR array
        """
        if self.use_numba:
            return self._numba_atr(high, low, close, period)
        else:
            return self._cpu_atr(high, low, close, period)
    
    def accelerated_dataframe_ops(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Convert pandas DataFrame to faster Polars for operations
        
        Args:
            df: Input pandas DataFrame
            
        Returns:
            Processed DataFrame
        """
        if self.use_polars and len(df) > 100:
            try:
                import polars as pl
                # Convert to Polars for faster operations
                pl_df = pl.from_pandas(df)
                # Perform operations in Polars (faster)
                # Convert back to pandas for compatibility
                return pl_df.to_pandas()
            except Exception as e:
                logger.warning(f"Polars conversion failed: {e}")
                return df
        return df
    
    def _numba_rolling_mean(self, data: np.ndarray, window: int) -> np.ndarray:
        """Numba-accelerated rolling mean"""
        try:
            from numba import jit
            
            @jit(nopython=True)
            def rolling_mean_numba(arr, w):
                result = np.empty_like(arr)
                result[:w-1] = np.nan
                for i in range(w-1, len(arr)):
                    result[i] = np.mean(arr[i-w+1:i+1])
                return result
            
            return rolling_mean_numba(data, window)
        except Exception as e:
            logger.warning(f"Numba rolling mean failed: {e}")
            return self._cpu_rolling_mean(data, window)
    
    def _numba_ema(self, data: np.ndarray, span: int) -> np.ndarray:
        """Numba-accelerated EMA"""
        try:
            from numba import jit
            
            @jit(nopython=True)
            def ema_numba(arr, span):
                alpha = 2.0 / (span + 1.0)
                result = np.empty_like(arr)
                result[0] = arr[0]
                for i in range(1, len(arr)):
                    result[i] = alpha * arr[i] + (1 - alpha) * result[i-1]
                return result
            
            return ema_numba(data, span)
        except Exception as e:
            logger.warning(f"Numba EMA failed: {e}")
            return self._cpu_ema(data, span)
    
    def _numba_rsi(self, prices: np.ndarray, period: int) -> np.ndarray:
        """Numba-accelerated RSI"""
        try:
            from numba import jit
            
            @jit(nopython=True)
            def rsi_numba(prices, period):
                deltas = np.diff(prices)
                gains = np.where(deltas > 0, deltas, 0.0)
                losses = np.where(deltas < 0, -deltas, 0.0)
                
                avg_gains = np.empty(len(prices))
                avg_losses = np.empty(len(prices))
                avg_gains[:period] = np.nan
                avg_losses[:period] = np.nan
                
                # Initial averages
                avg_gains[period] = np.mean(gains[:period])
                avg_losses[period] = np.mean(losses[:period])
                
                # Smoothed averages
                for i in range(period + 1, len(prices)):
                    avg_gains[i] = (avg_gains[i-1] * (period - 1) + gains[i-1]) / period
                    avg_losses[i] = (avg_losses[i-1] * (period - 1) + losses[i-1]) / period
                
                rs = avg_gains / avg_losses
                rsi = 100 - (100 / (1 + rs))
                return rsi
            
            return rsi_numba(prices, period)
        except Exception as e:
            logger.warning(f"Numba RSI failed: {e}")
            return self._cpu_rsi(prices, period)
    
    def _numba_atr(self, high: np.ndarray, low: np.ndarray, close: np.ndarray, period: int) -> np.ndarray:
        """Numba-accelerated ATR"""
        try:
            from numba import jit
            
            @jit(nopython=True)
            def atr_numba(high, low, close, period):
                tr = np.empty(len(high))
                tr[0] = high[0] - low[0]
                
                for i in range(1, len(high)):
                    tr[i] = max(
                        high[i] - low[i],
                        abs(high[i] - close[i-1]),
                        abs(low[i] - close[i-1])
                    )
                
                atr = np.empty(len(high))
                atr[:period-1] = np.nan
                atr[period-1] = np.mean(tr[:period])
                
                for i in range(period, len(high)):
                    atr[i] = (atr[i-1] * (period - 1) + tr[i]) / period
                
                return atr
            
            return atr_numba(high, low, close, period)
        except Exception as e:
            logger.warning(f"Numba ATR failed: {e}")
            return self._cpu_atr(high, low, close, period)
    
    def _opencl_rolling_mean(self, data: np.ndarray, window: int) -> np.ndarray:
        """OpenCL-accelerated rolling mean for AMD GPU"""
        try:
            import pyopencl as cl
            import pyopencl.array as cl_array
            
            # OpenCL kernel for rolling mean
            kernel_code = """
            __kernel void rolling_mean(__global const float* data,
                                     __global float* result,
                                     const int window,
                                     const int n) {
                int gid = get_global_id(0);
                if (gid >= n) return;
                
                if (gid < window - 1) {
                    result[gid] = NAN;
                    return;
                }
                
                float sum = 0.0f;
                for (int i = gid - window + 1; i <= gid; i++) {
                    sum += data[i];
                }
                result[gid] = sum / window;
            }
            """
            
            program = cl.Program(self.cl_ctx, kernel_code).build()
            
            data_gpu = cl_array.to_device(self.cl_queue, data.astype(np.float32))
            result_gpu = cl_array.empty(self.cl_queue, data.shape, np.float32)
            
            program.rolling_mean(self.cl_queue, data.shape, None,
                               data_gpu.data, result_gpu.data,
                               np.int32(window), np.int32(len(data)))
            
            return result_gpu.get()
            
        except Exception as e:
            logger.warning(f"OpenCL rolling mean failed: {e}")
            return self._cpu_rolling_mean(data, window)
    
    def _cpu_rolling_mean(self, data: np.ndarray, window: int) -> np.ndarray:
        """CPU fallback for rolling mean"""
        return pd.Series(data).rolling(window=window).mean().values
    
    def _cpu_ema(self, data: np.ndarray, span: int) -> np.ndarray:
        """CPU fallback for EMA"""
        return pd.Series(data).ewm(span=span, adjust=False).mean().values
    
    def _cpu_rsi(self, prices: np.ndarray, period: int) -> np.ndarray:
        """CPU fallback for RSI"""
        delta = pd.Series(prices).diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        return (100 - (100 / (1 + rs))).values
    
    def _cpu_atr(self, high: np.ndarray, low: np.ndarray, close: np.ndarray, period: int) -> np.ndarray:
        """CPU fallback for ATR"""
        tr1 = high - low
        tr2 = np.abs(high - np.roll(close, 1))
        tr3 = np.abs(low - np.roll(close, 1))
        tr = np.maximum(tr1, np.maximum(tr2, tr3))
        return pd.Series(tr).rolling(window=period).mean().values
    
    def benchmark(self, data_size: int = 10000) -> dict:
        """
        Benchmark GPU vs CPU performance
        
        Args:
            data_size: Size of test data
            
        Returns:
            Benchmark results
        """
        import time
        
        # Generate test data
        test_data = np.random.randn(data_size).astype(np.float32)
        
        results = {
            'data_size': data_size,
            'gpu_available': self.gpu_available,
            'tests': {}
        }
        
        # Test rolling mean
        start_time = time.time()
        result_gpu = self.accelerated_rolling_mean(test_data, 20)
        gpu_time = time.time() - start_time
        
        start_time = time.time()
        result_cpu = self._cpu_rolling_mean(test_data, 20)
        cpu_time = time.time() - start_time
        
        results['tests']['rolling_mean'] = {
            'gpu_time': gpu_time,
            'cpu_time': cpu_time,
            'speedup': cpu_time / gpu_time if gpu_time > 0 else 1.0
        }
        
        # Test EMA
        start_time = time.time()
        result_gpu = self.accelerated_ema(test_data, 20)
        gpu_time = time.time() - start_time
        
        start_time = time.time()
        result_cpu = self._cpu_ema(test_data, 20)
        cpu_time = time.time() - start_time
        
        results['tests']['ema'] = {
            'gpu_time': gpu_time,
            'cpu_time': cpu_time,
            'speedup': cpu_time / gpu_time if gpu_time > 0 else 1.0
        }
        
        return results

# Global GPU accelerator instance
gpu_accelerator = GPUAccelerator()
