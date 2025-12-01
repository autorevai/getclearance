import React, { useEffect, useRef } from 'react';
import { AlertTriangle, X, Loader2 } from 'lucide-react';
import { useKeyboardShortcut } from '../../hooks/useKeyboardShortcut';

const styles = `
  .confirm-overlay {
    position: fixed;
    inset: 0;
    background: rgba(0, 0, 0, 0.6);
    backdrop-filter: blur(4px);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 10000;
    animation: fadeIn 0.15s ease;
  }

  @keyframes fadeIn {
    from { opacity: 0; }
    to { opacity: 1; }
  }

  @keyframes scaleIn {
    from {
      transform: scale(0.95);
      opacity: 0;
    }
    to {
      transform: scale(1);
      opacity: 1;
    }
  }

  .confirm-dialog {
    background: var(--bg-secondary);
    border: 1px solid var(--border-color);
    border-radius: 16px;
    width: 100%;
    max-width: 420px;
    animation: scaleIn 0.2s ease;
    overflow: hidden;
  }

  .confirm-header {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 20px 24px;
    border-bottom: 1px solid var(--border-color);
  }

  .confirm-icon {
    width: 40px;
    height: 40px;
    border-radius: 10px;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
  }

  .confirm-icon.danger {
    background: rgba(239, 68, 68, 0.15);
    color: var(--danger);
  }

  .confirm-icon.warning {
    background: rgba(245, 158, 11, 0.15);
    color: var(--warning);
  }

  .confirm-icon.info {
    background: rgba(59, 130, 246, 0.15);
    color: var(--info);
  }

  .confirm-title {
    flex: 1;
    font-size: 16px;
    font-weight: 600;
    color: var(--text-primary);
  }

  .confirm-close {
    width: 32px;
    height: 32px;
    border-radius: 8px;
    border: none;
    background: transparent;
    color: var(--text-muted);
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    transition: all 0.15s;
  }

  .confirm-close:hover {
    background: var(--bg-hover);
    color: var(--text-primary);
  }

  .confirm-body {
    padding: 20px 24px;
  }

  .confirm-message {
    font-size: 14px;
    color: var(--text-secondary);
    line-height: 1.6;
  }

  .confirm-footer {
    display: flex;
    justify-content: flex-end;
    gap: 12px;
    padding: 16px 24px;
    background: var(--bg-tertiary);
    border-top: 1px solid var(--border-color);
  }

  .confirm-btn {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 8px;
    padding: 10px 20px;
    border-radius: 8px;
    font-size: 14px;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.15s;
    border: none;
    font-family: inherit;
    min-width: 100px;
  }

  .confirm-btn:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }

  .confirm-btn-cancel {
    background: var(--bg-secondary);
    border: 1px solid var(--border-color);
    color: var(--text-primary);
  }

  .confirm-btn-cancel:hover:not(:disabled) {
    background: var(--bg-hover);
  }

  .confirm-btn-confirm {
    color: white;
  }

  .confirm-btn-confirm.danger {
    background: var(--danger);
  }

  .confirm-btn-confirm.warning {
    background: var(--warning);
  }

  .confirm-btn-confirm.primary {
    background: var(--accent-primary);
  }

  .confirm-btn-confirm.success {
    background: var(--success);
  }

  .confirm-btn-confirm:hover:not(:disabled) {
    opacity: 0.9;
  }

  .confirm-shortcut {
    font-size: 11px;
    padding: 2px 6px;
    background: rgba(255, 255, 255, 0.15);
    border-radius: 4px;
    margin-left: 4px;
  }

  @keyframes spin {
    from { transform: rotate(0deg); }
    to { transform: rotate(360deg); }
  }

  .spinner {
    animation: spin 1s linear infinite;
  }
`;

export default function ConfirmDialog({
  isOpen,
  title,
  message,
  confirmLabel = 'Confirm',
  cancelLabel = 'Cancel',
  variant = 'danger', // danger, warning, info, primary, success
  icon: CustomIcon,
  isLoading = false,
  onConfirm,
  onCancel,
}) {
  const confirmButtonRef = useRef(null);

  // Focus confirm button when dialog opens
  useEffect(() => {
    if (isOpen && confirmButtonRef.current) {
      confirmButtonRef.current.focus();
    }
  }, [isOpen]);

  // Escape to cancel
  useKeyboardShortcut('Escape', onCancel, { enabled: isOpen });

  // Enter to confirm
  useKeyboardShortcut('Enter', onConfirm, { enabled: isOpen && !isLoading });

  if (!isOpen) return null;

  const handleOverlayClick = (e) => {
    if (e.target === e.currentTarget && !isLoading) {
      onCancel();
    }
  };

  const Icon = CustomIcon || AlertTriangle;

  return (
    <>
      <style>{styles}</style>
      <div
        className="confirm-overlay"
        onClick={handleOverlayClick}
        role="dialog"
        aria-modal="true"
        aria-labelledby="confirm-title"
        aria-describedby="confirm-message"
      >
        <div className="confirm-dialog">
          <div className="confirm-header">
            <div className={`confirm-icon ${variant}`}>
              <Icon size={20} />
            </div>
            <h2 id="confirm-title" className="confirm-title">{title}</h2>
            <button
              className="confirm-close"
              onClick={onCancel}
              disabled={isLoading}
              aria-label="Close dialog"
            >
              <X size={18} />
            </button>
          </div>

          <div className="confirm-body">
            <p id="confirm-message" className="confirm-message">{message}</p>
          </div>

          <div className="confirm-footer">
            <button
              className="confirm-btn confirm-btn-cancel"
              onClick={onCancel}
              disabled={isLoading}
            >
              {cancelLabel}
              <span className="confirm-shortcut">Esc</span>
            </button>
            <button
              ref={confirmButtonRef}
              className={`confirm-btn confirm-btn-confirm ${variant}`}
              onClick={onConfirm}
              disabled={isLoading}
            >
              {isLoading ? (
                <>
                  <Loader2 size={16} className="spinner" />
                  Processing...
                </>
              ) : (
                <>
                  {confirmLabel}
                  <span className="confirm-shortcut">↵</span>
                </>
              )}
            </button>
          </div>
        </div>
      </div>
    </>
  );
}
