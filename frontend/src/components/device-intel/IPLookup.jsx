/**
 * IP Lookup Component
 *
 * Modal for quick IP reputation lookups without storing results.
 */

import React, { useState } from 'react';
import {
  X,
  Search,
  Globe,
  Shield,
  MapPin,
  Server,
  Wifi,
  AlertTriangle,
  CheckCircle,
  XCircle,
  Loader2,
} from 'lucide-react';
import { useCheckIP } from '../../hooks';

export default function IPLookup({ onClose }) {
  const [ipAddress, setIpAddress] = useState('');
  const checkIPMutation = useCheckIP();

  const handleSubmit = (e) => {
    e.preventDefault();
    if (ipAddress.trim()) {
      checkIPMutation.mutate(ipAddress.trim());
    }
  };

  const result = checkIPMutation.data;
  const isLoading = checkIPMutation.isPending;
  const error = checkIPMutation.error;

  const getFraudLevel = (score) => {
    if (score >= 85) return { label: 'High Risk', color: '#ef4444', bg: 'rgba(239, 68, 68, 0.1)' };
    if (score >= 70) return { label: 'Medium Risk', color: '#f59e0b', bg: 'rgba(245, 158, 11, 0.1)' };
    return { label: 'Low Risk', color: '#22c55e', bg: 'rgba(34, 197, 94, 0.1)' };
  };

  return (
    <div className="ip-lookup-overlay" onClick={onClose}>
      <style>{`
        .ip-lookup-overlay {
          position: fixed;
          top: 0;
          left: 0;
          right: 0;
          bottom: 0;
          background: rgba(0, 0, 0, 0.5);
          z-index: 1000;
          display: flex;
          align-items: center;
          justify-content: center;
          padding: 20px;
        }

        .ip-lookup-modal {
          width: 520px;
          max-width: 100%;
          max-height: 90vh;
          background: var(--bg-primary, #0a0b0e);
          border: 1px solid var(--border-primary, #23262f);
          border-radius: 16px;
          overflow: hidden;
          animation: modalIn 0.2s ease-out;
        }

        @keyframes modalIn {
          from {
            transform: scale(0.95);
            opacity: 0;
          }
          to {
            transform: scale(1);
            opacity: 1;
          }
        }

        .modal-header {
          display: flex;
          align-items: center;
          justify-content: space-between;
          padding: 20px 24px;
          border-bottom: 1px solid var(--border-primary, #23262f);
          background: var(--bg-secondary, #111318);
        }

        .modal-title {
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

        .modal-content {
          padding: 24px;
          overflow-y: auto;
          max-height: calc(90vh - 80px);
        }

        .search-form {
          display: flex;
          gap: 12px;
          margin-bottom: 24px;
        }

        .search-input {
          flex: 1;
          padding: 12px 16px;
          background: var(--bg-secondary, #111318);
          border: 1px solid var(--border-primary, #23262f);
          border-radius: 8px;
          color: var(--text-primary, #f0f2f5);
          font-size: 14px;
          font-family: monospace;
        }

        .search-input:focus {
          outline: none;
          border-color: var(--accent-primary, #6366f1);
        }

        .search-btn {
          display: flex;
          align-items: center;
          gap: 8px;
          padding: 12px 20px;
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

        .search-btn:hover:not(:disabled) {
          background: var(--accent-hover, #5558e3);
        }

        .search-btn:disabled {
          opacity: 0.6;
          cursor: not-allowed;
        }

        .search-btn svg {
          width: 16px;
          height: 16px;
        }

        .loading-state {
          display: flex;
          flex-direction: column;
          align-items: center;
          padding: 40px;
          color: var(--text-secondary, #8b919e);
        }

        .loading-state svg {
          width: 32px;
          height: 32px;
          animation: spin 1s linear infinite;
          margin-bottom: 12px;
        }

        @keyframes spin {
          to { transform: rotate(360deg); }
        }

        .error-state {
          padding: 20px;
          text-align: center;
          color: var(--error, #ef4444);
          background: rgba(239, 68, 68, 0.1);
          border-radius: 8px;
        }

        .result-section {
          background: var(--bg-secondary, #111318);
          border: 1px solid var(--border-primary, #23262f);
          border-radius: 12px;
          overflow: hidden;
        }

        .result-header {
          display: flex;
          align-items: center;
          gap: 16px;
          padding: 20px;
          border-bottom: 1px solid var(--border-primary, #23262f);
        }

        .risk-badge {
          display: flex;
          align-items: center;
          gap: 8px;
          padding: 8px 16px;
          border-radius: 20px;
          font-size: 14px;
          font-weight: 600;
        }

        .risk-badge svg {
          width: 16px;
          height: 16px;
        }

        .fraud-score {
          margin-left: auto;
          font-size: 24px;
          font-weight: 700;
        }

        .fraud-label {
          font-size: 12px;
          color: var(--text-secondary, #8b919e);
        }

        .result-grid {
          display: grid;
          grid-template-columns: repeat(2, 1fr);
          gap: 1px;
          background: var(--border-primary, #23262f);
        }

        .result-item {
          background: var(--bg-secondary, #111318);
          padding: 16px;
        }

        .result-item.full-width {
          grid-column: 1 / -1;
        }

        .result-label {
          display: flex;
          align-items: center;
          gap: 6px;
          font-size: 12px;
          color: var(--text-secondary, #8b919e);
          margin-bottom: 6px;
        }

        .result-label svg {
          width: 12px;
          height: 12px;
        }

        .result-value {
          font-size: 14px;
          color: var(--text-primary, #f0f2f5);
          font-weight: 500;
        }

        .flags-section {
          padding: 16px;
          background: var(--bg-tertiary, #1a1d24);
        }

        .flags-title {
          font-size: 12px;
          font-weight: 600;
          color: var(--text-secondary, #8b919e);
          text-transform: uppercase;
          letter-spacing: 0.5px;
          margin-bottom: 12px;
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
          padding: 8px 12px;
          background: var(--bg-secondary, #111318);
          border-radius: 6px;
          font-size: 13px;
        }

        .flag-item svg {
          width: 14px;
          height: 14px;
        }

        .flag-item.active {
          color: #ef4444;
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

        .empty-state {
          text-align: center;
          padding: 40px 20px;
          color: var(--text-secondary, #8b919e);
        }

        .empty-state svg {
          width: 48px;
          height: 48px;
          margin-bottom: 16px;
          opacity: 0.5;
        }

        .empty-state p {
          margin: 0;
        }
      `}</style>

      <div className="ip-lookup-modal" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h2 className="modal-title">IP Reputation Lookup</h2>
          <button className="close-btn" onClick={onClose}>
            <X />
          </button>
        </div>

        <div className="modal-content">
          <form className="search-form" onSubmit={handleSubmit}>
            <input
              type="text"
              className="search-input"
              placeholder="Enter IP address (e.g., 1.2.3.4)"
              value={ipAddress}
              onChange={(e) => setIpAddress(e.target.value)}
              autoFocus
            />
            <button
              type="submit"
              className="search-btn"
              disabled={!ipAddress.trim() || isLoading}
            >
              {isLoading ? <Loader2 /> : <Search />}
              {isLoading ? 'Checking...' : 'Check'}
            </button>
          </form>

          {isLoading && (
            <div className="loading-state">
              <Loader2 />
              <span>Checking IP reputation...</span>
            </div>
          )}

          {error && (
            <div className="error-state">
              <AlertTriangle style={{ width: 20, height: 20, marginBottom: 8 }} />
              <p>Failed to check IP: {error.message}</p>
            </div>
          )}

          {!isLoading && !error && !result && (
            <div className="empty-state">
              <Globe />
              <p>Enter an IP address to check its reputation</p>
            </div>
          )}

          {result && (
            <div className="result-section">
              <div className="result-header">
                {(() => {
                  const level = getFraudLevel(result.fraud_score);
                  return (
                    <>
                      <span
                        className="risk-badge"
                        style={{ color: level.color, background: level.bg }}
                      >
                        <Shield />
                        {level.label}
                      </span>
                      <div style={{ marginLeft: 'auto', textAlign: 'right' }}>
                        <div className="fraud-score" style={{ color: level.color }}>
                          {result.fraud_score}
                        </div>
                        <div className="fraud-label">Fraud Score</div>
                      </div>
                    </>
                  );
                })()}
              </div>

              <div className="result-grid">
                <div className="result-item full-width">
                  <div className="result-label">
                    <Globe /> IP Address
                  </div>
                  <div className="result-value" style={{ fontFamily: 'monospace' }}>
                    {result.ip_address}
                  </div>
                </div>
                <div className="result-item">
                  <div className="result-label">
                    <MapPin /> Location
                  </div>
                  <div className="result-value">
                    {result.city && result.country_code
                      ? `${result.city}, ${result.region || ''} ${result.country_code}`
                      : result.country_code || 'Unknown'}
                  </div>
                </div>
                <div className="result-item">
                  <div className="result-label">
                    <Server /> ISP
                  </div>
                  <div className="result-value">{result.isp || 'Unknown'}</div>
                </div>
                <div className="result-item">
                  <div className="result-label">
                    <Wifi /> Connection
                  </div>
                  <div className="result-value">
                    {result.connection_type || 'Unknown'}
                  </div>
                </div>
                <div className="result-item">
                  <div className="result-label">
                    <Server /> ASN
                  </div>
                  <div className="result-value">{result.asn || 'Unknown'}</div>
                </div>
              </div>

              <div className="flags-section">
                <div className="flags-title">Detection Flags</div>
                <div className="flags-grid">
                  <div className={`flag-item ${result.is_vpn ? 'active' : 'inactive'}`}>
                    {result.is_vpn ? <XCircle /> : <CheckCircle />}
                    VPN
                  </div>
                  <div className={`flag-item ${result.is_proxy ? 'active' : 'inactive'}`}>
                    {result.is_proxy ? <XCircle /> : <CheckCircle />}
                    Proxy
                  </div>
                  <div className={`flag-item ${result.is_tor ? 'active' : 'inactive'}`}>
                    {result.is_tor ? <XCircle /> : <CheckCircle />}
                    Tor
                  </div>
                  <div className={`flag-item ${result.is_bot ? 'active' : 'inactive'}`}>
                    {result.is_bot ? <XCircle /> : <CheckCircle />}
                    Bot
                  </div>
                  <div className={`flag-item ${result.is_datacenter ? 'active' : 'inactive'}`}>
                    {result.is_datacenter ? <XCircle /> : <CheckCircle />}
                    Datacenter
                  </div>
                  <div className={`flag-item ${result.recent_abuse ? 'active' : 'inactive'}`}>
                    {result.recent_abuse ? <XCircle /> : <CheckCircle />}
                    Recent Abuse
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
