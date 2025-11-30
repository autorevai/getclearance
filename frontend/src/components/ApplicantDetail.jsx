import React, { useState } from 'react';
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
  MapPin,
  Mail,
  Phone,
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
  MoreHorizontal,
  Fingerprint,
  Monitor,
  Smartphone
} from 'lucide-react';

const tabs = [
  { id: 'overview', label: 'Overview' },
  { id: 'kyc-steps', label: 'KYC Steps' },
  { id: 'documents', label: 'Documents' },
  { id: 'screening', label: 'Screening' },
  { id: 'activity', label: 'Activity' },
  { id: 'ai-snapshot', label: 'AI Snapshot', ai: true },
  { id: 'linked', label: 'Linked Items' },
];

const mockApplicant = {
  id: '9c5f0e14d3a267b9c1e4f306',
  name: 'Nathan Brooks',
  email: 'n.brooks@globalfin.za',
  phone: '+27 21 555 7890',
  dateOfBirth: '1985-07-22',
  nationality: 'South African',
  country: 'South Africa',
  countryCode: 'ZA',
  address: '45 Waterfront Drive, Cape Town, 8002',
  company: {
    name: 'Sterling Holdings',
    role: 'Chief Financial Officer'
  },
  workflow: 'id-and-liveness',
  workflowVersion: 'v2.0',
  reviewStatus: 'approved',
  riskScore: 45,
  riskBucket: 'medium',
  submittedAt: '2023-10-20T16:39:24Z',
  reviewedAt: '2023-10-20T16:39:24Z',
  reviewer: 'Manual Review',
  platform: 'API',
  deviceInfo: {
    type: 'Desktop',
    os: 'macOS 14.1',
    browser: 'Chrome 119',
    ip: '196.21.xxx.xxx',
    vpn: false,
    proxy: false
  },
  steps: [
    {
      name: 'ID Document',
      status: 'complete',
      icon: FileText,
      completedAt: '2023-10-20T16:35:00Z',
      details: {
        documentType: 'Passport',
        documentNumber: 'M12345678',
        issuingCountry: 'South Africa',
        expiryDate: '2028-05-20',
        ocrConfidence: 98.5
      }
    },
    {
      name: 'Liveness Check',
      status: 'complete',
      icon: Camera,
      completedAt: '2023-10-20T16:38:00Z',
      details: {
        matchScore: 94.2,
        spoofScore: 2.1,
        qualityScore: 97.8
      }
    }
  ],
  documents: [
    {
      id: 'doc-1',
      type: 'Passport',
      fileName: 'passport_front.jpg',
      uploadedAt: '2023-10-20T16:35:00Z',
      status: 'verified',
      ocrExtracted: true,
      thumbnail: '/api/placeholder/300/200'
    },
    {
      id: 'doc-2',
      type: 'Selfie',
      fileName: 'selfie.jpg',
      uploadedAt: '2023-10-20T16:38:00Z',
      status: 'verified',
      thumbnail: '/api/placeholder/300/200'
    }
  ],
  screeningResults: {
    sanctions: {
      status: 'clear',
      lastChecked: '2023-10-20T16:39:00Z',
      listVersion: 'OFAC-2023-10-19',
      hits: []
    },
    pep: {
      status: 'hit',
      lastChecked: '2023-10-20T16:39:00Z',
      hits: [
        {
          source: 'OpenSanctions',
          listId: 'za-peplist-2023',
          confidence: 72,
          matchedFields: ['name', 'date_of_birth', 'nationality'],
          pepTier: 2,
          position: 'CFO of state-owned enterprise subsidiary',
          relationship: 'Direct',
          notes: 'Family member of Tier 1 PEP (spouse is parliamentary official)'
        }
      ]
    },
    adverseMedia: {
      status: 'clear',
      lastChecked: '2023-10-20T16:39:00Z',
      hits: []
    }
  },
  activity: [
    { timestamp: '2023-10-20T16:39:24Z', event: 'Application approved', actor: 'Review Team', type: 'decision' },
    { timestamp: '2023-10-20T16:39:20Z', event: 'PEP hit manually reviewed and cleared', actor: 'Review Team', type: 'review' },
    { timestamp: '2023-10-20T16:39:00Z', event: 'Screening completed - PEP hit detected', actor: 'System', type: 'screening' },
    { timestamp: '2023-10-20T16:38:00Z', event: 'Liveness check passed (94.2% match)', actor: 'System', type: 'verification' },
    { timestamp: '2023-10-20T16:35:00Z', event: 'ID document verified', actor: 'System', type: 'verification' },
    { timestamp: '2023-10-20T16:30:00Z', event: 'Application submitted', actor: 'Applicant', type: 'submission' },
  ],
  aiSnapshot: {
    summary: `This applicant is a 38-year-old South African national working as CFO at Sterling Holdings. The application was flagged due to a **Tier 2 PEP match** - the applicant's spouse holds a position in South African parliament.

**Key Observations:**
- All identity documents verified successfully with high confidence (98.5% OCR, 94.2% face match)
- No sanctions or adverse media findings
- PEP status is indirect (through spouse) and does not indicate elevated financial crime risk
- Employment at a legitimate corporate entity with verifiable registration

**Recommendation:** The PEP flag alone does not warrant rejection. Standard monitoring protocols should apply. Approved for onboarding with annual re-screening cadence.`,
    confidence: 87,
    citations: [
      { type: 'list', source: 'OpenSanctions za-peplist-2023', detail: 'PEP match source' },
      { type: 'list', source: 'OFAC SDN List v2023-10-19', detail: 'Sanctions check (clear)' },
      { type: 'rule', source: 'rule_pep_tier2_review', detail: 'Triggered manual review' }
    ],
    generatedAt: '2023-10-20T16:39:15Z'
  }
};

