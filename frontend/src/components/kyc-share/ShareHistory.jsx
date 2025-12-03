/**
 * Get Clearance - Share History
 * ==============================
 * Displays access history for KYC share tokens.
 */

import React from 'react';
import {
  History,
  CheckCircle,
  XCircle,
  Globe,
  Clock,
  Shield,
  RefreshCw,
} from 'lucide-react';
import { formatDistanceToNow, format } from 'date-fns';

function LogEntry({ log }) {
  const isSuccess = log.success;

  return (
    <div
      className={`border rounded-lg p-4 ${
        isSuccess
          ? 'bg-white border-gray-200'
          : 'bg-red-50 border-red-200'
      }`}
    >
      <div className="flex items-start justify-between">
        <div className="flex items-start gap-3">
          <div
            className={`p-2 rounded-lg ${
              isSuccess ? 'bg-green-100' : 'bg-red-100'
            }`}
          >
            {isSuccess ? (
              <CheckCircle className="w-5 h-5 text-green-600" />
            ) : (
              <XCircle className="w-5 h-5 text-red-600" />
            )}
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-medium text-gray-900">
                {isSuccess ? 'Access Granted' : 'Access Denied'}
              </span>
              <span className="text-xs font-mono text-gray-500">
                {log.token_prefix}...
              </span>
            </div>
            <p className="text-sm text-gray-600 mt-0.5">
              Token for: {log.shared_with}
            </p>
            {log.failure_reason && (
              <p className="text-sm text-red-600 mt-1">
                Reason: {log.failure_reason}
              </p>
            )}
          </div>
        </div>
        <span className="text-xs text-gray-500">
          {formatDistanceToNow(new Date(log.accessed_at), { addSuffix: true })}
        </span>
      </div>

      {/* Access Details */}
      <div className="mt-3 pt-3 border-t border-gray-100 grid grid-cols-2 md:grid-cols-3 gap-3 text-xs">
        {log.requester_ip && (
          <div className="flex items-center gap-1.5 text-gray-500">
            <Globe className="w-3.5 h-3.5" />
            <span>{log.requester_ip}</span>
          </div>
        )}
        {log.requester_domain && (
          <div className="flex items-center gap-1.5 text-gray-500">
            <Shield className="w-3.5 h-3.5" />
            <span>{log.requester_domain}</span>
          </div>
        )}
        <div className="flex items-center gap-1.5 text-gray-500">
          <Clock className="w-3.5 h-3.5" />
          <span>{format(new Date(log.accessed_at), 'MMM d, yyyy HH:mm')}</span>
        </div>
      </div>

      {/* Accessed Permissions */}
      {isSuccess && log.accessed_permissions?.length > 0 && (
        <div className="mt-3 pt-3 border-t border-gray-100">
          <p className="text-xs text-gray-500 mb-1.5">Data Accessed:</p>
          <div className="flex flex-wrap gap-1">
            {log.accessed_permissions.map((perm) => (
              <span
                key={perm}
                className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-indigo-100 text-indigo-800 capitalize"
              >
                {perm.replace('_', ' ')}
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

export default function ShareHistory({ logs, isLoading }) {
  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <RefreshCw className="w-6 h-6 animate-spin text-indigo-600" />
      </div>
    );
  }

  if (logs.length === 0) {
    return (
      <div className="text-center py-12 bg-gray-50 rounded-lg border border-gray-200">
        <History className="w-12 h-12 text-gray-400 mx-auto mb-3" />
        <h3 className="text-lg font-medium text-gray-900 mb-1">
          No Access History
        </h3>
        <p className="text-gray-500 text-sm">
          Token access attempts will appear here once they occur.
        </p>
      </div>
    );
  }

  // Group logs by date
  const groupedLogs = logs.reduce((groups, log) => {
    const date = format(new Date(log.accessed_at), 'yyyy-MM-dd');
    if (!groups[date]) {
      groups[date] = [];
    }
    groups[date].push(log);
    return groups;
  }, {});

  return (
    <div className="space-y-6">
      {Object.entries(groupedLogs).map(([date, dateLogs]) => (
        <div key={date}>
          <h4 className="text-sm font-medium text-gray-500 mb-2">
            {format(new Date(date), 'EEEE, MMMM d, yyyy')}
          </h4>
          <div className="space-y-3">
            {dateLogs.map((log) => (
              <LogEntry key={log.id} log={log} />
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}
