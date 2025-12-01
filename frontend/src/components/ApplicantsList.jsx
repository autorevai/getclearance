import React, { useState, useEffect, useRef, useCallback } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
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
  Shield,
  FileText,
  Camera,
  Sparkles,
  ArrowUpDown,
  Eye,
  RefreshCw,
  Users,
  Building2,
  ChevronLeft,
  ChevronRight,
  X,
  Loader2
} from 'lucide-react';
import { useApplicants, useBatchReviewApplicants } from '../hooks/useApplicants';
import { useDebounce } from '../hooks/useDebounce';
import { useClickOutside } from '../hooks/useClickOutside';
import { useKeyboardShortcut } from '../hooks/useKeyboardShortcut';
import { useToast } from '../contexts/ToastContext';
import { ApplicantsTableSkeleton } from './shared/LoadingSkeleton';
import { ErrorState } from './shared/ErrorState';
import { ConfirmDialog } from './shared';
import CreateApplicantModal from './CreateApplicantModal';

const statusConfig = {
  approved: { label: 'Approved', color: 'success', icon: CheckCircle2 },
  rejected: { label: 'Rejected', color: 'danger', icon: XCircle },
  pending: { label: 'Pending', color: 'muted', icon: Clock },
  in_progress: { label: 'In Progress', color: 'warning', icon: Clock },
  review: { label: 'Review', color: 'info', icon: Eye },
  init: { label: 'New', color: 'muted', icon: Clock },
};

