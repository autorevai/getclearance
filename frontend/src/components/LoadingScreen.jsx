import React, { useEffect } from 'react';
import { Shield } from 'lucide-react';

// CSS keyframes injected once
const KEYFRAMES_ID = 'getclearance-loading-keyframes';
const keyframesCSS = `
  @keyframes gc-shimmer {
    0% { background-position: -200% 0; }
    100% { background-position: 200% 0; }
  }
  @keyframes gc-pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.5; }
  }
  @keyframes gc-spin {
    to { transform: rotate(360deg); }
  }
`;

/**
 * LoadingScreen component displays a full-page loading state.
 *
 * Two variants:
 * - 'simple': Basic centered spinner (for redirects)
 * - 'skeleton': Dashboard-like skeleton (for initial auth check)
 *
 * @param {string} message - Optional message to display below the spinner
 * @param {string} variant - 'simple' or 'skeleton' (default: 'simple')
 */
export function LoadingScreen({ message = 'Loading...', variant = 'simple' }) {
  // Inject keyframes CSS once on mount
  useEffect(() => {
    if (!document.getElementById(KEYFRAMES_ID)) {
      const styleSheet = document.createElement('style');
      styleSheet.id = KEYFRAMES_ID;
      styleSheet.textContent = keyframesCSS;
      document.head.appendChild(styleSheet);
    }
  }, []);

  if (variant === 'skeleton') {
    return <DashboardSkeleton message={message} />;
  }

  return (
    <div style={styles.container} role="status" aria-live="polite" aria-busy="true">
      <div style={styles.content}>
        {/* Logo */}
        <div style={styles.logoIcon} aria-hidden="true">
          <Shield size={32} color="#10b981" />
        </div>

        {/* Spinner */}
        <div style={styles.spinnerContainer} aria-hidden="true">
          <div style={styles.spinner} />
        </div>

        {/* Message */}
        <p style={styles.message}>{message}</p>
        <span className="sr-only">Loading, please wait</span>
      </div>
    </div>
  );
}

/**
 * Dashboard skeleton loader that matches the actual dashboard layout
 */
function DashboardSkeleton({ message }) {
  return (
    <div style={skeletonStyles.container} role="status" aria-live="polite" aria-busy="true">
      {/* Sidebar skeleton */}
      <aside style={skeletonStyles.sidebar} aria-hidden="true">
        <div style={skeletonStyles.sidebarHeader}>
          <div style={skeletonStyles.logoPlaceholder} />
          <div style={skeletonStyles.brandPlaceholder} />
        </div>
        <nav style={skeletonStyles.navSection}>
          {[1, 2, 3, 4, 5].map((i) => (
            <div key={i} style={skeletonStyles.navItem}>
              <div style={skeletonStyles.navIcon} />
              <div style={skeletonStyles.navLabel} />
            </div>
          ))}
          <div style={skeletonStyles.navDivider} />
          {[6, 7, 8].map((i) => (
            <div key={i} style={skeletonStyles.navItem}>
              <div style={skeletonStyles.navIcon} />
              <div style={skeletonStyles.navLabel} />
            </div>
          ))}
        </nav>
      </aside>

      {/* Main content skeleton */}
      <div style={skeletonStyles.mainWrapper}>
        {/* Top bar skeleton */}
        <header style={skeletonStyles.topBar}>
          <div style={skeletonStyles.searchBar} />
          <div style={skeletonStyles.topBarActions}>
            <div style={skeletonStyles.iconBtn} />
            <div style={skeletonStyles.iconBtn} />
            <div style={skeletonStyles.iconBtn} />
            <div style={skeletonStyles.userMenu}>
              <div style={skeletonStyles.avatar} />
              <div style={skeletonStyles.userInfo}>
                <div style={skeletonStyles.userNamePlaceholder} />
                <div style={skeletonStyles.userRolePlaceholder} />
              </div>
            </div>
          </div>
        </header>

        {/* Dashboard content skeleton */}
        <main style={skeletonStyles.mainContent}>
          {/* Greeting */}
          <div style={skeletonStyles.greetingPlaceholder} />
          <div style={skeletonStyles.subGreetingPlaceholder} />

          {/* KPI cards */}
          <div style={skeletonStyles.kpiGrid}>
            {[1, 2, 3, 4].map((i) => (
              <div key={i} style={skeletonStyles.kpiCard}>
                <div style={skeletonStyles.kpiLabel} />
                <div style={skeletonStyles.kpiValue} />
                <div style={skeletonStyles.kpiTrend} />
              </div>
            ))}
          </div>

          {/* Charts */}
          <div style={skeletonStyles.chartsGrid}>
            <div style={skeletonStyles.chartCard}>
              <div style={skeletonStyles.chartTitle} />
              <div style={skeletonStyles.chartPlaceholder} />
            </div>
            <div style={skeletonStyles.chartCard}>
              <div style={skeletonStyles.chartTitle} />
              <div style={skeletonStyles.chartPlaceholder} />
            </div>
          </div>

          {/* Loading message overlay */}
          <div style={skeletonStyles.loadingOverlay}>
            <div style={skeletonStyles.loadingCard}>
              <div style={styles.logoIcon}>
                <Shield size={24} color="#10b981" />
              </div>
              <div style={styles.spinner} />
              <p style={skeletonStyles.loadingMessage}>{message}</p>
            </div>
          </div>
        </main>
      </div>

      <span className="sr-only">Loading dashboard, please wait</span>
    </div>
  );
}

