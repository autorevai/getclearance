import React from 'react';

const styles = `
  @keyframes spin {
    from {
      transform: rotate(0deg);
    }
    to {
      transform: rotate(360deg);
    }
  }

  .loading-spinner-container {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 20px;
  }

  .loading-spinner-container.fullscreen {
    min-height: 400px;
  }

  .loading-spinner {
    border: 3px solid var(--border-color, #e5e7eb);
    border-top-color: var(--accent-primary, #6366f1);
    border-radius: 50%;
    animation: spin 0.8s linear infinite;
  }

  .loading-spinner.xs {
    width: 16px;
    height: 16px;
    border-width: 2px;
  }

  .loading-spinner.sm {
    width: 20px;
    height: 20px;
    border-width: 2px;
  }

  .loading-spinner.md {
    width: 32px;
    height: 32px;
    border-width: 3px;
  }

  .loading-spinner.lg {
    width: 48px;
    height: 48px;
    border-width: 4px;
  }

  .loading-spinner.xl {
    width: 64px;
    height: 64px;
    border-width: 4px;
  }

  .loading-spinner-text {
    margin-top: 12px;
    font-size: 14px;
    color: var(--text-secondary, #6b7280);
  }

  /* Button spinner variant */
  .btn-spinner {
    display: inline-flex;
    align-items: center;
    justify-content: center;
  }

  .btn-spinner .loading-spinner {
    border-top-color: currentColor;
    border-right-color: transparent;
    border-bottom-color: transparent;
    border-left-color: transparent;
  }
`;

/**
 * Loading spinner component with multiple sizes and variants
 *
 * @param {Object} props
 * @param {'xs' | 'sm' | 'md' | 'lg' | 'xl'} props.size - Spinner size (default: 'md')
 * @param {string} props.text - Optional text to display below spinner
 * @param {boolean} props.fullscreen - Center in full viewport height
 * @param {boolean} props.inline - Display inline (for buttons)
 * @param {string} props.className - Additional CSS classes
 */
export function LoadingSpinner({
  size = 'md',
  text,
  fullscreen = false,
  inline = false,
  className = '',
}) {
  // Inline variant for buttons
  if (inline) {
    return (
      <>
        <style>{styles}</style>
        <span className={`btn-spinner ${className}`}>
          <span className={`loading-spinner ${size}`} />
        </span>
      </>
    );
  }

  return (
    <>
      <style>{styles}</style>
      <div className={`loading-spinner-container ${fullscreen ? 'fullscreen' : ''} ${className}`}>
        <div className={`loading-spinner ${size}`} />
        {text && <div className="loading-spinner-text">{text}</div>}
      </div>
    </>
  );
}

/**
 * Button loading spinner - smaller, inline variant
 */
export function ButtonSpinner({ size = 'sm', className = '' }) {
  return <LoadingSpinner size={size} inline className={className} />;
}

/**
 * Full page loading spinner
 */
export function PageSpinner({ text = 'Loading...' }) {
  return <LoadingSpinner size="lg" text={text} fullscreen />;
}

/**
 * Overlay spinner - covers parent element
 */
export function OverlaySpinner({ text }) {
  return (
    <>
      <style>{`
        .overlay-spinner {
          position: absolute;
          top: 0;
          left: 0;
          right: 0;
          bottom: 0;
          background: rgba(255, 255, 255, 0.8);
          display: flex;
          align-items: center;
          justify-content: center;
          z-index: 10;
          border-radius: inherit;
        }

        [data-theme="dark"] .overlay-spinner {
          background: rgba(0, 0, 0, 0.6);
        }
      `}</style>
      <div className="overlay-spinner">
        <LoadingSpinner size="md" text={text} />
      </div>
    </>
  );
}

export default LoadingSpinner;
