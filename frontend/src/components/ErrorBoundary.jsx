import React from 'react';
import { AlertTriangle, RefreshCw, Home } from 'lucide-react';

/**
 * Error Boundary component
 *
 * Catches JavaScript errors anywhere in the child component tree,
 * logs those errors, and displays a fallback UI.
 */
export class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null, errorInfo: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    this.setState({ errorInfo });
    console.error('ErrorBoundary caught an error:', error, errorInfo);

    // You could send this to an error reporting service
    // e.g., Sentry, LogRocket, etc.
  }

  handleReset = () => {
    this.setState({ hasError: false, error: null, errorInfo: null });
  };

  handleGoHome = () => {
    window.location.href = '/';
  };

  render() {
    if (this.state.hasError) {
      // Custom fallback UI if provided
      if (this.props.fallback) {
        return this.props.fallback;
      }

      // Default error UI
      return (
        <div style={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          minHeight: '400px',
          padding: '40px',
          textAlign: 'center',
          fontFamily: 'system-ui, -apple-system, sans-serif',
        }}>
          <div style={{
            backgroundColor: '#fef2f2',
            borderRadius: '50%',
            padding: '16px',
            marginBottom: '24px',
          }}>
            <AlertTriangle size={48} color="#ef4444" />
          </div>

          <h2 style={{
            fontSize: '24px',
            fontWeight: '600',
            color: '#1f2937',
            margin: '0 0 8px 0',
          }}>
            Something went wrong
          </h2>

          <p style={{
            fontSize: '16px',
            color: '#6b7280',
            margin: '0 0 24px 0',
            maxWidth: '400px',
          }}>
            We encountered an unexpected error. Please try again or return to the dashboard.
          </p>

          {process.env.NODE_ENV === 'development' && this.state.error && (
            <details style={{
              backgroundColor: '#f9fafb',
              border: '1px solid #e5e7eb',
              borderRadius: '8px',
              padding: '16px',
              marginBottom: '24px',
              maxWidth: '600px',
              textAlign: 'left',
              fontSize: '14px',
            }}>
              <summary style={{
                cursor: 'pointer',
                fontWeight: '500',
                marginBottom: '8px',
              }}>
                Error Details (Development Only)
              </summary>
              <pre style={{
                overflow: 'auto',
                margin: '8px 0 0 0',
                padding: '12px',
                backgroundColor: '#1f2937',
                color: '#f9fafb',
                borderRadius: '4px',
                fontSize: '12px',
              }}>
                {this.state.error.toString()}
                {this.state.errorInfo?.componentStack}
              </pre>
            </details>
          )}

          <div style={{
            display: 'flex',
            gap: '12px',
          }}>
            <button
              onClick={this.handleReset}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                padding: '10px 20px',
                backgroundColor: '#3b82f6',
                color: 'white',
                border: 'none',
                borderRadius: '6px',
                fontSize: '14px',
                fontWeight: '500',
                cursor: 'pointer',
              }}
            >
              <RefreshCw size={16} />
              Try Again
            </button>

            <button
              onClick={this.handleGoHome}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                padding: '10px 20px',
                backgroundColor: 'white',
                color: '#374151',
                border: '1px solid #d1d5db',
                borderRadius: '6px',
                fontSize: '14px',
                fontWeight: '500',
                cursor: 'pointer',
              }}
            >
              <Home size={16} />
              Go to Dashboard
            </button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

/**
 * Inline error display component for query/mutation errors
 */
export function ErrorMessage({ error, onRetry, className = '' }) {
  const message = error?.message || 'An error occurred';

  return (
    <div
      className={className}
      style={{
        display: 'flex',
        alignItems: 'center',
        gap: '12px',
        padding: '12px 16px',
        backgroundColor: '#fef2f2',
        border: '1px solid #fecaca',
        borderRadius: '8px',
        color: '#991b1b',
        fontSize: '14px',
      }}
    >
      <AlertTriangle size={20} style={{ flexShrink: 0 }} />
      <span style={{ flex: 1 }}>{message}</span>
      {onRetry && (
        <button
          onClick={onRetry}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '4px',
            padding: '6px 12px',
            backgroundColor: 'white',
            color: '#991b1b',
            border: '1px solid #fecaca',
            borderRadius: '4px',
            fontSize: '13px',
            cursor: 'pointer',
          }}
        >
          <RefreshCw size={14} />
          Retry
        </button>
      )}
    </div>
  );
}

/**
 * Full-page error display
 */
export function ErrorPage({ title, message, onRetry }) {
  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      minHeight: '60vh',
      padding: '40px',
      textAlign: 'center',
    }}>
      <AlertTriangle size={48} color="#ef4444" style={{ marginBottom: '16px' }} />
      <h2 style={{
        fontSize: '20px',
        fontWeight: '600',
        color: '#1f2937',
        margin: '0 0 8px 0',
      }}>
        {title || 'Error'}
      </h2>
      <p style={{
        fontSize: '14px',
        color: '#6b7280',
        margin: '0 0 20px 0',
      }}>
        {message || 'Something went wrong'}
      </p>
      {onRetry && (
        <button
          onClick={onRetry}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            padding: '10px 20px',
            backgroundColor: '#3b82f6',
            color: 'white',
            border: 'none',
            borderRadius: '6px',
            fontSize: '14px',
            fontWeight: '500',
            cursor: 'pointer',
          }}
        >
          <RefreshCw size={16} />
          Try Again
        </button>
      )}
    </div>
  );
}

export default ErrorBoundary;
