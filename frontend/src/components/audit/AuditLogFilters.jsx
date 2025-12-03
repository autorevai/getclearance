import React, { useState, useEffect } from 'react';
import { Search, X, Filter } from 'lucide-react';
import { useAuditFilterOptions } from '../../hooks';
import { useDebounce } from '../../hooks';

export default function AuditLogFilters({ filters, onFilterChange }) {
  const [localFilters, setLocalFilters] = useState({
    search: '',
    action: '',
    resource_type: '',
    user_email: '',
    date_from: '',
    date_to: '',
  });

  const { data: filterOptions } = useAuditFilterOptions();
  const debouncedSearch = useDebounce(localFilters.search, 300);

  // Sync local filters with parent
  useEffect(() => {
    const newFilters = {
      action: localFilters.action,
      resource_type: localFilters.resource_type,
      user_email: localFilters.user_email,
      date_from: localFilters.date_from,
      date_to: localFilters.date_to,
    };
    // Remove empty values
    Object.keys(newFilters).forEach((key) => {
      if (!newFilters[key]) delete newFilters[key];
    });
    // Use debounced search
    if (debouncedSearch) {
      newFilters.search = debouncedSearch;
    } else {
      delete newFilters.search;
    }
    onFilterChange(newFilters);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [
    debouncedSearch,
    localFilters.action,
    localFilters.resource_type,
    localFilters.user_email,
    localFilters.date_from,
    localFilters.date_to,
  ]);

  const handleChange = (field, value) => {
    setLocalFilters((prev) => ({ ...prev, [field]: value }));
  };

  const clearFilters = () => {
    setLocalFilters({
      search: '',
      action: '',
      resource_type: '',
      user_email: '',
      date_from: '',
      date_to: '',
    });
  };

  const hasActiveFilters = Object.values(localFilters).some((v) => v);

  return (
    <div className="audit-filters">
      <style>{`
        .audit-filters {
          background: var(--bg-secondary, #111318);
          border: 1px solid var(--border-color, #2a2f3a);
          border-radius: 12px;
          padding: 16px;
          margin-bottom: 16px;
        }

        .filters-header {
          display: flex;
          align-items: center;
          justify-content: space-between;
          margin-bottom: 16px;
        }

        .filters-title {
          display: flex;
          align-items: center;
          gap: 8px;
          font-size: 14px;
          font-weight: 500;
          color: var(--text-primary, #f0f2f5);
        }

        .filters-title svg {
          width: 16px;
          height: 16px;
          color: var(--text-muted, #5c6370);
        }

        .clear-filters-btn {
          display: flex;
          align-items: center;
          gap: 6px;
          padding: 6px 12px;
          background: transparent;
          border: 1px solid var(--border-color, #2a2f3a);
          border-radius: 6px;
          color: var(--text-secondary, #8b919e);
          font-size: 13px;
          cursor: pointer;
          transition: all 0.15s;
          font-family: inherit;
        }

        .clear-filters-btn:hover {
          background: var(--bg-tertiary, #1a1d24);
          color: var(--text-primary, #f0f2f5);
        }

        .clear-filters-btn svg {
          width: 14px;
          height: 14px;
        }

        .filters-grid {
          display: grid;
          grid-template-columns: 2fr repeat(4, 1fr);
          gap: 12px;
        }

        @media (max-width: 1200px) {
          .filters-grid {
            grid-template-columns: repeat(3, 1fr);
          }
        }

        @media (max-width: 768px) {
          .filters-grid {
            grid-template-columns: 1fr 1fr;
          }
        }

        @media (max-width: 480px) {
          .filters-grid {
            grid-template-columns: 1fr;
          }
        }

        .filter-group {
          display: flex;
          flex-direction: column;
          gap: 6px;
        }

        .filter-label {
          font-size: 12px;
          font-weight: 500;
          color: var(--text-muted, #5c6370);
          text-transform: uppercase;
          letter-spacing: 0.05em;
        }

        .filter-input-wrapper {
          position: relative;
        }

        .filter-input-wrapper svg {
          position: absolute;
          left: 10px;
          top: 50%;
          transform: translateY(-50%);
          width: 16px;
          height: 16px;
          color: var(--text-muted, #5c6370);
          pointer-events: none;
        }

        .filter-input {
          width: 100%;
          padding: 10px 12px;
          padding-left: 36px;
          background: var(--bg-tertiary, #1a1d24);
          border: 1px solid var(--border-color, #2a2f3a);
          border-radius: 8px;
          color: var(--text-primary, #f0f2f5);
          font-size: 14px;
          font-family: inherit;
          transition: all 0.15s;
        }

        .filter-input:focus {
          outline: none;
          border-color: var(--accent-primary, #6366f1);
          box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.1);
        }

        .filter-input::placeholder {
          color: var(--text-muted, #5c6370);
        }

        .filter-select {
          width: 100%;
          padding: 10px 12px;
          background: var(--bg-tertiary, #1a1d24);
          border: 1px solid var(--border-color, #2a2f3a);
          border-radius: 8px;
          color: var(--text-primary, #f0f2f5);
          font-size: 14px;
          font-family: inherit;
          cursor: pointer;
          transition: all 0.15s;
          appearance: none;
          background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 24 24' fill='none' stroke='%235c6370' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpolyline points='6 9 12 15 18 9'%3E%3C/polyline%3E%3C/svg%3E");
          background-repeat: no-repeat;
          background-position: right 12px center;
          padding-right: 32px;
        }

        .filter-select:focus {
          outline: none;
          border-color: var(--accent-primary, #6366f1);
          box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.1);
        }

        .filter-select option {
          background: var(--bg-secondary, #111318);
          color: var(--text-primary, #f0f2f5);
        }

        .date-inputs {
          display: flex;
          gap: 8px;
        }

        .date-input {
          flex: 1;
          padding: 10px 12px;
          background: var(--bg-tertiary, #1a1d24);
          border: 1px solid var(--border-color, #2a2f3a);
          border-radius: 8px;
          color: var(--text-primary, #f0f2f5);
          font-size: 14px;
          font-family: inherit;
          transition: all 0.15s;
        }

        .date-input:focus {
          outline: none;
          border-color: var(--accent-primary, #6366f1);
          box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.1);
        }

        .date-input::-webkit-calendar-picker-indicator {
          filter: invert(0.5);
          cursor: pointer;
        }
      `}</style>

      <div className="filters-header">
        <div className="filters-title">
          <Filter />
          Filters
        </div>
        {hasActiveFilters && (
          <button className="clear-filters-btn" onClick={clearFilters}>
            <X />
            Clear all
          </button>
        )}
      </div>

      <div className="filters-grid">
        <div className="filter-group">
          <label className="filter-label">Search</label>
          <div className="filter-input-wrapper">
            <Search />
            <input
              type="text"
              className="filter-input"
              placeholder="Search by user, resource, or action..."
              value={localFilters.search}
              onChange={(e) => handleChange('search', e.target.value)}
            />
          </div>
        </div>

        <div className="filter-group">
          <label className="filter-label">Action</label>
          <select
            className="filter-select"
            value={localFilters.action}
            onChange={(e) => handleChange('action', e.target.value)}
          >
            <option value="">All actions</option>
            {filterOptions?.actions?.map((action) => (
              <option key={action} value={action}>
                {action.replace(/\./g, ' - ').replace(/_/g, ' ')}
              </option>
            ))}
          </select>
        </div>

        <div className="filter-group">
          <label className="filter-label">Resource Type</label>
          <select
            className="filter-select"
            value={localFilters.resource_type}
            onChange={(e) => handleChange('resource_type', e.target.value)}
          >
            <option value="">All types</option>
            {filterOptions?.resource_types?.map((type) => (
              <option key={type} value={type}>
                {type.charAt(0).toUpperCase() + type.slice(1)}
              </option>
            ))}
          </select>
        </div>

        <div className="filter-group">
          <label className="filter-label">User</label>
          <select
            className="filter-select"
            value={localFilters.user_email}
            onChange={(e) => handleChange('user_email', e.target.value)}
          >
            <option value="">All users</option>
            {filterOptions?.users?.map((user) => (
              <option key={user.email} value={user.email}>
                {user.email}
              </option>
            ))}
          </select>
        </div>

        <div className="filter-group">
          <label className="filter-label">Date Range</label>
          <div className="date-inputs">
            <input
              type="date"
              className="date-input"
              value={localFilters.date_from}
              onChange={(e) => handleChange('date_from', e.target.value)}
              placeholder="From"
            />
            <input
              type="date"
              className="date-input"
              value={localFilters.date_to}
              onChange={(e) => handleChange('date_to', e.target.value)}
              placeholder="To"
            />
          </div>
        </div>
      </div>
    </div>
  );
}
