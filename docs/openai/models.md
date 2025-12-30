# Models (Selection Guide) — Godfather Assistant

Last verified: 2025-12-28

## Canonical docs
- Models: `https://platform.openai.com/docs/models`
- Audio guide: `https://platform.openai.com/docs/guides/audio`
- Realtime guide: `https://platform.openai.com/docs/guides/realtime`

## What we use where

### Task planning + tool calling (text)
- Used by: `src/agent/assistant.py`
- Config: `OPENAI_MODEL` (defaults to `gpt-4o`)

Why:
- Reliable tool calling
- Great reasoning for multi-step tasks

### Voice-to-voice calls (realtime)
- Used by: `src/voice/realtime_bridge.py`
- Config: `OPENAI_REALTIME_MODEL` (defaults to `gpt-4o-realtime-preview`)

Why:
- Low latency
- Streaming audio in/out

### Transcription (if needed outside realtime)
If you later add async transcription of recordings, use the Audio transcription endpoints.\n
Reference: `https://platform.openai.com/docs/guides/speech-to-text`

## Practical guidance
- Prefer **Realtime** for live calls.\n
- Prefer **text model** for long “agentic” tasks that require structured planning and tool chains.\n
- Keep model names in env variables so you can swap without code changes.


