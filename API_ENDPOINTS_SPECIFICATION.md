# API Endpoints Specification for Call Center Manager Dashboard

This document defines all API endpoints required for the Call Center Manager Dashboard, including existing endpoints that need implementation and new endpoints to be created.

---

## Base URL

```
Production: https://api.yourdomain.com/api/v1
Development: http://localhost:8000/api/v1
```

---

## Authentication

All endpoints (except login) require authentication via JWT token:

```
Authorization: Bearer <token>
```

---

## 1. Call Management Endpoints

### 1.1 List Calls

**GET** `/calls`

Get a paginated list of calls with filtering and sorting options.

**Query Parameters:**
```typescript
{
  page?: number          // Default: 1
  limit?: number         // Default: 50, Max: 100
  status?: CallStatus    // 'initiated' | 'ringing' | 'in_progress' | 'completed' | 'failed' | 'escalated'
  direction?: 'inbound' | 'outbound'
  business_id?: string
  from_date?: string     // ISO 8601 date
  to_date?: string       // ISO 8601 date
  search?: string        // Search by phone number or call ID
  sort_by?: string       // 'started_at' | 'duration' | 'qa_score'
  sort_order?: 'asc' | 'desc'
  min_qa_score?: number  // Filter by minimum QA score
  max_qa_score?: number  // Filter by maximum QA score
  sentiment?: 'positive' | 'neutral' | 'negative'
}
```

**Response:**
```typescript
{
  calls: Call[]
  pagination: {
    page: number
    limit: number
    total: number
    total_pages: number
  }
}

interface Call {
  id: string
  twilio_call_sid: string
  direction: 'inbound' | 'outbound'
  status: CallStatus
  from_number: string
  to_number: string
  business_id?: string
  template_id?: string
  started_at: string        // ISO 8601
  ended_at?: string         // ISO 8601
  duration_seconds?: number
  created_at: string
  updated_at: string
  metadata: Record<string, any>
  // Computed fields
  qa_score?: number
  sentiment?: 'positive' | 'neutral' | 'negative'
  escalation_status?: 'pending' | 'in_progress' | 'completed'
  assigned_agent?: {
    id: string
    name: string
  }
}
```

**Status Codes:**
- `200 OK` - Success
- `400 Bad Request` - Invalid query parameters
- `401 Unauthorized` - Missing or invalid token
- `500 Internal Server Error`

---

### 1.2 Get Call Details

**GET** `/calls/{call_id}`

Get detailed information about a specific call.

**Path Parameters:**
- `call_id` (string, required) - Call ID

**Response:**
```typescript
{
  call: Call
  interactions_count: number
  qa_scores?: QAScore
  escalation?: Escalation
  agent?: HumanAgent
}

interface QAScore {
  id: number
  call_id: string
  overall_score: number
  sentiment_score: number
  compliance_score: number
  accuracy_score: number
  professionalism_score: number
  sentiment_label: 'positive' | 'neutral' | 'negative'
  compliance_issues: string[]
  flagged_issues: string[]
  reviewed_by: string
  review_notes?: string
  created_at: string
  updated_at: string
}

interface Escalation {
  id: number
  call_id: string
  status: 'pending' | 'in_progress' | 'completed' | 'cancelled'
  trigger_type: string
  trigger_details: Record<string, any>
  assigned_agent_id?: string
  agent_name?: string
  conversation_summary?: string
  context_data: Record<string, any>
  requested_at: string
  accepted_at?: string
  completed_at?: string
}
```

**Status Codes:**
- `200 OK` - Success
- `404 Not Found` - Call not found
- `401 Unauthorized`
- `500 Internal Server Error`

---

### 1.3 Get Call Interactions (Transcript)

**GET** `/calls/{call_id}/interactions`

Get the full transcript/interactions for a call.

**Path Parameters:**
- `call_id` (string, required)

**Query Parameters:**
```typescript
{
  limit?: number         // Default: 1000
  offset?: number        // Default: 0
  speaker?: 'ai' | 'customer'
}
```

