// Moteur de jeu MDR : machine à états pure (aucune E/S). Le Durable Object l'appelle
// pour chaque action, persiste l'état et diffuse à chaque joueuse sa propre vue.
// Toutes les règles (droit de jouer, de voter, points) sont décidées ici, jamais côté client.

export const LIMITS = {
  minPlayers: 2,
  maxPlayers: 10,
  handSize: 10,
  nameMax: 20,
  disconnectGraceMs: 45_000, // en partie : au-delà, la joueuse est « absente » et n'est plus attendue
  lobbyGraceMs: 120_000, // au salon : au-delà, la place est libérée
  idleExpiryMs: 30 * 60_000, // salle vide d'activité
  maxLifetimeMs: 12 * 3600_000,
};

export const CONFIG_CHOICES = {
  rounds: [5, 10, 15],
  pickSeconds: [0, 30, 45, 60, 90, 120],
  voteSeconds: [0, 20, 30, 45, 60],
  resultsSeconds: [0, 8, 12, 20],
};

export const DEFAULT_CONFIG = {
  rounds: 10,
  pickSeconds: 60,
  voteSeconds: 45,
  resultsSeconds: 12,
};

export class GameError extends Error {
  constructor(code, message) {
    super(message);
    this.code = code;
  }
}

const fail = (code, message) => {
  throw new GameError(code, message);
};

// ── utilitaires ─────────────────────────────────────────────

// Caractères de contrôle et invisibles (espaces de largeur nulle, marques de direction…).
const INVISIBLE_CHARS = new RegExp('[\\u0000-\\u001f\\u007f-\\u009f\\u200b-\\u200f\\u2028-\\u202e\\u2060-\\u206f\\ufeff]', 'g');

export function normalizeName(raw) {
  if (typeof raw !== 'string') return '';
  return raw
    .normalize('NFKC')
    .replace(INVISIBLE_CHARS, '')
    .replace(/\s+/g, ' ')
    .trim();
}

// Clé de comparaison : « Léa », « lea » et « LÉA » sont le même pseudo.
export const nameKey = (name) =>
  normalizeName(name)
    .normalize('NFD')
    .replace(/[̀-ͯ]/g, '')
    .toLowerCase();

export function validateName(raw) {
  const name = normalizeName(raw);
  if (!name) fail('NAME_EMPTY', 'Choisis un pseudo.');
  if ([...name].length > LIMITS.nameMax) fail('NAME_TOO_LONG', `Ton pseudo doit faire ${LIMITS.nameMax} caractères maximum.`);
  if (!/[\p{L}\p{N}\p{Extended_Pictographic}]/u.test(name)) fail('NAME_INVALID', 'Ton pseudo doit contenir au moins une lettre ou un chiffre.');
  return name;
}

// rng() renvoie un flottant dans [0, 1). Injecté pour des tests déterministes.
export function shuffle(list, rng) {
  const a = list.slice();
  for (let i = a.length - 1; i > 0; i--) {
    const j = Math.floor(rng() * (i + 1));
    [a[i], a[j]] = [a[j], a[i]];
  }
  return a;
}

export function sample(list, n, rng) {
  return shuffle(list, rng).slice(0, n);
}

const ID_ALPHABET = 'abcdefghijkmnpqrstuvwxyz23456789';
export const randomId = (rng, len = 10) =>
  Array.from({ length: len }, () => ID_ALPHABET[Math.floor(rng() * ID_ALPHABET.length)]).join('');

// ── salle ───────────────────────────────────────────────────

export function createRoom({ code, now, rng }) {
  return {
    v: 1,
    code,
    createdAt: now,
    lastActivity: now,
    status: 'lobby', // lobby | playing | finished | closed
    hostId: null,
    config: { ...DEFAULT_CONFIG },
    players: {},
    order: [],
    game: null,
    gameCount: 0,
    seed: randomId(rng, 6),
  };
}

