import React from 'react';
import { useAuth0 } from '@auth0/auth0-react';
import LoadingScreen from '../components/LoadingScreen';

/**
 * ProtectedRoute component guards routes that require authentication.
 *
 * Behavior:
 * - Shows loading screen while auth state is being determined
 * - Redirects to Auth0 login if user is not authenticated
 * - Renders children if user is authenticated
 *
 * Usage:
 *   <ProtectedRoute>
 *     <Dashboard />
 *   </ProtectedRoute>
 */
export function ProtectedRoute({ children }) {
  const { isAuthenticated, isLoading, loginWithRedirect } = useAuth0();

  // Show loading screen while checking authentication state
  if (isLoading) {
    return <LoadingScreen message="Checking authentication..." />;
  }

  // Redirect to login if not authenticated
  if (!isAuthenticated) {
    // Trigger login redirect
    loginWithRedirect({
      appState: {
        returnTo: window.location.pathname,
      },
    });

    // Show loading while redirecting
    return <LoadingScreen message="Redirecting to login..." />;
  }

  // User is authenticated, render the protected content
  return <>{children}</>;
}

export default ProtectedRoute;
