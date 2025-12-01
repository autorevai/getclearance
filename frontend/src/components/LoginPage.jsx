import React, { useEffect } from 'react';
import { Shield, ArrowRight, Lock, CheckCircle, AlertCircle } from 'lucide-react';
import { useAuth } from '../auth';

// CSS keyframes injected once via useEffect
const KEYFRAMES_ID = 'getclearance-keyframes';
const keyframesCSS = `
  @keyframes gc-spin {
    to { transform: rotate(360deg); }
  }
  @keyframes gc-pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.5; }
  }
`;

/**
 * LoginPage component displays the login screen with branding and Auth0 login button.
 *
 * Features:
 * - GetClearance branding with logo
 * - Feature highlights
 * - Auth0 Universal Login trigger
 * - Loading state during login
 * - Error handling with retry
 * - Full accessibility support
 */
export function LoginPage() {
  const { login, isLoading, error } = useAuth();

  // Inject keyframes CSS once on mount
  useEffect(() => {
    if (!document.getElementById(KEYFRAMES_ID)) {
      const styleSheet = document.createElement('style');
      styleSheet.id = KEYFRAMES_ID;
      styleSheet.textContent = keyframesCSS;
      document.head.appendChild(styleSheet);
    }
  }, []);

  const handleLogin = () => {
    login();
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      handleLogin();
    }
  };

  return (
    <div style={styles.container} role="main" aria-labelledby="login-title">
      <div style={styles.loginCard}>
        {/* Logo and Branding */}
        <div style={styles.logoSection}>
          <div style={styles.logoIcon} aria-hidden="true">
            <Shield size={32} color="#10b981" />
          </div>
          <h1 id="login-title" style={styles.logoText}>GetClearance</h1>
          <p style={styles.tagline}>AI-Native KYC/AML Compliance Platform</p>
        </div>

        {/* Feature highlights */}
        <ul style={styles.features} aria-label="Platform features">
          <li style={styles.feature}>
            <CheckCircle size={16} color="#10b981" aria-hidden="true" />
            <span>Automated identity verification</span>
          </li>
          <li style={styles.feature}>
            <CheckCircle size={16} color="#10b981" aria-hidden="true" />
            <span>Real-time AML screening</span>
          </li>
          <li style={styles.feature}>
            <CheckCircle size={16} color="#10b981" aria-hidden="true" />
            <span>AI-powered risk assessment</span>
          </li>
        </ul>

        {/* Error message */}
        {error && (
          <div style={styles.errorBox} role="alert" aria-live="polite">
            <AlertCircle size={16} color="#ef4444" aria-hidden="true" />
            <span>{error.message || 'Authentication failed. Please try again.'}</span>
          </div>
        )}

        {/* Login Button */}
        <button
          onClick={handleLogin}
          onKeyDown={handleKeyDown}
          disabled={isLoading}
          style={{
            ...styles.loginButton,
            ...(isLoading ? styles.loginButtonDisabled : {}),
          }}
          aria-busy={isLoading}
          aria-describedby="security-note"
        >
          {isLoading ? (
            <>
              <span style={styles.spinner} aria-hidden="true" />
              <span>Connecting...</span>
            </>
          ) : (
            <>
              <Lock size={18} aria-hidden="true" />
              <span>Sign in with Auth0</span>
              <ArrowRight size={18} aria-hidden="true" />
            </>
          )}
        </button>

        {/* Security note */}
        <p id="security-note" style={styles.securityNote}>
          <Lock size={12} aria-hidden="true" />
          <span>Secured with enterprise-grade authentication</span>
        </p>
      </div>

      {/* Footer */}
      <footer style={styles.footer}>
        <p>Built with AI by GetClearance</p>
      </footer>
    </div>
  );
}

const styles = {
  container: {
    minHeight: '100vh',
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    justifyContent: 'center',
    background: 'linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #0f172a 100%)',
    padding: 20,
    fontFamily: "'DM Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
  },
  loginCard: {
    background: 'rgba(30, 41, 59, 0.8)',
    backdropFilter: 'blur(10px)',
    WebkitBackdropFilter: 'blur(10px)', // Safari support
    borderRadius: 16,
    padding: 40,
    width: '100%',
    maxWidth: 400,
    border: '1px solid rgba(71, 85, 105, 0.5)',
    boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.5)',
  },
  logoSection: {
    textAlign: 'center',
    marginBottom: 32,
  },
  logoIcon: {
    width: 64,
    height: 64,
    borderRadius: 16,
    background: 'rgba(16, 185, 129, 0.1)',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    margin: '0 auto 16px',
    border: '1px solid rgba(16, 185, 129, 0.2)',
  },
  logoText: {
    fontSize: 28,
    fontWeight: 700,
    color: '#f8fafc',
    margin: 0,
    letterSpacing: '-0.02em',
  },
  tagline: {
    color: '#94a3b8',
    fontSize: 14,
    marginTop: 8,
    margin: '8px 0 0 0',
  },
  features: {
    display: 'flex',
    flexDirection: 'column',
    gap: 12,
    marginBottom: 32,
    padding: '20px 0',
    borderTop: '1px solid rgba(71, 85, 105, 0.3)',
    borderBottom: '1px solid rgba(71, 85, 105, 0.3)',
    listStyle: 'none',
    margin: '0 0 32px 0',
  },
  feature: {
    display: 'flex',
    alignItems: 'center',
    gap: 12,
    color: '#cbd5e1',
    fontSize: 14,
  },
  errorBox: {
    display: 'flex',
    alignItems: 'center',
    gap: 8,
    padding: '12px 16px',
    marginBottom: 16,
    background: 'rgba(239, 68, 68, 0.1)',
    border: '1px solid rgba(239, 68, 68, 0.3)',
    borderRadius: 8,
    color: '#fca5a5',
    fontSize: 14,
  },
  loginButton: {
    width: '100%',
    padding: '14px 20px',
    background: 'linear-gradient(135deg, #10b981 0%, #059669 100%)',
    color: '#fff',
    border: 'none',
    borderRadius: 10,
    fontSize: 16,
    fontWeight: 600,
    cursor: 'pointer',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 10,
    transition: 'all 0.2s ease',
    fontFamily: 'inherit',
  },
  loginButtonDisabled: {
    opacity: 0.7,
    cursor: 'not-allowed',
  },
  spinner: {
    width: 18,
    height: 18,
    border: '2px solid rgba(255, 255, 255, 0.3)',
    borderTopColor: '#fff',
    borderRadius: '50%',
    animation: 'gc-spin 0.8s linear infinite',
    display: 'inline-block',
  },
  securityNote: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 6,
    marginTop: 20,
    color: '#64748b',
    fontSize: 12,
    margin: '20px 0 0 0',
  },
  footer: {
    marginTop: 40,
    color: '#475569',
    fontSize: 12,
  },
};

export default LoginPage;