**Response:**
```typescript
{
  interactions: CallInteraction[]
  total: number
}

interface CallInteraction {
  id: number
  call_id: string
  speaker: 'ai' | 'customer'
  text: string
  audio_url?: string
  timestamp: string      // ISO 8601
  metadata: Record<string, any>
  // Computed fields
  sentiment?: {
    score: number
    label: 'positive' | 'neutral' | 'negative'
  }
}
```

**Status Codes:**
- `200 OK` - Success
- `404 Not Found` - Call not found
- `401 Unauthorized`
- `500 Internal Server Error`

---

### 1.4 Initiate Outbound Call

**POST** `/calls/initiate`

Initiate a new outbound call.

**Request Body:**
```typescript
{
  to_number: string      // Required
  from_number?: string   // Optional, uses default if not provided
  business_id?: string
  template_id?: string
  metadata?: Record<string, any>
}
```

**Response:**
```typescript
{
  call: Call
  message: string
}
```

**Status Codes:**
- `201 Created` - Call initiated
- `400 Bad Request` - Invalid request
- `401 Unauthorized`
- `500 Internal Server Error`

---

### 1.5 Escalate Call

**POST** `/calls/{call_id}/escalate`

Escalate a call to a human agent.

**Path Parameters:**
- `call_id` (string, required)

**Request Body:**
```typescript
{
  agent_id?: string      // Optional, auto-assigns if not provided
  reason?: string
  context_note?: string
}
```

**Response:**
```typescript
{
  escalation: Escalation
  message: string
}
```

**Status Codes:**
- `200 OK` - Escalation successful
- `400 Bad Request` - Invalid request or no available agents
- `404 Not Found` - Call not found
- `401 Unauthorized`
- `500 Internal Server Error`

---

### 1.6 Intervene in Call

**POST** `/calls/{call_id}/intervene`

Intervene in an active call (send message to AI, pause, etc.).

**Path Parameters:**
- `call_id` (string, required)

**Request Body:**
```typescript
{
  action: 'send_message' | 'pause' | 'resume' | 'override_instructions'
  message?: string       // Required for 'send_message'
  instructions?: string  // Required for 'override_instructions'
}
```

**Response:**
```typescript
{
  success: boolean
  message: string
}
```

**Status Codes:**
- `200 OK` - Intervention successful
- `400 Bad Request` - Invalid action or missing parameters
- `404 Not Found` - Call not found
- `401 Unauthorized`
- `500 Internal Server Error`

---

### 1.7 End Call

**POST** `/calls/{call_id}/end`

Forcefully end an active call.

**Path Parameters:**
- `call_id` (string, required)

**Request Body:**
```typescript
{
  reason?: string
  notes?: string
}
```

**Response:**
```typescript
{
  success: boolean
  message: string
  call: Call              // Updated call with ended_at
}
```

**Status Codes:**
- `200 OK` - Call ended
- `404 Not Found` - Call not found
- `401 Unauthorized`
- `500 Internal Server Error`

---

### 1.8 Add Note to Call

**POST** `/calls/{call_id}/notes`

Add a manager note to a call.

**Path Parameters:**
- `call_id` (string, required)

**Request Body:**
```typescript
{
  note: string           // Required
  tags?: string[]        // Optional tags
  category?: string      // Optional category
}
```

**Response:**
```typescript
{
  success: boolean
  note_id: number
  message: string
}
```

**Status Codes:**
- `201 Created` - Note added
- `400 Bad Request` - Invalid request
- `404 Not Found` - Call not found
- `401 Unauthorized`
- `500 Internal Server Error`

---

## 2. Real-Time WebSocket Endpoints

### 2.1 WebSocket Connection

**WS** `/ws/calls`

WebSocket endpoint for real-time call updates.

**Connection:**
```
wss://api.yourdomain.com/ws/calls?token=<jwt_token>
```

**Client → Server Events:**

**Subscribe to all calls:**
```typescript
{
  event: 'subscribe',
  data: { type: 'all_calls' }
}
```

**Subscribe to specific call:**
```typescript
{
  event: 'subscribe',
  data: { type: 'call', call_id: string }
}
```