const shimmerGradient = 'linear-gradient(90deg, transparent 0%, rgba(255,255,255,0.05) 50%, transparent 100%)';

const styles = {
  container: {
    minHeight: '100vh',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    background: 'linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #0f172a 100%)',
    fontFamily: "'DM Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
  },
  content: {
    textAlign: 'center',
  },
  logoIcon: {
    width: 64,
    height: 64,
    borderRadius: 16,
    background: 'rgba(16, 185, 129, 0.1)',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    margin: '0 auto 24px',
    border: '1px solid rgba(16, 185, 129, 0.2)',
  },
  spinnerContainer: {
    marginBottom: 16,
    display: 'flex',
    justifyContent: 'center',
  },
  spinner: {
    width: 32,
    height: 32,
    border: '3px solid rgba(16, 185, 129, 0.2)',
    borderTopColor: '#10b981',
    borderRadius: '50%',
    animation: 'gc-spin 1s linear infinite',
  },
  message: {
    color: '#94a3b8',
    fontSize: 14,
    margin: 0,
  },
};

const skeletonStyles = {
  container: {
    minHeight: '100vh',
    display: 'flex',
    background: '#0a0b0d',
    fontFamily: "'DM Sans', -apple-system, sans-serif",
  },
  sidebar: {
    width: 260,
    background: '#111318',
    borderRight: '1px solid #2a2f3a',
    padding: 0,
  },
  sidebarHeader: {
    padding: 20,
    borderBottom: '1px solid #2a2f3a',
    display: 'flex',
    alignItems: 'center',
    gap: 12,
  },
  logoPlaceholder: {
    width: 32,
    height: 32,
    borderRadius: 8,
    background: '#1a1d24',
    backgroundImage: shimmerGradient,
    backgroundSize: '200% 100%',
    animation: 'gc-shimmer 1.5s infinite',
  },
  brandPlaceholder: {
    width: 100,
    height: 20,
    borderRadius: 4,
    background: '#1a1d24',
    backgroundImage: shimmerGradient,
    backgroundSize: '200% 100%',
    animation: 'gc-shimmer 1.5s infinite',
  },
  navSection: {
    padding: 12,
  },
  navItem: {
    display: 'flex',
    alignItems: 'center',
    gap: 12,
    padding: '10px 12px',
    marginBottom: 2,
  },
  navIcon: {
    width: 20,
    height: 20,
    borderRadius: 4,
    background: '#1a1d24',
    backgroundImage: shimmerGradient,
    backgroundSize: '200% 100%',
    animation: 'gc-shimmer 1.5s infinite',
  },
  navLabel: {
    width: '70%',
    height: 14,
    borderRadius: 4,
    background: '#1a1d24',
    backgroundImage: shimmerGradient,
    backgroundSize: '200% 100%',
    animation: 'gc-shimmer 1.5s infinite',
  },
  navDivider: {
    height: 1,
    background: '#2a2f3a',
    margin: '12px 0',
  },
  mainWrapper: {
    flex: 1,
    display: 'flex',
    flexDirection: 'column',
  },
  topBar: {
    height: 64,
    background: '#111318',
    borderBottom: '1px solid #2a2f3a',
    display: 'flex',
    alignItems: 'center',
    padding: '0 24px',
    gap: 16,
  },
  searchBar: {
    flex: 1,
    maxWidth: 480,
    height: 40,
    borderRadius: 8,
    background: '#1a1d24',
    backgroundImage: shimmerGradient,
    backgroundSize: '200% 100%',
    animation: 'gc-shimmer 1.5s infinite',
  },
  topBarActions: {
    display: 'flex',
    alignItems: 'center',
    gap: 8,
    marginLeft: 'auto',
  },
  iconBtn: {
    width: 40,
    height: 40,
    borderRadius: 8,
    background: '#1a1d24',
    backgroundImage: shimmerGradient,
    backgroundSize: '200% 100%',
    animation: 'gc-shimmer 1.5s infinite',
  },
  userMenu: {
    display: 'flex',
    alignItems: 'center',
    gap: 8,
    padding: '6px 12px',
  },
  avatar: {
    width: 32,
    height: 32,
    borderRadius: '50%',
    background: '#1a1d24',
    backgroundImage: shimmerGradient,
    backgroundSize: '200% 100%',
    animation: 'gc-shimmer 1.5s infinite',
  },
  userInfo: {
    display: 'flex',
    flexDirection: 'column',
    gap: 4,
  },
  userNamePlaceholder: {
    width: 60,
    height: 12,
    borderRadius: 3,
    background: '#1a1d24',
    backgroundImage: shimmerGradient,
    backgroundSize: '200% 100%',
    animation: 'gc-shimmer 1.5s infinite',
  },
  userRolePlaceholder: {
    width: 40,
    height: 10,
    borderRadius: 3,
    background: '#1a1d24',
    backgroundImage: shimmerGradient,
    backgroundSize: '200% 100%',
    animation: 'gc-shimmer 1.5s infinite',
  },
  mainContent: {
    flex: 1,
    padding: 24,
    background: '#0a0b0d',
    position: 'relative',
  },
  greetingPlaceholder: {
    width: 200,
    height: 32,
    borderRadius: 6,
    background: '#1a1d24',
    backgroundImage: shimmerGradient,
    backgroundSize: '200% 100%',
    animation: 'gc-shimmer 1.5s infinite',
    marginBottom: 8,
  },
  subGreetingPlaceholder: {
    width: 300,
    height: 16,
    borderRadius: 4,
    background: '#1a1d24',
    backgroundImage: shimmerGradient,
    backgroundSize: '200% 100%',
    animation: 'gc-shimmer 1.5s infinite',
    marginBottom: 24,
  },
  kpiGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(4, 1fr)',
    gap: 16,
    marginBottom: 24,
  },
  kpiCard: {
    background: '#111318',
    borderRadius: 12,
    padding: 20,
    border: '1px solid #2a2f3a',
  },
  kpiLabel: {
    width: 80,
    height: 14,
    borderRadius: 4,
    background: '#1a1d24',
    backgroundImage: shimmerGradient,
    backgroundSize: '200% 100%',
    animation: 'gc-shimmer 1.5s infinite',
    marginBottom: 12,
  },
  kpiValue: {
    width: 60,
    height: 32,
    borderRadius: 6,
    background: '#1a1d24',
    backgroundImage: shimmerGradient,
    backgroundSize: '200% 100%',
    animation: 'gc-shimmer 1.5s infinite',
    marginBottom: 8,
  },
  kpiTrend: {
    width: 100,
    height: 12,
    borderRadius: 4,
    background: '#1a1d24',
    backgroundImage: shimmerGradient,
    backgroundSize: '200% 100%',
    animation: 'gc-shimmer 1.5s infinite',
  },
  chartsGrid: {
    display: 'grid',
    gridTemplateColumns: '2fr 1fr',
    gap: 16,
  },
  chartCard: {
    background: '#111318',
    borderRadius: 12,
    padding: 20,
    border: '1px solid #2a2f3a',
  },
  chartTitle: {
    width: 120,
    height: 18,
    borderRadius: 4,
    background: '#1a1d24',
    backgroundImage: shimmerGradient,
    backgroundSize: '200% 100%',
    animation: 'gc-shimmer 1.5s infinite',
    marginBottom: 16,
  },
  chartPlaceholder: {
    height: 200,
    borderRadius: 8,
    background: '#1a1d24',
    backgroundImage: shimmerGradient,
    backgroundSize: '200% 100%',
    animation: 'gc-shimmer 1.5s infinite',
  },
  loadingOverlay: {
    position: 'absolute',
    inset: 0,
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    background: 'rgba(10, 11, 13, 0.8)',
    backdropFilter: 'blur(4px)',
  },
  loadingCard: {
    background: '#111318',
    borderRadius: 16,
    padding: 32,
    border: '1px solid #2a2f3a',
    textAlign: 'center',
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    gap: 16,
  },
  loadingMessage: {
    color: '#94a3b8',
    fontSize: 14,
    margin: 0,
  },
};

export default LoadingScreen;
