const { chromium } = require('playwright');

const EMAIL = 'chris.diyanni@gmail.com';
const PASSWORD = 'xth4PYB.yqz3hwa5bjg';

(async () => {
  console.log('🧪 Testing AI Suggestion on existing Vladimir Putin hits\n');

  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext();
  const page = await context.newPage();

  // Track AI suggestion API call
  let suggestionResult = null;

  page.on('response', async response => {
    const url = response.url();
    if (url.includes('/suggestion')) {
      const status = response.status();
      console.log(`\n📡 AI Suggestion API Response: ${status}`);
      try {
        suggestionResult = await response.json();
        console.log('   Full response:', JSON.stringify(suggestionResult, null, 2));
      } catch (e) {
        const text = await response.text();
        console.log('   Error response:', text.substring(0, 500));
      }
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
    console.log('\n2. Going to screening page...');
    await page.goto('https://getclearance.vercel.app/screening', { waitUntil: 'networkidle' });
    await page.waitForTimeout(3000);

    // Debug: take screenshot to see current state
    await page.screenshot({ path: '/Users/chrisdiyanni/getclearance/debug-before-click.png' });
    console.log('   Debug screenshot saved');

    // Check if we're logged in by looking for user email or screening content
    const pageContent = await page.textContent('body');
    if (pageContent.includes('Sign in') || pageContent.includes('Log In')) {
      console.log('   ⚠️ Not logged in! Auth may have failed.');
    } else {
      console.log('   ✅ Page loaded, looking for Putin entry...');
    }

    // Click on Vladimir Putin with 5 hits (the Pending Review one)
    console.log('\n3. Clicking on Vladimir Putin entry with 5 hits...');

    // Wait for table to load
    await page.waitForSelector('text=Vladimir Putin', { timeout: 10000 }).catch(() => {
      console.log('   Could not find Vladimir Putin text');
    });

    // Click on the first row that has "5 hits" (Vladimir Putin with hits)
    console.log('   Looking for row with 5 hits...');

    // The eye icon is an SVG, click anywhere on the row
    const rows = await page.$$('div[class*="row"], tr, [role="row"]');
    console.log(`   Found ${rows.length} potential rows`);

    // Just click the first Vladimir Putin text we find
    try {
      await page.locator('text=Vladamir Putin').first().click({ timeout: 5000 });
      console.log('   Clicked on Vladamir Putin');
    } catch (e) {
      // Try clicking on "5 hits" which is unique
      console.log('   Trying to click on "5 hits"...');
      await page.locator('text=5 hits').click({ timeout: 5000 });
    }

    // Wait for detail panel and AI suggestion to load
    console.log('\n4. Waiting for AI suggestion to load (15 seconds)...');
    await page.waitForTimeout(15000);

    // Take screenshot
    await page.screenshot({ path: '/Users/chrisdiyanni/getclearance/ai-test-result.png', fullPage: true });
    console.log('\n📸 Screenshot saved: ai-test-result.png');

    // Check page content
    const pageText = await page.textContent('body');

    console.log('\n' + '='.repeat(60));
    console.log('📊 AI SUGGESTION TEST RESULTS');
    console.log('='.repeat(60));

    if (suggestionResult) {
      console.log('\n✅ AI API was called');
      console.log(`   Suggested resolution: ${suggestionResult.suggested_resolution}`);
      console.log(`   Confidence: ${suggestionResult.confidence}%`);
      console.log(`   Reasoning: ${suggestionResult.reasoning}`);

      if (suggestionResult.reasoning === 'Unable to generate suggestion, manual review required') {
        console.log('\n❌ AI returned FALLBACK response');
        console.log('   This means ANTHROPIC_API_KEY is missing or invalid');
        console.log('\n   To fix: Check Railway Variables for ANTHROPIC_API_KEY');
      } else {
        console.log('\n✅ AI IS WORKING! Real suggestion generated.');
      }
    } else {
      console.log('\n⚠️  No AI suggestion API call captured');
      console.log('   The suggestion endpoint may not have been called');
    }

    // Check what's displayed on the page
    if (pageText.includes('Unable to generate suggestion')) {
      console.log('\n❌ UI shows: "Unable to generate suggestion"');
    }
    if (pageText.includes('AI Review Recommendation')) {
      console.log('\n✅ UI shows AI Review Recommendation section');
    }

    console.log('\n' + '='.repeat(60));
    console.log('📋 EXPECTED FOR VLADIMIR PUTIN (Sumsub-standard):');
    console.log('='.repeat(60));
    console.log('• AI should recommend: CONFIRM MATCH (True Positive)');
    console.log('• Confidence: 80-100%');
    console.log('• Reasoning should mention:');
    console.log('  - Exact name match');
    console.log('  - Multiple sanctions lists');
    console.log('  - Known sanctioned individual');
    console.log('  - President of Russia');

  } catch (err) {
    console.error('\n❌ Test failed:', err.message);
  } finally {
    await browser.close();
  }
})();
