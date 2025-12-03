/**
 * Biometrics Demo - Simplified with inline styles
 */

import React, { useState } from 'react';
import {
  Upload,
  Camera,
  CheckCircle,
  XCircle,
  AlertCircle,
  Eye,
  Users,
  Scan,
} from 'lucide-react';
import { useCompareFaces, useDetectLiveness, useDetectFaces } from '../../hooks/useBiometrics';

const styles = {
  tabs: { display: 'flex', gap: '8px', marginBottom: '16px', borderBottom: '1px solid #e5e7eb', paddingBottom: '8px' },
  tab: { display: 'flex', alignItems: 'center', gap: '6px', padding: '8px 16px', borderRadius: '6px', border: 'none', cursor: 'pointer', fontSize: '14px', fontWeight: '500', backgroundColor: 'transparent', color: '#6b7280' },
  tabActive: { backgroundColor: '#eff6ff', color: '#2563eb' },
  panel: { display: 'flex', flexDirection: 'column', gap: '16px' },
  grid: { display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '16px' },
  card: { padding: '16px', border: '1px solid #e5e7eb', borderRadius: '8px', backgroundColor: 'white' },
  label: { fontSize: '14px', fontWeight: '500', marginBottom: '8px', display: 'block' },
  fileInput: { display: 'none' },
  fileLabel: { display: 'flex', alignItems: 'center', gap: '8px', padding: '10px 16px', borderRadius: '6px', border: '1px dashed #d1d5db', cursor: 'pointer', fontSize: '14px', color: '#6b7280', backgroundColor: '#f9fafb' },
  preview: { marginTop: '12px', borderRadius: '8px', maxHeight: '150px', objectFit: 'contain', width: '100%' },
  button: { display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px', padding: '10px 20px', borderRadius: '6px', border: 'none', cursor: 'pointer', fontSize: '14px', fontWeight: '500', backgroundColor: '#3b82f6', color: 'white' },
  buttonDisabled: { opacity: 0.5, cursor: 'not-allowed' },
  error: { padding: '12px', backgroundColor: '#fef2f2', borderRadius: '6px', color: '#dc2626', display: 'flex', alignItems: 'center', gap: '8px', fontSize: '14px' },
  resultCard: { padding: '16px', borderRadius: '8px', border: '1px solid #e5e7eb' },
  resultHeader: { display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' },
  resultIcon: { width: '40px', height: '40px', borderRadius: '8px', display: 'flex', alignItems: 'center', justifyContent: 'center' },
  badge: { display: 'inline-block', padding: '2px 8px', borderRadius: '12px', fontSize: '12px', fontWeight: '500' },
  progressBar: { height: '8px', backgroundColor: '#e5e7eb', borderRadius: '4px', overflow: 'hidden', marginBottom: '4px' },
  progressFill: { height: '100%', borderRadius: '4px', transition: 'width 0.3s' },
  metricsGrid: { display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px', marginTop: '12px' },
  metricLabel: { fontSize: '13px', color: '#6b7280', marginBottom: '4px' },
  metricValue: { fontWeight: '500', fontSize: '14px' },
  processingTime: { fontSize: '12px', color: '#9ca3af', marginTop: '12px' },
};

function fileToBase64(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.readAsDataURL(file);
    reader.onload = () => resolve(reader.result);
    reader.onerror = (error) => reject(error);
  });
}

function ProgressBar({ value, color }) {
  return (
    <div style={styles.progressBar}>
      <div style={{ ...styles.progressFill, width: `${value}%`, backgroundColor: color }} />
    </div>
  );
}

function ResultDisplay({ result, type }) {
  if (!result) return null;

  if (type === 'compare') {
    const bgColor = result.match ? '#f0fdf4' : '#fef2f2';
    const iconBg = result.match ? '#16a34a' : '#dc2626';
    return (
      <div style={{ ...styles.resultCard, backgroundColor: bgColor }}>
        <div style={styles.resultHeader}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <div style={{ ...styles.resultIcon, backgroundColor: iconBg }}>
              {result.match ? <CheckCircle size={20} color="white" /> : <XCircle size={20} color="white" />}
            </div>
            <div>
              <div style={{ fontWeight: '600' }}>{result.match ? 'Faces Match' : 'Faces Do Not Match'}</div>
              <div style={{ fontSize: '13px', color: '#6b7280' }}>{result.result}</div>
            </div>
          </div>
          {result.is_mock && <span style={{ ...styles.badge, backgroundColor: '#fef3c7', color: '#92400e' }}>Mock Result</span>}
        </div>

        <div style={styles.metricsGrid}>
          <div>
            <div style={styles.metricLabel}>Similarity</div>
            <ProgressBar value={result.similarity} color={result.similarity > 80 ? '#22c55e' : '#ef4444'} />
            <div style={styles.metricValue}>{result.similarity.toFixed(1)}%</div>
          </div>
          <div>
            <div style={styles.metricLabel}>Confidence</div>
            <ProgressBar value={result.confidence} color="#3b82f6" />
            <div style={styles.metricValue}>{result.confidence.toFixed(1)}%</div>
          </div>
        </div>

        <div style={styles.processingTime}>Processing time: {result.processing_time_ms}ms</div>
      </div>
    );
  }

  if (type === 'liveness') {
    const bgColor = result.is_live ? '#f0fdf4' : '#fef2f2';
    const iconBg = result.is_live ? '#16a34a' : '#dc2626';
    return (
      <div style={{ ...styles.resultCard, backgroundColor: bgColor }}>
        <div style={styles.resultHeader}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <div style={{ ...styles.resultIcon, backgroundColor: iconBg }}>
              {result.is_live ? <CheckCircle size={20} color="white" /> : <XCircle size={20} color="white" />}
            </div>
            <div>
              <div style={{ fontWeight: '600' }}>{result.is_live ? 'Live Person Detected' : 'Liveness Check Failed'}</div>
              <div style={{ fontSize: '13px', color: '#6b7280' }}>{result.confidence_level}</div>
            </div>
          </div>
          {result.is_mock && <span style={{ ...styles.badge, backgroundColor: '#fef3c7', color: '#92400e' }}>Mock Result</span>}
        </div>

        <div style={styles.metricsGrid}>
          <div>
            <div style={styles.metricLabel}>Confidence</div>
            <ProgressBar value={result.confidence} color={result.is_live ? '#22c55e' : '#ef4444'} />
            <div style={styles.metricValue}>{result.confidence.toFixed(1)}%</div>
          </div>
          <div>
            <div style={styles.metricLabel}>Anti-Spoofing Score</div>
            <ProgressBar value={result.anti_spoofing_score} color="#3b82f6" />
            <div style={styles.metricValue}>{result.anti_spoofing_score.toFixed(1)}%</div>
          </div>
        </div>

        {result.challenges_passed?.length > 0 && (
          <div style={{ marginTop: '12px', display: 'flex', flexWrap: 'wrap', gap: '6px', alignItems: 'center' }}>
            <span style={{ fontSize: '13px', color: '#6b7280' }}>Challenges passed:</span>
            {result.challenges_passed.map((c, i) => (
              <span key={i} style={{ ...styles.badge, backgroundColor: '#eff6ff', color: '#2563eb' }}>{c}</span>
            ))}
          </div>
        )}

        <div style={styles.processingTime}>Processing time: {result.processing_time_ms}ms</div>
      </div>
    );
  }

  if (type === 'detect') {
    return (
      <div style={styles.resultCard}>
        <div style={styles.resultHeader}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <div style={{ ...styles.resultIcon, backgroundColor: '#3b82f6' }}>
              <Users size={20} color="white" />
            </div>
            <div style={{ fontWeight: '600' }}>{result.faces_detected} Face(s) Detected</div>
          </div>
          {result.is_mock && <span style={{ ...styles.badge, backgroundColor: '#fef3c7', color: '#92400e' }}>Mock Result</span>}
        </div>

        {result.quality && (
          <div>
            <div style={{ fontSize: '14px', fontWeight: '500', marginBottom: '8px' }}>Quality Metrics:</div>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '12px' }}>
              <div>
                <div style={{ fontSize: '12px', color: '#6b7280', marginBottom: '4px' }}>Brightness</div>
                <ProgressBar value={result.quality.brightness} color="#3b82f6" />
              </div>
              <div>
                <div style={{ fontSize: '12px', color: '#6b7280', marginBottom: '4px' }}>Sharpness</div>
                <ProgressBar value={result.quality.sharpness} color="#3b82f6" />
              </div>
              <div>
                <div style={{ fontSize: '12px', color: '#6b7280', marginBottom: '4px' }}>Contrast</div>
                <ProgressBar value={result.quality.contrast} color="#3b82f6" />
              </div>
            </div>
            <div style={{ display: 'flex', gap: '8px', marginTop: '12px', flexWrap: 'wrap' }}>
              <span style={{ ...styles.badge, backgroundColor: result.quality.eyes_open ? '#dcfce7' : '#f3f4f6', color: result.quality.eyes_open ? '#16a34a' : '#6b7280' }}>
                Eyes {result.quality.eyes_open ? 'Open' : 'Closed'}
              </span>
              <span style={{ ...styles.badge, backgroundColor: result.quality.sunglasses ? '#fef2f2' : '#dcfce7', color: result.quality.sunglasses ? '#dc2626' : '#16a34a' }}>
                {result.quality.sunglasses ? 'Sunglasses' : 'No Sunglasses'}
              </span>
              <span style={{ ...styles.badge, backgroundColor: result.quality.is_acceptable ? '#dcfce7' : '#fef2f2', color: result.quality.is_acceptable ? '#16a34a' : '#dc2626' }}>
                {result.quality.is_acceptable ? 'Acceptable' : 'Poor Quality'}
              </span>
            </div>
          </div>
        )}

        {result.age_range && (
          <div style={{ fontSize: '14px', marginTop: '12px' }}>
            Estimated age: {result.age_range.min} - {result.age_range.max} years
          </div>
        )}

        {result.gender && (
          <div style={{ fontSize: '14px' }}>Gender: {result.gender}</div>
        )}
      </div>
    );
  }

  return null;
}

