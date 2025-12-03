/**
 * Fraud Statistics Component
 *
 * Displays fraud detection statistics in a grid of metric cards.
 */

import React from 'react';
import {
  Activity,
  AlertTriangle,
  Eye,
  Bot,
  Shield,
  Percent,
} from 'lucide-react';

export default function FraudStats({ stats }) {
  const metrics = [
    {
      label: 'Total Scans',
      value: stats?.total_scans || 0,
      icon: Activity,
      color: '#6366f1',
    },
    {
      label: 'High Risk',
      value: stats?.high_risk_count || 0,
      subValue: stats?.high_risk_pct ? `${stats.high_risk_pct.toFixed(1)}%` : null,
      icon: AlertTriangle,
      color: '#ef4444',
    },
    {
      label: 'VPN Detected',
      value: stats?.vpn_detected || 0,
      subValue: stats?.vpn_pct ? `${stats.vpn_pct.toFixed(1)}%` : null,
      icon: Eye,
      color: '#f59e0b',
    },
    {
      label: 'Bot Detected',
      value: stats?.bot_detected || 0,
      subValue: stats?.bot_pct ? `${stats.bot_pct.toFixed(1)}%` : null,
      icon: Bot,
      color: '#ef4444',
    },
    {
      label: 'Tor Detected',
      value: stats?.tor_detected || 0,
      subValue: stats?.tor_pct ? `${stats.tor_pct.toFixed(1)}%` : null,
      icon: Shield,
      color: '#ef4444',
    },
    {
      label: 'Avg Fraud Score',
      value: stats?.avg_fraud_score ? Math.round(stats.avg_fraud_score) : 0,
      icon: Percent,
      color: stats?.avg_fraud_score >= 70 ? '#ef4444' : stats?.avg_fraud_score >= 50 ? '#f59e0b' : '#22c55e',
    },
  ];

  return (
    <div className="fraud-stats">
      <style>{`
        .fraud-stats {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
          gap: 16px;
          margin-bottom: 24px;
        }

        .stat-card {
          background: var(--bg-secondary, #111318);
          border: 1px solid var(--border-primary, #23262f);
          border-radius: 12px;
          padding: 20px;
          display: flex;
          flex-direction: column;
          gap: 12px;
        }

        .stat-header {
          display: flex;
          align-items: center;
          justify-content: space-between;
        }

        .stat-label {
          font-size: 13px;
          color: var(--text-secondary, #8b919e);
          font-weight: 500;
        }

        .stat-icon {
          width: 32px;
          height: 32px;
          border-radius: 8px;
          display: flex;
          align-items: center;
          justify-content: center;
        }

        .stat-icon svg {
          width: 18px;
          height: 18px;
        }

        .stat-value-row {
          display: flex;
          align-items: baseline;
          gap: 8px;
        }

        .stat-value {
          font-size: 28px;
          font-weight: 600;
          color: var(--text-primary, #f0f2f5);
        }

        .stat-sub-value {
          font-size: 14px;
          color: var(--text-secondary, #8b919e);
        }

        .stat-period {
          font-size: 12px;
          color: var(--text-tertiary, #5c6370);
        }
      `}</style>

      {metrics.map((metric, index) => {
        const Icon = metric.icon;
        return (
          <div key={index} className="stat-card">
            <div className="stat-header">
              <span className="stat-label">{metric.label}</span>
              <div
                className="stat-icon"
                style={{ background: `${metric.color}15`, color: metric.color }}
              >
                <Icon />
              </div>
            </div>
            <div className="stat-value-row">
              <span className="stat-value">{metric.value.toLocaleString()}</span>
              {metric.subValue && (
                <span className="stat-sub-value">({metric.subValue})</span>
              )}
            </div>
            {stats?.period_days && (
              <span className="stat-period">Last {stats.period_days} days</span>
            )}
          </div>
        );
      })}
    </div>
  );
}
