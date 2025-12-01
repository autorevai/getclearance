import React from 'react';
import { Auth0Provider } from '@auth0/auth0-react';

/**
 * AuthProvider wraps the application with Auth0 authentication context.
 *
 * Configuration:
 * - Uses environment variables for Auth0 domain, client ID, and audience
 * - Enables offline_access for refresh tokens
 * - Uses localStorage for token persistence across page refreshes
 */
export function AuthProvider({ children }) {
  const domain = process.env.REACT_APP_AUTH0_DOMAIN;
  const clientId = process.env.REACT_APP_AUTH0_CLIENT_ID;
  const audience = process.env.REACT_APP_AUTH0_AUDIENCE;

  // Validate required configuration
  if (!domain || !clientId) {
    console.error('Auth0 configuration missing. Check environment variables.');
    return (
      <div style={{
        padding: 40,
        textAlign: 'center',
        color: '#ef4444',
        fontFamily: 'system-ui, -apple-system, sans-serif'
      }}>
        <h2>Configuration Error</h2>
        <p>Auth0 environment variables are not configured.</p>
        <p style={{ fontSize: 14, color: '#6b7280', marginTop: 16 }}>
          Please set REACT_APP_AUTH0_DOMAIN and REACT_APP_AUTH0_CLIENT_ID in your .env file.
        </p>
      </div>
    );
  }

  return (
    <Auth0Provider
      domain={domain}
      clientId={clientId}
      authorizationParams={{
        redirect_uri: window.location.origin,
        audience: audience,
        scope: 'openid profile email offline_access',
      }}
      cacheLocation="localstorage"
      useRefreshTokens={true}
    >
      {children}
    </Auth0Provider>
  );
}

export default AuthProvider;
