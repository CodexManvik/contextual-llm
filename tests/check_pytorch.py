#!/usr/bin/env python3
"""
Check PyTorch version and CUDA support
"""

try:
    import torch
    print(f"PyTorch version: {torch.__version__}")
    
    # Check if CUDA is available
    print(f"CUDA available: {torch.cuda.is_available()}")
    
    if torch.cuda.is_available():
        print(f"CUDA device count: {torch.cuda.device_count()}")
        print(f"Current device: {torch.cuda.current_device()}")
        print(f"Device name: {torch.cuda.get_device_name(0)}")
        print(f"Device memory: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f} GB")
    else:
        print("CUDA is not available. This is likely a CPU-only PyTorch installation.")
        
except ImportError:
    print("PyTorch is not installed")
except Exception as e:
    print(f"Error checking PyTorch: {e}")
