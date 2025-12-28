# OpenAI Voice Agents Documentation

This document contains the official OpenAI Voice Agents documentation integrated into the project.

**Source:** https://platform.openai.com/docs/guides/voice-agents

## Overview

OpenAI Voice Agents enable you to build conversational AI agents that can interact with users through voice. The Realtime API provides low-latency, bidirectional communication for natural voice conversations.

## Key Features

### 1. Realtime API
- **WebSocket-based**: Real-time bidirectional communication
- **Low latency**: Sub-second response times
- **Audio streaming**: Direct audio input/output processing
- **Event-driven**: Rich event system for conversation management

### 2. Voice Capabilities
- **Multiple voices**: alloy, echo, fable, onyx, nova, shimmer
- **Natural speech**: High-quality text-to-speech synthesis
- **Voice activity detection**: Automatic turn-taking
- **Transcription**: Built-in speech-to-text

### 3. AgentKit Integration
- **Tool calling**: Agents can execute functions during conversations
- **Multi-modal**: Support for text, audio, and structured data
- **Context awareness**: Maintains conversation context
- **Guardrails**: Built-in safety and monitoring

## Architecture

### Speech-to-Speech (Realtime) Architecture
```
User Audio → Realtime API → Agent Processing → Response Audio → User
```

**Best for:**
- Language tutoring
- Interactive customer service
- Natural conversations
- Low-latency requirements

### Chained Architecture
```
Audio → Text → LLM Processing → Text → Audio
```

**Best for:**
- Structured workflows
- Customer support
- Sales conversations
- High control requirements

## API Endpoints

### Realtime API
- **URL**: `wss://api.openai.com/v1/realtime`
- **Model**: `gpt-4o-realtime-preview` or `gpt-4o`
- **Authentication**: Bearer token with API key

## Session Configuration

### Basic Configuration
```json
{
  "model": "gpt-4o",
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

### Voice Options
- **alloy**: Neutral, balanced voice
- **echo**: Warm, friendly voice
- **fable**: Expressive, animated voice
- **onyx**: Deep, authoritative voice
- **nova**: Clear, professional voice (recommended for customer service)
- **shimmer**: Soft, gentle voice

## Event Types

### Input Events
- `input_audio_buffer.append`: Send audio data
- `input_audio_buffer.commit`: Commit audio buffer
- `conversation.item.create`: Add text message
- `response.interrupt`: Interrupt current response

### Output Events
- `response.audio.delta`: Audio chunk received
- `response.audio_transcript.delta`: Transcript chunk
- `conversation.item.input_audio_transcription.completed`: User transcription
- `response.function_call_arguments.delta`: Function call arguments
- `response.function_call.done`: Function call complete

## Tool Calling (AgentKit Abilities)

### Tool Definition
```json
{
  "type": "function",
  "function": {
    "name": "lookup_customer",
    "description": "Look up customer information",
    "parameters": {
      "type": "object",
      "properties": {
        "phone_number": {
          "type": "string",
          "description": "Customer phone number"
        }
      },
      "required": ["phone_number"]
    }
  }
}
```

### Tool Execution Flow
1. Agent detects need for tool during conversation
2. Agent calls tool with arguments
3. Tool executes and returns result
4. Agent incorporates result into response
5. Agent continues conversation naturally

## Best Practices

### 1. Voice Optimization
- Use concise, natural language
- Avoid complex technical terms
- Provide clear, actionable responses
- Use conversational tone

### 2. Turn Detection
- Configure appropriate silence duration
- Adjust threshold based on environment
- Test with different speaking styles
- Monitor for false positives

### 3. Error Handling
- Gracefully handle tool failures
- Provide fallback responses
- Log errors for debugging
- Retry transient failures

### 4. Performance
- Minimize tool execution time
- Cache frequently accessed data
- Optimize audio processing
- Monitor latency metrics

## Integration with AI Caller

### Current Implementation
- ✅ Realtime API client (`src/ai/openai_client.py`)
- ✅ Tool handlers (`src/ai/tool_handlers.py`)
- ✅ Session management
- ✅ Audio streaming
- ✅ Function calling support

### Usage Example
```python
from src.ai.openai_client import OpenAIRealtimeClient
from src.ai.tool_handlers import get_customer_support_tools

client = OpenAIRealtimeClient(business_id="business-123")

await client.create_session(
    session_id="call-123",
    system_prompt="You are a helpful customer service agent...",
    tools=get_customer_support_tools(),
    voice="nova",
    temperature=0.8,
)
```

## Resources

- **Official Documentation**: https://platform.openai.com/docs/guides/voice-agents
- **Realtime API Reference**: https://platform.openai.com/docs/api-reference/realtime
- **AgentKit Guide**: https://platform.openai.com/docs/guides/agents/agent-builder
- **Voice Models**: https://platform.openai.com/docs/models

## Security Considerations

1. **API Key Management**: Store keys securely, never in code
2. **Rate Limiting**: Implement rate limits to prevent abuse
3. **Input Validation**: Validate all tool inputs
4. **Output Filtering**: Filter sensitive information
5. **Audit Logging**: Log all interactions for compliance

## Troubleshooting

### Common Issues

1. **Connection Failures**
   - Verify API key is valid
   - Check network connectivity
   - Ensure WebSocket support

2. **Audio Quality Issues**
   - Verify audio format (PCM16)
   - Check sample rate (16kHz)
   - Test with different voices

3. **Tool Execution Errors**
   - Validate tool definitions
   - Check argument types
   - Review error logs

4. **Latency Issues**
   - Optimize tool execution
   - Reduce response token count
   - Use appropriate voice model

## Updates

This documentation is synchronized with OpenAI's official documentation. For the latest updates, refer to:
https://platform.openai.com/docs/guides/voice-agents

