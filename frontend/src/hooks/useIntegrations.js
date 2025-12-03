/**
 * React Query hooks for Integrations
 *
 * Hooks for API keys and webhooks management.
 */

import { useMemo } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useAuth } from '../auth';
import { IntegrationsService } from '../services';

// Query key factory
export const integrationsKeys = {
  all: ['integrations'],
  apiKeys: () => [...integrationsKeys.all, 'api-keys'],
  apiKeysList: () => [...integrationsKeys.apiKeys(), 'list'],
  permissions: () => [...integrationsKeys.apiKeys(), 'permissions'],
  webhooks: () => [...integrationsKeys.all, 'webhooks'],
  webhooksList: () => [...integrationsKeys.webhooks(), 'list'],
  webhook: (id) => [...integrationsKeys.webhooks(), 'detail', id],
  webhookLogs: (id) => [...integrationsKeys.webhooks(), 'logs', id],
  events: () => [...integrationsKeys.webhooks(), 'events'],
};

/**
 * Hook to get a memoized IntegrationsService instance
 */
function useIntegrationsService() {
  const { getToken } = useAuth();
  return useMemo(() => new IntegrationsService(getToken), [getToken]);
}

// API Keys Hooks
// ==============

/**
 * Hook to fetch list of API keys
 */
export function useApiKeys(options = {}) {
  const service = useIntegrationsService();

  return useQuery({
    queryKey: integrationsKeys.apiKeysList(),
    queryFn: ({ signal }) => service.listApiKeys({ signal }),
    staleTime: 30000,
    ...options,
  });
}

/**
 * Hook to fetch available permissions
 */
export function useAvailablePermissions(options = {}) {
  const service = useIntegrationsService();

  return useQuery({
    queryKey: integrationsKeys.permissions(),
    queryFn: ({ signal }) => service.getAvailablePermissions({ signal }),
    staleTime: 300000, // 5 minutes
    ...options,
  });
}

/**
 * Hook to create an API key
 */
export function useCreateApiKey() {
  const service = useIntegrationsService();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data) => service.createApiKey(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: integrationsKeys.apiKeysList() });
    },
  });
}

/**
 * Hook to revoke an API key
 */
export function useRevokeApiKey() {
  const service = useIntegrationsService();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (keyId) => service.revokeApiKey(keyId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: integrationsKeys.apiKeysList() });
    },
  });
}

/**
 * Hook to rotate an API key
 */
export function useRotateApiKey() {
  const service = useIntegrationsService();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (keyId) => service.rotateApiKey(keyId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: integrationsKeys.apiKeysList() });
    },
  });
}

// Webhook Hooks
// =============

/**
 * Hook to fetch list of webhooks
 */
export function useWebhooks(options = {}) {
  const service = useIntegrationsService();

  return useQuery({
    queryKey: integrationsKeys.webhooksList(),
    queryFn: ({ signal }) => service.listWebhooks({ signal }),
    staleTime: 30000,
    ...options,
  });
}

/**
 * Hook to fetch available webhook events
 */
export function useAvailableEvents(options = {}) {
  const service = useIntegrationsService();

  return useQuery({
    queryKey: integrationsKeys.events(),
    queryFn: ({ signal }) => service.getAvailableEvents({ signal }),
    staleTime: 300000, // 5 minutes
    ...options,
  });
}

/**
 * Hook to fetch webhook delivery logs
 */
export function useWebhookLogs(webhookId, options = {}) {
  const service = useIntegrationsService();

  return useQuery({
    queryKey: integrationsKeys.webhookLogs(webhookId),
    queryFn: ({ signal }) => service.getWebhookLogs(webhookId, {}, { signal }),
    enabled: !!webhookId,
    staleTime: 30000,
    ...options,
  });
}

/**
 * Hook to create a webhook
 */
export function useCreateWebhook() {
  const service = useIntegrationsService();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data) => service.createWebhook(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: integrationsKeys.webhooksList() });
    },
  });
}

/**
 * Hook to update a webhook
 */
export function useUpdateWebhook() {
  const service = useIntegrationsService();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ webhookId, data }) => service.updateWebhook(webhookId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: integrationsKeys.webhooksList() });
    },
  });
}

/**
 * Hook to delete a webhook
 */
export function useDeleteWebhook() {
  const service = useIntegrationsService();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (webhookId) => service.deleteWebhook(webhookId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: integrationsKeys.webhooksList() });
    },
  });
}

/**
 * Hook to test a webhook
 */
export function useTestWebhook() {
  const service = useIntegrationsService();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (webhookId) => service.testWebhook(webhookId),
    onSuccess: (_, webhookId) => {
      queryClient.invalidateQueries({ queryKey: integrationsKeys.webhookLogs(webhookId) });
      queryClient.invalidateQueries({ queryKey: integrationsKeys.webhooksList() });
    },
  });
}
