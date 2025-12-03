/**
 * Questionnaires Page
 *
 * Admin page for managing questionnaire templates.
 */

import React, { useState } from 'react';
import {
  ClipboardList,
  Plus,
  Search,
  MoreVertical,
  Edit,
  Trash2,
  Copy,
  Eye,
  AlertCircle,
  FileText,
  ChevronLeft,
  ChevronRight,
} from 'lucide-react';
import { useQuestionnaires, useDeleteQuestionnaire, useInitializeDefaults } from '../../hooks/useQuestionnaires';
import QuestionnaireBuilder from './QuestionnaireBuilder';
import QuestionnairePreview from './QuestionnairePreview';

const styles = {
  container: {
    padding: '24px',
    maxWidth: '1200px',
    margin: '0 auto',
  },
  header: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: '24px',
  },
  title: {
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
    fontSize: '24px',
    fontWeight: '600',
    margin: 0,
  },
  subtitle: {
    color: '#6b7280',
    fontSize: '14px',
    marginTop: '4px',
  },
  buttonGroup: {
    display: 'flex',
    gap: '8px',
  },
  button: {
    display: 'flex',
    alignItems: 'center',
    gap: '6px',
    padding: '8px 16px',
    borderRadius: '6px',
    border: 'none',
    cursor: 'pointer',
    fontSize: '14px',
    fontWeight: '500',
  },
  primaryButton: {
    backgroundColor: '#3b82f6',
    color: 'white',
  },
  secondaryButton: {
    backgroundColor: '#f3f4f6',
    color: '#374151',
    border: '1px solid #d1d5db',
  },
  filterBar: {
    display: 'flex',
    gap: '12px',
    padding: '16px',
    backgroundColor: 'white',
    borderRadius: '8px',
    border: '1px solid #e5e7eb',
    marginBottom: '16px',
  },
  searchInput: {
    flex: 1,
    padding: '8px 12px',
    paddingLeft: '36px',
    borderRadius: '6px',
    border: '1px solid #d1d5db',
    fontSize: '14px',
  },
  searchWrapper: {
    position: 'relative',
    flex: 1,
  },
  searchIcon: {
    position: 'absolute',
    left: '10px',
    top: '50%',
    transform: 'translateY(-50%)',
    color: '#9ca3af',
  },
  select: {
    padding: '8px 12px',
    borderRadius: '6px',
    border: '1px solid #d1d5db',
    fontSize: '14px',
    minWidth: '150px',
  },
  table: {
    width: '100%',
    backgroundColor: 'white',
    borderRadius: '8px',
    border: '1px solid #e5e7eb',
    borderCollapse: 'collapse',
    overflow: 'hidden',
  },
  th: {
    textAlign: 'left',
    padding: '12px 16px',
    backgroundColor: '#f9fafb',
    borderBottom: '1px solid #e5e7eb',
    fontSize: '12px',
    fontWeight: '600',
    color: '#6b7280',
    textTransform: 'uppercase',
  },
  td: {
    padding: '12px 16px',
    borderBottom: '1px solid #e5e7eb',
    fontSize: '14px',
  },
  badge: {
    display: 'inline-block',
    padding: '2px 8px',
    borderRadius: '12px',
    fontSize: '12px',
    fontWeight: '500',
  },
  menuButton: {
    background: 'none',
    border: 'none',
    cursor: 'pointer',
    padding: '4px',
    borderRadius: '4px',
  },
  dropdown: {
    position: 'absolute',
    right: 0,
    top: '100%',
    backgroundColor: 'white',
    borderRadius: '8px',
    boxShadow: '0 4px 12px rgba(0,0,0,0.15)',
    border: '1px solid #e5e7eb',
    minWidth: '150px',
    zIndex: 50,
  },
  dropdownItem: {
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
    padding: '8px 12px',
    width: '100%',
    border: 'none',
    background: 'none',
    cursor: 'pointer',
    fontSize: '14px',
    color: '#374151',
    textAlign: 'left',
  },
  modal: {
    position: 'fixed',
    inset: 0,
    backgroundColor: 'rgba(0,0,0,0.5)',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    zIndex: 100,
  },
  modalContent: {
    backgroundColor: 'white',
    borderRadius: '12px',
    width: '90%',
    maxWidth: '800px',
    maxHeight: '90vh',
    overflow: 'auto',
    padding: '24px',
  },
  pagination: {
    display: 'flex',
    justifyContent: 'center',
    gap: '8px',
    marginTop: '16px',
  },
  pageButton: {
    padding: '8px 12px',
    borderRadius: '6px',
    border: '1px solid #d1d5db',
    background: 'white',
    cursor: 'pointer',
  },
  emptyState: {
    textAlign: 'center',
    padding: '48px',
    color: '#6b7280',
  },
  loader: {
    display: 'flex',
    justifyContent: 'center',
    padding: '48px',
  },
  error: {
    padding: '16px',
    backgroundColor: '#fef2f2',
    borderRadius: '8px',
    color: '#dc2626',
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
  },
};