**Unsubscribe:**
```typescript
{
  event: 'unsubscribe',
  data: { type: 'call' | 'all_calls', call_id?: string }
}
```

**Server → Client Events:**

**Call Started:**
```typescript
{
  event: 'call.started',
  data: {
    call: Call
  }
}
```

**Call Updated:**
```typescript
{
  event: 'call.updated',
  data: {
    call: Call
  }
}
```

**Call Ended:**
```typescript
{
  event: 'call.ended',
  data: {
    call_id: string
  }
}
```

**Interaction Added:**
```typescript
{
  event: 'interaction.added',
  data: {
    call_id: string
    interaction: CallInteraction
  }
}
```

**QA Score Updated:**
```typescript
{
  event: 'qa.score.updated',
  data: {
    call_id: string
    qa_score: QAScore
  }
}
```

**Sentiment Changed:**
```typescript
{
  event: 'sentiment.changed',
  data: {
    call_id: string
    sentiment: {
      score: number
      label: 'positive' | 'neutral' | 'negative'
    }
  }
}
```

**Escalation Triggered:**
```typescript
{
  event: 'escalation.triggered',
  data: {
    call_id: string
    escalation: Escalation
  }
}
```

**Escalation Completed:**
```typescript
{
  event: 'escalation.completed',
  data: {
    call_id: string
    escalation: Escalation
  }
}
```

---

## 3. Analytics Endpoints

### 3.1 Dashboard Overview

**GET** `/analytics/overview`

Get overview metrics for the dashboard.

**Query Parameters:**
```typescript
{
  from_date?: string     // ISO 8601, default: 7 days ago
  to_date?: string       // ISO 8601, default: now
  business_id?: string
}
```

**Response:**
```typescript
{
  total_calls: number
  active_calls: number
  completed_calls: number
  failed_calls: number
  escalated_calls: number
  average_qa_score: number
  average_call_duration: number      // seconds
  escalation_rate: number            // percentage
  sentiment_distribution: {
    positive: number
    neutral: number
    negative: number
  }
  qa_score_distribution: {
    excellent: number    // >= 0.8
    good: number         // 0.6-0.79
    fair: number         // 0.4-0.59
    poor: number         // < 0.4
  }
}
```

**Status Codes:**
- `200 OK` - Success
- `401 Unauthorized`
- `500 Internal Server Error`

---

### 3.2 Call Volume Over Time

**GET** `/analytics/call-volume`

Get call volume statistics over time.

**Query Parameters:**
```typescript
{
  from_date: string      // Required
  to_date: string        // Required
  interval: 'hour' | 'day' | 'week' | 'month'  // Default: 'day'
  business_id?: string
  direction?: 'inbound' | 'outbound'
}
```

**Response:**
```typescript
{
  data: Array<{
    period: string       // ISO 8601 or formatted date
    total_calls: number
    inbound_calls: number
    outbound_calls: number
    completed_calls: number
    escalated_calls: number
  }>
}
```

**Status Codes:**
- `200 OK` - Success
- `400 Bad Request` - Invalid date range
- `401 Unauthorized`
- `500 Internal Server Error`

---

### 3.3 QA Statistics

**GET** `/analytics/qa`

Get QA score statistics.

**Query Parameters:**
```typescript
{
  from_date?: string
  to_date?: string
  business_id?: string
}
```

**Response:**
```typescript
{
  average_scores: {
    overall: number
    sentiment: number
    compliance: number
    accuracy: number
    professionalism: number
  }
  score_distribution: Array<{
    range: string        // e.g., "0.8-1.0"
    count: number
    percentage: number
  }>
  trends: Array<{
    period: string
    average_score: number
  }>
  top_issues: Array<{
    issue: string
    count: number
    percentage: number
  }>
}
```

**Status Codes:**
- `200 OK` - Success
- `401 Unauthorized`
- `500 Internal Server Error`

---

### 3.4 Sentiment Analysis

**GET** `/analytics/sentiment`

Get sentiment analysis statistics.

