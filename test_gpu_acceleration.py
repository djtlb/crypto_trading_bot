"""
Test script for AMD GPU acceleration
"""

import logging
import sys
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)

def main():
    print("Testing GPU acceleration with AMD support...")
    
    # Import the GPU accelerator
    from utils.gpu_acceleration import gpu_accelerator
    
    # Check if GPU is available
    print(f"GPU Available: {gpu_accelerator.gpu_available}")
    print(f"OpenCL: {gpu_accelerator.use_opencl}")
    print(f"ROCm: {gpu_accelerator.use_rocm}")
    print(f"Numba: {gpu_accelerator.use_numba}")
    print(f"Polars: {gpu_accelerator.use_polars}")
    
    # Run benchmarks if GPU is available
    if gpu_accelerator.gpu_available:
        print("\nRunning benchmarks...")
        
        # Run the benchmark with different data sizes
        sizes = [1000, 10000, 100000]
        
        for size in sizes:
            print(f"\nBenchmarking with data size: {size}")
            results = gpu_accelerator.benchmark(size)
            
            # Print results
            for test_name, test_results in results['tests'].items():
                if test_results.get('success', False):
                    print(f"  {test_name}:")
                    print(f"    GPU Time: {test_results['gpu_time']:.6f}s")
                    print(f"    CPU Time: {test_results['cpu_time']:.6f}s")
                    print(f"    Speedup: {test_results['speedup']:.2f}x")
                else:
                    print(f"  {test_name}: Failed - {test_results.get('error', 'Unknown error')}")
    else:
        print("\nGPU acceleration not available. Using CPU fallback.")
        
        # Try to run some operations on CPU
        import numpy as np
        data = np.random.randn(1000)
        
        # Test a few operations
        start_time = time.time()
        result = gpu_accelerator.accelerated_rolling_mean(data, 20)
        cpu_time = time.time() - start_time
        
        print(f"\nCPU Rolling Mean time: {cpu_time:.6f}s")
        print(f"Result shape: {result.shape}, first few values: {result[:5]}")
    
    print("\nGPU acceleration test complete.")

if __name__ == "__main__":
    main()
