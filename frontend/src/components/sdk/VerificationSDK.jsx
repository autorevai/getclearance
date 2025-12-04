/**
 * GetClearance Verification SDK
 * ==============================
 * Embeddable verification flow for customer websites.
 *
 * Usage:
 *   <VerificationSDK
 *     accessToken="sdk_xxx"
 *     onComplete={(result) => console.log('Verified!', result)}
 *     onError={(error) => console.error('Error:', error)}
 *   />
 *
 * Or use the standalone page at /sdk/verify?token=sdk_xxx
 */

import React, { useState, useEffect, useCallback, useRef } from 'react';
import {
  Shield,
  Camera,
  FileText,
  CheckCircle,
  AlertCircle,
  Loader2,
  ChevronRight,
  ChevronLeft,
  Upload,
  RefreshCw,
  X,
} from 'lucide-react';

// SDK API client
const createSDKClient = (accessToken, baseUrl = '/api/v1/sdk') => {
  const headers = {
    'Authorization': `Bearer ${accessToken}`,
    'Content-Type': 'application/json',
  };

  return {
    getConfig: async () => {
      const res = await fetch(`${baseUrl}/config`, { headers });
      if (!res.ok) throw new Error('Failed to load verification config');
      return res.json();
    },

    getStatus: async () => {
      const res = await fetch(`${baseUrl}/status`, { headers });
      if (!res.ok) throw new Error('Failed to get status');
      return res.json();
    },

    getUploadUrl: async (documentType, side, fileName, contentType) => {
      const res = await fetch(`${baseUrl}/documents/upload-url`, {
        method: 'POST',
        headers,
        body: JSON.stringify({
          document_type: documentType,
          side,
          file_name: fileName,
          content_type: contentType,
        }),
      });
      if (!res.ok) throw new Error('Failed to get upload URL');
      return res.json();
    },

    confirmUpload: async (documentId, fileSize) => {
      const res = await fetch(`${baseUrl}/documents/confirm`, {
        method: 'POST',
        headers,
        body: JSON.stringify({
          document_id: documentId,
          file_size: fileSize,
        }),
      });
      if (!res.ok) throw new Error('Failed to confirm upload');
      return res.json();
    },

    completeStep: async (stepName, data = null) => {
      const res = await fetch(`${baseUrl}/steps/complete`, {
        method: 'POST',
        headers,
        body: JSON.stringify({
          step_name: stepName,
          data,
        }),
      });
      if (!res.ok) throw new Error('Failed to complete step');
      return res.json();
    },

    submit: async () => {
      const res = await fetch(`${baseUrl}/submit`, {
        method: 'POST',
        headers,
      });
      if (!res.ok) throw new Error('Failed to submit verification');
      return res.json();
    },
  };
};

// Step Components
const ConsentStep = ({ onComplete, branding }) => {
  const [agreed, setAgreed] = useState(false);

  return (
    <div className="sdk-step consent-step">
      <div className="step-icon">
        <Shield size={48} />
      </div>
      <h2>Data Processing Consent</h2>
      <p className="step-description">
        We need your consent to process your personal data for identity verification.
        Your information will be securely stored and used only for verification purposes.
      </p>

      <div className="consent-details">
        <h3>What we collect:</h3>
        <ul>
          <li>Government-issued ID document image</li>
          <li>Selfie for identity verification</li>
          <li>Personal information from your ID</li>
        </ul>

        <h3>How we use it:</h3>
        <ul>
          <li>Verify your identity</li>
          <li>Check against sanctions and PEP lists</li>
          <li>Comply with regulatory requirements</li>
        </ul>
      </div>

      <label className="consent-checkbox">
        <input
          type="checkbox"
          checked={agreed}
          onChange={(e) => setAgreed(e.target.checked)}
        />
        <span>I consent to the processing of my personal data for identity verification</span>
      </label>

      <button
        className="sdk-btn primary"
        disabled={!agreed}
        onClick={() => onComplete({ consent: true })}
      >
        Continue
        <ChevronRight size={18} />
      </button>
    </div>
  );
};

