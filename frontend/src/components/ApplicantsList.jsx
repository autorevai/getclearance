import React, { useState } from 'react';
import {
  Search,
  Filter,
  Download,
  Plus,
  ChevronDown,
  MoreHorizontal,
  CheckCircle2,
  XCircle,
  Clock,
  AlertTriangle,
  Shield,
  FileText,
  Camera,
  Sparkles,
  ArrowUpDown,
  Eye,
  RefreshCw,
  Users,
  Building2,
  Globe,
  Calendar
} from 'lucide-react';

const mockApplicants = [
  {
    id: '69265783fc570e564756416e',
    name: 'John Mock-Doe',
    email: 'john.mockdoe@email.com',
    country: 'United States',
    countryCode: 'US',
    company: 'TechStart Inc.',
    workflow: 'id-and-liveness',
    workflowVersion: 'v2.1',
    steps: [
      { name: 'ID Document', status: 'complete', icon: FileText },
      { name: 'Liveness', status: 'complete', icon: Camera },
    ],
    reviewStatus: 'approved',
    flags: [],
    riskScore: 12,
    riskBucket: 'low',
    submittedAt: '2025-11-25T13:28:32Z',
    reviewedAt: '2025-11-25T13:28:33Z',
    reviewer: 'Auto-approved',
    slaDue: null,
    platform: 'Web',
    level: 'id-and-liveness',
    aiSummary: 'Clean application. All documents verified. No screening hits.'
  },
  {
    id: '69264dd6077ffd4c31a387ce',
    name: 'John Mock-Doe',
    email: 'john.mockdoe2@email.com',
    country: 'United States',
    countryCode: 'US',
    company: null,
    workflow: 'id-and-liveness',
    workflowVersion: 'v2.1',
    steps: [
      { name: 'ID Document', status: 'complete', icon: FileText },
      { name: 'Liveness', status: 'complete', icon: Camera },
    ],
    reviewStatus: 'approved',
    flags: [],
    riskScore: 18,
    riskBucket: 'low',
    submittedAt: '2025-11-25T19:49:05Z',
    reviewedAt: '2025-11-25T19:49:05Z',
    reviewer: 'Auto-approved',
    slaDue: null,
    platform: 'Web',
    level: 'id-and-liveness',
    aiSummary: 'Clean application. All documents verified. No screening hits.'
  },
  {
    id: '68a37b69f046cb214d070511',
    name: 'Jarryd Peters',
    email: 'jarryd.peters@company.za',
    country: 'South Africa',
    countryCode: 'ZA',
    company: 'Acme Corp',
    workflow: 'id-and-liveness',
    workflowVersion: 'v2.0',
    steps: [
      { name: 'ID Document', status: 'complete', icon: FileText },
      { name: 'Liveness', status: 'complete', icon: Camera },
    ],
    reviewStatus: 'approved',
    flags: ['pep'],
    riskScore: 45,
    riskBucket: 'medium',
    submittedAt: '2023-10-20T16:39:24Z',
    reviewedAt: '2023-10-20T16:39:24Z',
    reviewer: 'Manual Review',
    slaDue: null,
    platform: 'API',
    level: 'id-and-liveness',
    aiSummary: 'PEP match detected (Tier 2). Manually reviewed and cleared.'
  },
  {
    id: '68a37b70f046cb214d070587',
    name: 'Smith Andrew',
    email: 'smith.andrew@suspicious.net',
    country: 'United States',
    countryCode: 'US',
    company: null,
    workflow: 'id-and-liveness',
    workflowVersion: 'v2.0',
    steps: [
      { name: 'ID Document', status: 'failed', icon: FileText },
      { name: 'Liveness', status: 'complete', icon: Camera },
    ],
    reviewStatus: 'rejected',
    flags: ['forgery'],
    riskScore: 92,
    riskBucket: 'high',
    submittedAt: '2023-10-20T16:08:11Z',
    reviewedAt: '2023-10-20T16:08:11Z',
    reviewer: 'AI Detection',
    slaDue: null,
    platform: 'API',
    level: 'id-and-liveness',
    aiSummary: 'Document forgery detected. Passport image shows signs of digital manipulation. MRZ checksum invalid.',
    tag: 'Forgery'
  },
  {
    id: '69265783fc570e564756417f',
    name: 'Maria Garcia',
    email: 'maria.garcia@company.mx',
    country: 'Mexico',
    countryCode: 'MX',
    company: 'FinServe SA',
    workflow: 'enhanced-kyc',
    workflowVersion: 'v3.0',
    steps: [
      { name: 'ID Document', status: 'complete', icon: FileText },
      { name: 'Liveness', status: 'complete', icon: Camera },
      { name: 'Proof of Address', status: 'pending', icon: FileText },
      { name: 'Source of Funds', status: 'pending', icon: FileText },
    ],
    reviewStatus: 'in_progress',
    flags: ['sanctions'],
    riskScore: 78,
    riskBucket: 'high',
    submittedAt: '2025-11-28T08:15:00Z',
    reviewedAt: null,
    reviewer: null,
    slaDue: '2025-11-28T20:15:00Z',
    platform: 'Web',
    level: 'enhanced-kyc',
    aiSummary: 'Potential sanctions match against OFAC SDN (85% confidence). Awaiting additional documentation for EDD.'
  },
  {
    id: '69265783fc570e564756418a',
    name: 'Ahmed Hassan',
    email: 'a.hassan@techfirm.ae',
    country: 'United Arab Emirates',
    countryCode: 'AE',
    company: 'Tech Innovations FZ-LLC',
    workflow: 'id-and-liveness',
    workflowVersion: 'v2.1',
    steps: [
      { name: 'ID Document', status: 'complete', icon: FileText },
      { name: 'Liveness', status: 'review', icon: Camera },
    ],
    reviewStatus: 'review',
    flags: [],
    riskScore: 35,
    riskBucket: 'medium',
    submittedAt: '2025-11-28T10:22:00Z',
    reviewedAt: null,
    reviewer: null,
    slaDue: '2025-11-28T22:22:00Z',
    platform: 'Mobile',
    level: 'id-and-liveness',
    aiSummary: 'Liveness check requires manual review. Photo quality acceptable but face angle at boundary threshold.'
  }
];

