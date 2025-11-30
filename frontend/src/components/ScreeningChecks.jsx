import React, { useState } from 'react';
import {
  Search,
  Filter,
  Shield,
  AlertTriangle,
  CheckCircle2,
  Clock,
  User,
  Building2,
  Globe,
  Calendar,
  ChevronDown,
  ExternalLink,
  RefreshCw,
  Sparkles,
  Eye,
  MoreHorizontal,
  ArrowUpDown,
  Download,
  Play,
  Settings,
  Database
} from 'lucide-react';

const mockChecks = [
  {
    id: 'chk-001',
    entity: {
      type: 'individual',
      name: 'Maria Garcia',
      country: 'Mexico',
      countryCode: 'MX'
    },
    status: 'hit',
    matchStatus: 'pending_review',
    createdAt: '2025-11-28T08:15:00Z',
    hitCount: 2,
    hits: [
      {
        source: 'OFAC SDN',
        listVersion: 'OFAC-2025-11-27',
        confidence: 85,
        matchedFields: ['name', 'country'],
        details: 'Potential name match with Maria Elena Garcia on OFAC SDN list'
      },
      {
        source: 'EU Sanctions',
        listVersion: 'EU-2025-11-25',
        confidence: 62,
        matchedFields: ['name'],
        details: 'Partial name match - different middle name'
      }
    ]
  },
  {
    id: 'chk-002',
    entity: {
      type: 'individual',
      name: 'John Mock-Doe',
      country: 'United States',
      countryCode: 'US'
    },
    status: 'clear',
    matchStatus: 'clear',
    createdAt: '2025-11-25T13:28:32Z',
    hitCount: 0,
    hits: []
  },
  {
    id: 'chk-003',
    entity: {
      type: 'company',
      name: 'Acme Corp',
      country: 'South Africa',
      countryCode: 'ZA'
    },
    status: 'clear',
    matchStatus: 'clear',
    createdAt: '2025-11-24T10:00:00Z',
    hitCount: 0,
    hits: []
  },
  {
    id: 'chk-004',
    entity: {
      type: 'individual',
      name: 'Jarryd Peters',
      country: 'South Africa',
      countryCode: 'ZA'
    },
    status: 'hit',
    matchStatus: 'confirmed_clear',
    createdAt: '2023-10-20T16:39:00Z',
    hitCount: 1,
    hits: [
      {
        source: 'OpenSanctions PEP',
        listVersion: 'OS-PEP-2023-10-19',
        confidence: 72,
        matchedFields: ['name', 'date_of_birth', 'nationality'],
        details: 'PEP Tier 2 - Spouse of parliamentary official'
      }
    ],
    resolution: {
      status: 'cleared',
      reason: 'Indirect PEP relationship, low financial crime risk',
      reviewer: 'Sarah Johnson',
      resolvedAt: '2023-10-20T16:39:20Z'
    }
  },
  {
    id: 'chk-005',
    entity: {
      type: 'individual',
      name: 'Smith Andrew',
      country: 'United States',
      countryCode: 'US'
    },
    status: 'hit',
    matchStatus: 'confirmed_true',
    createdAt: '2023-10-20T16:08:11Z',
    hitCount: 1,
    hits: [
      {
        source: 'Internal Blocklist',
        listVersion: 'INT-2023-10-01',
        confidence: 100,
        matchedFields: ['document_number', 'name'],
        details: 'Previously rejected for document forgery'
      }
    ],
    resolution: {
      status: 'confirmed',
      reason: 'Known fraudulent actor',
      reviewer: 'AI Detection',
      resolvedAt: '2023-10-20T16:08:11Z'
    }
  }
];

const mockListSources = [
  { id: 'ofac', name: 'OFAC SDN', version: 'OFAC-2025-11-27', lastUpdated: '2025-11-27T00:00:00Z', entityCount: 12847 },
  { id: 'eu', name: 'EU Consolidated', version: 'EU-2025-11-25', lastUpdated: '2025-11-25T00:00:00Z', entityCount: 2156 },
  { id: 'un', name: 'UN Security Council', version: 'UN-2025-11-20', lastUpdated: '2025-11-20T00:00:00Z', entityCount: 892 },
  { id: 'uk', name: 'UK Sanctions', version: 'UK-2025-11-26', lastUpdated: '2025-11-26T00:00:00Z', entityCount: 3421 },
  { id: 'opensanctions', name: 'OpenSanctions', version: 'OS-2025-11-27', lastUpdated: '2025-11-27T06:00:00Z', entityCount: 89234 },
];

