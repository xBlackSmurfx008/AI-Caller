# OpenAI Voice Assistant Configuration

## ✅ Optimized Configuration Applied

Your AI Caller system has been configured with the **best voice assistant/agent models** from OpenAI.

### Model Configuration

**Primary Model:** `gpt-4o-realtime-preview`
- ✅ Specifically designed for realtime voice interactions
- ✅ Best for voice assistants and conversational agents
- ✅ Low-latency, bidirectional communication
- ✅ Native voice-to-voice capabilities

**Alternative:** `gpt-4o` (also excellent for voice)
- General-purpose model with voice capabilities
- Also supports realtime API

### Voice Settings

**Recommended Voice:** `nova`
- ✅ Clear, professional voice
- ✅ Optimized for customer service
- ✅ Natural and engaging

**Other Available Voices:**
- `alloy` - Neutral, balanced
- `echo` - Warm, friendly
- `fable` - Expressive, animated
- `onyx` - Deep, authoritative
- `shimmer` - Soft, gentle

### Configuration Files Updated

1. **`.env` file:**
   ```
   OPENAI_MODEL=gpt-4o-realtime-preview
   ```

2. **`src/utils/config.py`:**
   - Default model: `gpt-4o-realtime-preview`

3. **`config/default.yaml`:**
   - Model: `gpt-4o-realtime-preview`
   - Temperature: `0.8` (optimized for natural conversations)
   - Max tokens: `4096` (increased for better context)
   - Voice: `nova` (recommended for customer service)

### API Endpoint

**Realtime API URL:** `wss://api.openai.com/v1/realtime`
- WebSocket-based for real-time communication
- Low-latency audio streaming
- Event-driven architecture

### Features Enabled

✅ **Speech-to-Speech (Realtime)**
- Direct audio input/output processing
- Automatic speech recognition (ASR) with Whisper-1
- Text-to-speech (TTS) with multiple voice options
- Natural conversation flow with interruptions

✅ **Voice Activity Detection**
- Server-side VAD (Voice Activity Detection)
- Automatic turn-taking
- Configurable silence detection

✅ **Tool Calling (AgentKit)**
- Function execution during conversations
- Multi-modal support (text, audio, structured data)
- Context awareness
- Built-in safety and monitoring

### Session Configuration

The system uses optimized settings for voice assistants:

```python
{
    "model": "gpt-4o-realtime-preview",
    "voice": "nova",
    "temperature": 0.8,
    "max_response_output_tokens": 4096,
    "input_audio_format": "pcm16",
    "output_audio_format": "pcm16",
    "input_audio_transcription": {
        "model": "whisper-1"
    },
    "turn_detection": {
        "type": "server_vad",
        "threshold": 0.5,
        "prefix_padding_ms": 300,
        "silence_duration_ms": 500
    },
    "modalities": ["audio", "text"]
}
```

### Testing

To test the voice assistant configuration:

1. **Start the server:**
   ```bash
   source venv/bin/activate
   uvicorn src.main:app --reload
   ```

2. **Make a test call:**
   - Call your Twilio number: `+19472432891`
   - The AI will use `gpt-4o-realtime-preview` with `nova` voice

3. **Verify in logs:**
   - Check that sessions are created with the correct model
   - Verify voice is set to "nova"

### Custom Deployment

If you have a custom OpenAI deployment URL, you can set it in `.env`:

```bash
OPENAI_REALTIME_API_URL=wss://your-custom-deployment-url/v1/realtime
```

### Best Practices

1. **Voice Selection:**
   - Use `nova` for customer service (current default)
   - Use `onyx` for authoritative/formal interactions
   - Use `echo` for friendly, casual conversations

2. **Temperature:**
   - `0.8` - Natural, conversational (current)
   - `0.7` - More focused, consistent
   - `0.9` - More creative, varied

3. **Context Management:**
   - Max tokens set to `4096` for better context
   - Conversation history maintained automatically
   - Context summarization for long conversations

### Model Comparison

| Model | Best For | Latency | Voice Quality |
|-------|----------|---------|---------------|
| `gpt-4o-realtime-preview` | Voice assistants, realtime | Very Low | Excellent |
| `gpt-4o` | General purpose + voice | Low | Excellent |
| `gpt-4-turbo` | Text-focused | Medium | Good |

**Current Selection:** `gpt-4o-realtime-preview` ✅

### Next Steps

1. ✅ Model configured: `gpt-4o-realtime-preview`
2. ✅ Voice optimized: `nova`
3. ✅ Settings tuned for voice assistants
4. 🔄 Test with actual calls
5. 🔄 Monitor performance and adjust if needed

---

**Configuration Complete!** Your AI Caller is now using the best voice assistant models from OpenAI.

