// Captures PNG de pages choisies du HTML (contrôle visuel) : node src/preview.js book 1 5 36
const { chromium } = require('playwright');
const path = require('path');
const fs = require('fs');
(async () => {
  const root = path.resolve(__dirname, '..');
  const [name, ...nums] = process.argv.slice(2);
  const outDir = process.env.OUT || path.join(root, 'build', 'preview');
  fs.mkdirSync(outDir, { recursive: true });
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 900, height: 1200 }, deviceScaleFactor: +(process.env.SCALE || 1) });
  await page.goto('file://' + path.join(root, 'build', name + '.html'), { waitUntil: 'networkidle' });
  await page.emulateMedia({ media: 'print' });
  await page.addStyleTag({ content: '.page{margin:0!important;box-shadow:none!important}' });
  await page.evaluate(() => document.fonts.ready);
  // même ajustement que render_pdf.js
  await page.evaluate(() => {
    document.querySelectorAll('.page').forEach(pg => pg.querySelectorAll('.fit').forEach(fit => {
      const over = () => fit.scrollHeight > fit.clientHeight + 1;
      const notes = pg.querySelector('.box.notes');
      if (notes && (over() || notes.getBoundingClientRect().height < 26 * 3.78)) notes.remove();
      let f = 1;
      while (over() && f > 0.8) { f -= 0.02; pg.style.setProperty('--fs', f.toFixed(2)); }
    }));
  });
  const els = await page.$$('.page');
  for (const n of nums) {
    await els[+n - 1].screenshot({ path: path.join(outDir, `p${String(n).padStart(3, '0')}.png`) });
  }
  await browser.close();
})();
