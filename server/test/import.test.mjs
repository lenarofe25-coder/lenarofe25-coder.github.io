// Filtrage des licences et lecture de la réponse de l'API Commons (sans réseau, sur un exemple).
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { acceptedLicense, parseCommons } from '../scripts/import-commons.mjs';

test('licences : libres acceptées, NC/ND et inconnues refusées', () => {
  for (const ok of ['CC0', 'Public domain', 'CC BY 4.0', 'CC BY-SA 3.0', 'CC-BY-SA-2.0']) assert.ok(acceptedLicense(ok), ok);
  for (const ko of ['CC BY-NC 4.0', 'CC BY-ND 2.0', 'CC BY-NC-SA 3.0', 'All rights reserved', '', undefined]) assert.equal(acceptedLicense(ko), null, String(ko));
});

test('réponse Commons : auteur nettoyé, licence conservée, formats et licences filtrés', () => {
  const json = {
    query: {
      pages: {
        1: { title: 'File:Chat qui baille.jpg', imageinfo: [{ mime: 'image/jpeg', sha1: 'a1', thumburl: 'https://upload.wikimedia.org/x.jpg', descriptionurl: 'https://commons.wikimedia.org/wiki/File:Chat', extmetadata: { LicenseShortName: { value: 'CC BY-SA 4.0' }, LicenseUrl: { value: 'https://creativecommons.org/licenses/by-sa/4.0' }, Artist: { value: '<a href="//x">Jeanne Dupont</a>' } } }] },
        2: { title: 'File:Logo.svg', imageinfo: [{ mime: 'image/svg+xml', sha1: 'b2', thumburl: 'https://x/y.png', extmetadata: { LicenseShortName: { value: 'CC0' } } }] },
        3: { title: 'File:Photo NC.jpg', imageinfo: [{ mime: 'image/jpeg', sha1: 'c3', thumburl: 'https://x/z.jpg', extmetadata: { LicenseShortName: { value: 'CC BY-NC 2.0' } } }] },
      },
    },
  };
  const [cat, svg, nc] = parseCommons(json);
  assert.equal(cat.rejected, null);
  assert.equal(cat.author, 'Jeanne Dupont');
  assert.equal(cat.license, 'CC BY-SA 4.0');
  assert.equal(svg.rejected, 'format non pris en charge');
  assert.equal(nc.rejected, 'licence non compatible');
});
