/**
 * Company Documents Component
 *
 * Document management tab for company detail page.
 * Supports upload, download, and verification of corporate documents.
 */

import React, { useState, useRef } from 'react';
import {
  FileText,
  Upload,
  Download,
  CheckCircle,
  Clock,
  XCircle,
  Eye,
  Calendar,
  AlertTriangle,
} from 'lucide-react';
import {
  useCompanyDocuments,
  useRequestDocumentUpload,
  useVerifyCompanyDocument,
  useDownloadCompanyDocument,
} from '../../hooks';

const DOCUMENT_TYPES = [
  { value: 'registration_certificate', label: 'Registration Certificate' },
  { value: 'articles_of_incorporation', label: 'Articles of Incorporation' },
  { value: 'shareholder_register', label: 'Shareholder Register' },
  { value: 'board_resolution', label: 'Board Resolution' },
  { value: 'proof_of_address', label: 'Proof of Address' },
  { value: 'tax_certificate', label: 'Tax Certificate' },
  { value: 'bank_statement', label: 'Bank Statement' },
  { value: 'annual_report', label: 'Annual Report' },
  { value: 'other', label: 'Other' },
];

const STATUS_CONFIG = {
  pending: { label: 'Pending Review', color: '#8b919e', icon: Clock },
  verified: { label: 'Verified', color: '#22c55e', icon: CheckCircle },
  rejected: { label: 'Rejected', color: '#ef4444', icon: XCircle },
  expired: { label: 'Expired', color: '#f59e0b', icon: AlertTriangle },
};

