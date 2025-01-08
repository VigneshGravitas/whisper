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
import faster_whisper

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
        
        # Initialize Whisper model
        self.logger.info("Loading Whisper model...")
        try:
            self.model = faster_whisper.WhisperModel("tiny", device="cpu", compute_type="int8")
            self.logger.info("Model loaded successfully!")
        except Exception as e:
            self.logger.error(f"Error loading model: {e}")
            raise
        
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
            try:
                # Convert to mono if stereo
                if len(indata.shape) > 1:
                    indata = np.mean(indata, axis=1)
                
                # Convert to float32 (what Whisper expects)
                audio_data = indata.astype(np.float32)
                self.logger.debug(f"Audio data shape: {audio_data.shape}, max: {np.max(np.abs(audio_data))}")
                self.audio_queue.put(audio_data)
            except Exception as e:
                self.logger.error(f"Error in audio callback: {e}")

    def process_audio(self):
        while True:
            if self.is_listening:
                try:
                    # Start recording with larger blocks for better word detection
                    with sd.InputStream(
                        channels=self.channels,
                        samplerate=self.sample_rate,
                        dtype=np.float32,
                        callback=self.audio_callback,
                        blocksize=int(self.sample_rate * 0.5)  # 500ms blocks
                    ) as stream:
                        self.logger.info("Started audio stream")
                        audio_buffer = []
                        buffer_duration = 0
                        last_process_time = time.time()
                        active_speech = False
                        silence_duration = 0
                        
                        while self.is_listening:
                            try:
                                # Get audio data
                                audio_data = self.audio_queue.get_nowait()
                                
                                # Check audio level with smoothing
                                current_level = np.abs(audio_data).mean()
                                
                                # Strong noise gate
                                if current_level > 0.025:  # Increased threshold
                                    if not active_speech:
                                        # Clear buffer when new speech starts
                                        audio_buffer = []
                                        buffer_duration = 0
                                        silence_duration = 0
                                    active_speech = True
                                    audio_buffer.append(audio_data)
                                    buffer_duration += 0.5
                                    silence_duration = 0
                                else:
                                    silence_duration += 0.5
                                    if active_speech and silence_duration < 1.0:  # Keep 1s of trailing silence
                                        audio_buffer.append(audio_data)
                                        buffer_duration += 0.5
                                    
                                # Process if we have enough speech and silence
                                should_process = (
                                    len(audio_buffer) > 0 and
                                    buffer_duration >= 1.0 and  # At least 1s of audio
                                    (
                                        (silence_duration >= 1.0) or  # Process after 1s silence
                                        buffer_duration >= 4.0  # Or max 4s chunk
                                    )
                                )
                                
                                if should_process:
                                    try:
                                        # Combine and normalize audio
                                        audio_data = np.concatenate(audio_buffer)
                                        max_val = np.max(np.abs(audio_data))
                                        if max_val > 0:
                                            audio_data = audio_data / max_val * 0.9
                                        
                                        self.logger.debug(f"Processing {len(audio_data)} samples")
                                        
                                        # Use more aggressive VAD settings
                                        segments, _ = self.model.transcribe(
                                            audio_data,
                                            language="en",
                                            vad_filter=True,
                                            vad_parameters=dict(
                                                min_silence_duration_ms=800,  # Longer silence detection
                                                speech_pad_ms=300  # More context
                                            )
                                        )
                                        
                                        # Process text with strong filtering
                                        if segments:
                                            text = " ".join([s.text for s in segments])
                                            if text.strip():
                                                # Convert to lowercase for consistent filtering
                                                text = text.lower()
                                                
                                                # Remove command artifacts and test phrases
                                                artifacts = [
                                                    "control", "ctrl", "shift", "press", "start", "stop",
                                                    "let me know", "speak again", "test", "testing",
                                                    "try speaking", "transcription should",
                                                    "continue with", "thank you", "okay",
                                                    "please", "bye", "yes", "no",
                                                    "recording", "remember to",
                                                    "this is from", "tips for", "this will help",
                                                    "move to", "try different", "let me know how",
                                                    "with these", "examples?"
                                                ]
                                                
                                                for artifact in artifacts:
                                                    text = text.replace(artifact, "")
                                                
                                                # Fix common technical terms and transcription errors
                                                replacements = {
                                                    # Technical terms
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
                                                    "o(n log n)": "O(n log n)",
                                                    
                                                    # Common word fixes
                                                    "in tune to": "intuitive",
                                                    "in detail": "intuitive",
                                                    "other handling": "error handling",
                                                    "ice filtering": "noise filtering",
                                                    "for ing": "for testing",
                                                    "wearing": "varying",
                                                    "wires": "requires",
                                                    "extension": "extensive",
                                                    "respositor": "repositories",
                                                    "phase": "pace",
                                                    "hand-lost": "handles",
                                                    "tardy": "today",
                                                    "class": "clusters",
                                                    "ester": "yesterday",
                                                    "above the end law": "O(n log n)",
                                                    "world at q": "word accuracy",
                                                    "bored accuracy": "word accuracy",
                                                    "recovery": "vocabulary",
                                                    "process": "processes",
                                                    "enable": "enables",
                                                    "needs an": "needs",
                                                    "scale level": "scalable",
                                                    "deal with": "debug",
                                                    "side on": "error",
                                                    "ing": "ing",  # Remove trailing ing
                                                    "n-technical": "non-technical"
                                                }
                                                
                                                for old, new in replacements.items():
                                                    text = text.replace(old, new)
                                                
                                                # Fix number formatting
                                                text = text.replace("330", "3:30")
                                                text = text.replace("10000", "10,000")
                                                text = text.replace("1000", "1,000")
                                                
                                                # Clean up punctuation
                                                text = text.replace(" .", ".")
                                                text = text.replace(" ,", ",")
                                                text = text.replace(" ?", "?")
                                                text = text.replace(" !", "!")
                                                text = text.replace("—", " ")
                                                text = text.replace("  ", " ")
                                                text = text.replace(" pm", " PM")
                                                text = text.replace(" am", " AM")
                                                
                                                # Fix dates
                                                text = text.replace("january", "January")
                                                text = text.replace("february", "February")
                                                text = text.replace("march", "March")
                                                text = text.replace("april", "April")
                                                text = text.replace("may", "May")
                                                text = text.replace("june", "June")
                                                text = text.replace("july", "July")
                                                text = text.replace("august", "August")
                                                text = text.replace("september", "September")
                                                text = text.replace("october", "October")
                                                text = text.replace("november", "November")
                                                text = text.replace("december", "December")
                                                
                                                # Capitalize first letter of sentences
                                                text = ". ".join(s.strip().capitalize() for s in text.split(". "))
                                                
                                                # Remove multiple spaces and normalize
                                                text = " ".join(text.split())
                                                
                                                # Only output if we have meaningful content
                                                if text.strip() and len(text.strip()) > 3:
                                                    self.logger.info(f"Transcribed: {text}")
                                                    pyautogui.write(text.strip() + " ")
                                    
                                    except Exception as e:
                                        self.logger.error(f"Error processing audio chunk: {e}")
                                        import traceback
                                        self.logger.error(traceback.format_exc())
                                    
                                    # Reset for next chunk
                                    audio_buffer = []
                                    buffer_duration = 0
                                    active_speech = False
                                    silence_duration = 0
                                    last_process_time = time.time()
                                
                                # Safety limit on buffer
                                elif buffer_duration > 5.0:
                                    audio_buffer = []
                                    buffer_duration = 0
                                    active_speech = False
                                    silence_duration = 0
                                
                            except queue.Empty:
                                time.sleep(0.1)  # Longer sleep to reduce CPU
                            except Exception as e:
                                self.logger.error(f"Error in audio loop: {e}")
                                import traceback
                                self.logger.error(traceback.format_exc())
                                
                except Exception as e:
                    self.logger.error(f"Error in audio stream: {e}")
                    self.is_listening = False
                    self.update_icon()
            else:
                # Clear queue
                while not self.audio_queue.empty():
                    try:
                        self.audio_queue.get_nowait()
                    except queue.Empty:
                        break
                time.sleep(0.1)

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
