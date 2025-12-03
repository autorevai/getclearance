/**
 * Company Form Modal
 *
 * Create/Edit form for companies with sections for:
 * - Basic info (legal name, trading name, registration)
 * - Location (country, addresses)
 * - Contact (website, email, phone)
 * - Business info (industry, size)
 */

import React, { useState } from 'react';
import { X, Building2 } from 'lucide-react';

const LEGAL_FORMS = [
  { value: 'corporation', label: 'Corporation' },
  { value: 'llc', label: 'LLC' },
  { value: 'llp', label: 'LLP' },
  { value: 'partnership', label: 'Partnership' },
  { value: 'sole_proprietor', label: 'Sole Proprietor' },
  { value: 'nonprofit', label: 'Non-Profit' },
  { value: 'other', label: 'Other' },
];

const EMPLOYEE_RANGES = [
  { value: '1-10', label: '1-10' },
  { value: '11-50', label: '11-50' },
  { value: '51-200', label: '51-200' },
  { value: '201-500', label: '201-500' },
  { value: '501-1000', label: '501-1,000' },
  { value: '1001+', label: '1,000+' },
];

const REVENUE_RANGES = [
  { value: '<1M', label: 'Under $1M' },
  { value: '1-10M', label: '$1M - $10M' },
  { value: '10-50M', label: '$10M - $50M' },
  { value: '50-100M', label: '$50M - $100M' },
  { value: '100M+', label: 'Over $100M' },
];

