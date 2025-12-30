# OpenAI Platform (Curated Offline Reference)

This folder is a **curated**, repo-local reference to the OpenAI Platform docs for the features used by this project, so you rarely need to search online.

- Canonical docs live on `https://platform.openai.com/docs`
- This folder focuses on: **Realtime voice**, **tool calling**, **model selection**, **retries/rate limits**, and **safety/logging**.

## What to read first
- `realtime.md`: how our Twilio Media Streams voice bridge maps to Realtime WebSocket events
- `responses_and_tools.md`: tool calling patterns + confirmation policy
- `models.md`: model selection (chat vs realtime vs audio)

## Project mapping (where the code lives)
- Voice bridge: `src/voice/realtime_bridge.py`
- Twilio webhooks: `src/api/webhooks/twilio_webhook.py`
- Tool planner/executor: `src/agent/assistant.py`
- Tool implementations: `src/agent/tools.py`
- Policy/confirmations: `src/security/policy.py`

## Official links we reference frequently
- Audio overview: `https://platform.openai.com/docs/guides/audio`
- Realtime guide: `https://platform.openai.com/docs/guides/realtime`
- Voice agents guide: `https://platform.openai.com/docs/guides/voice-agents`
- Responses guide: `https://platform.openai.com/docs/guides/responses`
- API reference: `https://platform.openai.com/docs/api-reference`

## Maintenance
When OpenAI changes APIs/models, update the affected file(s) and add a note under “Last verified” in that doc.


