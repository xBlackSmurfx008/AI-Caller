import { useQuery } from '@tanstack/react-query';
import { analyticsAPI } from '../api/analytics';
import { subDays, format } from 'date-fns';

export const useAnalytics = (params?: {
  from_date?: string;
  to_date?: string;
  business_id?: string;
}) => {
  const defaultFromDate = format(subDays(new Date(), 7), 'yyyy-MM-dd');
  const defaultToDate = format(new Date(), 'yyyy-MM-dd');

  const overviewQuery = useQuery({
    queryKey: ['analytics', 'overview', params],
    queryFn: () =>
      analyticsAPI.getOverview({
        from_date: params?.from_date || defaultFromDate,
        to_date: params?.to_date || defaultToDate,
        business_id: params?.business_id,
      }),
  });

  const callVolumeQuery = useQuery({
    queryKey: ['analytics', 'call-volume', params],
    queryFn: () =>
      analyticsAPI.getCallVolume({
        from_date: params?.from_date || defaultFromDate,
        to_date: params?.to_date || defaultToDate,
        interval: 'day',
        business_id: params?.business_id,
      }),
  });

  const qaQuery = useQuery({
    queryKey: ['analytics', 'qa', params],
    queryFn: () =>
      analyticsAPI.getQA({
        from_date: params?.from_date || defaultFromDate,
        to_date: params?.to_date || defaultToDate,
        business_id: params?.business_id,
      }),
  });

  const sentimentQuery = useQuery({
    queryKey: ['analytics', 'sentiment', params],
    queryFn: () =>
      analyticsAPI.getSentiment({
        from_date: params?.from_date || defaultFromDate,
        to_date: params?.to_date || defaultToDate,
        business_id: params?.business_id,
      }),
  });

  const escalationsQuery = useQuery({
    queryKey: ['analytics', 'escalations', params],
    queryFn: () =>
      analyticsAPI.getEscalations({
        from_date: params?.from_date || defaultFromDate,
        to_date: params?.to_date || defaultToDate,
        business_id: params?.business_id,
      }),
  });

  return {
    overview: overviewQuery.data,
    callVolume: callVolumeQuery.data?.data || [],
    qa: qaQuery.data,
    sentiment: sentimentQuery.data,
    escalations: escalationsQuery.data,
    isLoading:
      overviewQuery.isLoading ||
      callVolumeQuery.isLoading ||
      qaQuery.isLoading ||
      sentimentQuery.isLoading ||
      escalationsQuery.isLoading,
    error:
      overviewQuery.error ||
      callVolumeQuery.error ||
      qaQuery.error ||
      sentimentQuery.error ||
      escalationsQuery.error,
  };
};

