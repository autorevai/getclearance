/**
 * Base API client for GetClearance backend
 *
 * Production-grade API client with:
 * - Authentication headers
 * - Request/response interceptors
 * - Timeout and abort handling
 * - Retry logic with exponential backoff
 * - Offline detection
 * - Request deduplication
 * - Comprehensive error handling
 */

const API_BASE = process.env.REACT_APP_API_BASE_URL || 'http://localhost:8000/api/v1';
const DEFAULT_TIMEOUT = 30000; // 30 seconds
const MAX_RETRIES = 3;
const RETRY_DELAY_BASE = 1000; // 1 second

/**
 * Custom error class for API errors with rich context
 */
export class ApiError extends Error {
  constructor(message, status, data = null, requestId = null) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.data = data;
    this.requestId = requestId;
    this.timestamp = new Date().toISOString();
    this.isNetworkError = status === 0;
    this.isServerError = status >= 500;
    this.isClientError = status >= 400 && status < 500;
    this.isRetryable = this.isNetworkError || this.isServerError;
  }

  toJSON() {
    return {
      name: this.name,
      message: this.message,
      status: this.status,
      data: this.data,
      requestId: this.requestId,
      timestamp: this.timestamp,
    };
  }
}

/**
 * Check if browser is online
 */
export function isOnline() {
  return typeof navigator !== 'undefined' ? navigator.onLine : true;
}

/**
 * Sleep helper for retry delays
 */
function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

/**
 * In-flight request cache for deduplication
 */
const inflightRequests = new Map();

/**
 * Generate cache key for request deduplication
 */
function getRequestKey(url, options) {
  const method = options.method || 'GET';
  // Only dedupe GET requests
  if (method !== 'GET') return null;
  return `${method}:${url}`;
}

/**
 * Base API client with authentication support
 */
export class ApiClient {
  /**
   * @param {Function} getToken - Async function that returns the auth token
   * @param {Object} options - Client options
   */
  constructor(getToken, options = {}) {
    this.baseUrl = options.baseUrl || API_BASE;
    this.getToken = getToken;
    this.timeout = options.timeout || DEFAULT_TIMEOUT;
    this.maxRetries = options.maxRetries ?? MAX_RETRIES;

    // Interceptors
    this.requestInterceptors = [];
    this.responseInterceptors = [];

    // Add default request interceptor for logging in dev
    if (process.env.NODE_ENV === 'development') {
      this.addRequestInterceptor((url, config) => {
        console.debug(`[API] ${config.method || 'GET'} ${url}`);
        return config;
      });
    }
  }

  /**
   * Add a request interceptor
   * @param {Function} interceptor - (url, config) => config
   */
  addRequestInterceptor(interceptor) {
    this.requestInterceptors.push(interceptor);
    return () => {
      const index = this.requestInterceptors.indexOf(interceptor);
      if (index > -1) this.requestInterceptors.splice(index, 1);
    };
  }

  /**
   * Add a response interceptor
   * @param {Function} interceptor - (response, data) => data
   */
  addResponseInterceptor(interceptor) {
    this.responseInterceptors.push(interceptor);
    return () => {
      const index = this.responseInterceptors.indexOf(interceptor);
      if (index > -1) this.responseInterceptors.splice(index, 1);
    };
  }

  /**
   * Make an authenticated API request with retry logic
   * @param {string} endpoint - API endpoint (e.g., '/applicants')
   * @param {Object} options - Fetch options
   * @param {AbortSignal} [options.signal] - AbortController signal
   * @param {number} [options.timeout] - Request timeout in ms
   * @param {boolean} [options.skipRetry] - Skip retry logic
   * @param {boolean} [options.dedupe] - Enable request deduplication (default: true for GET)
   * @returns {Promise<any>} - Parsed JSON response
   */
  async request(endpoint, options = {}) {
    // Check online status
    if (!isOnline()) {
      throw new ApiError('No internet connection', 0);
    }

    const url = `${this.baseUrl}${endpoint}`;
    const timeout = options.timeout || this.timeout;
    const skipRetry = options.skipRetry || false;
    const dedupe = options.dedupe !== false;

    // Request deduplication for GET requests
    const requestKey = dedupe ? getRequestKey(url, options) : null;
    if (requestKey && inflightRequests.has(requestKey)) {
      return inflightRequests.get(requestKey);
    }

    const executeRequest = async (attempt = 1) => {
      // Create abort controller for timeout
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), timeout);

