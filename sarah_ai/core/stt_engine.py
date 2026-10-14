from faster_whisper import WhisperModel
import numpy as np

class STTEngine:
    """
    Speech-to-Text engine using faster-whisper.
    Optimized for real-time transcription with minimal latency.
    """
    
    def __init__(self, model_size="base"):
        print("[SARAH STT]: Initializing Whisper model...")
        self.model = WhisperModel(model_size, device="cpu", compute_type="int8")
        print("[SARAH STT]: Ready to listen.")
    
    def transcribe_audio(self, audio_data: np.ndarray) -> str:
        """
        Transcribe audio data to text.
        audio_data: numpy array of float32 audio samples
        """
        segments, info = self.model.transcribe(audio_data, beam_size=5, vad_filter=True)
        text = "".join([segment.text for segment in segments])
        return text.strip()
    
    def transcribe_file(self, file_path: str) -> str:
        """Transcribe an audio file."""
        segments, info = self.model.transcribe(file_path, beam_size=5)
        text = "".join([segment.text for segment in segments])
        return text.strip()
