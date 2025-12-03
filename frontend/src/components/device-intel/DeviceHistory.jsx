/**
 * Device History Component
 *
 * Shows device fingerprint history for an applicant.
 * Used in ApplicantDetail page.
 */

import React, { useState } from 'react';
import {
  Fingerprint,
  Shield,
  Globe,
  Monitor,
  Smartphone,
  Eye,
  Bot,
  AlertTriangle,
  ChevronRight,
  Wifi,
} from 'lucide-react';
import { useApplicantDevices } from '../../hooks';
import DeviceRiskCard from './DeviceRiskCard';

const RISK_CONFIG = {
  low: { label: 'Low', color: '#22c55e', bg: 'rgba(34, 197, 94, 0.1)' },
  medium: { label: 'Medium', color: '#f59e0b', bg: 'rgba(245, 158, 11, 0.1)' },
  high: { label: 'High', color: '#ef4444', bg: 'rgba(239, 68, 68, 0.1)' },
};

export default function DeviceHistory({ applicantId }) {
  const [selectedDevice, setSelectedDevice] = useState(null);
  const { data, isLoading, error } = useApplicantDevices(applicantId);

  if (isLoading) {
    return (
      <div className="device-history-loading">
        <style>{`
          .device-history-loading {
            padding: 40px;
            text-align: center;
            color: var(--text-secondary, #8b919e);
          }
        `}</style>
        Loading device history...
      </div>
    );
  }

  if (error) {
    return (
      <div className="device-history-error">
        <style>{`
          .device-history-error {
            padding: 40px;
            text-align: center;
            color: var(--error, #ef4444);
          }
        `}</style>
        Failed to load device history
      </div>
    );
  }

  const devices = data?.devices || [];

  return (
    <div className="device-history">
      <style>{`
        .device-history {
          background: var(--bg-secondary, #111318);
          border: 1px solid var(--border-primary, #23262f);
          border-radius: 12px;
          overflow: hidden;
        }

        .history-header {
          display: flex;
          align-items: center;
          justify-content: space-between;
          padding: 16px 20px;
          border-bottom: 1px solid var(--border-primary, #23262f);
        }

        .history-title {
          display: flex;
          align-items: center;
          gap: 10px;
          font-size: 14px;
          font-weight: 600;
          color: var(--text-primary, #f0f2f5);
          margin: 0;
        }

        .history-title svg {
          width: 18px;
          height: 18px;
          color: var(--accent-primary, #6366f1);
        }

        .history-count {
          font-size: 12px;
          color: var(--text-secondary, #8b919e);
        }

        .risk-alerts {
          display: flex;
          gap: 8px;
        }

        .risk-alert {
          display: inline-flex;
          align-items: center;
          gap: 4px;
          padding: 4px 8px;
          border-radius: 4px;
          font-size: 11px;
          font-weight: 500;
        }

        .risk-alert svg {
          width: 12px;
          height: 12px;
        }

        .risk-alert.high-risk {
          background: rgba(239, 68, 68, 0.1);
          color: #ef4444;
        }

        .risk-alert.vpn {
          background: rgba(245, 158, 11, 0.1);
          color: #f59e0b;
        }

        .risk-alert.tor {
          background: rgba(239, 68, 68, 0.1);
          color: #ef4444;
        }

        .device-list {
          max-height: 400px;
          overflow-y: auto;
        }

        .device-item {
          display: flex;
          align-items: center;
          gap: 16px;
          padding: 14px 20px;
          border-bottom: 1px solid var(--border-primary, #23262f);
          cursor: pointer;
          transition: background 0.15s;
        }

        .device-item:last-child {
          border-bottom: none;
        }

        .device-item:hover {
          background: var(--bg-tertiary, #1a1d24);
        }

        .device-icon {
          width: 40px;
          height: 40px;
          border-radius: 8px;
          display: flex;
          align-items: center;
          justify-content: center;
          background: var(--bg-tertiary, #1a1d24);
          color: var(--text-secondary, #8b919e);
        }

        .device-icon svg {
          width: 20px;
          height: 20px;
        }

        .device-info {
          flex: 1;
          min-width: 0;
        }

        .device-ip {
          font-size: 14px;
          font-weight: 500;
          color: var(--text-primary, #f0f2f5);
          font-family: monospace;
          margin-bottom: 2px;
        }

        .device-meta {
          font-size: 12px;
          color: var(--text-secondary, #8b919e);
          display: flex;
          align-items: center;
          gap: 8px;
        }

        .device-meta svg {
          width: 12px;
          height: 12px;
        }

        .device-flags {
          display: flex;
          gap: 6px;
        }

        .device-flag {
          display: inline-flex;
          align-items: center;
          gap: 3px;
          padding: 2px 6px;
          border-radius: 4px;
          font-size: 10px;
          font-weight: 500;
        }

        .device-flag svg {
          width: 10px;
          height: 10px;
        }

        .device-flag.vpn {
          background: rgba(245, 158, 11, 0.1);
          color: #f59e0b;
        }

        .device-flag.tor {
          background: rgba(239, 68, 68, 0.1);
          color: #ef4444;
        }

        .device-flag.bot {
          background: rgba(239, 68, 68, 0.1);
          color: #ef4444;
        }

        .device-flag.proxy {
          background: rgba(245, 158, 11, 0.1);
          color: #f59e0b;
        }

        .device-risk {
          display: flex;
          flex-direction: column;
          align-items: flex-end;
          gap: 4px;
        }

        .risk-badge {
          display: inline-flex;
          align-items: center;
          gap: 4px;
          padding: 4px 8px;
          border-radius: 12px;
          font-size: 11px;
          font-weight: 500;
        }

        .risk-badge svg {
          width: 10px;
          height: 10px;
        }

        .device-date {
          font-size: 11px;
          color: var(--text-tertiary, #5c6370);
        }

        .chevron {
          color: var(--text-secondary, #8b919e);
        }

        .chevron svg {
          width: 16px;
          height: 16px;
        }

        .empty-state {
          padding: 40px 20px;
          text-align: center;
        }

        .empty-state svg {
          width: 40px;
          height: 40px;
          color: var(--text-secondary, #8b919e);
          margin-bottom: 12px;
        }

        .empty-title {
          font-size: 14px;
          font-weight: 500;
          color: var(--text-primary, #f0f2f5);
          margin: 0 0 4px;
        }

        .empty-message {
          font-size: 13px;
          color: var(--text-secondary, #8b919e);
          margin: 0;
        }
      `}</style>

      <div className="history-header">
        <h3 className="history-title">
          <Fingerprint />
          Device History
          <span className="history-count">({devices.length})</span>
        </h3>
        {(data?.has_high_risk || data?.has_vpn || data?.has_tor) && (
          <div className="risk-alerts">
            {data.has_high_risk && (
              <span className="risk-alert high-risk">
                <AlertTriangle /> High Risk
              </span>
            )}
            {data.has_vpn && (
              <span className="risk-alert vpn">
                <Eye /> VPN
              </span>
            )}
            {data.has_tor && (
              <span className="risk-alert tor">
                <Shield /> Tor
              </span>
            )}
          </div>
        )}
      </div>

      <div className="device-list">
        {devices.length === 0 ? (
          <div className="empty-state">
            <Fingerprint />
            <h4 className="empty-title">No device history</h4>
            <p className="empty-message">
              Device fingerprints will appear here after analysis
            </p>
          </div>
        ) : (
          devices.map((device) => {
            const risk = RISK_CONFIG[device.risk_level] || RISK_CONFIG.low;
            const DeviceIcon = device.device_type === 'mobile' ? Smartphone : Monitor;

            return (
              <div
                key={device.id}
                className="device-item"
                onClick={() => setSelectedDevice(device)}
              >
                <div className="device-icon">
                  <DeviceIcon />
                </div>
                <div className="device-info">
                  <div className="device-ip">{device.ip_address}</div>
                  <div className="device-meta">
                    {device.city && device.country_code && (
                      <>
                        <Globe />
                        {device.city}, {device.country_code}
                      </>
                    )}
                    <span>{device.browser || 'Unknown'}</span>
                  </div>
                </div>
                <div className="device-flags">
                  {device.is_vpn && (
                    <span className="device-flag vpn">
                      <Eye /> VPN
                    </span>
                  )}
                  {device.is_tor && (
                    <span className="device-flag tor">
                      <AlertTriangle /> Tor
                    </span>
                  )}
                  {device.is_bot && (
                    <span className="device-flag bot">
                      <Bot /> Bot
                    </span>
                  )}
                  {device.is_proxy && (
                    <span className="device-flag proxy">
                      <Wifi /> Proxy
                    </span>
                  )}
                </div>
                <div className="device-risk">
                  <span
                    className="risk-badge"
                    style={{ color: risk.color, background: risk.bg }}
                  >
                    <Shield />
                    {risk.label}
                  </span>
                  <span className="device-date">
                    {new Date(device.created_at).toLocaleDateString()}
                  </span>
                </div>
                <div className="chevron">
                  <ChevronRight />
                </div>
              </div>
            );
          })
        )}
      </div>

      {selectedDevice && (
        <DeviceRiskCard
          device={selectedDevice}
          onClose={() => setSelectedDevice(null)}
        />
      )}
    </div>
  );
}
