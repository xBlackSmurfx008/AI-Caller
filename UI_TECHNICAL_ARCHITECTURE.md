# Call Center Manager Dashboard - Technical Architecture

## Overview

This document outlines the technical architecture for implementing the Call Center Manager Dashboard frontend application.

---

## 1. Technology Stack

### Recommended Stack: React + TypeScript

**Core Framework:**
- **React 18+** - UI library with hooks
- **TypeScript** - Type safety and better DX
- **Vite** - Fast build tool and dev server

**State Management:**
- **Zustand** - Lightweight state management (or Redux Toolkit)
- **React Query (TanStack Query)** - Server state management and caching

**Real-Time Communication:**
- **Socket.io-client** - WebSocket client for real-time updates
- **Server-Sent Events (SSE)** - Alternative for one-way updates

**UI Framework:**
- **Tailwind CSS** - Utility-first CSS framework
- **Headless UI** - Unstyled accessible components
- **React Router** - Client-side routing

**Data Visualization:**
- **Recharts** - React charting library
- **Chart.js** - Alternative charting option

**Form Handling:**
- **React Hook Form** - Performant form library
- **Zod** - Schema validation

**HTTP Client:**
- **Axios** - HTTP client with interceptors

**Utilities:**
- **date-fns** - Date formatting and manipulation
- **clsx** - Conditional class names
- **react-hot-toast** - Toast notifications

---

## 2. Project Structure

```
frontend/
├── public/
│   ├── favicon.ico
│   └── assets/
├── src/
│   ├── api/
│   │   ├── client.ts              # Axios instance
│   │   ├── calls.ts                # Call API endpoints
│   │   ├── analytics.ts           # Analytics API endpoints
│   │   ├── config.ts              # Config API endpoints
│   │   ├── agents.ts              # Agent API endpoints
│   │   └── knowledge.ts           # Knowledge base API endpoints
│   │
│   ├── components/
│   │   ├── common/
│   │   │   ├── Button.tsx
│   │   │   ├── Input.tsx
│   │   │   ├── Select.tsx
│   │   │   ├── Modal.tsx
│   │   │   ├── Toast.tsx
│   │   │   └── LoadingSpinner.tsx
│   │   │
│   │   ├── layout/
│   │   │   ├── Header.tsx
│   │   │   ├── Sidebar.tsx
│   │   │   ├── MainLayout.tsx
│   │   │   └── PageContainer.tsx
│   │   │
│   │   ├── calls/
│   │   │   ├── CallList.tsx
│   │   │   ├── CallListItem.tsx
│   │   │   ├── CallDetail.tsx
│   │   │   ├── Transcript.tsx
│   │   │   ├── TranscriptMessage.tsx
│   │   │   ├── QAMetrics.tsx
│   │   │   ├── CallActions.tsx
│   │   │   └── CallHeader.tsx
│   │   │
│   │   ├── analytics/
│   │   │   ├── Dashboard.tsx
│   │   │   ├── MetricCard.tsx
│   │   │   ├── CallVolumeChart.tsx
│   │   │   ├── SentimentChart.tsx
│   │   │   ├── QAScoreChart.tsx
│   │   │   └── AgentPerformanceTable.tsx
│   │   │
│   │   ├── setup/
│   │   │   ├── SetupWizard.tsx
│   │   │   ├── APIConfigStep.tsx
│   │   │   ├── BusinessProfileStep.tsx
│   │   │   ├── KnowledgeBaseStep.tsx
│   │   │   ├── AgentsStep.tsx
│   │   │   └── QASettingsStep.tsx
│   │   │
│   │   └── config/
│   │       ├── BusinessConfigList.tsx
│   │       ├── BusinessConfigForm.tsx
│   │       ├── KnowledgeBaseManager.tsx
│   │       ├── AgentManager.tsx
│   │       └── EscalationRulesForm.tsx
│   │
│   ├── hooks/
│   │   ├── useWebSocket.ts         # WebSocket hook
│   │   ├── useCalls.ts             # Calls data hook
│   │   ├── useCallDetail.ts        # Single call hook
│   │   ├── useAnalytics.ts         # Analytics hook
│   │   ├── useRealtimeUpdates.ts   # Real-time updates hook
│   │   └── useAuth.ts              # Authentication hook
│   │
│   ├── store/
│   │   ├── callsStore.ts           # Calls state (Zustand)
│   │   ├── uiStore.ts              # UI state (selected call, filters)
│   │   ├── authStore.ts            # Auth state
│   │   └── configStore.ts          # Config state
│   │
│   ├── services/
│   │   ├── websocket.ts            # WebSocket service
│   │   ├── auth.ts                # Auth service
│   │   └── storage.ts             # LocalStorage service
│   │
│   ├── types/
│   │   ├── call.ts                # Call types
│   │   ├── analytics.ts           # Analytics types
│   │   ├── config.ts              # Config types
│   │   ├── agent.ts               # Agent types
│   │   └── api.ts                 # API response types
│   │
│   ├── utils/
│   │   ├── format.ts              # Formatting utilities
│   │   ├── validation.ts          # Validation schemas
│   │   ├── constants.ts           # Constants
│   │   └── helpers.ts             # Helper functions
│   │
│   ├── pages/
│   │   ├── Dashboard.tsx          # Main dashboard
│   │   ├── Calls.tsx              # Calls list page
│   │   ├── Analytics.tsx          # Analytics page
│   │   ├── Settings.tsx           # Settings page
│   │   ├── Setup.tsx              # Setup wizard page
│   │   └── Login.tsx              # Login page
│   │
│   ├── App.tsx
│   ├── main.tsx
│   └── vite-env.d.ts
│
├── .env
├── .env.example
├── .gitignore
├── index.html
├── package.json
├── tsconfig.json
├── tailwind.config.js
├── vite.config.ts
└── README.md
```

