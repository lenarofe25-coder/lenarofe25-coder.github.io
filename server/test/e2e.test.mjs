// Test de bout en bout contre le vrai Worker (lancer `npm run dev` avant `npm run test:e2e`).
// Plusieurs clients WebSocket jouent une partie complète de 10 manches.
import { test, after } from 'node:test';
import assert from 'node:assert/strict';

const BASE = process.env.MDR_SERVER || 'http://127.0.0.1:8787';
const ORIGIN = 'http://localhost:8080';
// Chaque test simule sa propre adresse IP pour ne pas épuiser le limiteur de débit des autres.
let ip = `10.${Math.floor(Math.random() * 200)}.0.1`;
const newIp = () => (ip = `10.${Math.floor(Math.random() * 200)}.${Math.floor(Math.random() * 250)}.${Math.floor(Math.random() * 250)}`);
const open = new Set();
after(() => open.forEach((c) => c.ws?.close()));

async function api(path, body, { origin = ORIGIN, method = body ? 'POST' : 'GET' } = {}) {
  const res = await fetch(BASE + path, {
    method,
    headers: { 'content-type': 'application/json', 'cf-connecting-ip': ip, ...(origin ? { origin } : {}) },
    body: body ? JSON.stringify(body) : undefined,
  });
  return { status: res.status, body: await res.json().catch(() => null) };
}

class Client {
  constructor(code, auth) {
    this.code = code;
    this.auth = auth;
    this.messages = [];
    this.waiters = [];
    this.state = null;
  }
  open() {
    return new Promise((resolve, reject) => {
      const ws = new WebSocket(`${BASE.replace('http', 'ws')}/api/rooms/${this.code}/ws`, { headers: { origin: ORIGIN } });
      this.ws = ws;
      open.add(this);
      ws.onopen = () => {
        ws.send(JSON.stringify({ t: 'hello', token: this.auth.token }));
        resolve();
      };
      ws.onerror = reject;
      ws.onmessage = (e) => {
        const msg = JSON.parse(e.data);
        this.messages.push(msg);
        if (msg.t === 'state') this.state = msg.s;
        this.waiters = this.waiters.filter((w) => !w(msg));
      };
      ws.onclose = (e) => {
        this.closed = e.code;
      };
    });
  }
  send(action) {
    this.ws.send(JSON.stringify(action));
  }
  // Attend un message qui satisfait le prédicat (ou un état déjà présent).
  until(pred, timeout = 5000, label = '') {
    if (this.state && pred({ t: 'state', s: this.state })) return Promise.resolve(this.state);
    return new Promise((resolve, reject) => {
      const timer = setTimeout(() => reject(new Error(`délai dépassé (${this.auth.name}) ${label} ; manche : ${JSON.stringify({ ...this.state?.round, hand: undefined, answers: undefined })} ; derniers messages : ${JSON.stringify(this.messages.slice(-3)).slice(0, 600)}`)), timeout);
      this.waiters.push((msg) => {
        if (!pred(msg)) return false;
        clearTimeout(timer);
        resolve(msg.t === 'state' ? msg.s : msg);
        return true;
      });
    });
  }
  untilState(pred, timeout, label = pred.toString()) {
    return this.until((m) => m.t === 'state' && pred(m.s), timeout, label);
  }
  async request(action) {
    const ref = Math.random().toString(36).slice(2);
    const reply = this.until((m) => (m.t === 'ack' || m.t === 'error') && m.ref === ref, 5000, JSON.stringify(action));
    this.send({ ...action, ref });
    return reply;
  }
  close() {
    this.ws.close();
  }
}

async function makeRoom(names) {
  newIp();
  const created = await api('/api/rooms', { name: names[0] });
  assert.equal(created.status, 201, JSON.stringify(created.body));
  const code = created.body.code;
  const auths = [{ ...created.body, name: names[0] }];
  for (const name of names.slice(1)) {
    const j = await api(`/api/rooms/${code}/join`, { name });
    assert.equal(j.status, 200, JSON.stringify(j.body));
    auths.push({ ...j.body, name });
  }
  const clients = auths.map((a) => new Client(code, a));
  await Promise.all(clients.map((c) => c.open()));
  await Promise.all(clients.map((c) => c.untilState((s) => s.players.length === names.length && s.players.every((p) => p.connected))));
  return { code, clients };
}

