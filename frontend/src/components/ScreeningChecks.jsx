import React, { useState, useMemo } from 'react';
import {
  Shield,
  AlertTriangle,
  CheckCircle2,
  User,
  Building2,
  Calendar,
  RefreshCw,
  Sparkles,
  Eye,
  Play,
  Settings,
  Database,
  Loader2,
  XCircle
} from 'lucide-react';
import { useScreeningChecks, useRunScreening, useResolveHit, useHitSuggestion, useScreeningLists } from '../hooks/useScreening';
import { useToast } from '../contexts/ToastContext';

const statusConfig = {
  pending_review: { label: 'Pending Review', color: 'warning' },
  confirmed_clear: { label: 'Confirmed Clear', color: 'success' },
  confirmed_true: { label: 'True Positive', color: 'danger' },
  clear: { label: 'Clear', color: 'success' },
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

// Helper to check if date is today
const isToday = (dateStr) => {
  if (!dateStr) return false;
  const date = new Date(dateStr);
  const today = new Date();
  return date.toDateString() === today.toDateString();
};

// Country code to flag emoji (ISO 3166-1 alpha-2 to regional indicator)
const countryToFlag = (countryCode) => {
  if (!countryCode || countryCode.length !== 2) return '🌍';
  const code = countryCode.toUpperCase();
  const offset = 127397; // Regional indicator symbol offset
  const flag = String.fromCodePoint(...[...code].map(c => c.charCodeAt(0) + offset));
  return flag;
};

// Country code to name mapping for display
const countryCodeToName = {
  US: 'United States', GB: 'United Kingdom', CA: 'Canada', AU: 'Australia',
  DE: 'Germany', FR: 'France', JP: 'Japan', KR: 'South Korea', IN: 'India',
  BR: 'Brazil', MX: 'Mexico', ZA: 'South Africa', AE: 'UAE', SA: 'Saudi Arabia',
  SG: 'Singapore', HK: 'Hong Kong', IL: 'Israel', NL: 'Netherlands', CH: 'Switzerland',
  IE: 'Ireland', RU: 'Russia', CN: 'China', IR: 'Iran', KP: 'North Korea',
  SY: 'Syria', CU: 'Cuba', VE: 'Venezuela', MM: 'Myanmar', BY: 'Belarus',
  UA: 'Ukraine', TR: 'Turkey', EG: 'Egypt', NG: 'Nigeria', PK: 'Pakistan',
};

// AI Suggestion Component for hit detail panel
function HitAISuggestion({ hitId, onResolve, isResolving }) {
  const { data: suggestion, isLoading, error } = useHitSuggestion(hitId);

  if (isLoading) {
    return (
      <div className="ai-review-section" style={{ opacity: 0.7 }}>
        <div className="ai-review-header">
          <Loader2 size={16} className="spinning" />
          Analyzing hit...
        </div>
        <div className="ai-review-text" style={{ color: 'var(--text-muted)' }}>
          AI is reviewing this match against available data...
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="ai-review-section" style={{ borderColor: 'var(--danger)' }}>
        <div className="ai-review-header" style={{ color: 'var(--danger)' }}>
          <XCircle size={16} />
          AI Review Unavailable
        </div>
        <div className="ai-review-text">
          Unable to get AI recommendation. Please review manually.
        </div>
        <div className="ai-actions">
          <button
            className="btn btn-success"
            style={{ flex: 1 }}
            onClick={() => onResolve('confirmed_false')}
            disabled={isResolving}
          >
            {isResolving ? <Loader2 size={14} className="spinning" /> : <CheckCircle2 size={14} />}
            Mark as Clear
          </button>
          <button
            className="btn btn-danger"
            style={{ flex: 1 }}
            onClick={() => onResolve('confirmed_true')}
            disabled={isResolving}
          >
            {isResolving ? <Loader2 size={14} className="spinning" /> : <AlertTriangle size={14} />}
            Confirm Match
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="ai-review-section">
      <div className="ai-review-header">
        <Sparkles size={16} />
        AI Review Recommendation
      </div>
      <div className="ai-review-text">
        {suggestion?.reasoning || 'No AI analysis available for this hit.'}
      </div>
      {suggestion && (
        <div style={{ marginBottom: 16, fontSize: 14 }}>
          Suggested: <strong>{suggestion.suggested_resolution === 'confirmed_false' ? 'Clear (False Positive)' : 'True Match'}</strong>
          {suggestion.confidence && ` (${Math.round(suggestion.confidence * 100)}% confidence)`}
        </div>
      )}
      <div className="ai-actions">
        <button
          className="btn btn-success"
          style={{ flex: 1 }}
          onClick={() => onResolve('confirmed_false')}
          disabled={isResolving}
        >
          {isResolving ? <Loader2 size={14} className="spinning" /> : <CheckCircle2 size={14} />}
          Mark as Clear
        </button>
        <button
          className="btn btn-danger"
          style={{ flex: 1 }}
          onClick={() => onResolve('confirmed_true')}
          disabled={isResolving}
        >
          {isResolving ? <Loader2 size={14} className="spinning" /> : <AlertTriangle size={14} />}
          Confirm Match
        </button>
      </div>
    </div>
  );
}

// Loading Skeleton Component
function ScreeningSkeleton() {
  return (
    <div className="screening-skeleton">
      <div className="skeleton-row" style={{ height: 60, marginBottom: 12 }} />
      <div className="skeleton-row" style={{ height: 60, marginBottom: 12 }} />
      <div className="skeleton-row" style={{ height: 60, marginBottom: 12 }} />
      <div className="skeleton-row" style={{ height: 60, marginBottom: 12 }} />
      <div className="skeleton-row" style={{ height: 60 }} />
    </div>
  );
}

// Error State Component
function ErrorState({ message, onRetry }) {
  return (
    <div className="error-state" style={{
      textAlign: 'center',
      padding: '60px 20px',
      background: 'var(--bg-secondary)',
      borderRadius: 12,
      border: '1px solid var(--border-color)'
    }}>
      <XCircle size={48} style={{ color: 'var(--danger)', marginBottom: 16 }} />
      <h3 style={{ marginBottom: 8 }}>Failed to Load Screening Checks</h3>
      <p style={{ color: 'var(--text-secondary)', marginBottom: 20 }}>{message}</p>
      {onRetry && (
        <button className="btn btn-primary" onClick={onRetry}>
          <RefreshCw size={14} />
          Try Again
        </button>
      )}
    </div>
  );
}

export default function ScreeningChecks() {
  const [activeFilter, setActiveFilter] = useState('all');
  const [showNewCheck, setShowNewCheck] = useState(false);
  const [selectedCheck, setSelectedCheck] = useState(null);
  const toast = useToast();

  // Form state for new check modal
  const [formData, setFormData] = useState({
    entity_type: 'individual',
    name: '',
    country: '',
    date_of_birth: ''
  });

  // Map UI filter to API filter
  const apiFilter = useMemo(() => {
    if (activeFilter === 'hits') return { status: 'hit' };
    if (activeFilter === 'pending') return { status: 'pending_review' };
    return {};
  }, [activeFilter]);

  // Fetch screening checks from API
  const { data, isLoading, error, refetch } = useScreeningChecks(apiFilter);

  // Fetch list sources from API
  const { data: listSourcesData } = useScreeningLists();

  // Mutations
  const runScreeningMutation = useRunScreening();
  const resolveHitMutation = useResolveHit();

  // Calculate stats from real data
  const stats = useMemo(() => {
    const items = data?.items || [];
    return {
      pendingReview: items.filter(c => c.hits?.some(h => h.resolution_status === 'pending')).length,
      totalHits: items.filter(c => c.status === 'hit').length,
      truePositives: items.filter(c => c.hits?.some(h => h.resolution_status === 'confirmed_true')).length,
      checksToday: items.filter(c => isToday(c.started_at || c.created_at)).length,
    };
  }, [data]);

  const checks = data?.items || [];
  const listSources = listSourcesData?.items || [];

  // Handle running a new screening check
  const handleRunCheck = async (e) => {
    e.preventDefault();

    if (!formData.name.trim()) {
      toast.error('Please enter a name to screen');
      return;
    }

    try {
      const result = await runScreeningMutation.mutateAsync({
        name: formData.name,
        country: formData.country || undefined,
        date_of_birth: formData.date_of_birth || undefined,
        check_types: ['sanctions', 'pep']
      });

      setShowNewCheck(false);
      setFormData({ entity_type: 'individual', name: '', country: '', date_of_birth: '' });

      if (result.hit_count > 0) {
        toast.warning(`${result.hit_count} potential match${result.hit_count > 1 ? 'es' : ''} found`);
      } else {
        toast.success('Screening clear - no matches found');
      }
    } catch (err) {
      toast.error(`Screening failed: ${err.message}`);
    }
  };

  // Handle resolving a hit
  const handleResolveHit = async (hitId, resolution) => {
    try {
      await resolveHitMutation.mutateAsync({
        hitId,
        resolution,
        checkId: selectedCheck?.id
      });
      toast.success(`Hit marked as ${resolution === 'confirmed_false' ? 'clear' : 'true match'}`);
      // Refresh the selected check data
      refetch();
    } catch (err) {
      toast.error(`Resolution failed: ${err.message}`);
    }
  };

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

        /* Loading skeleton */
        .screening-skeleton {
          padding: 20px;
        }

        .skeleton-row {
          background: linear-gradient(90deg, var(--bg-tertiary) 0%, var(--bg-secondary) 50%, var(--bg-tertiary) 100%);
          background-size: 200% 100%;
          animation: skeleton-shimmer 1.5s infinite;
          border-radius: 8px;
        }

        @keyframes skeleton-shimmer {
          0% { background-position: 200% 0; }
          100% { background-position: -200% 0; }
        }

        /* Spinning animation for loaders */
        .spinning {
          animation: spin 1s linear infinite;
        }

        @keyframes spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }

        /* Button states */
        .btn:disabled {
          opacity: 0.6;
          cursor: not-allowed;
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
          <div className="stat-value warning">{stats.pendingReview}</div>
        </div>
        <div className="stat-card">
          <div className="stat-label">Total Hits (30d)</div>
          <div className="stat-value">{stats.totalHits}</div>
        </div>
        <div className="stat-card">
          <div className="stat-label">True Positives</div>
          <div className="stat-value danger">{stats.truePositives}</div>
        </div>
        <div className="stat-card">
          <div className="stat-label">Checks Today</div>
          <div className="stat-value success">{stats.checksToday}</div>
        </div>
      </div>

      <div className="filter-tabs">
        <div
          className={`filter-tab ${activeFilter === 'all' ? 'active' : ''}`}
          onClick={() => setActiveFilter('all')}
        >
          All Checks
          <span className="filter-badge">{data?.total || 0}</span>
        </div>
        <div
          className={`filter-tab ${activeFilter === 'hits' ? 'active' : ''}`}
          onClick={() => setActiveFilter('hits')}
        >
          With Hits
          <span className="filter-badge">{stats.totalHits}</span>
        </div>
        <div
          className={`filter-tab ${activeFilter === 'pending' ? 'active' : ''}`}
          onClick={() => setActiveFilter('pending')}
        >
          Pending Review
          <span className="filter-badge">{stats.pendingReview}</span>
        </div>
      </div>
      
      {isLoading ? (
        <div className="table-container" style={{ padding: 20 }}>
          <ScreeningSkeleton />
        </div>
      ) : error ? (
        <ErrorState message={error.message} onRetry={refetch} />
      ) : checks.length === 0 ? (
        <div className="table-container" style={{ padding: '60px 20px', textAlign: 'center' }}>
          <Shield size={48} style={{ color: 'var(--text-muted)', marginBottom: 16 }} />
          <h3 style={{ marginBottom: 8 }}>No Screening Checks Found</h3>
          <p style={{ color: 'var(--text-secondary)', marginBottom: 20 }}>
            {activeFilter === 'all'
              ? 'Run your first screening check to get started.'
              : `No checks match the "${activeFilter}" filter.`}
          </p>
          <button className="btn btn-primary" onClick={() => setShowNewCheck(true)}>
            <Play size={14} />
            Run New Check
          </button>
        </div>
      ) : (
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
              {checks.map((check) => {
                // Determine match status from hits
                const hasUnresolvedHits = check.hits?.some(h => h.resolution_status === 'pending');
                const hasConfirmedTrue = check.hits?.some(h => h.resolution_status === 'confirmed_true');
                const matchStatusKey = hasUnresolvedHits
                  ? 'pending_review'
                  : hasConfirmedTrue
                  ? 'confirmed_true'
                  : check.status === 'hit'
                  ? 'confirmed_clear'
                  : 'clear';
                const matchStatus = statusConfig[matchStatusKey];

                return (
                  <tr key={check.id} onClick={() => setSelectedCheck(check)}>
                    <td>
                      <div className="entity-cell">
                        <div className="entity-icon">
                          {check.entity_type === 'individual' ? <User size={18} /> : <Building2 size={18} />}
                        </div>
                        <div className="entity-info">
                          <span className="entity-name">{check.screened_name}</span>
                          <span className="entity-meta">
                            {countryToFlag(check.screened_country)} {countryCodeToName[check.screened_country] || check.screened_country || 'Unknown'}
                            <span>•</span>
                            {check.entity_type || 'individual'}
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
                      ) : check.status === 'error' ? (
                        <span className="status-badge danger">
                          <XCircle size={12} />
                          Error
                        </span>
                      ) : (
                        <span className="status-badge success">
                          <CheckCircle2 size={12} />
                          Clear
                        </span>
                      )}
                    </td>
                    <td>
                      <div className={`hit-count ${check.hit_count > 0 ? 'has-hits' : 'clear'}`}>
                        {check.hit_count > 0 ? (
                          <>
                            <AlertTriangle size={14} />
                            {check.hit_count} {check.hit_count === 1 ? 'hit' : 'hits'}
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
                      {formatDateTime(check.started_at || check.created_at)}
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
      )}
      
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
        {listSources.length > 0 ? (
          listSources.map((source) => (
            <div key={source.id} className="list-source-row">
              <span className="list-source-name">{source.name}</span>
              <span className="list-source-version">{source.version}</span>
              <span className="list-source-count">{(source.entity_count || source.entityCount || 0).toLocaleString()} entities</span>
            </div>
          ))
        ) : (
          <div className="list-source-row" style={{ color: 'var(--text-muted)', justifyContent: 'center' }}>
            Loading list sources...
          </div>
        )}
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
                    {selectedCheck.entity_type === 'individual' ? <User size={18} /> : <Building2 size={18} />}
                  </div>
                  <div className="entity-info">
                    <span className="entity-name">{selectedCheck.screened_name}</span>
                    <span className="entity-meta">
                      {countryToFlag(selectedCheck.screened_country)} {countryCodeToName[selectedCheck.screened_country] || selectedCheck.screened_country || 'Unknown'}
                    </span>
                  </div>
                </div>
                {selectedCheck.screened_dob && (
                  <div style={{ fontSize: 13, color: 'var(--text-secondary)', marginTop: 8 }}>
                    <Calendar size={14} style={{ marginRight: 6, verticalAlign: 'middle' }} />
                    DOB: {selectedCheck.screened_dob}
                  </div>
                )}
              </div>

              {selectedCheck.hits?.length > 0 && (
                <div className="panel-section">
                  <div className="panel-section-title">Screening Hits ({selectedCheck.hits.length})</div>
                  {selectedCheck.hits.map((hit) => {
                    // Confidence is already a percentage from backend (e.g., 84.36)
                    const confidencePercent = Math.round(hit.confidence || 0);
                    const isResolved = hit.resolution_status !== 'pending';

                    return (
                      <div key={hit.id} className="hit-card">
                        <div className="hit-header">
                          <span className="hit-source">{hit.list_source || hit.hit_type}</span>
                          <div className="hit-confidence">
                            <div className="confidence-bar">
                              <div
                                className={`confidence-fill ${confidencePercent > 80 ? 'high' : confidencePercent > 60 ? 'medium' : 'low'}`}
                                style={{ width: `${confidencePercent}%` }}
                              />
                            </div>
                            <span>{confidencePercent}%</span>
                          </div>
                        </div>
                        <div className="hit-detail">
                          <strong>{hit.matched_name}</strong>
                          {hit.pep_position && ` - ${hit.pep_position}`}
                          {hit.pep_tier && ` (Tier ${hit.pep_tier})`}
                        </div>
                        <div className="hit-meta">List version: {hit.list_version_id}</div>
                        <div className="matched-fields">
                          {(hit.matched_fields || []).map((field, i) => (
                            <span key={i} className="matched-field">{field}</span>
                          ))}
                        </div>
                        {isResolved && (
                          <div style={{ marginTop: 12, paddingTop: 12, borderTop: '1px solid var(--border-color)' }}>
                            <span className={`status-badge ${hit.resolution_status === 'confirmed_false' ? 'success' : 'danger'}`}>
                              {hit.resolution_status === 'confirmed_false' ? 'Cleared' : 'Confirmed Match'}
                            </span>
                            {hit.resolution_notes && (
                              <div style={{ fontSize: 12, color: 'var(--text-secondary)', marginTop: 8 }}>
                                {hit.resolution_notes}
                              </div>
                            )}
                            {hit.resolved_at && (
                              <div className="hit-meta" style={{ marginTop: 4 }}>
                                Resolved: {formatDateTime(hit.resolved_at)}
                              </div>
                            )}
                          </div>
                        )}
                        {!isResolved && (
                          <div style={{ marginTop: 12 }}>
                            <HitAISuggestion
                              hitId={hit.id}
                              onResolve={(resolution) => handleResolveHit(hit.id, resolution)}
                              isResolving={resolveHitMutation.isPending}
                            />
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              )}

              {selectedCheck.hits?.length === 0 && selectedCheck.status === 'clear' && (
                <div className="panel-section">
                  <div style={{
                    textAlign: 'center',
                    padding: '40px 20px',
                    background: 'var(--bg-tertiary)',
                    borderRadius: 8
                  }}>
                    <CheckCircle2 size={48} style={{ color: 'var(--success)', marginBottom: 12 }} />
                    <h4 style={{ marginBottom: 8 }}>No Matches Found</h4>
                    <p style={{ color: 'var(--text-secondary)', fontSize: 14 }}>
                      This entity was screened against all connected list sources with no matches.
                    </p>
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
        <form onSubmit={handleRunCheck}>
          <div className="modal-header">
            <div className="modal-title">Run New Screening Check</div>
          </div>
          <div className="modal-content">
            <div className="form-group">
              <label className="form-label">Entity Type</label>
              <select
                className="form-input"
                style={{ cursor: 'pointer' }}
                value={formData.entity_type}
                onChange={(e) => setFormData(prev => ({ ...prev, entity_type: e.target.value }))}
              >
                <option value="individual">Individual</option>
                <option value="company">Company</option>
              </select>
            </div>
            <div className="form-group">
              <label className="form-label">Full Name *</label>
              <input
                type="text"
                className="form-input"
                placeholder="Enter full name..."
                value={formData.name}
                onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
                required
              />
            </div>
            <div className="form-group">
              <label className="form-label">Country</label>
              <select
                className="form-input"
                style={{ cursor: 'pointer' }}
                value={formData.country}
                onChange={(e) => setFormData(prev => ({ ...prev, country: e.target.value }))}
              >
                <option value="">Select country...</option>
                <optgroup label="High-Risk Jurisdictions">
                  <option value="RU">Russia</option>
                  <option value="CN">China</option>
                  <option value="IR">Iran</option>
                  <option value="KP">North Korea</option>
                  <option value="SY">Syria</option>
                  <option value="CU">Cuba</option>
                  <option value="VE">Venezuela</option>
                  <option value="MM">Myanmar</option>
                  <option value="BY">Belarus</option>
                </optgroup>
                <optgroup label="Common Countries">
                  <option value="US">United States</option>
                  <option value="GB">United Kingdom</option>
                  <option value="CA">Canada</option>
                  <option value="AU">Australia</option>
                  <option value="DE">Germany</option>
                  <option value="FR">France</option>
                  <option value="JP">Japan</option>
                  <option value="KR">South Korea</option>
                  <option value="IN">India</option>
                  <option value="BR">Brazil</option>
                  <option value="MX">Mexico</option>
                  <option value="ZA">South Africa</option>
                  <option value="AE">United Arab Emirates</option>
                  <option value="SA">Saudi Arabia</option>
                  <option value="SG">Singapore</option>
                  <option value="HK">Hong Kong</option>
                  <option value="IL">Israel</option>
                  <option value="NL">Netherlands</option>
                  <option value="CH">Switzerland</option>
                  <option value="IE">Ireland</option>
                </optgroup>
                <optgroup label="Europe">
                  <option value="AT">Austria</option>
                  <option value="BE">Belgium</option>
                  <option value="BG">Bulgaria</option>
                  <option value="HR">Croatia</option>
                  <option value="CY">Cyprus</option>
                  <option value="CZ">Czech Republic</option>
                  <option value="DK">Denmark</option>
                  <option value="EE">Estonia</option>
                  <option value="FI">Finland</option>
                  <option value="GR">Greece</option>
                  <option value="HU">Hungary</option>
                  <option value="IT">Italy</option>
                  <option value="LV">Latvia</option>
                  <option value="LT">Lithuania</option>
                  <option value="LU">Luxembourg</option>
                  <option value="MT">Malta</option>
                  <option value="NO">Norway</option>
                  <option value="PL">Poland</option>
                  <option value="PT">Portugal</option>
                  <option value="RO">Romania</option>
                  <option value="SK">Slovakia</option>
                  <option value="SI">Slovenia</option>
                  <option value="ES">Spain</option>
                  <option value="SE">Sweden</option>
                  <option value="UA">Ukraine</option>
                </optgroup>
                <optgroup label="Americas">
                  <option value="AR">Argentina</option>
                  <option value="CL">Chile</option>
                  <option value="CO">Colombia</option>
                  <option value="CR">Costa Rica</option>
                  <option value="DO">Dominican Republic</option>
                  <option value="EC">Ecuador</option>
                  <option value="GT">Guatemala</option>
                  <option value="PA">Panama</option>
                  <option value="PE">Peru</option>
                  <option value="PR">Puerto Rico</option>
                  <option value="UY">Uruguay</option>
                </optgroup>
                <optgroup label="Asia Pacific">
                  <option value="BD">Bangladesh</option>
                  <option value="ID">Indonesia</option>
                  <option value="MY">Malaysia</option>
                  <option value="NZ">New Zealand</option>
                  <option value="PK">Pakistan</option>
                  <option value="PH">Philippines</option>
                  <option value="TW">Taiwan</option>
                  <option value="TH">Thailand</option>
                  <option value="VN">Vietnam</option>
                </optgroup>
                <optgroup label="Middle East & Africa">
                  <option value="EG">Egypt</option>
                  <option value="JO">Jordan</option>
                  <option value="KW">Kuwait</option>
                  <option value="LB">Lebanon</option>
                  <option value="NG">Nigeria</option>
                  <option value="OM">Oman</option>
                  <option value="QA">Qatar</option>
                  <option value="TR">Turkey</option>
                </optgroup>
              </select>
            </div>
            <div className="form-group">
              <label className="form-label">Date of Birth (optional)</label>
              <input
                type="date"
                className="form-input"
                value={formData.date_of_birth}
                onChange={(e) => setFormData(prev => ({ ...prev, date_of_birth: e.target.value }))}
              />
            </div>
          </div>
          <div className="modal-footer">
            <button
              type="button"
              className="btn btn-secondary"
              onClick={() => {
                setShowNewCheck(false);
                setFormData({ entity_type: 'individual', name: '', country: '', date_of_birth: '' });
              }}
              disabled={runScreeningMutation.isPending}
            >
              Cancel
            </button>
            <button
              type="submit"
              className="btn btn-primary"
              disabled={runScreeningMutation.isPending}
            >
              {runScreeningMutation.isPending ? (
                <>
                  <Loader2 size={14} className="spinning" />
                  Running...
                </>
              ) : (
                <>
                  <Play size={14} />
                  Run Check
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
