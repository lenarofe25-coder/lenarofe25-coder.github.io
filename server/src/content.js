// Bibliothèques de contenu : les situations et les cartes réponses sont deux fichiers
// indépendants (jeu/data/*.json). Le Worker embarque une copie au déploiement et peut
// recharger la version publiée sur le site (CONTENT_URL) pour ajouter des cartes sans redéployer.

export const CARD_TYPES = ['text', 'image', 'image_text'];

const MISSING_CARD = (id) => ({ id, type: 'text', text: 'Carte indisponible', category: '', missing: true });

export function validateLibrary({ cards, situations }) {
  const errors = [];
  const ids = new Set();
  const keys = new Map();
  for (const c of cards) {
    if (!c.id || ids.has(c.id)) errors.push(`carte : identifiant manquant ou dupliqué (${c.id})`);
    ids.add(c.id);
    if (!CARD_TYPES.includes(c.type)) errors.push(`carte ${c.id} : type inconnu ${c.type}`);
    if ((c.type === 'text' || c.type === 'image_text') && !c.text) errors.push(`carte ${c.id} : texte manquant`);
    if ((c.type === 'image' || c.type === 'image_text') && !c.image) errors.push(`carte ${c.id} : image manquante`);
    if (c.image && !c.source?.license) errors.push(`carte ${c.id} : licence manquante`);
    if (!c.category) errors.push(`carte ${c.id} : catégorie manquante`);
    if (c.dedupeKey) {
      if (keys.has(c.dedupeKey)) errors.push(`carte ${c.id} : doublon de ${keys.get(c.dedupeKey)}`);
      keys.set(c.dedupeKey, c.id);
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

export function buildContent({ cards, situations }) {
  const cardMap = new Map(cards.map((c) => [c.id, c]));
  const sitMap = new Map(situations.map((s) => [s.id, s]));
  return {
    cards,
    situations,
    cardById: (id) => {
      const c = cardMap.get(id);
      if (!c) return MISSING_CARD(id);
      // On n'envoie au navigateur que ce qui sert à l'affichage.
      const out = { id: c.id, type: c.type, category: c.category };
      if (c.text) out.text = c.text;
      if (c.image) {
        out.image = c.image;
        out.alt = c.alt || '';
        // Attribution affichée sur la carte quand la licence l'exige (CC BY…).
        if (c.source?.attribution) out.credit = `${c.source.name} · ${c.source.license}`;
      }
      if (!c.active) out.missing = true;
      return out;
    },
    situationById: (id) => sitMap.get(id) || null,
    stats: () => ({
      cards: cards.length,
      activeCards: cards.filter((c) => c.active).length,
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
  const [cards, situations] = await Promise.all([get('cards.json'), get('situations.json')]);
  const lib = { cards: cards.cards, situations: situations.situations };
  const errors = validateLibrary(lib);
  if (errors.length) throw new Error(`bibliothèque distante invalide : ${errors.slice(0, 3).join(' ; ')}`);
  return lib;
}
