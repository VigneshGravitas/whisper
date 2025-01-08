# WhisperTyper Windows Installation Guide

This guide will help you install and run WhisperTyper on a Windows machine.

## System Requirements

### Minimum Requirements:
- Windows 10 or later
- Python 3.9 or higher
- 4GB RAM
- 1GB free disk space
- Working microphone
- Administrator privileges

### Recommended:
- 8GB RAM
- NVIDIA GPU (for faster processing)
- Windows 11
- Python 3.11

## Installation Steps

### 1. Install Python
1. Download Python from [python.org](https://www.python.org/downloads/)
2. Run the installer
3. **Important**: Check "Add Python to PATH" during installation
4. Verify installation by opening Command Prompt and typing:
   ```bash
   python --version
   ```

### 2. Install Visual C++ Redistributable
1. Download from [Microsoft's website](https://aka.ms/vs/17/release/vc_redist.x64.exe)
2. Run the installer
3. Restart your computer if prompted

### 3. Set Up WhisperTyper

#### Option 1: Using Git (Recommended)
```bash
# 1. Install Git if you haven't already
# Download from https://git-scm.com/download/win

# 2. Clone the repository
git clone https://github.com/VigneshGravitas/whisper.git
cd whisper

# 3. Create virtual environment
python -m venv venv

# 4. Activate virtual environment
venv\Scripts\activate

# 5. Install dependencies
pip install -r requirements.txt
```

#### Option 2: Manual Setup
```bash
# 1. Create project directory
mkdir WhisperTyper
cd WhisperTyper

# 2. Download the project files
# Download ZIP from https://github.com/VigneshGravitas/whisper
# Extract to WhisperTyper directory

# 3. Create virtual environment
python -m venv venv

# 4. Activate virtual environment
venv\Scripts\activate

# 5. Install dependencies
pip install -r requirements.txt
```

## Running WhisperTyper

1. Open Command Prompt as Administrator
2. Navigate to the project directory
3. Activate the virtual environment:
   ```bash
   venv\Scripts\activate
   ```
4. Run the application:
   ```bash
   python whisper_typer.py
   ```

## First-Time Setup

1. Allow Python through Windows Firewall if prompted
2. Grant accessibility permissions when requested
3. Check system tray for the WhisperTyper icon
4. Test the microphone in Windows Settings before starting

## Using WhisperTyper

1. Look for the WhisperTyper icon in the system tray (bottom right)
2. Use Ctrl+Shift+S to start/stop speech recognition
3. The icon will be:
   - Red when not listening
   - Green when actively listening

## Troubleshooting

### Common Issues:

1. **"Access Denied" Error**
   - Run Command Prompt as Administrator
   - Check Python PATH in Environment Variables

2. **No Microphone Input**
   - Check microphone settings in Windows
   - Set correct input device in Sound Settings
   - Test microphone in Windows Voice Recorder

3. **High CPU Usage**
   - Consider upgrading to a larger model
   - Close unnecessary background applications
   - Check Task Manager for resource usage

4. **Missing DLL Errors**
   - Install/Reinstall Visual C++ Redistributable
   - Update Windows
   - Check system PATH

5. **Permission Issues**
   - Run as Administrator
   - Check Windows Security settings
   - Allow Python through firewall

### Performance Tips:

1. **For Better Accuracy:**
   - Speak clearly and at a moderate pace
   - Use a good quality microphone
   - Minimize background noise

2. **For Better Performance:**
   - Close unnecessary applications
   - Use a dedicated GPU if available
   - Keep Windows and drivers updated

## Updating WhisperTyper

To update to the latest version:
```bash
git pull origin main
pip install -r requirements.txt
```

## Support

If you encounter any issues:
1. Check the log file: `whispertyper.log`
2. Visit our GitHub repository for updates
3. Submit issues on GitHub with:
   - Error messages
   - System specifications
   - Steps to reproduce the problem

## Uninstallation

1. Close WhisperTyper
2. Delete the project directory
3. (Optional) Remove Python if no longer needed

## Whisper Model Information

## Available Models

WhisperTyper uses the `faster-whisper` implementation of OpenAI's Whisper model. The following models are available:

| Model  | Size  | Memory Usage | Accuracy  | Speed    | Best Use Case |
|--------|-------|--------------|-----------|----------|---------------|
| tiny   | 39M   | ~1GB        | Good      | Fastest  | Quick transcription, low-resource systems |
| base   | 74M   | ~1.5GB      | Better    | Fast     | General purpose, good balance |
| small  | 244M  | ~2GB        | Very Good | Medium   | Professional use, accuracy needed |
| medium | 769M  | ~4GB        | Excellent | Slow     | High accuracy requirements |
| large  | 1.5GB | ~8GB        | Best      | Slowest  | Maximum accuracy needed |

## Model Selection Guide

### Current Default: Tiny Model
- Size: 39M parameters
- Memory: ~1GB
- Best for: Quick transcription and low-resource systems
- Use case: General note-taking, quick commands

### Choosing the Right Model

1. **Tiny Model (Default)**
   - Fastest response time
   - Lowest memory usage
   - Good for basic transcription
   - Recommended for: laptops, older computers

2. **Base Model**
   - Good balance of speed and accuracy
   - Moderate resource usage
   - Better recognition of complex words
   - Recommended for: modern laptops, desktop computers

3. **Small Model**
   - Very good accuracy
   - Reasonable speed
   - Better handling of accents
   - Recommended for: modern desktops, development work

4. **Medium Model**
   - Excellent accuracy
   - Slower processing
   - Great for technical terms
   - Recommended for: powerful workstations

5. **Large Model**
   - Best possible accuracy
   - Resource intensive
   - Perfect for professional use
   - Recommended for: high-performance workstations

## Changing Models

To use a different model, modify line 41 in `whisper_typer.py`:

```python
# Change "tiny" to any of: "base", "small", "medium", "large"
self.model = faster_whisper.WhisperModel("tiny", device="cpu", compute_type="int8")
```

### System Requirements for Different Models

1. **Tiny/Base Model**
   - 4GB RAM
   - Any modern CPU
   - 2GB free disk space

2. **Small Model**
   - 8GB RAM
   - Modern multi-core CPU
   - 4GB free disk space

3. **Medium Model**
   - 16GB RAM
   - Recent CPU or GPU
   - 8GB free disk space

4. **Large Model**
   - 32GB RAM
   - Powerful CPU or GPU
   - 16GB free disk space

### Performance Tips for Larger Models

1. **Using GPU Acceleration**
   ```python
   # For NVIDIA GPU users
   self.model = faster_whisper.WhisperModel("medium", device="cuda", compute_type="float16")
   ```

2. **Optimizing CPU Usage**
   ```python
   # For multi-core CPU optimization
   self.model = faster_whisper.WhisperModel("small", device="cpu", cpu_threads=4)
   ```

3. **Memory Optimization**
   ```python
   # For systems with limited RAM
   self.model = faster_whisper.WhisperModel("base", device="cpu", compute_type="int8")
   ```

## Model Download Information

- Models are downloaded automatically on first use
- Download size varies by model (39MB - 1.5GB)
- Models are cached locally for future use
- Ensure stable internet for initial download
