import React from 'react';
import {
  X,
  User,
  Clock,
  Globe,
  Hash,
  Shield,
  FileText,
  ArrowRight,
} from 'lucide-react';

function formatDate(dateStr) {
  if (!dateStr) return '-';
  const date = new Date(dateStr);
  return date.toLocaleString('en-US', {
    weekday: 'short',
    month: 'short',
    day: 'numeric',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  });
}

function formatAction(action) {
  return action
    .split('.')
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1).replace(/_/g, ' '))
    .join(' → ');
}

function JsonDiff({ oldValues, newValues }) {
  if (!oldValues && !newValues) {
    return (
      <div className="no-changes">No data changes recorded</div>
    );
  }

  const allKeys = new Set([
    ...Object.keys(oldValues || {}),
    ...Object.keys(newValues || {}),
  ]);

  const changes = [];
  allKeys.forEach((key) => {
    const oldVal = oldValues?.[key];
    const newVal = newValues?.[key];

    if (JSON.stringify(oldVal) !== JSON.stringify(newVal)) {
      changes.push({ key, oldVal, newVal });
    }
  });

  if (changes.length === 0) {
    return (
      <div className="no-changes">No changes detected</div>
    );
  }

  return (
    <div className="diff-container">
      {changes.map(({ key, oldVal, newVal }) => (
        <div key={key} className="diff-row">
          <div className="diff-key">{key}</div>
          <div className="diff-values">
            {oldVal !== undefined && (
              <div className="diff-old">
                <span className="diff-label">Before:</span>
                <code>{JSON.stringify(oldVal, null, 2)}</code>
              </div>
            )}
            <ArrowRight className="diff-arrow" />
            {newVal !== undefined && (
              <div className="diff-new">
                <span className="diff-label">After:</span>
                <code>{JSON.stringify(newVal, null, 2)}</code>
              </div>
            )}
          </div>
        </div>
      ))}
    </div>
  );
}

