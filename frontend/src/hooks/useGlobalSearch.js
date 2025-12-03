/**
 * Global Search Hook
 *
 * Searches across applicants and cases with debounced queries.
 * Uses React Query for caching and automatic state management.
 */

import { useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useAuth } from '../auth';
import { ApiClient } from '../services/api';

// Query key factory
export const globalSearchKeys = {
  all: ['globalSearch'],
  query: (q) => [...globalSearchKeys.all, q],
};

/**
 * Service class for global search operations
 */
class GlobalSearchService {
  constructor(getToken) {
    this.client = new ApiClient(getToken);
  }

  /**
   * Search across applicants and cases
   * @param {string} query - Search query
   * @param {Object} options - Request options
   * @returns {Promise<{applicants: Array, cases: Array}>}
   */
  async search(query, options = {}) {
    // Search both endpoints in parallel
    const [applicantsResult, casesResult] = await Promise.allSettled([
      this.client.get(`/applicants?search=${encodeURIComponent(query)}&limit=5`, options),
      this.client.get(`/cases?search=${encodeURIComponent(query)}&limit=5`, options),
    ]);

    return {
      applicants: applicantsResult.status === 'fulfilled' ? (applicantsResult.value.items || []) : [],
      cases: casesResult.status === 'fulfilled' ? (casesResult.value.items || []) : [],
    };
  }
}

/**
 * Hook for global search functionality
 * @param {string} query - Search query (minimum 2 characters)
 * @param {Object} options - Additional React Query options
 * @returns {Object} Query result with applicants and cases
 */
export function useGlobalSearch(query, options = {}) {
  const { getToken } = useAuth();
  const service = useMemo(() => new GlobalSearchService(getToken), [getToken]);

  return useQuery({
    queryKey: globalSearchKeys.query(query),
    queryFn: ({ signal }) => service.search(query, { signal }),
    enabled: query?.length >= 2,
    staleTime: 30000, // Cache results for 30 seconds
    gcTime: 60000, // Keep in garbage collection for 1 minute
    retry: 1,
    ...options,
  });
}

export default useGlobalSearch;
