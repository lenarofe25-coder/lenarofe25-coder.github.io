// Rend chaque SVG de build/svg en JPEG dans build/img (via Chromium/Playwright)
const { chromium } = require('playwright');
const fs = require('fs'), path = require('path');
(async () => {
  const root = path.resolve(__dirname, '..');
  const svgDir = path.join(root, 'build/svg'), out = path.join(root, 'build/img');
  fs.mkdirSync(out, { recursive: true });
  const only = process.argv.slice(2);
  const files = fs.readdirSync(svgDir).filter(f => f.endsWith('.svg') && (!only.length || only.includes(f.replace('.svg',''))));
  const fontDir = 'file://' + path.join(root, 'assets/fonts');
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1200, height: 1000 }, deviceScaleFactor: 1.3 });
  for (const f of files) {
    const dst = path.join(out, f.replace('.svg', '.jpg'));
    const svgPath = path.join(svgDir, f);
    if (!process.env.FORCE && fs.existsSync(dst) && fs.statSync(dst).mtimeMs > fs.statSync(svgPath).mtimeMs) continue;
    const svg = fs.readFileSync(svgPath, 'utf8');
    await page.setContent(`<html><head><style>@font-face{font-family:'Pinyon Script';src:url('${fontDir}/Pinyon-400.ttf')}body{margin:0}</style></head><body>${svg}</body></html>`, { waitUntil: 'load' });
    await page.screenshot({ path: dst, type: 'jpeg', quality: 80, clip: { x: 0, y: 0, width: 1200, height: 1000 } });
    process.stdout.write('.');
  }
  await browser.close();
  console.log(`\n${files.length} images`);
})();
