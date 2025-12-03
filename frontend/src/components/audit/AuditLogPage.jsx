import React, { useState, useMemo } from 'react';
import {
  ScrollText,
  Download,
  ShieldCheck,
  ShieldAlert,
  Loader2,
  ChevronLeft,
  ChevronRight,
  AlertCircle,
} from 'lucide-react';
import {
  useAuditLogs,
  useAuditStats,
  useChainVerification,
  useExportAuditLogs,
} from '../../hooks';
import AuditLogFilters from './AuditLogFilters';
import AuditLogDetail from './AuditLogDetail';

const PAGE_SIZE = 25;

function formatDate(dateStr) {
  if (!dateStr) return '-';
  const date = new Date(dateStr);
  return date.toLocaleString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}

function formatAction(action) {
  // Convert applicant.created -> Applicant Created
  return action
    .split('.')
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1).replace(/_/g, ' '))
    .join(' - ');
}

function getActionColor(action) {
  if (action.includes('created')) return '#10b981';
  if (action.includes('approved')) return '#10b981';
  if (action.includes('rejected')) return '#ef4444';
  if (action.includes('deleted')) return '#ef4444';
  if (action.includes('updated')) return '#f59e0b';
  if (action.includes('resolved')) return '#3b82f6';
  return '#6b7280';
}

function truncateId(id) {
  if (!id) return '-';
  const str = String(id);
  if (str.length <= 12) return str;
  return `${str.slice(0, 8)}...`;
}

