/**
 * DocumentUpload Component
 *
 * Production-grade drag & drop document upload with:
 * - File type validation (JPEG, PNG, PDF) with magic byte verification
 * - File size validation (max 50MB)
 * - Image thumbnail preview before upload
 * - Multi-file support for front/back documents
 * - Progress tracking (0-100%) with retry indicator
 * - Document type selection with side indicators
 * - Presigned URL upload flow
 * - Auto-trigger AI analysis
 * - Mobile camera capture support
 */

import React, { useState, useRef, useCallback, useEffect } from 'react';
import {
  Upload,
  X,
  FileText,
  Image,
  AlertCircle,
  CheckCircle2,
  Loader2,
  Camera,
  RotateCcw,
  Plus,
  Trash2
} from 'lucide-react';
import { useUploadDocument } from '../hooks/useDocuments';
import { useToast } from '../contexts/ToastContext';

// Constants
const MAX_FILE_SIZE = 50 * 1024 * 1024; // 50MB
const ACCEPTED_TYPES = {
  'image/jpeg': ['.jpg', '.jpeg'],
  'image/png': ['.png'],
  'application/pdf': ['.pdf'],
};

// Magic bytes for file type verification (security)
const MAGIC_BYTES = {
  'image/jpeg': [[0xFF, 0xD8, 0xFF]],
  'image/png': [[0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A]],
  'application/pdf': [[0x25, 0x50, 0x44, 0x46]], // %PDF
};

// Document types with metadata
const DOCUMENT_TYPES = [
  { value: 'passport', label: 'Passport', requiresBack: false },
  { value: 'driver_license', label: "Driver's License", requiresBack: true },
  { value: 'id_card', label: 'ID Card', requiresBack: true },
  { value: 'utility_bill', label: 'Utility Bill', requiresBack: false },
  { value: 'bank_statement', label: 'Bank Statement', requiresBack: false },
  { value: 'proof_of_address', label: 'Proof of Address', requiresBack: false },
];

const STAGE_LABELS = {
  preparing: 'Preparing upload...',
  uploading: 'Uploading file...',
  confirming: 'Confirming upload...',
  analyzing: 'Running AI analysis...',
};

/**
 * Verify file magic bytes match declared MIME type
 * Prevents spoofed file extensions
 */
async function verifyMagicBytes(file) {
  return new Promise((resolve) => {
    const reader = new FileReader();
    reader.onload = (e) => {
      const arr = new Uint8Array(e.target.result);
      const signatures = MAGIC_BYTES[file.type];

      if (!signatures) {
        resolve(false);
        return;
      }

      const matches = signatures.some((sig) =>
        sig.every((byte, i) => arr[i] === byte)
      );
      resolve(matches);
    };
    reader.onerror = () => resolve(false);
    // Only read first 16 bytes for signature check
    reader.readAsArrayBuffer(file.slice(0, 16));
  });
}

/**
 * Validate a file for upload (sync checks only)
 * @param {File} file - File to validate
 * @returns {{ valid: boolean, error?: string }}
 */
function validateFileSync(file) {
  // Check file type
  if (!Object.keys(ACCEPTED_TYPES).includes(file.type)) {
    return {
      valid: false,
      error: 'Invalid file type. Please upload JPEG, PNG, or PDF files only.',
    };
  }

  // Check file size
  if (file.size > MAX_FILE_SIZE) {
    const sizeMB = (file.size / (1024 * 1024)).toFixed(1);
    return {
      valid: false,
      error: `File too large (${sizeMB}MB). Maximum size is 50MB.`,
    };
  }

  return { valid: true };
}

/**
 * Full validation including magic byte verification
 */
async function validateFile(file) {
  const syncResult = validateFileSync(file);
  if (!syncResult.valid) return syncResult;

  // Verify magic bytes for security
  const validMagic = await verifyMagicBytes(file);
  if (!validMagic) {
    return {
      valid: false,
      error: 'File contents do not match declared type. Please upload an authentic document.',
    };
  }

  return { valid: true };
}

