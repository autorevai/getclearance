/**
 * React Query hooks for Documents
 *
 * Production-grade hooks with:
 * - Upload progress tracking with stage awareness
 * - Optimistic updates for deletions
 * - Proper abort handling
 * - Polling for processing status
 */

import { useMemo, useRef, useCallback, useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useAuth } from '../auth';
import { DocumentsService, uploadDocumentFlow } from '../services';
import { applicantKeys } from './useApplicants';

// Query key factory
export const documentKeys = {
  all: ['documents'],
  lists: () => [...documentKeys.all, 'list'],
  listByApplicant: (applicantId) => [...documentKeys.lists(), { applicantId }],
  details: () => [...documentKeys.all, 'detail'],
  detail: (id) => [...documentKeys.details(), id],
};

/**
 * Hook to get a memoized DocumentsService instance
 */
function useDocumentsService() {
  const { getToken } = useAuth();
  return useMemo(() => new DocumentsService(getToken), [getToken]);
}

/**
 * Hook to fetch a single document by ID
 * @param {string} id - Document ID
 * @param {Object} options - Additional React Query options
 */
export function useDocument(id, options = {}) {
  const service = useDocumentsService();

  return useQuery({
    queryKey: documentKeys.detail(id),
    queryFn: ({ signal }) => service.get(id, { signal }),
    enabled: !!id,
    staleTime: 30000,
    ...options,
  });
}

/**
 * Hook to fetch documents for an applicant
 * @param {string} applicantId - Applicant ID
 * @param {Object} options - Additional React Query options
 */
export function useApplicantDocuments(applicantId, options = {}) {
  const service = useDocumentsService();

  return useQuery({
    queryKey: documentKeys.listByApplicant(applicantId),
    queryFn: ({ signal }) => service.listByApplicant(applicantId, {}, { signal }),
    enabled: !!applicantId,
    staleTime: 30000,
    ...options,
  });
}

/**
 * Hook to poll a document until processing is complete
 * @param {string} id - Document ID
 * @param {Object} options - Additional options
 */
export function useDocumentPolling(id, options = {}) {
  const service = useDocumentsService();
  const { enabled = true, onComplete } = options;

  return useQuery({
    queryKey: [...documentKeys.detail(id), 'polling'],
    queryFn: ({ signal }) => service.get(id, { signal }),
    enabled: !!id && enabled,
    refetchInterval: (query) => {
      const doc = query.state.data;
      if (!doc) return 2000;

      // Stop polling when processing is done
      if (doc.status === 'verified' || doc.status === 'failed' || doc.status === 'rejected') {
        if (onComplete) onComplete(doc);
        return false;
      }

      // Poll every 2 seconds while processing
      return 2000;
    },
    staleTime: 0,
  });
}

/**
 * Hook to upload a document with full progress tracking
 * Provides progress percentage, current stage, and abort capability
 */
export function useUploadDocument() {
  const service = useDocumentsService();
  const queryClient = useQueryClient();
  const abortControllerRef = useRef(null);

  // Track upload state
  const [uploadState, setUploadState] = useState({
    progress: 0,
    stage: null, // 'preparing' | 'uploading' | 'confirming' | 'analyzing'
  });

  const mutation = useMutation({
    mutationFn: async ({ file, applicantId, documentType, analyze = false }) => {
      // Create abort controller for this upload
      abortControllerRef.current = new AbortController();

      const document = await uploadDocumentFlow(
        service,
        { file, applicantId, documentType },
        {
          onProgress: (progress) => setUploadState(s => ({ ...s, progress })),
          onStage: (stage) => setUploadState(s => ({ ...s, stage })),
          signal: abortControllerRef.current.signal,
          analyze,
        }
      );

      return document;
    },
    onSuccess: (document, { applicantId }) => {
      // Reset upload state
      setUploadState({ progress: 0, stage: null });

      // Add document to cache
      queryClient.setQueryData(documentKeys.detail(document.id), document);

      // Invalidate related queries
      queryClient.invalidateQueries({
        queryKey: documentKeys.listByApplicant(applicantId),
      });
      queryClient.invalidateQueries({
        queryKey: applicantKeys.detail(applicantId),
      });
    },
    onError: () => {
      setUploadState({ progress: 0, stage: null });
    },
  });

  // Abort function
  const abort = useCallback(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
    }
  }, []);

  return {
    ...mutation,
    progress: uploadState.progress,
    stage: uploadState.stage,
    abort,
  };
}

/**
 * Hook for direct upload (small files < 10MB)
 * Simpler than presigned URL flow
 */
export function useDirectUpload() {
  const service = useDocumentsService();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ file, applicantId, documentType }) => {
      return service.directUpload(file, applicantId, documentType);
    },
    onSuccess: (document, { applicantId }) => {
      queryClient.setQueryData(documentKeys.detail(document.id), document);
      queryClient.invalidateQueries({
        queryKey: documentKeys.listByApplicant(applicantId),
      });
      queryClient.invalidateQueries({
        queryKey: applicantKeys.detail(applicantId),
      });
    },
  });
}

/**
 * Hook to delete a document with optimistic update
 */
