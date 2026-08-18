import { chromium } from '/home/dev/.local/lib/node_modules/playwright/index.mjs';

const OUT = process.env.OUT;
const BASE = 'http://localhost:13000';
const browser = await chromium.launch();
const page = await browser.newPage();

await page.goto(`${BASE}/login`, { waitUntil: 'networkidle' });
await page.getByLabel(/e-?mail/i).fill('admin@betrieb.de');
await page.getByRole('textbox', { name: /passwort/i }).fill('QaLocalTest123!');
await Promise.all([
  page.waitForURL((url) => !url.pathname.includes('/login')),
  page.getByRole('button', { name: /anmelden|einloggen|login/i }).click(),
]);

await page.goto(`${BASE}/email/inbox`, { waitUntil: 'networkidle' });
const bodyText = await page.textContent('body');
const hasWarnung = /E-Mail-Abruf fehlgeschlagen/.test(bodyText);
console.log(hasWarnung ? 'PASS AC-5 Warnbanner sichtbar' : 'BUG AC-5 Warnbanner fehlt');
await page.screenshot({ path: `${OUT}/email-inbox-mit-warnung.png`, fullPage: true });

await browser.close();
