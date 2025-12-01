import React from 'react';
import { Shield, ArrowRight, Lock, CheckCircle } from 'lucide-react';
import { useAuth } from '../auth';

/**
 * LoginPage component displays the login screen with branding and Auth0 login button.
 *
 * Features:
 * - GetClearance branding with logo
 * - Feature highlights
 * - Auth0 Universal Login trigger
 * - Loading state during login
 */
export function LoginPage() {
  const { login, isLoading } = useAuth();

  const handleLogin = () => {
    login();
  };

  return (
    <div style={styles.container}>
      <div style={styles.loginCard}>
        {/* Logo and Branding */}
        <div style={styles.logoSection}>
          <div style={styles.logoIcon}>
            <Shield size={32} color="#10b981" />
          </div>
          <h1 style={styles.logoText}>GetClearance</h1>
          <p style={styles.tagline}>AI-Native KYC/AML Compliance Platform</p>
        </div>

        {/* Feature highlights */}
        <div style={styles.features}>
          <div style={styles.feature}>
            <CheckCircle size={16} color="#10b981" />
            <span>Automated identity verification</span>
          </div>
          <div style={styles.feature}>
            <CheckCircle size={16} color="#10b981" />
            <span>Real-time AML screening</span>
          </div>
          <div style={styles.feature}>
            <CheckCircle size={16} color="#10b981" />
            <span>AI-powered risk assessment</span>
          </div>
        </div>

        {/* Login Button */}
        <button
          onClick={handleLogin}
          disabled={isLoading}
          style={styles.loginButton}
        >
          {isLoading ? (
            <>
              <div style={styles.spinner} />
              <span>Connecting...</span>
            </>
          ) : (
            <>
              <Lock size={18} />
              <span>Sign in with Auth0</span>
              <ArrowRight size={18} />
            </>
          )}
        </button>

        {/* Security note */}
        <p style={styles.securityNote}>
          <Lock size={12} />
          <span>Secured with enterprise-grade authentication</span>
        </p>
      </div>

      {/* Footer */}
      <div style={styles.footer}>
        <p>Built with AI by GetClearance</p>
      </div>
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
  },
  loginCard: {
    background: 'rgba(30, 41, 59, 0.8)',
    backdropFilter: 'blur(10px)',
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
  },
  features: {
    display: 'flex',
    flexDirection: 'column',
    gap: 12,
    marginBottom: 32,
    padding: '20px 0',
    borderTop: '1px solid rgba(71, 85, 105, 0.3)',
    borderBottom: '1px solid rgba(71, 85, 105, 0.3)',
  },
  feature: {
    display: 'flex',
    alignItems: 'center',
    gap: 12,
    color: '#cbd5e1',
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
  },
  spinner: {
    width: 18,
    height: 18,
    border: '2px solid rgba(255, 255, 255, 0.3)',
    borderTopColor: '#fff',
    borderRadius: '50%',
    animation: 'spin 0.8s linear infinite',
  },
  securityNote: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 6,
    marginTop: 20,
    color: '#64748b',
    fontSize: 12,
  },
  footer: {
    marginTop: 40,
    color: '#475569',
    fontSize: 12,
  },
};

// Add keyframes for spinner animation
const styleSheet = document.createElement('style');
styleSheet.textContent = `
  @keyframes spin {
    to { transform: rotate(360deg); }
  }
`;
document.head.appendChild(styleSheet);

export default LoginPage;
