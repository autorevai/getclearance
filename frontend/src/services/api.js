/**
 * Base API client for GetClearance backend
 *
 * Handles authentication headers, error handling, and HTTP methods.
 * All service classes extend or use this client.
 */

const API_BASE = process.env.REACT_APP_API_BASE_URL || 'http://localhost:8000/api/v1';

/**
 * Custom error class for API errors
 */
export class ApiError extends Error {
  constructor(message, status, data = null) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.data = data;
  }
}

/**
 * Base API client with authentication support
 */
export class ApiClient {
  /**
   * @param {Function} getToken - Async function that returns the auth token
   */
  constructor(getToken) {
    this.baseUrl = API_BASE;
    this.getToken = getToken;
  }

  /**
   * Make an authenticated API request
   * @param {string} endpoint - API endpoint (e.g., '/applicants')
   * @param {Object} options - Fetch options
   * @returns {Promise<any>} - Parsed JSON response
   */
  async request(endpoint, options = {}) {
    const token = await this.getToken();

    const url = `${this.baseUrl}${endpoint}`;
    const config = {
      ...options,
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
        ...options.headers,
      },
    };

    // Remove Content-Type for FormData (let browser set it with boundary)
    if (options.body instanceof FormData) {
      delete config.headers['Content-Type'];
    }

    const response = await fetch(url, config);

    // Handle 401 Unauthorized - token expired or invalid
    if (response.status === 401) {
      window.location.href = '/login';
      throw new ApiError('Unauthorized - please log in again', 401);
    }

    // Handle 403 Forbidden - permission denied
    if (response.status === 403) {
      throw new ApiError('Permission denied', 403);
    }

    // Handle 404 Not Found
    if (response.status === 404) {
      const error = await response.json().catch(() => ({}));
      throw new ApiError(error.detail || 'Resource not found', 404, error);
    }

    // Handle 422 Validation Error
    if (response.status === 422) {
      const error = await response.json().catch(() => ({}));
      throw new ApiError(error.detail || 'Validation error', 422, error);
    }

    // Handle other errors
    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      throw new ApiError(
        error.detail || `HTTP ${response.status}`,
        response.status,
        error
      );
    }

    // Handle 204 No Content
    if (response.status === 204) {
      return null;
    }

    return response.json();
  }

  /**
   * Make a request that returns a blob (for file downloads)
   * @param {string} endpoint - API endpoint
   * @returns {Promise<Blob>}
   */
  async requestBlob(endpoint) {
    const token = await this.getToken();

    const response = await fetch(`${this.baseUrl}${endpoint}`, {
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      throw new ApiError(
        error.detail || `HTTP ${response.status}`,
        response.status,
        error
      );
    }

    return response.blob();
  }

  /**
   * GET request
   * @param {string} endpoint
   * @returns {Promise<any>}
   */
  get(endpoint) {
    return this.request(endpoint, { method: 'GET' });
  }

  /**
   * POST request
   * @param {string} endpoint
   * @param {Object} data - Request body
   * @returns {Promise<any>}
   */
  post(endpoint, data) {
    return this.request(endpoint, {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  /**
   * POST request with FormData
   * @param {string} endpoint
   * @param {FormData} formData
   * @returns {Promise<any>}
   */
  postForm(endpoint, formData) {
    return this.request(endpoint, {
      method: 'POST',
      body: formData,
    });
  }

  /**
   * PATCH request
   * @param {string} endpoint
   * @param {Object} data - Request body
   * @returns {Promise<any>}
   */
  patch(endpoint, data) {
    return this.request(endpoint, {
      method: 'PATCH',
      body: JSON.stringify(data),
    });
  }

  /**
   * PUT request
   * @param {string} endpoint
   * @param {Object} data - Request body
   * @returns {Promise<any>}
   */
  put(endpoint, data) {
    return this.request(endpoint, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  }

  /**
   * DELETE request
   * @param {string} endpoint
   * @returns {Promise<any>}
   */
  delete(endpoint) {
    return this.request(endpoint, { method: 'DELETE' });
  }
}

/**
 * Build query string from params object
 * Filters out null/undefined values
 * @param {Object} params
 * @returns {string}
 */
export function buildQueryString(params) {
  const searchParams = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value !== null && value !== undefined && value !== '') {
      searchParams.append(key, String(value));
    }
  });
  const queryString = searchParams.toString();
  return queryString ? `?${queryString}` : '';
}

export default ApiClient;
