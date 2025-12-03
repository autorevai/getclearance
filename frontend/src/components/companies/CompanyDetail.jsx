/**
 * Company Detail Page
 *
 * Comprehensive company view with tabs:
 * - Overview: Basic info, status, risk
 * - Beneficial Owners: UBO list with add/edit/link functionality
 * - Documents: Corporate documents
 * - Screening: Screening results and history
 */

import React, { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Building2,
  ArrowLeft,
  Users,
  FileText,
  Shield,
  CheckCircle,
  XCircle,
  Clock,
  AlertTriangle,
  Globe,
  Mail,
  Phone,
  Link as LinkIcon,
  Calendar,
  Edit,
  PlayCircle,
  Search,
} from 'lucide-react';
import {
  useCompany,
  useReviewCompany,
  useScreenCompany,
  useUpdateCompany,
} from '../../hooks';
import CompanyForm from './CompanyForm';
import UBOList from './UBOList';
import CompanyDocuments from './CompanyDocuments';
import CompanyScreening from './CompanyScreening';

const STATUS_CONFIG = {
  pending: { label: 'Pending', color: '#8b919e', bg: 'rgba(139, 145, 158, 0.1)', icon: Clock },
  in_review: { label: 'In Review', color: '#6366f1', bg: 'rgba(99, 102, 241, 0.1)', icon: Search },
  approved: { label: 'Approved', color: '#22c55e', bg: 'rgba(34, 197, 94, 0.1)', icon: CheckCircle },
  rejected: { label: 'Rejected', color: '#ef4444', bg: 'rgba(239, 68, 68, 0.1)', icon: XCircle },
};

const RISK_CONFIG = {
  low: { label: 'Low Risk', color: '#22c55e' },
  medium: { label: 'Medium Risk', color: '#f59e0b' },
  high: { label: 'High Risk', color: '#ef4444' },
};

const TABS = [
  { id: 'overview', label: 'Overview', icon: Building2 },
  { id: 'ubos', label: 'Beneficial Owners', icon: Users },
  { id: 'documents', label: 'Documents', icon: FileText },
  { id: 'screening', label: 'Screening', icon: Shield },
];

