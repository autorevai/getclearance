/**
 * Biometrics Service
 *
 * Handles face comparison, liveness detection, and verification.
 */

import { getSharedClient } from './api';

const client = getSharedClient();

export const BiometricsService = {
  // Face comparison
  async compareFaces(sourceImage, targetImage, threshold = 90.0) {
    return client.post('/biometrics/compare', {
      source_image: sourceImage,
      target_image: targetImage,
      similarity_threshold: threshold,
    });
  },

  // Liveness detection
  async detectLiveness(image, sessionId = null) {
    return client.post('/biometrics/liveness', {
      image,
      session_id: sessionId,
    });
  },

  // Face detection
  async detectFaces(image) {
    return client.post('/biometrics/detect', { image });
  },

  // Full applicant verification (base64)
  async verifyApplicant(applicantId, selfieImage, checkLiveness = true) {
    const formData = new FormData();
    formData.append('selfie_image', selfieImage);
    formData.append('check_liveness', checkLiveness.toString());

    return client.post(`/biometrics/verify/${applicantId}`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },

  // Full applicant verification (file upload)
  async verifyApplicantWithFile(applicantId, selfieFile, checkLiveness = true) {
    const formData = new FormData();
    formData.append('selfie', selfieFile);
    formData.append('check_liveness', checkLiveness.toString());

    return client.post(`/biometrics/verify-upload/${applicantId}`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },

  // Service status
  async getStatus() {
    return client.get('/biometrics/status');
  },
};

export default BiometricsService;