const activePlayers = (room) => room.order.map((id) => room.players[id]).filter((p) => p && !p.left);
const presentPlayers = (room) => activePlayers(room).filter((p) => !p.absent);
const participants = (room) => activePlayers(room).filter((p) => p.inGame);

export function joinRoom(room, { pid, name: rawName, tokenHash, now }) {
  if (room.status === 'closed') fail('ROOM_EXPIRED', 'Cette partie est terminée ou a expiré.');
  if (room.status === 'finished') fail('GAME_FINISHED', 'Cette partie est déjà terminée.');
  if (room.status === 'playing') fail('GAME_STARTED', 'La partie a déjà commencé. Demande à l’hôte de lancer une nouvelle partie.');
  const name = validateName(rawName);
  const players = activePlayers(room);
  if (players.length >= LIMITS.maxPlayers) fail('ROOM_FULL', `La salle est complète (${LIMITS.maxPlayers} joueuses maximum).`);
  const key = nameKey(name);
  if (players.some((p) => nameKey(p.name) === key)) fail('NAME_TAKEN', 'Ce pseudo est déjà pris dans cette salle.');
  room.players[pid] = {
    id: pid,
    name,
    tokenHash,
    joinedAt: now,
    ready: false,
    connected: false,
    disconnectedAt: now, // pas encore connectée en WebSocket
    absent: false,
    left: false,
    inGame: false,
    score: 0,
    roundsWon: 0,
  };
  room.order.push(pid);
  if (!room.hostId || !room.players[room.hostId] || room.players[room.hostId].left) room.hostId = pid;
  room.lastActivity = now;
  return room.players[pid];
}

export function findPlayerByToken(room, tokenHash) {
  return Object.values(room.players).find((p) => p.tokenHash === tokenHash && !p.left) || null;
}

function transferHostIfNeeded(room) {
  const host = room.players[room.hostId];
  if (host && !host.left && !host.absent) return;
  const candidates = activePlayers(room);
  const next = candidates.find((p) => p.connected) || candidates.find((p) => !p.absent);
  if (next) room.hostId = next.id;
}

function removeFromLobby(room, pid) {
  delete room.players[pid];
  room.order = room.order.filter((id) => id !== pid);
  if (room.hostId === pid) room.hostId = null;
  transferHostIfNeeded(room);
  if (!room.hostId && room.order.length) room.hostId = room.order[0];
}

export function connect(room, pid, now) {
  const p = room.players[pid];
  if (!p || p.left) return false;
  p.connected = true;
  p.disconnectedAt = null;
  const wasAbsent = p.absent;
  p.absent = false;
  room.lastActivity = now;
  if (wasAbsent) transferHostIfNeeded(room);
  if (room.status === 'playing') autoResumeIfPossible(room, now);
  return true;
}

export function disconnect(room, pid, now) {
  const p = room.players[pid];
  if (!p || p.left || !p.connected) return false;
  p.connected = false;
  p.disconnectedAt = now;
  room.lastActivity = now;
  return true;
}

// ── configuration ───────────────────────────────────────────

export function sanitizeConfig(input, current = DEFAULT_CONFIG) {
  const out = { ...current };
  if (input && typeof input === 'object') {
    for (const key of Object.keys(CONFIG_CHOICES)) {
      if (key in input) {
        const v = Number(input[key]);
        if (!CONFIG_CHOICES[key].includes(v)) fail('BAD_CONFIG', 'Réglage invalide.');
        out[key] = v;
      }
    }
  }
  return out;
}

// ── contenu ─────────────────────────────────────────────────

function pickSituation(room, ctx) {
  const pool = ctx.content.situations.filter((s) => s.active);
  if (!pool.length) fail('NO_CONTENT', 'Aucune situation disponible.');
  const used = new Set(room.game.usedSituations);
  let fresh = pool.filter((s) => !used.has(s.id));
  if (!fresh.length) {
    // Bibliothèque épuisée : on recommence le cycle plutôt que de bloquer la partie.
    room.game.usedSituations = [];
    fresh = pool;
  }
  const s = fresh[Math.floor(ctx.rng() * fresh.length)];
  room.game.usedSituations.push(s.id);
  return s.id;
}