      // Merge signals if external signal provided
      const signal = options.signal
        ? this._mergeSignals(options.signal, controller.signal)
        : controller.signal;

      try {
        const token = await this.getToken();

        let config = {
          ...options,
          signal,
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json',
            'X-Request-ID': this._generateRequestId(),
            ...options.headers,
          },
        };

        // Remove Content-Type for FormData (let browser set it with boundary)
        if (options.body instanceof FormData) {
          delete config.headers['Content-Type'];
        }

        // Apply request interceptors
        for (const interceptor of this.requestInterceptors) {
          config = await interceptor(url, config);
        }

        const response = await fetch(url, config);
        clearTimeout(timeoutId);

        // Extract request ID from response for error tracking
        const requestId = response.headers.get('X-Request-ID') || config.headers['X-Request-ID'];

        // Handle different status codes
        if (response.status === 401) {
          // Clear any cached auth state and redirect
          window.location.href = '/login';
          throw new ApiError('Session expired - please log in again', 401, null, requestId);
        }

        if (response.status === 403) {
          throw new ApiError('You do not have permission to perform this action', 403, null, requestId);
        }

        if (response.status === 404) {
          const error = await response.json().catch(() => ({}));
          throw new ApiError(error.detail || 'The requested resource was not found', 404, error, requestId);
        }

        if (response.status === 422) {
          const error = await response.json().catch(() => ({}));
          const message = this._formatValidationError(error);
          throw new ApiError(message, 422, error, requestId);
        }

        if (response.status === 429) {
          const retryAfter = response.headers.get('Retry-After');
          const error = new ApiError('Too many requests - please slow down', 429, { retryAfter }, requestId);

          // Auto-retry after the specified delay if within retry limit
          if (!skipRetry && attempt <= this.maxRetries && retryAfter) {
            await sleep(parseInt(retryAfter, 10) * 1000);
            return executeRequest(attempt + 1);
          }
          throw error;
        }

        if (!response.ok) {
          const error = await response.json().catch(() => ({}));
          const apiError = new ApiError(
            error.detail || `Request failed with status ${response.status}`,
            response.status,
            error,
            requestId
          );

          // Retry on server errors
          if (!skipRetry && apiError.isRetryable && attempt <= this.maxRetries) {
            const delay = RETRY_DELAY_BASE * Math.pow(2, attempt - 1);
            await sleep(delay);
            return executeRequest(attempt + 1);
          }

          throw apiError;
        }

        // Handle 204 No Content
        if (response.status === 204) {
          return null;
        }

        let data = await response.json();

        // Apply response interceptors
        for (const interceptor of this.responseInterceptors) {
          data = await interceptor(response, data);
        }

