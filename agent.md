# AI Agent Planning Framework

**Purpose**: This document ensures all feature requests and implementations are thoroughly analyzed, designed, and executed with complete consideration of user experience, technical architecture, and edge cases. **Never implement features "half-assed"** - always think through the complete picture.

---

## 1. REQUEST ANALYSIS & UNDERSTANDING

Before writing any code, answer these questions:

### 1.1 Core Understanding
- [ ] **What is the user actually trying to accomplish?** (Not just what they asked for, but the underlying goal)
- [ ] **What problem does this solve?** (Is it a real pain point or a nice-to-have?)
- [ ] **Who is the primary user?** (End user, admin, system, etc.)
- [ ] **What is the current state?** (What exists today that this will replace or enhance?)
- [ ] **What is the desired end state?** (What does success look like?)

### 1.2 Scope Definition
- [ ] **What is explicitly in scope?** (List all features/components)
- [ ] **What is explicitly out of scope?** (What are we NOT building?)
- [ ] **Are there related features that should be built together?** (Dependencies, logical groupings)
- [ ] **Are there future enhancements to consider?** (Even if not building now, design for extensibility)

### 1.3 User Stories & Scenarios
- [ ] **Primary user flow**: Step-by-step happy path
- [ ] **Alternative flows**: Different ways users might accomplish the same goal
- [ ] **Error scenarios**: What happens when things go wrong?
- [ ] **Edge cases**: Unusual but valid inputs/behaviors
- [ ] **Integration scenarios**: How does this interact with existing features?

---

## 2. USER EXPERIENCE (UX) DESIGN

### 2.1 User Journey Mapping
- [ ] **Entry point**: Where/how does the user discover/access this feature?
- [ ] **Onboarding**: If new, how do users learn about it? (Tooltips, help text, tutorials)
- [ ] **Primary actions**: What are the main things users will do?
- [ ] **Feedback mechanisms**: How do users know their action succeeded/failed?
- [ ] **Exit points**: Where do users go after completing the task?

### 2.2 Information Architecture
- [ ] **What information needs to be displayed?** (Data, status, history, etc.)
- [ ] **What information needs to be collected?** (Forms, inputs, selections)
- [ ] **Information hierarchy**: What's most important? What's secondary?
- [ ] **Data relationships**: How does this data relate to other features? (Contacts, tasks, calendar, etc.)

### 2.3 Interaction Design
- [ ] **Input methods**: Text, voice, clicks, drag-and-drop, etc.
- [ ] **Response time expectations**: Instant, loading states, async operations
- [ ] **Confirmation patterns**: When do we need explicit confirmation? (High-risk actions)
- [ ] **Undo/redo capabilities**: Can users reverse actions?
- [ ] **Multi-step flows**: If complex, how do we break it into manageable steps?

### 2.4 Accessibility & Inclusivity
- [ ] **Keyboard navigation**: Can users navigate without a mouse?
- [ ] **Screen reader support**: Are labels, ARIA attributes, and semantic HTML used?
- [ ] **Color contrast**: Does it meet WCAG standards?
- [ ] **Mobile responsiveness**: How does it work on small screens?
- [ ] **Error messages**: Are they clear, actionable, and accessible?

### 2.5 Visual Design Consistency
- [ ] **Design system alignment**: Does it match existing UI patterns?
- [ ] **Component reuse**: Can we use existing components? (Buttons, cards, modals, etc.)
- [ ] **Dark theme support**: Does it work with the current dark theme?
- [ ] **Spacing & layout**: Consistent with existing pages?

---

## 3. USER INTERFACE (UI) REQUIREMENTS

### 3.1 Component Inventory
- [ ] **New components needed**: List all new React components
- [ ] **Existing components to modify**: What needs to change?
- [ ] **Component hierarchy**: Parent-child relationships
- [ ] **State management**: Local state vs. global state (React Query, Context, etc.)
- [ ] **React Query integration**: Does this need `useQuery` or `useMutation`? (Check `frontend/src/lib/hooks.ts` for patterns)
- [ ] **Custom hooks**: Should this logic be extracted to a custom hook?

### 3.2 Page Structure (if new page)
- [ ] **Route definition**: What URL path? (`/new-feature`)
- [ ] **Navigation integration**: Add to Navbar? BottomNav? Both?
- [ ] **Layout structure**: Header, content area, sidebar, footer?
- [ ] **Mobile layout**: How does it adapt?

