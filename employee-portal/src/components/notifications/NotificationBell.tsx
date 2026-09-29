import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { formatDistanceToNow, parseISO } from 'date-fns';
import { AlertCircle, Bell, CheckCheck, RefreshCcw } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton';
import { cn } from '@/lib/utils';
import { useNotifications } from '@/hooks/useNotifications';
import type { Notification } from '@/types/notification.types';
import { purchaseRequestNavigationTarget } from './notificationNavigation';

/**
 * The notification bell + dropdown panel (Slice 3), matching the hand-rolled
 * dropdown pattern the user menu right next to it already uses in
 * Header.tsx (local state + a full-screen click-catcher to close on outside
 * click) rather than adding a new Radix dependency for this one panel.
 */
export function NotificationBell() {
  const navigate = useNavigate();
  const [isOpen, setIsOpen] = useState(false);
  const {
    unreadCount,
    notifications,
    isLoading,
    error,
    loadNotifications,
    markAsRead,
    markAllAsRead,
  } = useNotifications();

  const handleToggle = () => {
    const opening = !isOpen;
    setIsOpen(opening);
    if (opening) {
      loadNotifications();
    }
  };

  const handleSelect = (notification: Notification) => {
    markAsRead(notification.id);
    const target = purchaseRequestNavigationTarget(notification);
    setIsOpen(false);
    if (target) {
      navigate(target);
    }
  };

  return (
    <div className="relative">
      <Button
        type="button"
        variant="ghost"
        size="icon"
        className="relative text-white hover:bg-white/20"
        onClick={handleToggle}
        aria-label="Notifications"
      >
        <Bell className="h-5 w-5" />
        {unreadCount > 0 && (
          <span className="absolute top-1 right-1 flex h-4 min-w-4 items-center justify-center rounded-full bg-red-500 px-1 text-[10px] font-semibold leading-none text-white ring-2 ring-blue-700">
            {unreadCount > 9 ? '9+' : unreadCount}
          </span>
        )}
      </Button>

      {isOpen && (
        <>
          <div className="fixed inset-0 z-10" onClick={() => setIsOpen(false)} />
          <div className="absolute right-0 top-full mt-2 w-80 max-w-[90vw] rounded-xl bg-white border border-slate-200 shadow-xl z-20 overflow-hidden">
            <div className="flex items-center justify-between px-4 py-3 border-b border-slate-100">
              <p className="font-semibold text-slate-900 text-sm">Notifications</p>
              {unreadCount > 0 && (
                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  className="h-7 text-xs text-blue-700 hover:text-blue-800 hover:bg-blue-50"
                  onClick={() => markAllAsRead()}
                >
                  <CheckCheck className="h-3.5 w-3.5 mr-1" />
                  Mark all read
                </Button>
              )}
            </div>

            <div className="max-h-96 overflow-y-auto">
              {isLoading ? (
                <div className="p-4 space-y-3">
                  <Skeleton className="h-12 w-full" />
                  <Skeleton className="h-12 w-full" />
                  <Skeleton className="h-12 w-full" />
                </div>
              ) : error ? (
                <div className="p-6 text-center space-y-3">
                  <AlertCircle className="h-8 w-8 mx-auto text-destructive" />
                  <p className="text-sm text-muted-foreground">{error}</p>
                  <Button
                    type="button"
                    variant="outline"
                    size="sm"
                    onClick={() => loadNotifications()}
                  >
                    <RefreshCcw className="h-3.5 w-3.5 mr-2" />
                    Retry
                  </Button>
                </div>
              ) : notifications.length === 0 ? (
                <div className="p-6 text-center text-sm text-muted-foreground">
                  <Bell className="h-8 w-8 mx-auto mb-2 opacity-40" />
                  No notifications yet
                </div>
              ) : (
                <ul>
                  {notifications.map((notification) => {
                    const isLinkable = purchaseRequestNavigationTarget(notification) !== null;
                    return (
                      <li key={notification.id}>
                        <button
                          type="button"
                          onClick={() => handleSelect(notification)}
                          className={cn(
                            'w-full text-left px-4 py-3 border-b border-slate-50 last:border-b-0 hover:bg-slate-50 transition-colors',
                            !notification.is_read && 'bg-blue-50/60',
                            !isLinkable && 'cursor-default'
                          )}
                        >
                          <div className="flex items-start gap-2">
                            {!notification.is_read && (
                              <span className="mt-1.5 h-2 w-2 rounded-full bg-blue-600 flex-shrink-0" />
                            )}
                            <div className={cn('flex-1 min-w-0', notification.is_read && 'pl-4')}>
                              <p
                                className={cn(
                                  'text-sm text-slate-900',
                                  !notification.is_read && 'font-semibold'
                                )}
                              >
                                {notification.title}
                              </p>
                              <p className="text-xs text-slate-600 mt-0.5 line-clamp-2">
                                {notification.message}
                              </p>
                              <p className="text-xs text-slate-400 mt-1">
                                {formatDistanceToNow(parseISO(notification.created_at), {
                                  addSuffix: true,
                                })}
                              </p>
                            </div>
                          </div>
                        </button>
                      </li>
                    );
                  })}
                </ul>
              )}
            </div>
          </div>
        </>
      )}
    </div>
  );
}

export default NotificationBell;
