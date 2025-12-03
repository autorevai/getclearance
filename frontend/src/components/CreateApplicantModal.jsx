import React, { useState, useRef } from 'react';
import { X, User, Mail, Calendar, Globe, Loader2, AlertCircle } from 'lucide-react';
import { useCreateApplicant } from '../hooks/useApplicants';
import { useFocusTrap } from '../hooks/useFocusTrap';

const styles = `
  .modal-overlay {
    position: fixed;
    inset: 0;
    background: rgba(0, 0, 0, 0.6);
    backdrop-filter: blur(4px);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 1000;
    animation: fadeIn 0.15s ease;
  }

  @keyframes fadeIn {
    from { opacity: 0; }
    to { opacity: 1; }
  }

  @keyframes slideUp {
    from { transform: translateY(20px); opacity: 0; }
    to { transform: translateY(0); opacity: 1; }
  }

  .modal {
    background: var(--bg-secondary);
    border: 1px solid var(--border-color);
    border-radius: 16px;
    width: 100%;
    max-width: 520px;
    max-height: 90vh;
    overflow: hidden;
    animation: slideUp 0.2s ease;
  }

  .modal-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 20px 24px;
    border-bottom: 1px solid var(--border-color);
  }

  .modal-title {
    font-size: 18px;
    font-weight: 600;
  }

  .modal-close {
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

  .modal-close:hover {
    background: var(--bg-hover);
    color: var(--text-primary);
  }

  .modal-body {
    padding: 24px;
    overflow-y: auto;
  }

  .form-group {
    margin-bottom: 20px;
  }

  .form-label {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 14px;
    font-weight: 500;
    margin-bottom: 8px;
    color: var(--text-primary);
  }

  .form-label .required {
    color: var(--danger);
  }

  .form-input {
    width: 100%;
    height: 44px;
    background: var(--bg-tertiary);
    border: 1px solid var(--border-color);
    border-radius: 8px;
    padding: 0 14px;
    font-size: 14px;
    color: var(--text-primary);
    outline: none;
    transition: border-color 0.15s;
  }

  .form-input:focus {
    border-color: var(--accent-primary);
  }

  .form-input::placeholder {
    color: var(--text-muted);
  }

  .form-input.error {
    border-color: var(--danger);
  }

  .form-row {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 16px;
  }

  .form-error {
    display: flex;
    align-items: center;
    gap: 6px;
    font-size: 13px;
    color: var(--danger);
    margin-top: 6px;
  }

  .modal-footer {
    display: flex;
    justify-content: flex-end;
    gap: 12px;
    padding: 20px 24px;
    border-top: 1px solid var(--border-color);
    background: var(--bg-tertiary);
  }

  .btn {
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

  .btn:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }

  .btn-secondary {
    background: var(--bg-secondary);
    border: 1px solid var(--border-color);
    color: var(--text-primary);
  }

  .btn-secondary:hover:not(:disabled) {
    background: var(--bg-hover);
  }

  .btn-primary {
    background: var(--accent-primary);
    color: white;
  }

  .btn-primary:hover:not(:disabled) {
    opacity: 0.9;
  }

  .alert {
    display: flex;
    align-items: flex-start;
    gap: 12px;
    padding: 14px 16px;
    border-radius: 8px;
    margin-bottom: 20px;
    font-size: 14px;
    line-height: 1.5;
  }

  .alert-error {
    background: rgba(239, 68, 68, 0.1);
    border: 1px solid rgba(239, 68, 68, 0.3);
    color: var(--danger);
  }

  .alert-icon {
    flex-shrink: 0;
    margin-top: 2px;
  }

  @keyframes spin {
    from { transform: rotate(0deg); }
    to { transform: rotate(360deg); }
  }

  .spinner {
    animation: spin 1s linear infinite;
  }
`;

