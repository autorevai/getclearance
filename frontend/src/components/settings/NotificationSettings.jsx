import React, { useState, useEffect } from 'react';
import { Bell, Check, Loader2 } from 'lucide-react';
import { useNotificationPreferences, useUpdateNotificationPreferences } from '../../hooks';

const notificationOptions = [
  {
    key: 'email_new_applicant',
    label: 'New Applicant Created',
    description: 'Get notified when a new applicant is created',
  },
  {
    key: 'email_review_required',
    label: 'Review Required',
    description: 'Get notified when an applicant needs review',
  },
  {
    key: 'email_high_risk_alert',
    label: 'High Risk Alerts',
    description: 'Get notified when a high-risk applicant is detected',
  },
  {
    key: 'email_screening_hit',
    label: 'Screening Hits',
    description: 'Get notified when screening finds a potential match',
  },
  {
    key: 'email_case_assigned',
    label: 'Case Assignments',
    description: 'Get notified when a case is assigned to you',
  },
  {
    key: 'email_daily_digest',
    label: 'Daily Digest',
    description: 'Receive a daily summary of activity',
  },
  {
    key: 'email_weekly_report',
    label: 'Weekly Report',
    description: 'Receive a weekly compliance summary report',
  },
];

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

export default function NotificationSettings() {
  const { data: preferences, isLoading } = useNotificationPreferences();
  const updatePreferences = useUpdateNotificationPreferences();

  const [formData, setFormData] = useState({
    email_new_applicant: true,
    email_review_required: true,
    email_high_risk_alert: true,
    email_screening_hit: true,
    email_case_assigned: true,
    email_daily_digest: false,
    email_weekly_report: true,
  });
  const [saveSuccess, setSaveSuccess] = useState(false);

  // Initialize from server data
  useEffect(() => {
    if (preferences) {
      setFormData(preferences);
    }
  }, [preferences]);

  const handleToggle = (key, value) => {
    setFormData((prev) => ({ ...prev, [key]: value }));
    setSaveSuccess(false);
  };

  const handleSave = async () => {
    try {
      await updatePreferences.mutateAsync(formData);
      setSaveSuccess(true);
      setTimeout(() => setSaveSuccess(false), 3000);
    } catch (error) {
      console.error('Failed to save notification preferences:', error);
    }
  };

  if (isLoading) {
    return (
      <div className="settings-loading">
        <Loader2 className="spinner" />
        <span>Loading preferences...</span>
      </div>
    );
  }

  return (
    <div className="notification-settings">
      <style>{`
        .notification-settings h2 {
          font-size: 18px;
          font-weight: 600;
          color: var(--text-primary, #f0f2f5);
          margin: 0 0 8px;
          display: flex;
          align-items: center;
          gap: 8px;
        }

        .notification-settings h2 svg {
          width: 20px;
          height: 20px;
          color: var(--accent-primary, #6366f1);
        }

        .section-description {
          font-size: 14px;
          color: var(--text-secondary, #8b919e);
          margin-bottom: 24px;
        }

        .notification-list {
          display: flex;
          flex-direction: column;
          gap: 16px;
        }

        .notification-item {
          display: flex;
          align-items: center;
          justify-content: space-between;
          padding: 16px;
          background: var(--bg-tertiary, #1a1d24);
          border-radius: 10px;
          border: 1px solid var(--border-color, #2a2f3a);
        }

        .notification-info {
          flex: 1;
          min-width: 0;
        }

        .notification-label {
          font-size: 14px;
          font-weight: 500;
          color: var(--text-primary, #f0f2f5);
          margin-bottom: 4px;
        }

        .notification-description {
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
          margin-top: 24px;
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
        <Bell />
        Notification Preferences
      </h2>
      <p className="section-description">
        Choose which email notifications you'd like to receive.
      </p>

      <div className="notification-list">
        {notificationOptions.map((option) => (
          <div key={option.key} className="notification-item">
            <div className="notification-info">
              <div className="notification-label">{option.label}</div>
              <div className="notification-description">{option.description}</div>
            </div>
            <ToggleSwitch
              enabled={formData[option.key]}
              onChange={(value) => handleToggle(option.key, value)}
              disabled={updatePreferences.isPending}
            />
          </div>
        ))}
      </div>

      <button
        className={`save-button ${saveSuccess ? 'success' : ''}`}
        onClick={handleSave}
        disabled={updatePreferences.isPending}
      >
        {updatePreferences.isPending ? (
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
          'Save Preferences'
        )}
      </button>
    </div>
  );
}
