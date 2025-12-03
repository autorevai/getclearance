/**
 * Device Risk Card Component
 *
 * Slide-out panel showing detailed device fingerprint and risk analysis.
 */

import React from 'react';
import {
  X,
  Shield,
  Globe,
  Monitor,
  Smartphone,
  AlertTriangle,
  MapPin,
  Clock,
  Hash,
  Server,
  CheckCircle,
  XCircle,
} from 'lucide-react';

const RISK_CONFIG = {
  low: { label: 'Low Risk', color: '#22c55e', bg: 'rgba(34, 197, 94, 0.1)' },
  medium: { label: 'Medium Risk', color: '#f59e0b', bg: 'rgba(245, 158, 11, 0.1)' },
  high: { label: 'High Risk', color: '#ef4444', bg: 'rgba(239, 68, 68, 0.1)' },
};

export default function DeviceRiskCard({ device, onClose }) {
  if (!device) return null;

  const risk = RISK_CONFIG[device.risk_level] || RISK_CONFIG.low;
  const DeviceIcon = device.device_type === 'mobile' ? Smartphone : Monitor;

  const formatDate = (date) => {
    if (!date) return '—';
    return new Date(date).toLocaleString();
  };

  return (
    <div className="device-risk-card-overlay" onClick={onClose}>
      <style>{`
        .device-risk-card-overlay {
          position: fixed;
          top: 0;
          left: 0;
          right: 0;
          bottom: 0;
          background: rgba(0, 0, 0, 0.5);
          z-index: 1000;
          display: flex;
          justify-content: flex-end;
        }

        .device-risk-card {
          width: 480px;
          max-width: 100%;
          height: 100%;
          background: var(--bg-primary, #0a0b0e);
          border-left: 1px solid var(--border-primary, #23262f);
          overflow-y: auto;
          animation: slideIn 0.2s ease-out;
        }

        @keyframes slideIn {
          from {
            transform: translateX(100%);
          }
          to {
            transform: translateX(0);
          }
        }

        .card-header {
          display: flex;
          align-items: center;
          justify-content: space-between;
          padding: 20px 24px;
          border-bottom: 1px solid var(--border-primary, #23262f);
          background: var(--bg-secondary, #111318);
          position: sticky;
          top: 0;
          z-index: 10;
        }

        .card-title {
          font-size: 18px;
          font-weight: 600;
          color: var(--text-primary, #f0f2f5);
          margin: 0;
        }

        .close-btn {
          width: 32px;
          height: 32px;
          display: flex;
          align-items: center;
          justify-content: center;
          background: transparent;
          border: none;
          color: var(--text-secondary, #8b919e);
          cursor: pointer;
          border-radius: 6px;
          transition: all 0.15s;
        }

        .close-btn:hover {
          background: var(--bg-tertiary, #1a1d24);
          color: var(--text-primary, #f0f2f5);
        }

        .close-btn svg {
          width: 20px;
          height: 20px;
        }

        .card-content {
          padding: 24px;
        }

        .risk-banner {
          display: flex;
          align-items: center;
          gap: 16px;
          padding: 20px;
          border-radius: 12px;
          margin-bottom: 24px;
        }

        .risk-icon {
          width: 48px;
          height: 48px;
          border-radius: 12px;
          display: flex;
          align-items: center;
          justify-content: center;
        }

        .risk-icon svg {
          width: 24px;
          height: 24px;
        }

        .risk-info {
          flex: 1;
        }

        .risk-label {
          font-size: 16px;
          font-weight: 600;
          margin-bottom: 4px;
        }

        .risk-score {
          font-size: 13px;
          opacity: 0.8;
        }

        .section {
          margin-bottom: 24px;
        }

        .section-title {
          font-size: 12px;
          font-weight: 600;
          color: var(--text-secondary, #8b919e);
          text-transform: uppercase;
          letter-spacing: 0.5px;
          margin-bottom: 12px;
        }

        .info-grid {
          display: grid;
          grid-template-columns: repeat(2, 1fr);
          gap: 12px;
        }

        .info-item {
          background: var(--bg-secondary, #111318);
          border: 1px solid var(--border-primary, #23262f);
          border-radius: 8px;
          padding: 12px;
        }

        .info-item.full-width {
          grid-column: 1 / -1;
        }

        .info-label {
          display: flex;
          align-items: center;
          gap: 6px;
          font-size: 12px;
          color: var(--text-secondary, #8b919e);
          margin-bottom: 6px;
        }

        .info-label svg {
          width: 12px;
          height: 12px;
        }

        .info-value {
          font-size: 14px;
          color: var(--text-primary, #f0f2f5);
          font-weight: 500;
        }

        .info-value.mono {
          font-family: monospace;
        }

        .flags-grid {
          display: grid;
          grid-template-columns: repeat(2, 1fr);
          gap: 8px;
        }

        .flag-item {
          display: flex;
          align-items: center;
          gap: 8px;
          padding: 10px 12px;
          background: var(--bg-secondary, #111318);
          border: 1px solid var(--border-primary, #23262f);
          border-radius: 8px;
          font-size: 13px;
        }

        .flag-item svg {
          width: 16px;
          height: 16px;
        }

        .flag-item.active {
          border-color: rgba(239, 68, 68, 0.3);
          background: rgba(239, 68, 68, 0.05);
        }

        .flag-item.active svg {
          color: #ef4444;
        }

        .flag-item.inactive {
          color: var(--text-secondary, #8b919e);
        }

        .flag-item.inactive svg {
          color: #22c55e;
        }

        .flags-list {
          display: flex;
          flex-wrap: wrap;
          gap: 8px;
          margin-top: 12px;
        }

        .flag-tag {
          display: inline-flex;
          align-items: center;
          gap: 4px;
          padding: 4px 10px;
          background: rgba(239, 68, 68, 0.1);
          color: #ef4444;
          border-radius: 4px;
          font-size: 12px;
          font-weight: 500;
        }

        .flag-tag svg {
          width: 12px;
          height: 12px;
        }

        .flag-tag.vpn { background: rgba(245, 158, 11, 0.1); color: #f59e0b; }
        .flag-tag.proxy { background: rgba(245, 158, 11, 0.1); color: #f59e0b; }
        .flag-tag.tor { background: rgba(239, 68, 68, 0.1); color: #ef4444; }
        .flag-tag.bot { background: rgba(239, 68, 68, 0.1); color: #ef4444; }
        .flag-tag.datacenter { background: rgba(99, 102, 241, 0.1); color: #6366f1; }
      `}</style>

      <div className="device-risk-card" onClick={(e) => e.stopPropagation()}>
        <div className="card-header">
          <h2 className="card-title">Device Analysis</h2>
          <button className="close-btn" onClick={onClose}>
            <X />
          </button>
        </div>

        <div className="card-content">
          {/* Risk Banner */}
          <div
            className="risk-banner"
            style={{ background: risk.bg, color: risk.color }}
          >
            <div
              className="risk-icon"
              style={{ background: `${risk.color}20` }}
            >
              <Shield />
            </div>
            <div className="risk-info">
              <div className="risk-label">{risk.label}</div>
              <div className="risk-score">
                Fraud Score: {device.fraud_score || 0} / Risk Score: {device.risk_score || 0}
              </div>
            </div>
          </div>

          {/* IP Information */}
          <div className="section">
            <h3 className="section-title">IP Information</h3>
            <div className="info-grid">
              <div className="info-item full-width">
                <div className="info-label">
                  <Globe /> IP Address
                </div>
                <div className="info-value mono">{device.ip_address}</div>
              </div>
              <div className="info-item">
                <div className="info-label">
                  <MapPin /> Location
                </div>
                <div className="info-value">
                  {device.city && device.country_code
                    ? `${device.city}, ${device.country_code}`
                    : '—'}
                </div>
              </div>
              <div className="info-item">
                <div className="info-label">
                  <Server /> ISP
                </div>
                <div className="info-value">{device.isp || '—'}</div>
              </div>
            </div>
          </div>

          {/* Network Flags */}
          <div className="section">
            <h3 className="section-title">Network Analysis</h3>
            <div className="flags-grid">
              <div className={`flag-item ${device.is_vpn ? 'active' : 'inactive'}`}>
                {device.is_vpn ? <XCircle /> : <CheckCircle />}
                VPN {device.is_vpn ? 'Detected' : 'Not Detected'}
              </div>
              <div className={`flag-item ${device.is_proxy ? 'active' : 'inactive'}`}>
                {device.is_proxy ? <XCircle /> : <CheckCircle />}
                Proxy {device.is_proxy ? 'Detected' : 'Not Detected'}
              </div>
              <div className={`flag-item ${device.is_tor ? 'active' : 'inactive'}`}>
                {device.is_tor ? <XCircle /> : <CheckCircle />}
                Tor {device.is_tor ? 'Detected' : 'Not Detected'}
              </div>
              <div className={`flag-item ${device.is_bot ? 'active' : 'inactive'}`}>
                {device.is_bot ? <XCircle /> : <CheckCircle />}
                Bot {device.is_bot ? 'Detected' : 'Not Detected'}
              </div>
            </div>
          </div>

          {/* Device Information */}
          <div className="section">
            <h3 className="section-title">Device Information</h3>
            <div className="info-grid">
              <div className="info-item">
                <div className="info-label">
                  <DeviceIcon /> Device Type
                </div>
                <div className="info-value">{device.device_type || 'Unknown'}</div>
              </div>
              <div className="info-item">
                <div className="info-label">
                  <Monitor /> Browser
                </div>
                <div className="info-value">{device.browser || 'Unknown'}</div>
              </div>
              <div className="info-item full-width">
                <div className="info-label">
                  <Server /> Operating System
                </div>
                <div className="info-value">{device.operating_system || 'Unknown'}</div>
              </div>
            </div>
          </div>

          {/* Session Info */}
          <div className="section">
            <h3 className="section-title">Session Details</h3>
            <div className="info-grid">
              <div className="info-item full-width">
                <div className="info-label">
                  <Hash /> Session ID
                </div>
                <div className="info-value mono" style={{ fontSize: 12, wordBreak: 'break-all' }}>
                  {device.session_id}
                </div>
              </div>
              <div className="info-item full-width">
                <div className="info-label">
                  <Clock /> Analyzed At
                </div>
                <div className="info-value">{formatDate(device.created_at)}</div>
              </div>
            </div>
          </div>

          {/* Risk Flags Summary */}
          {device.flags && device.flags.length > 0 && (
            <div className="section">
              <h3 className="section-title">Risk Flags</h3>
              <div className="flags-list">
                {device.flags.map((flag, index) => (
                  <span
                    key={index}
                    className={`flag-tag ${flag.toLowerCase().replace('_', '-')}`}
                  >
                    <AlertTriangle />
                    {flag.replace(/_/g, ' ')}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
