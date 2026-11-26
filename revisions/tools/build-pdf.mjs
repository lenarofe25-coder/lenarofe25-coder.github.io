// Génère planning-e6-sisr.pdf (A4 paysage, version vierge) et contrôle que rien ne déborde.
// Usage (depuis revisions/) : node tools/build-pdf.mjs
import { createServer } from 'node:http';
import { readFile } from 'node:fs/promises';
import { extname, join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';
import { createRequire } from 'node:module';

const require = createRequire(import.meta.url);
const { chromium } = require('playwright');
const ROOT = join(dirname(fileURLToPath(import.meta.url)), '..');
const TYPES = { '.html': 'text/html', '.css': 'text/css', '.js': 'text/javascript', '.woff2': 'font/woff2', '.pdf': 'application/pdf' };

const server = createServer(async (req, res) => {
  const path = decodeURIComponent(new URL(req.url, 'http://x').pathname);
  try {
    const body = await readFile(join(ROOT, path === '/' ? 'index.html' : path));
    res.writeHead(200, { 'content-type': TYPES[extname(path)] || 'application/octet-stream' });
    res.end(body);
  } catch { res.writeHead(404); res.end(); }
}).listen(0);
const base = `http://127.0.0.1:${server.address().port}/`;

const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1400, height: 1000 } });
const errors = [];
page.on('pageerror', e => errors.push(e.message));
page.on('console', m => { if (m.type() === 'error' || m.type() === 'warning') errors.push(m.text()); });
await page.goto(base + 'index.html?vierge', { waitUntil: 'networkidle' });
await page.waitForFunction(() => document.documentElement.dataset.ready === '1');
await page.emulateMedia({ media: 'print' });
await page.waitForTimeout(300);

// contrôle des débordements en géométrie d'impression
const report = await page.evaluate(() => {
  const out = [];
  document.querySelectorAll('.page').forEach((p, i) => {
    const pr = p.getBoundingClientRect();
    const name = `p.${i + 1} ${p.dataset.label}`;
    if (Math.abs(pr.width - 1122.5) > 2 || Math.abs(pr.height - 793.7) > 2) out.push(`${name} : taille ${pr.width.toFixed(1)}×${pr.height.toFixed(1)} px`);
    p.querySelectorAll('.card, .exo, .colstack, .body, .write, .ttable, .trow > div, .info, .day').forEach(el => {
      if (el.scrollHeight > el.clientHeight + 2 && getComputedStyle(el).overflow !== 'visible' || el.scrollHeight > el.clientHeight + 2 && el.matches('.colstack, .body, .card, .exo, .day'))
        out.push(`${name} : débordement ${el.className} (+${el.scrollHeight - el.clientHeight}px)`);
    });
    const outside = [...p.querySelectorAll('*')].filter(el => { const r = el.getBoundingClientRect(); return r.width && (r.bottom > pr.bottom + 0.5 || r.right > pr.right + 0.5); });
    if (outside.length) out.push(`${name} : ${outside.length} éléments sortent de la feuille`);
  });
  return { pages: document.querySelectorAll('.page').length, issues: [...new Set(out)] };
});

await page.pdf({ path: join(ROOT, 'planning-e6-sisr.pdf'), preferCSSPageSize: true, printBackground: true });
await browser.close();
server.close();

console.log(`${report.pages} pages`);
if (errors.length) console.log('Erreurs console :\n- ' + errors.join('\n- '));
if (report.issues.length) { console.log('Problèmes de mise en page :\n- ' + report.issues.join('\n- ')); process.exitCode = 1; }
else console.log('Mise en page OK : aucune feuille ne déborde.');