test('API : création, code valide, refus des codes invalides, pseudos en double et origines inconnues', async () => {
  const created = await api('/api/rooms', { name: 'Inès' });
  assert.equal(created.status, 201);
  assert.match(created.body.code, /^[A-Z]{3}\d{3}$/);
  assert.ok(created.body.token.length >= 40);
  assert.equal((await api(`/api/rooms/${created.body.code}/peek`)).body.players, 1);
  assert.equal((await api('/api/rooms/ZZZ000/join', { name: 'X' })).body.code, 'ROOM_NOT_FOUND');
  assert.equal((await api('/api/rooms/abc/join', { name: 'X' })).body.code, 'ROOM_NOT_FOUND');
  assert.equal((await api(`/api/rooms/${created.body.code}/join`, { name: ' INES ' })).body.code, 'NAME_TAKEN');
  assert.equal((await api(`/api/rooms/${created.body.code}/join`, { name: '' })).body.code, 'NAME_EMPTY');
  assert.equal((await api('/api/rooms', { name: 'Pirate' }, { origin: 'https://evil.example' })).status, 403);
});

test('salle complète : la 11e joueuse est refusée', async () => {
  newIp();
  const created = await api('/api/rooms', { name: 'Hôte' });
  for (let i = 1; i < 10; i++) assert.equal((await api(`/api/rooms/${created.body.code}/join`, { name: `J${i}` })).status, 200);
  const full = await api(`/api/rooms/${created.body.code}/join`, { name: 'Onze' });
  assert.equal(full.status, 409);
  assert.equal(full.body.code, 'ROOM_FULL');
});

test('jeton invalide : connexion refusée', async () => {
  const created = await api('/api/rooms', { name: 'Maya' });
  const c = new Client(created.body.code, { token: 'faux', name: 'faux' });
  await c.open();
  const bye = await c.until((m) => m.t === 'bye');
  assert.equal(bye.code, 'BAD_TOKEN');
});

