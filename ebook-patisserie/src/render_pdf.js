// HTML -> PDF (A4) avec ajustement automatique du corps de texte des pages trop pleines.
const { chromium } = require('playwright');
const path = require('path'), fs = require('fs');
(async () => {
  const root = path.resolve(__dirname, '..');
  const name = process.argv[2] || 'book';
  const out = process.argv[3] || path.join(root, 'dist', name + '.pdf');
  const browser = await chromium.launch();
  const page = await browser.newPage();
  await page.goto('file://' + path.join(root, 'build', name + '.html'), { waitUntil: 'networkidle' });
  await page.evaluate(() => document.fonts.ready);
  await page.emulateMedia({ media: 'print' });
  const report = await page.evaluate(() => {
    const res = [];
    const pages = [...document.querySelectorAll('.page')];
    pages.forEach((pg, i) => {
      const fits = pg.querySelectorAll('.fit');
      fits.forEach(fit => {
        const over = () => fit.scrollHeight > fit.clientHeight + 1 || [...fit.querySelectorAll('.side,.cols,.steps,.grid')].some(e => e.scrollHeight > e.clientHeight + 1 && getComputedStyle(e).overflow !== 'visible');
        let fs = 1;
        // retire d'abord le bloc « notes » s'il manque de place
        const notes = pg.querySelector('.box.notes');
        if (notes && (over() || notes.getBoundingClientRect().height < 26 * 3.78)) notes.remove();
        while (over() && fs > 0.8) { fs -= 0.02; pg.style.setProperty('--fs', fs.toFixed(2)); }
        if (fs < 1) res.push({ page: i + 1, fs: +fs.toFixed(2), still: over() });
      });
    });
    return res;
  });
  const bad = report.filter(r => r.still);
  console.log(`ajustés: ${report.length}, débordements restants: ${bad.length}`);
  bad.forEach(b => console.log('  DÉBORDE page', b.page));
  report.filter(r => !r.still && r.fs < 0.9).forEach(b => console.log('  page', b.page, 'réduite à', b.fs));
  fs.mkdirSync(path.dirname(out), { recursive: true });
  await page.pdf({ path: out, format: 'A4', printBackground: true, preferCSSPageSize: true, tagged: true, outline: true });
  await browser.close();
  console.log('PDF ->', out);
})();
