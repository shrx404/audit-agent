const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch();
  const context = await browser.newContext();
  const page = await context.newPage();

  page.on('requestfailed', request => {
    console.log(`REQUEST_FAILED: ${request.url()} - ${request.failure().errorText}`);
  });
  
  page.on('console', msg => {
    if (msg.type() === 'error') {
      console.log(`CONSOLE_ERROR: ${msg.text()}`);
    }
  });

  await page.goto('http://localhost:3000/');
  
  // Wait for the UI
  await page.waitForSelector('.welcome-mark');
  
  // Fill text
  await page.fill('textarea', 'test question');
  await page.click('.send-button');
  
  // Wait a bit
  await page.waitForTimeout(3000);
  
  await browser.close();
})();
