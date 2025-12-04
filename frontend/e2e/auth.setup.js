/**
 * Get Clearance - Authentication Setup for E2E Tests
 * ====================================================
 * Sets up authenticated state for E2E tests.
 *
 * Since we use Auth0, this file provides:
 * - Mock authentication for local testing
 * - Storage state setup for authenticated sessions
 */

const { test: setup, expect } = require('@playwright/test');

const STORAGE_STATE_FILE = 'playwright/.auth/user.json';

/**
 * Setup mock authentication state.
 * In a real scenario, you'd log in via Auth0 test account.
 */
setup('authenticate', async ({ page, context }) => {
  // For local testing, we can bypass Auth0 with mock tokens
  // In CI, you would use Auth0 test credentials

  if (process.env.AUTH0_TEST_EMAIL && process.env.AUTH0_TEST_PASSWORD) {
    // Real Auth0 login flow
    await page.goto('/login');

    // Wait for Auth0 redirect
    await page.waitForURL(/.*auth0\.com.*/);

    // Fill Auth0 login form
    await page.fill('input[name="email"], input[name="username"]', process.env.AUTH0_TEST_EMAIL);
    await page.fill('input[name="password"]', process.env.AUTH0_TEST_PASSWORD);
    await page.click('button[type="submit"]');

    // Wait for redirect back to app
    await page.waitForURL('http://localhost:9000/**');

    // Verify logged in
    await expect(page.locator('[data-testid="user-menu"]')).toBeVisible({ timeout: 10000 });
  } else {
    // Mock authentication for local development
    console.log('No Auth0 credentials provided, setting up mock auth state');

    // Navigate to app (will redirect to login)
    await page.goto('/');

    // Set mock auth token in localStorage
    await page.evaluate(() => {
      const mockAuthState = {
        isAuthenticated: true,
        user: {
          sub: 'auth0|test-user-id',
          email: 'test@example.com',
          name: 'Test User',
          email_verified: true,
        },
        accessToken: 'mock-access-token-for-testing',
      };

      // Store auth state (format depends on Auth0 React SDK)
      localStorage.setItem('@@auth0spajs@@::test::default::openid profile email', JSON.stringify({
        body: mockAuthState,
        expiresAt: Math.floor(Date.now() / 1000) + 86400,
      }));
    });
  }

  // Save storage state
  await context.storageState({ path: STORAGE_STATE_FILE });
});

module.exports = { STORAGE_STATE_FILE };
