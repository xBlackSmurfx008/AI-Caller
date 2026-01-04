import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { useCalendarOAuth, useGmailOAuth, useOutlookOAuth, useCalendarStatus, useGmailStatus, useOutlookStatus } from '@/lib/hooks';
import { Loader2, CheckCircle2, Calendar, Mail, MessageSquare, Star, DollarSign, ArrowRight, ArrowLeft, Sparkles, Users } from 'lucide-react';
import toast from 'react-hot-toast';

interface OnboardingStep {
  id: string;
  title: string;
  description: string;
  icon: React.ComponentType<{ className?: string }>;
  optional?: boolean;
}

const steps: OnboardingStep[] = [
  {
    id: 'welcome',
    title: 'Welcome to AI Caller',
    description: 'Your AI-powered CRM and task orchestrator. Let\'s get you set up in under 5 minutes.',
    icon: Sparkles,
  },
  {
    id: 'calendar',
    title: 'Connect Your Calendar',
    description: 'Connect Google Calendar, Apple Calendar, Outlook, or any ICS feed.',
    icon: Calendar,
    optional: true, // Allow skipping - can be configured later in Settings
  },
  {
    id: 'email',
    title: 'Connect Email',
    description: 'Connect Gmail or Outlook to enable AI email management.',
    icon: Mail,
    optional: true,
  },
  {
    id: 'messaging',
    title: 'Set Up Messaging',
    description: 'Configure Twilio for SMS/WhatsApp messaging (can be done later).',
    icon: MessageSquare,
    optional: true,
  },
  {
    id: 'trusted',
    title: 'Add Trusted Preferences',
    description: 'Add your favorite vendors, providers, and defaults for AI to use automatically.',
    icon: Star,
    optional: true,
  },
  {
    id: 'budget',
    title: 'Set Budget Alerts',
    description: 'Configure spending limits and alerts to monitor AI service costs.',
    icon: DollarSign,
    optional: true,
  },
  {
    id: 'contacts',
    title: 'Import Contacts',
    description: 'Import your contacts to get started with relationship management.',
    icon: Users,
    optional: true,
  },
];

