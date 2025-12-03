/**
 * Biometrics Hooks
 *
 * React Query hooks for biometric verification operations.
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { BiometricsService } from '../services/biometrics';

export const biometricsKeys = {
  all: ['biometrics'],
  status: () => [...biometricsKeys.all, 'status'],
  verification: (applicantId) => [...biometricsKeys.all, 'verification', applicantId],
};

// Get biometrics service status
export function useBiometricsStatus() {
  return useQuery({
    queryKey: biometricsKeys.status(),
    queryFn: () => BiometricsService.getStatus(),
    staleTime: 1000 * 60 * 5, // 5 minutes
  });
}

// Compare faces
export function useCompareFaces() {
  return useMutation({
    mutationFn: ({ sourceImage, targetImage, threshold }) =>
      BiometricsService.compareFaces(sourceImage, targetImage, threshold),
  });
}

// Detect liveness
export function useDetectLiveness() {
  return useMutation({
    mutationFn: ({ image, sessionId }) =>
      BiometricsService.detectLiveness(image, sessionId),
  });
}

// Detect faces
export function useDetectFaces() {
  return useMutation({
    mutationFn: ({ image }) => BiometricsService.detectFaces(image),
  });
}

// Verify applicant (base64)
export function useVerifyApplicant() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ applicantId, selfieImage, checkLiveness }) =>
      BiometricsService.verifyApplicant(applicantId, selfieImage, checkLiveness),
    onSuccess: (_, { applicantId }) => {
      queryClient.invalidateQueries({
        queryKey: biometricsKeys.verification(applicantId)
      });
      // Also invalidate applicant data as biometrics update the document
      queryClient.invalidateQueries({ queryKey: ['applicants', 'detail', applicantId] });
    },
  });
}

// Verify applicant (file upload)
export function useVerifyApplicantWithFile() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ applicantId, selfieFile, checkLiveness }) =>
      BiometricsService.verifyApplicantWithFile(applicantId, selfieFile, checkLiveness),
    onSuccess: (_, { applicantId }) => {
      queryClient.invalidateQueries({
        queryKey: biometricsKeys.verification(applicantId)
      });
      queryClient.invalidateQueries({ queryKey: ['applicants', 'detail', applicantId] });
    },
  });
}
