/**
 * Companies Page (KYB)
 *
 * Main companies list page with filtering, search, and CRUD operations.
 */

import React, { useState, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Building2,
  Plus,
  Search,
  Filter,
  ChevronRight,
  AlertTriangle,
  CheckCircle,
  Clock,
  XCircle,
  Users,
  Globe,
  Shield,
} from 'lucide-react';
import { useCompanies, useCreateCompany } from '../../hooks';
import { useDebounce } from '../../hooks/useDebounce';
import CompanyForm from './CompanyForm';

const STATUS_CONFIG = {
  pending: { label: 'Pending', color: '#8b919e', bg: 'rgba(139, 145, 158, 0.1)', icon: Clock },
  in_review: { label: 'In Review', color: '#6366f1', bg: 'rgba(99, 102, 241, 0.1)', icon: Search },
  approved: { label: 'Approved', color: '#22c55e', bg: 'rgba(34, 197, 94, 0.1)', icon: CheckCircle },
  rejected: { label: 'Rejected', color: '#ef4444', bg: 'rgba(239, 68, 68, 0.1)', icon: XCircle },
};

const RISK_CONFIG = {
  low: { label: 'Low', color: '#22c55e' },
  medium: { label: 'Medium', color: '#f59e0b' },
  high: { label: 'High', color: '#ef4444' },
};

