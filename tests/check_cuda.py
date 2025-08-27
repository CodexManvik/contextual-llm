#!/usr/bin/env python3
"""
Check CUDA availability and GPU information
"""

try:
    import torch
    print(f"CUDA available: {torch.cuda.is_available()}")
    print(f"CUDA device count: {torch.cuda.device_count()}")
    
    if torch.cuda.is_available():
        print(f"Current device: {torch.cuda.current_device()}")
        print(f"Device name: {torch.cuda.get_device_name(0)}")
        print(f"Device memory: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f} GB")
    else:
        print("CUDA is not available. Please check your PyTorch installation and GPU drivers.")
        
except ImportError:
    print("PyTorch is not installed. Install with: pip install torch")
except Exception as e:
    print(f"Error checking CUDA: {e}")
