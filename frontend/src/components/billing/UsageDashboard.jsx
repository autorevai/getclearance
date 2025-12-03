/**
 * Usage Dashboard Component
 *
 * Displays current period usage metrics with progress bars.
 */

import React from 'react';
import {
  Users,
  FileText,
  Shield,
  Fingerprint,
  Zap,
  TrendingUp,
} from 'lucide-react';
import { useUsage, useUsageHistory } from '../../hooks';

const METRIC_CONFIG = {
  applicants: { icon: Users, label: 'Applicants', color: '#6366f1' },
  documents: { icon: FileText, label: 'Documents', color: '#22c55e' },
  screenings: { icon: Shield, label: 'Screenings', color: '#f59e0b' },
  device_scans: { icon: Fingerprint, label: 'Device Scans', color: '#ef4444' },
  api_calls: { icon: Zap, label: 'API Calls', color: '#8b5cf6' },
};

export default function UsageDashboard() {
  const { data: usage, isLoading, error } = useUsage();
  const { data: historyData } = useUsageHistory(3);

  if (isLoading) {
    return (
      <div className="usage-dashboard loading">
        <style>{`
          .usage-dashboard.loading {
            background: var(--bg-secondary, #111318);
            border: 1px solid var(--border-primary, #23262f);
            border-radius: 12px;
            padding: 40px;
            text-align: center;
            color: var(--text-secondary, #8b919e);
          }
        `}</style>
        Loading usage data...
      </div>
    );
  }

  if (error) {
    return (
      <div className="usage-dashboard error">
        <style>{`
          .usage-dashboard.error {
            background: var(--bg-secondary, #111318);
            border: 1px solid var(--border-primary, #23262f);
            border-radius: 12px;
            padding: 40px;
            text-align: center;
            color: var(--error, #ef4444);
          }
        `}</style>
        Failed to load usage data
      </div>
    );
  }

  const metrics = usage?.metrics || {};
  const history = historyData?.history || [];

  return (
    <div className="usage-dashboard">
      <style>{`
        .usage-dashboard {
          background: var(--bg-secondary, #111318);
          border: 1px solid var(--border-primary, #23262f);
          border-radius: 12px;
          overflow: hidden;
        }

        .dashboard-header {
          display: flex;
          align-items: center;
          justify-content: space-between;
          padding: 20px;
          border-bottom: 1px solid var(--border-primary, #23262f);
        }

        .dashboard-title {
          display: flex;
          align-items: center;
          gap: 10px;
          font-size: 16px;
          font-weight: 600;
          color: var(--text-primary, #f0f2f5);
          margin: 0;
        }

        .dashboard-title svg {
          width: 20px;
          height: 20px;
          color: var(--accent-primary, #6366f1);
        }

        .period-label {
          font-size: 13px;
          color: var(--text-secondary, #8b919e);
        }

        .metrics-grid {
          padding: 20px;
          display: flex;
          flex-direction: column;
          gap: 16px;
        }

        .metric-item {
          display: flex;
          align-items: center;
          gap: 16px;
        }

        .metric-icon {
          width: 40px;
          height: 40px;
          border-radius: 10px;
          display: flex;
          align-items: center;
          justify-content: center;
          flex-shrink: 0;
        }

        .metric-icon svg {
          width: 20px;
          height: 20px;
        }

        .metric-content {
          flex: 1;
          min-width: 0;
        }

        .metric-header {
          display: flex;
          align-items: center;
          justify-content: space-between;
          margin-bottom: 6px;
        }

        .metric-label {
          font-size: 13px;
          font-weight: 500;
          color: var(--text-primary, #f0f2f5);
        }

        .metric-value {
          font-size: 13px;
          color: var(--text-secondary, #8b919e);
        }

        .metric-value strong {
          color: var(--text-primary, #f0f2f5);
          font-weight: 600;
        }

        .progress-bar {
          height: 6px;
          background: var(--bg-tertiary, #1a1d24);
          border-radius: 3px;
          overflow: hidden;
        }

        .progress-fill {
          height: 100%;
          border-radius: 3px;
          transition: width 0.3s ease;
        }

        .progress-fill.warning {
          background: #f59e0b;
        }

        .progress-fill.danger {
          background: #ef4444;
        }

        .history-section {
          padding: 20px;
          border-top: 1px solid var(--border-primary, #23262f);
        }

        .history-title {
          display: flex;
          align-items: center;
          gap: 8px;
          font-size: 14px;
          font-weight: 600;
          color: var(--text-primary, #f0f2f5);
          margin: 0 0 16px;
        }

        .history-title svg {
          width: 16px;
          height: 16px;
          color: var(--text-secondary, #8b919e);
        }

        .history-list {
          display: flex;
          flex-direction: column;
          gap: 12px;
        }

        .history-item {
          display: flex;
          align-items: center;
          justify-content: space-between;
          padding: 12px;
          background: var(--bg-tertiary, #1a1d24);
          border-radius: 8px;
        }

        .history-month {
          font-size: 13px;
          font-weight: 500;
          color: var(--text-primary, #f0f2f5);
        }

        .history-cost {
          font-size: 14px;
          font-weight: 600;
          color: var(--accent-primary, #6366f1);
        }
      `}</style>

      <div className="dashboard-header">
        <h3 className="dashboard-title">
          <TrendingUp />
          Current Usage
        </h3>
        {usage?.period_start && usage?.period_end && (
          <span className="period-label">
            {new Date(usage.period_start).toLocaleDateString()} - {new Date(usage.period_end).toLocaleDateString()}
          </span>
        )}
      </div>

      <div className="metrics-grid">
        {Object.entries(metrics).map(([key, metric]) => {
          const config = METRIC_CONFIG[key];
          if (!config) return null;

          const Icon = config.icon;
          const percentage = metric.percentage_used || 0;
          const isWarning = percentage >= 75 && percentage < 90;
          const isDanger = percentage >= 90;

          return (
            <div key={key} className="metric-item">
              <div
                className="metric-icon"
                style={{
                  background: `${config.color}15`,
                  color: config.color,
                }}
              >
                <Icon />
              </div>
              <div className="metric-content">
                <div className="metric-header">
                  <span className="metric-label">{metric.name}</span>
                  <span className="metric-value">
                    <strong>{metric.count.toLocaleString()}</strong>
                    {metric.limit !== null && (
                      <> / {metric.limit.toLocaleString()}</>
                    )}
                    {metric.limit === null && <> (unlimited)</>}
                  </span>
                </div>
                {metric.limit !== null && (
                  <div className="progress-bar">
                    <div
                      className={`progress-fill ${isDanger ? 'danger' : isWarning ? 'warning' : ''}`}
                      style={{
                        width: `${Math.min(100, percentage)}%`,
                        background: isDanger ? undefined : isWarning ? undefined : config.color,
                      }}
                    />
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>

      {history.length > 0 && (
        <div className="history-section">
          <h4 className="history-title">
            <TrendingUp />
            Recent Months
          </h4>
          <div className="history-list">
            {history.slice(0, 3).map((item, index) => (
              <div key={index} className="history-item">
                <span className="history-month">{item.month_name}</span>
                <span className="history-cost">{item.total_cost_formatted}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