// 10 memes distincts par joueuse, tirées indépendamment ; on évite de redonner
// à une joueuse des cartes qu'elle a déjà eues dans la partie tant que c'est possible.
export function dealHand(pool, seenIds, size, rng) {
  const seen = new Set(seenIds);
  const fresh = pool.filter((id) => !seen.has(id));
  const hand = sample(fresh, size, rng);
  if (hand.length < size) {
    const inHand = new Set(hand);
    hand.push(...sample(pool.filter((id) => !inHand.has(id)), size - hand.length, rng));
  }
  return hand;
}

function cardPool(room, ctx) {
  return ctx.content.cards.filter((c) => c.active).map((c) => c.id);
}

// ── partie ──────────────────────────────────────────────────

const requireHost = (room, pid) => {
  if (room.hostId !== pid) fail('NOT_HOST', 'Seule l’hôte peut faire ça.');
};

const deadlineIn = (now, seconds) => (seconds > 0 ? now + seconds * 1000 : null);

export function canStart(room) {
  const present = presentPlayers(room);
  if (present.length < LIMITS.minPlayers) return { ok: false, reason: `Il faut au moins ${LIMITS.minPlayers} joueuses.` };
  const notReady = present.filter((p) => p.id !== room.hostId && !p.ready);
  if (notReady.length) return { ok: false, reason: `En attente : ${notReady.map((p) => p.name).join(', ')}.` };
  return { ok: true };
}

function startGame(room, ctx) {
  const check = canStart(room);
  if (!check.ok) fail('CANNOT_START', check.reason);
  const pool = cardPool(room, ctx);
  if (pool.length < LIMITS.handSize) fail('NO_CONTENT', 'Pas assez de memes disponibles.');
  room.gameCount += 1;
  room.status = 'playing';
  room.game = {
    id: randomId(ctx.rng, 12),
    startedAt: ctx.now,
    usedSituations: [],
    seen: {},
    history: [],
    round: null,
    paused: null,
    endReason: null,
  };
  for (const p of activePlayers(room)) {
    p.inGame = !p.absent;
    p.score = 0;
    p.roundsWon = 0;
    p.ready = false;
  }
  startRound(room, ctx, 1);
}

function startRound(room, ctx, n) {
  const g = room.game;
  const situationId = pickSituation(room, ctx);
  const pool = cardPool(room, ctx);
  const hands = {};
  for (const p of participants(room)) {
    hands[p.id] = dealHand(pool, g.seen[p.id] || [], LIMITS.handSize, ctx.rng);
    g.seen[p.id] = [...(g.seen[p.id] || []), ...hands[p.id]];
  }
  g.round = {
    n,
    situationId,
    phase: 'pick',
    startedAt: ctx.now,
    deadline: deadlineIn(ctx.now, room.config.pickSeconds),
    hands,
    picks: {},
    answers: [],
    votes: {},
    result: null,
    notice: null,
  };
  autoPauseIfNeeded(room, ctx.now);
}

// Joueuses attendues pour terminer la phase de sélection.
const expectedPickers = (room) => participants(room).filter((p) => !p.absent && room.game.round.hands[p.id]);

// Joueuses pouvant voter : présentes et ayant au moins une réponse qui n'est pas la leur.
function eligibleVoters(room) {
  const r = room.game.round;
  return participants(room).filter((p) => !p.absent && r.answers.some((a) => a.owner !== p.id));
}

