# Call Center Manager Dashboard - User Flow Diagrams

## Flow 1: Initial Setup & Configuration

```
┌─────────────────────────────────────────────────────────────┐
│                    SETUP FLOW                                │
└─────────────────────────────────────────────────────────────┘

[Start] → Welcome Screen
           │
           ├─→ [Skip Tour] → API Configuration
           │
           └─→ [Take Tour] → Feature Overview
                              │
                              └─→ API Configuration

API Configuration
  │
  ├─→ Enter OpenAI API Key
  │   └─→ [Test Connection] → ✅ Success / ❌ Error
  │
  ├─→ Enter Twilio Credentials
  │   ├─→ Account SID
  │   ├─→ Auth Token
  │   ├─→ Phone Number
  │   └─→ [Test Connection] → ✅ Success / ❌ Error
  │
  └─→ Configure Webhook URL
      └─→ [Test Webhook] → ✅ Success / ❌ Error

Business Profile Setup
  │
  ├─→ Enter Business Name
  │
  ├─→ Select Business Type
  │   ├─→ Customer Support
  │   ├─→ Sales
  │   ├─→ Appointments
  │   └─→ Custom Template
  │
  ├─→ Configure AI Settings
  │   ├─→ Voice Selection (alloy, echo, fable, etc.)
  │   ├─→ Temperature (0.0-1.0)
  │   ├─→ System Prompt
  │   └─→ Response Delay
  │
  └─→ [Save & Continue]

Knowledge Base Setup
  │
  ├─→ Upload Documents
  │   ├─→ PDF, DOCX, TXT files
  │   ├─→ [Upload] → Processing...
  │   └─→ [View Uploaded] → List of documents
  │
  ├─→ Add URLs
  │   ├─→ Enter URL
  │   └─→ [Scrape & Process]
  │
  ├─→ Configure RAG Settings
  │   ├─→ Top K results (default: 5)
  │   ├─→ Similarity threshold (default: 0.7)
  │   └─→ [Test Retrieval] → Sample query test
  │
  └─→ [Save & Continue]

Human Agents Setup
  │
  ├─→ Add Agent
  │   ├─→ Name, Email, Phone
  │   ├─→ Extension (optional)
  │   ├─→ Skills/Departments (tags)
  │   ├─→ Set Availability (Available/Busy/Offline)
  │   └─→ [Save Agent]
  │
  ├─→ [Add Another Agent] → Repeat
  │
  └─→ [Continue] → Review Agent List

QA Configuration
  │
  ├─→ Enable/Disable Features
  │   ├─→ ☑ Sentiment Analysis
  │   ├─→ ☑ Compliance Checking
  │   └─→ ☑ Auto-scoring
  │
  ├─→ Set Thresholds
  │   ├─→ Sentiment Alert: -0.5
  │   ├─→ Minimum QA Score: 0.6
  │   └─→ Compliance Threshold: 0.8
  │
  └─→ [Save & Continue]

Escalation Rules
  │
  ├─→ Configure Triggers
  │   ├─→ Sentiment Trigger
  │   │   └─→ Threshold: -0.5
  │   │
  │   ├─→ Keyword Trigger
  │   │   └─→ Keywords: ["manager", "supervisor", "human"]
  │   │
  │   └─→ Complexity Trigger
  │       └─→ Threshold: 0.8
  │
  ├─→ Warm Transfer Settings
  │   └─→ ☑ Enable warm transfer
  │
  └─→ [Save & Continue]

Final Review
  │
  ├─→ Review All Settings
  │   ├─→ API Configuration ✅
  │   ├─→ Business Profile ✅
  │   ├─→ Knowledge Base ✅
  │   ├─→ Agents ✅
  │   ├─→ QA Settings ✅
  │   └─→ Escalation Rules ✅
  │
  ├─→ [Test Complete Flow] → Test call simulation
  │
  └─→ [Go Live] → System activated
```

---

## Flow 2: Active Call Monitoring & Handling

