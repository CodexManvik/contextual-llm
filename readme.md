# Contextual LLM AI Assistant

A voice-enabled AI assistant for Windows automation, WhatsApp Web control, and natural language command parsing.

## Features

- **Whisper ASR as Default**: OpenAI Whisper speech recognition with GPU acceleration (faster-whisper)
- **Vosk as Fallback**: Automatic fallback to Vosk ASR if Whisper fails
- **Configurable ASR**: Easy configuration via `config/settings.json` and environment variables
- **Advanced Voice Detection**: 
  - Adaptive threshold system that learns from background noise
  - Improved sensitivity and responsiveness
  - Better state management for voice commands
  - Configurable voice duration limits
  - Real-time audio level monitoring
- **Voice Calibration**: Automatic and manual calibration tools
- WhatsApp Web automation (Selenium)
- System/application control (pywinauto)
- File operations
- Extensible command parsing (LLM-ready)

## Installation

### Quick Setup (Recommended)

Run the setup script to automatically configure everything:

```sh
python setup.py
```

This will:
- Install all dependencies
- Create necessary directories
- Set up environment configuration
- Check for required model files

**For Models (Recommended):**
```sh
python download_models.py
```

This downloads:
- Whisper ASR models (GPU-accelerated)
- Vosk ASR models (fallback)
- Piper TTS voices (high-quality female English voices)

### Manual Setup

#### 1. Clone the Repository

```sh
git clone https://github.com/yourusername/contextual-llm.git
cd contextual-llm
```

#### 2. Set Up Python Environment

```sh
python -m venv ai_assistant
ai_assistant\Scripts\activate
```

#### 3. Install Requirements

```sh
pip install -r requirements.txt
```

#### 4. Configure Environment

Copy the environment template and configure your settings:

```sh
copy env.template .env
```

Edit `.env` file to configure:
- `WHISPER_MODEL`: Model size (tiny, base, small, medium)
- `WHISPER_DEVICE`: cuda or cpu
- `WHISPER_DEVICE_INDEX`: GPU index (0 for RTX 3050)
- `WHISPER_COMPUTE_TYPE`: int8_float16 for 4GB VRAM

#### 5. Download Models

Run the model downloader to get all necessary models:

```sh
python download_models.py
```

This will download:
- **Whisper ASR models**: GPU-accelerated speech recognition (small + base)
- **Vosk ASR models**: Fallback speech recognition
- **Piper TTS voices**: High-quality female English voices (Amy, Sarah)

**GPU Setup**: Whisper will automatically use your NVIDIA RTX 3050 (GPU 0) with optimized settings for 4GB VRAM.

Environment overrides (optional) in `.env`:

```
WHISPER_MODEL=small            # tiny, base, small, medium; 'small' fits 4GB VRAM
WHISPER_DEVICE=cuda            # cuda or cpu
WHISPER_DEVICE_INDEX=0         # GPU index in Task Manager
WHISPER_COMPUTE_TYPE=int8_float16
WHISPER_LANGUAGE=en            # English/Indian English
WHISPER_BEAM_SIZE=1
WHISPER_VAD_FILTER=1
```

**Note:** The app works without Vosk if Whisper is installed. Without both, it runs voice detection mode only.

#### 6. Run the Assistant

```sh
python src/main.py
```

## Project Structure

```
contextual-llm/
├── src/
│   ├── main.py
|   |───llm_manager.py
|   |───piper_manager.py
│   ├── controllers/
|         |───app_discovery.py
|         |───system_controller.py
|         |───whatsapp_controller.py
│   ├── interfaces/
|         |───voice_interface.py
│   └── parsers/
|        |───command_parser.py
├── tests/
├── models/
├── logs/
├── requirements.txt
└── README.md
```

## ASR Configuration

The system now uses **Whisper ASR as the default** with Vosk as fallback. Configuration is available through:

### Settings File (`config/settings.json`)

```json
{
  "asr": {
    "default_system": "whisper",
    "fallback_system": "vosk",
    "whisper": {
      "model": "small",
      "device": "cuda",
      "compute_type": "int8_float16",
      "language": "en"
    }
  }
}
```

### Environment Variables

The following environment variables can be configured in your `.env` file:

| Variable | Description | Default |
|----------|-------------|---------|
| `WHISPER_MODEL` | Whisper model size | `small` |
| `WHISPER_DEVICE` | Device for Whisper | `cuda` |
| `WHISPER_DEVICE_INDEX` | GPU device index | `0` |
| `WHISPER_COMPUTE_TYPE` | Compute precision | `int8_float16` |
| `WHISPER_LANGUAGE` | Language for ASR | `en` |
| `WHISPER_BEAM_SIZE` | Beam search size | `1` |
| `WHISPER_VAD_FILTER` | Voice activity detection | `1` |

### Model Options

| Model | Size | Speed | Accuracy | GPU Memory |
|-------|------|-------|----------|------------|
| tiny  | 39MB | Fastest | Good | ~1GB |
| base  | 74MB | Fast | Better | ~1GB |
| small | 244MB | Medium | Best | ~2GB |
| medium| 769MB | Slow | Excellent | ~5GB |
| large | 1550MB| Slowest | Outstanding | ~10GB |

**Recommendation**: Use `small` for best balance of speed and accuracy.

### Testing Voice Detection

Test the improved voice detection system:

```bash
python test_voice_detection.py
```

This will verify:
- Voice detection sensitivity
- Adaptive threshold system
- Audio level monitoring
- ASR integration

### Voice Detection Calibration

Calibrate voice detection for your environment:

```bash
# Automatic calibration
python calibrate_voice.py

# Show current settings
python calibrate_voice.py show

# Manual adjustment
python calibrate_voice.py manual
```

### Testing ASR Integration

Test the Whisper ASR integration:

```bash
python test_whisper_asr.py
```

This will verify that:
- Whisper ASR is properly configured
- Fallback to Vosk works if needed
- Voice interface starts correctly
- TTS is working

## Notes

- Make sure Chrome is installed for WhatsApp automation.
- For voice features, your microphone must be accessible.
- Log files are written to the `logs/` folder.
- The application will work without a `.env` file using default settings.

## License

MIT (or your preferred license)