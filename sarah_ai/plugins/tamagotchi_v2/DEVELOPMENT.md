# Tamagotchi v2 Development Notes

This document tracks how to run and test the plugin locally.

Smoke test:

```bash
python3 sarah_ai/plugins/tamagotchi_v2/_smoke_test.py
python3 sarah_ai/plugins/tamagotchi_v2/_smoke_test2.py
```

Front-end preview (in dev server):

1. Start the Vite dev server in `app/`:

```bash
cd app
npm install
npm run dev
```

2. Open the app and navigate to the Tamagotchi Game panel (or import `TamagotchiGame` into `App.tsx`).
