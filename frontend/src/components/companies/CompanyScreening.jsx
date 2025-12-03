/**
 * Company Screening Component
 *
 * Screening results tab for company detail page.
 * Shows company and UBO screening history and results.
 */

import React from 'react';
import {
  Shield,
  CheckCircle,
  AlertTriangle,
  Clock,
  Users,
  Building2,
  Calendar,
  Search,
} from 'lucide-react';
import { useScreenCompany } from '../../hooks';

const SCREENING_STATUS = {
  clear: { label: 'Clear', color: '#22c55e', icon: CheckCircle },
  hits_pending: { label: 'Hits Pending', color: '#f59e0b', icon: AlertTriangle },
  hits_resolved: { label: 'Hits Resolved', color: '#6366f1', icon: CheckCircle },
  pending: { label: 'Not Screened', color: '#8b919e', icon: Clock },
};

export default function CompanyScreening({ companyId, company }) {
  const screenMutation = useScreenCompany();

  const screeningStatus = SCREENING_STATUS[company.screening_status] || SCREENING_STATUS.pending;
  const ScreeningIcon = screeningStatus.icon;

  const handleRunScreening = async () => {
    try {
      await screenMutation.mutateAsync(companyId);
    } catch (err) {
      console.error('Failed to run screening:', err);
    }
  };

  const companyFlags = company.flags || [];
  const ubos = company.beneficial_owners || [];
  const ubosWithHits = ubos.filter((ubo) => ubo.screening_status === 'hits');

  return (
    <div className="company-screening">
      <style>{`
        .company-screening {
          display: flex;
          flex-direction: column;
          gap: 24px;
        }

        .screening-header {
          display: flex;
          justify-content: space-between;
          align-items: flex-start;
          flex-wrap: wrap;
          gap: 16px;
        }

        .screening-title {
          font-size: 16px;
          font-weight: 600;
          color: var(--text-primary, #f0f2f5);
          margin: 0;
          display: flex;
          align-items: center;
          gap: 8px;
        }

        .screening-title svg {
          width: 20px;
          height: 20px;
          color: var(--accent-primary, #6366f1);
        }

        .run-screening-btn {
          display: flex;
          align-items: center;
          gap: 8px;
          padding: 10px 16px;
          background: var(--accent-primary, #6366f1);
          color: white;
          border: none;
          border-radius: 6px;
          font-size: 13px;
          font-weight: 500;
          cursor: pointer;
          transition: background 0.15s;
          font-family: inherit;
        }

        .run-screening-btn:hover {
          background: var(--accent-hover, #5558e3);
        }

        .run-screening-btn:disabled {
          opacity: 0.6;
          cursor: not-allowed;
        }

        .run-screening-btn svg {
          width: 14px;
          height: 14px;
        }

        .screening-summary {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
          gap: 16px;
        }

        .summary-card {
          background: var(--bg-tertiary, #1a1d24);
          border: 1px solid var(--border-primary, #23262f);
          border-radius: 8px;
          padding: 16px;
        }

        .summary-card-header {
          display: flex;
          align-items: center;
          gap: 8px;
          margin-bottom: 12px;
        }

        .summary-card-header svg {
          width: 16px;
          height: 16px;
          color: var(--text-secondary, #8b919e);
        }

        .summary-card-title {
          font-size: 13px;
          font-weight: 500;
          color: var(--text-secondary, #8b919e);
          margin: 0;
        }

        .summary-status {
          display: flex;
          align-items: center;
          gap: 8px;
        }

        .status-badge {
          display: inline-flex;
          align-items: center;
          gap: 6px;
          padding: 6px 12px;
          border-radius: 20px;
          font-size: 13px;
          font-weight: 500;
        }

        .status-badge svg {
          width: 14px;
          height: 14px;
        }

        .summary-date {
          font-size: 12px;
          color: var(--text-secondary, #8b919e);
          margin-top: 8px;
          display: flex;
          align-items: center;
          gap: 6px;
        }

        .summary-date svg {
          width: 12px;
          height: 12px;
        }

        .flags-section {
          margin-top: 16px;
          padding-top: 16px;
          border-top: 1px solid var(--border-primary, #23262f);
        }

        .flags-title {
          font-size: 12px;
          font-weight: 500;
          color: var(--text-secondary, #8b919e);
          margin: 0 0 8px;
        }

        .flags-list {
          display: flex;
          flex-wrap: wrap;
          gap: 6px;
        }

        .flag-badge {
          display: inline-flex;
          align-items: center;
          gap: 4px;
          padding: 4px 8px;
          background: rgba(239, 68, 68, 0.1);
          color: #ef4444;
          border-radius: 4px;
          font-size: 11px;
          font-weight: 500;
          text-transform: uppercase;
        }

        .flag-badge svg {
          width: 10px;
          height: 10px;
        }

        .ubo-screening-list {
          display: flex;
          flex-direction: column;
          gap: 12px;
        }

        .ubo-screening-title {
          font-size: 14px;
          font-weight: 600;
          color: var(--text-primary, #f0f2f5);
          margin: 0;
        }

        .ubo-screening-card {
          background: var(--bg-tertiary, #1a1d24);
          border: 1px solid var(--border-primary, #23262f);
          border-radius: 8px;
          padding: 16px;
          display: flex;
          justify-content: space-between;
          align-items: center;
          gap: 16px;
          flex-wrap: wrap;
        }

        .ubo-info {
          display: flex;
          flex-direction: column;
          gap: 4px;
        }

        .ubo-name {
          font-size: 14px;
          font-weight: 500;
          color: var(--text-primary, #f0f2f5);
        }

        .ubo-role {
          font-size: 12px;
          color: var(--text-secondary, #8b919e);
        }

        .ubo-screening-status {
          display: flex;
          align-items: center;
          gap: 12px;
        }

        .hits-warning {
          display: flex;
          align-items: center;
          gap: 6px;
          padding: 8px 12px;
          background: rgba(239, 68, 68, 0.1);
          color: #ef4444;
          border-radius: 6px;
          font-size: 13px;
          font-weight: 500;
        }

        .hits-warning svg {
          width: 14px;
          height: 14px;
        }

        .no-screening-message {
          padding: 40px;
          text-align: center;
          background: var(--bg-tertiary, #1a1d24);
          border: 1px solid var(--border-primary, #23262f);
          border-radius: 8px;
        }

        .no-screening-message svg {
          width: 40px;
          height: 40px;
          color: var(--text-secondary, #8b919e);
          margin-bottom: 12px;
        }

        .no-screening-message h4 {
          margin: 0 0 8px;
          font-size: 14px;
          color: var(--text-primary, #f0f2f5);
        }

        .no-screening-message p {
          margin: 0;
          font-size: 13px;
          color: var(--text-secondary, #8b919e);
        }
      `}</style>

      <div className="screening-header">
        <h3 className="screening-title">
          <Shield />
          Screening Results
        </h3>
        <button
          className="run-screening-btn"
          onClick={handleRunScreening}
          disabled={screenMutation.isPending}
        >
          <Search />
          {screenMutation.isPending ? 'Running...' : 'Run Screening'}
        </button>
      </div>

      {!company.last_screened_at ? (
        <div className="no-screening-message">
          <Shield />
          <h4>No screening performed</h4>
          <p>Run screening to check company and UBOs against sanctions and PEP lists.</p>
        </div>
      ) : (
        <>
          <div className="screening-summary">
            <div className="summary-card">
              <div className="summary-card-header">
                <Building2 />
                <h4 className="summary-card-title">Company Screening</h4>
              </div>
              <div className="summary-status">
                <span
                  className="status-badge"
                  style={{
                    color: screeningStatus.color,
                    background: `${screeningStatus.color}15`,
                  }}
                >
                  <ScreeningIcon />
                  {screeningStatus.label}
                </span>
              </div>
              <div className="summary-date">
                <Calendar />
                Last screened: {new Date(company.last_screened_at).toLocaleDateString()}
              </div>

              {companyFlags.length > 0 && (
                <div className="flags-section">
                  <h5 className="flags-title">Risk Flags</h5>
                  <div className="flags-list">
                    {companyFlags.map((flag) => (
                      <span key={flag} className="flag-badge">
                        <AlertTriangle />
                        {flag.replace(/_/g, ' ')}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>

            <div className="summary-card">
              <div className="summary-card-header">
                <Users />
                <h4 className="summary-card-title">UBO Screening</h4>
              </div>
              <div className="summary-status">
                {ubosWithHits.length > 0 ? (
                  <span
                    className="status-badge"
                    style={{
                      color: '#ef4444',
                      background: 'rgba(239, 68, 68, 0.1)',
                    }}
                  >
                    <AlertTriangle />
                    {ubosWithHits.length} UBO{ubosWithHits.length !== 1 ? 's' : ''} with hits
                  </span>
                ) : ubos.some((ubo) => ubo.screening_status === 'clear') ? (
                  <span
                    className="status-badge"
                    style={{
                      color: '#22c55e',
                      background: 'rgba(34, 197, 94, 0.1)',
                    }}
                  >
                    <CheckCircle />
                    All Clear
                  </span>
                ) : (
                  <span
                    className="status-badge"
                    style={{
                      color: '#8b919e',
                      background: 'rgba(139, 145, 158, 0.1)',
                    }}
                  >
                    <Clock />
                    Pending
                  </span>
                )}
              </div>
              <div className="summary-date">
                <Users />
                {ubos.length} beneficial owner{ubos.length !== 1 ? 's' : ''} tracked
              </div>
            </div>
          </div>

          {ubos.length > 0 && (
            <div className="ubo-screening-list">
              <h4 className="ubo-screening-title">Beneficial Owner Details</h4>

              {ubos.map((ubo) => {
                const uboStatus = SCREENING_STATUS[ubo.screening_status] || SCREENING_STATUS.pending;
                const UboIcon = uboStatus.icon;

                return (
                  <div key={ubo.id} className="ubo-screening-card">
                    <div className="ubo-info">
                      <span className="ubo-name">{ubo.full_name}</span>
                      {ubo.role_title && (
                        <span className="ubo-role">
                          {ubo.role_title}
                          {ubo.ownership_percentage && ` • ${ubo.ownership_percentage}%`}
                        </span>
                      )}
                    </div>

                    <div className="ubo-screening-status">
                      <span
                        className="status-badge"
                        style={{
                          color: uboStatus.color,
                          background: `${uboStatus.color}15`,
                        }}
                      >
                        <UboIcon />
                        {uboStatus.label}
                      </span>

                      {ubo.flags?.length > 0 && (
                        <div className="flags-list">
                          {ubo.flags.map((flag) => (
                            <span key={flag} className="flag-badge">
                              {flag.toUpperCase()}
                            </span>
                          ))}
                        </div>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </>
      )}
    </div>
  );
}
