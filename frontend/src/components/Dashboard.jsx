import React from 'react';
import {
  TrendingUp,
  TrendingDown,
  Users,
  CheckCircle2,
  XCircle,
  Clock,
  AlertTriangle,
  Shield,
  Sparkles,
  ArrowRight,
  Calendar,
  Filter,
  RefreshCw,
  FileText
} from 'lucide-react';
import {
  useDashboardStats,
  useScreeningSummary,
  useRecentActivity,
  useRefreshDashboard
} from '../hooks/useDashboard';

// AI Insights remain mock data for now (separate AI integration)
const mockAIInsights = [
  {
    type: 'efficiency',
    title: 'Processing Speed Up',
    description: 'Average review time decreased by 23% this week. AI pre-screening is identifying 67% of clear approvals.',
    action: 'View Analytics'
  },
  {
    type: 'risk',
    title: 'Geographic Risk Cluster',
    description: '4 applicants from high-risk jurisdiction detected in the last hour. Consider enhanced due diligence.',
    action: 'Review Applicants'
  },
  {
    type: 'compliance',
    title: 'OFAC List Updated',
    description: 'New sanctions list version (2025-11-27) available. 3 existing applicants require re-screening.',
    action: 'Run Re-screen'
  }
];

const getGreeting = () => {
  const hour = new Date().getHours();
  if (hour < 12) return 'Good morning';
  if (hour < 17) return 'Good afternoon';
  return 'Good evening';
};

// Format relative time for activity feed
function formatRelativeTime(timestamp) {
  const date = new Date(timestamp);
  const now = new Date();
  const diffMs = now - date;
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMs / 3600000);
  const diffDays = Math.floor(diffMs / 86400000);

  if (diffMins < 1) return 'just now';
  if (diffMins < 60) return `${diffMins} min ago`;
  if (diffHours < 24) return `${diffHours} hour${diffHours > 1 ? 's' : ''} ago`;
  return `${diffDays} day${diffDays > 1 ? 's' : ''} ago`;
}

// Build KPI cards from API data
function buildKpiCards(stats) {
  return [
    {
      label: "Today's Applicants",
      value: stats?.today_applicants ?? 0,
      change: stats?.today_applicants_change ?? 0,
      changeLabel: 'vs yesterday',
      trend: (stats?.today_applicants_change ?? 0) > 0 ? 'up' : (stats?.today_applicants_change ?? 0) < 0 ? 'down' : 'neutral',
      icon: Users
    },
    {
      label: 'Approved',
      value: stats?.approved ?? 0,
      change: stats?.approved_change ?? 0,
      changeLabel: 'vs yesterday',
      trend: (stats?.approved_change ?? 0) > 0 ? 'up' : (stats?.approved_change ?? 0) < 0 ? 'down' : 'neutral',
      icon: CheckCircle2,
      color: 'success'
    },
    {
      label: 'Rejected',
      value: stats?.rejected ?? 0,
      change: stats?.rejected_change ?? 0,
      changeLabel: 'vs yesterday',
      trend: (stats?.rejected_change ?? 0) > 0 ? 'up' : (stats?.rejected_change ?? 0) < 0 ? 'down' : 'neutral',
      icon: XCircle,
      color: 'danger'
    },
    {
      label: 'Pending Review',
      value: stats?.pending_review ?? 0,
      change: stats?.pending_review_change ?? 0,
      changeLabel: stats?.pending_review_change === 0 ? 'no change' : 'vs yesterday',
      trend: (stats?.pending_review_change ?? 0) > 0 ? 'up' : (stats?.pending_review_change ?? 0) < 0 ? 'down' : 'neutral',
      icon: Clock,
      color: 'warning'
    }
  ];
}

// Build screening hits from API data
function buildScreeningHits(screening) {
  return [
    { severity: 'high', count: screening?.sanctions_matches ?? 0, label: 'Sanctions Matches' },
    { severity: 'medium', count: screening?.pep_hits ?? 0, label: 'PEP Hits' },
    { severity: 'low', count: screening?.adverse_media ?? 0, label: 'Adverse Media' }
  ];
}