---

## 3. State Management Architecture

### 3.1 Zustand Stores

**Calls Store (`callsStore.ts`):**
```typescript
interface CallsStore {
  // State
  calls: Call[]
  activeCalls: Call[]
  selectedCallId: string | null
  filters: CallFilters
  isLoading: boolean
  
  // Actions
  setCalls: (calls: Call[]) => void
  addCall: (call: Call) => void
  updateCall: (callId: string, updates: Partial<Call>) => void
  selectCall: (callId: string | null) => void
  setFilters: (filters: CallFilters) => void
  refreshCalls: () => Promise<void>
}
```

**UI Store (`uiStore.ts`):**
```typescript
interface UIStore {
  // State
  sidebarOpen: boolean
  theme: 'light' | 'dark'
  notifications: Notification[]
  
  // Actions
  toggleSidebar: () => void
  setTheme: (theme: 'light' | 'dark') => void
  addNotification: (notification: Notification) => void
  removeNotification: (id: string) => void
}
```

### 3.2 React Query for Server State

**Calls Query:**
```typescript
const useCalls = (filters: CallFilters) => {
  return useQuery({
    queryKey: ['calls', filters],
    queryFn: () => callsAPI.list(filters),
    refetchInterval: 5000, // Poll every 5 seconds
  })
}
```

**Call Detail Query:**
```typescript
const useCallDetail = (callId: string) => {
  return useQuery({
    queryKey: ['call', callId],
    queryFn: () => callsAPI.get(callId),
    enabled: !!callId,
  })
}
```

---

## 4. WebSocket Integration

### 4.1 WebSocket Service

```typescript
// services/websocket.ts
class WebSocketService {
  private socket: Socket | null = null
  private reconnectAttempts = 0
  private maxReconnectAttempts = 5

  connect() {
    this.socket = io(WS_URL, {
      transports: ['websocket'],
      reconnection: true,
      reconnectionDelay: 1000,
      reconnectionAttempts: this.maxReconnectAttempts,
    })

    this.socket.on('connect', () => {
      console.log('WebSocket connected')
      this.reconnectAttempts = 0
    })

    this.socket.on('disconnect', () => {
      console.log('WebSocket disconnected')
    })

    this.socket.on('error', (error) => {
      console.error('WebSocket error:', error)
    })
  }

  subscribeToCall(callId: string) {
    this.socket?.emit('subscribe', { callId })
  }

  unsubscribeFromCall(callId: string) {
    this.socket?.emit('unsubscribe', { callId })
  }

  onEvent(event: string, callback: (data: any) => void) {
    this.socket?.on(event, callback)
  }

  offEvent(event: string) {
    this.socket?.off(event)
  }

  disconnect() {
    this.socket?.disconnect()
  }
}
```

