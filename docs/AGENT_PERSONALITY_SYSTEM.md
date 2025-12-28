# Agent Personality System

## Overview

The Agent Personality System allows you to customize AI agent behavior, communication style, voice, and skills through markdown-based personality definitions. This system integrates with OpenAI's Voice Agents API to provide consistent, personality-driven conversations.

## Architecture

### Components

1. **Personality Markdown Files** (`docs/agents/personalities/`)
   - Define agent personalities in markdown format
   - Include traits, skills, voice configuration, and conversation patterns
   - Currently available:
     - `CUSTOMER_SUPPORT_AGENT.md` - Professional, empathetic support agent
     - `SALES_AGENT.md` - Consultative, enthusiastic sales agent
     - `APPOINTMENT_AGENT.md` - Efficient, organized booking agent

2. **Personality Loader** (`src/ai/agent_personality.py`)
   - Loads and parses personality markdown files
   - Extracts structured data (traits, skills, prompts, voice config)
   - Provides API for accessing personality configurations

3. **Personality Applier** (`src/ai/personality_applier.py`)
   - Applies personality to OpenAI session configuration
   - Merges personality settings with base template settings
   - Generates final system prompts and voice configurations

4. **API Integration**
   - `GET /api/v1/config/personalities` - List available personalities
   - `POST /api/v1/calls/initiate` - Accept `agent_personality` parameter

5. **Frontend Integration**
   - `InitiateCallModal` - Personality selection dropdown
   - Loads personalities from API
   - Sends selected personality when initiating calls

## Usage

### Initiating a Call with Personality

1. **Via Frontend UI:**
   - Click "Initiate Call" button
   - Fill in call details
   - Select agent personality from dropdown (optional)
   - Click "Initiate Call"

2. **Via API:**
```python
POST /api/v1/calls/initiate
{
  "to_number": "+1234567890",
  "business_id": "business-123",
  "agent_personality": "CUSTOMER_SUPPORT_AGENT"
}
```

### How Personality is Applied

1. **Call Initiation:**
   - Personality name is stored in call metadata
   - Call record is created with personality reference

2. **Session Creation:**
   - When telephony bridge starts, personality is loaded
   - System prompt is enhanced with personality traits
   - Voice configuration is applied (voice, temperature, response delay)
   - OpenAI Realtime session is created with personality settings

3. **During Conversation:**
   - Agent follows personality-defined communication style
   - Uses personality-specific conversation patterns
   - Applies personality guidelines (do's and don'ts)

## Creating Custom Personalities

### Step 1: Create Markdown File

Create a new file in `docs/agents/personalities/YOUR_PERSONALITY.md`:

```markdown
# Your Personality Name

## Overview
Brief description of the personality...

## Personality Traits
- **Trait 1**: Description
- **Trait 2**: Description

## Skills & Capabilities
### Primary Skills
1. **Skill 1**: Description
2. **Skill 2**: Description

## Voice Configuration
- **Voice**: `nova` (or alloy, echo, fable, onyx, shimmer)
- **Temperature**: `0.7`
- **Response Delay**: `0.3s`
- **Language**: `en-US`

## Conversation Patterns
### Opening
```
"Your opening greeting..."
```

## Response Guidelines
### Do's
✅ Guideline 1
✅ Guideline 2

### Don'ts
❌ Guideline 1
❌ Guideline 2
```

### Step 2: System Auto-Detection

The system automatically:
- Detects new personality files on startup
- Loads and parses markdown content
- Makes personality available via API
- Includes in frontend dropdown

### Step 3: Use Your Personality

- Select from dropdown when initiating calls
- Or reference by name in API calls

## Personality File Structure

### Required Sections

1. **Overview** - High-level description
2. **Personality Traits** - Core characteristics
3. **Skills & Capabilities** - Agent abilities
4. **Voice Configuration** - Voice settings

### Optional Sections

- **Communication Style** - Tone, pace, language
- **Conversation Patterns** - Example interactions
- **Response Guidelines** - Do's and don'ts
- **Example Interactions** - Scenarios
- **Escalation Triggers** - When to escalate
- **Quality Metrics** - Success indicators

## Integration Points

### 1. Call Handler
- Stores personality in call metadata
- Passes personality to session creation

### 2. Telephony Bridge
- Loads personality when starting bridge
- Applies personality to OpenAI session

### 3. OpenAI Client
- Receives personality-enhanced system prompt
- Uses personality voice configuration
- Applies personality temperature and settings

### 4. Prompt Engine
- Can incorporate personality into prompts
- Merges personality with template prompts
- Enhances RAG context with personality style

## API Reference

### List Personalities

```http
GET /api/v1/config/personalities
```

**Response:**
```json
{
  "personalities": [
    {
      "name": "CUSTOMER_SUPPORT_AGENT",
      "display_name": "Customer Support Agent",
      "traits": ["Empathetic", "Patient", "Solution-Oriented"],
      "skills": ["Problem Diagnosis", "Solution Delivery"],
      "voice_config": {
        "voice": "nova",
        "temperature": 0.7,
        "response_delay": 0.3
      }
    }
  ]
}
```

### Initiate Call with Personality

```http
POST /api/v1/calls/initiate
Content-Type: application/json

{
  "to_number": "+1234567890",
  "business_id": "business-123",
  "agent_personality": "CUSTOMER_SUPPORT_AGENT"
}
```

## Best Practices

### 1. Personality Design
- **Be Specific**: Clear, actionable traits
- **Match Use Case**: Align with business type
- **Test Thoroughly**: Validate conversation quality
- **Iterate**: Refine based on call performance

### 2. Voice Configuration
- **Customer Support**: `nova` (clear, professional)
- **Sales**: `alloy` (balanced, approachable)
- **Appointments**: `echo` (warm, friendly)
- **Technical Support**: `onyx` (authoritative)

### 3. System Prompts
- Keep base prompts in templates
- Use personality for style enhancement
- Combine template + personality for best results

### 4. Skills Definition
- Focus on actionable capabilities
- Align with tool handlers
- Document expected behavior

## Troubleshooting

### Personality Not Loading
- Check file is in `docs/agents/personalities/`
- Verify markdown syntax is correct
- Check logs for parsing errors
- Restart application to reload personalities

### Personality Not Applied
- Verify personality name matches exactly
- Check call metadata contains personality
- Ensure telephony bridge loads personality
- Review logs for application errors

### Voice Not Changing
- Verify voice configuration in personality file
- Check voice name is valid (alloy, echo, fable, onyx, nova, shimmer)
- Ensure personality is loaded before session creation

## Future Enhancements

- [ ] Personality templates/generator
- [ ] A/B testing different personalities
- [ ] Personality performance analytics
- [ ] Dynamic personality switching mid-call
- [ ] Multi-language personality support
- [ ] Personality marketplace/sharing

## Related Documentation

- [OpenAI Voice Agents Guide](./OPENAI_VOICE_AGENTS.md)
- [AgentKit Voice Integration](./AGENTKIT_VOICE.md)
- [System Architecture](../SYSTEM_ARCHITECTURE_AND_CAPABILITIES.md)

