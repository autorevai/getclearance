/**
 * Get Clearance - Consent Flow
 * =============================
 * Consent flow component for end-user data sharing confirmation.
 * Used when an applicant initiates sharing their own KYC data.
 */

import React, { useState } from 'react';
import {
  Shield,
  CheckCircle,
  AlertTriangle,
  Eye,
  Lock,
  Clock,
  Building2,
} from 'lucide-react';
import { PERMISSION_DESCRIPTIONS } from '../../services/kycShare';

export default function ConsentFlow({
  applicantName,
  sharedWith,
  permissions,
  expiryDays,
  maxUses,
  onConfirm,
  onCancel,
  isLoading = false,
}) {
  const [step, setStep] = useState(1);
  const [agreedToTerms, setAgreedToTerms] = useState(false);
  const [confirmedIdentity, setConfirmedIdentity] = useState(false);

  const selectedPermissions = Object.entries(permissions)
    .filter(([, enabled]) => enabled)
    .map(([key]) => key);

  const canProceed = step === 1 ? true : agreedToTerms && confirmedIdentity;

  const handleNext = () => {
    if (step === 1) {
      setStep(2);
    } else if (step === 2 && canProceed) {
      onConfirm();
    }
  };

  return (
    <div className="max-w-lg mx-auto">
      {/* Header */}
      <div className="text-center mb-8">
        <div className="inline-flex p-3 bg-indigo-100 rounded-full mb-4">
          <Shield className="w-8 h-8 text-indigo-600" />
        </div>
        <h1 className="text-2xl font-bold text-gray-900 mb-2">
          Share Your KYC Data
        </h1>
        <p className="text-gray-600">
          Review the data sharing request before confirming
        </p>
      </div>

      {/* Progress */}
      <div className="flex items-center justify-center mb-8">
        <div className="flex items-center gap-2">
          <div
            className={`w-8 h-8 rounded-full flex items-center justify-center font-medium ${
              step >= 1
                ? 'bg-indigo-600 text-white'
                : 'bg-gray-200 text-gray-500'
            }`}
          >
            1
          </div>
          <div
            className={`w-16 h-1 ${
              step >= 2 ? 'bg-indigo-600' : 'bg-gray-200'
            }`}
          />
          <div
            className={`w-8 h-8 rounded-full flex items-center justify-center font-medium ${
              step >= 2
                ? 'bg-indigo-600 text-white'
                : 'bg-gray-200 text-gray-500'
            }`}
          >
            2
          </div>
        </div>
      </div>

      {/* Step 1: Review */}
      {step === 1 && (
        <div className="space-y-6">
          {/* Recipient */}
          <div className="bg-gray-50 rounded-lg p-4">
            <div className="flex items-center gap-3 mb-3">
              <div className="p-2 bg-white rounded-lg shadow-sm">
                <Building2 className="w-5 h-5 text-gray-600" />
              </div>
              <div>
                <p className="text-sm text-gray-500">Sharing with</p>
                <p className="font-semibold text-gray-900">{sharedWith}</p>
              </div>
            </div>
          </div>

          {/* What's being shared */}
          <div>
            <h3 className="flex items-center gap-2 font-medium text-gray-900 mb-3">
              <Eye className="w-4 h-4" />
              Data to be shared
            </h3>
            <div className="space-y-2">
              {selectedPermissions.map((perm) => (
                <div
                  key={perm}
                  className="flex items-start gap-3 p-3 bg-white border border-gray-200 rounded-lg"
                >
                  <CheckCircle className="w-5 h-5 text-green-500 mt-0.5" />
                  <div>
                    <p className="font-medium text-gray-900 capitalize">
                      {perm.replace('_', ' ')}
                    </p>
                    <p className="text-sm text-gray-500">
                      {PERMISSION_DESCRIPTIONS[perm]}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Terms */}
          <div className="grid grid-cols-2 gap-4">
            <div className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg">
              <Clock className="w-5 h-5 text-gray-500" />
              <div>
                <p className="text-xs text-gray-500">Expires in</p>
                <p className="font-medium text-gray-900">{expiryDays} days</p>
              </div>
            </div>
            <div className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg">
              <Lock className="w-5 h-5 text-gray-500" />
              <div>
                <p className="text-xs text-gray-500">Max uses</p>
                <p className="font-medium text-gray-900">{maxUses}</p>
              </div>
            </div>
          </div>

          {/* Info */}
          <div className="flex items-start gap-3 p-3 bg-blue-50 border border-blue-200 rounded-lg">
            <Shield className="w-5 h-5 text-blue-600 mt-0.5" />
            <div className="text-sm text-blue-700">
              <p className="font-medium">Your data is protected</p>
              <p className="mt-0.5">
                You can revoke this access at any time. The recipient will only
                see verified information, not your original documents.
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Step 2: Confirm */}
      {step === 2 && (
        <div className="space-y-6">
          <div className="flex items-start gap-3 p-4 bg-amber-50 border border-amber-200 rounded-lg">
            <AlertTriangle className="w-5 h-5 text-amber-600 mt-0.5" />
            <div>
              <p className="font-medium text-amber-800">Please confirm</p>
              <p className="text-sm text-amber-700 mt-1">
                By proceeding, you authorize {sharedWith} to access the selected
                verification data.
              </p>
            </div>
          </div>

          {/* Checkboxes */}
          <div className="space-y-3">
            <label className="flex items-start gap-3 p-4 border border-gray-200 rounded-lg cursor-pointer hover:border-indigo-300">
              <input
                type="checkbox"
                checked={confirmedIdentity}
                onChange={(e) => setConfirmedIdentity(e.target.checked)}
                className="mt-0.5 rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
              />
              <div>
                <p className="font-medium text-gray-900">
                  I confirm my identity
                </p>
                <p className="text-sm text-gray-500">
                  I am {applicantName} and I authorize this data sharing request.
                </p>
              </div>
            </label>

            <label className="flex items-start gap-3 p-4 border border-gray-200 rounded-lg cursor-pointer hover:border-indigo-300">
              <input
                type="checkbox"
                checked={agreedToTerms}
                onChange={(e) => setAgreedToTerms(e.target.checked)}
                className="mt-0.5 rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
              />
              <div>
                <p className="font-medium text-gray-900">
                  I understand and agree
                </p>
                <p className="text-sm text-gray-500">
                  I understand that my verification data will be shared with{' '}
                  {sharedWith} for the purpose described. I can revoke this access
                  at any time.
                </p>
              </div>
            </label>
          </div>
        </div>
      )}

      {/* Actions */}
      <div className="flex items-center justify-between mt-8 pt-6 border-t border-gray-200">
        <button
          onClick={step === 1 ? onCancel : () => setStep(1)}
          className="px-4 py-2 text-gray-700 hover:text-gray-900"
          disabled={isLoading}
        >
          {step === 1 ? 'Cancel' : 'Back'}
        </button>

        <button
          onClick={handleNext}
          disabled={!canProceed || isLoading}
          className="flex items-center gap-2 px-6 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          {isLoading ? (
            <>
              <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
              Processing...
            </>
          ) : step === 1 ? (
            'Continue'
          ) : (
            <>
              <CheckCircle className="w-4 h-4" />
              Confirm & Share
            </>
          )}
        </button>
      </div>
    </div>
  );
}