export default function AuditLogDetail({ entry, onClose }) {
  if (!entry) return null;

  return (
    <div className="audit-detail-overlay" onClick={onClose}>
      <style>{`
        .audit-detail-overlay {
          position: fixed;
          inset: 0;
          background: rgba(0, 0, 0, 0.7);
          display: flex;
          align-items: center;
          justify-content: center;
          z-index: 1000;
          padding: 20px;
        }

        .audit-detail-modal {
          background: var(--bg-secondary, #111318);
          border: 1px solid var(--border-color, #2a2f3a);
          border-radius: 16px;
          width: 100%;
          max-width: 700px;
          max-height: 90vh;
          overflow: hidden;
          display: flex;
          flex-direction: column;
        }

        .audit-detail-header {
          display: flex;
          align-items: center;
          justify-content: space-between;
          padding: 20px 24px;
          border-bottom: 1px solid var(--border-color, #2a2f3a);
        }

        .audit-detail-title {
          font-size: 18px;
          font-weight: 600;
          color: var(--text-primary, #f0f2f5);
          margin: 0;
        }

        .close-btn {
          display: flex;
          align-items: center;
          justify-content: center;
          width: 36px;
          height: 36px;
          background: transparent;
          border: 1px solid var(--border-color, #2a2f3a);
          border-radius: 8px;
          color: var(--text-secondary, #8b919e);
          cursor: pointer;
          transition: all 0.15s;
        }

        .close-btn:hover {
          background: var(--bg-tertiary, #1a1d24);
          color: var(--text-primary, #f0f2f5);
        }

        .audit-detail-content {
          padding: 24px;
          overflow-y: auto;
          flex: 1;
        }

        .detail-section {
          margin-bottom: 24px;
        }

        .detail-section:last-child {
          margin-bottom: 0;
        }

        .section-title {
          font-size: 12px;
          font-weight: 600;
          text-transform: uppercase;
          letter-spacing: 0.05em;
          color: var(--text-muted, #5c6370);
          margin-bottom: 12px;
        }

        .detail-grid {
          display: grid;
          grid-template-columns: repeat(2, 1fr);
          gap: 16px;
        }

        @media (max-width: 500px) {
          .detail-grid {
            grid-template-columns: 1fr;
          }
        }

        .detail-item {
          display: flex;
          flex-direction: column;
          gap: 4px;
        }

        .detail-item.full-width {
          grid-column: 1 / -1;
        }

        .detail-label {
          display: flex;
          align-items: center;
          gap: 6px;
          font-size: 12px;
          color: var(--text-muted, #5c6370);
        }

        .detail-label svg {
          width: 14px;
          height: 14px;
        }

        .detail-value {
          font-size: 14px;
          color: var(--text-primary, #f0f2f5);
          word-break: break-all;
        }

        .detail-value.mono {
          font-family: monospace;
          font-size: 13px;
          background: var(--bg-tertiary, #1a1d24);
          padding: 8px 12px;
          border-radius: 6px;
          border: 1px solid var(--border-color, #2a2f3a);
        }

        .action-badge {
          display: inline-flex;
          align-items: center;
          padding: 6px 12px;
          border-radius: 6px;
          font-size: 13px;
          font-weight: 500;
          background: rgba(99, 102, 241, 0.1);
          color: var(--accent-primary, #6366f1);
        }

        .diff-container {
          background: var(--bg-tertiary, #1a1d24);
          border: 1px solid var(--border-color, #2a2f3a);
          border-radius: 8px;
          overflow: hidden;
        }

        .diff-row {
          padding: 12px 16px;
          border-bottom: 1px solid var(--border-color, #2a2f3a);
        }

        .diff-row:last-child {
          border-bottom: none;
        }

        .diff-key {
          font-size: 13px;
          font-weight: 600;
          color: var(--text-primary, #f0f2f5);
          margin-bottom: 8px;
        }

        .diff-values {
          display: flex;
          align-items: flex-start;
          gap: 12px;
        }

        .diff-arrow {
          width: 16px;
          height: 16px;
          color: var(--text-muted, #5c6370);
          flex-shrink: 0;
          margin-top: 4px;
        }

        .diff-old,
        .diff-new {
          flex: 1;
          min-width: 0;
        }

        .diff-label {
          display: block;
          font-size: 11px;
          text-transform: uppercase;
          letter-spacing: 0.05em;
          margin-bottom: 4px;
        }

        .diff-old .diff-label {
          color: var(--danger, #ef4444);
        }

        .diff-new .diff-label {
          color: var(--success, #10b981);
        }

        .diff-old code,
        .diff-new code {
          display: block;
          font-size: 12px;
          padding: 8px;
          border-radius: 4px;
          white-space: pre-wrap;
          word-break: break-all;
        }

        .diff-old code {
          background: rgba(239, 68, 68, 0.1);
          color: #fca5a5;
        }

        .diff-new code {
          background: rgba(16, 185, 129, 0.1);
          color: #6ee7b7;
        }

        .no-changes {
          padding: 24px;
          text-align: center;
          color: var(--text-muted, #5c6370);
          font-size: 14px;
        }

        .extra-data-json {
          background: var(--bg-tertiary, #1a1d24);
          border: 1px solid var(--border-color, #2a2f3a);
          border-radius: 8px;
          padding: 12px 16px;
          font-family: monospace;
          font-size: 12px;
          color: var(--text-secondary, #8b919e);
          white-space: pre-wrap;
          word-break: break-all;
          max-height: 200px;
          overflow-y: auto;
        }

        .checksum-verified {
          display: flex;
          align-items: center;
          gap: 8px;
          font-size: 13px;
          color: var(--success, #10b981);
        }

        .checksum-verified svg {
          width: 16px;
          height: 16px;
        }
      `}</style>

      <div className="audit-detail-modal" onClick={(e) => e.stopPropagation()}>
        <div className="audit-detail-header">
          <h2 className="audit-detail-title">Audit Log Entry</h2>
          <button className="close-btn" onClick={onClose}>
            <X size={18} />
          </button>
        </div>

        <div className="audit-detail-content">
          <div className="detail-section">
            <div className="section-title">Event Details</div>
            <div className="detail-grid">
              <div className="detail-item">
                <div className="detail-label">
                  <Clock />
                  Timestamp
                </div>
                <div className="detail-value">{formatDate(entry.created_at)}</div>
              </div>

              <div className="detail-item">
                <div className="detail-label">
                  <FileText />
                  Action
                </div>
                <div className="detail-value">
                  <span className="action-badge">{formatAction(entry.action)}</span>
                </div>
              </div>

              <div className="detail-item">
                <div className="detail-label">
                  <User />
                  User
                </div>
                <div className="detail-value">{entry.user_email || 'System'}</div>
              </div>

              <div className="detail-item">
                <div className="detail-label">
                  <Globe />
                  IP Address
                </div>
                <div className="detail-value">{entry.ip_address || '-'}</div>
              </div>

              <div className="detail-item">
                <div className="detail-label">
                  <Hash />
                  Resource Type
                </div>
                <div className="detail-value" style={{ textTransform: 'capitalize' }}>
                  {entry.resource_type}
                </div>
              </div>

              <div className="detail-item">
                <div className="detail-label">
                  <Hash />
                  Resource ID
                </div>
                <div className="detail-value mono">{entry.resource_id}</div>
              </div>
            </div>
          </div>

          <div className="detail-section">
            <div className="section-title">Data Changes</div>
            <JsonDiff oldValues={entry.old_values} newValues={entry.new_values} />
          </div>

          {entry.extra_data && Object.keys(entry.extra_data).length > 0 && (
            <div className="detail-section">
              <div className="section-title">Additional Data</div>
              <div className="extra-data-json">
                {JSON.stringify(entry.extra_data, null, 2)}
              </div>
            </div>
          )}

          <div className="detail-section">
            <div className="section-title">Chain Integrity</div>
            <div className="detail-grid">
              <div className="detail-item full-width">
                <div className="detail-label">
                  <Shield />
                  Checksum
                </div>
                <div className="detail-value mono">{entry.checksum}</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
