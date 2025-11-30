/**
 * Design System - Get Clearance Compliance Platform
 * 
 * Color Palette (Dark Theme - Default):
 * --bg-primary: #0a0b0d (main background)
 * --bg-secondary: #111318 (cards, panels)
 * --bg-tertiary: #1a1d24 (inputs, nested elements)
 * --bg-hover: #22262f (hover states)
 * --border-color: #2a2f3a
 * --text-primary: #f0f2f5
 * --text-secondary: #8b919e
 * --text-muted: #5c6370
 * --accent-primary: #6366f1 (indigo)
 * --accent-secondary: #818cf8
 * --success: #10b981 (emerald)
 * --warning: #f59e0b (amber)
 * --danger: #ef4444 (red)
 * --info: #3b82f6 (blue)
 * 
 * Typography:
 * - Font Family: 'DM Sans' for UI, 'JetBrains Mono' for code/IDs
 * - Font Sizes: 11px (micro), 12px (small), 13px (body-small), 14px (body), 15px (title), 18px (h3), 28px (h1)
 * 
 * Spacing:
 * - Base unit: 4px
 * - Common: 8, 12, 16, 20, 24, 32, 40
 * 
 * Border Radius:
 * - Small: 4px (badges, chips)
 * - Medium: 8px (buttons, inputs)
 * - Large: 12px (cards)
 * - XL: 16px (modals)
 * - Round: 50% (avatars)
 */

import React from 'react';

// ========================================
// BUTTON COMPONENT
// ========================================
export function Button({ 
  children, 
  variant = 'secondary', 
  size = 'medium',
  icon: Icon,
  iconPosition = 'left',
  fullWidth = false,
  disabled = false,
  onClick,
  ...props 
}) {
  const baseStyles = {
    display: 'inline-flex',
    alignItems: 'center',
    justifyContent: 'center',
    gap: '8px',
    borderRadius: '8px',
    fontWeight: 500,
    cursor: disabled ? 'not-allowed' : 'pointer',
    transition: 'all 0.15s ease',
    border: 'none',
    fontFamily: 'inherit',
    width: fullWidth ? '100%' : 'auto',
    opacity: disabled ? 0.5 : 1,
  };

  const sizeStyles = {
    small: { padding: '6px 12px', fontSize: '13px' },
    medium: { padding: '10px 16px', fontSize: '14px' },
    large: { padding: '12px 20px', fontSize: '15px' },
  };

  const variantStyles = {
    primary: {
      background: 'var(--accent-primary)',
      color: 'white',
    },
    secondary: {
      background: 'var(--bg-secondary)',
      border: '1px solid var(--border-color)',
      color: 'var(--text-primary)',
    },
    ghost: {
      background: 'transparent',
      color: 'var(--text-secondary)',
    },
    danger: {
      background: 'var(--danger)',
      color: 'white',
    },
    success: {
      background: 'var(--success)',
      color: 'white',
    },
    ai: {
      background: 'linear-gradient(135deg, var(--accent-primary), #a855f7)',
      color: 'white',
    },
  };

  return (
    <button
      style={{
        ...baseStyles,
        ...sizeStyles[size],
        ...variantStyles[variant],
      }}
      disabled={disabled}
      onClick={onClick}
      {...props}
    >
      {Icon && iconPosition === 'left' && <Icon size={size === 'small' ? 14 : 16} />}
      {children}
      {Icon && iconPosition === 'right' && <Icon size={size === 'small' ? 14 : 16} />}
    </button>
  );
}

// ========================================
// BADGE COMPONENT
// ========================================
export function Badge({ 
  children, 
  variant = 'default',
  size = 'medium',
  icon: Icon,
}) {
  const baseStyles = {
    display: 'inline-flex',
    alignItems: 'center',
    gap: '4px',
    borderRadius: '4px',
    fontWeight: 600,
    textTransform: 'uppercase',
    letterSpacing: '0.02em',
  };

  const sizeStyles = {
    small: { padding: '2px 6px', fontSize: '10px' },
    medium: { padding: '3px 8px', fontSize: '11px' },
    large: { padding: '4px 10px', fontSize: '12px' },
  };

  const variantStyles = {
    default: {
      background: 'var(--bg-tertiary)',
      color: 'var(--text-muted)',
    },
    success: {
      background: 'rgba(16, 185, 129, 0.15)',
      color: 'var(--success)',
    },
    warning: {
      background: 'rgba(245, 158, 11, 0.15)',
      color: 'var(--warning)',
    },
    danger: {
      background: 'rgba(239, 68, 68, 0.15)',
      color: 'var(--danger)',
    },
    info: {
      background: 'rgba(59, 130, 246, 0.15)',
      color: 'var(--info)',
    },
    primary: {
      background: 'rgba(99, 102, 241, 0.15)',
      color: 'var(--accent-primary)',
    },
  };

  return (
    <span style={{ ...baseStyles, ...sizeStyles[size], ...variantStyles[variant] }}>
      {Icon && <Icon size={size === 'small' ? 10 : 12} />}
      {children}
    </span>
  );
}

