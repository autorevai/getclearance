/**
 * Invoice List Component
 *
 * Displays list of invoices with download links.
 */

import React from 'react';
import {
  Receipt,
  Download,
  ExternalLink,
  CheckCircle,
  Clock,
  AlertTriangle,
  FileText,
} from 'lucide-react';
import { useInvoices, useDownloadInvoice } from '../../hooks';

const STATUS_CONFIG = {
  paid: { label: 'Paid', color: '#22c55e', icon: CheckCircle },
  open: { label: 'Open', color: '#f59e0b', icon: Clock },
  draft: { label: 'Draft', color: '#8b919e', icon: FileText },
  uncollectible: { label: 'Uncollectible', color: '#ef4444', icon: AlertTriangle },
  void: { label: 'Void', color: '#8b919e', icon: AlertTriangle },
};

export default function InvoiceList() {
  const { data: invoices, isLoading, error } = useInvoices(20);
  const downloadMutation = useDownloadInvoice();

  if (isLoading) {
    return (
      <div className="invoice-list loading">
        <style>{`
          .invoice-list.loading {
            background: var(--bg-secondary, #111318);
            border: 1px solid var(--border-primary, #23262f);
            border-radius: 12px;
            padding: 40px;
            text-align: center;
            color: var(--text-secondary, #8b919e);
          }
        `}</style>
        Loading invoices...
      </div>
    );
  }

  if (error) {
    return (
      <div className="invoice-list error">
        <style>{`
          .invoice-list.error {
            background: var(--bg-secondary, #111318);
            border: 1px solid var(--border-primary, #23262f);
            border-radius: 12px;
            padding: 40px;
            text-align: center;
            color: var(--error, #ef4444);
          }
        `}</style>
        Failed to load invoices
      </div>
    );
  }

  return (
    <div className="invoice-list">
      <style>{`
        .invoice-list {
          background: var(--bg-secondary, #111318);
          border: 1px solid var(--border-primary, #23262f);
          border-radius: 12px;
          overflow: hidden;
        }

        .list-header {
          display: flex;
          align-items: center;
          justify-content: space-between;
          padding: 20px;
          border-bottom: 1px solid var(--border-primary, #23262f);
        }

        .list-title {
          display: flex;
          align-items: center;
          gap: 10px;
          font-size: 16px;
          font-weight: 600;
          color: var(--text-primary, #f0f2f5);
          margin: 0;
        }

        .list-title svg {
          width: 20px;
          height: 20px;
          color: var(--accent-primary, #6366f1);
        }

        .invoice-count {
          font-size: 13px;
          color: var(--text-secondary, #8b919e);
        }

        .invoices-table {
          width: 100%;
        }

        .table-header {
          display: grid;
          grid-template-columns: 1fr 1fr 1fr 1fr 120px;
          gap: 16px;
          padding: 12px 20px;
          background: var(--bg-tertiary, #1a1d24);
          border-bottom: 1px solid var(--border-primary, #23262f);
        }

        .table-header-cell {
          font-size: 11px;
          font-weight: 600;
          color: var(--text-secondary, #8b919e);
          text-transform: uppercase;
          letter-spacing: 0.5px;
        }

        .invoice-row {
          display: grid;
          grid-template-columns: 1fr 1fr 1fr 1fr 120px;
          gap: 16px;
          padding: 16px 20px;
          border-bottom: 1px solid var(--border-primary, #23262f);
          align-items: center;
        }

        .invoice-row:last-child {
          border-bottom: none;
        }

        .invoice-row:hover {
          background: var(--bg-tertiary, #1a1d24);
        }

        .invoice-number {
          font-size: 14px;
          font-weight: 500;
          color: var(--text-primary, #f0f2f5);
          font-family: monospace;
        }

        .invoice-date {
          font-size: 13px;
          color: var(--text-secondary, #8b919e);
        }

        .invoice-amount {
          font-size: 14px;
          font-weight: 600;
          color: var(--text-primary, #f0f2f5);
        }

        .status-badge {
          display: inline-flex;
          align-items: center;
          gap: 6px;
          padding: 4px 10px;
          border-radius: 12px;
          font-size: 12px;
          font-weight: 500;
          width: fit-content;
        }

        .status-badge svg {
          width: 12px;
          height: 12px;
        }

        .invoice-actions {
          display: flex;
          gap: 8px;
        }

        .action-btn {
          width: 32px;
          height: 32px;
          display: flex;
          align-items: center;
          justify-content: center;
          background: transparent;
          border: 1px solid var(--border-primary, #23262f);
          border-radius: 6px;
          color: var(--text-secondary, #8b919e);
          cursor: pointer;
          transition: all 0.15s;
        }

        .action-btn:hover {
          background: var(--bg-tertiary, #1a1d24);
          color: var(--text-primary, #f0f2f5);
          border-color: var(--accent-primary, #6366f1);
        }

        .action-btn svg {
          width: 14px;
          height: 14px;
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
          font-weight: 600;
          color: var(--text-primary, #f0f2f5);
          margin: 0 0 8px;
        }

        .empty-message {
          font-size: 14px;
          color: var(--text-secondary, #8b919e);
          margin: 0;
        }

        @media (max-width: 800px) {
          .table-header,
          .invoice-row {
            grid-template-columns: 1fr 1fr 1fr 80px;
          }

          .table-header-cell:nth-child(2),
          .invoice-row > *:nth-child(2) {
            display: none;
          }
        }
      `}</style>

      <div className="list-header">
        <h3 className="list-title">
          <Receipt />
          Invoices
        </h3>
        <span className="invoice-count">
          {invoices?.length || 0} invoice{invoices?.length !== 1 ? 's' : ''}
        </span>
      </div>

      {!invoices || invoices.length === 0 ? (
        <div className="empty-state">
          <Receipt className="empty-icon" />
          <h4 className="empty-title">No invoices yet</h4>
          <p className="empty-message">
            Invoices will appear here after your first billing cycle
          </p>
        </div>
      ) : (
        <div className="invoices-table">
          <div className="table-header">
            <div className="table-header-cell">Invoice</div>
            <div className="table-header-cell">Date</div>
            <div className="table-header-cell">Amount</div>
            <div className="table-header-cell">Status</div>
            <div className="table-header-cell">Actions</div>
          </div>

          {invoices.map((invoice) => {
            const status = STATUS_CONFIG[invoice.status] || STATUS_CONFIG.draft;
            const StatusIcon = status.icon;

            return (
              <div key={invoice.id} className="invoice-row">
                <div className="invoice-number">{invoice.number}</div>
                <div className="invoice-date">
                  {new Date(invoice.created).toLocaleDateString()}
                </div>
                <div className="invoice-amount">{invoice.amount_due_formatted}</div>
                <div>
                  <span
                    className="status-badge"
                    style={{
                      color: status.color,
                      background: `${status.color}15`,
                    }}
                  >
                    <StatusIcon />
                    {status.label}
                  </span>
                </div>
                <div className="invoice-actions">
                  {invoice.pdf_url && (
                    <button
                      className="action-btn"
                      onClick={() => downloadMutation.mutate(invoice.id)}
                      title="Download PDF"
                    >
                      <Download />
                    </button>
                  )}
                  {invoice.hosted_invoice_url && (
                    <button
                      className="action-btn"
                      onClick={() => window.open(invoice.hosted_invoice_url, '_blank')}
                      title="View Invoice"
                    >
                      <ExternalLink />
                    </button>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
