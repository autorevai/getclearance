/**
 * DocumentList Component
 *
 * Display uploaded documents for an applicant with:
 * - Document type, status, upload date
 * - OCR confidence score
 * - Extracted data (name, DOB, document number)
 * - Fraud signals if any
 * - Download via presigned URL
 * - Delete with confirmation
 */

import React, { useState, useCallback } from 'react';
import {
  FileText,
  Image,
  Download,
  Trash2,
  Eye,
  RefreshCw,
  CheckCircle2,
  XCircle,
  Clock,
  AlertTriangle,
  Loader2,
  ChevronDown,
  ChevronRight,
  Sparkles,
  Shield
} from 'lucide-react';
import { useApplicantDocuments, useDeleteDocument, useDownloadDocument, useAnalyzeDocument } from '../hooks/useDocuments';
import { useToast } from '../contexts/ToastContext';
import { ConfirmDialog } from './shared';

// Status configuration
const STATUS_CONFIG = {
  pending: { label: 'Pending', color: 'muted', icon: Clock },
  processing: { label: 'Processing', color: 'info', icon: Loader2, animate: true },
  verified: { label: 'Verified', color: 'success', icon: CheckCircle2 },
  failed: { label: 'Failed', color: 'danger', icon: XCircle },
  rejected: { label: 'Rejected', color: 'danger', icon: XCircle },
  pending_review: { label: 'Review', color: 'warning', icon: AlertTriangle },
};

// Document type labels
const DOCUMENT_TYPE_LABELS = {
  passport: 'Passport',
  driver_license: "Driver's License",
  id_card: 'ID Card',
  utility_bill: 'Utility Bill',
  bank_statement: 'Bank Statement',
  proof_of_address: 'Proof of Address',
  selfie: 'Selfie',
  other: 'Other Document',
};

/**
 * Format date for display
 */
function formatDate(dateStr) {
  if (!dateStr) return '—';
  const date = new Date(dateStr);
  return date.toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}

/**
 * Format file size
 */
