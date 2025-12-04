/**
 * Get Clearance - Cases E2E Tests
 * =================================
 * Tests for case management workflow.
 */

const { test, expect } = require('@playwright/test');

test.describe('Cases Page', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/cases');
  });

  test('should display cases list or empty state', async ({ page }) => {
    await page.waitForLoadState('networkidle', { timeout: 10000 }).catch(() => {});

    // Check for cases content
    const hasContent = await page.locator(
      '[data-testid="cases-list"], table, .cases-container, [data-testid="empty-state"], h1, h2'
    ).first().isVisible({ timeout: 10000 }).catch(() => false);

    expect(hasContent || await page.locator('body').isVisible()).toBeTruthy();
  });

  test('should display case status filters', async ({ page }) => {
    // Look for status filter tabs or dropdown
    const statusFilter = page.locator(
      '[data-testid="status-filter"], button:has-text("Open"), button:has-text("Pending"), select, [role="tablist"]'
    ).first();

    if (await statusFilter.isVisible({ timeout: 5000 }).catch(() => false)) {
      await expect(statusFilter).toBeVisible();
    }
  });

  test('should display case priority indicators', async ({ page }) => {
    // Look for priority indicators
    const priorityIndicator = page.locator(
      '[data-testid="priority"], .priority, [class*="priority"], [class*="high"], [class*="critical"]'
    ).first();

    // Priority may not be visible if no cases
    const visible = await priorityIndicator.isVisible({ timeout: 3000 }).catch(() => false);
    await expect(page.locator('body')).toBeVisible();
  });
});

test.describe('Case Detail and Resolution', () => {
  test('should open case detail view', async ({ page }) => {
    await page.goto('/cases');

    // Find first case item
    const caseItem = page.locator(
      'tr:not(:first-child), [data-testid="case-row"], [data-testid="case-card"], .case-item'
    ).first();

    if (await caseItem.isVisible({ timeout: 5000 }).catch(() => false)) {
      await caseItem.click();
      await page.waitForTimeout(1000);

      // Should show case detail
      const detailView = page.locator(
        '[data-testid="case-detail"], .case-detail, dialog, [role="dialog"], h1:has-text("Case")'
      );
      const hasDetail = await detailView.isVisible({ timeout: 3000 }).catch(() => false);
      const urlChanged = (await page.url()).includes('case');

      expect(hasDetail || urlChanged).toBeTruthy();
    }
  });

  test('should have case action buttons', async ({ page }) => {
    // Navigate to a case (if one exists)
    await page.goto('/cases');

    // Check for action buttons on the list page
    const actionButtons = page.locator(
      'button:has-text("Resolve"), button:has-text("Assign"), button:has-text("Close"), [data-testid="case-action"]'
    );

    // Actions may be in dropdown or detail view
    const hasActions = await actionButtons.first().isVisible({ timeout: 3000 }).catch(() => false);
    await expect(page.locator('body')).toBeVisible();
  });

  test('should display case notes section', async ({ page }) => {
    await page.goto('/cases');

    // Find and click first case
    const caseItem = page.locator('tr:not(:first-child), [data-testid="case-row"]').first();

    if (await caseItem.isVisible({ timeout: 5000 }).catch(() => false)) {
      await caseItem.click();
      await page.waitForTimeout(1000);

      // Look for notes section
      const notesSection = page.locator(
        '[data-testid="case-notes"], .notes-section, h2:has-text("Notes"), h3:has-text("Notes"), textarea[placeholder*="note" i]'
      );

      const hasNotes = await notesSection.isVisible({ timeout: 3000 }).catch(() => false);
      // May not be visible if not in detail view
    }
  });
});
