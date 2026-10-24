// Vérifie la bibliothèque publiée : 500 situations, au moins 300 memes visuels uniques.
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { validateLibrary } from '../src/content.js';

const read = (p) => JSON.parse(readFileSync(new URL(`../../jeu/${p}`, import.meta.url), 'utf8'));
const memes = read('data/memes.json').memes;
const situations = read('data/situations.json').situations;
const categories = read('data/categories.json');
const active = memes.filter((m) => m.active);

test('bibliothèque valide (identifiants, sources, doublons exacts)', () => {
  assert.deepEqual(validateLibrary({ memes, situations }), []);
});

test('au moins 300 memes visuels actifs', () => {
  assert.ok(active.length >= 300, `${active.length} memes actifs seulement`);
});

test('aucune image en double, même sous un autre nom (empreinte perceptuelle)', () => {
  const bits = (h) => BigInt(`0x${h}`);
  const dist = (a, b) => (bits(a) ^ bits(b)).toString(2).replace(/0/g, '').length;
  for (let i = 0; i < active.length; i++)
    for (let j = i + 1; j < active.length; j++)
      assert.ok(dist(active[i].phash, active[j].phash) > 8, `${active[i].id} et ${active[j].id} sont la même image`);
});

test('chaque meme a un nom, une image HTTPS vérifiée, une source et une mention de droits', () => {
  for (const m of active) {
    assert.ok(m.name && m.image.startsWith('https://') && m.width >= 150 && m.height >= 150, m.id);
    assert.ok(m.source.name && m.source.page && m.rights, m.id);
  }
});

test('500 situations, 50 par catégorie', () => {
  const on = situations.filter((s) => s.active);
  assert.equal(on.length, 500);
  for (const k of Object.keys(categories)) assert.equal(on.filter((s) => s.category === k).length, 50, k);
});
