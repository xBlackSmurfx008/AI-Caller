# Realtime API (Voice-to-Voice) — How We Use It

Last verified: 2025-12-28

## What we use Realtime for
We use the **Realtime WebSocket** API to power **low-latency speech-to-speech** for inbound (and later outbound) phone calls.

In this repo, the bridge is implemented in:
- `src/voice/realtime_bridge.py`
- `src/api/webhooks/twilio_webhook.py` (Twilio Media Streams → WebSocket endpoint)

## Canonical docs
- Realtime guide: `https://platform.openai.com/docs/guides/realtime`
- Realtime API reference: `https://platform.openai.com/docs/api-reference/realtime`
- Voice agents guide: `https://platform.openai.com/docs/guides/voice-agents`

## Connection basics (WebSocket)
Our bridge connects like this:
- Header: `Authorization: Bearer $OPENAI_API_KEY`
- Header: `OpenAI-Beta: realtime=v1`
- URL: `wss://api.openai.com/v1/realtime?model=...`

In code:
- `src/voice/realtime_bridge.py` → `RealtimeCallBridge.start()`

## Session configuration (`session.update`)
We send `session.update` immediately after connecting to configure:
- `modalities`: `["audio","text"]`
- `voice`: e.g. `alloy`
- `turn_detection`: `server_vad` (server-side VAD)
- `input_audio_format` / `output_audio_format`: `pcm16`
- `input_audio_transcription`: `whisper-1` (for transcripts)

This matches the pattern in:
- `OPENAI_VOICE_DOCUMENTATION.md` (project reference)
- `src/voice/realtime_bridge.py`

## Audio format mapping (Twilio ↔ OpenAI)
Twilio Media Streams audio arrives as:
- 8kHz µ-law frames (we decode to **PCM16 @ 8kHz**) inside `src/telephony/media_stream.py`

OpenAI Realtime typically uses:
- **PCM16 @ 24kHz**

So we:
- Upsample 8kHz → 24kHz before sending to OpenAI
- Downsample 24kHz → 8kHz before sending back to Twilio

Code:
- `src/voice/realtime_bridge.py` (`_pcm16_resample_x3`, `_pcm16_resample_div3`)

## Events we rely on (minimal set)
We currently use:
- Client → server:
  - `session.update`
  - `input_audio_buffer.append`
  - `input_audio_buffer.commit`
- Server → client:
  - `conversation.item.input_audio_transcription.completed`
  - `response.audio.delta`

## Tool calling in Realtime (planned)
For v1 we implemented tool calling in **chat/function-calling** mode (`src/agent/assistant.py`), and we will enable Realtime tool calling by attaching `tools` to `session.update` and handling tool call events.

When we enable it, the policy rule remains:
- If the tool is “high risk” (call/SMS/email/calendar), require a **confirmation turn** (Godfather only).

Policy code:
- `src/security/policy.py`


