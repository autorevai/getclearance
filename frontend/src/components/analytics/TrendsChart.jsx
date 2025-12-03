import React from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';
import { Loader2 } from 'lucide-react';

export default function TrendsChart({ data, isLoading, granularity }) {
  const chartData = data?.data || [];

  // Format date for X axis
  const formatXAxis = (dateStr) => {
    if (!dateStr) return '';
    const date = new Date(dateStr);
    if (granularity === 'month') {
      return date.toLocaleDateString('en-US', { month: 'short' });
    }
    if (granularity === 'week') {
      return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
    }
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
  };

  const CustomTooltip = ({ active, payload, label }) => {
    if (!active || !payload?.length) return null;

    return (
      <div className="chart-tooltip">
        <div className="tooltip-label">{formatXAxis(label)}</div>
        {payload.map((entry, index) => (
          <div key={index} className="tooltip-item" style={{ color: entry.color }}>
            <span className="tooltip-name">{entry.name}:</span>
            <span className="tooltip-value">{entry.value}</span>
          </div>
        ))}
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

        .chart-tooltip {
          background: var(--bg-secondary, #111318);
          border: 1px solid var(--border-color, #2a2f3a);
          border-radius: 8px;
          padding: 12px;
          box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
        }

        .tooltip-label {
          font-size: 12px;
          color: var(--text-muted, #5c6370);
          margin-bottom: 8px;
        }

        .tooltip-item {
          display: flex;
          justify-content: space-between;
          gap: 16px;
          font-size: 13px;
          margin-bottom: 4px;
        }

        .tooltip-name {
          text-transform: capitalize;
        }

        .tooltip-value {
          font-weight: 600;
        }

        .spinner {
          animation: spin 1s linear infinite;
        }

        @keyframes spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
      `}</style>

      <div className="chart-title">Applications Over Time</div>

      <div className="chart-content">
        {isLoading ? (
          <div className="chart-loading">
            <Loader2 className="spinner" size={24} />
          </div>
        ) : chartData.length === 0 ? (
          <div className="chart-empty">No data available for this period</div>
        ) : (
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={chartData} margin={{ top: 5, right: 20, left: 0, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#2a2f3a" />
              <XAxis
                dataKey="date"
                tickFormatter={formatXAxis}
                stroke="#5c6370"
                fontSize={12}
                tickLine={false}
              />
              <YAxis stroke="#5c6370" fontSize={12} tickLine={false} axisLine={false} />
              <Tooltip content={<CustomTooltip />} />
              <Legend
                wrapperStyle={{ fontSize: '12px', paddingTop: '10px' }}
                iconType="circle"
                iconSize={8}
              />
              <Line
                type="monotone"
                dataKey="submitted"
                name="Submitted"
                stroke="#6366f1"
                strokeWidth={2}
                dot={false}
                activeDot={{ r: 4 }}
              />
              <Line
                type="monotone"
                dataKey="approved"
                name="Approved"
                stroke="#10b981"
                strokeWidth={2}
                dot={false}
                activeDot={{ r: 4 }}
              />
              <Line
                type="monotone"
                dataKey="rejected"
                name="Rejected"
                stroke="#ef4444"
                strokeWidth={2}
                dot={false}
                activeDot={{ r: 4 }}
              />
            </LineChart>
          </ResponsiveContainer>
        )}
      </div>
    </div>
  );
}
