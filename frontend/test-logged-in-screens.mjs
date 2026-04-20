import { chromium } from 'playwright';

const BASE_URL = 'http://localhost:51735';
const BACKEND_URL = 'http://localhost:51734';

(async () => {
  const browser = await chromium.launch({ headless: false });
  const page = await browser.newPage();

  try {
    console.log('\n🚀 Testing TennetCTL Dashboard Screens\n');

    // Step 1: Sign up a test user via API
    console.log('1️⃣  Creating test user account...');
    const timestamp = Date.now();
    const testEmail = `testuser.${timestamp}@localhost.test`;
    const signupRes = await fetch(`${BACKEND_URL}/v1/auth/signup`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        email: testEmail,
        password: 'TestPassword123!@#',
        display_name: 'Test User'
      })
    });
    const signupData = await signupRes.json();

    if (!signupData.ok) {
      console.error('❌ Signup failed:', signupData.error);
      process.exit(1);
    }

    const token = signupData.data.token;
    const userId = signupData.data.user.id;
    console.log(`✅ User created: ${testEmail}`);
    console.log(`   Token: ${token.substring(0, 20)}...`);
    console.log(`   User ID: ${userId}\n`);

    // Step 2: Set localStorage with auth token
    console.log('2️⃣  Setting authentication token...');
    await page.goto(BASE_URL);
    await page.evaluate(token => {
      localStorage.setItem('auth_token', token);
      localStorage.setItem('user_id', 'test-user');
    }, token);
    console.log('✅ Auth token set in localStorage\n');

    // Step 3: Navigate to dashboard
    console.log('3️⃣  Loading dashboard...');
    await page.goto(BASE_URL, { waitUntil: 'networkidle', timeout: 10000 });
    const dashboardUrl = page.url();
    console.log(`✅ Navigated to: ${dashboardUrl}\n`);
    await page.screenshot({ path: '/tmp/screen-01-dashboard.png', fullPage: true });

    // Step 4: Check if logged in (look for navbar/sidebar)
    console.log('4️⃣  Verifying logged-in state...');
    const navbar = await page.locator('[role="navigation"]').first().isVisible().catch(() => false);
    const sidebar = await page.locator('aside').first().isVisible().catch(() => false);

    if (navbar || sidebar) {
      console.log('✅ Navigation found - user is logged in\n');

      // Get nav text to check for modules
      const navText = await page.locator('[role="navigation"], aside').first().innerText().catch(() => '');
      const modules = ['IAM', 'Audit', 'Vault', 'Notify', 'Monitoring', 'Feature Flags'];
      const foundModules = modules.filter(m => navText.toLowerCase().includes(m.toLowerCase()));

      console.log(`   Found ${foundModules.length}/${modules.length} modules in nav:`);
      foundModules.forEach(m => console.log(`   ✅ ${m}`));
      console.log();

      // Check for product_ops (should not be there)
      if (navText.toLowerCase().includes('product_ops') || navText.toLowerCase().includes('product ops')) {
        console.log('   ❌ product_ops still in navbar!');
      } else {
        console.log('   ✅ product_ops removed from navbar\n');
      }
    } else {
      console.log('⚠️  Not logged in - navbar/sidebar not found\n');
    }

    // Step 5: Navigate to each module and capture screenshot
    console.log('5️⃣  Testing core module screens...\n');
    const screens = [
      { path: '/iam', name: 'IAM Users' },
      { path: '/audit', name: 'Audit Log' },
      { path: '/vault', name: 'Vault Secrets' },
      { path: '/notify', name: 'Notify Templates' },
      { path: '/monitoring', name: 'Monitoring Dashboard' },
      { path: '/feature-flags', name: 'Feature Flags' },
      { path: '/system/health', name: 'System Health' },
    ];

    for (let i = 0; i < screens.length; i++) {
      const screen = screens[i];
      try {
        await page.goto(`${BASE_URL}${screen.path}`, {
          waitUntil: 'networkidle',
          timeout: 8000
        });

        const url = page.url();
        const isLoaded = url.includes(screen.path) && !url.includes('signin');

        if (isLoaded) {
          console.log(`✅ ${screen.name.padEnd(30)} loaded`);
          const filename = `/tmp/screen-${String(i + 2).padStart(2, '0')}-${screen.path.split('/').pop() || 'dashboard'}.png`;
          await page.screenshot({ path: filename, fullPage: true });
        } else {
          console.log(`❌ ${screen.name.padEnd(30)} failed - redirected to ${url.substring(BASE_URL.length)}`);
        }
      } catch (err) {
        console.log(`❌ ${screen.name.padEnd(30)} error - ${err.message.substring(0, 40)}`);
      }
    }

    console.log('\n✅ Logged-in screen testing complete!\n');
    console.log('Screenshots saved:');
    console.log('  /tmp/screen-01-dashboard.png');
    console.log('  /tmp/screen-02-iam.png');
    console.log('  /tmp/screen-03-audit.png');
    console.log('  /tmp/screen-04-vault.png');
    console.log('  /tmp/screen-05-notify.png');
    console.log('  /tmp/screen-06-monitoring.png');
    console.log('  /tmp/screen-07-feature-flags.png');
    console.log('  /tmp/screen-08-health.png\n');

  } catch (err) {
    console.error('❌ Test failed:', err.message);
    process.exit(1);
  } finally {
    await browser.close();
  }
})();