### 3.3 Data Display
- [ ] **Lists/tables**: How to display collections? (Pagination, filtering, sorting)
- [ ] **Empty states**: What shows when there's no data?
- [ ] **Loading states**: Skeletons, spinners, progress indicators
- [ ] **Error states**: How to display errors to users?
- [ ] **Success states**: Confirmation messages, toast notifications

### 3.4 Forms & Inputs
- [ ] **Form validation**: Client-side and server-side
- [ ] **Error handling**: Field-level and form-level errors
- [ ] **Input types**: Text, select, date, file upload, etc.
- [ ] **Auto-save**: Should forms save automatically?
- [ ] **Draft handling**: Can users save incomplete forms?

### 3.5 Real-time Updates
- [ ] **WebSocket/polling**: Does data need to update in real-time?
- [ ] **Optimistic updates**: Should UI update immediately before server confirms?
- [ ] **Conflict resolution**: What if data changes while user is editing?
- [ ] **React Query patterns**: Use `useQuery` for fetching, `useMutation` for mutations
- [ ] **Polling strategy**: Use `refetchInterval` for active states (tasks, messages)
- [ ] **Cache invalidation**: Invalidate queries after mutations (`queryClient.invalidateQueries()`)
- [ ] **Stale time**: Set appropriate `staleTime` based on data freshness needs

---

## 4. BACKEND ARCHITECTURE

### 4.1 API Endpoints
- [ ] **RESTful design**: Proper HTTP methods (GET, POST, PUT, DELETE, PATCH)
- [ ] **Endpoint naming**: Consistent with existing patterns (`/api/{resource}/{id}`)
- [ ] **Request/response models**: Pydantic models for validation
- [ ] **Query parameters**: Filtering, pagination, sorting
- [ ] **Path parameters**: Resource IDs, nested resources

### 4.2 Business Logic
- [ ] **Service layer**: Where does business logic live? (`src/orchestrator/`, `src/services/`)
- [ ] **Orchestration**: Does this need the OrchestratorService?
- [ ] **AI integration**: Does this need OpenAI calls? (Planning, execution, suggestions)
- [ ] **External APIs**: Twilio, email providers, calendar APIs, etc.

### 4.3 Data Processing
- [ ] **Data transformation**: Input sanitization, normalization
- [ ] **Validation rules**: Business rules, constraints
- [ ] **Computation**: Calculations, aggregations, derivations
- [ ] **Background tasks**: Async processing needed? (Celery, background workers)

### 4.4 Integration Points
- [ ] **Memory system**: Does this interact with `MemoryService`?
- [ ] **Contact system**: Does this relate to contacts?
- [ ] **Task system**: Does this create/update tasks?
- [ ] **Calendar system**: Does this interact with calendar?
- [ ] **Messaging system**: Does this send/receive messages?
- [ ] **Cost tracking**: Does this need cost monitoring?

### 4.5 Plan → Confirm → Execute Workflow (CRITICAL)
- [ ] **Planning phase**: Does this need `assistant.plan_task()`? (No side effects)
- [ ] **Confirmation required**: Does this involve high-risk tools? (`make_call`, `send_sms`, `send_email`, `calendar_*`)
- [ ] **Policy integration**: Does this need `decide_confirmation()` from `src/security/policy.py`?
- [ ] **Tool risk classification**: Is this tool classified in `tool_risk()`? (HIGH vs LOW risk)
- [ ] **Execution phase**: Does this need `execute_planned_tools()`? (Only after confirmation)
- [ ] **UI confirmation flow**: Does frontend need to show "awaiting_confirmation" state with Approve/Reject buttons?

### 4.6 Godfather Identity System
- [ ] **Actor identification**: Does this need to identify the actor? (`Actor` from `src/security/policy.py`)
- [ ] **Godfather verification**: Does this need `is_godfather(actor)` check?
- [ ] **Phone/email allowlist**: Does this interact with Godfather allowlist? (`src/security/godfather_store.py`)
- [ ] **External caller handling**: How are external callers handled differently?

