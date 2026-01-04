## Deep History Memory (Chat + Voice) — OpenAI Integrations Guide for This Repo

Last updated: 2026-01-03

This doc is written for **AI Caller** and explains:
- Why the assistant currently feels like it has “short memory”
- What “deep history” means in API terms (and what OpenAI does/doesn’t store for you)
- Which OpenAI docs/products map to the capabilities you want (Responses, Agents SDK, ChatKit, Realtime/voice, Assistants/Threads)
- A concrete, repo-compatible design to add **durable chat history + retrieval memory**

---

## 1) Current state in this repo (what exists today)

### Planning + tool calling (text)
- Planner is `src/agent/assistant.py` → `VoiceAssistant.plan_task()`
- It calls either:
  - Chat Completions: `client.chat.completions.create(...)`, or
  - Responses API: `client.responses.create(...)` (when `OPENAI_USE_RESPONSES` is enabled and supported by the SDK)
- Tools are defined in `src/agent/tools.py` (`TOOLS` + `TOOL_HANDLERS`)
- Execution policy (plan → confirm → execute) is in `src/security/policy.py`
- API entrypoint is `src/api/routes/tasks.py` (`POST /tasks`)

### Voice mode (Realtime)
- Realtime bridge is `src/voice/realtime_bridge.py` (Twilio Media Streams ↔ OpenAI Realtime WebSocket)
- Project docs: `docs/openai/realtime.md` and `OPENAI_VOICE_DOCUMENTATION.md`

### “Memory” that already exists (relationship memory, not chat memory)
You already store long-lived memory for **contacts**, across SMS/email/calls:
- Raw interactions: `Interaction` table
- Structured summaries: `MemorySummary` table
- Rolling state: `ContactMemoryState` table
- Summarization engine: `src/memory/memory_service.py`

This memory is injected into planning **only when** the backend detects a contact in the task and adds `context["contact_memory"]` (see `src/api/routes/tasks.py` → `_enhance_context_with_memory()`).

---

## 2) Why the assistant feels like it has short memory

### Root cause
The OpenAI API **does not** remember prior turns unless you:
- include them again as part of the request (classic “send history every turn”), or
- use a state/session mechanism (SDK sessions, threads, etc.) that replays history for you, and/or
- implement your own durable memory (DB + summaries + retrieval).

In this repo today:
- The “chat-like” UI component (`frontend/src/components/tasks/TaskIntaker.tsx`) keeps chat messages **only in React state**.
- When it calls the backend, it sends only:
  - `task: messageText`
  - (no `context.history`)
- The planner (`src/agent/assistant.py`) only adds prior messages if `context["history"]` is provided.

Net: every request is effectively:
1) system instructions
2) optional contact memory (only if a contact is detected)
3) the latest user text

So you get **no deep chat continuity**.

---

## 3) What “deep history memory” should mean (in practical terms)

You typically want **three layers** of memory:

### A) Short-term turn context (recency)
- The last N user/assistant turns from the current thread/session.
- Purpose: coherence, pronouns, immediate plan continuity.

### B) Rolling “thread summary” (compression)
- A continuously-updated summary of the conversation so far.
- Purpose: preserve long-running goals/decisions without blowing the context window.

### C) Long-term retrieval memory (selective recall)
- A store of older messages and extracted facts (optionally with embeddings).
- Each new user message triggers retrieval of top-K relevant memories.
- Purpose: “remembering” details from weeks/months ago without stuffing everything into every prompt.

Important: even with very large context models, you still want summarization + retrieval for cost and relevance.

---

## 4) OpenAI building blocks you’ll see mentioned (and which to use)

### Responses API (recommended primitive)
Use this as the primary “model call” API for agentic apps.
- Guide: `https://platform.openai.com/docs/guides/responses`
- API reference: `https://platform.openai.com/docs/api-reference/responses`

Why it matters for memory:
- You can standardize on one API that supports tool use and streaming.
- You still supply conversation state yourself (unless you use an SDK/session layer on top).

### Function calling / tools (already implemented here)
- Guide: `https://platform.openai.com/docs/guides/function-calling`
- In-repo: `src/agent/tools.py`, `src/security/policy.py`, `src/api/routes/tasks.py`

### Realtime API + Voice Agents (voice mode)
- Realtime guide: `https://platform.openai.com/docs/guides/realtime`
- Voice agents guide: `https://platform.openai.com/docs/guides/voice-agents`
- (Project reference) `docs/openai/realtime.md`, `OPENAI_VOICE_DOCUMENTATION.md`

Why it matters for memory:
- You can inject a call-specific “memory preamble” via `session.update` instructions and/or initial text items.
- You can persist transcripts and reuse the same summarization/retrieval pipeline as chat.

### Agents SDK (Python) — session memory + orchestration helpers
If you want a more structured “agent runtime” than hand-rolled loops, this is the most relevant doc I found:
- Sessions (built-in session memory): `https://openai.github.io/openai-agents-python/sessions/`

What it gives you:
- A session object that automatically stores/replays items across turns (so you stop manually assembling `history`).

What it does *not* magically give you:
- Cross-session durable memory of “facts about the user” unless you persist and retrieve those facts yourself.

