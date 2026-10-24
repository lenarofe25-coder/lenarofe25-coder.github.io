// Vérifie la bibliothèque publiée : nombre de cartes, doublons, licences, fichiers image.
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync, existsSync, statSync } from 'node:fs';
import { validateLibrary } from '../src/content.js';

const read = (p) => JSON.parse(readFileSync(new URL(`../../jeu/${p}`, import.meta.url), 'utf8'));
const cards = read('data/cards.json').cards;
const situations = read('data/situations.json').situations;
const categories = read('data/categories.json');

test('bibliothèque valide (identifiants, types, licences, doublons)', () => {
  assert.deepEqual(validateLibrary({ cards, situations }), []);
});

test('chaque image référencée existe, est un SVG non vide', () => {
  const images = new Set(cards.filter((c) => c.image).map((c) => c.image));
  for (const img of images) {
    const file = new URL(`../../jeu/${img}`, import.meta.url);
    assert.ok(existsSync(file), `fichier manquant : ${img}`);
    const svg = readFileSync(file, 'utf8');
    if (img.endsWith('.svg')) assert.ok(statSync(file).size > 200 && svg.startsWith('<svg') && svg.trim().endsWith('</svg>'), `SVG invalide : ${img}`);
    else assert.ok(statSync(file).size > 2048, `image trop petite : ${img}`);
  }
});

test('catégories connues ; humour noir marqué comme optionnel', () => {
  for (const x of [...cards, ...situations]) assert.ok(categories[x.category], `catégorie inconnue ${x.category}`);
  assert.equal(categories['humour-noir'].optIn, true);
});

test('textes : longueurs raisonnables pour un affichage mobile', () => {
  for (const s of situations) assert.ok(s.text.length >= 15 && s.text.length <= 140, `situation ${s.id} : ${s.text.length} caractères`);
  for (const c of cards.filter((c) => c.text)) assert.ok(c.text.length <= 90, `carte ${c.id} : ${c.text.length} caractères`);
});

test('mélange des types de cartes', () => {
  const by = (t) => cards.filter((c) => c.active && c.type === t).length;
  assert.ok(by('text') >= 200 && by('image') >= 100 && by('image_text') >= 150);
});

test('images à attribution : auteur et licence présents', () => {
  for (const c of cards.filter((c) => c.source?.attribution)) assert.ok(c.source.name && c.source.license && c.source.url, `attribution incomplète : ${c.id}`);
});
