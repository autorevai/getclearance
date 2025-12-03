import React, { useState } from 'react';
import {
  Settings,
  Users,
  Bell,
  Shield,
  Palette,
  Building2,
} from 'lucide-react';
import GeneralSettings from './GeneralSettings';
import TeamSettings from './TeamSettings';
import NotificationSettings from './NotificationSettings';
import SecuritySettings from './SecuritySettings';
import BrandingSettings from './BrandingSettings';

const tabs = [
  { id: 'general', label: 'General', icon: Building2 },
  { id: 'team', label: 'Team', icon: Users },
  { id: 'notifications', label: 'Notifications', icon: Bell },
  { id: 'security', label: 'Security', icon: Shield },
  { id: 'branding', label: 'Branding', icon: Palette },
];

export default function SettingsPage() {
  const [activeTab, setActiveTab] = useState('general');

  const renderTabContent = () => {
    switch (activeTab) {
      case 'general':
        return <GeneralSettings />;
      case 'team':
        return <TeamSettings />;
      case 'notifications':
        return <NotificationSettings />;
      case 'security':
        return <SecuritySettings />;
      case 'branding':
        return <BrandingSettings />;
      default:
        return <GeneralSettings />;
    }
  };

  return (
    <div className="settings-page">
      <style>{`
        .settings-page {
          max-width: 1200px;
          margin: 0 auto;
        }

        .settings-header {
          display: flex;
          align-items: center;
          gap: 12px;
          margin-bottom: 24px;
        }

        .settings-icon {
          width: 32px;
          height: 32px;
          color: var(--accent-primary, #6366f1);
        }

        .settings-title {
          font-size: 24px;
          font-weight: 600;
          color: var(--text-primary, #f0f2f5);
          margin: 0;
        }

        .settings-subtitle {
          font-size: 14px;
          color: var(--text-secondary, #8b919e);
          margin: 4px 0 0;
        }

        .settings-container {
          display: flex;
          gap: 24px;
        }

        .settings-sidebar {
          width: 220px;
          flex-shrink: 0;
        }

        .settings-tabs {
          display: flex;
          flex-direction: column;
          gap: 4px;
          background: var(--bg-secondary, #111318);
          border-radius: 12px;
          padding: 8px;
          border: 1px solid var(--border-color, #2a2f3a);
        }

        .settings-tab {
          display: flex;
          align-items: center;
          gap: 10px;
          padding: 10px 14px;
          border-radius: 8px;
          cursor: pointer;
          color: var(--text-secondary, #8b919e);
          transition: all 0.15s ease;
          border: none;
          background: transparent;
          font-size: 14px;
          font-weight: 500;
          text-align: left;
          width: 100%;
          font-family: inherit;
        }

        .settings-tab:hover {
          background: var(--bg-hover, #22262f);
          color: var(--text-primary, #f0f2f5);
        }

        .settings-tab.active {
          background: var(--accent-glow, rgba(99, 102, 241, 0.15));
          color: var(--accent-primary, #6366f1);
        }

        .settings-tab-icon {
          width: 18px;
          height: 18px;
        }

        .settings-content {
          flex: 1;
          min-width: 0;
        }

        .settings-panel {
          background: var(--bg-secondary, #111318);
          border-radius: 12px;
          border: 1px solid var(--border-color, #2a2f3a);
          padding: 24px;
        }

        @media (max-width: 768px) {
          .settings-container {
            flex-direction: column;
          }

          .settings-sidebar {
            width: 100%;
          }

          .settings-tabs {
            flex-direction: row;
            overflow-x: auto;
            gap: 0;
          }

          .settings-tab {
            flex-shrink: 0;
          }
        }
      `}</style>

      <div className="settings-header">
        <Settings className="settings-icon" />
        <div>
          <h1 className="settings-title">Settings</h1>
          <p className="settings-subtitle">
            Manage your workspace, team, and preferences
          </p>
        </div>
      </div>

      <div className="settings-container">
        <div className="settings-sidebar">
          <div className="settings-tabs">
            {tabs.map((tab) => (
              <button
                key={tab.id}
                className={`settings-tab ${activeTab === tab.id ? 'active' : ''}`}
                onClick={() => setActiveTab(tab.id)}
              >
                <tab.icon className="settings-tab-icon" />
                <span>{tab.label}</span>
              </button>
            ))}
          </div>
        </div>

        <div className="settings-content">
          <div className="settings-panel">
            {renderTabContent()}
          </div>
        </div>
      </div>
    </div>
  );
}