const statusConfig = {
  approved: { label: 'Approved', color: 'success', icon: CheckCircle2 },
  rejected: { label: 'Rejected', color: 'danger', icon: XCircle },
  in_progress: { label: 'In Progress', color: 'warning', icon: Clock },
  review: { label: 'Review', color: 'info', icon: Eye },
  pending: { label: 'Pending', color: 'muted', icon: Clock },
};

const flagConfig = {
  pep: { label: 'PEP', color: 'warning' },
  sanctions: { label: 'Sanctions', color: 'danger' },
  adverse: { label: 'Adverse Media', color: 'info' },
  forgery: { label: 'Forgery', color: 'danger' },
};

const getRiskColor = (bucket) => {
  switch (bucket) {
    case 'low': return 'success';
    case 'medium': return 'warning';
    case 'high': return 'danger';
    default: return 'muted';
  }
};

const formatDate = (dateStr) => {
  if (!dateStr) return '—';
  const date = new Date(dateStr);
  const now = new Date();
  const diffMs = now - date;
  const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));
  
  if (diffDays === 0) {
    const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
    if (diffHours === 0) {
      const diffMins = Math.floor(diffMs / (1000 * 60));
      return `${diffMins} min ago`;
    }
    return `${diffHours}h ago`;
  } else if (diffDays === 1) {
    return 'Yesterday';
  } else if (diffDays < 7) {
    return `${diffDays} days ago`;
  }
  
  return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
};

const countryFlags = {
  US: '🇺🇸',
  ZA: '🇿🇦',
  MX: '🇲🇽',
  AE: '🇦🇪',
  GB: '🇬🇧',
};

