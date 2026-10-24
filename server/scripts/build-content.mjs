// Génère jeu/data/situations.json depuis scripts/content-src/situations.mjs et vérifie la
// bibliothèque de memes jeu/data/memes.json (produite par server/memes/collect.py).
// Les identifiants de situations déjà publiés sont conservés ; une situation retirée de la
// source reste dans le fichier avec active: false.
// Usage : npm run content   (ajouter --check pour vérifier sans écrire)
import { readFileSync, writeFileSync, existsSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';
import situationsSrc from './content-src/situations.mjs';
import { validateLibrary } from '../src/content.js';

const root = join(dirname(fileURLToPath(import.meta.url)), '..', '..');
const dataDir = join(root, 'jeu', 'data');
const checkOnly = process.argv.includes('--check');

export const CATEGORIES = {
  crush: 'Crushs & flirts',
  ex: 'Ex & ruptures',
  amies: 'Meilleures amies',
  dramas: 'Dramas, secrets & trahisons',
  beaute: 'Beauté, tenues & confiance',
  dates: 'Dates, couples & jalousie',
  reseaux: 'Réseaux sociaux & messages',
  soirees: 'Sorties, soirées & groupes',
  quotidien: 'Famille, études & quotidien',
  absurde: 'Situations absurdes & gênantes',
};

export const textKey = (s) =>
  s
    .normalize('NFD')
    .replace(/[̀-ͯ]/g, '')
    .toLowerCase()
    .replace(/[’']/g, ' ')
    .replace(/[^a-z0-9 ]+/g, ' ')
    .replace(/\s+/g, ' ')
    .trim();

const readJson = (file, fallback) => (existsSync(file) ? JSON.parse(readFileSync(file, 'utf8')) : fallback);
const errors = [];
const warnings = [];

// ── situations ──────────────────────────────────────────────
const previous = readJson(join(dataDir, 'situations.json'), { situations: [] }).situations;
const byKey = new Map(previous.map((p) => [p.dedupeKey, p]));
let max = Math.max(0, ...previous.map((p) => Number(p.id.split('-').pop()) || 0));
const seen = new Map();
const situations = [];
for (const [category, list] of Object.entries(situationsSrc)) {
  if (!CATEGORIES[category]) errors.push(`catégorie inconnue : ${category}`);
  for (const raw of list) {
    const text = raw.trim();
    const dedupeKey = textKey(text);
    if (seen.has(dedupeKey)) errors.push(`situation en double : « ${text} »`);
    seen.set(dedupeKey, text);
    const id = byKey.get(dedupeKey)?.id || `s-${String(++max).padStart(4, '0')}`;
    situations.push({ id, text, category, active: true, dedupeKey });
  }
}
for (const p of previous) if (!seen.has(p.dedupeKey)) situations.push({ ...p, active: false });

// ── memes ───────────────────────────────────────────────────
const memesFile = join(dataDir, 'memes.json');
const memes = readJson(memesFile, { memes: [] }).memes;
if (!memes.length) warnings.push('jeu/data/memes.json absent ou vide : lancer le workflow « Import des memes ».');
errors.push(...validateLibrary({ memes, situations }));

const active = situations.filter((s) => s.active);
const activeMemes = memes.filter((m) => m.active);
const stats = {
  situations: active.length,
  situationsByCategory: Object.fromEntries(Object.keys(CATEGORIES).map((k) => [k, active.filter((s) => s.category === k).length])),
  memes: activeMemes.length,
  memesBySource: activeMemes.reduce((acc, m) => ({ ...acc, [m.source.name]: (acc[m.source.name] || 0) + 1 }), {}),
};
console.log(JSON.stringify(stats, null, 2));
for (const w of warnings) console.warn('⚠️ ', w);
if (errors.length) {
  for (const e of errors) console.error('❌', e);
  process.exit(1);
}
if (checkOnly) process.exit(0);

const version = new Date().toISOString().slice(0, 10);
writeFileSync(join(dataDir, 'situations.json'), JSON.stringify({ version, count: stats.situations, situations }, null, 1) + '\n');
writeFileSync(join(dataDir, 'categories.json'), JSON.stringify(CATEGORIES, null, 1) + '\n');
console.log(`✅ ${stats.situations} situations écrites ; ${stats.memes} memes actifs vérifiés.`);
