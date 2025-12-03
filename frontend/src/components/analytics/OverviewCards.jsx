import React from 'react';
import {
  CheckCircle2,
  Clock,
  TrendingUp,
  AlertTriangle,
  Shield,
  Percent,
} from 'lucide-react';

export default function OverviewCards({ data, isLoading }) {
  const cards = [
    {
      label: 'Total Verifications',
      value: data?.total_verifications ?? 0,
      icon: CheckCircle2,
      color: 'primary',
    },
    {
      label: 'Approval Rate',
      value: `${data?.approval_rate ?? 0}%`,
      icon: Percent,
      color: 'success',
    },
    {
      label: 'Avg Processing Time',
      value: `${data?.avg_processing_time_hours ?? 0}h`,
      icon: Clock,
      color: 'info',
    },
    {
      label: 'Avg Risk Score',
      value: data?.avg_risk_score ?? 0,
      icon: AlertTriangle,
      color: getRiskColor(data?.avg_risk_score),
    },
    {
      label: 'Total Screened',
      value: data?.total_screened ?? 0,
      icon: Shield,
      color: 'purple',
    },
    {
      label: 'Screening Hit Rate',
      value: `${data?.hit_rate ?? 0}%`,
      icon: TrendingUp,
      color: 'warning',
    },
  ];

  return (
    <div className="overview-cards">
      <style>{`
        .overview-cards {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
          gap: 16px;
          margin-bottom: 24px;
        }

        .overview-card {
          background: var(--bg-secondary, #111318);
          border: 1px solid var(--border-color, #2a2f3a);
          border-radius: 12px;
          padding: 20px;
          transition: all 0.2s;
        }

        .overview-card:hover {
          border-color: var(--accent-primary, #6366f1);
          box-shadow: 0 0 0 3px var(--accent-glow, rgba(99, 102, 241, 0.1));
        }

        .overview-card.skeleton {
          pointer-events: none;
        }

        .card-header {
          display: flex;
          justify-content: space-between;
          align-items: flex-start;
          margin-bottom: 12px;
        }

        .card-label {
          font-size: 13px;
          color: var(--text-secondary, #8b919e);
          font-weight: 500;
        }

        .card-icon {
          width: 36px;
          height: 36px;
          border-radius: 8px;
          display: flex;
          align-items: center;
          justify-content: center;
        }

        .card-icon.primary {
          background: rgba(99, 102, 241, 0.15);
          color: var(--accent-primary, #6366f1);
        }

        .card-icon.success {
          background: rgba(16, 185, 129, 0.15);
          color: var(--success, #10b981);
        }

        .card-icon.info {
          background: rgba(59, 130, 246, 0.15);
          color: var(--info, #3b82f6);
        }

        .card-icon.warning {
          background: rgba(245, 158, 11, 0.15);
          color: var(--warning, #f59e0b);
        }

        .card-icon.danger {
          background: rgba(239, 68, 68, 0.15);
          color: var(--danger, #ef4444);
        }

        .card-icon.purple {
          background: rgba(139, 92, 246, 0.15);
          color: #8b5cf6;
        }

        .card-value {
          font-size: 32px;
          font-weight: 700;
          letter-spacing: -0.02em;
          color: var(--text-primary, #f0f2f5);
        }

        .skeleton-text {
          background: linear-gradient(90deg, var(--bg-tertiary) 25%, var(--bg-hover) 50%, var(--bg-tertiary) 75%);
          background-size: 200% 100%;
          animation: skeleton-pulse 1.5s ease-in-out infinite;
          border-radius: 4px;
          display: block;
        }

        .skeleton-icon {
          width: 36px;
          height: 36px;
          border-radius: 8px;
          background: var(--bg-tertiary);
          animation: skeleton-pulse 1.5s ease-in-out infinite;
        }

        @keyframes skeleton-pulse {
          0% { background-position: 200% 0; }
          100% { background-position: -200% 0; }
        }
      `}</style>

      {isLoading
        ? Array.from({ length: 6 }).map((_, i) => (
            <div key={i} className="overview-card skeleton">
              <div className="card-header">
                <span className="skeleton-text" style={{ width: '100px', height: '13px' }} />
                <div className="skeleton-icon" />
              </div>
              <span className="skeleton-text" style={{ width: '80px', height: '32px' }} />
            </div>
          ))
        : cards.map((card, idx) => (
            <div key={idx} className="overview-card">
              <div className="card-header">
                <span className="card-label">{card.label}</span>
                <div className={`card-icon ${card.color}`}>
                  <card.icon size={18} />
                </div>
              </div>
              <div className="card-value">{card.value}</div>
            </div>
          ))}
    </div>
  );
}

function getRiskColor(score) {
  if (score === null || score === undefined) return 'info';
  if (score <= 30) return 'success';
  if (score <= 60) return 'warning';
  return 'danger';
}