function FileUpload({ id, value, onChange, icon: Icon, placeholder }) {
  const handleChange = (e) => {
    const file = e.target.files?.[0];
    onChange(file || null);
  };

  return (
    <div>
      <input
        type="file"
        id={id}
        accept="image/*"
        style={styles.fileInput}
        onChange={handleChange}
      />
      <label htmlFor={id} style={styles.fileLabel}>
        <Icon size={16} />
        {value ? value.name : placeholder}
      </label>
    </div>
  );
}

export default function BiometricsDemo() {
  const [activeTab, setActiveTab] = useState('compare');
  const [sourceFile, setSourceFile] = useState(null);
  const [targetFile, setTargetFile] = useState(null);
  const [singleFile, setSingleFile] = useState(null);
  const [sourcePreview, setSourcePreview] = useState(null);
  const [targetPreview, setTargetPreview] = useState(null);
  const [singlePreview, setSinglePreview] = useState(null);

  const compareMutation = useCompareFaces();
  const livenessMutation = useDetectLiveness();
  const detectMutation = useDetectFaces();

  const handleSourceChange = (file) => {
    setSourceFile(file);
    if (file) {
      setSourcePreview(URL.createObjectURL(file));
    } else {
      setSourcePreview(null);
    }
  };

  const handleTargetChange = (file) => {
    setTargetFile(file);
    if (file) {
      setTargetPreview(URL.createObjectURL(file));
    } else {
      setTargetPreview(null);
    }
  };

  const handleSingleChange = (file) => {
    setSingleFile(file);
    if (file) {
      setSinglePreview(URL.createObjectURL(file));
    } else {
      setSinglePreview(null);
    }
  };

  const handleCompare = async () => {
    if (!sourceFile || !targetFile) return;
    const sourceB64 = await fileToBase64(sourceFile);
    const targetB64 = await fileToBase64(targetFile);
    compareMutation.mutate({ sourceImage: sourceB64, targetImage: targetB64 });
  };

  const handleLiveness = async () => {
    if (!singleFile) return;
    const imageB64 = await fileToBase64(singleFile);
    livenessMutation.mutate({ image: imageB64 });
  };

  const handleDetect = async () => {
    if (!singleFile) return;
    const imageB64 = await fileToBase64(singleFile);
    detectMutation.mutate({ image: imageB64 });
  };

  const tabs = [
    { id: 'compare', label: 'Face Compare', icon: Users },
    { id: 'liveness', label: 'Liveness Check', icon: Eye },
    { id: 'detect', label: 'Face Detect', icon: Scan },
  ];

  return (
    <div>
      {/* Tabs */}
      <div style={styles.tabs}>
        {tabs.map((tab) => (
          <button
            key={tab.id}
            style={{ ...styles.tab, ...(activeTab === tab.id ? styles.tabActive : {}) }}
            onClick={() => setActiveTab(tab.id)}
          >
            <tab.icon size={16} />
            {tab.label}
          </button>
        ))}
      </div>

      {/* Face Compare Panel */}
      {activeTab === 'compare' && (
        <div style={styles.panel}>
          <div style={styles.grid}>
            <div style={styles.card}>
              <span style={styles.label}>Source Image (ID Photo)</span>
              <FileUpload
                id="source-file"
                value={sourceFile}
                onChange={handleSourceChange}
                icon={Upload}
                placeholder="Upload ID photo"
              />
              {sourcePreview && <img src={sourcePreview} alt="Source" style={styles.preview} />}
            </div>
            <div style={styles.card}>
              <span style={styles.label}>Target Image (Selfie)</span>
              <FileUpload
                id="target-file"
                value={targetFile}
                onChange={handleTargetChange}
                icon={Camera}
                placeholder="Upload selfie"
              />
              {targetPreview && <img src={targetPreview} alt="Target" style={styles.preview} />}
            </div>
          </div>

          <button
            style={{ ...styles.button, ...(!sourceFile || !targetFile || compareMutation.isPending ? styles.buttonDisabled : {}) }}
            onClick={handleCompare}
            disabled={!sourceFile || !targetFile || compareMutation.isPending}
          >
            <Users size={16} />
            {compareMutation.isPending ? 'Comparing...' : 'Compare Faces'}
          </button>

          {compareMutation.error && (
            <div style={styles.error}>
              <AlertCircle size={16} />
              {compareMutation.error.message}
            </div>
          )}

          <ResultDisplay result={compareMutation.data} type="compare" />
        </div>
      )}

      {/* Liveness Check Panel */}
      {activeTab === 'liveness' && (
        <div style={styles.panel}>
          <div style={styles.card}>
            <span style={styles.label}>Face Image</span>
            <FileUpload
              id="liveness-file"
              value={singleFile}
              onChange={handleSingleChange}
              icon={Camera}
              placeholder="Upload face image"
            />
            {singlePreview && <img src={singlePreview} alt="Face" style={styles.preview} />}
          </div>

          <button
            style={{ ...styles.button, ...(!singleFile || livenessMutation.isPending ? styles.buttonDisabled : {}) }}
            onClick={handleLiveness}
            disabled={!singleFile || livenessMutation.isPending}
          >
            <Eye size={16} />
            {livenessMutation.isPending ? 'Checking...' : 'Check Liveness'}
          </button>

          {livenessMutation.error && (
            <div style={styles.error}>
              <AlertCircle size={16} />
              {livenessMutation.error.message}
            </div>
          )}

          <ResultDisplay result={livenessMutation.data} type="liveness" />
        </div>
      )}

      {/* Face Detect Panel */}
      {activeTab === 'detect' && (
        <div style={styles.panel}>
          <div style={styles.card}>
            <span style={styles.label}>Image to Analyze</span>
            <FileUpload
              id="detect-file"
              value={singleFile}
              onChange={handleSingleChange}
              icon={Upload}
              placeholder="Upload image"
            />
            {singlePreview && <img src={singlePreview} alt="Analyze" style={styles.preview} />}
          </div>

          <button
            style={{ ...styles.button, ...(!singleFile || detectMutation.isPending ? styles.buttonDisabled : {}) }}
            onClick={handleDetect}
            disabled={!singleFile || detectMutation.isPending}
          >
            <Scan size={16} />
            {detectMutation.isPending ? 'Detecting...' : 'Detect Faces'}
          </button>

          {detectMutation.error && (
            <div style={styles.error}>
              <AlertCircle size={16} />
              {detectMutation.error.message}
            </div>
          )}

          <ResultDisplay result={detectMutation.data} type="detect" />
        </div>
      )}
    </div>
  );
}
