/**
 * Plan Selector Component
 *
 * Modal for selecting/changing subscription plans.
 */

import React, { useState } from 'react';
import {
  X,
  Check,
  Crown,
  Zap,
  Building2,
  Loader2,
} from 'lucide-react';
import { usePlans, useUpdateSubscription } from '../../hooks';

const PLAN_ICONS = {
  starter: Zap,
  professional: Crown,
  enterprise: Building2,
};

const PLAN_COLORS = {
  starter: '#22c55e',
  professional: '#6366f1',
  enterprise: '#f59e0b',
};

export default function PlanSelector({ currentPlanId, onClose }) {
  const [selectedPlan, setSelectedPlan] = useState(null);
  const { data: plans, isLoading: plansLoading } = usePlans();
  const updateMutation = useUpdateSubscription();

  const handleSelectPlan = async () => {
    if (!selectedPlan) return;

    try {
      await updateMutation.mutateAsync({ plan_id: selectedPlan });
      onClose();
    } catch (error) {
      console.error('Failed to update subscription:', error);
    }
  };

  return (
    <div className="plan-selector-overlay" onClick={onClose}>
      <style>{`
        .plan-selector-overlay {
          position: fixed;
          top: 0;
          left: 0;
          right: 0;
          bottom: 0;
          background: rgba(0, 0, 0, 0.5);
          z-index: 1000;
          display: flex;
          align-items: center;
          justify-content: center;
          padding: 20px;
        }

        .plan-selector-modal {
          width: 900px;
          max-width: 100%;
          max-height: 90vh;
          background: var(--bg-primary, #0a0b0e);
          border: 1px solid var(--border-primary, #23262f);
          border-radius: 16px;
          overflow: hidden;
          animation: modalIn 0.2s ease-out;
        }

        @keyframes modalIn {
          from {
            transform: scale(0.95);
            opacity: 0;
          }
          to {
            transform: scale(1);
            opacity: 1;
          }
        }

        .modal-header {
          display: flex;
          align-items: center;
          justify-content: space-between;
          padding: 20px 24px;
          border-bottom: 1px solid var(--border-primary, #23262f);
          background: var(--bg-secondary, #111318);
        }

        .modal-title {
          font-size: 18px;
          font-weight: 600;
          color: var(--text-primary, #f0f2f5);
          margin: 0;
        }

        .close-btn {
          width: 32px;
          height: 32px;
          display: flex;
          align-items: center;
          justify-content: center;
          background: transparent;
          border: none;
          color: var(--text-secondary, #8b919e);
          cursor: pointer;
          border-radius: 6px;
          transition: all 0.15s;
        }

        .close-btn:hover {
          background: var(--bg-tertiary, #1a1d24);
          color: var(--text-primary, #f0f2f5);
        }

        .close-btn svg {
          width: 20px;
          height: 20px;
        }

        .modal-content {
          padding: 24px;
          overflow-y: auto;
          max-height: calc(90vh - 140px);
        }

        .plans-grid {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
          gap: 20px;
        }

        .plan-card {
          background: var(--bg-secondary, #111318);
          border: 2px solid var(--border-primary, #23262f);
          border-radius: 12px;
          padding: 24px;
          cursor: pointer;
          transition: all 0.15s;
          position: relative;
        }

        .plan-card:hover {
          border-color: var(--accent-primary, #6366f1);
        }

        .plan-card.selected {
          border-color: var(--accent-primary, #6366f1);
          background: rgba(99, 102, 241, 0.05);
        }

        .plan-card.current {
          border-color: #22c55e;
        }

        .current-badge {
          position: absolute;
          top: -10px;
          right: 16px;
          padding: 4px 12px;
          background: #22c55e;
          color: white;
          font-size: 11px;
          font-weight: 600;
          border-radius: 12px;
        }

        .plan-icon {
          width: 48px;
          height: 48px;
          border-radius: 12px;
          display: flex;
          align-items: center;
          justify-content: center;
          margin-bottom: 16px;
        }

        .plan-icon svg {
          width: 24px;
          height: 24px;
        }

        .plan-name {
          font-size: 20px;
          font-weight: 600;
          color: var(--text-primary, #f0f2f5);
          margin: 0 0 8px;
        }

        .plan-price {
          display: flex;
          align-items: baseline;
          gap: 4px;
          margin-bottom: 20px;
        }

        .price-amount {
          font-size: 32px;
          font-weight: 700;
          color: var(--text-primary, #f0f2f5);
        }

        .price-interval {
          font-size: 14px;
          color: var(--text-secondary, #8b919e);
        }

        .plan-features {
          list-style: none;
          padding: 0;
          margin: 0;
          display: flex;
          flex-direction: column;
          gap: 12px;
        }

        .plan-feature {
          display: flex;
          align-items: flex-start;
          gap: 10px;
          font-size: 13px;
          color: var(--text-secondary, #8b919e);
        }

        .plan-feature svg {
          width: 16px;
          height: 16px;
          color: #22c55e;
          flex-shrink: 0;
          margin-top: 1px;
        }

        .modal-footer {
          display: flex;
          align-items: center;
          justify-content: flex-end;
          gap: 12px;
          padding: 16px 24px;
          border-top: 1px solid var(--border-primary, #23262f);
          background: var(--bg-secondary, #111318);
        }

        .cancel-btn {
          padding: 10px 20px;
          background: transparent;
          border: 1px solid var(--border-primary, #23262f);
          border-radius: 8px;
          color: var(--text-primary, #f0f2f5);
          font-size: 14px;
          font-weight: 500;
          cursor: pointer;
          transition: all 0.15s;
          font-family: inherit;
        }

        .cancel-btn:hover {
          background: var(--bg-tertiary, #1a1d24);
        }

        .confirm-btn {
          display: flex;
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
          transition: background 0.15s;
          font-family: inherit;
        }

        .confirm-btn:hover:not(:disabled) {
          background: var(--accent-hover, #5558e3);
        }

        .confirm-btn:disabled {
          opacity: 0.6;
          cursor: not-allowed;
        }

        .confirm-btn svg {
          width: 16px;
          height: 16px;
        }

        .loading-state {
          text-align: center;
          padding: 60px 20px;
          color: var(--text-secondary, #8b919e);
        }

        .loading-state svg {
          width: 32px;
          height: 32px;
          animation: spin 1s linear infinite;
          margin-bottom: 16px;
        }

        @keyframes spin {
          to { transform: rotate(360deg); }
        }
      `}</style>

      <div className="plan-selector-modal" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h2 className="modal-title">Choose Your Plan</h2>
          <button className="close-btn" onClick={onClose}>
            <X />
          </button>
        </div>

        <div className="modal-content">
          {plansLoading ? (
            <div className="loading-state">
              <Loader2 />
              <p>Loading plans...</p>
            </div>
          ) : (
            <div className="plans-grid">
              {plans?.map((plan) => {
                const Icon = PLAN_ICONS[plan.id] || Zap;
                const color = PLAN_COLORS[plan.id] || '#6366f1';
                const isCurrent = plan.id === currentPlanId;
                const isSelected = plan.id === selectedPlan;

                return (
                  <div
                    key={plan.id}
                    className={`plan-card ${isSelected ? 'selected' : ''} ${isCurrent ? 'current' : ''}`}
                    onClick={() => !isCurrent && setSelectedPlan(plan.id)}
                  >
                    {isCurrent && <span className="current-badge">Current Plan</span>}

                    <div
                      className="plan-icon"
                      style={{
                        background: `${color}15`,
                        color: color,
                      }}
                    >
                      <Icon />
                    </div>

                    <h3 className="plan-name">{plan.name}</h3>

                    <div className="plan-price">
                      <span className="price-amount">{plan.amount_formatted}</span>
                      <span className="price-interval">/{plan.interval}</span>
                    </div>

                    <ul className="plan-features">
                      {plan.features.map((feature, index) => (
                        <li key={index} className="plan-feature">
                          <Check />
                          {feature}
                        </li>
                      ))}
                    </ul>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        <div className="modal-footer">
          <button className="cancel-btn" onClick={onClose}>
            Cancel
          </button>
          <button
            className="confirm-btn"
            onClick={handleSelectPlan}
            disabled={!selectedPlan || selectedPlan === currentPlanId || updateMutation.isPending}
          >
            {updateMutation.isPending ? (
              <>
                <Loader2 />
                Updating...
              </>
            ) : (
              'Confirm Change'
            )}
          </button>
        </div>
      </div>
    </div>
  );
}
