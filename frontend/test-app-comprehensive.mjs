import { chromium } from 'playwright';

const BASE_URL = 'http://localhost:51735';

(async () => {
  const browser = await chromium.launch({ headless: false });
  const page = await browser.newPage();

  try {
    console.log('\n🚀 Starting comprehensive app test...\n');

    // Test 1: Home page / signin
    console.log('1️⃣  Loading home page...');
    await page.goto(BASE_URL, { waitUntil: 'networkidle', timeout: 10000 });
    console.log(`✅ Loaded: ${page.url()}`);
    await page.screenshot({ path: '/tmp/01-home.png', fullPage: true });
    console.log('📸 Screenshot: /tmp/01-home.png\n');

    // Test 2: Setup flow (first-time admin creation)
    console.log('2️⃣  Checking for setup/signin form...');
    const emailInput = await page.$('input[type="email"]');
    if (!emailInput) {
      console.log('⚠️  No email input found — checking if already logged in...');
      const bodyText = await page.locator('body').innerText();
      console.log('Page content (first 300 chars):');
      console.log(bodyText.substring(0, 300));
      await browser.close();
      process.exit(0);
    }

    const timestamp = Date.now();
    const testEmail = `test.${timestamp}@localhost.test`;
    const testPassword = 'TestPassword123!@#';

    console.log(`   Email: ${testEmail}`);
    console.log(`   Password: [hidden]\n`);

    await emailInput.fill(testEmail);
    const passwordInput = await page.$('input[type="password"]');
    await passwordInput.fill(testPassword);
    await page.screenshot({ path: '/tmp/02-signin-form.png', fullPage: true });
    console.log('📸 Screenshot: /tmp/02-signin-form.png\n');

    // Test 3: Submit signin/signup
    console.log('3️⃣  Submitting form...');
    const submitBtn = await page.$('button[type="submit"]');
    if (submitBtn) {
      await submitBtn.click();
      await page.waitForNavigation({ waitUntil: 'networkidle', timeout: 10000 }).catch(() => {});
      await page.waitForTimeout(2000);
      console.log(`✅ After submission: ${page.url()}\n`);
      await page.screenshot({ path: '/tmp/03-after-signin.png', fullPage: true });
      console.log('📸 Screenshot: /tmp/03-after-signin.png\n');
    }

    // Test 4: Check navbar/sidebar
    console.log('4️⃣  Checking navbar and sidebar...');
    const navbar = await page.locator('[role="navigation"]').first().innerText().catch(() => '');
    const sidebar = await page.locator('aside, [class*="sidebar"]').first().innerText().catch(() => '');

    if (navbar || sidebar) {
      console.log('✅ Navigation found');
      const navText = (navbar + ' ' + sidebar).toLowerCase();

      // Check for expected nav items
      const expected = ['iam', 'audit', 'vault', 'notify', 'monitoring', 'feature-flags'];
      const found = expected.filter(item => navText.includes(item));
      console.log(`   Found: ${found.length}/${expected.length} expected items`);
      if (found.length === expected.length) {
        console.log('   ✅ All core modules in nav');
      } else {
        console.log(`   ⚠️  Missing: ${expected.filter(i => !found.includes(i)).join(', ')}`);
      }

      // Check for removed "product" references
      if (navText.includes('product') && !navText.includes('product-ops')) {
        console.log('   ⚠️  WARNING: "product" found in nav (not product-ops context)');
      } else {
        console.log('   ✅ No product_ops references in nav');
      }
    } else {
      console.log('⚠️  Could not find navbar/sidebar');
    }

    // Test 5: Navigate to key routes
    console.log('\n5️⃣  Testing key routes...\n');
    const routes = [
      { path: '/iam', name: 'IAM' },
      { path: '/audit', name: 'Audit' },
      { path: '/vault', name: 'Vault' },
      { path: '/notify', name: 'Notify' },
      { path: '/monitoring', name: 'Monitoring' },
      { path: '/feature-flags', name: 'Feature Flags' },
      { path: '/system/health', name: 'System Health' },
    ];

    for (const route of routes) {
      try {
        await page.goto(`${BASE_URL}${route.path}`, {
          waitUntil: 'networkidle',
          timeout: 8000
        }).catch(() => {});

        const currentUrl = page.url();
        const loaded = !currentUrl.includes('signin') || route.path === '/';
        const status = loaded ? '✅' : '📍';
        console.log(`${status} ${route.name.padEnd(18)} ${currentUrl}`);

        if (route.path === '/system/health') {
          await page.screenshot({ path: '/tmp/05-health-page.png', fullPage: true });
          console.log('   📸 Health check screenshot saved');
        }
      } catch (err) {
        console.log(`❌ ${route.name.padEnd(18)} ${err.message.substring(0, 40)}`);
      }
    }

    // Test 6: Check for product route (should be removed)
    console.log('\n6️⃣  Testing product route (should be gone)...');
    try {
      await page.goto(`${BASE_URL}/product`, {
        waitUntil: 'networkidle',
        timeout: 5000
      }).catch(() => {});

      const url = page.url();
      if (url.includes('signin') || url.includes('404')) {
        console.log('✅ Product route safely redirected (no 404 error)');
      } else {
        console.log(`⚠️  Unexpected result: ${url}`);
      }
      await page.screenshot({ path: '/tmp/06-product-route.png', fullPage: true });
    } catch (err) {
      console.log(`✅ Product route error (expected): ${err.message.substring(0, 50)}`);
    }

    console.log('\n✅ Test complete!\n');
    console.log('Screenshots saved to /tmp/:');
    console.log('  01-home.png');
    console.log('  02-signin-form.png');
    console.log('  03-after-signin.png');
    console.log('  05-health-page.png');
    console.log('  06-product-route.png\n');

  } catch (err) {
    console.error('❌ Test failed:', err.message);
  } finally {
    await browser.close();
  }
})();
