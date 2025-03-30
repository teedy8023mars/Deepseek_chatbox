

# DeepSeek ChatBox v2

A feature-rich Tkinter GUI application for interacting with DeepSeek models via Ollama API.

## Key Features
- Multi-model support (1.5b/7b/8b/14b)
- Real-time chat with message history
- Clear chat history button (preserves system settings)
- Dynamic waiting animation with timer
- In-chat parameter configuration
- Response time tracking
- Thread-safe message queue
- Error handling with user notifications
- Cross-platform compatibility

## System Requirements
- Python 3.9+
- 8GB RAM minimum (16GB recommended)
- Ollama service running locally
- Stable internet connection

## Quick Start

### 1. Install Ollama
```bash
# MacOS/Linux
curl -fsSL https://ollama.com/install.sh | sh

# Windows: Download installer from https://ollama.com/download
```

### 2. Download Models
```bash
ollama pull deepseek-r1:1.5b  # Fastest for most tasks
ollama pull deepseek-r1:7b    # Balanced performance
# you can download other models as well
```

### 3. Set Up Python Environment
```bash
python -m venv venv
source venv/bin/activate  # MacOS/Linux
pip install -r requests
```

### 4. Start Application
```bash
# First terminal (Ollama service)
ollama serve

# Second terminal (Application)
python deepseek_chatbox_v2.py
```

## Interface Overview
1. Model Selector - Choose from available DeepSeek variants
2. Chat History - Color-coded messages with timestamps
3. Input Box - Supports parameter configuration (e.g. `temperature=0.5`)
4. Control Buttons:
   - Send/Stop: Toggle for message submission/request cancellation
   - Clear: Reset chat history (preserves system messages)
5. Status Area: Response time and system notifications

## Advanced Features

### Parameter Configuration
Modify model parameters directly in chat:
```plaintext
temperature=0.5  # More deterministic outputs (0.0-1.0)
top_p=0.95       # Broader sampling range (0.0-1.0) 
top_k=30         # Focused token selection (1-100)
```

### Troubleshooting Tips
1. Connection Issues:
```bash
# Verify Ollama status
curl http://localhost:11434
# expected output: Ollama is running%
```

2. Clear Chat History:
   - Use Clear button to reset conversation context
   - System parameters remain unchanged

3. Performance Tuning:
   - Smaller models (1.5b) for faster responses
   - Reduce temperature for more consistent outputs

## Development Notes
- Uses Tkinter's main thread for UI updates
- Background threads handle model requests
- Message queue ensures thread-safe UI operations
- Custom text tags enable rich chat formatting

