import React, { Component } from 'react';
import { Shield, RefreshCw, AlertTriangle } from 'lucide-react';

/**
 * AuthErrorBoundary catches errors from Auth0 SDK and provides fallback UI.
 *
 * Handles:
 * - Auth0 SDK initialization failures
 * - Network errors during auth flow
 * - Token refresh failures
 * - Misconfiguration errors
 */
class AuthErrorBoundary extends Component {
  constructor(props) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null
    };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    this.setState({ errorInfo });

    // Log to console in development
    if (process.env.NODE_ENV === 'development') {
      console.error('Auth Error Boundary caught an error:', error, errorInfo);
    }

    // In production, you might want to log to an error tracking service
    // logErrorToService(error, errorInfo);
  }

  handleRetry = () => {
    this.setState({ hasError: false, error: null, errorInfo: null });
    window.location.reload();
  };

  handleClearAndRetry = () => {
    // Clear any cached auth state that might be corrupted
    localStorage.removeItem('auth0.is.authenticated');
    // Clear all Auth0 related items
    Object.keys(localStorage).forEach(key => {
      if (key.startsWith('@@auth0')) {
        localStorage.removeItem(key);
      }
    });
    this.handleRetry();
  };

  getErrorMessage() {
    const { error } = this.state;

    if (!error) return 'An unexpected error occurred.';

    // Common Auth0 error messages
    if (error.message?.includes('Invalid state')) {
      return 'Your session expired. Please try logging in again.';
    }
    if (error.message?.includes('network')) {
      return 'Network error. Please check your connection and try again.';
    }
    if (error.message?.includes('configuration')) {
      return 'Authentication is not configured correctly. Please contact support.';
    }
    if (error.message?.includes('popup')) {
      return 'Login popup was blocked. Please allow popups for this site.';
    }

    return error.message || 'Authentication failed. Please try again.';
  }

  render() {
    if (this.state.hasError) {
      return (
        <div style={styles.container} role="alert" aria-live="assertive">
          <div style={styles.card}>
            {/* Logo */}
            <div style={styles.logoSection}>
              <div style={styles.logoIcon}>
                <Shield size={32} color="#10b981" />
              </div>
              <h1 style={styles.logoText}>GetClearance</h1>
            </div>

            {/* Error Icon */}
            <div style={styles.errorIcon}>
              <AlertTriangle size={48} color="#f59e0b" />
            </div>

            {/* Error Message */}
            <h2 style={styles.errorTitle}>Authentication Error</h2>
            <p style={styles.errorMessage}>{this.getErrorMessage()}</p>

            {/* Debug info in development */}
            {process.env.NODE_ENV === 'development' && this.state.error && (
              <details style={styles.details}>
                <summary style={styles.summary}>Technical Details</summary>
                <pre style={styles.pre}>
                  {this.state.error.toString()}
                  {this.state.errorInfo?.componentStack}
                </pre>
              </details>
            )}

            {/* Action Buttons */}
            <div style={styles.actions}>
              <button
                onClick={this.handleRetry}
                style={styles.primaryButton}
                aria-label="Retry authentication"
              >
                <RefreshCw size={18} aria-hidden="true" />
                <span>Try Again</span>
              </button>
              <button
                onClick={this.handleClearAndRetry}
                style={styles.secondaryButton}
                aria-label="Clear session and retry"
              >
                Clear Session & Retry
              </button>
            </div>

            {/* Help text */}
            <p style={styles.helpText}>
              If this problem persists, please contact{' '}
              <a href="mailto:support@getclearance.dev" style={styles.link}>
                support@getclearance.dev
              </a>
            </p>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

const styles = {
  container: {
    minHeight: '100vh',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    background: 'linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #0f172a 100%)',
    padding: 20,
    fontFamily: "'DM Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
  },
  card: {
    background: 'rgba(30, 41, 59, 0.9)',
    backdropFilter: 'blur(10px)',
    WebkitBackdropFilter: 'blur(10px)',
    borderRadius: 16,
    padding: 40,
    width: '100%',
    maxWidth: 440,
    border: '1px solid rgba(71, 85, 105, 0.5)',
    boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.5)',
    textAlign: 'center',
  },
  logoSection: {
    marginBottom: 24,
  },
  logoIcon: {
    width: 56,
    height: 56,
    borderRadius: 14,
    background: 'rgba(16, 185, 129, 0.1)',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    margin: '0 auto 12px',
    border: '1px solid rgba(16, 185, 129, 0.2)',
  },
  logoText: {
    fontSize: 22,
    fontWeight: 700,
    color: '#f8fafc',
    margin: 0,
    letterSpacing: '-0.02em',
  },
  errorIcon: {
    width: 80,
    height: 80,
    borderRadius: '50%',
    background: 'rgba(245, 158, 11, 0.1)',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    margin: '0 auto 20px',
    border: '1px solid rgba(245, 158, 11, 0.2)',
  },
  errorTitle: {
    fontSize: 20,
    fontWeight: 600,
    color: '#f8fafc',
    margin: '0 0 12px 0',
  },
  errorMessage: {
    fontSize: 14,
    color: '#94a3b8',
    margin: '0 0 24px 0',
    lineHeight: 1.6,
  },
  details: {
    background: 'rgba(0, 0, 0, 0.2)',
    borderRadius: 8,
    padding: '12px 16px',
    marginBottom: 24,
    textAlign: 'left',
  },
  summary: {
    cursor: 'pointer',
    color: '#94a3b8',
    fontSize: 12,
    fontWeight: 500,
  },
  pre: {
    marginTop: 12,
    fontSize: 11,
    color: '#ef4444',
    whiteSpace: 'pre-wrap',
    wordBreak: 'break-all',
    fontFamily: "'JetBrains Mono', monospace",
  },
  actions: {
    display: 'flex',
    flexDirection: 'column',
    gap: 12,
    marginBottom: 24,
  },
  primaryButton: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    width: '100%',
    padding: '14px 20px',
    background: 'linear-gradient(135deg, #10b981 0%, #059669 100%)',
    color: '#fff',
    border: 'none',
    borderRadius: 10,
    fontSize: 16,
    fontWeight: 600,
    cursor: 'pointer',
    transition: 'all 0.2s ease',
    fontFamily: 'inherit',
  },
  secondaryButton: {
    width: '100%',
    padding: '12px 20px',
    background: 'transparent',
    color: '#94a3b8',
    border: '1px solid rgba(71, 85, 105, 0.5)',
    borderRadius: 10,
    fontSize: 14,
    fontWeight: 500,
    cursor: 'pointer',
    transition: 'all 0.2s ease',
    fontFamily: 'inherit',
  },
  helpText: {
    fontSize: 12,
    color: '#64748b',
    margin: 0,
  },
  link: {
    color: '#10b981',
    textDecoration: 'none',
  },
};

export default AuthErrorBoundary;
