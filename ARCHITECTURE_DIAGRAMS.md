# Architecture Diagrams

**Last Updated**: 2025-01-29  
**Version**: 1.0

Comprehensive architecture diagrams for the AI Voice Assistant system using text-based diagrams.

---

## System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         AI Voice Assistant                        │
│                                                                   │
│  ┌──────────────┐         ┌──────────────┐                     │
│  │   Frontend   │─────────▶│   Backend    │                     │
│  │   (React)    │  HTTP    │  (FastAPI)   │                     │
│  └──────────────┘          └──────────────┘                     │
│                                      │                            │
│                                      ▼                            │
│                            ┌──────────────┐                     │
│                            │   Database   │                     │
│                            │ (SQLite/PG)  │                     │
│                            └──────────────┘                     │
└─────────────────────────────────────────────────────────────────┘
                                      │
                    ┌─────────────────┼─────────────────┐
                    ▼                 ▼                 ▼
            ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
            │   OpenAI     │  │    Twilio    │  │    Email     │
            │   (AI/LLM)   │  │  (Voice/SMS) │  │  (Gmail/...) │
            └──────────────┘  └──────────────┘  └──────────────┘
```

---

## Plan → Confirm → Execute Workflow

```
┌─────────────────────────────────────────────────────────────────┐
│                         Task Request Flow                        │
└─────────────────────────────────────────────────────────────────┘

User Request
    │
    ▼
┌─────────────────┐
│  POST /api/tasks│
│  {task: "..."}  │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────────┐
│  1. PLAN PHASE                      │
│  assistant.plan_task()               │
│  - AI analyzes request               │
│  - Generates tool calls              │
│  - NO side effects                   │
└────────────┬────────────────────────┘
             │
             ▼
┌─────────────────────────────────────┐
│  2. POLICY CHECK                    │
│  decide_confirmation()               │
│  - Evaluate risk level              │
│  - Check actor (Godfather?)         │
│  - Determine confirmation needed     │
└────────────┬────────────────────────┘
             │
    ┌────────┴────────┐
    │                 │
    ▼                 ▼
┌─────────┐    ┌──────────────┐
│ LOW Risk│    │  HIGH Risk    │
│ Auto-   │    │  Confirmation │
│ Execute │    │  Required    │
└────┬────┘    └──────┬───────┘
     │                │
     │                ▼
     │        ┌──────────────┐
     │        │ UI Shows      │
     │        │ Approve/     │
     │        │ Reject        │
     │        └──────┬───────┘
     │               │
     │               ▼
     │        ┌──────────────┐
     │        │ User Confirms│
     │        └──────┬───────┘
     │               │
     └───────┬───────┘
             │
             ▼
┌─────────────────────────────────────┐
│  3. EXECUTE PHASE                   │
│  execute_planned_tools()            │
│  - Execute tool handlers            │
│  - Capture interactions             │
│  - Track costs                      │
│  - Return results                   │
└────────────┬────────────────────────┘
             │
             ▼
         Results
```

---

## Voice Call Flow (Realtime API)

```
┌─────────────────────────────────────────────────────────────────┐
│                    Voice Call Flow (Inbound)                    │
└─────────────────────────────────────────────────────────────────┘

User Calls Twilio Number
    │
    ▼
┌─────────────────┐
│  Twilio         │
│  Receives Call  │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────────┐
│  POST /webhooks/twilio/voice        │
│  - Validates signature              │
│  - Creates Media Stream              │
└────────────┬────────────────────────┘
             │
             ▼
┌─────────────────────────────────────┐
│  Media Stream WebSocket             │
│  - Connects to server               │
│  - Sends audio (8kHz µ-law)         │
└────────────┬────────────────────────┘
             │
             ▼
┌─────────────────────────────────────┐
│  Realtime Bridge                    │
│  - Converts 8kHz → 24kHz            │
│  - Connects to OpenAI Realtime API  │
└────────────┬────────────────────────┘
             │
             ▼
┌─────────────────────────────────────┐
│  OpenAI Realtime API                │
│  - Processes audio                   │
│  - Generates response               │
│  - Returns audio (24kHz PCM16)      │
└────────────┬────────────────────────┘
             │
             ▼
┌─────────────────────────────────────┐
│  Realtime Bridge                    │
│  - Converts 24kHz → 8kHz            │
│  - Encodes to µ-law                 │
└────────────┬────────────────────────┘
             │
             ▼
┌─────────────────────────────────────┐
│  Media Stream WebSocket             │
│  - Sends audio to Twilio            │
└────────────┬────────────────────────┘
             │
             ▼
┌─────────────────┐
│  Twilio         │
│  Plays Audio    │
└────────┬────────┘
         │
         ▼
      User Hears Response