**Query Parameters:**
```typescript
{
  from_date?: string
  to_date?: string
  business_id?: string
}
```

**Response:**
```typescript
{
  distribution: {
    positive: number
    neutral: number
    negative: number
  }
  average_sentiment_score: number
  trends: Array<{
    period: string
    positive: number
    neutral: number
    negative: number
    average_score: number
  }>
  correlation: {
    sentiment_vs_qa: number      // Correlation coefficient
    sentiment_vs_escalation: number
  }
}
```

**Status Codes:**
- `200 OK` - Success
- `401 Unauthorized`
- `500 Internal Server Error`

---

### 3.5 Escalation Statistics

**GET** `/analytics/escalations`

Get escalation statistics.

**Query Parameters:**
```typescript
{
  from_date?: string
  to_date?: string
  business_id?: string
}
```

**Response:**
```typescript
{
  total_escalations: number
  escalation_rate: number        // percentage
  by_trigger_type: Array<{
    trigger_type: string
    count: number
    percentage: number
  }>
  by_status: {
    pending: number
    in_progress: number
    completed: number
    cancelled: number
  }
  average_resolution_time: number  // seconds
  trends: Array<{
    period: string
    escalation_count: number
    escalation_rate: number
  }>
}
```

**Status Codes:**
- `200 OK` - Success
- `401 Unauthorized`
- `500 Internal Server Error`

---

### 3.6 Export Analytics

**POST** `/analytics/export`

Export analytics data as CSV or PDF.

**Request Body:**
```typescript
{
  format: 'csv' | 'pdf'
  report_type: 'overview' | 'calls' | 'qa' | 'sentiment' | 'escalations' | 'full'
  from_date?: string
  to_date?: string
  business_id?: string
  include_charts?: boolean      // For PDF only
}
```

**Response:**
- For CSV: Returns file download
- For PDF: Returns file download or URL

**Status Codes:**
- `200 OK` - File generated
- `400 Bad Request` - Invalid parameters
- `401 Unauthorized`
- `500 Internal Server Error`

---

## 4. Configuration Endpoints

### 4.1 List Business Configurations

**GET** `/config/business`

Get list of business configurations.

**Query Parameters:**
```typescript
{
  is_active?: boolean
}
```

**Response:**
```typescript
{
  configs: BusinessConfig[]
}

interface BusinessConfig {
  id: string
  name: string
  type: string
  config_data: {
    ai: {
      model: string
      temperature: number
      system_prompt: string
    }
    voice: {
      language: string
      voice: string
      response_delay: number
    }
    knowledge_base: {
      enabled: boolean
      retrieval_top_k: number
      similarity_threshold: number
    }
    quality_assurance: {
      enabled: boolean
      sentiment_analysis: boolean
      compliance_check: boolean
      min_score_threshold: number
    }
    escalation: {
      enabled: boolean
      triggers: Array<{
        type: string
        threshold?: number
        keywords?: string[]
      }>
      warm_transfer: boolean
    }
  }
  is_active: boolean
  created_at: string
  updated_at: string
}
```

**Status Codes:**
- `200 OK` - Success
- `401 Unauthorized`
- `500 Internal Server Error`

---

### 4.2 Get Business Configuration

**GET** `/config/business/{business_id}`

Get a specific business configuration.

**Response:**
```typescript
{
  config: BusinessConfig
}
```

**Status Codes:**
- `200 OK` - Success
- `404 Not Found` - Config not found
- `401 Unauthorized`
- `500 Internal Server Error`

---

### 4.3 Create/Update Business Configuration

**POST** `/config/business`
**PUT** `/config/business/{business_id}`

Create or update a business configuration.

**Request Body:**
```typescript
{
  name: string           // Required
  type: string           // Required
  config_data: {
    // Same structure as BusinessConfig.config_data
  }
  is_active?: boolean
}
```

**Response:**
```typescript
{
  config: BusinessConfig
  message: string
}
```

**Status Codes:**
- `201 Created` - Config created (POST)
- `200 OK` - Config updated (PUT)
- `400 Bad Request` - Invalid data
- `401 Unauthorized`
- `500 Internal Server Error`

