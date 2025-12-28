import { useQuery } from '@tanstack/react-query';
import { callsAPI } from '../api/calls';
import type { CallFilters } from '../types/call';
import { useCallsStore } from '../store/callsStore';

export const useCalls = (filters?: CallFilters) => {
  const { setCalls } = useCallsStore();

  return useQuery({
    queryKey: ['calls', filters],
    queryFn: async () => {
      const response = await callsAPI.list(filters);
      setCalls(response.calls);
      return response;
    },
    refetchInterval: 5000, // Poll every 5 seconds as fallback
    staleTime: 2000,
  });
};

