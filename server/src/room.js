// Une salle = un Durable Object. Il exécute les messages un par un (pas de course entre
// deux votes simultanés), persiste l'état après chaque action et programme une alarme
// pour les chronos, les déconnexions et l'expiration de la salle.
import { DurableObject } from 'cloudflare:workers';
import * as engine from './engine.js';
import { buildContent, loadRemoteContent } from './content.js';
import bundledMemes from '../../jeu/data/memes.json';
import bundledSituations from '../../jeu/data/situations.json';

const REFRESH_MS = 10 * 60_000;
let contentCache = { content: buildContent({ memes: bundledMemes.memes, situations: bundledSituations.situations }), loadedAt: 0, source: 'bundled' };

async function getContent(env) {
  if (env.CONTENT_URL && Date.now() - contentCache.loadedAt > REFRESH_MS) {
    contentCache.loadedAt = Date.now();
    try {
      contentCache = { content: buildContent(await loadRemoteContent(env.CONTENT_URL)), loadedAt: Date.now(), source: 'remote' };
    } catch (err) {
      console.warn('Contenu distant ignoré, copie embarquée conservée :', err.message);
    }
  }
  return contentCache.content;
}

const rng = () => crypto.getRandomValues(new Uint32Array(1))[0] / 2 ** 32;

function randomToken() {
  const bytes = crypto.getRandomValues(new Uint8Array(32));
  return btoa(String.fromCharCode(...bytes)).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
}

async function sha256(text) {
  const digest = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(text));
  return [...new Uint8Array(digest)].map((b) => b.toString(16).padStart(2, '0')).join('');
}

const asError = (err) =>
  err instanceof engine.GameError ? { ok: false, code: err.code, message: err.message } : { ok: false, code: 'SERVER_ERROR', message: 'Erreur serveur, réessaie.' };

export class Room extends DurableObject {
  constructor(ctx, env) {
    super(ctx, env);
    this.room = null;
    this.buckets = new Map();
    ctx.blockConcurrencyWhile(async () => {
      this.room = (await ctx.storage.get('room')) || null;
    });
    // Les pings du client sont traités sans réveiller l'objet.
    ctx.setWebSocketAutoResponse(new WebSocketRequestResponsePair('{"t":"ping"}', '{"t":"pong"}'));
  }

  async save() {
    const room = this.room;
    if (room.status === 'closed') {
      await this.ctx.storage.deleteAll();
      await this.ctx.storage.put('room', { status: 'closed', code: room.code, closedAt: Date.now() });
      return;
    }
    await this.ctx.storage.put('room', room);
    const at = engine.nextWakeup(room);
    if (at != null) await this.ctx.storage.setAlarm(Math.max(at, Date.now() + 50));
  }

  ctxFor(content) {
    return { now: Date.now(), rng, content };
  }

  async contentStats() {
    const content = await getContent(this.env);
    return { ...content.stats(), source: contentCache.source };
  }

  async init(code, name, config) {
    if (this.room && this.room.status !== 'closed') return { ok: false, code: 'EXISTS' };
    try {
      const now = Date.now();
      const room = engine.createRoom({ code, now, rng });
      if (config) room.config = engine.sanitizeConfig(config, room.config);
      const token = randomToken();
      const pid = engine.randomId(rng, 12);
      engine.joinRoom(room, { pid, name, tokenHash: await sha256(token), now });
      this.room = room;
      await this.save();
      return { ok: true, code, playerId: pid, token };
    } catch (err) {
      return asError(err);
    }
  }

  async peek() {
    const room = this.room;
    if (!room) return { ok: false, code: 'ROOM_NOT_FOUND', message: 'Ce code de salle n’existe pas.' };
    if (room.status === 'closed') return { ok: false, code: 'ROOM_EXPIRED', message: 'Cette partie est terminée ou a expiré.' };
    const count = Object.values(room.players).filter((p) => !p.left).length;
    return { ok: true, code: room.code, status: room.status, players: count, max: engine.LIMITS.maxPlayers };
  }

  async join(name) {
    if (!this.room) return { ok: false, code: 'ROOM_NOT_FOUND', message: 'Ce code de salle n’existe pas.' };
    try {
      const token = randomToken();
      const pid = engine.randomId(rng, 12);
      engine.joinRoom(this.room, { pid, name, tokenHash: await sha256(token), now: Date.now() });
      await this.save();
      this.broadcast(await getContent(this.env));
      return { ok: true, code: this.room.code, playerId: pid, token };
    } catch (err) {
      return asError(err);
    }
  }

  async fetch(request) {
    if (request.headers.get('Upgrade') !== 'websocket') return new Response('WebSocket attendu', { status: 426 });
    const { 0: client, 1: server } = new WebSocketPair();
    this.ctx.acceptWebSocket(server);
    server.serializeAttachment({ pid: null });
    return new Response(null, { status: 101, webSocket: client });
  }

  socketsOf(pid) {
    return this.ctx.getWebSockets().filter((ws) => ws.deserializeAttachment()?.pid === pid);
  }

