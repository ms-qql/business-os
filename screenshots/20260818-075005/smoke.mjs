import { chromium } from '/home/dev/.local/lib/node_modules/playwright/index.mjs';
import fs from 'node:fs';

const OUT = process.env.OUT;
const BASE = 'http://localhost:13000';
const results = [];
const consoleErrors = [];

function log(status, name, detail) {
  results.push({ status, name, detail });
  console.log(`${status} ${name} ${detail || ''}`);
}

const browser = await chromium.launch();

async function newPage() {
  const page = await browser.newPage();
  page.on('console', (msg) => {
    if (msg.type() === 'error') consoleErrors.push(`[${page.url()}] ${msg.text()}`);
  });
  page.on('pageerror', (err) => consoleErrors.push(`[${page.url()}] pageerror: ${err.message}`));
  return page;
}

// 1) Login-Seite Render @ 4 Viewports
const viewports = [
  { name: 'mobile', width: 375, height: 812 },
  { name: 'tablet', width: 768, height: 1024 },
  { name: 'laptop', width: 1024, height: 768 },
  { name: 'desktop', width: 1440, height: 900 },
];
for (const vp of viewports) {
  const page = await newPage();
  await page.setViewportSize({ width: vp.width, height: vp.height });
  try {
    const resp = await page.goto(`${BASE}/login`, { waitUntil: 'networkidle', timeout: 15000 });
    log(resp && resp.ok() ? 'PASS' : 'BUG', `login-render-${vp.name}`, `HTTP ${resp?.status()}`);
    await page.screenshot({ path: `${OUT}/login-${vp.name}.png` });
  } catch (e) {
    log('BUG', `login-render-${vp.name}`, String(e));
  }
  await page.close();
}

// 2) Echter Login-Flow (Next.js = echtes DOM, keine CanvasKit-Limitation)
const page = await newPage();
try {
  await page.goto(`${BASE}/login`, { waitUntil: 'networkidle', timeout: 15000 });
  await page.getByLabel(/e-?mail/i).fill('admin@betrieb.de');
  await page.getByRole('textbox', { name: /passwort/i }).fill('QaLocalTest123!');
  await Promise.all([
    page.waitForURL((url) => !url.pathname.includes('/login'), { timeout: 15000 }),
    page.getByRole('button', { name: /anmelden|einloggen|login/i }).click(),
  ]);
  log('PASS', 'login-flow', page.url());
  await page.screenshot({ path: `${OUT}/after-login.png` });
} catch (e) {
  log('BUG', 'login-flow', String(e));
  await page.screenshot({ path: `${OUT}/login-flow-fail.png` }).catch(() => {});
}

// 3) Postfach-Einstellungen (Inhaber-only, PROJ-4)
try {
  await page.goto(`${BASE}/einstellungen/postfach`, { waitUntil: 'networkidle', timeout: 15000 });
  const bodyText = await page.textContent('body');
  log(bodyText && bodyText.length > 0 ? 'PASS' : 'BUG', 'postfach-einstellungen-render', `len=${bodyText?.length}`);
  await page.screenshot({ path: `${OUT}/postfach-einstellungen.png`, fullPage: true });
} catch (e) {
  log('BUG', 'postfach-einstellungen-render', String(e));
}

// 4) Email-Inbox (PROJ-4)
try {
  await page.goto(`${BASE}/email/inbox`, { waitUntil: 'networkidle', timeout: 15000 });
  const bodyText = await page.textContent('body');
  log(bodyText && bodyText.length > 0 ? 'PASS' : 'BUG', 'email-inbox-render', `len=${bodyText?.length}`);
  await page.screenshot({ path: `${OUT}/email-inbox.png`, fullPage: true });
} catch (e) {
  log('BUG', 'email-inbox-render', String(e));
}

await page.close();
await browser.close();

const report = [
  `# E2E Smoke Report — PROJ-4 (Business OS)`,
  ``,
  `**Datum:** ${new Date().toISOString()}`,
  `**Stack:** lokaler Docker-Compose (backend :18000, frontend :13000)`,
  ``,
  `## Ergebnisse`,
  ``,
  `| Status | Test | Detail |`,
  `|---|---|---|`,
  ...results.map((r) => `| ${r.status} | ${r.name} | ${r.detail ?? ''} |`),
  ``,
  `## Console-/Page-Errors`,
  ``,
  consoleErrors.length ? consoleErrors.map((e) => `- ${e}`).join('\n') : '_keine_',
  ``,
].join('\n');

fs.writeFileSync(`${OUT}/REPORT.md`, report);
console.log('--- REPORT ---');
console.log(report);
