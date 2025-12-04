import React from 'react';
import { Routes, Route, useNavigate, useLocation } from 'react-router-dom';
import { useAuth0 } from '@auth0/auth0-react';
import AppShell from './components/AppShell';
import Dashboard from './components/Dashboard';
import ApplicantsList from './components/ApplicantsList';
import ApplicantDetail from './components/ApplicantDetail';
import ScreeningChecks from './components/ScreeningChecks';
import CaseManagement from './components/CaseManagement';
import LoginPage from './components/LoginPage';
import LoadingScreen from './components/LoadingScreen';
import { ErrorBoundary } from './components/ErrorBoundary';
import { NotFoundPage } from './components/shared/NotFound';
import { useGlobalRealtimeUpdates } from './hooks/useRealtimeUpdates';
import { CompanyDetail } from './components/companies';

// Page components
import {
  CompaniesPage,
  IntegrationsPage,
  DeviceIntelligencePage,
  ReusableKYCPage,
  AnalyticsPage,
  SettingsPage,
  BillingPage,
  AuditLogPage,
  QuestionnairesPage,
  BiometricsPage,
} from './components/pages';

// KYC Share components
import { ReusableKYCPage as ApplicantKYCSharePage } from './components/kyc-share';

// SDK components (public, no auth required)
import SDKVerifyPage from './components/sdk/SDKVerifyPage';
import SDKDemoPage from './components/sdk/SDKDemoPage';

export default function App() {
  const location = useLocation();

  // SDK routes are public - render them without auth check
  if (location.pathname.startsWith('/sdk/')) {
    return (
      <Routes>
        <Route path="/sdk/verify" element={<SDKVerifyPage />} />
        <Route path="/sdk/demo" element={<SDKDemoPage />} />
      </Routes>
    );
  }

  // All other routes require authentication
  return <AuthenticatedApp />;
}

function AuthenticatedApp() {
  const { isAuthenticated, isLoading, user, logout } = useAuth0();
  const navigate = useNavigate();
  const location = useLocation();

  // Enable real-time WebSocket updates when authenticated
  useGlobalRealtimeUpdates();

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
    if (path.startsWith('/device-intel')) return 'device-intel';
    if (path.startsWith('/reusable-kyc')) return 'reusable-kyc';
    if (path.startsWith('/analytics')) return 'analytics';
    if (path.startsWith('/settings')) return 'settings';
    if (path.startsWith('/billing')) return 'billing';
    if (path.startsWith('/audit-log')) return 'audit-log';
    if (path.startsWith('/questionnaires')) return 'questionnaires';
    if (path.startsWith('/biometrics')) return 'biometrics';
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
      'device-intel': '/device-intel',
      'reusable-kyc': '/reusable-kyc',
      analytics: '/analytics',
      settings: '/settings',
      billing: '/billing',
      'audit-log': '/audit-log',
      questionnaires: '/questionnaires',
      biometrics: '/biometrics',
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
      <ErrorBoundary>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/applicants" element={<ApplicantsList />} />
          <Route path="/applicants/:id" element={<ApplicantDetail />} />
          <Route path="/companies" element={<CompaniesPage />} />
          <Route path="/companies/:id" element={<CompanyDetail />} />
          <Route path="/screening" element={<ScreeningChecks />} />
          <Route path="/cases" element={<CaseManagement />} />
          <Route path="/integrations" element={<IntegrationsPage />} />
          <Route path="/device-intel" element={<DeviceIntelligencePage />} />
          <Route path="/reusable-kyc" element={<ReusableKYCPage />} />
          <Route path="/applicants/:applicantId/share" element={<ApplicantKYCSharePage />} />
          <Route path="/analytics" element={<AnalyticsPage />} />
          <Route path="/settings" element={<SettingsPage />} />
          <Route path="/billing" element={<BillingPage />} />
          <Route path="/audit-log" element={<AuditLogPage />} />
          <Route path="/questionnaires" element={<QuestionnairesPage />} />
          <Route path="/biometrics" element={<BiometricsPage />} />
          <Route path="*" element={<NotFoundPage />} />
        </Routes>
      </ErrorBoundary>
    </AppShell>
  );
}
