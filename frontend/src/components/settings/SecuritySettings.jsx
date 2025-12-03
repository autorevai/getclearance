import React, { useState, useEffect } from 'react';
import { Shield, Clock, Key, Lock, Check, Loader2, AlertTriangle } from 'lucide-react';
import { useSecuritySettings, useUpdateSecuritySettings } from '../../hooks';

function ToggleSwitch({ enabled, onChange, disabled }) {
  return (
    <button
      type="button"
      role="switch"
      aria-checked={enabled}
      className={`toggle-switch ${enabled ? 'enabled' : ''}`}
      onClick={() => onChange(!enabled)}
      disabled={disabled}
    >
      <span className="toggle-thumb" />
    </button>
  );
}

export default function SecuritySettings() {
  const { data: settings, isLoading, error } = useSecuritySettings();
  const updateSettings = useUpdateSecuritySettings();

  const [formData, setFormData] = useState({
    session_timeout_minutes: 60,
    require_2fa: false,
    password_min_length: 12,
    password_require_uppercase: true,
    password_require_number: true,
    password_require_special: true,
    allowed_ip_ranges: [],
  });
  const [ipInput, setIpInput] = useState('');
  const [saveSuccess, setSaveSuccess] = useState(false);

  // Initialize from server data
  useEffect(() => {
    if (settings) {
      setFormData(settings);
    }
  }, [settings]);

  const handleChange = (field, value) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
    setSaveSuccess(false);
  };

  const handleAddIpRange = () => {
    if (ipInput && !formData.allowed_ip_ranges.includes(ipInput)) {
      setFormData((prev) => ({
        ...prev,
        allowed_ip_ranges: [...prev.allowed_ip_ranges, ipInput],
      }));
      setIpInput('');
      setSaveSuccess(false);
    }
  };

  const handleRemoveIpRange = (ip) => {
    setFormData((prev) => ({
      ...prev,
      allowed_ip_ranges: prev.allowed_ip_ranges.filter((r) => r !== ip),
    }));
    setSaveSuccess(false);
  };

  const handleSave = async () => {
    try {
      await updateSettings.mutateAsync(formData);
      setSaveSuccess(true);
      setTimeout(() => setSaveSuccess(false), 3000);
    } catch (err) {
      console.error('Failed to save security settings:', err);
    }
  };

  if (isLoading) {
    return (
      <div className="settings-loading">
        <Loader2 className="spinner" />
        <span>Loading security settings...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="settings-error">
        <AlertTriangle />
        <span>You need admin privileges to view security settings.</span>
      </div>
    );
  }

  return (
    <div className="security-settings">
      <style>{`
        .security-settings h2 {
          font-size: 18px;
          font-weight: 600;
          color: var(--text-primary, #f0f2f5);
          margin: 0 0 8px;
          display: flex;
          align-items: center;
          gap: 8px;
        }

        .security-settings h2 svg {
          width: 20px;
          height: 20px;
          color: var(--accent-primary, #6366f1);
        }

        .section-description {
          font-size: 14px;
          color: var(--text-secondary, #8b919e);
          margin-bottom: 24px;
        }

        .admin-notice {
          display: flex;
          align-items: center;
          gap: 8px;
          padding: 12px 16px;
          background: rgba(245, 158, 11, 0.1);
          border: 1px solid rgba(245, 158, 11, 0.3);
          border-radius: 8px;
          margin-bottom: 24px;
          font-size: 13px;
          color: var(--warning, #f59e0b);
        }

        .admin-notice svg {
          width: 16px;
          height: 16px;
          flex-shrink: 0;
        }

        .settings-section {
          margin-bottom: 32px;
          padding-bottom: 24px;
          border-bottom: 1px solid var(--border-color, #2a2f3a);
        }

        .settings-section:last-of-type {
          border-bottom: none;
          margin-bottom: 0;
        }

        .section-title {
          display: flex;
          align-items: center;
          gap: 8px;
          font-size: 14px;
          font-weight: 600;
          color: var(--text-primary, #f0f2f5);
          margin-bottom: 16px;
        }

        .section-title svg {
          width: 16px;
          height: 16px;
          color: var(--text-muted, #5c6370);
        }

        .setting-row {
          display: flex;
          align-items: center;
          justify-content: space-between;
          padding: 16px;
          background: var(--bg-tertiary, #1a1d24);
          border-radius: 10px;
          border: 1px solid var(--border-color, #2a2f3a);
          margin-bottom: 12px;
        }

        .setting-info {
          flex: 1;
          min-width: 0;
        }

        .setting-label {
          font-size: 14px;
          font-weight: 500;
          color: var(--text-primary, #f0f2f5);
          margin-bottom: 4px;
        }

        .setting-description {
          font-size: 13px;
          color: var(--text-secondary, #8b919e);
        }

        .toggle-switch {
          position: relative;
          width: 44px;
          height: 24px;
          background: var(--bg-hover, #22262f);
          border: none;
          border-radius: 12px;
          cursor: pointer;
          transition: background 0.2s;
          flex-shrink: 0;
          margin-left: 16px;
        }

        .toggle-switch:disabled {
          opacity: 0.5;
          cursor: not-allowed;
        }

        .toggle-switch.enabled {
          background: var(--accent-primary, #6366f1);
        }

        .toggle-thumb {
          position: absolute;
          top: 2px;
          left: 2px;
          width: 20px;
          height: 20px;
          background: white;
          border-radius: 50%;
          transition: transform 0.2s;
          box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
        }

        .toggle-switch.enabled .toggle-thumb {
          transform: translateX(20px);
        }

        .setting-input {
          width: 100px;
          height: 36px;
          padding: 0 12px;
          background: var(--bg-secondary, #111318);
          border: 1px solid var(--border-color, #2a2f3a);
          border-radius: 6px;
          color: var(--text-primary, #f0f2f5);
          font-size: 14px;
          text-align: center;
          font-family: inherit;
        }

        .setting-input:focus {
          outline: none;
          border-color: var(--accent-primary, #6366f1);
        }

        .ip-range-section {
          margin-top: 12px;
        }

        .ip-input-row {
          display: flex;
          gap: 8px;
          margin-bottom: 12px;
        }

        .ip-input {
          flex: 1;
          height: 40px;
          padding: 0 14px;
          background: var(--bg-tertiary, #1a1d24);
          border: 1px solid var(--border-color, #2a2f3a);
          border-radius: 8px;
          color: var(--text-primary, #f0f2f5);
          font-size: 14px;
          font-family: inherit;
        }

        .ip-input:focus {
          outline: none;
          border-color: var(--accent-primary, #6366f1);
        }

        .add-ip-btn {
          padding: 0 16px;
          background: var(--bg-tertiary, #1a1d24);
          border: 1px solid var(--border-color, #2a2f3a);
          border-radius: 8px;
          color: var(--text-primary, #f0f2f5);
          font-size: 14px;
          cursor: pointer;
          font-family: inherit;
          transition: all 0.15s;
        }

        .add-ip-btn:hover {
          background: var(--bg-hover, #22262f);
          border-color: var(--accent-primary, #6366f1);
        }

        .ip-tags {
          display: flex;
          flex-wrap: wrap;
          gap: 8px;
        }

        .ip-tag {
          display: inline-flex;
          align-items: center;
          gap: 6px;
          padding: 6px 10px;
          background: var(--bg-tertiary, #1a1d24);
          border-radius: 6px;
          font-size: 13px;
          color: var(--text-primary, #f0f2f5);
          font-family: monospace;
        }

        .ip-tag button {
          background: none;
          border: none;
          color: var(--text-muted, #5c6370);
          cursor: pointer;
          padding: 0;
          display: flex;
          transition: color 0.15s;
        }

        .ip-tag button:hover {
          color: var(--danger, #ef4444);
        }

        .ip-empty {
          font-size: 13px;
          color: var(--text-muted, #5c6370);
          font-style: italic;
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

        .settings-loading,
        .settings-error {
          display: flex;
          align-items: center;
          justify-content: center;
          gap: 12px;
          padding: 40px;
          color: var(--text-secondary, #8b919e);
        }

        .settings-error {
          color: var(--warning, #f59e0b);
        }

        .settings-loading .spinner,
        .settings-error svg {
          width: 20px;
          height: 20px;
        }
      `}</style>

      <h2>
        <Shield />
        Security Settings
      </h2>
      <p className="section-description">
        Configure security policies for your organization.
      </p>

      <div className="admin-notice">
        <AlertTriangle />
        Changes to security settings affect all users in your organization.
      </div>

      {/* Session Settings */}
      <div className="settings-section">
        <div className="section-title">
          <Clock />
          Session Settings
        </div>

        <div className="setting-row">
          <div className="setting-info">
            <div className="setting-label">Session Timeout</div>
            <div className="setting-description">
              Automatically log out users after inactivity (5-480 minutes)
            </div>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <input
              type="number"
              className="setting-input"
              value={formData.session_timeout_minutes}
              onChange={(e) => handleChange('session_timeout_minutes', parseInt(e.target.value) || 60)}
              min={5}
              max={480}
            />
            <span style={{ fontSize: 13, color: 'var(--text-muted)' }}>minutes</span>
          </div>
        </div>

        <div className="setting-row">
          <div className="setting-info">
            <div className="setting-label">Require Two-Factor Authentication</div>
            <div className="setting-description">
              Require all users to set up 2FA for account access
            </div>
          </div>
          <ToggleSwitch
            enabled={formData.require_2fa}
            onChange={(value) => handleChange('require_2fa', value)}
            disabled={updateSettings.isPending}
          />
        </div>
      </div>

      {/* Password Requirements */}
      <div className="settings-section">
        <div className="section-title">
          <Key />
          Password Requirements
        </div>

        <div className="setting-row">
          <div className="setting-info">
            <div className="setting-label">Minimum Password Length</div>
            <div className="setting-description">
              Minimum number of characters required (8-128)
            </div>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <input
              type="number"
              className="setting-input"
              value={formData.password_min_length}
              onChange={(e) => handleChange('password_min_length', parseInt(e.target.value) || 12)}
              min={8}
              max={128}
            />
            <span style={{ fontSize: 13, color: 'var(--text-muted)' }}>characters</span>
          </div>
        </div>

        <div className="setting-row">
          <div className="setting-info">
            <div className="setting-label">Require Uppercase Letter</div>
            <div className="setting-description">
              Password must contain at least one uppercase letter
            </div>
          </div>
          <ToggleSwitch
            enabled={formData.password_require_uppercase}
            onChange={(value) => handleChange('password_require_uppercase', value)}
            disabled={updateSettings.isPending}
          />
        </div>

        <div className="setting-row">
          <div className="setting-info">
            <div className="setting-label">Require Number</div>
            <div className="setting-description">
              Password must contain at least one number
            </div>
          </div>
          <ToggleSwitch
            enabled={formData.password_require_number}
            onChange={(value) => handleChange('password_require_number', value)}
            disabled={updateSettings.isPending}
          />
        </div>

        <div className="setting-row">
          <div className="setting-info">
            <div className="setting-label">Require Special Character</div>
            <div className="setting-description">
              Password must contain at least one special character (!@#$%^&*)
            </div>
          </div>
          <ToggleSwitch
            enabled={formData.password_require_special}
            onChange={(value) => handleChange('password_require_special', value)}
            disabled={updateSettings.isPending}
          />
        </div>
      </div>

      {/* IP Allowlist */}
      <div className="settings-section">
        <div className="section-title">
          <Lock />
          IP Allowlist
        </div>
        <p style={{ fontSize: 13, color: 'var(--text-secondary)', marginBottom: 16 }}>
          Restrict access to specific IP addresses or ranges. Leave empty to allow all IPs.
        </p>

        <div className="ip-range-section">
          <div className="ip-input-row">
            <input
              type="text"
              className="ip-input"
              value={ipInput}
              onChange={(e) => setIpInput(e.target.value)}
              placeholder="192.168.1.0/24 or 10.0.0.1"
              onKeyDown={(e) => e.key === 'Enter' && handleAddIpRange()}
            />
            <button className="add-ip-btn" onClick={handleAddIpRange}>
              Add
            </button>
          </div>

          <div className="ip-tags">
            {formData.allowed_ip_ranges.length === 0 ? (
              <span className="ip-empty">No IP restrictions configured</span>
            ) : (
              formData.allowed_ip_ranges.map((ip) => (
                <span key={ip} className="ip-tag">
                  {ip}
                  <button onClick={() => handleRemoveIpRange(ip)}>
                    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <path d="M18 6L6 18M6 6l12 12" />
                    </svg>
                  </button>
                </span>
              ))
            )}
          </div>
        </div>
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
          'Save Security Settings'
        )}
      </button>
    </div>
  );
}
