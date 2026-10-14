import asyncio
import numpy as np
import queue
import threading
import time
from typing import Optional, Callable, Dict, Any
from faster_whisper import WhisperModel
import webrtcvad
import collections
import audioop

class STTEngine:
    """
    Advanced Speech-to-Text engine with real-time conversation support.
    Features continuous listening, voice activity detection, interruption handling,
    and emotional tone analysis.
    """

    def __init__(self, model_size="base"):
        print("[SARAH STT]: Initializing advanced Whisper model...")
        self.model = WhisperModel(model_size, device="cpu", compute_type="int8")

        # Voice Activity Detection
        self.vad = webrtcvad.Vad(2)  # Aggressiveness level 0-3

        # Audio processing
        self.sample_rate = 16000
        self.channels = 1
        self.chunk_duration_ms = 30  # 30ms chunks for VAD
        self.chunk_size = int(self.sample_rate * self.chunk_duration_ms / 1000)

        # Conversation state
        self.is_listening = False
        self.is_speaking = False
        self.last_speech_time = 0
        self.silence_threshold = 0.5  # seconds
        self.interruption_detected = False

        # Audio buffers
        self.audio_queue = queue.Queue()
        self.speech_buffer = []
        self.silence_buffer = collections.deque(maxlen=50)  # Rolling silence detection

        # Callbacks
        self.on_transcription: Optional[Callable[[str, Dict[str, Any]], None]] = None
        self.on_interruption: Optional[Callable[[], None]] = None
        self.on_emotion_detected: Optional[Callable[[str], None]] = None

        # Processing thread
        self.processing_thread: Optional[threading.Thread] = None
        self.stop_processing = False

        print("[SARAH STT]: Advanced STT ready with real-time conversation support.")

    def start_continuous_listening(self):
        """Start continuous listening for voice input."""
        if self.is_listening:
            return

        self.is_listening = True
        self.stop_processing = False
        self.processing_thread = threading.Thread(target=self._processing_loop)
        self.processing_thread.daemon = True
        self.processing_thread.start()
        print("[SARAH STT]: Continuous listening started.")

    def stop_continuous_listening(self):
        """Stop continuous listening."""
        if not self.is_listening:
            return

        self.is_listening = False
        self.stop_processing = True
        if self.processing_thread:
            self.processing_thread.join(timeout=1.0)
        print("[SARAH STT]: Continuous listening stopped.")

    def add_audio_chunk(self, audio_data: bytes):
        """Add audio chunk from WebSocket stream."""
        if not self.is_listening:
            return

        # Convert to numpy array (assuming 16-bit PCM)
        audio_np = np.frombuffer(audio_data, dtype=np.int16).astype(np.float32) / 32768.0
        self.audio_queue.put(audio_np)

    def _processing_loop(self):
        """Main processing loop for real-time STT."""
        while not self.stop_processing:
            try:
                # Get audio chunk with timeout
                try:
                    audio_chunk = self.audio_queue.get(timeout=0.1)
                except queue.Empty:
                    continue

                # Process chunk for VAD
                vad_result = self._process_vad(audio_chunk)

                if vad_result["speech_detected"]:
                    self._handle_speech(audio_chunk, vad_result)
                else:
                    self._handle_silence(vad_result)

            except Exception as e:
                print(f"[SARAH STT]: Processing error: {e}")
                time.sleep(0.1)

    def _process_vad(self, audio_chunk: np.ndarray) -> Dict[str, Any]:
        """Process audio chunk with Voice Activity Detection."""
        # Convert to 16-bit PCM for VAD
        audio_16bit = (audio_chunk * 32767).astype(np.int16).tobytes()

        # Split into VAD-sized chunks
        results = []
        for i in range(0, len(audio_16bit), self.chunk_size * 2):  # *2 for 16-bit
            chunk = audio_16bit[i:i + self.chunk_size * 2]
            if len(chunk) == self.chunk_size * 2:
                try:
                    is_speech = self.vad.is_speech(chunk, self.sample_rate)
                    results.append(is_speech)
                except:
                    results.append(False)

        speech_ratio = sum(results) / len(results) if results else 0

        # Calculate audio energy for additional speech detection
        energy = audioop.rms(audio_16bit, 2) / 32767.0

        # Emotional tone analysis (basic)
        emotion_hints = self._analyze_emotion(audio_chunk)

        return {
            "speech_detected": speech_ratio > 0.3 or energy > 0.01,
            "speech_ratio": speech_ratio,
            "energy": energy,
            "emotion_hints": emotion_hints
        }

    def _handle_speech(self, audio_chunk: np.ndarray, vad_result: Dict[str, Any]):
        """Handle detected speech."""
        current_time = time.time()

        # Check for interruption (sudden speech while AI is speaking)
        if self.is_speaking and (current_time - self.last_speech_time) > 1.0:
            self.interruption_detected = True
            if self.on_interruption:
                asyncio.run(self.on_interruption())
            print("[SARAH STT]: User interruption detected!")

        self.last_speech_time = current_time
        self.speech_buffer.append(audio_chunk)

        # Clear silence buffer
        self.silence_buffer.clear()

        # Analyze emotion
        if vad_result["emotion_hints"] and self.on_emotion_detected:
            self.on_emotion_detected(vad_result["emotion_hints"])

    def _handle_silence(self, vad_result: Dict[str, Any]):
        """Handle silence periods."""
        self.silence_buffer.append(vad_result["energy"])

        # Check if speech has ended
        if len(self.speech_buffer) > 0:
            avg_silence = sum(self.silence_buffer) / len(self.silence_buffer)

            if avg_silence < 0.005 and len(self.silence_buffer) >= 10:  # ~300ms silence
                # Process accumulated speech
                self._process_speech_buffer()
                self.speech_buffer = []
                self.silence_buffer.clear()

    def _process_speech_buffer(self):
        """Process accumulated speech buffer for transcription."""
        if not self.speech_buffer:
            return

        # Concatenate audio chunks
        audio_data = np.concatenate(self.speech_buffer)

        try:
            # Transcribe
            segments, info = self.model.transcribe(
                audio_data,
                beam_size=5,
                vad_filter=True,
                language="en"
            )

            transcription = "".join([segment.text for segment in segments]).strip()

            if transcription and self.on_transcription:
                # Analyze final emotion and confidence
                emotion_analysis = self._analyze_emotion(audio_data)
                confidence = info.language_probability if hasattr(info, 'language_probability') else 0.8

                metadata = {
                    "confidence": confidence,
                    "emotion": emotion_analysis,
                    "interrupted": self.interruption_detected,
                    "duration": len(audio_data) / self.sample_rate
                }

                self.on_transcription(transcription, metadata)
                self.interruption_detected = False

        except Exception as e:
            print(f"[SARAH STT]: Transcription error: {e}")

    def _analyze_emotion(self, audio_data: np.ndarray) -> str:
        """Basic emotional tone analysis from audio features."""
        # Calculate basic audio features
        energy = np.mean(np.abs(audio_data))
        pitch_variation = np.std(audio_data) / (np.mean(np.abs(audio_data)) + 1e-6)
        speech_rate = len(audio_data) / self.sample_rate  # rough estimate

        # Simple emotion classification based on features
        if energy > 0.1 and pitch_variation > 0.8:
            return "excited"
        elif energy < 0.03:
            return "calm"
        elif pitch_variation > 1.2:
            return "angry"
        elif energy > 0.08:
            return "loud"
        else:
            return "neutral"

    def set_speaking_state(self, is_speaking: bool):
        """Set whether AI is currently speaking (for interruption detection)."""
        self.is_speaking = is_speaking

    def transcribe_audio(self, audio_data: np.ndarray) -> str:
        """Legacy method for batch transcription."""
        segments, info = self.model.transcribe(audio_data, beam_size=5, vad_filter=True)
        text = "".join([segment.text for segment in segments])
        return text.strip()

    def transcribe_file(self, file_path: str) -> str:
        """Transcribe an audio file."""
        segments, info = self.model.transcribe(file_path, beam_size=5)
        text = "".join([segment.text for segment in segments])
        return text.strip()