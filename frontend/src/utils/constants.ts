// Use relative URL in development to leverage Vite proxy, absolute URL in production
export const API_BASE_URL = import.meta.env.VITE_API_URL || (import.meta.env.DEV ? '/api/v1' : 'http://localhost:8000/api/v1');
export const WS_URL = import.meta.env.VITE_WS_URL || (import.meta.env.DEV ? 'ws://localhost:8000/ws/calls' : 'ws://localhost:8000/ws/calls');

export const CALL_STATUS_COLORS = {
  initiated: 'gray',
  ringing: 'blue',
  in_progress: 'green',
  completed: 'gray',
  failed: 'red',
  escalated: 'orange',
} as const;

export const SENTIMENT_EMOJIS = {
  positive: '😊',
  neutral: '😐',
  negative: '😞',
} as const;

export const SENTIMENT_COLORS = {
  positive: 'green',
  neutral: 'yellow',
  negative: 'red',
} as const;