function maybeEndPick(room, ctx, forced) {
  const r = room.game.round;
  if (r.phase !== 'pick') return;
  const waiting = expectedPickers(room).filter((p) => !r.picks[p.id]);
  if (waiting.length && !forced) return;
  const missed = participants(room).filter((p) => !r.picks[p.id]).map((p) => p.name);
  const picks = Object.entries(r.picks);
  r.answers = shuffle(picks, ctx.rng).map(([owner, cardId], i) => ({
    aid: randomId(ctx.rng, 8),
    label: String(i + 1), // repère neutre : des chiffres, pour ne pas évoquer l'initiale d'une joueuse
    owner,
    cardId,
  }));
  r.notice = missed.length ? { kind: 'pick_missed', names: missed } : null;
  if (r.answers.length < 2) {
    finishRound(room, ctx, 'not_enough_answers');
    return;
  }
  r.phase = 'vote';
  r.deadline = deadlineIn(ctx.now, room.config.voteSeconds);
  if (!eligibleVoters(room).length) finishRound(room, ctx, 'no_voters');
}

function maybeEndVote(room, ctx, forced) {
  const r = room.game.round;
  if (r.phase !== 'vote') return;
  const waiting = eligibleVoters(room).filter((p) => !r.votes[p.id]);
  if (waiting.length && !forced) return;
  finishRound(room, ctx, waiting.length ? 'vote_timeout' : null);
}

// Calcul des points d'une manche : chaque carte au nombre de votes maximal (> 0)
// rapporte 1 point à sa propriétaire. Exporté pour être testé isolément.
export function tallyVotes(answers, votes) {
  const counts = Object.fromEntries(answers.map((a) => [a.aid, 0]));
  for (const aid of Object.values(votes)) if (aid in counts) counts[aid] += 1;
  const max = Math.max(0, ...Object.values(counts));
  const winners = max > 0 ? answers.filter((a) => counts[a.aid] === max).map((a) => a.aid) : [];
  return { counts, max, winners };
}

function finishRound(room, ctx, reason) {
  const g = room.game;
  const r = g.round;
  if (r.phase === 'results') return; // idempotent : jamais deux attributions de points
  const { counts, winners } = tallyVotes(r.answers, r.votes);
  const points = {};
  for (const aid of winners) {
    const a = r.answers.find((x) => x.aid === aid);
    const p = room.players[a.owner];
    if (!p) continue;
    p.score += 1;
    p.roundsWon += 1;
    points[a.owner] = 1;
  }
  r.result = { counts, winners, points, reason };
  r.phase = 'results';
  r.deadline = deadlineIn(ctx.now, room.config.resultsSeconds);
  g.history.push({
    n: r.n,
    situationId: r.situationId,
    winners: winners.map((aid) => {
      const a = r.answers.find((x) => x.aid === aid);
      return { cardId: a.cardId, owner: a.owner, votes: counts[aid] };
    }),
    reason,
  });
}

function nextRound(room, ctx) {
  const r = room.game.round;
  if (r.phase !== 'results') fail('BAD_PHASE', 'La manche n’est pas terminée.');
  if (r.n >= room.config.rounds) endGame(room, ctx, 'completed');
  else startRound(room, ctx, r.n + 1);
}

function endGame(room, ctx, reason) {
  room.status = 'finished';
  room.game.endReason = reason;
  room.game.endedAt = ctx.now;
  room.game.paused = null;
  if (room.game.round) room.game.round.deadline = null;
}

// Moins de 2 joueuses présentes : la partie se met en pause toute seule au lieu de tourner à vide.
function autoPauseIfNeeded(room, now) {
  const g = room.game;
  if (!g || room.status !== 'playing' || g.paused) return;
  if (participants(room).filter((p) => !p.absent).length < LIMITS.minPlayers) pauseGame(room, now, 'auto');
}

function autoResumeIfPossible(room, now) {
  const g = room.game;
  if (g?.paused?.by === 'auto' && participants(room).filter((p) => !p.absent).length >= LIMITS.minPlayers) resumeGame(room, now);
}

function pauseGame(room, now, by) {
  const r = room.game.round;
  room.game.paused = { by, at: now, remainingMs: r.deadline ? Math.max(0, r.deadline - now) : null };
  r.deadline = null;
}