```
┌─────────────────────────────────────────────────────────────┐
│              ACTIVE CALL MONITORING FLOW                     │
└─────────────────────────────────────────────────────────────┘

Dashboard Load
  │
  ├─→ Connect WebSocket
  │   └─→ Subscribe to call updates
  │
  ├─→ Fetch Active Calls List
  │   └─→ Display in left panel
  │
  └─→ Show Default View (or last selected call)

User Selects Call from List
  │
  └─→ Load Call Details
      │
      ├─→ Fetch Call Info
      │   ├─→ Phone numbers
      │   ├─→ Status, duration
      │   └─→ Business template
      │
      ├─→ Fetch Transcript
      │   └─→ Display in transcript panel
      │
      ├─→ Fetch QA Metrics
      │   └─→ Display scores and alerts
      │
      └─→ Subscribe to Call-Specific WebSocket
          └─→ Real-time updates for this call

Real-Time Updates (WebSocket Events)
  │
  ├─→ New Interaction Added
  │   ├─→ Append to transcript
  │   ├─→ Auto-scroll (if enabled)
  │   └─→ Update sentiment indicator
  │
  ├─→ QA Score Updated
  │   ├─→ Update score displays
  │   ├─→ Update color coding
  │   └─→ Show alert if threshold crossed
  │
  ├─→ Sentiment Changed
  │   ├─→ Update sentiment indicator
  │   └─→ Highlight in transcript
  │
  └─→ Escalation Triggered
      ├─→ Show escalation alert
      ├─→ Update call status
      └─→ Display agent assignment

User Actions

Action: Escalate Call
  │
  ├─→ Click [Escalate] Button
  │
  ├─→ Escalation Modal Opens
  │   ├─→ Select Agent (dropdown)
  │   ├─→ Escalation Reason (optional)
  │   └─→ [Confirm] / [Cancel]
  │
  ├─→ [Confirm] → API Call
  │   ├─→ POST /api/v1/calls/{id}/escalate
  │   └─→ Transfer call to agent
  │
  └─→ Update UI
      ├─→ Show "Escalated" badge
      ├─→ Display assigned agent
      └─→ Show escalation context

Action: Intervene in Call
  │
  ├─→ Click [Intervene] Button
  │
  ├─→ Intervention Modal Opens
  │   ├─→ Options:
  │   │   ├─→ Send Message to AI
  │   │   ├─→ Pause AI Responses
  │   │   ├─→ Resume AI
  │   │   └─→ Override Instructions
  │   │
  │   └─→ [Confirm] / [Cancel]
  │
  ├─→ [Confirm] → API Call
  │   └─→ POST /api/v1/calls/{id}/intervene
  │
  └─→ Update UI
      └─→ Show intervention status

Action: Add Note
  │
  ├─→ Click [Add Note] Button
  │
  ├─→ Note Modal Opens
  │   ├─→ Text input
  │   ├─→ Tags (optional)
  │   └─→ [Save] / [Cancel]
  │
  ├─→ [Save] → API Call
  │   └─→ POST /api/v1/calls/{id}/notes
  │
  └─→ Update UI
      └─→ Note appears in metadata panel

Action: End Call
  │
  ├─→ Click [End Call] Button
  │
  ├─→ Confirmation Dialog
  │   ├─→ "Are you sure?"
  │   ├─→ Reason (optional)
  │   └─→ [Confirm] / [Cancel]
  │
  ├─→ [Confirm] → API Call
  │   └─→ POST /api/v1/calls/{id}/end
  │
  └─→ Update UI
      ├─→ Call moves to "Completed"
      ├─→ Show final QA report
      └─→ Remove from active calls
```

---

## Flow 3: Call Detail Deep Dive

```
┌─────────────────────────────────────────────────────────────┐
│              CALL DETAIL DEEP DIVE FLOW                    │
└─────────────────────────────────────────────────────────────┘

User Clicks on Call in List
  │
  └─→ Load Full Call Details
      │
      ├─→ Header Section
      │   ├─→ Call ID, SID
      │   ├─→ Phone numbers
      │   ├─→ Status, duration
      │   └─→ Action buttons
      │
      ├─→ Transcript Section
      │   ├─→ Load all interactions
      │   ├─→ Display chronologically
      │   ├─→ Color-code by speaker
      │   └─→ Show timestamps
      │
      ├─→ QA Metrics Section
      │   ├─→ Overall score
      │   ├─→ Sentiment timeline
      │   ├─→ Compliance issues
      │   └─→ Flagged issues
      │
      ├─→ Context Section
      │   ├─→ Conversation summary
      │   ├─→ Knowledge base hits
      │   ├─→ Escalation context (if any)
      │   └─→ Manager notes
      │
      └─→ Actions Section
          └─→ Available actions

User Expands Transcript
  │
  ├─→ View Full Transcript
  │   ├─→ All interactions
      │   ├─→ Search within transcript
      │   ├─→ Filter by speaker
      │   └─→ Export transcript
      │
      └─→ [Export] → Download as TXT/PDF

User Views QA Report
  │
  ├─→ Detailed QA Breakdown
  │   ├─→ Score components
  │   │   ├─→ Sentiment: 0.75 (30%)
  │   │   ├─→ Compliance: 0.90 (30%)
  │   │   ├─→ Accuracy: 0.80 (20%)
  │   │   └─→ Professionalism: 0.85 (20%)
  │   │
  │   ├─→ Timeline View
  │   │   └─→ Sentiment over time (chart)
  │   │
  │   ├─→ Compliance Issues List
  │   │   └─→ Detailed violations
  │   │
  │   └─→ Recommendations
  │       └─→ Improvement suggestions
  │
  └─→ [Export Report] → Download PDF

User Views Audio (if available)
  │
  ├─→ Click [Listen Live] or [Play Recording]
  │
  ├─→ Audio Player Opens
  │   ├─→ Play/Pause controls
  │   ├─→ Timeline scrubber
  │   ├─→ Speed control
  │   └─→ Transcript sync (highlight current line)
  │
  └─→ Audio plays with transcript highlighting
```

