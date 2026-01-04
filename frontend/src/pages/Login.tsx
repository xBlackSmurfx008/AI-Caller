import { useState, useEffect, useRef, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '@/lib/AuthContext';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card';
import { Loader2, AlertCircle, Sparkles } from 'lucide-react';

// Simple auth - credentials are verified client-side for this deployment
const VALID_EMAIL = 'ceo@digiwealth.io';
const VALID_PASSWORD = '062210';

export const Login = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [shouldNavigate, setShouldNavigate] = useState(false);
  const navigate = useNavigate();
  const { signIn, isAuthenticated } = useAuth();
  const formRef = useRef<HTMLFormElement>(null);

  // Scroll focused input into view when keyboard appears (iOS fix)
  const handleInputFocus = useCallback((e: React.FocusEvent<HTMLInputElement>) => {
    // Delay to allow keyboard to appear
    setTimeout(() => {
      e.target.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }, 300);
  }, []);

  // Use effect to handle navigation after auth state is confirmed
  // This is more reliable on iOS WKWebView than navigating in the submit handler
  useEffect(() => {
    if (shouldNavigate && isAuthenticated) {
      // Use requestAnimationFrame to ensure DOM is ready before navigation
      requestAnimationFrame(() => {
        navigate('/', { replace: true });
      });
    }
  }, [shouldNavigate, isAuthenticated, navigate]);

  // If already authenticated, redirect immediately
  useEffect(() => {
    if (isAuthenticated) {
      navigate('/', { replace: true });
    }
  }, [isAuthenticated, navigate]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setIsLoading(true);

    // Simulate network delay
    await new Promise(resolve => setTimeout(resolve, 300));

    if (email.toLowerCase() === VALID_EMAIL && password === VALID_PASSWORD) {
      // Update auth state - this will trigger the useEffect above
      signIn(email);
      // Signal that we should navigate once auth state is confirmed
      setShouldNavigate(true);
      return;
    } else {
      setError('Invalid email or password');
    }
    
    setIsLoading(false);
  };

  return (
    <div className="min-h-screen flex items-start justify-center bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 p-4 pt-[15vh] overflow-auto">
      <div className="absolute inset-0 bg-[url('data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNjAiIGhlaWdodD0iNjAiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+PGRlZnM+PHBhdHRlcm4gaWQ9ImdyaWQiIHdpZHRoPSI2MCIgaGVpZ2h0PSI2MCIgcGF0dGVyblVuaXRzPSJ1c2VyU3BhY2VPblVzZSI+PHBhdGggZD0iTSA2MCAwIEwgMCAwIDAgNjAiIGZpbGw9Im5vbmUiIHN0cm9rZT0icmdiYSgyNTUsMjU1LDI1NSwwLjAzKSIgc3Ryb2tlLXdpZHRoPSIxIi8+PC9wYXR0ZXJuPjwvZGVmcz48cmVjdCB3aWR0aD0iMTAwJSIgaGVpZ2h0PSIxMDAlIiBmaWxsPSJ1cmwoI2dyaWQpIi8+PC9zdmc+')] opacity-40 pointer-events-none" />
      
      <Card className="w-full max-w-md relative z-10 bg-slate-800/90 border-slate-700 backdrop-blur-sm shadow-2xl mb-[50vh]">
        <CardHeader className="text-center pb-2">
          <div className="mx-auto mb-4 w-16 h-16 bg-gradient-to-br from-purple-500 to-pink-500 rounded-2xl flex items-center justify-center shadow-lg shadow-purple-500/30">
            <Sparkles className="w-8 h-8 text-white" />
          </div>
          <CardTitle className="text-2xl font-bold bg-gradient-to-r from-white to-purple-200 bg-clip-text text-transparent">
            AI Caller
          </CardTitle>
          <p className="text-slate-400 mt-2">Sign in to your account</p>
        </CardHeader>
        
        <CardContent>
          <form ref={formRef} onSubmit={handleSubmit} className="space-y-4">
            {error && (
              <div className="bg-red-500/10 border border-red-500/50 rounded-lg p-3 flex items-center gap-2">
                <AlertCircle className="w-4 h-4 text-red-400 flex-shrink-0" />
                <p className="text-sm text-red-300">{error}</p>
              </div>
            )}
            
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2">
                Email
              </label>
              <Input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                onFocus={handleInputFocus}
                placeholder="you@example.com"
                disabled={isLoading}
                required
                autoComplete="email"
                className="bg-slate-900/50 border-slate-600 text-white placeholder:text-slate-500 focus:border-purple-500 focus:ring-purple-500"
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2">
                Password
              </label>
              <Input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                onFocus={handleInputFocus}
                placeholder="••••••••"
                disabled={isLoading}
                required
                autoComplete="current-password"
                className="bg-slate-900/50 border-slate-600 text-white placeholder:text-slate-500 focus:border-purple-500 focus:ring-purple-500"
              />
            </div>
            
            <Button
              type="submit"
              disabled={isLoading}
              className="w-full bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-500 hover:to-pink-500 text-white font-semibold py-2.5 shadow-lg shadow-purple-500/25"
            >
              {isLoading ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  Signing in...
                </>
              ) : (
                'Sign In'
              )}
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  );
};
