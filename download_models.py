#!/usr/bin/env python3
"""
Model Downloader for AI Assistant
Downloads ASR and TTS models for local use
"""

import os
import sys
import zipfile
import subprocess
from urllib.request import urlretrieve
from pathlib import Path

# Model configurations
VOSK_MODELS = {
}

WHISPER_MODELS = ["tiny", "base", "small", "medium"]  # Available sizes

PIPER_VOICES = {
    # British English female (preferred)
    "en-gb-sarah-medium": "https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_GB/sarah/medium/en_GB-sarah-medium.onnx",
    "en-gb-sarah-low": "https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_GB/sarah/low/en_GB-sarah-low.onnx",
    # American English female (fallback)
    "en-us-amy-medium": "https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_US/amy/medium/en_US-amy-medium.onnx",
    "en-us-amy-low": "https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_US/amy/low/en_US-amy-low.onnx",
}

DEST_DIR = Path("models")
VOSK_DIR = DEST_DIR / "vosk"
PIPER_DIR = DEST_DIR / "piper"


def download_file(url: str, dest_path: Path, description: str) -> bool:
    """Download a file with progress indication"""
    try:
        print(f"📥 Downloading {description}...")
        urlretrieve(url, dest_path)
        print(f"✅ Downloaded {description}")
        return True
    except Exception as e:
        print(f"❌ Failed to download {description}: {e}")
        return False


def extract_zip(zip_path: Path, extract_dir: Path, description: str) -> bool:
    """Extract a zip file"""
    try:
        print(f"📦 Extracting {description}...")
        with zipfile.ZipFile(zip_path, 'r') as zf:
            zf.extractall(extract_dir)
        print(f"✅ Extracted {description}")
        return True
    except Exception as e:
        print(f"❌ Failed to extract {description}: {e}")
        return False


def download_vosk_models():
    """Download Vosk ASR models"""
    print("\n🎤 Downloading Vosk ASR Models...")
    VOSK_DIR.mkdir(exist_ok=True)
    
    for model_name, url in VOSK_MODELS.items():
        zip_name = url.split('/')[-1]
        zip_path = VOSK_DIR / zip_name
        extract_path = VOSK_DIR / model_name
        
        if extract_path.exists():
            print(f"✅ {model_name} already exists, skipping...")
            continue
            
        if download_file(url, zip_path, f"Vosk {model_name}"):
            if extract_zip(zip_path, VOSK_DIR, f"Vosk {model_name}"):
                try:
                    zip_path.unlink()  # Remove zip after extraction
                except Exception:
                    pass


def download_whisper_models():
    """Download Whisper models via faster-whisper"""
    print("\n🤖 Downloading Whisper Models...")
    
    try:
        from faster_whisper import WhisperModel
    except ImportError:
        print("❌ faster-whisper not installed. Install with: pip install faster-whisper")
        return
    
    # Download small and base models (good balance for RTX 3050)
    models_to_download = ["small", "base"]
    
    for model_size in models_to_download:
        try:
            print(f"📥 Downloading Whisper {model_size} model...")
            # This will trigger automatic download
            model = WhisperModel(model_size, device="cpu", compute_type="int8")
            print(f"✅ Whisper {model_size} model ready")
        except Exception as e:
            print(f"❌ Failed to download Whisper {model_size}: {e}")


def download_piper_voices():
    """Download Piper TTS voices"""
    print("\n🔊 Downloading Piper TTS Voices...")
    PIPER_DIR.mkdir(exist_ok=True)
    
    # Download high-quality British female first, then US
    voices_to_download = ["en-gb-sarah-medium", "en-us-amy-medium", "en-gb-sarah-low", "en-us-amy-low"]
    
    for voice_name in voices_to_download:
        if voice_name not in PIPER_VOICES:
            continue
            
        voice_path = PIPER_DIR / f"{voice_name}.onnx"
        if voice_path.exists():
            print(f"✅ {voice_name} already exists, skipping...")
            continue
            
        url = PIPER_VOICES[voice_name]
        if download_file(url, voice_path, f"Piper voice {voice_name}"):
            print(f"✅ Downloaded {voice_name}")


def main():
    """Main download function"""
    print("🤖 AI Assistant Model Downloader")
    print("=" * 40)
    
    DEST_DIR.mkdir(exist_ok=True)
    
    # Download ASR models
    download_vosk_models()
    download_whisper_models()
    
    # Ask about TTS
    try:
        use_piper = input("\n❓ Download Piper TTS voices for better quality? (y/n): ").lower() == 'y'
        if use_piper:
            download_piper_voices()
    except Exception:
        print("⚠️ Non-interactive mode, skipping Piper TTS")
    
    print("\n🎉 Model download completed!")
    print("\nNext steps:")
    print("1. Run: python src/main.py")
    print("2. The assistant will automatically use the best available models")


if __name__ == "__main__":
    main()
