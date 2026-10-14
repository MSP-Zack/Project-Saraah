import edge_tts
import asyncio
import os
import json
import sys
import threading
from pathlib import Path
from datetime import datetime
from typing import Optional

class TTSEngine:
    """
    Upgraded TTS engine with anime-style voice options.
    Supports multiple free voices, speed/pitch control,
    and voice preset profiles.
    """
    
    def __init__(self):
        # Voice presets for different vibes
        self.voices = {
            # Anime/Cute Japanese-English voices
            "sarah_cute": "ja-JP-NanamiNeural",  # Soft, cute anime girl
            "sarah_sweet": "en-US-AnaNeural",     # Sweet, young voice
            "sarah_gentle": "en-US-JennyNeural",  # Warm, feminine
            "sarah_energy": "en-US-AriaNeural",   # Energetic
            "sarah_shy": "en-GB-SoniaNeural",     # Soft British
            "sarah_tsun": "ja-JP-AoiNeural",      # Tsundere-style
        }
        
        self.current_voice = "sarah_cute"
        self.rate = "+10%"      # Speed (slower = cuter)
        self.pitch = "+5Hz"     # Slightly higher pitch
        self.volume = "+10%"    # Slightly louder
        
        self.profiles = {
            "default": {"voice": "sarah_cute", "rate": "+10%", "pitch": "+5Hz", "volume": "+10%"},
            "excited": {"voice": "sarah_energy", "rate": "+15%", "pitch": "+10Hz", "volume": "+15%"},
            "shy": {"voice": "sarah_shy", "rate": "+5%", "pitch": "+0Hz", "volume": "+5%"},
            "tsundere": {"voice": "sarah_tsun", "rate": "+12%", "pitch": "+8Hz", "volume": "+12%"},
            "gentle": {"voice": "sarah_gentle", "rate": "+8%", "pitch": "+3Hz", "volume": "+8%"},
        }

        # Custom/cloned voices uploaded by users
        # Format: { "custom_id": { "path": "/abs/path/to/sample.wav", "name": "User Voice" } }
        self.custom_voices = {}
        self.current_custom = None

        # Sarah's replies use the locally installed Kitten Micro model. Keep it
        # lazy so the rest of the app can still start if TTS assets are absent.
        self.kitten_voices = ["Bella", "Jasper", "Luna", "Bruno", "Rosie", "Hugo", "Kiki", "Leo"]
        self.kitten_default_voice = "Rosie"
        self._kitten_model = None
        self._kitten_load_lock = threading.Lock()
        self._kitten_inference_lock = threading.Lock()
        self._project_root = Path(__file__).resolve().parents[2]
        self._static_root = self._project_root / "sarah_ai" / "static"
        
        print(f"[SARAH THROAT]: Vocal cords initialized using {self.current_voice} profile.")
    
    def set_voice(self, voice_key: str):
        if voice_key in self.voices:
            self.current_voice = voice_key
            print(f"[SARAH THROAT]: Switched to {voice_key}")

    def set_custom_voice(self, custom_id: str):
        if custom_id in self.custom_voices:
            self.current_custom = custom_id
            self.current_voice = f"custom:{custom_id}"
            print(f"[SARAH THROAT]: Switched to custom voice {custom_id}")
    
    def set_profile(self, profile_name: str):
        if profile_name in self.profiles:
            p = self.profiles[profile_name]
            self.current_voice = p["voice"]
            self.rate = p["rate"]
            self.pitch = p["pitch"]
            self.volume = p["volume"]
            print(f"[SARAH THROAT]: Applied profile '{profile_name}'")
    
    async def speak_to_file(self, text: str, output_path: str = "static/response.mp3", emotion: str = None) -> str:
        """
        Convert text to anime-style speech and save to file.
        Returns the path to the generated audio.
        """
        # Select profile based on emotion hint
        if emotion:
            if "excited" in emotion.lower() or "happy" in emotion.lower():
                self.set_profile("excited")
            elif "shy" in emotion.lower() or "nervous" in emotion.lower():
                self.set_profile("shy")
            elif "angry" in emotion.lower() or "tsun" in emotion.lower():
                self.set_profile("tsundere")
            elif "gentle" in emotion.lower() or "calm" in emotion.lower():
                self.set_profile("gentle")
        
        # Clean text - remove actions and markdown
        clean_text = self._clean_text(text)
        
        # If a custom/cloned voice is selected, we currently fallback to the configured default
        # because real voice cloning/synthesis is not implemented here.
        if self.current_voice and isinstance(self.current_voice, str) and self.current_voice.startswith("custom:"):
            print(f"[SARAH THROAT]: Custom voice {self.current_voice} selected — voice-clone synthesis not available, falling back to profile voice.")
            voice_id = self.voices.get(self.profiles.get("default", {}).get("voice", "sarah_cute"), self.voices["sarah_cute"])
        else:
            voice_id = self.voices.get(self.current_voice, self.voices["sarah_cute"])
        
        try:
            communicate = edge_tts.Communicate(
                clean_text, 
                voice_id, 
                rate=self.rate,
                pitch=self.pitch,
                volume=self.volume
            )
            await communicate.save(output_path)
            
            # Restore default after speaking
            self.set_profile("default")
            
            return output_path
        except Exception as e:
            print(f"[SARAH THROAT]: TTS error: {e}")
            return None
    
    def _clean_text(self, text: str) -> str:
        """Remove action markers, asterisks, and markdown from text."""
        import re
        # Remove [ACTION: ...] and [EXPRESSION: ...] markers
        text = re.sub(r'\[ACTION:\s*[^\]]+\]', '', text)
        text = re.sub(r'\[EXPRESSION:\s*[^\]]+\]', '', text)
        # Remove asterisks (roleplay actions)
        text = text.replace('*', '')
        # Remove URLs
        text = re.sub(r'https?://\S+', 'link', text)
        # Remove markdown
        text = re.sub(r'[#*_`~]', '', text)
        return text.strip()
    
    def get_voice_list(self) -> dict:
        """Return available voices."""
        return {
            "voices": self.voices,
            "profiles": self.profiles,
            "current": self.current_voice,
            "custom_voices": self.custom_voices,
            "kitten_voices": self.kitten_voices,
            "kitten_default_voice": self.kitten_default_voice,
            "kitten_available": self._kitten_model_dir().is_dir(),
        }

    def _kitten_repo_dir(self) -> Path:
        configured = os.environ.get("KITTEN_TTS_SOURCE_DIR")
        if configured:
            return Path(configured).expanduser().resolve()
        return self._project_root.parent / "KittenTTS-0.8.1" / "KittenTTS-0.8.1"

    def _kitten_model_dir(self) -> Path:
        configured = os.environ.get("KITTEN_TTS_MICRO_MODEL_DIR")
        if configured:
            return Path(configured).expanduser().resolve()
        return self._kitten_repo_dir() / "models" / "micro-0.8"

    def _load_kitten_model(self):
        if self._kitten_model is not None:
            return self._kitten_model

        with self._kitten_load_lock:
            if self._kitten_model is not None:
                return self._kitten_model

            repo_dir = self._kitten_repo_dir()
            model_dir = self._kitten_model_dir()
            if not model_dir.is_dir():
                raise FileNotFoundError(
                    f"Kitten Micro model folder not found: {model_dir}. "
                    "Set KITTEN_TTS_MICRO_MODEL_DIR to the folder containing config.json."
                )

            # The project venv and the existing WinPython base interpreter use
            # the same Python build. Reuse its already-installed Kitten runtime
            # when those packages are not installed in the venv.
            base_site_packages = Path(sys.base_prefix) / "Lib" / "site-packages"
            if base_site_packages.is_dir() and str(base_site_packages) not in sys.path:
                sys.path.append(str(base_site_packages))
            if repo_dir.is_dir() and str(repo_dir) not in sys.path:
                sys.path.insert(0, str(repo_dir))

            from kittentts import KittenTTS

            self._kitten_model = KittenTTS(str(model_dir))
            return self._kitten_model

    def warm_kitten_model(self) -> bool:
        """Load and prime the local model before the first chat reply."""
        model = self._load_kitten_model()
        with self._kitten_inference_lock:
            model.generate(text="Hello.", voice=self.kitten_default_voice)
        return True

    @staticmethod
    def _split_for_stream(text: str, max_chars: int = 120) -> list[str]:
        """Make short speech chunks, preferring sentence boundaries."""
        import re

        sentences = re.split(r"(?<=[.!?;:])\s+|\n+", text)
        chunks = []
        for sentence in sentences:
            remaining = sentence.strip()
            while remaining:
                if len(remaining) <= max_chars:
                    chunks.append(remaining)
                    break
                split_at = remaining.rfind(" ", 0, max_chars + 1)
                if split_at < max_chars // 2:
                    split_at = max_chars
                chunks.append(remaining[:split_at].strip())
                remaining = remaining[split_at:].strip()
        return [chunk for chunk in chunks if chunk]

    def _synthesize_kitten_chunk(self, text: str, voice: str, output_path: Path) -> None:
        import soundfile as sf

        model = self._load_kitten_model()
        with self._kitten_inference_lock:
            audio = model.generate(text=text, voice=voice)
            sf.write(str(output_path), audio, 24000)

    async def stream_kitten_chunks(self, text: str, voice: str = "Rosie", speech_id: str = "speech"):
        """Yield a playable WAV as soon as each short Kitten chunk is ready."""
        clean_text = self._clean_text(text)
        selected_voice = voice if voice in self.kitten_voices else self.kitten_default_voice
        chunks = self._split_for_stream(clean_text)
        output_dir = self._static_root / "tts"
        output_dir.mkdir(parents=True, exist_ok=True)

        for index, chunk in enumerate(chunks):
            filename = f"{speech_id}-{index:03d}.wav"
            output_path = output_dir / filename
            await asyncio.to_thread(self._synthesize_kitten_chunk, chunk, selected_voice, output_path)
            yield {
                "sequence": index,
                "path": str(output_path),
                "url": f"/static/tts/{filename}",
            }
    
    async def preview_voice(self, voice_key: str, output_path: Optional[str] = None) -> str:
        """Generate a preview of a voice."""
        test_text = "Hello! I'm Sarah, your AI companion. How are you today?"
        if voice_key in self.kitten_voices:
            preview_path = self._static_root / "tts" / f"preview-{voice_key.lower()}.wav"
            preview_path.parent.mkdir(parents=True, exist_ok=True)
            await asyncio.to_thread(self._synthesize_kitten_chunk, test_text, voice_key, preview_path)
            return str(preview_path)

        preview_path = Path(output_path) if output_path else self._static_root / "preview.mp3"
        preview_path.parent.mkdir(parents=True, exist_ok=True)
        output_path = str(preview_path)

        # If previewing a custom/cloned voice, return the uploaded sample instead of synthesizing
        if voice_key and (voice_key.startswith("custom:") or voice_key in self.custom_voices):
            # Accept either 'custom:<id>' or '<id>'
            cid = voice_key.split(':', 1)[1] if voice_key.startswith('custom:') else voice_key
            entry = self.custom_voices.get(cid)
            if entry and os.path.exists(entry.get('path')):
                # If the custom entry is associated with a provider that supports synthesis,
                # try to synthesize a short preview using that provider. Otherwise copy sample.
                provider = entry.get('provider')
                provider_id = entry.get('provider_id')
                try:
                    if provider == 'coqui' and provider_id:
                        from core.tts_providers.coqui import CoquiAdapter
                        adapter = CoquiAdapter()
                        out = await asyncio.to_thread(adapter.synthesize_to_file, test_text, provider_id, output_path)
                        return out
                except Exception as e:
                    print(f"[SARAH THROAT]: Provider preview failed: {e}")

                # Fallback: copy uploaded sample so the frontend can play a consistent path
                try:
                    import shutil
                    os.makedirs(os.path.dirname(output_path), exist_ok=True)
                    shutil.copyfile(entry.get('path'), output_path)
                    return output_path
                except Exception as e:
                    print(f"[SARAH THROAT]: Failed to copy custom sample: {e}")

        voice_id = self.voices.get(voice_key, self.voices["sarah_cute"])
        communicate = edge_tts.Communicate(test_text, voice_id, rate=self.rate)
        await communicate.save(output_path)
        return output_path

    def add_custom_voice(self, custom_id: str, file_path: str, metadata: dict = None):
        """Register a custom voice sample. This does not perform cloning — it stores sample metadata."""
        metadata = metadata or {}
        entry = {
            "id": custom_id,
            "path": file_path,
            "name": metadata.get("name", custom_id),
            "status": metadata.get("status", "uploaded"),
            "created_at": metadata.get("created_at") or datetime.now().isoformat(),
            "provider": metadata.get("provider"),
            "provider_id": metadata.get("provider_id"),
            "note": metadata.get("note")
        }
        self.custom_voices[custom_id] = entry
        return entry

    def list_custom_voices(self) -> dict:
        return self.custom_voices

    def remove_custom_voice(self, custom_id: str) -> bool:
        """Remove a registered custom voice and delete the stored sample file."""
        entry = self.custom_voices.get(custom_id)
        if not entry:
            return False
        path = entry.get("path")
        try:
            if path and os.path.exists(path):
                os.remove(path)
            del self.custom_voices[custom_id]
            return True
        except Exception as e:
            print(f"[SARAH THROAT]: Failed to remove custom voice {custom_id}: {e}")
            return False
