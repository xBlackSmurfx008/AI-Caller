# Call Center Manager Dashboard - Comprehensive UI/UX Plan

## Executive Summary

This document outlines the complete user interface and user experience design for the Call Center Manager Dashboard. The dashboard enables managers/owners to **setup**, **handle**, and **monitor** all aspects of the AI-powered call center system with real-time visibility into every conversation.

---

## 1. User Persona & Goals

### Primary User: Call Center Manager/Owner

**Goals:**
- Monitor all active and historical calls in real-time
- Visually see exactly what's happening in each conversation
- Quickly intervene when needed (escalate, take over, provide guidance)
- Configure and customize the AI system for their business
- Track performance metrics and quality assurance scores
- Manage human agents and escalations
- Maintain knowledge base and business templates

**Key Requirements:**
- **Real-time updates** - No page refresh needed
- **Visual clarity** - Instant understanding of call status, sentiment, issues
- **Quick actions** - One-click intervention capabilities
- **Comprehensive view** - See everything at a glance, drill down for details
- **Mobile responsive** - Access from any device

---

## 2. System Architecture Overview

### Current Backend Capabilities
- ✅ Call management (inbound/outbound)
- ✅ Real-time conversation tracking (CallInteraction model)
- ✅ QA monitoring (sentiment analysis, compliance checking)
- ✅ Escalation management
- ✅ Knowledge base (RAG system)
- ✅ Business configuration templates
- ✅ Human agent management

### Required Frontend Architecture
- **Real-time WebSocket connection** for live updates
- **REST API integration** for all operations
- **State management** for call data, filters, UI state
- **Component-based UI** (React/Vue recommended)
- **Responsive design** framework

---

## 3. User Flow: Setup Phase

### 3.1 Initial Setup Wizard

**Flow:**
1. **Welcome & Onboarding**
   - System overview
   - Quick tour of key features
   - Skip option for experienced users

2. **API Configuration**
   - OpenAI API key setup
   - Twilio credentials (Account SID, Auth Token, Phone Number)
   - Connection testing
   - Webhook URL configuration

3. **Business Profile Setup**
   - Business name and type
   - Select or create business template:
     - Customer Support
     - Sales
     - Appointments
     - Custom
   - Configure AI personality and voice settings

4. **Knowledge Base Setup**
   - Upload documents (PDF, DOCX, TXT)
   - Add URLs for web scraping
   - Configure RAG settings (top_k, similarity threshold)
   - Test knowledge retrieval

5. **Human Agents Setup**
   - Add agent profiles (name, email, phone, extension)
   - Configure agent skills/departments
   - Set availability status
   - Test escalation routing

6. **Quality Assurance Configuration**
   - Enable/disable QA features
   - Set sentiment thresholds
   - Configure compliance rules
   - Set minimum score thresholds

7. **Escalation Rules**
   - Configure escalation triggers:
     - Sentiment threshold
     - Keywords list
     - Complexity threshold
   - Set warm transfer preferences
   - Test escalation flow

8. **Final Review & Launch**
   - Review all configurations
   - Test complete call flow
   - Go live

**UI Components:**
- Multi-step wizard with progress indicator
- Form validation and error handling
- Connection testing indicators
- Preview/test panels
- Save draft functionality

---

## 4. User Flow: Handle Phase (Active Call Management)

### 4.1 Main Dashboard View

