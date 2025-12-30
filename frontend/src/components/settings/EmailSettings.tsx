import { useGmailStatus, useGmailOAuth, useOutlookStatus, useOutlookOAuth } from '@/lib/hooks';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { CheckCircle2, XCircle, Loader2, AlertCircle, Mail } from 'lucide-react';

export const EmailSettings = () => {
  const { data: gmailStatus, isLoading: gmailLoading, error: gmailError, refetch: refetchGmail } = useGmailStatus();
  const { data: outlookStatus, isLoading: outlookLoading, error: outlookError, refetch: refetchOutlook } = useOutlookStatus();
  const gmailOAuth = useGmailOAuth();
  const outlookOAuth = useOutlookOAuth();

  const gmailConnected = gmailStatus?.connected ?? false;
  const outlookConnected = outlookStatus?.connected ?? false;

  const handleGmailConnect = () => {
    gmailOAuth.mutate();
  };

  const handleOutlookConnect = () => {
    outlookOAuth.mutate();
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-white mb-2">Email Accounts</h2>
        <p className="text-slate-400">
          Connect your Gmail or Outlook accounts to enable email sending and reading
        </p>
      </div>

      {/* Gmail Card */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Mail className="w-5 h-5" />
            Gmail
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {gmailLoading && gmailStatus === undefined && !gmailError && (
            <div className="flex items-center justify-center py-4">
              <Loader2 className="w-6 h-6 animate-spin text-purple-600" />
            </div>
          )}
          
          {gmailError && (
            <div className="bg-amber-500/10 border border-amber-500/30 rounded-lg p-3 flex items-center gap-2">
              <AlertCircle className="w-4 h-4 text-amber-400" />
              <p className="text-sm text-amber-300 flex-1">Unable to check Gmail status</p>
              <Button onClick={() => refetchGmail()} variant="ghost" size="sm" className="ml-auto">
                Retry
              </Button>
            </div>
          )}
          
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              {gmailConnected ? (
                <>
                  <CheckCircle2 className="w-5 h-5 text-emerald-400" />
                  <Badge variant="success">Connected</Badge>
                </>
              ) : (
                <>
                  <XCircle className="w-5 h-5 text-red-400" />
                  <Badge variant="error">Not Connected</Badge>
                </>
              )}
            </div>
            <Button
              onClick={handleGmailConnect}
              disabled={gmailOAuth.isPending}
              variant={gmailConnected ? 'outline' : 'primary'}
            >
              {gmailOAuth.isPending ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  Connecting...
                </>
              ) : gmailConnected ? (
                'Reconnect'
              ) : (
                'Connect Gmail'
              )}
            </Button>
          </div>
          
          {gmailConnected && (
            <div className="bg-emerald-500/10 border border-emerald-500/30 rounded-lg p-3">
              <p className="text-sm text-emerald-300">
                Gmail is connected. You can now send and read emails via Gmail.
              </p>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Outlook Card */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Mail className="w-5 h-5" />
            Outlook
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {outlookLoading && outlookStatus === undefined && !outlookError && (
            <div className="flex items-center justify-center py-4">
              <Loader2 className="w-6 h-6 animate-spin text-purple-600" />
            </div>
          )}
          
          {outlookError && (
            <div className="bg-amber-500/10 border border-amber-500/30 rounded-lg p-3 flex items-center gap-2">
              <AlertCircle className="w-4 h-4 text-amber-400" />
              <p className="text-sm text-amber-300 flex-1">Unable to check Outlook status</p>
              <Button onClick={() => refetchOutlook()} variant="ghost" size="sm" className="ml-auto">
                Retry
              </Button>
            </div>
          )}
          
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              {outlookConnected ? (
                <>
                  <CheckCircle2 className="w-5 h-5 text-emerald-400" />
                  <Badge variant="success">Connected</Badge>
                </>
              ) : (
                <>
                  <XCircle className="w-5 h-5 text-red-400" />
                  <Badge variant="error">Not Connected</Badge>
                </>
              )}
            </div>
            <Button
              onClick={handleOutlookConnect}
              disabled={outlookOAuth.isPending}
              variant={outlookConnected ? 'outline' : 'primary'}
            >
              {outlookOAuth.isPending ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  Connecting...
                </>
              ) : outlookConnected ? (
                'Reconnect'
              ) : (
                'Connect Outlook'
              )}
            </Button>
          </div>
          
          {outlookConnected && (
            <div className="bg-emerald-500/10 border border-emerald-500/30 rounded-lg p-3">
              <p className="text-sm text-emerald-300">
                Outlook is connected. You can now send and read emails via Outlook.
              </p>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Info Card */}
      <Card>
        <CardContent className="pt-6">
          <div className="bg-purple-500/10 border border-purple-500/30 rounded-lg p-4">
            <h3 className="text-sm font-semibold text-purple-300 mb-2">How it works</h3>
            <ul className="text-sm text-purple-200 space-y-1 list-disc list-inside">
              <li>Connect your Gmail or Outlook account using OAuth</li>
              <li>The AI assistant can automatically send emails using your connected account</li>
              <li>You can also read and search your emails through the AI</li>
              <li>If both are connected, Gmail will be preferred, then Outlook, then SMTP fallback</li>
            </ul>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

