#!/usr/bin/env python3
"""
Setup script for AI Assistant
Helps configure the environment and check dependencies
"""

import os
import sys
import subprocess
import shutil

def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required")
        return False
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor} detected")
    return True

def install_dependencies():
    """Install required dependencies"""
    print("\n📦 Installing dependencies...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        return False

def setup_env_file():
    """Create .env file from template if it doesn't exist"""
    if os.path.exists(".env"):
        print("✅ .env file already exists")
        return True
    
    if os.path.exists("env.template"):
        try:
            shutil.copy("env.template", ".env")
            print("✅ Created .env file from template")
            print("📝 Please edit .env file to configure your settings")
            return True
        except Exception as e:
            print(f"❌ Failed to create .env file: {e}")
            return False
    else:
        print("⚠️ env.template not found, creating basic .env file")
        try:
            with open(".env", "w") as f:
                f.write("# AI Assistant Configuration\n")
                # Whisper defaults for RTX 3050 4GB
                f.write("WHISPER_MODEL=small\n")
                f.write("WHISPER_DEVICE=cuda\n")
                f.write("WHISPER_DEVICE_INDEX=0\n")
                f.write("WHISPER_COMPUTE_TYPE=int8_float16\n")
                f.write("WHISPER_LANGUAGE=en\n")
            print("✅ Created basic .env file")
            return True
        except Exception as e:
            print(f"❌ Failed to create .env file: {e}")
            return False

def check_model_file():
    """Check if ASR model files exist"""
    whisper_models = ["small", "base"]
    vosk_model = "models/vosk-model-small-en-us-0.15"
    
    models_found = []
    if os.path.exists(vosk_model):
        models_found.append("Vosk")
    
    # Check for Whisper models (they're downloaded automatically by faster-whisper)
    try:
        from faster_whisper import WhisperModel
        for model_size in whisper_models:
            try:
                # This will trigger download if not present
                model = WhisperModel(model_size, device="cpu", compute_type="int8")
                models_found.append(f"Whisper {model_size}")
                break
            except Exception:
                continue
    except ImportError:
        pass
    
    if models_found:
        print(f"✅ ASR models found: {', '.join(models_found)}")
        return True
    else:
        print("⚠️ No ASR models found")
        print("📥 Run: python download_models.py to download models")
        return False

def create_directories():
    """Create necessary directories"""
    directories = ["logs", "models", "data"]
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
    print("✅ Created necessary directories")

def main():
    """Main setup function"""
    print("🤖 AI Assistant Setup")
    print("=" * 40)
    
    # Check Python version
    if not check_python_version():
        return False
    
    # Create directories
    create_directories()
    
    # Install dependencies
    if not install_dependencies():
        return False
    
    # Setup environment file
    if not setup_env_file():
        return False
    
    # Check model file
    check_model_file()
    
    print("\n🎉 Setup completed!")
    print("\nNext steps:")
    print("1. Edit .env file to configure your settings")
    print("2. Run: python download_models.py to download ASR models")
    print("3. Run: python src/main.py")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
