import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Home, ArrowLeft, Search, FileQuestion } from 'lucide-react';

const styles = `
  .not-found-page {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    min-height: 80vh;
    padding: 40px 20px;
    text-align: center;
  }

  .not-found-illustration {
    position: relative;
    margin-bottom: 32px;
  }

  .not-found-code {
    font-size: 120px;
    font-weight: 800;
    color: var(--bg-tertiary);
    letter-spacing: -0.05em;
    line-height: 1;
    user-select: none;
  }

  .not-found-icon-wrapper {
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    width: 80px;
    height: 80px;
    background: var(--bg-secondary);
    border: 2px solid var(--border-color);
    border-radius: 20px;
    display: flex;
    align-items: center;
    justify-content: center;
    color: var(--text-muted);
  }

  .not-found-title {
    font-size: 24px;
    font-weight: 700;
    color: var(--text-primary);
    margin-bottom: 8px;
    letter-spacing: -0.02em;
  }

  .not-found-message {
    font-size: 16px;
    color: var(--text-secondary);
    max-width: 400px;
    line-height: 1.6;
    margin-bottom: 32px;
  }

  .not-found-actions {
    display: flex;
    gap: 12px;
    flex-wrap: wrap;
    justify-content: center;
  }

  .not-found-btn {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    padding: 12px 24px;
    border-radius: 10px;
    font-size: 14px;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.15s;
    text-decoration: none;
    border: none;
    font-family: inherit;
  }

  .not-found-btn-primary {
    background: var(--accent-primary);
    color: white;
  }

  .not-found-btn-primary:hover {
    opacity: 0.9;
    transform: translateY(-1px);
  }

  .not-found-btn-secondary {
    background: var(--bg-secondary);
    border: 1px solid var(--border-color);
    color: var(--text-primary);
  }

  .not-found-btn-secondary:hover {
    background: var(--bg-hover);
  }

  .not-found-suggestions {
    margin-top: 48px;
    padding-top: 32px;
    border-top: 1px solid var(--border-color);
    max-width: 500px;
  }

  .suggestions-title {
    font-size: 13px;
    color: var(--text-muted);
    text-transform: uppercase;
    letter-spacing: 0.05em;
    margin-bottom: 16px;
  }

  .suggestions-list {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    justify-content: center;
  }

  .suggestion-link {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 8px 16px;
    background: var(--bg-tertiary);
    border: 1px solid var(--border-color);
    border-radius: 20px;
    font-size: 13px;
    color: var(--text-secondary);
    text-decoration: none;
    cursor: pointer;
    transition: all 0.15s;
  }

  .suggestion-link:hover {
    background: var(--bg-hover);
    color: var(--text-primary);
    border-color: var(--accent-primary);
  }
`;

const commonPages = [
  { path: '/', label: 'Dashboard', icon: Home },
  { path: '/applicants', label: 'Applicants', icon: Search },
  { path: '/screening', label: 'Screening', icon: Search },
  { path: '/cases', label: 'Cases', icon: FileQuestion },
];

/**
 * 404 Not Found page component
 *
 * @param {Object} props
 * @param {string} props.title - Custom title (default: "Page not found")
 * @param {string} props.message - Custom message
 * @param {boolean} props.showSuggestions - Show suggested pages (default: true)
 */
export function NotFoundPage({
  title = "Page not found",
  message = "Sorry, we couldn't find the page you're looking for. It might have been moved or deleted.",
  showSuggestions = true,
}) {
  const navigate = useNavigate();

  return (
    <>
      <style>{styles}</style>
      <div className="not-found-page">
        <div className="not-found-illustration">
          <div className="not-found-code">404</div>
          <div className="not-found-icon-wrapper">
            <FileQuestion size={36} />
          </div>
        </div>

        <h1 className="not-found-title">{title}</h1>
        <p className="not-found-message">{message}</p>

        <div className="not-found-actions">
          <button
            className="not-found-btn not-found-btn-secondary"
            onClick={() => navigate(-1)}
          >
            <ArrowLeft size={16} />
            Go Back
          </button>
          <button
            className="not-found-btn not-found-btn-primary"
            onClick={() => navigate('/')}
          >
            <Home size={16} />
            Back to Dashboard
          </button>
        </div>

        {showSuggestions && (
          <div className="not-found-suggestions">
            <div className="suggestions-title">Popular Pages</div>
            <div className="suggestions-list">
              {commonPages.map(({ path, label, icon: Icon }) => (
                <button
                  key={path}
                  className="suggestion-link"
                  onClick={() => navigate(path)}
                >
                  <Icon size={14} />
                  {label}
                </button>
              ))}
            </div>
          </div>
        )}
      </div>
    </>
  );
}

/**
 * Resource not found component (for inline use)
 * Use when an API returns 404 for a specific resource
 */
export function ResourceNotFound({
  resourceType = 'Resource',
  resourceId,
  onBack,
  onHome,
}) {
  return (
    <>
      <style>{styles}</style>
      <div className="not-found-page" style={{ minHeight: 400 }}>
        <div className="not-found-icon-wrapper" style={{ position: 'relative', marginBottom: 24 }}>
          <FileQuestion size={32} />
        </div>

        <h2 className="not-found-title">{resourceType} not found</h2>
        <p className="not-found-message">
          {resourceId
            ? `The ${resourceType.toLowerCase()} with ID "${resourceId}" doesn't exist or has been removed.`
            : `This ${resourceType.toLowerCase()} doesn't exist or has been removed.`}
        </p>

        <div className="not-found-actions">
          {onBack && (
            <button className="not-found-btn not-found-btn-secondary" onClick={onBack}>
              <ArrowLeft size={16} />
              Go Back
            </button>
          )}
          {onHome && (
            <button className="not-found-btn not-found-btn-primary" onClick={onHome}>
              <Home size={16} />
              Back to Dashboard
            </button>
          )}
        </div>
      </div>
    </>
  );
}

export default NotFoundPage;
