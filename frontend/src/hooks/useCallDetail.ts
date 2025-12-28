import { useQuery } from '@tanstack/react-query';
import { callsAPI } from '../api/calls';
import type { Call, CallInteraction } from '../types/call';

export const useCallDetail = (callId: string | null) => {
  const callQuery = useQuery({
    queryKey: ['call', callId],
    queryFn: async () => {
      if (!callId) return null;
      return await callsAPI.get(callId);
    },
    enabled: !!callId,
  });

  const interactionsQuery = useQuery({
    queryKey: ['call-interactions', callId],
    queryFn: async () => {
      if (!callId) return { interactions: [], total: 0 };
      return await callsAPI.getInteractions(callId);
    },
    enabled: !!callId,
    refetchInterval: 2000, // Poll every 2 seconds for new interactions
  });

  return {
    call: callQuery.data || null,
    interactions: interactionsQuery.data?.interactions || [],
    isLoading: callQuery.isLoading || interactionsQuery.isLoading,
    error: callQuery.error || interactionsQuery.error,
    refetch: () => {
      callQuery.refetch();
      interactionsQuery.refetch();
    },
  };
};

