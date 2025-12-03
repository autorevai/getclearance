import React, { useState } from 'react';
import {
  Plus,
  Trash2,
  Play,
  Pause,
  Send,
  List,
  Webhook,
  Loader2,
  X,
  Check,
  AlertCircle,
} from 'lucide-react';
import {
  useWebhooks,
  useAvailableEvents,
  useCreateWebhook,
  useUpdateWebhook,
  useDeleteWebhook,
  useTestWebhook,
  useWebhookLogs,
} from '../../hooks';

function formatDate(dateStr) {
  if (!dateStr) return 'Never';
  const date = new Date(dateStr);
  return date.toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}

function getStatusColor(status) {
  switch (status) {
    case 'active':
      return 'success';
    case 'paused':
      return 'muted';
    case 'degraded':
      return 'warning';
    case 'failing':
      return 'danger';
    default:
      return 'muted';
  }
}

export default function WebhooksTab() {
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showLogsModal, setShowLogsModal] = useState(false);
  const [selectedWebhook, setSelectedWebhook] = useState(null);

  const { data, isLoading } = useWebhooks();
  const updateWebhook = useUpdateWebhook();
  const deleteWebhook = useDeleteWebhook();
  const testWebhook = useTestWebhook();

  const webhooks = data?.items || [];

  const handleToggleActive = async (webhook) => {
    await updateWebhook.mutateAsync({
      webhookId: webhook.id,
      data: { active: !webhook.active },
    });
  };

  const handleDelete = async (webhookId) => {
    if (window.confirm('Are you sure you want to delete this webhook?')) {
      await deleteWebhook.mutateAsync(webhookId);
    }
  };

  const handleTest = async (webhookId) => {
    await testWebhook.mutateAsync(webhookId);
  };

  const handleViewLogs = (webhook) => {
    setSelectedWebhook(webhook);
    setShowLogsModal(true);
  };

  return (
    <div className="webhooks-tab">
      <style>{`
        .webhooks-tab {
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

        .webhooks-table {
          width: 100%;
          border-collapse: collapse;
        }

        .webhooks-table th {
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

        .webhooks-table td {
          padding: 16px 20px;
          border-bottom: 1px solid var(--border-color, #2a2f3a);
          font-size: 14px;
          color: var(--text-primary, #f0f2f5);
        }

        .webhooks-table tbody tr:last-child td {
          border-bottom: none;
        }

        .webhook-name {
          font-weight: 500;
        }

        .webhook-url {
          font-family: monospace;
          font-size: 12px;
          color: var(--text-secondary, #8b919e);
          max-width: 200px;
          overflow: hidden;
          text-overflow: ellipsis;
          white-space: nowrap;
        }

        .events-badge {
          display: inline-flex;
          padding: 4px 8px;
          background: var(--bg-tertiary, #1a1d24);
          border-radius: 4px;
          font-size: 12px;
          color: var(--text-secondary, #8b919e);
        }

        .webhook-status {
          display: inline-flex;
          align-items: center;
          padding: 4px 8px;
          border-radius: 4px;
          font-size: 12px;
          font-weight: 500;
          text-transform: capitalize;
        }

        .webhook-status.success {
          background: rgba(16, 185, 129, 0.15);
          color: var(--success, #10b981);
        }

        .webhook-status.warning {
          background: rgba(245, 158, 11, 0.15);
          color: var(--warning, #f59e0b);
        }

        .webhook-status.danger {
          background: rgba(239, 68, 68, 0.15);
          color: var(--danger, #ef4444);
        }

        .webhook-status.muted {
          background: var(--bg-tertiary, #1a1d24);
          color: var(--text-muted, #5c6370);
        }

        .webhook-actions {
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
        <div className="tab-title">Webhooks</div>
        <button className="create-btn" onClick={() => setShowCreateModal(true)}>
          <Plus size={16} />
          Create Webhook
        </button>
      </div>

      {isLoading ? (
        <div className="loading-state">
          <Loader2 className="spinner" size={24} />
        </div>
      ) : webhooks.length === 0 ? (
        <div className="empty-state">
          <Webhook />
          <div>No webhooks configured yet</div>
          <div style={{ fontSize: 13, marginTop: 8 }}>
            Create a webhook to receive real-time event notifications
          </div>
        </div>
      ) : (
        <table className="webhooks-table">
          <thead>
            <tr>
              <th>Name</th>
              <th>URL</th>
              <th>Events</th>
              <th>Status</th>
              <th>Last Delivery</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {webhooks.map((webhook) => (
              <tr key={webhook.id}>
                <td className="webhook-name">{webhook.name}</td>
                <td>
                  <span className="webhook-url" title={webhook.url}>
                    {webhook.url}
                  </span>
                </td>
                <td>
                  <span className="events-badge">
                    {webhook.events.length} events
                  </span>
                </td>
                <td>
                  <span className={`webhook-status ${getStatusColor(webhook.status)}`}>
                    {webhook.status}
                  </span>
                </td>
                <td>{formatDate(webhook.last_success_at)}</td>
                <td>
                  <div className="webhook-actions">
                    <button
                      className="action-btn"
                      title={webhook.active ? 'Pause' : 'Activate'}
                      onClick={() => handleToggleActive(webhook)}
                      disabled={updateWebhook.isPending}
                    >
                      {webhook.active ? <Pause size={14} /> : <Play size={14} />}
                    </button>
                    <button
                      className="action-btn"
                      title="Test webhook"
                      onClick={() => handleTest(webhook.id)}
                      disabled={testWebhook.isPending}
                    >
                      <Send size={14} />
                    </button>
                    <button
                      className="action-btn"
                      title="View logs"
                      onClick={() => handleViewLogs(webhook)}
                    >
                      <List size={14} />
                    </button>
                    <button
                      className="action-btn danger"
                      title="Delete"
                      onClick={() => handleDelete(webhook.id)}
                      disabled={deleteWebhook.isPending}
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
        <CreateWebhookModal onClose={() => setShowCreateModal(false)} />
      )}

      {showLogsModal && selectedWebhook && (
        <WebhookLogsModal
          webhook={selectedWebhook}
          onClose={() => {
            setShowLogsModal(false);
            setSelectedWebhook(null);
          }}
        />
      )}
    </div>
  );
}

function CreateWebhookModal({ onClose }) {
  const [name, setName] = useState('');
  const [url, setUrl] = useState('');
  const [selectedEvents, setSelectedEvents] = useState([]);

  const { data: eventsData } = useAvailableEvents();
  const createWebhook = useCreateWebhook();

  const events = eventsData?.events || [];

  const handleSubmit = async (e) => {
    e.preventDefault();
    await createWebhook.mutateAsync({
      name,
      url,
      events: selectedEvents,
      active: true,
    });
    onClose();
  };

  const toggleEvent = (event) => {
    setSelectedEvents((prev) =>
      prev.includes(event) ? prev.filter((e) => e !== event) : [...prev, event]
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
          display: flex;
          flex-direction: column;
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
        }

        .modal-body {
          padding: 24px;
          overflow-y: auto;
          flex: 1;
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

        .events-list {
          max-height: 200px;
          overflow-y: auto;
          border: 1px solid var(--border-color, #2a2f3a);
          border-radius: 8px;
        }

        .event-checkbox {
          display: flex;
          align-items: center;
          gap: 10px;
          padding: 10px 12px;
          border-bottom: 1px solid var(--border-color, #2a2f3a);
          cursor: pointer;
          transition: background 0.15s;
        }

        .event-checkbox:last-child {
          border-bottom: none;
        }

        .event-checkbox:hover {
          background: var(--bg-tertiary, #1a1d24);
        }

        .event-checkbox.selected {
          background: var(--accent-glow, rgba(99, 102, 241, 0.1));
        }

        .event-checkbox input {
          display: none;
        }

        .event-check {
          width: 18px;
          height: 18px;
          border: 1px solid var(--border-color, #2a2f3a);
          border-radius: 4px;
          display: flex;
          align-items: center;
          justify-content: center;
          color: white;
        }

        .event-checkbox.selected .event-check {
          background: var(--accent-primary, #6366f1);
          border-color: var(--accent-primary, #6366f1);
        }

        .event-label {
          font-size: 13px;
          color: var(--text-primary, #f0f2f5);
          font-family: monospace;
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
          font-family: inherit;
        }

        .btn-secondary {
          background: var(--bg-tertiary, #1a1d24);
          border: 1px solid var(--border-color, #2a2f3a);
          color: var(--text-primary, #f0f2f5);
        }

        .btn-primary {
          background: var(--accent-primary, #6366f1);
          border: none;
          color: white;
        }

        .btn-primary:disabled {
          opacity: 0.6;
          cursor: not-allowed;
        }
      `}</style>

      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h2 className="modal-title">Create Webhook</h2>
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
                placeholder="e.g., Production Webhook"
                required
              />
            </div>

            <div className="form-group">
              <label className="form-label">URL</label>
              <input
                type="url"
                className="form-input"
                value={url}
                onChange={(e) => setUrl(e.target.value)}
                placeholder="https://your-server.com/webhook"
                required
              />
            </div>

            <div className="form-group">
              <label className="form-label">Events ({selectedEvents.length} selected)</label>
              <div className="events-list">
                {events.map((event) => (
                  <label
                    key={event}
                    className={`event-checkbox ${
                      selectedEvents.includes(event) ? 'selected' : ''
                    }`}
                  >
                    <input
                      type="checkbox"
                      checked={selectedEvents.includes(event)}
                      onChange={() => toggleEvent(event)}
                    />
                    <span className="event-check">
                      {selectedEvents.includes(event) && <Check size={12} />}
                    </span>
                    <span className="event-label">{event}</span>
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
              disabled={!name || !url || selectedEvents.length === 0 || createWebhook.isPending}
            >
              {createWebhook.isPending ? 'Creating...' : 'Create Webhook'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

function WebhookLogsModal({ webhook, onClose }) {
  const { data, isLoading } = useWebhookLogs(webhook.id);
  const logs = data?.items || [];

  return (
    <div className="modal-overlay" onClick={onClose}>
      <style>{`
        .logs-modal {
          background: var(--bg-secondary, #111318);
          border: 1px solid var(--border-color, #2a2f3a);
          border-radius: 16px;
          width: 100%;
          max-width: 700px;
          max-height: 90vh;
          overflow: hidden;
          display: flex;
          flex-direction: column;
        }

        .logs-header {
          display: flex;
          align-items: center;
          justify-content: space-between;
          padding: 20px 24px;
          border-bottom: 1px solid var(--border-color, #2a2f3a);
        }

        .logs-title {
          font-size: 18px;
          font-weight: 600;
          color: var(--text-primary, #f0f2f5);
        }

        .logs-content {
          flex: 1;
          overflow-y: auto;
        }

        .logs-table {
          width: 100%;
          border-collapse: collapse;
        }

        .logs-table th {
          text-align: left;
          padding: 12px 20px;
          font-size: 12px;
          font-weight: 600;
          text-transform: uppercase;
          color: var(--text-muted, #5c6370);
          background: var(--bg-tertiary, #1a1d24);
          border-bottom: 1px solid var(--border-color, #2a2f3a);
          position: sticky;
          top: 0;
        }

        .logs-table td {
          padding: 12px 20px;
          border-bottom: 1px solid var(--border-color, #2a2f3a);
          font-size: 13px;
          color: var(--text-primary, #f0f2f5);
        }

        .log-status {
          display: inline-flex;
          align-items: center;
          gap: 4px;
        }

        .log-status.success {
          color: var(--success, #10b981);
        }

        .log-status.failed {
          color: var(--danger, #ef4444);
        }

        .log-event {
          font-family: monospace;
          font-size: 12px;
        }

        .empty-logs {
          padding: 40px 20px;
          text-align: center;
          color: var(--text-muted, #5c6370);
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
        }
      `}</style>

      <div className="logs-modal" onClick={(e) => e.stopPropagation()}>
        <div className="logs-header">
          <h2 className="logs-title">Delivery Logs - {webhook.name}</h2>
          <button className="close-btn" onClick={onClose}>
            <X size={18} />
          </button>
        </div>

        <div className="logs-content">
          {isLoading ? (
            <div className="empty-logs">
              <Loader2 className="spinner" size={24} />
            </div>
          ) : logs.length === 0 ? (
            <div className="empty-logs">No delivery logs yet</div>
          ) : (
            <table className="logs-table">
              <thead>
                <tr>
                  <th>Event</th>
                  <th>Status</th>
                  <th>Response</th>
                  <th>Time</th>
                  <th>Delivered</th>
                </tr>
              </thead>
              <tbody>
                {logs.map((log) => (
                  <tr key={log.id}>
                    <td className="log-event">{log.event_type}</td>
                    <td>
                      <span className={`log-status ${log.success ? 'success' : 'failed'}`}>
                        {log.success ? <Check size={14} /> : <AlertCircle size={14} />}
                        {log.success ? 'Success' : 'Failed'}
                      </span>
                    </td>
                    <td>{log.response_code || '-'}</td>
                    <td>{log.response_time_ms ? `${log.response_time_ms}ms` : '-'}</td>
                    <td>{formatDate(log.delivered_at)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>
    </div>
  );
}