### 4.7 Cost Tracking Integration
- [ ] **Cost estimation**: Does this need `CostEstimator` for upfront estimates?
- [ ] **Runtime cost tracking**: Does this need `RuntimeCostTracker` for live cost updates?
- [ ] **Cost event logging**: Does this need `CostEventLogger` to log cost events?
- [ ] **Budget management**: Does this need `BudgetManager` for budget checks?
- [ ] **OpenAI instrumentation**: Does this make OpenAI calls that need `OpenAIInstrumentation`?
- [ ] **Cost display**: Should costs be shown to users in UI?

---

## 5. DATA MODELS & DATABASE

### 5.1 Database Schema
- [ ] **New tables**: What new tables are needed?
- [ ] **Table relationships**: Foreign keys, many-to-many, one-to-many
- [ ] **Indexes**: What fields need indexes for performance?
- [ ] **Constraints**: Unique constraints, check constraints, NOT NULL
- [ ] **Migrations**: Alembic migration files

### 5.2 SQLAlchemy Models
- [ ] **Model definition**: `src/database/models.py`
- [ ] **Relationships**: `relationship()`, `ForeignKey()`
- [ ] **Serialization**: How to convert to/from JSON?
- [ ] **Validation**: Pydantic models for API validation

### 5.3 Data Lifecycle
- [ ] **Creation**: How is data created? (User input, system-generated, imported)
- [ ] **Updates**: What fields can be updated? When?
- [ ] **Deletion**: Soft delete or hard delete? Cascade rules?
- [ ] **Archival**: Does old data need to be archived?

### 5.4 Data Integrity
- [ ] **Referential integrity**: Foreign key constraints
- [ ] **Data consistency**: Transactions, rollbacks
- [ ] **Concurrency**: Handling simultaneous updates
- [ ] **Data migration**: If changing existing schema, migration plan

---

## 6. API DESIGN

### 6.1 Request/Response Format
- [ ] **Request body structure**: JSON schema
- [ ] **Response structure**: Consistent format (success/error)
- [ ] **Error responses**: Standardized error format
- [ ] **Pagination**: If returning lists, pagination structure

### 6.2 Authentication & Authorization
- [ ] **Authentication**: Does this require auth? (Session, JWT, API key)
- [ ] **Authorization**: Who can access? (User roles, permissions)
- [ ] **Security policy**: Does this need `decide_confirmation()`? (High-risk actions - see section 4.5)
- [ ] **Godfather verification**: Does this need to verify Godfather identity? (`is_godfather()`)
- [ ] **Actor identification**: Does this need to identify the actor? (`Actor` with phone/email)
- [ ] **Rate limiting**: Should endpoints be rate-limited?
- [ ] **Webhook security**: If handling webhooks, signature validation required (Twilio, etc.)

### 6.3 Validation
- [ ] **Input validation**: Pydantic models, field validators
- [ ] **Business rule validation**: Custom validators
- [ ] **Error messages**: Clear, actionable error messages
- [ ] **Validation order**: Client-side first, then server-side

### 6.4 API Documentation
- [ ] **OpenAPI/Swagger**: Auto-generated docs
- [ ] **Endpoint descriptions**: What each endpoint does
- [ ] **Parameter documentation**: What each parameter means
- [ ] **Example requests/responses**: Real examples

---

## 7. SECURITY & PRIVACY

### 7.1 Data Security
- [ ] **Sensitive data**: PII, phone numbers, emails - how is it protected?
- [ ] **Encryption**: At rest? In transit? (HTTPS, database encryption)
- [ ] **Data access**: Who can see what data?
- [ ] **Audit logging**: Should actions be logged for security?

### 7.2 Input Security
- [ ] **SQL injection**: Parameterized queries
- [ ] **XSS prevention**: Input sanitization, output encoding
- [ ] **CSRF protection**: Tokens, same-site cookies
- [ ] **File upload security**: Validation, scanning, storage

### 7.3 API Security
- [ ] **Authentication**: How are requests authenticated?
- [ ] **Authorization**: Role-based access control
- [ ] **Rate limiting**: Prevent abuse
- [ ] **Webhook security**: Signature validation (Twilio, etc.)

### 7.4 Privacy Considerations
- [ ] **Data collection**: What data is collected? Why?
- [ ] **Data retention**: How long is data kept?
- [ ] **User consent**: Do users need to opt-in?
- [ ] **GDPR/compliance**: Does this affect compliance?

---

## 8. ERROR HANDLING & EDGE CASES

