/**
 * Billing Page
 *
 * Main billing and usage dashboard with subscription management.
 */

import React, { useState } from 'react';
import {
  CreditCard,
  Receipt,
  BarChart3,
  Settings,
  ExternalLink,
} from 'lucide-react';
import { useSubscription, useOpenPortal } from '../../hooks';
import UsageDashboard from './UsageDashboard';
import SubscriptionCard from './SubscriptionCard';
import InvoiceList from './InvoiceList';
import PlanSelector from './PlanSelector';

export default function BillingPage() {
  const [activeTab, setActiveTab] = useState('overview');
  const [showPlanSelector, setShowPlanSelector] = useState(false);
  const { data: subscription, isLoading: subscriptionLoading } = useSubscription();
  const openPortalMutation = useOpenPortal();

  const tabs = [
    { id: 'overview', label: 'Overview', icon: BarChart3 },
    { id: 'invoices', label: 'Invoices', icon: Receipt },
    { id: 'payment', label: 'Payment', icon: CreditCard },
  ];

  const handleManageBilling = () => {
    openPortalMutation.mutate(window.location.href);
  };

  return (
    <div className="billing-page">
      <style>{`
        .billing-page {
          max-width: 1200px;
          margin: 0 auto;
        }

        .page-header {
          display: flex;
          justify-content: space-between;
          align-items: flex-start;
          margin-bottom: 24px;
          gap: 16px;
          flex-wrap: wrap;
        }

        .page-title-section {
          display: flex;
          align-items: flex-start;
          gap: 12px;
        }

        .page-icon {
          width: 32px;
          height: 32px;
          color: var(--accent-primary, #6366f1);
        }

        .page-title {
          font-size: 24px;
          font-weight: 600;
          color: var(--text-primary, #f0f2f5);
          margin: 0;
        }

        .page-subtitle {
          font-size: 14px;
          color: var(--text-secondary, #8b919e);
          margin: 4px 0 0;
        }

        .header-actions {
          display: flex;
          gap: 12px;
          align-items: center;
        }

        .manage-btn {
          display: flex;
          align-items: center;
          gap: 8px;
          padding: 10px 16px;
          background: var(--bg-secondary, #111318);
          border: 1px solid var(--border-primary, #23262f);
          border-radius: 8px;
          color: var(--text-primary, #f0f2f5);
          font-size: 14px;
          font-weight: 500;
          cursor: pointer;
          transition: all 0.15s;
          font-family: inherit;
        }

        .manage-btn:hover {
          background: var(--bg-tertiary, #1a1d24);
          border-color: var(--accent-primary, #6366f1);
        }

        .manage-btn svg {
          width: 16px;
          height: 16px;
        }

        .tabs {
          display: flex;
          gap: 4px;
          padding: 4px;
          background: var(--bg-secondary, #111318);
          border: 1px solid var(--border-primary, #23262f);
          border-radius: 10px;
          margin-bottom: 24px;
          width: fit-content;
        }

        .tab {
          display: flex;
          align-items: center;
          gap: 8px;
          padding: 10px 16px;
          background: transparent;
          border: none;
          border-radius: 6px;
          color: var(--text-secondary, #8b919e);
          font-size: 14px;
          font-weight: 500;
          cursor: pointer;
          transition: all 0.15s;
          font-family: inherit;
        }

        .tab:hover {
          color: var(--text-primary, #f0f2f5);
        }

        .tab.active {
          background: var(--accent-primary, #6366f1);
          color: white;
        }

        .tab svg {
          width: 16px;
          height: 16px;
        }

        .content-grid {
          display: grid;
          gap: 24px;
        }

        .content-grid.two-col {
          grid-template-columns: 1fr 1fr;
        }

        @media (max-width: 900px) {
          .content-grid.two-col {
            grid-template-columns: 1fr;
          }
        }

        .section-title {
          font-size: 16px;
          font-weight: 600;
          color: var(--text-primary, #f0f2f5);
          margin: 0 0 16px;
        }
      `}</style>

      <div className="page-header">
        <div className="page-title-section">
          <CreditCard className="page-icon" />
          <div>
            <h1 className="page-title">Billing & Usage</h1>
            <p className="page-subtitle">
              Manage your subscription, view usage, and download invoices
            </p>
          </div>
        </div>
        <div className="header-actions">
          <button
            className="manage-btn"
            onClick={handleManageBilling}
            disabled={openPortalMutation.isPending}
          >
            <Settings />
            {openPortalMutation.isPending ? 'Opening...' : 'Manage in Stripe'}
            <ExternalLink />
          </button>
        </div>
      </div>

      <div className="tabs">
        {tabs.map((tab) => {
          const Icon = tab.icon;
          return (
            <button
              key={tab.id}
              className={`tab ${activeTab === tab.id ? 'active' : ''}`}
              onClick={() => setActiveTab(tab.id)}
            >
              <Icon />
              {tab.label}
            </button>
          );
        })}
      </div>

      {activeTab === 'overview' && (
        <div className="content-grid">
          <SubscriptionCard
            subscription={subscription}
            isLoading={subscriptionLoading}
            onUpgrade={() => setShowPlanSelector(true)}
          />
          <UsageDashboard />
        </div>
      )}

      {activeTab === 'invoices' && (
        <div className="content-grid">
          <InvoiceList />
        </div>
      )}

      {activeTab === 'payment' && (
        <div className="content-grid">
          <div>
            <h3 className="section-title">Payment Methods</h3>
            <p style={{ color: 'var(--text-secondary)', fontSize: 14 }}>
              Manage your payment methods through the Stripe customer portal.
            </p>
            <button
              className="manage-btn"
              onClick={handleManageBilling}
              style={{ marginTop: 16 }}
            >
              <CreditCard />
              Manage Payment Methods
              <ExternalLink />
            </button>
          </div>
        </div>
      )}

      {showPlanSelector && (
        <PlanSelector
          currentPlanId={subscription?.plan_id}
          onClose={() => setShowPlanSelector(false)}
        />
      )}
    </div>
  );
}
