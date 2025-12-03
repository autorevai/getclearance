/**
 * Get Clearance - Reusable KYC Page (Overview)
 * =============================================
 * Overview page for the Reusable KYC feature showing recent tokens
 * and links to applicant-specific KYC sharing.
 */

import React from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Share2,
  Shield,
  Key,
  Users,
  ArrowRight,
  History,
  CheckCircle,
  Clock,
  XCircle,
} from 'lucide-react';

export default function ReusableKYCPage() {
  const navigate = useNavigate();

  // Feature cards describing the capability
  const features = [
    {
      icon: Key,
      title: 'Secure Tokens',
      description: 'Generate time-limited, use-limited tokens for sharing verification data.',
    },
    {
      icon: Shield,
      title: 'Permission Control',
      description: 'Choose exactly what data to share: basic info, ID, address, screening, or documents.',
    },
    {
      icon: History,
      title: 'Full Audit Trail',
      description: 'Track every access attempt with IP, timestamp, and data accessed.',
    },
    {
      icon: XCircle,
      title: 'Instant Revocation',
      description: 'Revoke any token immediately if access is no longer needed.',
    },
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Reusable KYC</h1>
        <p className="text-gray-600 mt-1">
          Enable verified applicants to share their KYC data with third parties securely.
        </p>
      </div>

      {/* Main Info Card */}
      <div className="bg-gradient-to-br from-indigo-500 to-purple-600 rounded-xl p-6 text-white">
        <div className="flex items-start gap-4">
          <div className="p-3 bg-white/20 rounded-lg">
            <Share2 className="w-8 h-8" />
          </div>
          <div className="flex-1">
            <h2 className="text-xl font-semibold mb-2">Portable Identity</h2>
            <p className="text-indigo-100 mb-4">
              Allow your verified applicants to share their KYC verification with
              partner organizations without re-doing the entire verification process.
              Tokens are secure, time-limited, and fully auditable.
            </p>
            <div className="flex items-center gap-6 text-sm">
              <div className="flex items-center gap-2">
                <Clock className="w-4 h-4" />
                <span>Max 90-day expiry</span>
              </div>
              <div className="flex items-center gap-2">
                <Key className="w-4 h-4" />
                <span>Max 10 uses per token</span>
              </div>
              <div className="flex items-center gap-2">
                <CheckCircle className="w-4 h-4" />
                <span>Consent tracked</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* How It Works */}
      <div className="bg-white border border-gray-200 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">How It Works</h3>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="text-center p-4">
            <div className="w-10 h-10 bg-indigo-100 rounded-full flex items-center justify-center mx-auto mb-3">
              <span className="text-indigo-600 font-semibold">1</span>
            </div>
            <h4 className="font-medium text-gray-900 mb-1">Select Applicant</h4>
            <p className="text-sm text-gray-500">
              Choose an approved applicant to share their KYC
            </p>
          </div>
          <div className="text-center p-4">
            <div className="w-10 h-10 bg-indigo-100 rounded-full flex items-center justify-center mx-auto mb-3">
              <span className="text-indigo-600 font-semibold">2</span>
            </div>
            <h4 className="font-medium text-gray-900 mb-1">Set Permissions</h4>
            <p className="text-sm text-gray-500">
              Choose what data the recipient can access
            </p>
          </div>
          <div className="text-center p-4">
            <div className="w-10 h-10 bg-indigo-100 rounded-full flex items-center justify-center mx-auto mb-3">
              <span className="text-indigo-600 font-semibold">3</span>
            </div>
            <h4 className="font-medium text-gray-900 mb-1">Generate Token</h4>
            <p className="text-sm text-gray-500">
              Create a secure, time-limited share token
            </p>
          </div>
          <div className="text-center p-4">
            <div className="w-10 h-10 bg-indigo-100 rounded-full flex items-center justify-center mx-auto mb-3">
              <span className="text-indigo-600 font-semibold">4</span>
            </div>
            <h4 className="font-medium text-gray-900 mb-1">Share Securely</h4>
            <p className="text-sm text-gray-500">
              Send the token to the verified recipient
            </p>
          </div>
        </div>
      </div>

      {/* Feature Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {features.map((feature, index) => {
          const Icon = feature.icon;
          return (
            <div
              key={index}
              className="bg-white border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow"
            >
              <div className="flex items-start gap-3">
                <div className="p-2 bg-indigo-100 rounded-lg">
                  <Icon className="w-5 h-5 text-indigo-600" />
                </div>
                <div>
                  <h4 className="font-medium text-gray-900">{feature.title}</h4>
                  <p className="text-sm text-gray-500 mt-1">{feature.description}</p>
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Get Started */}
      <div className="bg-gray-50 border border-gray-200 rounded-lg p-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className="p-3 bg-indigo-100 rounded-lg">
              <Users className="w-6 h-6 text-indigo-600" />
            </div>
            <div>
              <h3 className="font-semibold text-gray-900">Get Started</h3>
              <p className="text-gray-600 text-sm">
                Go to an approved applicant's profile and click "Share KYC" to generate a token.
              </p>
            </div>
          </div>
          <button
            onClick={() => navigate('/applicants?status=approved')}
            className="flex items-center gap-2 px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors"
          >
            View Approved Applicants
            <ArrowRight className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  );
}
