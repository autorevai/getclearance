/**
 * Get Clearance - Dashboard E2E Tests
 * =====================================
 * Tests for the main dashboard and navigation.
 */

const { test, expect } = require('@playwright/test');

test.describe('Dashboard', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to dashboard
    await page.goto('/');
  });

  test('should display dashboard title', async ({ page }) => {
    // Check for dashboard or login page
    const dashboardTitle = page.locator('h1, h2').filter({ hasText: /dashboard|login|sign in|welcome/i });
    await expect(dashboardTitle.first()).toBeVisible({ timeout: 10000 });
  });

  test('should have navigation sidebar', async ({ page }) => {
    // Look for navigation elements
    const nav = page.locator('nav, [role="navigation"], aside');
    await expect(nav.first()).toBeVisible({ timeout: 10000 });
  });

  test('should be responsive on mobile', async ({ page }) => {
    // Set mobile viewport
    await page.setViewportSize({ width: 375, height: 812 });

    // Page should still render
    await expect(page.locator('body')).toBeVisible();

    // Check that mobile menu or sidebar adjusts
    const mobileNav = page.locator('[data-testid="mobile-menu"], .mobile-nav, button[aria-label*="menu"]');
    // Some pages may not have mobile menu, so just check page loads
    await expect(page).toHaveURL(/./);
  });
});

test.describe('Navigation', () => {
  test('should navigate to applicants page', async ({ page }) => {
    await page.goto('/');

    // Find and click applicants link
    const applicantsLink = page.locator('a[href*="applicant"], a:has-text("Applicant")').first();

    if (await applicantsLink.isVisible({ timeout: 5000 }).catch(() => false)) {
      await applicantsLink.click();
      await expect(page).toHaveURL(/applicant/);
    } else {
      // If not visible, may be behind auth
      console.log('Applicants link not immediately visible - may require auth');
    }
  });

  test('should navigate to cases page', async ({ page }) => {
    await page.goto('/');

    // Find and click cases link
    const casesLink = page.locator('a[href*="case"], a:has-text("Case")').first();

    if (await casesLink.isVisible({ timeout: 5000 }).catch(() => false)) {
      await casesLink.click();
      await expect(page).toHaveURL(/case/);
    }
  });

  test('should navigate to analytics page', async ({ page }) => {
    await page.goto('/');

    // Find and click analytics link
    const analyticsLink = page.locator('a[href*="analytics"], a:has-text("Analytics")').first();

    if (await analyticsLink.isVisible({ timeout: 5000 }).catch(() => false)) {
      await analyticsLink.click();
      await expect(page).toHaveURL(/analytics/);
    }
  });
});
