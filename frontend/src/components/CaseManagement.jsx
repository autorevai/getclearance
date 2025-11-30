import React, { useState } from 'react';
import {
  Search,
  Filter,
  Plus,
  FolderKanban,
  AlertTriangle,
  CheckCircle2,
  Clock,
  User,
  Building2,
  Calendar,
  ChevronDown,
  ExternalLink,
  Download,
  MessageSquare,
  Paperclip,
  Send,
  Sparkles,
  Flag,
  MoreHorizontal,
  ArrowRight,
  FileText,
  Shield,
  Link2
} from 'lucide-react';

const mockCases = [
  {
    id: 'CASE-2025-001',
    title: 'Sanctions Match Investigation - Maria Garcia',
    type: 'sanctions',
    priority: 'high',
    status: 'open',
    assignee: {
      name: 'Sarah Johnson',
      avatar: 'SJ'
    },
    subject: {
      type: 'individual',
      name: 'Maria Garcia',
      id: '69265783fc570e564756417f'
    },
    createdAt: '2025-11-28T08:20:00Z',
    dueAt: '2025-11-29T17:00:00Z',
    lastActivity: '2025-11-28T14:30:00Z',
    source: 'AML Screening',
    notes: 3,
    attachments: 2
  },
  {
    id: 'CASE-2025-002',
    title: 'Document Verification Failure - Ahmed Hassan',
    type: 'verification',
    priority: 'medium',
    status: 'in_progress',
    assignee: {
      name: 'Mike Chen',
      avatar: 'MC'
    },
    subject: {
      type: 'individual',
      name: 'Ahmed Hassan',
      id: '69265783fc570e564756418a'
    },
    createdAt: '2025-11-28T10:25:00Z',
    dueAt: '2025-11-30T17:00:00Z',
    lastActivity: '2025-11-28T12:00:00Z',
    source: 'KYC Review',
    notes: 1,
    attachments: 4
  },
  {
    id: 'CASE-2024-089',
    title: 'PEP Review - Jarryd Peters',
    type: 'pep',
    priority: 'medium',
    status: 'resolved',
    assignee: {
      name: 'Sarah Johnson',
      avatar: 'SJ'
    },
    subject: {
      type: 'individual',
      name: 'Jarryd Peters',
      id: '68a37b69f046cb214d070511'
    },
    createdAt: '2023-10-20T16:39:00Z',
    dueAt: '2023-10-21T17:00:00Z',
    resolvedAt: '2023-10-20T16:39:24Z',
    lastActivity: '2023-10-20T16:39:24Z',
    source: 'AML Screening',
    resolution: 'cleared',
    notes: 5,
    attachments: 3
  },
  {
    id: 'CASE-2024-088',
    title: 'Fraud Detection - Smith Andrew',
    type: 'fraud',
    priority: 'critical',
    status: 'resolved',
    assignee: {
      name: 'AI System',
      avatar: '🤖'
    },
    subject: {
      type: 'individual',
      name: 'Smith Andrew',
      id: '68a37b70f046cb214d070587'
    },
    createdAt: '2023-10-20T16:08:11Z',
    dueAt: '2023-10-20T17:00:00Z',
    resolvedAt: '2023-10-20T16:08:11Z',
    lastActivity: '2023-10-20T16:08:11Z',
    source: 'AI Detection',
    resolution: 'rejected',
    notes: 2,
    attachments: 1
  }
];

const typeConfig = {
  sanctions: { label: 'Sanctions', color: 'danger', icon: Shield },
  pep: { label: 'PEP', color: 'warning', icon: User },
  verification: { label: 'Verification', color: 'info', icon: FileText },
  fraud: { label: 'Fraud', color: 'danger', icon: AlertTriangle },
  aml: { label: 'AML', color: 'warning', icon: Shield }
};

const priorityConfig = {
  critical: { label: 'Critical', color: 'danger' },
  high: { label: 'High', color: 'warning' },
  medium: { label: 'Medium', color: 'info' },
  low: { label: 'Low', color: 'muted' }
};