test('partie complète à 4 : synchro, secret des mains et des propriétaires, votes, reconnexion, 10 manches', { timeout: 120_000 }, async () => {
  const { code, clients } = await makeRoom(['Alice', 'Bianca', 'Chloé', 'Dalia']);
  const [host, ...others] = clients;
  const ids = Object.fromEntries(clients.map((c) => [c.auth.playerId, c]));

  // Statut prête synchronisé chez tout le monde.
  for (const c of others) c.send({ t: 'ready' });
  await Promise.all(clients.map((c) => c.untilState((s) => s.canStart?.ok)));
  assert.equal((await others[0].request({ t: 'start' })).code, 'NOT_HOST');
  host.send({ t: 'config', config: { pickSeconds: 0, voteSeconds: 0, resultsSeconds: 0 } });
  await host.untilState((s) => s.config.pickSeconds === 0);
  host.send({ t: 'start' });

  const late = await api(`/api/rooms/${code}/join`, { name: 'Retard' });
  assert.equal(late.body.code, 'GAME_STARTED');

  const totals = {};
  for (let n = 1; n <= 10; n++) {
    const states = await Promise.all(clients.map((c) => c.untilState((s) => s.round?.n === n && s.round.phase === 'pick')));
    // Même situation pour toutes, 10 cartes distinctes chacune.
    assert.equal(new Set(states.map((s) => s.round.situation.id)).size, 1);
    for (const s of states) {
      assert.equal(s.round.hand.length, 10);
      assert.equal(new Set(s.round.hand.map((c) => c.id)).size, 10);
    }

    if (n === 3) {
      // Déconnexion puis reconnexion de Dalia avec son jeton : même main, partie intacte.
      const dalia = clients[3];
      const before = dalia.state.round.hand.map((c) => c.id);
      dalia.close();
      await host.untilState((s) => s.players.find((p) => p.name === 'Dalia').connected === false);
      const again = new Client(code, dalia.auth);
      await again.open();
      const s = await again.untilState((st) => st.round?.n === 3);
      assert.deepEqual(s.round.hand.map((c) => c.id), before);
      clients[3] = again;
      ids[dalia.auth.playerId] = again;
    }

    // Carte hors main refusée.
    const foreign = states[1].round.hand.find((c) => !states[0].round.hand.some((h) => h.id === c.id));
    // Contrôles d'actions invalides sur les deux premières manches.
    const checks = n <= 2;
    if (checks) assert.equal((await clients[0].request({ t: 'pick', cardId: foreign.id })).code, 'CARD_NOT_IN_HAND');

    const picks = {};
    for (const c of clients) {
      const card = c.state.round.hand[n % 10];
      picks[c.auth.playerId] = card.id;
      const res = await c.request({ t: 'pick', cardId: card.id });
      assert.equal(res.t, 'ack');
      if (checks && c === clients[0]) {
        // Une fois validé, on ne peut plus changer.
        const other = c.state.round.hand.find((h) => h.id !== card.id);
        assert.equal((await c.request({ t: 'pick', cardId: other.id })).code, 'ALREADY_PICKED');
      }
    }

    const votes = await Promise.all(clients.map((c) => c.untilState((s) => s.round?.n === n && s.round.phase === 'vote')));
    for (const s of votes) {
      assert.equal(s.round.answers.length, 4);
      const json = JSON.stringify(s.round);
      for (const pid of Object.keys(ids)) assert.ok(!json.includes(pid), 'un identifiant de joueuse est visible pendant le vote');
      assert.equal(s.round.result, undefined);
    }
    // Tout le monde vote pour la réponse « 1 » sauf sa propriétaire, qui vote « 2 ».
    for (const c of clients) {
      const s = c.state.round;
      const mine = s.myAnswer;
      if (checks) assert.equal((await c.request({ t: 'vote', aid: mine })).code, 'SELF_VOTE');
      const target = s.answers.find((a) => a.label === '1').aid === mine ? s.answers.find((a) => a.label === '2') : s.answers.find((a) => a.label === '1');
      const voted = await c.request({ t: 'vote', aid: target.aid });
      assert.equal(voted.t, 'ack', JSON.stringify(voted));
      if (checks && c === clients[0]) {
        const third = s.answers.find((a) => a.aid !== target.aid && a.aid !== mine);
        assert.equal((await c.request({ t: 'vote', aid: third.aid })).code, 'ALREADY_VOTED');
      }
    }

    const results = await Promise.all(clients.map((c) => c.untilState((s) => s.round?.n === n && s.round.phase === 'results')));
    const r = results[0].round;
    const winnerAid = r.answers.find((a) => a.label === '1').aid;
    assert.deepEqual(r.result.winners, [winnerAid]);
    assert.equal(r.result.counts[winnerAid], 3);
    const winner = r.result.owners[winnerAid];
    assert.equal(picks[winner], r.answers.find((a) => a.aid === winnerAid).card.id);
    totals[winner] = (totals[winner] || 0) + 1;
    for (const s of results) for (const p of s.players) assert.equal(p.score, totals[p.id] || 0);

    host.send({ t: 'next' });
  }

  const finals = await Promise.all(clients.map((c) => c.untilState((s) => s.status === 'finished')));
  for (const s of finals) {
    assert.equal(s.history.length, 10);
    assert.equal(s.players.reduce((sum, p) => sum + p.score, 0), 10);
  }
  // Les états reçus par chaque joueuse avant les résultats n'ont jamais contenu de propriétaire.
  for (const c of clients) {
    for (const m of c.messages) {
      if (m.t !== 'state' || !m.s.round || m.s.round.phase === 'results') continue;
      assert.equal(m.s.round.result, undefined);
    }
  }
  // Rejouer : retour au salon, scores remis à zéro.
  host.send({ t: 'replay' });
  const lobby = await others[0].untilState((s) => s.status === 'lobby');
  assert.ok(lobby.players.every((p) => p.score === 0));
  clients.forEach((c) => c.close());
});