const DocumentStep = ({ onComplete, allowedTypes, client }) => {
  const [documentType, setDocumentType] = useState('passport');
  const [frontFile, setFrontFile] = useState(null);
  const [backFile, setBackFile] = useState(null);
  const [frontPreview, setFrontPreview] = useState(null);
  const [backPreview, setBackPreview] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [error, setError] = useState(null);

  const frontInputRef = useRef(null);
  const backInputRef = useRef(null);

  const requiresBack = ['driver_license', 'id_card'].includes(documentType);

  const documentTypes = [
    { value: 'passport', label: 'Passport', icon: '🛂', requiresBack: false },
    { value: 'driver_license', label: "Driver's License", icon: '🚗', requiresBack: true },
    { value: 'id_card', label: 'ID Card', icon: '🪪', requiresBack: true },
  ];

  const handleFileSelect = (e, side) => {
    const file = e.target.files?.[0];
    if (!file) return;

    // Validate file type
    const allowedMimes = ['image/jpeg', 'image/png', 'application/pdf'];
    if (!allowedMimes.includes(file.type)) {
      setError('Please upload a JPEG, PNG, or PDF file');
      return;
    }

    // Validate size (50MB max)
    if (file.size > 50 * 1024 * 1024) {
      setError('File size must be less than 50MB');
      return;
    }

    setError(null);

    // Create preview
    const preview = URL.createObjectURL(file);

    if (side === 'front') {
      if (frontPreview) URL.revokeObjectURL(frontPreview);
      setFrontFile(file);
      setFrontPreview(preview);
    } else {
      if (backPreview) URL.revokeObjectURL(backPreview);
      setBackFile(file);
      setBackPreview(preview);
    }
  };

  const handleUpload = async () => {
    if (!frontFile || (requiresBack && !backFile)) {
      setError('Please upload all required document images');
      return;
    }

    setUploading(true);
    setUploadProgress(0);
    setError(null);

    try {
      // Upload front
      setUploadProgress(10);
      const frontUploadData = await client.getUploadUrl(
        documentType,
        'front',
        frontFile.name,
        frontFile.type
      );

      setUploadProgress(25);
      await fetch(frontUploadData.upload_url, {
        method: 'PUT',
        body: frontFile,
        headers: { 'Content-Type': frontFile.type },
      });

      setUploadProgress(40);
      await client.confirmUpload(frontUploadData.document_id, frontFile.size);

      // Upload back if needed
      if (requiresBack && backFile) {
        setUploadProgress(55);
        const backUploadData = await client.getUploadUrl(
          documentType,
          'back',
          backFile.name,
          backFile.type
        );

        setUploadProgress(70);
        await fetch(backUploadData.upload_url, {
          method: 'PUT',
          body: backFile,
          headers: { 'Content-Type': backFile.type },
        });

        setUploadProgress(85);
        await client.confirmUpload(backUploadData.document_id, backFile.size);
      }

      setUploadProgress(100);

      // Complete step
      await onComplete({
        document_type: documentType,
        front_uploaded: true,
        back_uploaded: requiresBack && !!backFile,
      });

    } catch (err) {
      setError(err.message || 'Upload failed. Please try again.');
    } finally {
      setUploading(false);
    }
  };

  const clearFile = (side) => {
    if (side === 'front') {
      if (frontPreview) URL.revokeObjectURL(frontPreview);
      setFrontFile(null);
      setFrontPreview(null);
    } else {
      if (backPreview) URL.revokeObjectURL(backPreview);
      setBackFile(null);
      setBackPreview(null);
    }
  };

  const canUpload = frontFile && (!requiresBack || backFile) && !uploading;

  return (
    <div className="sdk-step document-step">
      <div className="step-icon">
        <FileText size={48} />
      </div>
      <h2>Upload ID Document</h2>
      <p className="step-description">
        Take a clear photo of your government-issued ID document.
        Make sure all text is readable.
      </p>

      {/* Document type selector */}
      <div className="document-type-selector">
        {documentTypes.map((type) => (
          <button
            key={type.value}
            className={`doc-type-btn ${documentType === type.value ? 'selected' : ''}`}
            onClick={() => {
              setDocumentType(type.value);
              // Clear files when type changes
              clearFile('front');
              clearFile('back');
            }}
            disabled={uploading}
          >
            <span className="doc-icon">{type.icon}</span>
            <span>{type.label}</span>
          </button>
        ))}
      </div>

      {/* Upload areas */}
      <div className={`upload-areas ${requiresBack ? 'two-up' : ''}`}>
        {/* Front */}
        <div className="upload-area">
          <label>{requiresBack ? 'Front Side' : 'Document'}</label>
          {frontPreview ? (
            <div className="preview-container">
              <img src={frontPreview} alt="Front" />
              <button
                className="clear-btn"
                onClick={() => clearFile('front')}
                disabled={uploading}
              >
                <X size={16} />
              </button>
            </div>
          ) : (
            <div
              className="drop-zone"
              onClick={() => frontInputRef.current?.click()}
            >
              <Camera size={24} />
              <span>Take photo or upload</span>
            </div>
          )}
          <input
            ref={frontInputRef}
            type="file"
            accept="image/jpeg,image/png,application/pdf"
            capture="environment"
            onChange={(e) => handleFileSelect(e, 'front')}
            style={{ display: 'none' }}
          />
        </div>

        {/* Back (if required) */}
        {requiresBack && (
          <div className="upload-area">
            <label>Back Side</label>
            {backPreview ? (
              <div className="preview-container">
                <img src={backPreview} alt="Back" />
                <button
                  className="clear-btn"
                  onClick={() => clearFile('back')}
                  disabled={uploading}
                >
                  <X size={16} />
                </button>
              </div>
            ) : (
              <div
                className="drop-zone"
                onClick={() => backInputRef.current?.click()}
              >
                <Camera size={24} />
                <span>Take photo or upload</span>
              </div>
            )}
            <input
              ref={backInputRef}
              type="file"
              accept="image/jpeg,image/png,application/pdf"
              capture="environment"
              onChange={(e) => handleFileSelect(e, 'back')}
              style={{ display: 'none' }}
            />
          </div>
        )}
      </div>

      {/* Progress bar */}
      {uploading && (
        <div className="upload-progress">
          <div className="progress-bar">
            <div
              className="progress-fill"
              style={{ width: `${uploadProgress}%` }}
            />
          </div>
          <span>{uploadProgress < 100 ? 'Uploading...' : 'Processing...'}</span>
        </div>
      )}

      {/* Error */}
      {error && (
        <div className="error-message">
          <AlertCircle size={16} />
          {error}
        </div>
      )}

      <button
        className="sdk-btn primary"
        disabled={!canUpload}
        onClick={handleUpload}
      >
        {uploading ? (
          <>
            <Loader2 size={18} className="spin" />
            Uploading...
          </>
        ) : (
          <>
            <Upload size={18} />
            Upload Document
          </>
        )}
      </button>
    </div>
  );
};