export const Onboarding = () => {
  const navigate = useNavigate();
  const [currentStep, setCurrentStep] = useState(0);
  const [completedSteps, setCompletedSteps] = useState<Set<string>>(new Set());
  const [skippedSteps, setSkippedSteps] = useState<Set<string>>(new Set());

  const calendarOAuth = useCalendarOAuth();
  const gmailOAuth = useGmailOAuth();
  const outlookOAuth = useOutlookOAuth();
  const { data: calendarStatus } = useCalendarStatus();
  const { data: gmailStatus } = useGmailStatus();
  const { data: outlookStatus } = useOutlookStatus();

  // Check if user has already completed onboarding
  // Use prefixed storage key for iOS WKWebView compatibility
  useEffect(() => {
    const onboardingCompleted = localStorage.getItem('aiadmin_onboarding_completed');
    if (onboardingCompleted === 'true') {
      navigate('/');
    }
  }, [navigate]);

  // Track completed steps
  useEffect(() => {
    const newCompleted = new Set(completedSteps);
    
    if (calendarStatus?.connected) {
      newCompleted.add('calendar');
    }
    if (gmailStatus?.connected || outlookStatus?.connected) {
      newCompleted.add('email');
    }
    
    setCompletedSteps(newCompleted);
  }, [calendarStatus, gmailStatus, outlookStatus, completedSteps]);

  const handleNext = () => {
    if (currentStep < steps.length - 1) {
      setCurrentStep(currentStep + 1);
    } else {
      handleComplete();
    }
  };

  const handleBack = () => {
    if (currentStep > 0) {
      setCurrentStep(currentStep - 1);
    }
  };

  const handleSkip = () => {
    const step = steps[currentStep];
    if (step.optional) {
      setSkippedSteps(new Set([...skippedSteps, step.id]));
      handleNext();
    }
  };

  const handleComplete = () => {
    localStorage.setItem('aiadmin_onboarding_completed', 'true');
    toast.success('Welcome! You\'re all set up.');
    navigate('/');
  };

  const handleConnectCalendar = async () => {
    try {
      await calendarOAuth.mutateAsync();
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Failed to connect calendar');
    }
  };

  const handleConnectGmail = async () => {
    try {
      await gmailOAuth.mutateAsync();
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Failed to connect Gmail');
    }
  };

  const handleConnectOutlook = async () => {
    try {
      await outlookOAuth.mutateAsync();
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Failed to connect Outlook');
    }
  };

  const currentStepData = steps[currentStep];
  const Icon = currentStepData.icon;
  const isCompleted = completedSteps.has(currentStepData.id);
  const isSkipped = skippedSteps.has(currentStepData.id);
  const progress = ((currentStep + 1) / steps.length) * 100;

  return (
    <div className="min-h-screen flex items-center justify-center px-4 py-8">
      <div className="max-w-2xl w-full">
        {/* Progress Bar */}
        <div className="mb-8">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm text-slate-400">
              Step {currentStep + 1} of {steps.length}
            </span>
            <span className="text-sm text-slate-400">{Math.round(progress)}%</span>
          </div>
          <div className="w-full bg-slate-700 rounded-full h-2">
            <div
              className="bg-gradient-to-r from-purple-600 to-indigo-600 h-2 rounded-full transition-all duration-300"
              style={{ width: `${progress}%` }}
            />
          </div>
        </div>

        {/* Step Card */}
        <Card className="bg-slate-900/50 border-slate-700">
          <CardHeader>
            <div className="flex items-center gap-4 mb-4">
              <div className={`p-3 rounded-lg ${
                isCompleted
                  ? 'bg-emerald-500/20 text-emerald-400'
                  : 'bg-purple-500/20 text-purple-400'
              }`}>
                {isCompleted ? (
                  <CheckCircle2 className="w-6 h-6" />
                ) : (
                  <Icon className="w-6 h-6" />
                )}
              </div>
              <div className="flex-1">
                <CardTitle className="text-white text-2xl mb-2">
                  {currentStepData.title}
                </CardTitle>
                {currentStepData.optional && (
                  <span className="text-xs text-slate-400 bg-slate-800/50 px-2 py-1 rounded">
                    Optional
                  </span>
                )}
              </div>
            </div>
          </CardHeader>
          <CardContent>
            <p className="text-slate-400 mb-6">{currentStepData.description}</p>

            {/* Step-specific content */}
            {currentStepData.id === 'welcome' && (
              <div className="space-y-4">
                <div className="bg-slate-800/50 rounded-lg p-4">
                  <h4 className="font-semibold text-white mb-2">What you can do:</h4>
                  <ul className="space-y-2 text-sm text-slate-300">
                    <li className="flex items-start gap-2">
                      <CheckCircle2 className="w-4 h-4 text-emerald-400 mt-0.5 flex-shrink-0" />
                      <span>Manage contacts and relationships</span>
                    </li>
                    <li className="flex items-start gap-2">
                      <CheckCircle2 className="w-4 h-4 text-emerald-400 mt-0.5 flex-shrink-0" />
                      <span>Create projects with AI-powered task planning</span>
                    </li>
                    <li className="flex items-start gap-2">
                      <CheckCircle2 className="w-4 h-4 text-emerald-400 mt-0.5 flex-shrink-0" />
                      <span>Schedule tasks automatically</span>
                    </li>
                    <li className="flex items-start gap-2">
                      <CheckCircle2 className="w-4 h-4 text-emerald-400 mt-0.5 flex-shrink-0" />
                      <span>Send messages with AI assistance</span>
                    </li>
                    <li className="flex items-start gap-2">
                      <CheckCircle2 className="w-4 h-4 text-emerald-400 mt-0.5 flex-shrink-0" />
                      <span>Monitor costs and budgets</span>
                    </li>
                  </ul>
                </div>
              </div>
            )}

            {currentStepData.id === 'calendar' && (
              <div className="space-y-4">
                {isCompleted ? (
                  <div className="bg-emerald-500/10 border border-emerald-500/30 rounded-lg p-4">
                    <div className="flex items-center gap-2 text-emerald-400">
                      <CheckCircle2 className="w-5 h-5" />
                      <span className="font-medium">Calendar connected</span>
                    </div>
                  </div>
                ) : (
                  <div className="space-y-4">
                    {/* Google Calendar */}
                    <div className="space-y-2">
                      <Button
                        onClick={handleConnectCalendar}
                        disabled={calendarOAuth.isPending}
                        variant="primary"
                        className="w-full"
                      >
                        {calendarOAuth.isPending ? (
                          <Loader2 className="w-4 h-4 animate-spin mr-2" />
                        ) : (
                          <Calendar className="w-4 h-4 mr-2" />
                        )}
                        Connect Google Calendar
                      </Button>
                    </div>

                    {/* Divider */}
                    <div className="relative">
                      <div className="absolute inset-0 flex items-center">
                        <div className="w-full border-t border-slate-700"></div>
                      </div>
                      <div className="relative flex justify-center text-sm">
                        <span className="px-2 bg-slate-900 text-slate-400">or</span>
                      </div>
                    </div>

                    {/* ICS / Other Calendar */}
                    <div className="bg-slate-800/50 rounded-lg p-4 border border-slate-700">
                      <h4 className="text-sm font-medium text-white mb-2">Other Calendars</h4>
                      <p className="text-xs text-slate-400 mb-3">
                        Apple Calendar, Outlook, or any ICS feed can be connected in Settings.
                      </p>
                      <Button
                        variant="secondary"
                        size="sm"
                        onClick={() => {
                          setSkippedSteps(new Set([...skippedSteps, 'calendar']));
                          navigate('/settings');
                        }}
                        className="w-full"
                      >
                        Set Up Later in Settings
                      </Button>
                    </div>

                    <p className="text-xs text-slate-500 text-center">
                      Calendar integration is recommended but not required.
                    </p>
                  </div>
                )}
              </div>
            )}

            {currentStepData.id === 'email' && (
              <div className="space-y-4">
                {isCompleted ? (
                  <div className="bg-emerald-500/10 border border-emerald-500/30 rounded-lg p-4">
                    <div className="flex items-center gap-2 text-emerald-400">
                      <CheckCircle2 className="w-5 h-5" />
                      <span className="font-medium">Email connected</span>
                    </div>
                  </div>
                ) : (
                  <div className="grid grid-cols-2 gap-3">
                    <Button
                      onClick={handleConnectGmail}
                      disabled={gmailOAuth.isPending || gmailStatus?.connected}
                      variant={gmailStatus?.connected ? 'secondary' : 'primary'}
                      className="w-full"
                    >
                      {gmailOAuth.isPending ? (
                        <Loader2 className="w-4 h-4 animate-spin mr-2" />
                      ) : gmailStatus?.connected ? (
                        <CheckCircle2 className="w-4 h-4 mr-2" />
                      ) : (
                        <Mail className="w-4 h-4 mr-2" />
                      )}
                      Gmail
                    </Button>
                    <Button
                      onClick={handleConnectOutlook}
                      disabled={outlookOAuth.isPending || outlookStatus?.connected}
                      variant={outlookStatus?.connected ? 'secondary' : 'primary'}
                      className="w-full"
                    >
                      {outlookOAuth.isPending ? (
                        <Loader2 className="w-4 h-4 animate-spin mr-2" />
                      ) : outlookStatus?.connected ? (
                        <CheckCircle2 className="w-4 h-4 mr-2" />
                      ) : (
                        <Mail className="w-4 h-4 mr-2" />
                      )}
                      Outlook
                    </Button>
                  </div>
                )}
              </div>
            )}

            {currentStepData.id === 'messaging' && (
              <div className="space-y-4">
                <div className="bg-slate-800/50 rounded-lg p-4">
                  <p className="text-sm text-slate-300 mb-3">
                    Twilio messaging setup requires API credentials. You can configure this later in Settings.
                  </p>
                  <Button
                    onClick={() => navigate('/settings')}
                    variant="secondary"
                    className="w-full"
                  >
                    Go to Settings
                  </Button>
                </div>
              </div>
            )}

            {currentStepData.id === 'trusted' && (
              <div className="space-y-4">
                <div className="bg-slate-800/50 rounded-lg p-4">
                  <p className="text-sm text-slate-300 mb-3">
                    Add vendors, providers, and defaults that AI will use automatically.
                  </p>
                  <Button
                    onClick={() => navigate('/trusted-list')}
                    variant="secondary"
                    className="w-full"
                  >
                    Go to Trusted List
                  </Button>
                </div>
              </div>
            )}

            {currentStepData.id === 'budget' && (
              <div className="space-y-4">
                <div className="bg-slate-800/50 rounded-lg p-4">
                  <p className="text-sm text-slate-300 mb-3">
                    Set spending limits and alerts to monitor AI service costs.
                  </p>
                  <Button
                    onClick={() => navigate('/cost')}
                    variant="secondary"
                    className="w-full"
                  >
                    Go to Cost Monitoring
                  </Button>
                </div>
              </div>
            )}

            {currentStepData.id === 'contacts' && (
              <div className="space-y-4">
                <div className="bg-slate-800/50 rounded-lg p-4">
                  <p className="text-sm text-slate-300 mb-3">
                    Import contacts from your phone or upload a vCard/CSV file.
                  </p>
                  <Button
                    onClick={() => navigate('/contacts')}
                    variant="secondary"
                    className="w-full"
                  >
                    Go to Contacts
                  </Button>
                </div>
              </div>
            )}

            {/* Navigation Buttons */}
            <div className="flex items-center justify-between mt-8 pt-6 border-t border-slate-700">
              <div>
                {currentStep > 0 && (
                  <Button variant="ghost" onClick={handleBack}>
                    <ArrowLeft className="w-4 h-4 mr-2" />
                    Back
                  </Button>
                )}
              </div>
              <div className="flex gap-2">
                {currentStepData.optional && !isCompleted && (
                  <Button variant="ghost" onClick={handleSkip}>
                    Skip
                  </Button>
                )}
                <Button
                  variant="primary"
                  onClick={handleNext}
                >
                  {currentStep === steps.length - 1 ? 'Complete Setup' : 'Next'}
                  {currentStep < steps.length - 1 && <ArrowRight className="w-4 h-4 ml-2" />}
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

