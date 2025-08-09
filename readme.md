# Contextual LLM AI Assistant

A voice-enabled AI assistant for Windows automation, WhatsApp Web control, and natural language command parsing.

## Features

- Voice commands with wake word detection (Vosk + pyttsx3)
- WhatsApp Web automation (Selenium)
- System/application control (pywinauto)
- File operations
- Extensible command parsing (LLM-ready)

## Installation

### 1. Clone the Repository

```sh
git clone https://github.com/yourusername/contextual-llm.git
cd contextual-llm
```

### 2. Set Up Python Environment

```sh
python -m venv ai_assistant
ai_assistant\Scripts\activate
```

### 3. Install Requirements

```sh
pip install -r requirements.txt
```

### 4. Download Vosk Model

Download the [vosk-model-en-us-0.22](https://alphacephei.com/vosk/models) and place it in the `models/` folder:

```
contextual-llm/
├── models/
│   └── vosk-model-en-us-0.22/
```

### 5. Create Logs Folder

```sh
mkdir logs
```

### 6. Run the Assistant

```sh
cd src
python main.py
```

## Project Structure

```
contextual-llm/
├── src/
│   ├── main.py
│   ├── controllers/
│   ├── interfaces/
│   └── parsers/
├── tests/
├── models/
├── logs/
├── requirements.txt
└── README.md
```

## Notes

- Make sure Chrome is installed for WhatsApp automation.
- For voice features, your microphone must be accessible.
- Log files are written to the `logs/` folder.

## License

MIT (or your preferred license)