const SelfieStep = ({ onComplete, client }) => {
  const [selfieFile, setSelfieFile] = useState(null);
  const [selfiePreview, setSelfiePreview] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState(null);
  const [cameraMode, setCameraMode] = useState(false);

  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const fileInputRef = useRef(null);
  const streamRef = useRef(null);

  const startCamera = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: 'user', width: 640, height: 480 },
      });
      streamRef.current = stream;
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
      }
      setCameraMode(true);
    } catch (err) {
      setError('Unable to access camera. Please upload a photo instead.');
    }
  };

  const stopCamera = () => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(track => track.stop());
      streamRef.current = null;
    }
    setCameraMode(false);
  };

  const capturePhoto = () => {
    if (!videoRef.current || !canvasRef.current) return;

    const video = videoRef.current;
    const canvas = canvasRef.current;
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;

    const ctx = canvas.getContext('2d');
    ctx.drawImage(video, 0, 0);

    canvas.toBlob((blob) => {
      const file = new File([blob], 'selfie.jpg', { type: 'image/jpeg' });
      setSelfieFile(file);
      setSelfiePreview(URL.createObjectURL(blob));
      stopCamera();
    }, 'image/jpeg', 0.9);
  };

  const handleFileSelect = (e) => {
    const file = e.target.files?.[0];
    if (!file) return;

    if (!file.type.startsWith('image/')) {
      setError('Please select an image file');
      return;
    }

    setError(null);
    setSelfieFile(file);
    setSelfiePreview(URL.createObjectURL(file));
  };

  const handleUpload = async () => {
    if (!selfieFile) return;

    setUploading(true);
    setError(null);

    try {
      // Get upload URL
      const uploadData = await client.getUploadUrl(
        'selfie',
        'front',
        selfieFile.name,
        selfieFile.type
      );

      // Upload to storage
      await fetch(uploadData.upload_url, {
        method: 'PUT',
        body: selfieFile,
        headers: { 'Content-Type': selfieFile.type },
      });

      // Confirm upload
      await client.confirmUpload(uploadData.document_id, selfieFile.size);

      // Complete step
      await onComplete({ selfie_uploaded: true });

    } catch (err) {
      setError(err.message || 'Upload failed. Please try again.');
    } finally {
      setUploading(false);
    }
  };

  const clearSelfie = () => {
    if (selfiePreview) URL.revokeObjectURL(selfiePreview);
    setSelfieFile(null);
    setSelfiePreview(null);
  };

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      stopCamera();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <div className="sdk-step selfie-step">
      <div className="step-icon">
        <Camera size={48} />
      </div>
      <h2>Take a Selfie</h2>
      <p className="step-description">
        Take a clear photo of your face. Make sure you're in good lighting
        and your face is clearly visible.
      </p>

      <div className="selfie-tips">
        <div className="tip">Good lighting</div>
        <div className="tip">Face centered</div>
        <div className="tip">No glasses</div>
      </div>

      <div className="selfie-area">
        {cameraMode ? (
          <div className="camera-view">
            <video ref={videoRef} autoPlay playsInline muted />
            <div className="face-guide" />
            <div className="camera-actions">
              <button className="sdk-btn secondary" onClick={stopCamera}>
                Cancel
              </button>
              <button className="sdk-btn primary capture" onClick={capturePhoto}>
                <Camera size={24} />
              </button>
            </div>
          </div>
        ) : selfiePreview ? (
          <div className="selfie-preview">
            <img src={selfiePreview} alt="Selfie" />
            <button className="retake-btn" onClick={clearSelfie} disabled={uploading}>
              <RefreshCw size={16} />
              Retake
            </button>
          </div>
        ) : (
          <div className="selfie-options">
            <button className="option-btn" onClick={startCamera}>
              <Camera size={32} />
              <span>Take Photo</span>
            </button>
            <button
              className="option-btn"
              onClick={() => fileInputRef.current?.click()}
            >
              <Upload size={32} />
              <span>Upload Photo</span>
            </button>
          </div>
        )}

        <input
          ref={fileInputRef}
          type="file"
          accept="image/*"
          capture="user"
          onChange={handleFileSelect}
          style={{ display: 'none' }}
        />
        <canvas ref={canvasRef} style={{ display: 'none' }} />
      </div>

      {error && (
        <div className="error-message">
          <AlertCircle size={16} />
          {error}
        </div>
      )}

      {selfieFile && !cameraMode && (
        <button
          className="sdk-btn primary"
          disabled={uploading}
          onClick={handleUpload}
        >
          {uploading ? (
            <>
              <Loader2 size={18} className="spin" />
              Uploading...
            </>
          ) : (
            <>
              Continue
              <ChevronRight size={18} />
            </>
          )}
        </button>
      )}
    </div>
  );
};