---

## Flow 4: Analytics & Reporting

```
┌─────────────────────────────────────────────────────────────┐
│              ANALYTICS & REPORTING FLOW                      │
└─────────────────────────────────────────────────────────────┘

Navigate to Analytics Dashboard
  │
  ├─→ Load Overview Metrics
  │   ├─→ Total calls
  │   ├─→ Active calls
  │   ├─→ Average QA score
  │   └─→ Escalation rate
  │
  ├─→ Load Charts
  │   ├─→ Call volume over time
  │   ├─→ Sentiment distribution
  │   ├─→ QA score distribution
  │   └─→ Escalation reasons
  │
  └─→ Load Tables
      ├─→ Top issues
      └─→ Agent performance

User Applies Filters
  │
  ├─→ Select Date Range
  │   ├─→ Today
  │   ├─→ Last 7 days
  │   ├─→ Last 30 days
  │   └─→ Custom range
  │
  ├─→ Select Business Template
  │   └─→ Filter by template
  │
  ├─→ Select Call Direction
  │   ├─→ Inbound
  │   └─→ Outbound
  │
  ├─→ Select Status
  │   ├─→ All
  │   ├─→ Completed
  │   ├─→ Failed
  │   └─→ Escalated
  │
  └─→ [Apply Filters] → Refresh data

User Views Specific Metric
  │
  ├─→ Click on Metric Card
  │
  └─→ Detailed View Opens
      ├─→ Breakdown by time period
      ├─→ Trend analysis
      ├─→ Comparison to previous period
      └─→ [Export Data]

User Searches Call History
  │
  ├─→ Enter Search Query
  │   ├─→ Phone number
  │   ├─→ Call ID
  │   ├─→ Date range
  │   └─→ Full-text search
  │
  ├─→ [Search] → API Call
  │   └─→ GET /api/v1/calls?search=...
  │
  ├─→ Results Display
  │   ├─→ Paginated list
  │   ├─→ Sortable columns
  │   └─→ Quick actions
  │
  └─→ Click Result → Load call details

User Exports Report
  │
  ├─→ Click [Export] Button
  │
  ├─→ Export Options Modal
  │   ├─→ Format: CSV / PDF
  │   ├─→ Date range
  │   ├─→ Include: Calls, QA, Analytics
  │   └─→ [Generate Report]
  │
  ├─→ [Generate] → API Call
  │   └─→ POST /api/v1/analytics/export
  │
  └─→ Download File
      └─→ File downloads to user's device
```

---

## Flow 5: Configuration Management

```
┌─────────────────────────────────────────────────────────────┐
│           CONFIGURATION MANAGEMENT FLOW                     │
└─────────────────────────────────────────────────────────────┘

Navigate to Settings
  │
  └─→ Settings Dashboard
      │
      ├─→ Business Configurations Tab
      │   ├─→ List of business configs
      │   ├─→ [Create New] / [Edit] / [Delete]
      │   └─→ Active/Inactive toggle
      │
      ├─→ Knowledge Base Tab
      │   ├─→ List of documents
      │   ├─→ [Upload] / [Add URL] / [Delete]
      │   └─→ RAG settings
      │
      ├─→ Agents Tab
      │   ├─→ List of agents
      │   ├─→ [Add Agent] / [Edit] / [Delete]
      │   └─→ Availability management
      │
      ├─→ QA Settings Tab
      │   ├─→ Enable/disable features
      │   ├─→ Threshold configuration
      │   └─→ Compliance rules
      │
      └─→ Escalation Rules Tab
          ├─→ Trigger configuration
          └─→ Transfer settings

User Creates/Edits Business Config
  │
  ├─→ Click [Create New] or [Edit]
  │
  ├─→ Config Form Opens
  │   ├─→ Basic Info
  │   │   ├─→ Name
  │   │   └─→ Type
  │   │
  │   ├─→ AI Settings
  │   │   ├─→ Model selection
  │   │   ├─→ Temperature
  │   │   ├─→ System prompt
  │   │   └─→ Voice settings
  │   │
  │   ├─→ Knowledge Base
  │   │   └─→ Link to knowledge entries
  │   │
  │   ├─→ QA Settings
  │   │   └─→ Override global QA settings
  │   │
  │   └─→ Escalation Rules
  │       └─→ Override global escalation rules
  │
  ├─→ [Save] → API Call
  │   └─→ POST /api/v1/config/business
  │
  └─→ Success → Return to list

User Manages Knowledge Base
  │
  ├─→ Upload Document
  │   ├─→ Select file
  │   ├─→ [Upload] → Processing...
  │   └─→ Success → Document appears in list
  │
  ├─→ Add URL
  │   ├─→ Enter URL
  │   ├─→ [Scrape] → Processing...
  │   └─→ Success → Content added
  │
  ├─→ Edit Document
  │   ├─→ Click [Edit]
  │   ├─→ Update title/content
  │   └─→ [Save]
  │
  └─→ Delete Document
      ├─→ Click [Delete]
      ├─→ Confirmation dialog
      └─→ [Confirm] → Deleted

User Manages Agents
  │
  ├─→ Add Agent
  │   ├─→ Fill form (name, email, phone, etc.)
  │   ├─→ Set skills/departments
  │   └─→ [Save]
  │
  ├─→ Edit Agent
  │   ├─→ Click [Edit]
  │   ├─→ Update information
  │   └─→ [Save]
  │
  ├─→ Toggle Availability
  │   ├─→ Click availability toggle
  │   └─→ Status updates immediately
  │
  └─→ Delete Agent
      ├─→ Click [Delete]
      ├─→ Confirmation (check for active escalations)
      └─→ [Confirm] → Deleted
```

