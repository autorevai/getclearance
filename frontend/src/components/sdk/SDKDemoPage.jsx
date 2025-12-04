/**
 * SDK Demo Page
 * ==============
 * Test page for the GetClearance Verification SDK.
 *
 * This page demonstrates:
 * 1. How to generate an SDK access token
 * 2. How to embed the verification SDK
 * 3. The full verification flow
 */

import React, { useState } from 'react';
import {
  Play,
  Code,
  Terminal,
  Copy,
  Check,
  RefreshCw,
  ExternalLink,
  Shield,
} from 'lucide-react';
import VerificationSDK from './VerificationSDK';

export default function SDKDemoPage() {
  const [apiKey, setApiKey] = useState('');
  const [externalUserId, setExternalUserId] = useState(`demo_user_${Date.now()}`);
  const [accessToken, setAccessToken] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [showSDK, setShowSDK] = useState(false);
  const [copied, setCopied] = useState(null);
  const [result, setResult] = useState(null);

  const generateToken = async () => {
    if (!apiKey) {
      setError('Please enter your API key');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const response = await fetch('/api/v1/sdk/access-token', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-API-Key': apiKey,
        },
        body: JSON.stringify({
          external_user_id: externalUserId,
          email: 'demo@example.com',
          first_name: 'Demo',
          last_name: 'User',
          flow_name: 'default',
          redirect_url: window.location.href,
          expires_in: 3600,
        }),
      });

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.detail || 'Failed to generate token');
      }

      const data = await response.json();
      setAccessToken(data.access_token);
      setShowSDK(false);
      setResult(null);

    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const copyToClipboard = (text, id) => {
    navigator.clipboard.writeText(text);
    setCopied(id);
    setTimeout(() => setCopied(null), 2000);
  };

  const handleComplete = (completionResult) => {
    setResult(completionResult);
    setShowSDK(false);
  };

  const handleError = (err) => {
    setError(err.message);
  };

  const curlExample = `curl -X POST ${window.location.origin}/api/v1/sdk/access-token \\
  -H "Content-Type: application/json" \\
  -H "X-API-Key: YOUR_API_KEY" \\
  -d '{
    "external_user_id": "user_123",
    "email": "user@example.com",
    "flow_name": "default"
  }'`;

  const jsExample = `// 1. Generate access token from your backend
const response = await fetch('/api/v1/sdk/access-token', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'X-API-Key': process.env.GETCLEARANCE_API_KEY,
  },
  body: JSON.stringify({
    external_user_id: user.id,
    email: user.email,
  }),
});
const { access_token, sdk_url } = await response.json();

// 2. Redirect user to SDK or embed in iframe
window.location.href = sdk_url;

// OR embed the React component:
<VerificationSDK
  accessToken={access_token}
  onComplete={(result) => console.log('Done!', result)}
  onError={(error) => console.error(error)}
/>`;

  return (
    <div className="sdk-demo-page">
      <div className="demo-container">
        {/* Header */}
        <div className="demo-header">
          <div className="logo">
            <Shield size={32} />
            <span>GetClearance</span>
          </div>
          <h1>Web SDK Demo</h1>
          <p>
            Test the embeddable verification SDK that your customers can
            use to verify their identity.
          </p>
        </div>

        {!showSDK ? (
          <>
            {/* Step 1: API Key */}
            <div className="demo-section">
              <div className="section-header">
                <span className="step-number">1</span>
                <h2>Enter Your API Key</h2>
              </div>
              <p>
                Get your API key from the{' '}
                <a href="/integrations">Integrations page</a> or use a test key.
              </p>
              <div className="input-group">
                <input
                  type="password"
                  placeholder="sk_live_xxxxx or test_xxxxx"
                  value={apiKey}
                  onChange={(e) => setApiKey(e.target.value)}
                />
                <button
                  className="btn-secondary"
                  onClick={() => setApiKey('test_demo_key')}
                >
                  Use Test Key
                </button>
              </div>
            </div>

            {/* Step 2: User ID */}
            <div className="demo-section">
              <div className="section-header">
                <span className="step-number">2</span>
                <h2>External User ID</h2>
              </div>
              <p>
                This is your unique identifier for the user in your system.
              </p>
              <div className="input-group">
                <input
                  type="text"
                  placeholder="user_123"
                  value={externalUserId}
                  onChange={(e) => setExternalUserId(e.target.value)}
                />
                <button
                  className="btn-secondary"
                  onClick={() => setExternalUserId(`demo_user_${Date.now()}`)}
                >
                  <RefreshCw size={16} />
                </button>
              </div>
            </div>

            {/* Step 3: Generate Token */}
            <div className="demo-section">
              <div className="section-header">
                <span className="step-number">3</span>
                <h2>Generate Access Token</h2>
              </div>
              <p>
                This would normally be done on your backend server.
              </p>
              <button
                className="btn-primary"
                onClick={generateToken}
                disabled={loading || !apiKey}
              >
                {loading ? 'Generating...' : 'Generate Token'}
              </button>

              {error && (
                <div className="error-box">
                  {error}
                </div>
              )}

              {accessToken && (
                <div className="token-box">
                  <div className="token-header">
                    <span>Access Token</span>
                    <button
                      className="copy-btn"
                      onClick={() => copyToClipboard(accessToken, 'token')}
                    >
                      {copied === 'token' ? <Check size={14} /> : <Copy size={14} />}
                    </button>
                  </div>
                  <code>{accessToken}</code>
                </div>
              )}
            </div>

            {/* Step 4: Launch SDK */}
            {accessToken && (
              <div className="demo-section">
                <div className="section-header">
                  <span className="step-number">4</span>
                  <h2>Launch Verification SDK</h2>
                </div>
                <p>
                  Start the verification flow. This is what your users will see.
                </p>
                <div className="launch-options">
                  <button
                    className="btn-primary large"
                    onClick={() => setShowSDK(true)}
                  >
                    <Play size={20} />
                    Open SDK Here
                  </button>
                  <a
                    href={`/sdk/verify?token=${accessToken}`}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="btn-secondary large"
                  >
                    <ExternalLink size={20} />
                    Open in New Tab
                  </a>
                </div>
              </div>
            )}

            {/* Result */}
            {result && (
              <div className="demo-section">
                <div className="section-header">
                  <span className="step-number success">✓</span>
                  <h2>Verification Submitted</h2>
                </div>
                <div className="result-box">
                  <pre>{JSON.stringify(result, null, 2)}</pre>
                </div>
              </div>
            )}

            {/* Code Examples */}
            <div className="demo-section code-section">
              <h2>Integration Code Examples</h2>

              <div className="code-tabs">
                <div className="code-tab">
                  <div className="tab-header">
                    <Terminal size={16} />
                    cURL
                  </div>
                  <div className="code-block">
                    <button
                      className="copy-btn"
                      onClick={() => copyToClipboard(curlExample, 'curl')}
                    >
                      {copied === 'curl' ? <Check size={14} /> : <Copy size={14} />}
                    </button>
                    <pre>{curlExample}</pre>
                  </div>
                </div>

                <div className="code-tab">
                  <div className="tab-header">
                    <Code size={16} />
                    JavaScript / React
                  </div>
                  <div className="code-block">
                    <button
                      className="copy-btn"
                      onClick={() => copyToClipboard(jsExample, 'js')}
                    >
                      {copied === 'js' ? <Check size={14} /> : <Copy size={14} />}
                    </button>
                    <pre>{jsExample}</pre>
                  </div>
                </div>
              </div>
            </div>
          </>
        ) : (
          /* SDK Embedded View */
          <div className="sdk-container">
            <button
              className="close-sdk"
              onClick={() => setShowSDK(false)}
            >
              ← Back to Demo
            </button>
            <VerificationSDK
              accessToken={accessToken}
              onComplete={handleComplete}
              onError={handleError}
            />
          </div>
        )}
      </div>

      <style>{`
        .sdk-demo-page {
          min-height: 100vh;
          background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
          padding: 40px 20px;
          font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        }

        .demo-container {
          max-width: 800px;
          margin: 0 auto;
        }

        .demo-header {
          text-align: center;
          margin-bottom: 48px;
        }

        .logo {
          display: flex;
          align-items: center;
          justify-content: center;
          gap: 12px;
          color: #6366f1;
          font-size: 24px;
          font-weight: 700;
          margin-bottom: 24px;
        }

        .demo-header h1 {
          font-size: 36px;
          font-weight: 700;
          color: #111827;
          margin: 0 0 12px;
        }

        .demo-header p {
          font-size: 18px;
          color: #6b7280;
          max-width: 500px;
          margin: 0 auto;
        }

        .demo-section {
          background: white;
          border-radius: 16px;
          padding: 32px;
          margin-bottom: 24px;
          box-shadow: 0 4px 24px rgba(0, 0, 0, 0.06);
        }

        .section-header {
          display: flex;
          align-items: center;
          gap: 16px;
          margin-bottom: 16px;
        }

        .step-number {
          width: 32px;
          height: 32px;
          border-radius: 50%;
          background: linear-gradient(135deg, #6366f1, #8b5cf6);
          color: white;
          display: flex;
          align-items: center;
          justify-content: center;
          font-weight: 600;
          font-size: 14px;
        }

        .step-number.success {
          background: linear-gradient(135deg, #10b981, #34d399);
        }

        .section-header h2 {
          margin: 0;
          font-size: 20px;
          color: #111827;
        }

        .demo-section p {
          color: #6b7280;
          margin: 0 0 20px;
          line-height: 1.6;
        }

        .demo-section a {
          color: #6366f1;
          text-decoration: none;
        }

        .demo-section a:hover {
          text-decoration: underline;
        }

        .input-group {
          display: flex;
          gap: 12px;
        }

        .input-group input {
          flex: 1;
          padding: 14px 16px;
          border: 2px solid #e5e7eb;
          border-radius: 12px;
          font-size: 15px;
          transition: border-color 0.2s;
        }

        .input-group input:focus {
          outline: none;
          border-color: #6366f1;
        }

        .btn-primary {
          padding: 14px 28px;
          background: linear-gradient(135deg, #6366f1, #8b5cf6);
          color: white;
          border: none;
          border-radius: 12px;
          font-size: 15px;
          font-weight: 600;
          cursor: pointer;
          transition: all 0.2s;
          display: inline-flex;
          align-items: center;
          gap: 8px;
        }

        .btn-primary:hover:not(:disabled) {
          transform: translateY(-1px);
          box-shadow: 0 4px 12px rgba(99, 102, 241, 0.4);
        }

        .btn-primary:disabled {
          opacity: 0.6;
          cursor: not-allowed;
        }

        .btn-secondary {
          padding: 14px 20px;
          background: #f3f4f6;
          color: #374151;
          border: none;
          border-radius: 12px;
          font-size: 15px;
          font-weight: 500;
          cursor: pointer;
          transition: all 0.2s;
          display: inline-flex;
          align-items: center;
          gap: 8px;
          text-decoration: none;
        }

        .btn-secondary:hover {
          background: #e5e7eb;
        }

        .btn-primary.large,
        .btn-secondary.large {
          padding: 18px 32px;
          font-size: 16px;
        }

        .launch-options {
          display: flex;
          gap: 16px;
          flex-wrap: wrap;
        }

        .error-box {
          margin-top: 16px;
          padding: 16px;
          background: #fef2f2;
          border: 1px solid #fecaca;
          border-radius: 12px;
          color: #dc2626;
        }

        .token-box {
          margin-top: 16px;
          background: #f0fdf4;
          border: 1px solid #bbf7d0;
          border-radius: 12px;
          overflow: hidden;
        }

        .token-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 12px 16px;
          background: #dcfce7;
          font-weight: 600;
          color: #166534;
          font-size: 14px;
        }

        .token-box code {
          display: block;
          padding: 16px;
          font-size: 13px;
          word-break: break-all;
          color: #166534;
        }

        .copy-btn {
          padding: 6px;
          background: transparent;
          border: none;
          cursor: pointer;
          color: inherit;
          opacity: 0.7;
          transition: opacity 0.2s;
        }

        .copy-btn:hover {
          opacity: 1;
        }

        .result-box {
          background: #f9fafb;
          border-radius: 12px;
          padding: 16px;
          overflow: auto;
        }

        .result-box pre {
          margin: 0;
          font-size: 13px;
          color: #374151;
        }

        /* Code examples */
        .code-section h2 {
          font-size: 20px;
          margin: 0 0 24px;
          color: #111827;
        }

        .code-tabs {
          display: flex;
          flex-direction: column;
          gap: 16px;
        }

        .code-tab {
          border: 1px solid #e5e7eb;
          border-radius: 12px;
          overflow: hidden;
        }

        .tab-header {
          display: flex;
          align-items: center;
          gap: 8px;
          padding: 12px 16px;
          background: #f9fafb;
          font-weight: 600;
          font-size: 14px;
          color: #374151;
        }

        .code-block {
          position: relative;
          background: #1e1e1e;
          padding: 16px;
        }

        .code-block .copy-btn {
          position: absolute;
          top: 12px;
          right: 12px;
          color: #9ca3af;
        }

        .code-block pre {
          margin: 0;
          font-size: 13px;
          color: #d4d4d4;
          overflow-x: auto;
          line-height: 1.6;
        }

        /* SDK container */
        .sdk-container {
          background: white;
          border-radius: 16px;
          padding: 24px;
          box-shadow: 0 4px 24px rgba(0, 0, 0, 0.1);
        }

        .close-sdk {
          display: flex;
          align-items: center;
          gap: 8px;
          padding: 10px 16px;
          background: transparent;
          border: 1px solid #e5e7eb;
          border-radius: 8px;
          font-size: 14px;
          color: #6b7280;
          cursor: pointer;
          margin-bottom: 24px;
        }

        .close-sdk:hover {
          background: #f9fafb;
        }

        @media (max-width: 640px) {
          .sdk-demo-page {
            padding: 20px 16px;
          }

          .demo-section {
            padding: 24px;
          }

          .demo-header h1 {
            font-size: 28px;
          }

          .input-group {
            flex-direction: column;
          }

          .launch-options {
            flex-direction: column;
          }
        }
      `}</style>
    </div>
  );
}
