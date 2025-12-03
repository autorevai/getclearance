/**
 * UBO List Component
 *
 * Beneficial owners tab for company detail page.
 * Features add, edit, delete, and link to applicant KYC.
 */

import React, { useState } from 'react';
import {
  Plus,
  Users,
  CheckCircle,
  Clock,
  AlertTriangle,
  Link as LinkIcon,
  Edit,
  Trash2,
  X,
  Search,
} from 'lucide-react';
import {
  useAddUBO,
  useUpdateUBO,
  useDeleteUBO,
  useLinkUBOToApplicant,
  useSearchApplicants,
} from '../../hooks';
import { useDebounce } from '../../hooks/useDebounce';

const VERIFICATION_STATUS = {
  pending: { label: 'Pending', color: '#8b919e', icon: Clock },
  verified: { label: 'Verified', color: '#22c55e', icon: CheckCircle },
  linked: { label: 'Linked to KYC', color: '#6366f1', icon: LinkIcon },
  failed: { label: 'Failed', color: '#ef4444', icon: AlertTriangle },
};

export default function UBOList({ companyId, company }) {
  const [showAddModal, setShowAddModal] = useState(false);
  const [editingUBO, setEditingUBO] = useState(null);
  const [linkingUBO, setLinkingUBO] = useState(null);

  const addMutation = useAddUBO();
  const updateMutation = useUpdateUBO();
  const deleteMutation = useDeleteUBO();
  const linkMutation = useLinkUBOToApplicant();

  const ubos = company?.beneficial_owners || [];

  const handleAdd = async (data) => {
    try {
      await addMutation.mutateAsync({ companyId, data });
      setShowAddModal(false);
    } catch (err) {
      console.error('Failed to add UBO:', err);
    }
  };

  const handleUpdate = async (data) => {
    try {
      await updateMutation.mutateAsync({
        companyId,
        uboId: editingUBO.id,
        data,
      });
      setEditingUBO(null);
    } catch (err) {
      console.error('Failed to update UBO:', err);
    }
  };

  const handleDelete = async (uboId) => {
    // eslint-disable-next-line no-restricted-globals
    if (!confirm('Are you sure you want to remove this beneficial owner?')) {
      return;
    }
    try {
      await deleteMutation.mutateAsync({ companyId, uboId });
    } catch (err) {
      console.error('Failed to delete UBO:', err);
    }
  };

  const handleLink = async (applicantId) => {
    try {
      await linkMutation.mutateAsync({
        companyId,
        uboId: linkingUBO.id,
        applicantId,
      });
      setLinkingUBO(null);
    } catch (err) {
      console.error('Failed to link UBO:', err);
    }
  };

  return (
    <div className="ubo-list">
      <style>{`
        .ubo-list {
          display: flex;
          flex-direction: column;
          gap: 16px;
        }

        .ubo-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
        }

        .ubo-title {
          font-size: 16px;
          font-weight: 600;
          color: var(--text-primary, #f0f2f5);
          margin: 0;
          display: flex;
          align-items: center;
          gap: 8px;
        }

        .ubo-title svg {
          width: 20px;
          height: 20px;
          color: var(--accent-primary, #6366f1);
        }

        .add-btn {
          display: flex;
          align-items: center;
          gap: 8px;
          padding: 8px 14px;
          background: var(--accent-primary, #6366f1);
          color: white;
          border: none;
          border-radius: 6px;
          font-size: 13px;
          font-weight: 500;
          cursor: pointer;
          transition: background 0.15s;
          font-family: inherit;
        }

        .add-btn:hover {
          background: var(--accent-hover, #5558e3);
        }

        .add-btn svg {
          width: 14px;
          height: 14px;
        }

        .ubo-table {
          border: 1px solid var(--border-primary, #23262f);
          border-radius: 8px;
          overflow: hidden;
        }

        .ubo-table-header {
          display: grid;
          grid-template-columns: 2fr 1fr 1fr 1fr 100px;
          gap: 16px;
          padding: 12px 16px;
          background: var(--bg-tertiary, #1a1d24);
          border-bottom: 1px solid var(--border-primary, #23262f);
        }

        .table-header-cell {
          font-size: 11px;
          font-weight: 600;
          color: var(--text-secondary, #8b919e);
          text-transform: uppercase;
          letter-spacing: 0.5px;
        }

        .ubo-row {
          display: grid;
          grid-template-columns: 2fr 1fr 1fr 1fr 100px;
          gap: 16px;
          padding: 14px 16px;
          border-bottom: 1px solid var(--border-primary, #23262f);
          align-items: center;
        }

        .ubo-row:last-child {
          border-bottom: none;
        }

        .ubo-row:hover {
          background: var(--bg-tertiary, #1a1d24);
        }

        .ubo-name-cell {
          display: flex;
          flex-direction: column;
          gap: 4px;
        }

        .ubo-name {
          font-size: 14px;
          font-weight: 500;
          color: var(--text-primary, #f0f2f5);
        }

        .ubo-role {
          font-size: 12px;
          color: var(--text-secondary, #8b919e);
        }

        .ownership-value {
          font-size: 14px;
          color: var(--text-primary, #f0f2f5);
          font-weight: 500;
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

        .screening-cell {
          display: flex;
          align-items: center;
          gap: 6px;
        }

        .screening-badge {
          display: inline-flex;
          align-items: center;
          gap: 4px;
          padding: 4px 8px;
          border-radius: 4px;
          font-size: 12px;
          font-weight: 500;
        }

        .screening-badge.clear {
          background: rgba(34, 197, 94, 0.1);
          color: #22c55e;
        }

        .screening-badge.hits {
          background: rgba(239, 68, 68, 0.1);
          color: #ef4444;
        }

        .screening-badge svg {
          width: 12px;
          height: 12px;
        }

        .actions-cell {
          display: flex;
          gap: 8px;
        }

        .action-icon-btn {
          padding: 6px;
          background: transparent;
          border: none;
          color: var(--text-secondary, #8b919e);
          cursor: pointer;
          border-radius: 4px;
          transition: all 0.15s;
        }

        .action-icon-btn:hover {
          background: var(--bg-secondary, #111318);
          color: var(--text-primary, #f0f2f5);
        }

        .action-icon-btn.link:hover {
          color: var(--accent-primary, #6366f1);
        }

        .action-icon-btn.delete:hover {
          color: #ef4444;
        }

        .action-icon-btn svg {
          width: 14px;
          height: 14px;
        }

        .empty-state {
          padding: 40px;
          text-align: center;
          color: var(--text-secondary, #8b919e);
        }

        .empty-state svg {
          width: 40px;
          height: 40px;
          margin-bottom: 12px;
        }

        .empty-state h4 {
          margin: 0 0 8px;
          font-size: 14px;
          color: var(--text-primary, #f0f2f5);
        }

        .empty-state p {
          margin: 0;
          font-size: 13px;
        }
      `}</style>

      <div className="ubo-header">
        <h3 className="ubo-title">
          <Users />
          Beneficial Owners ({ubos.length})
        </h3>
        <button className="add-btn" onClick={() => setShowAddModal(true)}>
          <Plus />
          Add UBO
        </button>
      </div>

      {ubos.length === 0 ? (
        <div className="empty-state">
          <Users />
          <h4>No beneficial owners</h4>
          <p>Add beneficial owners who own or control 25% or more of the company.</p>
        </div>
      ) : (
        <div className="ubo-table">
          <div className="ubo-table-header">
            <div className="table-header-cell">Name</div>
            <div className="table-header-cell">Ownership</div>
            <div className="table-header-cell">Status</div>
            <div className="table-header-cell">Screening</div>
            <div className="table-header-cell">Actions</div>
          </div>

          {ubos.map((ubo) => {
            const status =
              VERIFICATION_STATUS[ubo.verification_status] ||
              VERIFICATION_STATUS.pending;
            const StatusIcon = status.icon;

            return (
              <div key={ubo.id} className="ubo-row">
                <div className="ubo-name-cell">
                  <span className="ubo-name">{ubo.full_name}</span>
                  {ubo.role_title && (
                    <span className="ubo-role">{ubo.role_title}</span>
                  )}
                </div>
                <div className="ownership-value">
                  {ubo.ownership_percentage != null
                    ? `${ubo.ownership_percentage}%`
                    : '—'}
                </div>
                <div>
                  <span
                    className="status-badge"
                    style={{
                      color: status.color,
                      background: `${status.color}15`,
                    }}
                  >
                    <StatusIcon />
                    {status.label}
                  </span>
                </div>
                <div className="screening-cell">
                  {ubo.screening_status === 'clear' ? (
                    <span className="screening-badge clear">
                      <CheckCircle />
                      Clear
                    </span>
                  ) : ubo.screening_status === 'hits' ? (
                    <span className="screening-badge hits">
                      <AlertTriangle />
                      Hits
                    </span>
                  ) : (
                    <span style={{ color: 'var(--text-secondary)', fontSize: 13 }}>
                      Not screened
                    </span>
                  )}
                </div>
                <div className="actions-cell">
                  {!ubo.applicant_id && (
                    <button
                      className="action-icon-btn link"
                      onClick={() => setLinkingUBO(ubo)}
                      title="Link to KYC"
                    >
                      <LinkIcon />
                    </button>
                  )}
                  <button
                    className="action-icon-btn"
                    onClick={() => setEditingUBO(ubo)}
                    title="Edit"
                  >
                    <Edit />
                  </button>
                  <button
                    className="action-icon-btn delete"
                    onClick={() => handleDelete(ubo.id)}
                    title="Delete"
                  >
                    <Trash2 />
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {showAddModal && (
        <UBOFormModal
          onSubmit={handleAdd}
          onClose={() => setShowAddModal(false)}
          isSubmitting={addMutation.isPending}
        />
      )}

      {editingUBO && (
        <UBOFormModal
          ubo={editingUBO}
          onSubmit={handleUpdate}
          onClose={() => setEditingUBO(null)}
          isSubmitting={updateMutation.isPending}
        />
      )}

      {linkingUBO && (
        <LinkApplicantModal
          ubo={linkingUBO}
          onLink={handleLink}
          onClose={() => setLinkingUBO(null)}
          isLinking={linkMutation.isPending}
        />
      )}
    </div>
  );
}

function UBOFormModal({ ubo, onSubmit, onClose, isSubmitting }) {
  const [formData, setFormData] = useState({
    full_name: ubo?.full_name || '',
    date_of_birth: ubo?.date_of_birth || '',
    nationality: ubo?.nationality || '',
    country_of_residence: ubo?.country_of_residence || '',
    ownership_percentage: ubo?.ownership_percentage || '',
    ownership_type: ubo?.ownership_type || 'direct',
    is_director: ubo?.is_director || false,
    is_shareholder: ubo?.is_shareholder || false,
    role_title: ubo?.role_title || '',
  });

  const handleChange = (field, value) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    const data = { ...formData };
    if (data.ownership_percentage) {
      data.ownership_percentage = parseFloat(data.ownership_percentage);
    } else {
      data.ownership_percentage = null;
    }
    if (!data.date_of_birth) data.date_of_birth = null;
    if (!data.nationality) data.nationality = null;
    if (!data.country_of_residence) data.country_of_residence = null;
    if (!data.role_title) data.role_title = null;
    onSubmit(data);
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <style>{`
        .modal-overlay {
          position: fixed;
          top: 0;
          left: 0;
          right: 0;
          bottom: 0;
          background: rgba(0, 0, 0, 0.7);
          display: flex;
          align-items: center;
          justify-content: center;
          z-index: 1000;
          padding: 20px;
        }

        .modal-content {
          background: var(--bg-primary, #0a0b0e);
          border: 1px solid var(--border-primary, #23262f);
          border-radius: 12px;
          width: 100%;
          max-width: 500px;
        }

        .modal-header {
          display: flex;
          align-items: center;
          justify-content: space-between;
          padding: 16px 20px;
          border-bottom: 1px solid var(--border-primary, #23262f);
        }

        .modal-title {
          font-size: 16px;
          font-weight: 600;
          color: var(--text-primary, #f0f2f5);
          margin: 0;
        }

        .close-btn {
          padding: 6px;
          background: transparent;
          border: none;
          color: var(--text-secondary, #8b919e);
          cursor: pointer;
          border-radius: 4px;
        }

        .close-btn:hover {
          background: var(--bg-secondary, #111318);
        }

        .modal-body {
          padding: 20px;
          display: flex;
          flex-direction: column;
          gap: 16px;
        }

        .form-row {
          display: grid;
          grid-template-columns: 1fr 1fr;
          gap: 12px;
        }

        .form-group {
          display: flex;
          flex-direction: column;
          gap: 6px;
        }

        .form-group.full-width {
          grid-column: 1 / -1;
        }

        .form-label {
          font-size: 12px;
          font-weight: 500;
          color: var(--text-secondary, #8b919e);
        }

        .form-input,
        .form-select {
          padding: 10px 12px;
          background: var(--bg-secondary, #111318);
          border: 1px solid var(--border-primary, #23262f);
          border-radius: 6px;
          color: var(--text-primary, #f0f2f5);
          font-size: 14px;
          font-family: inherit;
        }

        .form-input:focus,
        .form-select:focus {
          outline: none;
          border-color: var(--accent-primary, #6366f1);
        }

        .checkbox-row {
          display: flex;
          gap: 20px;
          margin-top: 4px;
        }

        .checkbox-label {
          display: flex;
          align-items: center;
          gap: 8px;
          font-size: 13px;
          color: var(--text-secondary, #8b919e);
          cursor: pointer;
        }

        .checkbox-label input {
          width: 16px;
          height: 16px;
        }

        .modal-footer {
          display: flex;
          justify-content: flex-end;
          gap: 12px;
          padding: 16px 20px;
          border-top: 1px solid var(--border-primary, #23262f);
        }

        .btn {
          padding: 10px 16px;
          border-radius: 6px;
          font-size: 14px;
          font-weight: 500;
          cursor: pointer;
          font-family: inherit;
          border: none;
        }

        .btn-secondary {
          background: var(--bg-secondary, #111318);
          color: var(--text-primary, #f0f2f5);
          border: 1px solid var(--border-primary, #23262f);
        }

        .btn-primary {
          background: var(--accent-primary, #6366f1);
          color: white;
        }

        .btn-primary:disabled {
          opacity: 0.6;
          cursor: not-allowed;
        }
      `}</style>

      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h3 className="modal-title">
            {ubo ? 'Edit Beneficial Owner' : 'Add Beneficial Owner'}
          </h3>
          <button className="close-btn" onClick={onClose}>
            <X size={18} />
          </button>
        </div>

        <form onSubmit={handleSubmit}>
          <div className="modal-body">
            <div className="form-group full-width">
              <label className="form-label">Full Name *</label>
              <input
                type="text"
                className="form-input"
                value={formData.full_name}
                onChange={(e) => handleChange('full_name', e.target.value)}
                required
              />
            </div>

            <div className="form-row">
              <div className="form-group">
                <label className="form-label">Date of Birth</label>
                <input
                  type="date"
                  className="form-input"
                  value={formData.date_of_birth}
                  onChange={(e) => handleChange('date_of_birth', e.target.value)}
                />
              </div>
              <div className="form-group">
                <label className="form-label">Nationality (ISO 2)</label>
                <input
                  type="text"
                  className="form-input"
                  value={formData.nationality}
                  onChange={(e) =>
                    handleChange(
                      'nationality',
                      e.target.value.toUpperCase().slice(0, 2)
                    )
                  }
                  maxLength={2}
                  placeholder="US"
                />
              </div>
            </div>

            <div className="form-row">
              <div className="form-group">
                <label className="form-label">Ownership %</label>
                <input
                  type="number"
                  className="form-input"
                  value={formData.ownership_percentage}
                  onChange={(e) =>
                    handleChange('ownership_percentage', e.target.value)
                  }
                  min={0}
                  max={100}
                  step={0.01}
                />
              </div>
              <div className="form-group">
                <label className="form-label">Ownership Type</label>
                <select
                  className="form-select"
                  value={formData.ownership_type}
                  onChange={(e) => handleChange('ownership_type', e.target.value)}
                >
                  <option value="direct">Direct</option>
                  <option value="indirect">Indirect</option>
                  <option value="control">Control</option>
                </select>
              </div>
            </div>

            <div className="form-group full-width">
              <label className="form-label">Role/Title</label>
              <input
                type="text"
                className="form-input"
                value={formData.role_title}
                onChange={(e) => handleChange('role_title', e.target.value)}
                placeholder="CEO, Director, etc."
              />
            </div>

            <div className="form-group full-width">
              <label className="form-label">Roles</label>
              <div className="checkbox-row">
                <label className="checkbox-label">
                  <input
                    type="checkbox"
                    checked={formData.is_director}
                    onChange={(e) =>
                      handleChange('is_director', e.target.checked)
                    }
                  />
                  Director
                </label>
                <label className="checkbox-label">
                  <input
                    type="checkbox"
                    checked={formData.is_shareholder}
                    onChange={(e) =>
                      handleChange('is_shareholder', e.target.checked)
                    }
                  />
                  Shareholder
                </label>
              </div>
            </div>
          </div>

          <div className="modal-footer">
            <button type="button" className="btn btn-secondary" onClick={onClose}>
              Cancel
            </button>
            <button type="submit" className="btn btn-primary" disabled={isSubmitting}>
              {isSubmitting ? 'Saving...' : ubo ? 'Save Changes' : 'Add UBO'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

function LinkApplicantModal({ ubo, onLink, onClose, isLinking }) {
  const [search, setSearch] = useState('');
  const debouncedSearch = useDebounce(search, 300);
  const { data, isLoading } = useSearchApplicants(debouncedSearch);

  const applicants = data?.items || [];

  return (
    <div className="modal-overlay" onClick={onClose}>
      <style>{`
        .link-modal-content {
          background: var(--bg-primary, #0a0b0e);
          border: 1px solid var(--border-primary, #23262f);
          border-radius: 12px;
          width: 100%;
          max-width: 500px;
          max-height: 80vh;
          display: flex;
          flex-direction: column;
        }

        .link-modal-header {
          padding: 16px 20px;
          border-bottom: 1px solid var(--border-primary, #23262f);
        }

        .link-modal-title {
          font-size: 16px;
          font-weight: 600;
          color: var(--text-primary, #f0f2f5);
          margin: 0 0 4px;
        }

        .link-modal-subtitle {
          font-size: 13px;
          color: var(--text-secondary, #8b919e);
          margin: 0;
        }

        .search-wrapper {
          position: relative;
          padding: 16px 20px;
          border-bottom: 1px solid var(--border-primary, #23262f);
        }

        .search-wrapper input {
          width: 100%;
          padding: 10px 12px 10px 36px;
          background: var(--bg-secondary, #111318);
          border: 1px solid var(--border-primary, #23262f);
          border-radius: 6px;
          color: var(--text-primary, #f0f2f5);
          font-size: 14px;
          font-family: inherit;
        }

        .search-wrapper input:focus {
          outline: none;
          border-color: var(--accent-primary, #6366f1);
        }

        .search-wrapper svg {
          position: absolute;
          left: 32px;
          top: 50%;
          transform: translateY(-50%);
          width: 16px;
          height: 16px;
          color: var(--text-secondary, #8b919e);
        }

        .applicant-list {
          flex: 1;
          overflow-y: auto;
          padding: 8px;
        }

        .applicant-item {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 12px;
          border-radius: 6px;
          cursor: pointer;
          transition: background 0.15s;
        }

        .applicant-item:hover {
          background: var(--bg-secondary, #111318);
        }

        .applicant-info {
          display: flex;
          flex-direction: column;
          gap: 2px;
        }

        .applicant-name {
          font-size: 14px;
          font-weight: 500;
          color: var(--text-primary, #f0f2f5);
        }

        .applicant-email {
          font-size: 12px;
          color: var(--text-secondary, #8b919e);
        }

        .select-btn {
          padding: 6px 12px;
          background: var(--accent-primary, #6366f1);
          color: white;
          border: none;
          border-radius: 4px;
          font-size: 12px;
          font-weight: 500;
          cursor: pointer;
          font-family: inherit;
        }

        .select-btn:disabled {
          opacity: 0.6;
          cursor: not-allowed;
        }

        .empty-search {
          padding: 40px;
          text-align: center;
          color: var(--text-secondary, #8b919e);
          font-size: 13px;
        }

        .link-modal-footer {
          padding: 12px 20px;
          border-top: 1px solid var(--border-primary, #23262f);
          display: flex;
          justify-content: flex-end;
        }

        .cancel-btn {
          padding: 8px 16px;
          background: var(--bg-secondary, #111318);
          color: var(--text-primary, #f0f2f5);
          border: 1px solid var(--border-primary, #23262f);
          border-radius: 6px;
          font-size: 13px;
          cursor: pointer;
          font-family: inherit;
        }
      `}</style>

      <div className="link-modal-content" onClick={(e) => e.stopPropagation()}>
        <div className="link-modal-header">
          <h3 className="link-modal-title">Link to KYC Applicant</h3>
          <p className="link-modal-subtitle">
            Link {ubo.full_name} to an existing KYC applicant record
          </p>
        </div>

        <div className="search-wrapper">
          <Search />
          <input
            type="text"
            placeholder="Search applicants by name or email..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            autoFocus
          />
        </div>

        <div className="applicant-list">
          {isLoading ? (
            <div className="empty-search">Searching...</div>
          ) : !search ? (
            <div className="empty-search">
              Start typing to search for applicants
            </div>
          ) : applicants.length === 0 ? (
            <div className="empty-search">No applicants found</div>
          ) : (
            applicants.map((applicant) => (
              <div key={applicant.id} className="applicant-item">
                <div className="applicant-info">
                  <span className="applicant-name">{applicant.full_name}</span>
                  <span className="applicant-email">{applicant.email}</span>
                </div>
                <button
                  className="select-btn"
                  onClick={() => onLink(applicant.id)}
                  disabled={isLinking}
                >
                  {isLinking ? 'Linking...' : 'Select'}
                </button>
              </div>
            ))
          )}
        </div>

        <div className="link-modal-footer">
          <button className="cancel-btn" onClick={onClose}>
            Cancel
          </button>
        </div>
      </div>
    </div>
  );
}
