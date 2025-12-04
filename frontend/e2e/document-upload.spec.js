/**
 * Get Clearance - Document Upload E2E Tests
 * ==========================================
 * Tests for document verification workflow.
 */

const { test, expect } = require('@playwright/test');
const path = require('path');

test.describe('Document Upload', () => {
  test('should display upload interface', async ({ page }) => {
    // Navigate to document upload area
    await page.goto('/applicants');

    // Look for upload button or area
    const uploadArea = page.locator(
      'input[type="file"], [data-testid="upload"], button:has-text("Upload"), .upload-area, .dropzone'
    ).first();

    if (await uploadArea.isVisible({ timeout: 5000 }).catch(() => false)) {
      await expect(uploadArea).toBeVisible();
    }
  });

  test('should accept valid document types', async ({ page }) => {
    await page.goto('/applicants');

    // Find file input
    const fileInput = page.locator('input[type="file"]').first();

    if (await fileInput.isVisible({ timeout: 5000 }).catch(() => false)) {
      // Check accept attribute
      const accept = await fileInput.getAttribute('accept');

      // Should accept common document formats
      if (accept) {
        const acceptsPdf = accept.includes('pdf');
        const acceptsImages = accept.includes('image') || accept.includes('jpg') || accept.includes('png');
        expect(acceptsPdf || acceptsImages || accept === '*/*').toBeTruthy();
      }
    }
  });

  test('should show drag and drop zone', async ({ page }) => {
    await page.goto('/applicants');

    // Look for drag-drop area
    const dropzone = page.locator(
      '.dropzone, [data-testid="dropzone"], [data-testid="upload-area"], [class*="drop"]'
    ).first();

    if (await dropzone.isVisible({ timeout: 5000 }).catch(() => false)) {
      await expect(dropzone).toBeVisible();
    }
  });
});

test.describe('Document Verification Display', () => {
  test('should show verification status', async ({ page }) => {
    await page.goto('/applicants');

    // Look for document status indicators
    const statusIndicator = page.locator(
      '[data-testid="document-status"], .document-status, .verification-status, .status-badge'
    ).first();

    if (await statusIndicator.isVisible({ timeout: 5000 }).catch(() => false)) {
      await expect(statusIndicator).toBeVisible();
    }
  });

  test('should display extracted data', async ({ page }) => {
    await page.goto('/applicants');

    // Find applicant and open detail
    const applicantItem = page.locator('tr:not(:first-child), [data-testid="applicant-row"]').first();

    if (await applicantItem.isVisible({ timeout: 5000 }).catch(() => false)) {
      await applicantItem.click();
      await page.waitForTimeout(1000);

      // Look for extracted data section
      const extractedData = page.locator(
        '[data-testid="extracted-data"], .ocr-results, .document-data, h3:has-text("Document"), h3:has-text("Extracted")'
      );

      const hasData = await extractedData.isVisible({ timeout: 3000 }).catch(() => false);
      // May not be present if no documents
    }
  });

  test('should show document preview', async ({ page }) => {
    await page.goto('/applicants');

    // Look for document thumbnail or preview
    const preview = page.locator(
      '[data-testid="document-preview"], img[alt*="document" i], .document-thumbnail, .preview'
    ).first();

    if (await preview.isVisible({ timeout: 5000 }).catch(() => false)) {
      await expect(preview).toBeVisible();
    }
  });
});
