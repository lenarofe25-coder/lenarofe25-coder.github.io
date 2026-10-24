// Point d'entrée HTTP du serveur MDR. Le site statique (GitHub Pages) appelle cette API ;
// chaque salle vit dans son propre Durable Object, qui est la seule source de vérité.
import { Room } from './room.js';
import { Limiter } from './limiter.js';

export { Room, Limiter };

const CODE_RE = /^[A-Z]{3}[0-9]{3}$/;
// Sans I ni O pour éviter les confusions avec 1 et 0.
const CODE_LETTERS = 'ABCDEFGHJKLMNPQRSTUVWXYZ';

function randomCode() {
  const b = crypto.getRandomValues(new Uint32Array(6));
  const letters = [0, 1, 2].map((i) => CODE_LETTERS[b[i] % CODE_LETTERS.length]).join('');
  const digits = [3, 4, 5].map((i) => b[i] % 10).join('');
  return letters + digits;
}

function allowedOrigin(request, env) {
  const origin = request.headers.get('Origin');
  if (!origin) return null;
  const list = (env.ALLOWED_ORIGINS || '').split(',').map((s) => s.trim()).filter(Boolean);
  return list.includes('*') || list.includes(origin) ? origin : null;
}

function json(body, status, origin) {
  const headers = { 'content-type': 'application/json; charset=utf-8', 'cache-control': 'no-store' };
  if (origin) Object.assign(headers, { 'access-control-allow-origin': origin, vary: 'Origin' });
  return new Response(JSON.stringify(body), { status, headers });
}

const STATUS = { ROOM_NOT_FOUND: 404, ROOM_EXPIRED: 410, GAME_FINISHED: 410, GAME_STARTED: 409, ROOM_FULL: 409, NAME_TAKEN: 409, RATE_LIMITED: 429 };

async function readJson(request) {
  const text = await request.text();
  if (text.length > 2000) return null;
  try {
    return JSON.parse(text);
  } catch {
    return null;
  }
}

async function limited(env, request, bucket, limit, windowMs) {
  const ip = request.headers.get('CF-Connecting-IP') || 'local';
  const stub = env.LIMITER.get(env.LIMITER.idFromName(ip));
  return !(await stub.hit(bucket, limit, windowMs));
}

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    const origin = allowedOrigin(request, env);

    if (request.method === 'OPTIONS') {
      if (!origin) return new Response(null, { status: 403 });
      return new Response(null, {
        status: 204,
        headers: {
          'access-control-allow-origin': origin,
          'access-control-allow-methods': 'GET, POST, OPTIONS',
          'access-control-allow-headers': 'content-type',
          'access-control-max-age': '86400',
          vary: 'Origin',
        },
      });
    }

    if (url.pathname === '/api/health') return json({ ok: true }, 200, origin);

    // Les appels viennent du site : un navigateur d'une autre origine est refusé.
    if (request.headers.get('Origin') && !origin) return json({ code: 'FORBIDDEN', message: 'Origine non autorisée.' }, 403, null);

    if (url.pathname === '/api/content/stats' && request.method === 'GET') {
      const stub = env.ROOMS.get(env.ROOMS.idFromName('__stats__'));
      return json(await stub.contentStats(), 200, origin);
    }

    if (url.pathname === '/api/rooms' && request.method === 'POST') {
      if (await limited(env, request, 'create', 10, 10 * 60_000)) return json({ code: 'RATE_LIMITED', message: 'Trop de parties créées. Réessaie dans quelques minutes.' }, 429, origin);
      const body = await readJson(request);
      if (!body) return json({ code: 'BAD_REQUEST', message: 'Requête invalide.' }, 400, origin);
      for (let attempt = 0; attempt < 6; attempt++) {
        const code = randomCode();
        const stub = env.ROOMS.get(env.ROOMS.idFromName(code));
        const res = await stub.init(code, body.name, body.config);
        if (res.code === 'EXISTS') continue;
        return json(res, res.ok ? 201 : STATUS[res.code] || 400, origin);
      }
      return json({ code: 'SERVER_ERROR', message: 'Impossible de créer une salle, réessaie.' }, 503, origin);
    }

    const m = url.pathname.match(/^\/api\/rooms\/([A-Za-z0-9]{1,12})\/(join|ws|peek)$/);
    if (m) {
      const code = m[1].toUpperCase();
      const action = m[2];
      if (action !== 'ws' && (await limited(env, request, 'join', 40, 10 * 60_000))) {
        return json({ code: 'RATE_LIMITED', message: 'Trop de tentatives. Réessaie dans quelques minutes.' }, 429, origin);
      }
      if (!CODE_RE.test(code)) return json({ code: 'ROOM_NOT_FOUND', message: 'Ce code de salle n’existe pas.' }, 404, origin);
      const stub = env.ROOMS.get(env.ROOMS.idFromName(code));
      if (action === 'ws') {
        if (request.headers.get('Upgrade') !== 'websocket') return json({ code: 'BAD_REQUEST', message: 'WebSocket attendu.' }, 426, origin);
        if (!origin) return new Response('Origine non autorisée', { status: 403 });
        return stub.fetch(request);
      }
      if (action === 'peek' && request.method === 'GET') {
        const res = await stub.peek();
        return json(res, res.ok ? 200 : STATUS[res.code] || 400, origin);
      }
      if (action === 'join' && request.method === 'POST') {
        const body = await readJson(request);
        if (!body) return json({ code: 'BAD_REQUEST', message: 'Requête invalide.' }, 400, origin);
        const res = await stub.join(body.name);
        return json(res, res.ok ? 200 : STATUS[res.code] || 400, origin);
      }
    }

    return json({ code: 'NOT_FOUND', message: 'Route inconnue.' }, 404, origin);
  },
};
