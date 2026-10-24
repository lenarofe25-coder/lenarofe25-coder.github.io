// Génère les bibliothèques du jeu à partir des sources éditoriales :
//   jeu/data/situations.json, jeu/data/cards.json, jeu/data/categories.json, jeu/cards/img/*.svg
// Les identifiants déjà publiés sont conservés (correspondance par clé de déduplication) ;
// une entrée retirée de la source reste dans le fichier avec active: false.
// Usage : npm run content   (ajouter --check pour vérifier sans écrire)
import { readFileSync, writeFileSync, mkdirSync, existsSync, readdirSync, unlinkSync } from 'node:fs';
import { createRequire } from 'node:module';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';
import situationsSrc from './content-src/situations.mjs';
import * as cardsSrc from './content-src/cards.mjs';
import { validateLibrary } from '../src/content.js';

const require = createRequire(import.meta.url);
const root = join(dirname(fileURLToPath(import.meta.url)), '..', '..');
const dataDir = join(root, 'jeu', 'data');
const imgDir = join(root, 'jeu', 'cards', 'img');
const checkOnly = process.argv.includes('--check');

const CATEGORIES = {
  amitie: { label: 'Amitié', emoji: '👯‍♀️' },
  couple: { label: 'Couple & crush', emoji: '💘' },
  gene: { label: 'Situations gênantes', emoji: '🫣' },
  'ecole-travail': { label: 'École & travail', emoji: '📚' },
  famille: { label: 'Famille', emoji: '🏡' },
  soirees: { label: 'Soirées', emoji: '🪩' },
  reseaux: { label: 'Réseaux & messages', emoji: '📱' },
  absurde: { label: 'Humour absurde', emoji: '🦆' },
  excuses: { label: 'Mensonges & excuses', emoji: '🤥' },
  'humour-noir': { label: 'Humour noir', emoji: '💀', optIn: true },
  internet: { label: 'Culture Internet', emoji: '🌐' },
  reactions: { label: 'Réactions', emoji: '😱' },
  'classiques-internet': { label: 'Classiques d’Internet', emoji: '✨' },
  cultes: { label: 'Expressions cultes', emoji: '🗣️' },
};

const FLUENT_SOURCE = {
  name: 'Fluent Emoji (Microsoft)',
  url: 'https://github.com/microsoft/fluentui-emoji',
  license: 'MIT',
  note: 'Illustration MIT ; légende originale écrite pour MDR',
};
const ORIGINAL_SOURCE = { name: 'MDR (texte original)', license: 'Contenu original du projet' };

