import React, { useState } from 'react';
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
  const [currentPage, setCurrentPage] = useState('dashboard');
  const [selectedApplicant, setSelectedApplicant] = useState(null);

  // Show loading screen while checking auth state
  if (isLoading) {
    return <LoadingScreen message="Checking authentication..." />;
  }

  // Show login page if not authenticated
  if (!isAuthenticated) {
    return <LoginPage />;
  }

  const handleNavigate = (page) => {
    setCurrentPage(page);
    setSelectedApplicant(null);
  };

  const handleSelectApplicant = (applicant) => {
    setSelectedApplicant(applicant);
  };

  const handleBackFromDetail = () => {
    setSelectedApplicant(null);
  };

  const handleLogout = () => {
    logout({
      logoutParams: {
        returnTo: window.location.origin,
      },
    });
  };

  const renderContent = () => {
    // If we have a selected applicant, show detail view
    if (selectedApplicant) {
      return (
        <ApplicantDetail
          applicant={selectedApplicant}
          onBack={handleBackFromDetail}
        />
      );
    }

    switch (currentPage) {
      case 'dashboard':
        return <Dashboard />;
      case 'applicants':
        return <ApplicantsList onSelectApplicant={handleSelectApplicant} />;
      case 'companies':
        return <CompaniesList />;
      case 'screening':
        return <ScreeningChecks />;
      case 'cases':
        return <CaseManagement />;
      case 'integrations':
        return <IntegrationsPage />;
      case 'settings':
        return <SettingsPage />;
      case 'billing':
        return <BillingPage />;
      case 'audit-log':
        return <AuditLogPage />;
      default:
        return <ComingSoonPage pageName={currentPage} />;
    }
  };

  return (
    <AppShell
      currentPage={currentPage}
      onNavigate={handleNavigate}
      user={user}
      onLogout={handleLogout}
    >
      {renderContent()}
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

function ComingSoonPage({ pageName }) {
  return (
    <div style={{ padding: 40, textAlign: 'center', color: 'var(--text-muted)' }}>
      <h2 style={{ marginBottom: 16, color: 'var(--text-primary)' }}>
        {pageName.split('-').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ')}
      </h2>
      <p>This feature is coming soon.</p>
    </div>
  );
}
