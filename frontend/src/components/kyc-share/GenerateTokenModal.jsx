/**
 * Get Clearance - Generate Token Modal
 * =====================================
 * Modal for generating new KYC share tokens with consent flow.
 */

import React, { useState, useEffect } from 'react';
import {
  X,
  Share2,
  Shield,
  Key,
  CheckCircle,
  Copy,
  AlertCircle,
  Info,
} from 'lucide-react';
import { useGenerateShareToken } from '../../hooks/useKYCShare';
import { PERMISSION_DESCRIPTIONS } from '../../services/kycShare';

const STEPS = {
  PERMISSIONS: 'permissions',
  DETAILS: 'details',
  CONSENT: 'consent',
  SUCCESS: 'success',
};

export default function GenerateTokenModal({
  applicantId,
  applicantName,
  onClose,
  onSuccess,
}) {
  const [step, setStep] = useState(STEPS.PERMISSIONS);
  const [copied, setCopied] = useState(false);
  const [generatedToken, setGeneratedToken] = useState(null);

  // Form state
  const [formData, setFormData] = useState({
    permissions: {
      basic_info: true,
      id_verification: false,
      address: false,
      screening: false,
      documents: false,
      full: false,
    },
    shared_with: '',
    shared_with_email: '',
    purpose: '',
    expires_days: 30,
    max_uses: 1,
    consent_confirmed: false,
  });

  const generateMutation = useGenerateShareToken();

  // Handle full permission toggle
  useEffect(() => {
    if (formData.permissions.full) {
      setFormData((prev) => ({
        ...prev,
        permissions: {
          basic_info: true,
          id_verification: true,
          address: true,
          screening: true,
          documents: true,
          full: true,
        },
      }));
    }
  }, [formData.permissions.full]);

  const handlePermissionChange = (key) => {
    if (key === 'full') {
      setFormData((prev) => ({
        ...prev,
        permissions: {
          ...prev.permissions,
          full: !prev.permissions.full,
        },
      }));
    } else {
      setFormData((prev) => ({
        ...prev,
        permissions: {
          ...prev.permissions,
          [key]: !prev.permissions[key],
          full: false, // Uncheck full if individual is changed
        },
      }));
    }
  };

  const handleSubmit = async () => {
    try {
      const result = await generateMutation.mutateAsync({
        applicant_id: applicantId,
        shared_with: formData.shared_with,
        shared_with_email: formData.shared_with_email || undefined,
        purpose: formData.purpose || undefined,
        permissions: formData.permissions,
        expires_days: formData.expires_days,
        max_uses: formData.max_uses,
      });
      setGeneratedToken(result);
      setStep(STEPS.SUCCESS);
    } catch (error) {
      console.error('Failed to generate token:', error);
    }
  };

  const handleCopy = async () => {
    if (generatedToken?.token) {
      await navigator.clipboard.writeText(generatedToken.token);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const handleClose = () => {
    if (step === STEPS.SUCCESS) {
      onSuccess?.();
    }
    onClose();
  };

  const selectedPermissions = Object.entries(formData.permissions)
    .filter(([, enabled]) => enabled)
    .map(([key]) => key);

  const canProceed = {
    [STEPS.PERMISSIONS]: selectedPermissions.length > 0,
    [STEPS.DETAILS]: formData.shared_with.trim().length > 0,
    [STEPS.CONSENT]: formData.consent_confirmed,
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl shadow-xl max-w-lg w-full max-h-[90vh] overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-gray-200">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-indigo-100 rounded-lg">
              <Share2 className="w-5 h-5 text-indigo-600" />
            </div>
            <div>
              <h2 className="text-lg font-semibold text-gray-900">
                Generate Share Token
              </h2>
              <p className="text-sm text-gray-500">{applicantName}</p>
            </div>
          </div>
          <button
            onClick={handleClose}
            className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
          >
            <X className="w-5 h-5 text-gray-500" />
          </button>
        </div>

        {/* Content */}
        <div className="p-4 overflow-y-auto max-h-[60vh]">
          {/* Step 1: Permissions */}
          {step === STEPS.PERMISSIONS && (
            <div className="space-y-4">
              <div className="flex items-start gap-3 p-3 bg-indigo-50 rounded-lg">
                <Info className="w-5 h-5 text-indigo-600 mt-0.5" />
                <p className="text-sm text-indigo-700">
                  Select what data the recipient will be able to access.
                </p>
              </div>

              <div className="space-y-2">
                {Object.entries(PERMISSION_DESCRIPTIONS).map(([key, desc]) => (
                  <label
                    key={key}
                    className={`flex items-start gap-3 p-3 border rounded-lg cursor-pointer transition-colors ${
                      formData.permissions[key]
                        ? 'border-indigo-500 bg-indigo-50'
                        : 'border-gray-200 hover:border-gray-300'
                    }`}
                  >
                    <input
                      type="checkbox"
                      checked={formData.permissions[key]}
                      onChange={() => handlePermissionChange(key)}
                      className="mt-0.5 rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
                    />
                    <div>
                      <p className="font-medium text-gray-900 capitalize">
                        {key.replace('_', ' ')}
                      </p>
                      <p className="text-sm text-gray-500">{desc}</p>
                    </div>
                  </label>
                ))}
              </div>
            </div>
          )}

          {/* Step 2: Details */}
          {step === STEPS.DETAILS && (
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Share with (Company/Organization) *
                </label>
                <input
                  type="text"
                  value={formData.shared_with}
                  onChange={(e) =>
                    setFormData({ ...formData, shared_with: e.target.value })
                  }
                  placeholder="e.g., Acme Corp"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Contact Email (optional)
                </label>
                <input
                  type="email"
                  value={formData.shared_with_email}
                  onChange={(e) =>
                    setFormData({ ...formData, shared_with_email: e.target.value })
                  }
                  placeholder="e.g., compliance@acme.com"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Purpose (optional)
                </label>
                <input
                  type="text"
                  value={formData.purpose}
                  onChange={(e) =>
                    setFormData({ ...formData, purpose: e.target.value })
                  }
                  placeholder="e.g., Employment verification"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Expires in (days)
                  </label>
                  <select
                    value={formData.expires_days}
                    onChange={(e) =>
                      setFormData({
                        ...formData,
                        expires_days: parseInt(e.target.value),
                      })
                    }
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                  >
                    <option value={7}>7 days</option>
                    <option value={14}>14 days</option>
                    <option value={30}>30 days</option>
                    <option value={60}>60 days</option>
                    <option value={90}>90 days (max)</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Max uses
                  </label>
                  <select
                    value={formData.max_uses}
                    onChange={(e) =>
                      setFormData({
                        ...formData,
                        max_uses: parseInt(e.target.value),
                      })
                    }
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                  >
                    {[1, 2, 3, 4, 5, 6, 7, 8, 9, 10].map((n) => (
                      <option key={n} value={n}>
                        {n} {n === 1 ? 'use' : 'uses'}
                      </option>
                    ))}
                  </select>
                </div>
              </div>
            </div>
          )}

          {/* Step 3: Consent */}
          {step === STEPS.CONSENT && (
            <div className="space-y-4">
              <div className="flex items-start gap-3 p-3 bg-amber-50 border border-amber-200 rounded-lg">
                <Shield className="w-5 h-5 text-amber-600 mt-0.5" />
                <div>
                  <p className="font-medium text-amber-800">
                    Consent Confirmation Required
                  </p>
                  <p className="text-sm text-amber-700 mt-1">
                    By generating this token, you confirm that the applicant has
                    consented to share their KYC data.
                  </p>
                </div>
              </div>

              <div className="bg-gray-50 rounded-lg p-4 space-y-3">
                <h4 className="font-medium text-gray-900">Summary</h4>
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-gray-500">Shared with:</span>
                    <span className="font-medium">{formData.shared_with}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-500">Permissions:</span>
                    <span className="font-medium">
                      {selectedPermissions.length} granted
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-500">Expires:</span>
                    <span className="font-medium">{formData.expires_days} days</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-500">Max uses:</span>
                    <span className="font-medium">{formData.max_uses}</span>
                  </div>
                </div>
              </div>

              <label className="flex items-start gap-3 p-3 border border-gray-200 rounded-lg cursor-pointer hover:border-indigo-300">
                <input
                  type="checkbox"
                  checked={formData.consent_confirmed}
                  onChange={(e) =>
                    setFormData({
                      ...formData,
                      consent_confirmed: e.target.checked,
                    })
                  }
                  className="mt-0.5 rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
                />
                <span className="text-sm text-gray-700">
                  I confirm that the applicant has provided informed consent to share
                  their KYC verification data with the specified party.
                </span>
              </label>

              {generateMutation.error && (
                <div className="flex items-start gap-2 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
                  <AlertCircle className="w-5 h-5 mt-0.5" />
                  <span>
                    {generateMutation.error.message || 'Failed to generate token'}
                  </span>
                </div>
              )}
            </div>
          )}

          {/* Step 4: Success */}
          {step === STEPS.SUCCESS && generatedToken && (
            <div className="space-y-4">
              <div className="flex items-center justify-center py-4">
                <div className="p-3 bg-green-100 rounded-full">
                  <CheckCircle className="w-8 h-8 text-green-600" />
                </div>
              </div>

              <div className="text-center">
                <h3 className="text-lg font-semibold text-gray-900">
                  Token Generated Successfully
                </h3>
                <p className="text-sm text-gray-500 mt-1">
                  Copy and securely share this token. It will only be shown once.
                </p>
              </div>

              <div className="bg-gray-900 rounded-lg p-4">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs text-gray-400 font-medium">
                    SHARE TOKEN
                  </span>
                  <button
                    onClick={handleCopy}
                    className="flex items-center gap-1 text-xs text-indigo-400 hover:text-indigo-300"
                  >
                    <Copy className="w-3.5 h-3.5" />
                    {copied ? 'Copied!' : 'Copy'}
                  </button>
                </div>
                <code className="block text-sm text-green-400 break-all font-mono">
                  {generatedToken.token}
                </code>
              </div>

              <div className="flex items-start gap-2 p-3 bg-amber-50 border border-amber-200 rounded-lg">
                <AlertCircle className="w-5 h-5 text-amber-600 mt-0.5" />
                <div className="text-sm text-amber-700">
                  <p className="font-medium">Important</p>
                  <p>
                    This token will not be shown again. Make sure to copy it before
                    closing this dialog.
                  </p>
                </div>
              </div>

              <div className="bg-gray-50 rounded-lg p-3 text-sm">
                <div className="grid grid-cols-2 gap-2">
                  <div>
                    <span className="text-gray-500">Token ID:</span>
                    <span className="ml-1 font-mono text-xs">
                      {generatedToken.token_prefix}...
                    </span>
                  </div>
                  <div>
                    <span className="text-gray-500">Expires:</span>
                    <span className="ml-1">
                      {new Date(generatedToken.expires_at).toLocaleDateString()}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between p-4 border-t border-gray-200 bg-gray-50">
          {step !== STEPS.SUCCESS ? (
            <>
              <button
                onClick={() => {
                  if (step === STEPS.PERMISSIONS) {
                    handleClose();
                  } else if (step === STEPS.DETAILS) {
                    setStep(STEPS.PERMISSIONS);
                  } else if (step === STEPS.CONSENT) {
                    setStep(STEPS.DETAILS);
                  }
                }}
                className="px-4 py-2 text-gray-700 hover:text-gray-900"
              >
                {step === STEPS.PERMISSIONS ? 'Cancel' : 'Back'}
              </button>

              <button
                onClick={() => {
                  if (step === STEPS.PERMISSIONS) {
                    setStep(STEPS.DETAILS);
                  } else if (step === STEPS.DETAILS) {
                    setStep(STEPS.CONSENT);
                  } else if (step === STEPS.CONSENT) {
                    handleSubmit();
                  }
                }}
                disabled={!canProceed[step] || generateMutation.isPending}
                className="flex items-center gap-2 px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                {generateMutation.isPending ? (
                  <>
                    <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                    Generating...
                  </>
                ) : step === STEPS.CONSENT ? (
                  <>
                    <Key className="w-4 h-4" />
                    Generate Token
                  </>
                ) : (
                  'Continue'
                )}
              </button>
            </>
          ) : (
            <button
              onClick={handleClose}
              className="w-full px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors"
            >
              Done
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
