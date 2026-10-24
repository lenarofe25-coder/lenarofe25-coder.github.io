// Tests des règles du jeu sur le moteur pur (aucun réseau).
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import * as E from '../src/engine.js';
import { buildContent } from '../src/content.js';

const lib = (p) => JSON.parse(readFileSync(new URL(`../../jeu/data/${p}`, import.meta.url), 'utf8'));
const content = buildContent({ cards: lib('cards.json').cards, situations: lib('situations.json').situations });

// Générateur pseudo-aléatoire déterministe (mulberry32).
function seeded(seed = 42) {
  let a = seed;
  return () => {
    a |= 0;
    a = (a + 0x6d2b79f5) | 0;
    let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

function setup(n = 3, config = {}) {
  const clock = { now: 1_000_000 };
  const rng = seeded(7);
  const ctx = () => ({ now: clock.now, rng, content });
  const room = E.createRoom({ code: 'MDR482', now: clock.now, rng });
  const ids = [];
  for (let i = 0; i < n; i++) {
    const pid = `p${i}`;
    E.joinRoom(room, { pid, name: `Joueuse ${i}`, tokenHash: `h${i}`, now: clock.now });
    E.connect(room, pid, clock.now);
    ids.push(pid);
  }
  if (Object.keys(config).length) E.applyAction(room, 'p0', { t: 'config', config }, ctx());
  const act = (pid, action) => E.applyAction(room, pid, action, ctx());
  const start = () => {
    for (const pid of ids.slice(1)) act(pid, { t: 'ready' });
    act('p0', { t: 'start' });
  };
  return { room, ids, clock, ctx, act, start };
}

const round = (room) => room.game.round;
const ownerOf = (room, aid) => round(room).answers.find((a) => a.aid === aid).owner;
const pickAll = (room, ids, act) => {
  for (const pid of ids) if (round(room).hands[pid] && !round(room).picks[pid]) act(pid, { t: 'pick', cardId: round(room).hands[pid][0] });
};
// Chaque joueuse vote pour la première réponse qui n'est pas la sienne.
const voteAll = (room, ids, act) => {
  for (const pid of ids) {
    const target = round(room).answers.find((a) => a.owner !== pid);
    if (target && !round(room).votes[pid]) act(pid, { t: 'vote', aid: target.aid });
  }
};

const expectCode = (fn, code) => assert.throws(fn, (e) => e instanceof E.GameError && e.code === code);

test('bibliothèques : au moins 500 situations et 500 cartes actives, identifiants uniques', () => {
  const s = content.stats();
  assert.ok(s.activeSituations >= 500, `situations : ${s.activeSituations}`);
  assert.ok(s.activeCards >= 500, `cartes : ${s.activeCards}`);
  assert.equal(new Set(content.cards.map((c) => c.id)).size, content.cards.length);
  assert.equal(new Set(content.situations.map((c) => c.id)).size, content.situations.length);
});

test('pseudos : vides, trop longs et doublons (insensibles à la casse et aux accents) refusés', () => {
  const { room, clock } = setup(1);
  expectCode(() => E.joinRoom(room, { pid: 'x', name: '   ', tokenHash: 'x', now: clock.now }), 'NAME_EMPTY');
  expectCode(() => E.joinRoom(room, { pid: 'x', name: 'a'.repeat(21), tokenHash: 'x', now: clock.now }), 'NAME_TOO_LONG');
  expectCode(() => E.joinRoom(room, { pid: 'x', name: 'joueuse 0', tokenHash: 'x', now: clock.now }), 'NAME_TAKEN');
  E.joinRoom(room, { pid: 'l1', name: 'Léa', tokenHash: 'l1', now: clock.now });
  expectCode(() => E.joinRoom(room, { pid: 'l2', name: 'LEA', tokenHash: 'l2', now: clock.now }), 'NAME_TAKEN');
});

test('salle complète à 10 joueuses, partie commencée refusée', () => {
  const { room, clock, start } = setup(10);
  expectCode(() => E.joinRoom(room, { pid: 'x', name: 'Onzième', tokenHash: 'x', now: clock.now }), 'ROOM_FULL');
  start();
  expectCode(() => E.joinRoom(room, { pid: 'y', name: 'Retard', tokenHash: 'y', now: clock.now }), 'GAME_STARTED');
});

test('lancement réservé à l’hôte, au moins 2 joueuses prêtes', () => {
  const solo = setup(1);
  expectCode(() => solo.act('p0', { t: 'start' }), 'CANNOT_START');
  const { act } = setup(3);
  expectCode(() => act('p1', { t: 'start' }), 'NOT_HOST');
  act('p1', { t: 'ready' });
  expectCode(() => act('p0', { t: 'start' }), 'CANNOT_START'); // p2 pas prête
  act('p2', { t: 'ready' });
  act('p0', { t: 'start' });
});

test('distribution : 10 cartes distinctes par joueuse, mains privées, même situation pour toutes', () => {
  const { room, ids, start } = setup(6);
  start();
  const r = round(room);
  for (const pid of ids) {
    assert.equal(r.hands[pid].length, 10);
    assert.equal(new Set(r.hands[pid]).size, 10);
  }
  const views = ids.map((pid) => E.viewFor(room, pid, content));
  assert.equal(new Set(views.map((v) => v.round.situation.id)).size, 1);
  for (const v of views) {
    assert.deepEqual(v.round.hand.map((c) => c.id), r.hands[v.you]);
    const json = JSON.stringify(v);
    for (const other of ids.filter((x) => x !== v.you)) {
      const foreign = r.hands[other].filter((id) => !r.hands[v.you].includes(id));
      for (const id of foreign) assert.ok(!json.includes(`"${id}"`), `la vue de ${v.you} contient la carte ${id} de ${other}`);
    }
    assert.ok(!('hands' in v.round) && !('picks' in v.round));
  }
});

test('sélection : carte hors main refusée, choix verrouillé, idempotent, choix secret', () => {
  const { room, act, start } = setup(3);
  start();
  const r = round(room);
  const foreign = r.hands.p1.find((id) => !r.hands.p0.includes(id));
  expectCode(() => act('p0', { t: 'pick', cardId: foreign }), 'CARD_NOT_IN_HAND');
  act('p0', { t: 'pick', cardId: r.hands.p0[3] });
  act('p0', { t: 'pick', cardId: r.hands.p0[3] }); // requête répétée : sans effet
  expectCode(() => act('p0', { t: 'pick', cardId: r.hands.p0[4] }), 'ALREADY_PICKED');
  const v1 = E.viewFor(room, 'p1', content);
  assert.equal(v1.players.find((p) => p.id === 'p0').picked, true);
  assert.ok(!JSON.stringify(v1).includes(r.hands.p0[3]) || r.hands.p1.includes(r.hands.p0[3]));
  assert.deepEqual(v1.round.progress, { done: 1, total: 3 });
});

test('révélation anonyme puis vote : pas d’auto-vote, pas de double vote, réponse inconnue refusée', () => {
  const { room, ids, act, start } = setup(4);
  start();
  pickAll(room, ids, act);
  const r = round(room);
  assert.equal(r.phase, 'vote');
  assert.equal(r.answers.length, 4);
  for (const pid of ids) {
    const v = E.viewFor(room, pid, content);
    const json = JSON.stringify(v.round.answers);
    for (const other of ids) assert.ok(!json.includes(`"${other}"`), 'un identifiant de joueuse apparaît dans les réponses');
    assert.ok(!('result' in v.round));
    assert.equal(v.round.myAnswer, r.answers.find((a) => a.owner === pid).aid);
  }
  const mine = r.answers.find((a) => a.owner === 'p0');
  expectCode(() => act('p0', { t: 'vote', aid: mine.aid }), 'SELF_VOTE');
  expectCode(() => act('p0', { t: 'vote', aid: 'nope' }), 'BAD_ANSWER');
  const other = r.answers.find((a) => a.owner !== 'p0');
  act('p0', { t: 'vote', aid: other.aid });
  act('p0', { t: 'vote', aid: other.aid });
  const third = r.answers.find((a) => a.owner !== 'p0' && a.aid !== other.aid);
  expectCode(() => act('p0', { t: 'vote', aid: third.aid }), 'ALREADY_VOTED');
  // Les votes restent secrets pendant le vote.
  assert.ok(!JSON.stringify(E.viewFor(room, 'p1', content)).includes(`"myVote":"${other.aid}"`));
});

test('scores : une victoire nette rapporte 1 point, une égalité rapporte 1 point à chaque carte ex aequo', () => {
  const answers = [{ aid: 'a' }, { aid: 'b' }, { aid: 'c' }];
  assert.deepEqual(E.tallyVotes(answers, { x: 'a', y: 'a', z: 'b' }).winners, ['a']);
  assert.deepEqual(E.tallyVotes(answers, { x: 'a', y: 'b' }).winners, ['a', 'b']);
  assert.deepEqual(E.tallyVotes(answers, {}).winners, []);

  const { room, ids, act, start } = setup(3);
  start();
  pickAll(room, ids, act);
  const r = round(room);
  // p0 et p1 votent pour p2, p2 vote pour p0 → p2 gagne seule.
  const a = (owner) => r.answers.find((x) => x.owner === owner).aid;
  act('p0', { t: 'vote', aid: a('p2') });
  act('p1', { t: 'vote', aid: a('p2') });
  act('p2', { t: 'vote', aid: a('p0') });
  assert.equal(r.phase, 'results');
  assert.deepEqual(Object.fromEntries(ids.map((id) => [id, room.players[id].score])), { p0: 0, p1: 0, p2: 1 });
  // Toute action rejouée après la clôture ne change rien.
  expectCode(() => act('p0', { t: 'vote', aid: a('p1') }), 'BAD_PHASE');
  assert.equal(room.players.p2.score, 1);
  const v = E.viewFor(room, 'p0', content);
  assert.equal(v.round.result.owners[a('p2')], 'p2');

  act('p0', { t: 'next' });
  pickAll(room, ids, act);
  const r2 = round(room);
  const b = (owner) => r2.answers.find((x) => x.owner === owner).aid;
  act('p0', { t: 'vote', aid: b('p1') });
  act('p1', { t: 'vote', aid: b('p2') });
  act('p2', { t: 'vote', aid: b('p0') });
  assert.deepEqual(Object.fromEntries(ids.map((id) => [id, room.players[id].score])), { p0: 1, p1: 1, p2: 2 });
});

test('partie complète : exactement 10 manches, situations jamais répétées, classement final', () => {
  const { room, ids, act, start } = setup(4);
  start();
  const situations = [];
  let rounds = 0;
  while (room.status === 'playing') {
    rounds++;
    situations.push(round(room).situationId);
    pickAll(room, ids, act);
    voteAll(room, ids, act);
    assert.equal(round(room).phase, 'results');
    act('p0', { t: 'next' });
  }
  assert.equal(rounds, 10);
  assert.equal(room.status, 'finished');
  assert.equal(new Set(situations).size, 10);
  const total = ids.reduce((s, id) => s + room.players[id].score, 0);
  const history = room.game.history;
  assert.equal(history.length, 10);
  assert.equal(total, history.reduce((s, h) => s + h.winners.length, 0));
  const v = E.viewFor(room, 'p1', content);
  assert.equal(v.history.length, 10);
  assert.ok(v.history.every((h) => h.winners.every((w) => w.card.id)));
  // Hors partie, plus aucune action de jeu possible.
  expectCode(() => act('p0', { t: 'next' }), 'BAD_PHASE');
});

test('cartes renouvelées à chaque manche, sans redonner une carte déjà vue tant que possible', () => {
  const { room, ids, act, start } = setup(2);
  start();
  const seen = { p0: new Set(), p1: new Set() };
  for (let n = 0; n < 10; n++) {
    for (const pid of ids) {
      for (const id of round(room).hands[pid]) {
        assert.ok(!seen[pid].has(id), `carte ${id} redistribuée à ${pid}`);
        seen[pid].add(id);
      }
    }
    pickAll(room, ids, act);
    voteAll(room, ids, act);
    act('p0', { t: 'next' });
  }
});

test('humour noir : exclu par défaut, inclus si l’hôte l’active', () => {
  const dark = (cfg) => {
    const { room, ids, act, start } = setup(2, cfg);
    start();
    const cards = new Set();
    for (let n = 0; n < 10; n++) {
      for (const pid of ids) round(room).hands[pid].forEach((id) => cards.add(content.cardById(id).category));
      cards.add(content.situationById(round(room).situationId).category);
      pickAll(room, ids, act);
      voteAll(room, ids, act);
      act('p0', { t: 'next' });
    }
    return cards.has('humour-noir');
  };
  assert.equal(dark({}), false);
  assert.equal(dark({ darkHumor: true }), true);
});

test('chrono : la sélection se clôt à l’échéance, les retardataires passent leur tour (annoncé)', () => {
  const { room, act, start, clock, ctx } = setup(3, { pickSeconds: 30, voteSeconds: 20 });
  start();
  const r = round(room);
  act('p0', { t: 'pick', cardId: r.hands.p0[0] });
  act('p1', { t: 'pick', cardId: r.hands.p1[0] });
  clock.now += 29_000;
  E.tick(room, ctx());
  assert.equal(r.phase, 'pick');
  clock.now += 2_000;
  E.tick(room, ctx());
  assert.equal(r.phase, 'vote');
  assert.equal(r.answers.length, 2);
  assert.deepEqual(r.notice, { kind: 'pick_missed', names: ['Joueuse 2'] });
  // p2 n'a pas de carte mais peut voter ; p0 et p1 ne peuvent voter que pour l'autre.
  assert.equal(E.viewFor(room, 'p2', content).round.canVote, true);
  clock.now += 21_000;
  E.tick(room, ctx());
  assert.equal(r.phase, 'results');
  assert.equal(r.result.reason, 'vote_timeout');
  assert.deepEqual(r.result.winners, []);
});

test('moins de 2 réponses : manche sans vote ni point', () => {
  const { room, act, start, clock, ctx } = setup(3, { pickSeconds: 30 });
  start();
  act('p0', { t: 'pick', cardId: round(room).hands.p0[0] });
  clock.now += 31_000;
  E.tick(room, ctx());
  assert.equal(round(room).phase, 'results');
  assert.equal(round(room).result.reason, 'not_enough_answers');
  assert.equal(room.players.p0.score, 0);
});

test('déconnexion : la joueuse est attendue pendant le délai de grâce, puis n’est plus attendue', () => {
  const { room, act, start, clock, ctx } = setup(3, { pickSeconds: 0 });
  start();
  const r = round(room);
  E.disconnect(room, 'p2', clock.now);
  act('p0', { t: 'pick', cardId: r.hands.p0[0] });
  act('p1', { t: 'pick', cardId: r.hands.p1[0] });
  assert.equal(r.phase, 'pick'); // p2 encore dans son délai de grâce
  clock.now += E.LIMITS.disconnectGraceMs;
  E.tick(room, ctx());
  assert.equal(room.players.p2.absent, true);
  assert.equal(r.phase, 'vote');
  // Retour de p2 : elle retrouve sa place et ses points, sans réinitialiser la partie.
  E.connect(room, 'p2', clock.now);
  assert.equal(room.players.p2.absent, false);
  assert.equal(room.status, 'playing');
  assert.equal(E.viewFor(room, 'p2', content).round.phase, 'vote');
});

test('reconnexion pendant la sélection : la joueuse retrouve exactement sa main', () => {
  const { room, start, clock } = setup(2);
  start();
  const hand = [...round(room).hands.p1];
  E.disconnect(room, 'p1', clock.now);
  clock.now += 10_000;
  E.connect(room, 'p1', clock.now);
  assert.deepEqual(E.viewFor(room, 'p1', content).round.hand.map((c) => c.id), hand);
});

test('hôte : transfert si elle quitte ou reste absente ; pause automatique sous 2 joueuses présentes', () => {
  const { room, act, start, clock, ctx } = setup(3);
  start();
  act('p0', { t: 'leave' });
  assert.equal(room.hostId, 'p1');
  E.disconnect(room, 'p1', clock.now);
  clock.now += E.LIMITS.disconnectGraceMs + 1;
  E.tick(room, ctx());
  assert.equal(room.hostId, 'p2');
  assert.equal(room.game.paused?.by, 'auto');
  E.connect(room, 'p1', clock.now);
  assert.equal(room.game.paused, null);
});

test('la partie se termine proprement s’il reste moins de 2 joueuses', () => {
  const { room, act, start } = setup(2);
  start();
  act('p1', { t: 'leave' });
  assert.equal(room.status, 'finished');
  assert.equal(room.game.endReason, 'not_enough_players');
});

test('pause, reprise et arrêt par l’hôte ; les actions sont bloquées pendant la pause', () => {
  const { room, act, start, clock, ctx } = setup(2, { pickSeconds: 60 });
  start();
  clock.now += 20_000;
  act('p0', { t: 'pause' });
  expectCode(() => act('p1', { t: 'pause' }), 'NOT_HOST');
  expectCode(() => act('p1', { t: 'pick', cardId: round(room).hands.p1[0] }), 'PAUSED');
  clock.now += 600_000;
  E.tick(room, ctx());
  assert.equal(round(room).phase, 'pick');
  act('p0', { t: 'resume' });
  assert.equal(round(room).deadline, clock.now + 40_000);
  act('p0', { t: 'stop' });
  assert.equal(room.status, 'finished');
  assert.equal(room.game.endReason, 'stopped');
});

test('l’hôte peut débloquer une phase sans chrono', () => {
  const { room, act, start } = setup(3, { pickSeconds: 0, voteSeconds: 0 });
  start();
  act('p0', { t: 'pick', cardId: round(room).hands.p0[0] });
  act('p1', { t: 'pick', cardId: round(room).hands.p1[0] });
  expectCode(() => act('p1', { t: 'skip' }), 'NOT_HOST');
  act('p0', { t: 'skip' });
  assert.equal(round(room).phase, 'vote');
});

test('rejouer : scores remis à zéro, joueuses conservées, nouvelle partie', () => {
  const { room, ids, act, start } = setup(3, { rounds: 5 });
  start();
  const firstId = room.game.id;
  while (room.status === 'playing') {
    pickAll(room, ids, act);
    voteAll(room, ids, act);
    act('p0', { t: 'next' });
  }
  act('p0', { t: 'replay' });
  assert.equal(room.status, 'lobby');
  assert.equal(room.order.length, 3);
  assert.ok(ids.every((id) => room.players[id].score === 0 && !room.players[id].ready));
  start();
  assert.notEqual(room.game.id, firstId);
});

test('réglages : seules les valeurs prévues sont acceptées, uniquement par l’hôte', () => {
  const { act, room } = setup(2);
  expectCode(() => act('p0', { t: 'config', config: { pickSeconds: 7 } }), 'BAD_CONFIG');
  expectCode(() => act('p1', { t: 'config', config: { pickSeconds: 30 } }), 'NOT_HOST');
  act('p0', { t: 'config', config: { pickSeconds: 30, darkHumor: true } });
  assert.equal(room.config.pickSeconds, 30);
  assert.equal(room.config.darkHumor, true);
});

test('expiration : salle fermée après inactivité sans personne connectée', () => {
  const { room, ids, clock, ctx } = setup(2);
  for (const id of ids) E.disconnect(room, id, clock.now);
  clock.now += E.LIMITS.idleExpiryMs + 1;
  E.tick(room, ctx());
  assert.equal(room.status, 'closed');
  expectCode(() => E.joinRoom(room, { pid: 'z', name: 'Zoé', tokenHash: 'z', now: clock.now }), 'ROOM_EXPIRED');
});

test('carte retirée de la bibliothèque : affichée comme indisponible au lieu de casser la vue', () => {
  const c = content.cardById('c-9999');
  assert.equal(c.missing, true);
  assert.equal(c.text, 'Carte indisponible');
});