export default function CompanyDocuments({ companyId }) {
  const [showUploadModal, setShowUploadModal] = useState(false);
  const [verifyingDoc, setVerifyingDoc] = useState(null);

  const { data: documents = [], isLoading } = useCompanyDocuments(companyId);
  const uploadMutation = useRequestDocumentUpload();
  const verifyMutation = useVerifyCompanyDocument();
  const downloadMutation = useDownloadCompanyDocument();

  const handleUpload = async (file, metadata) => {
    try {
      const result = await uploadMutation.mutateAsync({
        companyId,
        data: {
          file_name: file.name,
          file_type: file.type,
          file_size: file.size,
          ...metadata,
        },
      });

      // Upload to presigned URL
      await fetch(result.upload_url, {
        method: 'PUT',
        body: file,
        headers: {
          'Content-Type': file.type,
        },
      });

      setShowUploadModal(false);
    } catch (err) {
      console.error('Failed to upload document:', err);
    }
  };

  const handleVerify = async (decision, notes) => {
    try {
      await verifyMutation.mutateAsync({
        companyId,
        documentId: verifyingDoc.id,
        decision,
        notes,
      });
      setVerifyingDoc(null);
    } catch (err) {
      console.error('Failed to verify document:', err);
    }
  };

  const handleDownload = (doc) => {
    downloadMutation.mutate({
      companyId,
      documentId: doc.id,
    });
  };

  return (
    <div className="company-documents">
      <style>{`
        .company-documents {
          display: flex;
          flex-direction: column;
          gap: 16px;
        }

        .docs-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
        }

        .docs-title {
          font-size: 16px;
          font-weight: 600;
          color: var(--text-primary, #f0f2f5);
          margin: 0;
          display: flex;
          align-items: center;
          gap: 8px;
        }

        .docs-title svg {
          width: 20px;
          height: 20px;
          color: var(--accent-primary, #6366f1);
        }

        .upload-btn {
          display: flex;
          align-items: center;
          gap: 8px;
          padding: 8px 14px;
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

        .upload-btn:hover {
          background: var(--accent-hover, #5558e3);
        }

        .upload-btn svg {
          width: 14px;
          height: 14px;
        }

        .docs-grid {
          display: grid;
          grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
          gap: 16px;
        }

        .doc-card {
          background: var(--bg-tertiary, #1a1d24);
          border: 1px solid var(--border-primary, #23262f);
          border-radius: 8px;
          padding: 16px;
          display: flex;
          flex-direction: column;
          gap: 12px;
        }

        .doc-card-header {
          display: flex;
          align-items: flex-start;
          gap: 12px;
        }

        .doc-icon {
          width: 40px;
          height: 40px;
          background: var(--bg-secondary, #111318);
          border-radius: 8px;
          display: flex;
          align-items: center;
          justify-content: center;
          color: var(--accent-primary, #6366f1);
          flex-shrink: 0;
        }

        .doc-icon svg {
          width: 20px;
          height: 20px;
        }

        .doc-info {
          flex: 1;
          min-width: 0;
        }

        .doc-name {
          font-size: 14px;
          font-weight: 500;
          color: var(--text-primary, #f0f2f5);
          margin: 0;
          white-space: nowrap;
          overflow: hidden;
          text-overflow: ellipsis;
        }

        .doc-type {
          font-size: 12px;
          color: var(--text-secondary, #8b919e);
          margin: 4px 0 0;
        }

        .doc-meta {
          display: flex;
          flex-direction: column;
          gap: 6px;
        }

        .doc-meta-row {
          display: flex;
          align-items: center;
          gap: 8px;
          font-size: 12px;
          color: var(--text-secondary, #8b919e);
        }

        .doc-meta-row svg {
          width: 12px;
          height: 12px;
        }

        .status-badge {
          display: inline-flex;
          align-items: center;
          gap: 4px;
          padding: 4px 8px;
          border-radius: 4px;
          font-size: 11px;
          font-weight: 500;
          width: fit-content;
        }

        .status-badge svg {
          width: 10px;
          height: 10px;
        }

        .doc-actions {
          display: flex;
          gap: 8px;
          margin-top: auto;
          padding-top: 12px;
          border-top: 1px solid var(--border-primary, #23262f);
        }

        .doc-action-btn {
          flex: 1;
          display: flex;
          align-items: center;
          justify-content: center;
          gap: 6px;
          padding: 8px 12px;
          background: var(--bg-secondary, #111318);
          border: 1px solid var(--border-primary, #23262f);
          border-radius: 6px;
          color: var(--text-secondary, #8b919e);
          font-size: 12px;
          cursor: pointer;
          transition: all 0.15s;
          font-family: inherit;
        }

        .doc-action-btn:hover {
          background: var(--bg-primary, #0a0b0e);
          color: var(--text-primary, #f0f2f5);
        }

        .doc-action-btn svg {
          width: 12px;
          height: 12px;
        }

        .empty-state {
          padding: 40px;
          text-align: center;
          color: var(--text-secondary, #8b919e);
        }

        .empty-state svg {
          width: 40px;
          height: 40px;
          margin-bottom: 12px;
        }

        .empty-state h4 {
          margin: 0 0 8px;
          font-size: 14px;
          color: var(--text-primary, #f0f2f5);
        }

        .empty-state p {
          margin: 0;
          font-size: 13px;
        }
      `}</style>

      <div className="docs-header">
        <h3 className="docs-title">
          <FileText />
          Documents ({documents.length})
        </h3>
        <button className="upload-btn" onClick={() => setShowUploadModal(true)}>
          <Upload />
          Upload Document
        </button>
      </div>

      {isLoading ? (
        <div className="empty-state">Loading documents...</div>
      ) : documents.length === 0 ? (
        <div className="empty-state">
          <FileText />
          <h4>No documents</h4>
          <p>Upload corporate documents for verification.</p>
        </div>
      ) : (
        <div className="docs-grid">
          {documents.map((doc) => {
            const docStatus = doc.is_expired
              ? STATUS_CONFIG.expired
              : STATUS_CONFIG[doc.status] || STATUS_CONFIG.pending;
            const StatusIcon = docStatus.icon;

            return (
              <div key={doc.id} className="doc-card">
                <div className="doc-card-header">
                  <div className="doc-icon">
                    <FileText />
                  </div>
                  <div className="doc-info">
                    <h4 className="doc-name">{doc.file_name}</h4>
                    <p className="doc-type">
                      {DOCUMENT_TYPES.find((t) => t.value === doc.document_type)
                        ?.label || doc.document_type}
                    </p>
                  </div>
                </div>

                <div className="doc-meta">
                  <span
                    className="status-badge"
                    style={{
                      color: docStatus.color,
                      background: `${docStatus.color}15`,
                    }}
                  >
                    <StatusIcon />
                    {docStatus.label}
                  </span>

                  {doc.expiry_date && (
                    <div className="doc-meta-row">
                      <Calendar />
                      Expires: {new Date(doc.expiry_date).toLocaleDateString()}
                    </div>
                  )}

                  {doc.issuing_authority && (
                    <div className="doc-meta-row">
                      Issued by: {doc.issuing_authority}
                    </div>
                  )}
                </div>

                <div className="doc-actions">
                  <button
                    className="doc-action-btn"
                    onClick={() => handleDownload(doc)}
                    disabled={downloadMutation.isPending}
                  >
                    <Download />
                    Download
                  </button>
                  {doc.status === 'pending' && (
                    <button
                      className="doc-action-btn"
                      onClick={() => setVerifyingDoc(doc)}
                    >
                      <Eye />
                      Review
                    </button>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}

      {showUploadModal && (
        <UploadModal
          onUpload={handleUpload}
          onClose={() => setShowUploadModal(false)}
          isUploading={uploadMutation.isPending}
        />
      )}

      {verifyingDoc && (
        <VerifyModal
          document={verifyingDoc}
          onVerify={handleVerify}
          onClose={() => setVerifyingDoc(null)}
          isVerifying={verifyMutation.isPending}
        />
      )}
    </div>
  );
}

function UploadModal({ onUpload, onClose, isUploading }) {
  const fileInputRef = useRef(null);
  const [file, setFile] = useState(null);
  const [metadata, setMetadata] = useState({
    document_type: '',
    issue_date: '',
    expiry_date: '',
    issuing_authority: '',
    document_number: '',
  });

  const handleFileSelect = (e) => {
    const selectedFile = e.target.files[0];
    if (selectedFile) {
      setFile(selectedFile);
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (file && metadata.document_type) {
      onUpload(file, metadata);
    }
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <style>{`
        .modal-overlay {
          position: fixed;
          top: 0;
          left: 0;
          right: 0;
          bottom: 0;
          background: rgba(0, 0, 0, 0.7);
          display: flex;
          align-items: center;
          justify-content: center;
          z-index: 1000;
          padding: 20px;
        }

        .upload-modal {
          background: var(--bg-primary, #0a0b0e);
          border: 1px solid var(--border-primary, #23262f);
          border-radius: 12px;
          width: 100%;
          max-width: 500px;
        }

        .modal-header {
          display: flex;
          align-items: center;
          justify-content: space-between;
          padding: 16px 20px;
          border-bottom: 1px solid var(--border-primary, #23262f);
        }

        .modal-title {
          font-size: 16px;
          font-weight: 600;
          color: var(--text-primary, #f0f2f5);
          margin: 0;
        }

        .modal-body {
          padding: 20px;
          display: flex;
          flex-direction: column;
          gap: 16px;
        }

        .file-drop-zone {
          border: 2px dashed var(--border-primary, #23262f);
          border-radius: 8px;
          padding: 24px;
          text-align: center;
          cursor: pointer;
          transition: all 0.15s;
        }

        .file-drop-zone:hover {
          border-color: var(--accent-primary, #6366f1);
          background: rgba(99, 102, 241, 0.05);
        }

        .file-drop-zone svg {
          width: 32px;
          height: 32px;
          color: var(--text-secondary, #8b919e);
          margin-bottom: 8px;
        }

        .file-drop-zone p {
          margin: 0;
          font-size: 13px;
          color: var(--text-secondary, #8b919e);
        }

        .file-selected {
          font-size: 14px;
          color: var(--text-primary, #f0f2f5);
          font-weight: 500;
        }

        .form-group {
          display: flex;
          flex-direction: column;
          gap: 6px;
        }

        .form-label {
          font-size: 12px;
          font-weight: 500;
          color: var(--text-secondary, #8b919e);
        }

        .form-input,
        .form-select {
          padding: 10px 12px;
          background: var(--bg-secondary, #111318);
          border: 1px solid var(--border-primary, #23262f);
          border-radius: 6px;
          color: var(--text-primary, #f0f2f5);
          font-size: 14px;
          font-family: inherit;
        }

        .form-input:focus,
        .form-select:focus {
          outline: none;
          border-color: var(--accent-primary, #6366f1);
        }

        .form-row {
          display: grid;
          grid-template-columns: 1fr 1fr;
          gap: 12px;
        }

        .modal-footer {
          display: flex;
          justify-content: flex-end;
          gap: 12px;
          padding: 16px 20px;
          border-top: 1px solid var(--border-primary, #23262f);
        }

        .btn {
          padding: 10px 16px;
          border-radius: 6px;
          font-size: 14px;
          font-weight: 500;
          cursor: pointer;
          font-family: inherit;
          border: none;
        }

        .btn-secondary {
          background: var(--bg-secondary, #111318);
          color: var(--text-primary, #f0f2f5);
          border: 1px solid var(--border-primary, #23262f);
        }

        .btn-primary {
          background: var(--accent-primary, #6366f1);
          color: white;
        }

        .btn-primary:disabled {
          opacity: 0.6;
          cursor: not-allowed;
        }
      `}</style>

      <div className="upload-modal" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h3 className="modal-title">Upload Document</h3>
        </div>

        <form onSubmit={handleSubmit}>
          <div className="modal-body">
            <input
              type="file"
              ref={fileInputRef}
              onChange={handleFileSelect}
              style={{ display: 'none' }}
              accept=".pdf,.jpg,.jpeg,.png,.doc,.docx"
            />

            <div
              className="file-drop-zone"
              onClick={() => fileInputRef.current?.click()}
            >
              <Upload />
              {file ? (
                <p className="file-selected">{file.name}</p>
              ) : (
                <p>Click to select a file</p>
              )}
            </div>

            <div className="form-group">
              <label className="form-label">Document Type *</label>
              <select
                className="form-select"
                value={metadata.document_type}
                onChange={(e) =>
                  setMetadata({ ...metadata, document_type: e.target.value })
                }
                required
              >
                <option value="">Select type</option>
                {DOCUMENT_TYPES.map((type) => (
                  <option key={type.value} value={type.value}>
                    {type.label}
                  </option>
                ))}
              </select>
            </div>

            <div className="form-row">
              <div className="form-group">
                <label className="form-label">Issue Date</label>
                <input
                  type="date"
                  className="form-input"
                  value={metadata.issue_date}
                  onChange={(e) =>
                    setMetadata({ ...metadata, issue_date: e.target.value })
                  }
                />
              </div>
              <div className="form-group">
                <label className="form-label">Expiry Date</label>
                <input
                  type="date"
                  className="form-input"
                  value={metadata.expiry_date}
                  onChange={(e) =>
                    setMetadata({ ...metadata, expiry_date: e.target.value })
                  }
                />
              </div>
            </div>

            <div className="form-group">
              <label className="form-label">Issuing Authority</label>
              <input
                type="text"
                className="form-input"
                value={metadata.issuing_authority}
                onChange={(e) =>
                  setMetadata({ ...metadata, issuing_authority: e.target.value })
                }
                placeholder="e.g., Delaware Secretary of State"
              />
            </div>
          </div>

          <div className="modal-footer">
            <button type="button" className="btn btn-secondary" onClick={onClose}>
              Cancel
            </button>
            <button
              type="submit"
              className="btn btn-primary"
              disabled={!file || !metadata.document_type || isUploading}
            >
              {isUploading ? 'Uploading...' : 'Upload'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

function VerifyModal({ document, onVerify, onClose, isVerifying }) {
  const [notes, setNotes] = useState('');

  return (
    <div className="modal-overlay" onClick={onClose}>
      <style>{`
        .verify-modal {
          background: var(--bg-primary, #0a0b0e);
          border: 1px solid var(--border-primary, #23262f);
          border-radius: 12px;
          width: 100%;
          max-width: 450px;
        }

        .modal-header {
          padding: 16px 20px;
          border-bottom: 1px solid var(--border-primary, #23262f);
        }

        .modal-title {
          font-size: 16px;
          font-weight: 600;
          color: var(--text-primary, #f0f2f5);
          margin: 0 0 4px;
        }

        .modal-subtitle {
          font-size: 13px;
          color: var(--text-secondary, #8b919e);
          margin: 0;
        }

        .modal-body {
          padding: 20px;
        }

        .form-group {
          display: flex;
          flex-direction: column;
          gap: 6px;
        }

        .form-label {
          font-size: 12px;
          font-weight: 500;
          color: var(--text-secondary, #8b919e);
        }

        .form-textarea {
          padding: 10px 12px;
          background: var(--bg-secondary, #111318);
          border: 1px solid var(--border-primary, #23262f);
          border-radius: 6px;
          color: var(--text-primary, #f0f2f5);
          font-size: 14px;
          font-family: inherit;
          min-height: 80px;
          resize: vertical;
        }

        .form-textarea:focus {
          outline: none;
          border-color: var(--accent-primary, #6366f1);
        }

        .modal-footer {
          display: flex;
          gap: 12px;
          padding: 16px 20px;
          border-top: 1px solid var(--border-primary, #23262f);
        }

        .btn {
          flex: 1;
          padding: 10px 16px;
          border-radius: 6px;
          font-size: 14px;
          font-weight: 500;
          cursor: pointer;
          font-family: inherit;
          border: none;
          display: flex;
          align-items: center;
          justify-content: center;
          gap: 6px;
        }

        .btn-reject {
          background: rgba(239, 68, 68, 0.1);
          color: #ef4444;
        }

        .btn-reject:hover {
          background: rgba(239, 68, 68, 0.2);
        }

        .btn-approve {
          background: #22c55e;
          color: white;
        }

        .btn-approve:hover {
          background: #16a34a;
        }

        .btn:disabled {
          opacity: 0.6;
          cursor: not-allowed;
        }

        .btn svg {
          width: 14px;
          height: 14px;
        }
      `}</style>

      <div className="verify-modal" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h3 className="modal-title">Review Document</h3>
          <p className="modal-subtitle">{document.file_name}</p>
        </div>

        <div className="modal-body">
          <div className="form-group">
            <label className="form-label">Notes (optional)</label>
            <textarea
              className="form-textarea"
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              placeholder="Add verification notes..."
            />
          </div>
        </div>

        <div className="modal-footer">
          <button
            className="btn btn-reject"
            onClick={() => onVerify('rejected', notes)}
            disabled={isVerifying}
          >
            <XCircle />
            Reject
          </button>
          <button
            className="btn btn-approve"
            onClick={() => onVerify('verified', notes)}
            disabled={isVerifying}
          >
            <CheckCircle />
            Verify
          </button>
        </div>
      </div>
    </div>
  );
}
