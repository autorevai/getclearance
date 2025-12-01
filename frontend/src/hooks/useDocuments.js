/**
 * React Query hooks for Documents
 *
 * Provides data fetching, caching, and mutation hooks for document operations.
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useAuth } from '../auth';
import { DocumentsService, uploadToPresignedUrl } from '../services';
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
 * Hook to fetch a single document by ID
 * @param {string} id - Document ID
 * @param {Object} options - Additional React Query options
 */
export function useDocument(id, options = {}) {
  const { getToken } = useAuth();

  return useQuery({
    queryKey: documentKeys.detail(id),
    queryFn: async () => {
      const service = new DocumentsService(getToken);
      return service.get(id);
    },
    enabled: !!id,
    ...options,
  });
}

/**
 * Hook to fetch documents for an applicant
 * @param {string} applicantId - Applicant ID
 * @param {Object} options - Additional React Query options
 */
export function useApplicantDocuments(applicantId, options = {}) {
  const { getToken } = useAuth();

  return useQuery({
    queryKey: documentKeys.listByApplicant(applicantId),
    queryFn: async () => {
      const service = new DocumentsService(getToken);
      return service.listByApplicant(applicantId);
    },
    enabled: !!applicantId,
    ...options,
  });
}

/**
 * Hook to upload a document using presigned URL
 * Handles the full flow: get URL -> upload to R2 -> confirm
 * @returns Mutation with progress tracking
 */
export function useUploadDocument() {
  const { getToken } = useAuth();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ file, applicantId, documentType, onProgress }) => {
      const service = new DocumentsService(getToken);

      // Step 1: Get presigned upload URL
      const { upload_url, document_id } = await service.getUploadUrl(
        applicantId,
        documentType,
        file.name,
        file.type
      );

      // Step 2: Upload directly to R2
      await uploadToPresignedUrl(upload_url, file, onProgress);

      // Step 3: Confirm upload
      const document = await service.confirmUpload(document_id, file.size);

      return document;
    },
    onSuccess: (_, { applicantId }) => {
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
 * Hook for direct upload (small files < 10MB)
 * @returns Mutation object
 */
export function useDirectUpload() {
  const { getToken } = useAuth();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ file, applicantId, documentType }) => {
      const service = new DocumentsService(getToken);
      return service.directUpload(file, applicantId, documentType);
    },
    onSuccess: (_, { applicantId }) => {
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
 * Hook to delete a document
 * @returns Mutation object
 */
export function useDeleteDocument() {
  const { getToken } = useAuth();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ id, applicantId }) => {
      const service = new DocumentsService(getToken);
      return service.delete(id);
    },
    onSuccess: (_, { id, applicantId }) => {
      queryClient.invalidateQueries({ queryKey: documentKeys.detail(id) });
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
 * @returns Mutation object
 */
export function useAnalyzeDocument() {
  const { getToken } = useAuth();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ id }) => {
      const service = new DocumentsService(getToken);
      return service.analyze(id);
    },
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: documentKeys.detail(id) });
    },
  });
}

/**
 * Hook to get download URL for a document
 * @returns Mutation that returns the download URL
 */
export function useDocumentDownloadUrl() {
  const { getToken } = useAuth();

  return useMutation({
    mutationFn: async ({ id }) => {
      const service = new DocumentsService(getToken);
      const { download_url } = await service.getDownloadUrl(id);
      return download_url;
    },
  });
}

/**
 * Hook to download a document
 * Opens the document in a new tab or downloads it
 */
export function useDownloadDocument() {
  const { getToken } = useAuth();

  return useMutation({
    mutationFn: async ({ id, openInNewTab = true }) => {
      const service = new DocumentsService(getToken);
      const { download_url } = await service.getDownloadUrl(id);

      if (openInNewTab) {
        window.open(download_url, '_blank');
      } else {
        const a = document.createElement('a');
        a.href = download_url;
        a.download = '';
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
      }

      return download_url;
    },
  });
}
