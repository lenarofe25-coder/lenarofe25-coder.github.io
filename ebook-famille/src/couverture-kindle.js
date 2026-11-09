// Rend la couverture Kindle en JPEG 1600 × 2560 : node src/couverture-kindle.js
const { chromium } = require('playwright');
const path = require('path');
const fs = require('fs');

(async () => {
  const root = path.resolve(__dirname, '..');
  const out = path.join(root, 'dist', 'kindle');
  fs.mkdirSync(out, { recursive: true });
  const b = await chromium.launch();
  const p = await b.newPage({ viewport: { width: 1600, height: 2560 }, deviceScaleFactor: 1 });
  await p.goto('file://' + path.join(root, 'src', 'couverture-kindle.html'), { waitUntil: 'networkidle' });
  await p.evaluate(() => document.fonts.ready);
  await p.screenshot({ path: path.join(out, 'couverture-kindle.jpg'), type: 'jpeg', quality: 92 });
  await b.close();
  console.log('couverture ->', path.join(out, 'couverture-kindle.jpg'));
})();