export function useDeleteDocument() {
  const service = useDocumentsService();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ id }) => {
      return service.delete(id);
    },

    // Optimistic update - remove from list immediately
    onMutate: async ({ id, applicantId }) => {
      if (!applicantId) return {};

      await queryClient.cancelQueries({
        queryKey: documentKeys.listByApplicant(applicantId),
      });

      const previousDocs = queryClient.getQueryData(
        documentKeys.listByApplicant(applicantId)
      );

      // Optimistically remove the document
      if (previousDocs) {
        queryClient.setQueryData(
          documentKeys.listByApplicant(applicantId),
          previousDocs.filter(doc => doc.id !== id)
        );
      }

      return { previousDocs, applicantId };
    },

    onError: (err, { id, applicantId }, context) => {
      // Rollback on error
      if (context?.previousDocs && context?.applicantId) {
        queryClient.setQueryData(
          documentKeys.listByApplicant(context.applicantId),
          context.previousDocs
        );
      }
    },

    onSettled: (_, __, { id, applicantId }) => {
      queryClient.removeQueries({ queryKey: documentKeys.detail(id) });
      if (applicantId) {
        queryClient.invalidateQueries({
          queryKey: documentKeys.listByApplicant(applicantId),
        });
        queryClient.invalidateQueries({
          queryKey: applicantKeys.detail(applicantId),
        });
      }
    },
  });
}

/**
 * Hook to trigger document analysis
 */
export function useAnalyzeDocument() {
  const service = useDocumentsService();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ id }) => {
      return service.analyze(id);
    },

    // Optimistic update - set status to processing
    onMutate: async ({ id }) => {
      await queryClient.cancelQueries({ queryKey: documentKeys.detail(id) });

      const previousDoc = queryClient.getQueryData(documentKeys.detail(id));

      if (previousDoc) {
        queryClient.setQueryData(documentKeys.detail(id), {
          ...previousDoc,
          status: 'processing',
          analysis_started_at: new Date().toISOString(),
        });
      }

      return { previousDoc };
    },

    onError: (err, { id }, context) => {
      if (context?.previousDoc) {
        queryClient.setQueryData(documentKeys.detail(id), context.previousDoc);
      }
    },

    onSettled: (_, __, { id }) => {
      queryClient.invalidateQueries({ queryKey: documentKeys.detail(id) });
    },
  });
}

/**
 * Hook to get download URL for a document
 */
export function useDocumentDownloadUrl() {
  const service = useDocumentsService();

  return useMutation({
    mutationFn: async ({ id }) => {
      const { download_url } = await service.getDownloadUrl(id);
      return download_url;
    },
  });
}

/**
 * Hook to download a document
 * Opens the document in a new tab or triggers download
 */
export function useDownloadDocument() {
  const service = useDocumentsService();

  return useMutation({
    mutationFn: async ({ id, openInNewTab = true, filename }) => {
      const { download_url } = await service.getDownloadUrl(id);

      if (openInNewTab) {
        window.open(download_url, '_blank', 'noopener,noreferrer');
      } else {
        // Trigger download
        const a = document.createElement('a');
        a.href = download_url;
        a.download = filename || '';
        a.style.display = 'none';
        document.body.appendChild(a);
        a.click();
        setTimeout(() => document.body.removeChild(a), 100);
      }

      return download_url;
    },
  });
}

/**
 * Hook to batch upload multiple documents
 * Tracks individual and overall progress
 */
export function useBatchUpload() {
  const service = useDocumentsService();
  const queryClient = useQueryClient();

  const [batchState, setBatchState] = useState({
    total: 0,
    completed: 0,
    failed: 0,
    currentFile: null,
    currentProgress: 0,
  });

  const mutation = useMutation({
    mutationFn: async ({ files, applicantId, documentType }) => {
      const results = [];

      setBatchState({
        total: files.length,
        completed: 0,
        failed: 0,
        currentFile: null,
        currentProgress: 0,
      });

      for (const file of files) {
        setBatchState(s => ({ ...s, currentFile: file.name, currentProgress: 0 }));

        try {
          const document = await uploadDocumentFlow(
            service,
            { file, applicantId, documentType },
            {
              onProgress: (progress) =>
                setBatchState(s => ({ ...s, currentProgress: progress })),
            }
          );
          results.push({ success: true, document, file });
          setBatchState(s => ({ ...s, completed: s.completed + 1 }));
        } catch (error) {
          results.push({ success: false, error, file });
          setBatchState(s => ({ ...s, failed: s.failed + 1 }));
        }
      }

      return results;
    },
    onSettled: (_, __, { applicantId }) => {
      setBatchState({ total: 0, completed: 0, failed: 0, currentFile: null, currentProgress: 0 });
      queryClient.invalidateQueries({
        queryKey: documentKeys.listByApplicant(applicantId),
      });
      queryClient.invalidateQueries({
        queryKey: applicantKeys.detail(applicantId),
      });
    },
  });

  return {
    ...mutation,
    batchState,
    overallProgress: batchState.total
      ? Math.round(((batchState.completed + batchState.failed) / batchState.total) * 100)
      : 0,
  };
}
