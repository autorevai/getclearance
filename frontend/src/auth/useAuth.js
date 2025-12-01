import { useAuth0 } from '@auth0/auth0-react';
import { useCallback, useState, useEffect, useRef } from 'react';

/**
 * Custom hook that wraps Auth0's useAuth0 hook with additional convenience methods.
 *
 * Provides:
 * - isAuthenticated: boolean indicating if user is logged in
 * - isLoading: boolean indicating if auth state is being determined
 * - user: user profile object with name, email, picture, etc.
 * - login(): trigger Auth0 Universal Login
 * - logout(): clear session and redirect to login
 * - getToken(): get access token for API calls (async)
 * - isRefreshing: boolean indicating if token is being refreshed
 * - tokenError: error from last token refresh attempt
 *
 * Token Refresh Handling:
 * - Automatically handles token expiration
 * - Provides UI feedback during refresh
 * - Graceful fallback to re-login on refresh failure
 *
 * Usage:
 *   const { isAuthenticated, user, login, logout, getToken, isRefreshing } = useAuth();
 */
export function useAuth() {
  const {
    isAuthenticated,
    isLoading,
    user,
    loginWithRedirect,
    logout: auth0Logout,
    getAccessTokenSilently,
    error,
  } = useAuth0();

  // Track token refresh state for UI feedback
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [tokenError, setTokenError] = useState(null);

  // Track if we've already triggered a login redirect to prevent loops
  const loginRedirectTriggered = useRef(false);

  // Reset redirect flag when auth state changes
  useEffect(() => {
    if (isAuthenticated) {
      loginRedirectTriggered.current = false;
      setTokenError(null);
    }
  }, [isAuthenticated]);

  /**
   * Trigger Auth0 Universal Login flow
   * @param {Object} options - Optional login options
   */
  const login = useCallback((options = {}) => {
    return loginWithRedirect({
      appState: {
        returnTo: window.location.pathname,
      },
      ...options,
    });
  }, [loginWithRedirect]);

  /**
   * Logout user and redirect to login page
   * Clears local session and Auth0 session
   */
  const logout = useCallback(() => {
    auth0Logout({
      logoutParams: {
        returnTo: window.location.origin,
      },
    });
  }, [auth0Logout]);

  /**
   * Get access token for API calls with enhanced error handling
   * Returns a JWT token that can be used in Authorization header
   *
   * Handles:
   * - Normal token retrieval
   * - Token refresh when expired
   * - Re-login redirect when refresh fails
   * - Prevents redirect loops
   *
   * @param {Object} options - Optional token options
   * @param {boolean} options.silentOnly - If true, don't redirect to login on failure
   * @returns {Promise<string>} The access token
   * @throws {Error} If token cannot be obtained
   */
  const getToken = useCallback(async (options = {}) => {
    const { silentOnly = false } = options;

    setIsRefreshing(true);
    setTokenError(null);

    try {
      const token = await getAccessTokenSilently({
        authorizationParams: {
          audience: process.env.REACT_APP_AUTH0_AUDIENCE,
        },
        // Use cached token if available and not expired
        cacheMode: 'on',
      });

      setIsRefreshing(false);
      return token;
    } catch (err) {
      setIsRefreshing(false);
      setTokenError(err);

      // Log error for debugging
      if (process.env.NODE_ENV === 'development') {
        console.error('Token acquisition failed:', {
          error: err.error,
          message: err.message,
          description: err.error_description,
        });
      }

      // Determine if we need to re-authenticate
      const requiresLogin =
        err.error === 'login_required' ||
        err.error === 'consent_required' ||
        err.error === 'interaction_required' ||
        err.message?.includes('Login required') ||
        err.message?.includes('Consent required');

      if (requiresLogin && !silentOnly) {
        // Prevent redirect loops
        if (!loginRedirectTriggered.current) {
          loginRedirectTriggered.current = true;

          // Small delay to allow any UI updates
          setTimeout(() => {
            login({
              appState: {
                returnTo: window.location.pathname + window.location.search,
              },
            });
          }, 100);
        }
      }

      throw err;
    }
  }, [getAccessTokenSilently, login]);

  /**
   * Check if the current token is close to expiration
   * Useful for proactive token refresh
   *
   * @param {number} thresholdSeconds - Seconds before expiry to consider "close"
   * @returns {Promise<boolean>} True if token expires within threshold
   */
  const isTokenExpiringSoon = useCallback(async (thresholdSeconds = 300) => {
    try {
      // Try to get token claims to check expiration
      const token = await getAccessTokenSilently({
        cacheMode: 'cache-only',
      });

      if (!token) return true;

      // Decode JWT to get expiration (without verifying signature)
      const [, payload] = token.split('.');
      const decoded = JSON.parse(atob(payload));
      const expiresAt = decoded.exp * 1000; // Convert to milliseconds
      const now = Date.now();
      const threshold = thresholdSeconds * 1000;

      return expiresAt - now < threshold;
    } catch {
      // If we can't check, assume it might be expiring
      return true;
    }
  }, [getAccessTokenSilently]);

  /**
   * Proactively refresh token before it expires
   * Call this periodically or before important operations
   */
  const refreshTokenIfNeeded = useCallback(async () => {
    const expiringSoon = await isTokenExpiringSoon();

    if (expiringSoon && isAuthenticated) {
      try {
        await getToken();
      } catch (err) {
        // Token refresh failed, but don't throw - let the next API call handle it
        console.warn('Proactive token refresh failed:', err.message);
      }
    }
  }, [isTokenExpiringSoon, isAuthenticated, getToken]);

  // Set up periodic token refresh check (every 4 minutes)
  useEffect(() => {
    if (!isAuthenticated) return;

    const intervalId = setInterval(() => {
      refreshTokenIfNeeded();
    }, 4 * 60 * 1000); // 4 minutes

    return () => clearInterval(intervalId);
  }, [isAuthenticated, refreshTokenIfNeeded]);

  return {
    isAuthenticated,
    isLoading,
    user,
    login,
    logout,
    getToken,
    error,
    // New additions for token refresh handling
    isRefreshing,
    tokenError,
    refreshTokenIfNeeded,
    isTokenExpiringSoon,
  };
}

export default useAuth;
