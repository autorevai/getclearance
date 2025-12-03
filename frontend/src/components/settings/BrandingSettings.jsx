import React, { useState, useEffect } from 'react';
import { Palette, Check, Loader2, Image } from 'lucide-react';
import { useBrandingSettings, useUpdateBrandingSettings } from '../../hooks';

export default function BrandingSettings() {
  const { data: settings, isLoading } = useBrandingSettings();
  const updateSettings = useUpdateBrandingSettings();

  const [formData, setFormData] = useState({
    logo_url: '',
    primary_color: '#6366f1',
    accent_color: '#818cf8',
    favicon_url: '',
  });
  const [saveSuccess, setSaveSuccess] = useState(false);

  // Initialize from server data
  useEffect(() => {
    if (settings) {
      setFormData({
        logo_url: settings.logo_url || '',
        primary_color: settings.primary_color || '#6366f1',
        accent_color: settings.accent_color || '#818cf8',
        favicon_url: settings.favicon_url || '',
      });
    }
  }, [settings]);

  const handleChange = (field, value) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
    setSaveSuccess(false);
  };

  const handleSave = async () => {
    try {
      await updateSettings.mutateAsync(formData);
      setSaveSuccess(true);
      setTimeout(() => setSaveSuccess(false), 3000);
    } catch (error) {
      console.error('Failed to save branding settings:', error);
    }
  };

  if (isLoading) {
    return (
      <div className="settings-loading">
        <Loader2 className="spinner" />
        <span>Loading branding settings...</span>
      </div>
    );
  }

  return (
    <div className="branding-settings">
      <style>{`
        .branding-settings h2 {
          font-size: 18px;
          font-weight: 600;
          color: var(--text-primary, #f0f2f5);
          margin: 0 0 8px;
          display: flex;
          align-items: center;
          gap: 8px;
        }

        .branding-settings h2 svg {
          width: 20px;
          height: 20px;
          color: var(--accent-primary, #6366f1);
        }

        .section-description {
          font-size: 14px;
          color: var(--text-secondary, #8b919e);
          margin-bottom: 24px;
        }

        .branding-section {
          margin-bottom: 32px;
        }

        .section-title {
          font-size: 14px;
          font-weight: 600;
          color: var(--text-primary, #f0f2f5);
          margin-bottom: 16px;
        }

        .logo-upload-area {
          display: flex;
          gap: 24px;
          padding: 20px;
          background: var(--bg-tertiary, #1a1d24);
          border: 1px solid var(--border-color, #2a2f3a);
          border-radius: 12px;
        }

        .logo-preview {
          width: 120px;
          height: 120px;
          background: var(--bg-secondary, #111318);
          border: 2px dashed var(--border-color, #2a2f3a);
          border-radius: 12px;
          display: flex;
          align-items: center;
          justify-content: center;
          overflow: hidden;
          flex-shrink: 0;
        }

        .logo-preview.has-image {
          border-style: solid;
        }

        .logo-preview img {
          max-width: 100%;
          max-height: 100%;
          object-fit: contain;
        }

        .logo-preview svg {
          width: 32px;
          height: 32px;
          color: var(--text-muted, #5c6370);
        }

        .logo-upload-info {
          flex: 1;
        }

        .logo-upload-title {
          font-size: 14px;
          font-weight: 500;
          color: var(--text-primary, #f0f2f5);
          margin-bottom: 8px;
        }

        .logo-upload-hint {
          font-size: 13px;
          color: var(--text-secondary, #8b919e);
          margin-bottom: 16px;
        }

        .url-input {
          width: 100%;
          height: 40px;
          padding: 0 14px;
          background: var(--bg-secondary, #111318);
          border: 1px solid var(--border-color, #2a2f3a);
          border-radius: 8px;
          color: var(--text-primary, #f0f2f5);
          font-size: 14px;
          font-family: inherit;
        }

        .url-input:focus {
          outline: none;
          border-color: var(--accent-primary, #6366f1);
        }

        .url-input::placeholder {
          color: var(--text-muted, #5c6370);
        }

        .color-settings {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
          gap: 16px;
        }

        .color-setting {
          padding: 16px;
          background: var(--bg-tertiary, #1a1d24);
          border: 1px solid var(--border-color, #2a2f3a);
          border-radius: 12px;
        }

        .color-label {
          font-size: 14px;
          font-weight: 500;
          color: var(--text-primary, #f0f2f5);
          margin-bottom: 8px;
        }

        .color-description {
          font-size: 13px;
          color: var(--text-secondary, #8b919e);
          margin-bottom: 16px;
        }

        .color-input-wrapper {
          display: flex;
          align-items: center;
          gap: 12px;
        }

        .color-picker {
          width: 48px;
          height: 48px;
          border: none;
          border-radius: 8px;
          cursor: pointer;
          padding: 0;
          background: transparent;
        }

        .color-picker::-webkit-color-swatch-wrapper {
          padding: 0;
        }

        .color-picker::-webkit-color-swatch {
          border: 2px solid var(--border-color, #2a2f3a);
          border-radius: 8px;
        }

        .color-hex-input {
          flex: 1;
          height: 40px;
          padding: 0 14px;
          background: var(--bg-secondary, #111318);
          border: 1px solid var(--border-color, #2a2f3a);
          border-radius: 8px;
          color: var(--text-primary, #f0f2f5);
          font-size: 14px;
          font-family: monospace;
          text-transform: uppercase;
        }

        .color-hex-input:focus {
          outline: none;
          border-color: var(--accent-primary, #6366f1);
        }

        .preview-section {
          margin-top: 24px;
          padding: 20px;
          background: var(--bg-tertiary, #1a1d24);
          border: 1px solid var(--border-color, #2a2f3a);
          border-radius: 12px;
        }

        .preview-title {
          font-size: 14px;
          font-weight: 600;
          color: var(--text-primary, #f0f2f5);
          margin-bottom: 16px;
        }

        .preview-buttons {
          display: flex;
          gap: 12px;
          flex-wrap: wrap;
        }

        .preview-btn {
          padding: 10px 20px;
          border-radius: 8px;
          font-size: 14px;
          font-weight: 500;
          border: none;
          cursor: pointer;
          font-family: inherit;
        }

        .preview-btn.primary {
          color: white;
        }

        .preview-btn.secondary {
          background: var(--bg-secondary, #111318);
          color: var(--text-primary, #f0f2f5);
          border: 1px solid var(--border-color, #2a2f3a);
        }

        .save-button {
          display: inline-flex;
          align-items: center;
          gap: 8px;
          padding: 10px 20px;
          background: var(--accent-primary, #6366f1);
          color: white;
          border: none;
          border-radius: 8px;
          font-size: 14px;
          font-weight: 500;
          cursor: pointer;
          transition: opacity 0.2s;
          font-family: inherit;
          margin-top: 24px;
        }

        .save-button:hover:not(:disabled) {
          opacity: 0.9;
        }

        .save-button:disabled {
          opacity: 0.6;
          cursor: not-allowed;
        }

        .save-button.success {
          background: var(--success, #10b981);
        }

        .save-button svg {
          width: 16px;
          height: 16px;
        }

        .spinner {
          animation: spin 1s linear infinite;
        }

        @keyframes spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }

        .settings-loading {
          display: flex;
          align-items: center;
          justify-content: center;
          gap: 12px;
          padding: 40px;
          color: var(--text-secondary, #8b919e);
        }

        .settings-loading .spinner {
          width: 20px;
          height: 20px;
        }
      `}</style>

      <h2>
        <Palette />
        Branding Settings
      </h2>
      <p className="section-description">
        Customize the appearance of your compliance platform.
      </p>

      {/* Logo */}
      <div className="branding-section">
        <div className="section-title">Company Logo</div>
        <div className="logo-upload-area">
          <div className={`logo-preview ${formData.logo_url ? 'has-image' : ''}`}>
            {formData.logo_url ? (
              <img src={formData.logo_url} alt="Company logo" />
            ) : (
              <Image />
            )}
          </div>
          <div className="logo-upload-info">
            <div className="logo-upload-title">Logo URL</div>
            <div className="logo-upload-hint">
              Enter a URL to your company logo. Recommended size: 200x50px. PNG or SVG format.
            </div>
            <input
              type="url"
              className="url-input"
              value={formData.logo_url}
              onChange={(e) => handleChange('logo_url', e.target.value)}
              placeholder="https://example.com/logo.png"
            />
          </div>
        </div>
      </div>

      {/* Favicon */}
      <div className="branding-section">
        <div className="section-title">Favicon</div>
        <div className="logo-upload-area">
          <div className={`logo-preview ${formData.favicon_url ? 'has-image' : ''}`} style={{ width: 64, height: 64 }}>
            {formData.favicon_url ? (
              <img src={formData.favicon_url} alt="Favicon" />
            ) : (
              <Image style={{ width: 24, height: 24 }} />
            )}
          </div>
          <div className="logo-upload-info">
            <div className="logo-upload-title">Favicon URL</div>
            <div className="logo-upload-hint">
              Enter a URL to your favicon. Recommended size: 32x32px. ICO, PNG, or SVG format.
            </div>
            <input
              type="url"
              className="url-input"
              value={formData.favicon_url}
              onChange={(e) => handleChange('favicon_url', e.target.value)}
              placeholder="https://example.com/favicon.ico"
            />
          </div>
        </div>
      </div>

      {/* Colors */}
      <div className="branding-section">
        <div className="section-title">Brand Colors</div>
        <div className="color-settings">
          <div className="color-setting">
            <div className="color-label">Primary Color</div>
            <div className="color-description">
              Main brand color used for buttons, links, and highlights
            </div>
            <div className="color-input-wrapper">
              <input
                type="color"
                className="color-picker"
                value={formData.primary_color}
                onChange={(e) => handleChange('primary_color', e.target.value)}
              />
              <input
                type="text"
                className="color-hex-input"
                value={formData.primary_color}
                onChange={(e) => handleChange('primary_color', e.target.value)}
                placeholder="#6366f1"
                maxLength={7}
              />
            </div>
          </div>

          <div className="color-setting">
            <div className="color-label">Accent Color</div>
            <div className="color-description">
              Secondary color for hover states and gradients
            </div>
            <div className="color-input-wrapper">
              <input
                type="color"
                className="color-picker"
                value={formData.accent_color}
                onChange={(e) => handleChange('accent_color', e.target.value)}
              />
              <input
                type="text"
                className="color-hex-input"
                value={formData.accent_color}
                onChange={(e) => handleChange('accent_color', e.target.value)}
                placeholder="#818cf8"
                maxLength={7}
              />
            </div>
          </div>
        </div>
      </div>

      {/* Preview */}
      <div className="preview-section">
        <div className="preview-title">Preview</div>
        <div className="preview-buttons">
          <button
            className="preview-btn primary"
            style={{ background: formData.primary_color }}
          >
            Primary Button
          </button>
          <button
            className="preview-btn primary"
            style={{
              background: `linear-gradient(135deg, ${formData.primary_color}, ${formData.accent_color})`,
            }}
          >
            Gradient Button
          </button>
          <button className="preview-btn secondary">
            Secondary Button
          </button>
          <span
            style={{
              color: formData.primary_color,
              fontWeight: 500,
              padding: '10px 0',
            }}
          >
            Link Text Color
          </span>
        </div>
      </div>

      <button
        className={`save-button ${saveSuccess ? 'success' : ''}`}
        onClick={handleSave}
        disabled={updateSettings.isPending}
      >
        {updateSettings.isPending ? (
          <>
            <Loader2 className="spinner" />
            Saving...
          </>
        ) : saveSuccess ? (
          <>
            <Check />
            Saved!
          </>
        ) : (
          'Save Branding'
        )}
      </button>
    </div>
  );
}
