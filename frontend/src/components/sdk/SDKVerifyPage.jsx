/**
 * SDK Verify Page
 * ================
 * Standalone page for SDK verification flow.
 *
 * Access via: /sdk/verify?token=sdk_xxx
 *
 * This page can be opened in an iframe or new window by customers.
 */

import React, { useMemo } from 'react';
import { useSearchParams } from 'react-router-dom';
import VerificationSDK from './VerificationSDK';

export default function SDKVerifyPage() {
  const [searchParams] = useSearchParams();

  const token = searchParams.get('token');
  const theme = searchParams.get('theme') || 'light';

  // Determine API base URL from current environment
  const baseUrl = useMemo(() => {
    // In production, use the same origin
    // In development, proxy to backend
    return '/api/v1/sdk';
  }, []);

  const handleComplete = (result) => {
    console.log('Verification complete:', result);

    // If there's a redirect URL, the SDK component handles it
    // Otherwise, show a success message or close the window
    if (!result?.redirect_url) {
      // Post message to parent window (for iframe integration)
      if (window.parent !== window) {
        window.parent.postMessage(
          { type: 'getclearance:complete', result },
          '*'
        );
      }
    }
  };

  const handleError = (error) => {
    console.error('Verification error:', error);

    // Post message to parent window
    if (window.parent !== window) {
      window.parent.postMessage(
        { type: 'getclearance:error', error: error.message },
        '*'
      );
    }
  };

  if (!token) {
    return (
      <div className="sdk-page">
        <div className="sdk-page-error">
          <h1>Missing Token</h1>
          <p>
            No verification token provided. Please use the URL provided by
            your application.
          </p>
        </div>
        <style>{`
          .sdk-page {
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 24px;
            background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
          }
          .sdk-page-error {
            text-align: center;
            padding: 48px;
            background: white;
            border-radius: 16px;
            box-shadow: 0 4px 24px rgba(0, 0, 0, 0.1);
            max-width: 400px;
          }
          .sdk-page-error h1 {
            color: #ef4444;
            margin: 0 0 16px;
          }
          .sdk-page-error p {
            color: #6b7280;
            margin: 0;
          }
        `}</style>
      </div>
    );
  }

  return (
    <div className={`sdk-page ${theme}`}>
      <VerificationSDK
        accessToken={token}
        baseUrl={baseUrl}
        onComplete={handleComplete}
        onError={handleError}
        theme={theme}
      />
      <style>{`
        .sdk-page {
          min-height: 100vh;
          display: flex;
          align-items: center;
          justify-content: center;
          padding: 24px;
          background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
        }
        .sdk-page.dark {
          background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
        }
        @media (max-width: 480px) {
          .sdk-page {
            padding: 0;
            align-items: stretch;
          }
        }
      `}</style>
    </div>
  );
}