```

---

## Tool Execution Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                      Tool Execution Flow                        │
└─────────────────────────────────────────────────────────────────┘

AI Decides to Use Tool
    │
    ▼
┌─────────────────────────────────────┐
│  conversation.item.requires_action   │
│  Event (Realtime API)                │
│  OR                                  │
│  planned_tool_calls (Chat API)       │
└────────────┬────────────────────────┘
             │
             ▼
┌─────────────────────────────────────┐
│  Policy Check                       │
│  decide_confirmation()               │
│  - tool_risk() classification       │
│  - is_godfather() check             │
└────────────┬────────────────────────┘
             │
    ┌────────┴────────┐
    │                 │
    ▼                 ▼
┌─────────┐    ┌──────────────┐
│ LOW Risk│    │  HIGH Risk    │
│ Execute │    │  Ask User     │
│ Now     │    │  Confirm        │
└────┬────┘    └──────┬───────┘
     │                │
     │                ▼
     │        ┌──────────────┐
     │        │ "Should I    │
     │        │  call John?" │
     │        └──────┬───────┘
     │               │
     │               ▼
     │        ┌──────────────┐
     │        │ User: "Yes"  │
     │        └──────┬───────┘
     │               │
     └───────┬───────┘
             │
             ▼
┌─────────────────────────────────────┐
│  Execute Tool Handler                │
│  TOOL_HANDLERS[tool_name]()         │
│  - make_call()                       │
│  - send_sms()                        │
│  - send_email()                      │
│  - web_research()                    │
└────────────┬────────────────────────┘
             │
             ▼
┌─────────────────────────────────────┐
│  Capture Interaction                 │
│  - Store in database                 │
│  - Update memory                     │
│  - Log for audit                     │
└────────────┬────────────────────────┘
             │
             ▼
┌─────────────────────────────────────┐
│  Return Result                       │
│  - Submit to OpenAI                  │
│  - Update task status                │
│  - Notify user                       │
└─────────────────────────────────────┘
```

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      System Architecture                        │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                          Frontend Layer                          │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐      │
│  │Dashboard │  │  Tasks   │  │ Calendar │  │ Contacts │      │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘      │
│                                                                  │
│  React + TypeScript + Tailwind CSS                              │
│  React Query for data fetching                              │
└─────────────────────────────────────────────────────────────────┘
                            │
                            │ HTTP/REST
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                          API Layer                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐        │
│  │  /api/tasks  │  │ /api/contacts│  │ /api/calendar│        │
│  └──────────────┘  └──────────────┘  └──────────────┘        │
│                                                                  │
│  FastAPI + Pydantic + SQLAlchemy                                │
└─────────────────────────────────────────────────────────────────┘
                            │
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
        ▼                   ▼                   ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│   Agent      │  │ Orchestrator │  │   Memory     │
│   System     │  │   Service    │  │   Service    │
└──────────────┘  └──────────────┘  └──────────────┘
        │                   │                   │
        │                   │                   │
        └───────────────────┼───────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                        Database Layer                            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐        │
│  │    Tasks     │  │   Contacts   │  │ Interactions│        │
│  └──────────────┘  └──────────────┘  └──────────────┘        │
│                                                                  │
│  SQLite (dev) / PostgreSQL (prod)                              │
└─────────────────────────────────────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
        ▼                   ▼                   ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│   OpenAI     │  │    Twilio    │  │    Email      │
│   (AI/LLM)   │  │  (Voice/SMS) │  │  (Gmail/...)  │
└──────────────┘  └──────────────┘  └──────────────┘
```

---

## Data Flow: Task Creation

```
┌─────────────────────────────────────────────────────────────────┐
│                    Task Creation Data Flow                     │
└─────────────────────────────────────────────────────────────────┘

User Input
    │
    ▼
┌─────────────────────────────────────┐
│  Frontend: TaskInput Component       │
│  - User types task                  │
│  - Submits via useCreateTask()      │
└────────────┬────────────────────────┘
             │
             ▼
┌─────────────────────────────────────┐
│  POST /api/tasks/                   │
│  {task: "...", context: {...}}      │
└────────────┬────────────────────────┘
             │
             ▼
┌─────────────────────────────────────┐
│  Enhance Context                    │
│  - Get contact memory               │
│  - Resolve preferences              │
│  - Add orchestrator suggestions     │
└────────────┬────────────────────────┘
             │
             ▼
┌─────────────────────────────────────┐
│  Plan Task                          │
│  assistant.plan_task()              │
│  - OpenAI Chat Completion           │
│  - Function calling enabled          │
│  - Returns planned_tool_calls        │
└────────────┬────────────────────────┘
             │
             ▼
