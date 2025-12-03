import React, { useState } from 'react';
import {
  Users,
  UserPlus,
  Mail,
  MoreVertical,
  Trash2,
  Clock,
  Check,
  X,
  Loader2,
  RefreshCw,
  AlertCircle,
} from 'lucide-react';
import {
  useTeamMembers,
  useUpdateTeamMemberRole,
  useRemoveTeamMember,
  useInvitations,
  useInviteTeamMember,
  useCancelInvitation,
  useResendInvitation,
} from '../../hooks';

const roles = [
  { value: 'admin', label: 'Admin', description: 'Full access to all features' },
  { value: 'reviewer', label: 'Reviewer', description: 'Can review and approve applicants' },
  { value: 'analyst', label: 'Analyst', description: 'Can view and manage cases' },
  { value: 'viewer', label: 'Viewer', description: 'Read-only access' },
];

function InviteModal({ isOpen, onClose }) {
  const [email, setEmail] = useState('');
  const [role, setRole] = useState('analyst');
  const inviteMember = useInviteTeamMember();

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      await inviteMember.mutateAsync({ email, role });
      setEmail('');
      setRole('analyst');
      onClose();
    } catch (error) {
      console.error('Failed to send invitation:', error);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <h3>Invite Team Member</h3>
        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label className="form-label">Email Address</label>
            <input
              type="email"
              className="form-input"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="colleague@company.com"
              required
            />
          </div>
          <div className="form-group">
            <label className="form-label">Role</label>
            <select
              className="form-select"
              value={role}
              onChange={(e) => setRole(e.target.value)}
            >
              {roles.map((r) => (
                <option key={r.value} value={r.value}>
                  {r.label} - {r.description}
                </option>
              ))}
            </select>
          </div>
          <div className="modal-actions">
            <button type="button" className="btn-secondary" onClick={onClose}>
              Cancel
            </button>
            <button type="submit" className="btn-primary" disabled={inviteMember.isPending}>
              {inviteMember.isPending ? (
                <>
                  <Loader2 className="spinner" />
                  Sending...
                </>
              ) : (
                <>
                  <Mail />
                  Send Invitation
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

function MemberRow({ member, onUpdateRole, onRemove }) {
  const [menuOpen, setMenuOpen] = useState(false);
  const [roleMenuOpen, setRoleMenuOpen] = useState(false);

  const formatDate = (dateStr) => {
    if (!dateStr) return 'Never';
    return new Date(dateStr).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
    });
  };

  const getRoleColor = (role) => {
    switch (role) {
      case 'admin': return '#ef4444';
      case 'reviewer': return '#f59e0b';
      case 'analyst': return '#3b82f6';
      default: return '#6b7280';
    }
  };

  return (
    <tr className="member-row">
      <td>
        <div className="member-info">
          <div className="member-avatar">
            {member.avatar_url ? (
              <img src={member.avatar_url} alt="" />
            ) : (
              member.name?.[0] || member.email[0].toUpperCase()
            )}
          </div>
          <div>
            <div className="member-name">{member.name || 'Unnamed User'}</div>
            <div className="member-email">{member.email}</div>
          </div>
        </div>
      </td>
      <td>
        <div className="role-dropdown">
          <button
            className="role-badge"
            style={{ background: `${getRoleColor(member.role)}20`, color: getRoleColor(member.role) }}
            onClick={() => setRoleMenuOpen(!roleMenuOpen)}
          >
            {member.role.charAt(0).toUpperCase() + member.role.slice(1)}
          </button>
          {roleMenuOpen && (
            <>
              <div className="dropdown-overlay" onClick={() => setRoleMenuOpen(false)} />
              <div className="dropdown-menu">
                {roles.map((r) => (
                  <button
                    key={r.value}
                    className={`dropdown-item ${member.role === r.value ? 'active' : ''}`}
                    onClick={() => {
                      if (member.role !== r.value) {
                        onUpdateRole(member.id, r.value);
                      }
                      setRoleMenuOpen(false);
                    }}
                  >
                    <span>{r.label}</span>
                    {member.role === r.value && <Check size={14} />}
                  </button>
                ))}
              </div>
            </>
          )}
        </div>
      </td>
      <td className="last-active">
        <Clock size={14} />
        {formatDate(member.last_login_at)}
      </td>
      <td>
        <div className="actions">
          <button
            className="action-btn"
            onClick={() => setMenuOpen(!menuOpen)}
          >
            <MoreVertical size={16} />
          </button>
          {menuOpen && (
            <>
              <div className="dropdown-overlay" onClick={() => setMenuOpen(false)} />
              <div className="dropdown-menu">
                <button
                  className="dropdown-item danger"
                  onClick={() => {
                    onRemove(member.id);
                    setMenuOpen(false);
                  }}
                >
                  <Trash2 size={14} />
                  Remove from team
                </button>
              </div>
            </>
          )}
        </div>
      </td>
    </tr>
  );
}

function InvitationRow({ invitation, onCancel, onResend }) {
  const formatDate = (dateStr) => {
    return new Date(dateStr).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
    });
  };

  const isExpired = new Date(invitation.expires_at) < new Date();

  return (
    <tr className="invitation-row">
      <td>
        <div className="member-info">
          <div className="member-avatar pending">
            <Mail size={16} />
          </div>
          <div>
            <div className="member-email">{invitation.email}</div>
            <div className="invitation-status">
              {isExpired ? (
                <span className="status expired">
                  <AlertCircle size={12} />
                  Expired
                </span>
              ) : (
                <span className="status pending">
                  <Clock size={12} />
                  Pending - Expires {formatDate(invitation.expires_at)}
                </span>
              )}
            </div>
          </div>
        </div>
      </td>
      <td>
        <span className="role-badge" style={{ background: '#6b728020', color: '#6b7280' }}>
          {invitation.role.charAt(0).toUpperCase() + invitation.role.slice(1)}
        </span>
      </td>
      <td className="last-active">
        <Clock size={14} />
        Invited {formatDate(invitation.invited_at)}
      </td>
      <td>
        <div className="actions">
          <button
            className="action-btn"
            onClick={() => onResend(invitation.id)}
            title="Resend invitation"
          >
            <RefreshCw size={16} />
          </button>
          <button
            className="action-btn danger"
            onClick={() => onCancel(invitation.id)}
            title="Cancel invitation"
          >
            <X size={16} />
          </button>
        </div>
      </td>
    </tr>
  );
}