// Skeleton component for loading states
function KPISkeleton() {
  return (
    <div className="kpi-card skeleton">
      <div className="kpi-header">
        <span className="skeleton-text" style={{ width: '100px', height: '13px' }} />
        <div className="skeleton-icon" />
      </div>
      <div className="skeleton-text" style={{ width: '60px', height: '36px', marginBottom: '8px' }} />
      <div className="skeleton-text" style={{ width: '80px', height: '13px' }} />
    </div>
  );
}

function ScreeningSkeleton() {
  return (
    <>
      {[1, 2, 3].map(i => (
        <div key={i} className="screening-bar">
          <span className="skeleton-indicator" />
          <span className="skeleton-text" style={{ flex: 1, height: '14px' }} />
          <span className="skeleton-text" style={{ width: '30px', height: '18px' }} />
        </div>
      ))}
    </>
  );
}

function ActivitySkeleton() {
  return (
    <>
      {[1, 2, 3, 4].map(i => (
        <div key={i} className="activity-item">
          <div className="skeleton-avatar" />
          <div className="activity-content">
            <div className="skeleton-text" style={{ width: '120px', height: '14px', marginBottom: '4px' }} />
            <div className="skeleton-text" style={{ width: '180px', height: '13px' }} />
          </div>
          <span className="skeleton-text" style={{ width: '60px', height: '12px' }} />
        </div>
      ))}
    </>
  );
}

function ErrorState({ message, onRetry }) {
  return (
    <div className="error-state">
      <AlertTriangle size={24} />
      <p>{message}</p>
      {onRetry && (
        <button className="retry-btn" onClick={onRetry}>
          <RefreshCw size={14} />
          Retry
        </button>
      )}
    </div>
  );
}

