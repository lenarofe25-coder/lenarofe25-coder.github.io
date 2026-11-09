// node src/render.js <maquette|livre>  -> dist/<nom>.pdf + build/<nom>/pNNN.png (si PNG=1)
// Les fiches trop longues sont réduites légèrement (zoom) pour tenir sur la page.
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
  const rep = await p.evaluate(() => {
    const mm = 3.78, out = [];
    document.querySelectorAll('.page').forEach((pg, i) => {
      const fit = pg.querySelector('.fit');
      if (!fit) return;
      const limite = pg.getBoundingClientRect().bottom - 17 * mm;
      const bas = () => Math.max(...[...fit.querySelectorAll('*')].map(e => e.getBoundingClientRect().bottom));
      let z = 1;
      while (bas() > limite && z > 0.78) { z -= 0.02; fit.style.zoom = z.toFixed(2); }
      if (z < 1) out.push([i + 1, +z.toFixed(2), bas() > limite]);
    });
    return out;
  });
  const bad = rep.filter(r => r[2]);
  console.log(`pages ajustées : ${rep.length}, encore trop longues : ${bad.map(r => r[0]).join(', ') || 'aucune'}`);
  rep.filter(r => r[1] < 0.88).forEach(r => console.log('  page', r[0], 'zoom', r[1]));
  if (process.env.PNG) {
    const outDir = path.join(root, 'build', name);
    fs.mkdirSync(outDir, { recursive: true });
    await p.addStyleTag({ content: '.page{margin:0!important;box-shadow:none!important}' });
    const els = await p.$$('.page');
    const only = process.env.PAGES ? process.env.PAGES.split(',').map(Number) : null;
    for (let i = 0; i < els.length; i++) {
      if (only && !only.includes(i + 1)) continue;
      await els[i].screenshot({ path: path.join(outDir, `p${String(i + 1).padStart(3, '0')}.png`) });
    }
  }
  fs.mkdirSync(path.join(root, 'dist'), { recursive: true });
  const out = process.env.OUT || path.join(root, 'dist', name + '.pdf');
  await p.pdf({ path: out, format: 'A4', printBackground: true, preferCSSPageSize: true, tagged: true, outline: true });
  await b.close();
  console.log('PDF ->', out);
})();