export default function CompanyDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState('overview');
  const [showEditModal, setShowEditModal] = useState(false);

  const { data: company, isLoading, error } = useCompany(id);
  const reviewMutation = useReviewCompany();
  const screenMutation = useScreenCompany();
  const updateMutation = useUpdateCompany();

  if (isLoading) {
    return (
      <div className="loading-container">
        <div className="loading-spinner" />
        Loading company details...
      </div>
    );
  }

  if (error || !company) {
    return (
      <div className="error-container">
        <AlertTriangle size={48} />
        <h2>Company not found</h2>
        <button onClick={() => navigate('/companies')}>Back to Companies</button>
      </div>
    );
  }

  const status = STATUS_CONFIG[company.status] || STATUS_CONFIG.pending;
  const StatusIcon = status.icon;
  const risk = RISK_CONFIG[company.risk_level];

  const handleReview = async (decision) => {
    try {
      await reviewMutation.mutateAsync({ id, decision });
    } catch (err) {
      console.error('Failed to review company:', err);
    }
  };

  const handleScreen = async () => {
    try {
      await screenMutation.mutateAsync(id);
    } catch (err) {
      console.error('Failed to run screening:', err);
    }
  };

  const handleUpdate = async (data) => {
    try {
      await updateMutation.mutateAsync({ id, data });
      setShowEditModal(false);
    } catch (err) {
      console.error('Failed to update company:', err);
    }
  };

  return (
    <div className="company-detail">
      <style>{`
        .company-detail {
          max-width: 1200px;
          margin: 0 auto;
        }

        .loading-container,
        .error-container {
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          height: 400px;
          color: var(--text-secondary, #8b919e);
          gap: 16px;
        }

        .back-link {
          display: inline-flex;
          align-items: center;
          gap: 8px;
          color: var(--text-secondary, #8b919e);
          text-decoration: none;
          font-size: 14px;
          margin-bottom: 16px;
          cursor: pointer;
          background: none;
          border: none;
          padding: 0;
          font-family: inherit;
        }

        .back-link:hover {
          color: var(--text-primary, #f0f2f5);
        }

        .back-link svg {
          width: 16px;
          height: 16px;
        }

        .company-header {
          display: flex;
          justify-content: space-between;
          align-items: flex-start;
          gap: 24px;
          margin-bottom: 24px;
          flex-wrap: wrap;
        }

        .company-info {
          display: flex;
          gap: 16px;
          align-items: flex-start;
        }

        .company-icon {
          width: 56px;
          height: 56px;
          background: var(--bg-secondary, #111318);
          border-radius: 12px;
          display: flex;
          align-items: center;
          justify-content: center;
          color: var(--accent-primary, #6366f1);
        }

        .company-icon svg {
          width: 28px;
          height: 28px;
        }

        .company-title-section {
          display: flex;
          flex-direction: column;
          gap: 8px;
        }

        .company-name {
          font-size: 24px;
          font-weight: 600;
          color: var(--text-primary, #f0f2f5);
          margin: 0;
        }

        .company-trading {
          font-size: 14px;
          color: var(--text-secondary, #8b919e);
        }

        .company-badges {
          display: flex;
          gap: 8px;
          flex-wrap: wrap;
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

        .status-badge svg {
          width: 14px;
          height: 14px;
        }

        .risk-badge {
          display: inline-flex;
          align-items: center;
          gap: 6px;
          padding: 6px 12px;
          border-radius: 20px;
          font-size: 13px;
          font-weight: 500;
        }

        .risk-badge svg {
          width: 14px;
          height: 14px;
        }

        .header-actions {
          display: flex;
          gap: 12px;
          flex-wrap: wrap;
        }

        .action-btn {
          display: flex;
          align-items: center;
          gap: 8px;
          padding: 10px 16px;
          border-radius: 8px;
          font-size: 14px;
          font-weight: 500;
          cursor: pointer;
          transition: all 0.15s;
          font-family: inherit;
          border: 1px solid var(--border-primary, #23262f);
          background: var(--bg-secondary, #111318);
          color: var(--text-primary, #f0f2f5);
        }

        .action-btn:hover {
          background: var(--bg-tertiary, #1a1d24);
        }

        .action-btn svg {
          width: 16px;
          height: 16px;
        }

        .action-btn.primary {
          background: var(--accent-primary, #6366f1);
          border-color: var(--accent-primary, #6366f1);
          color: white;
        }

        .action-btn.primary:hover {
          background: var(--accent-hover, #5558e3);
        }

        .action-btn.success {
          background: #22c55e;
          border-color: #22c55e;
          color: white;
        }

        .action-btn.success:hover {
          background: #16a34a;
        }

        .action-btn.danger {
          background: #ef4444;
          border-color: #ef4444;
          color: white;
        }

        .action-btn.danger:hover {
          background: #dc2626;
        }

        .action-btn:disabled {
          opacity: 0.6;
          cursor: not-allowed;
        }

        .tabs {
          display: flex;
          gap: 4px;
          padding: 4px;
          background: var(--bg-secondary, #111318);
          border-radius: 10px;
          margin-bottom: 24px;
          width: fit-content;
        }

        .tab-btn {
          display: flex;
          align-items: center;
          gap: 8px;
          padding: 10px 16px;
          background: transparent;
          border: none;
          border-radius: 8px;
          color: var(--text-secondary, #8b919e);
          font-size: 14px;
          font-weight: 500;
          cursor: pointer;
          transition: all 0.15s;
          font-family: inherit;
        }

        .tab-btn:hover {
          color: var(--text-primary, #f0f2f5);
          background: var(--bg-tertiary, #1a1d24);
        }

        .tab-btn.active {
          background: var(--accent-primary, #6366f1);
          color: white;
        }

        .tab-btn svg {
          width: 16px;
          height: 16px;
        }

        .tab-badge {
          padding: 2px 6px;
          background: rgba(255, 255, 255, 0.2);
          border-radius: 10px;
          font-size: 11px;
        }

        .tab-content {
          background: var(--bg-secondary, #111318);
          border: 1px solid var(--border-primary, #23262f);
          border-radius: 12px;
          padding: 24px;
        }

        .overview-grid {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
          gap: 24px;
        }

        .info-section {
          display: flex;
          flex-direction: column;
          gap: 16px;
        }

        .info-section-title {
          font-size: 14px;
          font-weight: 600;
          color: var(--text-primary, #f0f2f5);
          margin: 0;
          padding-bottom: 8px;
          border-bottom: 1px solid var(--border-primary, #23262f);
        }

        .info-row {
          display: flex;
          align-items: center;
          gap: 12px;
        }

        .info-row svg {
          width: 16px;
          height: 16px;
          color: var(--text-secondary, #8b919e);
          flex-shrink: 0;
        }

        .info-label {
          font-size: 13px;
          color: var(--text-secondary, #8b919e);
          min-width: 120px;
        }

        .info-value {
          font-size: 14px;
          color: var(--text-primary, #f0f2f5);
        }

        .info-value a {
          color: var(--accent-primary, #6366f1);
          text-decoration: none;
        }

        .info-value a:hover {
          text-decoration: underline;
        }

        .flag-list {
          display: flex;
          gap: 8px;
          flex-wrap: wrap;
        }

        .flag-badge {
          display: inline-flex;
          align-items: center;
          gap: 4px;
          padding: 4px 8px;
          background: rgba(239, 68, 68, 0.1);
          color: #ef4444;
          border-radius: 4px;
          font-size: 12px;
          font-weight: 500;
        }

        .flag-badge svg {
          width: 12px;
          height: 12px;
        }

        .address-block {
          font-size: 14px;
          color: var(--text-primary, #f0f2f5);
          line-height: 1.6;
        }
      `}</style>

      <button className="back-link" onClick={() => navigate('/companies')}>
        <ArrowLeft />
        Back to Companies
      </button>

      <div className="company-header">
        <div className="company-info">
          <div className="company-icon">
            <Building2 />
          </div>
          <div className="company-title-section">
            <h1 className="company-name">{company.legal_name}</h1>
            {company.trading_name && company.trading_name !== company.legal_name && (
              <span className="company-trading">DBA: {company.trading_name}</span>
            )}
            <div className="company-badges">
              <span
                className="status-badge"
                style={{ color: status.color, background: status.bg }}
              >
                <StatusIcon />
                {status.label}
              </span>
              {risk && (
                <span
                  className="risk-badge"
                  style={{ color: risk.color, background: `${risk.color}15` }}
                >
                  <Shield />
                  {risk.label}
                </span>
              )}
              {company.has_hits && (
                <span
                  className="risk-badge"
                  style={{ color: '#f59e0b', background: 'rgba(245, 158, 11, 0.1)' }}
                >
                  <AlertTriangle />
                  Screening Hits
                </span>
              )}
            </div>
          </div>
        </div>

        <div className="header-actions">
          <button className="action-btn" onClick={() => setShowEditModal(true)}>
            <Edit />
            Edit
          </button>
          <button
            className="action-btn"
            onClick={handleScreen}
            disabled={screenMutation.isPending}
          >
            <PlayCircle />
            {screenMutation.isPending ? 'Running...' : 'Run Screening'}
          </button>
          {company.status === 'pending' || company.status === 'in_review' ? (
            <>
              <button
                className="action-btn success"
                onClick={() => handleReview('approved')}
                disabled={reviewMutation.isPending}
              >
                <CheckCircle />
                Approve
              </button>
              <button
                className="action-btn danger"
                onClick={() => handleReview('rejected')}
                disabled={reviewMutation.isPending}
              >
                <XCircle />
                Reject
              </button>
            </>
          ) : null}
        </div>
      </div>

      <div className="tabs">
        {TABS.map((tab) => (
          <button
            key={tab.id}
            className={`tab-btn ${activeTab === tab.id ? 'active' : ''}`}
            onClick={() => setActiveTab(tab.id)}
          >
            <tab.icon />
            {tab.label}
            {tab.id === 'ubos' && company.ubo_count > 0 && (
              <span className="tab-badge">{company.ubo_count}</span>
            )}
            {tab.id === 'documents' && company.documents?.length > 0 && (
              <span className="tab-badge">{company.documents.length}</span>
            )}
          </button>
        ))}
      </div>

      <div className="tab-content">
        {activeTab === 'overview' && (
          <div className="overview-grid">
            <div className="info-section">
              <h3 className="info-section-title">Company Information</h3>
              <div className="info-row">
                <Building2 />
                <span className="info-label">Registration #</span>
                <span className="info-value">
                  {company.registration_number || '—'}
                </span>
              </div>
              <div className="info-row">
                <FileText />
                <span className="info-label">Tax ID</span>
                <span className="info-value">{company.tax_id || '—'}</span>
              </div>
              <div className="info-row">
                <Globe />
                <span className="info-label">Country</span>
                <span className="info-value">
                  {company.incorporation_country || '—'}
                </span>
              </div>
              <div className="info-row">
                <Calendar />
                <span className="info-label">Incorporated</span>
                <span className="info-value">
                  {company.incorporation_date || '—'}
                </span>
              </div>
              <div className="info-row">
                <FileText />
                <span className="info-label">Legal Form</span>
                <span className="info-value">{company.legal_form || '—'}</span>
              </div>
              <div className="info-row">
                <Building2 />
                <span className="info-label">Industry</span>
                <span className="info-value">{company.industry || '—'}</span>
              </div>
            </div>

            <div className="info-section">
              <h3 className="info-section-title">Contact</h3>
              <div className="info-row">
                <LinkIcon />
                <span className="info-label">Website</span>
                <span className="info-value">
                  {company.website ? (
                    <a
                      href={company.website}
                      target="_blank"
                      rel="noopener noreferrer"
                    >
                      {company.website}
                    </a>
                  ) : (
                    '—'
                  )}
                </span>
              </div>
              <div className="info-row">
                <Mail />
                <span className="info-label">Email</span>
                <span className="info-value">
                  {company.email ? (
                    <a href={`mailto:${company.email}`}>{company.email}</a>
                  ) : (
                    '—'
                  )}
                </span>
              </div>
              <div className="info-row">
                <Phone />
                <span className="info-label">Phone</span>
                <span className="info-value">{company.phone || '—'}</span>
              </div>
            </div>

            {company.registered_address && (
              <div className="info-section">
                <h3 className="info-section-title">Registered Address</h3>
                <div className="address-block">
                  {company.registered_address.street && (
                    <div>{company.registered_address.street}</div>
                  )}
                  <div>
                    {[
                      company.registered_address.city,
                      company.registered_address.state,
                      company.registered_address.postal_code,
                    ]
                      .filter(Boolean)
                      .join(', ')}
                  </div>
                  {company.registered_address.country && (
                    <div>{company.registered_address.country}</div>
                  )}
                </div>
              </div>
            )}

            {company.flags?.length > 0 && (
              <div className="info-section">
                <h3 className="info-section-title">Risk Flags</h3>
                <div className="flag-list">
                  {company.flags.map((flag) => (
                    <span key={flag} className="flag-badge">
                      <AlertTriangle />
                      {flag.replace(/_/g, ' ').toUpperCase()}
                    </span>
                  ))}
                </div>
              </div>
            )}

            <div className="info-section">
              <h3 className="info-section-title">Business Details</h3>
              <div className="info-row">
                <Users />
                <span className="info-label">Employees</span>
                <span className="info-value">
                  {company.employee_count || '—'}
                </span>
              </div>
              <div className="info-row">
                <FileText />
                <span className="info-label">Revenue</span>
                <span className="info-value">
                  {company.annual_revenue || '—'}
                </span>
              </div>
              {company.description && (
                <div style={{ marginTop: 8 }}>
                  <span
                    className="info-label"
                    style={{ display: 'block', marginBottom: 8 }}
                  >
                    Description
                  </span>
                  <p
                    style={{
                      margin: 0,
                      fontSize: 14,
                      color: 'var(--text-primary)',
                      lineHeight: 1.6,
                    }}
                  >
                    {company.description}
                  </p>
                </div>
              )}
            </div>
          </div>
        )}

        {activeTab === 'ubos' && <UBOList companyId={id} company={company} />}

        {activeTab === 'documents' && <CompanyDocuments companyId={id} />}

        {activeTab === 'screening' && <CompanyScreening companyId={id} company={company} />}
      </div>

      {showEditModal && (
        <CompanyForm
          company={company}
          onSubmit={handleUpdate}
          onClose={() => setShowEditModal(false)}
          isSubmitting={updateMutation.isPending}
        />
      )}
    </div>
  );
}