function resumeGame(room, now) {
  const { remainingMs } = room.game.paused;
  room.game.round.deadline = remainingMs == null ? null : now + Math.max(remainingMs, 5000);
  room.game.paused = null;
}

function resetToLobby(room) {
  room.status = 'lobby';
  room.game = null;
  for (const id of [...room.order]) {
    const p = room.players[id];
    if (p.left) {
      delete room.players[id];
      room.order = room.order.filter((x) => x !== id);
    } else {
      p.ready = false;
      p.inGame = false;
      p.score = 0;
      p.roundsWon = 0;
    }
  }
  transferHostIfNeeded(room);
}

function leave(room, pid, ctx) {
  const p = room.players[pid];
  if (room.status === 'lobby') {
    removeFromLobby(room, pid);
    return;
  }
  p.left = true;
  p.connected = false;
  transferHostIfNeeded(room);
  if (room.status !== 'playing') return;
  if (participants(room).length < LIMITS.minPlayers) {
    endGame(room, ctx, 'not_enough_players');
    return;
  }
  settle(room, ctx);
}

// Après un changement de présence, une phase peut être devenue complète.
function settle(room, ctx) {
  if (room.status !== 'playing' || room.game.paused) return;
  const r = room.game.round;
  if (r.phase === 'pick') maybeEndPick(room, ctx, false);
  if (r.phase === 'vote') maybeEndVote(room, ctx, false);
}

// ── actions des joueuses ────────────────────────────────────

export function applyAction(room, pid, action, ctx) {
  const p = room.players[pid];
  if (!p || p.left) fail('NOT_IN_ROOM', 'Tu ne fais plus partie de cette salle.');
  if (!action || typeof action.t !== 'string') fail('BAD_REQUEST', 'Requête invalide.');
  room.lastActivity = ctx.now;
  const g = room.game;
  const r = g?.round;
  const playing = room.status === 'playing';
  const requirePlaying = () => {
    if (!playing) fail('BAD_PHASE', 'Aucune manche en cours.');
    if (g.paused) fail('PAUSED', 'La partie est en pause.');
  };

  switch (action.t) {
    case 'ready': {
      if (room.status !== 'lobby') fail('BAD_PHASE', 'La partie a déjà commencé.');
      p.ready = action.value !== false;
      return;
    }
    case 'config': {
      requireHost(room, pid);
      if (room.status !== 'lobby') fail('BAD_PHASE', 'Les réglages se changent au salon.');
      room.config = sanitizeConfig(action.config, room.config);
      return;
    }
    case 'kick': {
      requireHost(room, pid);
      if (room.status !== 'lobby') fail('BAD_PHASE', 'On ne peut retirer quelqu’un qu’au salon.');
      if (action.pid === pid || !room.players[action.pid]) fail('BAD_REQUEST', 'Joueuse introuvable.');
      removeFromLobby(room, action.pid);
      return;
    }
    case 'start': {
      requireHost(room, pid);
      if (room.status !== 'lobby') fail('BAD_PHASE', 'La partie a déjà commencé.');
      startGame(room, ctx);
      return;
    }
    case 'pick': {
      requirePlaying();
      if (r.phase !== 'pick') fail('BAD_PHASE', 'Le choix des cartes est terminé pour cette manche.');
      const hand = r.hands[pid];
      if (!hand) fail('NOT_PLAYING', 'Tu ne joues pas cette manche.');
      if (r.picks[pid]) {
        if (r.picks[pid] === action.cardId) return; // requête répétée : idempotent
        fail('ALREADY_PICKED', 'Ton choix est déjà validé.');
      }
      if (!hand.includes(action.cardId)) fail('CARD_NOT_IN_HAND', 'Cette carte ne fait pas partie de ta main.');
      r.picks[pid] = action.cardId;
      maybeEndPick(room, ctx, false);
      return;
    }
    case 'vote': {
      requirePlaying();
      if (r.phase !== 'vote') fail('BAD_PHASE', 'Le vote n’est pas ouvert.');
      const answer = r.answers.find((a) => a.aid === action.aid);
      if (!answer) fail('BAD_ANSWER', 'Cette réponse n’existe pas dans cette manche.');
      if (!p.inGame) fail('NOT_PLAYING', 'Tu ne joues pas cette partie.');
      if (r.votes[pid]) {
        if (r.votes[pid] === action.aid) return;
        fail('ALREADY_VOTED', 'Tu as déjà voté.');
      }
      if (answer.owner === pid) fail('SELF_VOTE', 'Tu ne peux pas voter pour ta propre carte.');
      r.votes[pid] = action.aid;
      maybeEndVote(room, ctx, false);
      return;
    }
    case 'next': {
      requireHost(room, pid);
      requirePlaying();
      nextRound(room, ctx);
      return;
    }
    case 'skip': {
      // L'hôte débloque une phase si quelqu'un traîne (utile quand le chrono est désactivé).
      requireHost(room, pid);
      requirePlaying();
      if (r.phase === 'pick') maybeEndPick(room, ctx, true);
      else if (r.phase === 'vote') maybeEndVote(room, ctx, true);
      else nextRound(room, ctx);
      return;
    }
    case 'pause': {
      requireHost(room, pid);
      if (!playing) fail('BAD_PHASE', 'Aucune partie en cours.');
      if (g.paused) return;
      pauseGame(room, ctx.now, 'host');
      return;
    }
    case 'resume': {
      requireHost(room, pid);
      if (!playing) fail('BAD_PHASE', 'Aucune partie en cours.');
      if (!g.paused) return;
      if (participants(room).filter((x) => !x.absent).length < LIMITS.minPlayers) fail('CANNOT_RESUME', 'Il faut au moins 2 joueuses connectées pour reprendre.');
      resumeGame(room, ctx.now);
      settle(room, ctx);
      return;
    }
    case 'stop': {
      requireHost(room, pid);
      if (!playing) fail('BAD_PHASE', 'Aucune partie en cours.');
      endGame(room, ctx, 'stopped');
      return;
    }
    case 'replay': {
      requireHost(room, pid);
      if (room.status !== 'finished') fail('BAD_PHASE', 'La partie n’est pas terminée.');
      resetToLobby(room);
      return;
    }
    case 'leave': {
      leave(room, pid, ctx);
      return;
    }
    default:
      fail('BAD_REQUEST', 'Action inconnue.');
  }
}