export default function CompanyForm({ company, onSubmit, onClose, isSubmitting }) {
  const [formData, setFormData] = useState({
    legal_name: company?.legal_name || '',
    trading_name: company?.trading_name || '',
    registration_number: company?.registration_number || '',
    tax_id: company?.tax_id || '',
    incorporation_date: company?.incorporation_date || '',
    incorporation_country: company?.incorporation_country || '',
    legal_form: company?.legal_form || '',
    website: company?.website || '',
    email: company?.email || '',
    phone: company?.phone || '',
    industry: company?.industry || '',
    description: company?.description || '',
    employee_count: company?.employee_count || '',
    annual_revenue: company?.annual_revenue || '',
    external_id: company?.external_id || '',
    registered_address: company?.registered_address || {
      street: '',
      city: '',
      state: '',
      postal_code: '',
      country: '',
    },
    business_address: company?.business_address || null,
  });

  const [sameAddress, setSameAddress] = useState(true);
  const [errors, setErrors] = useState({});

  const handleChange = (field, value) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
    if (errors[field]) {
      setErrors((prev) => ({ ...prev, [field]: null }));
    }
  };

  const handleAddressChange = (type, field, value) => {
    setFormData((prev) => ({
      ...prev,
      [type]: { ...prev[type], [field]: value },
    }));
  };

  const validate = () => {
    const newErrors = {};
    if (!formData.legal_name.trim()) {
      newErrors.legal_name = 'Legal name is required';
    }
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!validate()) return;

    const submitData = { ...formData };

    // Clean up empty address
    if (
      !submitData.registered_address?.street &&
      !submitData.registered_address?.city
    ) {
      submitData.registered_address = null;
    }

    // Handle same address
    if (sameAddress) {
      submitData.business_address = null;
    } else if (
      !submitData.business_address?.street &&
      !submitData.business_address?.city
    ) {
      submitData.business_address = null;
    }

    // Remove empty strings
    Object.keys(submitData).forEach((key) => {
      if (submitData[key] === '') {
        submitData[key] = null;
      }
    });

    onSubmit(submitData);
  };

  return (
    <div className="modal-overlay">
      <style>{`
        .modal-overlay {
          position: fixed;
          top: 0;
          left: 0;
          right: 0;
          bottom: 0;
          background: rgba(0, 0, 0, 0.7);
          display: flex;
          align-items: center;
          justify-content: center;
          z-index: 1000;
          padding: 20px;
        }

        .modal-content {
          background: var(--bg-primary, #0a0b0e);
          border: 1px solid var(--border-primary, #23262f);
          border-radius: 12px;
          width: 100%;
          max-width: 700px;
          max-height: 90vh;
          display: flex;
          flex-direction: column;
        }

        .modal-header {
          display: flex;
          align-items: center;
          justify-content: space-between;
          padding: 20px 24px;
          border-bottom: 1px solid var(--border-primary, #23262f);
        }

        .modal-title {
          display: flex;
          align-items: center;
          gap: 12px;
          font-size: 18px;
          font-weight: 600;
          color: var(--text-primary, #f0f2f5);
          margin: 0;
        }

        .modal-title svg {
          width: 24px;
          height: 24px;
          color: var(--accent-primary, #6366f1);
        }

        .close-btn {
          padding: 8px;
          background: transparent;
          border: none;
          color: var(--text-secondary, #8b919e);
          cursor: pointer;
          border-radius: 6px;
          transition: all 0.15s;
        }

        .close-btn:hover {
          background: var(--bg-secondary, #111318);
          color: var(--text-primary, #f0f2f5);
        }

        .modal-body {
          padding: 24px;
          overflow-y: auto;
          flex: 1;
        }

        .form-section {
          margin-bottom: 24px;
        }

        .form-section:last-child {
          margin-bottom: 0;
        }

        .section-title {
          font-size: 14px;
          font-weight: 600;
          color: var(--text-primary, #f0f2f5);
          margin: 0 0 16px;
          padding-bottom: 8px;
          border-bottom: 1px solid var(--border-primary, #23262f);
        }

        .form-grid {
          display: grid;
          grid-template-columns: repeat(2, 1fr);
          gap: 16px;
        }

        .form-group {
          display: flex;
          flex-direction: column;
          gap: 6px;
        }

        .form-group.full-width {
          grid-column: 1 / -1;
        }

        .form-label {
          font-size: 13px;
          font-weight: 500;
          color: var(--text-secondary, #8b919e);
        }

        .form-label .required {
          color: var(--error, #ef4444);
          margin-left: 2px;
        }

        .form-input,
        .form-select,
        .form-textarea {
          padding: 10px 12px;
          background: var(--bg-secondary, #111318);
          border: 1px solid var(--border-primary, #23262f);
          border-radius: 8px;
          color: var(--text-primary, #f0f2f5);
          font-size: 14px;
          font-family: inherit;
          transition: border-color 0.15s;
        }

        .form-input:focus,
        .form-select:focus,
        .form-textarea:focus {
          outline: none;
          border-color: var(--accent-primary, #6366f1);
        }

        .form-input.error,
        .form-select.error {
          border-color: var(--error, #ef4444);
        }

        .form-error {
          font-size: 12px;
          color: var(--error, #ef4444);
        }

        .form-textarea {
          min-height: 80px;
          resize: vertical;
        }

        .checkbox-group {
          display: flex;
          align-items: center;
          gap: 8px;
          margin-top: 8px;
        }

        .checkbox-group input {
          width: 16px;
          height: 16px;
          cursor: pointer;
        }

        .checkbox-group label {
          font-size: 13px;
          color: var(--text-secondary, #8b919e);
          cursor: pointer;
        }

        .modal-footer {
          display: flex;
          justify-content: flex-end;
          gap: 12px;
          padding: 16px 24px;
          border-top: 1px solid var(--border-primary, #23262f);
        }

        .btn {
          padding: 10px 20px;
          border-radius: 8px;
          font-size: 14px;
          font-weight: 500;
          cursor: pointer;
          transition: all 0.15s;
          font-family: inherit;
          border: none;
        }

        .btn-secondary {
          background: var(--bg-secondary, #111318);
          color: var(--text-primary, #f0f2f5);
          border: 1px solid var(--border-primary, #23262f);
        }

        .btn-secondary:hover {
          background: var(--bg-tertiary, #1a1d24);
        }

        .btn-primary {
          background: var(--accent-primary, #6366f1);
          color: white;
        }

        .btn-primary:hover {
          background: var(--accent-hover, #5558e3);
        }

        .btn-primary:disabled {
          opacity: 0.6;
          cursor: not-allowed;
        }
      `}</style>

      <div className="modal-content">
        <div className="modal-header">
          <h2 className="modal-title">
            <Building2 />
            {company ? 'Edit Company' : 'Add Company'}
          </h2>
          <button className="close-btn" onClick={onClose}>
            <X size={20} />
          </button>
        </div>

        <form onSubmit={handleSubmit}>
          <div className="modal-body">
            {/* Basic Information */}
            <div className="form-section">
              <h3 className="section-title">Basic Information</h3>
              <div className="form-grid">
                <div className="form-group">
                  <label className="form-label">
                    Legal Name <span className="required">*</span>
                  </label>
                  <input
                    type="text"
                    className={`form-input ${errors.legal_name ? 'error' : ''}`}
                    value={formData.legal_name}
                    onChange={(e) => handleChange('legal_name', e.target.value)}
                    placeholder="Acme Corporation"
                  />
                  {errors.legal_name && (
                    <span className="form-error">{errors.legal_name}</span>
                  )}
                </div>
                <div className="form-group">
                  <label className="form-label">Trading Name (DBA)</label>
                  <input
                    type="text"
                    className="form-input"
                    value={formData.trading_name}
                    onChange={(e) => handleChange('trading_name', e.target.value)}
                    placeholder="Acme"
                  />
                </div>
                <div className="form-group">
                  <label className="form-label">Registration Number</label>
                  <input
                    type="text"
                    className="form-input"
                    value={formData.registration_number}
                    onChange={(e) =>
                      handleChange('registration_number', e.target.value)
                    }
                    placeholder="123456789"
                  />
                </div>
                <div className="form-group">
                  <label className="form-label">Tax ID</label>
                  <input
                    type="text"
                    className="form-input"
                    value={formData.tax_id}
                    onChange={(e) => handleChange('tax_id', e.target.value)}
                    placeholder="XX-XXXXXXX"
                  />
                </div>
                <div className="form-group">
                  <label className="form-label">Legal Form</label>
                  <select
                    className="form-select"
                    value={formData.legal_form}
                    onChange={(e) => handleChange('legal_form', e.target.value)}
                  >
                    <option value="">Select legal form</option>
                    {LEGAL_FORMS.map((form) => (
                      <option key={form.value} value={form.value}>
                        {form.label}
                      </option>
                    ))}
                  </select>
                </div>
                <div className="form-group">
                  <label className="form-label">Incorporation Date</label>
                  <input
                    type="date"
                    className="form-input"
                    value={formData.incorporation_date}
                    onChange={(e) =>
                      handleChange('incorporation_date', e.target.value)
                    }
                  />
                </div>
              </div>
            </div>

            {/* Location */}
            <div className="form-section">
              <h3 className="section-title">Location</h3>
              <div className="form-grid">
                <div className="form-group">
                  <label className="form-label">Country of Incorporation</label>
                  <input
                    type="text"
                    className="form-input"
                    value={formData.incorporation_country}
                    onChange={(e) =>
                      handleChange(
                        'incorporation_country',
                        e.target.value.toUpperCase().slice(0, 2)
                      )
                    }
                    placeholder="US"
                    maxLength={2}
                  />
                </div>
                <div className="form-group">
                  <label className="form-label">External ID</label>
                  <input
                    type="text"
                    className="form-input"
                    value={formData.external_id}
                    onChange={(e) => handleChange('external_id', e.target.value)}
                    placeholder="Your internal reference"
                  />
                </div>
              </div>

              <h4
                style={{
                  fontSize: 13,
                  color: 'var(--text-secondary)',
                  margin: '16px 0 12px',
                }}
              >
                Registered Address
              </h4>
              <div className="form-grid">
                <div className="form-group full-width">
                  <input
                    type="text"
                    className="form-input"
                    value={formData.registered_address?.street || ''}
                    onChange={(e) =>
                      handleAddressChange(
                        'registered_address',
                        'street',
                        e.target.value
                      )
                    }
                    placeholder="Street address"
                  />
                </div>
                <div className="form-group">
                  <input
                    type="text"
                    className="form-input"
                    value={formData.registered_address?.city || ''}
                    onChange={(e) =>
                      handleAddressChange(
                        'registered_address',
                        'city',
                        e.target.value
                      )
                    }
                    placeholder="City"
                  />
                </div>
                <div className="form-group">
                  <input
                    type="text"
                    className="form-input"
                    value={formData.registered_address?.state || ''}
                    onChange={(e) =>
                      handleAddressChange(
                        'registered_address',
                        'state',
                        e.target.value
                      )
                    }
                    placeholder="State/Province"
                  />
                </div>
                <div className="form-group">
                  <input
                    type="text"
                    className="form-input"
                    value={formData.registered_address?.postal_code || ''}
                    onChange={(e) =>
                      handleAddressChange(
                        'registered_address',
                        'postal_code',
                        e.target.value
                      )
                    }
                    placeholder="Postal code"
                  />
                </div>
                <div className="form-group">
                  <input
                    type="text"
                    className="form-input"
                    value={formData.registered_address?.country || ''}
                    onChange={(e) =>
                      handleAddressChange(
                        'registered_address',
                        'country',
                        e.target.value.toUpperCase().slice(0, 2)
                      )
                    }
                    placeholder="Country (e.g., US)"
                    maxLength={2}
                  />
                </div>
              </div>

              <div className="checkbox-group">
                <input
                  type="checkbox"
                  id="sameAddress"
                  checked={sameAddress}
                  onChange={(e) => setSameAddress(e.target.checked)}
                />
                <label htmlFor="sameAddress">
                  Business address same as registered address
                </label>
              </div>
            </div>

            {/* Contact */}
            <div className="form-section">
              <h3 className="section-title">Contact Information</h3>
              <div className="form-grid">
                <div className="form-group">
                  <label className="form-label">Website</label>
                  <input
                    type="url"
                    className="form-input"
                    value={formData.website}
                    onChange={(e) => handleChange('website', e.target.value)}
                    placeholder="https://example.com"
                  />
                </div>
                <div className="form-group">
                  <label className="form-label">Email</label>
                  <input
                    type="email"
                    className="form-input"
                    value={formData.email}
                    onChange={(e) => handleChange('email', e.target.value)}
                    placeholder="contact@example.com"
                  />
                </div>
                <div className="form-group">
                  <label className="form-label">Phone</label>
                  <input
                    type="tel"
                    className="form-input"
                    value={formData.phone}
                    onChange={(e) => handleChange('phone', e.target.value)}
                    placeholder="+1 555 123 4567"
                  />
                </div>
              </div>
            </div>

            {/* Business Info */}
            <div className="form-section">
              <h3 className="section-title">Business Details</h3>
              <div className="form-grid">
                <div className="form-group">
                  <label className="form-label">Industry</label>
                  <input
                    type="text"
                    className="form-input"
                    value={formData.industry}
                    onChange={(e) => handleChange('industry', e.target.value)}
                    placeholder="Technology, Finance, etc."
                  />
                </div>
                <div className="form-group">
                  <label className="form-label">Employee Count</label>
                  <select
                    className="form-select"
                    value={formData.employee_count}
                    onChange={(e) =>
                      handleChange('employee_count', e.target.value)
                    }
                  >
                    <option value="">Select range</option>
                    {EMPLOYEE_RANGES.map((range) => (
                      <option key={range.value} value={range.value}>
                        {range.label}
                      </option>
                    ))}
                  </select>
                </div>
                <div className="form-group">
                  <label className="form-label">Annual Revenue</label>
                  <select
                    className="form-select"
                    value={formData.annual_revenue}
                    onChange={(e) =>
                      handleChange('annual_revenue', e.target.value)
                    }
                  >
                    <option value="">Select range</option>
                    {REVENUE_RANGES.map((range) => (
                      <option key={range.value} value={range.value}>
                        {range.label}
                      </option>
                    ))}
                  </select>
                </div>
                <div className="form-group full-width">
                  <label className="form-label">Description</label>
                  <textarea
                    className="form-textarea"
                    value={formData.description}
                    onChange={(e) => handleChange('description', e.target.value)}
                    placeholder="Brief description of the company's business activities..."
                  />
                </div>
              </div>
            </div>
          </div>

          <div className="modal-footer">
            <button type="button" className="btn btn-secondary" onClick={onClose}>
              Cancel
            </button>
            <button
              type="submit"
              className="btn btn-primary"
              disabled={isSubmitting}
            >
              {isSubmitting
                ? 'Saving...'
                : company
                ? 'Save Changes'
                : 'Add Company'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
