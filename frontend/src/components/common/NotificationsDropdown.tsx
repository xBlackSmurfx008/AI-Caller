import React, { useState, useEffect, useRef } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { notificationsAPI } from '../../api/notifications';
import { useNavigate } from 'react-router-dom';
import { formatRelativeTime } from '../../utils/format';
import { LoadingSpinner } from './LoadingSpinner';
import { cn } from '../../utils/helpers';
import type { Notification, NotificationType } from '../../types/notification';

interface NotificationsDropdownProps {
  isOpen: boolean;
  onClose: () => void;
}

const getNotificationIcon = (type: NotificationType): string => {
  switch (type) {
    case 'call_escalated':
      return '📞';
    case 'qa_alert':
      return '⭐';
    case 'system_update':
      return '🔔';
    case 'agent_status':
      return '👤';
    case 'call_ended':
      return '📴';
    case 'compliance_alert':
      return '⚠️';
    default:
      return '🔔';
  }
};

const getNotificationColor = (type: NotificationType): string => {
  switch (type) {
    case 'call_escalated':
      return 'var(--ai-color-brand-error)';
    case 'qa_alert':
      return 'var(--ai-color-brand-warning)';
    case 'compliance_alert':
      return 'var(--ai-color-brand-error)';
    default:
      return 'var(--ai-color-brand-primary)';
  }
};