// ========================================
// STATUS BADGE (Pill style)
// ========================================
export function StatusBadge({ 
  children, 
  variant = 'default',
  icon: Icon,
}) {
  const baseStyles = {
    display: 'inline-flex',
    alignItems: 'center',
    gap: '6px',
    padding: '4px 10px',
    borderRadius: '20px',
    fontSize: '12px',
    fontWeight: 500,
  };

  const variantStyles = {
    default: {
      background: 'var(--bg-tertiary)',
      color: 'var(--text-muted)',
    },
    success: {
      background: 'rgba(16, 185, 129, 0.15)',
      color: 'var(--success)',
    },
    warning: {
      background: 'rgba(245, 158, 11, 0.15)',
      color: 'var(--warning)',
    },
    danger: {
      background: 'rgba(239, 68, 68, 0.15)',
      color: 'var(--danger)',
    },
    info: {
      background: 'rgba(59, 130, 246, 0.15)',
      color: 'var(--info)',
    },
  };

  return (
    <span style={{ ...baseStyles, ...variantStyles[variant] }}>
      {Icon && <Icon size={12} />}
      {children}
    </span>
  );
}

// ========================================
// CARD COMPONENT
// ========================================
export function Card({ 
  children, 
  title,
  subtitle,
  icon: Icon,
  action,
  padding = true,
  ...props 
}) {
  return (
    <div
      style={{
        background: 'var(--bg-secondary)',
        border: '1px solid var(--border-color)',
        borderRadius: '12px',
        overflow: 'hidden',
      }}
      {...props}
    >
      {title && (
        <div
          style={{
            padding: '16px 20px',
            borderBottom: '1px solid var(--border-color)',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            {Icon && <Icon size={16} />}
            <span style={{ fontSize: '15px', fontWeight: 600 }}>{title}</span>
            {subtitle && (
              <span style={{ fontSize: '13px', color: 'var(--text-muted)' }}>
                {subtitle}
              </span>
            )}
          </div>
          {action}
        </div>
      )}
      <div style={{ padding: padding ? '20px' : 0 }}>{children}</div>
    </div>
  );
}

// ========================================
// INPUT COMPONENT
// ========================================
export function Input({
  label,
  placeholder,
  type = 'text',
  icon: Icon,
  value,
  onChange,
  error,
  ...props
}) {
  return (
    <div style={{ marginBottom: '16px' }}>
      {label && (
        <label
          style={{
            display: 'block',
            fontSize: '13px',
            fontWeight: 500,
            marginBottom: '8px',
            color: 'var(--text-primary)',
          }}
        >
          {label}
        </label>
      )}
      <div style={{ position: 'relative' }}>
        {Icon && (
          <Icon
            size={16}
            style={{
              position: 'absolute',
              left: '12px',
              top: '50%',
              transform: 'translateY(-50%)',
              color: 'var(--text-muted)',
            }}
          />
        )}
        <input
          type={type}
          placeholder={placeholder}
          value={value}
          onChange={onChange}
          style={{
            width: '100%',
            height: '44px',
            background: 'var(--bg-tertiary)',
            border: `1px solid ${error ? 'var(--danger)' : 'var(--border-color)'}`,
            borderRadius: '8px',
            padding: Icon ? '0 14px 0 40px' : '0 14px',
            fontSize: '14px',
            color: 'var(--text-primary)',
            outline: 'none',
            transition: 'border-color 0.15s',
          }}
          {...props}
        />
      </div>
      {error && (
        <span style={{ fontSize: '12px', color: 'var(--danger)', marginTop: '4px' }}>
          {error}
        </span>
      )}
    </div>
  );
}

// ========================================
// AVATAR COMPONENT
// ========================================
export function Avatar({ 
  name, 
  src, 
  size = 32,
  variant = 'default',
}) {
  const initials = name
    ?.split(' ')
    .map((n) => n[0])
    .join('')
    .toUpperCase()
    .slice(0, 2);

  const gradients = [
    'linear-gradient(135deg, #6366f1, #a855f7)',
    'linear-gradient(135deg, #f59e0b, #ef4444)',
    'linear-gradient(135deg, #10b981, #3b82f6)',
    'linear-gradient(135deg, #ec4899, #8b5cf6)',
  ];

  // Simple hash to pick consistent gradient
  const gradientIndex = name ? name.charCodeAt(0) % gradients.length : 0;

  return (
    <div
      style={{
        width: size,
        height: size,
        borderRadius: '50%',
        background: src ? `url(${src}) center/cover` : gradients[gradientIndex],
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        fontSize: size * 0.4,
        fontWeight: 600,
        color: 'white',
        flexShrink: 0,
      }}
    >
      {!src && initials}
    </div>
  );
}

// ========================================
// RISK SCORE COMPONENT
// ========================================
export function RiskScore({ score, size = 'medium' }) {
  const getBucket = (s) => {
    if (s < 30) return { label: 'Low', color: 'var(--success)' };
    if (s < 70) return { label: 'Medium', color: 'var(--warning)' };
    return { label: 'High', color: 'var(--danger)' };
  };

  const bucket = getBucket(score);

  const sizeStyles = {
    small: { fontSize: '14px', barWidth: '40px', barHeight: '4px' },
    medium: { fontSize: '18px', barWidth: '60px', barHeight: '6px' },
    large: { fontSize: '36px', barWidth: '100px', barHeight: '8px' },
  };

  const styles = sizeStyles[size];

  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
      <span style={{ fontSize: styles.fontSize, fontWeight: 600, color: bucket.color }}>
        {score}
      </span>
      <div
        style={{
          width: styles.barWidth,
          height: styles.barHeight,
          background: 'var(--bg-tertiary)',
          borderRadius: styles.barHeight / 2,
          overflow: 'hidden',
        }}
      >
        <div
          style={{
            width: `${score}%`,
            height: '100%',
            background: bucket.color,
            borderRadius: styles.barHeight / 2,
          }}
        />
      </div>
    </div>
  );
}

// ========================================
// EMPTY STATE COMPONENT
// ========================================
export function EmptyState({ 
  icon: Icon, 
  title, 
  description, 
  action,
}) {
  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '60px 40px',
        textAlign: 'center',
      }}
    >
      {Icon && (
        <div
          style={{
            width: '64px',
            height: '64px',
            borderRadius: '16px',
            background: 'var(--bg-tertiary)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            marginBottom: '16px',
            color: 'var(--text-muted)',
          }}
        >
          <Icon size={28} />
        </div>
      )}
      <h3 style={{ fontSize: '16px', fontWeight: 600, marginBottom: '8px' }}>
        {title}
      </h3>
      <p style={{ fontSize: '14px', color: 'var(--text-muted)', marginBottom: '20px' }}>
        {description}
      </p>
      {action}
    </div>
  );
}