**Layout:**
```
┌─────────────────────────────────────────────────────────────┐
│  Header: Logo | Search | Notifications | User Profile      │
├─────────────────────────────────────────────────────────────┤
│  [Active Calls] [Queue] [Agents] [Analytics] [Settings]    │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────────┐  ┌──────────────────────────────────┐ │
│  │  Active Calls    │  │   Selected Call Detail View     │ │
│  │  (Left Panel)    │  │   (Right Panel - 60% width)     │ │
│  │                  │  │                                  │ │
│  │  🔴 Call #1234   │  │  ┌────────────────────────────┐ │ │
│  │  📞 +1-555-0100  │  │  │ Call Header & Controls    │ │ │
│  │  ⏱️  5:23        │  │  └────────────────────────────┘ │ │
│  │  😊 Positive     │  │                                  │ │
│  │  ⭐ 0.85 QA      │  │  ┌────────────────────────────┐ │ │
│  │                  │  │  │ Live Transcript (Real-time) │ │ │
│  │  🟡 Call #1235   │  │  │                              │ │ │
│  │  📞 +1-555-0101  │  │  │ Customer: "I need help..." │ │ │
│  │  ⏱️  2:15        │  │  │ AI: "I'd be happy to..."    │ │ │
│  │  😐 Neutral      │  │  │ Customer: "That's great!"  │ │ │
│  │  ⭐ 0.72 QA      │  │  │                              │ │ │
│  │                  │  │  │ [Auto-scrolling]            │ │ │
│  │  🟢 Call #1236   │  │  └────────────────────────────┘ │ │
│  │  📞 +1-555-0102  │  │                                  │ │
│  │  ⏱️  0:45        │  │  ┌────────────────────────────┐ │ │
│  │  😊 Positive     │  │  │ QA Metrics & Alerts        │ │ │
│  │  ⭐ 0.91 QA      │  │  │ Sentiment: 😊 Positive     │ │ │
│  │                  │  │  │ Compliance: ✅ Pass         │ │ │
│  │  [Filters]       │  │  │ Overall Score: 0.85        │ │ │
│  │  [Sort]          │  │  │                            │ │ │
│  │                  │  │  │ ⚠️ Alert: Escalation risk  │ │ │
│  │                  │  │  └────────────────────────────┘ │ │
│  │                  │  │                                  │ │
│  │                  │  │  ┌────────────────────────────┐ │ │
│  │                  │  │  │ Action Buttons              │ │ │
│  │                  │  │  │ [Escalate] [Intervene]     │ │ │
│  │                  │  │  │ [Add Note] [End Call]      │ │ │
│  │                  │  │  └────────────────────────────┘ │ │
│  └──────────────────┘  └──────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### 4.2 Active Calls List (Left Panel - 40% width)

**Features:**
- **Real-time updates** via WebSocket
- **Color-coded status indicators:**
  - 🔴 Red: Needs attention (negative sentiment, low QA, escalation pending)
  - 🟡 Yellow: Warning (neutral sentiment, moderate QA)
  - 🟢 Green: Healthy (positive sentiment, good QA)
  - ⚪ Gray: Completed/Ended

**Display Information:**
- Call ID (clickable)
- Phone numbers (from/to)
- Call duration (live timer)
- Sentiment indicator (😊/😐/😞)
- QA score (0.0-1.0) with color coding
- Escalation status badge
- Business template name
- Time since call started

**Interactive Features:**
- Click to select and view details
- Filter by: Status, Sentiment, QA Score, Business, Agent
- Sort by: Time, Duration, QA Score, Sentiment
- Search by phone number or call ID
- Auto-refresh every 2 seconds (or WebSocket push)

### 4.3 Call Detail View (Right Panel - 60% width)

#### 4.3.1 Call Header Section
**Information Display:**
- Call ID and Twilio Call SID
- Phone numbers (from ↔ to)
- Call direction badge (Inbound/Outbound)
- Business template name
- Current status (In Progress, Escalated, Completed)
- Call duration (live timer)
- Start time and end time (if completed)

**Action Buttons:**
- **🔊 Listen Live** - Stream audio (if available)
- **📞 Escalate** - Transfer to human agent
- **✋ Intervene** - Take control/override AI
- **📝 Add Note** - Add manager notes
- **📊 View Full Report** - Detailed QA report
- **🔚 End Call** - Force end call (admin only)

#### 4.3.2 Live Transcript Section
**Real-time Conversation Display:**
- **Auto-scrolling** transcript window
- **Speaker identification:**
  - Customer: Left-aligned, blue background
  - AI: Right-aligned, gray background
- **Timestamps** for each message
- **Sentiment indicators** per message (if negative, highlight)
- **Keyword highlighting** (escalation triggers, important terms)
- **Scroll lock/unlock** toggle
- **Search within transcript**

**Visual Indicators:**
- ⚠️ Warning icon for negative sentiment messages
- 🚨 Alert icon for escalation triggers
- ✅ Checkmark for compliance-passed AI responses
- ❌ X for compliance issues

#### 4.3.3 QA Metrics Panel
**Real-time Metrics:**
- **Sentiment Score:** -1.0 to +1.0 with visual gauge
  - Color: Red (negative) → Yellow (neutral) → Green (positive)
- **Compliance Score:** 0.0 to 1.0
  - List of compliance issues (if any)
- **Overall QA Score:** 0.0 to 1.0
  - Breakdown: Sentiment (30%), Compliance (30%), Accuracy (20%), Professionalism (20%)
- **Flagged Issues:** List of active flags
  - Negative sentiment
  - Compliance issues
  - Low overall score

**Alerts:**
- ⚠️ Escalation risk warning
- 🚨 Immediate attention needed
- ✅ All systems normal

#### 4.3.4 Context & Metadata Panel
**Display:**
- Conversation summary (auto-generated)
- Knowledge base retrievals (what AI accessed)
- Escalation context (if escalated)
- Assigned agent (if escalated)
- Custom metadata/tags
- Call notes (manager-added)

#### 4.3.5 Action Panel
**Quick Actions:**
- **Escalate to Agent:**
  - Select agent from dropdown
  - Add escalation reason
  - Transfer with context
- **Intervene:**
  - Send message to AI (override instructions)
  - Pause AI responses
  - Resume AI
- **Add Note:**
  - Free-form text
  - Tags/categories
  - Attach to call record
- **End Call:**
  - Confirm dialog
  - Reason selection
  - Final notes

---

## 5. User Flow: Monitor Phase (Analytics & Reporting)

### 5.1 Analytics Dashboard

**Main Metrics Overview:**
```
┌─────────────────────────────────────────────────────────────┐
│  Analytics Dashboard                                          │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐      │
│  │ Total    │ │ Active   │ │ Avg QA   │ │ Escal.   │      │
│  │ Calls    │ │ Calls    │ │ Score    │ │ Rate     │      │
│  │ 1,234    │ │ 12       │ │ 0.82     │ │ 8.5%     │      │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘      │
│                                                               │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ Call Volume Over Time (Chart)                        │   │
│  │ [Line/Bar Chart: Last 7/30/90 days]                 │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                               │
│  ┌──────────────────┐  ┌────────────────────────────────┐  │
│  │ Sentiment        │  │ QA Score Distribution          │  │
│  │ Distribution     │  │ [Histogram/Bar Chart]          │  │
│  │ [Pie Chart]      │  │                                │  │
│  │ 😊 65%           │  │                                │  │
│  │ 😐 25%           │  │                                │  │
│  │ 😞 10%           │  │                                │  │
│  └──────────────────┘  └────────────────────────────────┘  │
│                                                               │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ Top Issues & Escalation Reasons                       │   │
│  │ [Table/List]                                          │   │
│  │ 1. Negative Sentiment (45%)                           │   │
│  │ 2. Keyword Trigger (30%)                              │   │
│  │ 3. High Complexity (25%)                              │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                               │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ Agent Performance                                     │   │
│  │ [Table with metrics per agent]                       │   │
│  │ Name | Calls | Avg Time | Avg Rating | Status        │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