export default function CompaniesPage() {
  const navigate = useNavigate();
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [riskFilter, setRiskFilter] = useState('');
  const [showFilters, setShowFilters] = useState(false);
  const [showCreateModal, setShowCreateModal] = useState(false);

  const debouncedSearch = useDebounce(search, 300);

  const filters = useMemo(() => ({
    ...(debouncedSearch && { search: debouncedSearch }),
    ...(statusFilter && { status: statusFilter }),
    ...(riskFilter && { risk_level: riskFilter }),
    limit: 50,
  }), [debouncedSearch, statusFilter, riskFilter]);

  const { data, isLoading, error } = useCompanies(filters);
  const createMutation = useCreateCompany();

  const handleCreate = async (formData) => {
    try {
      const company = await createMutation.mutateAsync(formData);
      setShowCreateModal(false);
      navigate(`/companies/${company.id}`);
    } catch (err) {
      console.error('Failed to create company:', err);
    }
  };

  const companies = data?.items || [];

  return (
    <div className="companies-page">
      <style>{`
        .companies-page {
          max-width: 1400px;
          margin: 0 auto;
        }

        .page-header {
          display: flex;
          justify-content: space-between;
          align-items: flex-start;
          margin-bottom: 24px;
          gap: 16px;
          flex-wrap: wrap;
        }

        .page-title-section {
          display: flex;
          align-items: flex-start;
          gap: 12px;
        }

        .page-icon {
          width: 32px;
          height: 32px;
          color: var(--accent-primary, #6366f1);
        }

        .page-title {
          font-size: 24px;
          font-weight: 600;
          color: var(--text-primary, #f0f2f5);
          margin: 0;
        }

        .page-subtitle {
          font-size: 14px;
          color: var(--text-secondary, #8b919e);
          margin: 4px 0 0;
        }

        .header-actions {
          display: flex;
          gap: 12px;
          align-items: center;
        }

        .create-btn {
          display: flex;
          align-items: center;
          gap: 8px;
          padding: 10px 16px;
          background: var(--accent-primary, #6366f1);
          color: white;
          border: none;
          border-radius: 8px;
          font-size: 14px;
          font-weight: 500;
          cursor: pointer;
          transition: background 0.15s;
          font-family: inherit;
        }

        .create-btn:hover {
          background: var(--accent-hover, #5558e3);
        }

        .create-btn svg {
          width: 16px;
          height: 16px;
        }

        .toolbar {
          display: flex;
          gap: 12px;
          margin-bottom: 24px;
          flex-wrap: wrap;
        }

        .search-input {
          flex: 1;
          min-width: 200px;
          max-width: 400px;
          padding: 10px 12px 10px 40px;
          background: var(--bg-secondary, #111318);
          border: 1px solid var(--border-primary, #23262f);
          border-radius: 8px;
          color: var(--text-primary, #f0f2f5);
          font-size: 14px;
          position: relative;
        }

        .search-wrapper {
          position: relative;
          flex: 1;
          min-width: 200px;
          max-width: 400px;
        }

        .search-wrapper svg {
          position: absolute;
          left: 12px;
          top: 50%;
          transform: translateY(-50%);
          width: 16px;
          height: 16px;
          color: var(--text-secondary, #8b919e);
        }

        .filter-btn {
          display: flex;
          align-items: center;
          gap: 8px;
          padding: 10px 16px;
          background: var(--bg-secondary, #111318);
          border: 1px solid var(--border-primary, #23262f);
          border-radius: 8px;
          color: var(--text-secondary, #8b919e);
          font-size: 14px;
          cursor: pointer;
          transition: all 0.15s;
          font-family: inherit;
        }

        .filter-btn:hover,
        .filter-btn.active {
          background: var(--bg-tertiary, #1a1d24);
          color: var(--text-primary, #f0f2f5);
          border-color: var(--accent-primary, #6366f1);
        }

        .filter-btn svg {
          width: 16px;
          height: 16px;
        }

        .filters-panel {
          display: flex;
          gap: 12px;
          padding: 16px;
          background: var(--bg-secondary, #111318);
          border: 1px solid var(--border-primary, #23262f);
          border-radius: 8px;
          margin-bottom: 24px;
          flex-wrap: wrap;
        }

        .filter-select {
          padding: 8px 12px;
          background: var(--bg-tertiary, #1a1d24);
          border: 1px solid var(--border-primary, #23262f);
          border-radius: 6px;
          color: var(--text-primary, #f0f2f5);
          font-size: 13px;
          min-width: 150px;
          cursor: pointer;
          font-family: inherit;
        }

        .clear-filters-btn {
          padding: 8px 12px;
          background: transparent;
          border: none;
          color: var(--accent-primary, #6366f1);
          font-size: 13px;
          cursor: pointer;
          font-family: inherit;
        }

        .companies-table {
          background: var(--bg-secondary, #111318);
          border: 1px solid var(--border-primary, #23262f);
          border-radius: 12px;
          overflow: hidden;
        }

        .table-header {
          display: grid;
          grid-template-columns: 2fr 1fr 1fr 1fr 1fr 100px 40px;
          gap: 16px;
          padding: 12px 20px;
          background: var(--bg-tertiary, #1a1d24);
          border-bottom: 1px solid var(--border-primary, #23262f);
        }

        .table-header-cell {
          font-size: 12px;
          font-weight: 600;
          color: var(--text-secondary, #8b919e);
          text-transform: uppercase;
          letter-spacing: 0.5px;
        }

        .company-row {
          display: grid;
          grid-template-columns: 2fr 1fr 1fr 1fr 1fr 100px 40px;
          gap: 16px;
          padding: 16px 20px;
          border-bottom: 1px solid var(--border-primary, #23262f);
          cursor: pointer;
          transition: background 0.15s;
          align-items: center;
        }

        .company-row:last-child {
          border-bottom: none;
        }

        .company-row:hover {
          background: var(--bg-tertiary, #1a1d24);
        }

        .company-name-cell {
          display: flex;
          flex-direction: column;
          gap: 4px;
        }

        .company-legal-name {
          font-size: 14px;
          font-weight: 500;
          color: var(--text-primary, #f0f2f5);
        }

        .company-trading-name {
          font-size: 12px;
          color: var(--text-secondary, #8b919e);
        }

        .company-reg-number {
          font-size: 13px;
          color: var(--text-secondary, #8b919e);
          font-family: monospace;
        }

        .country-badge {
          display: inline-flex;
          align-items: center;
          gap: 6px;
          padding: 4px 8px;
          background: var(--bg-tertiary, #1a1d24);
          border-radius: 4px;
          font-size: 12px;
          color: var(--text-secondary, #8b919e);
        }

        .country-badge svg {
          width: 12px;
          height: 12px;
        }

        .status-badge {
          display: inline-flex;
          align-items: center;
          gap: 6px;
          padding: 4px 10px;
          border-radius: 20px;
          font-size: 12px;
          font-weight: 500;
          width: fit-content;
        }

        .status-badge svg {
          width: 12px;
          height: 12px;
        }

        .risk-badge {
          display: inline-flex;
          align-items: center;
          gap: 6px;
          padding: 4px 10px;
          border-radius: 4px;
          font-size: 12px;
          font-weight: 500;
          width: fit-content;
        }

        .risk-badge svg {
          width: 12px;
          height: 12px;
        }

        .ubo-count {
          display: flex;
          align-items: center;
          gap: 6px;
          font-size: 13px;
          color: var(--text-secondary, #8b919e);
        }

        .ubo-count svg {
          width: 14px;
          height: 14px;
        }

        .chevron-cell {
          color: var(--text-secondary, #8b919e);
        }

        .chevron-cell svg {
          width: 16px;
          height: 16px;
        }

        .empty-state {
          padding: 60px 20px;
          text-align: center;
        }

        .empty-icon {
          width: 48px;
          height: 48px;
          color: var(--text-secondary, #8b919e);
          margin-bottom: 16px;
        }

        .empty-title {
          font-size: 16px;
          font-weight: 500;
          color: var(--text-primary, #f0f2f5);
          margin: 0 0 8px;
        }

        .empty-message {
          font-size: 14px;
          color: var(--text-secondary, #8b919e);
          margin: 0;
        }

        .loading-state {
          padding: 60px 20px;
          text-align: center;
          color: var(--text-secondary, #8b919e);
        }

        .error-state {
          padding: 60px 20px;
          text-align: center;
          color: var(--error, #ef4444);
        }

        .flags-cell {
          display: flex;
          gap: 4px;
        }

        .flag-indicator {
          width: 8px;
          height: 8px;
          border-radius: 50%;
          background: var(--warning, #f59e0b);
        }

        .flag-indicator.sanctions {
          background: var(--error, #ef4444);
        }

        .flag-indicator.pep {
          background: var(--warning, #f59e0b);
        }

        @media (max-width: 1200px) {
          .table-header,
          .company-row {
            grid-template-columns: 2fr 1fr 1fr 1fr 40px;
          }

          .table-header-cell:nth-child(5),
          .company-row > *:nth-child(5),
          .table-header-cell:nth-child(6),
          .company-row > *:nth-child(6) {
            display: none;
          }
        }
      `}</style>

      <div className="page-header">
        <div className="page-title-section">
          <Building2 className="page-icon" />
          <div>
            <h1 className="page-title">Companies</h1>
            <p className="page-subtitle">
              Know Your Business (KYB) verification and management
            </p>
          </div>
        </div>
        <div className="header-actions">
          <button className="create-btn" onClick={() => setShowCreateModal(true)}>
            <Plus />
            Add Company
          </button>
        </div>
      </div>

      <div className="toolbar">
        <div className="search-wrapper">
          <Search />
          <input
            type="text"
            className="search-input"
            placeholder="Search companies..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
        <button
          className={`filter-btn ${showFilters ? 'active' : ''}`}
          onClick={() => setShowFilters(!showFilters)}
        >
          <Filter />
          Filters
        </button>
      </div>

      {showFilters && (
        <div className="filters-panel">
          <select
            className="filter-select"
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
          >
            <option value="">All Statuses</option>
            <option value="pending">Pending</option>
            <option value="in_review">In Review</option>
            <option value="approved">Approved</option>
            <option value="rejected">Rejected</option>
          </select>
          <select
            className="filter-select"
            value={riskFilter}
            onChange={(e) => setRiskFilter(e.target.value)}
          >
            <option value="">All Risk Levels</option>
            <option value="low">Low Risk</option>
            <option value="medium">Medium Risk</option>
            <option value="high">High Risk</option>
          </select>
          {(statusFilter || riskFilter) && (
            <button
              className="clear-filters-btn"
              onClick={() => {
                setStatusFilter('');
                setRiskFilter('');
              }}
            >
              Clear Filters
            </button>
          )}
        </div>
      )}

      <div className="companies-table">
        <div className="table-header">
          <div className="table-header-cell">Company</div>
          <div className="table-header-cell">Registration</div>
          <div className="table-header-cell">Country</div>
          <div className="table-header-cell">Status</div>
          <div className="table-header-cell">Risk</div>
          <div className="table-header-cell">UBOs</div>
          <div className="table-header-cell"></div>
        </div>

        {isLoading ? (
          <div className="loading-state">Loading companies...</div>
        ) : error ? (
          <div className="error-state">Failed to load companies</div>
        ) : companies.length === 0 ? (
          <div className="empty-state">
            <Building2 className="empty-icon" />
            <h3 className="empty-title">No companies found</h3>
            <p className="empty-message">
              {search || statusFilter || riskFilter
                ? 'Try adjusting your filters'
                : 'Add your first company to get started'}
            </p>
          </div>
        ) : (
          companies.map((company) => {
            const status = STATUS_CONFIG[company.status] || STATUS_CONFIG.pending;
            const StatusIcon = status.icon;
            const risk = RISK_CONFIG[company.risk_level];

            return (
              <div
                key={company.id}
                className="company-row"
                onClick={() => navigate(`/companies/${company.id}`)}
              >
                <div className="company-name-cell">
                  <span className="company-legal-name">{company.legal_name}</span>
                  {company.trading_name && company.trading_name !== company.legal_name && (
                    <span className="company-trading-name">
                      DBA: {company.trading_name}
                    </span>
                  )}
                </div>
                <div className="company-reg-number">
                  {company.registration_number || '—'}
                </div>
                <div>
                  {company.incorporation_country ? (
                    <span className="country-badge">
                      <Globe />
                      {company.incorporation_country}
                    </span>
                  ) : (
                    '—'
                  )}
                </div>
                <div>
                  <span
                    className="status-badge"
                    style={{ color: status.color, background: status.bg }}
                  >
                    <StatusIcon />
                    {status.label}
                  </span>
                </div>
                <div>
                  {risk ? (
                    <span
                      className="risk-badge"
                      style={{
                        color: risk.color,
                        background: `${risk.color}15`,
                      }}
                    >
                      <Shield />
                      {risk.label}
                    </span>
                  ) : (
                    '—'
                  )}
                </div>
                <div className="ubo-count">
                  <Users />
                  {company.ubo_count || 0}
                  {company.has_hits && (
                    <div className="flags-cell">
                      <AlertTriangle
                        style={{ width: 14, height: 14, color: '#f59e0b' }}
                      />
                    </div>
                  )}
                </div>
                <div className="chevron-cell">
                  <ChevronRight />
                </div>
              </div>
            );
          })
        )}
      </div>

      {showCreateModal && (
        <CompanyForm
          onSubmit={handleCreate}
          onClose={() => setShowCreateModal(false)}
          isSubmitting={createMutation.isPending}
        />
      )}
    </div>
  );
}