### ChatKit / AgentKit (product + UI kits)
If you want an “official” embedded chat UX, OpenAI docs point to:
- ChatKit guide: `https://platform.openai.com/docs/guides/chatkit`
- AgentKit announcement: `https://openai.com/index/introducing-agentkit/`

How this maps to this repo:
- Your frontend already has a custom chat-like UI (`TaskIntaker`), but it’s not persisted.
- ChatKit can accelerate a thread-aware UI, but you still need your backend memory design.

### Models + audio (selection + capabilities)
- Models: `https://platform.openai.com/docs/models`
- Audio guide: `https://platform.openai.com/docs/guides/audio`

---

## 5) Recommended deep-memory design for THIS repo (minimal disruption)

Your codebase already has strong patterns for:
- DB persistence (SQLAlchemy + Alembic)
- Summarization with structured JSON (`MemoryService.generate_summary()`)
- A plan/confirm/execute workflow for tool safety

So the cleanest approach is to add a **parallel “chat memory” system** (like `MemoryService`, but for chat threads).

### 5.1 Data model (proposed)
Add tables (names are suggestions):
- `chat_sessions`
  - `id`, `title`, `created_at`, `updated_at`
  - optional: `actor_phone`, `actor_email` (so “Godfather” can have multiple threads)
- `chat_messages`
  - `id`, `session_id`, `role` (`user`/`assistant`/`tool`/`system`), `content`, `created_at`
  - optional: `tool_name`, `tool_call_id`, `metadata`
- `chat_session_summaries`
  - `session_id`, `summary_text`, `updated_at`, `version`
- (optional) `chat_memory_items`
  - extracted “facts” or “events” + an embedding vector (for semantic retrieval)

### 5.2 Request flow (chat)
On each user turn:
1) Persist the user message into `chat_messages`.
2) Build model context with:
   - system instructions
   - thread summary (if exists)
   - last N turns (recency window)
   - top-K retrieved memories (optional but recommended)
   - contact memory (existing feature) if a contact is detected
3) Call the model (Responses API or chat.completions).
4) Persist assistant message + tool calls + tool results.
5) Update thread summary periodically (token-based or every M turns), similar to how SMS conversations trigger summarization.

### 5.3 Two scopes: Global Godfather + Per-project
This project can maintain **two durable chat memories** in parallel:
- **Global Godfather memory**: used when no `project_id` is present (default “assistant chat”)
- **Per-project memory**: used automatically when `project_id` is present

Implementation detail:
- `ChatSession.scope_type`: `"global"` or `"project"`
- `ChatSession.scope_id`: stores the `project_id` when `scope_type=="project"`
- `POST /api/tasks/` auto-resolves a session when `chat_session_id` is not provided:
  - if `project_id` → project-scoped session
  - else → global-scoped session

### 5.4 “Quick win” improvement (even before new tables)
Your planner already supports `context["history"]`.
You can immediately improve continuity by having the frontend send:
- `context.history = messages.map(m => ({ role, content }))`

This will still be “short” once history exceeds the model context window, but it proves the end-to-end wiring.

### 5.5 Voice flow (Realtime)
For voice calls, you already have:
- transcripts from realtime (`input_audio_transcription`)
- a call session id (`call_sid`)

Add:
1) Persist transcripts (user + assistant) under a “voice session” record.
2) After the call (or periodically), summarize into:
   - “call summary”
   - extracted facts/commitments
3) On future calls, inject a short memory preamble into the realtime session:
   - either by including it in `session.update.instructions`
   - and/or sending an initial text item with a “Memory Context” block

---

## 6) Practical implementation roadmap (repo-focused)

### Phase 1 — Make current chat UI send history (1–2 hours)
- Change `TaskIntaker` to include `context.history`.
- Backend requires no changes (it already accepts `context`).

### Phase 2 — Persist chat sessions in DB (core “deep history”)
- Add `ChatSession` + `ChatMessage` models.
- Add routes:
  - `POST /chat/sessions`
  - `POST /chat/sessions/{id}/messages` (returns assistant response)
  - `GET /chat/sessions/{id}` (messages + summary)
- Update frontend to use session ids rather than purely local React state.

### Phase 3 — Add rolling summaries (cheap, high value)
- Create `ChatMemoryService` modeled after `MemoryService`.
- Summarize every N messages or when token estimate crosses a threshold.

### Phase 4 — Add retrieval memory (best long-term)
Two good options:
- **Local embeddings + DB vector search** (fast, controllable, works offline)
- **OpenAI file/vector-store tools** (if you prefer managed retrieval; align with Responses/Agents built-in tools)

---

## 7) Notes on “Assistants / Threads / Agent mode”

You’ll see older “Assistants API / Threads” terminology in docs and blog posts.
Key point for project planning:
- Threads-style server-side history exists in some OpenAI surfaces, but OpenAI is clearly pushing toward **Responses + Agents** as the main primitives going forward (and deprecations are being discussed publicly).

In this repo, you’re already mostly aligned with the modern direction because:
- you have a tools schema + policy gate
- you can switch to Responses API (`OPENAI_USE_RESPONSES`)
- you already implemented Realtime voice yourself

So: implement memory in your application layer, and treat OpenAI APIs as stateless unless you explicitly opt into an SDK/session abstraction.


