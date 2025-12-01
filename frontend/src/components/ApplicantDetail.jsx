import React, { useState } from 'react';
import { useParams, useNavigate, useSearchParams } from 'react-router-dom';
import {
  ArrowLeft,
  CheckCircle2,
  XCircle,
  Clock,
  AlertTriangle,
  Shield,
  FileText,
  Camera,
  User,
  Mail,
  Calendar,
  Globe,
  Building2,
  Sparkles,
  ChevronRight,
  ExternalLink,
  Download,
  RefreshCw,
  MessageSquare,
  History,
  Link2,
  Languages,
  Copy,
  Fingerprint,
  Monitor,
  Loader2
} from 'lucide-react';
import { useApplicant, useApplicantTimeline, useReviewApplicant, useDownloadEvidence } from '../hooks/useApplicants';
import { useRiskSummary, useRegenerateRiskSummary } from '../hooks/useAI';
import { useKeyboardShortcut } from '../hooks/useKeyboardShortcut';
import { useToast } from '../contexts/ToastContext';
import { ApplicantDetailSkeleton } from './shared/LoadingSkeleton';
import { ErrorState, NotFound } from './shared/ErrorState';
import { ConfirmDialog } from './shared';

const tabs = [
  { id: 'overview', label: 'Overview' },
  { id: 'kyc-steps', label: 'KYC Steps' },
  { id: 'documents', label: 'Documents' },
  { id: 'screening', label: 'Screening' },
  { id: 'activity', label: 'Activity' },
  { id: 'ai-snapshot', label: 'AI Snapshot', ai: true },
  { id: 'linked', label: 'Linked Items' },
];

const statusConfig = {
  approved: { label: 'Approved', color: 'success', icon: CheckCircle2 },
  rejected: { label: 'Rejected', color: 'danger', icon: XCircle },
  pending: { label: 'Pending', color: 'muted', icon: Clock },
  in_progress: { label: 'In Progress', color: 'warning', icon: Clock },
  review: { label: 'Review', color: 'info', icon: Clock },
  init: { label: 'New', color: 'muted', icon: Clock },
};

const getRiskColor = (bucket) => {
  switch (bucket) {
    case 'low': return 'success';
    case 'medium': return 'warning';
    case 'high': return 'danger';
    default: return 'muted';
  }
};

const getRiskBucket = (score) => {
  if (score === null || score === undefined) return 'muted';
  if (score < 30) return 'low';
  if (score < 70) return 'medium';
  return 'high';
};

const formatDateTime = (dateStr) => {
  if (!dateStr) return '—';
  const date = new Date(dateStr);
  return date.toLocaleString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  });
};

const countryFlags = {
  US: '🇺🇸', ZA: '🇿🇦', MX: '🇲🇽', AE: '🇦🇪', GB: '🇬🇧',
  CA: '🇨🇦', AU: '🇦🇺', DE: '🇩🇪', FR: '🇫🇷', JP: '🇯🇵',
  CN: '🇨🇳', IN: '🇮🇳', BR: '🇧🇷', RU: '🇷🇺', KR: '🇰🇷',
  SG: '🇸🇬', HK: '🇭🇰', NG: '🇳🇬', KE: '🇰🇪',
};

const stepIcons = {
  identity: FileText,
  id_document: FileText,
  liveness: Camera,
  selfie: Camera,
  proof_of_address: FileText,
  source_of_funds: FileText,
  screening: Shield,
};

