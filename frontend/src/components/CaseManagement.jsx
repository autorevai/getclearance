import React, { useState } from 'react';
import {
  Search,
  Plus,
  FolderKanban,
  AlertTriangle,
  CheckCircle2,
  User,
  ExternalLink,
  Download,
  MessageSquare,
  Paperclip,
  Send,
  Sparkles,
  Flag,
  FileText,
  Shield,
  X,
  Loader2,
  RefreshCw
} from 'lucide-react';
import { useCases, useCase, useCreateCase, useResolveCase, useAddCaseNote, useCaseCounts } from '../hooks/useCases';
import { useRiskSummary } from '../hooks/useAI';
import { useApplicants } from '../hooks/useApplicants';
import { useToast } from '../contexts/ToastContext';

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

// Create Case Modal Component
function CreateCaseModal({ isOpen, onClose, onSubmit, isSubmitting }) {
  const [formData, setFormData] = useState({
    title: '',
    type: 'verification',
    priority: 'medium',
    applicant_id: '',
    description: ''
  });
  const [searchTerm, setSearchTerm] = useState('');

  // Fetch applicants for selection
  const { data: applicantsData } = useApplicants({ search: searchTerm, limit: 10 });
  const applicants = applicantsData?.items || [];

  const handleSubmit = (e) => {
    e.preventDefault();
    onSubmit(formData);
  };

  if (!isOpen) return null;

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={e => e.stopPropagation()}>
        <div className="modal-header">
          <h2>Create New Case</h2>
          <button className="modal-close" onClick={onClose}>
            <X size={20} />
          </button>
        </div>
        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label>Title *</label>
            <input
              type="text"
              value={formData.title}
              onChange={e => setFormData(prev => ({ ...prev, title: e.target.value }))}
              placeholder="Case title..."
              required
            />
          </div>

          <div className="form-row">
            <div className="form-group">
              <label>Type</label>
              <select
                value={formData.type}
                onChange={e => setFormData(prev => ({ ...prev, type: e.target.value }))}
              >
                <option value="verification">Verification</option>
                <option value="sanctions">Sanctions</option>
                <option value="pep">PEP</option>
                <option value="fraud">Fraud</option>
                <option value="aml">AML</option>
              </select>
            </div>
            <div className="form-group">
              <label>Priority</label>
              <select
                value={formData.priority}
                onChange={e => setFormData(prev => ({ ...prev, priority: e.target.value }))}
              >
                <option value="low">Low</option>
                <option value="medium">Medium</option>
                <option value="high">High</option>
                <option value="critical">Critical</option>
              </select>
            </div>
          </div>

          <div className="form-group">
            <label>Link to Applicant</label>
            <input
              type="text"
              value={searchTerm}
              onChange={e => setSearchTerm(e.target.value)}
              placeholder="Search applicants..."
            />
            {applicants.length > 0 && searchTerm && (
              <div className="applicant-dropdown">
                {applicants.map(a => (
                  <div
                    key={a.id}
                    className={`applicant-option ${formData.applicant_id === a.id ? 'selected' : ''}`}
                    onClick={() => {
                      setFormData(prev => ({ ...prev, applicant_id: a.id }));
                      setSearchTerm(`${a.first_name} ${a.last_name}`);
                    }}
                  >
                    {a.first_name} {a.last_name} - {a.email}
                  </div>
                ))}
              </div>
            )}
          </div>

          <div className="form-group">
            <label>Description</label>
            <textarea
              value={formData.description}
              onChange={e => setFormData(prev => ({ ...prev, description: e.target.value }))}
              placeholder="Case description..."
              rows={3}
            />
          </div>

          <div className="modal-footer">
            <button type="button" className="btn btn-secondary" onClick={onClose}>
              Cancel
            </button>
            <button type="submit" className="btn btn-primary" disabled={isSubmitting || !formData.title}>
              {isSubmitting ? <><Loader2 size={16} className="spin" /> Creating...</> : 'Create Case'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

// AI Summary Component for Case Detail
function CaseAISummary({ applicantId, caseType }) {
  const { data: riskSummary, isLoading, error } = useRiskSummary(applicantId);

  if (!applicantId) {
    // Fallback to type-based summary if no applicant linked
    const typeBasedSummaries = {
      sanctions: "This case involves a potential OFAC SDN match. Recommend verifying identity documents and requesting additional proof of identity before disposition.",
      pep: "PEP match identified. Standard enhanced due diligence should be completed to assess risk profile.",
      verification: "Verification check requires manual review. Please examine the flagged documents or liveness results.",
      fraud: "Potential fraud indicators detected. Review all submitted documents for signs of manipulation.",
      aml: "AML screening hit requires investigation. Review transaction history and source of funds."
    };

    return (
      <div className="ai-summary">
        <div className="ai-summary-header">
          <Sparkles size={14} />
          AI Analysis
        </div>
        <div className="ai-summary-text">
          {typeBasedSummaries[caseType] || "AI analysis pending. Link an applicant to see detailed risk assessment."}
        </div>
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className="ai-summary loading">
        <div className="ai-summary-header">
          <Loader2 size={14} className="spin" />
          Loading AI Analysis...
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="ai-summary error">
        <div className="ai-summary-header">
          <AlertTriangle size={14} />
          Analysis Unavailable
        </div>
        <div className="ai-summary-text">
          Unable to load AI analysis. Please try again later.
        </div>
      </div>
    );
  }

  return (
    <div className="ai-summary">
      <div className="ai-summary-header">
        <Sparkles size={14} />
        AI Analysis
        {riskSummary?.generated_at && (
          <span className="ai-timestamp">
            {new Date(riskSummary.generated_at).toLocaleDateString()}
          </span>
        )}
      </div>
      <div className="ai-summary-text">
        {riskSummary?.summary || riskSummary?.analysis || "No AI summary available for this applicant."}
      </div>
      {riskSummary?.risk_score && (
        <div className="ai-risk-score">
          Risk Score: <strong>{riskSummary.risk_score}/100</strong>
        </div>
      )}
    </div>
  );
}

export default function CaseManagement() {
  const [activeFilter, setActiveFilter] = useState('open');
  const [selectedCaseId, setSelectedCaseId] = useState(null);
  const [noteText, setNoteText] = useState('');
  const [searchQuery, setSearchQuery] = useState('');
  const [showCreateModal, setShowCreateModal] = useState(false);

  // Toast notifications
  const toast = useToast();

  // API hooks
  const statusFilter = activeFilter === 'all' ? {} : { status: activeFilter };
  const { data: casesData, isLoading, error, refetch } = useCases({ ...statusFilter, search: searchQuery });
  const { data: counts } = useCaseCounts();
  const { data: selectedCaseData } = useCase(selectedCaseId);

  const createCaseMutation = useCreateCase();
  const resolveCaseMutation = useResolveCase();
  const addNoteMutation = useAddCaseNote();

  const cases = casesData?.items || [];
  const selectedCase = selectedCaseData || cases.find(c => c.id === selectedCaseId);

  const handleCreateCase = async (formData) => {
    try {
      await createCaseMutation.mutateAsync(formData);
      setShowCreateModal(false);
      toast.success('Case created successfully');
    } catch (err) {
      console.error('Failed to create case:', err);
      toast.error(`Failed to create case: ${err.message}`);
    }
  };

  const handleResolve = async (resolution) => {
    if (!selectedCaseId) return;
    try {
      await resolveCaseMutation.mutateAsync({
        id: selectedCaseId,
        resolution,
        notes: null
      });
      setSelectedCaseId(null);
      const resolutionLabel = resolution === 'cleared' ? 'cleared' : 'escalated';
      toast.success(`Case ${resolutionLabel} successfully`);
    } catch (err) {
      console.error('Failed to resolve case:', err);
      toast.error(`Failed to resolve case: ${err.message}`);
    }
  };

  const handleAddNote = async () => {
    if (!noteText.trim() || !selectedCaseId) return;
    try {
      await addNoteMutation.mutateAsync({
        id: selectedCaseId,
        content: noteText
      });
      setNoteText('');
      toast.success('Note added');
    } catch (err) {
      console.error('Failed to add note:', err);
      toast.error(`Failed to add note: ${err.message}`);
    }
  };

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

        /* Modal Styles */
        .modal-overlay {
          position: fixed;
          top: 0;
          left: 0;
          right: 0;
          bottom: 0;
          background: rgba(0, 0, 0, 0.6);
          display: flex;
          align-items: center;
          justify-content: center;
          z-index: 1000;
        }

        .modal-content {
          background: var(--bg-secondary);
          border: 1px solid var(--border-color);
          border-radius: 16px;
          width: 100%;
          max-width: 500px;
          max-height: 90vh;
          overflow-y: auto;
        }

        .modal-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 20px;
          border-bottom: 1px solid var(--border-color);
        }

        .modal-header h2 {
          font-size: 18px;
          font-weight: 600;
          margin: 0;
        }

        .modal-close {
          background: transparent;
          border: none;
          color: var(--text-muted);
          cursor: pointer;
          padding: 4px;
          border-radius: 4px;
        }

        .modal-close:hover {
          background: var(--bg-hover);
          color: var(--text-primary);
        }

        .modal-content form {
          padding: 20px;
        }

        .form-group {
          margin-bottom: 16px;
        }

        .form-group label {
          display: block;
          font-size: 13px;
          font-weight: 500;
          margin-bottom: 6px;
          color: var(--text-secondary);
        }

        .form-group input,
        .form-group select,
        .form-group textarea {
          width: 100%;
          padding: 10px 12px;
          background: var(--bg-tertiary);
          border: 1px solid var(--border-color);
          border-radius: 8px;
          font-size: 14px;
          color: var(--text-primary);
          font-family: inherit;
        }

        .form-group input:focus,
        .form-group select:focus,
        .form-group textarea:focus {
          outline: none;
          border-color: var(--accent-primary);
        }

        .form-row {
          display: grid;
          grid-template-columns: 1fr 1fr;
          gap: 12px;
        }

        .applicant-dropdown {
          background: var(--bg-tertiary);
          border: 1px solid var(--border-color);
          border-radius: 8px;
          margin-top: 4px;
          max-height: 150px;
          overflow-y: auto;
        }

        .applicant-option {
          padding: 10px 12px;
          cursor: pointer;
          font-size: 13px;
          border-bottom: 1px solid var(--border-color);
        }

        .applicant-option:last-child {
          border-bottom: none;
        }

        .applicant-option:hover {
          background: var(--bg-hover);
        }

        .applicant-option.selected {
          background: var(--accent-glow);
          color: var(--accent-primary);
        }

        .modal-footer {
          display: flex;
          justify-content: flex-end;
          gap: 12px;
          padding: 16px 20px;
          border-top: 1px solid var(--border-color);
          margin-top: 8px;
        }

        /* Loading States */
        .loading-container {
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          padding: 60px 20px;
          color: var(--text-muted);
        }

        .spin {
          animation: spin 1s linear infinite;
        }

        @keyframes spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }

        .error-container {
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          padding: 40px 20px;
          text-align: center;
          color: var(--danger);
        }

        .error-container button {
          margin-top: 16px;
        }

        .no-cases {
          padding: 40px 20px;
          text-align: center;
          color: var(--text-muted);
        }

        .ai-timestamp {
          margin-left: auto;
          font-weight: 400;
          font-size: 11px;
          color: var(--text-muted);
        }

        .ai-risk-score {
          margin-top: 12px;
          padding-top: 12px;
          border-top: 1px solid var(--border-color);
          font-size: 13px;
          color: var(--text-secondary);
        }

        .ai-summary.loading,
        .ai-summary.error {
          border-color: var(--border-color);
          background: var(--bg-tertiary);
        }

        .ai-summary.error .ai-summary-header {
          color: var(--danger);
        }

        .btn:disabled {
          opacity: 0.5;
          cursor: not-allowed;
        }

        .action-btn:disabled {
          opacity: 0.5;
          cursor: not-allowed;
        }
      `}</style>
      
      {/* Create Case Modal */}
      <CreateCaseModal
        isOpen={showCreateModal}
        onClose={() => setShowCreateModal(false)}
        onSubmit={handleCreateCase}
        isSubmitting={createCaseMutation.isPending}
      />

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
          <button className="btn btn-primary" onClick={() => setShowCreateModal(true)}>
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
          <div className="stat-value warning">{counts?.open ?? '-'}</div>
        </div>
        <div
          className={`stat-card ${activeFilter === 'in_progress' ? 'active' : ''}`}
          onClick={() => setActiveFilter('in_progress')}
        >
          <div className="stat-label">In Progress</div>
          <div className="stat-value info">{counts?.in_progress ?? '-'}</div>
        </div>
        <div
          className={`stat-card ${activeFilter === 'resolved' ? 'active' : ''}`}
          onClick={() => setActiveFilter('resolved')}
        >
          <div className="stat-label">Resolved (30d)</div>
          <div className="stat-value success">{counts?.resolved ?? '-'}</div>
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
          <div className="stat-value">{counts?.total ?? cases.length}</div>
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
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
              />
            </div>
            <button className="btn btn-secondary" style={{ padding: '8px 12px' }} onClick={() => refetch()}>
              <RefreshCw size={14} className={isLoading ? 'spin' : ''} />
              Refresh
            </button>
          </div>

          {/* Loading State */}
          {isLoading && (
            <div className="loading-container">
              <Loader2 size={32} className="spin" />
              <div style={{ marginTop: 12 }}>Loading cases...</div>
            </div>
          )}

          {/* Error State */}
          {error && !isLoading && (
            <div className="error-container">
              <AlertTriangle size={32} />
              <div style={{ marginTop: 12 }}>Failed to load cases</div>
              <button className="btn btn-secondary" onClick={() => refetch()}>
                Try Again
              </button>
            </div>
          )}

          {/* Empty State */}
          {!isLoading && !error && cases.length === 0 && (
            <div className="no-cases">
              <FolderKanban size={32} style={{ marginBottom: 12, opacity: 0.5 }} />
              <div>No cases found</div>
              <div style={{ fontSize: 13, marginTop: 4 }}>
                {searchQuery ? 'Try a different search term' : 'Create a new case to get started'}
              </div>
            </div>
          )}

          {/* Cases List */}
          {!isLoading && !error && cases.map((caseItem) => {
            const type = typeConfig[caseItem.type];
            const priority = priorityConfig[caseItem.priority];
            const status = statusConfig[caseItem.status];
            const TypeIcon = type?.icon;

            // Handle both API format and display format
            const caseId = caseItem.case_number || caseItem.id;
            const lastActivity = caseItem.updated_at || caseItem.lastActivity || caseItem.created_at;
            const noteCount = caseItem.notes?.length || caseItem.note_count || 0;
            const attachmentCount = caseItem.attachments?.length || caseItem.attachment_count || 0;

            return (
              <div
                key={caseItem.id}
                className={`case-item ${selectedCaseId === caseItem.id ? 'selected' : ''}`}
                onClick={() => setSelectedCaseId(caseItem.id)}
              >
                <div className="case-header">
                  <span className="case-id">{caseId}</span>
                  <span className="case-time">{formatRelativeTime(lastActivity)}</span>
                </div>
                <div className="case-title">{caseItem.title}</div>
                <div className="case-meta">
                  <span className={`case-badge ${type?.color || 'muted'}`}>
                    {TypeIcon && <TypeIcon size={10} />}
                    {type?.label || caseItem.type}
                  </span>
                  <span className={`case-badge ${priority?.color || 'muted'}`}>
                    {priority?.label || caseItem.priority}
                  </span>
                  <span className={`case-badge ${status?.color || 'muted'}`}>
                    {status?.label || caseItem.status}
                  </span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: 12 }}>
                  <div className="case-assignee">
                    <div className="assignee-avatar">
                      {caseItem.assigned_to ? (caseItem.assigned_to.name?.[0] || 'U') : 'RT'}
                    </div>
                    {caseItem.assigned_to?.name || 'Unassigned'}
                  </div>
                  <div className="case-indicators">
                    <span className="indicator">
                      <MessageSquare size={12} />
                      {noteCount}
                    </span>
                    <span className="indicator">
                      <Paperclip size={12} />
                      {attachmentCount}
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
                <div className="case-id" style={{ marginBottom: 8 }}>
                  {selectedCase.case_number || selectedCase.id}
                </div>
                <div className="detail-title">{selectedCase.title}</div>
                <div className="detail-meta">
                  <span className={`case-badge ${typeConfig[selectedCase.type]?.color || 'muted'}`}>
                    {typeConfig[selectedCase.type]?.label || selectedCase.type}
                  </span>
                  <span className={`case-badge ${priorityConfig[selectedCase.priority]?.color || 'muted'}`}>
                    {priorityConfig[selectedCase.priority]?.label || selectedCase.priority}
                  </span>
                  <span className={`case-badge ${statusConfig[selectedCase.status]?.color || 'muted'}`}>
                    {statusConfig[selectedCase.status]?.label || selectedCase.status}
                  </span>
                </div>
              </div>

              <div className="detail-content">
                {/* Subject Section */}
                <div className="detail-section">
                  <div className="section-title">Subject</div>
                  {selectedCase.applicant_id || selectedCase.applicant ? (
                    <div className="subject-card">
                      <div className="subject-icon">
                        <User size={20} />
                      </div>
                      <div className="subject-info">
                        <div className="subject-name">
                          {selectedCase.applicant?.first_name
                            ? `${selectedCase.applicant.first_name} ${selectedCase.applicant.last_name}`
                            : 'Linked Applicant'}
                        </div>
                        <div className="subject-id">
                          {selectedCase.applicant_id || selectedCase.applicant?.id}
                        </div>
                      </div>
                      <ExternalLink size={16} className="subject-link" />
                    </div>
                  ) : (
                    <div className="subject-card" style={{ color: 'var(--text-muted)' }}>
                      <div className="subject-icon">
                        <User size={20} />
                      </div>
                      <div className="subject-info">
                        <div className="subject-name">No linked applicant</div>
                        <div className="subject-id">Case created manually</div>
                      </div>
                    </div>
                  )}
                </div>

                {/* AI Summary Section */}
                <div className="detail-section">
                  <div className="section-title">AI Summary</div>
                  <CaseAISummary
                    applicantId={selectedCase.applicant_id || selectedCase.applicant?.id}
                    caseType={selectedCase.type}
                  />
                </div>

                {/* Notes Section */}
                <div className="detail-section">
                  <div className="section-title">
                    Notes ({selectedCase.notes?.length || 0})
                  </div>
                  {selectedCase.notes && selectedCase.notes.length > 0 ? (
                    selectedCase.notes.map((note, idx) => (
                      <div key={note.id || idx} className="note-item">
                        <div className="note-header">
                          <div className="assignee-avatar" style={{ width: 24, height: 24, fontSize: 10 }}>
                            {note.created_by?.name?.[0] || note.author?.[0] || '?'}
                          </div>
                          <span className="note-author">
                            {note.created_by?.name || note.author || 'Unknown'}
                          </span>
                          <span className="note-time">
                            {formatRelativeTime(note.created_at)}
                          </span>
                        </div>
                        <div className="note-text">{note.content}</div>
                      </div>
                    ))
                  ) : (
                    <div style={{ color: 'var(--text-muted)', fontSize: 13 }}>
                      No notes yet. Add a note below.
                    </div>
                  )}
                </div>

                {/* Action Buttons */}
                {selectedCase.status !== 'resolved' && (
                  <div className="action-buttons">
                    <button
                      className="action-btn success"
                      onClick={() => handleResolve('cleared')}
                      disabled={resolveCaseMutation.isPending}
                    >
                      {resolveCaseMutation.isPending ? (
                        <Loader2 size={14} className="spin" />
                      ) : (
                        <CheckCircle2 size={14} />
                      )}
                      Clear
                    </button>
                    <button
                      className="action-btn danger"
                      onClick={() => handleResolve('escalated')}
                      disabled={resolveCaseMutation.isPending}
                    >
                      {resolveCaseMutation.isPending ? (
                        <Loader2 size={14} className="spin" />
                      ) : (
                        <Flag size={14} />
                      )}
                      Escalate
                    </button>
                    <button className="action-btn secondary">
                      <Download size={14} />
                      Export
                    </button>
                  </div>
                )}

                {/* Show resolution info for resolved cases */}
                {selectedCase.status === 'resolved' && (
                  <div style={{
                    background: 'var(--bg-tertiary)',
                    padding: 16,
                    borderRadius: 8,
                    marginTop: 16
                  }}>
                    <div style={{ fontSize: 12, color: 'var(--text-muted)', marginBottom: 4 }}>
                      Resolution
                    </div>
                    <div style={{ fontSize: 14, fontWeight: 500 }}>
                      {selectedCase.resolution === 'cleared' ? '✓ Cleared' :
                       selectedCase.resolution === 'escalated' ? '⚠ Escalated' :
                       selectedCase.resolution || 'Resolved'}
                    </div>
                    {selectedCase.resolved_at && (
                      <div style={{ fontSize: 12, color: 'var(--text-muted)', marginTop: 4 }}>
                        {formatDateTime(selectedCase.resolved_at)}
                      </div>
                    )}
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
                    onKeyDown={(e) => e.key === 'Enter' && handleAddNote()}
                    disabled={addNoteMutation.isPending}
                  />
                  <button
                    className="send-btn"
                    onClick={handleAddNote}
                    disabled={!noteText.trim() || addNoteMutation.isPending}
                  >
                    {addNoteMutation.isPending ? (
                      <Loader2 size={16} className="spin" />
                    ) : (
                      <Send size={16} />
                    )}
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
