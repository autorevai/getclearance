/**
 * Error handling utilities
 *
 * Provides helpers for handling and displaying API errors.
 */

import { ApiError } from '../services/api';

/**
 * Extract a user-friendly error message from various error types
 * @param {Error|ApiError|unknown} error
 * @returns {string}
 */
export function getErrorMessage(error) {
  if (!error) {
    return 'An unknown error occurred';
  }

  // ApiError with detailed message
  if (error instanceof ApiError) {
    return error.message;
  }

  // Standard Error
  if (error instanceof Error) {
    return error.message;
  }

  // String error
  if (typeof error === 'string') {
    return error;
  }

  // Object with message property
  if (typeof error === 'object' && error.message) {
    return String(error.message);
  }

  // Object with detail property (FastAPI style)
  if (typeof error === 'object' && error.detail) {
    if (typeof error.detail === 'string') {
      return error.detail;
    }
    // Validation errors array
    if (Array.isArray(error.detail)) {
      return error.detail
        .map((e) => `${e.loc?.join('.') || 'Field'}: ${e.msg}`)
        .join(', ');
    }
  }

  return 'An unexpected error occurred';
}

/**
 * Get HTTP status code from error
 * @param {Error|ApiError|unknown} error
 * @returns {number|null}
 */
export function getErrorStatus(error) {
  if (error instanceof ApiError) {
    return error.status;
  }
  if (typeof error === 'object' && error.status) {
    return error.status;
  }
  return null;
}

/**
 * Check if error is a specific HTTP status
 * @param {Error|ApiError|unknown} error
 * @param {number} status
 * @returns {boolean}
 */
export function isHttpStatus(error, status) {
  return getErrorStatus(error) === status;
}

/**
 * Check if error is an authentication error (401)
 * @param {Error|ApiError|unknown} error
 * @returns {boolean}
 */
export function isAuthError(error) {
  return isHttpStatus(error, 401);
}

/**
 * Check if error is a permission error (403)
 * @param {Error|ApiError|unknown} error
 * @returns {boolean}
 */
export function isPermissionError(error) {
  return isHttpStatus(error, 403);
}

/**
 * Check if error is a not found error (404)
 * @param {Error|ApiError|unknown} error
 * @returns {boolean}
 */
export function isNotFoundError(error) {
  return isHttpStatus(error, 404);
}

/**
 * Check if error is a validation error (422)
 * @param {Error|ApiError|unknown} error
 * @returns {boolean}
 */
export function isValidationError(error) {
  return isHttpStatus(error, 422);
}

/**
 * Check if error is a server error (5xx)
 * @param {Error|ApiError|unknown} error
 * @returns {boolean}
 */
export function isServerError(error) {
  const status = getErrorStatus(error);
  return status !== null && status >= 500 && status < 600;
}

/**
 * Get appropriate error title based on status code
 * @param {Error|ApiError|unknown} error
 * @returns {string}
 */
export function getErrorTitle(error) {
  const status = getErrorStatus(error);

  switch (status) {
    case 401:
      return 'Authentication Required';
    case 403:
      return 'Permission Denied';
    case 404:
      return 'Not Found';
    case 422:
      return 'Validation Error';
    case 429:
      return 'Too Many Requests';
    case 500:
    case 502:
    case 503:
    case 504:
      return 'Server Error';
    default:
      return 'Error';
  }
}

/**
 * Log error with context for debugging
 * @param {Error|ApiError|unknown} error
 * @param {string} context - Where the error occurred
 * @param {Object} [additionalData] - Extra debug info
 */
export function logError(error, context, additionalData = {}) {
  console.error(`[${context}] Error:`, {
    message: getErrorMessage(error),
    status: getErrorStatus(error),
    error,
    ...additionalData,
  });
}
