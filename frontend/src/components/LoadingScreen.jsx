import React from 'react';
import { Shield, Loader2 } from 'lucide-react';

/**
 * LoadingScreen component displays a full-page loading state.
 *
 * Used during:
 * - Initial auth state check
 * - Redirect to Auth0 login
 * - Page transitions
 *
 * @param {string} message - Optional message to display below the spinner
 */
export function LoadingScreen({ message = 'Loading...' }) {
  return (
    <div style={styles.container}>
      <div style={styles.content}>
        {/* Logo */}
        <div style={styles.logoIcon}>
          <Shield size={32} color="#10b981" />
        </div>

        {/* Spinner */}
        <div style={styles.spinnerContainer}>
          <Loader2 size={32} color="#10b981" style={styles.spinner} />
        </div>

        {/* Message */}
        <p style={styles.message}>{message}</p>
      </div>
    </div>
  );
}

const styles = {
  container: {
    minHeight: '100vh',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    background: 'linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #0f172a 100%)',
  },
  content: {
    textAlign: 'center',
  },
  logoIcon: {
    width: 64,
    height: 64,
    borderRadius: 16,
    background: 'rgba(16, 185, 129, 0.1)',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    margin: '0 auto 24px',
    border: '1px solid rgba(16, 185, 129, 0.2)',
  },
  spinnerContainer: {
    marginBottom: 16,
  },
  spinner: {
    animation: 'spin 1s linear infinite',
  },
  message: {
    color: '#94a3b8',
    fontSize: 14,
    margin: 0,
  },
};

// Add keyframes for spinner animation if not already added
if (!document.getElementById('loading-screen-styles')) {
  const styleSheet = document.createElement('style');
  styleSheet.id = 'loading-screen-styles';
  styleSheet.textContent = `
    @keyframes spin {
      to { transform: rotate(360deg); }
    }
  `;
  document.head.appendChild(styleSheet);
}

export default LoadingScreen;
