"""
GPU Acceleration Module for AMD GPUs
===================================

Provides GPU-accelerated computations for trading strategies using AMD ROCm/OpenCL.
Falls back to CPU if GPU is not available.
Enhanced for better AMD hardware support with multiple acceleration backends.
"""

import logging
import numpy as np
import pandas as pd
from typing import Dict, Any, List, Optional, Callable, Union
import os
import sys
import platform
import json
import requests
import time
import subprocess
import threading
from datetime import datetime
import websocket

logger = logging.getLogger("GPUAcceleration")

class GPUAccelerator:

    def fetch_eth_gas_price(self, cache_ttl: int = 30) -> dict:
        """
        Fetch current Ethereum gas prices from Etherscan API with caching.
        Args:
            cache_ttl: Cache time-to-live in seconds (default: 30)
        Returns:
            Dictionary with gas price info or error
        """
        import time
        import requests
        now = time.time()
        # Use cached data if recent
        if self.last_gas_update and (now - self.last_gas_update < cache_ttl) and self.last_gas_data:
            return {"source": "cache", **self.last_gas_data}
        url = f"https://api.etherscan.io/api?module=gastracker&action=gasoracle&apikey={self.api_key}"
        try:
            resp = requests.get(url, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                if data.get("status") == "1" and "result" in data:
                    gas = data["result"]
                    # Save to history and cache
                    self.last_gas_update = now
                    self.last_gas_data = gas
                    self.gas_history_data.append({"timestamp": now, **gas})
                    return {"source": "etherscan", **gas}
                else:
                    return {"error": "Etherscan API error", "data": data}
            else:
                return {"error": f"HTTP {resp.status_code}", "text": resp.text}
        except Exception as e:
            return {"error": str(e)}
    """GPU acceleration handler for AMD GPUs with multiple backends"""
    
    def __init__(self):
        """Initialize GPU acceleration"""
        self.gpu_available = False
        self.use_opencl = False
        self.use_rocm = False  # ROCm for AMD GPUs
        self.use_numba = False
        self.use_polars = False
        self.cl_ctx = None
        self.cl_queue = None
        self.rocm_device = None
        self.gpu_info = {}
        
        # API Keys for external services
        self.api_key = "KQ52UKBQHJDXUADF1IB1CEXCZ1ZEIWB7IA"  # Etherscan API key
        
        # Initialize gas tracking data structures
        self.last_gas_update = None
        self.last_gas_data = None
        self.gas_history_data = []
        
        # Set environment variables to help with AMD detection
        os.environ["HSA_ENABLE_SDMA"] = "0"  # Helps with some AMD ROCm issues
        os.environ["HIP_VISIBLE_DEVICES"] = "0"  # Use first GPU
        
        self._initialize_gpu()
    
    def _initialize_gpu(self):
        """Initialize GPU acceleration libraries with enhanced AMD support"""
        # Log system information for debugging
        logger.info(f"System: {platform.system()} {platform.release()}")
        logger.info(f"Python: {sys.version}")
        
        # First try ROCm/HIP for AMD GPUs (preferred for newer AMD hardware)
        self._try_initialize_rocm()
        
        # If ROCm fails, try OpenCL as fallback
        if not self.use_rocm:
            self._try_initialize_opencl()
            
        # Try Numba for CPU/GPU JIT compilation
        try:
            import numba
            # Check if numba can access CUDA
            has_cuda = hasattr(numba, 'cuda') and numba.cuda.is_available()
            if has_cuda:
                logger.info("Numba CUDA acceleration enabled")
            else:
                logger.info("Numba CPU acceleration enabled")
            self.use_numba = True
        except ImportError:
            logger.info("Numba not available")
        
        # Try Polars for fast DataFrame operations
        try:
            import polars
            self.use_polars = True
            logger.info("Polars fast DataFrame operations enabled")
        except ImportError:
            logger.info("Polars not available")
        
        self.gpu_available = self.use_opencl or self.use_rocm or self.use_numba or self.use_polars
        
        if self.gpu_available:
            logger.info("GPU acceleration successfully initialized")
        else:
            logger.warning("GPU acceleration not available, using CPU fallback")
    
    def _try_initialize_rocm(self):
        """Try to initialize ROCm/HIP for AMD GPUs"""
        try:
            # First try rocm-smi to check for AMD GPUs
            import subprocess
            try:
                result = subprocess.run(['rocm-smi'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                if "GPU ID" in result.stdout:
                    logger.info("ROCm detected via rocm-smi")
                    self.gpu_info['rocm_smi'] = True
            except Exception as e:
                logger.debug(f"rocm-smi check failed: {e}")
            
            # DexScreener API endpoints
            self.dex_screener_api = {
                "token_profiles": "https://api.dexscreener.com/token-profiles/latest/v1",
                "token_boosts": "https://api.dexscreener.com/token-boosts/latest/v1",
                "token_boosts_top": "https://api.dexscreener.com/token-boosts/top/v1",
                "orders": "https://api.dexscreener.com/orders/v1",
                "dex_pairs": "https://api.dexscreener.com/latest/dex/pairs",
                "dex_search": "https://api.dexscreener.com/latest/dex/search",
                "token_pairs": "https://api.dexscreener.com/token-pairs/v1",
                "tokens": "https://api.dexscreener.com/tokens/v1"
            }
            
            # Try importing PyTorch with ROCm
            try:
                import torch
                if torch.backends.mps.is_available():
                    logger.info("PyTorch Metal backend available (Apple GPU)")
                    self.use_rocm = True
                    self.rocm_device = "mps"
                    return
                
                if hasattr(torch, 'version') and hasattr(torch.version, 'hip') and torch.version.hip is not None:
                    if torch.cuda.is_available():  # CUDA API works with ROCm in PyTorch
                        device_count = torch.cuda.device_count()
                        if device_count > 0:
                            device_name = torch.cuda.get_device_name(0)
                            logger.info(f"PyTorch with ROCm enabled: {device_name}")
                            self.use_rocm = True
                            self.rocm_device = "pytorch"
                            return
            except ImportError:
                logger.debug("PyTorch not available")
            except Exception as e:
                logger.debug(f"PyTorch ROCm check failed: {e}")
            
            # Try importing TensorFlow with ROCm support
            try:
                import tensorflow as tf
                gpu_devices = tf.config.list_physical_devices('GPU')
                if len(gpu_devices) > 0:
                    logger.info(f"TensorFlow with GPU support: {gpu_devices}")
                    self.use_rocm = True
                    self.rocm_device = "tensorflow"
                    return
            except ImportError:
                logger.debug("TensorFlow not available")
            except Exception as e:
                logger.debug(f"TensorFlow GPU check failed: {e}")
                
            # Try importing CuPy (works with ROCm on some setups)
            try:
                import cupy as cp
                if cp.cuda.runtime.getDeviceCount() > 0:
                    device_name = cp.cuda.runtime.getDeviceProperties(0)['name'].decode('utf-8')
                    logger.info(f"CuPy with GPU support: {device_name}")
                    self.use_rocm = True
                    self.rocm_device = "cupy"
                    return
            except ImportError:
                logger.debug("CuPy not available")
            except Exception as e:
                logger.debug(f"CuPy GPU check failed: {e}")
                
        except Exception as e:
            logger.warning(f"Failed to initialize ROCm/HIP: {e}")
    
    def _try_initialize_opencl(self):
        """Try to initialize OpenCL with better AMD detection"""
        try:
            import pyopencl as cl
            
            # Get all platforms
            platforms = cl.get_platforms()
            if not platforms:
                logger.warning("No OpenCL platforms found")
                return
                
            logger.debug(f"Found {len(platforms)} OpenCL platforms")
            for i, platform in enumerate(platforms):
                logger.debug(f"Platform {i}: {platform.name} - {platform.vendor}")
                
                # Try to detect AMD platform through various vendor strings
                is_amd = False
                vendor_lower = platform.vendor.lower()
                name_lower = platform.name.lower()
                
                # Check for various AMD identifiers
                amd_identifiers = ['amd', 'advanced micro', 'radeon', 'rx', 'ati']
                for identifier in amd_identifiers:
                    if identifier in vendor_lower or identifier in name_lower:
                        is_amd = True
                        break
                
                # Try to get devices for this platform
                try:
                    # First try to get GPU devices
                    devices = platform.get_devices(device_type=cl.device_type.GPU)
                    if not devices:
                        # If no GPU devices, try ALL devices
                        devices = platform.get_devices(device_type=cl.device_type.ALL)
                    
                    if devices:
                        for j, device in enumerate(devices):
                            logger.debug(f"  Device {j}: {device.name} - Type: {cl.device_type.to_string(device.type)}")
                            
                            # If we found an AMD platform or device, use it
                            device_name_lower = device.name.lower()
                            if is_amd or any(id in device_name_lower for id in amd_identifiers):
                                try:
                                    # Try to create context and queue with this device
                                    self.cl_ctx = cl.Context([device])
                                    self.cl_queue = cl.CommandQueue(self.cl_ctx)
                                    self.use_opencl = True
                                    logger.info(f"AMD GPU acceleration enabled via OpenCL: {device.name}")
                                    return
                                except Exception as device_err:
                                    logger.debug(f"Failed to create context for device {device.name}: {device_err}")
                
                except Exception as dev_err:
                    logger.debug(f"Could not get devices for platform {platform.name}: {dev_err}")
            
            # If we haven't found an AMD device, try with any available GPU
            for platform in platforms:
                try:
                    devices = platform.get_devices(device_type=cl.device_type.GPU)
                    if devices:
                        try:
                            self.cl_ctx = cl.Context([devices[0]])
                            self.cl_queue = cl.CommandQueue(self.cl_ctx)
                            self.use_opencl = True
                            logger.info(f"Non-AMD GPU acceleration enabled via OpenCL: {devices[0].name}")
                            return
                        except Exception as e:
                            logger.debug(f"Failed to create context for non-AMD device: {e}")
                except Exception:
                    pass
            
            # Last resort: try with CPU device
            for platform in platforms:
                try:
                    devices = platform.get_devices(device_type=cl.device_type.CPU)
                    if devices:
                        try:
                            self.cl_ctx = cl.Context([devices[0]])
                            self.cl_queue = cl.CommandQueue(self.cl_ctx)
                            self.use_opencl = True
                            logger.info(f"CPU OpenCL acceleration enabled: {devices[0].name}")
                            return
                        except Exception as e:
                            logger.debug(f"Failed to create CPU OpenCL context: {e}")
                except Exception:
                    pass
                    
            logger.warning("No suitable OpenCL devices found")
                
        except ImportError:
            logger.info("PyOpenCL not available for GPU acceleration")
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
        elif self.use_rocm and len(data) > 1000:  # Use ROCm for larger datasets
            return self._rocm_rolling_mean(data, window)
        else:
            return self._cpu_rolling_mean(data, window)
    
    def accelerated_rolling_std(self, data: np.ndarray, window: int) -> np.ndarray:
        """
        GPU-accelerated rolling standard deviation
        
        Args:
            data: Input data array
            window: Rolling window size
            
        Returns:
            Rolling standard deviation array
        """
        if self.use_numba:
            return self._numba_rolling_std(data, window)
        elif self.use_opencl and len(data) > 1000:
            return self._opencl_rolling_std(data, window)
        elif self.use_rocm and len(data) > 1000:
            return self._rocm_rolling_std(data, window)
        else:
            return self._cpu_rolling_std(data, window)
    
    def accelerated_momentum(self, data: np.ndarray, period: int) -> np.ndarray:
        """
        GPU-accelerated momentum calculation
        
        Args:
            data: Input price data array
            period: Momentum period
            
        Returns:
            Momentum array
        """
        if self.use_numba:
            return self._numba_momentum(data, period)
        elif self.use_opencl and len(data) > 1000:
            return self._opencl_momentum(data, period)
        elif self.use_rocm and len(data) > 1000:
            return self._rocm_momentum(data, period)
        else:
            return self._cpu_momentum(data, period)
    
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
        elif self.use_rocm and len(data) > 1000:
            return self._rocm_ema(data, span)
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
    
    def _numba_rolling_std(self, data: np.ndarray, window: int) -> np.ndarray:
        """Numba-accelerated rolling standard deviation"""
        try:
            from numba import jit
            
            @jit(nopython=True)
            def rolling_std_numba(arr, w):
                result = np.empty_like(arr)
                result[:w-1] = np.nan
                for i in range(w-1, len(arr)):
                    segment = arr[i-w+1:i+1]
                    mean = 0.0
                    for j in range(len(segment)):
                        mean += segment[j]
                    mean /= w
                    
                    var = 0.0
                    for j in range(len(segment)):
                        var += (segment[j] - mean) ** 2
                    var /= w
                    
                    result[i] = np.sqrt(var)
                return result
            
            return rolling_std_numba(data, window)
        except Exception as e:
            logger.warning(f"Numba rolling std failed: {e}")
            return self._cpu_rolling_std(data, window)
    
    def _cpu_rolling_std(self, data: np.ndarray, window: int) -> np.ndarray:
        """CPU fallback for rolling standard deviation"""
        return pd.Series(data).rolling(window=window).std().values
    
    def _numba_momentum(self, data: np.ndarray, period: int) -> np.ndarray:
        """Numba-accelerated momentum calculation"""
        try:
            from numba import jit
            
            @jit(nopython=True)
            def momentum_numba(arr, period):
                result = np.empty_like(arr)
                result[:period] = np.nan
                for i in range(period, len(arr)):
                    result[i] = arr[i] / arr[i - period] - 1.0
                return result
            
            return momentum_numba(data, period)
        except Exception as e:
            logger.warning(f"Numba momentum failed: {e}")
            return self._cpu_momentum(data, period)
    
    def _cpu_momentum(self, data: np.ndarray, period: int) -> np.ndarray:
        """CPU fallback for momentum calculation"""
        result = np.empty_like(data)
        result[:period] = np.nan
        result[period:] = data[period:] / data[:-period] - 1.0
        return result
    
    def _opencl_rolling_std(self, data: np.ndarray, window: int) -> np.ndarray:
        """OpenCL-accelerated rolling standard deviation"""
        try:
            import pyopencl as cl
            import pyopencl.array as cl_array
            
            # OpenCL kernel for rolling std
            kernel_code = """
            __kernel void rolling_std(__global const float* data,
                                    __global float* result,
                                    const int window,
                                    const int n) {
                int gid = get_global_id(0);
                if (gid >= n) return;
                
                if (gid < window - 1) {
                    result[gid] = NAN;
                    return;
                }
                
                // Calculate mean
                float sum = 0.0f;
                for (int i = gid - window + 1; i <= gid; i++) {
                    sum += data[i];
                }
                float mean = sum / window;
                
                // Calculate variance
                float var_sum = 0.0f;
                for (int i = gid - window + 1; i <= gid; i++) {
                    float diff = data[i] - mean;
                    var_sum += diff * diff;
                }
                float variance = var_sum / window;
                
                // Standard deviation
                result[gid] = sqrt(variance);
            }
            """
            
            program = cl.Program(self.cl_ctx, kernel_code).build()
            
            data_gpu = cl_array.to_device(self.cl_queue, data.astype(np.float32))
            result_gpu = cl_array.empty(self.cl_queue, data.shape, np.float32)
            
            program.rolling_std(self.cl_queue, data.shape, None,
                               data_gpu.data, result_gpu.data,
                               np.int32(window), np.int32(len(data)))
            
            return result_gpu.get()
            
        except Exception as e:
            logger.warning(f"OpenCL rolling std failed: {e}")
            return self._cpu_rolling_std(data, window)
    
    def _opencl_momentum(self, data: np.ndarray, period: int) -> np.ndarray:
        """OpenCL-accelerated momentum calculation"""
        try:
            import pyopencl as cl
            import pyopencl.array as cl_array
            
            # OpenCL kernel for momentum
            kernel_code = """
            __kernel void momentum(__global const float* data,
                                  __global float* result,
                                  const int period,
                                  const int n) {
                int gid = get_global_id(0);
                if (gid >= n) return;
                
                if (gid < period) {
                    result[gid] = NAN;
                    return;
                }
                
                result[gid] = data[gid] / data[gid - period] - 1.0f;
            }
            """
            
            program = cl.Program(self.cl_ctx, kernel_code).build()
            
            data_gpu = cl_array.to_device(self.cl_queue, data.astype(np.float32))
            result_gpu = cl_array.empty(self.cl_queue, data.shape, np.float32)
            
            program.momentum(self.cl_queue, data.shape, None,
                           data_gpu.data, result_gpu.data,
                           np.int32(period), np.int32(len(data)))
            
            return result_gpu.get()
            
        except Exception as e:
            logger.warning(f"OpenCL momentum failed: {e}")
            return self._cpu_momentum(data, period)
    
    def _rocm_rolling_mean(self, data: np.ndarray, window: int) -> np.ndarray:
        """ROCm-accelerated rolling mean (via PyTorch or TensorFlow)"""
        # Try PyTorch implementation first
        if self.rocm_device == "pytorch" or self.rocm_device == "mps":
            try:
                try:
                    import torch
                except ImportError:
                    logger.debug("PyTorch not available for rolling mean calculation")
                    return self._cpu_rolling_mean(data, window)
                
                # Convert to tensor
                if self.rocm_device == "mps":
                    device = torch.device("mps")
                else:
                    device = torch.device("cuda:0")  # ROCm uses CUDA API in PyTorch
                
                x = torch.tensor(data, dtype=torch.float32, device=device)
                
                # Create rolling window tensor
                result = torch.zeros_like(x)
                result[:window-1] = float('nan')
                
                # Do rolling calculation on GPU
                for i in range(window-1, len(data)):
                    result[i] = torch.mean(x[i-window+1:i+1])
                
                return result.cpu().numpy()
            except Exception as e:
                logger.warning(f"PyTorch rolling mean failed: {e}")
        
        # Try TensorFlow implementation
        elif self.rocm_device == "tensorflow":
            try:
                import tensorflow as tf
                
                # Convert to tensor and calculate rolling mean
                x = tf.convert_to_tensor(data, dtype=tf.float32)
                result = tf.zeros_like(x)
                
                # Create a tensor with NaNs for the first window-1 elements
                nan_tensor = tf.fill([window-1], np.nan)
                
                # Initialize a TensorArray to build the result
                ta = tf.TensorArray(tf.float32, size=len(data))
                ta = ta.write_many(0, nan_tensor)
                
                # Run the rolling mean operation
                for i in range(window-1, len(data)):
                    window_mean = tf.reduce_mean(x[i-window+1:i+1])
                    ta = ta.write(i, window_mean)
                
                # Stack the results
                result = ta.stack()
                
                return result.numpy()
            except Exception as e:
                logger.warning(f"TensorFlow rolling mean failed: {e}")
        
        # Fallback to CPU
        return self._cpu_rolling_mean(data, window)
    
    def _rocm_rolling_std(self, data: np.ndarray, window: int) -> np.ndarray:
        """ROCm-accelerated rolling standard deviation"""
        # Try PyTorch implementation first
        if self.rocm_device == "pytorch" or self.rocm_device == "mps":
            try:
                import torch
                
                # Convert to tensor
                if self.rocm_device == "mps":
                    device = torch.device("mps")
                else:
                    device = torch.device("cuda:0")  # ROCm uses CUDA API in PyTorch
                
                x = torch.tensor(data, dtype=torch.float32, device=device)
                
                # Create rolling window tensor
                result = torch.zeros_like(x)
                result[:window-1] = float('nan')
                
                # Do rolling calculation on GPU
                for i in range(window-1, len(data)):
                    result[i] = torch.std(x[i-window+1:i+1], unbiased=False)
                
                return result.cpu().numpy()
            except Exception as e:
                logger.warning(f"PyTorch rolling std failed: {e}")
        
        # Fallback to CPU implementation
        return self._cpu_rolling_std(data, window)
    
    def _rocm_momentum(self, data: np.ndarray, period: int) -> np.ndarray:
        """ROCm-accelerated momentum calculation"""
        # Try PyTorch implementation first
        if self.rocm_device == "pytorch" or self.rocm_device == "mps":
            try:
                import torch
                
                # Convert to tensor
                if self.rocm_device == "mps":
                    device = torch.device("mps")
                else:
                    device = torch.device("cuda:0")  # ROCm uses CUDA API in PyTorch
                
                x = torch.tensor(data, dtype=torch.float32, device=device)
                
                # Create result tensor
                result = torch.zeros_like(x)
                result[:period] = float('nan')
                
                # Calculate momentum
                result[period:] = x[period:] / x[:-period] - 1.0
                
                return result.cpu().numpy()
            except Exception as e:
                logger.warning(f"PyTorch momentum failed: {e}")
        
        # Fallback to CPU implementation
        return self._cpu_momentum(data, period)
    
    def _rocm_ema(self, data: np.ndarray, span: int) -> np.ndarray:
        """ROCm-accelerated EMA calculation"""
        # Moralis WebSocket URL for real-time blockchain events
        self.moralis_ws_url = "wss://ws.moralis.io/mainnet?apiKey=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJub25jZSI6IjEzMGM1NGU3LTI0ZGQtNGRmZC04ZDViLTU4NTBlNTE2NTBhMiIsIm9yZ0lkIjoiNDYzNjgyIiwidXNlcklkIjoiNDc3MDMzIiwidHlwZUlkIjoiNjkwZWI2ZDAtMDFlZS00ZmMzLTg0OWItM2Y4ZTNhZGE2Nzc1IiwidHlwZSI6IlBST0pFQ1QiLCJpYXQiOjE3NTQ1Mzc1MjUsImV4cCI6NDkxMDI5NzUyNX0.QJJu4v6JZC77miG3JXEUKxAw3d_OfNTcE_P9B7YTG-I"
        
        # Try PyTorch implementation first
        if self.rocm_device == "pytorch" or self.rocm_device == "mps":
            try:
                import torch
                
                # Convert to tensor
                if self.rocm_device == "mps":
                    device = torch.device("mps")
                else:
                    device = torch.device("cuda:0")  # ROCm uses CUDA API in PyTorch
                
                x = torch.tensor(data, dtype=torch.float32, device=device)
                
                # Create result tensor and calculate EMA
                result = torch.zeros_like(x)
                alpha = 2.0 / (span + 1.0)
                
                result[0] = x[0]
                for i in range(1, len(data)):
                    result[i] = alpha * x[i] + (1 - alpha) * result[i-1]
                
                return result.cpu().numpy()
            except Exception as e:
                logger.warning(f"PyTorch EMA failed: {e}")
        
        # Fallback to CPU implementation
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
        Benchmark GPU vs CPU performance for various calculations
        
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
            'gpu_type': 'ROCm' if self.use_rocm else 'OpenCL' if self.use_opencl else 'None',
            'acceleration_methods': {
                'opencl': self.use_opencl,
                'rocm': self.use_rocm,
                'numba': self.use_numba,
                'polars': self.use_polars
            },
            'device_info': self.gpu_info,
            'tests': {}
        }
        
        # Test each calculation method
        test_functions = [
            ('rolling_mean', self.accelerated_rolling_mean, self._cpu_rolling_mean, [test_data, 20]),
            ('rolling_std', self.accelerated_rolling_std, self._cpu_rolling_std, [test_data, 20]),
            ('ema', self.accelerated_ema, self._cpu_ema, [test_data, 20]),
            ('momentum', self.accelerated_momentum, self._cpu_momentum, [test_data, 14]),
        ]
        
        for test_name, accel_func, cpu_func, args in test_functions:
            try:
                # Test accelerated version
                start_time = time.time()
                accel_func(*args)  # Use result but don't assign to avoid linter warnings
                gpu_time = time.time() - start_time
                
                # Test CPU version
                start_time = time.time()
                cpu_func(*args)  # Use result but don't assign to avoid linter warnings
                cpu_time = time.time() - start_time
                
                # Calculate speedup
                speedup = cpu_time / gpu_time if gpu_time > 0 else 1.0
                
                # Add results to the dictionary
                results['tests'][test_name] = {
                    'gpu_time': gpu_time,
                    'cpu_time': cpu_time,
                    'speedup': speedup,
                    'success': True
                }
            except Exception as e:
                results['tests'][test_name] = {
                    'error': str(e),
                    'success': False
                }
        
        return results
        
    def analyze_dex_trading_pair(self, chain_id: str, pair_id: str, time_period: str = "1d") -> dict:
        """
        Perform advanced analysis on a DEX trading pair using GPU acceleration
        
        Args:
            chain_id: The blockchain ID (ethereum, bsc, etc.)
            pair_id: The DEX pair identifier
            time_period: Time period for analysis (1h, 4h, 1d, 1w)
            
        Returns:
            Advanced analysis including liquidity, volatility, and trading signals
        """
        try:
            # First fetch the pair data
            pair_data = self.fetch_dex_pair(pair_id, chain_id)
            
            if "error" in pair_data:
                return pair_data
                
            # Extract price and volume data
            if "pair" not in pair_data or not pair_data["pair"]:
                return {"error": "No pair data available"}
                
            # Initialize result dictionary
            analysis = {
                "pairInfo": {
                    "address": pair_data["pair"].get("pairAddress", ""),
                    "baseToken": pair_data["pair"].get("baseToken", {}).get("symbol", ""),
                    "quoteToken": pair_data["pair"].get("quoteToken", {}).get("symbol", ""),
                    "dexId": pair_data["pair"].get("dexId", ""),
                    "chainId": chain_id
                },
                "priceData": {
                    "current": pair_data["pair"].get("priceUsd", 0),
                    "change24h": pair_data["pair"].get("priceChange", {}).get("h24", 0)
                },
                "liquidity": {
                    "usd": pair_data["pair"].get("liquidity", {}).get("usd", 0),
                },
                "volume": {
                    "h24": pair_data["pair"].get("volume", {}).get("h24", 0),
                },
                "indicators": {},
                "signals": {},
                "riskAssessment": {}
            }
            
            # Check if we have price history for technical analysis
            if not self.gpu_available or "priceUsd" not in pair_data["pair"]:
                analysis["indicators"] = {
                    "status": "GPU acceleration unavailable or insufficient price data"
                }
                return analysis
                
            # In a real implementation, we would extract historical price data
            # Here we'll simulate the calculation using GPU acceleration
            # This would typically come from additional API calls or websocket data
            
            # This is a placeholder - in a real implementation, you would fetch historical data
            # For demo purposes, we'll generate random price data similar to current price
            base_price = float(pair_data["pair"].get("priceUsd", 1.0))
            
            # Generate synthetic price data with realistic patterns
            n_points = 500
            if time_period == "1h":
                n_points = 60  # 1-minute intervals
            elif time_period == "4h":
                n_points = 240  # 1-minute intervals
            elif time_period == "1d":
                n_points = 1440  # 1-minute intervals
            elif time_period == "1w":
                n_points = 168  # 1-hour intervals
                
            # Use numpy for efficient data generation
            np.random.seed(int(base_price * 1000) % 1000)  # Seed based on price for reproducibility
            
            # Generate synthetic price data with trend and volatility based on 24h change
            trend = pair_data["pair"].get("priceChange", {}).get("h24", 0) / 100  # Convert percentage to decimal
            volatility = abs(trend) * 2 + 0.005  # Higher trend typically means higher volatility
            
            # Generate time series with random walk but following the trend
            random_changes = np.random.normal(trend/n_points, volatility/np.sqrt(n_points), n_points)
            cumulative_changes = np.cumprod(1 + random_changes)
            price_history = base_price / cumulative_changes[-1] * cumulative_changes
            
            # Calculate technical indicators using GPU acceleration
            analysis["indicators"] = {
                "rsi": {
                    "current": float(self.accelerated_rsi(price_history, 14)[-1]),
                    "period": 14
                },
                "ema": {
                    "ema20": float(self.accelerated_ema(price_history, 20)[-1]),
                    "ema50": float(self.accelerated_ema(price_history, 50)[-1]),
                },
                "volatility": float(self.accelerated_rolling_std(price_history, 20)[-1] / price_history[-1]),
                "momentum": float(self.accelerated_momentum(price_history, 14)[-1])
            }
            
            # Calculate trading signals
            rsi = analysis["indicators"]["rsi"]["current"]
            ema20 = analysis["indicators"]["ema"]["ema20"]
            ema50 = analysis["indicators"]["ema"]["ema50"]
            
            # Determine trading signals
            analysis["signals"] = {
                "rsiSignal": "oversold" if rsi < 30 else "overbought" if rsi > 70 else "neutral",
                "trendSignal": "bullish" if ema20 > ema50 else "bearish" if ema20 < ema50 else "neutral",
                "overallSignal": "neutral"  # Default
            }
            
            # Determine overall signal (simple logic for demonstration)
            rsi_bullish = rsi < 40 and rsi > 20
            rsi_bearish = rsi > 60 and rsi < 80
            trend_bullish = ema20 > ema50
            
            if rsi_bullish and trend_bullish:
                analysis["signals"]["overallSignal"] = "strong_buy"
            elif rsi_bearish and not trend_bullish:
                analysis["signals"]["overallSignal"] = "strong_sell"
            elif trend_bullish:
                analysis["signals"]["overallSignal"] = "buy"
            elif not trend_bullish:
                analysis["signals"]["overallSignal"] = "sell"
            
            # Risk assessment
            liquidity = float(pair_data["pair"].get("liquidity", {}).get("usd", 0))
            volume_24h = float(pair_data["pair"].get("volume", {}).get("h24", 0))
            
            # Calculate liquidity to volume ratio (higher is better)
            liq_vol_ratio = liquidity / volume_24h if volume_24h > 0 else 0
            
            analysis["riskAssessment"] = {
                "liquidityRisk": "high" if liquidity < 50000 else "medium" if liquidity < 500000 else "low",
                "volatilityRisk": "high" if analysis["indicators"]["volatility"] > 0.1 else 
                                "medium" if analysis["indicators"]["volatility"] > 0.05 else "low",
                "liquidityToVolumeRatio": liq_vol_ratio,
                "overallRisk": "high" if liquidity < 100000 or analysis["indicators"]["volatility"] > 0.15 else 
                              "medium" if liquidity < 500000 or analysis["indicators"]["volatility"] > 0.08 else "low"
            }
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing DEX trading pair: {e}")
            return {"error": str(e)}
            
    def find_arbitrage_opportunities(self, token_address: str, chain_id: str = "ethereum", min_price_diff_percent: float = 1.0) -> dict:
        """
        Find arbitrage opportunities for a token across multiple DEXes
        
        Args:
            token_address: The contract address of the token
            chain_id: The blockchain (ethereum, bsc, polygon, etc.)
            min_price_diff_percent: Minimum price difference to consider as an opportunity (%)
            
        Returns:
            List of arbitrage opportunities sorted by potential profit
        """
        try:
            # Moralis WebSocket URL for mainnet events
            self.moralis_ws_url = "wss://ws.moralis.io/mainnet?apiKey=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJub25jZSI6IjEzMGM1NGU3LTI0ZGQtNGRmZC04ZDViLTU4NTBlNTE2NTBhMiIsIm9yZ0lkIjoiNDYzNjgyIiwidXNlcklkIjoiNDc3MDMzIiwidHlwZUlkIjoiNjkwZWI2ZDAtMDFlZS00ZmMzLTg0OWItM2Y4ZTNhZGE2Nzc1IiwidHlwZSI6IlBST0pFQ1QiLCJpYXQiOjE3NTQ1Mzc1MjUsImV4cCI6NDkxMDI5NzUyNX0.QJJu4v6JZC77miG3JXEUKxAw3d_OfNTcE_P9B7YTG-I"
            
            # Fetch all trading pairs for the token
            pairs_data = self.fetch_token_pairs(token_address, chain_id)
            
            if "error" in pairs_data:
                return pairs_data
                
            if "pairs" not in pairs_data or not pairs_data["pairs"]:
                return {"status": "No pairs found for this token"}
                
            # Extract and process pair data
            pairs = pairs_data.get("pairs", [])
            
            # Filter for WETH or USDT pairs
            eth_or_usdt_pairs = [
                p for p in pairs 
                if (p.get("baseToken", {}).get("symbol", "") == "WETH" or 
                    p.get("quoteToken", {}).get("symbol", "") == "USDT")
            ]
            
            # If we have filtered pairs, use those; otherwise use all pairs
            filtered_pairs = eth_or_usdt_pairs if eth_or_usdt_pairs else pairs
            
            # Filter out pairs with insufficient liquidity
            min_liquidity = 10000  # $10k minimum liquidity
            viable_pairs = [
                p for p in filtered_pairs 
                if p.get("liquidity", {}).get("usd", 0) > min_liquidity
            ]
            
            if not viable_pairs:
                return {"status": "No viable pairs with sufficient liquidity found"}
                
            # Organize pairs by DEX and extract prices
            dex_prices = {}
            for pair in viable_pairs:
                dex_id = pair.get("dexId", "unknown")
                price_usd = pair.get("priceUsd", 0)
                liquidity = pair.get("liquidity", {}).get("usd", 0)
                
                if price_usd > 0:
                    if dex_id not in dex_prices:
                        dex_prices[dex_id] = []
                    
                    dex_prices[dex_id].append({
                        "pairAddress": pair.get("pairAddress", ""),
                        "baseToken": pair.get("baseToken", {}).get("symbol", ""),
                        "quoteToken": pair.get("quoteToken", {}).get("symbol", ""),
                        "priceUsd": price_usd,
                        "liquidity": liquidity
                    })
            
            # Find arbitrage opportunities between DEXes
            opportunities = []
            
            dex_ids = list(dex_prices.keys())
            for i in range(len(dex_ids)):
                for j in range(i+1, len(dex_ids)):
                    dex_a = dex_ids[i]
                    dex_b = dex_ids[j]
                    
                    for pair_a in dex_prices[dex_a]:
                        for pair_b in dex_prices[dex_b]:
                            # Ensure we're comparing the same quote token (e.g., USDT/USDC)
                            if pair_a["quoteToken"] != pair_b["quoteToken"]:
                                continue
                            
                            price_a = pair_a["priceUsd"]
                            price_b = pair_b["priceUsd"]
                            
                            # Calculate price difference and direction
                            if price_a > price_b:
                                buy_dex = dex_b
                                buy_pair = pair_b
                                sell_dex = dex_a
                                sell_pair = pair_a
                                price_diff_percent = (price_a - price_b) / price_b * 100
                            else:
                                buy_dex = dex_a
                                buy_pair = pair_a
                                sell_dex = dex_b
                                sell_pair = pair_b
                                price_diff_percent = (price_b - price_a) / price_a * 100
                            
                            # Check if difference exceeds minimum threshold
                            if price_diff_percent >= min_price_diff_percent:
                                # Calculate maximum profitable trade size based on liquidity
                                max_trade_size = min(buy_pair["liquidity"], sell_pair["liquidity"]) * 0.05  # 5% of liquidity
                                potential_profit = max_trade_size * price_diff_percent / 100
                                
                                opportunities.append({
                                    "buyDex": buy_dex,
                                    "buyPrice": buy_pair["priceUsd"],
                                    "buyPair": buy_pair["pairAddress"],
                                    "sellDex": sell_dex,
                                    "sellPrice": sell_pair["priceUsd"],
                                    "sellPair": sell_pair["pairAddress"],
                                    "priceDiffPercent": price_diff_percent,
                                    "maxTradeSize": max_trade_size,
                                    "potentialProfit": potential_profit,
                                    "baseToken": pair_a["baseToken"],
                                    "quoteToken": pair_a["quoteToken"]
                                })
            
            # Sort opportunities by potential profit (descending)
            opportunities.sort(key=lambda x: x["potentialProfit"], reverse=True)
            
            # Add additional analysis with GPU acceleration if available
            if self.gpu_available and opportunities:
                # In a real implementation, we would compute additional metrics
                # like volatility, risk, etc. using GPU acceleration
                pass
            
            return {
                "token": token_address,
                "chainId": chain_id,
                "opportunitiesCount": len(opportunities),
                "opportunities": opportunities,
                "filteredByEthOrUsdt": len(eth_or_usdt_pairs),
                "totalPairsFound": len(pairs),
                "viablePairsCount": len(viable_pairs)
            }
            
        except Exception as e:
            logger.error(f"Error finding arbitrage opportunities: {e}")
            return {"error": str(e)}
    
    def monitor_eth_based_tokens(self, callback=None, min_liquidity_usd=10000):
        """
        Monitor new ETH-based tokens in real-time using Moralis WebSocket
        
        Args:
            callback: Callback function to process new token events
            min_liquidity_usd: Minimum liquidity in USD to consider a token viable
            
        Returns:
            WebSocket connection object
        """
        try:
            import websocket
            import json
            import threading
            
            # Moralis WebSocket URL with API key
            ws_url = "wss://ws.moralis.io/mainnet?apiKey=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJub25jZSI6IjEzMGM1NGU3LTI0ZGQtNGRmZC04ZDViLTU4NTBlNTE2NTBhMiIsIm9yZ0lkIjoiNDYzNjgyIiwidXNlcklkIjoiNDc3MDMzIiwidHlwZUlkIjoiNjkwZWI2ZDAtMDFlZS00ZmMzLTg0OWItM2Y4ZTNhZGE2Nzc1IiwidHlwZSI6IlBST0pFQ1QiLCJpYXQiOjE3NTQ1Mzc1MjUsImV4cCI6NDkxMDI5NzUyNX0.QJJu4v6JZC77miG3JXEUKxAw3d_OfNTcE_P9B7YTG-I"
            
            def on_message(ws, message):
                try:
                    data = json.loads(message)
                    # Process messages for new pair listings with WETH or USDT
                    if "topic" in data and data["topic"] == "PairCreated":
                        pair_data = data.get("data", {})
                        token0 = pair_data.get("token0", {})
                        token1 = pair_data.get("token1", {})
                        
                        # Check if one of the tokens is WETH or USDT
                        is_eth_pair = (token0.get("symbol") == "WETH" or 
                                       token1.get("symbol") == "WETH")
                        is_usdt_pair = (token0.get("symbol") == "USDT" or 
                                        token1.get("symbol") == "USDT")
                        
                        if is_eth_pair or is_usdt_pair:
                            # For new ETH pairs, get the non-ETH token
                            if is_eth_pair:
                                new_token = token1 if token0.get("symbol") == "WETH" else token0
                            else:
                                new_token = token1 if token0.get("symbol") == "USDT" else token0
                            
                            # Enrich with DexScreener data
                            token_data = self.fetch_token_profile(new_token.get("address"))
                            
                            # Add pair creation data
                            token_data["pairCreated"] = {
                                "pairAddress": pair_data.get("pairAddress"),
                                "dex": pair_data.get("dexId", "unknown"),
                                "block": pair_data.get("block"),
                                "timestamp": pair_data.get("timestamp")
                            }
                            
                            # Check liquidity threshold
                            liquidity = token_data.get("liquidity", {}).get("usd", 0)
                            if liquidity >= min_liquidity_usd:
                                # Process using callback if provided
                                if callback:
                                    callback(token_data)
                                else:
                                    logger.info(f"New ETH-based token: {new_token.get('symbol')} with ${liquidity} liquidity")
                except Exception as e:
                    logger.error(f"Error processing WebSocket message: {e}")
            
            def on_error(ws, error):
                logger.error(f"WebSocket error: {error}")
            
            def on_close(ws, close_status_code, close_msg):
                logger.info(f"WebSocket connection closed: {close_msg}")
            
            def on_open(ws):
                logger.info("WebSocket connection established")
                # Subscribe to pair creation events
                subscribe_msg = json.dumps({
                    "action": "subscribe",
                    "topic": "PairCreated",
                    "options": {
                        "chains": ["eth"],
                        "include": ["token0", "token1", "pairAddress", "dexId", "block", "timestamp"]
                    }
                })
                ws.send(subscribe_msg)
            
            # Initialize WebSocket connection
            websocket.enableTrace(False)
            ws = websocket.WebSocketApp(ws_url,
                                       on_message=on_message,
                                       on_error=on_error,
                                       on_close=on_close,
                                       on_open=on_open)
            
            # Start WebSocket connection in a separate thread
            wst = threading.Thread(target=ws.run_forever)
            wst.daemon = True
            wst.start()
            
            return ws
            
        except Exception as e:
            logger.error(f"Error setting up ETH token monitor: {e}")
            return None
    
    def fetch_token_profile(self, token_address: str, chain_id: str = "ethereum") -> dict:
        """
        Fetch token profile data from DexScreener API
        
        Args:
            token_address: The contract address of the token
            chain_id: The blockchain (ethereum, bsc, polygon, etc.)
            
        Returns:
            Token profile data
        """
        try:
            import requests
            
            url = f"{self.dex_screener_api['token_profiles']}/{chain_id}/{token_address}"
            headers = {
                "Accept": "application/json",
                "User-Agent": "CryptoTradingBot/1.0"
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                data = response.json()
                # Apply GPU acceleration to process metrics if available
                if self.gpu_available and data.get("priceChart") and len(data["priceChart"]) > 1000:
                    price_data = np.array([point["value"] for point in data["priceChart"]])
                    # Add technical indicators using GPU acceleration
                    data["technicalIndicators"] = {
                        "rsi": self.accelerated_rsi(price_data).tolist(),
                        "ema20": self.accelerated_ema(price_data, 20).tolist(),
                        "ema50": self.accelerated_ema(price_data, 50).tolist(),
                        "volatility": self.accelerated_rolling_std(price_data, 20).tolist()
                    }
                return data
            else:
                logger.warning(f"DexScreener API returned status code {response.status_code}")
                return {"error": f"API returned status code {response.status_code}"}
                
        except Exception as e:
            logger.error(f"Error fetching token profile: {e}")
            return {"error": str(e)}

    def continue_to_iterate(self, data: np.ndarray, threshold: float = 0.05) -> bool:
        """
        Determine if we should continue iterating based on convergence
        
        Args:
            data: Input data array to check for convergence
            threshold: Convergence threshold
            
        Returns:
            Boolean indicating whether to continue iterating
        """
        if len(data) < 2:
            return True
        
        # Calculate change rate
        change_rate = np.abs(data[-1] - data[-2]) / (np.abs(data[-2]) + 1e-8)
        
        # Return True if we need to continue (change rate > threshold)
        return change_rate > threshold
        
    def fetch_token_boosts(self, chain_id: str = None) -> dict:
        """
        Fetch latest token boosts from DexScreener
        
        Args:
            chain_id: Optional blockchain ID to filter results
            
        Returns:
            Token boost data
        """
        try:
            import requests
            
            url = self.dex_screener_api['token_boosts']
            if chain_id:
                url += f"?chainId={chain_id}"
                
            headers = {
                "Accept": "application/json",
                "User-Agent": "CryptoTradingBot/1.0"
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                return response.json()
            else:
                logger.warning(f"DexScreener API returned status code {response.status_code}")
                return {"error": f"API returned status code {response.status_code}"}
                
        except Exception as e:
            logger.error(f"Error fetching token boosts: {e}")
            return {"error": str(e)}
            
    def fetch_top_token_boosts(self, limit: int = 10, chain_id: str = None) -> dict:
        """
        Fetch top token boosts from DexScreener
        
        Args:
            limit: Maximum number of results to return (1-100)
            chain_id: Optional blockchain ID to filter results
            
        Returns:
            Top token boost data
        """
        try:
            import requests
            
            url = f"{self.dex_screener_api['token_boosts_top']}?limit={limit}"
            if chain_id:
                url += f"&chainId={chain_id}"
                
            headers = {
                "Accept": "application/json",
                "User-Agent": "CryptoTradingBot/1.0"
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                return response.json()
            else:
                logger.warning(f"DexScreener API returned status code {response.status_code}")
                return {"error": f"API returned status code {response.status_code}"}
                
        except Exception as e:
            logger.error(f"Error fetching top token boosts: {e}")
            return {"error": str(e)}
            
    def fetch_token_orders(self, token_address: str, chain_id: str = "ethereum") -> dict:
        """
        Fetch order book data for a token from DexScreener
        
        Args:
            token_address: The contract address of the token
            chain_id: The blockchain (ethereum, bsc, polygon, etc.)
            
        Returns:
            Order book data
        """
        try:
            import requests
            
            url = f"{self.dex_screener_api['orders']}/{chain_id}/{token_address}"
            headers = {
                "Accept": "application/json",
                "User-Agent": "CryptoTradingBot/1.0"
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                return response.json()
            else:
                logger.warning(f"DexScreener API returned status code {response.status_code}")
                return {"error": f"API returned status code {response.status_code}"}
                
        except Exception as e:
            logger.error(f"Error fetching token orders: {e}")
            return {"error": str(e)}
            
    def fetch_dex_pair(self, pair_id: str, chain_id: str = "ethereum") -> dict:
        """
        Fetch trading pair data from DexScreener
        
        Args:
            pair_id: The DEX pair ID
            chain_id: The blockchain (ethereum, bsc, polygon, etc.)
            
        Returns:
            DEX pair data
        """
        try:
            import requests
            
            url = f"{self.dex_screener_api['dex_pairs']}/{chain_id}/{pair_id}"
            headers = {
                "Accept": "application/json",
                "User-Agent": "CryptoTradingBot/1.0"
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                data = response.json()
                # Apply GPU acceleration to calculate additional metrics if price history is available
                if self.gpu_available and "priceUsd" in data.get("pair", {}):
                    # This is a placeholder - in a real implementation, we would extract price history 
                    # and calculate technical indicators using GPU acceleration
                    pass
                return data
            else:
                logger.warning(f"DexScreener API returned status code {response.status_code}")
                return {"error": f"API returned status code {response.status_code}"}
                
        except Exception as e:
            logger.error(f"Error fetching DEX pair: {e}")
            return {"error": str(e)}
            
    def search_dex_pairs(self, query: str) -> dict:
        """
        Search for DEX pairs by token name or address
        
        Args:
            query: Search query (token name, symbol or address)
            
        Returns:
            Search results with DEX pairs
        """
        try:
            import requests
            
            url = f"{self.dex_screener_api['dex_search']}?q={query}"
            headers = {
                "Accept": "application/json",
                "User-Agent": "CryptoTradingBot/1.0"
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                return response.json()
            else:
                logger.warning(f"DexScreener API returned status code {response.status_code}")
                return {"error": f"API returned status code {response.status_code}"}
                
        except Exception as e:
            logger.error(f"Error searching DEX pairs: {e}")
            return {"error": str(e)}
            
    def fetch_token_pairs(self, token_address: str, chain_id: str = "ethereum") -> dict:
        """
        Fetch all trading pairs for a token from DexScreener
        
        Args:
            token_address: The contract address of the token
            chain_id: The blockchain (ethereum, bsc, polygon, etc.)
            
        Returns:
            Token pairs data
        """
        try:
            import requests
            
            url = f"{self.dex_screener_api['token_pairs']}/{chain_id}/{token_address}"
            headers = {
                "Accept": "application/json",
                "User-Agent": "CryptoTradingBot/1.0"
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                return response.json()
            else:
                logger.warning(f"DexScreener API returned status code {response.status_code}")
                return {"error": f"API returned status code {response.status_code}"}
                
        except Exception as e:
            logger.error(f"Error fetching token pairs: {e}")
            return {"error": str(e)}
            
    def fetch_tokens(self, token_addresses: list, chain_id: str = "ethereum") -> dict:
        """
        Fetch data for multiple tokens from DexScreener
        
        Args:
            token_addresses: List of token contract addresses
            chain_id: The blockchain (ethereum, bsc, polygon, etc.)
            
        Returns:
            Token data for multiple tokens
        """
        try:
            import requests
            
            # Join addresses with commas
            addresses_str = ",".join(token_addresses)
            
            url = f"{self.dex_screener_api['tokens']}/{chain_id}/{addresses_str}"
            headers = {
                "Accept": "application/json",
                "User-Agent": "CryptoTradingBot/1.0"
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                return response.json()
            else:
                logger.warning(f"DexScreener API returned status code {response.status_code}")
                return {"error": f"API returned status code {response.status_code}"}
                
        except Exception as e:
            logger.error(f"Error fetching tokens: {e}")
            return {"error": str(e)}
    
    def fetch_gas_prices(self) -> dict:
        """
        Fetch current Ethereum gas prices from Etherscan API
        
        Returns:
            Dictionary containing current gas prices (safe, standard, fast)
        """
        try:
            import requests
            
            # Etherscan Gas Tracker API endpoint
            url = f"https://api.etherscan.io/api?module=gastracker&action=gasoracle&apikey={self.api_key}"
            
            headers = {
                "Accept": "application/json",
                "User-Agent": "CryptoTradingBot/1.0"
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                if data["status"] == "1" and data["message"] == "OK":
                    result = data["result"]
                    # Apply time-based caching to avoid hitting rate limits
                    current_time = time.time()
                    
                    # Store last updated timestamp and data
                    if not hasattr(self, 'last_gas_update'):
                        self.last_gas_update = current_time
                        self.last_gas_data = result
                    else:
                        self.last_gas_update = current_time
                        self.last_gas_data = result
                    
                    # Calculate additional stats for algorithmic trading
                    if self.gpu_available and hasattr(self, 'gas_history_data'):
                        # Add to historical data for trend analysis
                        if not hasattr(self, 'gas_history_data'):
                            self.gas_history_data = []
                        
                        # Add timestamp to the data
                        result['timestamp'] = current_time
                        self.gas_history_data.append(result)
                        
                        # Limit history to 1000 data points
                        if len(self.gas_history_data) > 1000:
                            self.gas_history_data.pop(0)
                    
                    # Format gas price data for easier consumption
                    formatted_result = {
                        "safe_gas_price": float(result.get("SafeGasPrice", 0)),
                        "standard_gas_price": float(result.get("ProposeGasPrice", 0)),
                        "fast_gas_price": float(result.get("FastGasPrice", 0)),
                        "base_fee": float(result.get("suggestBaseFee", 0)),
                        "gas_used_ratio": float(result.get("gasUsedRatio", 0)),
                        "timestamp": current_time,
                        "raw_data": result
                    }
                    
                    return formatted_result
                else:
                    logger.warning(f"Etherscan API error: {data.get('message', 'Unknown error')}")
                    return {"error": data.get("message", "Unknown error")}
            else:
                logger.warning(f"Etherscan API returned status code {response.status_code}")
                return {"error": f"API returned status code {response.status_code}"}
                
        except Exception as e:
            logger.error(f"Error fetching gas prices: {e}")
            return {"error": str(e)}
    
    def estimate_transaction_cost(self, gas_limit: int = 21000) -> dict:
        """
        Estimate Ethereum transaction costs based on current gas prices
        
        Args:
            gas_limit: Gas limit for the transaction (default: 21000 for simple ETH transfer)
            
        Returns:
            Dictionary containing estimated costs in Gwei and USD
        """
        try:
            # Fetch current gas prices
            gas_prices = self.fetch_gas_prices()
            
            if "error" in gas_prices:
                return gas_prices
            
            # Get ETH price in USD (placeholder - in production this would call a price API)
            eth_price_usd = 3500  # Example price
            
            # Calculate costs for different speeds
            costs = {}
            for speed in ["safe_gas_price", "standard_gas_price", "fast_gas_price"]:
                gas_price = gas_prices[speed]
                
                # Gas price is in Gwei, convert to ETH (1 Gwei = 0.000000001 ETH)
                cost_in_eth = (gas_price * gas_limit) * 0.000000001
                cost_in_usd = cost_in_eth * eth_price_usd
                
                speed_name = speed.replace("_gas_price", "")
                costs[speed_name] = {
                    "gas_price_gwei": gas_price,
                    "gas_limit": gas_limit,
                    "cost_eth": cost_in_eth,
                    "cost_usd": cost_in_usd
                }
            
            # Add timestamp and base fee
            costs["timestamp"] = gas_prices["timestamp"]
            costs["base_fee"] = gas_prices["base_fee"]
            costs["gas_used_ratio"] = gas_prices["gas_used_ratio"]
            
            return costs
            
        except Exception as e:
            logger.error(f"Error estimating transaction cost: {e}")
            return {"error": str(e)}

# Global GPU accelerator instance
gpu_accelerator = GPUAccelerator()