### 8.1 Error Categories
- [ ] **User errors**: Invalid input, missing required fields
- [ ] **System errors**: Database failures, API timeouts
- [ ] **External service errors**: Twilio, OpenAI, email provider failures
- [ ] **Network errors**: Connection issues, timeouts

### 8.2 Error Handling Strategy
- [ ] **Error messages**: User-friendly, actionable messages (use `get_openai_error_message()` for OpenAI errors)
- [ ] **Error logging**: Detailed logs for debugging (use `get_logger()` from `src/utils/logging`)
- [ ] **Error recovery**: Retry logic, fallback behaviors (use `retry_openai_call()` decorator for OpenAI)
- [ ] **Error reporting**: How are errors surfaced to users?
- [ ] **OpenAI-specific errors**: Handle `RateLimitError`, `APIConnectionError`, `APITimeoutError`, `APIError`
- [ ] **Twilio-specific errors**: Handle `TwilioException`, `TwilioRestException` with proper error codes
- [ ] **Retry strategy**: Exponential backoff with jitter, respect `retry-after` headers

### 8.3 Edge Cases
- [ ] **Empty data**: What if no data exists?
- [ ] **Large datasets**: Performance with thousands of records
- [ ] **Concurrent modifications**: Multiple users editing same data
- [ ] **Partial failures**: What if some steps succeed but others fail?
- [ ] **Timeout scenarios**: Long-running operations
- [ ] **Invalid states**: Data in unexpected states

### 8.4 Validation Edge Cases
- [ ] **Boundary values**: Min/max, empty strings, null values
- [ ] **Special characters**: Unicode, emojis, SQL injection attempts
- [ ] **Very long inputs**: Text length limits
- [ ] **Malformed data**: Invalid JSON, wrong data types

---

## 9. INTEGRATION POINTS

### 9.1 Existing Systems
- [ ] **Memory Service**: Does this need to read/write memory? (`MemoryService.store_interaction()`, `get_contact_memory()`)
- [ ] **Orchestrator Service**: Does this need orchestration? (`OrchestratorService` for suggestions, project planning)
- [ ] **Contact System**: Does this interact with contacts? (Contact CRUD, contact parsing)
- [ ] **Task System**: Does this create/update tasks? (Task lifecycle, status tracking)
- [ ] **Calendar System**: Does this interact with calendar? (Google Calendar integration)
- [ ] **Messaging System**: Does this send messages? (SMS, email via messaging service)
- [ ] **Cost Tracking**: Does this need cost monitoring? (See section 4.7)
- [ ] **Preference Resolver**: Does this need user preferences? (`PreferenceResolver.resolve_preferences()`)
- [ ] **Commitment Manager**: Does this track commitments? (`CommitmentManager` for contact commitments)
- [ ] **Scheduler**: Does this need scheduling? (`Scheduler` for task scheduling)

### 9.2 External Services
- [ ] **Twilio**: Voice calls, SMS (via `TwilioClient`, webhook signature validation required)
- [ ] **OpenAI**: AI planning, execution, suggestions (with retry logic, cost tracking)
- [ ] **Email providers**: Gmail (OAuth), Outlook (OAuth), SMTP (fallback)
- [ ] **Calendar providers**: Google Calendar (OAuth integration)
- [ ] **Other APIs**: Any third-party integrations?

### 9.3 Voice & Telephony Considerations
- [ ] **Voice calls**: Does this involve voice calls? (Inbound/outbound via Twilio)
- [ ] **Realtime API**: Does this need OpenAI Realtime API? (`src/voice/realtime_bridge.py`)
- [ ] **Media streaming**: Does this handle audio streaming? (`src/telephony/media_stream.py`)
- [ ] **Webhook handling**: Does this handle Twilio webhooks? (Signature validation required)
- [ ] **Call state management**: Does this track call states? (Ringing, in-progress, completed)
- [ ] **Voice input/output**: Does this process voice input or generate voice output?

### 9.4 Integration Patterns
- [ ] **Synchronous**: Immediate response required
- [ ] **Asynchronous**: Background processing (`src/memory/background_tasks.py`, `src/messaging/background_tasks.py`)
- [ ] **Webhooks**: Incoming webhooks to handle (Twilio signature validation required)
- [ ] **Polling**: Periodic checks for updates
- [ ] **Event-driven**: React to events from other systems
- [ ] **Interaction capture**: Does this need to capture interactions for memory? (`capture_sms_interaction()`, `capture_email_interaction()`)

