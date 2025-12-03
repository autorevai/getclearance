import React from 'react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from 'recharts';
import { Loader2 } from 'lucide-react';

const RISK_COLORS = {
  '0-20': '#10b981',
  '21-40': '#6ee7b7',
  '41-60': '#fbbf24',
  '61-80': '#f97316',
  '81-100': '#ef4444',
};

export default function RiskHistogram({ data, isLoading }) {
  const chartData = data?.data || [];

  const CustomTooltip = ({ active, payload }) => {
    if (!active || !payload?.length) return null;

    const entry = payload[0];
    return (
      <div className="risk-tooltip">
        <div className="tooltip-label">Risk Score {entry.payload.bucket}</div>
        <div className="tooltip-value">{entry.value.toLocaleString()} applicants</div>
      </div>
    );
  };

  return (
    <div className="chart-container">
      <style>{`
        .chart-container {
          background: var(--bg-secondary, #111318);
          border: 1px solid var(--border-color, #2a2f3a);
          border-radius: 12px;
          padding: 20px;
          height: 350px;
        }

        .chart-title {
          font-size: 15px;
          font-weight: 600;
          color: var(--text-primary, #f0f2f5);
          margin-bottom: 16px;
        }

        .chart-content {
          height: calc(100% - 40px);
        }

        .chart-loading {
          display: flex;
          align-items: center;
          justify-content: center;
          height: 100%;
          color: var(--text-secondary, #8b919e);
        }

        .chart-empty {
          display: flex;
          align-items: center;
          justify-content: center;
          height: 100%;
          color: var(--text-muted, #5c6370);
          font-size: 14px;
        }

        .risk-tooltip {
          background: var(--bg-secondary, #111318);
          border: 1px solid var(--border-color, #2a2f3a);
          border-radius: 8px;
          padding: 12px;
          box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
        }

        .tooltip-label {
          font-size: 12px;
          color: var(--text-muted, #5c6370);
          margin-bottom: 4px;
        }

        .tooltip-value {
          font-size: 14px;
          font-weight: 600;
          color: var(--text-primary, #f0f2f5);
        }

        .spinner {
          animation: spin 1s linear infinite;
        }

        @keyframes spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
      `}</style>

      <div className="chart-title">Risk Score Distribution</div>

      <div className="chart-content">
        {isLoading ? (
          <div className="chart-loading">
            <Loader2 className="spinner" size={24} />
          </div>
        ) : chartData.length === 0 || chartData.every((d) => d.count === 0) ? (
          <div className="chart-empty">No risk data available</div>
        ) : (
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={chartData} margin={{ top: 5, right: 20, left: 0, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#2a2f3a" vertical={false} />
              <XAxis
                dataKey="bucket"
                stroke="#5c6370"
                fontSize={12}
                tickLine={false}
                axisLine={false}
              />
              <YAxis stroke="#5c6370" fontSize={12} tickLine={false} axisLine={false} />
              <Tooltip content={<CustomTooltip />} cursor={{ fill: 'rgba(99, 102, 241, 0.1)' }} />
              <Bar dataKey="count" radius={[4, 4, 0, 0]} maxBarSize={60}>
                {chartData.map((entry, index) => (
                  <Cell
                    key={`cell-${index}`}
                    fill={RISK_COLORS[entry.bucket] || '#6366f1'}
                  />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        )}
      </div>
    </div>
  );
}
