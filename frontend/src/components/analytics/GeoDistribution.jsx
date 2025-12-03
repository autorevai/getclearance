import React from 'react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts';
import { Loader2 } from 'lucide-react';

// Country code to name mapping (common ones)
const COUNTRY_NAMES = {
  USA: 'United States',
  GBR: 'United Kingdom',
  CAN: 'Canada',
  AUS: 'Australia',
  DEU: 'Germany',
  FRA: 'France',
  JPN: 'Japan',
  CHN: 'China',
  IND: 'India',
  BRA: 'Brazil',
  MEX: 'Mexico',
  ESP: 'Spain',
  ITA: 'Italy',
  NLD: 'Netherlands',
  SGP: 'Singapore',
  HKG: 'Hong Kong',
  KOR: 'South Korea',
  RUS: 'Russia',
  UAE: 'UAE',
  SAU: 'Saudi Arabia',
};

export default function GeoDistribution({ data, isLoading }) {
  const chartData =
    data?.data?.map((item) => ({
      country: COUNTRY_NAMES[item.country] || item.country,
      code: item.country,
      count: item.count,
    })) || [];

  const CustomTooltip = ({ active, payload }) => {
    if (!active || !payload?.length) return null;

    const entry = payload[0];
    return (
      <div className="geo-tooltip">
        <div className="tooltip-label">{entry.payload.country}</div>
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

        .geo-tooltip {
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

      <div className="chart-title">Geographic Distribution</div>

      <div className="chart-content">
        {isLoading ? (
          <div className="chart-loading">
            <Loader2 className="spinner" size={24} />
          </div>
        ) : chartData.length === 0 ? (
          <div className="chart-empty">No geographic data available</div>
        ) : (
          <ResponsiveContainer width="100%" height="100%">
            <BarChart
              data={chartData.slice(0, 10)}
              layout="vertical"
              margin={{ top: 5, right: 30, left: 100, bottom: 5 }}
            >
              <CartesianGrid strokeDasharray="3 3" stroke="#2a2f3a" horizontal={false} />
              <XAxis type="number" stroke="#5c6370" fontSize={12} tickLine={false} />
              <YAxis
                type="category"
                dataKey="country"
                stroke="#5c6370"
                fontSize={12}
                tickLine={false}
                axisLine={false}
                width={90}
              />
              <Tooltip content={<CustomTooltip />} cursor={{ fill: 'rgba(99, 102, 241, 0.1)' }} />
              <Bar dataKey="count" fill="#6366f1" radius={[0, 4, 4, 0]} maxBarSize={30} />
            </BarChart>
          </ResponsiveContainer>
        )}
      </div>
    </div>
  );
}
