/**
 * Get Clearance - KYC Share Service
 * ==================================
 * API service for Reusable KYC / Portable Identity feature.
 */

import api from './api';

/**
 * Generate a new KYC share token for an applicant.
 * @param {Object} data - Token creation data
 * @param {string} data.applicant_id - UUID of the applicant
 * @param {string} data.shared_with - Name of company receiving data
 * @param {string} [data.shared_with_email] - Contact email
 * @param {string} [data.purpose] - Purpose for sharing
 * @param {Object} data.permissions - Permissions to grant
 * @param {number} [data.expires_days=30] - Days until expiry (max 90)
 * @param {number} [data.max_uses=1] - Max uses (max 10)
 * @returns {Promise<Object>} Token response with token shown once
 */
export async function generateShareToken(data) {
  const response = await api.post('/kyc-share/token', data);
  return response.data;
}

/**
 * List all share tokens for an applicant.
 * @param {string} applicantId - Applicant UUID
 * @param {boolean} [includeExpired=false] - Include expired tokens
 * @returns {Promise<Object>} List of tokens
 */
export async function listShareTokens(applicantId, includeExpired = false) {
  const params = new URLSearchParams();
  if (includeExpired) {
    params.append('include_expired', 'true');
  }
  const query = params.toString() ? `?${params.toString()}` : '';
  const response = await api.get(`/kyc-share/tokens/${applicantId}${query}`);
  return response.data;
}

/**
 * Revoke a share token.
 * @param {string} tokenId - Token UUID to revoke
 * @param {string} [reason] - Optional reason for revocation
 * @returns {Promise<void>}
 */
export async function revokeShareToken(tokenId, reason = null) {
  await api.post(`/kyc-share/revoke/${tokenId}`, reason ? { reason } : {});
}

/**
 * Verify a share token and get the shared KYC data.
 * This is typically called by a third party, not the token creator.
 * @param {string} token - The share token
 * @returns {Promise<Object>} Shared KYC data
 */
export async function verifyShareToken(token) {
  const response = await api.post('/kyc-share/verify', { token });
  return response.data;
}

/**
 * Get access history for an applicant's shared tokens.
 * @param {string} applicantId - Applicant UUID
 * @param {number} [limit=50] - Maximum records to return
 * @returns {Promise<Object>} Access history
 */
export async function getAccessHistory(applicantId, limit = 50) {
  const response = await api.get(`/kyc-share/history/${applicantId}?limit=${limit}`);
  return response.data;
}

/**
 * Get available permissions for KYC sharing.
 * @returns {Promise<Object>} Available permissions
 */
export async function getAvailablePermissions() {
  const response = await api.get('/kyc-share/permissions');
  return response.data;
}

// Permission keys for reference
export const PERMISSION_KEYS = {
  BASIC_INFO: 'basic_info',
  ID_VERIFICATION: 'id_verification',
  ADDRESS: 'address',
  SCREENING: 'screening',
  DOCUMENTS: 'documents',
  FULL: 'full',
};

// Default permission descriptions
export const PERMISSION_DESCRIPTIONS = {
  basic_info: 'Name and date of birth',
  id_verification: 'ID type, number, and verification status',
  address: 'Verified address',
  screening: 'AML/sanctions screening result',
  documents: 'Access to verified documents',
  full: 'All verification data',
};

const kycShareService = {
  generateShareToken,
  listShareTokens,
  revokeShareToken,
  verifyShareToken,
  getAccessHistory,
  getAvailablePermissions,
  PERMISSION_KEYS,
  PERMISSION_DESCRIPTIONS,
};

export default kycShareService;