export default function TeamSettings() {
  const [inviteModalOpen, setInviteModalOpen] = useState(false);

  const { data: teamData, isLoading: loadingMembers } = useTeamMembers();
  const { data: invitationsData } = useInvitations();
  const updateRole = useUpdateTeamMemberRole();
  const removeMember = useRemoveTeamMember();
  const cancelInvitation = useCancelInvitation();
  const resendInvitation = useResendInvitation();

  const handleUpdateRole = async (memberId, role) => {
    try {
      await updateRole.mutateAsync({ memberId, role });
    } catch (error) {
      console.error('Failed to update role:', error);
    }
  };

  const handleRemoveMember = async (memberId) => {
    if (window.confirm('Are you sure you want to remove this team member?')) {
      try {
        await removeMember.mutateAsync(memberId);
      } catch (error) {
        console.error('Failed to remove member:', error);
      }
    }
  };

  const handleCancelInvitation = async (invitationId) => {
    try {
      await cancelInvitation.mutateAsync(invitationId);
    } catch (error) {
      console.error('Failed to cancel invitation:', error);
    }
  };

  const handleResendInvitation = async (invitationId) => {
    try {
      await resendInvitation.mutateAsync(invitationId);
    } catch (error) {
      console.error('Failed to resend invitation:', error);
    }
  };

  const members = teamData?.items || [];
  const invitations = invitationsData?.items || [];

  return (
    <div className="team-settings">
      <style>{`
        .team-settings h2 {
          font-size: 18px;
          font-weight: 600;
          color: var(--text-primary, #f0f2f5);
          margin: 0 0 8px;
          display: flex;
          align-items: center;
          gap: 8px;
        }

        .team-settings h2 svg {
          width: 20px;
          height: 20px;
          color: var(--accent-primary, #6366f1);
        }

        .section-description {
          font-size: 14px;
          color: var(--text-secondary, #8b919e);
          margin-bottom: 24px;
        }

        .team-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 16px;
        }

        .invite-btn {
          display: inline-flex;
          align-items: center;
          gap: 8px;
          padding: 8px 16px;
          background: var(--accent-primary, #6366f1);
          color: white;
          border: none;
          border-radius: 8px;
          font-size: 14px;
          font-weight: 500;
          cursor: pointer;
          transition: opacity 0.2s;
          font-family: inherit;
        }

        .invite-btn:hover {
          opacity: 0.9;
        }

        .invite-btn svg {
          width: 16px;
          height: 16px;
        }

        .team-table {
          width: 100%;
          border-collapse: collapse;
        }

        .team-table th {
          text-align: left;
          padding: 12px 16px;
          font-size: 12px;
          font-weight: 600;
          text-transform: uppercase;
          letter-spacing: 0.05em;
          color: var(--text-muted, #5c6370);
          border-bottom: 1px solid var(--border-color, #2a2f3a);
        }

        .team-table td {
          padding: 12px 16px;
          border-bottom: 1px solid var(--border-color, #2a2f3a);
        }

        .member-row:hover {
          background: var(--bg-hover, #22262f);
        }

        .member-info {
          display: flex;
          align-items: center;
          gap: 12px;
        }

        .member-avatar {
          width: 36px;
          height: 36px;
          border-radius: 50%;
          background: linear-gradient(135deg, #f59e0b, #ef4444);
          display: flex;
          align-items: center;
          justify-content: center;
          font-weight: 600;
          font-size: 14px;
          color: white;
          overflow: hidden;
        }

        .member-avatar img {
          width: 100%;
          height: 100%;
          object-fit: cover;
        }

        .member-avatar.pending {
          background: var(--bg-tertiary, #1a1d24);
          color: var(--text-muted, #5c6370);
        }

        .member-name {
          font-size: 14px;
          font-weight: 500;
          color: var(--text-primary, #f0f2f5);
        }

        .member-email {
          font-size: 13px;
          color: var(--text-secondary, #8b919e);
        }

        .role-dropdown {
          position: relative;
        }

        .role-badge {
          display: inline-flex;
          align-items: center;
          gap: 4px;
          padding: 4px 10px;
          border-radius: 6px;
          font-size: 12px;
          font-weight: 500;
          border: none;
          cursor: pointer;
          font-family: inherit;
        }

        .last-active {
          display: flex;
          align-items: center;
          gap: 6px;
          font-size: 13px;
          color: var(--text-secondary, #8b919e);
        }

        .actions {
          display: flex;
          gap: 4px;
          position: relative;
        }

        .action-btn {
          width: 32px;
          height: 32px;
          display: flex;
          align-items: center;
          justify-content: center;
          border-radius: 6px;
          background: transparent;
          border: none;
          color: var(--text-secondary, #8b919e);
          cursor: pointer;
          transition: all 0.15s;
        }

        .action-btn:hover {
          background: var(--bg-hover, #22262f);
          color: var(--text-primary, #f0f2f5);
        }

        .action-btn.danger:hover {
          background: rgba(239, 68, 68, 0.1);
          color: var(--danger, #ef4444);
        }

        .dropdown-overlay {
          position: fixed;
          inset: 0;
          z-index: 99;
        }

        .dropdown-menu {
          position: absolute;
          top: 100%;
          right: 0;
          margin-top: 4px;
          background: var(--bg-secondary, #111318);
          border: 1px solid var(--border-color, #2a2f3a);
          border-radius: 8px;
          box-shadow: 0 10px 40px rgba(0, 0, 0, 0.3);
          min-width: 180px;
          z-index: 100;
          overflow: hidden;
        }

        .dropdown-item {
          display: flex;
          align-items: center;
          justify-content: space-between;
          gap: 8px;
          width: 100%;
          padding: 10px 14px;
          background: none;
          border: none;
          color: var(--text-primary, #f0f2f5);
          font-size: 14px;
          cursor: pointer;
          transition: background 0.15s;
          font-family: inherit;
          text-align: left;
        }

        .dropdown-item:hover {
          background: var(--bg-hover, #22262f);
        }

        .dropdown-item.active {
          background: var(--accent-glow, rgba(99, 102, 241, 0.15));
          color: var(--accent-primary, #6366f1);
        }

        .dropdown-item.danger {
          color: var(--danger, #ef4444);
        }

        .dropdown-item.danger:hover {
          background: rgba(239, 68, 68, 0.1);
        }

        .invitation-status .status {
          display: inline-flex;
          align-items: center;
          gap: 4px;
          font-size: 12px;
        }

        .status.pending {
          color: var(--warning, #f59e0b);
        }

        .status.expired {
          color: var(--danger, #ef4444);
        }

        .section-divider {
          margin: 32px 0 24px;
          padding-top: 24px;
          border-top: 1px solid var(--border-color, #2a2f3a);
        }

        .section-divider h3 {
          font-size: 14px;
          font-weight: 600;
          color: var(--text-primary, #f0f2f5);
          margin: 0 0 16px;
          display: flex;
          align-items: center;
          gap: 8px;
        }

        .section-divider h3 svg {
          width: 16px;
          height: 16px;
          color: var(--text-muted, #5c6370);
        }

        /* Modal styles */
        .modal-overlay {
          position: fixed;
          inset: 0;
          background: rgba(0, 0, 0, 0.6);
          display: flex;
          align-items: center;
          justify-content: center;
          z-index: 1000;
        }

        .modal-content {
          background: var(--bg-secondary, #111318);
          border: 1px solid var(--border-color, #2a2f3a);
          border-radius: 12px;
          padding: 24px;
          width: 100%;
          max-width: 440px;
          box-shadow: 0 20px 60px rgba(0, 0, 0, 0.4);
        }

        .modal-content h3 {
          font-size: 18px;
          font-weight: 600;
          color: var(--text-primary, #f0f2f5);
          margin: 0 0 20px;
        }

        .form-group {
          margin-bottom: 16px;
        }

        .form-label {
          display: block;
          font-size: 14px;
          font-weight: 500;
          color: var(--text-primary, #f0f2f5);
          margin-bottom: 8px;
        }

        .form-input,
        .form-select {
          width: 100%;
          height: 42px;
          padding: 0 14px;
          background: var(--bg-tertiary, #1a1d24);
          border: 1px solid var(--border-color, #2a2f3a);
          border-radius: 8px;
          color: var(--text-primary, #f0f2f5);
          font-size: 14px;
          font-family: inherit;
        }

        .form-input:focus,
        .form-select:focus {
          outline: none;
          border-color: var(--accent-primary, #6366f1);
        }

        .modal-actions {
          display: flex;
          gap: 12px;
          margin-top: 24px;
        }

        .btn-secondary {
          flex: 1;
          padding: 10px 16px;
          background: var(--bg-tertiary, #1a1d24);
          border: 1px solid var(--border-color, #2a2f3a);
          border-radius: 8px;
          color: var(--text-primary, #f0f2f5);
          font-size: 14px;
          font-weight: 500;
          cursor: pointer;
          font-family: inherit;
        }

        .btn-primary {
          flex: 1;
          display: inline-flex;
          align-items: center;
          justify-content: center;
          gap: 8px;
          padding: 10px 16px;
          background: var(--accent-primary, #6366f1);
          border: none;
          border-radius: 8px;
          color: white;
          font-size: 14px;
          font-weight: 500;
          cursor: pointer;
          font-family: inherit;
        }

        .btn-primary:disabled {
          opacity: 0.6;
          cursor: not-allowed;
        }

        .btn-primary svg {
          width: 16px;
          height: 16px;
        }

        .spinner {
          animation: spin 1s linear infinite;
        }

        @keyframes spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }

        .empty-state {
          text-align: center;
          padding: 32px;
          color: var(--text-secondary, #8b919e);
        }
      `}</style>

      <h2>
        <Users />
        Team Management
      </h2>
      <p className="section-description">
        Manage your team members and their access permissions.
      </p>

      <div className="team-header">
        <span style={{ fontSize: 14, color: 'var(--text-secondary)' }}>
          {members.length} team member{members.length !== 1 ? 's' : ''}
        </span>
        <button className="invite-btn" onClick={() => setInviteModalOpen(true)}>
          <UserPlus />
          Invite Member
        </button>
      </div>

      <table className="team-table">
        <thead>
          <tr>
            <th>Member</th>
            <th>Role</th>
            <th>Last Active</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          {loadingMembers ? (
            <tr>
              <td colSpan={4} className="empty-state">
                <Loader2 className="spinner" style={{ width: 20, height: 20 }} />
              </td>
            </tr>
          ) : members.length === 0 ? (
            <tr>
              <td colSpan={4} className="empty-state">
                No team members found
              </td>
            </tr>
          ) : (
            members.map((member) => (
              <MemberRow
                key={member.id}
                member={member}
                onUpdateRole={handleUpdateRole}
                onRemove={handleRemoveMember}
              />
            ))
          )}
        </tbody>
      </table>

      {invitations.length > 0 && (
        <div className="section-divider">
          <h3>
            <Mail />
            Pending Invitations ({invitations.length})
          </h3>
          <table className="team-table">
            <tbody>
              {invitations.map((invitation) => (
                <InvitationRow
                  key={invitation.id}
                  invitation={invitation}
                  onCancel={handleCancelInvitation}
                  onResend={handleResendInvitation}
                />
              ))}
            </tbody>
          </table>
        </div>
      )}

      <InviteModal
        isOpen={inviteModalOpen}
        onClose={() => setInviteModalOpen(false)}
      />
    </div>
  );
}