/**
 * Create image preview URL
 */
function createPreviewUrl(file) {
  if (file.type.startsWith('image/')) {
    return URL.createObjectURL(file);
  }
  return null;
}

/**
 * Format file size for display
 */
function formatFileSize(bytes) {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

/**
 * Get icon for file type
 */
function FileIcon({ type }) {
  if (type.startsWith('image/')) {
    return <Image size={24} />;
  }
  return <FileText size={24} />;
}

export default function DocumentUpload({
  applicantId,
  onUploadComplete,
  onUploadError,
  defaultDocumentType = 'passport',
  analyze = true,
  compact = false,
}) {
  const toast = useToast();
  const fileInputRef = useRef(null);
  const backFileInputRef = useRef(null);

  // Local state
  const [documentType, setDocumentType] = useState(defaultDocumentType);
  const [frontFile, setFrontFile] = useState(null);
  const [backFile, setBackFile] = useState(null);
  const [frontPreview, setFrontPreview] = useState(null);
  const [backPreview, setBackPreview] = useState(null);
  const [validationError, setValidationError] = useState(null);
  const [isDragOver, setIsDragOver] = useState(false);
  const [activeSide, setActiveSide] = useState('front'); // 'front' or 'back'
  const [isValidating, setIsValidating] = useState(false);
  const [uploadingFile, setUploadingFile] = useState(null); // 'front' or 'back'

  // Get document type config
  const docTypeConfig = DOCUMENT_TYPES.find((t) => t.value === documentType) || DOCUMENT_TYPES[0];
  const requiresBack = docTypeConfig.requiresBack;

  // Upload hook with progress tracking
  const uploadMutation = useUploadDocument();
  const { progress, stage, abort, isPending } = uploadMutation;

  // Cleanup preview URLs on unmount
  useEffect(() => {
    return () => {
      if (frontPreview) URL.revokeObjectURL(frontPreview);
      if (backPreview) URL.revokeObjectURL(backPreview);
    };
  }, [frontPreview, backPreview]);

  // Handle file selection with async validation
  const handleFileSelect = useCallback(async (file, side = 'front') => {
    setValidationError(null);
    setIsValidating(true);

    try {
      const validation = await validateFile(file);
      if (!validation.valid) {
        setValidationError(validation.error);
        setIsValidating(false);
        return;
      }

      const previewUrl = createPreviewUrl(file);

      if (side === 'front') {
        if (frontPreview) URL.revokeObjectURL(frontPreview);
        setFrontFile(file);
        setFrontPreview(previewUrl);
      } else {
        if (backPreview) URL.revokeObjectURL(backPreview);
        setBackFile(file);
        setBackPreview(previewUrl);
      }
    } finally {
      setIsValidating(false);
    }
  }, [frontPreview, backPreview]);

  // Legacy single-file getter for compatibility
  const selectedFile = frontFile;

  // Handle file input change
  const handleInputChange = useCallback((e, side = 'front') => {
    const file = e.target.files?.[0];
    if (file) {
      handleFileSelect(file, side);
    }
    // Reset input so the same file can be selected again
    e.target.value = '';
  }, [handleFileSelect]);

  // Handle drag events
  const handleDragOver = useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragOver(true);
  }, []);

  const handleDragLeave = useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragOver(false);
  }, []);

  const handleDrop = useCallback((e, side = 'front') => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragOver(false);

    const file = e.dataTransfer.files?.[0];
    if (file) {
      handleFileSelect(file, side);
    }
  }, [handleFileSelect]);

  // Clear selected file
  const handleClearFile = useCallback((side = 'front') => {
    if (side === 'front') {
      if (frontPreview) URL.revokeObjectURL(frontPreview);
      setFrontFile(null);
      setFrontPreview(null);
    } else {
      if (backPreview) URL.revokeObjectURL(backPreview);
      setBackFile(null);
      setBackPreview(null);
    }
    setValidationError(null);
  }, [frontPreview, backPreview]);

  // Clear all files
  const handleClearAll = useCallback(() => {
    if (frontPreview) URL.revokeObjectURL(frontPreview);
    if (backPreview) URL.revokeObjectURL(backPreview);
    setFrontFile(null);
    setBackFile(null);
    setFrontPreview(null);
    setBackPreview(null);
    setValidationError(null);
  }, [frontPreview, backPreview]);

  // Handle upload - supports both single and multi-file
  const handleUpload = useCallback(async () => {
    if (!frontFile || !applicantId) return;

    // Check if back is required but missing
    if (requiresBack && !backFile) {
      setValidationError('Please upload both front and back of the document.');
      return;
    }

    const uploadedDocs = [];

    try {
      // Upload front
      setUploadingFile('front');
      const frontDoc = await uploadMutation.mutateAsync({
        file: frontFile,
        applicantId,
        documentType: requiresBack ? `${documentType}_front` : documentType,
        analyze,
      });
      uploadedDocs.push(frontDoc);

      // Upload back if required
      if (requiresBack && backFile) {
        setUploadingFile('back');
        const backDoc = await uploadMutation.mutateAsync({
          file: backFile,
          applicantId,
          documentType: `${documentType}_back`,
          analyze,
        });
        uploadedDocs.push(backDoc);
      }

      toast.success(requiresBack && backFile
        ? 'Both document sides uploaded successfully'
        : 'Document uploaded successfully'
      );

      handleClearAll();
      onUploadComplete?.(uploadedDocs.length === 1 ? uploadedDocs[0] : uploadedDocs);
    } catch (error) {
      const message = error.message || 'Upload failed';
      toast.error(message);
      onUploadError?.(error);
    } finally {
      setUploadingFile(null);
    }
  }, [frontFile, backFile, applicantId, documentType, analyze, requiresBack, uploadMutation, toast, onUploadComplete, onUploadError, handleClearAll]);

  // Handle cancel
  const handleCancel = useCallback(() => {
    abort();
    handleClearAll();
  }, [abort, handleClearAll]);

  // Click to upload
  const handleClick = useCallback((side = 'front') => {
    if (!isPending && !isValidating) {
      if (side === 'front') {
        fileInputRef.current?.click();
      } else {
        backFileInputRef.current?.click();
      }
    }
  }, [isPending, isValidating]);

  // Check if ready to upload
  const canUpload = frontFile && (!requiresBack || backFile) && !isPending && !isValidating;

  // Get current uploading status text
  const getUploadStatusText = () => {
    if (isValidating) return 'Validating file...';
    if (!isPending) return null;
    if (uploadingFile === 'front') {
      return requiresBack ? 'Uploading front side...' : STAGE_LABELS[stage] || 'Processing...';
    }
    if (uploadingFile === 'back') {
      return 'Uploading back side...';
    }
    return STAGE_LABELS[stage] || 'Processing...';
  };

  return (
    <div className="document-upload-container">
      <style>{`
        .document-upload-container {
          width: 100%;
        }

        .document-type-select {
          margin-bottom: 16px;
        }

        .document-type-select label {
          display: block;
          font-size: 13px;
          font-weight: 500;
          color: var(--text-secondary);
          margin-bottom: 6px;
        }

        .document-type-select select {
          width: 100%;
          padding: 10px 12px;
          font-size: 14px;
          border: 1px solid var(--border-color);
          border-radius: 8px;
          background: var(--bg-secondary);
          color: var(--text-primary);
          cursor: pointer;
          font-family: inherit;
        }

        .document-type-select select:focus {
          outline: none;
          border-color: var(--accent-primary);
          box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.1);
        }

        .drop-zone {
          border: 2px dashed var(--border-color);
          border-radius: 12px;
          padding: ${compact ? '24px' : '40px'};
          text-align: center;
          cursor: pointer;
          transition: all 0.2s ease;
          background: var(--bg-secondary);
        }

        .drop-zone:hover {
          border-color: var(--accent-primary);
          background: rgba(99, 102, 241, 0.05);
        }

        .drop-zone.drag-over {
          border-color: var(--accent-primary);
          background: rgba(99, 102, 241, 0.1);
          border-style: solid;
        }

        .drop-zone.uploading {
          pointer-events: none;
          border-style: solid;
          border-color: var(--accent-primary);
        }

        .drop-zone.has-file {
          border-color: var(--success);
          background: rgba(16, 185, 129, 0.05);
        }

        .drop-zone-icon {
          width: 48px;
          height: 48px;
          border-radius: 12px;
          background: var(--bg-tertiary);
          display: flex;
          align-items: center;
          justify-content: center;
          margin: 0 auto 16px;
          color: var(--text-muted);
          transition: all 0.2s ease;
        }

        .drop-zone:hover .drop-zone-icon,
        .drop-zone.drag-over .drop-zone-icon {
          background: rgba(99, 102, 241, 0.15);
          color: var(--accent-primary);
        }

        .drop-zone.has-file .drop-zone-icon {
          background: rgba(16, 185, 129, 0.15);
          color: var(--success);
        }

        .drop-zone-text {
          font-size: 14px;
          color: var(--text-secondary);
          margin-bottom: 8px;
        }

        .drop-zone-text strong {
          color: var(--accent-primary);
          cursor: pointer;
        }

        .drop-zone-hint {
          font-size: 12px;
          color: var(--text-muted);
        }

        /* Selected file display */
        .selected-file {
          display: flex;
          align-items: center;
          gap: 12px;
          padding: 12px;
          background: var(--bg-tertiary);
          border-radius: 8px;
          margin-top: 16px;
        }

        .selected-file-icon {
          width: 40px;
          height: 40px;
          border-radius: 8px;
          background: var(--bg-secondary);
          display: flex;
          align-items: center;
          justify-content: center;
          color: var(--text-muted);
        }

        .selected-file-info {
          flex: 1;
          min-width: 0;
        }

        .selected-file-name {
          font-size: 14px;
          font-weight: 500;
          color: var(--text-primary);
          white-space: nowrap;
          overflow: hidden;
          text-overflow: ellipsis;
        }

        .selected-file-size {
          font-size: 12px;
          color: var(--text-muted);
        }

        .selected-file-remove {
          padding: 6px;
          border-radius: 6px;
          background: transparent;
          border: none;
          color: var(--text-muted);
          cursor: pointer;
          transition: all 0.15s;
        }

        .selected-file-remove:hover {
          background: var(--bg-hover);
          color: var(--danger);
        }

        /* Progress display */
        .upload-progress {
          margin-top: 16px;
        }

        .upload-progress-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 8px;
        }

        .upload-progress-stage {
          font-size: 13px;
          color: var(--text-secondary);
          display: flex;
          align-items: center;
          gap: 8px;
        }

        .upload-progress-percent {
          font-size: 13px;
          font-weight: 600;
          color: var(--accent-primary);
        }

        .progress-bar {
          height: 8px;
          background: var(--bg-tertiary);
          border-radius: 4px;
          overflow: hidden;
        }

        .progress-bar-fill {
          height: 100%;
          background: linear-gradient(90deg, var(--accent-primary), #a855f7);
          border-radius: 4px;
          transition: width 0.3s ease;
        }

        /* Error message */
        .upload-error {
          display: flex;
          align-items: flex-start;
          gap: 8px;
          padding: 12px;
          background: rgba(239, 68, 68, 0.1);
          border: 1px solid rgba(239, 68, 68, 0.3);
          border-radius: 8px;
          margin-top: 16px;
        }

        .upload-error-icon {
          color: var(--danger);
          flex-shrink: 0;
          margin-top: 1px;
        }

        .upload-error-text {
          font-size: 13px;
          color: var(--danger);
        }

        /* Action buttons */
        .upload-actions {
          display: flex;
          gap: 12px;
          margin-top: 16px;
        }

        .btn-upload {
          flex: 1;
          display: flex;
          align-items: center;
          justify-content: center;
          gap: 8px;
          padding: 12px 20px;
          font-size: 14px;
          font-weight: 500;
          border-radius: 8px;
          cursor: pointer;
          transition: all 0.15s;
          border: none;
          font-family: inherit;
        }

        .btn-upload-primary {
          background: var(--accent-primary);
          color: white;
        }

        .btn-upload-primary:hover:not(:disabled) {
          opacity: 0.9;
        }

        .btn-upload-primary:disabled {
          opacity: 0.6;
          cursor: not-allowed;
        }

        .btn-upload-secondary {
          background: var(--bg-secondary);
          color: var(--text-primary);
          border: 1px solid var(--border-color);
        }

        .btn-upload-secondary:hover {
          background: var(--bg-hover);
        }

        /* Multi-side upload layout */
        .upload-sides {
          display: flex;
          gap: 16px;
        }

        .upload-sides.single-side {
          display: block;
        }

        .upload-sides.two-sides .upload-side {
          flex: 1;
        }

        .upload-side {
          display: flex;
          flex-direction: column;
          gap: 8px;
        }

        .upload-side-label {
          font-size: 12px;
          font-weight: 600;
          text-transform: uppercase;
          letter-spacing: 0.05em;
          color: var(--text-muted);
          display: flex;
          align-items: center;
          gap: 6px;
        }

        .side-check {
          color: var(--success);
        }

        /* Mini drop zone for multi-file */
        .drop-zone.mini {
          padding: 32px 16px;
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          gap: 8px;
          min-height: 120px;
          font-size: 13px;
          color: var(--text-muted);
        }

        /* Preview container */
        .preview-container {
          position: relative;
          border-radius: 12px;
          overflow: hidden;
          background: var(--bg-tertiary);
          border: 2px solid var(--border-color);
        }

        .file-preview {
          width: 100%;
          height: 160px;
          object-fit: cover;
          display: block;
        }

        .preview-overlay {
          position: absolute;
          top: 0;
          left: 0;
          right: 0;
          bottom: 0;
          background: rgba(0, 0, 0, 0.5);
          display: flex;
          align-items: center;
          justify-content: center;
          gap: 12px;
          opacity: 0;
          transition: opacity 0.2s ease;
        }

        .preview-container:hover .preview-overlay {
          opacity: 1;
        }

        .preview-action {
          width: 40px;
          height: 40px;
          border-radius: 8px;
          background: rgba(255, 255, 255, 0.9);
          border: none;
          display: flex;
          align-items: center;
          justify-content: center;
          cursor: pointer;
          color: var(--text-primary);
          transition: all 0.15s;
        }

        .preview-action:hover {
          background: white;
          transform: scale(1.05);
        }

        .preview-action:disabled {
          opacity: 0.5;
          cursor: not-allowed;
        }

        .preview-info {
          position: absolute;
          bottom: 0;
          left: 0;
          right: 0;
          padding: 8px 12px;
          background: linear-gradient(transparent, rgba(0, 0, 0, 0.7));
          color: white;
          font-size: 11px;
          display: flex;
          justify-content: space-between;
        }

        .preview-info span {
          white-space: nowrap;
          overflow: hidden;
          text-overflow: ellipsis;
        }

        /* File card for PDFs */
        .file-card {
          display: flex;
          align-items: center;
          gap: 12px;
          padding: 16px;
          background: var(--bg-tertiary);
          border: 2px solid var(--border-color);
          border-radius: 12px;
          min-height: 80px;
        }

        .file-card-info {
          flex: 1;
          min-width: 0;
        }

        .file-card-name {
          font-size: 13px;
          font-weight: 500;
          white-space: nowrap;
          overflow: hidden;
          text-overflow: ellipsis;
        }

        .file-card-size {
          font-size: 12px;
          color: var(--text-muted);
        }

        .file-card-remove {
          padding: 8px;
          border-radius: 6px;
          background: transparent;
          border: none;
          color: var(--text-muted);
          cursor: pointer;
        }

        .file-card-remove:hover {
          background: rgba(239, 68, 68, 0.1);
          color: var(--danger);
        }

        @keyframes spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }

        .spinner {
          animation: spin 1s linear infinite;
        }

        @media (max-width: 600px) {
          .upload-sides.two-sides {
            flex-direction: column;
          }
        }
      `}</style>

      {/* Hidden file inputs */}
      <input
        ref={fileInputRef}
        type="file"
        accept={Object.keys(ACCEPTED_TYPES).join(',')}
        onChange={(e) => handleInputChange(e, 'front')}
        style={{ display: 'none' }}
        capture="environment"
      />
      <input
        ref={backFileInputRef}
        type="file"
        accept={Object.keys(ACCEPTED_TYPES).join(',')}
        onChange={(e) => handleInputChange(e, 'back')}
        style={{ display: 'none' }}
        capture="environment"
      />

      {/* Document type selector */}
      <div className="document-type-select">
        <label htmlFor="documentType">Document Type</label>
        <select
          id="documentType"
          value={documentType}
          onChange={(e) => {
            setDocumentType(e.target.value);
            handleClearAll(); // Clear files when type changes
          }}
          disabled={isPending}
        >
          {DOCUMENT_TYPES.map((type) => (
            <option key={type.value} value={type.value}>
              {type.label} {type.requiresBack ? '(Front & Back)' : ''}
            </option>
          ))}
        </select>
      </div>

      {/* Multi-file upload area */}
      <div className={`upload-sides ${requiresBack ? 'two-sides' : 'single-side'}`}>
        {/* Front side drop zone */}
        <div className="upload-side">
          <div className="upload-side-label">
            {requiresBack ? 'Front Side' : 'Document'}
            {frontFile && <CheckCircle2 size={14} className="side-check" />}
          </div>

          {frontPreview ? (
            <div className="preview-container">
              <img src={frontPreview} alt="Front preview" className="file-preview" />
              <div className="preview-overlay">
                <button
                  className="preview-action"
                  onClick={() => handleClearFile('front')}
                  disabled={isPending}
                  title="Remove"
                >
                  <Trash2 size={16} />
                </button>
                <button
                  className="preview-action"
                  onClick={() => handleClick('front')}
                  disabled={isPending}
                  title="Replace"
                >
                  <RotateCcw size={16} />
                </button>
              </div>
              <div className="preview-info">
                <span>{frontFile.name}</span>
                <span>{formatFileSize(frontFile.size)}</span>
              </div>
            </div>
          ) : frontFile ? (
            <div className="file-card">
              <FileIcon type={frontFile.type} />
              <div className="file-card-info">
                <div className="file-card-name">{frontFile.name}</div>
                <div className="file-card-size">{formatFileSize(frontFile.size)}</div>
              </div>
              <button
                className="file-card-remove"
                onClick={() => handleClearFile('front')}
                disabled={isPending}
              >
                <X size={16} />
              </button>
            </div>
          ) : (
            <div
              className={`drop-zone mini ${isDragOver && activeSide === 'front' ? 'drag-over' : ''} ${isPending ? 'uploading' : ''}`}
              onClick={() => handleClick('front')}
              onDragOver={(e) => { handleDragOver(e); setActiveSide('front'); }}
              onDragLeave={handleDragLeave}
              onDrop={(e) => handleDrop(e, 'front')}
              role="button"
              tabIndex={0}
              onKeyDown={(e) => e.key === 'Enter' && handleClick('front')}
            >
              {isValidating ? (
                <Loader2 size={20} className="spinner" />
              ) : (
                <Plus size={20} />
              )}
              <span>{isValidating ? 'Validating...' : 'Add file'}</span>
            </div>
          )}
        </div>

        {/* Back side drop zone (only for documents that require it) */}
        {requiresBack && (
          <div className="upload-side">
            <div className="upload-side-label">
              Back Side
              {backFile && <CheckCircle2 size={14} className="side-check" />}
            </div>

            {backPreview ? (
              <div className="preview-container">
                <img src={backPreview} alt="Back preview" className="file-preview" />
                <div className="preview-overlay">
                  <button
                    className="preview-action"
                    onClick={() => handleClearFile('back')}
                    disabled={isPending}
                    title="Remove"
                  >
                    <Trash2 size={16} />
                  </button>
                  <button
                    className="preview-action"
                    onClick={() => handleClick('back')}
                    disabled={isPending}
                    title="Replace"
                  >
                    <RotateCcw size={16} />
                  </button>
                </div>
                <div className="preview-info">
                  <span>{backFile.name}</span>
                  <span>{formatFileSize(backFile.size)}</span>
                </div>
              </div>
            ) : backFile ? (
              <div className="file-card">
                <FileIcon type={backFile.type} />
                <div className="file-card-info">
                  <div className="file-card-name">{backFile.name}</div>
                  <div className="file-card-size">{formatFileSize(backFile.size)}</div>
                </div>
                <button
                  className="file-card-remove"
                  onClick={() => handleClearFile('back')}
                  disabled={isPending}
                >
                  <X size={16} />
                </button>
              </div>
            ) : (
              <div
                className={`drop-zone mini ${isDragOver && activeSide === 'back' ? 'drag-over' : ''} ${isPending ? 'uploading' : ''}`}
                onClick={() => handleClick('back')}
                onDragOver={(e) => { handleDragOver(e); setActiveSide('back'); }}
                onDragLeave={handleDragLeave}
                onDrop={(e) => handleDrop(e, 'back')}
                role="button"
                tabIndex={0}
                onKeyDown={(e) => e.key === 'Enter' && handleClick('back')}
              >
                <Plus size={20} />
                <span>Add file</span>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Upload progress */}
      {(isPending || isValidating) && (
        <div className="upload-progress">
          <div className="upload-progress-header">
            <span className="upload-progress-stage">
              <Loader2 size={14} className="spinner" />
              {getUploadStatusText()}
            </span>
            {isPending && <span className="upload-progress-percent">{progress}%</span>}
          </div>
          {isPending && (
            <div className="progress-bar">
              <div
                className="progress-bar-fill"
                style={{ width: `${progress}%` }}
              />
            </div>
          )}
        </div>
      )}

      {/* Validation error */}
      {validationError && (
        <div className="upload-error">
          <AlertCircle size={16} className="upload-error-icon" />
          <span className="upload-error-text">{validationError}</span>
        </div>
      )}

      {/* Action buttons */}
      {(frontFile || isPending) && (
        <div className="upload-actions">
          {isPending ? (
            <button
              className="btn-upload btn-upload-secondary"
              onClick={handleCancel}
            >
              Cancel
            </button>
          ) : (
            <>
              <button
                className="btn-upload btn-upload-secondary"
                onClick={handleClearAll}
              >
                Clear
              </button>
              <button
                className="btn-upload btn-upload-primary"
                onClick={handleUpload}
                disabled={!canUpload}
              >
                <Upload size={16} />
                {requiresBack ? 'Upload Both Sides' : 'Upload Document'}
              </button>
            </>
          )}
        </div>
      )}
    </div>
  );
}