export default function CreateApplicantModal({ onClose, onSuccess, triggerRef }) {
  const createApplicant = useCreateApplicant();
  const emailInputRef = useRef(null);

  // Focus trap with Escape to close and return focus to trigger
  const focusTrapRef = useFocusTrap(true, {
    initialFocus: emailInputRef.current,
    onEscape: createApplicant.isPending ? undefined : onClose,
    returnFocus: triggerRef?.current,
  });

  const [formData, setFormData] = useState({
    email: '',
    first_name: '',
    last_name: '',
    date_of_birth: '',
    nationality: '',
    phone: '',
  });

  const [errors, setErrors] = useState({});

  const validateForm = () => {
    const newErrors = {};

    if (!formData.email) {
      newErrors.email = 'Email is required';
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email)) {
      newErrors.email = 'Please enter a valid email address';
    }

    if (!formData.first_name) {
      newErrors.first_name = 'First name is required';
    }

    if (!formData.last_name) {
      newErrors.last_name = 'Last name is required';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
    // Clear error when user starts typing
    if (errors[name]) {
      setErrors(prev => ({ ...prev, [name]: null }));
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!validateForm()) return;

    // Build the payload, only including non-empty fields
    const payload = {
      email: formData.email,
      first_name: formData.first_name,
      last_name: formData.last_name,
      external_id: `ext_${Date.now()}_${Math.random().toString(36).slice(2, 9)}`,
    };

    if (formData.date_of_birth) {
      payload.date_of_birth = formData.date_of_birth;
    }
    if (formData.nationality) {
      payload.nationality = formData.nationality;
    }
    if (formData.phone) {
      payload.phone = formData.phone;
    }

    try {
      await createApplicant.mutateAsync(payload);
      onSuccess?.();
    } catch (error) {
      // Error is handled by the mutation state
      console.error('Failed to create applicant:', error);
    }
  };

  const handleOverlayClick = (e) => {
    if (e.target === e.currentTarget && !createApplicant.isPending) {
      onClose();
    }
  };

  return (
    <>
      <style>{styles}</style>
      <div
        className="modal-overlay"
        onClick={handleOverlayClick}
        role="dialog"
        aria-modal="true"
        aria-labelledby="modal-title"
      >
        <div className="modal" ref={focusTrapRef}>
          <div className="modal-header">
            <h2 id="modal-title" className="modal-title">Create New Applicant</h2>
            <button className="modal-close" onClick={onClose} disabled={createApplicant.isPending} aria-label="Close modal">
              <X size={18} />
            </button>
          </div>

          <form onSubmit={handleSubmit}>
            <div className="modal-body">
              {createApplicant.error && (
                <div className="alert alert-error">
                  <AlertCircle size={18} className="alert-icon" />
                  <div>
                    <strong>Failed to create applicant</strong>
                    <p style={{ margin: '4px 0 0' }}>
                      {createApplicant.error?.message || 'An unexpected error occurred. Please try again.'}
                    </p>
                  </div>
                </div>
              )}

              <div className="form-group">
                <label className="form-label">
                  <Mail size={16} />
                  Email <span className="required">*</span>
                </label>
                <input
                  ref={emailInputRef}
                  type="email"
                  name="email"
                  className={`form-input ${errors.email ? 'error' : ''}`}
                  placeholder="applicant@example.com"
                  value={formData.email}
                  onChange={handleChange}
                />
                {errors.email && (
                  <div className="form-error">
                    <AlertCircle size={14} />
                    {errors.email}
                  </div>
                )}
              </div>

              <div className="form-row">
                <div className="form-group">
                  <label className="form-label">
                    <User size={16} />
                    First Name <span className="required">*</span>
                  </label>
                  <input
                    type="text"
                    name="first_name"
                    className={`form-input ${errors.first_name ? 'error' : ''}`}
                    placeholder="John"
                    value={formData.first_name}
                    onChange={handleChange}
                  />
                  {errors.first_name && (
                    <div className="form-error">
                      <AlertCircle size={14} />
                      {errors.first_name}
                    </div>
                  )}
                </div>

                <div className="form-group">
                  <label className="form-label">
                    <User size={16} />
                    Last Name <span className="required">*</span>
                  </label>
                  <input
                    type="text"
                    name="last_name"
                    className={`form-input ${errors.last_name ? 'error' : ''}`}
                    placeholder="Doe"
                    value={formData.last_name}
                    onChange={handleChange}
                  />
                  {errors.last_name && (
                    <div className="form-error">
                      <AlertCircle size={14} />
                      {errors.last_name}
                    </div>
                  )}
                </div>
              </div>

              <div className="form-row">
                <div className="form-group">
                  <label className="form-label">
                    <Calendar size={16} />
                    Date of Birth
                  </label>
                  <input
                    type="date"
                    name="date_of_birth"
                    className="form-input"
                    value={formData.date_of_birth}
                    onChange={handleChange}
                    max={new Date().toISOString().split('T')[0]}
                  />
                </div>

                <div className="form-group">
                  <label className="form-label">
                    <Globe size={16} />
                    Nationality
                  </label>
                  <input
                    type="text"
                    name="nationality"
                    className="form-input"
                    placeholder="e.g. US, GB, DE"
                    value={formData.nationality}
                    onChange={handleChange}
                    maxLength={2}
                    style={{ textTransform: 'uppercase' }}
                  />
                </div>
              </div>

              <div className="form-group" style={{ marginBottom: 0 }}>
                <label className="form-label">
                  Phone Number
                </label>
                <input
                  type="tel"
                  name="phone"
                  className="form-input"
                  placeholder="+1 (555) 123-4567"
                  value={formData.phone}
                  onChange={handleChange}
                />
              </div>
            </div>

            <div className="modal-footer">
              <button
                type="button"
                className="btn btn-secondary"
                onClick={onClose}
                disabled={createApplicant.isPending}
              >
                Cancel
              </button>
              <button
                type="submit"
                className="btn btn-primary"
                disabled={createApplicant.isPending}
              >
                {createApplicant.isPending ? (
                  <>
                    <Loader2 size={16} className="spinner" />
                    Creating...
                  </>
                ) : (
                  'Create Applicant'
                )}
              </button>
            </div>
          </form>
        </div>
      </div>
    </>
  );
}
