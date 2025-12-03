/**
 * Device Intelligence Page
 *
 * Main page for device fingerprinting and fraud detection.
 * Shows fraud statistics, device list with filters, and IP lookup tool.
 */

import React, { useState, useMemo } from 'react';
import {
  Fingerprint,
  Search,
  Filter,
  Shield,
  AlertTriangle,
  Wifi,
  Globe,
  Monitor,
  Smartphone,
  Bot,
  Eye,
  ChevronRight,
} from 'lucide-react';
import { useDevices, useDeviceStats } from '../../hooks';
import { useDebounce } from '../../hooks/useDebounce';
import FraudStats from './FraudStats';
import IPLookup from './IPLookup';
import DeviceRiskCard from './DeviceRiskCard';

const RISK_CONFIG = {
  low: { label: 'Low', color: '#22c55e', bg: 'rgba(34, 197, 94, 0.1)' },
  medium: { label: 'Medium', color: '#f59e0b', bg: 'rgba(245, 158, 11, 0.1)' },
  high: { label: 'High', color: '#ef4444', bg: 'rgba(239, 68, 68, 0.1)' },
};

export default function DeviceIntelPage() {
  const [ipSearch, setIpSearch] = useState('');
  const [riskFilter, setRiskFilter] = useState('');
  const [showFilters, setShowFilters] = useState(false);
  const [showIPLookup, setShowIPLookup] = useState(false);
  const [selectedDevice, setSelectedDevice] = useState(null);

  const debouncedIpSearch = useDebounce(ipSearch, 300);

  const filters = useMemo(() => ({
    ...(debouncedIpSearch && { ip_address: debouncedIpSearch }),
    ...(riskFilter && { risk_level: riskFilter }),
    limit: 50,
  }), [debouncedIpSearch, riskFilter]);

  const { data, isLoading, error } = useDevices(filters);
  const { data: stats } = useDeviceStats(30);

  const devices = data?.items || [];

  return (
    <div className="device-intel-page">
      <style>{`
        .device-intel-page {
          max-width: 1400px;
          margin: 0 auto;
        }

        .page-header {
          display: flex;
          justify-content: space-between;
          align-items: flex-start;
          margin-bottom: 24px;
          gap: 16px;
          flex-wrap: wrap;
        }

        .page-title-section {
          display: flex;
          align-items: flex-start;
          gap: 12px;
        }

        .page-icon {
          width: 32px;
          height: 32px;
          color: var(--accent-primary, #6366f1);
        }

        .page-title {
          font-size: 24px;
          font-weight: 600;
          color: var(--text-primary, #f0f2f5);
          margin: 0;
        }

        .page-subtitle {
          font-size: 14px;
          color: var(--text-secondary, #8b919e);
          margin: 4px 0 0;
        }

        .header-actions {
          display: flex;
          gap: 12px;
          align-items: center;
        }

        .lookup-btn {
          display: flex;
          align-items: center;
          gap: 8px;
          padding: 10px 16px;
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

        .lookup-btn:hover {
          background: var(--accent-hover, #5558e3);
        }

        .lookup-btn svg {
          width: 16px;
          height: 16px;
        }

        .toolbar {
          display: flex;
          gap: 12px;
          margin-bottom: 24px;
          flex-wrap: wrap;
        }

        .search-wrapper {
          position: relative;
          flex: 1;
          min-width: 200px;
          max-width: 400px;
        }

        .search-wrapper svg {
          position: absolute;
          left: 12px;
          top: 50%;
          transform: translateY(-50%);
          width: 16px;
          height: 16px;
          color: var(--text-secondary, #8b919e);
        }

        .search-input {
          width: 100%;
          padding: 10px 12px 10px 40px;
          background: var(--bg-secondary, #111318);
          border: 1px solid var(--border-primary, #23262f);
          border-radius: 8px;
          color: var(--text-primary, #f0f2f5);
          font-size: 14px;
        }

        .filter-btn {
          display: flex;
          align-items: center;
          gap: 8px;
          padding: 10px 16px;
          background: var(--bg-secondary, #111318);
          border: 1px solid var(--border-primary, #23262f);
          border-radius: 8px;
          color: var(--text-secondary, #8b919e);
          font-size: 14px;
          cursor: pointer;
          transition: all 0.15s;
          font-family: inherit;
        }

        .filter-btn:hover,
        .filter-btn.active {
          background: var(--bg-tertiary, #1a1d24);
          color: var(--text-primary, #f0f2f5);
          border-color: var(--accent-primary, #6366f1);
        }

        .filter-btn svg {
          width: 16px;
          height: 16px;
        }

        .filters-panel {
          display: flex;
          gap: 12px;
          padding: 16px;
          background: var(--bg-secondary, #111318);
          border: 1px solid var(--border-primary, #23262f);
          border-radius: 8px;
          margin-bottom: 24px;
          flex-wrap: wrap;
        }

        .filter-select {
          padding: 8px 12px;
          background: var(--bg-tertiary, #1a1d24);
          border: 1px solid var(--border-primary, #23262f);
          border-radius: 6px;
          color: var(--text-primary, #f0f2f5);
          font-size: 13px;
          min-width: 150px;
          cursor: pointer;
          font-family: inherit;
        }

        .clear-filters-btn {
          padding: 8px 12px;
          background: transparent;
          border: none;
          color: var(--accent-primary, #6366f1);
          font-size: 13px;
          cursor: pointer;
          font-family: inherit;
        }

        .devices-table {
          background: var(--bg-secondary, #111318);
          border: 1px solid var(--border-primary, #23262f);
          border-radius: 12px;
          overflow: hidden;
        }

        .table-header {
          display: grid;
          grid-template-columns: 1.5fr 1fr 1fr 1fr 1.5fr 40px;
          gap: 16px;
          padding: 12px 20px;
          background: var(--bg-tertiary, #1a1d24);
          border-bottom: 1px solid var(--border-primary, #23262f);
        }

        .table-header-cell {
          font-size: 12px;
          font-weight: 600;
          color: var(--text-secondary, #8b919e);
          text-transform: uppercase;
          letter-spacing: 0.5px;
        }

        .device-row {
          display: grid;
          grid-template-columns: 1.5fr 1fr 1fr 1fr 1.5fr 40px;
          gap: 16px;
          padding: 16px 20px;
          border-bottom: 1px solid var(--border-primary, #23262f);
          cursor: pointer;
          transition: background 0.15s;
          align-items: center;
        }

        .device-row:last-child {
          border-bottom: none;
        }

        .device-row:hover {
          background: var(--bg-tertiary, #1a1d24);
        }

        .ip-cell {
          display: flex;
          flex-direction: column;
          gap: 4px;
        }

        .ip-address {
          font-size: 14px;
          font-weight: 500;
          color: var(--text-primary, #f0f2f5);
          font-family: monospace;
        }

        .ip-location {
          font-size: 12px;
          color: var(--text-secondary, #8b919e);
          display: flex;
          align-items: center;
          gap: 4px;
        }

        .ip-location svg {
          width: 12px;
          height: 12px;
        }

        .risk-badge {
          display: inline-flex;
          align-items: center;
          gap: 6px;
          padding: 4px 10px;
          border-radius: 20px;
          font-size: 12px;
          font-weight: 500;
          width: fit-content;
        }

        .risk-badge svg {
          width: 12px;
          height: 12px;
        }

        .fraud-score {
          font-size: 14px;
          font-weight: 600;
        }

        .fraud-score.low { color: #22c55e; }
        .fraud-score.medium { color: #f59e0b; }
        .fraud-score.high { color: #ef4444; }

        .device-info {
          display: flex;
          align-items: center;
          gap: 6px;
          font-size: 13px;
          color: var(--text-secondary, #8b919e);
        }

        .device-info svg {
          width: 14px;
          height: 14px;
        }

        .flags-cell {
          display: flex;
          gap: 8px;
          flex-wrap: wrap;
        }

        .flag-tag {
          display: inline-flex;
          align-items: center;
          gap: 4px;
          padding: 2px 8px;
          background: rgba(239, 68, 68, 0.1);
          color: #ef4444;
          border-radius: 4px;
          font-size: 11px;
          font-weight: 500;
        }

        .flag-tag svg {
          width: 10px;
          height: 10px;
        }

        .flag-tag.vpn { background: rgba(245, 158, 11, 0.1); color: #f59e0b; }
        .flag-tag.tor { background: rgba(239, 68, 68, 0.1); color: #ef4444; }
        .flag-tag.bot { background: rgba(239, 68, 68, 0.1); color: #ef4444; }
        .flag-tag.proxy { background: rgba(245, 158, 11, 0.1); color: #f59e0b; }

        .chevron-cell {
          color: var(--text-secondary, #8b919e);
        }

        .chevron-cell svg {
          width: 16px;
          height: 16px;
        }

        .empty-state {
          padding: 60px 20px;
          text-align: center;
        }

        .empty-icon {
          width: 48px;
          height: 48px;
          color: var(--text-secondary, #8b919e);
          margin-bottom: 16px;
        }

        .empty-title {
          font-size: 16px;
          font-weight: 500;
          color: var(--text-primary, #f0f2f5);
          margin: 0 0 8px;
        }

        .empty-message {
          font-size: 14px;
          color: var(--text-secondary, #8b919e);
          margin: 0;
        }

        .loading-state {
          padding: 60px 20px;
          text-align: center;
          color: var(--text-secondary, #8b919e);
        }

        .error-state {
          padding: 60px 20px;
          text-align: center;
          color: var(--error, #ef4444);
        }

        @media (max-width: 1200px) {
          .table-header,
          .device-row {
            grid-template-columns: 1.5fr 1fr 1fr 1.5fr 40px;
          }

          .table-header-cell:nth-child(3),
          .device-row > *:nth-child(3) {
            display: none;
          }
        }

        @media (max-width: 900px) {
          .table-header,
          .device-row {
            grid-template-columns: 1.5fr 1fr 1.5fr 40px;
          }

          .table-header-cell:nth-child(4),
          .device-row > *:nth-child(4) {
            display: none;
          }
        }
      `}</style>

      <div className="page-header">
        <div className="page-title-section">
          <Fingerprint className="page-icon" />
          <div>
            <h1 className="page-title">Device Intelligence</h1>
            <p className="page-subtitle">
              Device fingerprinting and fraud detection powered by IPQualityScore
            </p>
          </div>
        </div>
        <div className="header-actions">
          <button className="lookup-btn" onClick={() => setShowIPLookup(true)}>
            <Search />
            IP Lookup
          </button>
        </div>
      </div>

      {/* Fraud Statistics */}
      <FraudStats stats={stats} />

      <div className="toolbar">
        <div className="search-wrapper">
          <Search />
          <input
            type="text"
            className="search-input"
            placeholder="Search by IP address..."
            value={ipSearch}
            onChange={(e) => setIpSearch(e.target.value)}
          />
        </div>
        <button
          className={`filter-btn ${showFilters ? 'active' : ''}`}
          onClick={() => setShowFilters(!showFilters)}
        >
          <Filter />
          Filters
        </button>
      </div>

      {showFilters && (
        <div className="filters-panel">
          <select
            className="filter-select"
            value={riskFilter}
            onChange={(e) => setRiskFilter(e.target.value)}
          >
            <option value="">All Risk Levels</option>
            <option value="low">Low Risk</option>
            <option value="medium">Medium Risk</option>
            <option value="high">High Risk</option>
          </select>
          {riskFilter && (
            <button
              className="clear-filters-btn"
              onClick={() => setRiskFilter('')}
            >
              Clear Filters
            </button>
          )}
        </div>
      )}

      <div className="devices-table">
        <div className="table-header">
          <div className="table-header-cell">IP Address</div>
          <div className="table-header-cell">Risk Level</div>
          <div className="table-header-cell">Fraud Score</div>
          <div className="table-header-cell">Device</div>
          <div className="table-header-cell">Flags</div>
          <div className="table-header-cell"></div>
        </div>

        {isLoading ? (
          <div className="loading-state">Loading device data...</div>
        ) : error ? (
          <div className="error-state">Failed to load device data</div>
        ) : devices.length === 0 ? (
          <div className="empty-state">
            <Fingerprint className="empty-icon" />
            <h3 className="empty-title">No device scans yet</h3>
            <p className="empty-message">
              {ipSearch || riskFilter
                ? 'Try adjusting your filters'
                : 'Device fingerprints will appear here after analysis'}
            </p>
          </div>
        ) : (
          devices.map((device) => {
            const risk = RISK_CONFIG[device.risk_level] || RISK_CONFIG.low;
            const fraudLevel = device.fraud_score >= 85 ? 'high' : device.fraud_score >= 70 ? 'medium' : 'low';
            const DeviceIcon = device.device_type === 'mobile' ? Smartphone : Monitor;

            return (
              <div
                key={device.id}
                className="device-row"
                onClick={() => setSelectedDevice(device)}
              >
                <div className="ip-cell">
                  <span className="ip-address">{device.ip_address}</span>
                  {device.city && device.country_code && (
                    <span className="ip-location">
                      <Globe />
                      {device.city}, {device.country_code}
                    </span>
                  )}
                </div>
                <div>
                  <span
                    className="risk-badge"
                    style={{ color: risk.color, background: risk.bg }}
                  >
                    <Shield />
                    {risk.label}
                  </span>
                </div>
                <div>
                  <span className={`fraud-score ${fraudLevel}`}>
                    {device.fraud_score || 0}
                  </span>
                </div>
                <div className="device-info">
                  <DeviceIcon />
                  {device.browser || 'Unknown'} / {device.operating_system || 'Unknown'}
                </div>
                <div className="flags-cell">
                  {device.is_vpn && (
                    <span className="flag-tag vpn">
                      <Eye /> VPN
                    </span>
                  )}
                  {device.is_tor && (
                    <span className="flag-tag tor">
                      <AlertTriangle /> Tor
                    </span>
                  )}
                  {device.is_bot && (
                    <span className="flag-tag bot">
                      <Bot /> Bot
                    </span>
                  )}
                  {device.is_proxy && (
                    <span className="flag-tag proxy">
                      <Wifi /> Proxy
                    </span>
                  )}
                </div>
                <div className="chevron-cell">
                  <ChevronRight />
                </div>
              </div>
            );
          })
        )}
      </div>

      {/* IP Lookup Modal */}
      {showIPLookup && (
        <IPLookup onClose={() => setShowIPLookup(false)} />
      )}

      {/* Device Detail Drawer */}
      {selectedDevice && (
        <DeviceRiskCard
          device={selectedDevice}
          onClose={() => setSelectedDevice(null)}
        />
      )}
    </div>
  );
}