const flagConfig = {
  pep: { label: 'PEP', color: 'warning' },
  sanctions: { label: 'Sanctions', color: 'danger' },
  adverse: { label: 'Adverse Media', color: 'info' },
  adverse_media: { label: 'Adverse Media', color: 'info' },
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

const getRiskBucket = (score) => {
  if (score === null || score === undefined) return 'muted';
  if (score < 30) return 'low';
  if (score < 70) return 'medium';
  return 'high';
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

export default function ApplicantsList() {
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();
  const toast = useToast();
  const searchInputRef = useRef(null);
  const statusDropdownRef = useRef(null);
  const riskDropdownRef = useRef(null);

  // Local search state (for immediate UI feedback)
  const [searchInput, setSearchInput] = useState(searchParams.get('search') || '');
  const debouncedSearch = useDebounce(searchInput, 300);

  // Initialize filters from URL params
  const [filters, setFilters] = useState({
    status: searchParams.get('status') || null,
    risk_level: searchParams.get('risk_level') || null,
    search: searchParams.get('search') || '',
    limit: parseInt(searchParams.get('limit') || '50', 10),
    offset: parseInt(searchParams.get('offset') || '0', 10),
  });

  const [selectedIds, setSelectedIds] = useState([]);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [activeDropdown, setActiveDropdown] = useState(null);
  const [confirmDialog, setConfirmDialog] = useState({ isOpen: false, action: null });

  // Update filters when debounced search changes
  useEffect(() => {
    setFilters(prev => ({
      ...prev,
      search: debouncedSearch,
      offset: 0,
    }));
  }, [debouncedSearch]);

  // Fetch applicants with current filters
  const { data, isLoading, error, refetch, isFetching } = useApplicants(filters);

  // Batch review mutation
  const batchReviewMutation = useBatchReviewApplicants();

  // Sync filters to URL params
  useEffect(() => {
    const params = new URLSearchParams();
    if (filters.status) params.set('status', filters.status);
    if (filters.risk_level) params.set('risk_level', filters.risk_level);
    if (filters.search) params.set('search', filters.search);
    if (filters.offset > 0) params.set('offset', filters.offset.toString());
    if (filters.limit !== 50) params.set('limit', filters.limit.toString());
    setSearchParams(params, { replace: true });
  }, [filters, setSearchParams]);

  // Click outside handlers for dropdowns
  const closeDropdowns = useCallback(() => setActiveDropdown(null), []);
  useClickOutside(statusDropdownRef, closeDropdowns, activeDropdown === 'status');
  useClickOutside(riskDropdownRef, closeDropdowns, activeDropdown === 'risk');

  // Keyboard shortcuts
  useKeyboardShortcut(['meta', 'k'], () => searchInputRef.current?.focus());
  useKeyboardShortcut(['ctrl', 'k'], () => searchInputRef.current?.focus());
  useKeyboardShortcut('Escape', closeDropdowns, { enabled: !!activeDropdown });

  const applicants = data?.items || [];
  const total = data?.total || 0;
  const currentPage = Math.floor(filters.offset / filters.limit) + 1;
  const totalPages = Math.ceil(total / filters.limit) || 1;

  const updateFilter = (key, value) => {
    setFilters(prev => ({
      ...prev,
      [key]: value,
      offset: 0,
    }));
  };

  const handlePageChange = (newPage) => {
    setFilters(prev => ({
      ...prev,
      offset: (newPage - 1) * prev.limit,
    }));
  };

  const toggleSelect = (id) => {
    setSelectedIds(prev =>
      prev.includes(id) ? prev.filter(i => i !== id) : [...prev, id]
    );
  };

  const toggleSelectAll = () => {
    setSelectedIds(prev =>
      prev.length === applicants.length ? [] : applicants.map(a => a.id)
    );
  };

  const handleRowClick = (applicant) => {
    navigate(`/applicants/${applicant.id}`);
  };

  const handleBatchApprove = () => {
    setConfirmDialog({
      isOpen: true,
      action: 'approve',
      title: 'Approve Selected Applicants',
      message: `Are you sure you want to approve ${selectedIds.length} applicant${selectedIds.length > 1 ? 's' : ''}? This will mark them as verified.`,
    });
  };

  const handleBatchReject = () => {
    setConfirmDialog({
      isOpen: true,
      action: 'reject',
      title: 'Reject Selected Applicants',
      message: `Are you sure you want to reject ${selectedIds.length} applicant${selectedIds.length > 1 ? 's' : ''}? This action cannot be undone.`,
    });
  };

  const executeBatchAction = async () => {
    const action = confirmDialog.action;
    setConfirmDialog({ isOpen: false, action: null });

    try {
      const result = await batchReviewMutation.mutateAsync({
        ids: selectedIds,
        decision: action,
        notes: `Batch ${action}d via dashboard`,
      });

      if (result.failed === 0) {
        toast.success(`Successfully ${action}d ${result.succeeded} applicant${result.succeeded > 1 ? 's' : ''}`);
      } else {
        toast.warning(`${action === 'approve' ? 'Approved' : 'Rejected'} ${result.succeeded} of ${result.total} applicants. ${result.failed} failed.`);
      }

      setSelectedIds([]);
    } catch (err) {
      toast.error(`Failed to ${action} applicants: ${err.message}`);
    }
  };

  const handleCreateSuccess = () => {
    setShowCreateModal(false);
    toast.success('Applicant created successfully');
    refetch();
  };

  if (error) {
    return (
      <ErrorState
        title="Failed to load applicants"
        message="We couldn't load the applicants list. Please check your connection and try again."
        error={error}
        onRetry={refetch}
      />
    );
  }

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

        .btn-primary {
          background: var(--accent-primary);
          color: white;
        }

        .btn-primary:hover:not(:disabled) {
          opacity: 0.9;
        }

        .btn-ai {
          background: linear-gradient(135deg, var(--accent-primary), #a855f7);
          color: white;
        }

        .btn-success {
          background: var(--success);
          color: white;
        }

        .btn-danger {
          background: var(--danger);
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

        .search-shortcut {
          position: absolute;
          right: 12px;
          top: 50%;
          transform: translateY(-50%);
          font-size: 11px;
          color: var(--text-muted);
          background: var(--bg-secondary);
          padding: 2px 6px;
          border-radius: 4px;
          border: 1px solid var(--border-color);
        }

        .filter-wrapper {
          position: relative;
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

        .filter-dropdown {
          position: absolute;
          top: 100%;
          left: 0;
          margin-top: 4px;
          background: var(--bg-secondary);
          border: 1px solid var(--border-color);
          border-radius: 8px;
          padding: 8px;
          min-width: 180px;
          z-index: 100;
          box-shadow: 0 8px 24px rgba(0, 0, 0, 0.2);
        }

        .filter-option {
          display: flex;
          align-items: center;
          gap: 8px;
          padding: 8px 12px;
          border-radius: 6px;
          cursor: pointer;
          font-size: 13px;
          color: var(--text-secondary);
        }

        .filter-option:hover {
          background: var(--bg-hover);
          color: var(--text-primary);
        }

        .filter-option.active {
          background: var(--accent-glow);
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

        .table tbody tr {
          cursor: pointer;
        }

        .table tbody tr:hover {
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
        }

        .step-badge.complete, .step-badge.completed {
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

        .step-badge.review, .step-badge.in_progress {
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
        .risk-score.muted { color: var(--text-muted); }

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
          align-items: center;
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

        .page-btn:hover:not(:disabled) {
          background: var(--bg-hover);
        }

        .page-btn:disabled {
          opacity: 0.5;
          cursor: not-allowed;
        }

        .page-btn.active {
          background: var(--accent-primary);
          border-color: var(--accent-primary);
          color: white;
        }

        .empty-state {
          padding: 60px 40px;
          text-align: center;
          color: var(--text-muted);
        }

        .empty-state h3 {
          color: var(--text-primary);
          margin-bottom: 8px;
        }

        @keyframes spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }

        .spinner {
          animation: spin 1s linear infinite;
        }
      `}</style>

      <div className="list-header">
        <div>
          <h1 className="list-title">Applicants</h1>
          <p className="list-subtitle">Manage and review individual KYC applications</p>
        </div>

        <div className="list-actions">
          <button className="btn btn-secondary" aria-label="Export applicants to CSV">
            <Download size={16} />
            Export CSV
          </button>
          <button className="btn btn-ai" aria-label="Run AI batch review on applicants">
            <Sparkles size={16} />
            AI Batch Review
          </button>
          <button
            className="btn btn-primary"
            onClick={() => setShowCreateModal(true)}
            aria-label="Create new applicant"
          >
            <Plus size={16} />
            Create Applicant
          </button>
        </div>
      </div>

      <div className="toolbar">
        <div className="search-wrapper">
          <Search size={16} className="search-icon" aria-hidden="true" />
          <input
            ref={searchInputRef}
            type="text"
            className="search-input"
            placeholder="Search by name, ID, email..."
            value={searchInput}
            onChange={(e) => setSearchInput(e.target.value)}
            aria-label="Search applicants"
          />
          <span className="search-shortcut" aria-hidden="true">⌘K</span>
        </div>

        <div className="toolbar-divider" />

        {/* Status Filter */}
        <div className="filter-wrapper" ref={statusDropdownRef}>
          <button
            className={`filter-chip ${filters.status ? 'active' : ''}`}
            onClick={() => setActiveDropdown(activeDropdown === 'status' ? null : 'status')}
            aria-expanded={activeDropdown === 'status'}
            aria-haspopup="listbox"
            aria-label="Filter by review status"
          >
            <Filter size={14} aria-hidden="true" />
            {filters.status ? statusConfig[filters.status]?.label || filters.status : 'Review Status'}
            {filters.status && (
              <X
                size={14}
                onClick={(e) => { e.stopPropagation(); updateFilter('status', null); }}
                style={{ marginLeft: 4 }}
                aria-label="Clear status filter"
              />
            )}
            <ChevronDown size={14} aria-hidden="true" />
          </button>
          {activeDropdown === 'status' && (
            <div className="filter-dropdown" role="listbox" aria-label="Status options">
              <div
                className={`filter-option ${!filters.status ? 'active' : ''}`}
                onClick={() => { updateFilter('status', null); setActiveDropdown(null); }}
                role="option"
                aria-selected={!filters.status}
              >
                All Statuses
              </div>
              {Object.entries(statusConfig).map(([key, config]) => (
                <div
                  key={key}
                  className={`filter-option ${filters.status === key ? 'active' : ''}`}
                  onClick={() => { updateFilter('status', key); setActiveDropdown(null); }}
                  role="option"
                  aria-selected={filters.status === key}
                >
                  <config.icon size={14} aria-hidden="true" />
                  {config.label}
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Risk Level Filter */}
        <div className="filter-wrapper" ref={riskDropdownRef}>
          <button
            className={`filter-chip ${filters.risk_level ? 'active' : ''}`}
            onClick={() => setActiveDropdown(activeDropdown === 'risk' ? null : 'risk')}
            aria-expanded={activeDropdown === 'risk'}
            aria-haspopup="listbox"
            aria-label="Filter by risk level"
          >
            <Shield size={14} aria-hidden="true" />
            {filters.risk_level ? `${filters.risk_level.charAt(0).toUpperCase() + filters.risk_level.slice(1)} Risk` : 'Risk Level'}
            {filters.risk_level && (
              <X
                size={14}
                onClick={(e) => { e.stopPropagation(); updateFilter('risk_level', null); }}
                style={{ marginLeft: 4 }}
                aria-label="Clear risk filter"
              />
            )}
            <ChevronDown size={14} aria-hidden="true" />
          </button>
          {activeDropdown === 'risk' && (
            <div className="filter-dropdown" role="listbox" aria-label="Risk level options">
              <div
                className={`filter-option ${!filters.risk_level ? 'active' : ''}`}
                onClick={() => { updateFilter('risk_level', null); setActiveDropdown(null); }}
                role="option"
                aria-selected={!filters.risk_level}
              >
                All Risk Levels
              </div>
              {['low', 'medium', 'high'].map(level => (
                <div
                  key={level}
                  className={`filter-option ${filters.risk_level === level ? 'active' : ''}`}
                  onClick={() => { updateFilter('risk_level', level); setActiveDropdown(null); }}
                  role="option"
                  aria-selected={filters.risk_level === level}
                >
                  {level.charAt(0).toUpperCase() + level.slice(1)} Risk
                </div>
              ))}
            </div>
          )}
        </div>

        <div style={{ marginLeft: 'auto', display: 'flex', alignItems: 'center', gap: 8 }}>
          {isFetching && !isLoading && (
            <RefreshCw size={16} className="spinner" style={{ color: 'var(--text-muted)' }} aria-label="Loading" />
          )}
          <button
            className="filter-chip"
            onClick={() => refetch()}
            aria-label="Refresh applicants list"
          >
            <RefreshCw size={14} aria-hidden="true" />
          </button>
        </div>
      </div>

      {isLoading ? (
        <ApplicantsTableSkeleton rows={10} />
      ) : (
        <div className="table-container">
          {applicants.length === 0 ? (
            <div className="empty-state">
              <Users size={48} style={{ marginBottom: 16, opacity: 0.5 }} aria-hidden="true" />
              <h3>No applicants found</h3>
              <p>
                {filters.search || filters.status || filters.risk_level
                  ? 'Try adjusting your filters or search query.'
                  : 'Create your first applicant to get started.'}
              </p>
              {!filters.search && !filters.status && !filters.risk_level && (
                <button
                  className="btn btn-primary"
                  style={{ marginTop: 16 }}
                  onClick={() => setShowCreateModal(true)}
                >
                  <Plus size={16} />
                  Create Applicant
                </button>
              )}
            </div>
          ) : (
            <>
              <table className="table" role="grid">
                <thead>
                  <tr>
                    <th style={{ width: 48 }}>
                      <div
                        className={`checkbox ${selectedIds.length === applicants.length ? 'checked' : ''}`}
                        onClick={toggleSelectAll}
                        role="checkbox"
                        aria-checked={selectedIds.length === applicants.length}
                        aria-label="Select all applicants"
                        tabIndex={0}
                        onKeyDown={(e) => e.key === 'Enter' && toggleSelectAll()}
                      >
                        {selectedIds.length === applicants.length && <CheckCircle2 size={12} color="white" aria-hidden="true" />}
                      </div>
                    </th>
                    <th className="sortable">
                      <div className="th-content">
                        Applicant
                        <ArrowUpDown size={12} aria-hidden="true" />
                      </div>
                    </th>
                    <th>Steps</th>
                    <th className="sortable">
                      <div className="th-content">
                        Status
                        <ArrowUpDown size={12} aria-hidden="true" />
                      </div>
                    </th>
                    <th>Flags</th>
                    <th className="sortable">
                      <div className="th-content">
                        Risk
                        <ArrowUpDown size={12} aria-hidden="true" />
                      </div>
                    </th>
                    <th className="sortable">
                      <div className="th-content">
                        Submitted
                        <ArrowUpDown size={12} aria-hidden="true" />
                      </div>
                    </th>
                    <th>Reviewer</th>
                    <th style={{ width: 80 }}></th>
                  </tr>
                </thead>
                <tbody>
                  {applicants.map((applicant) => {
                    const status = statusConfig[applicant.review_status] || statusConfig.pending;
                    const StatusIcon = status?.icon;
                    const riskBucket = applicant.risk_level || getRiskBucket(applicant.risk_score);
                    const riskColor = getRiskColor(riskBucket);
                    const countryCode = applicant.country_code || applicant.nationality?.slice(0, 2)?.toUpperCase();

                    const displayName = applicant.first_name && applicant.last_name
                      ? `${applicant.first_name} ${applicant.last_name}`
                      : applicant.email?.split('@')[0] || `Applicant ${applicant.id.slice(0, 8)}`;

                    const steps = applicant.steps || [];
                    const flags = applicant.flags || [];

                    return (
                      <tr
                        key={applicant.id}
                        className={selectedIds.includes(applicant.id) ? 'selected' : ''}
                        onClick={() => handleRowClick(applicant)}
                      >
                        <td onClick={(e) => e.stopPropagation()}>
                          <div
                            className={`checkbox ${selectedIds.includes(applicant.id) ? 'checked' : ''}`}
                            onClick={() => toggleSelect(applicant.id)}
                            role="checkbox"
                            aria-checked={selectedIds.includes(applicant.id)}
                            aria-label={`Select ${displayName}`}
                            tabIndex={0}
                            onKeyDown={(e) => e.key === 'Enter' && toggleSelect(applicant.id)}
                          >
                            {selectedIds.includes(applicant.id) && <CheckCircle2 size={12} color="white" aria-hidden="true" />}
                          </div>
                        </td>
                        <td>
                          <div className="applicant-cell">
                            <span className="applicant-name">{displayName}</span>
                            <span className="applicant-id">ID: {applicant.id.slice(0, 12)}...</span>
                            <div className="applicant-meta">
                              {countryCode && (
                                <>
                                  <span>{countryFlags[countryCode] || '🌍'} {applicant.nationality || countryCode}</span>
                                  <span>•</span>
                                </>
                              )}
                              <span>{applicant.platform || 'Web'}</span>
                              {applicant.company_name && (
                                <>
                                  <span>•</span>
                                  <span><Building2 size={12} style={{ display: 'inline', verticalAlign: 'middle' }} aria-hidden="true" /> {applicant.company_name}</span>
                                </>
                              )}
                            </div>
                          </div>
                        </td>
                        <td>
                          <div className="steps-cell">
                            {steps.length > 0 ? (
                              steps.slice(0, 4).map((step, idx) => {
                                const StepIcon = stepIcons[step.name] || stepIcons[step.step_name] || FileText;
                                return (
                                  <div
                                    key={idx}
                                    className={`step-badge ${step.status}`}
                                    title={`${step.name || step.step_name}: ${step.status}`}
                                    aria-label={`${step.name || step.step_name}: ${step.status}`}
                                  >
                                    <StepIcon size={14} aria-hidden="true" />
                                  </div>
                                );
                              })
                            ) : (
                              <span style={{ color: 'var(--text-muted)', fontSize: 13 }}>—</span>
                            )}
                          </div>
                        </td>
                        <td>
                          <span className={`status-badge ${status?.color}`}>
                            {StatusIcon && <StatusIcon size={12} aria-hidden="true" />}
                            {status?.label}
                          </span>
                        </td>
                        <td>
                          <div className="flags-cell">
                            {flags.length === 0 ? (
                              <span style={{ color: 'var(--text-muted)', fontSize: 13 }}>—</span>
                            ) : (
                              flags.slice(0, 3).map((flag, idx) => {
                                const flagKey = typeof flag === 'string' ? flag : flag.type;
                                const flagInfo = flagConfig[flagKey] || { label: flagKey, color: 'info' };
                                return (
                                  <span key={idx} className={`flag-badge ${flagInfo.color}`}>
                                    {flagInfo.label}
                                  </span>
                                );
                              })
                            )}
                          </div>
                        </td>
                        <td>
                          <div className="risk-cell">
                            <span className={`risk-score ${riskColor}`}>
                              {applicant.risk_score ?? '—'}
                            </span>
                            {applicant.risk_score !== null && applicant.risk_score !== undefined && (
                              <div className="risk-bar" aria-hidden="true">
                                <div
                                  className={`risk-bar-fill ${riskColor}`}
                                  style={{ width: `${applicant.risk_score}%` }}
                                />
                              </div>
                            )}
                          </div>
                        </td>
                        <td>
                          <span style={{ color: 'var(--text-secondary)', fontSize: 13 }}>
                            {formatDate(applicant.created_at)}
                          </span>
                        </td>
                        <td>
                          <span style={{ color: 'var(--text-secondary)', fontSize: 13 }}>
                            {applicant.reviewed_by || '—'}
                          </span>
                        </td>
                        <td onClick={(e) => e.stopPropagation()}>
                          <div className="actions-cell">
                            <button
                              className="action-btn"
                              title="View Details"
                              aria-label={`View details for ${displayName}`}
                              onClick={() => handleRowClick(applicant)}
                            >
                              <Eye size={16} aria-hidden="true" />
                            </button>
                            <button
                              className="action-btn"
                              title="More Actions"
                              aria-label={`More actions for ${displayName}`}
                            >
                              <MoreHorizontal size={16} aria-hidden="true" />
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
                  Showing {filters.offset + 1}-{Math.min(filters.offset + filters.limit, total)} of {total} applicants
                </span>
                <div className="pagination-controls">
                  <button
                    className="page-btn"
                    disabled={currentPage === 1}
                    onClick={() => handlePageChange(currentPage - 1)}
                    aria-label="Previous page"
                  >
                    <ChevronLeft size={16} aria-hidden="true" />
                  </button>
                  {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
                    let pageNum;
                    if (totalPages <= 5) {
                      pageNum = i + 1;
                    } else if (currentPage <= 3) {
                      pageNum = i + 1;
                    } else if (currentPage >= totalPages - 2) {
                      pageNum = totalPages - 4 + i;
                    } else {
                      pageNum = currentPage - 2 + i;
                    }
                    return (
                      <button
                        key={pageNum}
                        className={`page-btn ${currentPage === pageNum ? 'active' : ''}`}
                        onClick={() => handlePageChange(pageNum)}
                        aria-label={`Page ${pageNum}`}
                        aria-current={currentPage === pageNum ? 'page' : undefined}
                      >
                        {pageNum}
                      </button>
                    );
                  })}
                  <button
                    className="page-btn"
                    disabled={currentPage === totalPages}
                    onClick={() => handlePageChange(currentPage + 1)}
                    aria-label="Next page"
                  >
                    <ChevronRight size={16} aria-hidden="true" />
                  </button>
                </div>
              </div>
            </>
          )}
        </div>
      )}

      {selectedIds.length > 0 && (
        <div className="batch-actions" role="toolbar" aria-label="Batch actions">
          <span className="batch-count">{selectedIds.length} selected</span>
          <div className="batch-divider" />
          <button
            className="btn btn-success"
            style={{ padding: '8px 12px' }}
            onClick={handleBatchApprove}
            disabled={batchReviewMutation.isPending}
            aria-label={`Approve ${selectedIds.length} selected applicants`}
          >
            {batchReviewMutation.isPending ? (
              <Loader2 size={14} className="spinner" aria-hidden="true" />
            ) : (
              <CheckCircle2 size={14} aria-hidden="true" />
            )}
            Approve
          </button>
          <button
            className="btn btn-danger"
            style={{ padding: '8px 12px' }}
            onClick={handleBatchReject}
            disabled={batchReviewMutation.isPending}
            aria-label={`Reject ${selectedIds.length} selected applicants`}
          >
            {batchReviewMutation.isPending ? (
              <Loader2 size={14} className="spinner" aria-hidden="true" />
            ) : (
              <XCircle size={14} aria-hidden="true" />
            )}
            Reject
          </button>
          <button
            className="btn btn-secondary"
            style={{ padding: '8px 12px' }}
            onClick={() => setSelectedIds([])}
            aria-label="Clear selection"
          >
            <X size={14} aria-hidden="true" />
            Clear
          </button>
        </div>
      )}

      {showCreateModal && (
        <CreateApplicantModal
          onClose={() => setShowCreateModal(false)}
          onSuccess={handleCreateSuccess}
        />
      )}

      <ConfirmDialog
        isOpen={confirmDialog.isOpen}
        title={confirmDialog.title}
        message={confirmDialog.message}
        confirmLabel={confirmDialog.action === 'approve' ? 'Approve All' : 'Reject All'}
        variant={confirmDialog.action === 'approve' ? 'success' : 'danger'}
        isLoading={batchReviewMutation.isPending}
        onConfirm={executeBatchAction}
        onCancel={() => setConfirmDialog({ isOpen: false, action: null })}
      />
    </div>
  );
}