┌─────────────────────────────────────┐
│  Policy Check                       │
│  decide_confirmation()               │
│  - Classify risk                    │
│  - Check actor                      │
└────────────┬────────────────────────┘
             │
             ▼
┌─────────────────────────────────────┐
│  Create Task Record                 │
│  - Store in database                │
│  - Set status (awaiting_confirmation│
│    or processing)                   │
└────────────┬────────────────────────┘
             │
             ▼
┌─────────────────────────────────────┐
│  Return Task Response               │
│  {task_id, status, plan, ...}       │
└────────────┬────────────────────────┘
             │
             ▼
┌─────────────────────────────────────┐
│  Frontend: TaskCard Component       │
│  - Display task status              │
│  - Show confirmation UI if needed   │
└─────────────────────────────────────┘
```

---

## Security Policy Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                    Security Policy Flow                         │
└─────────────────────────────────────────────────────────────────┘

Action Requested
    │
    ▼
┌─────────────────────────────────────┐
│  Identify Actor                    │
│  Actor(kind, phone, email)         │
└────────────┬────────────────────────┘
             │
             ▼
┌─────────────────────────────────────┐
│  Check Godfather Identity           │
│  is_godfather(actor)                │
│  - Check phone allowlist            │
│  - Check email allowlist            │
└────────────┬────────────────────────┘
             │
    ┌────────┴────────┐
    │                 │
    ▼                 ▼
┌─────────┐    ┌──────────────┐
│Godfather│    │   External   │
└────┬────┘    └──────┬───────┘
     │                │
     │                │
     └───────┬────────┘
             │
             ▼
┌─────────────────────────────────────┐
│  Classify Tool Risk                 │
│  tool_risk(tool_name)               │
│  - HIGH: calls, SMS, email, calendar│
│  - LOW: web_research                │
└────────────┬────────────────────────┘
             │
    ┌────────┴────────┐
    │                 │
    ▼                 ▼
┌─────────┐    ┌──────────────┐
│ LOW Risk│    │  HIGH Risk   │
└────┬────┘    └──────┬───────┘
     │                │
     │                ▼
     │        ┌──────────────┐
     │        │ Confirmation │
     │        │ Required     │
     │        └──────┬───────┘
     │               │
     │               ▼
     │        ┌──────────────┐
     │        │ Godfather?   │
     │        └──────┬───────┘
     │               │
     │        ┌──────┴───────┐
     │        │              │
     │        ▼              ▼
     │    ┌──────┐      ┌──────────┐
     │    │ Yes  │      │   No     │
     │    │ Allow│      │  Block   │
     │    └──────┘      └──────────┘
     │
     └───────▶ Auto-Execute
```

---

## Memory System Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                      Memory System Flow                         │
└─────────────────────────────────────────────────────────────────┘

Interaction Occurs
    │
    ▼
┌─────────────────────────────────────┐
│  Capture Interaction               │
│  - SMS, Email, or Call              │
│  - Store raw content                │
│  - Extract metadata                 │
└────────────┬────────────────────────┘
             │
             ▼
┌─────────────────────────────────────┐
│  Store in Database                  │
│  - Interaction table                │
│  - Link to contact                  │
│  - Timestamp, channel, content     │
└────────────┬────────────────────────┘
             │
             ▼
┌─────────────────────────────────────┐
│  Generate Summary (Background)     │
│  - OpenAI generates summary         │
│  - Extract key points               │
│  - Update sentiment                 │
└────────────┬────────────────────────┘
             │
             ▼
┌─────────────────────────────────────┐
│  Update Memory State                │
│  - Latest summary                   │
│  - Sentiment trend                  │
│  - Relationship status              │
└────────────┬────────────────────────┘
             │
             ▼
┌─────────────────────────────────────┐
│  Retrieve for Context               │
│  - get_contact_memory()             │
│  - Enhance task context              │
│  - Provide to AI                    │
└─────────────────────────────────────┘
```

---

## Integration Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Integration Architecture                     │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                    Application Core                             │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │  VoiceAssistant                                           │ │
│  │  - plan_task()                                            │ │
│  │  - execute_planned_tools()                               │ │
│  └──────────────────────────────────────────────────────────┘ │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │  OrchestratorService                                      │ │
│  │  - generate_suggestions()                                │ │
│  │  - generate_project_plan()                               │ │
│  └──────────────────────────────────────────────────────────┘ │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │  MemoryService                                            │ │
│  │  - store_interaction()                                   │ │
│  │  - get_contact_memory()                                 │ │
│  └──────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
        ▼                   ▼                   ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│   OpenAI     │  │    Twilio    │  │    Email     │
│              │  │              │  │              │
│  - Chat API  │  │  - Voice     │  │  - Gmail     │
│  - Realtime  │  │  - SMS       │  │  - Outlook   │
│  - TTS/STT   │  │  - Media     │  │  - SMTP      │
└──────────────┘  └──────────────┘  └──────────────┘
```

