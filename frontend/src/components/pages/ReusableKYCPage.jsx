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
    <div className="reusable-kyc-page">
      <style>{`
        .reusable-kyc-page {
          max-width: 1200px;
          margin: 0 auto;
        }

        .reusable-kyc-page .page-header {
          margin-bottom: 24px;
        }

        .reusable-kyc-page .page-title {
          font-size: 24px;
          font-weight: 600;
          color: var(--text-primary, #f0f2f5);
          margin: 0 0 8px;
        }

        .reusable-kyc-page .page-subtitle {
          font-size: 14px;
          color: var(--text-secondary, #8b919e);
          margin: 0;
        }

        .reusable-kyc-page .hero-card {
          background: linear-gradient(135deg, #6366f1, #8b5cf6);
          border-radius: 12px;
          padding: 24px;
          color: white;
          margin-bottom: 24px;
        }

        .reusable-kyc-page .hero-content {
          display: flex;
          gap: 16px;
        }

        .reusable-kyc-page .hero-icon {
          padding: 12px;
          background: rgba(255, 255, 255, 0.2);
          border-radius: 12px;
          flex-shrink: 0;
        }

        .reusable-kyc-page .hero-icon svg {
          width: 32px;
          height: 32px;
        }

        .reusable-kyc-page .hero-title {
          font-size: 20px;
          font-weight: 600;
          margin: 0 0 8px;
        }

        .reusable-kyc-page .hero-description {
          color: rgba(255, 255, 255, 0.9);
          margin: 0 0 16px;
          line-height: 1.5;
        }

        .reusable-kyc-page .hero-features {
          display: flex;
          gap: 24px;
          font-size: 14px;
        }

        .reusable-kyc-page .hero-feature {
          display: flex;
          align-items: center;
          gap: 8px;
        }

        .reusable-kyc-page .hero-feature svg {
          width: 16px;
          height: 16px;
        }

        .reusable-kyc-page .section-card {
          background: var(--bg-secondary, #111318);
          border: 1px solid var(--border-color, #2a2f3a);
          border-radius: 12px;
          padding: 24px;
          margin-bottom: 24px;
        }

        .reusable-kyc-page .section-title {
          font-size: 16px;
          font-weight: 600;
          color: var(--text-primary, #f0f2f5);
          margin: 0 0 20px;
        }

        .reusable-kyc-page .steps-grid {
          display: grid;
          grid-template-columns: repeat(4, 1fr);
          gap: 16px;
        }

        @media (max-width: 768px) {
          .reusable-kyc-page .steps-grid {
            grid-template-columns: repeat(2, 1fr);
          }
        }

        .reusable-kyc-page .step-card {
          text-align: center;
          padding: 16px;
        }

        .reusable-kyc-page .step-number {
          width: 40px;
          height: 40px;
          background: var(--accent-glow, rgba(99, 102, 241, 0.1));
          border-radius: 50%;
          display: flex;
          align-items: center;
          justify-content: center;
          margin: 0 auto 12px;
          font-weight: 600;
          color: var(--accent-primary, #6366f1);
        }

        .reusable-kyc-page .step-title {
          font-weight: 500;
          color: var(--text-primary, #f0f2f5);
          margin: 0 0 4px;
        }

        .reusable-kyc-page .step-description {
          font-size: 13px;
          color: var(--text-secondary, #8b919e);
          margin: 0;
        }

        .reusable-kyc-page .features-grid {
          display: grid;
          grid-template-columns: repeat(2, 1fr);
          gap: 16px;
          margin-bottom: 24px;
        }

        @media (max-width: 768px) {
          .reusable-kyc-page .features-grid {
            grid-template-columns: 1fr;
          }
        }

        .reusable-kyc-page .feature-card {
          background: var(--bg-secondary, #111318);
          border: 1px solid var(--border-color, #2a2f3a);
          border-radius: 12px;
          padding: 16px;
          display: flex;
          gap: 12px;
          transition: border-color 0.15s;
        }

        .reusable-kyc-page .feature-card:hover {
          border-color: var(--accent-primary, #6366f1);
        }

        .reusable-kyc-page .feature-icon {
          padding: 8px;
          background: var(--accent-glow, rgba(99, 102, 241, 0.1));
          border-radius: 8px;
          flex-shrink: 0;
          height: fit-content;
        }

        .reusable-kyc-page .feature-icon svg {
          width: 20px;
          height: 20px;
          color: var(--accent-primary, #6366f1);
        }

        .reusable-kyc-page .feature-title {
          font-weight: 500;
          color: var(--text-primary, #f0f2f5);
          margin: 0 0 4px;
        }

        .reusable-kyc-page .feature-description {
          font-size: 13px;
          color: var(--text-secondary, #8b919e);
          margin: 0;
          line-height: 1.4;
        }

        .reusable-kyc-page .cta-card {
          background: var(--bg-tertiary, #1a1d24);
          border: 1px solid var(--border-color, #2a2f3a);
          border-radius: 12px;
          padding: 24px;
          display: flex;
          align-items: center;
          justify-content: space-between;
          gap: 16px;
        }

        .reusable-kyc-page .cta-content {
          display: flex;
          align-items: center;
          gap: 16px;
        }

        .reusable-kyc-page .cta-icon {
          padding: 12px;
          background: var(--accent-glow, rgba(99, 102, 241, 0.1));
          border-radius: 12px;
        }

        .reusable-kyc-page .cta-icon svg {
          width: 24px;
          height: 24px;
          color: var(--accent-primary, #6366f1);
        }

        .reusable-kyc-page .cta-title {
          font-weight: 600;
          color: var(--text-primary, #f0f2f5);
          margin: 0 0 4px;
        }

        .reusable-kyc-page .cta-description {
          font-size: 14px;
          color: var(--text-secondary, #8b919e);
          margin: 0;
        }

        .reusable-kyc-page .cta-button {
          display: flex;
          align-items: center;
          gap: 8px;
          padding: 10px 16px;
          background: var(--accent-primary, #6366f1);
          color: white;
          border: none;
          border-radius: 8px;
          font-size: 14px;
          font-weight: 500;
          cursor: pointer;
          transition: background 0.15s;
          white-space: nowrap;
        }

        .reusable-kyc-page .cta-button:hover {
          background: var(--accent-hover, #5558e8);
        }

        .reusable-kyc-page .cta-button svg {
          width: 16px;
          height: 16px;
        }
      `}</style>

      {/* Header */}
      <div className="page-header">
        <h1 className="page-title">Reusable KYC</h1>
        <p className="page-subtitle">
          Enable verified applicants to share their KYC data with third parties securely.
        </p>
      </div>

      {/* Main Info Card */}
      <div className="hero-card">
        <div className="hero-content">
          <div className="hero-icon">
            <Share2 />
          </div>
          <div>
            <h2 className="hero-title">Portable Identity</h2>
            <p className="hero-description">
              Allow your verified applicants to share their KYC verification with
              partner organizations without re-doing the entire verification process.
              Tokens are secure, time-limited, and fully auditable.
            </p>
            <div className="hero-features">
              <div className="hero-feature">
                <Clock />
                <span>Max 90-day expiry</span>
              </div>
              <div className="hero-feature">
                <Key />
                <span>Max 10 uses per token</span>
              </div>
              <div className="hero-feature">
                <CheckCircle />
                <span>Consent tracked</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* How It Works */}
      <div className="section-card">
        <h3 className="section-title">How It Works</h3>
        <div className="steps-grid">
          <div className="step-card">
            <div className="step-number">1</div>
            <h4 className="step-title">Select Applicant</h4>
            <p className="step-description">
              Choose an approved applicant to share their KYC
            </p>
          </div>
          <div className="step-card">
            <div className="step-number">2</div>
            <h4 className="step-title">Set Permissions</h4>
            <p className="step-description">
              Choose what data the recipient can access
            </p>
          </div>
          <div className="step-card">
            <div className="step-number">3</div>
            <h4 className="step-title">Generate Token</h4>
            <p className="step-description">
              Create a secure, time-limited share token
            </p>
          </div>
          <div className="step-card">
            <div className="step-number">4</div>
            <h4 className="step-title">Share Securely</h4>
            <p className="step-description">
              Send the token to the verified recipient
            </p>
          </div>
        </div>
      </div>

      {/* Feature Cards */}
      <div className="features-grid">
        {features.map((feature, index) => {
          const Icon = feature.icon;
          return (
            <div key={index} className="feature-card">
              <div className="feature-icon">
                <Icon />
              </div>
              <div>
                <h4 className="feature-title">{feature.title}</h4>
                <p className="feature-description">{feature.description}</p>
              </div>
            </div>
          );
        })}
      </div>

      {/* Get Started */}
      <div className="cta-card">
        <div className="cta-content">
          <div className="cta-icon">
            <Users />
          </div>
          <div>
            <h3 className="cta-title">Get Started</h3>
            <p className="cta-description">
              Go to an approved applicant's profile and click "Share KYC" to generate a token.
            </p>
          </div>
        </div>
        <button
          onClick={() => navigate('/applicants?status=approved')}
          className="cta-button"
        >
          View Approved Applicants
          <ArrowRight />
        </button>
      </div>
    </div>
  );
}
