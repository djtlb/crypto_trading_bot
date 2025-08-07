# AMD GPU Acceleration for Crypto Trading Bot

## Overview

This module provides optimized GPU acceleration for the cryptocurrency trading bot, with specific support for AMD GPUs. The implementation uses multiple acceleration backends to ensure the best performance on AMD hardware, with graceful fallbacks when hardware acceleration isn't available.

## Features

- **Multiple Acceleration Backends**:
  - ROCm/HIP for newer AMD GPUs
  - PyOpenCL for cross-platform compatibility
  - Numba JIT for CPU acceleration
  - Polars for fast DataFrame operations

- **Smart Fallback System**:
  - Automatically detects available acceleration methods
  - Gracefully falls back to the best available option
  - Provides consistent API regardless of backend

- **Enhanced AMD Detection**:
  - Improved detection of AMD GPU platforms
  - Better handling of AMD-specific environment variables
  - Support for multiple AMD GPU models

- **Performance Benchmarking**:
  - Built-in tools to compare GPU vs CPU performance
  - Metrics for various calculation types
  - Automatic use of faster methods for each operation

## Usage

```python
from utils.gpu_acceleration import gpu_accelerator

# Use accelerated calculations
data = np.array([...])  # Your price data
result = gpu_accelerator.accelerated_rolling_mean(data, window=20)

# Check which acceleration methods are available
print(f"GPU Available: {gpu_accelerator.gpu_available}")
print(f"OpenCL: {gpu_accelerator.use_opencl}")
print(f"ROCm: {gpu_accelerator.use_rocm}")
print(f"Numba: {gpu_accelerator.use_numba}")
print(f"Polars: {gpu_accelerator.use_polars}")

# Run benchmarks to compare GPU vs CPU performance
benchmark_results = gpu_accelerator.benchmark(data_size=10000)
```

## Supported Calculations

The module accelerates these common trading calculations:

- Rolling mean (moving averages)
- Rolling standard deviation
- Exponential moving average (EMA)
- Relative Strength Index (RSI)
- Average True Range (ATR)
- Momentum indicators
- DataFrame operations (via Polars)

## AMD Setup Instructions

### Prerequisites

For best performance on AMD GPUs:

1. **Install PyOpenCL**:
   ```bash
   pip install pyopencl
   ```

2. **Install Numba**:
   ```bash
   pip install numba
   ```

3. **Install Polars**:
   ```bash
   pip install polars
   ```

4. **Optional: Install ROCm** (for newer AMD GPUs):
   Follow AMD's ROCm installation guide for your specific OS:
   https://rocmdocs.amd.com/en/latest/Installation_Guide/Installation-Guide.html

### Troubleshooting

If you encounter OpenCL initialization errors:

1. **Update GPU Drivers**:
   Ensure you have the latest AMD GPU drivers installed.

2. **Check OpenCL Support**:
   Verify that your AMD GPU supports OpenCL.

3. **Environment Variables**:
   The module automatically sets recommended environment variables for AMD GPUs.

4. **Fallback Mode**:
   Even without OpenCL, the system will use Numba and Polars for acceleration.

## Testing

To test GPU acceleration on your system:

```bash
python test_gpu_acceleration.py
```

This will run benchmarks to check if the acceleration is working correctly and measure the performance improvement.

## Performance Expectations

Performance improvements depend on your specific AMD GPU:

- **High-end AMD GPUs with ROCm**: 10-50x speedup for large datasets
- **AMD GPUs with OpenCL**: 5-20x speedup for large datasets
- **CPU-only with Numba**: 2-10x speedup compared to pure Python
- **Polars DataFrames**: 2-5x speedup for DataFrame operations

Performance is most noticeable with larger datasets (10,000+ data points).
