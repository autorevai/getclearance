/**
 * Biometrics Page - Simplified
 */

import React from 'react';
import { Scan, CheckCircle, AlertCircle, Camera, Eye, Activity } from 'lucide-react';
import { useBiometricsStatus } from '../../hooks/useBiometrics';
import BiometricsDemo from './BiometricsDemo';

const styles = {
  container: { padding: '24px', maxWidth: '1200px', margin: '0 auto' },
  header: { display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '24px' },
  title: { display: 'flex', alignItems: 'center', gap: '8px', fontSize: '24px', fontWeight: '600', margin: 0 },
  subtitle: { color: '#6b7280', fontSize: '14px', marginTop: '4px' },
  badge: { display: 'inline-flex', alignItems: 'center', gap: '6px', padding: '6px 12px', borderRadius: '16px', fontSize: '14px', fontWeight: '500' },
  statusCard: { padding: '20px', backgroundColor: 'white', borderRadius: '8px', border: '1px solid #e5e7eb', marginBottom: '24px' },
  grid: { display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '16px', marginBottom: '24px' },
  card: { padding: '20px', backgroundColor: 'white', borderRadius: '8px', border: '1px solid #e5e7eb' },
  cardIcon: { width: '48px', height: '48px', borderRadius: '8px', display: 'flex', alignItems: 'center', justifyContent: 'center', marginBottom: '12px' },
  warning: { padding: '16px', backgroundColor: '#fef3c7', borderRadius: '8px', color: '#92400e', display: 'flex', alignItems: 'flex-start', gap: '12px' },
  section: { padding: '20px', backgroundColor: 'white', borderRadius: '8px', border: '1px solid #e5e7eb' },
  sectionHeader: { display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '16px', fontWeight: '500' },
  loader: { padding: '32px', textAlign: 'center', color: '#6b7280' },
  error: { padding: '16px', backgroundColor: '#fef2f2', borderRadius: '8px', color: '#dc2626' },
};

export default function BiometricsPage() {
  const { data: status, isLoading, error } = useBiometricsStatus();

  if (isLoading) return <div style={styles.container}><div style={styles.loader}>Loading biometrics status...</div></div>;
  if (error) return <div style={styles.container}><div style={styles.error}><AlertCircle size={16} /> {error.message}</div></div>;

  return (
    <div style={styles.container}>
      <div style={styles.header}>
        <div>
          <h1 style={styles.title}><Scan size={28} /> Biometrics</h1>
          <p style={styles.subtitle}>Face verification and liveness detection for identity verification</p>
        </div>
        <span style={{
          ...styles.badge,
          backgroundColor: status?.is_configured ? '#dcfce7' : '#fef3c7',
          color: status?.is_configured ? '#16a34a' : '#92400e'
        }}>
          {status?.is_configured ? <CheckCircle size={14} /> : <AlertCircle size={14} />}
          {status?.is_configured ? 'AWS Rekognition Connected' : 'Mock Mode'}
        </span>
      </div>

      {/* Status */}
      <div style={styles.statusCard}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
          <strong>Service Status</strong>
          <span style={styles.badge}>{status?.provider || 'Unknown'}</span>
        </div>
        <div style={{ display: 'flex', gap: '24px' }}>
          <div>
            <div style={{ color: '#6b7280', fontSize: '13px', marginBottom: '8px' }}>Capabilities:</div>
            {status?.capabilities?.map((cap, i) => (
              <div key={i} style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '14px', marginBottom: '4px' }}>
                <CheckCircle size={12} color="#22c55e" /> {cap}
              </div>
            ))}
          </div>
          {status?.mock_mode && (
            <div style={styles.warning}>
              <AlertCircle size={16} />
              <div>
                <strong>Mock Mode Active</strong>
                <div style={{ fontSize: '13px', marginTop: '4px' }}>
                  Configure AWS Rekognition credentials to enable real face matching and liveness detection.
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Capability Cards */}
      <div style={styles.grid}>
        <div style={styles.card}>
          <div style={{ ...styles.cardIcon, backgroundColor: '#dbeafe' }}><Camera size={24} color="#2563eb" /></div>
          <h3 style={{ margin: '0 0 8px', fontSize: '16px' }}>Face Comparison</h3>
          <p style={{ margin: 0, color: '#6b7280', fontSize: '14px' }}>
            Compare ID document photo with selfie to verify identity. Returns similarity score and match confidence.
          </p>
        </div>
        <div style={styles.card}>
          <div style={{ ...styles.cardIcon, backgroundColor: '#dcfce7' }}><Eye size={24} color="#16a34a" /></div>
          <h3 style={{ margin: '0 0 8px', fontSize: '16px' }}>Liveness Detection</h3>
          <p style={{ margin: 0, color: '#6b7280', fontSize: '14px' }}>
            Detect if image contains a live person vs photo/screen. Anti-spoofing protection.
          </p>
        </div>
        <div style={styles.card}>
          <div style={{ ...styles.cardIcon, backgroundColor: '#f3e8ff' }}><Activity size={24} color="#7c3aed" /></div>
          <h3 style={{ margin: '0 0 8px', fontSize: '16px' }}>Quality Assessment</h3>
          <p style={{ margin: 0, color: '#6b7280', fontSize: '14px' }}>
            Analyze image quality including brightness, sharpness, pose, and other factors.
          </p>
        </div>
      </div>

      {/* Demo */}
      <div style={styles.section}>
        <div style={styles.sectionHeader}><Scan size={18} /> Test Biometrics</div>
        <BiometricsDemo />
      </div>
    </div>
  );
}