const statusConfig = {
  open: { label: 'Open', color: 'warning' },
  in_progress: { label: 'In Progress', color: 'info' },
  pending_info: { label: 'Pending Info', color: 'muted' },
  resolved: { label: 'Resolved', color: 'success' },
  escalated: { label: 'Escalated', color: 'danger' }
};

const formatDateTime = (dateStr) => {
  const date = new Date(dateStr);
  return date.toLocaleString('en-US', {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  });
};

const formatRelativeTime = (dateStr) => {
  const date = new Date(dateStr);
  const now = new Date();
  const diffMs = now - date;
  const diffMins = Math.floor(diffMs / (1000 * 60));
  const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
  const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));
  
  if (diffMins < 60) return `${diffMins}m ago`;
  if (diffHours < 24) return `${diffHours}h ago`;
  if (diffDays < 7) return `${diffDays}d ago`;
  return formatDateTime(dateStr);
};

export default function CaseManagement() {
  const [activeFilter, setActiveFilter] = useState('open');
  const [selectedCase, setSelectedCase] = useState(null);
  const [noteText, setNoteText] = useState('');

  const filteredCases = activeFilter === 'all' 
    ? mockCases 
    : mockCases.filter(c => c.status === activeFilter || (activeFilter === 'open' && c.status === 'in_progress'));

  return (
    <div className="case-management">
      <style>{`
        .case-management {
          max-width: 1400px;
        }
        
        .page-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 24px;
        }
        
        .page-title {
          font-size: 28px;
          font-weight: 600;
          letter-spacing: -0.02em;
        }
        
        .page-subtitle {
          color: var(--text-secondary);
          font-size: 14px;
          margin-top: 4px;
        }
        
        .page-actions {
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
        
        /* Kanban Toggle */
        .view-toggle {
          display: flex;
          background: var(--bg-secondary);
          border: 1px solid var(--border-color);
          border-radius: 8px;
          padding: 4px;
        }
        
        .view-toggle-btn {
          padding: 8px 16px;
          border: none;
          background: transparent;
          color: var(--text-secondary);
          font-size: 13px;
          cursor: pointer;
          border-radius: 6px;
          transition: all 0.15s;
        }
        
        .view-toggle-btn.active {
          background: var(--bg-tertiary);
          color: var(--text-primary);
        }
        
        /* Stats Row */
        .stats-row {
          display: grid;
          grid-template-columns: repeat(5, 1fr);
          gap: 16px;
          margin-bottom: 24px;
        }
        
        .stat-card {
          background: var(--bg-secondary);
          border: 1px solid var(--border-color);
          border-radius: 12px;
          padding: 16px 20px;
          cursor: pointer;
          transition: all 0.15s;
        }
        
        .stat-card:hover {
          border-color: var(--accent-primary);
        }
        
        .stat-card.active {
          border-color: var(--accent-primary);
          background: var(--accent-glow);
        }
        
        .stat-label {
          font-size: 13px;
          color: var(--text-secondary);
          margin-bottom: 4px;
        }
        
        .stat-value {
          font-size: 28px;
          font-weight: 700;
          letter-spacing: -0.02em;
        }
        
        .stat-value.warning { color: var(--warning); }
        .stat-value.success { color: var(--success); }
        .stat-value.danger { color: var(--danger); }
        .stat-value.info { color: var(--info); }
        
        /* Cases List */
        .cases-container {
          display: grid;
          grid-template-columns: 1fr 400px;
          gap: 24px;
        }
        
        .cases-list {
          background: var(--bg-secondary);
          border: 1px solid var(--border-color);
          border-radius: 12px;
          overflow: hidden;
        }
        
        .cases-header {
          padding: 16px 20px;
          border-bottom: 1px solid var(--border-color);
          display: flex;
          align-items: center;
          gap: 12px;
        }
        
        .search-wrapper {
          flex: 1;
          position: relative;
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
        
        .search-icon {
          position: absolute;
          left: 12px;
          top: 50%;
          transform: translateY(-50%);
          color: var(--text-muted);
        }
        
        /* Case Item */
        .case-item {
          padding: 16px 20px;
          border-bottom: 1px solid var(--border-color);
          cursor: pointer;
          transition: background 0.15s;
        }
        
        .case-item:last-child {
          border-bottom: none;
        }
        
        .case-item:hover {
          background: var(--bg-hover);
        }
        
        .case-item.selected {
          background: var(--accent-glow);
          border-left: 3px solid var(--accent-primary);
        }
        
        .case-header {
          display: flex;
          align-items: flex-start;
          justify-content: space-between;
          margin-bottom: 8px;
        }
        
        .case-id {
          font-size: 12px;
          color: var(--text-muted);
          font-family: 'JetBrains Mono', monospace;
        }
        
        .case-title {
          font-size: 14px;
          font-weight: 500;
          margin-bottom: 8px;
          line-height: 1.4;
        }
        
        .case-meta {
          display: flex;
          align-items: center;
          gap: 12px;
          flex-wrap: wrap;
        }
        
        .case-badge {
          display: inline-flex;
          align-items: center;
          gap: 4px;
          padding: 3px 8px;
          border-radius: 4px;
          font-size: 11px;
          font-weight: 600;
          text-transform: uppercase;
          letter-spacing: 0.02em;
        }
        
        .case-badge.danger { background: rgba(239, 68, 68, 0.15); color: var(--danger); }
        .case-badge.warning { background: rgba(245, 158, 11, 0.15); color: var(--warning); }
        .case-badge.info { background: rgba(59, 130, 246, 0.15); color: var(--info); }
        .case-badge.success { background: rgba(16, 185, 129, 0.15); color: var(--success); }
        .case-badge.muted { background: var(--bg-tertiary); color: var(--text-muted); }
        
        .case-assignee {
          display: flex;
          align-items: center;
          gap: 6px;
          font-size: 12px;
          color: var(--text-secondary);
        }
        
        .assignee-avatar {
          width: 20px;
          height: 20px;
          border-radius: 50%;
          background: linear-gradient(135deg, var(--accent-primary), #a855f7);
          display: flex;
          align-items: center;
          justify-content: center;
          font-size: 9px;
          font-weight: 600;
          color: white;
        }
        
        .case-time {
          font-size: 12px;
          color: var(--text-muted);
        }
        
        .case-indicators {
          display: flex;
          align-items: center;
          gap: 8px;
          font-size: 12px;
          color: var(--text-muted);
        }
        
        .indicator {
          display: flex;
          align-items: center;
          gap: 4px;
        }
        
        /* Case Detail Panel */
        .case-detail {
          background: var(--bg-secondary);
          border: 1px solid var(--border-color);
          border-radius: 12px;
          display: flex;
          flex-direction: column;
          max-height: calc(100vh - 200px);
        }
        
        .detail-header {
          padding: 20px;
          border-bottom: 1px solid var(--border-color);
        }
        
        .detail-title {
          font-size: 16px;
          font-weight: 600;
          margin-bottom: 12px;
          line-height: 1.4;
        }
        
        .detail-meta {
          display: flex;
          flex-wrap: wrap;
          gap: 8px;
        }
        
        .detail-content {
          flex: 1;
          overflow-y: auto;
          padding: 20px;
        }
        
        .detail-section {
          margin-bottom: 24px;
        }
        
        .section-title {
          font-size: 12px;
          font-weight: 600;
          color: var(--text-muted);
          text-transform: uppercase;
          letter-spacing: 0.05em;
          margin-bottom: 12px;
        }
        
        .subject-card {
          background: var(--bg-tertiary);
          border-radius: 8px;
          padding: 12px;
          display: flex;
          align-items: center;
          gap: 12px;
        }
        
        .subject-icon {
          width: 40px;
          height: 40px;
          border-radius: 8px;
          background: var(--bg-hover);
          display: flex;
          align-items: center;
          justify-content: center;
          color: var(--text-secondary);
        }
        
        .subject-info {
          flex: 1;
        }
        
        .subject-name {
          font-weight: 500;
          font-size: 14px;
        }
        
        .subject-id {
          font-size: 12px;
          color: var(--text-muted);
          font-family: 'JetBrains Mono', monospace;
        }
        
        .subject-link {
          color: var(--accent-primary);
          cursor: pointer;
        }
        
        /* AI Summary */
        .ai-summary {
          background: linear-gradient(135deg, var(--bg-tertiary), rgba(99, 102, 241, 0.05));
          border: 1px solid var(--accent-primary);
          border-radius: 8px;
          padding: 16px;
        }
        
        .ai-summary-header {
          display: flex;
          align-items: center;
          gap: 8px;
          font-weight: 600;
          color: var(--accent-primary);
          margin-bottom: 8px;
          font-size: 13px;
        }
        
        .ai-summary-text {
          font-size: 13px;
          line-height: 1.6;
          color: var(--text-primary);
        }
        
        /* Notes */
        .note-item {
          background: var(--bg-tertiary);
          border-radius: 8px;
          padding: 12px;
          margin-bottom: 8px;
        }
        
        .note-header {
          display: flex;
          align-items: center;
          gap: 8px;
          margin-bottom: 8px;
        }
        
        .note-author {
          font-weight: 500;
          font-size: 13px;
        }
        
        .note-time {
          font-size: 11px;
          color: var(--text-muted);
        }
        
        .note-text {
          font-size: 13px;
          line-height: 1.5;
          color: var(--text-secondary);
        }
        
        /* Note Input */
        .detail-footer {
          padding: 16px 20px;
          border-top: 1px solid var(--border-color);
        }
        
        .note-input-wrapper {
          display: flex;
          gap: 8px;
        }
        
        .note-input {
          flex: 1;
          height: 40px;
          background: var(--bg-tertiary);
          border: 1px solid var(--border-color);
          border-radius: 8px;
          padding: 0 12px;
          font-size: 14px;
          color: var(--text-primary);
          outline: none;
        }
        
        .note-input:focus {
          border-color: var(--accent-primary);
        }
        
        .send-btn {
          width: 40px;
          height: 40px;
          border-radius: 8px;
          border: none;
          background: var(--accent-primary);
          color: white;
          cursor: pointer;
          display: flex;
          align-items: center;
          justify-content: center;
        }
        
        /* Actions */
        .action-buttons {
          display: flex;
          gap: 8px;
          margin-top: 16px;
        }
        
        .action-btn {
          flex: 1;
          padding: 10px;
          border-radius: 8px;
          font-size: 13px;
          font-weight: 500;
          cursor: pointer;
          display: flex;
          align-items: center;
          justify-content: center;
          gap: 6px;
          transition: all 0.15s;
        }
        
        .action-btn.success {
          background: var(--success);
          border: none;
          color: white;
        }
        
        .action-btn.danger {
          background: var(--danger);
          border: none;
          color: white;
        }
        
        .action-btn.secondary {
          background: var(--bg-tertiary);
          border: 1px solid var(--border-color);
          color: var(--text-primary);
        }
        
        .empty-state {
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          height: 100%;
          padding: 40px;
          text-align: center;
          color: var(--text-muted);
        }
        
        .empty-state-icon {
          width: 64px;
          height: 64px;
          border-radius: 16px;
          background: var(--bg-tertiary);
          display: flex;
          align-items: center;
          justify-content: center;
          margin-bottom: 16px;
        }
      `}</style>
      
      <div className="page-header">
        <div>
          <h1 className="page-title">Case Management</h1>
          <p className="page-subtitle">Investigate and resolve compliance cases</p>
        </div>
        
        <div className="page-actions">
          <div className="view-toggle">
            <button className="view-toggle-btn active">List</button>
            <button className="view-toggle-btn">Kanban</button>
          </div>
          <button className="btn btn-secondary">
            <Download size={16} />
            Export
          </button>
          <button className="btn btn-primary">
            <Plus size={16} />
            Create Case
          </button>
        </div>
      </div>
      
      <div className="stats-row">
        <div 
          className={`stat-card ${activeFilter === 'open' ? 'active' : ''}`}
          onClick={() => setActiveFilter('open')}
        >
          <div className="stat-label">Open Cases</div>
          <div className="stat-value warning">2</div>
        </div>
        <div 
          className={`stat-card ${activeFilter === 'in_progress' ? 'active' : ''}`}
          onClick={() => setActiveFilter('in_progress')}
        >
          <div className="stat-label">In Progress</div>
          <div className="stat-value info">1</div>
        </div>
        <div 
          className={`stat-card ${activeFilter === 'resolved' ? 'active' : ''}`}
          onClick={() => setActiveFilter('resolved')}
        >
          <div className="stat-label">Resolved (30d)</div>
          <div className="stat-value success">12</div>
        </div>
        <div 
          className={`stat-card ${activeFilter === 'escalated' ? 'active' : ''}`}
          onClick={() => setActiveFilter('escalated')}
        >
          <div className="stat-label">Escalated</div>
          <div className="stat-value danger">0</div>
        </div>
        <div 
          className={`stat-card ${activeFilter === 'all' ? 'active' : ''}`}
          onClick={() => setActiveFilter('all')}
        >
          <div className="stat-label">All Cases</div>
          <div className="stat-value">{mockCases.length}</div>
        </div>
      </div>
      
      <div className="cases-container">
        <div className="cases-list">
          <div className="cases-header">
            <div className="search-wrapper">
              <Search size={16} className="search-icon" />
              <input 
                type="text" 
                className="search-input" 
                placeholder="Search cases..." 
              />
            </div>
            <button className="btn btn-secondary" style={{ padding: '8px 12px' }}>
              <Filter size={14} />
              Filters
            </button>
          </div>
          
          {filteredCases.map((caseItem) => {
            const type = typeConfig[caseItem.type];
            const priority = priorityConfig[caseItem.priority];
            const status = statusConfig[caseItem.status];
            const TypeIcon = type?.icon;
            
            return (
              <div 
                key={caseItem.id}
                className={`case-item ${selectedCase?.id === caseItem.id ? 'selected' : ''}`}
                onClick={() => setSelectedCase(caseItem)}
              >
                <div className="case-header">
                  <span className="case-id">{caseItem.id}</span>
                  <span className="case-time">{formatRelativeTime(caseItem.lastActivity)}</span>
                </div>
                <div className="case-title">{caseItem.title}</div>
                <div className="case-meta">
                  <span className={`case-badge ${type?.color}`}>
                    {TypeIcon && <TypeIcon size={10} />}
                    {type?.label}
                  </span>
                  <span className={`case-badge ${priority?.color}`}>
                    {priority?.label}
                  </span>
                  <span className={`case-badge ${status?.color}`}>
                    {status?.label}
                  </span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: 12 }}>
                  <div className="case-assignee">
                    <div className="assignee-avatar">{caseItem.assignee.avatar}</div>
                    {caseItem.assignee.name}
                  </div>
                  <div className="case-indicators">
                    <span className="indicator">
                      <MessageSquare size={12} />
                      {caseItem.notes}
                    </span>
                    <span className="indicator">
                      <Paperclip size={12} />
                      {caseItem.attachments}
                    </span>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
        
        <div className="case-detail">
          {selectedCase ? (
            <>
              <div className="detail-header">
                <div className="case-id" style={{ marginBottom: 8 }}>{selectedCase.id}</div>
                <div className="detail-title">{selectedCase.title}</div>
                <div className="detail-meta">
                  <span className={`case-badge ${typeConfig[selectedCase.type]?.color}`}>
                    {typeConfig[selectedCase.type]?.label}
                  </span>
                  <span className={`case-badge ${priorityConfig[selectedCase.priority]?.color}`}>
                    {priorityConfig[selectedCase.priority]?.label}
                  </span>
                  <span className={`case-badge ${statusConfig[selectedCase.status]?.color}`}>
                    {statusConfig[selectedCase.status]?.label}
                  </span>
                </div>
              </div>
              
              <div className="detail-content">
                <div className="detail-section">
                  <div className="section-title">Subject</div>
                  <div className="subject-card">
                    <div className="subject-icon">
                      {selectedCase.subject.type === 'individual' ? <User size={20} /> : <Building2 size={20} />}
                    </div>
                    <div className="subject-info">
                      <div className="subject-name">{selectedCase.subject.name}</div>
                      <div className="subject-id">{selectedCase.subject.id}</div>
                    </div>
                    <ExternalLink size={16} className="subject-link" />
                  </div>
                </div>
                
                <div className="detail-section">
                  <div className="section-title">AI Summary</div>
                  <div className="ai-summary">
                    <div className="ai-summary-header">
                      <Sparkles size={14} />
                      AI Analysis
                    </div>
                    <div className="ai-summary-text">
                      {selectedCase.type === 'sanctions' && 
                        "This case involves a potential OFAC SDN match with 85% confidence. The matched entity shares the same name and country of residence. Recommend verifying identity documents and requesting additional proof of identity before disposition."}
                      {selectedCase.type === 'pep' && 
                        "PEP Tier 2 match identified through spouse relationship. The subject's spouse holds a parliamentary position. Standard EDD completed with no adverse findings. Risk profile indicates low financial crime exposure."}
                      {selectedCase.type === 'verification' && 
                        "Liveness check returned borderline score (82%). Face angle was at the edge of acceptable range. Manual review required to confirm identity match. Document verification passed all other checks."}
                      {selectedCase.type === 'fraud' && 
                        "Document forgery detected with high confidence. Passport image shows evidence of digital manipulation in the MRZ zone. Checksum validation failed. Auto-rejected per policy."}
                    </div>
                  </div>
                </div>
                
                <div className="detail-section">
                  <div className="section-title">Notes ({selectedCase.notes})</div>
                  <div className="note-item">
                    <div className="note-header">
                      <div className="assignee-avatar" style={{ width: 24, height: 24, fontSize: 10 }}>SJ</div>
                      <span className="note-author">Sarah Johnson</span>
                      <span className="note-time">2 hours ago</span>
                    </div>
                    <div className="note-text">
                      Reviewed documentation. Requesting additional proof of address before final disposition.
                    </div>
                  </div>
                  <div className="note-item">
                    <div className="note-header">
                      <div className="assignee-avatar" style={{ width: 24, height: 24, fontSize: 10 }}>🤖</div>
                      <span className="note-author">AI System</span>
                      <span className="note-time">4 hours ago</span>
                    </div>
                    <div className="note-text">
                      Case auto-created from AML screening hit. Confidence threshold exceeded (85%).
                    </div>
                  </div>
                </div>
                
                {selectedCase.status !== 'resolved' && (
                  <div className="action-buttons">
                    <button className="action-btn success">
                      <CheckCircle2 size={14} />
                      Clear
                    </button>
                    <button className="action-btn danger">
                      <Flag size={14} />
                      Escalate
                    </button>
                    <button className="action-btn secondary">
                      <Download size={14} />
                      Export
                    </button>
                  </div>
                )}
              </div>
              
              <div className="detail-footer">
                <div className="note-input-wrapper">
                  <input 
                    type="text" 
                    className="note-input" 
                    placeholder="Add a note..."
                    value={noteText}
                    onChange={(e) => setNoteText(e.target.value)}
                  />
                  <button className="send-btn">
                    <Send size={16} />
                  </button>
                </div>
              </div>
            </>
          ) : (
            <div className="empty-state">
              <div className="empty-state-icon">
                <FolderKanban size={28} />
              </div>
              <div style={{ fontSize: 14, fontWeight: 500, marginBottom: 4 }}>No case selected</div>
              <div style={{ fontSize: 13 }}>Select a case from the list to view details</div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
