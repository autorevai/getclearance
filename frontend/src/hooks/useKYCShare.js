/**
 * Get Clearance - KYC Share Hooks
 * ================================
 * React Query hooks for Reusable KYC / Portable Identity feature.
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  generateShareToken,
  listShareTokens,
  revokeShareToken,
  verifyShareToken,
  getAccessHistory,
  getAvailablePermissions,
} from '../services/kycShare';

// Query keys
export const kycShareKeys = {
  all: ['kyc-share'],
  tokens: (applicantId) => [...kycShareKeys.all, 'tokens', applicantId],
  history: (applicantId) => [...kycShareKeys.all, 'history', applicantId],
  permissions: () => [...kycShareKeys.all, 'permissions'],
  verify: (token) => [...kycShareKeys.all, 'verify', token],
};

/**
 * Hook to list share tokens for an applicant.
 * @param {string} applicantId - Applicant UUID
 * @param {Object} options - Query options
 * @param {boolean} [options.includeExpired=false] - Include expired tokens
 * @param {boolean} [options.enabled=true] - Enable/disable query
 */
export function useShareTokens(applicantId, options = {}) {
  const { includeExpired = false, enabled = true, ...queryOptions } = options;

  return useQuery({
    queryKey: kycShareKeys.tokens(applicantId),
    queryFn: () => listShareTokens(applicantId, includeExpired),
    enabled: enabled && !!applicantId,
    staleTime: 30 * 1000, // 30 seconds
    ...queryOptions,
  });
}

/**
 * Hook to generate a new share token.
 * Returns the token ONCE - user must save it.
 */
export function useGenerateShareToken() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: generateShareToken,
    onSuccess: (data, variables) => {
      // Invalidate tokens list
      queryClient.invalidateQueries({
        queryKey: kycShareKeys.tokens(variables.applicant_id),
      });
    },
  });
}

/**
 * Hook to revoke a share token.
 */
export function useRevokeShareToken() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ tokenId, reason }) => revokeShareToken(tokenId, reason),
    onSuccess: () => {
      // Invalidate all token queries
      queryClient.invalidateQueries({
        queryKey: kycShareKeys.all,
      });
    },
  });
}

/**
 * Hook to verify a share token (for third-party use).
 * @param {string} token - The share token to verify
 * @param {Object} options - Query options
 */
export function useVerifyShareToken(token, options = {}) {
  const { enabled = true, ...queryOptions } = options;

  return useQuery({
    queryKey: kycShareKeys.verify(token),
    queryFn: () => verifyShareToken(token),
    enabled: enabled && !!token,
    staleTime: 0, // Always fetch fresh
    retry: false, // Don't retry on failure
    ...queryOptions,
  });
}

/**
 * Hook to verify a share token on demand (mutation style).
 */
export function useVerifyShareTokenMutation() {
  return useMutation({
    mutationFn: verifyShareToken,
  });
}

/**
 * Hook to get access history for an applicant.
 * @param {string} applicantId - Applicant UUID
 * @param {Object} options - Query options
 */
export function useAccessHistory(applicantId, options = {}) {
  const { limit = 50, enabled = true, ...queryOptions } = options;

  return useQuery({
    queryKey: kycShareKeys.history(applicantId),
    queryFn: () => getAccessHistory(applicantId, limit),
    enabled: enabled && !!applicantId,
    staleTime: 60 * 1000, // 1 minute
    ...queryOptions,
  });
}

/**
 * Hook to get available permissions.
 */
export function useAvailablePermissions(options = {}) {
  return useQuery({
    queryKey: kycShareKeys.permissions(),
    queryFn: getAvailablePermissions,
    staleTime: 24 * 60 * 60 * 1000, // 24 hours (rarely changes)
    ...options,
  });
}

const kycShareHooks = {
  kycShareKeys,
  useShareTokens,
  useGenerateShareToken,
  useRevokeShareToken,
  useVerifyShareToken,
  useVerifyShareTokenMutation,
  useAccessHistory,
  useAvailablePermissions,
};

export default kycShareHooks;