export const NotificationsDropdown: React.FC<NotificationsDropdownProps> = ({
  isOpen,
  onClose,
}) => {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const dropdownRef = useRef<HTMLDivElement>(null);

  const { data, isLoading } = useQuery({
    queryKey: ['notifications'],
    queryFn: () => notificationsAPI.list({ limit: 20 }),
    enabled: isOpen,
  });

  const { data: unreadCount } = useQuery({
    queryKey: ['notifications', 'unread-count'],
    queryFn: () => notificationsAPI.getUnreadCount(),
    refetchInterval: 30000, // Refetch every 30 seconds
  });

  const markAsReadMutation = useMutation({
    mutationFn: (id: string) => notificationsAPI.markAsRead(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['notifications'] });
      queryClient.invalidateQueries({ queryKey: ['notifications', 'unread-count'] });
    },
  });

  const markAllAsReadMutation = useMutation({
    mutationFn: () => notificationsAPI.markAllAsRead(),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['notifications'] });
      queryClient.invalidateQueries({ queryKey: ['notifications', 'unread-count'] });
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => notificationsAPI.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['notifications'] });
      queryClient.invalidateQueries({ queryKey: ['notifications', 'unread-count'] });
    },
  });

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        onClose();
      }
    };

    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside);
    }

    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [isOpen, onClose]);

  const handleNotificationClick = async (notification: Notification) => {
    if (!notification.read) {
      await markAsReadMutation.mutateAsync(notification.id);
    }

    if (notification.action_url) {
      navigate(notification.action_url);
      onClose();
    }
  };

  const handleMarkAllAsRead = async () => {
    await markAllAsReadMutation.mutateAsync();
  };

  const handleDelete = async (e: React.MouseEvent, notificationId: string) => {
    e.stopPropagation();
    await deleteMutation.mutateAsync(notificationId);
  };

  if (!isOpen) return null;

  const notifications = data?.notifications || [];
  const hasUnread = (unreadCount || 0) > 0;

  return (
    <div
      ref={dropdownRef}
      className="absolute right-0 top-full mt-2 w-96 z-50"
      style={{
        backgroundColor: 'var(--ai-color-bg-primary)',
        border: '0.5px solid var(--ai-color-border-heavy)',
        borderRadius: 'var(--ai-radius-lg)',
        boxShadow: 'var(--ai-elevation-3-shadow)',
        maxHeight: '500px',
        display: 'flex',
        flexDirection: 'column',
      }}
    >
      {/* Header */}
      <div
        style={{
          padding: 'var(--ai-spacing-6) var(--ai-spacing-8)',
          borderBottom: '0.5px solid var(--ai-color-border-heavy)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
        }}
      >
        <h3
          style={{
            fontSize: 'var(--ai-font-size-body-emph)',
            fontWeight: 'var(--ai-font-weight-semibold)',
            color: 'var(--ai-color-text-primary)',
            margin: 0,
          }}
        >
          Notifications
        </h3>
        {hasUnread && (
          <button
            onClick={handleMarkAllAsRead}
            disabled={markAllAsReadMutation.isPending}
            style={{
              fontSize: 'var(--ai-font-size-body-small)',
              color: 'var(--ai-color-brand-primary)',
              backgroundColor: 'transparent',
              border: 'none',
              cursor: 'pointer',
              padding: 'var(--ai-spacing-2) var(--ai-spacing-4)',
            }}
          >
            Mark all as read
          </button>
        )}
      </div>

      {/* Notifications List */}
      <div
        style={{
          flex: 1,
          overflowY: 'auto',
          maxHeight: '400px',
        }}
        className="chatkit-scrollbar"
      >
        {isLoading ? (
          <div className="flex items-center justify-center py-8">
            <LoadingSpinner />
          </div>
        ) : notifications.length === 0 ? (
          <div className="text-center py-8">
            <p
              style={{
                fontSize: 'var(--ai-font-size-body-small)',
                color: 'var(--ai-color-text-tertiary)',
              }}
            >
              No notifications
            </p>
          </div>
        ) : (
          <div>
            {notifications.map((notification) => (
              <div
                key={notification.id}
                onClick={() => handleNotificationClick(notification)}
                className={cn(
                  'px-4 py-3 border-b border-gray-100 cursor-pointer transition-colors',
                  !notification.read && 'bg-blue-50'
                )}
                style={{
                  borderBottom: '0.5px solid var(--ai-color-border-default)',
                }}
              >
                <div className="flex items-start gap-3">
                  <div
                    style={{
                      width: '32px',
                      height: '32px',
                      borderRadius: 'var(--ai-radius-full)',
                      backgroundColor: getNotificationColor(notification.type),
                      color: '#ffffff',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      flexShrink: 0,
                      fontSize: '16px',
                    }}
                  >
                    {getNotificationIcon(notification.type)}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-start justify-between gap-2">
                      <div className="flex-1">
                        <h4
                          style={{
                            fontSize: 'var(--ai-font-size-body-small)',
                            fontWeight: notification.read
                              ? 'var(--ai-font-weight-medium)'
                              : 'var(--ai-font-weight-semibold)',
                            color: 'var(--ai-color-text-primary)',
                            marginBottom: 'var(--ai-spacing-2)',
                          }}
                        >
                          {notification.title}
                        </h4>
                        <p
                          style={{
                            fontSize: 'var(--ai-font-size-body-small)',
                            color: 'var(--ai-color-text-secondary)',
                            marginBottom: 'var(--ai-spacing-2)',
                          }}
                        >
                          {notification.message}
                        </p>
                        <span
                          style={{
                            fontSize: 'var(--ai-font-size-caption)',
                            color: 'var(--ai-color-text-tertiary)',
                          }}
                        >
                          {formatRelativeTime(notification.created_at)}
                        </span>
                      </div>
                      <button
                        onClick={(e) => handleDelete(e, notification.id)}
                        disabled={deleteMutation.isPending}
                        style={{
                          padding: 'var(--ai-spacing-2)',
                          color: 'var(--ai-color-text-tertiary)',
                          backgroundColor: 'transparent',
                          border: 'none',
                          cursor: 'pointer',
                          borderRadius: 'var(--ai-radius-base)',
                          opacity: 0.6,
                        }}
                        onMouseEnter={(e) => {
                          e.currentTarget.style.opacity = '1';
                          e.currentTarget.style.color = 'var(--ai-color-brand-error)';
                        }}
                        onMouseLeave={(e) => {
                          e.currentTarget.style.opacity = '0.6';
                          e.currentTarget.style.color = 'var(--ai-color-text-tertiary)';
                        }}
                      >
                        ×
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

