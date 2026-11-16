// Relais entre l'appli Métro (GitHub Pages) et l'API PRIM d'Île-de-France Mobilités.
// - garde la clé PRIM côté serveur (secret PRIM_API_KEY), jamais dans le navigateur ;
// - ajoute les en-têtes CORS pour les seules origines autorisées ;
// - ne laisse passer que des GET vers les routes utiles à l'appli ;
// - met en cache quelques secondes pour ménager le quota PRIM.

const UPSTREAM = 'https://prim.iledefrance-mobilites.fr/marketplace/';

// Routes PRIM autorisées (chemin relatif à /marketplace/) et durée de cache en secondes.
const ROUTES = [
  { prefix: 'stop-monitoring', ttl: 20 },
  { prefix: 'general-message', ttl: 120 },
  { prefix: 'v2/navitia/places', ttl: 3600 },
  { prefix: 'v2/navitia/pt_objects', ttl: 3600 },
  { prefix: 'v2/navitia/journeys', ttl: 20 },
  { prefix: 'v2/navitia/stop_areas/', ttl: 20 },
  { prefix: 'v2/navitia/lines/', ttl: 3600 },
  { prefix: 'v2/navitia/coord/', ttl: 600 },
];

function cors(origin, env) {
  const allowed = (env.ALLOWED_ORIGINS || '').split(',').map((s) => s.trim()).filter(Boolean);
  const ok = origin && allowed.includes(origin);
  return {
    'Access-Control-Allow-Origin': ok ? origin : allowed[0] || 'null',
    'Access-Control-Allow-Methods': 'GET, OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type',
    'Access-Control-Max-Age': '86400',
    Vary: 'Origin',
  };
}

function json(body, status, headers) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json; charset=utf-8', ...headers },
  });
}

export function routeFor(path) {
  if (path.includes('..') || path.includes('//')) return null;
  return ROUTES.find((r) => path === r.prefix || path.startsWith(r.prefix.endsWith('/') ? r.prefix : r.prefix + '/') || path.startsWith(r.prefix + '?')) || null;
}

export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);
    const origin = request.headers.get('Origin');
    const h = cors(origin, env);

    if (request.method === 'OPTIONS') return new Response(null, { status: 204, headers: h });
    if (url.pathname === '/health') return json({ ok: true, key: Boolean(env.PRIM_API_KEY) }, 200, h);
    if (request.method !== 'GET') return json({ error: 'Méthode non autorisée' }, 405, h);

    // Un navigateur d'une autre origine ne doit pas pouvoir consommer le quota.
    const allowed = (env.ALLOWED_ORIGINS || '').split(',').map((s) => s.trim());
    if (origin && !allowed.includes(origin)) return json({ error: 'Origine non autorisée' }, 403, h);

    if (!url.pathname.startsWith('/prim/')) return json({ error: 'Introuvable' }, 404, h);
    const path = url.pathname.slice('/prim/'.length);
    const route = routeFor(path);
    if (!route) return json({ error: 'Route PRIM non autorisée' }, 404, h);
    if (!env.PRIM_API_KEY) return json({ error: 'Clé PRIM absente du relais (secret PRIM_API_KEY)' }, 500, h);

    const target = UPSTREAM + path + url.search;
    const cache = caches.default;
    const cacheKey = new Request(target, { method: 'GET' });
    const hit = await cache.match(cacheKey);
    if (hit) {
      const r = new Response(hit.body, hit);
      Object.entries(h).forEach(([k, v]) => r.headers.set(k, v));
      r.headers.set('X-Relais-Cache', 'HIT');
      return r;
    }

    let upstream;
    try {
      upstream = await fetch(target, { headers: { apiKey: env.PRIM_API_KEY, Accept: 'application/json' } });
    } catch (e) {
      return json({ error: 'PRIM injoignable' }, 502, h);
    }
    const body = await upstream.arrayBuffer();
    const headers = {
      'Content-Type': upstream.headers.get('Content-Type') || 'application/json',
      'Cache-Control': `public, max-age=${route.ttl}`,
    };
    const res = new Response(body, { status: upstream.status, headers });
    if (upstream.ok) ctx.waitUntil(cache.put(cacheKey, res.clone()));
    const out = new Response(body, { status: upstream.status, headers: { ...headers, ...h, 'X-Relais-Cache': 'MISS' } });
    return out;
  },
};