### 4.2 WebSocket Hook

```typescript
// hooks/useWebSocket.ts
export const useWebSocket = () => {
  const { updateCall, addInteraction } = useCallsStore()

  useEffect(() => {
    const ws = new WebSocketService()
    ws.connect()

    // Subscribe to general call updates
    ws.onEvent('call.started', (data) => {
      addCall(data.call)
    })

    ws.onEvent('call.updated', (data) => {
      updateCall(data.call.id, data.call)
    })

    ws.onEvent('interaction.added', (data) => {
      addInteraction(data.callId, data.interaction)
    })

    ws.onEvent('qa.score.updated', (data) => {
      updateCall(data.callId, { qaScore: data.score })
    })

    return () => {
      ws.disconnect()
    }
  }, [])
}
```

---

## 5. API Client Architecture

### 5.1 Axios Instance

```typescript
// api/client.ts
const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor for auth
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('auth_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Response interceptor for error handling
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Handle unauthorized
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)
```

### 5.2 API Endpoints

```typescript
// api/calls.ts
export const callsAPI = {
  list: (filters: CallFilters) => 
    apiClient.get('/calls', { params: filters }),
  
  get: (callId: string) => 
    apiClient.get(`/calls/${callId}`),
  
  getInteractions: (callId: string) => 
    apiClient.get(`/calls/${callId}/interactions`),
  
  escalate: (callId: string, data: EscalationData) => 
    apiClient.post(`/calls/${callId}/escalate`, data),
  
  intervene: (callId: string, data: InterventionData) => 
    apiClient.post(`/calls/${callId}/intervene`, data),
  
  end: (callId: string, reason?: string) => 
    apiClient.post(`/calls/${callId}/end`, { reason }),
  
  addNote: (callId: string, note: string) => 
    apiClient.post(`/calls/${callId}/notes`, { note }),
}
```

---

## 6. Component Architecture

### 6.1 Component Hierarchy

```
App
├── MainLayout
│   ├── Header
│   ├── Sidebar
│   └── PageContainer
│       ├── Dashboard (default)
│       │   ├── CallList (left panel)
│       │   └── CallDetail (right panel)
│       │       ├── CallHeader
│       │       ├── Transcript
│       │       ├── QAMetrics
│       │       └── CallActions
│       │
│       ├── Analytics
│       │   ├── MetricCards
│       │   ├── Charts
│       │   └── Tables
│       │
│       └── Settings
│           ├── BusinessConfigList
│           ├── KnowledgeBaseManager
│           └── AgentManager
```

### 6.2 Key Components

**CallList Component:**
- Displays list of calls
- Real-time updates via WebSocket
- Filtering and sorting
- Click to select call

**Transcript Component:**
- Real-time message display
- Auto-scrolling
- Speaker identification
- Sentiment highlighting
- Search functionality

**QAMetrics Component:**
- Score displays with gauges
- Sentiment timeline
- Compliance issues list
- Alert indicators

---

## 7. Real-Time Update Strategy

### 7.1 Hybrid Approach

**WebSocket for Real-Time:**
- New interactions
- Status changes
- QA score updates
- Escalation events

**Polling for Fallback:**
- If WebSocket fails, fall back to polling
- Poll every 5 seconds for active calls
- Poll every 30 seconds for analytics

### 7.2 Update Flow

```
1. WebSocket receives event
   ↓
2. Update Zustand store
   ↓
3. React Query cache invalidation (if needed)
   ↓
4. Component re-renders with new data
   ↓
5. Visual feedback (animations, highlights)
```

---

## 8. Performance Optimization

### 8.1 Code Splitting

