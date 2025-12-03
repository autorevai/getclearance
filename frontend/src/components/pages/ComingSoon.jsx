import React from 'react';
import { ArrowLeft, Clock } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

/**
 * Reusable Coming Soon placeholder page component
 * Shows planned features and expected timeline
 */
export default function ComingSoon({
  title,
  description,
  icon: Icon,
  expectedDate,
  features = []
}) {
  const navigate = useNavigate();

  return (
    <div className="coming-soon-page">
      <style>{`
        .coming-soon-page {
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          min-height: 60vh;
          padding: 40px;
          text-align: center;
        }

        .coming-soon-icon {
          width: 80px;
          height: 80px;
          border-radius: 20px;
          background: var(--accent-glow);
          display: flex;
          align-items: center;
          justify-content: center;
          margin-bottom: 24px;
          color: var(--accent-primary);
        }

        .coming-soon-title {
          font-size: 32px;
          font-weight: 700;
          letter-spacing: -0.02em;
          margin-bottom: 12px;
          color: var(--text-primary);
        }

        .coming-soon-description {
          font-size: 16px;
          color: var(--text-secondary);
          max-width: 480px;
          line-height: 1.6;
          margin-bottom: 32px;
        }

        .planned-features {
          background: var(--bg-secondary);
          border: 1px solid var(--border-color);
          border-radius: 12px;
          padding: 24px;
          max-width: 400px;
          width: 100%;
          margin-bottom: 24px;
          text-align: left;
        }

        .planned-features h3 {
          font-size: 14px;
          font-weight: 600;
          color: var(--text-primary);
          margin-bottom: 16px;
          text-transform: uppercase;
          letter-spacing: 0.05em;
        }

        .planned-features ul {
          list-style: none;
          padding: 0;
          margin: 0;
        }

        .planned-features li {
          display: flex;
          align-items: flex-start;
          gap: 12px;
          padding: 10px 0;
          font-size: 14px;
          color: var(--text-secondary);
          border-bottom: 1px solid var(--border-color);
        }

        .planned-features li:last-child {
          border-bottom: none;
        }

        .feature-bullet {
          width: 6px;
          height: 6px;
          background: var(--accent-primary);
          border-radius: 50%;
          margin-top: 7px;
          flex-shrink: 0;
        }

        .expected-date {
          display: flex;
          align-items: center;
          gap: 8px;
          font-size: 13px;
          color: var(--text-muted);
          margin-bottom: 24px;
        }

        .back-btn {
          display: flex;
          align-items: center;
          gap: 8px;
          padding: 12px 24px;
          background: var(--bg-secondary);
          border: 1px solid var(--border-color);
          border-radius: 8px;
          color: var(--text-primary);
          font-size: 14px;
          font-weight: 500;
          cursor: pointer;
          transition: all 0.15s;
        }

        .back-btn:hover {
          background: var(--bg-hover);
          border-color: var(--accent-primary);
        }

        .beta-badge {
          display: inline-flex;
          align-items: center;
          gap: 4px;
          background: var(--bg-tertiary);
          color: var(--text-muted);
          font-size: 11px;
          font-weight: 600;
          padding: 4px 8px;
          border-radius: 4px;
          text-transform: uppercase;
          letter-spacing: 0.05em;
          margin-left: 8px;
          vertical-align: middle;
        }
      `}</style>

      {Icon && (
        <div className="coming-soon-icon">
          <Icon size={40} />
        </div>
      )}

      <h1 className="coming-soon-title">{title}</h1>
      <p className="coming-soon-description">{description}</p>

      {features.length > 0 && (
        <div className="planned-features">
          <h3>Planned Features</h3>
          <ul>
            {features.map((feature, i) => (
              <li key={i}>
                <span className="feature-bullet" />
                {feature}
              </li>
            ))}
          </ul>
        </div>
      )}

      {expectedDate && (
        <p className="expected-date">
          <Clock size={14} />
          Expected: {expectedDate}
        </p>
      )}

      <button className="back-btn" onClick={() => navigate(-1)}>
        <ArrowLeft size={16} />
        Go Back
      </button>
    </div>
  );
}