const BADGE_COLORS = {
  source_of_funds: { bg: '#dcfce7', color: '#16a34a' },
  pep_declaration: { bg: '#fee2e2', color: '#dc2626' },
  tax_residency: { bg: '#dbeafe', color: '#2563eb' },
  business_info: { bg: '#f3e8ff', color: '#7c3aed' },
  general: { bg: '#f3f4f6', color: '#6b7280' },
};

export default function QuestionnairesPage() {
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState('');
  const [typeFilter, setTypeFilter] = useState('');
  const [activeFilter, setActiveFilter] = useState('');
  const [builderOpen, setBuilderOpen] = useState(false);
  const [editingId, setEditingId] = useState(null);
  const [previewId, setPreviewId] = useState(null);
  const [openMenu, setOpenMenu] = useState(null);

  const { data, isLoading, error } = useQuestionnaires({
    page,
    page_size: 10,
    search: search || undefined,
    questionnaire_type: typeFilter || undefined,
    is_active: activeFilter === '' ? undefined : activeFilter === 'true',
  });

  const deleteMutation = useDeleteQuestionnaire();
  const initDefaultsMutation = useInitializeDefaults();

  const handleDelete = async (id) => {
    if (window.confirm('Are you sure you want to delete this questionnaire?')) {
      await deleteMutation.mutateAsync(id);
    }
    setOpenMenu(null);
  };

  const handleEdit = (id) => {
    setEditingId(id);
    setBuilderOpen(true);
    setOpenMenu(null);
  };

  const handleCreate = () => {
    setEditingId(null);
    setBuilderOpen(true);
  };

  if (isLoading) {
    return (
      <div style={styles.container}>
        <div style={styles.loader}>Loading questionnaires...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div style={styles.container}>
        <div style={styles.error}>
          <AlertCircle size={16} />
          Error loading questionnaires: {error.message}
        </div>
      </div>
    );
  }

  const questionnaires = data?.items || [];
  const totalPages = data?.pages || 1;

  return (
    <div style={styles.container}>
      {/* Header */}
      <div style={styles.header}>
        <div>
          <h1 style={styles.title}>
            <ClipboardList size={28} />
            Questionnaires
          </h1>
          <p style={styles.subtitle}>
            Create and manage custom questionnaires for KYC/KYB verification
          </p>
        </div>
        <div style={styles.buttonGroup}>
          <button
            style={{ ...styles.button, ...styles.secondaryButton }}
            onClick={() => initDefaultsMutation.mutate()}
            disabled={initDefaultsMutation.isPending}
          >
            <FileText size={16} />
            {initDefaultsMutation.isPending ? 'Initializing...' : 'Initialize Defaults'}
          </button>
          <button
            style={{ ...styles.button, ...styles.primaryButton }}
            onClick={handleCreate}
          >
            <Plus size={16} />
            New Questionnaire
          </button>
        </div>
      </div>

      {/* Filters */}
      <div style={styles.filterBar}>
        <div style={styles.searchWrapper}>
          <Search size={16} style={styles.searchIcon} />
          <input
            type="text"
            placeholder="Search questionnaires..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            style={styles.searchInput}
          />
        </div>
        <select
          value={typeFilter}
          onChange={(e) => setTypeFilter(e.target.value)}
          style={styles.select}
        >
          <option value="">All Types</option>
          <option value="general">General</option>
          <option value="source_of_funds">Source of Funds</option>
          <option value="pep_declaration">PEP Declaration</option>
          <option value="tax_residency">Tax Residency</option>
          <option value="business_info">Business Info</option>
        </select>
        <select
          value={activeFilter}
          onChange={(e) => setActiveFilter(e.target.value)}
          style={styles.select}
        >
          <option value="">All Status</option>
          <option value="true">Active</option>
          <option value="false">Inactive</option>
        </select>
      </div>

      {/* Table */}
      <table style={styles.table}>
        <thead>
          <tr>
            <th style={styles.th}>Name</th>
            <th style={styles.th}>Type</th>
            <th style={styles.th}>Questions</th>
            <th style={styles.th}>Completions</th>
            <th style={styles.th}>Avg Risk</th>
            <th style={styles.th}>Status</th>
            <th style={{ ...styles.th, width: '50px' }}></th>
          </tr>
        </thead>
        <tbody>
          {questionnaires.length === 0 ? (
            <tr>
              <td colSpan={7} style={styles.emptyState}>
                No questionnaires found. Create one or initialize defaults.
              </td>
            </tr>
          ) : (
            questionnaires.map((q) => {
              const typeColor = BADGE_COLORS[q.questionnaire_type] || BADGE_COLORS.general;
              return (
                <tr key={q.id}>
                  <td style={styles.td}>
                    <div style={{ fontWeight: 500 }}>{q.name}</div>
                    {q.description && (
                      <div style={{ fontSize: '12px', color: '#6b7280', marginTop: '2px' }}>
                        {q.description.substring(0, 50)}...
                      </div>
                    )}
                  </td>
                  <td style={styles.td}>
                    <span style={{ ...styles.badge, backgroundColor: typeColor.bg, color: typeColor.color }}>
                      {q.questionnaire_type.replace(/_/g, ' ')}
                    </span>
                  </td>
                  <td style={styles.td}>{q.question_count}</td>
                  <td style={styles.td}>{q.times_completed}</td>
                  <td style={styles.td}>
                    {q.average_risk_score !== null ? (
                      <span style={{
                        ...styles.badge,
                        backgroundColor: q.average_risk_score > 50 ? '#fee2e2' : q.average_risk_score > 25 ? '#fef3c7' : '#dcfce7',
                        color: q.average_risk_score > 50 ? '#dc2626' : q.average_risk_score > 25 ? '#d97706' : '#16a34a',
                      }}>
                        {q.average_risk_score}
                      </span>
                    ) : '—'}
                  </td>
                  <td style={styles.td}>
                    <span style={{
                      ...styles.badge,
                      backgroundColor: q.is_active ? '#dcfce7' : '#f3f4f6',
                      color: q.is_active ? '#16a34a' : '#6b7280',
                    }}>
                      {q.is_active ? 'Active' : 'Inactive'}
                    </span>
                  </td>
                  <td style={{ ...styles.td, position: 'relative' }}>
                    <button
                      style={styles.menuButton}
                      onClick={() => setOpenMenu(openMenu === q.id ? null : q.id)}
                    >
                      <MoreVertical size={16} />
                    </button>
                    {openMenu === q.id && (
                      <div style={styles.dropdown}>
                        <button style={styles.dropdownItem} onClick={() => { setPreviewId(q.id); setOpenMenu(null); }}>
                          <Eye size={14} /> Preview
                        </button>
                        <button style={styles.dropdownItem} onClick={() => handleEdit(q.id)}>
                          <Edit size={14} /> Edit
                        </button>
                        <button style={styles.dropdownItem}>
                          <Copy size={14} /> Duplicate
                        </button>
                        <button
                          style={{ ...styles.dropdownItem, color: '#dc2626' }}
                          onClick={() => handleDelete(q.id)}
                        >
                          <Trash2 size={14} /> Delete
                        </button>
                      </div>
                    )}
                  </td>
                </tr>
              );
            })
          )}
        </tbody>
      </table>

      {/* Pagination */}
      {totalPages > 1 && (
        <div style={styles.pagination}>
          <button
            style={styles.pageButton}
            onClick={() => setPage(p => Math.max(1, p - 1))}
            disabled={page === 1}
          >
            <ChevronLeft size={16} />
          </button>
          <span style={{ padding: '8px 16px' }}>
            Page {page} of {totalPages}
          </span>
          <button
            style={styles.pageButton}
            onClick={() => setPage(p => Math.min(totalPages, p + 1))}
            disabled={page === totalPages}
          >
            <ChevronRight size={16} />
          </button>
        </div>
      )}

      {/* Builder Modal */}
      {builderOpen && (
        <div style={styles.modal} onClick={() => setBuilderOpen(false)}>
          <div style={styles.modalContent} onClick={(e) => e.stopPropagation()}>
            <h2 style={{ margin: '0 0 16px', fontSize: '20px' }}>
              {editingId ? 'Edit Questionnaire' : 'Create Questionnaire'}
            </h2>
            <QuestionnaireBuilder
              questionnaireId={editingId}
              onClose={() => setBuilderOpen(false)}
            />
          </div>
        </div>
      )}

      {/* Preview Modal */}
      {previewId && (
        <div style={styles.modal} onClick={() => setPreviewId(null)}>
          <div style={styles.modalContent} onClick={(e) => e.stopPropagation()}>
            <h2 style={{ margin: '0 0 16px', fontSize: '20px' }}>Questionnaire Preview</h2>
            <QuestionnairePreview questionnaireId={previewId} />
            <button
              style={{ ...styles.button, ...styles.secondaryButton, marginTop: '16px' }}
              onClick={() => setPreviewId(null)}
            >
              Close
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
