#!/usr/bin/env python3
"""
Setup script for NVIDIA Task Classifier integration
Optimized for local GPU inference without Triton server
"""

import os
import sys
import subprocess
from pathlib import Path

def check_dependencies():
    """Check if required dependencies are installed"""
    print("🔍 Checking dependencies...")
    
    required_packages = [
        "onnxruntime-gpu",
        "numpy"
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace('-', '_').split('[')[0])
            print(f"✅ {package}")
        except ImportError:
            missing_packages.append(package)
            print(f"❌ {package}")
    
    return missing_packages

def install_dependencies(missing_packages):
    """Install missing dependencies"""
    if not missing_packages:
        print("✅ All dependencies are already installed!")
        return True
    
    print(f"\n📦 Installing missing packages: {', '.join(missing_packages)}")
    
    try:
        # Install packages
        for package in missing_packages:
            print(f"Installing {package}...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        
        print("✅ All packages installed successfully!")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install packages: {e}")
        return False

def check_cuda_availability():
    """Check if CUDA is available"""
    print("\n🔍 Checking CUDA availability...")
    
    try:
        import torch
        cuda_available = torch.cuda.is_available()
        if cuda_available:
            print(f"✅ CUDA is available - Device: {torch.cuda.get_device_name(0)}")
            # Check CUDA version using a safer approach
            try:
                cuda_version = torch.version.cuda  # type: ignore
                print(f"   CUDA Version: {cuda_version}")
            except AttributeError:
                print("   CUDA Version: Unknown (torch.version.cuda not available)")
        else:
            print("⚠️ CUDA is not available - Using CPU mode")
        return cuda_available
        
    except ImportError:
        print("❌ PyTorch not installed - CUDA check skipped")
        return False

def setup_nvidia_models():
    """Setup NVIDIA model directories and download models"""
    print("\n📁 Setting up NVIDIA model directories...")
    
    models_dir = Path("models")
    nvidia_dir = models_dir / "nvidia"
    
    # Create directories
    models_dir.mkdir(exist_ok=True)
    nvidia_dir.mkdir(exist_ok=True)
    
    print(f"✅ Model directories created at: {nvidia_dir}")
    
    # Check if models need to be downloaded
    model_files = list(nvidia_dir.glob("*.onnx"))
    if model_files:
        print("✅ NVIDIA model files already exist")
        for model_file in model_files:
            print(f"   Found: {model_file.name}")
    else:
        print("⚠️ NVIDIA model files not found")
        print("   Run: python download_models.py to download models")
    
    return nvidia_dir

def main():
    """Main setup function"""
    print("🤖 NVIDIA Integration Setup")
    print("=" * 50)
    
    # Check and install dependencies
    missing_packages = check_dependencies()
    if missing_packages:
        if not install_dependencies(missing_packages):
            print("❌ Setup failed - could not install dependencies")
            return False
    
    # Check CUDA
    cuda_available = check_cuda_availability()
    
    # Setup model directories
    setup_nvidia_models()
    
    print("\n🎉 NVIDIA Integration Setup Complete!")
    print("\nNext steps:")
    print("1. Download NVIDIA models: python download_models.py")
    print("2. Test integration: python test_nvidia_integration.py")
    print("3. Start the assistant: python src/main.py")
    
    if cuda_available:
        print("4. NVIDIA models will use local GPU acceleration")
    else:
        print("4. NVIDIA models will use CPU mode")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
