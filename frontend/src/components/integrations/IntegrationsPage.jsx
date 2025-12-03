import React, { useState } from 'react';
import { Plug, Key, Webhook } from 'lucide-react';
import ApiKeysTab from './ApiKeysTab';
import WebhooksTab from './WebhooksTab';

const TABS = [
  { id: 'api-keys', label: 'API Keys', icon: Key },
  { id: 'webhooks', label: 'Webhooks', icon: Webhook },
];

export default function IntegrationsPage() {
  const [activeTab, setActiveTab] = useState('api-keys');

  return (
    <div className="integrations-page">
      <style>{`
        .integrations-page {
          max-width: 1200px;
          margin: 0 auto;
        }

        .integrations-header {
          display: flex;
          align-items: flex-start;
          gap: 12px;
          margin-bottom: 24px;
        }

        .integrations-icon {
          width: 32px;
          height: 32px;
          color: var(--accent-primary, #6366f1);
        }

        .integrations-title {
          font-size: 24px;
          font-weight: 600;
          color: var(--text-primary, #f0f2f5);
          margin: 0;
        }

        .integrations-subtitle {
          font-size: 14px;
          color: var(--text-secondary, #8b919e);
          margin: 4px 0 0;
        }

        .integrations-tabs {
          display: flex;
          gap: 4px;
          padding: 4px;
          background: var(--bg-secondary, #111318);
          border-radius: 10px;
          margin-bottom: 24px;
          width: fit-content;
        }

        .tab-btn {
          display: flex;
          align-items: center;
          gap: 8px;
          padding: 10px 16px;
          background: transparent;
          border: none;
          border-radius: 8px;
          color: var(--text-secondary, #8b919e);
          font-size: 14px;
          font-weight: 500;
          cursor: pointer;
          transition: all 0.15s;
          font-family: inherit;
        }

        .tab-btn:hover {
          color: var(--text-primary, #f0f2f5);
          background: var(--bg-tertiary, #1a1d24);
        }

        .tab-btn.active {
          background: var(--accent-primary, #6366f1);
          color: white;
        }

        .tab-btn svg {
          width: 16px;
          height: 16px;
        }
      `}</style>

      <div className="integrations-header">
        <Plug className="integrations-icon" />
        <div>
          <h1 className="integrations-title">Integrations</h1>
          <p className="integrations-subtitle">
            Manage API keys and webhook configurations
          </p>
        </div>
      </div>

      <div className="integrations-tabs">
        {TABS.map((tab) => (
          <button
            key={tab.id}
            className={`tab-btn ${activeTab === tab.id ? 'active' : ''}`}
            onClick={() => setActiveTab(tab.id)}
          >
            <tab.icon />
            {tab.label}
          </button>
        ))}
      </div>

      {activeTab === 'api-keys' && <ApiKeysTab />}
      {activeTab === 'webhooks' && <WebhooksTab />}
    </div>
  );
}