---

### 4.4 Delete Business Configuration

**DELETE** `/config/business/{business_id}`

Delete a business configuration.

**Response:**
```typescript
{
  success: boolean
  message: string
}
```

**Status Codes:**
- `200 OK` - Config deleted
- `404 Not Found` - Config not found
- `401 Unauthorized`
- `400 Bad Request` - Config in use
- `500 Internal Server Error`

---

## 5. Knowledge Base Endpoints

### 5.1 List Knowledge Entries

**GET** `/knowledge`

Get list of knowledge base entries.

**Query Parameters:**
```typescript
{
  business_id?: string
  page?: number
  limit?: number
  search?: string
}
```

**Response:**
```typescript
{
  entries: KnowledgeEntry[]
  pagination: {
    page: number
    limit: number
    total: number
    total_pages: number
  }
}

interface KnowledgeEntry {
  id: number
  business_id?: string
  title: string
  content: string
  source?: string
  source_type?: string
  vector_id?: string
  metadata: Record<string, any>
  created_at: string
  updated_at: string
}
```

**Status Codes:**
- `200 OK` - Success
- `401 Unauthorized`
- `500 Internal Server Error`

---

### 5.2 Add Knowledge Entry

**POST** `/knowledge`

Add a new knowledge base entry.

**Request Body:**
```typescript
{
  business_id?: string
  title: string           // Required
  content: string         // Required
  source?: string
  source_type?: string
  metadata?: Record<string, any>
}
```

**Response:**
```typescript
{
  entry: KnowledgeEntry
  message: string
}
```

**Status Codes:**
- `201 Created` - Entry created
- `400 Bad Request` - Invalid data
- `401 Unauthorized`
- `500 Internal Server Error`

---

### 5.3 Upload Document

**POST** `/knowledge/upload`

Upload a document to the knowledge base.

**Request:**
- Content-Type: `multipart/form-data`
- Body:
  - `file`: File (PDF, DOCX, TXT)
  - `business_id?`: string
  - `title?`: string

**Response:**
```typescript
{
  entry: KnowledgeEntry
  message: string
  processing_status: 'processing' | 'completed' | 'failed'
}
```

**Status Codes:**
- `202 Accepted` - Upload accepted, processing
- `400 Bad Request` - Invalid file
- `401 Unauthorized`
- `500 Internal Server Error`

---

### 5.4 Delete Knowledge Entry

**DELETE** `/knowledge/{entry_id}`

Delete a knowledge base entry.

**Response:**
```typescript
{
  success: boolean
  message: string
}
```

**Status Codes:**
- `200 OK` - Entry deleted
- `404 Not Found` - Entry not found
- `401 Unauthorized`
- `500 Internal Server Error`

---

## 6. Agent Management Endpoints

### 6.1 List Agents

**GET** `/agents`

Get list of human agents.

**Query Parameters:**
```typescript
{
  is_active?: boolean
  is_available?: boolean
}
```

**Response:**
```typescript
{
  agents: HumanAgent[]
}

interface HumanAgent {
  id: string
  name: string
  email: string
  phone_number?: string
  extension?: string
  is_available: boolean
  is_active: boolean
  skills: string[]
  departments: string[]
  total_calls_handled: number
  average_rating?: number
  created_at: string
  updated_at: string
  last_active_at?: string
  metadata: Record<string, any>
}
```

**Status Codes:**
- `200 OK` - Success
- `401 Unauthorized`
- `500 Internal Server Error`

---

### 6.2 Get Agent

**GET** `/agents/{agent_id}`

Get a specific agent.

**Response:**
```typescript
{
  agent: HumanAgent
}
```

**Status Codes:**
- `200 OK` - Success
- `404 Not Found` - Agent not found
- `401 Unauthorized`
- `500 Internal Server Error`

---

### 6.3 Create/Update Agent

**POST** `/agents`
**PUT** `/agents/{agent_id}`

Create or update an agent.

