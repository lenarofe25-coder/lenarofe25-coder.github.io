// Vérifie dans un vrai navigateur (Chromium) que chaque meme actif s'affiche, avec la même
// politique de referrer que le jeu. Écrit server/memes/report/navigateur.json et une capture.
// Usage (réseau requis) : node server/memes/check-browser.mjs
import { chromium } from 'playwright';
import { readFileSync, writeFileSync } from 'node:fs';

const root = new URL('../../', import.meta.url);
const memes = JSON.parse(readFileSync(new URL('jeu/data/memes.json', root))).memes.filter((m) => m.active);
const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1400, height: 900 } });
const esc = (s) => s.replace(/"/g, '&quot;');
await page.setContent(`<!doctype html><style>body{margin:0;display:grid;grid-template-columns:repeat(14,100px);gap:0}img{width:100px;height:100px;object-fit:cover}</style>
  ${memes.map((m) => `<img data-id="${esc(m.id)}" src="${esc(m.image)}" referrerpolicy="no-referrer">`).join('')}`);
await page.waitForFunction(() => [...document.images].every((i) => i.complete), null, { timeout: 180_000 }).catch(() => {});
const results = await page.$$eval('img', (imgs) => imgs.map((i) => ({ id: i.dataset.id, ok: i.complete && i.naturalWidth > 0, w: i.naturalWidth, h: i.naturalHeight })));
await page.screenshot({ path: new URL('server/memes/report/navigateur.jpg', root).pathname, fullPage: true, type: 'jpeg', quality: 60 });
await browser.close();
const failed = results.filter((r) => !r.ok);
writeFileSync(new URL('server/memes/report/navigateur.json', root), JSON.stringify({ checked: results.length, displayed: results.length - failed.length, failed }, null, 1) + '\n');
console.log(`Navigateur : ${results.length - failed.length}/${results.length} memes affichés.`);
if (failed.length) console.log('Échecs :', failed.map((f) => f.id).join(', '));