### 9.5 Data Flow
- [ ] **Data sources**: Where does data come from?
- [ ] **Data transformations**: How is data transformed?
- [ ] **Data destinations**: Where does data go?
- [ ] **Data sync**: Does data need to stay in sync?
- [ ] **Memory enrichment**: Does context need to be enhanced with memory? (`_enhance_context_with_memory()`)
- [ ] **Preference context**: Does this need preference resolution? (`PreferenceResolver.resolve_preferences()`)

---

## 10. PERFORMANCE CONSIDERATIONS

### 10.1 Database Performance
- [ ] **Query optimization**: Efficient queries, proper indexes
- [ ] **N+1 queries**: Avoid loading related data in loops
- [ ] **Pagination**: Limit result sets
- [ ] **Caching**: Can data be cached? (Redis, in-memory)

### 10.2 API Performance
- [ ] **Response time**: Target response times
- [ ] **Async operations**: Background processing for long tasks
- [ ] **Rate limiting**: Prevent abuse
- [ ] **Connection pooling**: Database, HTTP clients

### 10.3 Frontend Performance
- [ ] **Bundle size**: Code splitting, lazy loading
- [ ] **Rendering optimization**: React.memo, useMemo, useCallback
- [ ] **Image optimization**: Lazy loading, proper formats
- [ ] **API calls**: Debouncing, request deduplication

### 10.4 Scalability
- [ ] **Horizontal scaling**: Can this scale across multiple servers?
- [ ] **State management**: Stateless design where possible
- [ ] **Resource limits**: Memory, CPU, database connections

---

## 11. TESTING STRATEGY

### 11.1 Unit Tests
- [ ] **Backend functions**: Test individual functions/methods
- [ ] **Frontend components**: Test component rendering, interactions
- [ ] **Business logic**: Test core logic in isolation
- [ ] **Edge cases**: Test boundary conditions

### 11.2 Integration Tests
- [ ] **API endpoints**: Test full request/response cycle
- [ ] **Database operations**: Test CRUD operations
- [ ] **External services**: Mock external API calls
- [ ] **Component integration**: Test component interactions

### 11.3 End-to-End Tests
- [ ] **User flows**: Test complete user journeys
- [ ] **Cross-browser**: Test in different browsers
- [ ] **Mobile**: Test on mobile devices
- [ ] **Accessibility**: Test with screen readers

### 11.4 Test Data
- [ ] **Fixtures**: Reusable test data
- [ ] **Factories**: Generate test data programmatically
- [ ] **Mocking**: Mock external services
- [ ] **Cleanup**: Ensure tests don't leave data behind

---

## 12. DOCUMENTATION

### 12.1 Code Documentation
- [ ] **Docstrings**: All functions, classes, methods
- [ ] **Type hints**: Python type hints, TypeScript types
- [ ] **Comments**: Complex logic explained
- [ ] **README updates**: Update main README if needed

### 12.2 API Documentation
- [ ] **OpenAPI spec**: Auto-generated from code
- [ ] **Endpoint descriptions**: What each endpoint does
- [ ] **Example requests**: cURL, JavaScript examples
- [ ] **Error responses**: Documented error codes

### 12.3 User Documentation
- [ ] **Feature description**: What the feature does
- [ ] **How-to guides**: Step-by-step instructions
- [ ] **FAQ**: Common questions
- [ ] **Screenshots**: Visual documentation

### 12.4 Internal Documentation
- [ ] **Architecture decisions**: Why certain choices were made
- [ ] **Integration notes**: How to integrate with this feature
- [ ] **Troubleshooting**: Common issues and solutions

---

## 13. DEPLOYMENT CONSIDERATIONS

### 13.1 Environment Configuration
- [ ] **Environment variables**: What new env vars are needed?
- [ ] **Configuration files**: Updates to `config/default.yaml`
- [ ] **Secrets management**: API keys, credentials
- [ ] **Feature flags**: Should this be feature-flagged?

### 13.2 Database Migrations
- [ ] **Migration files**: Alembic migrations
- [ ] **Migration strategy**: How to deploy without downtime?
- [ ] **Rollback plan**: How to rollback if issues occur?
- [ ] **Data migration**: If migrating existing data

