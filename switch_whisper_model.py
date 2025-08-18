#!/usr/bin/env python3
"""
Utility script to switch between different Whisper models
"""

import os
import json
import sys

def switch_whisper_model(model_name):
    """Switch to a different Whisper model"""
    
    # Valid models
    valid_models = ['tiny', 'base', 'small', 'medium', 'large']
    
    if model_name not in valid_models:
        print(f"❌ Invalid model: {model_name}")
        print(f"Valid models: {', '.join(valid_models)}")
        return False
    
    # Model information
    model_info = {
        'tiny': {'size': '39MB', 'memory': '~1GB', 'speed': 'Fastest', 'accuracy': 'Good'},
        'base': {'size': '74MB', 'memory': '~1GB', 'speed': 'Fast', 'accuracy': 'Better'},
        'small': {'size': '244MB', 'memory': '~2GB', 'speed': 'Medium', 'accuracy': 'Best'},
        'medium': {'size': '769MB', 'memory': '~5GB', 'speed': 'Slow', 'accuracy': 'Excellent'},
        'large': {'size': '1550MB', 'memory': '~10GB', 'speed': 'Slowest', 'accuracy': 'Outstanding'}
    }
    
    info = model_info[model_name]
    
    print(f"🔄 Switching to Whisper model: {model_name}")
    print(f"   Size: {info['size']}")
    print(f"   GPU Memory: {info['memory']}")
    print(f"   Speed: {info['speed']}")
    print(f"   Accuracy: {info['accuracy']}")
    
    # Update config file
    config_path = "config/settings.json"
    
    try:
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                config = json.load(f)
        else:
            config = {
                "asr": {
                    "default_system": "whisper",
                    "fallback_system": "vosk",
                    "whisper": {
                        "model": "small",
                        "device": "cuda",
                        "compute_type": "int8_float16",
                        "language": "en",
                        "beam_size": 1,
                        "vad_filter": True
                    }
                },
                "voice_interface": {
                    "sample_rate": 16000,
                    "voice_threshold": 0.5,
                    "silence_threshold": 0.01,
                    "min_voice_duration": 0.5
                }
            }
        
        # Update the model
        config['asr']['whisper']['model'] = model_name
        
        # Write back to file
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)
        
        print(f"✅ Successfully switched to {model_name} model!")
        print(f"   Configuration saved to: {config_path}")
        
        # Also set environment variable for immediate use
        os.environ['WHISPER_MODEL'] = model_name
        print(f"   Environment variable WHISPER_MODEL set to: {model_name}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error updating configuration: {e}")
        return False

def show_current_model():
    """Show the currently configured model"""
    
    config_path = "config/settings.json"
    
    try:
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                config = json.load(f)
                current_model = config.get('asr', {}).get('whisper', {}).get('model', 'small')
        else:
            current_model = 'small'  # default
        
        env_model = os.environ.get('WHISPER_MODEL', None)
        
        print(f"📋 Current Whisper model configuration:")
        print(f"   Config file: {current_model}")
        if env_model:
            print(f"   Environment: {env_model}")
        else:
            print(f"   Environment: Not set (using config file)")
        
        return current_model
        
    except Exception as e:
        print(f"❌ Error reading configuration: {e}")
        return None

def main():
    """Main function"""
    
    if len(sys.argv) < 2:
        print("🔧 Whisper Model Switcher")
        print("=" * 30)
        print("Usage:")
        print("  python switch_whisper_model.py <model>")
        print("  python switch_whisper_model.py --current")
        print("")
        print("Available models:")
        print("  tiny   - 39MB, Fastest, Good accuracy")
        print("  base   - 74MB, Fast, Better accuracy")
        print("  small  - 244MB, Medium, Best accuracy (default)")
        print("  medium - 769MB, Slow, Excellent accuracy")
        print("  large  - 1550MB, Slowest, Outstanding accuracy")
        print("")
        show_current_model()
        return
    
    if sys.argv[1] == '--current':
        show_current_model()
        return
    
    model_name = sys.argv[1].lower()
    success = switch_whisper_model(model_name)
    
    if success:
        print("\n💡 Next steps:")
        print("   1. Restart your voice assistant")
        print("   2. Test with: python test_whisper_asr.py")
        print("   3. The new model will be downloaded automatically on first use")

if __name__ == "__main__":
    main()