const ReviewStep = ({ onComplete, status }) => {
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState(null);

  const handleSubmit = async () => {
    setSubmitting(true);
    setError(null);

    try {
      await onComplete();
    } catch (err) {
      setError(err.message || 'Submission failed. Please try again.');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="sdk-step review-step">
      <div className="step-icon success">
        <CheckCircle size={48} />
      </div>
      <h2>Review & Submit</h2>
      <p className="step-description">
        Please review your submission. Once submitted, your verification
        will be processed automatically.
      </p>

      <div className="review-summary">
        <div className="summary-item">
          <CheckCircle size={18} />
          <span>Consent provided</span>
        </div>
        <div className="summary-item">
          <CheckCircle size={18} />
          <span>ID document uploaded</span>
        </div>
        {status?.steps_completed?.includes('selfie') && (
          <div className="summary-item">
            <CheckCircle size={18} />
            <span>Selfie uploaded</span>
          </div>
        )}
      </div>

      {error && (
        <div className="error-message">
          <AlertCircle size={16} />
          {error}
        </div>
      )}

      <button
        className="sdk-btn primary"
        disabled={submitting}
        onClick={handleSubmit}
      >
        {submitting ? (
          <>
            <Loader2 size={18} className="spin" />
            Submitting...
          </>
        ) : (
          <>
            Submit Verification
            <ChevronRight size={18} />
          </>
        )}
      </button>
    </div>
  );
};

const CompleteStep = ({ redirectUrl }) => {
  useEffect(() => {
    if (redirectUrl) {
      const timer = setTimeout(() => {
        window.location.href = redirectUrl;
      }, 3000);
      return () => clearTimeout(timer);
    }
  }, [redirectUrl]);

  return (
    <div className="sdk-step complete-step">
      <div className="step-icon success animate">
        <CheckCircle size={64} />
      </div>
      <h2>Verification Submitted!</h2>
      <p className="step-description">
        Thank you! Your verification has been submitted and is being processed.
        You will be notified of the result.
      </p>

      {redirectUrl && (
        <p className="redirect-notice">
          Redirecting you back in a few seconds...
        </p>
      )}
    </div>
  );
};

// Main SDK Component
export default function VerificationSDK({
  accessToken,
  baseUrl = '/api/v1/sdk',
  onComplete,
  onError,
  theme = 'light',
}) {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [config, setConfig] = useState(null);
  const [status, setStatus] = useState(null);
  const [currentStep, setCurrentStep] = useState(0);
  const [completed, setCompleted] = useState(false);

  const client = useCallback(
    () => createSDKClient(accessToken, baseUrl),
    [accessToken, baseUrl]
  )();

  // Load config and status on mount
  useEffect(() => {
    const init = async () => {
      try {
        setLoading(true);
        const [configData, statusData] = await Promise.all([
          client.getConfig(),
          client.getStatus(),
        ]);

        setConfig(configData);
        setStatus(statusData);

        // Resume from last completed step
        const stepsCompleted = statusData.steps_completed || [];
        const allSteps = ['consent', 'document', 'selfie', 'review'];
        const nextStep = allSteps.findIndex(s => !stepsCompleted.includes(s));
        setCurrentStep(nextStep >= 0 ? nextStep : 0);

      } catch (err) {
        setError(err.message);
        onError?.(err);
      } finally {
        setLoading(false);
      }
    };

    if (accessToken) {
      init();
    }
  }, [accessToken, client, onError]);

  const handleStepComplete = async (stepName, data) => {
    try {
      await client.completeStep(stepName, data);

      // Refresh status
      const newStatus = await client.getStatus();
      setStatus(newStatus);

      // Move to next step
      setCurrentStep((prev) => prev + 1);

    } catch (err) {
      setError(err.message);
      onError?.(err);
    }
  };

  const handleSubmit = async () => {
    try {
      const result = await client.submit();
      setCompleted(true);
      onComplete?.(result);
      return result;
    } catch (err) {
      throw err;
    }
  };

  if (loading) {
    return (
      <div className={`verification-sdk ${theme}`}>
        <div className="sdk-loading">
          <Loader2 size={32} className="spin" />
          <span>Loading verification...</span>
        </div>
        <SDKStyles />
      </div>
    );
  }

  if (error && !config) {
    return (
      <div className={`verification-sdk ${theme}`}>
        <div className="sdk-error">
          <AlertCircle size={48} />
          <h2>Unable to Load</h2>
          <p>{error}</p>
        </div>
        <SDKStyles />
      </div>
    );
  }

  if (completed) {
    return (
      <div className={`verification-sdk ${theme}`}>
        <CompleteStep redirectUrl={status?.redirect_url} />
        <SDKStyles />
      </div>
    );
  }

  const steps = ['consent', 'document', 'selfie', 'review'];

  return (
    <div className={`verification-sdk ${theme}`}>
      {/* Progress indicator */}
      <div className="sdk-progress">
        {steps.map((step, idx) => (
          <div
            key={step}
            className={`progress-step ${
              idx < currentStep ? 'completed' : ''
            } ${idx === currentStep ? 'active' : ''}`}
          >
            <div className="step-dot">
              {idx < currentStep ? <CheckCircle size={14} /> : idx + 1}
            </div>
            <span className="step-label">{step}</span>
          </div>
        ))}
      </div>

      {/* Current step content */}
      <div className="sdk-content">
        {currentStep === 0 && (
          <ConsentStep
            onComplete={(data) => handleStepComplete('consent', data)}
            branding={config?.branding}
          />
        )}
        {currentStep === 1 && (
          <DocumentStep
            onComplete={(data) => handleStepComplete('document', data)}
            allowedTypes={config?.allowed_document_types}
            client={client}
          />
        )}
        {currentStep === 2 && (
          <SelfieStep
            onComplete={(data) => handleStepComplete('selfie', data)}
            client={client}
          />
        )}
        {currentStep === 3 && (
          <ReviewStep
            onComplete={handleSubmit}
            status={status}
          />
        )}
      </div>

      {/* Navigation */}
      {currentStep > 0 && currentStep < steps.length && (
        <div className="sdk-navigation">
          <button
            className="sdk-btn secondary"
            onClick={() => setCurrentStep((prev) => prev - 1)}
          >
            <ChevronLeft size={18} />
            Back
          </button>
        </div>
      )}

      <SDKStyles />
    </div>
  );
}

// Styles component
function SDKStyles() {
  return (
    <style>{`
      .verification-sdk {
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        max-width: 480px;
        margin: 0 auto;
        padding: 24px;
        background: #ffffff;
        border-radius: 16px;
        box-shadow: 0 4px 24px rgba(0, 0, 0, 0.1);
      }

      .verification-sdk.dark {
        background: #1a1a2e;
        color: #e0e0e0;
      }

      /* Loading & Error */
      .sdk-loading, .sdk-error {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        padding: 48px 24px;
        text-align: center;
        gap: 16px;
      }

      .sdk-error h2 { color: #ef4444; margin: 0; }

      /* Progress */
      .sdk-progress {
        display: flex;
        justify-content: space-between;
        margin-bottom: 32px;
        padding: 0 16px;
      }

      .progress-step {
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 8px;
        flex: 1;
      }

      .step-dot {
        width: 32px;
        height: 32px;
        border-radius: 50%;
        background: #e5e7eb;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 14px;
        font-weight: 600;
        color: #6b7280;
        transition: all 0.3s;
      }

      .progress-step.completed .step-dot {
        background: #10b981;
        color: white;
      }

      .progress-step.active .step-dot {
        background: #6366f1;
        color: white;
        transform: scale(1.1);
      }

      .step-label {
        font-size: 11px;
        text-transform: uppercase;
        color: #9ca3af;
        font-weight: 500;
      }

      .progress-step.active .step-label {
        color: #6366f1;
      }

      /* Step content */
      .sdk-step {
        text-align: center;
        padding: 24px 0;
      }

      .step-icon {
        width: 80px;
        height: 80px;
        border-radius: 50%;
        background: linear-gradient(135deg, #6366f1, #8b5cf6);
        display: flex;
        align-items: center;
        justify-content: center;
        margin: 0 auto 24px;
        color: white;
      }

      .step-icon.success {
        background: linear-gradient(135deg, #10b981, #34d399);
      }

      .step-icon.animate {
        animation: pulse 1.5s ease-in-out infinite;
      }

      @keyframes pulse {
        0%, 100% { transform: scale(1); }
        50% { transform: scale(1.05); }
      }

      .sdk-step h2 {
        font-size: 24px;
        font-weight: 600;
        margin: 0 0 12px;
        color: #111827;
      }

      .dark .sdk-step h2 { color: #f3f4f6; }

      .step-description {
        color: #6b7280;
        line-height: 1.6;
        margin-bottom: 24px;
      }

      /* Consent step */
      .consent-details {
        text-align: left;
        background: #f9fafb;
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 24px;
      }

      .dark .consent-details { background: #252540; }

      .consent-details h3 {
        font-size: 14px;
        font-weight: 600;
        margin: 0 0 8px;
        color: #374151;
      }

      .dark .consent-details h3 { color: #e5e7eb; }

      .consent-details ul {
        margin: 0 0 16px;
        padding-left: 20px;
        color: #6b7280;
        font-size: 14px;
        line-height: 1.8;
      }

      .consent-checkbox {
        display: flex;
        align-items: flex-start;
        gap: 12px;
        text-align: left;
        padding: 16px;
        background: #f0f9ff;
        border-radius: 12px;
        margin-bottom: 24px;
        cursor: pointer;
      }

      .consent-checkbox input {
        width: 20px;
        height: 20px;
        margin-top: 2px;
        accent-color: #6366f1;
      }

      .consent-checkbox span {
        font-size: 14px;
        color: #374151;
      }

      /* Document step */
      .document-type-selector {
        display: flex;
        gap: 12px;
        margin-bottom: 24px;
        justify-content: center;
      }

      .doc-type-btn {
        flex: 1;
        max-width: 120px;
        padding: 16px 8px;
        border: 2px solid #e5e7eb;
        border-radius: 12px;
        background: white;
        cursor: pointer;
        transition: all 0.2s;
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 8px;
      }

      .doc-type-btn:hover { border-color: #6366f1; }
      .doc-type-btn.selected {
        border-color: #6366f1;
        background: #f5f3ff;
      }

      .doc-icon { font-size: 28px; }
      .doc-type-btn span:last-child { font-size: 12px; color: #374151; }

      .upload-areas {
        display: flex;
        gap: 16px;
        margin-bottom: 24px;
      }

      .upload-areas.two-up .upload-area { flex: 1; }

      .upload-area {
        text-align: left;
      }

      .upload-area label {
        display: block;
        font-size: 13px;
        font-weight: 600;
        color: #374151;
        margin-bottom: 8px;
      }

      .drop-zone {
        border: 2px dashed #d1d5db;
        border-radius: 12px;
        padding: 32px 16px;
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 8px;
        cursor: pointer;
        transition: all 0.2s;
        color: #6b7280;
        background: #f9fafb;
      }

      .drop-zone:hover {
        border-color: #6366f1;
        background: #f5f3ff;
      }

      .preview-container {
        position: relative;
        border-radius: 12px;
        overflow: hidden;
        aspect-ratio: 4/3;
      }

      .preview-container img {
        width: 100%;
        height: 100%;
        object-fit: cover;
      }

      .clear-btn {
        position: absolute;
        top: 8px;
        right: 8px;
        width: 28px;
        height: 28px;
        border-radius: 50%;
        background: rgba(0, 0, 0, 0.6);
        border: none;
        color: white;
        cursor: pointer;
        display: flex;
        align-items: center;
        justify-content: center;
      }

      /* Selfie step */
      .selfie-tips {
        display: flex;
        gap: 12px;
        justify-content: center;
        margin-bottom: 24px;
      }

      .tip {
        padding: 8px 16px;
        background: #f3f4f6;
        border-radius: 20px;
        font-size: 13px;
        color: #4b5563;
      }

      .selfie-area {
        margin-bottom: 24px;
      }

      .selfie-options {
        display: flex;
        gap: 16px;
        justify-content: center;
      }

      .option-btn {
        width: 140px;
        padding: 32px 16px;
        border: 2px solid #e5e7eb;
        border-radius: 16px;
        background: white;
        cursor: pointer;
        transition: all 0.2s;
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 12px;
        color: #374151;
      }

      .option-btn:hover {
        border-color: #6366f1;
        background: #f5f3ff;
      }

      .camera-view {
        position: relative;
        border-radius: 16px;
        overflow: hidden;
        background: #000;
      }

      .camera-view video {
        width: 100%;
        display: block;
        transform: scaleX(-1);
      }

      .face-guide {
        position: absolute;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        width: 200px;
        height: 260px;
        border: 3px solid rgba(255, 255, 255, 0.6);
        border-radius: 50%;
        pointer-events: none;
      }

      .camera-actions {
        position: absolute;
        bottom: 20px;
        left: 0;
        right: 0;
        display: flex;
        justify-content: center;
        gap: 16px;
      }

      .selfie-preview {
        position: relative;
        border-radius: 16px;
        overflow: hidden;
        max-width: 320px;
        margin: 0 auto;
      }

      .selfie-preview img {
        width: 100%;
        display: block;
      }

      .retake-btn {
        position: absolute;
        bottom: 16px;
        left: 50%;
        transform: translateX(-50%);
        padding: 8px 16px;
        background: rgba(0, 0, 0, 0.7);
        color: white;
        border: none;
        border-radius: 20px;
        font-size: 13px;
        cursor: pointer;
        display: flex;
        align-items: center;
        gap: 6px;
      }

      /* Review step */
      .review-summary {
        background: #f0fdf4;
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 24px;
      }

      .summary-item {
        display: flex;
        align-items: center;
        gap: 12px;
        padding: 8px 0;
        color: #166534;
      }

      /* Complete step */
      .complete-step .step-description {
        max-width: 320px;
        margin: 0 auto 24px;
      }

      .redirect-notice {
        color: #6b7280;
        font-size: 14px;
      }

      /* Progress bar */
      .upload-progress {
        margin-bottom: 20px;
      }

      .progress-bar {
        height: 8px;
        background: #e5e7eb;
        border-radius: 4px;
        overflow: hidden;
        margin-bottom: 8px;
      }

      .progress-fill {
        height: 100%;
        background: linear-gradient(90deg, #6366f1, #8b5cf6);
        transition: width 0.3s;
      }

      /* Error message */
      .error-message {
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 8px;
        padding: 12px;
        background: #fef2f2;
        border: 1px solid #fecaca;
        border-radius: 8px;
        color: #dc2626;
        font-size: 14px;
        margin-bottom: 16px;
      }

      /* Buttons */
      .sdk-btn {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        gap: 8px;
        padding: 14px 28px;
        font-size: 15px;
        font-weight: 600;
        border-radius: 12px;
        border: none;
        cursor: pointer;
        transition: all 0.2s;
        font-family: inherit;
      }

      .sdk-btn.primary {
        background: linear-gradient(135deg, #6366f1, #8b5cf6);
        color: white;
      }

      .sdk-btn.primary:hover:not(:disabled) {
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(99, 102, 241, 0.4);
      }

      .sdk-btn.primary:disabled {
        opacity: 0.6;
        cursor: not-allowed;
      }

      .sdk-btn.secondary {
        background: #f3f4f6;
        color: #374151;
      }

      .sdk-btn.secondary:hover {
        background: #e5e7eb;
      }

      .sdk-btn.capture {
        width: 64px;
        height: 64px;
        border-radius: 50%;
        padding: 0;
      }

      /* Navigation */
      .sdk-navigation {
        display: flex;
        justify-content: center;
        padding-top: 16px;
        border-top: 1px solid #e5e7eb;
        margin-top: 24px;
      }

      /* Animations */
      @keyframes spin {
        from { transform: rotate(0deg); }
        to { transform: rotate(360deg); }
      }

      .spin { animation: spin 1s linear infinite; }

      /* Responsive */
      @media (max-width: 480px) {
        .verification-sdk {
          margin: 0;
          border-radius: 0;
          min-height: 100vh;
        }

        .document-type-selector {
          flex-wrap: wrap;
        }

        .doc-type-btn {
          max-width: none;
          width: calc(33% - 8px);
        }

        .upload-areas.two-up {
          flex-direction: column;
        }
      }
    `}</style>
  );
}

// Export individual components for custom implementations
export { ConsentStep, DocumentStep, SelfieStep, ReviewStep, CompleteStep };
