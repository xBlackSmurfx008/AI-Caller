import React, { useState, useEffect, useRef } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { NotificationsDropdown } from '../common/NotificationsDropdown';
import { useQuery } from '@tanstack/react-query';
import { notificationsAPI } from '../../api/notifications';

export const Header: React.FC = () => {
  const location = useLocation();
  const [notificationsOpen, setNotificationsOpen] = useState(false);
  const [providersMenuOpen, setProvidersMenuOpen] = useState(false);
  const providersMenuRef = useRef<HTMLDivElement>(null);

  const { data: unreadCount } = useQuery({
    queryKey: ['notifications', 'unread-count'],
    queryFn: () => notificationsAPI.getUnreadCount(),
    refetchInterval: 30000, // Refetch every 30 seconds
  });

  // Close providers menu when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (providersMenuRef.current && !providersMenuRef.current.contains(event.target as Node)) {
        setProvidersMenuOpen(false);
      }
    };

    if (providersMenuOpen) {
      document.addEventListener('mousedown', handleClickOutside);
    }

    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [providersMenuOpen]);

  const navItems = [
    { path: '/', label: 'Dashboard', icon: '📊' },
    { path: '/analytics', label: 'Analytics', icon: '📈' },
    { path: '/settings', label: 'Settings', icon: '⚙️' },
    { path: '/documentation', label: 'Documentation', icon: '📚' },
  ];

  return (
    <header 
      style={{
        position: 'sticky',
        top: 0,
        zIndex: 50,
        backgroundColor: 'var(--ai-color-bg-primary)',
        borderBottom: '0.5px solid var(--ai-color-border-heavy)',
        boxShadow: 'var(--ai-elevation-1-shadow)',
      }}
    >
      <div style={{ padding: 'var(--ai-spacing-8) var(--ai-spacing-12)' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--ai-spacing-16)' }}>
            <Link to="/" style={{ display: 'flex', alignItems: 'center', gap: 'var(--ai-spacing-6)', textDecoration: 'none' }}>
              <div 
                style={{
                  width: '32px',
                  height: '32px',
                  backgroundColor: 'var(--ai-color-brand-primary)',
                  borderRadius: 'var(--ai-radius-base)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  transition: 'background-color 0.15s ease',
                }}
                onMouseEnter={(e) => e.currentTarget.style.backgroundColor = 'var(--ai-color-brand-primary-hover)'}
                onMouseLeave={(e) => e.currentTarget.style.backgroundColor = 'var(--ai-color-brand-primary)'}
              >
                <svg style={{ width: '16px', height: '16px', color: 'var(--ai-color-brand-on-primary)' }} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 5a2 2 0 012-2h3.28a1 1 0 01.948.684l1.498 4.493a1 1 0 01-.502 1.21l-2.257 1.13a11.042 11.042 0 005.516 5.516l1.13-2.257a1 1 0 011.21-.502l4.493 1.498a1 1 0 01.684.949V19a2 2 0 01-2 2h-1C9.716 21 3 14.284 3 6V5z" />
                </svg>
              </div>
              <span style={{
                fontSize: 'var(--ai-font-size-body-emph)',
                fontWeight: 'var(--ai-font-weight-body-emph)',
                color: 'var(--ai-color-text-primary)',
              }}>
                AI Caller
              </span>
            </Link>
            
            <nav style={{ display: 'flex', gap: 'var(--ai-spacing-2)' }}>
              {navItems.map((item) => {
                const isActive = location.pathname === item.path;
                return (
                  <Link
                    key={item.path}
                    to={item.path}
                    style={{
                      padding: 'var(--ai-spacing-4) var(--ai-spacing-6)',
                      borderRadius: 'var(--ai-radius-md)',
                      fontSize: 'var(--ai-font-size-body-small)',
                      fontWeight: 'var(--ai-font-weight-medium)',
                      display: 'flex',
                      alignItems: 'center',
                      gap: 'var(--ai-spacing-4)',
                      textDecoration: 'none',
                      backgroundColor: isActive ? 'var(--ai-color-bg-tertiary)' : 'transparent',
                      color: isActive ? 'var(--ai-color-text-primary)' : 'var(--ai-color-text-secondary)',
                      transition: 'background-color 0.15s ease, color 0.15s ease',
                    }}
                    onMouseEnter={(e) => {
                      if (!isActive) {
                        e.currentTarget.style.backgroundColor = 'var(--ai-color-bg-tertiary)';
                        e.currentTarget.style.color = 'var(--ai-color-text-primary)';
                      }
                    }}
                    onMouseLeave={(e) => {
                      if (!isActive) {
                        e.currentTarget.style.backgroundColor = 'transparent';
                        e.currentTarget.style.color = 'var(--ai-color-text-secondary)';
                      }
                    }}
                  >
                    <span>{item.icon}</span>
                    <span>{item.label}</span>
                  </Link>
                );
              })}
            </nav>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--ai-spacing-6)', position: 'relative' }}>
            {/* Telephony Providers Dropdown */}
            <div ref={providersMenuRef} style={{ position: 'relative' }}>
              <button 
                type="button"
                style={{
                  padding: 'var(--ai-spacing-4) var(--ai-spacing-6)',
                  color: 'var(--ai-color-text-secondary)',
                  backgroundColor: 'transparent',
                  border: '0.5px solid var(--ai-color-border-heavy)',
                  borderRadius: 'var(--ai-radius-md)',
                  cursor: 'pointer',
                  fontSize: 'var(--ai-font-size-body-small)',
                  fontWeight: 'var(--ai-font-weight-medium)',
                  display: 'flex',
                  alignItems: 'center',
                  gap: 'var(--ai-spacing-4)',
                  transition: 'background-color 0.15s ease, color 0.15s ease',
                }}
                onClick={() => setProvidersMenuOpen(!providersMenuOpen)}
                onMouseEnter={(e) => {
                  e.currentTarget.style.backgroundColor = 'var(--ai-color-bg-tertiary)';
                  e.currentTarget.style.color = 'var(--ai-color-text-primary)';
                }}
                onMouseLeave={(e) => {
                  if (!providersMenuOpen) {
                    e.currentTarget.style.backgroundColor = 'transparent';
                    e.currentTarget.style.color = 'var(--ai-color-text-secondary)';
                  }
                }}
              >
                <span>📞</span>
                <span>Providers</span>
                <svg style={{ width: '16px', height: '16px' }} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                </svg>
              </button>
              {providersMenuOpen && (
                <div style={{
                  position: 'absolute',
                  top: '100%',
                  right: 0,
                  marginTop: 'var(--ai-spacing-4)',
                  backgroundColor: 'var(--ai-color-bg-primary)',
                  border: '0.5px solid var(--ai-color-border-heavy)',
                  borderRadius: 'var(--ai-radius-md)',
                  boxShadow: 'var(--ai-elevation-2-shadow)',
                  minWidth: '200px',
                  zIndex: 100,
                }}>
                  <Link
                    to="/twilio"
                    style={{
                      display: 'block',
                      padding: 'var(--ai-spacing-6) var(--ai-spacing-8)',
                      textDecoration: 'none',
                      color: 'var(--ai-color-text-primary)',
                      fontSize: 'var(--ai-font-size-body-small)',
                      borderBottom: '0.5px solid var(--ai-color-border-default)',
                    }}
                    onClick={() => setProvidersMenuOpen(false)}
                    onMouseEnter={(e) => {
                      e.currentTarget.style.backgroundColor = 'var(--ai-color-bg-tertiary)';
                    }}
                    onMouseLeave={(e) => {
                      e.currentTarget.style.backgroundColor = 'transparent';
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--ai-spacing-4)' }}>
                      <span>📱</span>
                      <div>
                        <div style={{ fontWeight: 'var(--ai-font-weight-medium)' }}>Twilio Dashboard</div>
                        <div style={{ fontSize: 'var(--ai-font-size-body-tiny)', color: 'var(--ai-color-text-secondary)' }}>
                          View Twilio stats
                        </div>
                      </div>
                    </div>
                  </Link>
                  <Link
                    to="/ringcentral"
                    style={{
                      display: 'block',
                      padding: 'var(--ai-spacing-6) var(--ai-spacing-8)',
                      textDecoration: 'none',
                      color: 'var(--ai-color-text-primary)',
                      fontSize: 'var(--ai-font-size-body-small)',
                    }}
                    onClick={() => setProvidersMenuOpen(false)}
                    onMouseEnter={(e) => {
                      e.currentTarget.style.backgroundColor = 'var(--ai-color-bg-tertiary)';
                    }}
                    onMouseLeave={(e) => {
                      e.currentTarget.style.backgroundColor = 'transparent';
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--ai-spacing-4)' }}>
                      <span>☎️</span>
                      <div>
                        <div style={{ fontWeight: 'var(--ai-font-weight-medium)' }}>RingCentral Dashboard</div>
                        <div style={{ fontSize: 'var(--ai-font-size-body-tiny)', color: 'var(--ai-color-text-secondary)' }}>
                          View RingCentral stats
                        </div>
                      </div>
                    </div>
                  </Link>
                </div>
              )}
            </div>

            {/* Notifications */}
            <div style={{ position: 'relative' }}>
              <button 
                type="button"
                style={{
                  position: 'relative',
                  padding: 'var(--ai-spacing-4)',
                  color: 'var(--ai-color-text-secondary)',
                  backgroundColor: 'transparent',
                  border: 'none',
                  borderRadius: 'var(--ai-radius-md)',
                  cursor: 'pointer',
                  transition: 'background-color 0.15s ease, color 0.15s ease',
                }}
                onClick={() => setNotificationsOpen(!notificationsOpen)}
                onMouseEnter={(e) => {
                  e.currentTarget.style.backgroundColor = 'var(--ai-color-bg-tertiary)';
                  e.currentTarget.style.color = 'var(--ai-color-text-primary)';
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.backgroundColor = 'transparent';
                  e.currentTarget.style.color = 'var(--ai-color-text-secondary)';
                }}
              >
                <svg style={{ width: '20px', height: '20px' }} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
                </svg>
                {(unreadCount || 0) > 0 && (
                  <span style={{
                    position: 'absolute',
                    top: '4px',
                    right: '4px',
                    minWidth: '18px',
                    height: '18px',
                    padding: '0 4px',
                    backgroundColor: 'var(--ai-color-brand-error)',
                    color: '#ffffff',
                    borderRadius: 'var(--ai-radius-full)',
                    fontSize: '10px',
                    fontWeight: 'var(--ai-font-weight-semibold)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                  }}>
                    {unreadCount! > 99 ? '99+' : unreadCount}
                  </span>
                )}
              </button>
              <NotificationsDropdown
                isOpen={notificationsOpen}
                onClose={() => setNotificationsOpen(false)}
              />
            </div>

          </div>
        </div>
      </div>

    </header>
  );
};
