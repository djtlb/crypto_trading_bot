"""
Example benchmark results from the GPU accelerator on an AMD system with ROCm
"""

# Sample benchmark results for an AMD GPU with ROCm support
ROCM_BENCHMARK_RESULTS = {
    'data_size': 100000,
    'gpu_available': True,
    'gpu_type': 'ROCm',
    'acceleration_methods': {
        'opencl': False,
        'rocm': True,
        'numba': True,
        'polars': True
    },
    'device_info': {
        'gpu_name': 'AMD Radeon RX 6800',
        'platform': 'AMD ROCm',
        'driver_version': '5.2.0'
    },
    'tests': {
        'rolling_mean': {
            'gpu_time': 0.00268,
            'cpu_time': 0.08732,
            'speedup': 32.58,
            'success': True
        },
        'rolling_std': {
            'gpu_time': 0.00387,
            'cpu_time': 0.10521,
            'speedup': 27.19,
            'success': True
        },
        'ema': {
            'gpu_time': 0.00174,
            'cpu_time': 0.05623,
            'speedup': 32.32,
            'success': True
        },
        'momentum': {
            'gpu_time': 0.00142,
            'cpu_time': 0.02876,
            'speedup': 20.25,
            'success': True
        }
    }
}

# Sample benchmark results for an AMD GPU with Numba only (no ROCm/OpenCL)
NUMBA_BENCHMARK_RESULTS = {
    'data_size': 100000,
    'gpu_available': True,
    'gpu_type': 'None',
    'acceleration_methods': {
        'opencl': False,
        'rocm': False,
        'numba': True,
        'polars': True
    },
    'device_info': {},
    'tests': {
        'rolling_mean': {
            'gpu_time': 0.02184,
            'cpu_time': 0.08732,
            'speedup': 4.0,
            'success': True
        },
        'rolling_std': {
            'gpu_time': 0.03257,
            'cpu_time': 0.10521,
            'speedup': 3.23,
            'success': True
        },
        'ema': {
            'gpu_time': 0.01836,
            'cpu_time': 0.05623,
            'speedup': 3.06,
            'success': True
        },
        'momentum': {
            'gpu_time': 0.00947,
            'cpu_time': 0.02876,
            'speedup': 3.04,
            'success': True
        }
    }
}

# Sample benchmark results for a system with CPU-only (no GPU acceleration)
CPU_ONLY_BENCHMARK_RESULTS = {
    'data_size': 100000,
    'gpu_available': False,
    'gpu_type': 'None',
    'acceleration_methods': {
        'opencl': False,
        'rocm': False,
        'numba': False,
        'polars': True
    },
    'device_info': {},
    'tests': {
        'rolling_mean': {
            'gpu_time': 0.08732,
            'cpu_time': 0.08732,
            'speedup': 1.0,
            'success': True
        },
        'rolling_std': {
            'gpu_time': 0.10521,
            'cpu_time': 0.10521,
            'speedup': 1.0,
            'success': True
        },
        'ema': {
            'gpu_time': 0.05623,
            'cpu_time': 0.05623,
            'speedup': 1.0,
            'success': True
        },
        'momentum': {
            'gpu_time': 0.02876,
            'cpu_time': 0.02876,
            'speedup': 1.0,
            'success': True
        }
    }
}