// ========================================
// LOADING SPINNER
// ========================================
export function Spinner({ size = 24 }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      style={{ animation: 'spin 1s linear infinite' }}
    >
      <style>
        {`@keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }`}
      </style>
      <circle
        cx="12"
        cy="12"
        r="10"
        stroke="var(--border-color)"
        strokeWidth="3"
        fill="none"
      />
      <path
        d="M12 2a10 10 0 0 1 10 10"
        stroke="var(--accent-primary)"
        strokeWidth="3"
        strokeLinecap="round"
        fill="none"
      />
    </svg>
  );
}

// ========================================
// TOOLTIP
// ========================================
export function Tooltip({ children, content }) {
  const [show, setShow] = React.useState(false);

  return (
    <div
      style={{ position: 'relative', display: 'inline-flex' }}
      onMouseEnter={() => setShow(true)}
      onMouseLeave={() => setShow(false)}
    >
      {children}
      {show && (
        <div
          style={{
            position: 'absolute',
            bottom: '100%',
            left: '50%',
            transform: 'translateX(-50%)',
            marginBottom: '8px',
            padding: '6px 10px',
            background: 'var(--bg-tertiary)',
            border: '1px solid var(--border-color)',
            borderRadius: '6px',
            fontSize: '12px',
            color: 'var(--text-primary)',
            whiteSpace: 'nowrap',
            zIndex: 1000,
          }}
        >
          {content}
        </div>
      )}
    </div>
  );
}

export default {
  Button,
  Badge,
  StatusBadge,
  Card,
  Input,
  Avatar,
  RiskScore,
  EmptyState,
  Spinner,
  Tooltip,
};
