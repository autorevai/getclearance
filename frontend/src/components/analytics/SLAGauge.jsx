import React from 'react';
import { Loader2, Clock, AlertTriangle } from 'lucide-react';

export default function SLAGauge({ data, isLoading }) {
  const onTimeRate = data?.on_time_rate ?? 0;
  const avgResolutionTime = data?.avg_resolution_time_hours ?? 0;
  const atRiskCount = data?.at_risk_count ?? 0;

  // Calculate stroke offset for circular progress
  const circumference = 2 * Math.PI * 54; // radius = 54
  const strokeOffset = circumference - (onTimeRate / 100) * circumference;

  // Determine color based on rate
  const getProgressColor = () => {
    if (onTimeRate >= 90) return 'var(--success, #10b981)';
    if (onTimeRate >= 70) return 'var(--warning, #f59e0b)';
    return 'var(--danger, #ef4444)';
  };

  return (
    <div className="sla-gauge-container">
      <style>{`
        .sla-gauge-container {
          background: var(--bg-secondary, #111318);
          border: 1px solid var(--border-color, #2a2f3a);
          border-radius: 12px;
          padding: 20px;
          height: 350px;
          display: flex;
          flex-direction: column;
        }

        .chart-title {
          font-size: 15px;
          font-weight: 600;
          color: var(--text-primary, #f0f2f5);
          margin-bottom: 16px;
        }

        .gauge-content {
          flex: 1;
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
        }

        .sla-ring {
          width: 160px;
          height: 160px;
          position: relative;
          margin-bottom: 24px;
        }

        .sla-ring svg {
          transform: rotate(-90deg);
        }

        .sla-ring-bg {
          fill: none;
          stroke: var(--bg-tertiary, #1a1d24);
          stroke-width: 10;
        }

        .sla-ring-progress {
          fill: none;
          stroke-width: 10;
          stroke-linecap: round;
          transition: stroke-dashoffset 0.5s ease;
        }

        .sla-ring-text {
          position: absolute;
          inset: 0;
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
        }

        .sla-percentage {
          font-size: 36px;
          font-weight: 700;
          color: var(--text-primary, #f0f2f5);
        }

        .sla-label {
          font-size: 13px;
          color: var(--text-muted, #5c6370);
        }

        .sla-stats {
          display: grid;
          grid-template-columns: 1fr 1fr;
          gap: 16px;
          width: 100%;
          text-align: center;
        }

        .sla-stat {
          padding: 12px;
          background: var(--bg-tertiary, #1a1d24);
          border-radius: 8px;
        }

        .sla-stat-icon {
          display: flex;
          align-items: center;
          justify-content: center;
          margin-bottom: 8px;
        }

        .sla-stat-value {
          font-size: 20px;
          font-weight: 600;
          color: var(--text-primary, #f0f2f5);
          margin-bottom: 4px;
        }

        .sla-stat-label {
          font-size: 12px;
          color: var(--text-muted, #5c6370);
        }

        .sla-stat.at-risk .sla-stat-icon {
          color: var(--warning, #f59e0b);
        }

        .sla-stat.breached .sla-stat-icon {
          color: var(--danger, #ef4444);
        }

        .sla-stat.avg-time .sla-stat-icon {
          color: var(--info, #3b82f6);
        }

        .chart-loading {
          display: flex;
          align-items: center;
          justify-content: center;
          height: 100%;
          color: var(--text-secondary, #8b919e);
        }

        .spinner {
          animation: spin 1s linear infinite;
        }

        @keyframes spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
      `}</style>

      <div className="chart-title">SLA Performance</div>

      {isLoading ? (
        <div className="chart-loading">
          <Loader2 className="spinner" size={24} />
        </div>
      ) : (
        <div className="gauge-content">
          <div className="sla-ring">
            <svg width="160" height="160" viewBox="0 0 160 160">
              <circle className="sla-ring-bg" cx="80" cy="80" r="54" />
              <circle
                className="sla-ring-progress"
                cx="80"
                cy="80"
                r="54"
                stroke={getProgressColor()}
                strokeDasharray={circumference}
                strokeDashoffset={strokeOffset}
              />
            </svg>
            <div className="sla-ring-text">
              <span className="sla-percentage">{Math.round(onTimeRate)}%</span>
              <span className="sla-label">On Time</span>
            </div>
          </div>

          <div className="sla-stats">
            <div className="sla-stat avg-time">
              <div className="sla-stat-icon">
                <Clock size={18} />
              </div>
              <div className="sla-stat-value">{avgResolutionTime.toFixed(1)}h</div>
              <div className="sla-stat-label">Avg Resolution</div>
            </div>
            <div className="sla-stat at-risk">
              <div className="sla-stat-icon">
                <AlertTriangle size={18} />
              </div>
              <div className="sla-stat-value">{atRiskCount}</div>
              <div className="sla-stat-label">At Risk</div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
