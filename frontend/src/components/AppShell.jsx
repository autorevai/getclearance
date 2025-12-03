import React, { useState, useEffect, useRef, useCallback } from 'react';
import {
  LayoutDashboard,
  Users,
  Building2,
  Shield,
  FolderKanban,
  Plug,
  Fingerprint,
  Network,
  BarChart3,
  Settings,
  CreditCard,
  ScrollText,
  ChevronDown,
  ChevronLeft,
  ChevronRight,
  Search,
  Bell,
  Sparkles,
  Moon,
  Sun,
  LogOut
} from 'lucide-react';
import SearchModal from './SearchModal';
import { useNavigationCounts, formatBadgeCount } from '../hooks/useNavigationCounts';

const navItems = [
  { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard, priority: 'P0' },
  { id: 'applicants', label: 'Applicants', icon: Users, priority: 'P0', badgeKey: 'pending_applicants' },
  { id: 'companies', label: 'Companies', icon: Building2, priority: 'P0' },
  { id: 'screening', label: 'Screening', icon: Shield, priority: 'P0', badgeKey: 'unresolved_hits' },
  { id: 'cases', label: 'Cases', icon: FolderKanban, priority: 'P0', badgeKey: 'open_cases' },
  { id: 'integrations', label: 'Integrations', icon: Plug, priority: 'P0' },
  { divider: true },
  { id: 'device-intel', label: 'Device Intelligence', icon: Fingerprint, priority: 'P1', beta: true },
  { id: 'reusable-kyc', label: 'Reusable KYC', icon: Network, priority: 'P1', beta: true },
  { id: 'analytics', label: 'Analytics', icon: BarChart3, priority: 'P1' },
  { divider: true },
  { id: 'settings', label: 'Settings', icon: Settings, priority: 'P0' },
  { id: 'billing', label: 'Billing & Usage', icon: CreditCard, priority: 'P0' },
  { id: 'audit-log', label: 'Audit Log', icon: ScrollText, priority: 'P0' },
];