        return data;

      } catch (error) {
        clearTimeout(timeoutId);

        // Handle abort/timeout
        if (error.name === 'AbortError') {
          throw new ApiError('Request timed out', 0);
        }

        // Handle network errors with retry
        if (error instanceof TypeError && error.message === 'Failed to fetch') {
          if (!skipRetry && attempt <= this.maxRetries) {
            const delay = RETRY_DELAY_BASE * Math.pow(2, attempt - 1);
            await sleep(delay);
            return executeRequest(attempt + 1);
          }
          throw new ApiError('Network error - please check your connection', 0);
        }

        throw error;
      }
    };

    // Execute with deduplication
    const promise = executeRequest();

    if (requestKey) {
      inflightRequests.set(requestKey, promise);
      promise.finally(() => {
        inflightRequests.delete(requestKey);
      });
    }

    return promise;
  }

  /**
   * Format validation errors into readable message
   */
  _formatValidationError(error) {
    if (typeof error.detail === 'string') {
      return error.detail;
    }
    if (Array.isArray(error.detail)) {
      return error.detail
        .map(e => {
          const field = e.loc?.slice(1).join('.') || 'Field';
          return `${field}: ${e.msg}`;
        })
        .join('. ');
    }
    return 'Validation error - please check your input';
  }

  /**
   * Generate unique request ID
   */
  _generateRequestId() {
    return `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
  }

  /**
   * Merge multiple abort signals
   */
  _mergeSignals(signal1, signal2) {
    const controller = new AbortController();

    const onAbort = () => controller.abort();
    signal1.addEventListener('abort', onAbort);
    signal2.addEventListener('abort', onAbort);

    return controller.signal;
  }

  /**
   * Make a request that returns a blob (for file downloads)
   * @param {string} endpoint - API endpoint
   * @param {Object} options - Fetch options
   * @returns {Promise<Blob>}
   */
  async requestBlob(endpoint, options = {}) {
    if (!isOnline()) {
      throw new ApiError('No internet connection', 0);
    }

    const token = await this.getToken();
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), options.timeout || this.timeout);

    try {
      const response = await fetch(`${this.baseUrl}${endpoint}`, {
        ...options,
        signal: options.signal || controller.signal,
        headers: {
          'Authorization': `Bearer ${token}`,
          ...options.headers,
        },
      });

      clearTimeout(timeoutId);

      if (!response.ok) {
        const error = await response.json().catch(() => ({}));
        throw new ApiError(
          error.detail || `Download failed with status ${response.status}`,
          response.status,
          error
        );
      }

      return response.blob();
    } catch (error) {
      clearTimeout(timeoutId);
      if (error.name === 'AbortError') {
        throw new ApiError('Download timed out', 0);
      }
      throw error;
    }
  }

  /**
   * Make a request that returns text (for CSV exports)
   * @param {string} endpoint - API endpoint
   * @param {Object} options - Fetch options
   * @returns {Promise<string>}
   */
  async requestText(endpoint, options = {}) {
    if (!isOnline()) {
      throw new ApiError('No internet connection', 0);
    }

    const token = await this.getToken();
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), options.timeout || this.timeout);

    try {
      const response = await fetch(`${this.baseUrl}${endpoint}`, {
        ...options,
        signal: options.signal || controller.signal,
        headers: {
          'Authorization': `Bearer ${token}`,
          'Accept': 'text/csv',
          ...options.headers,
        },
      });

      clearTimeout(timeoutId);

      if (!response.ok) {
        const error = await response.json().catch(() => ({}));
        throw new ApiError(
          error.detail || `Export failed with status ${response.status}`,
          response.status,
          error
        );
      }

      return response.text();
    } catch (error) {
      clearTimeout(timeoutId);
      if (error.name === 'AbortError') {
        throw new ApiError('Export timed out', 0);
      }
      throw error;
    }
  }

  /**
   * GET request
   */
  get(endpoint, options = {}) {
    return this.request(endpoint, { ...options, method: 'GET' });
  }

  /**
   * POST request
   */
  post(endpoint, data, options = {}) {
    return this.request(endpoint, {
      ...options,
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  /**
   * POST request with FormData
   */
  postForm(endpoint, formData, options = {}) {
    return this.request(endpoint, {
      ...options,
      method: 'POST',
      body: formData,
    });
  }

  /**
   * PATCH request
   */
  patch(endpoint, data, options = {}) {
    return this.request(endpoint, {
      ...options,
      method: 'PATCH',
      body: JSON.stringify(data),
    });
  }

  /**
   * PUT request
   */
  put(endpoint, data, options = {}) {
    return this.request(endpoint, {
      ...options,
      method: 'PUT',
      body: JSON.stringify(data),
    });
  }

  /**
   * DELETE request
   */
  delete(endpoint, options = {}) {
    return this.request(endpoint, { ...options, method: 'DELETE' });
  }
}

/**
 * Build query string from params object
 * Filters out null/undefined values and handles arrays
 * @param {Object} params
 * @returns {string}
 */
export function buildQueryString(params) {
  const searchParams = new URLSearchParams();

  Object.entries(params).forEach(([key, value]) => {
    if (value === null || value === undefined || value === '') {
      return;
    }

    // Handle arrays (e.g., status[]=pending&status[]=approved)
    if (Array.isArray(value)) {
      value.forEach(v => {
        if (v !== null && v !== undefined && v !== '') {
          searchParams.append(key, String(v));
        }
      });
    } else {
      searchParams.append(key, String(value));
    }
  });

  const queryString = searchParams.toString();
  return queryString ? `?${queryString}` : '';
}

/**
 * Create a singleton API client instance
 * Use this when you need a shared client across the app
 */
let sharedClient = null;

export function getSharedClient(getToken) {
  if (!sharedClient) {
    sharedClient = new ApiClient(getToken);
  }
  return sharedClient;
}

export function resetSharedClient() {
  sharedClient = null;
}

export default ApiClient;
