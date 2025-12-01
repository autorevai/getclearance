import React from 'react';

const styles = `
  @keyframes shimmer {
    0% {
      background-position: -200% 0;
    }
    100% {
      background-position: 200% 0;
    }
  }

  .skeleton {
    background: linear-gradient(
      90deg,
      var(--bg-tertiary) 25%,
      var(--bg-hover) 50%,
      var(--bg-tertiary) 75%
    );
    background-size: 200% 100%;
    animation: shimmer 1.5s ease-in-out infinite;
    border-radius: 6px;
  }

  .skeleton-text {
    height: 14px;
    margin-bottom: 8px;
  }

  .skeleton-text.short {
    width: 60%;
  }

  .skeleton-text.medium {
    width: 80%;
  }

  .skeleton-circle {
    border-radius: 50%;
  }

  .skeleton-row {
    display: flex;
    align-items: center;
    gap: 16px;
    padding: 16px;
    border-bottom: 1px solid var(--border-color);
  }

  .skeleton-row:last-child {
    border-bottom: none;
  }

  .skeleton-table-container {
    background: var(--bg-secondary);
    border: 1px solid var(--border-color);
    border-radius: 12px;
    overflow: hidden;
  }

  .skeleton-card {
    background: var(--bg-secondary);
    border: 1px solid var(--border-color);
    border-radius: 12px;
    padding: 20px;
    margin-bottom: 16px;
  }
`;

export function SkeletonText({ width = '100%', height = 14, className = '' }) {
  return (
    <div
      className={`skeleton ${className}`}
      style={{ width, height, borderRadius: 4 }}
    />
  );
}

export function SkeletonCircle({ size = 40 }) {
  return (
    <div
      className="skeleton skeleton-circle"
      style={{ width: size, height: size }}
    />
  );
}

export function SkeletonBox({ width = '100%', height = 100 }) {
  return (
    <div
      className="skeleton"
      style={{ width, height }}
    />
  );
}

export function TableRowSkeleton() {
  return (
    <div className="skeleton-row">
      <div className="skeleton" style={{ width: 18, height: 18 }} />
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: 4 }}>
        <SkeletonText width="40%" height={14} />
        <SkeletonText width="60%" height={12} />
        <SkeletonText width="35%" height={12} />
      </div>
      <div style={{ display: 'flex', gap: 6 }}>
        <div className="skeleton" style={{ width: 28, height: 28, borderRadius: 6 }} />
        <div className="skeleton" style={{ width: 28, height: 28, borderRadius: 6 }} />
      </div>
      <div className="skeleton" style={{ width: 80, height: 24, borderRadius: 20 }} />
      <SkeletonText width={60} height={14} />
      <SkeletonText width={80} height={14} />
      <SkeletonText width={100} height={14} />
      <SkeletonText width={80} height={14} />
      <div style={{ display: 'flex', gap: 8 }}>
        <div className="skeleton" style={{ width: 32, height: 32, borderRadius: 6 }} />
        <div className="skeleton" style={{ width: 32, height: 32, borderRadius: 6 }} />
      </div>
    </div>
  );
}

export function ApplicantsTableSkeleton({ rows = 10 }) {
  return (
    <>
      <style>{styles}</style>
      <div className="skeleton-table-container">
        {Array.from({ length: rows }).map((_, idx) => (
          <TableRowSkeleton key={idx} />
        ))}
      </div>
    </>
  );
}

export function ApplicantDetailSkeleton() {
  return (
    <>
      <style>{styles}</style>
      <div style={{ maxWidth: 1400 }}>
        {/* Header skeleton */}
        <div style={{ display: 'flex', gap: 24, marginBottom: 24 }}>
          <div className="skeleton" style={{ width: 80, height: 40, borderRadius: 8 }} />
          <div style={{ flex: 1 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 16, marginBottom: 8 }}>
              <SkeletonText width={200} height={28} />
              <div className="skeleton" style={{ width: 100, height: 28, borderRadius: 20 }} />
            </div>
            <div style={{ display: 'flex', gap: 16 }}>
              <SkeletonText width={150} height={14} />
              <SkeletonText width={100} height={14} />
              <SkeletonText width={180} height={14} />
            </div>
          </div>
          <div style={{ display: 'flex', gap: 12 }}>
            {[1, 2, 3, 4, 5].map((i) => (
              <div key={i} className="skeleton" style={{ width: 100, height: 40, borderRadius: 8 }} />
            ))}
          </div>
        </div>

        {/* Tabs skeleton */}
        <div className="skeleton" style={{ height: 48, borderRadius: 12, marginBottom: 24 }} />

        {/* Content grid skeleton */}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 360px', gap: 24 }}>
          <div>
            <div className="skeleton-card">
              <SkeletonText width={150} height={16} />
              <div style={{ marginTop: 16, display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20 }}>
                {[1, 2, 3, 4, 5, 6].map((i) => (
                  <div key={i}>
                    <SkeletonText width={80} height={12} />
                    <SkeletonText width="90%" height={14} />
                  </div>
                ))}
              </div>
            </div>
          </div>
          <div>
            <div className="skeleton-card" style={{ textAlign: 'center' }}>
              <SkeletonText width={80} height={56} />
              <SkeletonText width={100} height={14} />
              <div className="skeleton" style={{ height: 8, borderRadius: 4, marginTop: 16 }} />
            </div>
          </div>
        </div>
      </div>
    </>
  );
}

export function CardSkeleton({ height = 200 }) {
  return (
    <>
      <style>{styles}</style>
      <div className="skeleton-card">
        <SkeletonText width={150} height={16} />
        <div style={{ marginTop: 16 }}>
          <SkeletonText width="100%" height={14} />
          <SkeletonText width="80%" height={14} />
          <SkeletonText width="60%" height={14} />
        </div>
      </div>
    </>
  );
}

export default function LoadingSkeleton({ type = 'table', rows = 10 }) {
  switch (type) {
    case 'table':
      return <ApplicantsTableSkeleton rows={rows} />;
    case 'detail':
      return <ApplicantDetailSkeleton />;
    case 'card':
      return <CardSkeleton />;
    default:
      return <ApplicantsTableSkeleton rows={rows} />;
  }
}
