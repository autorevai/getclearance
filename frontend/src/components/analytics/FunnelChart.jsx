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

const FUNNEL_COLORS = ['#6366f1', '#8b5cf6', '#a855f7', '#10b981', '#ef4444'];

export default function FunnelChart({ data, isLoading }) {
  const chartData = data
    ? [
        { name: 'Submitted', value: data.submitted, label: 'Applications' },
        { name: 'Documents', value: data.documents_uploaded, label: 'With Documents' },
        { name: 'Screened', value: data.screening_complete, label: 'Screening Done' },
        { name: 'Approved', value: data.approved, label: 'Approved' },
        { name: 'Rejected', value: data.rejected, label: 'Rejected' },
      ]
    : [];

  // Calculate conversion rates
  const getConversionRate = (current, previous) => {
    if (!previous || previous === 0) return null;
    return Math.round((current / previous) * 100);
  };

  const CustomTooltip = ({ active, payload }) => {
    if (!active || !payload?.length) return null;

    const entry = payload[0];
    const currentIdx = chartData.findIndex((d) => d.name === entry.payload.name);
    const previousValue = currentIdx > 0 ? chartData[currentIdx - 1].value : null;
    const conversionRate = getConversionRate(entry.value, previousValue);

    return (
      <div className="funnel-tooltip">
        <div className="tooltip-label">{entry.payload.label}</div>
        <div className="tooltip-value">{entry.value.toLocaleString()}</div>
        {conversionRate !== null && (
          <div className="tooltip-rate">{conversionRate}% conversion</div>
        )}
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

        .funnel-tooltip {
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
          font-size: 18px;
          font-weight: 600;
          color: var(--text-primary, #f0f2f5);
        }

        .tooltip-rate {
          font-size: 12px;
          color: var(--success, #10b981);
          margin-top: 4px;
        }

        .spinner {
          animation: spin 1s linear infinite;
        }

        @keyframes spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
      `}</style>

      <div className="chart-title">Verification Funnel</div>

      <div className="chart-content">
        {isLoading ? (
          <div className="chart-loading">
            <Loader2 className="spinner" size={24} />
          </div>
        ) : chartData.length === 0 || chartData.every((d) => d.value === 0) ? (
          <div className="chart-empty">No data available for this period</div>
        ) : (
          <ResponsiveContainer width="100%" height="100%">
            <BarChart
              data={chartData}
              layout="vertical"
              margin={{ top: 5, right: 30, left: 80, bottom: 5 }}
            >
              <CartesianGrid strokeDasharray="3 3" stroke="#2a2f3a" horizontal={false} />
              <XAxis type="number" stroke="#5c6370" fontSize={12} tickLine={false} />
              <YAxis
                type="category"
                dataKey="name"
                stroke="#5c6370"
                fontSize={12}
                tickLine={false}
                axisLine={false}
              />
              <Tooltip content={<CustomTooltip />} cursor={{ fill: 'rgba(99, 102, 241, 0.1)' }} />
              <Bar dataKey="value" radius={[0, 4, 4, 0]} maxBarSize={40}>
                {chartData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={FUNNEL_COLORS[index % FUNNEL_COLORS.length]} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        )}
      </div>
    </div>
  );
}
