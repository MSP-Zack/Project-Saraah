# Project Saraah

Project Saraah runs a FastAPI backend and a React/Vite frontend. The backend serves the latest frontend build from `sarah_ai/static/`.

## Local Windows setup

Use Python 3.12. The project environment is `.venv`; in PyCharm, select the existing interpreter at `.venv\Scripts\python.exe`.

The backend dependencies are pinned in the root `requirements.txt`. From the project root, install them with:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Copy `.env.example` to `.env` and add your `GEMINI_API_KEY` if you want chat generation. The server loads `.env` from the project root. `HUGGINGFACE_API_KEY` is optional.

Sarah's chat speech uses the local Kitten TTS Micro model with Rosie selected by default. This checkout looks for the existing Kitten TTS source and model in the sibling `..\KittenTTS-0.8.1\KittenTTS-0.8.1` folder and reuses Kitten's dependencies from the WinPython installation that created `.venv`. If those folders are elsewhere, set `KITTEN_TTS_SOURCE_DIR` and/or `KITTEN_TTS_MICRO_MODEL_DIR` in `.env`; the model folder must contain `config.json`, its ONNX model, and `voices.npz`. Chat audio is generated in short chunks so Sarah can begin speaking before the rest is synthesized.

## Run the backend

Run from the project root so memory and configuration paths resolve consistently:

```powershell
.\.venv\Scripts\python.exe .\sarah_ai\main.py
```

Open <http://127.0.0.1:8000>. `0.0.0.0` is the server's listen address and cannot be opened directly in a browser; use `127.0.0.1` or `localhost`.

Voice recognition initializes the Faster-Whisper base model at startup and may download it on the first run. If that optional model is unavailable, the server logs the STT failure and continues without voice recognition.

## Frontend development

Node.js and npm are needed only when editing the React frontend. In one terminal, run the backend as above. In a second terminal:

```powershell
cd app
npm ci
npm run dev
```

Open <http://localhost:3000>. Vite proxies `/api` and `/ws` to the backend on port 8000. `npm run build` writes the UI bundle into `sarah_ai/static/` and preserves the VRM models and other static assets.

The file-driven VRM animation/emotion area is still a demo. It can look incomplete until its animation and emotion files are added.