export default function AuditLogPage() {
  const [filters, setFilters] = useState({});
  const [currentPage, setCurrentPage] = useState(0);
  const [selectedEntry, setSelectedEntry] = useState(null);

  const queryFilters = useMemo(
    () => ({
      ...filters,
      limit: PAGE_SIZE,
      offset: currentPage * PAGE_SIZE,
      sort_order: 'desc',
    }),
    [filters, currentPage]
  );

  const { data, isLoading, error } = useAuditLogs(queryFilters);
  const { data: stats } = useAuditStats();
  const { data: verification, isLoading: verifying } = useChainVerification();
  const exportAuditLogs = useExportAuditLogs();

  const entries = data?.items || [];
  const total = data?.total || 0;
  const totalPages = Math.ceil(total / PAGE_SIZE);

  const handleFilterChange = (newFilters) => {
    setFilters(newFilters);
    setCurrentPage(0);
  };

  const handleExport = () => {
    exportAuditLogs.mutate(filters);
  };

  return (
    <div className="audit-log-page">
      <style>{`
        .audit-log-page {
          max-width: 1400px;
          margin: 0 auto;
        }

        .audit-header {
          display: flex;
          align-items: flex-start;
          justify-content: space-between;
          gap: 24px;
          margin-bottom: 24px;
        }

        .audit-title-section {
          display: flex;
          align-items: center;
          gap: 12px;
        }

        .audit-icon {
          width: 32px;
          height: 32px;
          color: var(--accent-primary, #6366f1);
        }

        .audit-title {
          font-size: 24px;
          font-weight: 600;
          color: var(--text-primary, #f0f2f5);
          margin: 0;
        }

        .audit-subtitle {
          font-size: 14px;
          color: var(--text-secondary, #8b919e);
          margin: 4px 0 0;
        }

        .audit-actions {
          display: flex;
          gap: 12px;
          align-items: center;
        }

        .chain-status {
          display: flex;
          align-items: center;
          gap: 8px;
          padding: 8px 14px;
          border-radius: 8px;
          font-size: 13px;
          font-weight: 500;
        }

        .chain-status.valid {
          background: rgba(16, 185, 129, 0.1);
          color: var(--success, #10b981);
        }

        .chain-status.invalid {
          background: rgba(239, 68, 68, 0.1);
          color: var(--danger, #ef4444);
        }

        .chain-status.loading {
          background: var(--bg-tertiary, #1a1d24);
          color: var(--text-secondary, #8b919e);
        }

        .chain-status svg {
          width: 16px;
          height: 16px;
        }

        .export-btn {
          display: inline-flex;
          align-items: center;
          gap: 8px;
          padding: 8px 16px;
          background: var(--bg-secondary, #111318);
          border: 1px solid var(--border-color, #2a2f3a);
          border-radius: 8px;
          color: var(--text-primary, #f0f2f5);
          font-size: 14px;
          font-weight: 500;
          cursor: pointer;
          transition: all 0.15s;
          font-family: inherit;
        }

        .export-btn:hover:not(:disabled) {
          background: var(--bg-hover, #22262f);
          border-color: var(--accent-primary, #6366f1);
        }

        .export-btn:disabled {
          opacity: 0.6;
          cursor: not-allowed;
        }

        .export-btn svg {
          width: 16px;
          height: 16px;
        }

        .stats-row {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
          gap: 16px;
          margin-bottom: 24px;
        }

        .stat-card {
          background: var(--bg-secondary, #111318);
          border: 1px solid var(--border-color, #2a2f3a);
          border-radius: 10px;
          padding: 16px;
        }

        .stat-label {
          font-size: 12px;
          color: var(--text-muted, #5c6370);
          text-transform: uppercase;
          letter-spacing: 0.05em;
          margin-bottom: 4px;
        }

        .stat-value {
          font-size: 24px;
          font-weight: 600;
          color: var(--text-primary, #f0f2f5);
        }

        .audit-content {
          background: var(--bg-secondary, #111318);
          border: 1px solid var(--border-color, #2a2f3a);
          border-radius: 12px;
          overflow: hidden;
        }

        .audit-table-wrapper {
          overflow-x: auto;
        }

        .audit-table {
          width: 100%;
          border-collapse: collapse;
        }

        .audit-table th {
          text-align: left;
          padding: 14px 16px;
          font-size: 12px;
          font-weight: 600;
          text-transform: uppercase;
          letter-spacing: 0.05em;
          color: var(--text-muted, #5c6370);
          background: var(--bg-tertiary, #1a1d24);
          border-bottom: 1px solid var(--border-color, #2a2f3a);
          white-space: nowrap;
        }

        .audit-table td {
          padding: 14px 16px;
          border-bottom: 1px solid var(--border-color, #2a2f3a);
          font-size: 14px;
          color: var(--text-primary, #f0f2f5);
        }

        .audit-table tbody tr {
          cursor: pointer;
          transition: background 0.15s;
        }

        .audit-table tbody tr:hover {
          background: var(--bg-hover, #22262f);
        }

        .audit-table tbody tr:last-child td {
          border-bottom: none;
        }

        .action-badge {
          display: inline-flex;
          align-items: center;
          padding: 4px 10px;
          border-radius: 6px;
          font-size: 12px;
          font-weight: 500;
          white-space: nowrap;
        }

        .resource-type {
          display: inline-flex;
          align-items: center;
          padding: 4px 8px;
          background: var(--bg-tertiary, #1a1d24);
          border-radius: 4px;
          font-size: 12px;
          color: var(--text-secondary, #8b919e);
          text-transform: capitalize;
        }

        .user-cell {
          display: flex;
          flex-direction: column;
        }

        .user-email {
          font-size: 14px;
          color: var(--text-primary, #f0f2f5);
        }

        .user-ip {
          font-size: 12px;
          color: var(--text-muted, #5c6370);
        }

        .resource-id {
          font-family: monospace;
          font-size: 12px;
          color: var(--text-secondary, #8b919e);
        }

        .timestamp {
          white-space: nowrap;
          color: var(--text-secondary, #8b919e);
        }

        .pagination {
          display: flex;
          align-items: center;
          justify-content: space-between;
          padding: 16px;
          border-top: 1px solid var(--border-color, #2a2f3a);
        }

        .pagination-info {
          font-size: 14px;
          color: var(--text-secondary, #8b919e);
        }

        .pagination-controls {
          display: flex;
          gap: 8px;
        }

        .pagination-btn {
          display: flex;
          align-items: center;
          justify-content: center;
          width: 36px;
          height: 36px;
          border-radius: 8px;
          background: var(--bg-tertiary, #1a1d24);
          border: 1px solid var(--border-color, #2a2f3a);
          color: var(--text-primary, #f0f2f5);
          cursor: pointer;
          transition: all 0.15s;
        }

        .pagination-btn:hover:not(:disabled) {
          background: var(--bg-hover, #22262f);
          border-color: var(--accent-primary, #6366f1);
        }

        .pagination-btn:disabled {
          opacity: 0.4;
          cursor: not-allowed;
        }

        .empty-state {
          padding: 60px 20px;
          text-align: center;
          color: var(--text-secondary, #8b919e);
        }

        .empty-state svg {
          width: 48px;
          height: 48px;
          margin-bottom: 16px;
          opacity: 0.5;
        }

        .loading-state {
          display: flex;
          align-items: center;
          justify-content: center;
          padding: 60px;
          color: var(--text-secondary, #8b919e);
        }

        .spinner {
          animation: spin 1s linear infinite;
        }

        @keyframes spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }

        .error-state {
          padding: 40px 20px;
          text-align: center;
          color: var(--danger, #ef4444);
        }

        .error-state svg {
          width: 32px;
          height: 32px;
          margin-bottom: 12px;
        }
      `}</style>

      <div className="audit-header">
        <div className="audit-title-section">
          <ScrollText className="audit-icon" />
          <div>
            <h1 className="audit-title">Audit Log</h1>
            <p className="audit-subtitle">
              Complete history of all compliance actions
            </p>
          </div>
        </div>

        <div className="audit-actions">
          {verifying ? (
            <div className="chain-status loading">
              <Loader2 className="spinner" />
              Verifying chain...
            </div>
          ) : verification?.is_valid ? (
            <div className="chain-status valid">
              <ShieldCheck />
              Chain verified
            </div>
          ) : verification?.is_valid === false ? (
            <div className="chain-status invalid">
              <ShieldAlert />
              Chain integrity issue
            </div>
          ) : null}

          <button
            className="export-btn"
            onClick={handleExport}
            disabled={exportAuditLogs.isPending}
          >
            {exportAuditLogs.isPending ? (
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

      {stats && (
        <div className="stats-row">
          <div className="stat-card">
            <div className="stat-label">Total Entries</div>
            <div className="stat-value">{stats.total_entries.toLocaleString()}</div>
          </div>
          <div className="stat-card">
            <div className="stat-label">Today</div>
            <div className="stat-value">{stats.entries_today.toLocaleString()}</div>
          </div>
          <div className="stat-card">
            <div className="stat-label">This Week</div>
            <div className="stat-value">{stats.entries_this_week.toLocaleString()}</div>
          </div>
          <div className="stat-card">
            <div className="stat-label">This Month</div>
            <div className="stat-value">{stats.entries_this_month.toLocaleString()}</div>
          </div>
        </div>
      )}

      <AuditLogFilters filters={filters} onFilterChange={handleFilterChange} />

      <div className="audit-content">
        {isLoading ? (
          <div className="loading-state">
            <Loader2 className="spinner" size={24} />
          </div>
        ) : error ? (
          <div className="error-state">
            <AlertCircle />
            <div>Failed to load audit logs</div>
          </div>
        ) : entries.length === 0 ? (
          <div className="empty-state">
            <ScrollText />
            <div>No audit log entries found</div>
            <div style={{ fontSize: 13, marginTop: 8 }}>
              Try adjusting your filters
            </div>
          </div>
        ) : (
          <>
            <div className="audit-table-wrapper">
              <table className="audit-table">
                <thead>
                  <tr>
                    <th>Timestamp</th>
                    <th>User</th>
                    <th>Action</th>
                    <th>Resource Type</th>
                    <th>Resource ID</th>
                  </tr>
                </thead>
                <tbody>
                  {entries.map((entry) => (
                    <tr key={entry.id} onClick={() => setSelectedEntry(entry)}>
                      <td className="timestamp">{formatDate(entry.created_at)}</td>
                      <td>
                        <div className="user-cell">
                          <span className="user-email">
                            {entry.user_email || 'System'}
                          </span>
                          {entry.ip_address && (
                            <span className="user-ip">{entry.ip_address}</span>
                          )}
                        </div>
                      </td>
                      <td>
                        <span
                          className="action-badge"
                          style={{
                            background: `${getActionColor(entry.action)}15`,
                            color: getActionColor(entry.action),
                          }}
                        >
                          {formatAction(entry.action)}
                        </span>
                      </td>
                      <td>
                        <span className="resource-type">{entry.resource_type}</span>
                      </td>
                      <td>
                        <span className="resource-id" title={entry.resource_id}>
                          {truncateId(entry.resource_id)}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <div className="pagination">
              <div className="pagination-info">
                Showing {currentPage * PAGE_SIZE + 1}-
                {Math.min((currentPage + 1) * PAGE_SIZE, total)} of {total}
              </div>
              <div className="pagination-controls">
                <button
                  className="pagination-btn"
                  onClick={() => setCurrentPage((p) => p - 1)}
                  disabled={currentPage === 0}
                >
                  <ChevronLeft size={18} />
                </button>
                <button
                  className="pagination-btn"
                  onClick={() => setCurrentPage((p) => p + 1)}
                  disabled={currentPage >= totalPages - 1}
                >
                  <ChevronRight size={18} />
                </button>
              </div>
            </div>
          </>
        )}
      </div>

      {selectedEntry && (
        <AuditLogDetail
          entry={selectedEntry}
          onClose={() => setSelectedEntry(null)}
        />
      )}
    </div>
  );
}
