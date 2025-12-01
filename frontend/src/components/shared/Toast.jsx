import React, { useState, useEffect } from 'react';
import { CheckCircle2, XCircle, AlertTriangle, Info, X } from 'lucide-react';

const styles = `
  @keyframes slideIn {
    from {
      transform: translateX(100%);
      opacity: 0;
    }
    to {
      transform: translateX(0);
      opacity: 1;
    }
  }

  @keyframes slideOut {
    from {
      transform: translateX(0);
      opacity: 1;
    }
    to {
      transform: translateX(100%);
      opacity: 0;
    }
  }

  .toast {
    display: flex;
    align-items: flex-start;
    gap: 12px;
    padding: 14px 16px;
    background: var(--bg-secondary);
    border: 1px solid var(--border-color);
    border-radius: 12px;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
    animation: slideIn 0.25s ease-out;
    min-width: 300px;
    max-width: 400px;
  }

  .toast.exiting {
    animation: slideOut 0.2s ease-in forwards;
  }

  .toast-icon {
    flex-shrink: 0;
    margin-top: 2px;
  }

  .toast-icon.success { color: var(--success); }
  .toast-icon.error { color: var(--danger); }
  .toast-icon.warning { color: var(--warning); }
  .toast-icon.info { color: var(--info); }

  .toast-content {
    flex: 1;
    min-width: 0;
  }

  .toast-message {
    font-size: 14px;
    color: var(--text-primary);
    line-height: 1.5;
    word-wrap: break-word;
  }

  .toast-action {
    margin-top: 8px;
  }

  .toast-action-btn {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    padding: 6px 12px;
    background: var(--bg-tertiary);
    border: 1px solid var(--border-color);
    border-radius: 6px;
    font-size: 13px;
    font-weight: 500;
    color: var(--text-primary);
    cursor: pointer;
    transition: all 0.15s;
  }

  .toast-action-btn:hover {
    background: var(--bg-hover);
  }

  .toast-close {
    flex-shrink: 0;
    width: 24px;
    height: 24px;
    border-radius: 6px;
    border: none;
    background: transparent;
    color: var(--text-muted);
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    transition: all 0.15s;
    margin: -4px -4px -4px 0;
  }

  .toast-close:hover {
    background: var(--bg-hover);
    color: var(--text-primary);
  }

  .toast-progress {
    position: absolute;
    bottom: 0;
    left: 0;
    right: 0;
    height: 3px;
    background: var(--bg-tertiary);
    border-radius: 0 0 12px 12px;
    overflow: hidden;
  }

  .toast-progress-bar {
    height: 100%;
    transition: width linear;
  }

  .toast-progress-bar.success { background: var(--success); }
  .toast-progress-bar.error { background: var(--danger); }
  .toast-progress-bar.warning { background: var(--warning); }
  .toast-progress-bar.info { background: var(--info); }
`;

const icons = {
  success: CheckCircle2,
  error: XCircle,
  warning: AlertTriangle,
  info: Info,
};

export default function Toast({ toast, onClose }) {
  const [exiting, setExiting] = useState(false);
  const [progress, setProgress] = useState(100);

  const Icon = icons[toast.type] || Info;

  useEffect(() => {
    if (toast.duration > 0) {
      const startTime = Date.now();
      const interval = setInterval(() => {
        const elapsed = Date.now() - startTime;
        const remaining = Math.max(0, 100 - (elapsed / toast.duration) * 100);
        setProgress(remaining);
      }, 50);

      return () => clearInterval(interval);
    }
  }, [toast.duration]);

  const handleClose = () => {
    setExiting(true);
    setTimeout(onClose, 200);
  };

  return (
    <>
      <style>{styles}</style>
      <div
        className={`toast ${exiting ? 'exiting' : ''}`}
        role="alert"
        aria-live="assertive"
        style={{ position: 'relative' }}
      >
        <Icon size={20} className={`toast-icon ${toast.type}`} />

        <div className="toast-content">
          <div className="toast-message">{toast.message}</div>
          {toast.action && (
            <div className="toast-action">
              <button
                className="toast-action-btn"
                onClick={() => {
                  toast.action.onClick();
                  handleClose();
                }}
              >
                {toast.action.label}
              </button>
            </div>
          )}
        </div>

        <button
          className="toast-close"
          onClick={handleClose}
          aria-label="Dismiss notification"
        >
          <X size={16} />
        </button>

        {toast.duration > 0 && (
          <div className="toast-progress">
            <div
              className={`toast-progress-bar ${toast.type}`}
              style={{ width: `${progress}%` }}
            />
          </div>
        )}
      </div>
    </>
  );
}
