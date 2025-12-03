const { chromium } = require('playwright');

const EMAIL = 'chris.diyanni@gmail.com';
const PASSWORD = 'xth4PYB.yqz3hwa5bjg';

const PAGES_TO_TEST = [
  { name: 'Dashboard', path: '/' },
  { name: 'Applicants', path: '/applicants' },
  { name: 'Screening', path: '/screening' },
  { name: 'Cases', path: '/cases' },
];

(async () => {
  console.log('🚀 Testing all pages...\n');

  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext();
  const page = await context.newPage();

  // Login first
  console.log('1. Logging in...');
  await page.goto('https://getclearance.vercel.app', { waitUntil: 'networkidle' });

  const loginButton = await page.$('button:has-text("Log In"), button:has-text("Sign In"), a:has-text("Log In")');
  if (loginButton) {
    await loginButton.click();
    await page.waitForTimeout(2000);

    await page.waitForSelector('input[name="username"], input[name="email"], input[type="email"]', { timeout: 10000 });
    const emailInput = await page.$('input[name="username"]') || await page.$('input[name="email"]') || await page.$('input[type="email"]');
    if (emailInput) await emailInput.fill(EMAIL);

    const passwordInput = await page.$('input[name="password"], input[type="password"]');
    if (passwordInput) await passwordInput.fill(PASSWORD);

    const submitButton = await page.$('button[type="submit"], button:has-text("Continue"), button:has-text("Log In")');
    if (submitButton) await submitButton.click();

    await page.waitForTimeout(5000);
  }

  console.log('2. Logged in, testing pages...\n');

  // Test each page
  for (const pageInfo of PAGES_TO_TEST) {
    const errors = [];

    page.on('response', async response => {
      if (response.status() >= 400) {
        let body = '';
        try { body = await response.text(); } catch (e) {}
        errors.push({
          status: response.status(),
          url: response.url().replace('https://getclearance-production.up.railway.app', ''),
          body: body.substring(0, 200)
        });
      }
    });

    console.log(`Testing: ${pageInfo.name} (${pageInfo.path})`);

    try {
      await page.goto(`https://getclearance.vercel.app${pageInfo.path}`, {
        waitUntil: 'networkidle',
        timeout: 30000
      });
      await page.waitForTimeout(3000);

      if (errors.length > 0) {
        console.log(`  ❌ ${errors.length} errors:`);
        errors.forEach(e => console.log(`     ${e.status} ${e.url} - ${e.body.substring(0, 100)}`));
      } else {
        console.log(`  ✅ No errors`);
      }

      // Take screenshot
      await page.screenshot({
        path: `/Users/chrisdiyanni/getclearance/test-${pageInfo.name.toLowerCase()}.png`,
        fullPage: true
      });

    } catch (err) {
      console.log(`  ❌ Failed: ${err.message}`);
    }

    // Clear errors for next page
    errors.length = 0;
    console.log('');
  }

  await browser.close();
  console.log('Done! Screenshots saved.');
})();
