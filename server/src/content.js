// Bibliothèques de contenu : les situations (jeu/data/situations.json) et les memes
// (jeu/data/memes.json) sont deux fichiers indépendants. Le Worker embarque une copie au
// déploiement et peut recharger la version publiée sur le site (CONTENT_URL) pour ajouter
// des memes ou des situations sans redéployer.

const MISSING_CARD = (id) => ({ id, type: 'meme', name: 'Meme indisponible', missing: true });

export function validateLibrary({ memes, situations }) {
  const errors = [];
  const ids = new Set();
  const hashes = new Map();
  for (const m of memes) {
    if (!m.id || ids.has(m.id)) errors.push(`meme : identifiant manquant ou dupliqué (${m.id})`);
    ids.add(m.id);
    if (!m.name) errors.push(`meme ${m.id} : nom manquant`);
    if (!/^https:\/\//.test(m.image || '')) errors.push(`meme ${m.id} : image absente ou non HTTPS`);
    if (!m.source?.name || !m.source?.page) errors.push(`meme ${m.id} : source manquante`);
    if (m.active && m.sha256) {
      if (hashes.has(m.sha256)) errors.push(`meme ${m.id} : même image que ${hashes.get(m.sha256)}`);
      hashes.set(m.sha256, m.id);
    }
  }
  const sids = new Set();
  for (const s of situations) {
    if (!s.id || sids.has(s.id)) errors.push(`situation : identifiant manquant ou dupliqué (${s.id})`);
    sids.add(s.id);
    if (!s.text) errors.push(`situation ${s.id} : texte manquant`);
    if (!s.category) errors.push(`situation ${s.id} : catégorie manquante`);
  }
  return errors;
}

export function buildContent({ memes, situations }) {
  const memeMap = new Map(memes.map((m) => [m.id, m]));
  const sitMap = new Map(situations.map((s) => [s.id, s]));
  return {
    cards: memes,
    situations,
    // Seul ce qui sert à l'affichage part vers le navigateur.
    cardById: (id) => {
      const m = memeMap.get(id);
      if (!m) return MISSING_CARD(id);
      const out = { id: m.id, type: 'meme', name: m.name, image: m.image, credit: m.source.name };
      if (m.width && m.height) out.ratio = Math.round((m.width / m.height) * 100) / 100;
      if (!m.active) out.missing = true;
      return out;
    },
    situationById: (id) => sitMap.get(id) || null,
    stats: () => ({
      memes: memes.length,
      activeMemes: memes.filter((m) => m.active).length,
      situations: situations.length,
      activeSituations: situations.filter((s) => s.active).length,
    }),
  };
}

// Charge la version publiée si elle est valide, sinon garde la copie embarquée.
export async function loadRemoteContent(baseUrl, fetchImpl = fetch) {
  const get = async (name) => {
    const res = await fetchImpl(new URL(name, baseUrl), { cf: { cacheTtl: 300 } });
    if (!res.ok) throw new Error(`${name}: HTTP ${res.status}`);
    return res.json();
  };
  const [memes, situations] = await Promise.all([get('memes.json'), get('situations.json')]);
  const lib = { memes: memes.memes, situations: situations.situations };
  const errors = validateLibrary(lib);
  if (errors.length) throw new Error(`bibliothèque distante invalide : ${errors.slice(0, 3).join(' ; ')}`);
  return lib;
}
