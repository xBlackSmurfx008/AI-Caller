# AI Caller - Frontend Dashboard

React + TypeScript frontend application for the AI Caller call center management system.

## Features

- **Real-time Call Monitoring** - Live updates via WebSocket
- **Call Management** - View transcripts, QA metrics, and manage calls
- **Analytics Dashboard** - Comprehensive metrics and charts
- **Configuration Management** - Business configs, agents, knowledge base
- **Setup Wizard** - Guided initial configuration

## Tech Stack

- **React 18+** with TypeScript
- **Vite** - Build tool and dev server
- **Zustand** - State management
- **React Query** - Server state management
- **Socket.io-client** - WebSocket communication
- **Tailwind CSS** - Styling
- **Recharts** - Data visualization
- **React Router** - Routing
- **React Hook Form + Zod** - Form handling and validation

## Getting Started

### Prerequisites

- Node.js 18+ and npm
- Backend API running on `http://localhost:8000`

### Installation

```bash
# Install dependencies
npm install

# Start development server
npm run dev
```

The app will be available at `http://localhost:5173`

### Environment Variables

Create a `.env` file in the frontend directory:

```env
VITE_API_URL=http://localhost:8000/api/v1
VITE_WS_URL=ws://localhost:8000/ws/calls
```

## Project Structure

```
frontend/
├── src/
│   ├── api/              # API client and endpoints
│   ├── components/       # React components
│   │   ├── common/      # Reusable UI components
│   │   ├── layout/      # Layout components
│   │   ├── calls/       # Call-related components
│   │   ├── analytics/   # Analytics components
│   │   ├── setup/       # Setup wizard components
│   │   └── config/      # Configuration components
│   ├── hooks/           # Custom React hooks
│   ├── store/           # Zustand stores
│   ├── services/        # Services (WebSocket, auth)
│   ├── types/           # TypeScript types
│   ├── utils/           # Utility functions
│   └── pages/           # Page components
├── public/              # Static assets
└── package.json
```

## Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run preview` - Preview production build
- `npm run lint` - Run ESLint

## Key Features Implementation

### Real-time Updates

The app uses WebSocket for real-time call updates. The WebSocket service automatically reconnects on disconnect and handles all call-related events.

### State Management

- **Zustand** for client-side state (calls, UI, auth, config)
- **React Query** for server state (API data, caching, refetching)

### Authentication

Mock authentication is implemented for development. In production, integrate with your backend auth system.

## Development Notes

- The app uses mock authentication for development
- Some API endpoints may not be fully implemented on the backend yet
- WebSocket server needs to be implemented on the backend
- All components are responsive and work on mobile/tablet/desktop

## Building for Production

```bash
npm run build
```

The production build will be in the `dist/` directory.

## License

[Your License Here]
