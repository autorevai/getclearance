/**
 * DocumentPreview Component
 *
 * Modal component to preview document with:
 * - Document image/PDF viewer
 * - Extracted OCR text
 * - AI analysis results
 * - Verification checks (pass/fail)
 */

import React, { useState, useEffect, useCallback } from 'react';
import {
  X,
  Download,
  RefreshCw,
  FileText,
  Image,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  Sparkles,
  Shield,
  Loader2,
  ExternalLink,
  ZoomIn,
  ZoomOut,
  RotateCw
} from 'lucide-react';
import { useDocument, useDownloadDocument, useAnalyzeDocument, useDocumentPolling } from '../hooks/useDocuments';
import { useToast } from '../contexts/ToastContext';

// Status configuration
const STATUS_CONFIG = {
  pending: { label: 'Pending', color: 'muted', icon: Sparkles },
  processing: { label: 'Processing', color: 'info', icon: Loader2, animate: true },
  verified: { label: 'Verified', color: 'success', icon: CheckCircle2 },
  failed: { label: 'Failed', color: 'danger', icon: XCircle },
  rejected: { label: 'Rejected', color: 'danger', icon: XCircle },
  pending_review: { label: 'Needs Review', color: 'warning', icon: AlertTriangle },
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
 * Verification check item
 */
function VerificationCheck({ label, passed, details }) {
  return (
    <div className={`verification-check ${passed ? 'passed' : 'failed'}`}>
      {passed ? <CheckCircle2 size={16} /> : <XCircle size={16} />}
      <div className="verification-check-content">
        <span className="verification-check-label">{label}</span>
        {details && <span className="verification-check-details">{details}</span>}
      </div>
    </div>
  );
}

export default function DocumentPreview({ documentId, document: initialDocument, isOpen, onClose }) {
  const toast = useToast();

  // State
  const [previewUrl, setPreviewUrl] = useState(null);
  const [imageZoom, setImageZoom] = useState(1);
  const [imageRotation, setImageRotation] = useState(0);
  const [activeTab, setActiveTab] = useState('preview');

  // Fetch document data if not provided
  const { data: fetchedDocument, isLoading: isLoadingDocument } = useDocument(
    initialDocument ? null : documentId,
    { enabled: isOpen && !initialDocument }
  );

  const document = initialDocument || fetchedDocument;

  // Poll for processing updates
  const { data: polledDocument } = useDocumentPolling(
    document?.status === 'processing' ? document.id : null,
    {
      enabled: isOpen && document?.status === 'processing',
      onComplete: () => {
        toast.success('Document processing complete');
      },
    }
  );

  // Use polled document if available
  const currentDocument = polledDocument || document;

  // Mutations
  const downloadMutation = useDownloadDocument();
  const analyzeMutation = useAnalyzeDocument();

  // Fetch preview URL when document is available
  useEffect(() => {
    if (!currentDocument || !isOpen) {
      setPreviewUrl(null);
      return;
    }

    // If document has a storage URL, use it
    if (currentDocument.storage_url) {
      setPreviewUrl(currentDocument.storage_url);
    }
  }, [currentDocument, isOpen]);

  // Reset state when modal opens/closes
  useEffect(() => {
    if (isOpen) {
      setImageZoom(1);
      setImageRotation(0);
      setActiveTab('preview');
    }
  }, [isOpen]);

  // Handle close with escape key
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === 'Escape' && isOpen) {
        onClose();
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onClose]);

  // Handle download
  const handleDownload = useCallback(async () => {
    if (!currentDocument) return;

    try {
      await downloadMutation.mutateAsync({
        id: currentDocument.id,
        openInNewTab: false,
        filename: currentDocument.file_name || currentDocument.filename,
      });
      toast.success('Download started');
    } catch (err) {
      toast.error(`Download failed: ${err.message}`);
    }
  }, [currentDocument, downloadMutation, toast]);

  // Handle re-analyze
  const handleReanalyze = useCallback(async () => {
    if (!currentDocument) return;

    try {
      await analyzeMutation.mutateAsync({ id: currentDocument.id });
      toast.success('AI analysis started');
    } catch (err) {
      toast.error(`Analysis failed: ${err.message}`);
    }
  }, [currentDocument, analyzeMutation, toast]);

  // Zoom controls
  const handleZoomIn = useCallback(() => {
    setImageZoom((z) => Math.min(z + 0.25, 3));
  }, []);

  const handleZoomOut = useCallback(() => {
    setImageZoom((z) => Math.max(z - 0.25, 0.5));
  }, []);

  const handleRotate = useCallback(() => {
    setImageRotation((r) => (r + 90) % 360);
  }, []);

  // Handle backdrop click
  const handleBackdropClick = useCallback((e) => {
    if (e.target === e.currentTarget) {
      onClose();
    }
  }, [onClose]);

  if (!isOpen) return null;

  // Loading state
  if (isLoadingDocument) {
    return (
      <div className="document-preview-modal" onClick={handleBackdropClick}>
        <div className="document-preview-loading">
          <Loader2 size={32} className="spinner" />
          <span>Loading document...</span>
        </div>
      </div>
    );
  }

  // No document
  if (!currentDocument) {
    return (
      <div className="document-preview-modal" onClick={handleBackdropClick}>
        <div className="document-preview-error">
          <AlertTriangle size={32} />
          <span>Document not found</span>
          <button onClick={onClose}>Close</button>
        </div>
      </div>
    );
  }

  const status = STATUS_CONFIG[currentDocument.status] || STATUS_CONFIG.pending;
  const StatusIcon = status.icon;
  const typeLabel = DOCUMENT_TYPE_LABELS[currentDocument.document_type] || currentDocument.document_type;
  const isImage = currentDocument.content_type?.startsWith('image/');

  // Determine verification checks
  const verificationChecks = [];

  if (currentDocument.mrz_valid !== undefined) {
    verificationChecks.push({
      label: 'MRZ Validation',
      passed: currentDocument.mrz_valid,
      details: currentDocument.mrz_valid ? 'Checksums verified' : 'Invalid checksums detected',
    });
  }

  if (currentDocument.ocr_confidence !== undefined) {
    verificationChecks.push({
      label: 'OCR Quality',
      passed: currentDocument.ocr_confidence >= 0.7,
      details: `${Math.round(currentDocument.ocr_confidence * 100)}% confidence`,
    });
  }

  if (currentDocument.fraud_signals) {
    verificationChecks.push({
      label: 'Fraud Detection',
      passed: currentDocument.fraud_signals.length === 0,
      details: currentDocument.fraud_signals.length > 0
        ? `${currentDocument.fraud_signals.length} signal(s) detected`
        : 'No fraud signals',
    });
  }

  if (currentDocument.status === 'verified') {
    verificationChecks.push({
      label: 'Overall Status',
      passed: true,
      details: 'Document verified',
    });
  } else if (currentDocument.status === 'failed' || currentDocument.status === 'rejected') {
    verificationChecks.push({
      label: 'Overall Status',
      passed: false,
      details: currentDocument.rejection_reason || 'Verification failed',
    });
  }

  return (
    <div className="document-preview-modal" onClick={handleBackdropClick}>
      <style>{`
        .document-preview-modal {
          position: fixed;
          inset: 0;
          background: rgba(0, 0, 0, 0.8);
          display: flex;
          align-items: center;
          justify-content: center;
          z-index: 1000;
          padding: 24px;
        }

        .document-preview-loading,
        .document-preview-error {
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          gap: 16px;
          color: white;
          text-align: center;
        }

        .document-preview-error button {
          padding: 8px 16px;
          background: var(--bg-secondary);
          border: 1px solid var(--border-color);
          border-radius: 6px;
          color: var(--text-primary);
          cursor: pointer;
        }

        .document-preview-container {
          background: var(--bg-primary);
          border-radius: 16px;
          overflow: hidden;
          width: 100%;
          max-width: 1200px;
          max-height: 90vh;
          display: flex;
          flex-direction: column;
        }

        .document-preview-header {
          display: flex;
          align-items: center;
          gap: 16px;
          padding: 16px 20px;
          border-bottom: 1px solid var(--border-color);
          background: var(--bg-secondary);
        }

        .document-preview-icon {
          width: 48px;
          height: 48px;
          border-radius: 10px;
          background: var(--bg-tertiary);
          display: flex;
          align-items: center;
          justify-content: center;
          color: var(--text-muted);
        }

        .document-preview-info {
          flex: 1;
        }

        .document-preview-title {
          font-size: 18px;
          font-weight: 600;
          margin-bottom: 4px;
        }

        .document-preview-meta {
          font-size: 13px;
          color: var(--text-muted);
        }

        .document-preview-status {
          display: flex;
          align-items: center;
          gap: 6px;
          padding: 8px 14px;
          border-radius: 20px;
          font-size: 13px;
          font-weight: 500;
        }

        .document-preview-status.success {
          background: rgba(16, 185, 129, 0.15);
          color: var(--success);
        }

        .document-preview-status.danger {
          background: rgba(239, 68, 68, 0.15);
          color: var(--danger);
        }

        .document-preview-status.warning {
          background: rgba(245, 158, 11, 0.15);
          color: var(--warning);
        }

        .document-preview-status.info {
          background: rgba(59, 130, 246, 0.15);
          color: var(--info);
        }

        .document-preview-status.muted {
          background: var(--bg-tertiary);
          color: var(--text-muted);
        }

        .document-preview-actions {
          display: flex;
          gap: 8px;
        }

        .preview-action-btn {
          padding: 10px;
          border-radius: 8px;
          background: var(--bg-tertiary);
          border: none;
          color: var(--text-secondary);
          cursor: pointer;
          transition: all 0.15s;
        }

        .preview-action-btn:hover:not(:disabled) {
          background: var(--bg-hover);
          color: var(--text-primary);
        }

        .preview-action-btn:disabled {
          opacity: 0.5;
          cursor: not-allowed;
        }

        .preview-close-btn {
          padding: 10px;
          border-radius: 8px;
          background: transparent;
          border: none;
          color: var(--text-muted);
          cursor: pointer;
          transition: all 0.15s;
        }

        .preview-close-btn:hover {
          background: var(--bg-hover);
          color: var(--text-primary);
        }

        /* Tabs */
        .document-preview-tabs {
          display: flex;
          gap: 4px;
          padding: 12px 20px;
          background: var(--bg-secondary);
          border-bottom: 1px solid var(--border-color);
        }

        .preview-tab {
          padding: 8px 16px;
          border-radius: 6px;
          font-size: 13px;
          font-weight: 500;
          color: var(--text-muted);
          cursor: pointer;
          transition: all 0.15s;
        }

        .preview-tab:hover {
          color: var(--text-secondary);
        }

        .preview-tab.active {
          background: var(--bg-tertiary);
          color: var(--text-primary);
        }

        /* Content area */
        .document-preview-content {
          flex: 1;
          overflow: auto;
          display: flex;
        }

        /* Preview panel */
        .preview-panel {
          flex: 1;
          display: flex;
          align-items: center;
          justify-content: center;
          background: var(--bg-tertiary);
          position: relative;
          min-height: 400px;
        }

        .preview-image-container {
          max-width: 100%;
          max-height: 100%;
          overflow: auto;
          display: flex;
          align-items: center;
          justify-content: center;
          padding: 24px;
        }

        .preview-image {
          max-width: 100%;
          max-height: 100%;
          object-fit: contain;
          border-radius: 8px;
          box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2);
          transition: transform 0.2s ease;
        }

        .preview-controls {
          position: absolute;
          bottom: 16px;
          left: 50%;
          transform: translateX(-50%);
          display: flex;
          gap: 8px;
          padding: 8px;
          background: var(--bg-secondary);
          border-radius: 8px;
          box-shadow: 0 2px 10px rgba(0, 0, 0, 0.2);
        }

        .preview-control-btn {
          padding: 8px;
          border-radius: 6px;
          background: transparent;
          border: none;
          color: var(--text-secondary);
          cursor: pointer;
          transition: all 0.15s;
        }

        .preview-control-btn:hover {
          background: var(--bg-hover);
          color: var(--text-primary);
        }

        .preview-no-preview {
          display: flex;
          flex-direction: column;
          align-items: center;
          gap: 12px;
          color: var(--text-muted);
        }

        .preview-no-preview-btn {
          display: flex;
          align-items: center;
          gap: 6px;
          padding: 10px 16px;
          background: var(--bg-secondary);
          border: 1px solid var(--border-color);
          border-radius: 8px;
          color: var(--text-primary);
          cursor: pointer;
          font-size: 13px;
          transition: all 0.15s;
        }

        .preview-no-preview-btn:hover {
          background: var(--bg-hover);
        }

        /* Details panel */
        .details-panel {
          width: 360px;
          border-left: 1px solid var(--border-color);
          overflow-y: auto;
          flex-shrink: 0;
        }

        .details-section {
          padding: 20px;
          border-bottom: 1px solid var(--border-color);
        }

        .details-section:last-child {
          border-bottom: none;
        }

        .details-section-title {
          display: flex;
          align-items: center;
          gap: 8px;
          font-size: 12px;
          font-weight: 600;
          text-transform: uppercase;
          letter-spacing: 0.05em;
          color: var(--text-muted);
          margin-bottom: 14px;
        }

        /* Verification checks */
        .verification-check {
          display: flex;
          align-items: flex-start;
          gap: 10px;
          padding: 10px 12px;
          border-radius: 8px;
          margin-bottom: 8px;
        }

        .verification-check:last-child {
          margin-bottom: 0;
        }

        .verification-check.passed {
          background: rgba(16, 185, 129, 0.1);
          color: var(--success);
        }

        .verification-check.failed {
          background: rgba(239, 68, 68, 0.1);
          color: var(--danger);
        }

        .verification-check-content {
          flex: 1;
        }

        .verification-check-label {
          display: block;
          font-size: 13px;
          font-weight: 500;
        }

        .verification-check-details {
          display: block;
          font-size: 12px;
          opacity: 0.8;
          margin-top: 2px;
        }

        /* Extracted data */
        .extracted-data-grid {
          display: grid;
          gap: 12px;
        }

        .extracted-data-item {
          display: flex;
          flex-direction: column;
          gap: 2px;
        }

        .extracted-data-label {
          font-size: 11px;
          color: var(--text-muted);
          text-transform: uppercase;
          letter-spacing: 0.03em;
        }

        .extracted-data-value {
          font-size: 13px;
          color: var(--text-primary);
        }

        /* AI analysis */
        .ai-analysis-content {
          font-size: 13px;
          line-height: 1.6;
          color: var(--text-secondary);
        }

        .ai-confidence {
          display: flex;
          align-items: center;
          gap: 8px;
          margin-top: 12px;
          padding: 10px 12px;
          background: var(--bg-tertiary);
          border-radius: 8px;
        }

        .ai-confidence-bar {
          flex: 1;
          height: 6px;
          background: var(--border-color);
          border-radius: 3px;
          overflow: hidden;
        }

        .ai-confidence-fill {
          height: 100%;
          background: var(--accent-primary);
          border-radius: 3px;
        }

        /* Fraud signals */
        .fraud-signal {
          display: flex;
          align-items: flex-start;
          gap: 8px;
          padding: 10px 12px;
          background: rgba(245, 158, 11, 0.1);
          border: 1px solid rgba(245, 158, 11, 0.2);
          border-radius: 8px;
          margin-bottom: 8px;
          font-size: 13px;
          color: var(--warning);
        }

        .fraud-signal:last-child {
          margin-bottom: 0;
        }

        @keyframes spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }

        .spinner {
          animation: spin 1s linear infinite;
        }

        @media (max-width: 900px) {
          .document-preview-container {
            max-width: 100%;
            max-height: 100%;
            border-radius: 0;
          }

          .document-preview-content {
            flex-direction: column;
          }

          .details-panel {
            width: 100%;
            border-left: none;
            border-top: 1px solid var(--border-color);
          }

          .preview-panel {
            min-height: 300px;
          }
        }
      `}</style>

      <div className="document-preview-container" onClick={(e) => e.stopPropagation()}>
        {/* Header */}
        <div className="document-preview-header">
          <div className="document-preview-icon">
            {isImage ? <Image size={24} /> : <FileText size={24} />}
          </div>

          <div className="document-preview-info">
            <div className="document-preview-title">{typeLabel}</div>
            <div className="document-preview-meta">
              {currentDocument.file_name || currentDocument.filename || 'Unnamed document'}
              {' • '}
              {formatFileSize(currentDocument.file_size)}
              {' • '}
              Uploaded {formatDate(currentDocument.uploaded_at || currentDocument.created_at)}
            </div>
          </div>

          <div className={`document-preview-status ${status.color}`}>
            <StatusIcon size={14} className={status.animate ? 'spinner' : ''} />
            {status.label}
          </div>

          <div className="document-preview-actions">
            <button
              className="preview-action-btn"
              onClick={handleReanalyze}
              disabled={analyzeMutation.isPending || currentDocument.status === 'processing'}
              title="Re-run AI analysis"
            >
              {analyzeMutation.isPending ? (
                <Loader2 size={18} className="spinner" />
              ) : (
                <RefreshCw size={18} />
              )}
            </button>
            <button
              className="preview-action-btn"
              onClick={handleDownload}
              disabled={downloadMutation.isPending}
              title="Download document"
            >
              {downloadMutation.isPending ? (
                <Loader2 size={18} className="spinner" />
              ) : (
                <Download size={18} />
              )}
            </button>
          </div>

          <button className="preview-close-btn" onClick={onClose} title="Close">
            <X size={20} />
          </button>
        </div>

        {/* Tabs */}
        <div className="document-preview-tabs">
          <div
            className={`preview-tab ${activeTab === 'preview' ? 'active' : ''}`}
            onClick={() => setActiveTab('preview')}
          >
            Preview
          </div>
          <div
            className={`preview-tab ${activeTab === 'extracted' ? 'active' : ''}`}
            onClick={() => setActiveTab('extracted')}
          >
            Extracted Data
          </div>
          <div
            className={`preview-tab ${activeTab === 'analysis' ? 'active' : ''}`}
            onClick={() => setActiveTab('analysis')}
          >
            AI Analysis
          </div>
        </div>

        {/* Content */}
        <div className="document-preview-content">
          {/* Preview Panel */}
          {activeTab === 'preview' && (
            <div className="preview-panel">
              {previewUrl && isImage ? (
                <>
                  <div className="preview-image-container">
                    <img
                      src={previewUrl}
                      alt={currentDocument.file_name || 'Document'}
                      className="preview-image"
                      style={{
                        transform: `scale(${imageZoom}) rotate(${imageRotation}deg)`,
                      }}
                    />
                  </div>
                  <div className="preview-controls">
                    <button className="preview-control-btn" onClick={handleZoomOut} title="Zoom out">
                      <ZoomOut size={18} />
                    </button>
                    <button className="preview-control-btn" onClick={handleZoomIn} title="Zoom in">
                      <ZoomIn size={18} />
                    </button>
                    <button className="preview-control-btn" onClick={handleRotate} title="Rotate">
                      <RotateCw size={18} />
                    </button>
                  </div>
                </>
              ) : (
                <div className="preview-no-preview">
                  <FileText size={48} />
                  <span>Preview not available</span>
                  <button className="preview-no-preview-btn" onClick={handleDownload}>
                    <ExternalLink size={16} />
                    Open in new tab
                  </button>
                </div>
              )}
            </div>
          )}

          {activeTab === 'extracted' && (
            <div className="preview-panel" style={{ padding: 24, alignItems: 'flex-start', justifyContent: 'flex-start' }}>
              <div style={{ width: '100%', maxWidth: 600 }}>
                {currentDocument.extracted_data && Object.keys(currentDocument.extracted_data).length > 0 ? (
                  <div className="extracted-data-grid">
                    {Object.entries(currentDocument.extracted_data).map(([key, value]) => (
                      <div key={key} className="extracted-data-item">
                        <span className="extracted-data-label">{key.replace(/_/g, ' ')}</span>
                        <span className="extracted-data-value">{value || '—'}</span>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div style={{ color: 'var(--text-muted)', textAlign: 'center', padding: 40 }}>
                    No data extracted yet
                  </div>
                )}
              </div>
            </div>
          )}

          {activeTab === 'analysis' && (
            <div className="preview-panel" style={{ padding: 24, alignItems: 'flex-start', justifyContent: 'flex-start' }}>
              <div style={{ width: '100%', maxWidth: 600 }}>
                {currentDocument.ai_analysis ? (
                  <>
                    <div className="ai-analysis-content">
                      {currentDocument.ai_analysis.summary ||
                       currentDocument.ai_analysis.notes ||
                       JSON.stringify(currentDocument.ai_analysis, null, 2)}
                    </div>
                    {currentDocument.ai_analysis.confidence && (
                      <div className="ai-confidence">
                        <Sparkles size={14} style={{ color: 'var(--accent-primary)' }} />
                        <span style={{ fontSize: 13 }}>Confidence</span>
                        <div className="ai-confidence-bar">
                          <div
                            className="ai-confidence-fill"
                            style={{ width: `${currentDocument.ai_analysis.confidence * 100}%` }}
                          />
                        </div>
                        <span style={{ fontSize: 13, fontWeight: 600 }}>
                          {Math.round(currentDocument.ai_analysis.confidence * 100)}%
                        </span>
                      </div>
                    )}
                  </>
                ) : (
                  <div style={{ color: 'var(--text-muted)', textAlign: 'center', padding: 40 }}>
                    No AI analysis available yet
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Details sidebar */}
          <div className="details-panel">
            {/* Verification checks */}
            {verificationChecks.length > 0 && (
              <div className="details-section">
                <div className="details-section-title">
                  <Shield size={14} />
                  Verification Checks
                </div>
                {verificationChecks.map((check, idx) => (
                  <VerificationCheck
                    key={idx}
                    label={check.label}
                    passed={check.passed}
                    details={check.details}
                  />
                ))}
              </div>
            )}

            {/* Fraud signals */}
            {currentDocument.fraud_signals && currentDocument.fraud_signals.length > 0 && (
              <div className="details-section">
                <div className="details-section-title" style={{ color: 'var(--warning)' }}>
                  <AlertTriangle size={14} />
                  Fraud Signals
                </div>
                {currentDocument.fraud_signals.map((signal, idx) => (
                  <div key={idx} className="fraud-signal">
                    <AlertTriangle size={14} style={{ flexShrink: 0, marginTop: 2 }} />
                    <span>{signal.description || signal.type || signal}</span>
                  </div>
                ))}
              </div>
            )}

            {/* OCR text */}
            {currentDocument.ocr_text && (
              <div className="details-section">
                <div className="details-section-title">
                  <FileText size={14} />
                  OCR Text
                </div>
                <div style={{
                  fontSize: 12,
                  fontFamily: "'JetBrains Mono', monospace",
                  color: 'var(--text-secondary)',
                  background: 'var(--bg-tertiary)',
                  padding: 12,
                  borderRadius: 8,
                  maxHeight: 200,
                  overflow: 'auto',
                  whiteSpace: 'pre-wrap',
                }}>
                  {currentDocument.ocr_text}
                </div>
              </div>
            )}

            {/* Processing info */}
            <div className="details-section">
              <div className="details-section-title">
                <Sparkles size={14} />
                Processing Info
              </div>
              <div className="extracted-data-grid">
                <div className="extracted-data-item">
                  <span className="extracted-data-label">Document ID</span>
                  <span className="extracted-data-value" style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: 11 }}>
                    {currentDocument.id}
                  </span>
                </div>
                {currentDocument.processed_at && (
                  <div className="extracted-data-item">
                    <span className="extracted-data-label">Processed</span>
                    <span className="extracted-data-value">{formatDate(currentDocument.processed_at)}</span>
                  </div>
                )}
                {currentDocument.ocr_confidence !== undefined && (
                  <div className="extracted-data-item">
                    <span className="extracted-data-label">OCR Confidence</span>
                    <span className="extracted-data-value">{Math.round(currentDocument.ocr_confidence * 100)}%</span>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