const statusConfig = {
  approved: { label: 'Approved', color: 'success', icon: CheckCircle2 },
  rejected: { label: 'Rejected', color: 'danger', icon: XCircle },
  in_progress: { label: 'In Progress', color: 'warning', icon: Clock },
  review: { label: 'Review', color: 'info', icon: Clock },
};

const getRiskColor = (bucket) => {
  switch (bucket) {
    case 'low': return 'success';
    case 'medium': return 'warning';
    case 'high': return 'danger';
    default: return 'muted';
  }
};

const formatDateTime = (dateStr) => {
  const date = new Date(dateStr);
  return date.toLocaleString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  });
};

export default function ApplicantDetail({ applicant = mockApplicant, onBack }) {
  const [activeTab, setActiveTab] = useState('overview');
  
  const status = statusConfig[applicant.reviewStatus];
  const StatusIcon = status?.icon;
  const riskColor = getRiskColor(applicant.riskBucket);

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
        
        .btn-secondary {
          background: var(--bg-secondary);
          border: 1px solid var(--border-color);
          color: var(--text-primary);
        }
        
        .btn-secondary:hover {
          background: var(--bg-hover);
        }
        
        .btn-success {
          background: var(--success);
          color: white;
        }
        
        .btn-danger {
          background: var(--danger);
          color: white;
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
        
        @media (max-width: 1200px) {
          .content-grid {
            grid-template-columns: 1fr;
          }
        }
      `}</style>
      
      <div className="detail-header">
        <button className="back-btn" onClick={onBack}>
          <ArrowLeft size={16} />
          Back
        </button>
        
        <div className="header-content">
          <div className="header-top">
            <h1 className="applicant-name">{applicant.name}</h1>
            <span className={`status-badge ${status?.color}`}>
              {StatusIcon && <StatusIcon size={14} />}
              {status?.label}
            </span>
          </div>
          
          <div className="header-meta">
            <span className="header-meta-item">
              <Mail size={14} />
              {applicant.email}
            </span>
            <span className="header-meta-item">
              <Globe size={14} />
              {applicant.country}
            </span>
            <span className="header-meta-item">
              <Calendar size={14} />
              Submitted {formatDateTime(applicant.submittedAt)}
            </span>
            <span className="header-meta-item" style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: 12, color: 'var(--text-muted)' }}>
              ID: {applicant.id}
            </span>
          </div>
        </div>
        
        <div className="header-actions">
          <button className="btn btn-secondary">
            <Download size={16} />
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
          <button className="btn btn-danger">
            <XCircle size={16} />
            Reject
          </button>
          <button className="btn btn-success">
            <CheckCircle2 size={16} />
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
                      <span className="info-value">{applicant.name}</span>
                    </div>
                    <div className="info-item">
                      <span className="info-label">Email</span>
                      <span className="info-value">
                        {applicant.email}
                        <Copy size={12} className="copy-btn" style={{ cursor: 'pointer', color: 'var(--text-muted)' }} />
                      </span>
                    </div>
                    <div className="info-item">
                      <span className="info-label">Phone</span>
                      <span className="info-value">{applicant.phone}</span>
                    </div>
                    <div className="info-item">
                      <span className="info-label">Date of Birth</span>
                      <span className="info-value">{applicant.dateOfBirth}</span>
                    </div>
                    <div className="info-item">
                      <span className="info-label">Nationality</span>
                      <span className="info-value">{applicant.nationality}</span>
                    </div>
                    <div className="info-item">
                      <span className="info-label">Country of Residence</span>
                      <span className="info-value">🇿🇦 {applicant.country}</span>
                    </div>
                    <div className="info-item" style={{ gridColumn: 'span 2' }}>
                      <span className="info-label">Address</span>
                      <span className="info-value">{applicant.address}</span>
                    </div>
                  </div>
                </div>
              </div>
              
              {applicant.company && (
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
                        <span className="info-value">{applicant.company.name}</span>
                      </div>
                      <div className="info-item">
                        <span className="info-label">Role</span>
                        <span className="info-value">{applicant.company.role}</span>
                      </div>
                    </div>
                  </div>
                </div>
              )}
              
              <div className="card">
                <div className="card-header">
                  <div className="card-title">
                    <Fingerprint size={16} />
                    Device & Session Info
                  </div>
                </div>
                <div className="card-content">
                  <div className="device-info">
                    <div className="device-item">
                      <Monitor size={16} className="device-icon" />
                      <span>{applicant.deviceInfo.type} • {applicant.deviceInfo.os}</span>
                    </div>
                    <div className="device-item">
                      <Globe size={16} className="device-icon" />
                      <span>{applicant.deviceInfo.browser}</span>
                    </div>
                    <div className="device-item">
                      <MapPin size={16} className="device-icon" />
                      <span>IP: {applicant.deviceInfo.ip}</span>
                    </div>
                    <div className="device-item">
                      <Shield size={16} className="device-icon" />
                      <span>VPN: {applicant.deviceInfo.vpn ? 'Detected' : 'No'} • Proxy: {applicant.deviceInfo.proxy ? 'Detected' : 'No'}</span>
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
                <div className="screening-item">
                  <div className="screening-header">
                    <span className="screening-type">Sanctions</span>
                    <span className={`screening-status ${applicant.screeningResults.sanctions.status}`}>
                      {applicant.screeningResults.sanctions.status === 'clear' ? <CheckCircle2 size={14} /> : <AlertTriangle size={14} />}
                      {applicant.screeningResults.sanctions.status === 'clear' ? 'Clear' : 'Hit'}
                    </span>
                  </div>
                  <div className="screening-meta">
                    Last checked: {formatDateTime(applicant.screeningResults.sanctions.lastChecked)} • 
                    List version: {applicant.screeningResults.sanctions.listVersion}
                  </div>
                </div>
                
                <div className="screening-item">
                  <div className="screening-header">
                    <span className="screening-type">PEP (Politically Exposed Person)</span>
                    <span className={`screening-status ${applicant.screeningResults.pep.status}`}>
                      {applicant.screeningResults.pep.status === 'clear' ? <CheckCircle2 size={14} /> : <AlertTriangle size={14} />}
                      {applicant.screeningResults.pep.status === 'clear' ? 'Clear' : 'Hit'}
                    </span>
                  </div>
                  <div className="screening-meta">
                    Last checked: {formatDateTime(applicant.screeningResults.pep.lastChecked)}
                  </div>
                  
                  {applicant.screeningResults.pep.hits.map((hit, idx) => (
                    <div key={idx} className="screening-hit">
                      <div className="screening-hit-header">
                        <span className="screening-hit-source">{hit.source}</span>
                        <span style={{ fontSize: 11, background: 'rgba(245, 158, 11, 0.2)', padding: '2px 6px', borderRadius: 4, color: 'var(--warning)' }}>
                          Tier {hit.pepTier}
                        </span>
                        <span className="screening-hit-confidence">{hit.confidence}% match</span>
                      </div>
                      <div className="screening-hit-detail">
                        <strong>Position:</strong> {hit.position}<br />
                        <strong>Relationship:</strong> {hit.relationship}<br />
                        <strong>Notes:</strong> {hit.notes}<br />
                        <strong>Matched fields:</strong> {hit.matchedFields.join(', ')}
                      </div>
                    </div>
                  ))}
                </div>
                
                <div className="screening-item">
                  <div className="screening-header">
                    <span className="screening-type">Adverse Media</span>
                    <span className={`screening-status ${applicant.screeningResults.adverseMedia.status}`}>
                      {applicant.screeningResults.adverseMedia.status === 'clear' ? <CheckCircle2 size={14} /> : <AlertTriangle size={14} />}
                      {applicant.screeningResults.adverseMedia.status === 'clear' ? 'Clear' : 'Hit'}
                    </span>
                  </div>
                  <div className="screening-meta">
                    Last checked: {formatDateTime(applicant.screeningResults.adverseMedia.lastChecked)}
                  </div>
                </div>
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
                <span style={{ fontSize: 12, color: 'var(--text-muted)' }}>
                  Generated {formatDateTime(applicant.aiSnapshot.generatedAt)}
                </span>
              </div>
              <div className="card-content">
                <div className="ai-summary" dangerouslySetInnerHTML={{ 
                  __html: applicant.aiSnapshot.summary
                    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
                    .replace(/\n/g, '<br />') 
                }} />
                
                <div className="ai-confidence">
                  <Sparkles size={14} style={{ color: 'var(--accent-primary)' }} />
                  <span style={{ fontSize: 13 }}>Confidence</span>
                  <div className="ai-confidence-bar">
                    <div 
                      className="ai-confidence-fill" 
                      style={{ width: `${applicant.aiSnapshot.confidence}%` }} 
                    />
                  </div>
                  <span style={{ fontSize: 13, fontWeight: 600 }}>{applicant.aiSnapshot.confidence}%</span>
                </div>
                
                <div className="ai-citations">
                  <div style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-muted)', marginBottom: 12, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                    Citations & Sources
                  </div>
                  {applicant.aiSnapshot.citations.map((citation, idx) => (
                    <div key={idx} className="ai-citation">
                      <span className={`ai-citation-type ${citation.type}`}>{citation.type}</span>
                      <span style={{ flex: 1 }}>{citation.source}</span>
                      <span style={{ color: 'var(--text-muted)' }}>{citation.detail}</span>
                    </div>
                  ))}
                </div>
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
                <div className="timeline">
                  {applicant.activity.map((item, idx) => (
                    <div key={idx} className="timeline-item">
                      <div className={`timeline-dot ${item.type}`}>
                        {item.type === 'decision' && <CheckCircle2 size={14} />}
                        {item.type === 'review' && <User size={14} />}
                        {item.type === 'screening' && <Shield size={14} />}
                        {item.type === 'verification' && <FileText size={14} />}
                        {item.type === 'submission' && <Clock size={14} />}
                      </div>
                      <div className="timeline-content">
                        <div className="timeline-event">{item.event}</div>
                        <div className="timeline-meta">
                          {item.actor} • {formatDateTime(item.timestamp)}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}
        </div>
        
        <div className="side-column">
          <div className="card" style={{ marginBottom: 24 }}>
            <div className="card-content risk-card">
              <div className={`risk-score-large ${riskColor}`}>{applicant.riskScore}</div>
              <div className="risk-label">Risk Score • {applicant.riskBucket.charAt(0).toUpperCase() + applicant.riskBucket.slice(1)} Risk</div>
              <div className="risk-bar-large">
                <div 
                  className={`risk-bar-fill ${riskColor}`}
                  style={{ width: `${applicant.riskScore}%` }}
                />
              </div>
              <div className="risk-factors">
                <div className="risk-factor">
                  <span className="risk-factor-indicator" style={{ background: 'var(--success)' }} />
                  Document verification passed
                </div>
                <div className="risk-factor">
                  <span className="risk-factor-indicator" style={{ background: 'var(--success)' }} />
                  Liveness check passed
                </div>
                <div className="risk-factor">
                  <span className="risk-factor-indicator" style={{ background: 'var(--warning)' }} />
                  PEP Tier 2 match
                </div>
                <div className="risk-factor">
                  <span className="risk-factor-indicator" style={{ background: 'var(--success)' }} />
                  No sanctions matches
                </div>
              </div>
            </div>
          </div>
          
          <div className="card" style={{ marginBottom: 24 }}>
            <div className="card-header">
              <div className="card-title">KYC Steps</div>
            </div>
            <div className="card-content">
              {applicant.steps.map((step, idx) => (
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
                    background: step.status === 'complete' ? 'rgba(16, 185, 129, 0.15)' : 'var(--bg-tertiary)',
                    color: step.status === 'complete' ? 'var(--success)' : 'var(--text-muted)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center'
                  }}>
                    <step.icon size={16} />
                  </div>
                  <div style={{ flex: 1 }}>
                    <div style={{ fontSize: 14, fontWeight: 500 }}>{step.name}</div>
                    <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>
                      {step.status === 'complete' ? 'Completed' : 'Pending'}
                    </div>
                  </div>
                  {step.status === 'complete' && <CheckCircle2 size={16} color="var(--success)" />}
                </div>
              ))}
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
              <button className="btn btn-secondary" style={{ width: '100%', marginBottom: 8, justifyContent: 'center' }}>
                <Download size={16} />
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
    </div>
  );
}
