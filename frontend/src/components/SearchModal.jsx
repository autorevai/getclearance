import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Search,
  X,
  Users,
  FolderKanban,
  ArrowRight,
  Loader2
} from 'lucide-react';
import { useGlobalSearch } from '../hooks/useGlobalSearch';
import { useDebounce } from '../hooks/useDebounce';

export default function SearchModal({ isOpen, onClose }) {
  const [query, setQuery] = useState('');
  const debouncedQuery = useDebounce(query, 300);
  const inputRef = useRef(null);
  const navigate = useNavigate();

  const { data: results, isLoading, error } = useGlobalSearch(debouncedQuery);

  // Focus input when modal opens
  useEffect(() => {
    if (isOpen && inputRef.current) {
      inputRef.current.focus();
    }
  }, [isOpen]);

  // Clear query when modal closes
  useEffect(() => {
    if (!isOpen) {
      setQuery('');
    }
  }, [isOpen]);

  // Handle keyboard navigation
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === 'Escape') {
        onClose();
      }
    };

    if (isOpen) {
      document.addEventListener('keydown', handleKeyDown);
    }

    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onClose]);

  const handleSelect = (type, id) => {
    navigate(type === 'applicant' ? `/applicants/${id}` : `/cases/${id}`);
    onClose();
  };

  if (!isOpen) return null;

  const hasResults = results && (results.applicants?.length > 0 || results.cases?.length > 0);
  const showNoResults = debouncedQuery.length >= 2 && !isLoading && !hasResults;

  return (
    <>
      <div className="search-modal-overlay" onClick={onClose} />
      <div className="search-modal">
        <style>{`
          .search-modal-overlay {
            position: fixed;
            inset: 0;
            background: rgba(0, 0, 0, 0.6);
            z-index: 1000;
            backdrop-filter: blur(4px);
          }

          .search-modal {
            position: fixed;
            top: 20%;
            left: 50%;
            transform: translateX(-50%);
            width: 90%;
            max-width: 560px;
            background: var(--bg-secondary);
            border: 1px solid var(--border-color);
            border-radius: 16px;
            box-shadow: 0 24px 48px rgba(0, 0, 0, 0.4);
            z-index: 1001;
            overflow: hidden;
          }

          .search-input-container {
            display: flex;
            align-items: center;
            gap: 12px;
            padding: 16px 20px;
            border-bottom: 1px solid var(--border-color);
          }

          .search-input-icon {
            color: var(--text-muted);
          }

          .search-modal-input {
            flex: 1;
            background: transparent;
            border: none;
            outline: none;
            font-size: 16px;
            color: var(--text-primary);
            font-family: inherit;
          }

          .search-modal-input::placeholder {
            color: var(--text-muted);
          }

          .search-close-btn {
            width: 32px;
            height: 32px;
            border-radius: 8px;
            border: none;
            background: var(--bg-tertiary);
            color: var(--text-muted);
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: all 0.15s;
          }

          .search-close-btn:hover {
            background: var(--bg-hover);
            color: var(--text-primary);
          }

          .search-results {
            max-height: 400px;
            overflow-y: auto;
          }

          .search-section {
            padding: 12px 20px;
          }

          .search-section-title {
            font-size: 11px;
            font-weight: 600;
            color: var(--text-muted);
            text-transform: uppercase;
            letter-spacing: 0.05em;
            margin-bottom: 8px;
            display: flex;
            align-items: center;
            gap: 8px;
          }

          .search-result-item {
            display: flex;
            align-items: center;
            gap: 12px;
            padding: 12px;
            border-radius: 8px;
            cursor: pointer;
            transition: all 0.15s;
          }

          .search-result-item:hover {
            background: var(--bg-hover);
          }

          .search-result-icon {
            width: 36px;
            height: 36px;
            border-radius: 8px;
            display: flex;
            align-items: center;
            justify-content: center;
            flex-shrink: 0;
          }

          .search-result-icon.applicant {
            background: rgba(99, 102, 241, 0.15);
            color: var(--accent-primary);
          }

          .search-result-icon.case {
            background: rgba(245, 158, 11, 0.15);
            color: var(--warning);
          }

          .search-result-content {
            flex: 1;
            min-width: 0;
          }

          .search-result-title {
            font-size: 14px;
            font-weight: 500;
            color: var(--text-primary);
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
          }

          .search-result-meta {
            font-size: 12px;
            color: var(--text-muted);
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
          }

          .search-result-arrow {
            color: var(--text-muted);
            opacity: 0;
            transition: opacity 0.15s;
          }

          .search-result-item:hover .search-result-arrow {
            opacity: 1;
          }

          .search-loading {
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 12px;
            padding: 40px 20px;
            color: var(--text-muted);
          }

          .search-loading svg {
            animation: spin 1s linear infinite;
          }

          @keyframes spin {
            from { transform: rotate(0deg); }
            to { transform: rotate(360deg); }
          }

          .search-empty {
            padding: 40px 20px;
            text-align: center;
            color: var(--text-muted);
          }

          .search-empty-icon {
            margin-bottom: 12px;
            opacity: 0.5;
          }

          .search-empty h4 {
            color: var(--text-primary);
            margin-bottom: 4px;
          }

          .search-hint {
            padding: 12px 20px;
            font-size: 12px;
            color: var(--text-muted);
            text-align: center;
            border-top: 1px solid var(--border-color);
          }

          .search-hint kbd {
            background: var(--bg-tertiary);
            padding: 2px 6px;
            border-radius: 4px;
            font-family: 'JetBrains Mono', monospace;
            font-size: 11px;
          }
        `}</style>

        <div className="search-input-container">
          <Search size={20} className="search-input-icon" />
          <input
            ref={inputRef}
            type="text"
            className="search-modal-input"
            placeholder="Search applicants, cases..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
          />
          <button className="search-close-btn" onClick={onClose}>
            <X size={16} />
          </button>
        </div>

        <div className="search-results">
          {isLoading && (
            <div className="search-loading">
              <Loader2 size={20} />
              Searching...
            </div>
          )}

          {error && (
            <div className="search-empty">
              <div className="search-empty-icon">
                <Search size={32} />
              </div>
              <h4>Search Error</h4>
              <p>Unable to search. Please try again.</p>
            </div>
          )}

          {showNoResults && (
            <div className="search-empty">
              <div className="search-empty-icon">
                <Search size={32} />
              </div>
              <h4>No results found</h4>
              <p>Try a different search term</p>
            </div>
          )}

          {hasResults && (
            <>
              {results.applicants?.length > 0 && (
                <div className="search-section">
                  <div className="search-section-title">
                    <Users size={14} />
                    Applicants ({results.applicants.length})
                  </div>
                  {results.applicants.map((applicant) => (
                    <div
                      key={applicant.id}
                      className="search-result-item"
                      onClick={() => handleSelect('applicant', applicant.id)}
                    >
                      <div className="search-result-icon applicant">
                        <Users size={16} />
                      </div>
                      <div className="search-result-content">
                        <div className="search-result-title">
                          {applicant.first_name && applicant.last_name
                            ? `${applicant.first_name} ${applicant.last_name}`
                            : applicant.email?.split('@')[0] || `Applicant ${applicant.id.slice(0, 8)}`}
                        </div>
                        <div className="search-result-meta">
                          {applicant.email} • {applicant.review_status || 'pending'}
                        </div>
                      </div>
                      <ArrowRight size={16} className="search-result-arrow" />
                    </div>
                  ))}
                </div>
              )}

              {results.cases?.length > 0 && (
                <div className="search-section">
                  <div className="search-section-title">
                    <FolderKanban size={14} />
                    Cases ({results.cases.length})
                  </div>
                  {results.cases.map((caseItem) => (
                    <div
                      key={caseItem.id}
                      className="search-result-item"
                      onClick={() => handleSelect('case', caseItem.id)}
                    >
                      <div className="search-result-icon case">
                        <FolderKanban size={16} />
                      </div>
                      <div className="search-result-content">
                        <div className="search-result-title">{caseItem.title}</div>
                        <div className="search-result-meta">
                          {caseItem.status} • {caseItem.priority || 'normal'} priority
                        </div>
                      </div>
                      <ArrowRight size={16} className="search-result-arrow" />
                    </div>
                  ))}
                </div>
              )}
            </>
          )}

          {!isLoading && query.length < 2 && (
            <div className="search-empty">
              <div className="search-empty-icon">
                <Search size={32} />
              </div>
              <h4>Search GetClearance</h4>
              <p>Type at least 2 characters to search</p>
            </div>
          )}
        </div>

        <div className="search-hint">
          Press <kbd>Esc</kbd> to close • <kbd>Enter</kbd> to select
        </div>
      </div>
    </>
  );
}
