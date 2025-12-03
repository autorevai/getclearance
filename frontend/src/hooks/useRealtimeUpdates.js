/**
 * useRealtimeUpdates - WebSocket hook for real-time data updates
 *
 * Listens to WebSocket events from the backend and automatically
 * invalidates React Query caches when relevant data changes.
 *
 * Event types:
 * - applicant.created / applicant.updated / applicant.reviewed
 * - screening.completed
 * - document.processed
 * - case.created / case.resolved
 */

import { useEffect, useRef, useCallback, useState } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { useAuth } from '../auth';
import { useToast } from '../contexts/ToastContext';

// Query key imports for invalidation
import { applicantKeys } from './useApplicants';
import { caseKeys } from './useCases';

// Build WebSocket URL from environment
const getWebSocketUrl = () => {
  const wsUrl = process.env.REACT_APP_WS_URL;
  if (wsUrl) return wsUrl;

  // Fallback: derive from API URL
  const apiUrl = process.env.REACT_APP_API_BASE_URL || '';
  return apiUrl.replace(/^http/, 'ws').replace('/api/v1', '/ws');
};

/**
 * Hook for real-time updates via WebSocket
 *
 * @param {Object} options
 * @param {boolean} options.enabled - Whether to connect (default: true)
 * @param {boolean} options.showNotifications - Show toast on events (default: true)
 * @param {Function} options.onEvent - Custom event handler
 */
