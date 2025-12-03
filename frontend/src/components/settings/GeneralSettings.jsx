import React, { useState, useEffect } from 'react';
import { Building2, Globe, Calendar, Check, Loader2 } from 'lucide-react';
import { useSettings, useUpdateGeneralSettings } from '../../hooks';

const timezones = [
  { value: 'America/New_York', label: 'Eastern Time (ET)' },
  { value: 'America/Chicago', label: 'Central Time (CT)' },
  { value: 'America/Denver', label: 'Mountain Time (MT)' },
  { value: 'America/Los_Angeles', label: 'Pacific Time (PT)' },
  { value: 'America/Anchorage', label: 'Alaska Time' },
  { value: 'Pacific/Honolulu', label: 'Hawaii Time' },
  { value: 'UTC', label: 'UTC' },
  { value: 'Europe/London', label: 'London (GMT/BST)' },
  { value: 'Europe/Paris', label: 'Paris (CET/CEST)' },
  { value: 'Europe/Berlin', label: 'Berlin (CET/CEST)' },
  { value: 'Asia/Tokyo', label: 'Tokyo (JST)' },
  { value: 'Asia/Shanghai', label: 'Shanghai (CST)' },
  { value: 'Asia/Singapore', label: 'Singapore (SGT)' },
  { value: 'Australia/Sydney', label: 'Sydney (AEST/AEDT)' },
];

const dateFormats = [
  { value: 'MM/DD/YYYY', label: 'MM/DD/YYYY (US)' },
  { value: 'DD/MM/YYYY', label: 'DD/MM/YYYY (EU)' },
  { value: 'YYYY-MM-DD', label: 'YYYY-MM-DD (ISO)' },
];

const languages = [
  { value: 'en', label: 'English' },
  { value: 'es', label: 'Spanish' },
  { value: 'fr', label: 'French' },
  { value: 'de', label: 'German' },
  { value: 'pt', label: 'Portuguese' },
];

