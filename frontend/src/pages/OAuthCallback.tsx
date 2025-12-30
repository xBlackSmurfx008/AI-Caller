import { useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { useQueryClient } from '@tanstack/react-query';
import { Card, CardContent } from '@/components/ui/Card';
import { CheckCircle2, XCircle, Loader2 } from 'lucide-react';

export const OAuthCallback = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const code = searchParams.get('code');
  const error = searchParams.get('error');
  const pathname = window.location.pathname;

  // Determine which service based on the callback path
  const isGmail = pathname.includes('/gmail/oauth/callback');
  const isOutlook = pathname.includes('/outlook/oauth/callback');
  const isCalendar = pathname.includes('/calendar/oauth/callback') || (!isGmail && !isOutlook);

  useEffect(() => {
    if (code || error) {
      // Invalidate appropriate status queries
      if (isGmail) {
        queryClient.invalidateQueries({ queryKey: ['gmail', 'status'] });
      } else if (isOutlook) {
        queryClient.invalidateQueries({ queryKey: ['outlook', 'status'] });
      } else {
        queryClient.invalidateQueries({ queryKey: ['calendar', 'status'] });
      }
      
      // Redirect to appropriate page after a short delay
      setTimeout(() => {
        if (isGmail || isOutlook) {
          navigate('/settings');
        } else {
          navigate('/calendar');
        }
      }, 2000);
    }
  }, [code, error, navigate, queryClient, isGmail, isOutlook]);

  const getServiceName = () => {
    if (isGmail) return 'Gmail';
    if (isOutlook) return 'Outlook';
    return 'Google Calendar';
  };

  const getRedirectPage = () => {
    if (isGmail || isOutlook) return 'settings page';
    return 'calendar page';
  };

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center p-4">
        <Card className="max-w-md w-full">
          <CardContent className="pt-6 text-center">
            <XCircle className="w-12 h-12 text-red-600 mx-auto mb-4" />
            <h2 className="text-xl font-semibold text-gray-900 mb-2">Authorization Failed</h2>
            <p className="text-gray-600 mb-4">{error}</p>
            <p className="text-sm text-gray-500">Redirecting to {getRedirectPage()}...</p>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (code) {
    return (
      <div className="min-h-screen flex items-center justify-center p-4">
        <Card className="max-w-md w-full">
          <CardContent className="pt-6 text-center">
            <CheckCircle2 className="w-12 h-12 text-green-600 mx-auto mb-4" />
            <h2 className="text-xl font-semibold text-gray-900 mb-2">Authorization Successful</h2>
            <p className="text-gray-600 mb-4">Your {getServiceName()} has been connected.</p>
            <p className="text-sm text-gray-500">Redirecting to {getRedirectPage()}...</p>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex items-center justify-center p-4">
      <Card className="max-w-md w-full">
        <CardContent className="pt-6 text-center">
          <Loader2 className="w-12 h-12 text-purple-600 mx-auto mb-4 animate-spin" />
          <p className="text-gray-600">Processing authorization...</p>
        </CardContent>
      </Card>
    </div>
  );
};