```typescript
// Lazy load routes
const Dashboard = lazy(() => import('./pages/Dashboard'))
const Analytics = lazy(() => import('./pages/Analytics'))
const Settings = lazy(() => import('./pages/Settings'))
```

### 8.2 Memoization

```typescript
// Memoize expensive components
const CallListItem = memo(({ call }: { call: Call }) => {
  // Component implementation
})

// Memoize callbacks
const handleCallSelect = useCallback((callId: string) => {
  selectCall(callId)
}, [selectCall])
```

### 8.3 Virtual Scrolling

For long call lists and transcripts:
- Use `react-window` or `react-virtualized`
- Only render visible items
- Significantly improves performance

### 8.4 Debouncing

```typescript
// Debounce search input
const debouncedSearch = useMemo(
  () => debounce((query: string) => {
    setSearchQuery(query)
  }, 300),
  []
)
```

---

## 9. Error Handling

### 9.1 Error Boundaries

```typescript
// ErrorBoundary component
class ErrorBoundary extends React.Component {
  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    // Log to error tracking service
    logError(error, errorInfo)
  }

  render() {
    if (this.state.hasError) {
      return <ErrorFallback />
    }
    return this.props.children
  }
}
```

### 9.2 API Error Handling

```typescript
// Centralized error handling
try {
  const response = await callsAPI.get(callId)
  return response.data
} catch (error) {
  if (axios.isAxiosError(error)) {
    handleAPIError(error)
  } else {
    handleUnexpectedError(error)
  }
  throw error
}
```

---

## 10. Testing Strategy

### 10.1 Unit Tests

- Component tests with React Testing Library
- Hook tests
- Utility function tests
- Store tests

### 10.2 Integration Tests

- API integration tests
- WebSocket connection tests
- User flow tests

### 10.3 E2E Tests

- Playwright or Cypress
- Critical user journeys
- Real-time update scenarios

---

## 11. Deployment

### 11.1 Build Configuration

```typescript
// vite.config.ts
export default defineConfig({
  build: {
    outDir: 'dist',
    sourcemap: true,
    rollupOptions: {
      output: {
        manualChunks: {
          vendor: ['react', 'react-dom'],
          charts: ['recharts'],
        },
      },
    },
  },
})
```

### 11.2 Environment Variables

```bash
# .env.production
VITE_API_URL=https://api.yourdomain.com
VITE_WS_URL=wss://api.yourdomain.com/ws
VITE_APP_NAME=AI Caller Dashboard
```

### 11.3 Docker Deployment

```dockerfile
FROM node:18-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/nginx.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

---

## 12. Security Considerations

### 12.1 Authentication

- JWT tokens stored in httpOnly cookies (preferred) or localStorage
- Token refresh mechanism
- Automatic logout on token expiry

### 12.2 XSS Prevention

- Sanitize user input
- Use React's built-in XSS protection
- Content Security Policy headers

### 12.3 CORS

- Configure CORS on backend
- Only allow trusted origins
- Credentials handling

---

## 13. Monitoring & Observability

### 13.1 Error Tracking

- Sentry or similar service
- Track errors, performance issues
- User feedback collection

### 13.2 Analytics

- Track user interactions
- Monitor performance metrics
- A/B testing capabilities

### 13.3 Logging

- Structured logging
- Log levels (debug, info, warn, error)
- Centralized log aggregation

---

## 14. Development Workflow

### 14.1 Development Server

```bash
npm run dev
# Starts Vite dev server with HMR
```

### 14.2 Code Quality

- ESLint for linting
- Prettier for formatting
- Husky for git hooks
- Pre-commit checks

### 14.3 Type Safety

- Strict TypeScript configuration
- Type checking in CI/CD
- No `any` types allowed

---

## Conclusion

This architecture provides a solid foundation for building a scalable, maintainable, and performant call center manager dashboard. The modular structure allows for incremental development and easy maintenance.

Key principles:
- **Separation of concerns** - Clear boundaries between layers
- **Type safety** - TypeScript throughout
- **Performance** - Optimized rendering and data fetching
- **Real-time** - WebSocket integration for live updates
- **User experience** - Fast, responsive, intuitive interface