  send(ws, msg) {
    try {
      ws.send(JSON.stringify(msg));
    } catch {
      // socket déjà fermé
    }
  }

  broadcast(content) {
    for (const ws of this.ctx.getWebSockets()) {
      const pid = ws.deserializeAttachment()?.pid;
      if (pid && this.room.players[pid]) this.send(ws, { t: 'state', s: engine.viewFor(this.room, pid, content), now: Date.now() });
    }
  }

  allowed(ws) {
    // Par défaut 30 actions par tranche de 10 secondes et par connexion : largement assez pour jouer.
    const limit = Number(this.env.ACTIONS_PER_10S) || 30;
    const now = Date.now();
    const b = this.buckets.get(ws) || { start: now, n: 0 };
    if (now - b.start > 10_000) {
      b.start = now;
      b.n = 0;
    }
    b.n += 1;
    this.buckets.set(ws, b);
    return b.n <= limit;
  }

  async webSocketMessage(ws, raw) {
    if (typeof raw !== 'string' || raw.length > 2000) return ws.close(1009, 'Message trop long');
    let msg;
    try {
      msg = JSON.parse(raw);
    } catch {
      return this.send(ws, { t: 'error', code: 'BAD_REQUEST', message: 'Message illisible.' });
    }
    if (!this.allowed(ws)) return this.send(ws, { t: 'error', code: 'RATE_LIMITED', message: 'Doucement ! Trop d’actions d’un coup.', ref: msg.ref });
    const room = this.room;
    if (!room || room.status === 'closed') {
      this.send(ws, { t: 'bye', code: 'ROOM_EXPIRED', message: 'Cette partie est terminée ou a expiré.' });
      return ws.close(4410, 'expired');
    }
    const content = await getContent(this.env);

    if (msg.t === 'hello') {
      const player = typeof msg.token === 'string' ? engine.findPlayerByToken(room, await sha256(msg.token)) : null;
      if (!player) {
        this.send(ws, { t: 'bye', code: 'BAD_TOKEN', message: 'Ta session dans cette salle n’existe plus. Rejoins-la à nouveau.' });
        return ws.close(4401, 'bad token');
      }
      // Un seul onglet actif par joueuse : l'ancien est fermé.
      for (const other of this.socketsOf(player.id)) {
        if (other !== ws) {
          this.send(other, { t: 'bye', code: 'REPLACED', message: 'Tu as ouvert la partie dans un autre onglet.' });
          other.close(4409, 'replaced');
        }
      }
      ws.serializeAttachment({ pid: player.id });
      engine.connect(room, player.id, Date.now());
      engine.tick(room, this.ctxFor(content));
      await this.save();
      this.broadcast(content);
      return;
    }

    const pid = ws.deserializeAttachment()?.pid;
    if (!pid || !room.players[pid]) {
      this.send(ws, { t: 'bye', code: 'BAD_TOKEN', message: 'Session inconnue.' });
      return ws.close(4401, 'unknown');
    }
    try {
      engine.applyAction(room, pid, msg, this.ctxFor(content));
      await this.save();
      this.send(ws, { t: 'ack', ref: msg.ref });
      if (msg.t === 'leave' || msg.t === 'kick') {
        const gone = msg.t === 'leave' ? pid : msg.pid;
        for (const s of this.socketsOf(gone)) {
          this.send(s, { t: 'bye', code: msg.t === 'leave' ? 'LEFT' : 'KICKED', message: msg.t === 'leave' ? 'Tu as quitté la partie.' : 'L’hôte t’a retirée du salon.' });
          s.close(4000, msg.t);
        }
      }
      this.broadcast(content);
    } catch (err) {
      if (!(err instanceof engine.GameError)) console.error(err);
      this.send(ws, { t: 'error', ref: msg.ref, ...asError(err) });
    }
  }

  async webSocketClose(ws) {
    await this.onSocketGone(ws);
  }

  async webSocketError(ws) {
    await this.onSocketGone(ws);
  }

  async onSocketGone(ws) {
    this.buckets.delete(ws);
    const pid = ws.deserializeAttachment()?.pid;
    if (!pid || !this.room?.players[pid]) return;
    if (this.socketsOf(pid).some((s) => s !== ws && s.readyState === WebSocket.OPEN)) return;
    if (engine.disconnect(this.room, pid, Date.now())) {
      await this.save();
      this.broadcast(await getContent(this.env));
    }
  }

  async alarm() {
    if (!this.room || this.room.status === 'closed') return;
    const content = await getContent(this.env);
    engine.tick(this.room, this.ctxFor(content));
    if (this.room.status === 'closed') {
      for (const ws of this.ctx.getWebSockets()) {
        this.send(ws, { t: 'bye', code: 'ROOM_EXPIRED', message: 'La salle a expiré faute d’activité.' });
        ws.close(4410, 'expired');
      }
    } else {
      this.broadcast(content);
    }
    await this.save();
  }
}
