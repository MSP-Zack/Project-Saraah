"""Coqui TTS provider adapter.

This adapter expects a running Coqui TTS HTTP inference server reachable via
the `COQUI_TTS_URL` environment variable. It is intentionally tolerant: it
will attempt to handle either binary audio responses or JSON containing a
base64-encoded audio field.

See VOICE_CLONE.md for setup guidance.
"""
import os
import requests
import base64
import shutil


class CoquiAdapter:
    def __init__(self, base_url: str = None):
        self.base_url = (base_url or os.environ.get("COQUI_TTS_URL") or "").rstrip("/")
        # Endpoints can be customized via env
        self.synth_endpoint = os.environ.get("COQUI_TTS_SYNTH_ENDPOINT", "/synthesize")
        self.create_voice_endpoint = os.environ.get("COQUI_TTS_CREATE_VOICE_ENDPOINT", "/voices")

    def _full(self, path: str) -> str:
        if not self.base_url:
            raise RuntimeError("COQUI_TTS_URL is not configured")
        return f"{self.base_url}{path}"

    def synthesize_to_file(self, text: str, voice: str = None, output_path: str = "static/response_coqui.wav") -> str:
        """Synthesize `text` via the Coqui server and write to `output_path`.

        Returns the output_path on success or raises an exception.
        """
        if not self.base_url:
            raise RuntimeError("Coqui base URL not configured")

        url = self._full(self.synth_endpoint)
        payload = {"text": text}
        if voice:
            payload["voice"] = voice

        resp = requests.post(url, json=payload, timeout=60)
        if resp.status_code != 200:
            raise RuntimeError(f"Coqui synth failed: {resp.status_code} {resp.text}")

        content_type = resp.headers.get("Content-Type", "")
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        # If server returned binary audio
        if "audio" in content_type or resp.content and not content_type.startswith("application/json"):
            with open(output_path, "wb") as f:
                f.write(resp.content)
            return output_path

        # Otherwise expect JSON with a base64 'audio' field
        data = resp.json()
        b64 = None
        for k in ("audio", "wav", "pcm", "audio_base64"):
            if k in data:
                b64 = data[k]
                break

        if not b64:
            raise RuntimeError("Coqui synth returned unexpected JSON payload")

        audio_bytes = base64.b64decode(b64)
        with open(output_path, "wb") as f:
            f.write(audio_bytes)
        return output_path

    def create_voice_from_sample(self, sample_path: str, display_name: str = None) -> str:
        """Upload a sample to the Coqui server and request creation of a speaker/voice.

        Returns a provider voice id on success.
        """
        if not self.base_url:
            raise RuntimeError("Coqui base URL not configured")

        url = self._full(self.create_voice_endpoint)
        files = {"file": open(sample_path, "rb")}
        data = {"name": display_name or os.path.basename(sample_path)}
        try:
            resp = requests.post(url, files=files, data=data, timeout=120)
        finally:
            try:
                files["file"].close()
            except Exception:
                pass

        if resp.status_code not in (200, 201):
            raise RuntimeError(f"Coqui create voice failed: {resp.status_code} {resp.text}")

        j = resp.json()
        # Expecting returned JSON to include an id or voice identifier
        for key in ("id", "voice_id", "speaker_id", "name"):
            if key in j:
                return j[key]

        # Otherwise return the whole JSON as string fallback
        return str(j)