export function useRealtimeUpdates(options = {}) {
  const {
    enabled = true,
    showNotifications = true,
    onEvent,
  } = options;

  const queryClient = useQueryClient();
  const { getToken, isAuthenticated } = useAuth();
  const toast = useToast();

  const wsRef = useRef(null);
  const reconnectTimeoutRef = useRef(null);
  const reconnectAttemptsRef = useRef(0);
  const [connectionState, setConnectionState] = useState('disconnected');

  const MAX_RECONNECT_ATTEMPTS = 5;
  const RECONNECT_DELAY_BASE = 1000;

  // Handle incoming WebSocket messages
  const handleMessage = useCallback(
    (event) => {
      try {
        const data = JSON.parse(event.data);

        // Call custom event handler if provided
        if (onEvent) {
          onEvent(data);
        }

        // Invalidate relevant queries based on event type
        switch (data.type) {
          case 'applicant.created':
            queryClient.invalidateQueries({ queryKey: applicantKeys.lists() });
            if (showNotifications) {
              toast.info('New applicant created');
            }
            break;

          case 'applicant.updated':
            if (data.applicant_id) {
              queryClient.invalidateQueries({
                queryKey: applicantKeys.detail(data.applicant_id),
              });
            }
            queryClient.invalidateQueries({ queryKey: applicantKeys.lists() });
            break;

          case 'applicant.reviewed':
            if (data.applicant_id) {
              queryClient.invalidateQueries({
                queryKey: applicantKeys.detail(data.applicant_id),
              });
            }
            queryClient.invalidateQueries({ queryKey: applicantKeys.lists() });
            if (showNotifications && data.decision) {
              const status = data.decision === 'approved' ? 'approved' : 'rejected';
              toast.info(`Applicant ${status}`);
            }
            break;

          case 'screening.completed':
            queryClient.invalidateQueries({ queryKey: ['screeningChecks'] });
            if (data.applicant_id) {
              queryClient.invalidateQueries({
                queryKey: applicantKeys.detail(data.applicant_id),
              });
            }
            if (showNotifications) {
              if (data.hit_count > 0) {
                toast.warning(`Screening complete: ${data.hit_count} hit(s) found`);
              } else {
                toast.success('Screening complete: No matches');
              }
            }
            break;

          case 'document.processed':
            if (data.applicant_id) {
              queryClient.invalidateQueries({
                queryKey: applicantKeys.detail(data.applicant_id),
              });
            }
            queryClient.invalidateQueries({ queryKey: ['documents'] });
            if (showNotifications) {
              toast.info('Document processed');
            }
            break;

          case 'case.created':
            queryClient.invalidateQueries({ queryKey: caseKeys.lists() });
            if (showNotifications) {
              toast.info('New case created');
            }
            break;

          case 'case.resolved':
            if (data.case_id) {
              queryClient.invalidateQueries({
                queryKey: caseKeys.detail(data.case_id),
              });
            }
            queryClient.invalidateQueries({ queryKey: caseKeys.lists() });
            if (showNotifications) {
              toast.success('Case resolved');
            }
            break;

          case 'ping':
            // Heartbeat message - no action needed
            break;

          default:
            console.debug('Unhandled WebSocket event:', data.type);
        }
      } catch (err) {
        console.error('Failed to parse WebSocket message:', err);
      }
    },
    [queryClient, toast, showNotifications, onEvent]
  );

  // Use ref for scheduleReconnect to avoid circular dependency
  const scheduleReconnectRef = useRef(null);

  // Schedule reconnection with exponential backoff
  const scheduleReconnect = useCallback(() => {
    if (reconnectAttemptsRef.current >= MAX_RECONNECT_ATTEMPTS) {
      console.warn('Max WebSocket reconnection attempts reached');
      return;
    }

    const delay = RECONNECT_DELAY_BASE * Math.pow(2, reconnectAttemptsRef.current);
    reconnectAttemptsRef.current++;

    console.debug(`Scheduling WebSocket reconnection in ${delay}ms`);

    reconnectTimeoutRef.current = setTimeout(() => {
      // Call connect through connectRef to avoid stale closure
      if (connectRef.current) {
        connectRef.current();
      }
    }, delay);
  }, []);

  // Store scheduleReconnect in ref for use in connect
  scheduleReconnectRef.current = scheduleReconnect;

  // Use ref for connect to avoid circular dependency with scheduleReconnect
  const connectRef = useRef(null);

  // Connect to WebSocket
  const connect = useCallback(async () => {
    if (!enabled || !isAuthenticated) {
      return;
    }

    // Don't reconnect if already connected or connecting
    if (wsRef.current?.readyState === WebSocket.OPEN ||
        wsRef.current?.readyState === WebSocket.CONNECTING) {
      return;
    }

    setConnectionState('connecting');

    try {
      const token = await getToken();
      const wsUrl = getWebSocketUrl();

      // Append token as query parameter
      const url = new URL(wsUrl);
      url.searchParams.set('token', token);

      const ws = new WebSocket(url.toString());
      wsRef.current = ws;

      ws.onopen = () => {
        console.debug('WebSocket connected');
        setConnectionState('connected');
        reconnectAttemptsRef.current = 0;
      };

      ws.onmessage = handleMessage;

      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        setConnectionState('error');
      };

      ws.onclose = (event) => {
        console.debug('WebSocket closed:', event.code, event.reason);
        setConnectionState('disconnected');
        wsRef.current = null;

        // Attempt reconnection if not intentionally closed
        if (event.code !== 1000 && enabled) {
          if (scheduleReconnectRef.current) {
            scheduleReconnectRef.current();
          }
        }
      };
    } catch (err) {
      console.error('Failed to connect WebSocket:', err);
      setConnectionState('error');
      if (scheduleReconnectRef.current) {
        scheduleReconnectRef.current();
      }
    }
  }, [enabled, isAuthenticated, getToken, handleMessage]);

  // Store connect in ref for use in scheduleReconnect
  connectRef.current = connect;

  // Disconnect WebSocket
  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }

    if (wsRef.current) {
      wsRef.current.close(1000, 'Client disconnect');
      wsRef.current = null;
    }

    setConnectionState('disconnected');
  }, []);

  // Connect on mount, disconnect on unmount
  useEffect(() => {
    if (enabled && isAuthenticated) {
      connect();
    }

    return () => {
      disconnect();
    };
  }, [enabled, isAuthenticated, connect, disconnect]);

  // Manual reconnect function
  const reconnect = useCallback(() => {
    disconnect();
    reconnectAttemptsRef.current = 0;
    connect();
  }, [disconnect, connect]);

  return {
    connectionState,
    isConnected: connectionState === 'connected',
    reconnect,
    disconnect,
  };
}

/**
 * Hook to use at the app level to enable global real-time updates
 */
export function useGlobalRealtimeUpdates() {
  return useRealtimeUpdates({
    enabled: true,
    showNotifications: true,
  });
}

export default useRealtimeUpdates;