---

## Flow 6: Real-Time Alert Handling

```
┌─────────────────────────────────────────────────────────────┐
│              REAL-TIME ALERT HANDLING FLOW                  │
└─────────────────────────────────────────────────────────────┘

System Detects Alert Condition
  │
  ├─→ Escalation Triggered
  │   ├─→ WebSocket event: escalation.triggered
  │   ├─→ Show notification toast
  │   ├─→ Highlight call in list (red badge)
  │   ├─→ Play sound alert (optional)
  │   └─→ Update call detail view
  │
  ├─→ Negative Sentiment Detected
  │   ├─→ WebSocket event: sentiment.changed
  │   ├─→ Update sentiment indicator (red)
  │   ├─→ Highlight in transcript
  │   └─→ Show warning in QA panel
  │
  ├─→ Low QA Score
  │   ├─→ WebSocket event: qa.score.updated
  │   ├─→ Score drops below threshold
  │   ├─→ Update score color (red)
  │   └─→ Show alert badge
  │
  └─→ Compliance Issue Detected
      ├─→ WebSocket event: compliance.issue
      ├─→ Show compliance alert
      └─→ List issues in QA panel

User Responds to Alert
  │
  ├─→ Click on Alert/Notification
  │   └─→ Navigate to call detail view
  │
  ├─→ Review Situation
  │   ├─→ Read transcript
  │   ├─→ Check QA metrics
  │   └─→ Review context
  │
  └─→ Take Action
      ├─→ Escalate (if not already)
      ├─→ Intervene
      ├─→ Add note
      └─→ Dismiss alert (if resolved)
```

---

## Key Interaction Patterns

### Pattern 1: Quick Action Flow
**Goal:** Minimize clicks for common actions

1. See call in list → Click → View details → Click action button → Confirm → Done
2. **Total:** 3-4 clicks for most actions

### Pattern 2: Multi-Task Monitoring
**Goal:** Monitor multiple calls simultaneously

1. Open multiple browser tabs/windows
2. Each tab shows different call
3. Real-time updates in all tabs
4. Centralized notification system

### Pattern 3: Drill-Down Analysis
**Goal:** Go from overview to detail quickly

1. Dashboard → See metric → Click → Detailed view → Click call → Full details
2. **Total:** 2-3 clicks from overview to call detail

### Pattern 4: Contextual Help
**Goal:** Help users understand features

1. Hover over icon → Tooltip appears
2. Click (?) → Help panel opens
3. Search help → Relevant articles
4. In-app tutorials for new features

---

## Error Handling Flows

### Connection Lost
```
WebSocket Disconnected
  │
  ├─→ Show reconnection indicator
  │
  ├─→ Attempt auto-reconnect (exponential backoff)
  │
  ├─→ If reconnected → Resume updates
  │
  └─→ If failed → Show error message
      └─→ [Manual Reconnect] button
```

### API Error
```
API Call Failed
  │
  ├─→ Show error toast notification
  │
  ├─→ Display error message
  │   ├─→ User-friendly message
  │   └─→ Technical details (expandable)
  │
  ├─→ Offer retry option
  │
  └─→ Log error for debugging
```

### Data Loading
```
Loading States
  │
  ├─→ Initial Load
  │   └─→ Skeleton screens
  │
  ├─→ Refreshing Data
  │   └─→ Subtle loading indicator
  │
  └─→ Empty States
      └─→ Helpful message + action button
```

