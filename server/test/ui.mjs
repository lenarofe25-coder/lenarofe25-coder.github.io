// Parcours navigateur réel : 3 joueuses (2 iPhone, 1 desktop) jouent une partie complète.
// Prérequis : `npm run dev` (port 8787) et un serveur statique du site sur le port 8080.
// Usage : node test/ui.mjs [dossier-captures]
import { createRequire } from 'node:module';
// Playwright est installé globalement dans l'environnement de test (résolu via require).
const { chromium, devices } = createRequire(import.meta.url)('playwright');
import assert from 'node:assert/strict';

const offline = process.env.MDR_OFFLINE_IMAGES === '1';
const SITE = process.env.MDR_SITE || 'http://localhost:8080/jeu/';
const OUT = process.argv[2] || '.';
const browser = await chromium.launch();
const errors = [];
const mk = async (name, device) => {
  const ctx = await browser.newContext(device);
  const page = await ctx.newPage();
  // Sans accès réseau aux sources, on sert des images de remplacement aux proportions variées
  // (larges, carrées, très hautes) pour reproduire la mise en page avec de vrais memes.
  if (offline) {
    await page.route(/^https:\/\/(?!127\.0\.0\.1|localhost)[^/]*\/.*\.(jpe?g|png|webp|gif)|memebo|imagekit|memegen|imgflip/i, (route) => {
      const n = [...route.request().url()].reduce((h, c) => (h * 31 + c.charCodeAt(0)) >>> 0, 7);
      const [w, h] = [[1200, 600], [500, 500], [400, 1300], [800, 1000], [1600, 400]][n % 5];
      const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="${w}" height="${h}"><rect width="100%" height="100%" fill="hsl(${n % 360},60%,60%)"/><text x="20" y="60" font-size="48">${w}x${h}</text></svg>`;
      route.fulfill({ status: 200, contentType: 'image/svg+xml', body: svg });
    });
  }
  page.on('pageerror', (e) => errors.push(`${name}: ${e.message}`));
  page.on('console', (m) => m.type() === 'error' && errors.push(`${name} console: ${m.text()}`));
  return { name, ctx, page };
};
// Avant chaque capture, on attend que les images visibles aient fini de charger.
const shot = async (p, file) => {
  await p.page.waitForFunction(() => [...document.images].filter((i) => i.getBoundingClientRect().top < innerHeight).every((i) => i.complete), null, { timeout: 15000 }).catch(() => {});
  await p.page.screenshot({ path: `${OUT}/${file}.png`, fullPage: false });
};
const noHScroll = async (p) => assert.ok(await p.page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth + 1), `${p.name} : débordement horizontal`);

const a = await mk('Alice', devices['iPhone 13']);
const b = await mk('Bianca', devices['iPhone SE']);
const c = await mk('Chloé', { viewport: { width: 1366, height: 860 } });

// Accueil + création
await a.page.goto(SITE);
await a.page.waitForSelector('.wordmark');
await a.page.waitForSelector('.fan .card').catch(() => {});
await noHScroll(a);
await shot(a, '01-accueil-mobile');
await c.page.goto(SITE);
await shot(c, '01-accueil-desktop');
await a.page.click('[data-act="create"]');
assert.match(await a.page.textContent('#homeError'), /pseudo/);
await a.page.fill('#name', 'Alice');
await a.page.click('button[data-act="create"]');
await a.page.waitForSelector('.code-card .code');
const code = (await a.page.textContent('.code-card .code')).trim();
assert.match(code, /^[A-Z]{3}\d{3}$/);

// Code invalide puis lien d'invitation
await b.page.goto(SITE);
await b.page.fill('#name', 'Bianca');
await b.page.fill('#code', 'ZZZ999');
await b.page.click('button[data-act="join"]');
await b.page.waitForFunction(() => !document.getElementById('homeError').hidden);
assert.match(await b.page.textContent('#homeError'), /n’existe pas/);
await b.page.goto(`${SITE}?code=${code}`);
await b.page.waitForSelector('[data-part="peek"] b');
await b.page.fill('#name', 'alice');
await b.page.click('button[data-act="join"]');
await b.page.waitForFunction(() => /déjà pris/.test(document.getElementById('homeError').textContent));
await b.page.fill('#name', 'Bianca');
await b.page.click('button[data-act="join"]');
await b.page.waitForSelector('.code-card');
await c.page.goto(`${SITE}?code=${code}`);
await c.page.fill('#name', 'Chloé');
await c.page.click('button[data-act="join"]');
await c.page.waitForSelector('.code-card');

// Statut prête synchronisé, lancement par l'hôte
await a.page.waitForFunction(() => document.querySelectorAll('.player').length === 3);
assert.ok(await a.page.isDisabled('[data-act="start"]'));
await b.page.click('[data-act="ready"]');
await c.page.click('[data-act="ready"]');
await a.page.waitForFunction(() => document.querySelectorAll('.badge.ready').length === 2);
await noHScroll(a);
await noHScroll(b);
await shot(a, '02-salon-mobile');
await a.page.selectOption('#cfg-pickSeconds', '90');
await a.page.selectOption('#cfg-resultsSeconds', '0');
await b.page.waitForFunction(() => document.body.textContent.includes('90 s'));
await a.page.click('[data-act="start"]');

const players = [a, b, c];
for (let n = 1; n <= 10; n++) {
  for (const p of players) await p.page.waitForFunction((n) => document.querySelector('.round-pill')?.textContent.startsWith(`Manche ${n}`) && document.querySelectorAll('[data-grid] .card').length === 10, n);
  const situations = await Promise.all(players.map((p) => p.page.textContent('.prompt h1')));
  assert.equal(new Set(situations).size, 1, 'situation différente selon les joueuses');
  if (n === 1) {
    await a.page.waitForTimeout(700);
    await shot(a, '03-main-mobile');
    await shot(c, '03-main-desktop');
    await noHScroll(a);
    await noHScroll(b);
    // Changer d'avis avant de valider
    await a.page.click('[data-grid] .card-slot:nth-child(2) .card');
    await a.page.click('[data-grid] .card-slot:nth-child(4) .card');
    // La loupe agrandit le meme sans le sélectionner.
    await a.page.click('[data-grid] .card-slot:nth-child(1) .zoom');
    await a.page.waitForSelector('dialog[open] .zoom-img');
    await shot(a, '04b-loupe-mobile');
    await a.page.click('dialog[open] [data-act="close-sheet"]');
    assert.equal(await a.page.locator('.card.is-selected').count(), 1);
    assert.equal(await a.page.locator('.card.is-selected').count(), 1);
    await shot(a, '04-selection-mobile');
  }
  if (n === 2) {
    // Reconnexion après rechargement de la page : même main.
    const before = await b.page.$$eval('[data-grid] .card', (els) => els.map((e) => e.getAttribute('aria-label')));
    await b.page.reload();
    await b.page.waitForFunction(() => document.querySelectorAll('[data-grid] .card').length === 10);
    const after = await b.page.$$eval('[data-grid] .card', (els) => els.map((e) => e.getAttribute('aria-label')));
    assert.deepEqual(after, before);
  }
  for (const p of players) {
    await p.page.click(`[data-grid] .card-slot:nth-child(${(n % 10) + 1}) .card`);
    try {
      await p.page.click('[data-act="confirm-pick"]', { timeout: 5000 });
    } catch (e) {
      await p.page.screenshot({ path: `${OUT}/echec-${p.name}-${n}.png` });
      const sel = await p.page.$$eval('.card.is-selected', (els) => els.length);
      throw new Error(`manche ${n}, ${p.name} : validation impossible (cartes sélectionnées : ${sel})`);
    }
  }
  if (n === 1) {
    await players[0].page.waitForTimeout(100);
  }
  for (const p of players) await p.page.waitForFunction(() => document.querySelectorAll('[data-grid] .card').length === 3 && document.querySelector('.status strong')?.textContent.includes('Vote'));
  if (n === 1) {
    await a.page.waitForTimeout(900);
    await shot(a, '05-vote-mobile');
    await shot(c, '05-vote-desktop');
  }
  // Sa propre carte est désactivée ; on vote pour la première autre.
  for (const p of players) {
    assert.equal(await p.page.locator('[data-grid] .card.is-mine').count(), 1);
    assert.ok(await p.page.locator('[data-grid] .card.is-mine').isDisabled());
    await p.page.click('[data-grid] .card:not(.is-mine) >> nth=0');
    await p.page.click('[data-act="confirm-vote"]');
  }
  for (const p of players) await p.page.waitForSelector('.result-card');
  if (n === 1) {
    await a.page.waitForTimeout(900);
    await shot(a, '06-resultats-mobile');
    await a.page.evaluate(() => window.scrollTo(0, document.body.scrollHeight));
    await shot(a, '06b-classement-mobile');
    await shot(c, '06-resultats-desktop');
  }
  const scores = await Promise.all(players.map((p) => p.page.$$eval('.standings .pts', (els) => els.map((e) => parseInt(e.textContent, 10)).reduce((x, y) => x + y, 0))));
  assert.equal(new Set(scores).size, 1, 'classements différents selon les joueuses');
  await a.page.click('[data-act="next"]');
}

for (const p of players) await p.page.waitForSelector('.podium h1');
await a.page.waitForTimeout(1200);
await shot(a, '07-fin-mobile');
await shot(c, '07-fin-desktop');
assert.equal(await a.page.locator('.history-item').count(), 10);
await noHScroll(a);

// Image cassée : la description remplace l'image.
await c.page.evaluate(() => {
  const img = document.querySelector('.card-img');
  if (img) img.src = 'cards/img/nexiste-pas.svg';
});
await c.page.waitForTimeout(500);

// Rejouer → retour au salon pour tout le monde
await a.page.click('[data-act="replay"]');
for (const p of players) await p.page.waitForSelector('.code-card');

// Quitter : retour à l'accueil
await c.page.click('[data-act="leave"]');
await c.page.click('[data-act="leave-confirm"]');
await c.page.waitForSelector('.wordmark');
await a.page.waitForFunction(() => document.querySelectorAll('.player').length === 2);

await browser.close();
// Les 404/409 provoqués exprès (code inconnu, pseudo pris, image cassée) ne sont pas des erreurs.
// Les 404/409 provoqués exprès (code inconnu, pseudo pris, image cassée) ne sont pas des erreurs ;
// MDR_OFFLINE_IMAGES=1 : images des memes injoignables depuis l'environnement de test (réseau filtré).
const relevant = errors.filter((e) => !/Failed to load resource: the server responded with a status of (404|409)/.test(e) && !(offline && /ERR_|Failed to load resource/.test(e)));
assert.deepEqual(relevant, [], relevant.join('\n'));
console.log(`OK : partie complète à 3 dans le navigateur, salle ${code}`);
