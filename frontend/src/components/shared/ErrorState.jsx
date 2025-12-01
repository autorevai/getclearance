import React from 'react';
import { AlertTriangle, RefreshCw, ArrowLeft, Home } from 'lucide-react';

const styles = `
  .error-state {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 60px 40px;
    text-align: center;
    min-height: 400px;
  }

  .error-icon-wrapper {
    width: 80px;
    height: 80px;
    border-radius: 50%;
    background: rgba(239, 68, 68, 0.1);
    display: flex;
    align-items: center;
    justify-content: center;
    margin-bottom: 24px;
  }

  .error-icon {
    color: var(--danger);
  }

  .error-title {
    font-size: 20px;
    font-weight: 600;
    color: var(--text-primary);
    margin-bottom: 8px;
  }

  .error-message {
    font-size: 14px;
    color: var(--text-secondary);
    max-width: 400px;
    line-height: 1.6;
    margin-bottom: 24px;
  }

  .error-code {
    font-family: 'JetBrains Mono', monospace;
    font-size: 12px;
    color: var(--text-muted);
    background: var(--bg-tertiary);
    padding: 8px 12px;
    border-radius: 6px;
    margin-bottom: 24px;
  }

  .error-actions {
    display: flex;
    gap: 12px;
  }

  .error-btn {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 10px 20px;
    border-radius: 8px;
    font-size: 14px;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.15s;
    border: none;
    font-family: inherit;
  }

  .error-btn-primary {
    background: var(--accent-primary);
    color: white;
  }

  .error-btn-primary:hover {
    opacity: 0.9;
  }

  .error-btn-secondary {
    background: var(--bg-secondary);
    border: 1px solid var(--border-color);
    color: var(--text-primary);
  }

  .error-btn-secondary:hover {
    background: var(--bg-hover);
  }

  .not-found-icon-wrapper {
    width: 120px;
    height: 120px;
    border-radius: 50%;
    background: var(--bg-tertiary);
    display: flex;
    align-items: center;
    justify-content: center;
    margin-bottom: 24px;
    font-size: 48px;
  }
`;

export function ErrorState({
  title = 'Something went wrong',
  message = 'An unexpected error occurred. Please try again.',
  error,
  onRetry,
  onBack,
  showHomeButton = false,
  onHome
}) {
  const errorCode = error?.message || error?.toString();

  return (
    <>
      <style>{styles}</style>
      <div className="error-state">
        <div className="error-icon-wrapper">
          <AlertTriangle size={40} className="error-icon" />
        </div>
        <h2 className="error-title">{title}</h2>
        <p className="error-message">{message}</p>
        {errorCode && (
          <div className="error-code">{errorCode}</div>
        )}
        <div className="error-actions">
          {onBack && (
            <button className="error-btn error-btn-secondary" onClick={onBack}>
              <ArrowLeft size={16} />
              Go Back
            </button>
          )}
          {showHomeButton && onHome && (
            <button className="error-btn error-btn-secondary" onClick={onHome}>
              <Home size={16} />
              Home
            </button>
          )}
          {onRetry && (
            <button className="error-btn error-btn-primary" onClick={onRetry}>
              <RefreshCw size={16} />
              Try Again
            </button>
          )}
        </div>
      </div>
    </>
  );
}

export function NotFound({
  title = 'Not Found',
  message = "The resource you're looking for doesn't exist or has been removed.",
  onBack,
  onHome
}) {
  return (
    <>
      <style>{styles}</style>
      <div className="error-state">
        <div className="not-found-icon-wrapper">
          404
        </div>
        <h2 className="error-title">{title}</h2>
        <p className="error-message">{message}</p>
        <div className="error-actions">
          {onBack && (
            <button className="error-btn error-btn-secondary" onClick={onBack}>
              <ArrowLeft size={16} />
              Go Back
            </button>
          )}
          {onHome && (
            <button className="error-btn error-btn-primary" onClick={onHome}>
              <Home size={16} />
              Back to Dashboard
            </button>
          )}
        </div>
      </div>
    </>
  );
}

export default ErrorState;
