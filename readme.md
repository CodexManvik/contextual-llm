# Contextual LLM AI Assistant

A privacy-focused, locally run AI assistant for Windows enabling voice control of apps, automation, and natural language command parsing.

## Features

- Whisper ASR as default with GPU acceleration and Vosk fallback
- Configurable voice detection with adaptive thresholds and background noise learning
- Voice calibration (automatic and manual)
- WhatsApp Web automation via Selenium
- System and application control through pywinauto and GUI automation
- **NVIDIA Task Classifier** for advanced intent parsing and complexity scoring
- Extensible command parsing powered by local LLM
- Continuous voice recognition improvement through learning

## Installation

### Quick Setup

Run the setup script to install dependencies and configure environment:
```python
python setup.py
```

Download models:
```python
python download_models.py
```

### Manual Setup

1. Clone the repository:
```bash
git clone https://github.com/yourusername/contextual-llm.git
cd contextual-llm
```

2. Create virtual environment and activate:
```bash
python -m venv ai_assistant
# Windows
ai_assistant\Scripts\activate
# macOS/Linux
source ai_assistant/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Configure environment variables:
```bash
python create_env.py
```

Edit `.env` file to your setup (e.g., GPU device, model sizes).

5. Download required models (if not using download script):
- Whisper ASR models
- Vosk ASR fallback models
- Piper TTS voices

6. Run the assistant:
```python
python src/main.py
```

## Project Structure

```
contextual-llm/
├── src/
│   ├── core/                  # AI core modules
│   │   ├── intent_parser.py
│   │   ├── context_manager.py
│   │   ├── voice_optimizer.py
│   │   ├── command_planner.py
│   │   └── correction_learner.py
│   ├── controllers/           # System controls and automation
│   │   ├── system_controller.py
│   │   ├── app_discovery.py
│   │   └── whatsapp_controller.py
│   ├── interfaces/            # Voice and other interfaces
│   │   └── voice_interface.py
│   ├── parsers/               # Additional parsers if any
│   │   └── command_parser.py
│   ├── llm_manager.py         # Conversational AI manager
│   ├── piper_manager.py       # TTS manager
│   └── main.py                # Entry point
├── models/                    # AI models and voices (user needs to download)
├── config/                    # Configurations and settings
│   └── settings.json
├── logs/                      # Logs and runtime files
├── tests/                     # Unit and integration tests (private)
├── requirements.txt           # Dependencies
└── README.md                  # This file
```

## Usage Examples

- “Open Notepad”
- “Launch Firefox”
- “Open Word and write a paragraph about AI”

## Advanced Configuration

Control model parameters and device setup in `.env` or `config/settings.json`.

| Variable           | Description                     | Default      |
|--------------------|---------------------------------|--------------|
| WHISPER_MODEL      | Whisper ASR model size          | `small`      |
| WHISPER_DEVICE     | Device for Whisper (cuda/cpu)  | `cuda`       |
| WHISPER_COMPUTE_TYPE | Model compute precision        | `int8_float16` |
| OLLAMA_MODEL       | Local LLM model                 | `gemma2:2b`  |

### NVIDIA Task Classifier Integration

The assistant includes NVIDIA's prompt-task-and-complexity-classifier for advanced intent parsing. To use this feature:

1. **Quick Setup**:
   ```bash
   python setup_nvidia_integration.py
   python download_models.py
   ```

2. **Manual Setup**:
   ```bash
   # Install dependencies
   pip install onnxruntime-gpu tritonclient[http]
   
   # Download models (when prompted)
   python download_models.py
   ```

3. **Optional Triton Server** (for GPU acceleration):
   ```bash
   docker run --gpus=all -p 8000:8000 nvcr.io/nvidia/tritonserver:23.09-py3
   ```

The NVIDIA classifier provides:
- Advanced task classification (7 task types)
- Complexity scoring for commands
- Automatic fallback to rule-based classification
- GPU acceleration support

For detailed setup instructions, see [NVIDIA_INTEGRATION_GUIDE.md](NVIDIA_INTEGRATION_GUIDE.md).

## Branching and Collaboration (for collaborators):

Use branch naming convention:

- `updates/manvik-ai-core`
- `updates/person2-app-discovery`
- `updates/person3-ui-automation`

Typical workflow:

```bash
git checkout -b updates/yourname-feature
git add .
git commit -m "feat: description"
git push origin updates/yourname-feature
```

Open a pull request to merge to `main`.