export default function Dashboard() {
  // Fetch dashboard data
  const { data: stats, isLoading: statsLoading, isError: statsError, refetch: refetchStats } = useDashboardStats();
  const { data: screening, isLoading: screeningLoading, isError: screeningError, refetch: refetchScreening } = useScreeningSummary();
  const { data: activity, isLoading: activityLoading, isError: activityError, refetch: refetchActivity } = useRecentActivity();
  const refreshAll = useRefreshDashboard();

  // Derive display data from API response
  const kpiCards = buildKpiCards(stats);
  const screeningHits = buildScreeningHits(screening);
  const activityItems = activity?.items ?? [];

  // Last updated timestamp
  const lastUpdated = stats ? new Date().toLocaleTimeString() : null;

  return (
    <div className="dashboard">
      <style>{`
        .dashboard {
          max-width: 1400px;
        }
        
        .dashboard-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 24px;
        }
        
        .dashboard-title {
          font-size: 28px;
          font-weight: 600;
          letter-spacing: -0.02em;
        }
        
        .dashboard-subtitle {
          color: var(--text-secondary);
          font-size: 14px;
          margin-top: 4px;
        }
        
        .dashboard-filters {
          display: flex;
          gap: 12px;
        }
        
        .filter-btn {
          display: flex;
          align-items: center;
          gap: 8px;
          padding: 8px 16px;
          background: var(--bg-secondary);
          border: 1px solid var(--border-color);
          border-radius: 8px;
          color: var(--text-secondary);
          font-size: 14px;
          cursor: pointer;
          transition: all 0.15s;
        }
        
        .filter-btn:hover {
          background: var(--bg-hover);
          color: var(--text-primary);
        }
        
        /* KPI Grid */
        .kpi-grid {
          display: grid;
          grid-template-columns: repeat(4, 1fr);
          gap: 16px;
          margin-bottom: 24px;
        }
        
        .kpi-card {
          background: var(--bg-secondary);
          border: 1px solid var(--border-color);
          border-radius: 12px;
          padding: 20px;
          transition: all 0.2s;
        }
        
        .kpi-card:hover {
          border-color: var(--accent-primary);
          box-shadow: 0 0 0 3px var(--accent-glow);
        }
        
        .kpi-header {
          display: flex;
          justify-content: space-between;
          align-items: flex-start;
          margin-bottom: 12px;
        }
        
        .kpi-label {
          font-size: 13px;
          color: var(--text-secondary);
          font-weight: 500;
        }
        
        .kpi-icon {
          width: 36px;
          height: 36px;
          border-radius: 8px;
          display: flex;
          align-items: center;
          justify-content: center;
          background: var(--bg-tertiary);
          color: var(--text-secondary);
        }
        
        .kpi-icon.success { background: rgba(16, 185, 129, 0.15); color: var(--success); }
        .kpi-icon.danger { background: rgba(239, 68, 68, 0.15); color: var(--danger); }
        .kpi-icon.warning { background: rgba(245, 158, 11, 0.15); color: var(--warning); }
        
        .kpi-value {
          font-size: 36px;
          font-weight: 700;
          letter-spacing: -0.02em;
          margin-bottom: 8px;
        }
        
        .kpi-change {
          display: flex;
          align-items: center;
          gap: 4px;
          font-size: 13px;
        }
        
        .kpi-change.up { color: var(--success); }
        .kpi-change.down { color: var(--danger); }
        .kpi-change.neutral { color: var(--text-muted); }
        
        /* Main Grid */
        .dashboard-grid {
          display: grid;
          grid-template-columns: 2fr 1fr;
          gap: 24px;
        }
        
        .card {
          background: var(--bg-secondary);
          border: 1px solid var(--border-color);
          border-radius: 12px;
          overflow: hidden;
        }
        
        .card-header {
          padding: 16px 20px;
          border-bottom: 1px solid var(--border-color);
          display: flex;
          justify-content: space-between;
          align-items: center;
        }
        
        .card-title {
          font-size: 15px;
          font-weight: 600;
          display: flex;
          align-items: center;
          gap: 8px;
        }
        
        .card-action {
          font-size: 13px;
          color: var(--accent-primary);
          cursor: pointer;
          display: flex;
          align-items: center;
          gap: 4px;
        }
        
        .card-action:hover {
          text-decoration: underline;
        }
        
        .card-content {
          padding: 20px;
        }
        
        /* AI Insights */
        .ai-insights-card {
          border: 1px solid var(--accent-primary);
          background: linear-gradient(135deg, var(--bg-secondary), var(--accent-glow));
        }
        
        .ai-insight {
          padding: 16px;
          background: var(--bg-tertiary);
          border-radius: 8px;
          margin-bottom: 12px;
        }
        
        .ai-insight:last-child {
          margin-bottom: 0;
        }
        
        .ai-insight-header {
          display: flex;
          align-items: center;
          gap: 8px;
          margin-bottom: 8px;
        }
        
        .ai-insight-type {
          font-size: 10px;
          font-weight: 600;
          text-transform: uppercase;
          letter-spacing: 0.05em;
          padding: 2px 6px;
          border-radius: 4px;
        }
        
        .ai-insight-type.efficiency {
          background: rgba(16, 185, 129, 0.15);
          color: var(--success);
        }
        
        .ai-insight-type.risk {
          background: rgba(245, 158, 11, 0.15);
          color: var(--warning);
        }
        
        .ai-insight-type.compliance {
          background: rgba(59, 130, 246, 0.15);
          color: var(--info);
        }
        
        .ai-insight-title {
          font-size: 14px;
          font-weight: 600;
        }
        
        .ai-insight-description {
          font-size: 13px;
          color: var(--text-secondary);
          line-height: 1.5;
          margin-bottom: 12px;
        }
        
        .ai-insight-action {
          font-size: 13px;
          color: var(--accent-primary);
          font-weight: 500;
          cursor: pointer;
          display: inline-flex;
          align-items: center;
          gap: 4px;
        }
        
        /* Screening Summary */
        .screening-bar {
          display: flex;
          align-items: center;
          padding: 12px 0;
          border-bottom: 1px solid var(--border-color);
        }
        
        .screening-bar:last-child {
          border-bottom: none;
        }
        
        .screening-indicator {
          width: 8px;
          height: 8px;
          border-radius: 50%;
          margin-right: 12px;
        }
        
        .screening-indicator.high { background: var(--danger); }
        .screening-indicator.medium { background: var(--warning); }
        .screening-indicator.low { background: var(--info); }
        
        .screening-label {
          flex: 1;
          font-size: 14px;
        }
        
        .screening-count {
          font-size: 18px;
          font-weight: 600;
        }
        
        /* Activity Feed */
        .activity-item {
          display: flex;
          gap: 12px;
          padding: 14px 0;
          border-bottom: 1px solid var(--border-color);
        }
        
        .activity-item:last-child {
          border-bottom: none;
        }
        
        .activity-icon {
          width: 32px;
          height: 32px;
          border-radius: 50%;
          display: flex;
          align-items: center;
          justify-content: center;
          flex-shrink: 0;
        }
        
        .activity-icon.approved {
          background: rgba(16, 185, 129, 0.15);
          color: var(--success);
        }
        
        .activity-icon.rejected {
          background: rgba(239, 68, 68, 0.15);
          color: var(--danger);
        }
        
        .activity-icon.screening_hit {
          background: rgba(245, 158, 11, 0.15);
          color: var(--warning);
        }
        
        .activity-icon.resubmission {
          background: rgba(59, 130, 246, 0.15);
          color: var(--info);
        }
        
        .activity-content {
          flex: 1;
          min-width: 0;
        }
        
        .activity-title {
          font-size: 14px;
          font-weight: 500;
          margin-bottom: 2px;
        }
        
        .activity-detail {
          font-size: 13px;
          color: var(--text-secondary);
        }
        
        .activity-time {
          font-size: 12px;
          color: var(--text-muted);
          white-space: nowrap;
        }
        
        /* SLA Widget */
        .sla-ring {
          width: 120px;
          height: 120px;
          margin: 0 auto 16px;
          position: relative;
        }
        
        .sla-ring svg {
          transform: rotate(-90deg);
        }
        
        .sla-ring-bg {
          fill: none;
          stroke: var(--bg-tertiary);
          stroke-width: 8;
        }
        
        .sla-ring-progress {
          fill: none;
          stroke: var(--success);
          stroke-width: 8;
          stroke-linecap: round;
          stroke-dasharray: 339.3;
          stroke-dashoffset: 33.93;
        }
        
        .sla-ring-text {
          position: absolute;
          inset: 0;
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
        }
        
        .sla-percentage {
          font-size: 28px;
          font-weight: 700;
        }
        
        .sla-label {
          font-size: 12px;
          color: var(--text-muted);
        }
        
        .sla-stats {
          display: grid;
          grid-template-columns: 1fr 1fr;
          gap: 12px;
          text-align: center;
        }
        
        .sla-stat-value {
          font-size: 20px;
          font-weight: 600;
        }
        
        .sla-stat-label {
          font-size: 12px;
          color: var(--text-muted);
        }
        
        /* Skeleton Loading States */
        .skeleton-text {
          background: linear-gradient(90deg, var(--bg-tertiary) 25%, var(--bg-hover) 50%, var(--bg-tertiary) 75%);
          background-size: 200% 100%;
          animation: skeleton-pulse 1.5s ease-in-out infinite;
          border-radius: 4px;
          display: block;
        }

        .skeleton-icon {
          width: 36px;
          height: 36px;
          border-radius: 8px;
          background: var(--bg-tertiary);
          animation: skeleton-pulse 1.5s ease-in-out infinite;
        }

        .skeleton-indicator {
          width: 8px;
          height: 8px;
          border-radius: 50%;
          margin-right: 12px;
          background: var(--bg-tertiary);
          animation: skeleton-pulse 1.5s ease-in-out infinite;
        }

        .skeleton-avatar {
          width: 32px;
          height: 32px;
          border-radius: 50%;
          background: var(--bg-tertiary);
          animation: skeleton-pulse 1.5s ease-in-out infinite;
          flex-shrink: 0;
        }

        .kpi-card.skeleton:hover {
          border-color: var(--border-color);
          box-shadow: none;
        }

        @keyframes skeleton-pulse {
          0% { background-position: 200% 0; }
          100% { background-position: -200% 0; }
        }

        /* Error State */
        .error-state {
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          padding: 32px 20px;
          color: var(--text-secondary);
          text-align: center;
          gap: 12px;
        }

        .error-state p {
          margin: 0;
          font-size: 14px;
        }

        .retry-btn {
          display: flex;
          align-items: center;
          gap: 6px;
          padding: 8px 16px;
          background: var(--accent-primary);
          color: white;
          border: none;
          border-radius: 6px;
          font-size: 13px;
          font-weight: 500;
          cursor: pointer;
          transition: all 0.15s;
        }

        .retry-btn:hover {
          opacity: 0.9;
        }

        /* Refresh Button */
        .refresh-btn {
          display: flex;
          align-items: center;
          gap: 6px;
          padding: 8px 12px;
          background: transparent;
          border: 1px solid var(--border-color);
          border-radius: 6px;
          color: var(--text-secondary);
          font-size: 13px;
          cursor: pointer;
          transition: all 0.15s;
        }

        .refresh-btn:hover {
          background: var(--bg-hover);
          color: var(--text-primary);
        }

        .refresh-btn.spinning svg {
          animation: spin 1s linear infinite;
        }

        @keyframes spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }

        /* Last Updated */
        .last-updated {
          font-size: 12px;
          color: var(--text-muted);
          display: flex;
          align-items: center;
          gap: 4px;
        }

        /* Empty State */
        .empty-state {
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          padding: 32px 20px;
          color: var(--text-muted);
          text-align: center;
          gap: 8px;
        }

        .empty-state p {
          margin: 0;
          font-size: 14px;
        }

        /* Document uploaded activity icon */
        .activity-icon.document_uploaded {
          background: rgba(139, 92, 246, 0.15);
          color: var(--purple, #8B5CF6);
        }

        @media (max-width: 1200px) {
          .kpi-grid {
            grid-template-columns: repeat(2, 1fr);
          }

          .dashboard-grid {
            grid-template-columns: 1fr;
          }
        }
      `}</style>
      
      <div className="dashboard-header">
        <div>
          <h1 className="dashboard-title">{getGreeting()}</h1>
          <p className="dashboard-subtitle">Here's what's happening with your compliance pipeline</p>
          {lastUpdated && (
            <span className="last-updated">Last updated: {lastUpdated}</span>
          )}
        </div>

        <div className="dashboard-filters">
          <button
            className={`refresh-btn ${statsLoading ? 'spinning' : ''}`}
            onClick={refreshAll}
            disabled={statsLoading}
          >
            <RefreshCw size={14} />
            Refresh
          </button>
          <button className="filter-btn">
            <Calendar size={16} />
            Today
          </button>
          <button className="filter-btn">
            <Filter size={16} />
            All Products
          </button>
        </div>
      </div>
      
      <div className="kpi-grid">
        {statsLoading ? (
          <>
            <KPISkeleton />
            <KPISkeleton />
            <KPISkeleton />
            <KPISkeleton />
          </>
        ) : statsError ? (
          <div className="kpi-card" style={{ gridColumn: '1 / -1' }}>
            <ErrorState message="Failed to load stats" onRetry={refetchStats} />
          </div>
        ) : (
          kpiCards.map((kpi, idx) => (
            <div key={idx} className="kpi-card">
              <div className="kpi-header">
                <span className="kpi-label">{kpi.label}</span>
                <div className={`kpi-icon ${kpi.color || ''}`}>
                  <kpi.icon size={18} />
                </div>
              </div>
              <div className="kpi-value">{kpi.value}</div>
              <div className={`kpi-change ${kpi.trend}`}>
                {kpi.trend === 'up' && <TrendingUp size={14} />}
                {kpi.trend === 'down' && <TrendingDown size={14} />}
                {kpi.change > 0 ? `+${kpi.change}` : kpi.change} {kpi.changeLabel}
              </div>
            </div>
          ))
        )}
      </div>
      
      <div className="dashboard-grid">
        <div className="left-column">
          <div className="card ai-insights-card" style={{ marginBottom: 24 }}>
            <div className="card-header">
              <div className="card-title">
                <Sparkles size={18} style={{ color: 'var(--accent-primary)' }} />
                AI Insights
              </div>
              <span className="card-action">
                View All <ArrowRight size={14} />
              </span>
            </div>
            <div className="card-content">
              {mockAIInsights.map((insight, idx) => (
                <div key={idx} className="ai-insight">
                  <div className="ai-insight-header">
                    <span className={`ai-insight-type ${insight.type}`}>{insight.type}</span>
                    <span className="ai-insight-title">{insight.title}</span>
                  </div>
                  <p className="ai-insight-description">{insight.description}</p>
                  <span className="ai-insight-action">
                    {insight.action} <ArrowRight size={12} />
                  </span>
                </div>
              ))}
            </div>
          </div>
          
          <div className="card">
            <div className="card-header">
              <div className="card-title">Recent Activity</div>
              <span className="card-action">
                View All <ArrowRight size={14} />
              </span>
            </div>
            <div className="card-content">
              {activityLoading ? (
                <ActivitySkeleton />
              ) : activityError ? (
                <ErrorState message="Failed to load activity" onRetry={refetchActivity} />
              ) : activityItems.length === 0 ? (
                <div className="empty-state">
                  <Clock size={24} />
                  <p>No recent activity</p>
                </div>
              ) : (
                activityItems.map((item, idx) => (
                  <div key={idx} className="activity-item">
                    <div className={`activity-icon ${item.type}`}>
                      {item.type === 'approved' && <CheckCircle2 size={16} />}
                      {item.type === 'rejected' && <XCircle size={16} />}
                      {item.type === 'screening_hit' && <AlertTriangle size={16} />}
                      {item.type === 'resubmission' && <Clock size={16} />}
                      {item.type === 'document_uploaded' && <FileText size={16} />}
                    </div>
                    <div className="activity-content">
                      <div className="activity-title">{item.applicant_name}</div>
                      <div className="activity-detail">
                        {item.type === 'approved' && `Approved by ${item.reviewer || 'System'}`}
                        {item.type === 'rejected' && (item.detail ? `${item.detail}` : `Rejected by ${item.reviewer || 'System'}`)}
                        {item.type === 'screening_hit' && item.detail}
                        {item.type === 'resubmission' && item.detail}
                        {item.type === 'document_uploaded' && item.detail}
                      </div>
                    </div>
                    <span className="activity-time">{formatRelativeTime(item.time)}</span>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
        
        <div className="right-column">
          <div className="card" style={{ marginBottom: 24 }}>
            <div className="card-header">
              <div className="card-title">
                <Shield size={16} />
                Screening Hits
              </div>
            </div>
            <div className="card-content">
              {screeningLoading ? (
                <ScreeningSkeleton />
              ) : screeningError ? (
                <ErrorState message="Failed to load screening data" onRetry={refetchScreening} />
              ) : (
                screeningHits.map((hit, idx) => (
                  <div key={idx} className="screening-bar">
                    <span className={`screening-indicator ${hit.severity}`} />
                    <span className="screening-label">{hit.label}</span>
                    <span className="screening-count">{hit.count}</span>
                  </div>
                ))
              )}
            </div>
          </div>
          
          <div className="card">
            <div className="card-header">
              <div className="card-title">
                <Clock size={16} />
                SLA Performance
              </div>
            </div>
            <div className="card-content">
              <div className="sla-ring">
                <svg width="120" height="120" viewBox="0 0 120 120">
                  <circle className="sla-ring-bg" cx="60" cy="60" r="54" />
                  <circle className="sla-ring-progress" cx="60" cy="60" r="54" />
                </svg>
                <div className="sla-ring-text">
                  <span className="sla-percentage">94%</span>
                  <span className="sla-label">On Time</span>
                </div>
              </div>
              <div className="sla-stats">
                <div>
                  <div className="sla-stat-value">2.4h</div>
                  <div className="sla-stat-label">Avg Review Time</div>
                </div>
                <div>
                  <div className="sla-stat-value">3</div>
                  <div className="sla-stat-label">At Risk</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
