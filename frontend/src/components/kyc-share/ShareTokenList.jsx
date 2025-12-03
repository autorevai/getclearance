/**
 * Get Clearance - Share Token List
 * =================================
 * Displays list of KYC share tokens with status and actions.
 */

import React, { useState } from 'react';
import {
  Key,
  Clock,
  CheckCircle,
  XCircle,
  AlertTriangle,
  Trash2,
  Eye,
  RefreshCw,
} from 'lucide-react';
import { useRevokeShareToken } from '../../hooks/useKYCShare';
import { formatDistanceToNow } from 'date-fns';
import ConfirmDialog from '../shared/ConfirmDialog';

const STATUS_STYLES = {
  active: {
    bg: 'bg-green-100',
    text: 'text-green-800',
    icon: CheckCircle,
  },
  expired: {
    bg: 'bg-gray-100',
    text: 'text-gray-600',
    icon: Clock,
  },
  exhausted: {
    bg: 'bg-amber-100',
    text: 'text-amber-800',
    icon: AlertTriangle,
  },
  revoked: {
    bg: 'bg-red-100',
    text: 'text-red-800',
    icon: XCircle,
  },
};

function PermissionBadge({ permission }) {
  const labels = {
    basic_info: 'Basic Info',
    id_verification: 'ID Verification',
    address: 'Address',
    screening: 'Screening',
    documents: 'Documents',
    full: 'Full Access',
  };

  return (
    <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-indigo-100 text-indigo-800">
      {labels[permission] || permission}
    </span>
  );
}

function TokenCard({ token, onRevoke }) {
  const [showDetails, setShowDetails] = useState(false);
  const statusConfig = STATUS_STYLES[token.status] || STATUS_STYLES.active;
  const StatusIcon = statusConfig.icon;

  const permissions = Object.entries(token.permissions || {})
    .filter(([, enabled]) => enabled)
    .map(([key]) => key);

  return (
    <div className="bg-white border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow">
      <div className="flex items-start justify-between">
        <div className="flex items-start gap-3">
          <div className="p-2 bg-gray-100 rounded-lg">
            <Key className="w-5 h-5 text-gray-600" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-mono text-sm text-gray-900">
                {token.token_prefix}...
              </span>
              <span
                className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium ${statusConfig.bg} ${statusConfig.text}`}
              >
                <StatusIcon className="w-3 h-3" />
                {token.status.charAt(0).toUpperCase() + token.status.slice(1)}
              </span>
            </div>
            <p className="text-sm text-gray-600 mt-1">
              Shared with: <span className="font-medium">{token.shared_with}</span>
            </p>
            {token.purpose && (
              <p className="text-xs text-gray-500 mt-0.5">
                Purpose: {token.purpose}
              </p>
            )}
          </div>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => setShowDetails(!showDetails)}
            className="p-1.5 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded"
            title="Toggle details"
          >
            <Eye className="w-4 h-4" />
          </button>
          {token.status === 'active' && (
            <button
              onClick={() => onRevoke(token)}
              className="p-1.5 text-red-400 hover:text-red-600 hover:bg-red-50 rounded"
              title="Revoke token"
            >
              <Trash2 className="w-4 h-4" />
            </button>
          )}
        </div>
      </div>

      {/* Token Stats */}
      <div className="flex items-center gap-4 mt-3 text-xs text-gray-500">
        <span className="flex items-center gap-1">
          <Clock className="w-3.5 h-3.5" />
          Expires {formatDistanceToNow(new Date(token.expires_at), { addSuffix: true })}
        </span>
        <span>
          Uses: {token.use_count} / {token.max_uses}
        </span>
        <span>
          Created {formatDistanceToNow(new Date(token.created_at), { addSuffix: true })}
        </span>
      </div>

      {/* Expanded Details */}
      {showDetails && (
        <div className="mt-4 pt-4 border-t border-gray-100 space-y-3">
          <div>
            <p className="text-xs font-medium text-gray-500 mb-1">Permissions</p>
            <div className="flex flex-wrap gap-1">
              {permissions.map((perm) => (
                <PermissionBadge key={perm} permission={perm} />
              ))}
            </div>
          </div>

          {token.shared_with_email && (
            <div>
              <p className="text-xs font-medium text-gray-500 mb-0.5">Contact Email</p>
              <p className="text-sm text-gray-900">{token.shared_with_email}</p>
            </div>
          )}

          {token.revoked_at && (
            <div>
              <p className="text-xs font-medium text-gray-500 mb-0.5">Revoked</p>
              <p className="text-sm text-gray-900">
                {formatDistanceToNow(new Date(token.revoked_at), { addSuffix: true })}
                {token.revoked_reason && ` - ${token.revoked_reason}`}
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default function ShareTokenList({ tokens, isLoading, onRefresh }) {
  const [tokenToRevoke, setTokenToRevoke] = useState(null);
  const [revokeReason, setRevokeReason] = useState('');

  const revokeMutation = useRevokeShareToken();

  const handleRevoke = async () => {
    if (!tokenToRevoke) return;

    try {
      await revokeMutation.mutateAsync({
        tokenId: tokenToRevoke.id,
        reason: revokeReason || undefined,
      });
      setTokenToRevoke(null);
      setRevokeReason('');
      onRefresh?.();
    } catch (error) {
      console.error('Failed to revoke token:', error);
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <RefreshCw className="w-6 h-6 animate-spin text-indigo-600" />
      </div>
    );
  }

  if (tokens.length === 0) {
    return (
      <div className="text-center py-12 bg-gray-50 rounded-lg border border-gray-200">
        <Key className="w-12 h-12 text-gray-400 mx-auto mb-3" />
        <h3 className="text-lg font-medium text-gray-900 mb-1">No Share Tokens</h3>
        <p className="text-gray-500 text-sm">
          Generate a token to share this applicant's KYC with third parties.
        </p>
      </div>
    );
  }

  return (
    <>
      <div className="space-y-3">
        {tokens.map((token) => (
          <TokenCard
            key={token.id}
            token={token}
            onRevoke={setTokenToRevoke}
          />
        ))}
      </div>

      {/* Revoke Confirmation Dialog */}
      {tokenToRevoke && (
        <ConfirmDialog
          title="Revoke Share Token"
          message={`Are you sure you want to revoke this token shared with "${tokenToRevoke.shared_with}"? This action cannot be undone.`}
          confirmLabel="Revoke Token"
          confirmVariant="danger"
          isLoading={revokeMutation.isPending}
          onConfirm={handleRevoke}
          onCancel={() => {
            setTokenToRevoke(null);
            setRevokeReason('');
          }}
        >
          <div className="mt-4">
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Reason (optional)
            </label>
            <input
              type="text"
              value={revokeReason}
              onChange={(e) => setRevokeReason(e.target.value)}
              placeholder="e.g., No longer needed, security concern"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
            />
          </div>
        </ConfirmDialog>
      )}
    </>
  );
}
