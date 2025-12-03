/**
 * Subscription Card Component
 *
 * Displays current subscription status and plan details.
 */

import React from 'react';
import {
  Crown,
  Calendar,
  AlertTriangle,
  CheckCircle,
  Clock,
  ArrowUpRight,
} from 'lucide-react';

const STATUS_CONFIG = {
  active: { label: 'Active', color: '#22c55e', icon: CheckCircle },
  trialing: { label: 'Trial', color: '#6366f1', icon: Clock },
  past_due: { label: 'Past Due', color: '#ef4444', icon: AlertTriangle },
  canceled: { label: 'Canceled', color: '#8b919e', icon: AlertTriangle },
  unpaid: { label: 'Unpaid', color: '#ef4444', icon: AlertTriangle },
};

export default function SubscriptionCard({ subscription, isLoading, onUpgrade }) {
  if (isLoading) {
    return (
      <div className="subscription-card loading">
        <style>{`
          .subscription-card.loading {
            background: var(--bg-secondary, #111318);
            border: 1px solid var(--border-primary, #23262f);
            border-radius: 12px;
            padding: 40px;
            text-align: center;
            color: var(--text-secondary, #8b919e);
          }
        `}</style>
        Loading subscription...
      </div>
    );
  }

  const status = subscription ? STATUS_CONFIG[subscription.status] || STATUS_CONFIG.active : null;
  const StatusIcon = status?.icon || CheckCircle;

  return (
    <div className="subscription-card">
      <style>{`
        .subscription-card {
          background: var(--bg-secondary, #111318);
          border: 1px solid var(--border-primary, #23262f);
          border-radius: 12px;
          overflow: hidden;
        }

        .card-header {
          display: flex;
          align-items: center;
          justify-content: space-between;
          padding: 20px;
          border-bottom: 1px solid var(--border-primary, #23262f);
        }

        .card-title {
          display: flex;
          align-items: center;
          gap: 10px;
          font-size: 16px;
          font-weight: 600;
          color: var(--text-primary, #f0f2f5);
          margin: 0;
        }

        .card-title svg {
          width: 20px;
          height: 20px;
          color: var(--accent-primary, #6366f1);
        }

        .status-badge {
          display: inline-flex;
          align-items: center;
          gap: 6px;
          padding: 6px 12px;
          border-radius: 20px;
          font-size: 12px;
          font-weight: 500;
        }

        .status-badge svg {
          width: 14px;
          height: 14px;
        }

        .card-content {
          padding: 20px;
        }

        .plan-info {
          display: flex;
          align-items: flex-end;
          gap: 8px;
          margin-bottom: 20px;
        }

        .plan-name {
          font-size: 28px;
          font-weight: 700;
          color: var(--text-primary, #f0f2f5);
        }

        .plan-price {
          font-size: 16px;
          color: var(--text-secondary, #8b919e);
          margin-bottom: 4px;
        }

        .info-grid {
          display: grid;
          grid-template-columns: repeat(2, 1fr);
          gap: 16px;
          margin-bottom: 20px;
        }

        .info-item {
          display: flex;
          flex-direction: column;
          gap: 4px;
        }

        .info-label {
          display: flex;
          align-items: center;
          gap: 6px;
          font-size: 12px;
          color: var(--text-secondary, #8b919e);
        }

        .info-label svg {
          width: 12px;
          height: 12px;
        }

        .info-value {
          font-size: 14px;
          font-weight: 500;
          color: var(--text-primary, #f0f2f5);
        }

        .cancel-warning {
          display: flex;
          align-items: center;
          gap: 10px;
          padding: 12px;
          background: rgba(245, 158, 11, 0.1);
          border-radius: 8px;
          margin-bottom: 20px;
        }

        .cancel-warning svg {
          width: 20px;
          height: 20px;
          color: #f59e0b;
          flex-shrink: 0;
        }

        .cancel-warning-text {
          font-size: 13px;
          color: #f59e0b;
        }

        .upgrade-btn {
          display: flex;
          align-items: center;
          justify-content: center;
          gap: 8px;
          width: 100%;
          padding: 12px;
          background: var(--accent-primary, #6366f1);
          color: white;
          border: none;
          border-radius: 8px;
          font-size: 14px;
          font-weight: 500;
          cursor: pointer;
          transition: background 0.15s;
          font-family: inherit;
        }

        .upgrade-btn:hover {
          background: var(--accent-hover, #5558e3);
        }

        .upgrade-btn svg {
          width: 16px;
          height: 16px;
        }

        .no-subscription {
          text-align: center;
          padding: 40px 20px;
        }

        .no-subscription-icon {
          width: 48px;
          height: 48px;
          color: var(--text-secondary, #8b919e);
          margin-bottom: 16px;
        }

        .no-subscription-title {
          font-size: 16px;
          font-weight: 600;
          color: var(--text-primary, #f0f2f5);
          margin: 0 0 8px;
        }

        .no-subscription-text {
          font-size: 14px;
          color: var(--text-secondary, #8b919e);
          margin: 0 0 20px;
        }

        .payment-method {
          display: flex;
          align-items: center;
          gap: 10px;
          padding: 12px;
          background: var(--bg-tertiary, #1a1d24);
          border-radius: 8px;
        }

        .payment-icon {
          width: 40px;
          height: 26px;
          background: var(--bg-secondary, #111318);
          border-radius: 4px;
          display: flex;
          align-items: center;
          justify-content: center;
          font-size: 10px;
          font-weight: 600;
          color: var(--text-secondary, #8b919e);
          text-transform: uppercase;
        }

        .payment-details {
          flex: 1;
        }

        .payment-card {
          font-size: 13px;
          font-weight: 500;
          color: var(--text-primary, #f0f2f5);
        }

        .payment-expiry {
          font-size: 12px;
          color: var(--text-secondary, #8b919e);
        }
      `}</style>

      <div className="card-header">
        <h3 className="card-title">
          <Crown />
          Subscription
        </h3>
        {status && (
          <span
            className="status-badge"
            style={{
              color: status.color,
              background: `${status.color}15`,
            }}
          >
            <StatusIcon />
            {status.label}
          </span>
        )}
      </div>

      <div className="card-content">
        {subscription ? (
          <>
            <div className="plan-info">
              <span className="plan-name">{subscription.plan_name}</span>
              <span className="plan-price">
                {subscription.amount_formatted}/{subscription.interval}
              </span>
            </div>

            {subscription.cancel_at_period_end && (
              <div className="cancel-warning">
                <AlertTriangle />
                <span className="cancel-warning-text">
                  Your subscription will end on {new Date(subscription.current_period_end).toLocaleDateString()}
                </span>
              </div>
            )}

            <div className="info-grid">
              <div className="info-item">
                <span className="info-label">
                  <Calendar /> Billing Period
                </span>
                <span className="info-value">
                  {new Date(subscription.current_period_start).toLocaleDateString()} - {new Date(subscription.current_period_end).toLocaleDateString()}
                </span>
              </div>
              <div className="info-item">
                <span className="info-label">
                  <Calendar /> Next Invoice
                </span>
                <span className="info-value">
                  {subscription.cancel_at_period_end
                    ? 'N/A'
                    : new Date(subscription.current_period_end).toLocaleDateString()
                  }
                </span>
              </div>
            </div>

            {subscription.payment_method && (
              <div className="payment-method">
                <div className="payment-icon">
                  {subscription.payment_method.brand}
                </div>
                <div className="payment-details">
                  <div className="payment-card">
                    **** **** **** {subscription.payment_method.last4}
                  </div>
                  <div className="payment-expiry">
                    Expires {subscription.payment_method.exp_month}/{subscription.payment_method.exp_year}
                  </div>
                </div>
              </div>
            )}

            <button className="upgrade-btn" onClick={onUpgrade} style={{ marginTop: 20 }}>
              <ArrowUpRight />
              Change Plan
            </button>
          </>
        ) : (
          <div className="no-subscription">
            <Crown className="no-subscription-icon" />
            <h4 className="no-subscription-title">No Active Subscription</h4>
            <p className="no-subscription-text">
              Choose a plan to unlock all features
            </p>
            <button className="upgrade-btn" onClick={onUpgrade}>
              <ArrowUpRight />
              Choose a Plan
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
