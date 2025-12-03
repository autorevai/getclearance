import React, { useState } from 'react';
import {
  Plus,
  Trash2,
  RefreshCw,
  Key,
  Copy,
  Check,
  AlertTriangle,
  Loader2,
  X,
} from 'lucide-react';
import {
  useApiKeys,
  useAvailablePermissions,
  useCreateApiKey,
  useRevokeApiKey,
  useRotateApiKey,
} from '../../hooks';

function formatDate(dateStr) {
  if (!dateStr) return 'Never';
  const date = new Date(dateStr);
  return date.toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  });
}

export default function ApiKeysTab() {
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showKeyModal, setShowKeyModal] = useState(false);
  const [newKey, setNewKey] = useState(null);

  const { data, isLoading } = useApiKeys();
  const revokeApiKey = useRevokeApiKey();
  const rotateApiKey = useRotateApiKey();

  const keys = data?.items || [];

  const handleRevoke = async (keyId) => {
    if (window.confirm('Are you sure you want to revoke this API key? This cannot be undone.')) {
      await revokeApiKey.mutateAsync(keyId);
    }
  };

  const handleRotate = async (keyId) => {
    if (window.confirm('Rotating will revoke the current key and create a new one. Continue?')) {
      const result = await rotateApiKey.mutateAsync(keyId);
      setNewKey(result);
      setShowKeyModal(true);
    }
  };

  const handleKeyCreated = (key) => {
    setNewKey(key);
    setShowCreateModal(false);
    setShowKeyModal(true);
  };

  return (
    <div className="api-keys-tab">
      <style>{`
        .api-keys-tab {
          background: var(--bg-secondary, #111318);
          border: 1px solid var(--border-color, #2a2f3a);
          border-radius: 12px;
        }

        .tab-header {
          display: flex;
          align-items: center;
          justify-content: space-between;
          padding: 20px;
          border-bottom: 1px solid var(--border-color, #2a2f3a);
        }

        .tab-title {
          font-size: 16px;
          font-weight: 600;
          color: var(--text-primary, #f0f2f5);
        }

        .create-btn {
          display: flex;
          align-items: center;
          gap: 8px;
          padding: 8px 16px;
          background: var(--accent-primary, #6366f1);
          border: none;
          border-radius: 8px;
          color: white;
          font-size: 14px;
          font-weight: 500;
          cursor: pointer;
          transition: all 0.15s;
          font-family: inherit;
        }

        .create-btn:hover {
          background: var(--accent-hover, #5558e8);
        }

        .create-btn svg {
          width: 16px;
          height: 16px;
        }

        .keys-table {
          width: 100%;
          border-collapse: collapse;
        }

        .keys-table th {
          text-align: left;
          padding: 12px 20px;
          font-size: 12px;
          font-weight: 600;
          text-transform: uppercase;
          letter-spacing: 0.05em;
          color: var(--text-muted, #5c6370);
          background: var(--bg-tertiary, #1a1d24);
          border-bottom: 1px solid var(--border-color, #2a2f3a);
        }

        .keys-table td {
          padding: 16px 20px;
          border-bottom: 1px solid var(--border-color, #2a2f3a);
          font-size: 14px;
          color: var(--text-primary, #f0f2f5);
        }

        .keys-table tbody tr:last-child td {
          border-bottom: none;
        }

        .key-name {
          font-weight: 500;
        }

        .key-prefix {
          font-family: monospace;
          font-size: 13px;
          color: var(--text-secondary, #8b919e);
          background: var(--bg-tertiary, #1a1d24);
          padding: 4px 8px;
          border-radius: 4px;
        }

        .key-status {
          display: inline-flex;
          align-items: center;
          padding: 4px 8px;
          border-radius: 4px;
          font-size: 12px;
          font-weight: 500;
        }

        .key-status.active {
          background: rgba(16, 185, 129, 0.15);
          color: var(--success, #10b981);
        }

        .key-status.revoked {
          background: rgba(239, 68, 68, 0.15);
          color: var(--danger, #ef4444);
        }

        .key-actions {
          display: flex;
          gap: 8px;
        }

        .action-btn {
          display: flex;
          align-items: center;
          justify-content: center;
          width: 32px;
          height: 32px;
          background: var(--bg-tertiary, #1a1d24);
          border: 1px solid var(--border-color, #2a2f3a);
          border-radius: 6px;
          color: var(--text-secondary, #8b919e);
          cursor: pointer;
          transition: all 0.15s;
        }

        .action-btn:hover:not(:disabled) {
          background: var(--bg-hover, #22262f);
          color: var(--text-primary, #f0f2f5);
          border-color: var(--accent-primary, #6366f1);
        }

        .action-btn:disabled {
          opacity: 0.5;
          cursor: not-allowed;
        }

        .action-btn.danger:hover:not(:disabled) {
          border-color: var(--danger, #ef4444);
          color: var(--danger, #ef4444);
        }

        .empty-state {
          padding: 60px 20px;
          text-align: center;
          color: var(--text-secondary, #8b919e);
        }

        .empty-state svg {
          width: 48px;
          height: 48px;
          margin-bottom: 16px;
          opacity: 0.5;
        }

        .loading-state {
          display: flex;
          align-items: center;
          justify-content: center;
          padding: 60px;
          color: var(--text-secondary, #8b919e);
        }

        .spinner {
          animation: spin 1s linear infinite;
        }

        @keyframes spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
      `}</style>

      <div className="tab-header">
        <div className="tab-title">API Keys</div>
        <button className="create-btn" onClick={() => setShowCreateModal(true)}>
          <Plus />
          Create API Key
        </button>
      </div>

      {isLoading ? (
        <div className="loading-state">
          <Loader2 className="spinner" size={24} />
        </div>
      ) : keys.length === 0 ? (
        <div className="empty-state">
          <Key />
          <div>No API keys created yet</div>
          <div style={{ fontSize: 13, marginTop: 8 }}>
            Create an API key to get started with the API
          </div>
        </div>
      ) : (
        <table className="keys-table">
          <thead>
            <tr>
              <th>Name</th>
              <th>Key</th>
              <th>Last Used</th>
              <th>Created</th>
              <th>Status</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {keys.map((key) => (
              <tr key={key.id}>
                <td className="key-name">{key.name}</td>
                <td>
                  <span className="key-prefix">{key.key_prefix}...</span>
                </td>
                <td>{formatDate(key.last_used_at)}</td>
                <td>{formatDate(key.created_at)}</td>
                <td>
                  <span className={`key-status ${key.is_active ? 'active' : 'revoked'}`}>
                    {key.is_active ? 'Active' : 'Revoked'}
                  </span>
                </td>
                <td>
                  <div className="key-actions">
                    <button
                      className="action-btn"
                      title="Rotate key"
                      onClick={() => handleRotate(key.id)}
                      disabled={!key.is_active || rotateApiKey.isPending}
                    >
                      <RefreshCw size={14} />
                    </button>
                    <button
                      className="action-btn danger"
                      title="Revoke key"
                      onClick={() => handleRevoke(key.id)}
                      disabled={!key.is_active || revokeApiKey.isPending}
                    >
                      <Trash2 size={14} />
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      {showCreateModal && (
        <CreateApiKeyModal
          onClose={() => setShowCreateModal(false)}
          onCreated={handleKeyCreated}
        />
      )}

      {showKeyModal && newKey && (
        <KeyCreatedModal
          keyData={newKey}
          onClose={() => {
            setShowKeyModal(false);
            setNewKey(null);
          }}
        />
      )}
    </div>
  );
}

function CreateApiKeyModal({ onClose, onCreated }) {
  const [name, setName] = useState('');
  const [selectedPermissions, setSelectedPermissions] = useState([]);

  const { data: permissionsData } = useAvailablePermissions();
  const createApiKey = useCreateApiKey();

  const permissions = permissionsData?.permissions || [];

  const handleSubmit = async (e) => {
    e.preventDefault();
    const result = await createApiKey.mutateAsync({
      name,
      permissions: selectedPermissions,
    });
    onCreated(result);
  };

  const togglePermission = (perm) => {
    setSelectedPermissions((prev) =>
      prev.includes(perm) ? prev.filter((p) => p !== perm) : [...prev, perm]
    );
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <style>{`
        .modal-overlay {
          position: fixed;
          inset: 0;
          background: rgba(0, 0, 0, 0.7);
          display: flex;
          align-items: center;
          justify-content: center;
          z-index: 1000;
          padding: 20px;
        }

        .modal-content {
          background: var(--bg-secondary, #111318);
          border: 1px solid var(--border-color, #2a2f3a);
          border-radius: 16px;
          width: 100%;
          max-width: 500px;
          max-height: 90vh;
          overflow: hidden;
        }

        .modal-header {
          display: flex;
          align-items: center;
          justify-content: space-between;
          padding: 20px 24px;
          border-bottom: 1px solid var(--border-color, #2a2f3a);
        }

        .modal-title {
          font-size: 18px;
          font-weight: 600;
          color: var(--text-primary, #f0f2f5);
        }

        .close-btn {
          display: flex;
          align-items: center;
          justify-content: center;
          width: 32px;
          height: 32px;
          background: transparent;
          border: 1px solid var(--border-color, #2a2f3a);
          border-radius: 6px;
          color: var(--text-secondary, #8b919e);
          cursor: pointer;
          transition: all 0.15s;
        }

        .close-btn:hover {
          background: var(--bg-tertiary, #1a1d24);
          color: var(--text-primary, #f0f2f5);
        }

        .modal-body {
          padding: 24px;
          overflow-y: auto;
        }

        .form-group {
          margin-bottom: 20px;
        }

        .form-label {
          display: block;
          font-size: 13px;
          font-weight: 500;
          color: var(--text-secondary, #8b919e);
          margin-bottom: 8px;
        }

        .form-input {
          width: 100%;
          padding: 10px 12px;
          background: var(--bg-tertiary, #1a1d24);
          border: 1px solid var(--border-color, #2a2f3a);
          border-radius: 8px;
          color: var(--text-primary, #f0f2f5);
          font-size: 14px;
          font-family: inherit;
        }

        .form-input:focus {
          outline: none;
          border-color: var(--accent-primary, #6366f1);
        }

        .permissions-grid {
          display: grid;
          grid-template-columns: repeat(2, 1fr);
          gap: 8px;
        }

        .permission-checkbox {
          display: flex;
          align-items: center;
          gap: 8px;
          padding: 8px 12px;
          background: var(--bg-tertiary, #1a1d24);
          border: 1px solid var(--border-color, #2a2f3a);
          border-radius: 6px;
          cursor: pointer;
          transition: all 0.15s;
        }

        .permission-checkbox:hover {
          border-color: var(--accent-primary, #6366f1);
        }

        .permission-checkbox.selected {
          background: var(--accent-glow, rgba(99, 102, 241, 0.1));
          border-color: var(--accent-primary, #6366f1);
        }

        .permission-checkbox input {
          display: none;
        }

        .permission-label {
          font-size: 13px;
          color: var(--text-primary, #f0f2f5);
        }

        .modal-footer {
          display: flex;
          justify-content: flex-end;
          gap: 12px;
          padding: 16px 24px;
          border-top: 1px solid var(--border-color, #2a2f3a);
        }

        .btn {
          padding: 10px 20px;
          border-radius: 8px;
          font-size: 14px;
          font-weight: 500;
          cursor: pointer;
          transition: all 0.15s;
          font-family: inherit;
        }

        .btn-secondary {
          background: var(--bg-tertiary, #1a1d24);
          border: 1px solid var(--border-color, #2a2f3a);
          color: var(--text-primary, #f0f2f5);
        }

        .btn-secondary:hover {
          background: var(--bg-hover, #22262f);
        }

        .btn-primary {
          background: var(--accent-primary, #6366f1);
          border: none;
          color: white;
        }

        .btn-primary:hover:not(:disabled) {
          background: var(--accent-hover, #5558e8);
        }

        .btn-primary:disabled {
          opacity: 0.6;
          cursor: not-allowed;
        }
      `}</style>

      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h2 className="modal-title">Create API Key</h2>
          <button className="close-btn" onClick={onClose}>
            <X size={18} />
          </button>
        </div>

        <form onSubmit={handleSubmit}>
          <div className="modal-body">
            <div className="form-group">
              <label className="form-label">Name</label>
              <input
                type="text"
                className="form-input"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="e.g., Production API Key"
                required
              />
            </div>

            <div className="form-group">
              <label className="form-label">Permissions</label>
              <div className="permissions-grid">
                {permissions.map((perm) => (
                  <label
                    key={perm}
                    className={`permission-checkbox ${
                      selectedPermissions.includes(perm) ? 'selected' : ''
                    }`}
                  >
                    <input
                      type="checkbox"
                      checked={selectedPermissions.includes(perm)}
                      onChange={() => togglePermission(perm)}
                    />
                    <span className="permission-label">{perm}</span>
                  </label>
                ))}
              </div>
            </div>
          </div>

          <div className="modal-footer">
            <button type="button" className="btn btn-secondary" onClick={onClose}>
              Cancel
            </button>
            <button
              type="submit"
              className="btn btn-primary"
              disabled={!name || createApiKey.isPending}
            >
              {createApiKey.isPending ? 'Creating...' : 'Create Key'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

function KeyCreatedModal({ keyData, onClose }) {
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(keyData.key);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <style>{`
        .key-created-modal {
          background: var(--bg-secondary, #111318);
          border: 1px solid var(--border-color, #2a2f3a);
          border-radius: 16px;
          width: 100%;
          max-width: 500px;
          padding: 24px;
        }

        .key-created-icon {
          display: flex;
          align-items: center;
          justify-content: center;
          width: 56px;
          height: 56px;
          background: rgba(16, 185, 129, 0.15);
          border-radius: 12px;
          color: var(--success, #10b981);
          margin: 0 auto 16px;
        }

        .key-created-title {
          font-size: 20px;
          font-weight: 600;
          text-align: center;
          color: var(--text-primary, #f0f2f5);
          margin-bottom: 8px;
        }

        .key-created-warning {
          display: flex;
          align-items: center;
          gap: 8px;
          padding: 12px;
          background: rgba(245, 158, 11, 0.1);
          border: 1px solid rgba(245, 158, 11, 0.3);
          border-radius: 8px;
          color: var(--warning, #f59e0b);
          font-size: 13px;
          margin-bottom: 20px;
        }

        .key-display {
          background: var(--bg-tertiary, #1a1d24);
          border: 1px solid var(--border-color, #2a2f3a);
          border-radius: 8px;
          padding: 16px;
          margin-bottom: 20px;
        }

        .key-value {
          font-family: monospace;
          font-size: 13px;
          color: var(--text-primary, #f0f2f5);
          word-break: break-all;
          margin-bottom: 12px;
        }

        .copy-btn {
          display: flex;
          align-items: center;
          justify-content: center;
          gap: 8px;
          width: 100%;
          padding: 10px;
          background: var(--accent-primary, #6366f1);
          border: none;
          border-radius: 6px;
          color: white;
          font-size: 14px;
          font-weight: 500;
          cursor: pointer;
          transition: all 0.15s;
          font-family: inherit;
        }

        .copy-btn:hover {
          background: var(--accent-hover, #5558e8);
        }

        .copy-btn.copied {
          background: var(--success, #10b981);
        }

        .done-btn {
          width: 100%;
          padding: 12px;
          background: var(--bg-tertiary, #1a1d24);
          border: 1px solid var(--border-color, #2a2f3a);
          border-radius: 8px;
          color: var(--text-primary, #f0f2f5);
          font-size: 14px;
          font-weight: 500;
          cursor: pointer;
          transition: all 0.15s;
          font-family: inherit;
        }

        .done-btn:hover {
          background: var(--bg-hover, #22262f);
        }
      `}</style>

      <div className="key-created-modal" onClick={(e) => e.stopPropagation()}>
        <div className="key-created-icon">
          <Check size={28} />
        </div>

        <h2 className="key-created-title">API Key Created</h2>

        <div className="key-created-warning">
          <AlertTriangle size={16} />
          <span>This key will only be shown once. Copy and store it securely!</span>
        </div>

        <div className="key-display">
          <div className="key-value">{keyData.key}</div>
          <button className={`copy-btn ${copied ? 'copied' : ''}`} onClick={handleCopy}>
            {copied ? (
              <>
                <Check size={16} />
                Copied!
              </>
            ) : (
              <>
                <Copy size={16} />
                Copy to Clipboard
              </>
            )}
          </button>
        </div>

        <button className="done-btn" onClick={onClose}>
          Done
        </button>
      </div>
    </div>
  );
}