### 13.3 Deployment Process
- [ ] **Build process**: Any new build steps?
- [ ] **Docker**: Updates to Dockerfile if needed
- [ ] **Vercel**: Updates to vercel.json if needed
- [ ] **CI/CD**: Test automation, deployment automation

### 13.4 Monitoring & Observability
- [ ] **Logging**: What should be logged?
- [ ] **Metrics**: What metrics should be tracked?
- [ ] **Alerts**: What should trigger alerts?
- [ ] **Error tracking**: Sentry, error monitoring

---

## 14. IMPLEMENTATION CHECKLIST

Before marking a feature as "complete", verify:

### 14.1 Functionality
- [ ] **Core feature works**: Happy path tested
- [ ] **Edge cases handled**: Error scenarios tested
- [ ] **Integration works**: All integrations tested
- [ ] **Performance acceptable**: Meets performance targets

### 14.2 User Experience
- [ ] **UI is intuitive**: Users can figure it out
- [ ] **Feedback is clear**: Users know what's happening
- [ ] **Errors are helpful**: Error messages guide users
- [ ] **Mobile responsive**: Works on mobile devices

### 14.3 Code Quality
- [ ] **Code is clean**: Readable, maintainable
- [ ] **Tests pass**: All tests green
- [ ] **No linter errors**: Code follows style guide
- [ ] **Documentation complete**: Code and user docs updated

### 14.4 Security & Privacy
- [ ] **Security reviewed**: No obvious vulnerabilities
- [ ] **Privacy considered**: Data handling is appropriate
- [ ] **Authentication/authorization**: Properly implemented
- [ ] **Input validation**: All inputs validated

### 14.5 Deployment Ready
- [ ] **Environment configured**: All env vars documented
- [ ] **Migrations ready**: Database migrations tested
- [ ] **Monitoring set up**: Logging and metrics configured
- [ ] **Rollback plan**: Know how to rollback if needed

---

## 15. POST-IMPLEMENTATION

### 15.1 User Feedback
- [ ] **Gather feedback**: How are users using it?
- [ ] **Identify issues**: What problems are users encountering?
- [ ] **Measure success**: Are users achieving their goals?

### 15.2 Iteration Planning
- [ ] **Improvements identified**: What could be better?
- [ ] **Technical debt**: What shortcuts need to be fixed?
- [ ] **Future enhancements**: What's next?

---

## USAGE INSTRUCTIONS

**When receiving a feature request:**

1. **Read the request carefully** and use this framework to analyze it
2. **Go through each section** and answer the questions
3. **Create a comprehensive plan** before writing any code
4. **Share the plan** with the user if needed for confirmation
5. **Implement systematically** following the plan
6. **Verify completion** using the implementation checklist

**Remember**: It's better to spend time planning upfront than to implement something incomplete and have to redo it later. **Never implement features "half-assed"** - always think through the complete picture.

---

## QUICK REFERENCE: COMMON PATTERNS

### Adding a New Page
1. Create page component in `frontend/src/pages/`
2. Add route in `frontend/src/App.tsx`
3. Add navigation link in `Navbar` or `BottomNav`
4. Create API endpoints in `src/api/routes/`
5. Add database models if needed
6. Update documentation

### Adding a New API Endpoint
1. Define Pydantic models for request/response
2. Create route handler in appropriate router (`src/api/routes/`)
3. Implement business logic in service layer
4. Add database operations if needed
5. Add error handling (use structured error responses)
6. Add cost tracking if making OpenAI/external API calls
7. Add memory capture if interacting with contacts
8. Update OpenAPI docs
9. Add tests

### Adding a New Tool (AI Function Calling)
1. Implement tool handler in `src/agent/tools.py`
2. Add tool schema to `TOOLS` array (JSON schema format)
3. Add handler to `TOOL_HANDLERS` dictionary
4. Classify risk in `src/security/policy.py` → `tool_risk()` (HIGH or LOW)
5. Update `decide_confirmation()` if needed
6. Add cost tracking if tool makes external API calls
7. Add memory capture if tool interacts with contacts
8. Add error handling with `TaskError` for user-facing errors
9. Add tests with mocks for external services

### Adding a New Database Table
1. Create SQLAlchemy model in `src/database/models.py`
2. Create Alembic migration
3. Update API models if needed
4. Add CRUD operations
5. Add tests