export default function ApplicantsList({ onSelectApplicant }) {
  const [selectedIds, setSelectedIds] = useState([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [showAIPanel, setShowAIPanel] = useState(false);
  
  const toggleSelect = (id) => {
    setSelectedIds(prev => 
      prev.includes(id) ? prev.filter(i => i !== id) : [...prev, id]
    );
  };
  
  const toggleSelectAll = () => {
    setSelectedIds(prev => 
      prev.length === mockApplicants.length ? [] : mockApplicants.map(a => a.id)
    );
  };

  return (
    <div className="applicants-list">
      <style>{`
        .applicants-list {
          height: 100%;
        }
        
        .list-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 24px;
        }
        
        .list-title {
          font-size: 28px;
          font-weight: 600;
          letter-spacing: -0.02em;
        }
        
        .list-subtitle {
          color: var(--text-secondary);
          font-size: 14px;
          margin-top: 4px;
        }
        
        .list-actions {
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
        
        .btn-primary {
          background: var(--accent-primary);
          color: white;
        }
        
        .btn-primary:hover {
          opacity: 0.9;
        }
        
        .btn-ai {
          background: linear-gradient(135deg, var(--accent-primary), #a855f7);
          color: white;
        }
        
        /* Toolbar */
        .toolbar {
          background: var(--bg-secondary);
          border: 1px solid var(--border-color);
          border-radius: 12px 12px 0 0;
          padding: 16px 20px;
          display: flex;
          align-items: center;
          gap: 12px;
        }
        
        .search-wrapper {
          position: relative;
          flex: 1;
          max-width: 320px;
        }
        
        .search-input {
          width: 100%;
          height: 40px;
          background: var(--bg-tertiary);
          border: 1px solid var(--border-color);
          border-radius: 8px;
          padding: 0 12px 0 40px;
          font-size: 14px;
          color: var(--text-primary);
          outline: none;
        }
        
        .search-input:focus {
          border-color: var(--accent-primary);
        }
        
        .search-input::placeholder {
          color: var(--text-muted);
        }
        
        .search-icon {
          position: absolute;
          left: 12px;
          top: 50%;
          transform: translateY(-50%);
          color: var(--text-muted);
        }
        
        .filter-chip {
          display: flex;
          align-items: center;
          gap: 6px;
          padding: 8px 12px;
          background: var(--bg-tertiary);
          border: 1px solid var(--border-color);
          border-radius: 8px;
          font-size: 13px;
          color: var(--text-secondary);
          cursor: pointer;
          transition: all 0.15s;
        }
        
        .filter-chip:hover {
          background: var(--bg-hover);
          color: var(--text-primary);
        }
        
        .filter-chip.active {
          background: var(--accent-glow);
          border-color: var(--accent-primary);
          color: var(--accent-primary);
        }
        
        .toolbar-divider {
          width: 1px;
          height: 24px;
          background: var(--border-color);
          margin: 0 8px;
        }
        
        /* Table */
        .table-container {
          background: var(--bg-secondary);
          border: 1px solid var(--border-color);
          border-top: none;
          border-radius: 0 0 12px 12px;
          overflow: hidden;
        }
        
        .table {
          width: 100%;
          border-collapse: collapse;
        }
        
        .table th {
          text-align: left;
          padding: 12px 16px;
          font-size: 12px;
          font-weight: 600;
          color: var(--text-muted);
          text-transform: uppercase;
          letter-spacing: 0.05em;
          background: var(--bg-tertiary);
          border-bottom: 1px solid var(--border-color);
        }
        
        .table th.sortable {
          cursor: pointer;
        }
        
        .table th.sortable:hover {
          color: var(--text-primary);
        }
        
        .th-content {
          display: flex;
          align-items: center;
          gap: 4px;
        }
        
        .table td {
          padding: 16px;
          border-bottom: 1px solid var(--border-color);
          font-size: 14px;
          vertical-align: middle;
        }
        
        .table tr:last-child td {
          border-bottom: none;
        }
        
        .table tr:hover {
          background: var(--bg-hover);
        }
        
        .table tr.selected {
          background: var(--accent-glow);
        }
        
        /* Checkbox */
        .checkbox {
          width: 18px;
          height: 18px;
          border: 2px solid var(--border-color);
          border-radius: 4px;
          cursor: pointer;
          display: flex;
          align-items: center;
          justify-content: center;
          transition: all 0.15s;
        }
        
        .checkbox:hover {
          border-color: var(--accent-primary);
        }
        
        .checkbox.checked {
          background: var(--accent-primary);
          border-color: var(--accent-primary);
        }
        
        /* Applicant Cell */
        .applicant-cell {
          display: flex;
          flex-direction: column;
          gap: 2px;
        }
        
        .applicant-name {
          font-weight: 500;
          color: var(--text-primary);
          cursor: pointer;
        }
        
        .applicant-name:hover {
          color: var(--accent-primary);
          text-decoration: underline;
        }
        
        .applicant-id {
          font-size: 12px;
          color: var(--text-muted);
          font-family: 'JetBrains Mono', monospace;
        }
        
        .applicant-meta {
          display: flex;
          align-items: center;
          gap: 8px;
          font-size: 12px;
          color: var(--text-secondary);
          margin-top: 4px;
        }
        
        /* Steps */
        .steps-cell {
          display: flex;
          gap: 6px;
        }
        
        .step-badge {
          width: 28px;
          height: 28px;
          border-radius: 6px;
          display: flex;
          align-items: center;
          justify-content: center;
          position: relative;
        }
        
        .step-badge.complete {
          background: rgba(16, 185, 129, 0.15);
          color: var(--success);
        }
        
        .step-badge.failed {
          background: rgba(239, 68, 68, 0.15);
          color: var(--danger);
        }
        
        .step-badge.pending {
          background: var(--bg-tertiary);
          color: var(--text-muted);
        }
        
        .step-badge.review {
          background: rgba(59, 130, 246, 0.15);
          color: var(--info);
        }
        
        /* Status Badge */
        .status-badge {
          display: inline-flex;
          align-items: center;
          gap: 6px;
          padding: 4px 10px;
          border-radius: 20px;
          font-size: 12px;
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
        
        .status-badge.info {
          background: rgba(59, 130, 246, 0.15);
          color: var(--info);
        }
        
        .status-badge.muted {
          background: var(--bg-tertiary);
          color: var(--text-muted);
        }
        
        /* Flags */
        .flags-cell {
          display: flex;
          gap: 6px;
        }
        
        .flag-badge {
          padding: 2px 8px;
          border-radius: 4px;
          font-size: 11px;
          font-weight: 600;
          text-transform: uppercase;
          letter-spacing: 0.02em;
        }
        
        .flag-badge.warning {
          background: rgba(245, 158, 11, 0.15);
          color: var(--warning);
        }
        
        .flag-badge.danger {
          background: rgba(239, 68, 68, 0.15);
          color: var(--danger);
        }
        
        .flag-badge.info {
          background: rgba(59, 130, 246, 0.15);
          color: var(--info);
        }
        
        /* Risk Score */
        .risk-cell {
          display: flex;
          align-items: center;
          gap: 8px;
        }
        
        .risk-score {
          font-weight: 600;
          font-size: 14px;
        }
        
        .risk-score.success { color: var(--success); }
        .risk-score.warning { color: var(--warning); }
        .risk-score.danger { color: var(--danger); }
        
        .risk-bar {
          width: 40px;
          height: 4px;
          background: var(--bg-tertiary);
          border-radius: 2px;
          overflow: hidden;
        }
        
        .risk-bar-fill {
          height: 100%;
          border-radius: 2px;
        }
        
        .risk-bar-fill.success { background: var(--success); }
        .risk-bar-fill.warning { background: var(--warning); }
        .risk-bar-fill.danger { background: var(--danger); }
        
        /* Actions */
        .actions-cell {
          display: flex;
          gap: 8px;
        }
        
        .action-btn {
          width: 32px;
          height: 32px;
          border-radius: 6px;
          border: none;
          background: transparent;
          color: var(--text-muted);
          cursor: pointer;
          display: flex;
          align-items: center;
          justify-content: center;
          transition: all 0.15s;
        }
        
        .action-btn:hover {
          background: var(--bg-hover);
          color: var(--text-primary);
        }
        
        /* AI Summary Tooltip */
        .ai-summary-trigger {
          display: flex;
          align-items: center;
          gap: 4px;
          font-size: 12px;
          color: var(--accent-primary);
          cursor: pointer;
          margin-top: 4px;
        }
        
        .ai-summary-trigger:hover {
          text-decoration: underline;
        }
        
        /* Batch Actions Bar */
        .batch-actions {
          position: fixed;
          bottom: 24px;
          left: 50%;
          transform: translateX(-50%);
          background: var(--bg-secondary);
          border: 1px solid var(--border-color);
          border-radius: 12px;
          padding: 12px 20px;
          display: flex;
          align-items: center;
          gap: 16px;
          box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
          z-index: 100;
        }
        
        .batch-count {
          font-size: 14px;
          font-weight: 500;
        }
        
        .batch-divider {
          width: 1px;
          height: 24px;
          background: var(--border-color);
        }
        
        /* Pagination */
        .pagination {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 16px 20px;
          background: var(--bg-secondary);
          border-top: 1px solid var(--border-color);
        }
        
        .pagination-info {
          font-size: 13px;
          color: var(--text-secondary);
        }
        
        .pagination-controls {
          display: flex;
          gap: 8px;
        }
        
        .page-btn {
          width: 32px;
          height: 32px;
          border-radius: 6px;
          border: 1px solid var(--border-color);
          background: transparent;
          color: var(--text-secondary);
          cursor: pointer;
          display: flex;
          align-items: center;
          justify-content: center;
          transition: all 0.15s;
        }
        
        .page-btn:hover {
          background: var(--bg-hover);
        }
        
        .page-btn.active {
          background: var(--accent-primary);
          border-color: var(--accent-primary);
          color: white;
        }
      `}</style>
      
      <div className="list-header">
        <div>
          <h1 className="list-title">Applicants</h1>
          <p className="list-subtitle">Manage and review individual KYC applications</p>
        </div>
        
        <div className="list-actions">
          <button className="btn btn-secondary">
            <Download size={16} />
            Export CSV
          </button>
          <button className="btn btn-ai">
            <Sparkles size={16} />
            AI Batch Review
          </button>
          <button className="btn btn-primary">
            <Plus size={16} />
            Create Applicant
          </button>
        </div>
      </div>
      
      <div className="toolbar">
        <div className="search-wrapper">
          <Search size={16} className="search-icon" />
          <input
            type="text"
            className="search-input"
            placeholder="Search by name, ID, email..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
        </div>
        
        <div className="toolbar-divider" />
        
        <button className="filter-chip active">
          All Time
          <ChevronDown size={14} />
        </button>
        
        <button className="filter-chip">
          <Filter size={14} />
          Review Status
          <ChevronDown size={14} />
        </button>
        
        <button className="filter-chip">
          <Shield size={14} />
          Flags
          <ChevronDown size={14} />
        </button>
        
        <button className="filter-chip">
          <Globe size={14} />
          Country
          <ChevronDown size={14} />
        </button>
        
        <button className="filter-chip">
          + Add Filter
        </button>
        
        <div style={{ marginLeft: 'auto' }}>
          <button className="filter-chip">
            <RefreshCw size={14} />
          </button>
        </div>
      </div>
      
      <div className="table-container">
        <table className="table">
          <thead>
            <tr>
              <th style={{ width: 48 }}>
                <div 
                  className={`checkbox ${selectedIds.length === mockApplicants.length ? 'checked' : ''}`}
                  onClick={toggleSelectAll}
                >
                  {selectedIds.length === mockApplicants.length && <CheckCircle2 size={12} color="white" />}
                </div>
              </th>
              <th className="sortable">
                <div className="th-content">
                  Applicant
                  <ArrowUpDown size={12} />
                </div>
              </th>
              <th>Steps</th>
              <th className="sortable">
                <div className="th-content">
                  Status
                  <ArrowUpDown size={12} />
                </div>
              </th>
              <th>Flags</th>
              <th className="sortable">
                <div className="th-content">
                  Risk
                  <ArrowUpDown size={12} />
                </div>
              </th>
              <th className="sortable">
                <div className="th-content">
                  Submitted
                  <ArrowUpDown size={12} />
                </div>
              </th>
              <th>Reviewer</th>
              <th style={{ width: 80 }}></th>
            </tr>
          </thead>
          <tbody>
            {mockApplicants.map((applicant) => {
              const status = statusConfig[applicant.reviewStatus];
              const StatusIcon = status?.icon;
              const riskColor = getRiskColor(applicant.riskBucket);
              
              return (
                <tr 
                  key={applicant.id}
                  className={selectedIds.includes(applicant.id) ? 'selected' : ''}
                >
                  <td>
                    <div 
                      className={`checkbox ${selectedIds.includes(applicant.id) ? 'checked' : ''}`}
                      onClick={() => toggleSelect(applicant.id)}
                    >
                      {selectedIds.includes(applicant.id) && <CheckCircle2 size={12} color="white" />}
                    </div>
                  </td>
                  <td>
                    <div className="applicant-cell">
                      <span 
                        className="applicant-name"
                        onClick={() => onSelectApplicant?.(applicant)}
                      >
                        {applicant.name}
                      </span>
                      <span className="applicant-id">ID: {applicant.id.slice(0, 12)}...</span>
                      <div className="applicant-meta">
                        <span>{countryFlags[applicant.countryCode]} {applicant.country}</span>
                        <span>•</span>
                        <span>{applicant.platform}</span>
                        {applicant.company && (
                          <>
                            <span>•</span>
                            <span><Building2 size={12} style={{ display: 'inline', verticalAlign: 'middle' }} /> {applicant.company}</span>
                          </>
                        )}
                      </div>
                      <div className="ai-summary-trigger">
                        <Sparkles size={12} />
                        View AI Summary
                      </div>
                    </div>
                  </td>
                  <td>
                    <div className="steps-cell">
                      {applicant.steps.map((step, idx) => (
                        <div 
                          key={idx} 
                          className={`step-badge ${step.status}`}
                          title={`${step.name}: ${step.status}`}
                        >
                          <step.icon size={14} />
                        </div>
                      ))}
                    </div>
                  </td>
                  <td>
                    <span className={`status-badge ${status?.color}`}>
                      {StatusIcon && <StatusIcon size={12} />}
                      {status?.label}
                    </span>
                  </td>
                  <td>
                    <div className="flags-cell">
                      {applicant.flags.length === 0 ? (
                        <span style={{ color: 'var(--text-muted)', fontSize: 13 }}>—</span>
                      ) : (
                        applicant.flags.map((flag, idx) => {
                          const flagInfo = flagConfig[flag];
                          return (
                            <span key={idx} className={`flag-badge ${flagInfo?.color}`}>
                              {flagInfo?.label}
                            </span>
                          );
                        })
                      )}
                    </div>
                  </td>
                  <td>
                    <div className="risk-cell">
                      <span className={`risk-score ${riskColor}`}>{applicant.riskScore}</span>
                      <div className="risk-bar">
                        <div 
                          className={`risk-bar-fill ${riskColor}`}
                          style={{ width: `${applicant.riskScore}%` }}
                        />
                      </div>
                    </div>
                  </td>
                  <td>
                    <span style={{ color: 'var(--text-secondary)', fontSize: 13 }}>
                      {formatDate(applicant.submittedAt)}
                    </span>
                  </td>
                  <td>
                    <span style={{ color: 'var(--text-secondary)', fontSize: 13 }}>
                      {applicant.reviewer || '—'}
                    </span>
                  </td>
                  <td>
                    <div className="actions-cell">
                      <button className="action-btn" title="View Details">
                        <Eye size={16} />
                      </button>
                      <button className="action-btn" title="More Actions">
                        <MoreHorizontal size={16} />
                      </button>
                    </div>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
        
        <div className="pagination">
          <span className="pagination-info">
            Showing 1-6 of 6 applicants
          </span>
          <div className="pagination-controls">
            <button className="page-btn active">1</button>
          </div>
        </div>
      </div>
      
      {selectedIds.length > 0 && (
        <div className="batch-actions">
          <span className="batch-count">{selectedIds.length} selected</span>
          <div className="batch-divider" />
          <button className="btn btn-secondary" style={{ padding: '8px 12px' }}>
            <CheckCircle2 size={14} />
            Approve
          </button>
          <button className="btn btn-secondary" style={{ padding: '8px 12px' }}>
            <XCircle size={14} />
            Reject
          </button>
          <button className="btn btn-secondary" style={{ padding: '8px 12px' }}>
            <RefreshCw size={14} />
            Request Resubmission
          </button>
          <button className="btn btn-ai" style={{ padding: '8px 12px' }}>
            <Sparkles size={14} />
            AI Review All
          </button>
        </div>
      )}
    </div>
  );
}