// ── outils ──────────────────────────────────────────────────
export const textKey = (s) =>
  s
    .normalize('NFD')
    .replace(/[̀-ͯ]/g, '')
    .toLowerCase()
    .replace(/[’']/g, ' ')
    .replace(/[^a-z0-9 ]+/g, ' ')
    .replace(/\s+/g, ' ')
    .trim();

const STOP = new Set('a au aux de des du d l la le les un une et en est que qui quand tu te ton ta tes t ma mon mes me je j il elle on ce c ca s se sa son ses pour pas ne n y dans sur avec plus tout vous nous'.split(' '));
const tokens = (s) => new Set(textKey(s).split(' ').filter((w) => w.length > 1 && !STOP.has(w)));
const jaccard = (a, b) => {
  let inter = 0;
  for (const x of a) if (b.has(x)) inter++;
  return inter / (a.size + b.size - inter || 1);
};

function nearDuplicates(items, threshold) {
  const toks = items.map((it) => tokens(it.text));
  const pairs = [];
  for (let i = 0; i < items.length; i++)
    for (let j = i + 1; j < items.length; j++) {
      const score = jaccard(toks[i], toks[j]);
      if (score >= threshold) pairs.push([items[i], items[j], score]);
    }
  return pairs;
}

const readJson = (file, fallback) => (existsSync(file) ? JSON.parse(readFileSync(file, 'utf8')) : fallback);

// Conserve les identifiants publiés : clé → id ; nouveaux identifiants à la suite.
function assignIds(entries, previous, prefix) {
  const byKey = new Map(previous.map((p) => [p.dedupeKey, p]));
  let max = Math.max(0, ...previous.map((p) => Number(p.id.split('-').pop()) || 0));
  const seen = new Set();
  const out = entries.map((e) => {
    seen.add(e.dedupeKey);
    const id = byKey.get(e.dedupeKey)?.id || `${prefix}-${String(++max).padStart(4, '0')}`;
    return { id, ...e };
  });
  for (const p of previous) if (!seen.has(p.dedupeKey)) out.push({ ...p, active: false });
  return out;
}

// ── illustrations ───────────────────────────────────────────
const iconSet = require('@iconify-json/fluent-emoji/icons.json');
function resolveIcon(name) {
  let n = name;
  for (let i = 0; i < 5 && !iconSet.icons[n] && iconSet.aliases?.[n]; i++) n = iconSet.aliases[n].parent;
  const icon = iconSet.icons[n];
  if (!icon) return null;
  const w = icon.width || iconSet.width || 16;
  const h = icon.height || iconSet.height || 16;
  return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="${icon.left || 0} ${icon.top || 0} ${w} ${h}" width="${w * 4}" height="${h * 4}">${icon.body}</svg>\n`;
}

const errors = [];
const warnings = [];
const usedIcons = new Map();
const iconFor = (name) => {
  if (!usedIcons.has(name)) {
    const svg = resolveIcon(name);
    if (!svg) errors.push(`illustration introuvable dans Fluent Emoji : ${name}`);
    else if (svg.length < 200) errors.push(`illustration suspecte (trop petite) : ${name}`);
    usedIcons.set(name, svg);
  }
  return `cards/img/${name}.svg`;
};

// Illustrations utilisées par l'interface elle-même (accueil, fin de partie, erreurs).
for (const name of ['face-with-tears-of-joy', 'face-with-spiral-eyes', 'trophy', 'handshake', 'skull', 'face-holding-back-tears']) iconFor(name);

// ── situations ──────────────────────────────────────────────
const prevSituations = readJson(join(dataDir, 'situations.json'), { situations: [] }).situations;
const situationEntries = [];
for (const [category, list] of Object.entries(situationsSrc)) {
  if (!CATEGORIES[category]) errors.push(`catégorie de situation inconnue : ${category}`);
  for (const text of list) situationEntries.push({ text: text.trim(), category, active: true, dedupeKey: textKey(text) });
}
const situations = assignIds(situationEntries, prevSituations, 's');

// ── cartes ──────────────────────────────────────────────────
const prevCards = readJson(join(dataDir, 'cards.json'), { cards: [] }).cards;
const cardEntries = [];
for (const [category, list] of Object.entries(cardsSrc.text)) {
  for (const t of list) cardEntries.push({ type: 'text', text: t.trim(), category, source: ORIGINAL_SOURCE, active: true, dedupeKey: textKey(t) });
}
for (const [icon, category, alt] of cardsSrc.image) {
  cardEntries.push({ type: 'image', image: iconFor(icon), alt, category, source: { ...FLUENT_SOURCE, note: 'Illustration MIT' }, active: true, dedupeKey: `img:${icon}` });
}
for (const [icon, category, caption] of cardsSrc.imageText) {
  cardEntries.push({ type: 'image_text', image: iconFor(icon), alt: caption, text: caption.trim(), category, source: FLUENT_SOURCE, active: true, dedupeKey: textKey(caption) });
}
// Images importées de Wikimedia Commons (scripts/import-commons.mjs), avec attribution obligatoire.
const importedFile = join(dirname(fileURLToPath(import.meta.url)), 'content-src', 'imported.json');
for (const it of readJson(importedFile, [])) {
  if (!existsSync(join(root, 'jeu', it.file))) errors.push(`image importée manquante : ${it.file}`);
  cardEntries.push({
    type: 'image', image: it.file, alt: it.alt, category: it.category, active: it.active !== false, dedupeKey: `sha:${it.contentHash}`,
    source: { name: `${it.author} · Wikimedia Commons`, url: it.sourceUrl, license: it.license, licenseUrl: it.licenseUrl, attribution: true },
  });
}
for (const c of cardEntries) if (!CATEGORIES[c.category]) errors.push(`catégorie de carte inconnue : ${c.category}`);
const cards = assignIds(cardEntries, prevCards, 'c');

// ── contrôles ───────────────────────────────────────────────
const dupCheck = (list, label) => {
  const seen = new Map();
  for (const it of list.filter((x) => x.active)) {
    if (seen.has(it.dedupeKey)) errors.push(`${label} en double : « ${it.text || it.image} » (${seen.get(it.dedupeKey)} et ${it.id})`);
    seen.set(it.dedupeKey, it.id);
  }
};
dupCheck(situations, 'situation');
dupCheck(cards, 'carte');
errors.push(...validateLibrary({ cards, situations }));
for (const [a, b, score] of nearDuplicates(situations.filter((s) => s.active), 0.45)) warnings.push(`situations proches (${score.toFixed(2)}) : « ${a.text} » / « ${b.text} »`);
for (const [a, b, score] of nearDuplicates(cards.filter((c) => c.active && c.text), 0.6)) warnings.push(`cartes proches (${score.toFixed(2)}) : « ${a.text} » / « ${b.text} »`);

const active = cards.filter((c) => c.active);
const count = (pred) => active.filter(pred).length;
const byCat = (list) => Object.fromEntries(Object.keys(CATEGORIES).map((k) => [k, list.filter((x) => x.active && x.category === k).length]).filter(([, n]) => n));
const stats = {
  situations: situations.filter((s) => s.active).length,
  cards: active.length,
  text: count((c) => c.type === 'text'),
  image: count((c) => c.type === 'image'),
  imageText: count((c) => c.type === 'image_text'),
  illustrations: [...usedIcons.values()].filter(Boolean).length,
  situationsByCategory: byCat(situations),
  cardsByCategory: byCat(cards),
};

console.log(JSON.stringify(stats, null, 2));
for (const w of warnings) console.warn('⚠️ ', w);
if (errors.length) {
  for (const e of errors) console.error('❌', e);
  process.exit(1);
}
if (checkOnly) process.exit(0);

// ── écriture ────────────────────────────────────────────────
mkdirSync(dataDir, { recursive: true });
mkdirSync(imgDir, { recursive: true });
const version = new Date().toISOString().slice(0, 10);
writeFileSync(join(dataDir, 'situations.json'), JSON.stringify({ version, count: stats.situations, situations }, null, 1) + '\n');
writeFileSync(
  join(dataDir, 'cards.json'),
  JSON.stringify(
    {
      version,
      count: stats.cards,
      sources: [
        { ...FLUENT_SOURCE, scope: 'illustrations des cartes image et image + légende', licenseUrl: 'https://github.com/microsoft/fluentui-emoji/blob/main/LICENSE' },
        { ...ORIGINAL_SOURCE, scope: 'toutes les phrases et légendes' },
      ],
      cards,
    },
    null,
    1,
  ) + '\n',
);
writeFileSync(join(dataDir, 'categories.json'), JSON.stringify(CATEGORIES, null, 1) + '\n');
const keep = new Set();
for (const [name, svg] of usedIcons) {
  if (!svg) continue;
  keep.add(`${name}.svg`);
  writeFileSync(join(imgDir, `${name}.svg`), svg);
}
for (const f of readdirSync(imgDir)) if (f.endsWith('.svg') && !keep.has(f)) unlinkSync(join(imgDir, f));
console.log(`✅ ${stats.situations} situations, ${stats.cards} cartes, ${keep.size} illustrations écrites.`);