// ── temps ───────────────────────────────────────────────────

export function tick(room, ctx) {
  const { now } = ctx;
  if (room.status === 'closed') return;
  const idleSince = now - room.lastActivity;
  const anyoneConnected = activePlayers(room).some((p) => p.connected);
  if ((!anyoneConnected && idleSince >= LIMITS.idleExpiryMs) || now - room.createdAt >= LIMITS.maxLifetimeMs) {
    room.status = 'closed';
    return;
  }
  for (const p of activePlayers(room)) {
    if (p.connected || p.disconnectedAt == null) continue;
    if (room.status === 'lobby' && now - p.disconnectedAt >= LIMITS.lobbyGraceMs) removeFromLobby(room, p.id);
    else if (room.status !== 'lobby' && !p.absent && now - p.disconnectedAt >= LIMITS.disconnectGraceMs) {
      p.absent = true;
      transferHostIfNeeded(room);
    }
  }
  if (room.status !== 'playing') return;
  autoPauseIfNeeded(room, now);
  settle(room, ctx);
  const r = room.game.round;
  if (!room.game.paused && r.deadline != null && now >= r.deadline) {
    if (r.phase === 'pick') maybeEndPick(room, ctx, true);
    else if (r.phase === 'vote') maybeEndVote(room, ctx, true);
    else nextRound(room, ctx);
  }
}

