#!/usr/bin/env python3
"""
Voice Detection Calibration Tool
Helps users calibrate voice detection for their environment
"""

import os
import sys
import time
import json

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from interfaces.voice_interface import VoiceInterface

def calibrate_voice_detection():
    """Calibrate voice detection for the user's environment"""
    print("🎤 Voice Detection Calibration Tool")
    print("=" * 50)
    print("This tool will help you calibrate voice detection for your environment.")
    print("Follow the instructions to get optimal voice detection sensitivity.")
    print()
    
    # Create voice interface
    vi = VoiceInterface()
    
    print("📋 Current Settings:")
    print(f"   Voice Threshold: {vi.voice_threshold}")
    print(f"   Min Voice Duration: {vi.min_voice_duration}s")
    print(f"   Adaptive Threshold: {vi.config.get('voice_interface', {}).get('adaptive_threshold', True)}")
    print()
    
    print("🔧 Starting Calibration...")
    print("1. Please remain SILENT for 5 seconds to measure background noise")
    print("2. Then speak normally for 3 seconds")
    print("3. The system will adjust settings automatically")
    print()
    
    try:
        vi.start_listening()
        
        # Phase 1: Measure background noise
        print("🎯 Phase 1: Measuring background noise...")
        print("   Please remain SILENT for 5 seconds...")
        time.sleep(5)
        
        # Calculate background statistics
        if len(vi.background_levels) > 0:
            background_mean = sum(vi.background_levels) / len(vi.background_levels)
            background_max = max(vi.background_levels)
            print(f"   Background noise level: {background_mean:.4f} (max: {background_max:.4f})")
        else:
            background_mean = 0.01
            print("   No background data collected, using default")
        
        # Phase 2: Measure voice levels
        print("\n🎯 Phase 2: Measuring voice levels...")
        print("   Please speak normally for 3 seconds...")
        time.sleep(3)
        
        # Calculate voice statistics
        if len(vi.voice_levels) > 0:
            voice_mean = sum(vi.voice_levels) / len(vi.voice_levels)
            voice_min = min(vi.voice_levels)
            print(f"   Voice level: {voice_mean:.4f} (min: {voice_min:.4f})")
        else:
            voice_mean = 0.2
            print("   No voice data collected, using default")
        
        # Calculate optimal threshold
        optimal_threshold = max(background_mean + 0.02, voice_min * 0.7)
        optimal_threshold = min(optimal_threshold, 0.3)  # Cap at 0.3
        
        print(f"\n🎯 Calibration Results:")
        print(f"   Background noise: {background_mean:.4f}")
        print(f"   Voice level: {voice_mean:.4f}")
        print(f"   Recommended threshold: {optimal_threshold:.4f}")
        
        # Ask user if they want to apply the new settings
        print(f"\n❓ Apply these optimized settings? (y/n): ", end="")
        try:
            response = input().lower().strip()
            if response in ['y', 'yes']:
                # Update configuration
                config_path = "config/settings.json"
                if os.path.exists(config_path):
                    with open(config_path, 'r') as f:
                        config = json.load(f)
                else:
                    config = {}
                
                # Ensure voice_interface section exists
                if 'voice_interface' not in config:
                    config['voice_interface'] = {}
                
                # Update settings
                config['voice_interface']['voice_threshold'] = round(optimal_threshold, 3)
                config['voice_interface']['adaptive_threshold'] = True
                
                # Write back to file
                with open(config_path, 'w') as f:
                    json.dump(config, f, indent=2)
                
                print(f"✅ Settings updated! New threshold: {optimal_threshold:.3f}")
                print(f"   Restart the assistant to apply the new settings.")
            else:
                print("   Settings not changed.")
        
        except KeyboardInterrupt:
            print("\n   Calibration cancelled.")
        
        # Test the new settings
        print(f"\n🧪 Testing calibrated settings...")
        print("   Speak normally to test voice detection...")
        print("   Press Ctrl+C to stop...")
        
        # Reset for testing
        vi.background_levels.clear()
        vi.voice_levels.clear()
        
        # Let user test
        time.sleep(10)
        
    except KeyboardInterrupt:
        print("\n🛑 Calibration stopped.")
    finally:
        vi.stop_listening()

def show_current_settings():
    """Show current voice detection settings"""
    print("📋 Current Voice Detection Settings:")
    print("=" * 40)
    
    config_path = "config/settings.json"
    if os.path.exists(config_path):
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        voice_config = config.get('voice_interface', {})
        print(f"   Voice Threshold: {voice_config.get('voice_threshold', 0.1)}")
        print(f"   Min Voice Duration: {voice_config.get('min_voice_duration', 0.3)}s")
        print(f"   Max Voice Duration: {voice_config.get('max_voice_duration', 10.0)}s")
        print(f"   Adaptive Threshold: {voice_config.get('adaptive_threshold', True)}")
        print(f"   Noise Reduction: {voice_config.get('noise_reduction', True)}")
    else:
        print("   No configuration file found.")

def manual_adjustment():
    """Manually adjust voice detection settings"""
    print("🔧 Manual Voice Detection Adjustment")
    print("=" * 40)
    
    config_path = "config/settings.json"
    if os.path.exists(config_path):
        with open(config_path, 'r') as f:
            config = json.load(f)
    else:
        config = {}
    
    if 'voice_interface' not in config:
        config['voice_interface'] = {}
    
    voice_config = config['voice_interface']
    
    print("Current settings:")
    print(f"   Voice Threshold: {voice_config.get('voice_threshold', 0.1)}")
    print(f"   Min Voice Duration: {voice_config.get('min_voice_duration', 0.3)}s")
    print(f"   Adaptive Threshold: {voice_config.get('adaptive_threshold', True)}")
    print()
    
    try:
        print("Enter new voice threshold (0.05-0.5, current: {}): ".format(
            voice_config.get('voice_threshold', 0.1)), end="")
        new_threshold = float(input().strip())
        
        if 0.05 <= new_threshold <= 0.5:
            voice_config['voice_threshold'] = new_threshold
            
            with open(config_path, 'w') as f:
                json.dump(config, f, indent=2)
            
            print(f"✅ Voice threshold updated to: {new_threshold}")
        else:
            print("❌ Invalid threshold value. Must be between 0.05 and 0.5")
    
    except (ValueError, KeyboardInterrupt):
        print("❌ Invalid input or cancelled.")

def main():
    """Main calibration function"""
    if len(sys.argv) > 1:
        if sys.argv[1] == 'show':
            show_current_settings()
        elif sys.argv[1] == 'manual':
            manual_adjustment()
        else:
            print("Usage: python calibrate_voice.py [show|manual]")
    else:
        calibrate_voice_detection()

if __name__ == "__main__":
    main()
