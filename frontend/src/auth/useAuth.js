import { useAuth0 } from '@auth0/auth0-react';
import { useCallback } from 'react';

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
 *
 * Usage:
 *   const { isAuthenticated, user, login, logout, getToken } = useAuth();
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
   * Get access token for API calls
   * Returns a JWT token that can be used in Authorization header
   * @returns {Promise<string>} The access token
   */
  const getToken = useCallback(async () => {
    try {
      const token = await getAccessTokenSilently({
        authorizationParams: {
          audience: process.env.REACT_APP_AUTH0_AUDIENCE,
        },
      });
      return token;
    } catch (err) {
      console.error('Error getting access token:', err);
      // If we can't get a token silently, trigger a login
      if (err.error === 'login_required' || err.error === 'consent_required') {
        login();
      }
      throw err;
    }
  }, [getAccessTokenSilently, login]);

  return {
    isAuthenticated,
    isLoading,
    user,
    login,
    logout,
    getToken,
    error,
  };
}

export default useAuth;