const statusConfig = {
  pending_review: { label: 'Pending Review', color: 'warning' },
  confirmed_clear: { label: 'Confirmed Clear', color: 'success' },
  confirmed_true: { label: 'True Positive', color: 'danger' },
  clear: { label: 'Clear', color: 'success' },
};

const countryFlags = {
  US: '🇺🇸',
  ZA: '🇿🇦',
  MX: '🇲🇽',
  AE: '🇦🇪',
  GB: '🇬🇧',
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

export default function ScreeningChecks() {
  const [activeFilter, setActiveFilter] = useState('all');
  const [showNewCheck, setShowNewCheck] = useState(false);
  const [searchName, setSearchName] = useState('');
  const [selectedCheck, setSelectedCheck] = useState(null);

  const filteredChecks = activeFilter === 'all' 
    ? mockChecks 
    : activeFilter === 'hits'
    ? mockChecks.filter(c => c.status === 'hit')
    : mockChecks.filter(c => c.matchStatus === 'pending_review');

  return (
    <div className="screening-checks">
      <style>{`
        .screening-checks {
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
        
        .btn-primary:hover {
          opacity: 0.9;
        }
        
        /* Stats Row */
        .stats-row {
          display: grid;
          grid-template-columns: repeat(4, 1fr);
          gap: 16px;
          margin-bottom: 24px;
        }
        
        .stat-card {
          background: var(--bg-secondary);
          border: 1px solid var(--border-color);
          border-radius: 12px;
          padding: 20px;
        }
        
        .stat-label {
          font-size: 13px;
          color: var(--text-secondary);
          margin-bottom: 8px;
        }
        
        .stat-value {
          font-size: 32px;
          font-weight: 700;
          letter-spacing: -0.02em;
        }
        
        .stat-value.warning { color: var(--warning); }
        .stat-value.success { color: var(--success); }
        .stat-value.danger { color: var(--danger); }
        
        /* Filter Tabs */
        .filter-tabs {
          display: flex;
          gap: 4px;
          background: var(--bg-secondary);
          border: 1px solid var(--border-color);
          border-radius: 12px 12px 0 0;
          padding: 16px 20px;
        }
        
        .filter-tab {
          padding: 8px 16px;
          border-radius: 8px;
          font-size: 14px;
          font-weight: 500;
          color: var(--text-secondary);
          cursor: pointer;
          transition: all 0.15s;
          display: flex;
          align-items: center;
          gap: 8px;
        }
        
        .filter-tab:hover {
          background: var(--bg-hover);
          color: var(--text-primary);
        }
        
        .filter-tab.active {
          background: var(--accent-glow);
          color: var(--accent-primary);
        }
        
        .filter-badge {
          background: var(--bg-tertiary);
          padding: 2px 8px;
          border-radius: 10px;
          font-size: 12px;
        }
        
        .filter-tab.active .filter-badge {
          background: var(--accent-primary);
          color: white;
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
        
        .table td {
          padding: 16px;
          border-bottom: 1px solid var(--border-color);
          font-size: 14px;
        }
        
        .table tr:last-child td {
          border-bottom: none;
        }
        
        .table tr:hover {
          background: var(--bg-hover);
          cursor: pointer;
        }
        
        /* Entity Cell */
        .entity-cell {
          display: flex;
          align-items: center;
          gap: 12px;
        }
        
        .entity-icon {
          width: 36px;
          height: 36px;
          border-radius: 8px;
          background: var(--bg-tertiary);
          display: flex;
          align-items: center;
          justify-content: center;
          color: var(--text-secondary);
        }
        
        .entity-info {
          display: flex;
          flex-direction: column;
        }
        
        .entity-name {
          font-weight: 500;
        }
        
        .entity-meta {
          font-size: 12px;
          color: var(--text-muted);
          display: flex;
          align-items: center;
          gap: 6px;
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
        
        .status-badge.warning {
          background: rgba(245, 158, 11, 0.15);
          color: var(--warning);
        }
        
        .status-badge.danger {
          background: rgba(239, 68, 68, 0.15);
          color: var(--danger);
        }
        
        /* Hit Count */
        .hit-count {
          display: flex;
          align-items: center;
          gap: 6px;
        }
        
        .hit-count.has-hits {
          color: var(--warning);
        }
        
        .hit-count.clear {
          color: var(--success);
        }
        
        /* Sidebar Panel */
        .check-detail-panel {
          position: fixed;
          right: 0;
          top: 0;
          bottom: 0;
          width: 480px;
          background: var(--bg-secondary);
          border-left: 1px solid var(--border-color);
          z-index: 200;
          overflow-y: auto;
          transform: translateX(${selectedCheck ? '0' : '100%'});
          transition: transform 0.3s ease;
        }
        
        .panel-overlay {
          position: fixed;
          inset: 0;
          background: rgba(0, 0, 0, 0.5);
          z-index: 150;
          opacity: ${selectedCheck ? 1 : 0};
          pointer-events: ${selectedCheck ? 'auto' : 'none'};
          transition: opacity 0.3s;
        }
        
        .panel-header {
          padding: 20px;
          border-bottom: 1px solid var(--border-color);
          display: flex;
          align-items: center;
          justify-content: space-between;
          position: sticky;
          top: 0;
          background: var(--bg-secondary);
          z-index: 10;
        }
        
        .panel-title {
          font-size: 18px;
          font-weight: 600;
        }
        
        .panel-close {
          width: 32px;
          height: 32px;
          border-radius: 8px;
          border: none;
          background: var(--bg-tertiary);
          color: var(--text-secondary);
          cursor: pointer;
          display: flex;
          align-items: center;
          justify-content: center;
        }
        
        .panel-content {
          padding: 20px;
        }
        
        .panel-section {
          margin-bottom: 24px;
        }
        
        .panel-section-title {
          font-size: 12px;
          font-weight: 600;
          color: var(--text-muted);
          text-transform: uppercase;
          letter-spacing: 0.05em;
          margin-bottom: 12px;
        }
        
        .hit-card {
          background: var(--bg-tertiary);
          border-radius: 8px;
          padding: 16px;
          margin-bottom: 12px;
        }
        
        .hit-header {
          display: flex;
          align-items: center;
          justify-content: space-between;
          margin-bottom: 12px;
        }
        
        .hit-source {
          font-weight: 600;
          font-size: 14px;
        }
        
        .hit-confidence {
          display: flex;
          align-items: center;
          gap: 6px;
          font-size: 13px;
        }
        
        .confidence-bar {
          width: 60px;
          height: 6px;
          background: var(--border-color);
          border-radius: 3px;
          overflow: hidden;
        }
        
        .confidence-fill {
          height: 100%;
          border-radius: 3px;
        }
        
        .confidence-fill.high { background: var(--danger); }
        .confidence-fill.medium { background: var(--warning); }
        .confidence-fill.low { background: var(--success); }
        
        .hit-detail {
          font-size: 13px;
          color: var(--text-secondary);
          line-height: 1.5;
          margin-bottom: 12px;
        }
        
        .hit-meta {
          font-size: 12px;
          color: var(--text-muted);
        }
        
        .matched-fields {
          display: flex;
          gap: 6px;
          flex-wrap: wrap;
          margin-top: 8px;
        }
        
        .matched-field {
          padding: 2px 8px;
          background: rgba(99, 102, 241, 0.15);
          color: var(--accent-primary);
          border-radius: 4px;
          font-size: 11px;
          font-weight: 500;
        }
        
        /* AI Review Section */
        .ai-review-section {
          background: linear-gradient(135deg, var(--bg-tertiary), rgba(99, 102, 241, 0.05));
          border: 1px solid var(--accent-primary);
          border-radius: 12px;
          padding: 16px;
        }
        
        .ai-review-header {
          display: flex;
          align-items: center;
          gap: 8px;
          margin-bottom: 12px;
          font-weight: 600;
          color: var(--accent-primary);
        }
        
        .ai-review-text {
          font-size: 14px;
          line-height: 1.6;
          color: var(--text-primary);
          margin-bottom: 16px;
        }
        
        .ai-actions {
          display: flex;
          gap: 8px;
        }
        
        /* List Sources Card */
        .list-sources-card {
          background: var(--bg-secondary);
          border: 1px solid var(--border-color);
          border-radius: 12px;
          margin-top: 24px;
        }
        
        .list-sources-header {
          padding: 16px 20px;
          border-bottom: 1px solid var(--border-color);
          display: flex;
          align-items: center;
          justify-content: space-between;
        }
        
        .list-sources-title {
          font-size: 15px;
          font-weight: 600;
          display: flex;
          align-items: center;
          gap: 8px;
        }
        
        .list-source-row {
          display: flex;
          align-items: center;
          padding: 12px 20px;
          border-bottom: 1px solid var(--border-color);
        }
        
        .list-source-row:last-child {
          border-bottom: none;
        }
        
        .list-source-name {
          flex: 1;
          font-weight: 500;
          font-size: 14px;
        }
        
        .list-source-version {
          font-size: 12px;
          color: var(--text-muted);
          font-family: 'JetBrains Mono', monospace;
          margin-right: 16px;
        }
        
        .list-source-count {
          font-size: 13px;
          color: var(--text-secondary);
        }
        
        /* New Check Modal */
        .new-check-modal {
          position: fixed;
          top: 50%;
          left: 50%;
          transform: translate(-50%, -50%);
          background: var(--bg-secondary);
          border: 1px solid var(--border-color);
          border-radius: 16px;
          width: 500px;
          z-index: 300;
          display: ${showNewCheck ? 'block' : 'none'};
        }
        
        .modal-overlay {
          position: fixed;
          inset: 0;
          background: rgba(0, 0, 0, 0.5);
          z-index: 250;
          display: ${showNewCheck ? 'block' : 'none'};
        }
        
        .modal-header {
          padding: 20px;
          border-bottom: 1px solid var(--border-color);
        }
        
        .modal-title {
          font-size: 18px;
          font-weight: 600;
        }
        
        .modal-content {
          padding: 20px;
        }
        
        .form-group {
          margin-bottom: 20px;
        }
        
        .form-label {
          display: block;
          font-size: 13px;
          font-weight: 500;
          margin-bottom: 8px;
        }
        
        .form-input {
          width: 100%;
          height: 44px;
          background: var(--bg-tertiary);
          border: 1px solid var(--border-color);
          border-radius: 8px;
          padding: 0 14px;
          font-size: 14px;
          color: var(--text-primary);
          outline: none;
        }
        
        .form-input:focus {
          border-color: var(--accent-primary);
        }
        
        .modal-footer {
          padding: 16px 20px;
          border-top: 1px solid var(--border-color);
          display: flex;
          justify-content: flex-end;
          gap: 12px;
        }
      `}</style>
      
      <div className="page-header">
        <div>
          <h1 className="page-title">AML Screening</h1>
          <p className="page-subtitle">Sanctions, PEP, and adverse media screening checks</p>
        </div>
        
        <div className="page-actions">
          <button className="btn btn-secondary">
            <Settings size={16} />
            Monitoring Settings
          </button>
          <button className="btn btn-primary" onClick={() => setShowNewCheck(true)}>
            <Play size={16} />
            Run New Check
          </button>
        </div>
      </div>
      
      <div className="stats-row">
        <div className="stat-card">
          <div className="stat-label">Pending Review</div>
          <div className="stat-value warning">1</div>
        </div>
        <div className="stat-card">
          <div className="stat-label">Total Hits (30d)</div>
          <div className="stat-value">15</div>
        </div>
        <div className="stat-card">
          <div className="stat-label">True Positives</div>
          <div className="stat-value danger">3</div>
        </div>
        <div className="stat-card">
          <div className="stat-label">Checks Today</div>
          <div className="stat-value success">47</div>
        </div>
      </div>
      
      <div className="filter-tabs">
        <div 
          className={`filter-tab ${activeFilter === 'all' ? 'active' : ''}`}
          onClick={() => setActiveFilter('all')}
        >
          All Checks
          <span className="filter-badge">{mockChecks.length}</span>
        </div>
        <div 
          className={`filter-tab ${activeFilter === 'hits' ? 'active' : ''}`}
          onClick={() => setActiveFilter('hits')}
        >
          With Hits
          <span className="filter-badge">{mockChecks.filter(c => c.status === 'hit').length}</span>
        </div>
        <div 
          className={`filter-tab ${activeFilter === 'pending' ? 'active' : ''}`}
          onClick={() => setActiveFilter('pending')}
        >
          Pending Review
          <span className="filter-badge">{mockChecks.filter(c => c.matchStatus === 'pending_review').length}</span>
        </div>
      </div>
      
      <div className="table-container">
        <table className="table">
          <thead>
            <tr>
              <th>Entity</th>
              <th>Check Status</th>
              <th>Hits</th>
              <th>Match Status</th>
              <th>Created</th>
              <th style={{ width: 80 }}></th>
            </tr>
          </thead>
          <tbody>
            {filteredChecks.map((check) => {
              const matchStatus = statusConfig[check.matchStatus];
              
              return (
                <tr key={check.id} onClick={() => setSelectedCheck(check)}>
                  <td>
                    <div className="entity-cell">
                      <div className="entity-icon">
                        {check.entity.type === 'individual' ? <User size={18} /> : <Building2 size={18} />}
                      </div>
                      <div className="entity-info">
                        <span className="entity-name">{check.entity.name}</span>
                        <span className="entity-meta">
                          {countryFlags[check.entity.countryCode]} {check.entity.country}
                          <span>•</span>
                          {check.entity.type}
                        </span>
                      </div>
                    </div>
                  </td>
                  <td>
                    {check.status === 'hit' ? (
                      <span className="status-badge warning">
                        <AlertTriangle size={12} />
                        Hit
                      </span>
                    ) : (
                      <span className="status-badge success">
                        <CheckCircle2 size={12} />
                        Clear
                      </span>
                    )}
                  </td>
                  <td>
                    <div className={`hit-count ${check.hitCount > 0 ? 'has-hits' : 'clear'}`}>
                      {check.hitCount > 0 ? (
                        <>
                          <AlertTriangle size={14} />
                          {check.hitCount} {check.hitCount === 1 ? 'hit' : 'hits'}
                        </>
                      ) : (
                        <>
                          <CheckCircle2 size={14} />
                          No hits
                        </>
                      )}
                    </div>
                  </td>
                  <td>
                    <span className={`status-badge ${matchStatus?.color}`}>
                      {matchStatus?.label}
                    </span>
                  </td>
                  <td style={{ color: 'var(--text-secondary)', fontSize: 13 }}>
                    {formatDateTime(check.createdAt)}
                  </td>
                  <td>
                    <button style={{
                      width: 32,
                      height: 32,
                      border: 'none',
                      background: 'transparent',
                      color: 'var(--text-muted)',
                      cursor: 'pointer',
                      borderRadius: 6
                    }}>
                      <Eye size={16} />
                    </button>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
      
      <div className="list-sources-card">
        <div className="list-sources-header">
          <div className="list-sources-title">
            <Database size={16} />
            Connected List Sources
          </div>
          <button className="btn btn-secondary" style={{ padding: '6px 12px', fontSize: 13 }}>
            <RefreshCw size={14} />
            Sync All
          </button>
        </div>
        {mockListSources.map((source) => (
          <div key={source.id} className="list-source-row">
            <span className="list-source-name">{source.name}</span>
            <span className="list-source-version">{source.version}</span>
            <span className="list-source-count">{source.entityCount.toLocaleString()} entities</span>
          </div>
        ))}
      </div>
      
      {/* Detail Panel */}
      <div className="panel-overlay" onClick={() => setSelectedCheck(null)} />
      <div className="check-detail-panel">
        {selectedCheck && (
          <>
            <div className="panel-header">
              <span className="panel-title">Check Details</span>
              <button className="panel-close" onClick={() => setSelectedCheck(null)}>×</button>
            </div>
            <div className="panel-content">
              <div className="panel-section">
                <div className="panel-section-title">Entity</div>
                <div className="entity-cell" style={{ marginBottom: 16 }}>
                  <div className="entity-icon">
                    {selectedCheck.entity.type === 'individual' ? <User size={18} /> : <Building2 size={18} />}
                  </div>
                  <div className="entity-info">
                    <span className="entity-name">{selectedCheck.entity.name}</span>
                    <span className="entity-meta">
                      {countryFlags[selectedCheck.entity.countryCode]} {selectedCheck.entity.country}
                    </span>
                  </div>
                </div>
              </div>
              
              {selectedCheck.hits.length > 0 && (
                <div className="panel-section">
                  <div className="panel-section-title">Screening Hits ({selectedCheck.hits.length})</div>
                  {selectedCheck.hits.map((hit, idx) => (
                    <div key={idx} className="hit-card">
                      <div className="hit-header">
                        <span className="hit-source">{hit.source}</span>
                        <div className="hit-confidence">
                          <div className="confidence-bar">
                            <div 
                              className={`confidence-fill ${hit.confidence > 80 ? 'high' : hit.confidence > 60 ? 'medium' : 'low'}`}
                              style={{ width: `${hit.confidence}%` }}
                            />
                          </div>
                          <span>{hit.confidence}%</span>
                        </div>
                      </div>
                      <div className="hit-detail">{hit.details}</div>
                      <div className="hit-meta">List version: {hit.listVersion}</div>
                      <div className="matched-fields">
                        {hit.matchedFields.map((field, i) => (
                          <span key={i} className="matched-field">{field}</span>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              )}
              
              {selectedCheck.matchStatus === 'pending_review' && (
                <div className="panel-section">
                  <div className="ai-review-section">
                    <div className="ai-review-header">
                      <Sparkles size={16} />
                      AI Review Recommendation
                    </div>
                    <div className="ai-review-text">
                      Based on the match confidence (85%) and matched fields, this appears to be a potential <strong>true positive</strong>. 
                      The name "Maria Garcia" has a high overlap with the OFAC entry. Recommend requesting additional documentation 
                      (proof of identity, source of funds) before making a final determination.
                    </div>
                    <div className="ai-actions">
                      <button className="btn btn-success" style={{ flex: 1 }}>
                        <CheckCircle2 size={14} />
                        Mark as Clear
                      </button>
                      <button className="btn btn-danger" style={{ flex: 1 }}>
                        <AlertTriangle size={14} />
                        Confirm Match
                      </button>
                    </div>
                  </div>
                </div>
              )}
              
              {selectedCheck.resolution && (
                <div className="panel-section">
                  <div className="panel-section-title">Resolution</div>
                  <div className="hit-card">
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
                      <span className={`status-badge ${selectedCheck.resolution.status === 'cleared' ? 'success' : 'danger'}`}>
                        {selectedCheck.resolution.status === 'cleared' ? 'Cleared' : 'Confirmed'}
                      </span>
                    </div>
                    <div style={{ fontSize: 14, marginBottom: 8 }}>{selectedCheck.resolution.reason}</div>
                    <div className="hit-meta">
                      {selectedCheck.resolution.reviewer} • {formatDateTime(selectedCheck.resolution.resolvedAt)}
                    </div>
                  </div>
                </div>
              )}
            </div>
          </>
        )}
      </div>
      
      {/* New Check Modal */}
      <div className="modal-overlay" onClick={() => setShowNewCheck(false)} />
      <div className="new-check-modal">
        <div className="modal-header">
          <div className="modal-title">Run New Screening Check</div>
        </div>
        <div className="modal-content">
          <div className="form-group">
            <label className="form-label">Entity Type</label>
            <select className="form-input" style={{ cursor: 'pointer' }}>
              <option>Individual</option>
              <option>Company</option>
            </select>
          </div>
          <div className="form-group">
            <label className="form-label">Full Name</label>
            <input 
              type="text" 
              className="form-input" 
              placeholder="Enter full name..."
              value={searchName}
              onChange={(e) => setSearchName(e.target.value)}
            />
          </div>
          <div className="form-group">
            <label className="form-label">Country</label>
            <select className="form-input" style={{ cursor: 'pointer' }}>
              <option>Select country...</option>
              <option>United States</option>
              <option>United Kingdom</option>
              <option>Mexico</option>
              <option>South Africa</option>
            </select>
          </div>
          <div className="form-group">
            <label className="form-label">Date of Birth (optional)</label>
            <input type="date" className="form-input" />
          </div>
        </div>
        <div className="modal-footer">
          <button className="btn btn-secondary" onClick={() => setShowNewCheck(false)}>
            Cancel
          </button>
          <button className="btn btn-primary">
            <Play size={14} />
            Run Check
          </button>
        </div>
      </div>
    </div>
  );
}