**Key Metrics:**
- **Call Volume:** Total, by day/hour, trends
- **Call Duration:** Average, median, distribution
- **QA Scores:** Average, distribution, trends over time
- **Sentiment Analysis:** Distribution, trends, correlation with outcomes
- **Escalation Rate:** Percentage, reasons, trends
- **Agent Performance:** Calls handled, average time, ratings
- **Business Template Performance:** Compare different templates
- **Knowledge Base Usage:** Most accessed documents, retrieval success rate

**Filters:**
- Date range (Today, Last 7 days, Last 30 days, Custom)
- Business template
- Call direction (Inbound/Outbound)
- Status (All, Completed, Failed, Escalated)
- QA score range
- Sentiment filter

**Export Options:**
- CSV export
- PDF report generation
- Scheduled email reports

### 5.2 Call History & Search

**Features:**
- **Advanced search:**
  - By phone number
  - By call ID
  - By date range
  - By QA score
  - By sentiment
  - By agent (if escalated)
  - Full-text search in transcripts
- **List view:**
  - Paginated table
  - Sortable columns
  - Quick filters
  - Bulk actions
- **Detail view:**
  - Full transcript
  - Complete QA report
  - Audio playback (if available)
  - Export transcript
  - Download call recording

### 5.3 Quality Assurance Reports