export function nextWakeup(room) {
  if (room.status === 'closed') return null;
  const times = [room.createdAt + LIMITS.maxLifetimeMs, room.lastActivity + LIMITS.idleExpiryMs];
  for (const p of activePlayers(room)) {
    if (p.connected || p.disconnectedAt == null) continue;
    if (room.status === 'lobby') times.push(p.disconnectedAt + LIMITS.lobbyGraceMs);
    else if (!p.absent) times.push(p.disconnectedAt + LIMITS.disconnectGraceMs);
  }
  const r = room.game?.round;
  if (room.status === 'playing' && r?.deadline != null && !room.game.paused) times.push(r.deadline);
  return Math.min(...times);
}

// ── vue par joueuse ─────────────────────────────────────────
// Seule fonction qui produit ce qui part vers un navigateur : les mains des autres,
// les propriétaires des réponses et les votes n'y figurent qu'au moment autorisé.

export function viewFor(room, pid, content) {
  const me = room.players[pid];
  const g = room.game;
  const r = g?.round;
  const card = (id) => content.cardById(id);
  const situation = r ? content.situationById(r.situationId) : null;
  const players = activePlayers(room).map((p) => ({
    id: p.id,
    name: p.name,
    host: p.id === room.hostId,
    ready: p.ready,
    connected: p.connected,
    absent: p.absent,
    inGame: p.inGame,
    score: p.score,
    roundsWon: p.roundsWon,
    picked: room.status === 'playing' && r?.phase === 'pick' ? Boolean(r.picks[p.id]) : undefined,
    voted: room.status === 'playing' && r?.phase === 'vote' ? Boolean(r.votes[p.id]) : undefined,
  }));
  const view = {
    code: room.code,
    status: room.status,
    you: pid,
    hostId: room.hostId,
    config: room.config,
    players,
    limits: { min: LIMITS.minPlayers, max: LIMITS.maxPlayers },
    canStart: room.status === 'lobby' ? canStart(room) : undefined,
  };
  if (!g) return view;
  view.game = { id: g.id, paused: g.paused ? { by: g.paused.by } : null, endReason: g.endReason };
  if (r) {
    const round = {
      n: r.n,
      total: room.config.rounds,
      phase: r.phase,
      deadline: r.deadline,
      situation: situation ? { id: situation.id, text: situation.text, category: situation.category } : { id: r.situationId, text: 'Situation indisponible', category: '' },
      notice: r.notice,
    };
    if (r.phase === 'pick') {
      const expected = expectedPickers(room);
      round.progress = { done: expected.filter((p) => r.picks[p.id]).length, total: expected.length };
      round.hand = (r.hands[pid] || []).map(card);
      round.myPick = r.picks[pid] || null;
      round.playing = Boolean(r.hands[pid]);
    } else {
      // Réponses anonymes : jamais de propriétaire avant les résultats.
      round.answers = r.answers.map((a) => ({ aid: a.aid, label: a.label, card: card(a.cardId) }));
      round.myAnswer = r.answers.find((a) => a.owner === pid)?.aid || null;
      if (r.phase === 'vote') {
        const voters = eligibleVoters(room);
        round.progress = { done: voters.filter((p) => r.votes[p.id]).length, total: voters.length };
        round.myVote = r.votes[pid] || null;
        round.canVote = voters.some((p) => p.id === pid);
      } else {
        round.myVote = r.votes[pid] || null;
        round.result = {
          reason: r.result.reason,
          winners: r.result.winners,
          counts: r.result.counts,
          points: r.result.points,
          owners: Object.fromEntries(r.answers.map((a) => [a.aid, a.owner])),
        };
        round.isLast = r.n >= room.config.rounds;
      }
    }
    view.round = round;
  }
  if (room.status === 'finished') {
    view.history = g.history.map((h) => ({
      n: h.n,
      situation: content.situationById(h.situationId)?.text || '',
      winners: h.winners.map((w) => ({ card: card(w.cardId), owner: w.owner, votes: w.votes })),
    }));
  }
  if (me) view.me = { name: me.name, host: room.hostId === pid };
  return view;
}
