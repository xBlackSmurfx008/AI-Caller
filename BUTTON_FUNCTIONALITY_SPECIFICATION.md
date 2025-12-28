# Button Functionality Specification
## Complete Button Mapping for AI Caller Application

This document maps every button in the application, detailing its functionality, associated pages/pop-ups, backend requirements, and best practices inspired by HubSpot and industry standards.

---

## Table of Contents
1. [Navigation & Header Buttons](#navigation--header-buttons)
2. [Dashboard & Call Management Buttons](#dashboard--call-management-buttons)
3. [Call Actions Buttons](#call-actions-buttons)
4. [Settings & Configuration Buttons](#settings--configuration-buttons)
5. [Analytics Buttons](#analytics-buttons)
6. [Setup Wizard Buttons](#setup-wizard-buttons)
7. [Authentication Buttons](#authentication-buttons)
8. [Backend API Requirements](#backend-api-requirements)
9. [Missing Functionality & Recommendations](#missing-functionality--recommendations)

---

## Navigation & Header Buttons

### 1. Logo/Brand Button (Header)
**Location:** `frontend/src/components/layout/Header.tsx` (Line 38-64)

**Current Functionality:**
- Navigates to Dashboard (`/`)
- Visual branding element

**Expected Behavior:**
- ✅ Click → Navigate to Dashboard page
- ✅ Hover effect → Background color change
- ✅ Should always be visible and accessible

**Backend Requirements:**
- None (pure navigation)

**Status:** ✅ Implemented

---

### 2. Dashboard Navigation Button
**Location:** `frontend/src/components/layout/Header.tsx` (Line 70-102)

**Current Functionality:**
- Navigates to Dashboard (`/`)
- Shows active state when on dashboard

**Expected Behavior:**
- ✅ Click → Navigate to Dashboard
- ✅ Active state styling when `location.pathname === '/'`
- ✅ Hover effect → Background color change

**Backend Requirements:**
- None (pure navigation)

**Status:** ✅ Implemented

---

### 3. Analytics Navigation Button
**Location:** `frontend/src/components/layout/Header.tsx` (Line 70-102)

**Current Functionality:**
- Navigates to Analytics page (`/analytics`)
- Shows active state when on analytics

**Expected Behavior:**
- ✅ Click → Navigate to Analytics page
- ✅ Active state styling when `location.pathname === '/analytics'`
- ✅ Hover effect → Background color change

**Backend Requirements:**
- None (pure navigation)

**Status:** ✅ Implemented

---

### 4. Settings Navigation Button
**Location:** `frontend/src/components/layout/Header.tsx` (Line 70-102)

**Current Functionality:**
- Navigates to Settings page (`/settings`)
- Shows active state when on settings

**Expected Behavior:**
- ✅ Click → Navigate to Settings page
- ✅ Active state styling when `location.pathname === '/settings'`
- ✅ Hover effect → Background color change

**Backend Requirements:**
- None (pure navigation)

**Status:** ✅ Implemented

---

### 5. Notifications Button
**Location:** `frontend/src/components/layout/Header.tsx` (Line 109-145)

**Current Functionality:**
- Shows toast notification: "Notifications feature coming soon"
- Visual indicator (red dot) for unread notifications

**Expected Behavior:**
- ⚠️ **SHOULD:** Open notifications dropdown/panel
- ⚠️ **SHOULD:** Display list of notifications (call escalations, QA alerts, system updates)
- ⚠️ **SHOULD:** Mark notifications as read
- ⚠️ **SHOULD:** Show notification count badge
- ⚠️ **SHOULD:** Filter notifications by type (all, calls, escalations, system)

**Backend Requirements:**
- ❌ **MISSING:** `GET /notifications` - List notifications
- ❌ **MISSING:** `PATCH /notifications/{id}/read` - Mark as read
- ❌ **MISSING:** `GET /notifications/unread-count` - Get unread count
- ❌ **MISSING:** WebSocket events for real-time notifications

**Recommended Implementation:**
```typescript
// Notification types:
- Call Escalated: "Call {callId} escalated to {agentName}"
- QA Alert: "Call {callId} scored below threshold ({score})"
- System Update: "System maintenance scheduled"
- Agent Status: "{agentName} is now {available/unavailable}"
```

**Status:** ⚠️ Partially Implemented (needs full functionality)

---

### 6. Logout Button
**Location:** `frontend/src/components/layout/Header.tsx` (Line 178-185)

**Current Functionality:**
- Calls `logout()` from auth store
- Navigates to `/login`
- Shows toast on success

**Expected Behavior:**
- ✅ Click → Logout user
- ✅ Clear authentication tokens
- ✅ Clear user session data
- ✅ Navigate to login page
- ⚠️ **SHOULD:** Show confirmation dialog (HubSpot best practice)

**Backend Requirements:**
- ⚠️ **SHOULD:** `POST /auth/logout` - Invalidate session/token
- ✅ Currently handled client-side only

**Status:** ✅ Implemented (should add confirmation dialog)

---

## Dashboard & Call Management Buttons

### 7. Back Button (Mobile Call Detail)
**Location:** `frontend/src/pages/Dashboard.tsx` (Line 53-61)

**Current Functionality:**
- Closes call detail overlay on mobile
- Calls `selectCall(null)` to deselect call

**Expected Behavior:**
- ✅ Click → Close call detail overlay
- ✅ Return to call list view
- ✅ Only visible on mobile (`lg:hidden`)

**Backend Requirements:**
- None (UI state management)

**Status:** ✅ Implemented

---

### 8. Back to Calls Button (Call Detail)
**Location:** `frontend/src/components/calls/CallDetail.tsx` (Line 96-104)

**Current Functionality:**
- Deselects current call
- Returns to call list view

**Expected Behavior:**
- ✅ Click → Deselect call
- ✅ Show call list view
- ✅ Only visible on mobile (`lg:hidden`)

**Backend Requirements:**
- None (UI state management)

**Status:** ✅ Implemented

---

### 9. Call List Item (Clickable)
**Location:** `frontend/src/components/calls/CallListItem.tsx` (Line 60)

**Current Functionality:**
- Selects call when clicked
- Shows call detail panel

**Expected Behavior:**
- ✅ Click → Select call
- ✅ Show call detail panel
- ✅ Highlight selected call
- ✅ Hover effect → Background color change

**Backend Requirements:**
- None (UI state management)
- Call data already loaded via `useCalls` hook

**Status:** ✅ Implemented

---

## Call Actions Buttons

### 10. Escalate Button
**Location:** `frontend/src/components/calls/CallActions.tsx` (Line 95-102)

**Current Functionality:**
- Opens escalation modal
- Disabled when call is escalated or completed

**Expected Behavior:**
- ✅ Click → Open escalation modal
- ✅ Modal shows:
  - Agent selection dropdown (with "Auto-assign" option)
  - Reason textarea (optional)
  - Cancel and Escalate buttons
- ✅ On confirm → Call `POST /calls/{callId}/escalate`
- ✅ Show success toast
- ✅ Update call status to "escalated"
- ✅ Refresh call data
- ✅ Disabled states: `call.status === 'escalated' || call.status === 'completed'`

**Backend Requirements:**
- ✅ `POST /calls/{callId}/escalate` - Escalate call
- ✅ Should transfer call to selected agent
- ✅ Should send context to agent (warm transfer)
- ✅ Should update call status
- ✅ Should trigger WebSocket event for real-time update

**Status:** ✅ Implemented

---

### 11. Intervene Button
**Location:** `frontend/src/components/calls/CallActions.tsx` (Line 103-110)

**Current Functionality:**
- Opens intervention modal
- Disabled when call is completed

**Expected Behavior:**
- ✅ Click → Open intervention modal
- ✅ Modal shows:
  - Action type selector (send_message, pause, resume, override_instructions)
  - Message/instructions textarea (conditional)
  - Cancel and Apply buttons
- ✅ On confirm → Call `POST /calls/{callId}/intervene`
- ✅ Show success toast
- ✅ Refresh call data
- ✅ Disabled state: `call.status === 'completed'`

**Backend Requirements:**
- ✅ `POST /calls/{callId}/intervene` - Apply intervention
- ✅ Should execute intervention action:
  - `send_message`: Send message to AI during call
  - `pause`: Pause AI responses
  - `resume`: Resume AI responses
  - `override_instructions`: Update AI instructions
- ✅ Should trigger WebSocket event for real-time update

**Status:** ✅ Implemented

---

### 12. Add Note Button
**Location:** `frontend/src/components/calls/CallActions.tsx` (Line 111-117)

**Current Functionality:**
- Opens note modal
- Always enabled

**Expected Behavior:**
- ✅ Click → Open note modal
- ✅ Modal shows:
  - Note textarea
  - Tags input (optional - not currently shown)
  - Category selector (optional - not currently shown)
  - Cancel and Save Note buttons
- ✅ On confirm → Call `POST /calls/{callId}/notes`
- ✅ Show success toast
- ✅ Close modal and clear form
- ✅ Refresh call data to show new note

**Backend Requirements:**
- ✅ `POST /calls/{callId}/notes` - Add note to call
- ✅ Should save note with timestamp and user info
- ✅ Should support tags and categories (optional)
- ✅ Should be visible in call detail view

**Status:** ✅ Implemented (could enhance with tags/categories)

---

### 13. End Call Button
**Location:** `frontend/src/components/calls/CallActions.tsx` (Line 119-126)

**Current Functionality:**
- Opens end call confirmation modal
- Disabled when call is completed

**Expected Behavior:**
- ✅ Click → Open end call confirmation modal
- ✅ Modal shows:
  - Warning message (destructive action)
  - Reason textarea (optional)
  - Cancel and End Call buttons
- ✅ On confirm → Call `POST /calls/{callId}/end`
- ✅ Show success toast
- ✅ Update call status to "completed"
- ✅ Refresh call data
- ✅ Disabled state: `call.status === 'completed'`

**Backend Requirements:**
- ✅ `POST /calls/{callId}/end` - End call
- ✅ Should terminate call via Twilio
- ✅ Should update call status
- ✅ Should calculate final duration
- ✅ Should trigger WebSocket event for real-time update

**Status:** ✅ Implemented

---

### 14. Escalate Modal - Cancel Button
**Location:** `frontend/src/components/calls/CallActions.tsx` (Line 161-163)

**Expected Behavior:**
- ✅ Click → Close escalation modal
- ✅ Clear form data
- ✅ No backend call

**Status:** ✅ Implemented

---

### 15. Escalate Modal - Escalate Call Button
**Location:** `frontend/src/components/calls/CallActions.tsx` (Line 164-166)

**Expected Behavior:**
- ✅ Click → Call `handleEscalate()`
- ✅ Validate form (agent selection optional)
- ✅ Call `POST /calls/{callId}/escalate`
- ✅ Show loading state
- ✅ Show success/error toast
- ✅ Close modal on success

**Status:** ✅ Implemented

---

### 16. Intervene Modal - Cancel Button
**Location:** `frontend/src/components/calls/CallActions.tsx` (Line 204-206)

**Expected Behavior:**
- ✅ Click → Close intervention modal
- ✅ Clear form data

**Status:** ✅ Implemented

---

### 17. Intervene Modal - Apply Intervention Button
**Location:** `frontend/src/components/calls/CallActions.tsx` (Line 207-209)

**Expected Behavior:**
- ✅ Click → Call `handleIntervene()`
- ✅ Validate form (message required for send_message/override_instructions)
- ✅ Call `POST /calls/{callId}/intervene`
- ✅ Show loading state
- ✅ Show success/error toast
- ✅ Close modal on success

**Status:** ✅ Implemented

---

### 18. Note Modal - Cancel Button
**Location:** `frontend/src/components/calls/CallActions.tsx` (Line 234-236)

**Expected Behavior:**
- ✅ Click → Close note modal
- ✅ Clear note text

**Status:** ✅ Implemented

---

### 19. Note Modal - Save Note Button
**Location:** `frontend/src/components/calls/CallActions.tsx` (Line 237-239)

**Expected Behavior:**
- ✅ Click → Call `handleAddNote()`
- ✅ Validate note is not empty
- ✅ Call `POST /calls/{callId}/notes`
- ✅ Show loading state
- ✅ Show success/error toast
- ✅ Close modal and clear form on success

**Status:** ✅ Implemented

---

### 20. End Call Modal - Cancel Button
**Location:** `frontend/src/components/calls/CallActions.tsx` (Line 269-271)

**Expected Behavior:**
- ✅ Click → Close end call modal
- ✅ Clear reason text

**Status:** ✅ Implemented

---

### 21. End Call Modal - End Call Button (Destructive)
**Location:** `frontend/src/components/calls/CallActions.tsx` (Line 272-274)

**Expected Behavior:**
- ✅ Click → Call `handleEndCall()`
- ✅ Show loading state
- ✅ Call `POST /calls/{callId}/end`
- ✅ Show success/error toast
- ✅ Close modal on success
- ✅ Update call status

**Status:** ✅ Implemented

---

### 22. Auto-Scroll Toggle Button (Transcript)
**Location:** `frontend/src/components/calls/Transcript.tsx` (Line 65-72)

**Current Functionality:**
- Toggles auto-scroll feature in transcript
- Shows current state (enabled/disabled)

**Expected Behavior:**
- ✅ Click → Toggle `autoScroll` state
- ✅ When enabled → Automatically scroll to bottom on new messages
- ✅ Visual indicator of state

**Backend Requirements:**
- None (UI state only)

**Status:** ✅ Implemented

---

## Settings & Configuration Buttons

### 23. Settings Tab Buttons
**Location:** `frontend/src/pages/Settings.tsx` (Line 87-123)

**Current Functionality:**
- Switch between tabs: Business Configs, Knowledge Base, Agents
- Shows active tab state

**Expected Behavior:**
- ✅ Click → Switch active tab
- ✅ Show corresponding tab content
- ✅ Active tab styling (border-bottom, color)
- ✅ Hover effect on inactive tabs

**Backend Requirements:**
- None (UI state management)

**Status:** ✅ Implemented

---

### 24. Create Config Button (Header)
**Location:** `frontend/src/components/config/BusinessConfigList.tsx` (Line 25-27)

**Current Functionality:**
- Opens business config form modal
- Calls `onCreate()` callback

**Expected Behavior:**
- ✅ Click → Open business config form modal
- ✅ Modal shows 6-step wizard:
  1. Basic Information
  2. AI Configuration
  3. Voice Configuration
  4. Knowledge Base
  5. Quality Assurance
  6. Escalation
- ✅ Form in create mode (not edit mode)

**Backend Requirements:**
- ✅ `POST /config/business` - Create business config
- ✅ Should validate all required fields
- ✅ Should return created config

**Status:** ✅ Implemented

---

### 25. Create Config Button (Empty State)
**Location:** `frontend/src/components/config/BusinessConfigList.tsx` (Line 33-35)

**Expected Behavior:**
- ✅ Same as button #24
- ✅ Shown when no configs exist

**Status:** ✅ Implemented

---

### 26. Edit Config Button
**Location:** `frontend/src/components/config/BusinessConfigList.tsx` (Line 73-75)

**Current Functionality:**
- Opens business config form modal in edit mode
- Calls `onEdit(config)` callback

**Expected Behavior:**
- ✅ Click → Open business config form modal
- ✅ Pre-populate form with existing config data
- ✅ Form in edit mode
- ✅ All 6 steps available for editing

**Backend Requirements:**
- ✅ `GET /config/business/{id}` - Get config details
- ✅ `PUT /config/business/{id}` - Update config
- ✅ Should validate changes
- ✅ Should return updated config

**Status:** ✅ Implemented

---

### 27. Delete Config Button
**Location:** `frontend/src/components/config/BusinessConfigList.tsx` (Line 76-86)

**Current Functionality:**
- Shows browser confirmation dialog
- Calls `onDelete(config.id)` on confirm

**Expected Behavior:**
- ✅ Click → Show confirmation dialog
- ⚠️ **SHOULD:** Use custom modal instead of `window.confirm()` (HubSpot best practice)
- ✅ On confirm → Call `DELETE /config/business/{id}`
- ✅ Show success toast
- ✅ Refresh config list
- ⚠️ **SHOULD:** Check if config is in use before deletion
- ⚠️ **SHOULD:** Show warning if config has active calls

**Backend Requirements:**
- ✅ `DELETE /config/business/{id}` - Delete config
- ⚠️ **SHOULD:** Validate config is not in use
- ⚠️ **SHOULD:** Return error if config has active calls

**Status:** ✅ Implemented (should enhance with custom modal and validation)

---

### 28. Business Config Form - Previous Button
**Location:** `frontend/src/components/config/BusinessConfigForm.tsx` (Line 664-670)

**Current Functionality:**
- Navigates to previous step in wizard
- Only shown when `activeStep > 1`

**Expected Behavior:**
- ✅ Click → Decrement `activeStep`
- ✅ Show previous step content
- ✅ Preserve form data
- ✅ Not shown on step 1

**Backend Requirements:**
- None (UI state management)

**Status:** ✅ Implemented

---

### 29. Business Config Form - Cancel Button
**Location:** `frontend/src/components/config/BusinessConfigForm.tsx` (Line 674-680)

**Current Functionality:**
- Closes modal and resets form

**Expected Behavior:**
- ✅ Click → Close modal
- ✅ Reset form to default values
- ✅ Reset step to 1
- ⚠️ **SHOULD:** Show confirmation if form has unsaved changes (HubSpot best practice)

**Backend Requirements:**
- None (UI state management)

**Status:** ✅ Implemented (should add unsaved changes warning)

---

### 30. Business Config Form - Next Button
**Location:** `frontend/src/components/config/BusinessConfigForm.tsx` (Line 682-688)

**Current Functionality:**
- Navigates to next step in wizard
- Only shown when `activeStep < totalSteps`

**Expected Behavior:**
- ✅ Click → Increment `activeStep`
- ✅ Show next step content
- ✅ Preserve form data
- ⚠️ **SHOULD:** Validate current step before proceeding

**Backend Requirements:**
- None (UI state management)

**Status:** ✅ Implemented (should add step validation)

---

### 31. Business Config Form - Create/Update Button
**Location:** `frontend/src/components/config/BusinessConfigForm.tsx` (Line 690-696)

**Current Functionality:**
- Submits form (create or update)
- Shows loading state
- Only shown on final step

**Expected Behavior:**
- ✅ Click → Validate entire form
- ✅ Show loading state (`isSubmitting`)
- ✅ Call `POST /config/business` (create) or `PUT /config/business/{id}` (update)
- ✅ Show success toast
- ✅ Close modal and refresh list
- ✅ Reset form

**Backend Requirements:**
- ✅ `POST /config/business` - Create config
- ✅ `PUT /config/business/{id}` - Update config
- ✅ Should validate all fields
- ✅ Should return created/updated config

**Status:** ✅ Implemented

---

### 32. Add Escalation Trigger Button
**Location:** `frontend/src/components/config/BusinessConfigForm.tsx` (Line 524-526)

**Current Functionality:**
- Adds new escalation trigger to form array

**Expected Behavior:**
- ✅ Click → Add new trigger object to `config_data.escalation.triggers` array
- ✅ Show new trigger form fields
- ✅ Default values: `{ type: 'sentiment', threshold: 0.5, keywords: [] }`

**Backend Requirements:**
- None (form state management)

**Status:** ✅ Implemented

---

### 33. Remove Escalation Trigger Button
**Location:** `frontend/src/components/config/BusinessConfigForm.tsx` (Line 539-546)

**Current Functionality:**
- Removes escalation trigger from form array

**Expected Behavior:**
- ✅ Click → Remove trigger at index from array
- ✅ Update form state
- ✅ Remove trigger form fields from UI

**Backend Requirements:**
- None (form state management)

**Status:** ✅ Implemented

---

### 34. Upload Document Button (Knowledge Base)
**Location:** `frontend/src/components/config/KnowledgeBaseManager.tsx` (Line 72-74)

**Current Functionality:**
- Opens file picker dialog
- Uploads selected file

**Expected Behavior:**
- ✅ Click → Open file picker
- ✅ Accept files: `.pdf`, `.docx`, `.txt`
- ✅ On file select → Call `POST /knowledge/upload`
- ✅ Show loading state
- ✅ Show success toast
- ✅ Refresh knowledge base list
- ⚠️ **SHOULD:** Show upload progress
- ⚠️ **SHOULD:** Validate file size (max 10MB recommended)
- ⚠️ **SHOULD:** Show processing status

**Backend Requirements:**
- ✅ `POST /knowledge/upload` - Upload document
- ✅ Should process document (extract text, chunk, create embeddings)
- ✅ Should return entry with processing status
- ⚠️ **SHOULD:** Support async processing with status updates

**Status:** ✅ Implemented (should add progress and validation)

---

### 35. Add Entry Button (Knowledge Base)
**Location:** `frontend/src/components/config/KnowledgeBaseManager.tsx` (Line 82-88)

**Current Functionality:**
- Toggles add entry form visibility

**Expected Behavior:**
- ✅ Click → Toggle `showAddForm` state
- ✅ Show/hide add entry form
- ✅ Button text changes: "Add Entry" ↔ "Cancel"

**Backend Requirements:**
- None (UI state management)

**Status:** ✅ Implemented

---

### 36. Add Entry Submit Button
**Location:** `frontend/src/components/config/KnowledgeBaseManager.tsx` (Line 109-111)

**Current Functionality:**
- Submits new knowledge entry

**Expected Behavior:**
- ✅ Click → Validate title and content are not empty
- ✅ Call `POST /knowledge` with entry data
- ✅ Show loading state
- ✅ Show success toast
- ✅ Clear form and hide add form
- ✅ Refresh knowledge base list

**Backend Requirements:**
- ✅ `POST /knowledge` - Create knowledge entry
- ✅ Should create embeddings for content
- ✅ Should return created entry

**Status:** ✅ Implemented

---

### 37. Delete Entry Button (Knowledge Base)
**Location:** `frontend/src/components/config/KnowledgeBaseManager.tsx` (Line 141-147)

**Current Functionality:**
- Shows browser confirmation dialog
- Deletes knowledge entry

**Expected Behavior:**
- ✅ Click → Show confirmation dialog
- ⚠️ **SHOULD:** Use custom modal instead of `window.confirm()`
- ✅ On confirm → Call `DELETE /knowledge/{id}`
- ✅ Show success toast
- ✅ Refresh knowledge base list

**Backend Requirements:**
- ✅ `DELETE /knowledge/{id}` - Delete entry
- ✅ Should remove embeddings from vector store
- ✅ Should return success status

**Status:** ✅ Implemented (should use custom modal)

---

### 38. Add Agent Button (Header)
**Location:** `frontend/src/components/config/AgentManager.tsx` (Line 117-119)

**Current Functionality:**
- Opens agent form modal in create mode

**Expected Behavior:**
- ✅ Click → Open agent form modal
- ✅ Form in create mode
- ✅ Reset form fields

**Backend Requirements:**
- ✅ `POST /agents` - Create agent
- ✅ Should validate email uniqueness
- ✅ Should return created agent

**Status:** ✅ Implemented

---

### 39. Add Agent Button (Empty State)
**Location:** `frontend/src/components/config/AgentManager.tsx` (Line 127-129)

**Expected Behavior:**
- ✅ Same as button #38
- ✅ Shown when no agents exist

**Status:** ✅ Implemented

---

### 40. Set Available/Unavailable Button
**Location:** `frontend/src/components/config/AgentManager.tsx` (Line 177-183)

**Current Functionality:**
- Toggles agent availability status

**Expected Behavior:**
- ✅ Click → Toggle `is_available` status
- ✅ Call `PATCH /agents/{id}/availability`
- ✅ Show success toast
- ✅ Refresh agent list
- ✅ Update badge display

**Backend Requirements:**
- ✅ `PATCH /agents/{id}/availability` - Update availability
- ✅ Should update agent status
- ✅ Should trigger WebSocket event if agent is on call

**Status:** ✅ Implemented

---

### 41. Edit Agent Button
**Location:** `frontend/src/components/config/AgentManager.tsx` (Line 184-186)

**Current Functionality:**
- Opens agent form modal in edit mode

**Expected Behavior:**
- ✅ Click → Open agent form modal
- ✅ Pre-populate form with agent data
- ✅ Form in edit mode

**Backend Requirements:**
- ✅ `GET /agents/{id}` - Get agent details
- ✅ `PUT /agents/{id}` - Update agent
- ✅ Should validate email uniqueness (if changed)

**Status:** ✅ Implemented

---

### 42. Delete Agent Button
**Location:** `frontend/src/components/config/AgentManager.tsx` (Line 187-193)

**Current Functionality:**
- Shows browser confirmation dialog
- Deletes agent

**Expected Behavior:**
- ✅ Click → Show confirmation dialog
- ⚠️ **SHOULD:** Use custom modal
- ⚠️ **SHOULD:** Check if agent has active calls
- ⚠️ **SHOULD:** Warn if agent has call history
- ✅ On confirm → Call `DELETE /agents/{id}`
- ✅ Show success toast
- ✅ Refresh agent list

**Backend Requirements:**
- ✅ `DELETE /agents/{id}` - Delete agent
- ⚠️ **SHOULD:** Validate agent has no active calls
- ⚠️ **SHOULD:** Optionally archive instead of delete

**Status:** ✅ Implemented (should add validation and custom modal)

---

### 43. Agent Form - Cancel Button
**Location:** `frontend/src/components/config/AgentManager.tsx` (Line 246-255)

**Current Functionality:**
- Closes agent form modal

**Expected Behavior:**
- ✅ Click → Close modal
- ✅ Reset form
- ⚠️ **SHOULD:** Show confirmation if form has unsaved changes

**Backend Requirements:**
- None (UI state management)

**Status:** ✅ Implemented (should add unsaved changes warning)

---

### 44. Agent Form - Create/Update Button
**Location:** `frontend/src/components/config/AgentManager.tsx` (Line 256-258)

**Current Functionality:**
- Submits agent form

**Expected Behavior:**
- ✅ Click → Validate form
- ✅ Parse skills and departments (comma-separated)
- ✅ Call `POST /agents` (create) or `PUT /agents/{id}` (update)
- ✅ Show loading state
- ✅ Show success toast
- ✅ Close modal and refresh list

**Backend Requirements:**
- ✅ `POST /agents` - Create agent
- ✅ `PUT /agents/{id}` - Update agent
- ✅ Should validate email format and uniqueness

**Status:** ✅ Implemented

---

## Analytics Buttons

### 45. Export CSV Button
**Location:** `frontend/src/pages/Analytics.tsx` (Line 88-90)

**Current Functionality:**
- Exports analytics report as CSV

**Expected Behavior:**
- ✅ Click → Call `POST /analytics/export` with `format: 'csv'`
- ✅ Show loading state
- ✅ Download CSV file
- ✅ File name: `analytics-report-{from_date}-{to_date}.csv`
- ✅ Show success toast

**Backend Requirements:**
- ✅ `POST /analytics/export` - Export analytics
- ✅ Should generate CSV with all analytics data
- ✅ Should include date range and filters in filename

**Status:** ✅ Implemented

---

### 46. Export PDF Button
**Location:** `frontend/src/pages/Analytics.tsx` (Line 91-93)

**Current Functionality:**
- Exports analytics report as PDF

**Expected Behavior:**
- ✅ Click → Call `POST /analytics/export` with `format: 'pdf'`
- ✅ Show loading state
- ✅ Download PDF file
- ✅ File name: `analytics-report-{from_date}-{to_date}.pdf`
- ✅ Include charts in PDF (`include_charts: true`)
- ✅ Show success toast

**Backend Requirements:**
- ✅ `POST /analytics/export` - Export analytics
- ✅ Should generate PDF with charts and data
- ✅ Should include date range and filters
- ✅ Should be formatted for printing

**Status:** ✅ Implemented

---

### 47. Reset Filters Button
**Location:** `frontend/src/pages/Analytics.tsx` (Line 125-138)

**Current Functionality:**
- Resets date range and business filter to defaults

**Expected Behavior:**
- ✅ Click → Reset `dateRange` to last 7 days
- ✅ Reset `selectedBusinessId` to empty (all businesses)
- ✅ Trigger analytics data refresh
- ✅ Update UI filters

**Backend Requirements:**
- None (UI state management, triggers data refresh)

**Status:** ✅ Implemented

---

## Setup Wizard Buttons

### 48. Setup Step Button (Progress Indicator)
**Location:** `frontend/src/components/setup/SetupWizard.tsx` (Line 55-68)

**Current Functionality:**
- Allows navigation to completed steps
- Shows step number or checkmark

**Expected Behavior:**
- ✅ Click → Navigate to step (if `stepId <= currentStep`)
- ✅ Show step content
- ✅ Update progress indicator
- ✅ Preserve form data

**Backend Requirements:**
- None (UI state management)

**Status:** ✅ Implemented

---

### 49. Previous Button (Setup Steps)
**Location:** Multiple setup step components

**Current Functionality:**
- Navigates to previous step in wizard

**Expected Behavior:**
- ✅ Click → Decrement `currentStep`
- ✅ Show previous step content
- ✅ Preserve form data
- ✅ Not shown on first step

**Backend Requirements:**
- None (UI state management)

**Status:** ✅ Implemented

---

### 50. Next Button (Setup Steps)
**Location:** Multiple setup step components

**Current Functionality:**
- Navigates to next step in wizard
- Validates current step

**Expected Behavior:**
- ✅ Click → Validate current step
- ✅ Save step data to `formData`
- ✅ Increment `currentStep`
- ✅ Show next step content
- ⚠️ **SHOULD:** Show validation errors if step is invalid

**Backend Requirements:**
- None (UI state management, but may call test APIs)

**Status:** ✅ Implemented (should enhance validation)

---

### 51. Test Connection Button (API Config Step)
**Location:** `frontend/src/components/setup/APIConfigStep.tsx` (Line 126-133)

**Current Functionality:**
- Tests API connection before proceeding

**Expected Behavior:**
- ✅ Click → Call test endpoint (e.g., `POST /config/test-connection`)
- ✅ Show loading state (`isTesting`)
- ✅ Show success/error message
- ✅ Enable/disable Next button based on result
- ⚠️ **SHOULD:** Validate API keys format before testing

**Backend Requirements:**
- ⚠️ **SHOULD:** `POST /config/test-connection` - Test API credentials
- ⚠️ **SHOULD:** Validate credentials without saving
- ⚠️ **SHOULD:** Return connection status

**Status:** ⚠️ Partially Implemented (needs backend endpoint)

---

### 52. Complete Setup Button (Review Step)
**Location:** `frontend/src/components/setup/ReviewStep.tsx` (Line 149-155)

**Current Functionality:**
- Completes setup wizard
- Saves all configuration

**Expected Behavior:**
- ✅ Click → Validate all steps
- ✅ Submit all configuration data
- ✅ Show loading state
- ✅ Show success toast
- ✅ Navigate to Dashboard
- ⚠️ **SHOULD:** Show progress indicator during save

**Backend Requirements:**
- ⚠️ **SHOULD:** `POST /setup/complete` - Complete setup
- ⚠️ **SHOULD:** Save all configuration in transaction
- ⚠️ **SHOULD:** Return setup status

**Status:** ⚠️ Partially Implemented (needs backend endpoint)

---

## Authentication Buttons

### 53. Sign In Button (Login Page)
**Location:** `frontend/src/pages/Login.tsx` (Line 82-90)

**Current Functionality:**
- Submits login form
- Authenticates user

**Expected Behavior:**
- ✅ Click → Validate form (email, password)
- ✅ Show loading state (`isLoading`)
- ✅ Call `authService.login(data)`
- ✅ On success → Navigate to Dashboard
- ✅ Show success toast
- ✅ On error → Show error toast
- ⚠️ **SHOULD:** Handle rate limiting
- ⚠️ **SHOULD:** Show "Forgot Password" link

**Backend Requirements:**
- ✅ `POST /auth/login` - Authenticate user
- ✅ Should validate credentials
- ✅ Should return JWT token
- ✅ Should set session/cookie
- ⚠️ **SHOULD:** Implement rate limiting
- ⚠️ **SHOULD:** Support password reset

**Status:** ✅ Implemented (should add password reset)

---

## Backend API Requirements

### Implemented Endpoints

✅ **Calls:**
- `GET /calls` - List calls
- `GET /calls/{callId}` - Get call details
- `GET /calls/{callId}/interactions` - Get call interactions
- `POST /calls/initiate` - Initiate call
- `POST /calls/{callId}/escalate` - Escalate call
- `POST /calls/{callId}/intervene` - Intervene in call
- `POST /calls/{callId}/end` - End call
- `POST /calls/{callId}/notes` - Add note

✅ **Config:**
- `GET /config/business` - List business configs
- `GET /config/business/{id}` - Get business config
- `POST /config/business` - Create business config
- `PUT /config/business/{id}` - Update business config
- `DELETE /config/business/{id}` - Delete business config

✅ **Agents:**
- `GET /agents` - List agents
- `GET /agents/{id}` - Get agent
- `POST /agents` - Create agent
- `PUT /agents/{id}` - Update agent
- `DELETE /agents/{id}` - Delete agent
- `PATCH /agents/{id}/availability` - Update availability

✅ **Knowledge:**
- `GET /knowledge` - List entries
- `POST /knowledge` - Create entry
- `POST /knowledge/upload` - Upload document
- `DELETE /knowledge/{id}` - Delete entry

✅ **Analytics:**
- `GET /analytics/overview` - Get overview metrics
- `GET /analytics/call-volume` - Get call volume data
- `GET /analytics/qa` - Get QA statistics
- `GET /analytics/sentiment` - Get sentiment statistics
- `GET /analytics/escalations` - Get escalation statistics
- `POST /analytics/export` - Export analytics

✅ **Auth:**
- `POST /auth/login` - Login

### Missing/Incomplete Endpoints

❌ **Notifications:**
- `GET /notifications` - List notifications
- `GET /notifications/unread-count` - Get unread count
- `PATCH /notifications/{id}/read` - Mark as read
- WebSocket events for real-time notifications

❌ **Setup:**
- `POST /config/test-connection` - Test API connection
- `POST /setup/complete` - Complete setup wizard

❌ **Auth (Enhancements):**
- `POST /auth/logout` - Logout (invalidate session)
- `POST /auth/forgot-password` - Request password reset
- `POST /auth/reset-password` - Reset password

❌ **Calls (Enhancements):**
- `GET /calls/{callId}/notes` - List call notes
- `PUT /calls/{callId}/notes/{noteId}` - Update note
- `DELETE /calls/{callId}/notes/{noteId}` - Delete note

❌ **Validation Endpoints:**
- `GET /config/business/{id}/usage` - Check if config is in use
- `GET /agents/{id}/usage` - Check if agent has active calls

---

## Missing Functionality & Recommendations

### High Priority

1. **Notifications System**
   - Real-time notification dropdown
   - Notification types: escalations, QA alerts, system updates
   - Unread count badge
   - Mark as read functionality

2. **Custom Confirmation Modals**
   - Replace all `window.confirm()` calls with custom modals
   - Consistent styling with application theme
   - Better UX for destructive actions

3. **Unsaved Changes Warning**
   - Warn users before closing forms with unsaved changes
   - Apply to: Business Config Form, Agent Form, Knowledge Base Form

4. **Form Validation**
   - Step-by-step validation in multi-step forms
   - Show validation errors inline
   - Prevent navigation if step is invalid

5. **File Upload Enhancements**
   - Progress indicator for file uploads
   - File size validation (max 10MB)
   - File type validation
   - Processing status indicator

### Medium Priority

6. **Call Initiation**
   - UI for initiating outbound calls
   - Phone number input with validation
   - Business config selection
   - Call scheduling

7. **Enhanced Notes**
   - Tags and categories for notes
   - Note editing and deletion
   - Note search and filtering
   - Note templates

8. **Agent Management Enhancements**
   - Check agent usage before deletion
   - Agent performance metrics
   - Agent availability calendar
   - Agent skills management UI

9. **Business Config Enhancements**
   - Check config usage before deletion
   - Config versioning
   - Config templates library
   - Config testing/preview

10. **Analytics Enhancements**
    - Custom date range picker
    - More filter options
    - Export scheduling
    - Dashboard customization

### Low Priority

11. **Accessibility**
    - Keyboard navigation for all buttons
    - ARIA labels for screen readers
    - Focus management in modals
    - Keyboard shortcuts

12. **Performance**
    - Button debouncing for rapid clicks
    - Optimistic UI updates
    - Loading skeletons instead of spinners

13. **Internationalization**
    - Button text translation
    - Date/time formatting
    - Number formatting

---

## HubSpot Best Practices Applied

### Button Hierarchy
- ✅ Primary buttons for main actions (one per surface)
- ✅ Secondary buttons for alternative actions
- ✅ Destructive buttons for delete/end actions
- ✅ Ghost buttons for less prominent actions

### Button Placement
- ✅ Buttons at bottom of modals/forms
- ✅ Primary button on the right
- ✅ Cancel/secondary button on the left
- ✅ Consistent spacing and alignment

### Button States
- ✅ Disabled state for unavailable actions
- ✅ Loading state for async operations
- ✅ Hover effects for interactivity
- ⚠️ Should add focus states for accessibility

### Confirmation Patterns
- ⚠️ Should use custom modals instead of browser dialogs
- ✅ Warning messages for destructive actions
- ✅ Clear action labels ("Delete" vs "Cancel")
- ⚠️ Should add undo functionality where possible

---

## Summary

**Total Buttons Mapped:** 53

**Status Breakdown:**
- ✅ Fully Implemented: 45
- ⚠️ Partially Implemented: 6
- ❌ Missing Backend: 2

**Key Improvements Needed:**
1. Notifications system (high priority)
2. Custom confirmation modals (high priority)
3. Unsaved changes warnings (high priority)
4. Form validation enhancements (high priority)
5. File upload progress (medium priority)
6. Call initiation UI (medium priority)

This specification serves as a comprehensive guide for implementing, testing, and maintaining all button functionality in the AI Caller application.

