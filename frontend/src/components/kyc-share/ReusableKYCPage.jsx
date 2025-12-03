/**
 * Get Clearance - Reusable KYC Page
 * ==================================
 * Main page for managing KYC share tokens and viewing access history.
 */

import React, { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  ArrowLeft,
  Share2,
  History,
  Key,
  Shield,
  AlertCircle,
  RefreshCw,
} from 'lucide-react';
import { useApplicant } from '../../hooks';
import { useShareTokens, useAccessHistory } from '../../hooks/useKYCShare';
import ShareTokenList from './ShareTokenList';
import GenerateTokenModal from './GenerateTokenModal';
import ShareHistory from './ShareHistory';

export default function ReusableKYCPage() {
  const { applicantId } = useParams();
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState('tokens');
  const [showGenerateModal, setShowGenerateModal] = useState(false);
  const [includeExpired, setIncludeExpired] = useState(false);

  // Fetch applicant data
  const { data: applicant, isLoading: applicantLoading } = useApplicant(applicantId);

  // Fetch tokens
  const {
    data: tokensData,
    isLoading: tokensLoading,
    refetch: refetchTokens,
  } = useShareTokens(applicantId, { includeExpired });

  // Fetch access history
  const {
    data: historyData,
    isLoading: historyLoading,
    refetch: refetchHistory,
  } = useAccessHistory(applicantId);

  const isApproved = applicant?.status === 'approved';
  const tokens = tokensData?.tokens || [];
  const accessLogs = historyData?.logs || [];

  const handleBack = () => {
    navigate(`/applicants/${applicantId}`);
  };

  const handleTokenGenerated = () => {
    refetchTokens();
    setShowGenerateModal(false);
  };

  if (applicantLoading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <RefreshCw className="w-8 h-8 animate-spin text-indigo-600" />
      </div>
    );
  }

  if (!applicant) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-700">
        <AlertCircle className="w-5 h-5 inline mr-2" />
        Applicant not found
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <button
            onClick={handleBack}
            className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
          >
            <ArrowLeft className="w-5 h-5 text-gray-600" />
          </button>
          <div>
            <h1 className="text-2xl font-bold text-gray-900">
              Reusable KYC
            </h1>
            <p className="text-gray-600">
              {applicant.first_name} {applicant.last_name}
            </p>
          </div>
        </div>

        {isApproved && (
          <button
            onClick={() => setShowGenerateModal(true)}
            className="flex items-center gap-2 px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors"
          >
            <Share2 className="w-4 h-4" />
            Generate Share Token
          </button>
        )}
      </div>

      {/* Status Warning */}
      {!isApproved && (
        <div className="bg-amber-50 border border-amber-200 rounded-lg p-4">
          <div className="flex items-start gap-3">
            <AlertCircle className="w-5 h-5 text-amber-600 mt-0.5" />
            <div>
              <h3 className="font-semibold text-amber-800">
                Applicant Not Approved
              </h3>
              <p className="text-amber-700 text-sm mt-1">
                Only approved applicants can share their KYC data. Current status:{' '}
                <span className="font-medium capitalize">{applicant.status}</span>
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Info Card */}
      <div className="bg-indigo-50 border border-indigo-100 rounded-lg p-4">
        <div className="flex items-start gap-3">
          <Shield className="w-5 h-5 text-indigo-600 mt-0.5" />
          <div>
            <h3 className="font-semibold text-indigo-900">
              Portable Identity / Reusable KYC
            </h3>
            <p className="text-indigo-700 text-sm mt-1">
              Generate secure tokens that allow third parties to verify this applicant's
              KYC data. Tokens are time-limited, use-limited, and can be revoked at any time.
              You control exactly what data is shared through permissions.
            </p>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="border-b border-gray-200">
        <nav className="flex gap-8">
          <button
            onClick={() => setActiveTab('tokens')}
            className={`flex items-center gap-2 py-3 border-b-2 font-medium text-sm transition-colors ${
              activeTab === 'tokens'
                ? 'border-indigo-600 text-indigo-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            <Key className="w-4 h-4" />
            Share Tokens
            {tokens.length > 0 && (
              <span className="ml-2 bg-gray-100 text-gray-600 px-2 py-0.5 rounded-full text-xs">
                {tokens.length}
              </span>
            )}
          </button>
          <button
            onClick={() => setActiveTab('history')}
            className={`flex items-center gap-2 py-3 border-b-2 font-medium text-sm transition-colors ${
              activeTab === 'history'
                ? 'border-indigo-600 text-indigo-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            <History className="w-4 h-4" />
            Access History
            {accessLogs.length > 0 && (
              <span className="ml-2 bg-gray-100 text-gray-600 px-2 py-0.5 rounded-full text-xs">
                {accessLogs.length}
              </span>
            )}
          </button>
        </nav>
      </div>

      {/* Tab Content */}
      {activeTab === 'tokens' && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <label className="flex items-center gap-2 text-sm text-gray-600">
              <input
                type="checkbox"
                checked={includeExpired}
                onChange={(e) => setIncludeExpired(e.target.checked)}
                className="rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
              />
              Show expired tokens
            </label>
            <button
              onClick={() => refetchTokens()}
              className="text-sm text-indigo-600 hover:text-indigo-700 flex items-center gap-1"
            >
              <RefreshCw className="w-4 h-4" />
              Refresh
            </button>
          </div>

          <ShareTokenList
            tokens={tokens}
            isLoading={tokensLoading}
            onRefresh={refetchTokens}
          />
        </div>
      )}

      {activeTab === 'history' && (
        <div className="space-y-4">
          <div className="flex justify-end">
            <button
              onClick={() => refetchHistory()}
              className="text-sm text-indigo-600 hover:text-indigo-700 flex items-center gap-1"
            >
              <RefreshCw className="w-4 h-4" />
              Refresh
            </button>
          </div>

          <ShareHistory
            logs={accessLogs}
            isLoading={historyLoading}
          />
        </div>
      )}

      {/* Generate Token Modal */}
      {showGenerateModal && (
        <GenerateTokenModal
          applicantId={applicantId}
          applicantName={`${applicant.first_name} ${applicant.last_name}`}
          onClose={() => setShowGenerateModal(false)}
          onSuccess={handleTokenGenerated}
        />
      )}
    </div>
  );
}
