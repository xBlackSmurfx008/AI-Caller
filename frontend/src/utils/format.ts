import { format, formatDistance, intervalToDuration } from 'date-fns';

export const formatDate = (date: string | Date): string => {
  return format(new Date(date), 'MMM d, yyyy');
};

export const formatDateTime = (date: string | Date): string => {
  return format(new Date(date), 'MMM d, yyyy HH:mm:ss');
};

export const formatTime = (date: string | Date): string => {
  return format(new Date(date), 'HH:mm:ss');
};

export const formatRelativeTime = (date: string | Date): string => {
  return formatDistance(new Date(date), new Date(), { addSuffix: true });
};

export const formatCallDuration = (seconds: number): string => {
  const duration = intervalToDuration({ start: 0, end: seconds * 1000 });
  
  if (duration.hours) {
    return `${duration.hours}h ${duration.minutes || 0}m ${duration.seconds || 0}s`;
  } else if (duration.minutes) {
    return `${duration.minutes}m ${duration.seconds || 0}s`;
  } else {
    return `${duration.seconds || 0}s`;
  }
};

export const formatPhoneNumber = (phone: string): string => {
  // Simple formatting - can be enhanced
  return phone.replace(/(\d{3})(\d{3})(\d{4})/, '($1) $2-$3');
};

export const formatPercentage = (value: number, decimals: number = 1): string => {
  return `${(value * 100).toFixed(decimals)}%`;
};

export const formatScore = (score: number, decimals: number = 2): string => {
  return score.toFixed(decimals);
};

