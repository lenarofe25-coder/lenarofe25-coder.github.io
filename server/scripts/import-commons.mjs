// Importe des images de réaction depuis Wikimedia Commons, uniquement sous licence libre
// compatible (domaine public, CC0, CC BY, CC BY-SA), avec auteur et licence enregistrés.
// Les images sont téléchargées (miniature 480 px) dans jeu/cards/import/ et décrites dans
// scripts/content-src/imported.json ; `npm run content` les ajoute ensuite à la bibliothèque.
//
// Usage :
//   node scripts/import-commons.mjs --category "Category:Yawning cats" --game-category absurde --limit 40
//   node scripts/import-commons.mjs --category "..." --dry-run      (liste sans rien télécharger)
//
// Réseau requis vers commons.wikimedia.org et upload.wikimedia.org.
import { readFileSync, writeFileSync, mkdirSync, existsSync } from 'node:fs';
import { createHash } from 'node:crypto';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';

const root = join(dirname(fileURLToPath(import.meta.url)), '..', '..');
const API = 'https://commons.wikimedia.org/w/api.php';
const UA = 'MDR-jeu-de-memes/1.0 (https://lenarofe25-coder.github.io/jeu/; import ponctuel de cartes)';
export const ACCEPTED_MIME = ['image/jpeg', 'image/png', 'image/webp'];

// Licences acceptées : on garde la mention exacte pour l'attribution.
export function acceptedLicense(short = '') {
  const s = short.trim();
  if (/^(public domain|pd|cc0)/i.test(s)) return s;
  if (/^cc[ -]by(-sa)?[ -]\d(\.\d)?/i.test(s)) return s; // CC BY / CC BY-SA, toutes versions ; pas de NC ni ND
  return null;
}

const stripHtml = (s = '') => s.replace(/<[^>]*>/g, '').replace(/\s+/g, ' ').trim();

// Transforme une réponse de l'API (generator=categorymembers, prop=imageinfo) en candidats.
export function parseCommons(json) {
  const pages = Object.values(json?.query?.pages || {});
  const out = [];
  for (const page of pages) {
    const info = page.imageinfo?.[0];
    if (!info) continue;
    const meta = info.extmetadata || {};
    const license = acceptedLicense(meta.LicenseShortName?.value);
    const reason = !license ? 'licence non compatible' : !ACCEPTED_MIME.includes(info.mime) ? 'format non pris en charge' : !info.thumburl ? 'miniature absente' : null;
    out.push({
      title: page.title,
      sha1: info.sha1,
      thumb: info.thumburl,
      sourceUrl: info.descriptionurl,
      mime: info.mime,
      author: stripHtml(meta.Artist?.value) || 'Auteur inconnu',
      license: license || meta.LicenseShortName?.value || 'inconnue',
      licenseUrl: meta.LicenseUrl?.value || '',
      description: stripHtml(meta.ImageDescription?.value).slice(0, 120),
      rejected: reason,
    });
  }
  return out;
}

function args() {
  const a = process.argv.slice(2);
  const get = (k, d) => (a.includes(k) ? a[a.indexOf(k) + 1] : d);
  return { category: get('--category'), gameCategory: get('--game-category', 'reactions'), limit: Number(get('--limit', 40)), dryRun: a.includes('--dry-run') };
}

async function main() {
  const { category, gameCategory, limit, dryRun } = args();
  if (!category?.startsWith('Category:')) {
    console.error('Indique une catégorie Commons : --category "Category:..."');
    process.exit(1);
  }
  const url = new URL(API);
  Object.entries({
    action: 'query', format: 'json', generator: 'categorymembers', gcmtitle: category, gcmtype: 'file', gcmlimit: String(Math.min(limit * 2, 200)),
    prop: 'imageinfo', iiprop: 'url|mime|sha1|extmetadata', iiurlwidth: '480',
  }).forEach(([k, v]) => url.searchParams.set(k, v));
  const res = await fetch(url, { headers: { 'user-agent': UA } });
  if (!res.ok) throw new Error(`API Commons : HTTP ${res.status}`);
  const candidates = parseCommons(await res.json());

  const listFile = join(root, 'server/scripts/content-src/imported.json');
  const imported = existsSync(listFile) ? JSON.parse(readFileSync(listFile, 'utf8')) : [];
  const known = new Set(imported.flatMap((i) => [i.sha1, i.contentHash]));
  const dir = join(root, 'jeu/cards/import');
  mkdirSync(dir, { recursive: true });
  const report = { accepted: 0, rejected: {}, duplicates: 0, failed: 0 };

  for (const c of candidates) {
    if (report.accepted >= limit) break;
    if (c.rejected) {
      report.rejected[c.rejected] = (report.rejected[c.rejected] || 0) + 1;
      continue;
    }
    if (known.has(c.sha1)) {
      report.duplicates++;
      continue;
    }
    if (dryRun) {
      console.log(`✓ ${c.title} — ${c.author} — ${c.license}`);
      report.accepted++;
      continue;
    }
    // Vérification de l'image réellement servie : type, taille, empreinte (doublons exacts).
    const img = await fetch(c.thumb, { headers: { 'user-agent': UA } });
    const type = img.headers.get('content-type') || '';
    const bytes = Buffer.from(await img.arrayBuffer());
    if (!img.ok || !type.startsWith('image/') || bytes.length < 2048) {
      report.failed++;
      continue;
    }
    const contentHash = createHash('sha256').update(bytes).digest('hex');
    if (known.has(contentHash)) {
      report.duplicates++;
      continue;
    }
    const ext = type.includes('png') ? 'png' : type.includes('webp') ? 'webp' : 'jpg';
    const file = `${contentHash.slice(0, 16)}.${ext}`;
    writeFileSync(join(dir, file), bytes);
    imported.push({ file: `cards/import/${file}`, sha1: c.sha1, contentHash, title: c.title, author: c.author, license: c.license, licenseUrl: c.licenseUrl, sourceUrl: c.sourceUrl, alt: c.description || c.title.replace(/^File:|\.\w+$/g, ''), category: gameCategory, active: true });
    known.add(c.sha1).add(contentHash);
    report.accepted++;
    await new Promise((r) => setTimeout(r, 300)); // politesse envers les serveurs Wikimedia
  }
  if (!dryRun) writeFileSync(listFile, JSON.stringify(imported, null, 1) + '\n');
  console.log(JSON.stringify(report, null, 2));
  if (!dryRun) console.log('Relis les images importées (contenu adapté au jeu ?), puis lance `npm run content`.');
}

if (process.argv[1] === fileURLToPath(import.meta.url)) main().catch((e) => {
  console.error(e.message);
  process.exit(1);
});