---

## Webhook Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                        Webhook Flow                             │
└─────────────────────────────────────────────────────────────────┘

External Service Event
    │
    ▼
┌─────────────────────────────────────┐
│  POST /webhooks/{service}/{type}    │
│  - Twilio: /webhooks/twilio/voice   │
│  - Twilio: /webhooks/twilio/sms    │
└────────────┬────────────────────────┘
             │
             ▼
┌─────────────────────────────────────┐
│  Validate Signature                 │
│  - RequestValidator (Twilio)        │
│  - Verify authenticity              │
└────────────┬────────────────────────┘
             │
             ▼
┌─────────────────────────────────────┐
│  Process Event                      │
│  - Extract data                     │
│  - Route to handler                 │
└────────────┬────────────────────────┘
             │
             ▼
┌─────────────────────────────────────┐
│  Handler Logic                      │
│  - Voice: Create Media Stream       │
│  - SMS: Store message              │
│  - Status: Update call status       │
└────────────┬────────────────────────┘
             │
             ▼
┌─────────────────────────────────────┐
│  Capture Interaction                │
│  - Store in database                │
│  - Update memory                     │
└────────────┬────────────────────────┘
             │
             ▼
┌─────────────────────────────────────┐
│  Return Response                    │
│  - TwiML (for Twilio)               │
│  - 200 OK                           │
└─────────────────────────────────────┘
```

---

## Cost Tracking Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                      Cost Tracking Flow                        │
└─────────────────────────────────────────────────────────────────┘

API Call Initiated
    │
    ▼
┌─────────────────────────────────────┐
│  Estimate Cost                      │
│  CostEstimator.estimate_task_cost()│
│  - Calculate tokens                │
│  - Apply pricing                   │
└────────────┬────────────────────────┘
             │
             ▼
┌─────────────────────────────────────┐
│  Check Budget                       │
│  BudgetManager.check_budget()       │
│  - Verify sufficient budget         │
│  - Block if exceeded               │
└────────────┬────────────────────────┘
             │
             ▼
┌─────────────────────────────────────┐
│  Execute API Call                   │
│  - OpenAI API                       │
│  - Twilio API                       │
│  - Other services                   │
└────────────┬────────────────────────┘
             │
             ▼
┌─────────────────────────────────────┐
│  Log Cost Event                     │
│  CostEventLogger.log_cost_event()   │
│  - Record actual cost               │
│  - Store in database                │
└────────────┬────────────────────────┘
             │
             ▼
┌─────────────────────────────────────┐
│  Update Runtime Tracker             │
│  RuntimeCostTracker                 │
│  - Track live costs                 │
│  - Calculate projections            │
└────────────┬────────────────────────┘
             │
             ▼
┌─────────────────────────────────────┐
│  Return Cost Info                   │
│  - Estimated cost                   │
│  - Actual cost                      │
│  - Projected cost                   │
└─────────────────────────────────────┘
```

---

## Component Relationships

```
┌─────────────────────────────────────────────────────────────────┐
│                    Component Relationships                      │
└─────────────────────────────────────────────────────────────────┘

                    ┌──────────────┐
                    │   Frontend   │
                    │   (React)    │
                    └──────┬───────┘
                           │
                           ▼
                    ┌──────────────┐
                    │  API Routes  │
                    │  (FastAPI)   │
                    └──────┬───────┘
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
        ▼                  ▼                  ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│   Agent      │  │ Orchestrator │  │   Memory     │
│              │  │              │  │              │
│  - Tools     │  │  - Planning  │  │  - Storage   │
│  - Planning  │  │  - Scheduling│  │  - Retrieval  │
└──────┬───────┘  └──────┬───────┘  └──────┬───────┘
       │                 │                  │
       │                 │                  │
       └─────────────────┼──────────────────┘
                         │
                         ▼
                  ┌──────────────┐
                  │  Database    │
                  │  (SQLite/PG)│
                  └──────────────┘
                         │
        ┌────────────────┼────────────────┐
        │                │                │
        ▼                ▼                ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│   OpenAI     │  │    Twilio   │  │    Email     │
└──────────────┘  └──────────────┘  └──────────────┘
```

---

## Related Documentation

- [Security Policy](SECURITY_POLICY.md) - Security architecture
- [Error Codes](ERROR_CODES.md) - Error handling
- [OpenAI Voice Documentation](OPENAI_VOICE_DOCUMENTATION.md) - Voice API details
- [Twilio Documentation](TWILIO_DOCUMENTATION.md) - Twilio integration
- [Agent Planning Framework](agent.md) - Development framework

---

**Last Updated**: 2025-01-29  
**Maintained By**: Development Team

