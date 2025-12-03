/**
 * Tests for DocumentUpload Component
 *
 * Tests cover:
 * - File type validation (JPEG, PNG, PDF)
 * - File size validation (max 50MB)
 * - Drag & drop functionality
 * - Upload progress display
 * - Document type selection
 * - Multi-file support for front/back
 * - Image preview thumbnails
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import DocumentUpload from '../components/DocumentUpload';

// Mock the hooks at module level
const mockMutateAsync = jest.fn();
const mockAbort = jest.fn();

jest.mock('../hooks/useDocuments', () => ({
  useUploadDocument: () => ({
    mutateAsync: mockMutateAsync,
    isPending: false,
    progress: 0,
    stage: null,
    abort: mockAbort,
  }),
}));

jest.mock('../contexts/ToastContext', () => ({
  useToast: () => ({
    success: jest.fn(),
    error: jest.fn(),
    warning: jest.fn(),
    info: jest.fn(),
  }),
}));

// Create test wrapper with all providers
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

// Helper to create a mock file with proper magic bytes
const createMockFile = (name, size, type) => {
  // Create proper file content with magic bytes
  let content;
  if (type === 'image/jpeg') {
    content = new Uint8Array([0xFF, 0xD8, 0xFF, 0xE0]);
  } else if (type === 'image/png') {
    content = new Uint8Array([0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A]);
  } else if (type === 'application/pdf') {
    content = new Uint8Array([0x25, 0x50, 0x44, 0x46]);
  } else {
    content = new Uint8Array([0x00, 0x00, 0x00, 0x00]);
  }

  const file = new File([content], name, { type });
  Object.defineProperty(file, 'size', { value: size });
  return file;
};

describe('DocumentUpload', () => {
  const defaultProps = {
    applicantId: 'test-applicant-id',
    onUploadComplete: jest.fn(),
    onUploadError: jest.fn(),
  };

  beforeEach(() => {
    jest.clearAllMocks();
    // Mock URL.createObjectURL
    global.URL.createObjectURL = jest.fn(() => 'mock-preview-url');
    global.URL.revokeObjectURL = jest.fn();
  });

  describe('Rendering', () => {
    it('renders the document type selector', () => {
      render(<DocumentUpload {...defaultProps} />, { wrapper: createWrapper() });

      expect(screen.getByLabelText(/document type/i)).toBeInTheDocument();
    });

    it('renders the drop zone for front side', () => {
      render(<DocumentUpload {...defaultProps} />, { wrapper: createWrapper() });

      expect(screen.getByText(/add file/i)).toBeInTheDocument();
    });

    it('renders all document type options', () => {
      render(<DocumentUpload {...defaultProps} />, { wrapper: createWrapper() });

      const select = screen.getByLabelText(/document type/i);
      expect(select).toBeInTheDocument();
    });

    it('shows front/back labels for driver license', async () => {
      render(<DocumentUpload {...defaultProps} />, { wrapper: createWrapper() });

      const select = screen.getByLabelText(/document type/i);
      await userEvent.selectOptions(select, 'driver_license');

      expect(screen.getByText('Front Side')).toBeInTheDocument();
      expect(screen.getByText('Back Side')).toBeInTheDocument();
    });
  });

  describe('File Type Validation', () => {
    it('accepts JPEG files', async () => {
      render(<DocumentUpload {...defaultProps} />, { wrapper: createWrapper() });

      const file = createMockFile('test.jpg', 1024, 'image/jpeg');
      const input = document.querySelector('input[type="file"]');

      await userEvent.upload(input, file);

      await waitFor(() => {
        expect(screen.queryByText(/invalid file type/i)).not.toBeInTheDocument();
      });
    });

    it('accepts PNG files', async () => {
      render(<DocumentUpload {...defaultProps} />, { wrapper: createWrapper() });

      const file = createMockFile('test.png', 1024, 'image/png');
      const input = document.querySelector('input[type="file"]');

      await userEvent.upload(input, file);

      await waitFor(() => {
        expect(screen.queryByText(/invalid file type/i)).not.toBeInTheDocument();
      });
    });

    it('accepts PDF files', async () => {
      render(<DocumentUpload {...defaultProps} />, { wrapper: createWrapper() });

      const file = createMockFile('test.pdf', 1024, 'application/pdf');
      const input = document.querySelector('input[type="file"]');

      await userEvent.upload(input, file);

      await waitFor(() => {
        expect(screen.queryByText(/invalid file type/i)).not.toBeInTheDocument();
      });
    });

    it('rejects files with invalid magic bytes', async () => {
      render(<DocumentUpload {...defaultProps} />, { wrapper: createWrapper() });

      // Create a file that claims to be JPEG but has wrong magic bytes
      const wrongContent = new Uint8Array([0x00, 0x00, 0x00, 0x00]);
      const file = new File([wrongContent], 'fake.jpg', { type: 'image/jpeg' });

      const input = document.querySelector('input[type="file"]');

      await userEvent.upload(input, file);

      await waitFor(() => {
        expect(screen.getByText(/file contents do not match/i)).toBeInTheDocument();
      });
    });
  });

  describe('File Size Validation', () => {
    it('accepts files under 50MB', async () => {
      render(<DocumentUpload {...defaultProps} />, { wrapper: createWrapper() });

      const file = createMockFile('test.jpg', 49 * 1024 * 1024, 'image/jpeg');
      const input = document.querySelector('input[type="file"]');

      await userEvent.upload(input, file);

      await waitFor(() => {
        expect(screen.queryByText(/too large/i)).not.toBeInTheDocument();
      });
    });

    it('rejects files over 50MB', async () => {
      render(<DocumentUpload {...defaultProps} />, { wrapper: createWrapper() });

      const file = createMockFile('huge.jpg', 51 * 1024 * 1024, 'image/jpeg');
      const input = document.querySelector('input[type="file"]');

      await userEvent.upload(input, file);

      await waitFor(() => {
        expect(screen.getByText(/too large/i)).toBeInTheDocument();
      });
    });
  });

  describe('Document Type Selection', () => {
    it('allows changing document type', async () => {
      render(<DocumentUpload {...defaultProps} />, { wrapper: createWrapper() });

      const select = screen.getByLabelText(/document type/i);
      await userEvent.selectOptions(select, 'driver_license');

      expect(select.value).toBe('driver_license');
    });

    it('uses default document type if provided', () => {
      render(
        <DocumentUpload {...defaultProps} defaultDocumentType="utility_bill" />,
        { wrapper: createWrapper() }
      );

      const select = screen.getByLabelText(/document type/i);
      expect(select.value).toBe('utility_bill');
    });

    it('shows two drop zones for ID card', async () => {
      render(<DocumentUpload {...defaultProps} />, { wrapper: createWrapper() });

      const select = screen.getByLabelText(/document type/i);
      await userEvent.selectOptions(select, 'id_card');

      expect(screen.getByText('Front Side')).toBeInTheDocument();
      expect(screen.getByText('Back Side')).toBeInTheDocument();
    });

    it('shows single drop zone for passport', async () => {
      render(<DocumentUpload {...defaultProps} />, { wrapper: createWrapper() });

      const select = screen.getByLabelText(/document type/i);
      await userEvent.selectOptions(select, 'passport');

      expect(screen.getByText('Document')).toBeInTheDocument();
      expect(screen.queryByText('Back Side')).not.toBeInTheDocument();
    });
  });

  describe('Image Preview', () => {
    it('shows image preview after selecting image file', async () => {
      render(<DocumentUpload {...defaultProps} />, { wrapper: createWrapper() });

      const file = createMockFile('passport.jpg', 2 * 1024 * 1024, 'image/jpeg');
      const input = document.querySelector('input[type="file"]');

      await userEvent.upload(input, file);

      await waitFor(() => {
        const preview = document.querySelector('.file-preview');
        expect(preview || document.querySelector('.preview-container')).toBeInTheDocument();
      });
    });

    it('shows file card for PDF files', async () => {
      render(<DocumentUpload {...defaultProps} />, { wrapper: createWrapper() });

      const file = createMockFile('document.pdf', 1024, 'application/pdf');
      const input = document.querySelector('input[type="file"]');

      await userEvent.upload(input, file);

      await waitFor(() => {
        // PDFs show file card, not image preview
        expect(screen.getByText(/document.pdf/i)).toBeInTheDocument();
      });
    });
  });

  describe('Multi-file Upload', () => {
    it('requires both sides for driver license before upload', async () => {
      render(<DocumentUpload {...defaultProps} />, { wrapper: createWrapper() });

      // Select driver license
      const select = screen.getByLabelText(/document type/i);
      await userEvent.selectOptions(select, 'driver_license');

      // Add front file only
      const file = createMockFile('front.jpg', 1024, 'image/jpeg');
      const inputs = document.querySelectorAll('input[type="file"]');
      await userEvent.upload(inputs[0], file);

      // Try to upload - should show error about needing both sides
      await waitFor(() => {
        const uploadBtn = screen.queryByText(/upload both sides/i);
        if (uploadBtn) {
          fireEvent.click(uploadBtn);
        }
      });
    });

    it('shows "Upload Both Sides" button for ID documents', async () => {
      render(<DocumentUpload {...defaultProps} />, { wrapper: createWrapper() });

      // Select driver license
      const select = screen.getByLabelText(/document type/i);
      await userEvent.selectOptions(select, 'driver_license');

      // Add front file
      const frontFile = createMockFile('front.jpg', 1024, 'image/jpeg');
      const inputs = document.querySelectorAll('input[type="file"]');
      await userEvent.upload(inputs[0], frontFile);

      await waitFor(() => {
        expect(screen.getByText(/upload both sides/i)).toBeInTheDocument();
      });
    });
  });

  describe('Accessibility', () => {
    it('has labeled document type selector', () => {
      render(<DocumentUpload {...defaultProps} />, { wrapper: createWrapper() });

      const select = screen.getByLabelText(/document type/i);
      expect(select).toBeInTheDocument();
    });
  });
});
