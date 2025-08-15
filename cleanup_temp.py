#!/usr/bin/env python3
"""
Cleanup script to remove temp files and directories
"""

import os
import shutil
import glob

def cleanup_temp_files():
    """Clean up temporary files and directories"""
    print("🧹 Cleaning up temporary files...")
    
    # Clean up temp_asr directory
    temp_asr_dir = "temp_asr"
    if os.path.exists(temp_asr_dir):
        try:
            shutil.rmtree(temp_asr_dir, ignore_errors=True)
            print(f"✅ Removed {temp_asr_dir}")
        except Exception as e:
            print(f"⚠️ Could not remove {temp_asr_dir}: {e}")
    
    # Clean up any remaining temp files in project
    temp_patterns = [
        "*.tmp",
        "*.temp",
        "temp_*",
        "__pycache__",
        "*.pyc"
    ]
    
    for pattern in temp_patterns:
        matches = glob.glob(pattern, recursive=True)
        for match in matches:
            try:
                if os.path.isfile(match):
                    os.remove(match)
                    print(f"✅ Removed file: {match}")
                elif os.path.isdir(match):
                    shutil.rmtree(match, ignore_errors=True)
                    print(f"✅ Removed directory: {match}")
            except Exception as e:
                print(f"⚠️ Could not remove {match}: {e}")
    
    # Clean up Windows temp files that might be locked
    try:
        import tempfile
        tempfile.tempdir = None  # Reset temp directory
    except Exception:
        pass
    
    print("✅ Cleanup completed!")

if __name__ == "__main__":
    cleanup_temp_files()
