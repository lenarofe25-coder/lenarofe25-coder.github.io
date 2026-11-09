// node src/render.js maquette  -> dist/maquette.pdf + build/pNN.png
const { chromium } = require('playwright');
const path = require('path');
const fs = require('fs');

(async () => {
  const root = path.resolve(__dirname, '..');
  const name = process.argv[2] || 'maquette';
  const b = await chromium.launch();
  const p = await b.newPage({ viewport: { width: 900, height: 1200 }, deviceScaleFactor: +(process.env.SCALE || 1.5) });
  await p.goto('file://' + path.join(root, 'src', name + '.html'), { waitUntil: 'networkidle' });
  await p.evaluate(() => document.fonts.ready);
  await p.emulateMedia({ media: 'print' });
  const over = await p.evaluate(() => [...document.querySelectorAll('.page')].map((pg, i) => {
    const r = pg.getBoundingClientRect();
    const bad = [];
    pg.querySelectorAll('.inner *, .col *, .how *, .tgrid *, .kids *').forEach(e => {
      const q = e.getBoundingClientRect();
      if (q.height && (q.bottom > r.bottom - 14 * 3.78 || q.right > r.right + 1)) bad.push(e.className || e.tagName);
    });
    return [i + 1, bad.slice(0, 5)];
  }).filter(x => x[1].length));
  console.log('trop près du bas:', JSON.stringify(over));
  const outDir = path.join(root, 'build', name);
  fs.mkdirSync(outDir, { recursive: true });
  await p.addStyleTag({ content: '.page{margin:0!important;box-shadow:none!important}' });
  const els = await p.$$('.page');
  for (let i = 0; i < els.length; i++) {
    await els[i].screenshot({ path: path.join(outDir, `p${String(i + 1).padStart(2, '0')}.png`) });
  }
  fs.mkdirSync(path.join(root, 'dist'), { recursive: true });
  await p.pdf({ path: path.join(root, 'dist', name + '.pdf'), format: 'A4', printBackground: true, preferCSSPageSize: true });
  await b.close();
})();