**Request Body:**
```typescript
{
  name: string           // Required
  email: string          // Required
  phone_number?: string
  extension?: string
  skills?: string[]
  departments?: string[]
  is_available?: boolean
  is_active?: boolean
  metadata?: Record<string, any>
}
```

**Response:**
```typescript
{
  agent: HumanAgent
  message: string
}
```

**Status Codes:**
- `201 Created` - Agent created (POST)
- `200 OK` - Agent updated (PUT)
- `400 Bad Request` - Invalid data
- `401 Unauthorized`
- `500 Internal Server Error`

---

### 6.4 Delete Agent

**DELETE** `/agents/{agent_id}`

Delete an agent.

**Response:**
```typescript
{
  success: boolean
  message: string
}
```

**Status Codes:**
- `200 OK` - Agent deleted
- `404 Not Found` - Agent not found
- `401 Unauthorized`
- `400 Bad Request` - Agent has active escalations
- `500 Internal Server Error`

---

### 6.5 Update Agent Availability

**PATCH** `/agents/{agent_id}/availability`

Update agent availability status.

**Request Body:**
```typescript
{
  is_available: boolean
}
```

**Response:**
```typescript
{
  agent: HumanAgent
  message: string
}
```

**Status Codes:**
- `200 OK` - Availability updated
- `404 Not Found` - Agent not found
- `401 Unauthorized`
- `500 Internal Server Error`

---

## 7. Error Response Format

All error responses follow this format:

```typescript
{
  error: {
    code: string         // Error code (e.g., "CALL_NOT_FOUND")
    message: string      // Human-readable message
    details?: any        // Additional error details
  }
}
```

**Common Error Codes:**
- `UNAUTHORIZED` - Missing or invalid authentication
- `FORBIDDEN` - Insufficient permissions
- `NOT_FOUND` - Resource not found
- `VALIDATION_ERROR` - Invalid request data
- `INTERNAL_ERROR` - Server error

---

## 8. Rate Limiting

API endpoints are rate-limited:
- **Standard endpoints:** 100 requests per minute per user
- **WebSocket connections:** 10 concurrent connections per user
- **Analytics endpoints:** 20 requests per minute per user

Rate limit headers:
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1640995200
```

---

## 9. Pagination

All list endpoints support pagination:

**Query Parameters:**
- `page`: Page number (default: 1)
- `limit`: Items per page (default: 50, max: 100)

**Response includes:**
```typescript
{
  pagination: {
    page: number
    limit: number
    total: number
    total_pages: number
    has_next: boolean
    has_prev: boolean
  }
}
```

---

## 10. Implementation Priority

### Phase 1 (Critical - Week 1):
1. ✅ GET `/calls` - List calls
2. ✅ GET `/calls/{call_id}` - Get call details
3. ✅ GET `/calls/{call_id}/interactions` - Get transcript
4. ✅ POST `/calls/{call_id}/escalate` - Escalate call
5. ✅ WebSocket `/ws/calls` - Real-time updates

### Phase 2 (High Priority - Week 2):
6. ✅ GET `/analytics/overview` - Dashboard metrics
7. ✅ GET `/analytics/call-volume` - Call volume stats
8. ✅ POST `/calls/{call_id}/intervene` - Intervene
9. ✅ POST `/calls/{call_id}/notes` - Add note
10. ✅ GET `/config/business` - List configs

### Phase 3 (Medium Priority - Week 3):
11. ✅ GET `/analytics/qa` - QA statistics
12. ✅ GET `/analytics/sentiment` - Sentiment stats
13. ✅ GET `/agents` - List agents
14. ✅ POST `/agents` - Create agent
15. ✅ GET `/knowledge` - List knowledge entries

### Phase 4 (Nice to Have - Week 4):
16. ✅ POST `/analytics/export` - Export reports
17. ✅ POST `/knowledge/upload` - Upload documents
18. ✅ POST `/calls/initiate` - Initiate outbound call
19. ✅ POST `/calls/{call_id}/end` - End call

---

## Conclusion

This API specification provides a complete set of endpoints for the Call Center Manager Dashboard. All endpoints should be implemented with proper error handling, validation, and documentation.

