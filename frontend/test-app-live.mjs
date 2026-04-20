import { chromium } from 'playwright';

const BASE_URL = 'http://localhost:51735';

(async () => {
  const browser = await chromium.launch({ headless: false });
  const page = await browser.newPage();

  try {
    console.log('\n🚀 Starting live app test...\n');

    // Test 1: Home page
    console.log('1️⃣  Loading home page...');
    await page.goto(BASE_URL, { waitUntil: 'networkidle' });
    console.log(`✅ Page loaded: ${page.url()}`);

    const title = await page.title();
    console.log(`📄 Title: ${title}`);

    // Screenshot
    await page.screenshot({ path: '/tmp/01-home.png', fullPage: true });
    console.log('📸 Screenshot saved: /tmp/01-home.png\n');

    // Test 2: Check for signin/signup form
    console.log('2️⃣  Looking for authentication form...');
    const emailField = await page.$('input[type="email"]');
    const passwordField = await page.$('input[type="password"]');

    if (emailField && passwordField) {
      console.log('✅ Found signin/signup form');
      await page.screenshot({ path: '/tmp/02-auth-form.png', fullPage: true });
      console.log('📸 Screenshot saved: /tmp/02-auth-form.png\n');

      // Try signup with test credentials
      console.log('3️⃣  Attempting signup with test credentials...');
      const timestamp = Date.now();
      const testEmail = `test.${timestamp}@localhost.test`;
      const testPassword = 'TestPassword123!';

      console.log(`   Email: ${testEmail}`);
      console.log(`   Password: ${testPassword}`);

      await emailField.fill(testEmail);
      await passwordField.fill(testPassword);

      // Look for signup button
      const signupBtn = await page.$('button:has-text("Sign up")') ||
                        await page.$('button:has-text("Create account")') ||
                        await page.$('button[type="submit"]');

      if (signupBtn) {
        console.log('✅ Found signup button, clicking...');
        await signupBtn.click();

        // Wait for response
        await page.waitForNavigation({ waitUntil: 'networkidle' }).catch(() => {});
        await page.waitForTimeout(2000);

        console.log(`📍 After signup: ${page.url()}`);
        await page.screenshot({ path: '/tmp/03-after-signup.png', fullPage: true });
        console.log('📸 Screenshot saved: /tmp/03-after-signup.png\n');
      }
    } else {
      console.log('⚠️  No auth form found');
      const bodyText = await page.locator('body').innerText();
      console.log('📝 Page content (first 300 chars):');
      console.log(bodyText.substring(0, 300) + '\n');
    }

    // Test 4: Check navbar/sidebar for product_ops
    console.log('4️⃣  Checking for product references in UI...');
    const bodyText = await page.locator('body').innerText();
    const hasProductRef = bodyText.toLowerCase().includes('product');

    if (hasProductRef) {
      console.log('⚠️  WARNING: Found "product" reference in UI');
      const lines = bodyText.split('\n').filter(line => line.toLowerCase().includes('product'));
      console.log('   Lines:', lines.slice(0, 3).join(' | '));
    } else {
      console.log('✅ No "product" references found (cleanup successful!)');
    }

    // Test 5: Try navigating to key routes (if logged in)
    console.log('\n5️⃣  Testing key routes...');
    const routesToTest = [
      { path: '/iam', name: 'IAM' },
      { path: '/audit', name: 'Audit' },
      { path: '/vault', name: 'Vault' },
      { path: '/notify', name: 'Notify' },
      { path: '/feature-flags', name: 'Feature Flags' },
      { path: '/monitoring', name: 'Monitoring' },
      { path: '/system/health', name: 'System Health' },
      { path: '/product', name: 'Product (should 404)' },
    ];

    for (const route of routesToTest) {
      try {
        await page.goto(`${BASE_URL}${route.path}`, { waitUntil: 'networkidle', timeout: 5000 });
        const status = page.url().includes(route.path) ? '✅' : '⚠️';
        console.log(`   ${status} ${route.name}: ${page.url()}`);

        if (route.path === '/product') {
          await page.screenshot({ path: '/tmp/product-route-test.png', fullPage: true });
          console.log('      📸 Product route attempt saved');
        }
      } catch (err) {
        console.log(`   ❌ ${route.name}: ${err.message.substring(0, 50)}`);
      }
    }

    console.log('\n✅ Test complete!\n');
    console.log('Screenshots saved to /tmp/');
    console.log('Check these files:');
    console.log('  - /tmp/01-home.png');
    console.log('  - /tmp/02-auth-form.png');
    console.log('  - /tmp/03-after-signup.png');
    console.log('  - /tmp/product-route-test.png (should show 404)\n');

  } catch (err) {
    console.error('❌ Error:', err.message);
  } finally {
    await browser.close();
  }
})();
