/* QA helper: screenshots each case at key pipeline steps against a local preview server. */
import { chromium } from 'playwright';
import fs from 'fs';

const OUT = '/tmp/polis_case_shots';
fs.mkdirSync(OUT, { recursive: true });
const STEPS = [0, 2, 3, 5, 7];

const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1680, height: 1000 } });
const errors = [];
page.on('console', m => { if (m.type() === 'error') errors.push(m.text()); });
page.on('pageerror', e => errors.push(String(e)));
await page.goto('http://localhost:4173/', { waitUntil: 'networkidle' });
await page.waitForTimeout(4000);

for (const c of ['chicago', 'suzhou', 'london']) {
  await page.click(`.caseBtn:text-is("${c}")`);
  await page.waitForTimeout(3500);
  for (const s of STEPS) {
    await page.locator('.timeline input[type=range]').fill(String(s));
    await page.waitForTimeout(2600);
    await page.screenshot({ path: `${OUT}/${c}_step${s}.png` });
  }
  await page.locator('.timeline input[type=range]').fill('0');
  await page.waitForTimeout(800);
}
console.log('console errors:', errors.length ? errors.slice(0, 10) : 'none');
await browser.close();