**Per-Call QA Report:**
- Overall score breakdown
- Sentiment analysis timeline
- Compliance check results
- Flagged issues with details
- Recommendations for improvement
- Comparison to average scores

**Aggregate QA Reports:**
- Average scores by time period
- Trend analysis
- Issue frequency
- Compliance violation patterns
- Improvement recommendations

---

## 6. Real-Time Features & WebSocket Integration

### 6.1 WebSocket Events

**Client → Server:**
- Subscribe to call updates
- Subscribe to specific call
- Unsubscribe from call
- Request call list refresh

**Server → Client:**
- `call.started` - New call initiated
- `call.updated` - Call status changed
- `call.ended` - Call completed
- `interaction.added` - New transcript entry
- `qa.score.updated` - QA score changed
- `sentiment.changed` - Sentiment updated
- `escalation.triggered` - Escalation initiated
- `escalation.completed` - Escalation resolved
- `agent.status.changed` - Agent availability changed

### 6.2 Real-Time UI Updates

**Auto-updating Elements:**
- Call list (every 2 seconds or on event)
- Selected call transcript (instant on new interaction)
- QA metrics (instant on score update)
- Sentiment indicators (instant on sentiment change)
- Call duration timers (every second)
- Active call count (instant)

**Visual Feedback:**
- Pulsing animation for active calls
- Flash notification for new events
- Sound alerts (optional) for escalations
- Toast notifications for important events

---

## 7. Visual Design Principles

### 7.1 Color Scheme

**Status Colors:**
- 🔴 Red: Critical/Attention needed (negative sentiment, low QA, escalation)
- 🟡 Yellow: Warning (neutral sentiment, moderate QA)
- 🟢 Green: Healthy/Normal (positive sentiment, good QA)
- 🔵 Blue: Informational (in progress, active)
- ⚪ Gray: Inactive/Completed

