# OpenAI Voice API Documentation

Comprehensive documentation for OpenAI's voice capabilities, including Realtime API, Text-to-Speech (TTS), and Speech-to-Text (STT) integration in the AI Caller project.

## Table of Contents

1. [Overview](#overview)
2. [Realtime API](#realtime-api)
3. [Text-to-Speech (TTS) API](#text-to-speech-tts-api)
4. [Speech-to-Text (STT) API](#speech-to-text-stt-api)
5. [Available Voices](#available-voices)
6. [Audio Formats](#audio-formats)
7. [Configuration](#configuration)
8. [Integration Examples](#integration-examples)
9. [Best Practices](#best-practices)
10. [Error Handling](#error-handling)
11. [Resources](#resources)

---

## Overview

OpenAI provides three main voice APIs for building voice-enabled applications:

1. **Realtime API**: Low-latency, streaming voice-to-voice interactions for real-time conversations
2. **Text-to-Speech (TTS) API**: Convert text into natural-sounding speech
3. **Speech-to-Text (STT) API**: Transcribe audio into text with high accuracy

### Use Cases

- **Voice Agents**: Interactive assistants that can speak and listen in real-time
- **Call Centers**: Automated customer service with natural voice interactions
- **Accessibility**: Text-to-speech for visually impaired users
- **Transcription**: Meeting notes, call recordings, and audio content indexing
- **Content Creation**: Voiceovers, narrations, and multilingual content

---

## Realtime API

The Realtime API enables low-latency, bidirectional voice conversations through WebSocket connections. It's ideal for building voice agents that require immediate responses.

### Key Features

- **Low Latency**: Streaming audio input/output for real-time interactions
- **Speech-to-Speech**: Direct audio-to-audio processing without intermediate text
- **Function Calling**: Execute tools and actions during conversations
- **Voice Activity Detection (VAD)**: Automatic turn detection
- **Multimodal**: Support for audio and text modalities
- **Custom Instructions**: Configure assistant behavior and personality

### Models

- `gpt-4o-realtime-preview`: Original preview model (currently used in this project)
- `gpt-realtime`: Latest production-ready model with improved naturalness and expressiveness

### Connection

```python
# WebSocket connection to Realtime API
headers = {
    "Authorization": f"Bearer {OPENAI_API_KEY}",
    "OpenAI-Beta": "realtime=v1",
}
uri = f"wss://api.openai.com/v1/realtime?model={model}"
ws = await websockets.connect(uri, extra_headers=headers)
```

### Session Configuration

The session is configured using the `session.update` event:

```json
{
  "type": "session.update",
  "session": {
    "modalities": ["audio", "text"],
    "instructions": "You are a helpful voice assistant...",
    "voice": "alloy",
    "input_audio_format": "pcm16",
    "output_audio_format": "pcm16",
    "turn_detection": {
      "type": "server_vad",
      "threshold": 0.5,
      "prefix_padding_ms": 300,
      "silence_duration_ms": 500
    },
    "input_audio_transcription": {
      "model": "whisper-1"
    }
  }
}
```

### Session Parameters

#### Modalities
- `["audio"]`: Audio-only mode
- `["text"]`: Text-only mode
- `["audio", "text"]`: Both audio and text (recommended)

#### Voice Options
See [Available Voices](#available-voices) section for complete list.

#### Audio Formats
- **Input**: `pcm16`, `g711_ulaw`, `g711_alaw`
- **Output**: `pcm16`, `g711_ulaw`, `g711_alaw`

**Note**: This project uses `pcm16` for both input and output. Twilio provides 8kHz PCM16, while OpenAI Realtime API expects 24kHz PCM16, requiring resampling.

#### Turn Detection (VAD)

**Server VAD** (Recommended):
```json
{
  "type": "server_vad",
  "threshold": 0.5,           // Sensitivity (0.0-1.0)
  "prefix_padding_ms": 300,    // Audio before speech start
  "silence_duration_ms": 500   // Silence before turn end
}
```

**Client VAD**:
```json
{
  "type": "client_vad",
  "threshold": 0.5
}
```

### Audio Input/Output

#### Sending Audio to OpenAI

```python
# Resample from 8kHz (Twilio) to 24kHz (OpenAI)
pcm16_24k = resample_8k_to_24k(pcm16_8k)
audio_b64 = base64.b64encode(pcm16_24k).decode("utf-8")

# Send audio buffer
await ws.send(json.dumps({
    "type": "input_audio_buffer.append",
    "audio": audio_b64
}))

# Commit the buffer
await ws.send(json.dumps({
    "type": "input_audio_buffer.commit"
}))
```

#### Receiving Audio from OpenAI

```python
# Listen for response.audio.delta events
async for message in ws:
    event = json.loads(message)
    
    if event.get("type") == "response.audio.delta":
        # Decode base64 audio (24kHz PCM16)
        audio_24k = base64.b64decode(event.get("delta"))
        
        # Resample to 8kHz for Twilio
        audio_8k = resample_24k_to_8k(audio_24k)
        # Send to Twilio Media Stream
```

### Event Types

#### Client → Server Events

- `session.update`: Configure session settings
- `input_audio_buffer.append`: Add audio to input buffer
- `input_audio_buffer.commit`: Process buffered audio
- `input_audio_buffer.clear`: Clear input buffer
- `response.create`: Start a new response
- `response.cancel`: Cancel current response
- `conversation.item.create`: Create conversation item
- `item.input_audio_transcription.create`: Request transcription

#### Server → Client Events

- `session.created`: Session initialized
- `session.updated`: Session configuration updated
- `response.audio.delta`: Streaming audio chunks
- `response.audio_transcript.delta`: Streaming transcript chunks
- `response.audio_transcript.done`: Transcription complete
- `conversation.item.input_audio_transcription.completed`: User speech transcribed
- `conversation.item.output_audio_transcription.completed`: Assistant speech transcribed
- `error`: Error occurred

### Transcription Events

The Realtime API can transcribe both user and assistant speech:

```python
# User speech transcription
if event.get("type") == "conversation.item.input_audio_transcription.completed":
    user_transcript = event.get("transcript", "").strip()
    # Process user transcript

# Assistant speech transcription  
if event.get("type") == "conversation.item.output_audio_transcription.completed":
    assistant_transcript = event.get("transcript", "").strip()
    # Process assistant transcript
```

### Function Calling

The Realtime API supports function calling during conversations. Tools can be defined in the session configuration:

#### Enabling Tools

Tools are enabled in the `session.update` event:

```python
await self._send(ws, {
    "type": "session.update",
    "session": {
        "modalities": ["audio", "text"],
        "instructions": instructions,
        "voice": "alloy",
        "input_audio_format": "pcm16",
        "output_audio_format": "pcm16",
        "tools": [
            {
                "type": "function",
                "name": "make_call",
                "description": "Make a phone call to a contact",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "to_number": {
                            "type": "string",
                            "description": "Phone number in E.164 format (e.g., +15551234567)"
                        }
                    },
                    "required": ["to_number"]
                }
            }
        ]
    }
})
```

#### Tool Call Events

When the model wants to call a tool, it sends a `conversation.item.requires_action` event:

```json
{
    "type": "conversation.item.requires_action",
    "item": {
        "id": "item_abc123",
        "type": "message",
        "required_action": {
            "type": "submit_tool_outputs",
            "submit_tool_outputs": {
                "tool_calls": [
                    {
                        "id": "call_xyz789",
                        "type": "function",
                        "name": "make_call",
                        "parameters": {
                            "to_number": "+15551234567"
                        }
                    }
                ]
            }
        }
    }
}
```

#### Handling Tool Calls with Security Policy

```python
async def _listen(self, call_sid: str) -> None:
    st = self._sessions.get(call_sid)
    if not st:
        return
    ws = st.ws
    
    try:
        async for msg in ws:
            event = json.loads(msg)
            et = event.get("type")
            
            if et == "conversation.item.requires_action":
                # Tool call requested
                item = event.get("item", {})
                required_action = item.get("required_action", {})
                tool_calls = required_action.get("submit_tool_outputs", {}).get("tool_calls", [])
                
                for tool_call in tool_calls:
                    tool_name = tool_call.get("name")
                    tool_args = tool_call.get("parameters", {})
                    tool_call_id = tool_call.get("id")
                    
                    # Check security policy
                    from src.security.policy import decide_confirmation, PlannedToolCall
                    planned = PlannedToolCall(name=tool_name, arguments=tool_args)
                    decision = decide_confirmation(st.actor, [planned])
                    
                    if decision.requires_confirmation:
                        # Ask for confirmation via voice
                        await self._send(ws, {
                            "type": "response.create",
                            "response": {
                                "modalities": ["audio", "text"],
                                "instructions": f"Ask user to confirm: Should I {tool_name} with {tool_args}?"
                            }
                        })
                        # Store pending tool call
                        st.pending_tool_call = {
                            "item_id": item.get("id"),
                            "tool_call_id": tool_call_id,
                            "tool_name": tool_name,
                            "tool_args": tool_args
                        }
                    else:
                        # Execute tool immediately (low-risk)
                        from src.agent.tools import TOOL_HANDLERS
                        result = await TOOL_HANDLERS[tool_name](**tool_args)
                        
                        # Submit result
                        await self._send(ws, {
                            "type": "conversation.item.required_action.submit_tool_outputs",
                            "item_id": item.get("id"),
                            "tool_outputs": [{
                                "tool_call_id": tool_call_id,
                                "output": json.dumps(result)
                            }]
                        })
            
            elif et == "conversation.item.input_audio_transcription.completed":
                # Check if user confirmed
                transcript = (event.get("transcript") or "").strip().lower()
                if transcript in {"yes", "confirm", "approve", "go ahead"}:
                    st.last_confirmed = True
                    
                    # Execute pending tool call if exists
                    if hasattr(st, 'pending_tool_call') and st.pending_tool_call:
                        pending = st.pending_tool_call
                        from src.agent.tools import TOOL_HANDLERS
                        result = await TOOL_HANDLERS[pending["tool_name"]](**pending["tool_args"])
                        
                        await self._send(ws, {
                            "type": "conversation.item.required_action.submit_tool_outputs",
                            "item_id": pending["item_id"],
                            "tool_outputs": [{
                                "tool_call_id": pending["tool_call_id"],
                                "output": json.dumps(result)
                            }]
                        })
                        st.pending_tool_call = None
```

#### Confirmation Flow

1. **Model Requests Tool**: Sends `conversation.item.requires_action` event
2. **Policy Check**: System checks `decide_confirmation()` for risk level
3. **High-Risk Tools**: Model asks user: "Should I call John at 555-1234?"
4. **User Confirms**: User says "Yes" or "Confirm"
5. **Confirmation Detected**: System detects confirmation in transcript
6. **Tool Executed**: Tool is executed and result submitted
7. **Model Responds**: Model acknowledges result and continues conversation

#### Security Policy Integration

The Realtime API respects the security policy defined in `src/security/policy.py`:

- **High-Risk Tools**: `make_call`, `send_sms`, `send_email`, `calendar_create_event` require confirmation
- **Low-Risk Tools**: `web_research` can auto-execute
- **Godfather Only**: Only authorized users can execute high-risk tools
- **External Callers**: Cannot execute high-risk tools, must take message

See [Security Policy Integration](#security-policy-integration) section for details.

```json
{
  "type": "session.update",
  "session": {
    "tools": [
      {
        "type": "function",
        "name": "make_call",
        "description": "Make a phone call",
        "parameters": {
          "type": "object",
          "properties": {
            "phone_number": {
              "type": "string",
              "description": "Phone number to call"
            }
          }
        }
      }
    ]
  }
}
```

---

## Text-to-Speech (TTS) API

The TTS API converts text into natural-sounding speech. It's useful for generating pre-recorded messages, voiceovers, and non-real-time voice output.

### Models

- `tts-1`: Standard TTS model
- `tts-1-hd`: High-definition TTS model (better quality, slower)
- `gpt-4o-mini-tts`: Latest model with enhanced steerability

### API Endpoint

```
POST https://api.openai.com/v1/audio/speech
```

### Request Format

```python
from openai import OpenAI

client = OpenAI(api_key=OPENAI_API_KEY)

response = client.audio.speech.create(
    model="tts-1",
    voice="alloy",
    input="Hello, this is a test of the text-to-speech API.",
    response_format="mp3",
    speed=1.0
)
```

### Parameters

- **model**: `tts-1`, `tts-1-hd`, or `gpt-4o-mini-tts`
- **voice**: See [Available Voices](#available-voices)
- **input**: Text to convert (max 4096 characters)
- **response_format**: `mp3`, `opus`, `aac`, `flac`, `wav`, or `pcm`
- **speed**: Speech speed (0.25 to 4.0, default 1.0)

### Steerability (gpt-4o-mini-tts)

The `gpt-4o-mini-tts` model supports instruction-based voice customization:

```python
response = client.audio.speech.create(
    model="gpt-4o-mini-tts",
    voice="alloy",
    input="Hello, how can I help you today?",
    instructions="Speak like a sympathetic customer service agent with a warm, friendly tone."
)
```

### Response

The API returns binary audio data:

```python
# Save to file
with open("output.mp3", "wb") as f:
    f.write(response.content)

# Stream to client
return Response(content=response.content, media_type="audio/mpeg")
```

---

## Speech-to-Text (STT) API

The STT API transcribes audio into text with high accuracy. It supports multiple languages and handles challenging scenarios like accents and background noise.

### Models

- `whisper-1`: Original Whisper model
- `gpt-4o-transcribe`: Latest model with improved accuracy
- `gpt-4o-mini-transcribe`: Faster, more cost-effective option
- `gpt-4o-transcribe-diarize`: Includes speaker labels and timestamps

### API Endpoint

```
POST https://api.openai.com/v1/audio/transcriptions
```

### Request Format

```python
from openai import OpenAI

client = OpenAI(api_key=OPENAI_API_KEY)

with open("audio.mp3", "rb") as audio_file:
    transcript = client.audio.transcriptions.create(
        model="whisper-1",
        file=audio_file,
        language="en",
        response_format="json",
        temperature=0.0
    )
```

### Parameters

- **model**: `whisper-1`, `gpt-4o-transcribe`, `gpt-4o-mini-transcribe`, or `gpt-4o-transcribe-diarize`
- **file**: Audio file (mp3, mp4, mpeg, mpga, m4a, wav, webm)
- **language**: Language code (optional, auto-detected if not specified)
- **response_format**: `json`, `text`, `srt`, `verbose_json`, or `vtt`
- **temperature**: Randomness (0.0-1.0, default 0.0)
- **prompt**: Optional text prompt to guide transcription

### Supported Languages

The STT models support 99+ languages including:

- English (en)
- Spanish (es)
- French (fr)
- German (de)
- Chinese (zh)
- Japanese (ja)
- Arabic (ar)
- Hindi (hi)
- Russian (ru)
- Portuguese (pt)
- And many more...

### Diarization (Speaker Labels)

The `gpt-4o-transcribe-diarize` model adds speaker identification:

```python
transcript = client.audio.transcriptions.create(
    model="gpt-4o-transcribe-diarize",
    file=audio_file,
    response_format="verbose_json"
)

# Response includes speaker labels and timestamps
# {
#   "text": "...",
#   "segments": [
#     {
#       "speaker": "SPEAKER_00",
#       "start": 0.0,
#       "end": 2.5,
#       "text": "Hello, how are you?"
#     },
#     ...
#   ]
# }
```

### Response Formats

- **json**: `{"text": "transcribed text"}`
- **text**: Plain text string
- **srt**: SubRip subtitle format
- **verbose_json**: Detailed JSON with segments, timestamps, etc.
- **vtt**: WebVTT subtitle format

---

## Available Voices

OpenAI provides multiple pre-built voices for TTS and Realtime API:

### Standard Voices (Available in TTS and Realtime)

1. **alloy** - Neutral, balanced voice (default in this project)
2. **echo** - Clear, professional voice
3. **fable** - Warm, friendly voice
4. **onyx** - Deep, authoritative voice
5. **nova** - Bright, energetic voice
6. **shimmer** - Soft, gentle voice

### Realtime-Exclusive Voices

7. **cedar** - New voice, exclusive to Realtime API
8. **marin** - New voice, exclusive to Realtime API

### Voice Selection

```python
# In configuration
OPENAI_REALTIME_VOICE: str = "alloy"  # Default

# Or in session.update
{
  "session": {
    "voice": "nova"  # Choose any available voice
  }
}
```

### Custom Voices

OpenAI offers custom voice creation for eligible customers:

- Provide a short audio sample (15-30 seconds)
- Voice must be from a consenting voice actor
- Available across TTS, Realtime, and Chat Completions APIs
- Contact OpenAI sales for access

---

## Audio Formats

### Supported Input Formats (STT)

- MP3
- MP4
- MPEG
- MPGA
- M4A
- WAV
- WEBM

**Maximum file size**: 25 MB

### Supported Output Formats (TTS)

- **mp3** (default): Good quality, widely compatible
- **opus**: High quality, efficient compression
- **aac**: Good quality, Apple ecosystem
- **flac**: Lossless, large file size
- **wav**: Uncompressed, high quality
- **pcm**: Raw PCM data, low latency

### Audio Specifications

#### Realtime API
- **Input**: PCM16, 24kHz (typical)
- **Output**: PCM16, 24kHz (typical)
- **Sample Rate Conversion**: Required when bridging with Twilio (8kHz)

#### Twilio Media Streams
- **Format**: PCM16, 8kHz
- **Encoding**: µ-law (decoded to PCM16 in this project)

### Resampling

This project includes resampling functions to convert between 8kHz (Twilio) and 24kHz (OpenAI):

```python
# 8kHz → 24kHz (upsampling by factor of 3)
def resample_8k_to_24k(pcm16_8k: bytes) -> bytes:
    # Linear interpolation between samples
    # [s0, s1, s2] → [s0, s0+(s1-s0)/3, s0+2(s1-s0)/3, s1, ...]

# 24kHz → 8kHz (downsampling by factor of 3)
def resample_24k_to_8k(pcm16_24k: bytes) -> bytes:
    # Take every 3rd sample
    # [s0, s1, s2, s3, s4, s5] → [s0, s3]
```

---

## Configuration

### Environment Variables

```bash
# Required
OPENAI_API_KEY=sk-...

# Optional (with defaults)
OPENAI_MODEL=gpt-4o                          # For chat completions
OPENAI_REALTIME_API_URL=wss://api.openai.com/v1/realtime
OPENAI_REALTIME_MODEL=gpt-4o-realtime-preview
OPENAI_REALTIME_VOICE=alloy
```

### Configuration in Code

```python
from src.utils.config import get_settings

settings = get_settings()

# Access configuration
api_key = settings.OPENAI_API_KEY
model = settings.OPENAI_REALTIME_MODEL
voice = settings.OPENAI_REALTIME_VOICE
```

### Session Instructions

Customize assistant behavior with instructions:

```python
instructions = (
    "You are Godfather's voice assistant. Speak naturally and concisely.\n"
    "You may propose actions like calling, texting, emailing, scheduling, and web research.\n"
    "Before using any tool that contacts someone or changes the calendar, ask for explicit confirmation.\n"
    "If the caller is not Godfather, do not perform high-risk actions; instead take a message."
)
```

---

## Integration Examples

### Example 1: Realtime Voice Bridge

This project implements a bridge between Twilio Media Streams and OpenAI Realtime API:

```python
# src/voice/realtime_bridge.py

class RealtimeCallBridge:
    async def start(self, call_sid: str, actor: Actor) -> None:
        # Connect to OpenAI Realtime API
        headers = {
            "Authorization": f"Bearer {settings.OPENAI_API_KEY}",
            "OpenAI-Beta": "realtime=v1",
        }
        uri = f"{settings.OPENAI_REALTIME_API_URL}?model={model}"
        ws = await websockets.connect(uri, extra_headers=headers)
        
        # Configure session
        await self._send(ws, {
            "type": "session.update",
            "session": {
                "modalities": ["audio", "text"],
                "instructions": instructions,
                "voice": settings.OPENAI_REALTIME_VOICE,
                "input_audio_format": "pcm16",
                "output_audio_format": "pcm16",
                "turn_detection": {
                    "type": "server_vad",
                    "threshold": 0.5,
                    "prefix_padding_ms": 300,
                    "silence_duration_ms": 500,
                },
            }
        })
        
        # Start listening for events
        asyncio.create_task(self._listen(call_sid))
    
    async def handle_twilio_audio(self, call_sid: str, pcm16_8k: bytes) -> None:
        # Resample 8kHz → 24kHz
        pcm16_24k = _pcm16_resample_x3(pcm16_8k)
        audio_b64 = base64.b64encode(pcm16_24k).decode("utf-8")
        
        # Send to OpenAI
        await self._send(st.ws, {
            "type": "input_audio_buffer.append",
            "audio": audio_b64
        })
        await self._send(st.ws, {"type": "input_audio_buffer.commit"})
    
    async def pop_openai_audio_8k(self, call_sid: str, event: Dict[str, Any]) -> Optional[bytes]:
        # Extract audio from event
        delta = event.get("delta")
        if not delta:
            return None
        
        # Decode and resample 24kHz → 8kHz
        pcm16_24k = base64.b64decode(delta)
        return _pcm16_resample_div3(pcm16_24k)
```

### Example 2: TTS for Pre-recorded Messages

```python
from openai import OpenAI

client = OpenAI(api_key=OPENAI_API_KEY)

def generate_greeting(name: str) -> bytes:
    response = client.audio.speech.create(
        model="tts-1",
        voice="nova",
        input=f"Hello {name}, welcome to our service!",
        response_format="mp3"
    )
    return response.content
```

### Example 3: Transcription of Call Recording

```python
from openai import OpenAI

client = OpenAI(api_key=OPENAI_API_KEY)

def transcribe_call(audio_file_path: str) -> str:
    with open(audio_file_path, "rb") as audio_file:
        transcript = client.audio.transcriptions.create(
            model="gpt-4o-transcribe",
            file=audio_file,
            language="en",
            response_format="text"
        )
    return transcript
```

---

## Best Practices

### Latency Optimization

1. **Use Realtime API for live conversations**: Lower latency than TTS + STT pipeline
2. **Optimize audio buffer size**: Balance between latency and quality
3. **Use appropriate sample rates**: Match your telephony provider's requirements
4. **Enable server VAD**: Let OpenAI handle turn detection for better performance

### Audio Quality

1. **Choose appropriate voice**: Match voice to use case (professional vs. friendly)
2. **Use HD models for important content**: `tts-1-hd` for high-quality output
3. **Handle resampling carefully**: Use proper interpolation for upsampling
4. **Monitor audio levels**: Prevent clipping and distortion

### Error Handling

1. **Handle WebSocket disconnections**: Implement reconnection logic
2. **Validate audio format**: Ensure compatibility before processing
3. **Monitor API rate limits**: Implement backoff and retry strategies
4. **Log audio processing errors**: Debug resampling and encoding issues

### Security

1. **Protect API keys**: Never expose keys in client-side code
2. **Validate audio inputs**: Check file sizes and formats
3. **Implement rate limiting**: Prevent abuse of voice APIs
4. **Handle sensitive data**: Be careful with transcribed content

### Cost Optimization

1. **Use appropriate models**: `gpt-4o-mini-transcribe` for cost-sensitive use cases
2. **Cache TTS output**: Reuse generated audio for repeated content
3. **Optimize audio length**: Shorter audio = lower costs
4. **Monitor usage**: Track API calls and costs

---

## Error Handling

### Common Errors

#### Authentication Errors

```python
# 401 Unauthorized
{
    "error": {
        "message": "Incorrect API key provided",
        "type": "invalid_request_error",
        "code": "invalid_api_key"
    }
}
```

**Solution**: Verify `OPENAI_API_KEY` is set correctly.

#### Rate Limit Errors

```python
# 429 Too Many Requests
{
    "error": {
        "message": "Rate limit exceeded",
        "type": "rate_limit_error"
    }
}
```

**Solution**: Implement exponential backoff and retry logic.

#### WebSocket Connection Errors

```python
# Connection closed unexpectedly
try:
    ws = await websockets.connect(uri, extra_headers=headers)
except Exception as e:
    logger.error("websocket_connection_failed", error=str(e))
    # Implement reconnection logic
```

#### Audio Format Errors

```python
# Invalid audio format
try:
    pcm16_24k = base64.b64decode(audio_b64)
except Exception as e:
    logger.error("audio_decode_error", error=str(e))
    return None
```

### Error Handling in This Project

```python
# src/voice/realtime_bridge.py

async def _listen(self, call_sid: str) -> None:
    try:
        async for msg in ws:
            event = json.loads(msg)
            # Process event
    except Exception as e:
        logger.error("realtime_listen_error", call_sid=call_sid, error=str(e))
    finally:
        await self.stop(call_sid)  # Cleanup
```

---

## Frequently Asked Questions (FAQ)

### Realtime API

**Q: What's the difference between Realtime API and TTS/STT?**  
A: Realtime API provides low-latency voice-to-voice conversations with streaming audio, while TTS/STT are for one-way conversions (text-to-speech or speech-to-text). Realtime API is ideal for interactive voice agents, while TTS/STT are better for batch processing.

**Q: Which voice should I use?**  
A: "alloy" is neutral and works well for most use cases. "nova" is energetic and friendly, "onyx" is authoritative and professional. Choose based on your application's personality.

**Q: How do I handle audio format conversion?**  
A: Use the resampling functions in `src/voice/realtime_bridge.py` for 8kHz ↔ 24kHz conversion. The `_pcm16_resample_x3()` function handles Twilio's 8kHz to OpenAI's 24kHz conversion.

**Q: What's the latency of Realtime API?**  
A: Typically 200-500ms for voice-to-voice responses, depending on network conditions and audio buffer size. This is much lower than TTS + STT pipeline.

**Q: Can I use Realtime API for phone calls?**  
A: Yes, but you need to bridge it with a telephony provider like Twilio. See `src/telephony/media_stream.py` for Media Streams integration.

**Q: How do I enable function calling in Realtime API?**  
A: Pass tools array in `session.update()` call. Tools must be enabled in the session configuration. See integration examples above.

### Text-to-Speech (TTS)

**Q: Which TTS model should I use?**  
A: `tts-1` is faster and cheaper, `tts-1-hd` provides higher quality. Use `tts-1` for real-time applications, `tts-1-hd` for pre-recorded content.

**Q: What audio formats are supported?**  
A: MP3, Opus, AAC, and FLAC. MP3 is most compatible, Opus provides best quality-to-size ratio.

**Q: Can I control speech speed or pitch?**  
A: Not directly through the API, but you can post-process audio or use SSML (if supported in future versions).

### Speech-to-Text (STT)

**Q: Which transcription model should I use?**  
A: `whisper-1` is the standard model. `gpt-4o-transcribe` (if available) may provide better accuracy for specific use cases.

**Q: How accurate is the transcription?**  
A: Very high accuracy (typically 95%+ for clear audio). Accuracy depends on audio quality, background noise, and speaker clarity.

**Q: Can I transcribe multiple languages?**  
A: Yes, specify the `language` parameter. If not specified, Whisper will auto-detect the language.

### Audio Formats

**Q: What sample rate does OpenAI use?**  
A: Realtime API uses 24kHz PCM16. TTS outputs at various sample rates depending on format. STT accepts various sample rates.

**Q: How do I convert between audio formats?**  
A: Use libraries like `pydub` or `ffmpeg` for format conversion. For sample rate conversion, use the resampling functions in the codebase.

### Error Handling

**Q: What should I do if I get rate limit errors?**  
A: Implement exponential backoff with jitter. The codebase includes `retry_openai_call()` decorator that handles this automatically.

**Q: How do I handle WebSocket connection failures?**  
A: Implement reconnection logic with exponential backoff. See `src/voice/realtime_bridge.py` for example implementation.

**Q: What if audio quality is poor?**  
A: Check sample rate conversion, network latency, and buffer sizes. Ensure audio is properly encoded and not corrupted during transmission.

### Configuration

**Q: Where do I set my OpenAI API key?**  
A: Set `OPENAI_API_KEY` environment variable or in `.env` file. Never commit API keys to version control.

**Q: How do I change the Realtime API model?**  
A: Set `OPENAI_REALTIME_MODEL` environment variable (default: `gpt-4o-realtime-preview`).

**Q: Can I use different voices for different users?**  
A: Yes, specify voice in each session configuration. You can maintain multiple sessions with different voices.

---

## Security Policy Integration

### Overview

The system implements a comprehensive security policy to prevent unauthorized actions and protect user data. The policy is defined in `src/security/policy.py` and integrates with both Chat Completions and Realtime API.

### Policy Components

1. **Risk Classification**: Tools classified as HIGH or LOW risk
2. **Confirmation Requirements**: High-risk tools require explicit approval
3. **Godfather Identification**: Authorized user verification
4. **Actor System**: Tracks who initiated each action

### Risk Classification

```python
def tool_risk(tool_name: str) -> Tuple[Risk, List[str]]:
    """Classify tool as HIGH or LOW risk"""
    high_risk_tools = {
        "make_call": "initiates an outbound call",
        "send_sms": "sends an SMS message",
        "send_email": "sends an email",
        "calendar_create_event": "creates a calendar event",
        "calendar_update_event": "updates a calendar event",
        "calendar_cancel_event": "cancels a calendar event"
    }
    
    if tool_name in high_risk_tools:
        return Risk.HIGH, [high_risk_tools[tool_name]]
    
    # Low-risk tools
    if tool_name == "web_research":
        return Risk.LOW, ["performs web research (read-only)"]
    
    # Unknown tools default to HIGH risk
    return Risk.HIGH, ["unknown tool (default-high)"]
```

### Confirmation Decision

```python
def decide_confirmation(actor: Actor, planned_calls: List[PlannedToolCall]) -> PolicyDecision:
    """
    Determine if confirmation is required for planned tool calls.
    
    Rules:
    - Any HIGH-risk tool => confirmation required
    - External callers can never auto-execute HIGH-risk tools
    - Godfather can execute after confirmation
    """
    reasons = []
    worst_risk = Risk.LOW
    
    for call in planned_calls:
        risk, risk_reasons = tool_risk(call.name)
        reasons.extend(risk_reasons)
        if risk == Risk.HIGH:
            worst_risk = Risk.HIGH
    
    if worst_risk == Risk.LOW:
        return PolicyDecision(
            requires_confirmation=False,
            risk=worst_risk,
            reasons=reasons
        )
    
    # High-risk tools always require confirmation
    if not is_godfather(actor):
        reasons.append("initiator is not Godfather")
    
    return PolicyDecision(
        requires_confirmation=True,
        risk=Risk.HIGH,
        reasons=reasons
    )
```

### Godfather Identification

The system identifies authorized users ("Godfather") via:

1. **Phone Number Allowlist**: `GODFATHER_PHONE_NUMBERS` environment variable
2. **Email Address**: `GODFATHER_EMAIL` environment variable
3. **Stored Identity**: `secrets/godfather.json` file (gitignored)

```python
def is_godfather(actor: Actor) -> bool:
    """Check if actor is the authorized Godfather"""
    settings = get_settings()
    stored = load_identity()
    
    # Check phone number
    allowlist = set(parse_phone_allowlist(stored.phone_numbers_csv)) | \
                set(parse_phone_allowlist(settings.GODFATHER_PHONE_NUMBERS))
    
    if actor.phone_number and normalize_e164(actor.phone_number) in allowlist:
        return True
    
    # Check email
    stored_email = (stored.email or "").strip()
    env_email = (settings.GODFATHER_EMAIL or "").strip()
    
    if actor.email:
        if stored_email and actor.email.lower() == stored_email.lower():
            return True
        if env_email and actor.email.lower() == env_email.lower():
            return True
    
    return False
```

### Actor System

Every action has an associated `Actor`:

```python
@dataclass(frozen=True)
class Actor:
    """Who initiated the action"""
    kind: str  # "godfather" or "external"
    phone_number: Optional[str] = None
    email: Optional[str] = None
```

### Policy Enforcement Flow

1. **User Request**: User requests action via voice or text
2. **Planning**: AI plans tool calls (no side effects)
3. **Policy Check**: `decide_confirmation()` evaluates risk
4. **Confirmation**: If high-risk, ask user for confirmation
5. **Execution**: Only execute after confirmation (or for low-risk)
6. **Audit**: Log all tool executions for security

### External Caller Handling

External callers (not Godfather) have restricted permissions:

- **Cannot Execute**: High-risk tools are blocked
- **Can Request**: Can ask for actions, but system takes message
- **Message Taking**: System says "I'll ask Godfather about that"
- **No Auto-Execution**: Never auto-execute for external callers

### Configuration

```bash
# .env file
GODFATHER_PHONE_NUMBERS=+15551234567,+15559876543
GODFATHER_EMAIL=godfather@example.com
```

Or store in `secrets/godfather.json`:
```json
{
    "phone_numbers_csv": "+15551234567,+15559876543",
    "email": "godfather@example.com"
}
```

---

## Frequently Asked Questions

### Realtime API

**Q: What's the difference between Realtime API and TTS/STT?**
A: Realtime API provides low-latency, bidirectional voice-to-voice conversations in real-time. TTS converts text to speech, and STT converts speech to text. Realtime API combines both for natural conversations.

**Q: Which voice should I use?**
A: "alloy" is neutral and works well for most use cases. "nova" is energetic, "onyx" is authoritative, "shimmer" is soft. Choose based on your use case.

**Q: How do I handle audio format conversion?**
A: Use the resampling functions in `realtime_bridge.py` (`_pcm16_resample_x3` for 8kHz→24kHz, `_pcm16_resample_div3` for 24kHz→8kHz).

**Q: Can I use tools in Realtime API?**
A: Yes, enable tools in `session.update` and handle `conversation.item.requires_action` events. See the Function Calling section for details.

**Q: What's the latency of Realtime API?**
A: Typically 200-500ms for audio round-trip, depending on network conditions.

**Q: How do I handle errors in Realtime API?**
A: Implement error handling in the `_listen()` method, log errors, and gracefully close connections.

### TTS API

**Q: What's the maximum text length for TTS?**
A: 4096 characters per request.

**Q: Can I customize the voice style?**
A: Yes, with `gpt-4o-mini-tts` model, you can use instructions to customize tone and style.

**Q: What audio formats are supported?**
A: MP3 (default), Opus, AAC, FLAC, WAV, and PCM.

### STT API

**Q: What's the maximum file size for transcription?**
A: 25 MB per file.

**Q: Can I get speaker labels?**
A: Yes, use `gpt-4o-transcribe-diarize` model for speaker diarization.

**Q: What languages are supported?**
A: 99+ languages including English, Spanish, French, German, Chinese, Japanese, and more.

---

## Troubleshooting Guide

### Realtime API Issues

#### Issue: WebSocket Connection Fails Immediately
**Symptoms**: Connection closes immediately after opening
**Causes**:
- Invalid API key
- Network firewall blocking WebSocket
- Incorrect WebSocket URL format
- Missing required headers

**Solutions**:
1. Verify `OPENAI_API_KEY` is set correctly in environment
2. Check network connectivity: `curl https://api.openai.com`
3. Verify WebSocket URL: `wss://api.openai.com/v1/realtime?model=gpt-4o-realtime-preview`
4. Ensure headers include: `Authorization: Bearer <key>` and `OpenAI-Beta: realtime=v1`
5. Check firewall rules allow WebSocket connections

#### Issue: Audio Quality Issues
**Symptoms**: Choppy audio, delays, distortion, or no audio
**Causes**:
- Incorrect sample rate conversion
- Network latency
- Buffer size issues
- Audio format mismatch

**Solutions**:
1. Verify resampling functions are correct (8kHz ↔ 24kHz)
2. Check network latency: `ping api.openai.com`
3. Adjust buffer sizes in Media Stream handler
4. Verify audio format: PCM16, not µ-law
5. Check audio data is not corrupted before sending

#### Issue: Tool Calls Not Working
**Symptoms**: Tools not executing in Realtime API
**Causes**:
- Tools not enabled in session
- Tool schema incorrect
- Policy blocking execution
- Event handling not implemented

**Solutions**:
1. Verify tools array in `session.update` event
2. Check tool schema matches handler function signature
3. Verify security policy allows execution (`decide_confirmation()`)
4. Implement `conversation.item.requires_action` event handler
5. Check logs for tool call events

#### Issue: High Latency
**Symptoms**: Delayed responses, slow conversation
**Causes**:
- Network latency
- Large audio buffers
- Processing delays
- Server load

**Solutions**:
1. Optimize network path (use CDN if possible)
2. Reduce buffer sizes
3. Process audio in smaller chunks
4. Use server VAD for faster turn detection
5. Monitor OpenAI API status

### TTS API Issues

#### Issue: Audio Not Generated
**Symptoms**: No audio returned from TTS API
**Causes**:
- Invalid API key
- Text too long (>4096 chars)
- Invalid voice parameter
- Rate limit exceeded

**Solutions**:
1. Verify API key is valid
2. Split long text into chunks
3. Use valid voice name (alloy, echo, fable, etc.)
4. Implement rate limiting/retry logic

### STT API Issues

#### Issue: Transcription Fails
**Symptoms**: No transcription returned
**Causes**:
- File too large (>25 MB)
- Unsupported format
- Invalid language code
- API timeout

**Solutions**:
1. Compress or split large files
2. Use supported formats (MP3, WAV, etc.)
3. Use valid language code or auto-detect
4. Increase timeout for large files

---

## Resources

### Official Documentation

- [OpenAI Audio API Overview](https://platform.openai.com/docs/guides/audio)
- [Realtime API Documentation](https://platform.openai.com/docs/guides/realtime)
- [Text-to-Speech API](https://platform.openai.com/docs/guides/text-to-speech)
- [Speech-to-Text API](https://platform.openai.com/docs/guides/speech-to-text)
- [Voice Agents Guide](https://platform.openai.com/docs/guides/voice-agents)

### API Reference

- [OpenAI Python SDK](https://github.com/openai/openai-python)
- [Realtime API Reference](https://platform.openai.com/docs/api-reference/realtime)
- [Audio API Reference](https://platform.openai.com/docs/api-reference/audio)

### Community Resources

- [OpenAI Community Forum](https://community.openai.com/)
- [OpenAI Discord](https://discord.gg/openai)
- [GitHub Examples](https://github.com/openai)

### Project-Specific Files

- `src/voice/realtime_bridge.py`: Realtime API integration
- `src/agent/assistant.py`: Voice assistant implementation
- `src/utils/config.py`: Configuration management
- `src/telephony/call_handler.py`: Call handling

---

## Version History

- **2024-12**: Initial documentation created
- Current OpenAI SDK version: `1.12.0`
- Current Realtime model: `gpt-4o-realtime-preview`
- Latest available model: `gpt-realtime`

---

## Notes

- The Realtime API is in beta and subject to changes
- Custom voices require approval from OpenAI
- Audio file size limits: 25 MB for STT
- Text input limits: 4096 characters for TTS
- Rate limits vary by API tier and usage

For the most up-to-date information, refer to the [OpenAI Platform Documentation](https://platform.openai.com/docs).