export default function AppShell({ children, currentPage, onNavigate, user, onLogout }) {
  const [collapsed, setCollapsed] = useState(false);
  const [darkMode, setDarkMode] = useState(true);
  const [aiPanelOpen, setAiPanelOpen] = useState(false);
  const [userMenuOpen, setUserMenuOpen] = useState(false);
  const [searchOpen, setSearchOpen] = useState(false);
  const userMenuRef = useRef(null);
  const userMenuButtonRef = useRef(null);

  // Fetch real-time navigation badge counts
  const { data: navCounts } = useNavigationCounts();

  // Get user display info
  const userName = user?.name || user?.email || 'User';
  const userInitials = userName
    .split(' ')
    .map(n => n[0])
    .join('')
    .toUpperCase()
    .slice(0, 2);
  const userPicture = user?.picture;

  // Get role from Auth0 user metadata or claims
  const userRole = user?.['https://getclearance.dev/roles']?.[0]
    || user?.role
    || (user?.email?.includes('@getclearance') ? 'Admin' : 'User');

  // Close dropdown when clicking outside
  useEffect(() => {
    function handleClickOutside(event) {
      if (
        userMenuRef.current &&
        !userMenuRef.current.contains(event.target) &&
        userMenuButtonRef.current &&
        !userMenuButtonRef.current.contains(event.target)
      ) {
        setUserMenuOpen(false);
      }
    }

    if (userMenuOpen) {
      document.addEventListener('mousedown', handleClickOutside);
      document.addEventListener('touchstart', handleClickOutside);
    }

    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
      document.removeEventListener('touchstart', handleClickOutside);
    };
  }, [userMenuOpen]);

  // Close dropdown on Escape key and handle Cmd+K for search
  useEffect(() => {
    function handleKeyDown(event) {
      if (event.key === 'Escape') {
        setUserMenuOpen(false);
        setAiPanelOpen(false);
        setSearchOpen(false);
      }
      // Cmd+K or Ctrl+K to open search
      if ((event.metaKey || event.ctrlKey) && event.key === 'k') {
        event.preventDefault();
        setSearchOpen(true);
      }
    }

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, []);

  // Handle keyboard navigation in dropdown
  const handleDropdownKeyDown = useCallback((event) => {
    if (!userMenuOpen) return;

    const items = userMenuRef.current?.querySelectorAll('[role="menuitem"]');
    if (!items?.length) return;

    const currentIndex = Array.from(items).findIndex(item => item === document.activeElement);

    switch (event.key) {
      case 'ArrowDown':
        event.preventDefault();
        const nextIndex = currentIndex < items.length - 1 ? currentIndex + 1 : 0;
        items[nextIndex].focus();
        break;
      case 'ArrowUp':
        event.preventDefault();
        const prevIndex = currentIndex > 0 ? currentIndex - 1 : items.length - 1;
        items[prevIndex].focus();
        break;
      case 'Home':
        event.preventDefault();
        items[0].focus();
        break;
      case 'End':
        event.preventDefault();
        items[items.length - 1].focus();
        break;
      case 'Tab':
        setUserMenuOpen(false);
        break;
      default:
        break;
    }
  }, [userMenuOpen]);

  // Focus first item when dropdown opens
  useEffect(() => {
    if (userMenuOpen && userMenuRef.current) {
      const firstItem = userMenuRef.current.querySelector('[role="menuitem"]');
      if (firstItem) {
        setTimeout(() => firstItem.focus(), 0);
      }
    }
  }, [userMenuOpen]);

  return (
    <div className={`app-shell ${darkMode ? 'dark' : 'light'}`}>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=DM+Sans:ital,opsz,wght@0,9..40,100..1000;1,9..40,100..1000&family=JetBrains+Mono:wght@400;500&display=swap');
        
        * {
          margin: 0;
          padding: 0;
          box-sizing: border-box;
        }
        
        .app-shell {
          --bg-primary: #0a0b0d;
          --bg-secondary: #111318;
          --bg-tertiary: #1a1d24;
          --bg-hover: #22262f;
          --border-color: #2a2f3a;
          --text-primary: #f0f2f5;
          --text-secondary: #8b919e;
          --text-muted: #5c6370;
          --accent-primary: #6366f1;
          --accent-secondary: #818cf8;
          --accent-glow: rgba(99, 102, 241, 0.15);
          --success: #10b981;
          --warning: #f59e0b;
          --danger: #ef4444;
          --info: #3b82f6;
          
          font-family: 'DM Sans', -apple-system, sans-serif;
          background: var(--bg-primary);
          color: var(--text-primary);
          min-height: 100vh;
          display: flex;
        }
        
        .app-shell.light {
          --bg-primary: #fafbfc;
          --bg-secondary: #ffffff;
          --bg-tertiary: #f3f4f6;
          --bg-hover: #e5e7eb;
          --border-color: #e5e7eb;
          --text-primary: #111827;
          --text-secondary: #6b7280;
          --text-muted: #9ca3af;
        }
        
        /* Sidebar */
        .sidebar {
          width: ${collapsed ? '72px' : '260px'};
          background: var(--bg-secondary);
          border-right: 1px solid var(--border-color);
          display: flex;
          flex-direction: column;
          transition: width 0.2s ease;
          position: fixed;
          left: 0;
          top: 0;
          bottom: 0;
          z-index: 100;
        }
        
        .sidebar-header {
          padding: 20px;
          border-bottom: 1px solid var(--border-color);
          display: flex;
          align-items: center;
          gap: 12px;
        }

        .collapse-btn {
          position: absolute;
          right: -12px;
          top: 72px;
          width: 24px;
          height: 24px;
          border-radius: 50%;
          background: var(--bg-secondary);
          border: 1px solid var(--border-color);
          color: var(--text-secondary);
          cursor: pointer;
          display: flex;
          align-items: center;
          justify-content: center;
          z-index: 110;
          transition: all 0.15s;
        }

        .collapse-btn:hover {
          background: var(--bg-hover);
          color: var(--text-primary);
          border-color: var(--accent-primary);
        }
        
        .logo {
          width: 32px;
          height: 32px;
          background: linear-gradient(135deg, var(--accent-primary), var(--accent-secondary));
          border-radius: 8px;
          display: flex;
          align-items: center;
          justify-content: center;
          font-weight: 700;
          font-size: 14px;
          color: white;
          flex-shrink: 0;
        }
        
        .brand-name {
          font-weight: 600;
          font-size: 18px;
          letter-spacing: -0.02em;
          opacity: ${collapsed ? 0 : 1};
          transition: opacity 0.2s;
        }
        
        .nav-section {
          flex: 1;
          overflow-y: auto;
          padding: 12px;
        }
        
        .nav-item {
          display: flex;
          align-items: center;
          gap: 12px;
          padding: 10px 12px;
          border-radius: 8px;
          cursor: pointer;
          color: var(--text-secondary);
          transition: all 0.15s ease;
          margin-bottom: 2px;
          position: relative;
        }
        
        .nav-item:hover {
          background: var(--bg-hover);
          color: var(--text-primary);
        }
        
        .nav-item.active {
          background: var(--accent-glow);
          color: var(--accent-primary);
        }
        
        .nav-item.active::before {
          content: '';
          position: absolute;
          left: 0;
          top: 50%;
          transform: translateY(-50%);
          width: 3px;
          height: 20px;
          background: var(--accent-primary);
          border-radius: 0 4px 4px 0;
        }
        
        .nav-icon {
          width: 20px;
          height: 20px;
          flex-shrink: 0;
        }
        
        .nav-label {
          font-size: 14px;
          font-weight: 500;
          white-space: nowrap;
          opacity: ${collapsed ? 0 : 1};
          transition: opacity 0.2s;
        }
        
        .nav-badge {
          margin-left: auto;
          background: var(--accent-primary);
          color: white;
          font-size: 11px;
          font-weight: 600;
          padding: 2px 6px;
          border-radius: 10px;
          opacity: ${collapsed ? 0 : 1};
        }
        
        .nav-beta {
          margin-left: auto;
          background: var(--bg-tertiary);
          color: var(--text-muted);
          font-size: 10px;
          font-weight: 600;
          padding: 2px 6px;
          border-radius: 4px;
          text-transform: uppercase;
          letter-spacing: 0.05em;
          opacity: ${collapsed ? 0 : 1};
        }
        
        .nav-divider {
          height: 1px;
          background: var(--border-color);
          margin: 12px 0;
        }
        
        /* Main content */
        .main-wrapper {
          flex: 1;
          margin-left: ${collapsed ? '72px' : '260px'};
          transition: margin-left 0.2s ease;
          display: flex;
          flex-direction: column;
        }
        
        .top-bar {
          height: 64px;
          background: var(--bg-secondary);
          border-bottom: 1px solid var(--border-color);
          display: flex;
          align-items: center;
          padding: 0 24px;
          gap: 16px;
          position: sticky;
          top: 0;
          z-index: 50;
        }
        
        .search-bar {
          flex: 1;
          max-width: 480px;
          position: relative;
        }
        
        .search-input {
          width: 100%;
          height: 40px;
          background: var(--bg-tertiary);
          border: 1px solid var(--border-color);
          border-radius: 8px;
          padding: 0 16px 0 44px;
          font-size: 14px;
          color: var(--text-primary);
          outline: none;
          transition: all 0.2s;
        }
        
        .search-input::placeholder {
          color: var(--text-muted);
        }
        
        .search-input:focus {
          border-color: var(--accent-primary);
          box-shadow: 0 0 0 3px var(--accent-glow);
        }
        
        .search-icon {
          position: absolute;
          left: 14px;
          top: 50%;
          transform: translateY(-50%);
          color: var(--text-muted);
          width: 18px;
          height: 18px;
        }
        
        .search-shortcut {
          position: absolute;
          right: 12px;
          top: 50%;
          transform: translateY(-50%);
          background: var(--bg-hover);
          color: var(--text-muted);
          font-size: 11px;
          font-family: 'JetBrains Mono', monospace;
          padding: 3px 6px;
          border-radius: 4px;
        }
        
        .top-bar-actions {
          display: flex;
          align-items: center;
          gap: 8px;
        }
        
        .icon-btn {
          width: 40px;
          height: 40px;
          display: flex;
          align-items: center;
          justify-content: center;
          border-radius: 8px;
          background: transparent;
          border: none;
          color: var(--text-secondary);
          cursor: pointer;
          transition: all 0.15s;
        }
        
        .icon-btn:hover {
          background: var(--bg-hover);
          color: var(--text-primary);
        }
        
        .icon-btn.ai-btn {
          background: linear-gradient(135deg, var(--accent-primary), var(--accent-secondary));
          color: white;
        }
        
        .icon-btn.ai-btn:hover {
          opacity: 0.9;
        }
        
        .notification-btn {
          position: relative;
        }
        
        .notification-dot {
          position: absolute;
          top: 8px;
          right: 8px;
          width: 8px;
          height: 8px;
          background: var(--danger);
          border-radius: 50%;
          border: 2px solid var(--bg-secondary);
        }
        
        .user-menu {
          display: flex;
          align-items: center;
          gap: 8px;
          padding: 6px 12px;
          border-radius: 8px;
          cursor: pointer;
          transition: background 0.15s;
          position: relative;
        }

        .user-menu:hover {
          background: var(--bg-hover);
        }

        .user-avatar {
          width: 32px;
          height: 32px;
          background: linear-gradient(135deg, #f59e0b, #ef4444);
          border-radius: 50%;
          display: flex;
          align-items: center;
          justify-content: center;
          font-weight: 600;
          font-size: 13px;
          color: white;
          overflow: hidden;
        }

        .user-avatar img {
          width: 100%;
          height: 100%;
          object-fit: cover;
        }

        .user-info {
          display: flex;
          flex-direction: column;
        }

        .user-name {
          font-size: 13px;
          font-weight: 500;
        }

        .user-role {
          font-size: 11px;
          color: var(--text-muted);
        }

        .user-dropdown {
          position: absolute;
          top: 100%;
          right: 0;
          margin-top: 8px;
          background: var(--bg-secondary);
          border: 1px solid var(--border-color);
          border-radius: 8px;
          box-shadow: 0 10px 40px rgba(0, 0, 0, 0.3);
          min-width: 200px;
          z-index: 200;
          overflow: hidden;
        }

        .user-dropdown-header {
          padding: 12px 16px;
          border-bottom: 1px solid var(--border-color);
        }

        .user-dropdown-email {
          font-size: 12px;
          color: var(--text-muted);
          word-break: break-all;
        }

        .user-dropdown-item {
          display: flex;
          align-items: center;
          gap: 10px;
          padding: 10px 16px;
          cursor: pointer;
          transition: background 0.15s;
          color: var(--text-primary);
          font-size: 14px;
        }

        .user-dropdown-item:hover {
          background: var(--bg-hover);
        }

        .user-dropdown-item.danger {
          color: var(--danger);
        }

        .user-dropdown-item.danger:hover {
          background: rgba(239, 68, 68, 0.1);
        }
        
        .main-content {
          flex: 1;
          padding: 24px;
          background: var(--bg-primary);
        }
        
        /* AI Panel */
        .ai-panel {
          position: fixed;
          right: ${aiPanelOpen ? '0' : '-400px'};
          top: 0;
          bottom: 0;
          width: 400px;
          background: var(--bg-secondary);
          border-left: 1px solid var(--border-color);
          z-index: 200;
          transition: right 0.3s ease;
          display: flex;
          flex-direction: column;
        }
        
        .ai-panel-header {
          padding: 20px;
          border-bottom: 1px solid var(--border-color);
          display: flex;
          align-items: center;
          justify-content: space-between;
        }
        
        .ai-panel-title {
          display: flex;
          align-items: center;
          gap: 8px;
          font-weight: 600;
        }
        
        .ai-panel-content {
          flex: 1;
          padding: 20px;
          overflow-y: auto;
        }
        
        .ai-suggestion {
          background: var(--bg-tertiary);
          border-radius: 12px;
          padding: 16px;
          margin-bottom: 12px;
        }
        
        .ai-suggestion-label {
          font-size: 11px;
          color: var(--accent-primary);
          font-weight: 600;
          text-transform: uppercase;
          letter-spacing: 0.05em;
          margin-bottom: 8px;
        }
        
        .ai-suggestion-text {
          font-size: 14px;
          line-height: 1.5;
          color: var(--text-primary);
        }
        
        .ai-panel-input {
          padding: 20px;
          border-top: 1px solid var(--border-color);
        }
        
        .ai-input {
          width: 100%;
          height: 80px;
          background: var(--bg-tertiary);
          border: 1px solid var(--border-color);
          border-radius: 8px;
          padding: 12px;
          font-size: 14px;
          color: var(--text-primary);
          resize: none;
          outline: none;
          font-family: inherit;
        }
        
        .ai-input:focus {
          border-color: var(--accent-primary);
        }
        
        .ai-overlay {
          position: fixed;
          inset: 0;
          background: rgba(0, 0, 0, 0.5);
          z-index: 150;
          opacity: ${aiPanelOpen ? 1 : 0};
          pointer-events: ${aiPanelOpen ? 'auto' : 'none'};
          transition: opacity 0.3s;
        }
      `}</style>
      
      <nav className="sidebar">
        <button className="collapse-btn" onClick={() => setCollapsed(!collapsed)}>
          {collapsed ? <ChevronRight size={14} /> : <ChevronLeft size={14} />}
        </button>
        <div className="sidebar-header">
          <div className="logo">GC</div>
          {!collapsed && <span className="brand-name">Get Clearance</span>}
        </div>
        
        <div className="nav-section">
          {navItems.map((item, idx) => {
            if (item.divider) {
              return <div key={idx} className="nav-divider" />;
            }

            // Get dynamic badge count if badgeKey is specified
            const badgeCount = item.badgeKey && navCounts
              ? formatBadgeCount(navCounts[item.badgeKey])
              : null;

            return (
              <div
                key={item.id}
                className={`nav-item ${currentPage === item.id ? 'active' : ''}`}
                onClick={() => onNavigate?.(item.id)}
                title={collapsed ? item.label : ''}
              >
                <item.icon className="nav-icon" />
                {!collapsed && <span className="nav-label">{item.label}</span>}
                {!collapsed && badgeCount !== null && badgeCount > 0 && (
                  <span className="nav-badge">{badgeCount}</span>
                )}
                {!collapsed && item.beta && <span className="nav-beta">Beta</span>}
              </div>
            );
          })}
        </div>
      </nav>
      
      <div className="main-wrapper">
        <header className="top-bar">
          <div className="search-bar" onClick={() => setSearchOpen(true)} style={{ cursor: 'pointer' }}>
            <Search className="search-icon" />
            <input
              type="text"
              className="search-input"
              placeholder="Search applicants, companies, cases..."
              readOnly
              style={{ cursor: 'pointer' }}
            />
            <span className="search-shortcut">⌘K</span>
          </div>
          
          <div className="top-bar-actions">
            <button 
              className="icon-btn ai-btn"
              onClick={() => setAiPanelOpen(true)}
              title="AI Assistant"
            >
              <Sparkles size={18} />
            </button>
            
            <button className="icon-btn notification-btn">
              <Bell size={20} />
              <span className="notification-dot" />
            </button>
            
            <button 
              className="icon-btn"
              onClick={() => setDarkMode(!darkMode)}
            >
              {darkMode ? <Sun size={20} /> : <Moon size={20} />}
            </button>
            
            <div className="user-menu-container" style={{ position: 'relative' }}>
              <button
                ref={userMenuButtonRef}
                className="user-menu"
                onClick={() => setUserMenuOpen(!userMenuOpen)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' || e.key === ' ' || e.key === 'ArrowDown') {
                    e.preventDefault();
                    setUserMenuOpen(true);
                  }
                }}
                aria-haspopup="menu"
                aria-expanded={userMenuOpen}
                aria-label={`User menu for ${userName}`}
                style={{ background: 'none', border: 'none', width: '100%' }}
              >
                <div className="user-avatar" aria-hidden="true">
                  {userPicture ? (
                    <img src={userPicture} alt="" />
                  ) : (
                    userInitials
                  )}
                </div>
                <div className="user-info">
                  <span className="user-name">{userName.split(' ')[0]}</span>
                  <span className="user-role">{userRole}</span>
                </div>
                <ChevronDown
                  size={16}
                  aria-hidden="true"
                  style={{ transform: userMenuOpen ? 'rotate(180deg)' : 'none', transition: 'transform 0.2s' }}
                />
              </button>

              {userMenuOpen && (
                <div
                  ref={userMenuRef}
                  className="user-dropdown"
                  role="menu"
                  aria-label="User menu"
                  onKeyDown={handleDropdownKeyDown}
                >
                  <div className="user-dropdown-header" aria-hidden="true">
                    <div className="user-name">{userName}</div>
                    <div className="user-dropdown-email">{user?.email}</div>
                  </div>
                  <button
                    className="user-dropdown-item"
                    role="menuitem"
                    tabIndex={0}
                    onClick={() => { onNavigate?.('settings'); setUserMenuOpen(false); }}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter' || e.key === ' ') {
                        e.preventDefault();
                        onNavigate?.('settings');
                        setUserMenuOpen(false);
                      }
                    }}
                    style={{ background: 'none', border: 'none', width: '100%', textAlign: 'left', fontFamily: 'inherit' }}
                  >
                    <Settings size={16} aria-hidden="true" />
                    <span>Settings</span>
                  </button>
                  <button
                    className="user-dropdown-item danger"
                    role="menuitem"
                    tabIndex={0}
                    onClick={() => onLogout?.()}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter' || e.key === ' ') {
                        e.preventDefault();
                        onLogout?.();
                      }
                    }}
                    style={{ background: 'none', border: 'none', width: '100%', textAlign: 'left', fontFamily: 'inherit' }}
                  >
                    <LogOut size={16} aria-hidden="true" />
                    <span>Sign out</span>
                  </button>
                </div>
              )}
            </div>
          </div>
        </header>
        
        <main className="main-content">
          {children}
        </main>
      </div>
      
      <div className="ai-overlay" onClick={() => setAiPanelOpen(false)} />
      
      <aside className="ai-panel">
        <div className="ai-panel-header">
          <div className="ai-panel-title">
            <Sparkles size={18} />
            AI Assistant
          </div>
          <button className="icon-btn" onClick={() => setAiPanelOpen(false)}>×</button>
        </div>

        <div className="ai-panel-content">
          <div className="ai-suggestion">
            <div className="ai-suggestion-label">Quick Actions</div>
            <div className="ai-suggestion-text">
              You have 3 applicants pending review with high-confidence matches.
              Would you like me to prepare a summary for batch review?
            </div>
          </div>

          <div className="ai-suggestion">
            <div className="ai-suggestion-label">Risk Alert</div>
            <div className="ai-suggestion-text">
              Detected potential sanctions match for "Sofia Reyes" against OFAC SDN list
              (version 2025-11-27). Confidence: 85%. Review recommended.
            </div>
          </div>
        </div>

        <div className="ai-panel-input">
          <textarea
            className="ai-input"
            placeholder="Ask me anything about your compliance data..."
          />
        </div>
      </aside>

      <SearchModal isOpen={searchOpen} onClose={() => setSearchOpen(false)} />
    </div>
  );
}