function formatFileSize(bytes) {
  if (!bytes) return '—';
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

/**
 * Get icon for file type
 */
function FileIcon({ type, contentType }) {
  if (contentType?.startsWith('image/') || ['passport', 'driver_license', 'id_card', 'selfie'].includes(type)) {
    return <Image size={20} />;
  }
  return <FileText size={20} />;
}

/**
 * Single document item component
 */
function DocumentItem({ document, onView, onDownload, onDelete, onReanalyze, isDeleting, isDownloading, isReanalyzing }) {
  const [expanded, setExpanded] = useState(false);

  const status = STATUS_CONFIG[document.status] || STATUS_CONFIG.pending;
  const StatusIcon = status.icon;
  const typeLabel = DOCUMENT_TYPE_LABELS[document.document_type] || document.document_type;

  // Check for fraud signals
  const hasFraudSignals = document.fraud_signals && document.fraud_signals.length > 0;
  const hasExtractedData = document.extracted_data && Object.keys(document.extracted_data).length > 0;

  return (
    <div className={`document-item ${expanded ? 'expanded' : ''}`}>
      <div className="document-item-main" onClick={() => setExpanded(!expanded)}>
        <div className="document-item-icon">
          <FileIcon type={document.document_type} contentType={document.content_type} />
        </div>

        <div className="document-item-info">
          <div className="document-item-type">{typeLabel}</div>
          <div className="document-item-meta">
            {document.file_name || document.filename || 'Unnamed document'} • {formatFileSize(document.file_size)}
          </div>
        </div>

        <div className="document-item-center">
          {document.ocr_confidence !== null && document.ocr_confidence !== undefined && (
            <div className="document-ocr-score">
              <Sparkles size={14} />
              <span>{Math.round(document.ocr_confidence * 100)}% OCR</span>
            </div>
          )}

          {hasFraudSignals && (
            <div className="document-fraud-badge">
              <Shield size={14} />
              <span>{document.fraud_signals.length} signal{document.fraud_signals.length > 1 ? 's' : ''}</span>
            </div>
          )}
        </div>

        <div className={`document-status status-${status.color}`}>
          <StatusIcon size={14} className={status.animate ? 'spinner' : ''} />
          <span>{status.label}</span>
        </div>

        <div className="document-item-date">
          {formatDate(document.uploaded_at || document.created_at)}
        </div>

        <div className="document-item-actions">
          <button
            className="doc-action-btn"
            onClick={(e) => { e.stopPropagation(); onView(document); }}
            title="Preview document"
          >
            <Eye size={16} />
          </button>
          <button
            className="doc-action-btn"
            onClick={(e) => { e.stopPropagation(); onDownload(document); }}
            disabled={isDownloading}
            title="Download document"
          >
            {isDownloading ? <Loader2 size={16} className="spinner" /> : <Download size={16} />}
          </button>
          <button
            className="doc-action-btn"
            onClick={(e) => { e.stopPropagation(); onReanalyze(document); }}
            disabled={isReanalyzing || document.status === 'processing'}
            title="Re-run AI analysis"
          >
            {isReanalyzing ? <Loader2 size={16} className="spinner" /> : <RefreshCw size={16} />}
          </button>
          <button
            className="doc-action-btn doc-action-danger"
            onClick={(e) => { e.stopPropagation(); onDelete(document); }}
            disabled={isDeleting}
            title="Delete document"
          >
            {isDeleting ? <Loader2 size={16} className="spinner" /> : <Trash2 size={16} />}
          </button>
        </div>

        <div className="document-expand-icon">
          {expanded ? <ChevronDown size={16} /> : <ChevronRight size={16} />}
        </div>
      </div>

      {/* Expanded details */}
      {expanded && (
        <div className="document-item-details">
          {/* Extracted data */}
          {hasExtractedData && (
            <div className="document-detail-section">
              <div className="document-detail-title">
                <Sparkles size={14} />
                Extracted Data
              </div>
              <div className="document-extracted-grid">
                {document.extracted_data.full_name && (
                  <div className="extracted-item">
                    <span className="extracted-label">Full Name</span>
                    <span className="extracted-value">{document.extracted_data.full_name}</span>
                  </div>
                )}
                {document.extracted_data.date_of_birth && (
                  <div className="extracted-item">
                    <span className="extracted-label">Date of Birth</span>
                    <span className="extracted-value">{document.extracted_data.date_of_birth}</span>
                  </div>
                )}
                {document.extracted_data.document_number && (
                  <div className="extracted-item">
                    <span className="extracted-label">Document Number</span>
                    <span className="extracted-value">{document.extracted_data.document_number}</span>
                  </div>
                )}
                {document.extracted_data.expiry_date && (
                  <div className="extracted-item">
                    <span className="extracted-label">Expiry Date</span>
                    <span className="extracted-value">{document.extracted_data.expiry_date}</span>
                  </div>
                )}
                {document.extracted_data.nationality && (
                  <div className="extracted-item">
                    <span className="extracted-label">Nationality</span>
                    <span className="extracted-value">{document.extracted_data.nationality}</span>
                  </div>
                )}
                {document.extracted_data.issuing_country && (
                  <div className="extracted-item">
                    <span className="extracted-label">Issuing Country</span>
                    <span className="extracted-value">{document.extracted_data.issuing_country}</span>
                  </div>
                )}
                {document.extracted_data.address && (
                  <div className="extracted-item" style={{ gridColumn: 'span 2' }}>
                    <span className="extracted-label">Address</span>
                    <span className="extracted-value">{document.extracted_data.address}</span>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* MRZ validation */}
          {document.mrz_valid !== undefined && (
            <div className="document-detail-section">
              <div className="document-detail-title">
                <Shield size={14} />
                MRZ Validation
              </div>
              <div className={`mrz-status ${document.mrz_valid ? 'valid' : 'invalid'}`}>
                {document.mrz_valid ? <CheckCircle2 size={14} /> : <XCircle size={14} />}
                <span>{document.mrz_valid ? 'MRZ checksums valid' : 'MRZ validation failed'}</span>
              </div>
            </div>
          )}

          {/* Fraud signals */}
          {hasFraudSignals && (
            <div className="document-detail-section">
              <div className="document-detail-title fraud">
                <AlertTriangle size={14} />
                Fraud Signals
              </div>
              <div className="fraud-signals-list">
                {document.fraud_signals.map((signal, idx) => (
                  <div key={idx} className="fraud-signal-item">
                    <AlertTriangle size={14} />
                    <span>{signal.description || signal.type || signal}</span>
                    {signal.confidence && (
                      <span className="fraud-signal-confidence">{Math.round(signal.confidence * 100)}%</span>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* AI analysis */}
          {document.ai_analysis && (
            <div className="document-detail-section">
              <div className="document-detail-title">
                <Sparkles size={14} />
                AI Analysis
              </div>
              <div className="ai-analysis-content">
                {document.ai_analysis.summary || document.ai_analysis.notes || JSON.stringify(document.ai_analysis)}
              </div>
            </div>
          )}

          {/* No details available */}
          {!hasExtractedData && !hasFraudSignals && !document.ai_analysis && document.mrz_valid === undefined && (
            <div className="document-no-details">
              No additional details available
            </div>
          )}
        </div>
      )}
    </div>
  );
}

/**
 * Main DocumentList component
 */
export default function DocumentList({ applicantId, onDocumentClick, showEmpty = true }) {
  const toast = useToast();

  // State for delete confirmation
  const [deleteTarget, setDeleteTarget] = useState(null);

  // Fetch documents
  const { data: documents, isLoading, error, refetch } = useApplicantDocuments(applicantId);

  // Mutations
  const deleteMutation = useDeleteDocument();
  const downloadMutation = useDownloadDocument();
  const analyzeMutation = useAnalyzeDocument();

  // Handle document view
  const handleView = useCallback((doc) => {
    onDocumentClick?.(doc);
  }, [onDocumentClick]);

  // Handle document download
  const handleDownload = useCallback(async (doc) => {
    try {
      await downloadMutation.mutateAsync({
        id: doc.id,
        openInNewTab: true,
        filename: doc.file_name || doc.filename,
      });
    } catch (err) {
      toast.error(`Failed to download: ${err.message}`);
    }
  }, [downloadMutation, toast]);

  // Handle delete confirmation
  const handleDeleteClick = useCallback((doc) => {
    setDeleteTarget(doc);
  }, []);

  // Execute delete
  const handleDeleteConfirm = useCallback(async () => {
    if (!deleteTarget) return;

    try {
      await deleteMutation.mutateAsync({
        id: deleteTarget.id,
        applicantId,
      });
      toast.success('Document deleted successfully');
    } catch (err) {
      toast.error(`Failed to delete: ${err.message}`);
    } finally {
      setDeleteTarget(null);
    }
  }, [deleteTarget, deleteMutation, applicantId, toast]);

  // Handle re-analyze
  const handleReanalyze = useCallback(async (doc) => {
    try {
      await analyzeMutation.mutateAsync({ id: doc.id });
      toast.success('AI analysis started');
    } catch (err) {
      toast.error(`Failed to start analysis: ${err.message}`);
    }
  }, [analyzeMutation, toast]);

  // Loading state
  if (isLoading) {
    return (
      <div className="document-list-loading">
        <Loader2 size={24} className="spinner" />
        <span>Loading documents...</span>
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div className="document-list-error">
        <AlertTriangle size={24} />
        <span>Failed to load documents</span>
        <button onClick={() => refetch()} className="retry-btn">
          <RefreshCw size={14} />
          Retry
        </button>
      </div>
    );
  }

  // Empty state
  const documentList = Array.isArray(documents) ? documents : documents?.items || [];

  if (documentList.length === 0 && showEmpty) {
    return (
      <div className="document-list-empty">
        <FileText size={32} />
        <span>No documents uploaded yet</span>
      </div>
    );
  }

  return (
    <div className="document-list">
      <style>{`
        .document-list {
          display: flex;
          flex-direction: column;
          gap: 12px;
        }

        .document-list-loading,
        .document-list-error,
        .document-list-empty {
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          gap: 12px;
          padding: 40px;
          color: var(--text-muted);
          text-align: center;
        }

        .document-list-error {
          color: var(--danger);
        }

        .retry-btn {
          display: flex;
          align-items: center;
          gap: 6px;
          padding: 8px 16px;
          font-size: 13px;
          background: var(--bg-secondary);
          border: 1px solid var(--border-color);
          border-radius: 6px;
          color: var(--text-primary);
          cursor: pointer;
          transition: all 0.15s;
        }

        .retry-btn:hover {
          background: var(--bg-hover);
        }

        .document-item {
          background: var(--bg-tertiary);
          border-radius: 10px;
          overflow: hidden;
          transition: all 0.15s;
        }

        .document-item:hover {
          background: var(--bg-hover);
        }

        .document-item.expanded {
          background: var(--bg-secondary);
          border: 1px solid var(--border-color);
        }

        .document-item-main {
          display: flex;
          align-items: center;
          gap: 12px;
          padding: 14px 16px;
          cursor: pointer;
        }

        .document-item-icon {
          width: 40px;
          height: 40px;
          border-radius: 8px;
          background: var(--bg-secondary);
          display: flex;
          align-items: center;
          justify-content: center;
          color: var(--text-muted);
          flex-shrink: 0;
        }

        .document-item-info {
          flex: 1;
          min-width: 0;
        }

        .document-item-type {
          font-size: 14px;
          font-weight: 500;
          color: var(--text-primary);
        }

        .document-item-meta {
          font-size: 12px;
          color: var(--text-muted);
          white-space: nowrap;
          overflow: hidden;
          text-overflow: ellipsis;
        }

        .document-item-center {
          display: flex;
          align-items: center;
          gap: 12px;
          flex-shrink: 0;
        }

        .document-ocr-score {
          display: flex;
          align-items: center;
          gap: 4px;
          padding: 4px 8px;
          background: rgba(99, 102, 241, 0.1);
          border-radius: 6px;
          font-size: 11px;
          font-weight: 600;
          color: var(--accent-primary);
        }

        .document-fraud-badge {
          display: flex;
          align-items: center;
          gap: 4px;
          padding: 4px 8px;
          background: rgba(245, 158, 11, 0.15);
          border-radius: 6px;
          font-size: 11px;
          font-weight: 600;
          color: var(--warning);
        }

        .document-status {
          display: flex;
          align-items: center;
          gap: 6px;
          padding: 6px 12px;
          border-radius: 20px;
          font-size: 12px;
          font-weight: 500;
          flex-shrink: 0;
        }

        .document-status.status-success {
          background: rgba(16, 185, 129, 0.15);
          color: var(--success);
        }

        .document-status.status-danger {
          background: rgba(239, 68, 68, 0.15);
          color: var(--danger);
        }

        .document-status.status-warning {
          background: rgba(245, 158, 11, 0.15);
          color: var(--warning);
        }

        .document-status.status-info {
          background: rgba(59, 130, 246, 0.15);
          color: var(--info);
        }

        .document-status.status-muted {
          background: var(--bg-tertiary);
          color: var(--text-muted);
        }

        .document-item-date {
          font-size: 12px;
          color: var(--text-muted);
          flex-shrink: 0;
          min-width: 130px;
          text-align: right;
        }

        .document-item-actions {
          display: flex;
          gap: 4px;
          flex-shrink: 0;
        }

        .doc-action-btn {
          padding: 8px;
          border-radius: 6px;
          background: transparent;
          border: none;
          color: var(--text-muted);
          cursor: pointer;
          transition: all 0.15s;
        }

        .doc-action-btn:hover:not(:disabled) {
          background: var(--bg-secondary);
          color: var(--text-primary);
        }

        .doc-action-btn:disabled {
          opacity: 0.5;
          cursor: not-allowed;
        }

        .doc-action-btn.doc-action-danger:hover:not(:disabled) {
          background: rgba(239, 68, 68, 0.1);
          color: var(--danger);
        }

        .document-expand-icon {
          color: var(--text-muted);
          flex-shrink: 0;
        }

        /* Expanded details */
        .document-item-details {
          padding: 0 16px 16px;
          border-top: 1px solid var(--border-color);
          margin-top: 0;
          padding-top: 16px;
        }

        .document-detail-section {
          margin-bottom: 16px;
        }

        .document-detail-section:last-child {
          margin-bottom: 0;
        }

        .document-detail-title {
          display: flex;
          align-items: center;
          gap: 6px;
          font-size: 12px;
          font-weight: 600;
          text-transform: uppercase;
          letter-spacing: 0.05em;
          color: var(--text-muted);
          margin-bottom: 10px;
        }

        .document-detail-title.fraud {
          color: var(--warning);
        }

        .document-extracted-grid {
          display: grid;
          grid-template-columns: repeat(2, 1fr);
          gap: 12px;
        }

        .extracted-item {
          display: flex;
          flex-direction: column;
          gap: 2px;
        }

        .extracted-label {
          font-size: 11px;
          color: var(--text-muted);
          text-transform: uppercase;
          letter-spacing: 0.03em;
        }

        .extracted-value {
          font-size: 13px;
          color: var(--text-primary);
        }

        .mrz-status {
          display: flex;
          align-items: center;
          gap: 8px;
          padding: 10px 12px;
          border-radius: 8px;
          font-size: 13px;
        }

        .mrz-status.valid {
          background: rgba(16, 185, 129, 0.1);
          color: var(--success);
        }

        .mrz-status.invalid {
          background: rgba(239, 68, 68, 0.1);
          color: var(--danger);
        }

        .fraud-signals-list {
          display: flex;
          flex-direction: column;
          gap: 8px;
        }

        .fraud-signal-item {
          display: flex;
          align-items: center;
          gap: 8px;
          padding: 10px 12px;
          background: rgba(245, 158, 11, 0.1);
          border: 1px solid rgba(245, 158, 11, 0.2);
          border-radius: 8px;
          font-size: 13px;
          color: var(--warning);
        }

        .fraud-signal-confidence {
          margin-left: auto;
          font-weight: 600;
        }

        .ai-analysis-content {
          font-size: 13px;
          line-height: 1.6;
          color: var(--text-secondary);
          padding: 12px;
          background: var(--bg-tertiary);
          border-radius: 8px;
        }

        .document-no-details {
          text-align: center;
          padding: 20px;
          color: var(--text-muted);
          font-size: 13px;
        }

        @keyframes spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }

        .spinner {
          animation: spin 1s linear infinite;
        }

        @media (max-width: 900px) {
          .document-item-main {
            flex-wrap: wrap;
          }

          .document-item-center {
            order: 5;
            width: 100%;
            margin-top: 8px;
          }

          .document-item-date {
            display: none;
          }

          .document-extracted-grid {
            grid-template-columns: 1fr;
          }
        }
      `}</style>

      {documentList.map((doc) => (
        <DocumentItem
          key={doc.id}
          document={doc}
          onView={handleView}
          onDownload={handleDownload}
          onDelete={handleDeleteClick}
          onReanalyze={handleReanalyze}
          isDeleting={deleteMutation.isPending && deleteMutation.variables?.id === doc.id}
          isDownloading={downloadMutation.isPending && downloadMutation.variables?.id === doc.id}
          isReanalyzing={analyzeMutation.isPending && analyzeMutation.variables?.id === doc.id}
        />
      ))}

      {/* Delete confirmation dialog */}
      <ConfirmDialog
        isOpen={!!deleteTarget}
        title="Delete Document"
        message={`Are you sure you want to delete "${deleteTarget?.file_name || deleteTarget?.filename || 'this document'}"? This action cannot be undone.`}
        confirmLabel="Delete"
        variant="danger"
        isLoading={deleteMutation.isPending}
        onConfirm={handleDeleteConfirm}
        onCancel={() => setDeleteTarget(null)}
      />
    </div>
  );
}
