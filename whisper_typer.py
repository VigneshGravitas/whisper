import os
import queue
import logging
import sounddevice as sd
import numpy as np
import pyautogui
from pynput import keyboard
import pystray
from PIL import Image
import time
import threading
import torch

class WhisperTyper:
    def __init__(self):
        # Initialize logging
        logging.basicConfig(
            filename='whispertyper.log',
            level=logging.DEBUG,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
        
        # Test PyAutoGUI permissions
        self.logger.info("Testing PyAutoGUI permissions...")
        try:
            pyautogui.write('')
            self.logger.info("PyAutoGUI permissions OK")
        except Exception as e:
            self.logger.error(f"PyAutoGUI permissions error: {e}")
            raise
        
        # Initialize audio settings
        self.channels = 1
        self.sample_rate = 16000
        self.dtype = np.int16
        self.audio_queue = queue.Queue()
        self.is_listening = False
        self.icon = None
        
        # Initialize Silero model
        self.logger.info("Loading Silero model...")
        try:
            self.device = torch.device('cpu')  # Use CPU
            self.model, self.decoder, self.utils = torch.hub.load(
                repo_or_dir='snakers4/silero-models',
                model='silero_stt',
                language='en',
                device=self.device
            )
            self.model.eval()  # Set to evaluation mode
            self.logger.info("Model loaded successfully!")
        except Exception as e:
            self.logger.error(f"Error loading model: {e}")
            raise
        
        # Initialize audio buffer
        self.audio_buffer = []
        self.silence_threshold = 0.025
        self.silence_duration = 1.0  # seconds
        self.max_audio_duration = 4.0  # seconds
        self.last_speech_time = 0
        
        # Log audio devices
        devices = sd.query_devices()
        self.logger.info(f"Available audio devices: {devices}")
        default_device = sd.query_devices(kind='input')
        self.logger.info(f"Default input device: {default_device}")
        
        self.setup_tray()
        self.setup_hotkey()
        self.logger.info("WhisperTyper initialized successfully")
        
        # Start audio processing thread
        self.audio_thread = threading.Thread(target=self.process_audio)
        self.audio_thread.daemon = True
        self.audio_thread.start()
        self.logger.info("Audio processing thread started")

    def audio_callback(self, indata, frames, time, status):
        if status:
            self.logger.warning(f"Audio callback status: {status}")
        if self.is_listening:
            self.audio_queue.put(indata.copy())

    def process_audio(self):
        while True:
            if not self.audio_queue.empty():
                audio_data = self.audio_queue.get()
                
                # Convert to float32 and normalize
                audio_float = audio_data.astype(np.float32).flatten() / np.iinfo(np.int16).max
                
                # Add to buffer
                self.audio_buffer.extend(audio_float)
                
                # Check if we have enough audio
                buffer_duration = len(self.audio_buffer) / self.sample_rate
                
                # Detect silence
                current_energy = np.mean(np.abs(audio_float))
                current_time = time.time()
                is_silence = current_energy < self.silence_threshold
                
                should_process = (
                    buffer_duration >= self.max_audio_duration or
                    (is_silence and buffer_duration >= self.silence_duration)
                )
                
                if should_process and len(self.audio_buffer) > 0:
                    try:
                        # Convert to tensor
                        audio_tensor = torch.FloatTensor(self.audio_buffer).to(self.device)
                        
                        # Transcribe
                        with torch.no_grad():
                            text = self.model(audio_tensor, self.sample_rate)[0]
                        
                        if text.strip():
                            # Process text with strong filtering
                            text = text.lower()
                            
                            # Remove command artifacts
                            artifacts = [
                                "control", "ctrl", "shift", "press", "start", "stop",
                                "let me know", "speak again", "test", "testing",
                                "try speaking", "transcription should",
                                "continue with", "thank you", "okay",
                                "please", "bye", "yes", "no",
                                "recording", "remember to"
                            ]
                            
                            for artifact in artifacts:
                                text = text.replace(artifact, "")
                            
                            # Fix common technical terms
                            replacements = {
                                "cloud-competing": "cloud computing",
                                "cloud competing": "cloud computing",
                                "artificial intelligent": "artificial intelligence",
                                "machine learn": "machine learning",
                                "neural network": "neural networks",
                                "computing flood": "computing platform",
                                "computing platform": "computing platforms",
                                "javascript promised": "javascript promises",
                                "javascript promise": "javascript promises",
                                "hubanities": "kubernetes",
                                "kid prungis": "git branches",
                                "git prunges": "git branches",
                                "api end point": "api endpoint",
                                "rest end point": "rest endpoint",
                                "gpu": "GPU",
                                "api": "API",
                                "o(n log n)": "O(n log n)"
                            }
                            
                            for old, new in replacements.items():
                                text = text.replace(old, new)
                            
                            # Clean up punctuation and format
                            text = text.replace(" .", ".")
                            text = text.replace(" ,", ",")
                            text = text.replace(" ?", "?")
                            text = text.replace(" !", "!")
                            text = text.replace("—", " ")
                            text = text.replace("  ", " ")
                            
                            # Capitalize first letter of sentences
                            text = ". ".join(s.strip().capitalize() for s in text.split(". "))
                            
                            if text.strip() and len(text.strip()) > 3:
                                self.logger.info(f"Transcribed: {text}")
                                pyautogui.write(text.strip() + " ")
                    
                    except Exception as e:
                        self.logger.error(f"Error processing audio: {e}")
                    
                    # Clear buffer
                    self.audio_buffer = []
                    self.last_speech_time = current_time

    def setup_tray(self):
        try:
            # Create system tray icon
            image = Image.new('RGB', (64, 64), 'red')
            self.icon = pystray.Icon(
                'whispertyper',
                image,
                'WhisperTyper (Not Listening)'
            )
            self.logger.info("System tray icon set up successfully")
        except Exception as e:
            self.logger.error(f"Error setting up system tray: {e}")
            raise

    def setup_hotkey(self):
        try:
            # Set up hotkey listener
            self.listener = keyboard.GlobalHotKeys({
                '<ctrl>+<shift>+s': self.on_hotkey_press
            })
            self.listener.start()
            self.logger.info("Hotkey listener started")
        except Exception as e:
            self.logger.error(f"Error setting up hotkey: {e}")
            raise

    def on_hotkey_press(self):
        self.logger.info("Hotkey pressed!")
        self.is_listening = not self.is_listening
        self.update_icon()
        self.logger.info(f"{'Started' if self.is_listening else 'Stopped'} listening")

    def update_icon(self):
        if self.icon:
            color = 'green' if self.is_listening else 'red'
            image = Image.new('RGB', (64, 64), color)
            self.icon.icon = image
            status = 'Listening' if self.is_listening else 'Not Listening'
            self.icon.title = f'WhisperTyper ({status})'

    def run(self):
        self.icon.run()

if __name__ == "__main__":
    logging.info("Starting WhisperTyper...")
    app = WhisperTyper()
    app.run()
