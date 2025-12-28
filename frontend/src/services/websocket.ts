import { io, Socket } from 'socket.io-client';
import { WS_URL } from '../utils/constants';

class WebSocketService {
  private socket: Socket | null = null;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 1000;
  private listeners: Map<string, Set<(data: any) => void>> = new Map();

  connect(token?: string) {
    if (this.socket?.connected) {
      return;
    }

    const url = token ? `${WS_URL}?token=${token}` : WS_URL;

    this.socket = io(url, {
      transports: ['websocket'],
      reconnection: true,
      reconnectionDelay: this.reconnectDelay,
      reconnectionAttempts: this.maxReconnectAttempts,
    });

    this.socket.on('connect', () => {
      console.log('WebSocket connected');
      this.reconnectAttempts = 0;
      this.emit('connected', {});
    });

    this.socket.on('disconnect', () => {
      console.log('WebSocket disconnected');
    });

    this.socket.on('error', (error) => {
      console.error('WebSocket error:', error);
    });

    this.socket.on('reconnect', (attemptNumber) => {
      console.log('WebSocket reconnected after', attemptNumber, 'attempts');
      this.reconnectAttempts = 0;
    });

    this.socket.on('reconnect_attempt', (attemptNumber) => {
      console.log('WebSocket reconnect attempt', attemptNumber);
      this.reconnectAttempts = attemptNumber;
    });

    this.socket.on('reconnect_failed', () => {
      console.error('WebSocket reconnection failed');
    });

    // Set up event listeners
    this.setupEventListeners();
  }

  private setupEventListeners() {
    if (!this.socket) return;

    // Listen for all events and forward to registered listeners
    const events = [
      'call.started',
      'call.updated',
      'call.ended',
      'interaction.added',
      'qa.score.updated',
      'sentiment.changed',
      'escalation.triggered',
      'escalation.completed',
      'notification.created',
    ];

    events.forEach((event) => {
      this.socket?.on(event, (data) => {
        const listeners = this.listeners.get(event);
        if (listeners) {
          listeners.forEach((listener) => listener(data));
        }
      });
    });
  }

  subscribe(event: string, callback: (data: any) => void) {
    if (!this.listeners.has(event)) {
      this.listeners.set(event, new Set());
    }
    this.listeners.get(event)?.add(callback);

    // If subscribing to a specific call, emit subscribe event
    if (event.startsWith('call.') && this.socket?.connected) {
      this.emit('subscribe', { type: 'call', event });
    }
  }

  unsubscribe(event: string, callback: (data: any) => void) {
    const listeners = this.listeners.get(event);
    if (listeners) {
      listeners.delete(callback);
      if (listeners.size === 0) {
        this.listeners.delete(event);
      }
    }
  }

  subscribeToCall(callId: string) {
    if (this.socket?.connected) {
      this.emit('subscribe', { type: 'call', call_id: callId });
    }
  }

  unsubscribeFromCall(callId: string) {
    if (this.socket?.connected) {
      this.emit('unsubscribe', { type: 'call', call_id: callId });
    }
  }

  subscribeToAllCalls() {
    if (this.socket?.connected) {
      this.emit('subscribe', { type: 'all_calls' });
    }
  }

  emit(event: string, data: any) {
    if (this.socket?.connected) {
      this.socket.emit(event, data);
    }
  }

  disconnect() {
    if (this.socket) {
      this.socket.disconnect();
      this.socket = null;
      this.listeners.clear();
    }
  }

  isConnected(): boolean {
    return this.socket?.connected || false;
  }
}

export const websocketService = new WebSocketService();