export default function GeneralSettings() {
  const { data: settings, isLoading } = useSettings();
  const updateSettings = useUpdateGeneralSettings();

  const [formData, setFormData] = useState({
    company_name: '',
    timezone: 'America/New_York',
    date_format: 'MM/DD/YYYY',
    language: 'en',
  });
  const [saveSuccess, setSaveSuccess] = useState(false);

  // Initialize form from settings
  useEffect(() => {
    if (settings?.general) {
      setFormData({
        company_name: settings.general.company_name?.value || settings.general.company_name || '',
        timezone: settings.general.timezone?.value || 'America/New_York',
        date_format: settings.general.date_format?.value || 'MM/DD/YYYY',
        language: settings.general.language?.value || 'en',
      });
    }
  }, [settings]);

  const handleChange = (field, value) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
    setSaveSuccess(false);
  };

  const handleSave = async () => {
    try {
      await updateSettings.mutateAsync(formData);
      setSaveSuccess(true);
      setTimeout(() => setSaveSuccess(false), 3000);
    } catch (error) {
      console.error('Failed to save settings:', error);
    }
  };

  if (isLoading) {
    return (
      <div className="settings-loading">
        <Loader2 className="spinner" />
        <span>Loading settings...</span>
      </div>
    );
  }

  return (
    <div className="general-settings">
      <style>{`
        .general-settings h2 {
          font-size: 18px;
          font-weight: 600;
          color: var(--text-primary, #f0f2f5);
          margin: 0 0 8px;
          display: flex;
          align-items: center;
          gap: 8px;
        }

        .general-settings h2 svg {
          width: 20px;
          height: 20px;
          color: var(--accent-primary, #6366f1);
        }

        .section-description {
          font-size: 14px;
          color: var(--text-secondary, #8b919e);
          margin-bottom: 24px;
        }

        .form-group {
          margin-bottom: 20px;
        }

        .form-label {
          display: block;
          font-size: 14px;
          font-weight: 500;
          color: var(--text-primary, #f0f2f5);
          margin-bottom: 8px;
        }

        .form-input,
        .form-select {
          width: 100%;
          max-width: 400px;
          height: 42px;
          padding: 0 14px;
          background: var(--bg-tertiary, #1a1d24);
          border: 1px solid var(--border-color, #2a2f3a);
          border-radius: 8px;
          color: var(--text-primary, #f0f2f5);
          font-size: 14px;
          font-family: inherit;
          transition: border-color 0.2s;
        }

        .form-input:focus,
        .form-select:focus {
          outline: none;
          border-color: var(--accent-primary, #6366f1);
          box-shadow: 0 0 0 3px var(--accent-glow, rgba(99, 102, 241, 0.15));
        }

        .form-select {
          cursor: pointer;
          appearance: none;
          background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='16' height='16' viewBox='0 0 24 24' fill='none' stroke='%238b919e' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpolyline points='6 9 12 15 18 9'%3E%3C/polyline%3E%3C/svg%3E");
          background-repeat: no-repeat;
          background-position: right 12px center;
          padding-right: 40px;
        }

        .form-hint {
          font-size: 12px;
          color: var(--text-muted, #5c6370);
          margin-top: 6px;
        }

        .save-button {
          display: inline-flex;
          align-items: center;
          gap: 8px;
          padding: 10px 20px;
          background: var(--accent-primary, #6366f1);
          color: white;
          border: none;
          border-radius: 8px;
          font-size: 14px;
          font-weight: 500;
          cursor: pointer;
          transition: opacity 0.2s;
          font-family: inherit;
          margin-top: 8px;
        }

        .save-button:hover:not(:disabled) {
          opacity: 0.9;
        }

        .save-button:disabled {
          opacity: 0.6;
          cursor: not-allowed;
        }

        .save-button.success {
          background: var(--success, #10b981);
        }

        .save-button svg {
          width: 16px;
          height: 16px;
        }

        .spinner {
          animation: spin 1s linear infinite;
        }

        @keyframes spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }

        .settings-loading {
          display: flex;
          align-items: center;
          justify-content: center;
          gap: 12px;
          padding: 40px;
          color: var(--text-secondary, #8b919e);
        }

        .settings-loading .spinner {
          width: 20px;
          height: 20px;
        }
      `}</style>

      <h2>
        <Building2 />
        General Settings
      </h2>
      <p className="section-description">
        Configure your organization's basic information and preferences.
      </p>

      <div className="form-group">
        <label className="form-label">Company Name</label>
        <input
          type="text"
          className="form-input"
          value={formData.company_name}
          onChange={(e) => handleChange('company_name', e.target.value)}
          placeholder="Enter your company name"
        />
        <p className="form-hint">This name appears in reports and communications.</p>
      </div>

      <div className="form-group">
        <label className="form-label">
          <Globe className="inline-icon" style={{ width: 14, height: 14, marginRight: 6 }} />
          Timezone
        </label>
        <select
          className="form-select"
          value={formData.timezone}
          onChange={(e) => handleChange('timezone', e.target.value)}
        >
          {timezones.map((tz) => (
            <option key={tz.value} value={tz.value}>
              {tz.label}
            </option>
          ))}
        </select>
        <p className="form-hint">All timestamps will be displayed in this timezone.</p>
      </div>

      <div className="form-group">
        <label className="form-label">
          <Calendar className="inline-icon" style={{ width: 14, height: 14, marginRight: 6 }} />
          Date Format
        </label>
        <select
          className="form-select"
          value={formData.date_format}
          onChange={(e) => handleChange('date_format', e.target.value)}
        >
          {dateFormats.map((df) => (
            <option key={df.value} value={df.value}>
              {df.label}
            </option>
          ))}
        </select>
      </div>

      <div className="form-group">
        <label className="form-label">Language</label>
        <select
          className="form-select"
          value={formData.language}
          onChange={(e) => handleChange('language', e.target.value)}
        >
          {languages.map((lang) => (
            <option key={lang.value} value={lang.value}>
              {lang.label}
            </option>
          ))}
        </select>
        <p className="form-hint">Interface language for all users in your organization.</p>
      </div>

      <button
        className={`save-button ${saveSuccess ? 'success' : ''}`}
        onClick={handleSave}
        disabled={updateSettings.isPending}
      >
        {updateSettings.isPending ? (
          <>
            <Loader2 className="spinner" />
            Saving...
          </>
        ) : saveSuccess ? (
          <>
            <Check />
            Saved!
          </>
        ) : (
          'Save Changes'
        )}
      </button>
    </div>
  );
}
