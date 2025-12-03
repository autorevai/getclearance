/**
 * Tests for DocumentList Component
 *
 * Tests cover:
 * - Document display with all fields
 * - Status rendering (pending, processing, verified, failed)
 * - OCR confidence display
 * - Fraud signals display
 * - Loading and error states
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import DocumentList from '../components/DocumentList';

// Mock data
const mockDocuments = [
  {
    id: 'doc-1',
    document_type: 'passport',
    file_name: 'passport.jpg',
    file_size: 2048000,
    status: 'verified',
    uploaded_at: '2025-01-01T10:00:00Z',
    ocr_confidence: 0.95,
    mrz_valid: true,
    extracted_data: {
      full_name: 'John Doe',
      date_of_birth: '1990-01-15',
      document_number: 'AB1234567',
    },
    fraud_signals: [],
  },
  {
    id: 'doc-2',
    document_type: 'driver_license',
    file_name: 'license.pdf',
    file_size: 1024000,
    status: 'processing',
    uploaded_at: '2025-01-02T11:00:00Z',
    ocr_confidence: null,
    extracted_data: null,
    fraud_signals: null,
  },
  {
    id: 'doc-3',
    document_type: 'utility_bill',
    file_name: 'bill.png',
    file_size: 512000,
    status: 'pending_review',
    uploaded_at: '2025-01-03T12:00:00Z',
    ocr_confidence: 0.3,
    extracted_data: {},
    fraud_signals: [
      { type: 'image_manipulation', description: 'Possible editing detected', confidence: 0.85 },
    ],
  },
];

// Mock variables
const mockRefetch = jest.fn();
const mockDeleteMutateAsync = jest.fn();
const mockDownloadMutateAsync = jest.fn();
const mockAnalyzeMutateAsync = jest.fn();

let mockData = mockDocuments;
let mockIsLoading = false;
let mockError = null;

jest.mock('../hooks/useDocuments', () => ({
  useApplicantDocuments: () => ({
    data: mockData,
    isLoading: mockIsLoading,
    error: mockError,
    refetch: mockRefetch,
  }),
  useDeleteDocument: () => ({
    mutateAsync: mockDeleteMutateAsync,
    isPending: false,
    variables: null,
  }),
  useDownloadDocument: () => ({
    mutateAsync: mockDownloadMutateAsync,
    isPending: false,
    variables: null,
  }),
  useAnalyzeDocument: () => ({
    mutateAsync: mockAnalyzeMutateAsync,
    isPending: false,
    variables: null,
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

describe('DocumentList', () => {
  const defaultProps = {
    applicantId: 'test-applicant-id',
    onDocumentClick: jest.fn(),
  };

  beforeEach(() => {
    jest.clearAllMocks();
    mockData = mockDocuments;
    mockIsLoading = false;
    mockError = null;
  });

  describe('Rendering', () => {
    it('renders all documents', () => {
      render(<DocumentList {...defaultProps} />, { wrapper: createWrapper() });

      expect(screen.getByText('Passport')).toBeInTheDocument();
      expect(screen.getByText("Driver's License")).toBeInTheDocument();
      expect(screen.getByText('Utility Bill')).toBeInTheDocument();
    });

    it('displays file names', () => {
      render(<DocumentList {...defaultProps} />, { wrapper: createWrapper() });

      expect(screen.getByText(/passport.jpg/i)).toBeInTheDocument();
      expect(screen.getByText(/license.pdf/i)).toBeInTheDocument();
      expect(screen.getByText(/bill.png/i)).toBeInTheDocument();
    });
  });

  describe('Status Display', () => {
    it('shows verified status', () => {
      render(<DocumentList {...defaultProps} />, { wrapper: createWrapper() });

      expect(screen.getByText('Verified')).toBeInTheDocument();
    });

    it('shows processing status', () => {
      render(<DocumentList {...defaultProps} />, { wrapper: createWrapper() });

      expect(screen.getByText('Processing')).toBeInTheDocument();
    });

    it('shows review status', () => {
      render(<DocumentList {...defaultProps} />, { wrapper: createWrapper() });

      expect(screen.getByText('Review')).toBeInTheDocument();
    });
  });

  describe('OCR Confidence', () => {
    it('displays OCR confidence for verified documents', () => {
      render(<DocumentList {...defaultProps} />, { wrapper: createWrapper() });

      expect(screen.getByText('95% OCR')).toBeInTheDocument();
    });
  });

  describe('Fraud Signals', () => {
    it('displays fraud signal badge when present', () => {
      render(<DocumentList {...defaultProps} />, { wrapper: createWrapper() });

      expect(screen.getByText('1 signal')).toBeInTheDocument();
    });
  });

  describe('Actions', () => {
    it('calls onDocumentClick when view button is clicked', async () => {
      const onDocumentClick = jest.fn();
      render(
        <DocumentList {...defaultProps} onDocumentClick={onDocumentClick} />,
        { wrapper: createWrapper() }
      );

      const viewButtons = screen.getAllByTitle('Preview document');
      await userEvent.click(viewButtons[0]);

      expect(onDocumentClick).toHaveBeenCalledWith(mockDocuments[0]);
    });

    it('triggers download when download button is clicked', async () => {
      render(<DocumentList {...defaultProps} />, { wrapper: createWrapper() });

      const downloadButtons = screen.getAllByTitle('Download document');
      await userEvent.click(downloadButtons[0]);

      expect(mockDownloadMutateAsync).toHaveBeenCalled();
    });

    it('shows delete confirmation dialog', async () => {
      render(<DocumentList {...defaultProps} />, { wrapper: createWrapper() });

      const deleteButtons = screen.getAllByTitle('Delete document');
      await userEvent.click(deleteButtons[0]);

      expect(screen.getByText('Delete Document')).toBeInTheDocument();
    });
  });

  describe('Loading State', () => {
    it('shows loading spinner when loading', () => {
      mockData = null;
      mockIsLoading = true;

      render(<DocumentList {...defaultProps} />, { wrapper: createWrapper() });

      expect(screen.getByText(/loading documents/i)).toBeInTheDocument();
    });
  });

  describe('Error State', () => {
    it('shows error message when fetch fails', () => {
      mockData = null;
      mockIsLoading = false;
      mockError = new Error('Failed to fetch');

      render(<DocumentList {...defaultProps} />, { wrapper: createWrapper() });

      expect(screen.getByText(/failed to load documents/i)).toBeInTheDocument();
    });

    it('shows retry button on error', async () => {
      mockData = null;
      mockError = new Error('Failed to fetch');

      render(<DocumentList {...defaultProps} />, { wrapper: createWrapper() });

      const retryButton = screen.getByText(/retry/i);
      await userEvent.click(retryButton);

      expect(mockRefetch).toHaveBeenCalled();
    });
  });

  describe('Empty State', () => {
    it('shows empty message when no documents', () => {
      mockData = [];

      render(<DocumentList {...defaultProps} />, { wrapper: createWrapper() });

      expect(screen.getByText(/no documents uploaded/i)).toBeInTheDocument();
    });

    it('can hide empty state', () => {
      mockData = [];

      render(<DocumentList {...defaultProps} showEmpty={false} />, { wrapper: createWrapper() });

      expect(screen.queryByText(/no documents uploaded/i)).not.toBeInTheDocument();
    });
  });
});
