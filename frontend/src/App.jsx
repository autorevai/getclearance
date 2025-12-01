import React from 'react';
import { Routes, Route, Navigate, useNavigate, useLocation } from 'react-router-dom';
import { useAuth0 } from '@auth0/auth0-react';
import AppShell from './components/AppShell';
import Dashboard from './components/Dashboard';
import ApplicantsList from './components/ApplicantsList';
import ApplicantDetail from './components/ApplicantDetail';
import ScreeningChecks from './components/ScreeningChecks';
import CaseManagement from './components/CaseManagement';
import LoginPage from './components/LoginPage';
import LoadingScreen from './components/LoadingScreen';

export default function App() {
  const { isAuthenticated, isLoading, user, logout } = useAuth0();
  const navigate = useNavigate();
  const location = useLocation();

  // Show skeleton loading screen while checking auth state
  if (isLoading) {
    return <LoadingScreen message="Checking authentication..." variant="skeleton" />;
  }

  // Show login page if not authenticated
  if (!isAuthenticated) {
    return <LoginPage />;
  }

  // Determine current page from URL for sidebar highlighting
  const getCurrentPage = () => {
    const path = location.pathname;
    if (path.startsWith('/applicants')) return 'applicants';
    if (path.startsWith('/screening')) return 'screening';
    if (path.startsWith('/cases')) return 'cases';
    if (path.startsWith('/companies')) return 'companies';
    if (path.startsWith('/integrations')) return 'integrations';
    if (path.startsWith('/settings')) return 'settings';
    if (path.startsWith('/billing')) return 'billing';
    if (path.startsWith('/audit-log')) return 'audit-log';
    return 'dashboard';
  };

  const handleNavigate = (page) => {
    const routes = {
      dashboard: '/',
      applicants: '/applicants',
      companies: '/companies',
      screening: '/screening',
      cases: '/cases',
      integrations: '/integrations',
      settings: '/settings',
      billing: '/billing',
      'audit-log': '/audit-log',
    };
    navigate(routes[page] || '/');
  };

  const handleLogout = () => {
    logout({
      logoutParams: {
        returnTo: window.location.origin,
      },
    });
  };

  return (
    <AppShell
      currentPage={getCurrentPage()}
      onNavigate={handleNavigate}
      user={user}
      onLogout={handleLogout}
    >
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/applicants" element={<ApplicantsList />} />
        <Route path="/applicants/:id" element={<ApplicantDetail />} />
        <Route path="/companies" element={<CompaniesList />} />
        <Route path="/screening" element={<ScreeningChecks />} />
        <Route path="/cases" element={<CaseManagement />} />
        <Route path="/integrations" element={<IntegrationsPage />} />
        <Route path="/settings" element={<SettingsPage />} />
        <Route path="/billing" element={<BillingPage />} />
        <Route path="/audit-log" element={<AuditLogPage />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </AppShell>
  );
}

// Placeholder components for pages not yet built
function CompaniesList() {
  return (
    <div style={{ padding: 40, textAlign: 'center', color: 'var(--text-muted)' }}>
      <h2 style={{ marginBottom: 16, color: 'var(--text-primary)' }}>Companies (KYB)</h2>
      <p>Business entity verification coming soon.</p>
      <p style={{ marginTop: 8, fontSize: 14 }}>
        This will include UBO tracking, corporate document verification, and company risk scoring.
      </p>
    </div>
  );
}

function IntegrationsPage() {
  return (
    <div style={{ padding: 40, textAlign: 'center', color: 'var(--text-muted)' }}>
      <h2 style={{ marginBottom: 16, color: 'var(--text-primary)' }}>Integrations</h2>
      <p>Connect your data sources and third-party services.</p>
      <p style={{ marginTop: 8, fontSize: 14 }}>
        OpenSanctions, TRM Labs, Chainalysis, Sumsub webhooks, and more.
      </p>
    </div>
  );
}

function SettingsPage() {
  return (
    <div style={{ padding: 40, textAlign: 'center', color: 'var(--text-muted)' }}>
      <h2 style={{ marginBottom: 16, color: 'var(--text-primary)' }}>Settings</h2>
      <p>Configure workflows, roles, and SLAs.</p>
    </div>
  );
}

function BillingPage() {
  return (
    <div style={{ padding: 40, textAlign: 'center', color: 'var(--text-muted)' }}>
      <h2 style={{ marginBottom: 16, color: 'var(--text-primary)' }}>Billing & Usage</h2>
      <p>View usage metrics and manage your subscription.</p>
    </div>
  );
}

function AuditLogPage() {
  return (
    <div style={{ padding: 40, textAlign: 'center', color: 'var(--text-muted)' }}>
      <h2 style={{ marginBottom: 16, color: 'var(--text-primary)' }}>Audit Log</h2>
      <p>Immutable, signed audit trail of all actions.</p>
    </div>
  );
}