**UI Colors:**
- Primary: Professional blue (#2563EB)
- Secondary: Dark gray (#1F2937)
- Background: Light gray (#F9FAFB)
- Text: Dark gray (#111827)
- Borders: Light gray (#E5E7EB)

### 7.2 Typography

- **Headers:** Bold, 18-24px
- **Body:** Regular, 14-16px
- **Labels:** Medium, 12-14px
- **Monospace:** For call IDs, phone numbers, timestamps

### 7.3 Icons & Visual Elements

- **Status indicators:** Colored circles/badges
- **Sentiment:** Emoji or icon-based (😊/😐/😞)
- **Actions:** Clear icon + text buttons
- **Loading states:** Skeleton screens, spinners
- **Empty states:** Helpful illustrations and messages

### 7.4 Responsive Design

**Breakpoints:**
- Desktop: 1920px+ (Full dashboard)
- Laptop: 1280px-1919px (Condensed layout)
- Tablet: 768px-1279px (Stacked panels)
- Mobile: <768px (Single panel, tab navigation)

---

## 8. Technical Implementation Requirements

### 8.1 Frontend Stack Recommendations

**Option 1: React + TypeScript**
- React 18+ with hooks
- TypeScript for type safety
- React Query for data fetching
- Zustand/Redux for state management
- Socket.io-client for WebSocket
- Tailwind CSS for styling
- Recharts/Chart.js for analytics

**Option 2: Vue 3 + TypeScript**
- Vue 3 with Composition API
- TypeScript
- Pinia for state management
- VueUse for utilities
- Socket.io-client
- Tailwind CSS
- Chart.js

### 8.2 Required API Endpoints

**Call Management:**
- `GET /api/v1/calls` - List calls (with filters, pagination)
- `GET /api/v1/calls/{call_id}` - Get call details
- `GET /api/v1/calls/{call_id}/interactions` - Get transcript
- `GET /api/v1/calls/{call_id}/qa` - Get QA scores
- `POST /api/v1/calls/initiate` - Initiate outbound call
- `POST /api/v1/calls/{call_id}/escalate` - Escalate call
- `POST /api/v1/calls/{call_id}/intervene` - Intervene in call
- `POST /api/v1/calls/{call_id}/end` - End call
- `POST /api/v1/calls/{call_id}/notes` - Add note

**Real-time:**
- `WS /ws/calls` - WebSocket connection for call updates
- `WS /ws/calls/{call_id}` - WebSocket for specific call

**Analytics:**
- `GET /api/v1/analytics/overview` - Dashboard metrics
- `GET /api/v1/analytics/calls` - Call statistics
- `GET /api/v1/analytics/qa` - QA statistics
- `GET /api/v1/analytics/sentiment` - Sentiment analysis
- `GET /api/v1/analytics/escalations` - Escalation statistics

**Configuration:**
- `GET /api/v1/config/business` - Get business configs
- `POST /api/v1/config/business` - Create/update config
- `GET /api/v1/config/templates` - Get templates
- `GET /api/v1/agents` - List agents
- `POST /api/v1/agents` - Create/update agent
- `GET /api/v1/knowledge` - List knowledge entries
- `POST /api/v1/knowledge` - Add knowledge entry

### 8.3 Database Queries Optimization

**Indexes Required:**
- Calls: status, started_at, business_id
- Interactions: call_id, timestamp
- QA Scores: call_id, overall_score
- Escalations: call_id, status

**Caching Strategy:**
- Redis cache for active calls list
- Cache analytics queries (5-minute TTL)
- Cache business configs
- Real-time data via WebSocket (no cache)

---

## 9. Security & Permissions

### 9.1 Authentication

- JWT-based authentication
- Role-based access control (RBAC)
- Session management

### 9.2 Permission Levels

**Manager/Owner (Full Access):**
- View all calls
- Intervene in any call
- Configure system
- View all analytics
- Manage agents
- Export data

**Supervisor (Limited Access):**
- View assigned calls
- Escalate calls
- View analytics (limited)
- Add notes

**Viewer (Read-Only):**
- View calls (no actions)
- View analytics (no export)

---

## 10. Implementation Phases

### Phase 1: Core Dashboard (Week 1-2)
- Basic layout and navigation
- Call list with real-time updates
- Call detail view with transcript
- WebSocket integration
- Basic API integration

### Phase 2: Real-Time Features (Week 3)
- Live transcript updates
- QA metrics display
- Sentiment indicators
- Action buttons (escalate, intervene)
- WebSocket event handling

### Phase 3: Analytics (Week 4)
- Analytics dashboard
- Charts and visualizations
- Call history and search
- Export functionality

### Phase 4: Configuration UI (Week 5)
- Setup wizard
- Business config management
- Knowledge base UI
- Agent management UI

### Phase 5: Polish & Optimization (Week 6)
- Performance optimization
- Mobile responsiveness
- Error handling
- User testing and refinement

---

## 11. Success Metrics

**User Experience:**
- Time to find specific call: < 5 seconds
- Time to escalate: < 10 seconds
- Dashboard load time: < 2 seconds
- Real-time update latency: < 1 second

**System Performance:**
- Support 100+ concurrent active calls
- Handle 10,000+ calls in history
- WebSocket connection stability: 99.9%
- API response time: < 200ms (p95)

---

## 12. Future Enhancements

- **AI Insights:** Automated recommendations based on call patterns
- **Predictive Analytics:** Forecast call volume, identify trends
- **Custom Dashboards:** User-configurable widget layouts
- **Mobile App:** Native iOS/Android apps
- **Voice Commands:** Voice-controlled dashboard navigation
- **Integration:** CRM integration, Slack notifications, email alerts
- **Advanced Filtering:** Saved filter presets, smart filters
- **Call Recording Playback:** Integrated audio player with transcript sync

---

## Conclusion

This comprehensive plan provides a complete blueprint for building a world-class call center manager dashboard. The focus on **real-time visibility**, **visual clarity**, and **quick actions** ensures managers can effectively monitor and manage their AI-powered call center operations.

The modular architecture allows for incremental implementation, starting with core features and expanding based on user feedback and requirements.

