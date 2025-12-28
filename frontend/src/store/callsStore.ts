import { create } from 'zustand';
import type { Call, CallFilters, CallInteraction } from '../types/call';

interface CallsStore {
  calls: Call[];
  activeCalls: Call[];
  selectedCallId: string | null;
  filters: CallFilters;
  isLoading: boolean;
  setCalls: (calls: Call[]) => void;
  addCall: (call: Call) => void;
  updateCall: (callId: string, updates: Partial<Call>) => void;
  removeCall: (callId: string) => void;
  selectCall: (callId: string | null) => void;
  setFilters: (filters: CallFilters) => void;
  refreshCalls: () => Promise<void>;
  addInteraction: (callId: string, interaction: CallInteraction) => void;
}

export const useCallsStore = create<CallsStore>((set, get) => ({
  calls: [],
  activeCalls: [],
  selectedCallId: null,
  filters: {},
  isLoading: false,

  setCalls: (calls) => {
    const activeCalls = calls.filter(
      (call) => call.status === 'in_progress' || call.status === 'ringing' || call.status === 'initiated'
    );
    set({ calls, activeCalls });
  },

  addCall: (call) => {
    const { calls } = get();
    const updatedCalls = [...calls, call];
    const activeCalls = updatedCalls.filter(
      (c) => c.status === 'in_progress' || c.status === 'ringing' || c.status === 'initiated'
    );
    set({ calls: updatedCalls, activeCalls });
  },

  updateCall: (callId, updates) => {
    const { calls } = get();
    const updatedCalls = calls.map((call) =>
      call.id === callId ? { ...call, ...updates } : call
    );
    const activeCalls = updatedCalls.filter(
      (c) => c.status === 'in_progress' || c.status === 'ringing' || c.status === 'initiated'
    );
    set({ calls: updatedCalls, activeCalls });
  },

  removeCall: (callId) => {
    const { calls } = get();
    const updatedCalls = calls.filter((call) => call.id !== callId);
    const activeCalls = updatedCalls.filter(
      (c) => c.status === 'in_progress' || c.status === 'ringing' || c.status === 'initiated'
    );
    set({ calls: updatedCalls, activeCalls });
  },

  selectCall: (callId) => set({ selectedCallId: callId }),

  setFilters: (filters) => set({ filters }),

  refreshCalls: async () => {
    // This will be implemented when we have the API hook
    set({ isLoading: true });
    // API call will be made by the component using this store
    set({ isLoading: false });
  },

  addInteraction: (callId, interaction) => {
    // Interactions are managed separately, but we can update call metadata if needed
    const { calls } = get();
    const call = calls.find((c) => c.id === callId);
    if (call) {
      // Update call's last interaction timestamp or other metadata
      get().updateCall(callId, {
        updated_at: interaction.timestamp,
      });
    }
  },
}));

