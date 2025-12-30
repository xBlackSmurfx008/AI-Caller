# Voice-to-Voice AI Assistant Rebuild Plan

## Overview
Rebuilding the system from scratch to create a voice-to-voice AI assistant using OpenAI Agents SDK. The assistant will handle inbound/outbound calls and execute tasks (calling, texting, emailing) as instructed by the user.

## What We're Keeping
1. **Twilio Connection**: `src/telephony/twilio_client.py` (simplified)
2. **OpenAI Connection**: Will be refactored to use OpenAI Agents SDK
3. **Deployment Configs**: 
   - `Dockerfile`
   - `docker-compose.yml`
   - `vercel.json`
4. **Basic Config**: `src/utils/config.py` (simplified)
5. **Twilio Webhooks**: Basic webhook handler for voice calls

## What We're Removing
- All frontend code (rebuilding from scratch)
- All database models (except minimal task tracking)
- Knowledge base system
- QA/Compliance systems
- Escalation system
- All complex routes
- All documentation files (except this plan)

## New Architecture

### Core Components
1. **OpenAI Agents SDK Integration**
   - Agent with instructions for task execution
   - Tools: make_call, send_sms, send_email
   - Session management for conversations

2. **Task Management System**
   - User submits tasks via API/UI
   - Agent receives task and breaks it down
   - Agent executes using available tools
   - Status tracking and reporting

3. **Voice Integration**
   - Twilio for telephony (inbound/outbound)
   - OpenAI Realtime API for voice-to-voice
   - Bridge between Twilio and OpenAI

4. **Simple UI**
   - Task input form
   - Task status dashboard
   - Call management interface

## Implementation Steps
1. Research OpenAI Agents SDK structure
2. Clean up codebase (remove unnecessary files)
3. Create new simplified requirements.txt
4. Build core agent system with tools
5. Integrate Twilio voice calls with OpenAI
6. Create task management API
7. Build minimal UI
8. Test end-to-end flow

