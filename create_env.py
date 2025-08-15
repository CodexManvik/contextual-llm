#!/usr/bin/env python3
"""
Simple script to create .env file for AI Assistant
"""

import os

def create_env_file():
    """Create a basic .env file"""
    env_content = """# AI Assistant Environment Configuration
# Copy this file to .env and modify as needed

# Speech Recognition (ASR) Settings
# Whisper ASR settings (GPU-accelerated)
WHISPER_MODEL=small
WHISPER_DEVICE=cuda
WHISPER_DEVICE_INDEX=0
WHISPER_COMPUTE_TYPE=int8_float16
WHISPER_LANGUAGE=en

# Additional Whisper settings
WHISPER_BEAM_SIZE=1
WHISPER_VAD_FILTER=1

# System Settings
# These are automatically detected, but you can override if needed
# USERNAME=your_username

# WhatsApp Web Settings (if needed in future)
# WHATSAPP_SESSION_PATH=path/to/session

# Logging Level (optional)
# LOG_LEVEL=INFO
"""
    
    if os.path.exists(".env"):
        print("✅ .env file already exists")
        return True
    
    try:
        with open(".env", "w") as f:
            f.write(env_content)
        print("✅ Created .env file")
        print("📝 Please edit .env file to configure your settings")
        return True
    except Exception as e:
        print(f"❌ Failed to create .env file: {e}")
        return False

if __name__ == "__main__":
    print("🤖 Creating .env file for AI Assistant")
    print("=" * 40)
    create_env_file()
