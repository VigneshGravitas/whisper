# WhisperTyper

A desktop application that converts speech to text in real-time using OpenAI's Whisper model. The app runs in the system tray and types the recognized text wherever your cursor is focused.

## Features

- Real-time speech-to-text conversion using Whisper
- System tray integration for easy control
- Global hotkey (Ctrl+Shift+S) to toggle listening
- Visual feedback through icon color (green for active, red for inactive)
- Automatic text injection into any focused window

## Installation

1. Make sure you have Python 3.8+ installed
2. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

1. Run the application:
   ```bash
   python whisper_typer.py
   ```

2. The app will appear in your system tray with a red icon (inactive)
3. Click the tray icon to access the menu or use Ctrl+Shift+S to toggle listening
4. When the icon is green, speak normally and your speech will be converted to text
5. The recognized text will be typed automatically where your cursor is focused

## Notes

- The app uses the "base" Whisper model by default for a balance of accuracy and performance
- First-time startup may take a few moments as the Whisper model is downloaded
- Make sure your microphone is properly configured in your system settings
- The app requires appropriate permissions for keyboard input and microphone access

## Requirements

See `requirements.txt` for the complete list of dependencies.

## License

This project is licensed under the MIT License.
