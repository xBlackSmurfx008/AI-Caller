import React, { useState, useEffect } from 'react';
import { Link, useNavigate, useSearchParams } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { authService } from '../services/auth';
import { Input } from '../components/common/Input';
import { Button } from '../components/common/Button';
import { PageContainer } from '../components/layout/PageContainer';
import toast from 'react-hot-toast';

const resetPasswordSchema = z.object({
  password: z.string().min(8, 'Password must be at least 8 characters'),
  confirmPassword: z.string().min(8, 'Please confirm your password'),
}).refine((data) => data.password === data.confirmPassword, {
  message: "Passwords don't match",
  path: ['confirmPassword'],
});

type ResetPasswordFormData = z.infer<typeof resetPasswordSchema>;

export const ResetPassword: React.FC = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const [isLoading, setIsLoading] = useState(false);
  const [token, setToken] = useState<string | null>(null);
  const [isValidToken, setIsValidToken] = useState<boolean | null>(null);

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<ResetPasswordFormData>({
    resolver: zodResolver(resetPasswordSchema),
  });

  useEffect(() => {
    const tokenParam = searchParams.get('token');
    if (!tokenParam) {
      setIsValidToken(false);
      toast.error('Invalid reset link. Please request a new password reset.');
    } else {
      setToken(tokenParam);
      setIsValidToken(true);
    }
  }, [searchParams]);

  const onSubmit = async (data: ResetPasswordFormData) => {
    if (!token) {
      toast.error('Invalid reset token');
      return;
    }

    setIsLoading(true);
    try {
      await authService.resetPassword(token, data.password);
      toast.success('Password reset successfully! You can now login with your new password.');
      navigate('/login');
    } catch (error: any) {
      toast.error(error?.response?.data?.detail || 'Failed to reset password. The link may have expired.');
    } finally {
      setIsLoading(false);
    }
  };

  if (isValidToken === false) {
    return (
      <PageContainer>
        <div className="min-h-screen flex items-center justify-center bg-gray-50 px-4 sm:px-6 lg:px-8">
          <div className="max-w-md w-full">
            <div className="text-center mb-8">
              <div className="inline-flex items-center justify-center w-12 h-12 bg-red-100 rounded-full mb-4">
                <svg className="w-6 h-6 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </div>
              <h1 className="text-2xl font-semibold text-gray-800 mb-1">
                Invalid Reset Link
              </h1>
              <p className="text-sm text-gray-500">
                This password reset link is invalid or has expired
              </p>
            </div>

            <div className="chatkit-surface p-6 text-center">
              <p className="text-sm text-gray-600 mb-6">
                Please request a new password reset link.
              </p>
              <Link to="/forgot-password">
                <Button variant="primary" size="lg" className="w-full">
                  Request New Reset Link
                </Button>
              </Link>
              <Link to="/login" className="block mt-3">
                <Button variant="ghost" size="lg" className="w-full">
                  Back to Login
                </Button>
              </Link>
            </div>
          </div>
        </div>
      </PageContainer>
    );
  }

  return (
    <PageContainer>
      <div className="min-h-screen flex items-center justify-center bg-gray-50 px-4 sm:px-6 lg:px-8">
        <div className="max-w-md w-full">
          {/* Logo/Brand */}
          <div className="text-center mb-8">
            <div className="inline-flex items-center justify-center w-12 h-12 bg-primary-500 rounded-lg mb-4">
              <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 5a2 2 0 012-2h3.28a1 1 0 01.948.684l1.498 4.493a1 1 0 01-.502 1.21l-2.257 1.13a11.042 11.042 0 005.516 5.516l1.13-2.257a1 1 0 011.21-.502l4.493 1.498a1 1 0 01.684.949V19a2 2 0 01-2 2h-1C9.716 21 3 14.284 3 6V5z" />
              </svg>
            </div>
            <h1 className="text-2xl font-semibold text-gray-800 mb-1">
              Reset Password
            </h1>
            <p className="text-sm text-gray-500">
              Enter your new password below
            </p>
          </div>

          {/* Form Card */}
          <div className="chatkit-surface p-6">
            <form className="space-y-4" onSubmit={handleSubmit(onSubmit)}>
              <Input
                label="New Password"
                type="password"
                autoComplete="new-password"
                {...register('password')}
                error={errors.password?.message}
              />

              <Input
                label="Confirm New Password"
                type="password"
                autoComplete="new-password"
                {...register('confirmPassword')}
                error={errors.confirmPassword?.message}
              />

              <Button
                type="submit"
                variant="primary"
                size="lg"
                isLoading={isLoading}
                className="w-full"
              >
                {isLoading ? 'Resetting...' : 'Reset Password'}
              </Button>
            </form>

            <div className="mt-4 text-center">
              <Link to="/login" className="text-sm text-primary-600 hover:text-primary-700">
                Back to Login
              </Link>
            </div>
          </div>

          {/* Footer */}
          <p className="mt-6 text-center text-xs text-gray-400">
            Enterprise AI Call Center System
          </p>
        </div>
      </div>
    </PageContainer>
  );
};