export default function ApplicantDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();
  const toast = useToast();

  // Get active tab from URL, default to 'overview'
  const activeTab = searchParams.get('tab') || 'overview';
  const setActiveTab = (tab) => {
    setSearchParams({ tab }, { replace: true });
  };

  // Confirm dialog state
  const [confirmDialog, setConfirmDialog] = useState({
    isOpen: false,
    action: null,
  });

  // Fetch applicant data
  const { data: applicant, isLoading, error, refetch } = useApplicant(id);

  // Fetch timeline
  const { data: timeline } = useApplicantTimeline(id);

  // Fetch AI risk summary
  const { data: riskSummary, isLoading: riskLoading } = useRiskSummary(id);

  // Mutations
  const reviewMutation = useReviewApplicant();
  const downloadMutation = useDownloadEvidence();
  const regenerateRiskMutation = useRegenerateRiskSummary();

  // Keyboard shortcuts
  useKeyboardShortcut('a', () => {
    if (applicant && applicant.review_status !== 'approved') {
      setConfirmDialog({ isOpen: true, action: 'approve' });
    }
  });
  useKeyboardShortcut('r', () => {
    if (applicant && applicant.review_status !== 'rejected') {
      setConfirmDialog({ isOpen: true, action: 'reject' });
    }
  });
  useKeyboardShortcut('Escape', () => navigate('/applicants'), { enableOnFormElements: false });

  const handleBack = () => {
    navigate('/applicants');
  };

  const handleApproveClick = () => {
    setConfirmDialog({ isOpen: true, action: 'approve' });
  };

  const handleRejectClick = () => {
    setConfirmDialog({ isOpen: true, action: 'reject' });
  };

  const executeReviewAction = async () => {
    const action = confirmDialog.action;
    setConfirmDialog({ isOpen: false, action: null });

    try {
      await reviewMutation.mutateAsync({
        id,
        decision: action,
        notes: `${action === 'approve' ? 'Approved' : 'Rejected'} via dashboard`,
      });
      toast.success(`Applicant ${action === 'approve' ? 'approved' : 'rejected'} successfully`);
    } catch (err) {
      toast.error(`Failed to ${action} applicant: ${err.message}`);
    }
  };

  const handleDownloadEvidence = async () => {
    const displayName = applicant?.first_name && applicant?.last_name
      ? `${applicant.first_name}_${applicant.last_name}`
      : `applicant_${id.slice(0, 8)}`;

    try {
      await downloadMutation.mutateAsync({
        id,
        filename: `evidence_${displayName}.pdf`,
      });
      toast.success('Evidence pack downloaded successfully');
    } catch (err) {
      toast.error(`Failed to download evidence: ${err.message}`);
    }
  };

  const handleRegenerateRiskSummary = async () => {
    try {
      await regenerateRiskMutation.mutateAsync(id);
      toast.success('AI risk summary regenerated');
    } catch (err) {
      toast.error(`Failed to regenerate risk summary: ${err.message}`);
    }
  };

  // Loading state
  if (isLoading) {
    return <ApplicantDetailSkeleton />;
  }

  // Error state - check for 404
  if (error) {
    if (error.message?.includes('404') || error.message?.includes('not found')) {
      return (
        <NotFound
          title="Applicant Not Found"
          message="The applicant you're looking for doesn't exist or has been deleted."
          onBack={handleBack}
          onHome={() => navigate('/')}
        />
      );
    }
    return (
      <ErrorState
        title="Failed to load applicant"
        message="We couldn't load this applicant's details. Please try again."
        error={error}
        onRetry={refetch}
        onBack={handleBack}
      />
    );
  }

  if (!applicant) {
    return (
      <NotFound
        title="Applicant Not Found"
        message="The applicant you're looking for doesn't exist or has been deleted."
        onBack={handleBack}
        onHome={() => navigate('/')}
      />
    );
  }

  const status = statusConfig[applicant.review_status] || statusConfig.pending;
  const StatusIcon = status?.icon;
  const riskBucket = applicant.risk_level || getRiskBucket(applicant.risk_score);
  const riskColor = getRiskColor(riskBucket);

  const displayName = applicant.first_name && applicant.last_name
    ? `${applicant.first_name} ${applicant.last_name}`
    : applicant.email?.split('@')[0] || `Applicant ${applicant.id.slice(0, 8)}`;

  const countryCode = applicant.country_code || applicant.nationality?.slice(0, 2)?.toUpperCase();

  // Build activity from timeline or applicant events
  const activityItems = timeline || applicant.activity || [];

  return (
    <div className="applicant-detail">
      <style>{`
        .applicant-detail {
          max-width: 1400px;
        }

        /* Header */
        .detail-header {
          display: flex;
          align-items: flex-start;
          gap: 24px;
          margin-bottom: 24px;
        }

        .back-btn {
          display: flex;
          align-items: center;
          gap: 8px;
          padding: 8px 12px;
          background: var(--bg-secondary);
          border: 1px solid var(--border-color);
          border-radius: 8px;
          color: var(--text-secondary);
          cursor: pointer;
          font-size: 14px;
          transition: all 0.15s;
        }

        .back-btn:hover {
          background: var(--bg-hover);
          color: var(--text-primary);
        }

        .header-content {
          flex: 1;
        }

        .header-top {
          display: flex;
          align-items: center;
          gap: 16px;
          margin-bottom: 8px;
        }

        .applicant-name {
          font-size: 28px;
          font-weight: 600;
          letter-spacing: -0.02em;
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

        .status-badge.success {
          background: rgba(16, 185, 129, 0.15);
          color: var(--success);
        }

        .status-badge.danger {
          background: rgba(239, 68, 68, 0.15);
          color: var(--danger);
        }

        .status-badge.warning {
          background: rgba(245, 158, 11, 0.15);
          color: var(--warning);
        }

        .status-badge.muted {
          background: var(--bg-tertiary);
          color: var(--text-muted);
        }

        .status-badge.info {
          background: rgba(59, 130, 246, 0.15);
          color: var(--info);
        }

        .header-meta {
          display: flex;
          align-items: center;
          gap: 16px;
          color: var(--text-secondary);
          font-size: 14px;
        }

        .header-meta-item {
          display: flex;
          align-items: center;
          gap: 6px;
        }

        .header-actions {
          display: flex;
          gap: 12px;
        }

        .btn {
          display: flex;
          align-items: center;
          gap: 8px;
          padding: 10px 16px;
          border-radius: 8px;
          font-size: 14px;
          font-weight: 500;
          cursor: pointer;
          transition: all 0.15s;
          border: none;
          font-family: inherit;
        }

        .btn:disabled {
          opacity: 0.6;
          cursor: not-allowed;
        }

        .btn-secondary {
          background: var(--bg-secondary);
          border: 1px solid var(--border-color);
          color: var(--text-primary);
        }

        .btn-secondary:hover:not(:disabled) {
          background: var(--bg-hover);
        }

        .btn-success {
          background: var(--success);
          color: white;
        }

        .btn-success:hover:not(:disabled) {
          opacity: 0.9;
        }

        .btn-danger {
          background: var(--danger);
          color: white;
        }

        .btn-danger:hover:not(:disabled) {
          opacity: 0.9;
        }

        /* Tabs */
        .tabs {
          display: flex;
          gap: 4px;
          background: var(--bg-secondary);
          border: 1px solid var(--border-color);
          border-radius: 12px;
          padding: 4px;
          margin-bottom: 24px;
        }

        .tab {
          padding: 10px 16px;
          border-radius: 8px;
          font-size: 14px;
          font-weight: 500;
          color: var(--text-secondary);
          cursor: pointer;
          transition: all 0.15s;
          display: flex;
          align-items: center;
          gap: 6px;
        }

        .tab:hover {
          color: var(--text-primary);
        }

        .tab.active {
          background: var(--bg-tertiary);
          color: var(--text-primary);
        }

        .tab.ai {
          background: linear-gradient(135deg, rgba(99, 102, 241, 0.1), rgba(168, 85, 247, 0.1));
        }

        .tab.ai.active {
          background: linear-gradient(135deg, var(--accent-primary), #a855f7);
          color: white;
        }

        /* Content Grid */
        .content-grid {
          display: grid;
          grid-template-columns: 1fr 360px;
          gap: 24px;
        }

        .card {
          background: var(--bg-secondary);
          border: 1px solid var(--border-color);
          border-radius: 12px;
          overflow: hidden;
        }

        .card-header {
          padding: 16px 20px;
          border-bottom: 1px solid var(--border-color);
          display: flex;
          justify-content: space-between;
          align-items: center;
        }

        .card-title {
          font-size: 15px;
          font-weight: 600;
          display: flex;
          align-items: center;
          gap: 8px;
        }

        .card-content {
          padding: 20px;
        }

        /* Info Grid */
        .info-grid {
          display: grid;
          grid-template-columns: 1fr 1fr;
          gap: 20px;
        }

        .info-item {
          display: flex;
          flex-direction: column;
          gap: 4px;
        }

        .info-label {
          font-size: 12px;
          color: var(--text-muted);
          text-transform: uppercase;
          letter-spacing: 0.05em;
        }

        .info-value {
          font-size: 14px;
          color: var(--text-primary);
          display: flex;
          align-items: center;
          gap: 8px;
        }

        .info-value .copy-btn {
          opacity: 0;
          transition: opacity 0.15s;
          cursor: pointer;
        }

        .info-item:hover .copy-btn {
          opacity: 1;
        }

        /* Risk Score Card */
        .risk-card {
          text-align: center;
          padding: 24px;
        }

        .risk-score-large {
          font-size: 56px;
          font-weight: 700;
          line-height: 1;
          margin-bottom: 8px;
        }

        .risk-score-large.success { color: var(--success); }
        .risk-score-large.warning { color: var(--warning); }
        .risk-score-large.danger { color: var(--danger); }
        .risk-score-large.muted { color: var(--text-muted); }

        .risk-label {
          font-size: 14px;
          color: var(--text-secondary);
          margin-bottom: 16px;
        }

        .risk-bar-large {
          height: 8px;
          background: var(--bg-tertiary);
          border-radius: 4px;
          overflow: hidden;
          margin-bottom: 16px;
        }

        .risk-bar-fill {
          height: 100%;
          border-radius: 4px;
          transition: width 0.3s ease;
        }

        .risk-bar-fill.success { background: var(--success); }
        .risk-bar-fill.warning { background: var(--warning); }
        .risk-bar-fill.danger { background: var(--danger); }

        .risk-factors {
          text-align: left;
        }

        .risk-factor {
          display: flex;
          align-items: center;
          gap: 8px;
          padding: 8px 0;
          font-size: 13px;
          color: var(--text-secondary);
          border-bottom: 1px solid var(--border-color);
        }

        .risk-factor:last-child {
          border-bottom: none;
        }

        .risk-factor-indicator {
          width: 8px;
          height: 8px;
          border-radius: 50%;
        }

        /* Screening Results */
        .screening-item {
          padding: 16px;
          border-radius: 8px;
          background: var(--bg-tertiary);
          margin-bottom: 12px;
        }

        .screening-item:last-child {
          margin-bottom: 0;
        }

        .screening-header {
          display: flex;
          align-items: center;
          justify-content: space-between;
          margin-bottom: 8px;
        }

        .screening-type {
          font-weight: 600;
          font-size: 14px;
        }

        .screening-status {
          display: flex;
          align-items: center;
          gap: 6px;
          font-size: 12px;
          font-weight: 500;
        }

        .screening-status.clear {
          color: var(--success);
        }

        .screening-status.hit {
          color: var(--warning);
        }

        .screening-meta {
          font-size: 12px;
          color: var(--text-muted);
        }

        .screening-hit {
          margin-top: 12px;
          padding: 12px;
          background: rgba(245, 158, 11, 0.1);
          border: 1px solid rgba(245, 158, 11, 0.3);
          border-radius: 8px;
        }

        .screening-hit-header {
          display: flex;
          align-items: center;
          gap: 8px;
          margin-bottom: 8px;
        }

        .screening-hit-source {
          font-size: 11px;
          font-weight: 600;
          text-transform: uppercase;
          letter-spacing: 0.05em;
          color: var(--warning);
        }

        .screening-hit-confidence {
          margin-left: auto;
          font-size: 12px;
          color: var(--text-secondary);
        }

        .screening-hit-detail {
          font-size: 13px;
          color: var(--text-primary);
          line-height: 1.5;
        }

        /* AI Snapshot */
        .ai-snapshot-card {
          border: 1px solid var(--accent-primary);
          background: linear-gradient(135deg, var(--bg-secondary), rgba(99, 102, 241, 0.05));
        }

        .ai-summary {
          font-size: 14px;
          line-height: 1.7;
          color: var(--text-primary);
          white-space: pre-wrap;
        }

        .ai-summary strong {
          color: var(--accent-primary);
        }

        .ai-citations {
          margin-top: 20px;
          padding-top: 20px;
          border-top: 1px solid var(--border-color);
        }

        .ai-citation {
          display: flex;
          align-items: center;
          gap: 8px;
          padding: 8px 12px;
          background: var(--bg-tertiary);
          border-radius: 6px;
          margin-bottom: 8px;
          font-size: 12px;
        }

        .ai-citation-type {
          padding: 2px 6px;
          border-radius: 4px;
          font-weight: 600;
          text-transform: uppercase;
          letter-spacing: 0.03em;
          font-size: 10px;
        }

        .ai-citation-type.list {
          background: rgba(59, 130, 246, 0.15);
          color: var(--info);
        }

        .ai-citation-type.rule {
          background: rgba(168, 85, 247, 0.15);
          color: #a855f7;
        }

        .ai-confidence {
          display: flex;
          align-items: center;
          gap: 8px;
          margin-top: 20px;
          padding: 12px;
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

        /* Activity Timeline */
        .timeline {
          position: relative;
        }

        .timeline::before {
          content: '';
          position: absolute;
          left: 15px;
          top: 0;
          bottom: 0;
          width: 2px;
          background: var(--border-color);
        }

        .timeline-item {
          display: flex;
          gap: 16px;
          padding: 16px 0;
          position: relative;
        }

        .timeline-dot {
          width: 32px;
          height: 32px;
          border-radius: 50%;
          background: var(--bg-tertiary);
          border: 2px solid var(--border-color);
          display: flex;
          align-items: center;
          justify-content: center;
          flex-shrink: 0;
          z-index: 1;
        }

        .timeline-dot.decision { background: rgba(16, 185, 129, 0.15); border-color: var(--success); color: var(--success); }
        .timeline-dot.review { background: rgba(59, 130, 246, 0.15); border-color: var(--info); color: var(--info); }
        .timeline-dot.screening { background: rgba(245, 158, 11, 0.15); border-color: var(--warning); color: var(--warning); }
        .timeline-dot.verification { background: rgba(99, 102, 241, 0.15); border-color: var(--accent-primary); color: var(--accent-primary); }

        .timeline-content {
          flex: 1;
          padding-top: 4px;
        }

        .timeline-event {
          font-size: 14px;
          font-weight: 500;
          margin-bottom: 4px;
        }

        .timeline-meta {
          font-size: 12px;
          color: var(--text-muted);
        }

        /* Device Info */
        .device-info {
          display: grid;
          grid-template-columns: 1fr 1fr;
          gap: 12px;
        }

        .device-item {
          display: flex;
          align-items: center;
          gap: 8px;
          padding: 12px;
          background: var(--bg-tertiary);
          border-radius: 8px;
          font-size: 13px;
        }

        .device-icon {
          color: var(--text-muted);
        }

        .loading-inline {
          display: flex;
          align-items: center;
          justify-content: center;
          padding: 40px;
          color: var(--text-muted);
          gap: 8px;
        }

        @keyframes spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }

        .spinner {
          animation: spin 1s linear infinite;
        }

        @media (max-width: 1200px) {
          .content-grid {
            grid-template-columns: 1fr;
          }
        }
      `}</style>

      <div className="detail-header">
        <button className="back-btn" onClick={handleBack}>
          <ArrowLeft size={16} />
          Back
        </button>

        <div className="header-content">
          <div className="header-top">
            <h1 className="applicant-name">{displayName}</h1>
            <span className={`status-badge ${status?.color}`}>
              {StatusIcon && <StatusIcon size={14} />}
              {status?.label}
            </span>
          </div>

          <div className="header-meta">
            <span className="header-meta-item">
              <Mail size={14} />
              {applicant.email || '—'}
            </span>
            {countryCode && (
              <span className="header-meta-item">
                <Globe size={14} />
                {countryFlags[countryCode] || '🌍'} {applicant.nationality || countryCode}
              </span>
            )}
            <span className="header-meta-item">
              <Calendar size={14} />
              Submitted {formatDateTime(applicant.created_at)}
            </span>
            <span className="header-meta-item" style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: 12, color: 'var(--text-muted)' }}>
              ID: {applicant.id}
            </span>
          </div>
        </div>

        <div className="header-actions">
          <button
            className="btn btn-secondary"
            onClick={handleDownloadEvidence}
            disabled={downloadMutation.isPending}
          >
            {downloadMutation.isPending ? (
              <Loader2 size={16} className="spinner" />
            ) : (
              <Download size={16} />
            )}
            Export
          </button>
          <button className="btn btn-secondary">
            <RefreshCw size={16} />
            Re-screen
          </button>
          <button className="btn btn-secondary">
            <MessageSquare size={16} />
            Request Docs
          </button>
          <button
            className="btn btn-danger"
            onClick={handleRejectClick}
            disabled={reviewMutation.isPending || applicant.review_status === 'rejected'}
            aria-label="Reject applicant (R)"
            title="Reject (R)"
          >
            {reviewMutation.isPending && reviewMutation.variables?.decision === 'reject' ? (
              <Loader2 size={16} className="spinner" />
            ) : (
              <XCircle size={16} />
            )}
            Reject
          </button>
          <button
            className="btn btn-success"
            onClick={handleApproveClick}
            disabled={reviewMutation.isPending || applicant.review_status === 'approved'}
            aria-label="Approve applicant (A)"
            title="Approve (A)"
          >
            {reviewMutation.isPending && reviewMutation.variables?.decision === 'approve' ? (
              <Loader2 size={16} className="spinner" />
            ) : (
              <CheckCircle2 size={16} />
            )}
            Approve
          </button>
        </div>
      </div>

      <div className="tabs">
        {tabs.map(tab => (
          <div
            key={tab.id}
            className={`tab ${activeTab === tab.id ? 'active' : ''} ${tab.ai ? 'ai' : ''}`}
            onClick={() => setActiveTab(tab.id)}
          >
            {tab.ai && <Sparkles size={14} />}
            {tab.label}
          </div>
        ))}
      </div>

      <div className="content-grid">
        <div className="main-column">
          {activeTab === 'overview' && (
            <>
              <div className="card" style={{ marginBottom: 24 }}>
                <div className="card-header">
                  <div className="card-title">
                    <User size={16} />
                    Personal Information
                  </div>
                </div>
                <div className="card-content">
                  <div className="info-grid">
                    <div className="info-item">
                      <span className="info-label">Full Name</span>
                      <span className="info-value">{displayName}</span>
                    </div>
                    <div className="info-item">
                      <span className="info-label">Email</span>
                      <span className="info-value">
                        {applicant.email || '—'}
                        {applicant.email && (
                          <Copy size={12} className="copy-btn" style={{ color: 'var(--text-muted)' }} />
                        )}
                      </span>
                    </div>
                    <div className="info-item">
                      <span className="info-label">Phone</span>
                      <span className="info-value">{applicant.phone || '—'}</span>
                    </div>
                    <div className="info-item">
                      <span className="info-label">Date of Birth</span>
                      <span className="info-value">{applicant.date_of_birth || '—'}</span>
                    </div>
                    <div className="info-item">
                      <span className="info-label">Nationality</span>
                      <span className="info-value">
                        {countryCode ? `${countryFlags[countryCode] || '🌍'} ${applicant.nationality || countryCode}` : '—'}
                      </span>
                    </div>
                    <div className="info-item">
                      <span className="info-label">External ID</span>
                      <span className="info-value" style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: 12 }}>
                        {applicant.external_id || '—'}
                      </span>
                    </div>
                    {applicant.address && (
                      <div className="info-item" style={{ gridColumn: 'span 2' }}>
                        <span className="info-label">Address</span>
                        <span className="info-value">{applicant.address}</span>
                      </div>
                    )}
                  </div>
                </div>
              </div>

              {applicant.company_name && (
                <div className="card" style={{ marginBottom: 24 }}>
                  <div className="card-header">
                    <div className="card-title">
                      <Building2 size={16} />
                      Company Information
                    </div>
                    <span style={{ color: 'var(--accent-primary)', fontSize: 13, cursor: 'pointer' }}>
                      View Company <ChevronRight size={14} style={{ display: 'inline' }} />
                    </span>
                  </div>
                  <div className="card-content">
                    <div className="info-grid">
                      <div className="info-item">
                        <span className="info-label">Company Name</span>
                        <span className="info-value">{applicant.company_name}</span>
                      </div>
                      {applicant.company_role && (
                        <div className="info-item">
                          <span className="info-label">Role</span>
                          <span className="info-value">{applicant.company_role}</span>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              )}

              <div className="card">
                <div className="card-header">
                  <div className="card-title">
                    <Fingerprint size={16} />
                    Session Info
                  </div>
                </div>
                <div className="card-content">
                  <div className="device-info">
                    <div className="device-item">
                      <Monitor size={16} className="device-icon" />
                      <span>Platform: {applicant.platform || 'Web'}</span>
                    </div>
                    <div className="device-item">
                      <Globe size={16} className="device-icon" />
                      <span>Source: {applicant.source || 'API'}</span>
                    </div>
                  </div>
                </div>
              </div>
            </>
          )}

          {activeTab === 'screening' && (
            <div className="card">
              <div className="card-header">
                <div className="card-title">
                  <Shield size={16} />
                  Screening Results
                </div>
                <button className="btn btn-secondary" style={{ padding: '6px 12px', fontSize: 13 }}>
                  <RefreshCw size={14} />
                  Re-run All
                </button>
              </div>
              <div className="card-content">
                {applicant.screening_results ? (
                  Object.entries(applicant.screening_results).map(([type, result]) => (
                    <div key={type} className="screening-item">
                      <div className="screening-header">
                        <span className="screening-type">{type.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}</span>
                        <span className={`screening-status ${result.status}`}>
                          {result.status === 'clear' ? <CheckCircle2 size={14} /> : <AlertTriangle size={14} />}
                          {result.status === 'clear' ? 'Clear' : 'Hit'}
                        </span>
                      </div>
                      {result.last_checked && (
                        <div className="screening-meta">
                          Last checked: {formatDateTime(result.last_checked)}
                        </div>
                      )}
                      {result.hits && result.hits.length > 0 && result.hits.map((hit, idx) => (
                        <div key={idx} className="screening-hit">
                          <div className="screening-hit-header">
                            <span className="screening-hit-source">{hit.source}</span>
                            {hit.confidence && (
                              <span className="screening-hit-confidence">{hit.confidence}% match</span>
                            )}
                          </div>
                          <div className="screening-hit-detail">
                            {hit.details || hit.notes || JSON.stringify(hit, null, 2)}
                          </div>
                        </div>
                      ))}
                    </div>
                  ))
                ) : (
                  <div style={{ color: 'var(--text-muted)', textAlign: 'center', padding: 40 }}>
                    No screening results available
                  </div>
                )}
              </div>
            </div>
          )}

          {activeTab === 'ai-snapshot' && (
            <div className="card ai-snapshot-card">
              <div className="card-header">
                <div className="card-title">
                  <Sparkles size={16} style={{ color: 'var(--accent-primary)' }} />
                  AI Risk Assessment
                </div>
                <button
                  className="btn btn-secondary"
                  style={{ padding: '6px 12px', fontSize: 13 }}
                  onClick={handleRegenerateRiskSummary}
                  disabled={regenerateRiskMutation.isPending}
                >
                  {regenerateRiskMutation.isPending ? (
                    <Loader2 size={14} className="spinner" />
                  ) : (
                    <RefreshCw size={14} />
                  )}
                  Regenerate
                </button>
              </div>
              <div className="card-content">
                {riskLoading ? (
                  <div className="loading-inline">
                    <Loader2 size={20} className="spinner" />
                    Loading AI analysis...
                  </div>
                ) : riskSummary ? (
                  <>
                    <div
                      className="ai-summary"
                      dangerouslySetInnerHTML={{
                        __html: (riskSummary.summary || riskSummary.response || '')
                          .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
                          .replace(/\n/g, '<br />')
                      }}
                    />

                    {riskSummary.confidence && (
                      <div className="ai-confidence">
                        <Sparkles size={14} style={{ color: 'var(--accent-primary)' }} />
                        <span style={{ fontSize: 13 }}>Confidence</span>
                        <div className="ai-confidence-bar">
                          <div
                            className="ai-confidence-fill"
                            style={{ width: `${riskSummary.confidence}%` }}
                          />
                        </div>
                        <span style={{ fontSize: 13, fontWeight: 600 }}>{riskSummary.confidence}%</span>
                      </div>
                    )}

                    {riskSummary.citations && riskSummary.citations.length > 0 && (
                      <div className="ai-citations">
                        <div style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-muted)', marginBottom: 12, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                          Citations & Sources
                        </div>
                        {riskSummary.citations.map((citation, idx) => (
                          <div key={idx} className="ai-citation">
                            <span className={`ai-citation-type ${citation.type}`}>{citation.type}</span>
                            <span style={{ flex: 1 }}>{citation.source}</span>
                            <span style={{ color: 'var(--text-muted)' }}>{citation.detail}</span>
                          </div>
                        ))}
                      </div>
                    )}
                  </>
                ) : (
                  <div style={{ color: 'var(--text-muted)', textAlign: 'center', padding: 40 }}>
                    <Sparkles size={32} style={{ marginBottom: 12, opacity: 0.5 }} />
                    <p>No AI analysis available yet</p>
                    <button
                      className="btn btn-secondary"
                      style={{ marginTop: 16 }}
                      onClick={handleRegenerateRiskSummary}
                      disabled={regenerateRiskMutation.isPending}
                    >
                      {regenerateRiskMutation.isPending ? (
                        <>
                          <Loader2 size={14} className="spinner" />
                          Generating...
                        </>
                      ) : (
                        <>
                          <Sparkles size={14} />
                          Generate AI Analysis
                        </>
                      )}
                    </button>
                  </div>
                )}
              </div>
            </div>
          )}

          {activeTab === 'activity' && (
            <div className="card">
              <div className="card-header">
                <div className="card-title">
                  <History size={16} />
                  Activity Timeline
                </div>
              </div>
              <div className="card-content">
                {activityItems.length > 0 ? (
                  <div className="timeline">
                    {activityItems.map((item, idx) => (
                      <div key={idx} className="timeline-item">
                        <div className={`timeline-dot ${item.type || 'verification'}`}>
                          {item.type === 'decision' && <CheckCircle2 size={14} />}
                          {item.type === 'review' && <User size={14} />}
                          {item.type === 'screening' && <Shield size={14} />}
                          {(item.type === 'verification' || !item.type) && <FileText size={14} />}
                          {item.type === 'submission' && <Clock size={14} />}
                        </div>
                        <div className="timeline-content">
                          <div className="timeline-event">{item.event || item.description || item.action}</div>
                          <div className="timeline-meta">
                            {item.actor || item.user || 'System'} • {formatDateTime(item.timestamp || item.created_at)}
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div style={{ color: 'var(--text-muted)', textAlign: 'center', padding: 40 }}>
                    No activity recorded yet
                  </div>
                )}
              </div>
            </div>
          )}

          {activeTab === 'kyc-steps' && (
            <div className="card">
              <div className="card-header">
                <div className="card-title">
                  <CheckCircle2 size={16} />
                  Verification Steps
                </div>
              </div>
              <div className="card-content">
                {applicant.steps && applicant.steps.length > 0 ? (
                  applicant.steps.map((step, idx) => {
                    const StepIcon = stepIcons[step.name] || stepIcons[step.step_name] || FileText;
                    return (
                      <div
                        key={idx}
                        style={{
                          display: 'flex',
                          alignItems: 'center',
                          gap: 12,
                          padding: '16px 0',
                          borderBottom: idx < applicant.steps.length - 1 ? '1px solid var(--border-color)' : 'none'
                        }}
                      >
                        <div style={{
                          width: 40,
                          height: 40,
                          borderRadius: 8,
                          background: step.status === 'completed' || step.status === 'complete' ? 'rgba(16, 185, 129, 0.15)' : 'var(--bg-tertiary)',
                          color: step.status === 'completed' || step.status === 'complete' ? 'var(--success)' : 'var(--text-muted)',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center'
                        }}>
                          <StepIcon size={18} />
                        </div>
                        <div style={{ flex: 1 }}>
                          <div style={{ fontSize: 14, fontWeight: 500 }}>{step.name || step.step_name}</div>
                          <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>
                            {step.status === 'completed' || step.status === 'complete'
                              ? `Completed ${step.completed_at ? formatDateTime(step.completed_at) : ''}`
                              : step.status}
                          </div>
                        </div>
                        {(step.status === 'completed' || step.status === 'complete') && (
                          <CheckCircle2 size={18} color="var(--success)" />
                        )}
                      </div>
                    );
                  })
                ) : (
                  <div style={{ color: 'var(--text-muted)', textAlign: 'center', padding: 40 }}>
                    No verification steps configured
                  </div>
                )}
              </div>
            </div>
          )}

          {activeTab === 'documents' && (
            <div className="card">
              <div className="card-header">
                <div className="card-title">
                  <FileText size={16} />
                  Documents
                </div>
              </div>
              <div className="card-content">
                {applicant.documents && applicant.documents.length > 0 ? (
                  applicant.documents.map((doc, idx) => (
                    <div
                      key={idx}
                      style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: 12,
                        padding: '16px 0',
                        borderBottom: idx < applicant.documents.length - 1 ? '1px solid var(--border-color)' : 'none'
                      }}
                    >
                      <div style={{
                        width: 48,
                        height: 48,
                        borderRadius: 8,
                        background: 'var(--bg-tertiary)',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center'
                      }}>
                        <FileText size={20} style={{ color: 'var(--text-muted)' }} />
                      </div>
                      <div style={{ flex: 1 }}>
                        <div style={{ fontSize: 14, fontWeight: 500 }}>{doc.type || doc.document_type}</div>
                        <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>
                          {doc.file_name || doc.filename} • {formatDateTime(doc.uploaded_at || doc.created_at)}
                        </div>
                      </div>
                      <span style={{
                        padding: '4px 8px',
                        borderRadius: 4,
                        fontSize: 11,
                        fontWeight: 600,
                        background: doc.status === 'verified' ? 'rgba(16, 185, 129, 0.15)' : 'var(--bg-tertiary)',
                        color: doc.status === 'verified' ? 'var(--success)' : 'var(--text-muted)'
                      }}>
                        {doc.status?.toUpperCase() || 'PENDING'}
                      </span>
                    </div>
                  ))
                ) : (
                  <div style={{ color: 'var(--text-muted)', textAlign: 'center', padding: 40 }}>
                    No documents uploaded yet
                  </div>
                )}
              </div>
            </div>
          )}

          {activeTab === 'linked' && (
            <div className="card">
              <div className="card-header">
                <div className="card-title">
                  <Link2 size={16} />
                  Linked Items
                </div>
              </div>
              <div className="card-content">
                <div style={{ color: 'var(--text-muted)', textAlign: 'center', padding: 40 }}>
                  No linked items found
                </div>
              </div>
            </div>
          )}
        </div>

        <div className="side-column">
          <div className="card" style={{ marginBottom: 24 }}>
            <div className="card-content risk-card">
              <div className={`risk-score-large ${riskColor}`}>
                {applicant.risk_score ?? '—'}
              </div>
              <div className="risk-label">
                Risk Score • {riskBucket !== 'muted' ? riskBucket.charAt(0).toUpperCase() + riskBucket.slice(1) : 'Unknown'} Risk
              </div>
              {applicant.risk_score !== null && applicant.risk_score !== undefined && (
                <div className="risk-bar-large">
                  <div
                    className={`risk-bar-fill ${riskColor}`}
                    style={{ width: `${applicant.risk_score}%` }}
                  />
                </div>
              )}
              <div className="risk-factors">
                {applicant.steps?.some(s => s.status === 'completed' || s.status === 'complete') && (
                  <div className="risk-factor">
                    <span className="risk-factor-indicator" style={{ background: 'var(--success)' }} />
                    Verification steps completed
                  </div>
                )}
                {applicant.flags?.includes('pep') && (
                  <div className="risk-factor">
                    <span className="risk-factor-indicator" style={{ background: 'var(--warning)' }} />
                    PEP match detected
                  </div>
                )}
                {applicant.flags?.includes('sanctions') && (
                  <div className="risk-factor">
                    <span className="risk-factor-indicator" style={{ background: 'var(--danger)' }} />
                    Sanctions match detected
                  </div>
                )}
                {!applicant.flags?.length && (
                  <div className="risk-factor">
                    <span className="risk-factor-indicator" style={{ background: 'var(--success)' }} />
                    No screening flags
                  </div>
                )}
              </div>
            </div>
          </div>

          <div className="card" style={{ marginBottom: 24 }}>
            <div className="card-header">
              <div className="card-title">KYC Steps</div>
            </div>
            <div className="card-content">
              {applicant.steps && applicant.steps.length > 0 ? (
                applicant.steps.map((step, idx) => {
                  const StepIcon = stepIcons[step.name] || stepIcons[step.step_name] || FileText;
                  const isComplete = step.status === 'completed' || step.status === 'complete';
                  return (
                    <div
                      key={idx}
                      style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: 12,
                        padding: '12px 0',
                        borderBottom: idx < applicant.steps.length - 1 ? '1px solid var(--border-color)' : 'none'
                      }}
                    >
                      <div style={{
                        width: 32,
                        height: 32,
                        borderRadius: 8,
                        background: isComplete ? 'rgba(16, 185, 129, 0.15)' : 'var(--bg-tertiary)',
                        color: isComplete ? 'var(--success)' : 'var(--text-muted)',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center'
                      }}>
                        <StepIcon size={16} />
                      </div>
                      <div style={{ flex: 1 }}>
                        <div style={{ fontSize: 14, fontWeight: 500 }}>{step.name || step.step_name}</div>
                        <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>
                          {isComplete ? 'Completed' : step.status}
                        </div>
                      </div>
                      {isComplete && <CheckCircle2 size={16} color="var(--success)" />}
                    </div>
                  );
                })
              ) : (
                <div style={{ color: 'var(--text-muted)', fontSize: 13, textAlign: 'center', padding: 20 }}>
                  No steps configured
                </div>
              )}
            </div>
          </div>

          <div className="card">
            <div className="card-header">
              <div className="card-title">
                <Link2 size={16} />
                Quick Actions
              </div>
            </div>
            <div className="card-content">
              <button className="btn btn-secondary" style={{ width: '100%', marginBottom: 8, justifyContent: 'center' }}>
                <Languages size={16} />
                Translate Documents
              </button>
              <button
                className="btn btn-secondary"
                style={{ width: '100%', marginBottom: 8, justifyContent: 'center' }}
                onClick={handleDownloadEvidence}
                disabled={downloadMutation.isPending}
              >
                {downloadMutation.isPending ? (
                  <Loader2 size={16} className="spinner" />
                ) : (
                  <Download size={16} />
                )}
                Export Evidence Pack
              </button>
              <button className="btn btn-secondary" style={{ width: '100%', justifyContent: 'center' }}>
                <ExternalLink size={16} />
                Open in Case Management
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Confirmation Dialog */}
      <ConfirmDialog
        isOpen={confirmDialog.isOpen}
        title={confirmDialog.action === 'approve' ? 'Approve Applicant' : 'Reject Applicant'}
        message={
          confirmDialog.action === 'approve'
            ? `Are you sure you want to approve ${applicant?.full_name || 'this applicant'}? This will complete their verification process.`
            : `Are you sure you want to reject ${applicant?.full_name || 'this applicant'}? This action cannot be undone.`
        }
        confirmLabel={confirmDialog.action === 'approve' ? 'Approve' : 'Reject'}
        variant={confirmDialog.action === 'approve' ? 'success' : 'danger'}
        isLoading={reviewMutation.isPending}
        onConfirm={executeReviewAction}
        onCancel={() => setConfirmDialog({ isOpen: false, action: null })}
      />
    </div>
  );
}
