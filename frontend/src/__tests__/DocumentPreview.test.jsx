/**
 * Tests for DocumentPreview Component
 *
 * Tests cover:
 * - Modal open/close behavior
 * - Document info display
 * - Tab navigation
 * - Verification checks display
 * - Actions (download, re-analyze)
 */

import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import DocumentPreview from '../components/DocumentPreview';

// Mock document data
const mockDocument = {
  id: 'doc-123',
  document_type: 'passport',
  file_name: 'passport.jpg',
  file_size: 2048000,
  content_type: 'image/jpeg',
  status: 'verified',
  uploaded_at: '2025-01-01T10:00:00Z',
  processed_at: '2025-01-01T10:05:00Z',
  storage_url: 'https://example.com/passport.jpg',
  ocr_confidence: 0.95,
  mrz_valid: true,
  extracted_data: {
    full_name: 'John Doe',
    date_of_birth: '1990-01-15',
    document_number: 'AB1234567',
  },
  ai_analysis: {
    summary: 'Document appears authentic with high confidence.',
    confidence: 0.92,
  },
  fraud_signals: [],
  ocr_text: 'PASSPORT\nJOHN DOE',
};

// Mock hooks
const mockDownloadMutateAsync = jest.fn();
const mockAnalyzeMutateAsync = jest.fn();

jest.mock('../hooks/useDocuments', () => ({
  useDocument: () => ({
    data: null,
    isLoading: false,
  }),
  useDocumentPolling: () => ({
    data: null,
  }),
  useDownloadDocument: () => ({
    mutateAsync: mockDownloadMutateAsync,
    isPending: false,
  }),
  useAnalyzeDocument: () => ({
    mutateAsync: mockAnalyzeMutateAsync,
    isPending: false,
  }),
}));

jest.mock('../contexts/ToastContext', () => ({
  useToast: () => ({
    success: jest.fn(),
    error: jest.fn(),
  }),
}));

// Create test wrapper
const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  });

  return ({ children }) => (
    <QueryClientProvider client={queryClient}>
      {children}
    </QueryClientProvider>
  );
};

describe('DocumentPreview', () => {
  const defaultProps = {
    document: mockDocument,
    isOpen: true,
    onClose: jest.fn(),
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('Modal Behavior', () => {
    it('renders when isOpen is true', () => {
      render(<DocumentPreview {...defaultProps} />, { wrapper: createWrapper() });

      expect(screen.getByText('Passport')).toBeInTheDocument();
    });

    it('does not render when isOpen is false', () => {
      render(<DocumentPreview {...defaultProps} isOpen={false} />, { wrapper: createWrapper() });

      expect(screen.queryByText('Passport')).not.toBeInTheDocument();
    });

    it('calls onClose when close button is clicked', async () => {
      const onClose = jest.fn();
      render(<DocumentPreview {...defaultProps} onClose={onClose} />, { wrapper: createWrapper() });

      const closeButton = screen.getByTitle('Close');
      await userEvent.click(closeButton);

      expect(onClose).toHaveBeenCalled();
    });

    it('calls onClose when Escape key is pressed', () => {
      const onClose = jest.fn();
      render(<DocumentPreview {...defaultProps} onClose={onClose} />, { wrapper: createWrapper() });

      fireEvent.keyDown(window, { key: 'Escape' });

      expect(onClose).toHaveBeenCalled();
    });
  });

  describe('Header Display', () => {
    it('shows document type label', () => {
      render(<DocumentPreview {...defaultProps} />, { wrapper: createWrapper() });

      expect(screen.getByText('Passport')).toBeInTheDocument();
    });

    it('shows file name', () => {
      render(<DocumentPreview {...defaultProps} />, { wrapper: createWrapper() });

      expect(screen.getByText(/passport.jpg/i)).toBeInTheDocument();
    });

    it('shows document status', () => {
      render(<DocumentPreview {...defaultProps} />, { wrapper: createWrapper() });

      expect(screen.getByText('Verified')).toBeInTheDocument();
    });
  });

  describe('Tab Navigation', () => {
    it('shows preview tab by default', () => {
      render(<DocumentPreview {...defaultProps} />, { wrapper: createWrapper() });

      const previewTab = screen.getByText('Preview');
      expect(previewTab).toHaveClass('active');
    });

    it('switches to extracted data tab', async () => {
      render(<DocumentPreview {...defaultProps} />, { wrapper: createWrapper() });

      const extractedTab = screen.getByText('Extracted Data');
      await userEvent.click(extractedTab);

      expect(extractedTab).toHaveClass('active');
    });

    it('switches to AI analysis tab', async () => {
      render(<DocumentPreview {...defaultProps} />, { wrapper: createWrapper() });

      const analysisTab = screen.getByText('AI Analysis');
      await userEvent.click(analysisTab);

      expect(analysisTab).toHaveClass('active');
    });
  });

  describe('Verification Checks', () => {
    it('shows MRZ validation result', () => {
      render(<DocumentPreview {...defaultProps} />, { wrapper: createWrapper() });

      expect(screen.getByText('MRZ Validation')).toBeInTheDocument();
    });

    it('shows OCR quality check', () => {
      render(<DocumentPreview {...defaultProps} />, { wrapper: createWrapper() });

      expect(screen.getByText('OCR Quality')).toBeInTheDocument();
    });

    it('shows fraud detection check', () => {
      render(<DocumentPreview {...defaultProps} />, { wrapper: createWrapper() });

      expect(screen.getByText('Fraud Detection')).toBeInTheDocument();
    });
  });

  describe('Actions', () => {
    it('triggers download when download button is clicked', async () => {
      render(<DocumentPreview {...defaultProps} />, { wrapper: createWrapper() });

      const downloadButton = screen.getByTitle('Download document');
      await userEvent.click(downloadButton);

      expect(mockDownloadMutateAsync).toHaveBeenCalled();
    });

    it('triggers re-analyze when button is clicked', async () => {
      render(<DocumentPreview {...defaultProps} />, { wrapper: createWrapper() });

      const analyzeButton = screen.getByTitle('Re-run AI analysis');
      await userEvent.click(analyzeButton);

      expect(mockAnalyzeMutateAsync).toHaveBeenCalled();
    });

    it('disables re-analyze button during processing', () => {
      const processingDoc = { ...mockDocument, status: 'processing' };
      render(
        <DocumentPreview {...defaultProps} document={processingDoc} />,
        { wrapper: createWrapper() }
      );

      const analyzeButton = screen.getByTitle('Re-run AI analysis');
      expect(analyzeButton).toBeDisabled();
    });
  });

  describe('Error State', () => {
    it('shows error when document not found', () => {
      render(
        <DocumentPreview document={null} isOpen={true} onClose={jest.fn()} />,
        { wrapper: createWrapper() }
      );

      expect(screen.getByText(/document not found/i)).toBeInTheDocument();
    });
  });
});