test('chrono : manche qui avance seule quand une joueuse ne répond pas', { timeout: 60_000 }, async () => {
  const { clients } = await makeRoom(['Eva', 'Fanny', 'Gaby']);
  const [host, b, c] = clients;
  host.send({ t: 'config', config: { pickSeconds: 30, voteSeconds: 20 } });
  b.send({ t: 'ready' });
  c.send({ t: 'ready' });
  await host.untilState((s) => s.canStart?.ok && s.config.pickSeconds === 30);
  host.send({ t: 'start' });
  const s = await host.untilState((st) => st.round?.phase === 'pick');
  assert.ok(s.round.deadline > Date.now() + 25_000);
  // L'hôte débloque la manche sans attendre Gaby (même règle que l'échéance du chrono).
  host.send({ t: 'pick', cardId: s.round.hand[0].id });
  b.send({ t: 'pick', cardId: b.state.round.hand[0].id });
  await host.untilState((st) => st.round.progress?.done === 2);
  host.send({ t: 'skip' });
  const v = await c.untilState((st) => st.round?.phase === 'vote');
  assert.deepEqual(v.round.notice, { kind: 'pick_missed', names: ['Gaby'] });
  assert.equal(v.round.canVote, true);
  clients.forEach((x) => x.close());
});

test('limiteur de débit : trop de créations de salles depuis la même adresse', async () => {
  newIp();
  const statuses = [];
  for (let i = 0; i < 12; i++) statuses.push((await api('/api/rooms', { name: `Spam${i}` })).status);
  assert.deepEqual(statuses.slice(0, 10), Array(10).fill(201));
  assert.equal(statuses[11], 429);
});

test('limiteur de débit : une connexion qui inonde le serveur est freinée', async () => {
  const { clients } = await makeRoom(['Iris', 'Jade']);
  const [a] = clients;
  for (let i = 0; i < 400; i++) a.send({ t: 'ready', value: i % 2 === 0 });
  const err = await a.until((m) => m.t === 'error' && m.code === 'RATE_LIMITED');
  assert.equal(err.code, 'RATE_LIMITED');
  clients.forEach((c) => c.close());
});

// Tests lents : ils attendent les vraies alarmes du Durable Object (chrono et délai de grâce).
test('alarme : le chrono de sélection expire réellement côté serveur', { timeout: 60_000 }, async () => {
  const { clients } = await makeRoom(['Kim', 'Lou', 'Mia']);
  const [host, b, c] = clients;
  host.send({ t: 'config', config: { pickSeconds: 30, voteSeconds: 20 } });
  b.send({ t: 'ready' });
  c.send({ t: 'ready' });
  await host.untilState((s) => s.canStart?.ok && s.config.pickSeconds === 30);
  host.send({ t: 'start' });
  await host.untilState((s) => s.round?.phase === 'pick');
  host.send({ t: 'pick', cardId: host.state.round.hand[0].id });
  b.send({ t: 'pick', cardId: b.state.round.hand[0].id });
  const v = await c.untilState((s) => s.round?.phase === 'vote', 40_000);
  assert.deepEqual(v.round.notice.names, ['Mia']);
  const r = await c.untilState((s) => s.round?.phase === 'results', 30_000);
  assert.equal(r.round.result.reason, 'vote_timeout');
  clients.forEach((x) => x.close());
});

test('alarme : une joueuse déconnectée n’est plus attendue après 45 s, puis revient', { timeout: 90_000 }, async () => {
  const { code, clients } = await makeRoom(['Nina', 'Olga', 'Paula']);
  const [host, b, c] = clients;
  host.send({ t: 'config', config: { pickSeconds: 0, voteSeconds: 0 } });
  b.send({ t: 'ready' });
  c.send({ t: 'ready' });
  await host.untilState((s) => s.canStart?.ok && s.config.pickSeconds === 0);
  host.send({ t: 'start' });
  await Promise.all(clients.map((x) => x.untilState((st) => st.round?.phase === 'pick')));
  c.close();
  host.send({ t: 'pick', cardId: host.state.round.hand[0].id });
  b.send({ t: 'pick', cardId: b.state.round.hand[0].id });
  const s = await host.untilState((st) => st.round?.phase === 'vote', 60_000);
  assert.equal(s.players.find((p) => p.name === 'Paula').absent, true);
  const back = new Client(code, c.auth);
  await back.open();
  const mine = await back.untilState((st) => st.round?.phase === 'vote');
  assert.equal(mine.players.find((p) => p.name === 'Paula').absent, false);
  assert.equal(mine.round.canVote, true);
  [host, b, back].forEach((x) => x.close());
});
