import React, { useState, useMemo } from 'react';
import {
  BarChart3,
  Download,
  Calendar,
  RefreshCw,
  Loader2,
} from 'lucide-react';
import {
  useAllAnalytics,
  useExportAnalytics,
} from '../../hooks';
import OverviewCards from './OverviewCards';
import TrendsChart from './TrendsChart';
import FunnelChart from './FunnelChart';
import GeoDistribution from './GeoDistribution';
import RiskHistogram from './RiskHistogram';
import SLAGauge from './SLAGauge';

const DATE_PRESETS = [
  { label: 'Last 7 days', value: 7 },
  { label: 'Last 30 days', value: 30 },
  { label: 'Last 90 days', value: 90 },
  { label: 'Custom', value: 'custom' },
];

const GRANULARITY_OPTIONS = [
  { label: 'Day', value: 'day' },
  { label: 'Week', value: 'week' },
  { label: 'Month', value: 'month' },
];

export default function AnalyticsPage() {
  const [datePreset, setDatePreset] = useState(30);
  const [customDateRange, setCustomDateRange] = useState({ start: '', end: '' });
  const [granularity, setGranularity] = useState('day');
  const [showDateMenu, setShowDateMenu] = useState(false);

  // Calculate date range
  const { startDate, endDate } = useMemo(() => {
    if (datePreset === 'custom' && customDateRange.start && customDateRange.end) {
      return {
        startDate: new Date(customDateRange.start),
        endDate: new Date(customDateRange.end),
      };
    }
    const end = new Date();
    const start = new Date();
    start.setDate(start.getDate() - (typeof datePreset === 'number' ? datePreset : 30));
    return { startDate: start, endDate: end };
  }, [datePreset, customDateRange]);

  // Fetch all analytics data in a single request (fast!)
  const {
    overview,
    funnel,
    trends,
    geography,
    risk,
    sla,
    isLoading,
    refetch,
  } = useAllAnalytics(startDate, endDate, granularity);

  const exportAnalytics = useExportAnalytics();

  const handleRefresh = () => {
    refetch();
  };

  const handleExport = () => {
    exportAnalytics.mutate({ startDate, endDate, format: 'csv' });
  };

  const handleDatePresetChange = (preset) => {
    setDatePreset(preset);
    setShowDateMenu(false);
  };

  const currentPresetLabel = DATE_PRESETS.find(
    (p) => p.value === datePreset
  )?.label || 'Last 30 days';

  return (
    <div className="analytics-page">
      <style>{`
        .analytics-page {
          max-width: 1400px;
          margin: 0 auto;
        }

        .analytics-header {
          display: flex;
          align-items: flex-start;
          justify-content: space-between;
          gap: 24px;
          margin-bottom: 24px;
        }

        .analytics-title-section {
          display: flex;
          align-items: center;
          gap: 12px;
        }

        .analytics-icon {
          width: 32px;
          height: 32px;
          color: var(--accent-primary, #6366f1);
        }

        .analytics-title {
          font-size: 24px;
          font-weight: 600;
          color: var(--text-primary, #f0f2f5);
          margin: 0;
        }

        .analytics-subtitle {
          font-size: 14px;
          color: var(--text-secondary, #8b919e);
          margin: 4px 0 0;
        }

        .analytics-controls {
          display: flex;
          gap: 12px;
          align-items: center;
          flex-wrap: wrap;
        }

        .control-group {
          display: flex;
          align-items: center;
          gap: 8px;
        }

        .control-label {
          font-size: 13px;
          color: var(--text-muted, #5c6370);
        }

        .date-selector {
          position: relative;
        }

        .date-btn {
          display: flex;
          align-items: center;
          gap: 8px;
          padding: 8px 14px;
          background: var(--bg-secondary, #111318);
          border: 1px solid var(--border-color, #2a2f3a);
          border-radius: 8px;
          color: var(--text-primary, #f0f2f5);
          font-size: 14px;
          cursor: pointer;
          transition: all 0.15s;
          font-family: inherit;
        }

        .date-btn:hover {
          background: var(--bg-hover, #22262f);
          border-color: var(--accent-primary, #6366f1);
        }

        .date-btn svg {
          width: 16px;
          height: 16px;
          color: var(--text-muted, #5c6370);
        }

        .date-menu {
          position: absolute;
          top: 100%;
          right: 0;
          margin-top: 4px;
          background: var(--bg-secondary, #111318);
          border: 1px solid var(--border-color, #2a2f3a);
          border-radius: 8px;
          padding: 8px;
          min-width: 180px;
          z-index: 100;
          box-shadow: 0 8px 24px rgba(0, 0, 0, 0.3);
        }

        .date-menu-item {
          padding: 10px 12px;
          border-radius: 6px;
          font-size: 14px;
          color: var(--text-secondary, #8b919e);
          cursor: pointer;
          transition: all 0.15s;
        }

        .date-menu-item:hover {
          background: var(--bg-hover, #22262f);
          color: var(--text-primary, #f0f2f5);
        }

        .date-menu-item.active {
          background: var(--accent-glow, rgba(99, 102, 241, 0.1));
          color: var(--accent-primary, #6366f1);
        }

        .custom-date-inputs {
          display: flex;
          gap: 8px;
          padding: 8px 12px;
          border-top: 1px solid var(--border-color, #2a2f3a);
          margin-top: 8px;
        }

        .custom-date-input {
          flex: 1;
          padding: 8px;
          background: var(--bg-tertiary, #1a1d24);
          border: 1px solid var(--border-color, #2a2f3a);
          border-radius: 6px;
          color: var(--text-primary, #f0f2f5);
          font-size: 13px;
          font-family: inherit;
        }

        .custom-date-input:focus {
          outline: none;
          border-color: var(--accent-primary, #6366f1);
        }

        .granularity-select {
          padding: 8px 12px;
          background: var(--bg-secondary, #111318);
          border: 1px solid var(--border-color, #2a2f3a);
          border-radius: 8px;
          color: var(--text-primary, #f0f2f5);
          font-size: 14px;
          cursor: pointer;
          font-family: inherit;
        }

        .granularity-select:focus {
          outline: none;
          border-color: var(--accent-primary, #6366f1);
        }

        .action-btn {
          display: flex;
          align-items: center;
          gap: 8px;
          padding: 8px 14px;
          background: var(--bg-secondary, #111318);
          border: 1px solid var(--border-color, #2a2f3a);
          border-radius: 8px;
          color: var(--text-primary, #f0f2f5);
          font-size: 14px;
          cursor: pointer;
          transition: all 0.15s;
          font-family: inherit;
        }

        .action-btn:hover:not(:disabled) {
          background: var(--bg-hover, #22262f);
          border-color: var(--accent-primary, #6366f1);
        }

        .action-btn:disabled {
          opacity: 0.6;
          cursor: not-allowed;
        }

        .action-btn.primary {
          background: var(--accent-primary, #6366f1);
          border-color: var(--accent-primary, #6366f1);
          color: white;
        }

        .action-btn.primary:hover:not(:disabled) {
          background: var(--accent-hover, #5558e8);
        }

        .action-btn svg {
          width: 16px;
          height: 16px;
        }

        .charts-grid {
          display: grid;
          grid-template-columns: repeat(2, 1fr);
          gap: 20px;
        }

        @media (max-width: 1024px) {
          .charts-grid {
            grid-template-columns: 1fr;
          }
        }

        @media (max-width: 768px) {
          .analytics-header {
            flex-direction: column;
          }

          .analytics-controls {
            width: 100%;
            justify-content: flex-start;
          }
        }

        .spinner {
          animation: spin 1s linear infinite;
        }

        @keyframes spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
      `}</style>

      <div className="analytics-header">
        <div className="analytics-title-section">
          <BarChart3 className="analytics-icon" />
          <div>
            <h1 className="analytics-title">Analytics</h1>
            <p className="analytics-subtitle">
              Compliance metrics and verification insights
            </p>
          </div>
        </div>

        <div className="analytics-controls">
          <div className="control-group">
            <span className="control-label">Period:</span>
            <div className="date-selector">
              <button className="date-btn" onClick={() => setShowDateMenu(!showDateMenu)}>
                <Calendar />
                {currentPresetLabel}
              </button>

              {showDateMenu && (
                <div className="date-menu">
                  {DATE_PRESETS.map((preset) => (
                    <div
                      key={preset.value}
                      className={`date-menu-item ${datePreset === preset.value ? 'active' : ''}`}
                      onClick={() => handleDatePresetChange(preset.value)}
                    >
                      {preset.label}
                    </div>
                  ))}

                  {datePreset === 'custom' && (
                    <div className="custom-date-inputs">
                      <input
                        type="date"
                        className="custom-date-input"
                        value={customDateRange.start}
                        onChange={(e) =>
                          setCustomDateRange((prev) => ({ ...prev, start: e.target.value }))
                        }
                      />
                      <input
                        type="date"
                        className="custom-date-input"
                        value={customDateRange.end}
                        onChange={(e) =>
                          setCustomDateRange((prev) => ({ ...prev, end: e.target.value }))
                        }
                      />
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>

          <div className="control-group">
            <span className="control-label">Group by:</span>
            <select
              className="granularity-select"
              value={granularity}
              onChange={(e) => setGranularity(e.target.value)}
            >
              {GRANULARITY_OPTIONS.map((opt) => (
                <option key={opt.value} value={opt.value}>
                  {opt.label}
                </option>
              ))}
            </select>
          </div>

          <button
            className="action-btn"
            onClick={handleRefresh}
            disabled={isLoading}
          >
            <RefreshCw className={isLoading ? 'spinner' : ''} />
            Refresh
          </button>

          <button
            className="action-btn primary"
            onClick={handleExport}
            disabled={exportAnalytics.isPending}
          >
            {exportAnalytics.isPending ? (
              <>
                <Loader2 className="spinner" />
                Exporting...
              </>
            ) : (
              <>
                <Download />
                Export CSV
              </>
            )}
          </button>
        </div>
      </div>

      <OverviewCards data={overview} isLoading={isLoading} />

      <div className="charts-grid">
        <TrendsChart
          data={trends}
          isLoading={isLoading}
          granularity={granularity}
        />
        <FunnelChart data={funnel} isLoading={isLoading} />
        <GeoDistribution data={geography} isLoading={isLoading} />
        <RiskHistogram data={risk} isLoading={isLoading} />
        <SLAGauge data={sla} isLoading={isLoading} />
      </div>
    </div>
  );
}
