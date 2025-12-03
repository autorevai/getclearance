const { chromium } = require('playwright');

const EMAIL = 'chris.diyanni@gmail.com';
const PASSWORD = 'xth4PYB.yqz3hwa5bjg';

(async () => {
  console.log('🚀 Running NEW screening check to test fixes...\n');

  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext();
  const page = await context.newPage();

  const errors = [];
  page.on('response', async response => {
    if (response.status() >= 400) {
      errors.push({ status: response.status(), url: response.url() });
    }
  });

  try {
    // Login
    console.log('1. Logging in...');
    await page.goto('https://getclearance.vercel.app', { waitUntil: 'networkidle' });
    const loginButton = await page.$('button:has-text("Sign in with Auth0")');
    if (loginButton) {
      await loginButton.click();
      await page.waitForTimeout(2000);
      await page.waitForSelector('input[name="username"]', { timeout: 10000 });
      await page.fill('input[name="username"]', EMAIL);
      await page.fill('input[type="password"]', PASSWORD);
      await page.click('button[type="submit"]');
      await page.waitForTimeout(5000);
    }

    // Go to screening
    console.log('2. Going to screening page...');
    await page.goto('https://getclearance.vercel.app/screening', { waitUntil: 'networkidle' });
    await page.waitForTimeout(2000);

    // Run new check
    console.log('3. Running NEW check for Kim Jong Un...');
    await page.click('button:has-text("Run New Check")');
    await page.waitForTimeout(1000);

    await page.fill('input[type="text"]', 'Kim Jong Un');

    // Try to select North Korea
    const select = await page.$('select');
    if (select) {
      const options = await select.$$('option');
      for (const opt of options) {
        const text = await opt.textContent();
        if (text.includes('North Korea') || text.includes('KP')) {
          await select.selectOption({ label: text.trim() });
          break;
        }
      }
    }

    await page.waitForTimeout(500);
    await page.click('button:has-text("Run Check")');

    console.log('4. Waiting for screening result (can take 10-15 seconds)...');
    await page.waitForTimeout(15000);

    // Take screenshot
    await page.screenshot({ path: '/Users/chrisdiyanni/getclearance/new-check-result.png', fullPage: true });

    // Click on the new entry
    const newEntry = await page.$('tr:has-text("Kim Jong")');
    if (newEntry) {
      await newEntry.click();
      await page.waitForTimeout(2000);
      await page.screenshot({ path: '/Users/chrisdiyanni/getclearance/kim-detail.png', fullPage: true });
    }

    console.log('📸 Screenshots saved');

    // Check results
    const pageText = await page.textContent('body');

    console.log('\n📊 RESULTS:');
    if (errors.length > 0) {
      console.log('❌ Network errors:', errors.map(e => `${e.status}`).join(', '));
    } else {
      console.log('✅ No network errors');
    }

    if (pageText.includes('Kim Jong Un') && pageText.includes('Hit')) {
      console.log('✅ Kim Jong Un check shows hits');
    }

    // Check for Korean characters (foreign names)
    if (pageText.includes('김정은')) {
      console.log('❌ Still showing Korean name');
    } else {
      console.log('✅ Not showing Korean name');
    }

    // Check confidence
    if (pageText.match(/\d{4}%/)) {
      console.log('❌ Confidence still showing 4+ digits');
    } else if (pageText.match(/\d{2}%/)) {
      console.log('✅ Confidence showing correctly (2 digits)');
    }

  } catch (err) {
    console.error('❌ Test failed:', err.message);
    await page.screenshot({ path: '/Users/chrisdiyanni/getclearance/test-error.png', fullPage: true });
  } finally {
    await browser.close();
  }
})();