### Integrating with External Service
1. Check existing integrations in `src/integrations/`
2. Add connection handling (`src/integrations/connections.py`, `manager.py`)
3. Add error handling and retries (`src/integrations/retry.py`)
4. Add cost tracking if applicable (`CostEventLogger`, `RuntimeCostTracker`)
5. Add OAuth flow if needed (Gmail, Outlook, Google Calendar)
6. Add webhook handling if needed (signature validation for Twilio)
7. Add tests with mocks

### Adding Memory Integration
1. Determine if feature interacts with contacts
2. Use `MemoryService.store_interaction()` to store interactions
3. Use `MemoryService.get_contact_memory()` to retrieve context
4. Enhance task context with `_enhance_context_with_memory()` in task creation
5. Capture interactions from tool results using `capture_sms_interaction()` or `capture_email_interaction()`
6. Consider commitment tracking if feature involves promises/commitments

### Adding React Query Hooks
1. Check `frontend/src/lib/hooks.ts` for existing patterns
2. Use `useQuery` for data fetching (with appropriate `queryKey`, `queryFn`)
3. Use `useMutation` for mutations (with `onSuccess` to invalidate queries)
4. Set `refetchInterval` for active/polling data (tasks, messages)
5. Set `staleTime` based on data freshness needs (30s for calendar, 10s for messages)
6. Use `enabled` to conditionally fetch (e.g., only if calendar connected)
7. Handle errors appropriately (`retry: false` for user-facing errors)
8. Invalidate related queries after mutations

---

---

## PROJECT-SPECIFIC ARCHITECTURE PATTERNS

### Plan → Confirm → Execute Workflow
This is the **core pattern** for all AI-driven actions:

1. **Plan Phase** (`assistant.plan_task()`):
   - AI analyzes request and generates tool calls
   - NO side effects - only planning
   - Returns `planned_tool_calls` array
   - Cost estimation performed

2. **Confirm Phase** (`decide_confirmation()`):
   - Policy engine evaluates risk of planned tools
   - HIGH-risk tools (calls, SMS, email, calendar) → require confirmation
   - LOW-risk tools (web research) → can auto-execute
   - Godfather vs external caller distinction

3. **Execute Phase** (`execute_planned_tools()`):
   - Only runs after confirmation (or for LOW-risk)
   - Executes tool handlers
   - Captures interactions for memory
   - Tracks costs in real-time
   - Returns results

**UI Pattern**: Tasks in `awaiting_confirmation` state show Approve/Reject buttons.

### Tool Risk Classification
All tools must be classified in `src/security/policy.py`:

- **HIGH-risk**: `make_call`, `send_sms`, `send_email`, `calendar_*` events
- **LOW-risk**: `web_research` (read-only operations)

Unknown tools default to HIGH-risk until reviewed.

### Cost Tracking Pattern
Every OpenAI/external API call should track costs:

1. **Estimation**: `CostEstimator.estimate_task_cost()` before execution
2. **Runtime tracking**: `RuntimeCostTracker` during execution
3. **Event logging**: `CostEventLogger.log_cost_event()` for each API call
4. **Budget checks**: `BudgetManager.check_budget()` before expensive operations
5. **Instrumentation**: `OpenAIInstrumentation` decorator for automatic tracking

### Memory Integration Pattern
When interacting with contacts:

1. **Enhance context**: Add `contact_memory` to task context before planning
2. **Store interactions**: Capture all SMS/email/call interactions
3. **Retrieve memory**: Use `MemoryService.get_contact_memory()` for context
4. **Update summaries**: Memory service auto-generates summaries periodically
5. **Track commitments**: Use `CommitmentManager` for promises made

### Godfather Identity System
- **Actor identification**: Every action has an `Actor` (godfather or external)
- **Verification**: `is_godfather(actor)` checks phone/email allowlist
- **Policy**: External callers can never auto-execute HIGH-risk tools
- **Storage**: Godfather identity stored in `secrets/godfather.json` (gitignored)

### Error Handling Patterns
- **OpenAI errors**: Use `retry_openai_call()` decorator with exponential backoff
- **Twilio errors**: Handle specific error codes (20000-21608 range)
- **User-facing errors**: Use `TaskError` with clear messages
- **Logging**: Use structured logging with `get_logger()`
- **Retry logic**: Respect `retry-after` headers, max retries, jitter

---

**Last Updated**: 2025-01-29
**Version**: 1.1

