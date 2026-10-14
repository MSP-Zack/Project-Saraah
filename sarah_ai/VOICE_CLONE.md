Voice Cloning Integration Guide

Overview

This document explains how to enable voice-cloning integration for Sarah AI. The codebase includes UI and backend scaffolding for registering user-uploaded samples and previewing them. Fully automated cloning requires a third-party provider (cloud or self-hosted).

Supported integration options (examples):

- Resemble.ai (cloud)
  - Pros: Production-grade voice cloning and TTS, REST API, simple flow to create voices from samples.
  - Cons: Paid service. Requires account and API keys.
  - How to integrate (high level):
    1. Sign up for Resemble.ai and create a project.
    2. Obtain an API key and (optionally) a project ID.
    3. Add environment variables to the server environment (or a config.json):
       - RESEMBLE_API_KEY=your_api_key_here
       - RESEMBLE_PROJECT_ID=your_project_id_here (optional)
    4. Implement provider adapter in `sarah_ai/core/` that uploads the stored sample to Resemble and creates a voice using their API.
    5. Update `sarah_ai/main.py` `/api/tts/clone` or create a new endpoint to call the adapter and store returned voice id in `tts_engine.custom_voices`.

- Coqui TTS / Open Source
  - Pros: Fully self-hostable and privacy-preserving.
  - Cons: Requires GPU and model installation; training/voice cloning can be resource-intensive.
  - How to integrate (high level):
    1. Stand up a Coqui inference / training server.
    2. Implement an adapter that POSTs the sample and receives a voice or model endpoint to call for synthesis.

Coqui integration (this repo)

- This repository includes a Coqui adapter at `sarah_ai/core/tts_providers/coqui.py` which
  expects an HTTP inference server reachable at the URL provided in the `COQUI_TTS_URL`
  environment variable (for example: `http://localhost:5002`).

- To enable automated cloning/synthesis using Coqui:
  1. Start a Coqui TTS inference server and ensure it exposes the following endpoints (or
     configure the adapter environment overrides):
       - `POST /synthesize` accepting JSON `{ "text": "...", "voice": "<voice_id>" }` and returning either binary audio (wav) or JSON with a base64 `audio` field.
       - `POST /voices` accepting a multipart form upload `file` and `name` and returning JSON containing an `id` or `voice_id` for the created speaker.
  2. Set `COQUI_TTS_URL` in the server environment (or in `config.json`) to the base URL (e.g. `http://127.0.0.1:5002`).
  3. Upload a sample via the Settings panel in the app — the server will schedule a background job to send the sample to the Coqui adapter and store the returned provider id in the custom voice metadata.
  4. Once processing completes the custom voice entry will have `provider: coqui` and `provider_id: <id>` and previews/synthesis will use the Coqui server.

Notes

- The Coqui HTTP API surface varies depending on how you deploy it. If your specific server uses different endpoints, set the environment variables `COQUI_TTS_SYNTH_ENDPOINT` and `COQUI_TTS_CREATE_VOICE_ENDPOINT` accordingly (they default to `/synthesize` and `/voices`).
- This adapter is intentionally forgiving: it supports binary audio responses as well as JSON responses containing base64 audio. If your inference server returns a different shape, adapt the adapter accordingly.

Provider-agnostic flow implemented in this repo

- Frontend: `app/src/components/SettingsPanel.tsx` supports:
  - Listing available voice profiles and registered custom voices (`/api/tts/voices`).
  - Uploading a short sample via `/api/tts/clone` (FormData: `display_name` + `file`).
  - Previewing voices via `/api/tts/preview?profile=...`.
  - Managing (delete/use) uploaded samples.

- Backend: `sarah_ai/main.py` implements endpoints:
  - `GET /api/tts/voices` — returns `voices`, `profiles`, `current`, `custom_voices`.
  - `GET /api/tts/preview?profile=...` — generates a short preview (uses local TTS or returns the uploaded sample for custom voices).
  - `POST /api/tts/clone` — accepts an uploaded sample and registers it as a custom voice (stores sample under `static/voices/samples/` and registers in `tts_engine`).
  - `DELETE /api/tts/custom/{id}` — removes a registered sample and metadata.
  - `GET /api/tts/providers` — lists supported provider keys for the UI.

Next steps to enable full cloning automation

1. Choose a provider (Resemble.ai is recommended for fast, high-quality cloning).
2. Implement an adapter module, e.g., `sarah_ai/core/tts_providers/resemble.py`, that:
   - Reads provider credentials from environment variables.
   - Uploads samples, creates voices (or triggers training), and returns a stable voice id.
   - Provides a `synthesize(text, voice_id)` function that returns an audio blob or file path.
3. Modify `POST /api/tts/clone` to trigger the adapter when provider credentials are present. Store the provider voice id as metadata in `tts_engine.custom_voices[custom_id]`.
4. Optionally: add background worker / queue (e.g., Celery or asyncio tasks) for long-running cloning jobs.

Security & Privacy

- Voice samples are user-provided audio clips. If using a cloud provider, ensure you have user consent to upload samples to third-party services.
- Consider encrypting stored samples at rest if privacy is a concern.

Troubleshooting

- If `/api/tts/preview` returns no audio, confirm `edge_tts` is installed and the server has outbound network access to any cloud TTS provider used.
- For self-hosted Coqui, verify the service is reachable and the adapter URLs are correctly configured.

Contact

If you want, I can integrate a specific provider (Resemble.ai or Coqui). Tell me which one and I'll implement the adapter and server-side flow (I will add environment variable handling and code to call the provider's API).