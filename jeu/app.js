// Client du jeu MDR. Le navigateur n'est qu'un affichage : chaque action est envoyée au
// serveur, qui la valide et renvoie à chaque joueuse sa propre vue de la partie.

const params = new URLSearchParams(location.search);
const LOCAL = ['localhost', '127.0.0.1', ''].includes(location.hostname);
const SERVER = (params.get('server') || (LOCAL ? 'http://127.0.0.1:8787' : window.MDR_CONFIG?.server || '')).replace(/\/$/, '');
const CODE_RE = /^[A-Z]{3}[0-9]{3}$/;
const AVATAR_COLORS = ['#ffd43b', '#ff86bf', '#4fe0b0', '#9fd0ff', '#cbb8ff', '#ffb68a', '#b8f06a', '#ffe08a', '#8ef0e6', '#ffa3a3'];
const ART_COLORS = ['#fff2c6', '#ffd9ea', '#d6f7ec', '#dcebff', '#e9e1ff', '#ffe3d1'];
const reduceMotion = matchMedia('(prefers-reduced-motion: reduce)');

const app = document.getElementById('app');
const banner = document.getElementById('banner');
const sheet = document.getElementById('sheet');

const ui = {
  view: null,
  session: null, // { code, playerId, token, name }
  ws: null,
  conn: 'idle', // idle | connecting | open | lost
  retry: 0,
  retryTimer: null,
  skew: 0,
  selected: null,
  selectedKey: null,
  busy: false,
  mounted: null,
  parts: {},
  celebrated: null,
  peek: null,
  homeError: '',
  categories: null,
};

// ── utilitaires ───────────────────────────────────────────
const esc = (s) => String(s ?? '').replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[c]);
// Typographie française : espaces insécables avant ? ! : ; » et après «, et dans « 23 h 14 ».
const fr = (s) => esc(s).replace(/ ([?!:;»])/g, '\u00a0$1').replace(/« /g, '«\u00a0').replace(/(\d) (h|%|€|min|s)\b/g, '$1\u00a0$2').replace(/(\d\u00a0h) (\d)/g, '$1\u00a0$2');
const hash = (s) => [...String(s)].reduce((h, c) => (h * 31 + c.charCodeAt(0)) >>> 0, 7);
const plural = (n, one, many) => `${n} ${n > 1 ? many : one}`;
const store = {
  get(key) {
    try {
      return JSON.parse(localStorage.getItem(key));
    } catch {
      return null;
    }
  },
  set(key, value) {
    try {
      if (value == null) localStorage.removeItem(key);
      else localStorage.setItem(key, JSON.stringify(value));
    } catch {
      // stockage indisponible (navigation privée) : la reconnexion après rechargement ne marchera pas, le jeu oui
    }
  },
};
const sessionKey = (code) => `mdr:session:${code}`;

const ICONS = {
  menu: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"><path d="M4 7h16M4 12h16M4 17h16"/></svg>',
  close: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"><path d="M6 6l12 12M18 6L6 18"/></svg>',
  copy: '<svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linejoin="round"><rect x="8" y="8" width="12" height="12" rx="2.5"/><path d="M16 8V5.5A1.5 1.5 0 0 0 14.5 4h-9A1.5 1.5 0 0 0 4 5.5v9A1.5 1.5 0 0 0 5.5 16H8"/></svg>',
  zoom: '<svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"><circle cx="10.5" cy="10.5" r="6.5"/><path d="M15.5 15.5L21 21M10.5 7.5v6M7.5 10.5h6"/></svg>',
  share: '<svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 15V3M7 8l5-5 5 5M5 13v6a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2v-6"/></svg>',
};

function toast(message, kind = '') {
  const el = document.createElement('div');
  el.className = `toast ${kind}`;
  el.textContent = message;
  document.getElementById('toasts').append(el);
  setTimeout(() => el.remove(), 3800);
}

function openSheet(html) {
  sheet.innerHTML = `<div class="sheet-body">${html}</div>`;
  if (!sheet.open) sheet.showModal();
}
const closeSheet = () => sheet.open && sheet.close();
sheet.addEventListener('click', (e) => {
  if (e.target === sheet) closeSheet();
});

// ── API HTTP ──────────────────────────────────────────────
async function api(path, body) {
  if (!SERVER) throw { code: 'NO_SERVER', message: 'Le serveur du jeu n’est pas encore configuré sur ce site.' };
  let res;
  try {
    res = await fetch(SERVER + path, {
      method: body ? 'POST' : 'GET',
      headers: body ? { 'content-type': 'application/json' } : {},
      body: body ? JSON.stringify(body) : undefined,
    });
  } catch {
    throw { code: 'NETWORK', message: 'Impossible de joindre le serveur du jeu. Vérifie ta connexion puis réessaie.' };
  }
  const data = await res.json().catch(() => null);
  if (!res.ok || !data) throw data?.message ? data : { code: 'SERVER_ERROR', message: 'Le serveur a rencontré une erreur. Réessaie dans un instant.' };
  return data;
}

// ── connexion temps réel ──────────────────────────────────
function connect() {
  const s = ui.session;
  if (!s) return;
  clearTimeout(ui.retryTimer);
  if (ui.ws) {
    ui.ws.onclose = null;
    ui.ws.close();
  }
  ui.conn = ui.view ? 'lost' : 'connecting';
  const ws = new WebSocket(`${SERVER.replace(/^http/, 'ws')}/api/rooms/${s.code}/ws`);
  ui.ws = ws;
  let ping;
  ws.onopen = () => {
    ws.send(JSON.stringify({ t: 'hello', token: s.token }));
    ping = setInterval(() => ws.readyState === 1 && ws.send('{"t":"ping"}'), 25_000);
  };
  ws.onmessage = (e) => {
    let msg;
    try {
      msg = JSON.parse(e.data);
    } catch {
      return;
    }
    if (msg.t === 'state') {
      ui.conn = 'open';
      ui.retry = 0;
      if (msg.now) ui.skew = msg.now - Date.now();
      ui.view = msg.s;
      render();
    } else if (msg.t === 'error') {
      ui.busy = false;
      toast(msg.message, 'bad');
      render();
    } else if (msg.t === 'ack') {
      ui.busy = false;
    } else if (msg.t === 'bye') {
      onBye(msg);
    }
  };
  ws.onclose = () => {
    clearInterval(ping);
    if (ui.ws !== ws || ui.conn === 'ended') return;
    ui.conn = 'lost';
    const delay = Math.min(10_000, 800 * 2 ** ui.retry++);
    ui.retryTimer = setTimeout(connect, delay);
    render();
  };
}

function send(action) {
  if (ui.ws?.readyState !== 1) {
    toast('Connexion perdue : ton action n’a pas été envoyée. Réessaie dans un instant.', 'bad');
    return false;
  }
  ui.ws.send(JSON.stringify({ ...action, ref: Math.random().toString(36).slice(2) }));
  return true;
}

function endSession() {
  if (ui.session) store.set(sessionKey(ui.session.code), null);
  ui.conn = 'ended';
  ui.ws?.close();
  ui.ws = null;
  ui.session = null;
  ui.view = null;
}

const BYE_TITLES = {
  BAD_TOKEN: 'Session introuvable',
  KICKED: 'Tu as été retirée du salon',
  ROOM_EXPIRED: 'Salle fermée',
  REPLACED: 'Partie ouverte ailleurs',
};

function onBye(msg) {
  const code = ui.session?.code;
  if (msg.code === 'LEFT') {
    endSession();
    goHome();
    toast('Tu as quitté la partie.');
    return;
  }
  if (msg.code === 'REPLACED') {
    ui.conn = 'ended';
    ui.ws = null;
    showFatal(BYE_TITLES.REPLACED, msg.message, '<button class="btn" data-act="reclaim">Jouer dans cet onglet</button>');
    return;
  }
  endSession();
  const rejoin = msg.code === 'BAD_TOKEN' && code ? `<a class="btn" href="?code=${code}">Rejoindre à nouveau</a>` : '';
  showFatal(BYE_TITLES[msg.code] || 'Partie terminée', msg.message, `${rejoin}<button class="btn btn-ghost" data-act="home">Retour à l’accueil</button>`);
}

function showFatal(title, message, actions) {
  ui.mounted = 'fatal';
  banner.hidden = true;
  app.innerHTML = `<main class="wrap"><div class="fatal">
    <h1>${esc(title)}</h1><p>${esc(message)}</p><div class="final-actions">${actions}</div></div></main>`;
}

function goHome(code = '') {
  history.replaceState(null, '', code ? `?code=${code}` : location.pathname);
  ui.mounted = null;
  ui.peek = null;
  renderHome(code);
}

// ── rendu par morceaux ────────────────────────────────────
// Chaque écran a un squelette ; ses morceaux ([data-part]) ne sont réécrits que si leur HTML change,
// pour ne pas relancer les animations ni recharger les images à chaque mise à jour.
function mount(key, html) {
  if (ui.mounted === key) return false;
  ui.mounted = key;
  ui.parts = {};
  app.innerHTML = html;
  window.scrollTo({ top: 0, behavior: 'instant' });
  return true;
}
function part(name, html) {
  const el = app.querySelector(`[data-part="${name}"]`);
  if (!el || ui.parts[name] === html) return false;
  el.innerHTML = html;
  ui.parts[name] = html;
  return true;
}
function animateOnce(selector, cls) {
  const el = app.querySelector(selector);
  if (!el || reduceMotion.matches) return;
  el.classList.add(cls);
  setTimeout(() => el.classList.remove(cls), 1600);
}

const playerColor = (view, id) => AVATAR_COLORS[Math.max(0, view.players.findIndex((p) => p.id === id)) % AVATAR_COLORS.length];
const avatar = (view, p) => `<span class="avatar" style="--c:${playerColor(view, p.id)}" aria-hidden="true">${esc([...p.name][0]?.toUpperCase() || '?')}</span>`;
const nameOf = (view, id) => view.players.find((p) => p.id === id)?.name || 'Une joueuse partie';

function cardHtml(card, { tag = 'div', attrs = '', extra = '', cls = '', i = 0, zoom = false } = {}) {
  const tilt = ((hash(card.id) % 5) - 2) * 0.6;
  const style = `--tilt:${tilt}deg;--i:${i}`;
  const body = card.image
    ? `<div class="card-art"><img class="card-img" src="${esc(card.image)}" alt="${esc(card.name || 'Meme')}" loading="lazy" decoding="async" referrerpolicy="no-referrer"></div>`
    : `<div class="card-fallback">Meme indisponible</div>`;
  const label = card.name || 'Meme';
  const el = `<${tag} class="card type-meme${card.missing ? ' missing' : ''} ${cls}" style="${style}" ${attrs} ${tag === 'button' ? `type="button" aria-label="${esc(label)}"` : ''}>${extra}${body}</${tag}>`;
  if (!zoom || !card.image) return el;
  return `<div class="card-slot">${el}<button class="zoom" type="button" data-act="zoom" data-src="${esc(card.image)}" data-name="${esc(label)}" aria-label="Agrandir ${esc(label)}">${ICONS.zoom}</button></div>`;
}

// Image cassée : on affiche sa description au lieu d'un trou.
document.addEventListener(
  'error',
  (e) => {
    const img = e.target;
    if (!(img instanceof HTMLImageElement) || !img.classList.contains('card-img')) return;
    const art = img.closest('.card-art');
    if (art) art.innerHTML = `<div class="card-fallback">${esc(img.alt || 'Meme')}<br><small>Image momentanément indisponible</small></div>`;
  },
  true,
);

function render() {
  const v = ui.view;
  updateBanner();
  if (!v) return;
  if (v.status === 'lobby') renderLobby(v);
  else if (v.status === 'playing') renderRound(v);
  else if (v.status === 'finished') renderFinal(v);
  else showFatal('Salle fermée', 'Cette partie est terminée ou a expiré.', '<button class="btn" data-act="home">Retour à l’accueil</button>');
}

function updateBanner() {
  const v = ui.view;
  let html = '';
  let cls = 'banner';
  if (ui.session && ui.conn === 'lost') {
    html = `<span>Connexion perdue. Reconnexion…</span><button class="btn btn-small" data-act="retry">Réessayer</button>`;
  } else if (v?.status === 'playing' && v.game?.paused) {
    cls += ' pause';
    const host = v.hostId === v.you;
    html = v.game.paused.by === 'auto'
      ? `<span>Pause : il faut au moins 2 joueuses connectées.</span>`
      : `<span>Partie en pause</span>${host ? '<button class="btn btn-small btn-paper" data-act="resume">Reprendre</button>' : ''}`;
  }
  banner.className = cls;
  banner.hidden = !html;
  if (banner.innerHTML !== html) banner.innerHTML = html;
}

// ── accueil ───────────────────────────────────────────────
// L'éventail de l'accueil montre trois vrais memes de la bibliothèque.
const FAN = ['Drake Hotline Bling', 'Distracted Boyfriend', 'Woman Yelling At Cat'];
async function fillFan() {
  try {
    const { memes } = await (await fetch('data/memes.json')).json();
    const on = memes.filter((m) => m.active);
    const pickName = (n) => on.find((m) => m.name.toLowerCase() === n.toLowerCase()) || on[Math.floor(Math.random() * on.length)];
    const cards = FAN.map(pickName).map((m) => ({ id: m.id, type: 'meme', image: m.image, name: m.name }));
    const fan = app.querySelector('.fan');
    if (fan) fan.innerHTML = cards.map((c) => cardHtml(c)).join('');
  } catch {
    // l'accueil reste utilisable sans l'éventail
  }
}

function renderHome(prefill = '') {
  const code = (prefill || '').toUpperCase();
  const name = store.get('mdr:name') || '';
  const joinMode = CODE_RE.test(code);
  ui.mounted = 'home';
  banner.hidden = true;
  app.innerHTML = `<main class="wrap"><div class="home">
    <header class="hero">
      <div class="fan" aria-hidden="true"></div>
      <h1 class="wordmark">MDR!</h1>
      <p class="tagline">Une situation, dix cartes, une seule qui fera rire tout le groupe.</p>
    </header>
    <div class="home-grid">
      <form class="panel" id="homeForm" novalidate>
        ${!SERVER ? '<p class="error-text">Le serveur du jeu n’est pas encore configuré sur ce site : les parties ne peuvent pas démarrer.</p>' : ''}
        <label class="field"><span>Ton pseudo</span>
          <input class="input" id="name" name="name" maxlength="20" autocomplete="nickname" placeholder="Ex. : Léa" value="${esc(name)}" required></label>
        ${joinMode ? `
          <div class="room-peek" data-part="peek">Salle <b>${esc(code)}</b></div>
          <input type="hidden" id="code" value="${esc(code)}">
          <button class="btn btn-wide" type="submit" data-act="join">Rejoindre la salle</button>
          <div class="split">ou</div>
          <button class="btn btn-ghost btn-wide" type="button" data-act="create">Créer ma propre partie</button>
        ` : `
          <button class="btn btn-wide" type="submit" data-act="create">Créer une partie</button>
          <div class="split">ou rejoindre des copines</div>
          <label class="field"><span>Code de la salle</span>
            <div class="join-row"><input class="input input-code" id="code" maxlength="6" placeholder="MDR482" autocomplete="off" autocapitalize="characters" spellcheck="false" value="${esc(code)}">
            <button class="btn btn-ghost" type="button" data-act="join">Rejoindre</button></div></label>
        `}
        <p class="error-text" id="homeError" ${ui.homeError ? '' : 'hidden'}>${esc(ui.homeError)}</p>
        <p class="hint">Pas de compte à créer. De 2 à 10 joueuses par salle.</p>
      </form>
      <section class="rules" aria-labelledby="rulesTitle">
        <h2 id="rulesTitle">Comment on joue</h2>
        <ol class="steps">
          <li><div><b>Une situation pour tout le monde</b><span>« Quand ton crush te répond après 8 heures. »</span></div></li>
          <li><div><b>Tu joues ton meme en secret</b><span>Tu as 10 memes en main, nouveaux à chaque manche : choisis celui qui colle le mieux.</span></div></li>
          <li><div><b>Vote à l’aveugle</b><span>Les memes joués sont mélangés et anonymes. Impossible de voter pour le tien.</span></div></li>
          <li><div><b>1 point pour le plus voté</b><span>10 manches, puis le classement final désigne la reine du MDR.</span></div></li>
        </ol>
      </section>
    </div>
    <footer class="footer"><button class="link" data-act="credits">Crédits et licences</button><a href="../">Retour au site</a></footer>
  </div></main>`;
  ui.homeError = '';
  const codeInput = document.getElementById('code');
  if (codeInput && !joinMode) codeInput.addEventListener('input', () => (codeInput.value = codeInput.value.toUpperCase().replace(/[^A-Z0-9]/g, '')));
  document.getElementById('homeForm').addEventListener('submit', (e) => {
    e.preventDefault();
    homeAction(joinMode ? 'join' : 'create');
  });
  if (joinMode) peekRoom(code);
  fillFan();
}

async function peekRoom(code) {
  try {
    const p = await api(`/api/rooms/${code}/peek`);
    const status = p.status === 'lobby' ? `${plural(p.players, 'joueuse', 'joueuses')} dans le salon` : p.status === 'playing' ? 'partie en cours' : 'partie terminée';
    part('peek', `Salle <b>${esc(code)}</b> · ${esc(status)}`);
  } catch (err) {
    part('peek', `<span>${esc(err.message)}</span>`);
  }
}

function homeError(message) {
  const el = document.getElementById('homeError');
  if (!el) return toast(message, 'bad');
  el.textContent = message;
  el.hidden = false;
}

async function homeAction(kind) {
  if (ui.busy) return;
  const name = document.getElementById('name').value.trim();
  const code = (document.getElementById('code')?.value || '').trim().toUpperCase();
  if (!name) return homeError('Choisis un pseudo pour jouer.');
  if (kind === 'join' && !CODE_RE.test(code)) return homeError('Le code de salle fait 6 caractères : 3 lettres puis 3 chiffres (ex. MDR482).');
  store.set('mdr:name', name);
  ui.busy = true;
  app.querySelectorAll('#homeForm .btn').forEach((b) => (b.disabled = true));
  try {
    const res = kind === 'create' ? await api('/api/rooms', { name }) : await api(`/api/rooms/${code}/join`, { name });
    startSession({ code: res.code, playerId: res.playerId, token: res.token, name });
  } catch (err) {
    homeError(err.message || 'Une erreur est survenue.');
    app.querySelectorAll('#homeForm .btn').forEach((b) => (b.disabled = false));
  } finally {
    ui.busy = false;
  }
}

function startSession(session) {
  ui.session = session;
  store.set(sessionKey(session.code), session);
  history.replaceState(null, '', `?code=${session.code}`);
  ui.mounted = null;
  app.innerHTML = '<p class="boot">Connexion à la salle…</p>';
  ui.conn = 'connecting';
  connect();
}

// ── salon ─────────────────────────────────────────────────
const inviteLink = (code) => `${location.origin}${location.pathname}?code=${code}`;
const SETTINGS = [
  ['rounds', 'Nombre de manches', '', [5, 10, 15], (n) => `${n} manches`],
  ['pickSeconds', 'Temps pour choisir', '', [0, 30, 45, 60, 90, 120], (n) => (n ? `${n} s` : 'Sans chrono')],
  ['voteSeconds', 'Temps pour voter', '', [0, 20, 30, 45, 60], (n) => (n ? `${n} s` : 'Sans chrono')],
  ['resultsSeconds', 'Après les résultats', '', [0, 8, 12, 20], (n) => (n ? `Suite auto. après ${n} s` : 'L’hôte lance la suite')],
];

function renderLobby(v) {
  const host = v.hostId === v.you;
  mount(
    `lobby:${v.code}`,
    `<main class="wrap"><div class="lobby">
      <div class="topbar"><span class="title">Salon</span><button class="btn btn-ghost btn-small" data-act="leave">Quitter</button></div>
      <section class="code-card">
        <p>Donne ce code à tes copines</p>
        <div class="code" aria-label="Code de la salle">${esc(v.code)}</div>
        <div class="code-actions">
          <button class="btn btn-paper btn-small" data-act="copy-code">${ICONS.copy} Copier le code</button>
          <button class="btn btn-paper btn-small" data-act="share">${ICONS.share} Partager le lien</button>
        </div>
      </section>
      <section aria-labelledby="playersTitle"><div class="section-title"><h2 id="playersTitle">Joueuses</h2><span data-part="count"></span></div>
        <ul class="players" data-part="players"></ul></section>
      <section aria-labelledby="settingsTitle"><div class="section-title"><h2 id="settingsTitle">Réglages</h2></div>
        <div class="settings" data-part="settings"></div></section>
      <p class="rules-note">Chrono écoulé : les joueuses qui n’ont pas validé passent leur tour pour la manche. Une joueuse déconnectée plus de 45 secondes n’est plus attendue, et retrouve sa place et ses points en revenant.</p>
    </div></main>
    <div class="dock"><div class="dock-inner" data-part="dock"></div></div>`,
  );
  part('count', `${v.players.length}/${v.limits.max}`);
  part(
    'players',
    v.players
      .map((p) => {
        const status = p.id === v.hostId ? '<span class="badge host">Hôte</span>' : p.ready ? '<span class="badge ready">Prête</span>' : '<span class="badge">En attente</span>';
        const kick = host && p.id !== v.you ? `<button class="icon-btn kick" data-act="kick" data-id="${esc(p.id)}" aria-label="Retirer ${esc(p.name)} du salon">${ICONS.close}</button>` : '';
        return `<li class="player${p.connected ? '' : ' away'}">${avatar(v, p)}
          <div><div class="name">${esc(p.name)}${p.id === v.you ? ' (toi)' : ''}</div><div class="meta">${p.connected ? 'Connectée' : 'Déconnectée'}</div></div>
          <div class="player-end">${status}${kick}</div></li>`;
      })
      .join(''),
  );
  const c = v.config;
  const settings = SETTINGS.map(([key, label, , options, fmt]) =>
    host
      ? `<div class="setting"><label for="cfg-${key}">${label}</label><select class="select" id="cfg-${key}" data-config="${key}">${options.map((o) => `<option value="${o}"${o === c[key] ? ' selected' : ''}>${fmt(o)}</option>`).join('')}</select></div>`
      : `<div class="setting"><span>${label}</span><b>${fmt(c[key])}</b></div>`,
  ).join('');
  part('settings', settings);
  const me = v.players.find((p) => p.id === v.you);
  let dock;
  if (host) {
    dock = `<button class="btn btn-wide" data-act="start" ${v.canStart.ok ? '' : 'disabled'}>Lancer la partie</button>
      <p class="hint">${v.canStart.ok ? 'Tout le monde est prête !' : esc(v.canStart.reason)}</p>`;
  } else {
    dock = me?.ready
      ? `<button class="btn btn-ghost btn-wide" data-act="unready">Je ne suis plus prête</button><p class="hint">L’hôte lance la partie quand tout le monde est prête.</p>`
      : `<button class="btn btn-mint btn-wide" data-act="ready">Je suis prête</button><p class="hint">Signale que tu es prête à jouer.</p>`;
  }
  part('dock', dock);
}

// ── manche ────────────────────────────────────────────────
const CATEGORY_LABELS = {
  crush: 'Crushs & flirts', ex: 'Ex & ruptures', amies: 'Meilleures amies', dramas: 'Dramas & secrets', beaute: 'Beauté & tenues',
  dates: 'Dates & couples', reseaux: 'Réseaux & messages', soirees: 'Soirées', quotidien: 'Famille & quotidien', absurde: 'Absurde & gênant',
};

function renderRound(v) {
  const r = v.round;
  const fresh = mount(
    `round:${v.game.id}:${r.n}:${r.phase}`,
    `<main class="wrap">
      <div class="topbar">
        <span class="round-pill">Manche ${r.n}<small>/${r.total}</small></span>
        <span class="timer" data-timer></span>
        <button class="icon-btn" data-act="menu" aria-label="Menu de la partie">${ICONS.menu}</button>
      </div>
      <section class="prompt"><span class="cat">${esc(CATEGORY_LABELS[r.situation.category] || 'Situation')}</span><h1>${fr(r.situation.text)}</h1></section>
      <div class="status" data-part="status"></div>
      <div data-part="board"></div>
      <div data-part="standings"></div>
    </main>
    <div class="dock"><div class="dock-inner" data-part="dock"></div></div>`,
  );
  if (fresh) {
    ui.selected = null;
    ui.busy = false;
  }
  if (r.phase === 'pick') renderPick(v, r, fresh);
  else if (r.phase === 'vote') renderVote(v, r, fresh);
  else renderResults(v, r, fresh);
  tickTimer();
}

function progressHtml(r, verb) {
  const { done, total } = r.progress;
  const pct = total ? Math.round((done / total) * 100) : 0;
  return `<div class="status-line"><span>${done}/${total} joueuses ${verb}</span></div>
    <div class="bar" role="progressbar" aria-valuemin="0" aria-valuemax="${total}" aria-valuenow="${done}"><i style="--p:${pct}%"></i></div>`;
}

function chipsHtml(v, flag) {
  return `<div class="chips">${v.players
    .filter((p) => p.inGame)
    .map((p) => `<span class="chip${p[flag] ? ' done' : ''}${p.connected ? '' : ' away'}">${avatar(v, p)}${esc(p.name)}</span>`)
    .join('')}</div>`;
}

function renderPick(v, r, fresh) {
  const picked = r.myPick;
  part(
    'status',
    `<div class="status-line"><strong>${!r.playing ? 'Tu regardes cette manche' : picked ? 'Meme validé !' : 'Choisis ton meme'}</strong></div>
     ${progressHtml(r, 'ont choisi leur meme')}${chipsHtml(v, 'picked')}`,
  );
  if (!r.playing) {
    part('board', `<div class="waiting"><p>Tu n’as pas de memes pour cette manche. Tu joueras la suivante.</p></div>`);
    part('dock', '');
    return;
  }
  if (picked) {
    const card = r.hand.find((c) => c.id === picked);
    part('board', `<div class="waiting">${cardHtml(card, { extra: '<span class="sticker mint">Mon meme</span>' })}<p>Les autres choisissent encore. Personne ne voit ton meme avant la révélation.</p></div>`);
    part('dock', '');
    return;
  }
  if (ui.selected && !r.hand.some((c) => c.id === ui.selected)) ui.selected = null;
  const drew = part(
    'board',
    `<div class="grid hand" data-grid>${r.hand
      .map((c, i) => cardHtml(c, { tag: 'button', i, zoom: true, attrs: `data-act="select" data-id="${esc(c.id)}" aria-pressed="${ui.selected === c.id}"`, cls: ui.selected === c.id ? 'is-selected' : '' }))
      .join('')}</div>`,
  );
  if (drew && fresh) animateOnce('[data-grid]', 'deal');
  updatePickDock(r);
}

function updatePickDock(r) {
  part(
    'dock',
    `<button class="btn btn-wide" data-act="confirm-pick" ${ui.selected && !ui.busy ? '' : 'disabled'}>${ui.selected ? 'Valider ce meme' : 'Touche un meme'}</button>
     <p class="hint">Tu peux changer d’avis tant que tu n’as pas validé.</p>`,
  );
}

const NOTICES = {
  pick_missed: (n) => `Temps écoulé : ${n.names.join(', ')} ${n.names.length > 1 ? 'n’ont' : 'n’a'} pas validé de meme et passe${n.names.length > 1 ? 'nt' : ''} son tour. Tout le monde peut voter.`,
};

function renderVote(v, r, fresh) {
  const voted = r.myVote;
  part(
    'status',
    `<div class="status-line"><strong>${voted ? 'Vote enregistré !' : r.canVote ? 'Vote pour le meme le plus drôle' : 'Les autres votent'}</strong></div>
     ${r.notice ? `<p class="notice">${esc(NOTICES[r.notice.kind]?.(r.notice) || '')}</p>` : ''}
     ${progressHtml(r, 'ont voté')}${chipsHtml(v, 'voted')}`,
  );
  if (ui.selected && (ui.selected === r.myAnswer || !r.answers.some((a) => a.aid === ui.selected))) ui.selected = null;
  const drew = part(
    'board',
    `<div class="grid" data-grid>${r.answers
      .map((a, i) => {
        const mine = a.aid === r.myAnswer;
        const chosen = voted === a.aid;
        const extra = `<span class="letter">${a.label}</span>${mine ? '<span class="sticker gum">Ton meme</span>' : ''}${chosen ? '<span class="sticker">Ton vote</span>' : ''}`;
        const disabled = mine || voted || !r.canVote;
        const cls = [ui.selected === a.aid && !voted ? 'is-selected' : '', mine ? 'is-mine' : '', voted && !chosen && !mine ? 'is-dim' : ''].join(' ');
        return cardHtml(a.card, { tag: 'button', i, extra, cls, zoom: true, attrs: `data-act="select" data-id="${esc(a.aid)}" ${disabled ? 'disabled' : ''} aria-pressed="${ui.selected === a.aid}" aria-describedby="lbl-${a.aid}"` }) + `<span class="sr" id="lbl-${a.aid}">Meme ${a.label}${mine ? ', ton meme' : ''}</span>`;
      })
      .join('')}</div>`,
  );
  if (drew && fresh) animateOnce('[data-grid]', 'flip');
  updateVoteDock(r);
}

function updateVoteDock(r) {
  if (r.myVote || !r.canVote) {
    part('dock', r.canVote ? '' : '<p class="hint">Tu ne peux pas voter cette manche : il n’y a pas d’autre meme que le tien.</p>');
    return;
  }
  const label = r.answers.find((a) => a.aid === ui.selected)?.label;
  part(
    'dock',
    `<button class="btn btn-gum btn-wide" data-act="confirm-vote" ${label && !ui.busy ? '' : 'disabled'}>${label ? `Voter pour le meme ${label}` : 'Touche ton meme préféré'}</button>
     <p class="hint">Un seul vote, et pas pour ton propre meme.</p>`,
  );
}

const RESULT_REASONS = {
  not_enough_answers: 'Pas assez de memes joués : pas de vote cette manche.',
  no_voters: 'Personne ne pouvait voter : aucun point cette manche.',
};

function standingsHtml(v, points = {}) {
  const ranked = [...v.players].sort((a, b) => b.score - a.score || b.roundsWon - a.roundsWon || a.name.localeCompare(b.name));
  let rank = 0;
  let prev = null;
  return `<ol class="standings">${ranked
    .map((p, i) => {
      if (p.score !== prev) rank = i + 1;
      prev = p.score;
      return `<li class="${rank === 1 && p.score > 0 && v.status === 'finished' ? 'first' : ''}"><span class="rank">${rank}</span>${avatar(v, p)}
        <span class="who"><b>${esc(p.name)}${p.id === v.you ? ' (toi)' : ''}</b><small>${plural(p.roundsWon, 'manche gagnée', 'manches gagnées')}${p.inGame ? '' : ' · spectatrice'}</small></span>
        <span class="pts">${p.score}${points[p.id] ? '<span class="plus">+1</span>' : ''}</span></li>`;
    })
    .join('')}</ol>`;
}

function renderResults(v, r, fresh) {
  const res = r.result;
  const winners = res.winners.map((aid) => nameOf(v, res.owners[aid]));
  let headline;
  if (res.winners.length === 1) headline = `${winners[0]} remporte la manche !`;
  else if (res.winners.length > 1) headline = `Égalité ! ${winners.join(' et ')} marquent 1 point.`;
  else headline = RESULT_REASONS[res.reason] || 'Aucun vote : personne ne marque.';
  part('status', `<div class="status-line"><strong>${esc(headline)}</strong></div>${r.notice && res.reason !== 'not_enough_answers' ? `<p class="notice">${esc(NOTICES[r.notice.kind]?.(r.notice) || '')}</p>` : ''}`);
  const sorted = [...r.answers].sort((a, b) => (res.counts[b.aid] || 0) - (res.counts[a.aid] || 0));
  const drew = part(
    'board',
    `<div class="grid" data-grid>${sorted
      .map((a, i) => {
        const win = res.winners.includes(a.aid);
        const n = res.counts[a.aid] || 0;
        const owner = res.owners[a.aid];
        return `<div class="result-card">${cardHtml(a.card, { i, cls: win ? 'is-winner' : '', extra: `<span class="letter">${a.label}</span>${win ? '<span class="sticker">+1 point</span>' : ''}` })}
          <div class="result-meta"><span class="owner">${esc(nameOf(v, owner))}${owner === v.you ? ' (toi)' : ''}</span><span class="votes${win ? ' win' : ''}">${plural(n, 'vote', 'votes')}</span></div></div>`;
      })
      .join('')}</div>`,
  );
  if (drew && fresh) animateOnce('[data-grid]', 'flip');
  part('standings', `<h2 class="block-title">Classement provisoire</h2>${standingsHtml(v, res.points)}`);
  const host = v.hostId === v.you;
  const label = r.isLast ? 'Voir le classement final' : 'Manche suivante';
  part(
    'dock',
    host
      ? `<button class="btn btn-wide" data-act="next">${label}</button><p class="hint" data-auto></p>`
      : `<p class="hint" data-auto>${r.deadline ? '' : 'L’hôte lance la suite.'}</p>`,
  );
}

function tickTimer() {
  const v = ui.view;
  const r = v?.round;
  const el = app.querySelector('[data-timer]');
  const auto = app.querySelector('[data-auto]');
  if (!r || v.status !== 'playing') return;
  const left = r.deadline ? Math.max(0, Math.ceil((r.deadline - (Date.now() + ui.skew)) / 1000)) : null;
  if (el) {
    let text;
    if (v.game.paused) text = 'En pause';
    else if (left == null) text = r.phase === 'results' ? 'Résultats' : 'Sans chrono';
    else text = `${Math.floor(left / 60)}:${String(left % 60).padStart(2, '0')}`;
    if (el.textContent !== text) el.textContent = text;
    el.className = `timer${left == null || v.game.paused ? ' off' : left <= 10 && r.phase !== 'results' ? ' low' : ''}`;
    el.setAttribute('aria-label', left == null ? text : `${left} secondes restantes`);
  }
  if (auto && r.phase === 'results' && r.deadline && !v.game.paused) {
    const text = `${r.isLast ? 'Classement final' : 'Manche suivante'} dans ${left} s`;
    if (auto.textContent !== text) auto.textContent = text;
  }
}
setInterval(tickTimer, 250);

// ── fin de partie ─────────────────────────────────────────
function renderFinal(v) {
  const top = Math.max(...v.players.map((p) => p.score));
  const leaders = v.players.filter((p) => p.score === top);
  let title;
  let sub;
  if (top === 0) {
    title = 'Personne n’a marqué';
    sub = 'Aucun meme n’a reçu de vote. Revanche ?';
  } else if (leaders.length > 1) {
    title = 'Égalité !';
    sub = `${leaders.map((p) => p.name).join(' et ')} terminent ex æquo avec ${plural(top, 'point', 'points')}.`;
  } else {
    title = `${leaders[0].name} gagne !`;
    sub = `Reine du MDR avec ${plural(top, 'point', 'points')}.`;
  }
  const reason = v.game.endReason === 'stopped' ? 'Partie arrêtée par l’hôte.' : v.game.endReason === 'not_enough_players' ? 'Partie terminée : il ne restait pas assez de joueuses.' : '';
  const host = v.hostId === v.you;
  const fresh = mount(
    `final:${v.game.id}`,
    `<main class="wrap"><div class="final">
      <section class="podium">
        <h1>${esc(title)}</h1><p>${esc(sub)}</p>${reason ? `<p>${esc(reason)}</p>` : ''}</section>
      <section><h2 class="block-title">Classement</h2><div data-part="standings"></div></section>
      <section><h2 class="block-title">Les memes gagnants</h2><div class="history">${
        v.history.length
          ? v.history
              .map(
                (h) => `<div class="history-item"><div class="history-cards">${h.winners.length ? h.winners.map((w) => cardHtml(w.card)).join('') : '<p class="hint">Pas de gagnante</p>'}</div>
            <div><span class="n">Manche ${h.n}</span><p>${fr(h.situation)}</p><small>${h.winners.length ? h.winners.map((w) => `${esc(nameOf(v, w.owner))} (${plural(w.votes, 'vote', 'votes')})`).join(', ') : 'Aucun point'}</small></div></div>`,
              )
              .join('')
          : '<p class="hint">Aucune manche terminée.</p>'
      }</div></section>
      <div class="final-actions" data-part="actions"></div>
    </div></main>`,
  );
  part('standings', standingsHtml(v));
  part(
    'actions',
    host
      ? `<button class="btn btn-wide" data-act="replay">Rejouer avec le même groupe</button><button class="btn btn-ghost btn-wide" data-act="leave">Quitter la partie</button>`
      : `<p class="hint">L’hôte peut relancer une partie avec le même groupe : tu resteras dans le salon.</p><button class="btn btn-ghost btn-wide" data-act="leave">Quitter la partie</button>`,
  );
  if (fresh && top > 0 && ui.celebrated !== v.game.id) {
    ui.celebrated = v.game.id;
    confetti();
  }
}

function confetti() {
  if (reduceMotion.matches) return;
  const box = document.createElement('div');
  box.className = 'confetti';
  const colors = ['#ffd43b', '#ff86bf', '#4fe0b0', '#9fd0ff', '#fffdf7'];
  for (let i = 0; i < 70; i++) {
    const c = document.createElement('i');
    c.style.left = `${Math.random() * 100}%`;
    c.style.background = colors[i % colors.length];
    c.style.animationDuration = `${1.8 + Math.random() * 1.8}s`;
    c.style.animationDelay = `${Math.random() * 0.6}s`;
    box.append(c);
  }
  document.body.append(box);
  setTimeout(() => box.remove(), 4500);
}

// ── menus ─────────────────────────────────────────────────
function openMenu() {
  const v = ui.view;
  const host = v?.hostId === v?.you;
  const paused = v?.game?.paused;
  const phase = v?.round?.phase;
  openSheet(`<h2>Partie ${esc(v.code)}</h2>
    ${host ? `<p>Tu es l’hôte : tu contrôles le rythme de la partie.</p>
      ${paused ? '<button class="btn btn-wide" data-act="resume">Reprendre la partie</button>' : '<button class="btn btn-wide" data-act="pause">Mettre en pause</button>'}
      ${phase !== 'results' && !paused ? `<button class="btn btn-paper btn-wide" data-act="skip">${phase === 'pick' ? 'Passer au vote sans attendre' : 'Clore le vote maintenant'}</button>` : ''}
      <button class="btn btn-gum btn-wide" data-act="stop">Arrêter la partie</button>` : '<p>Seule l’hôte peut mettre en pause ou arrêter la partie.</p>'}
    <button class="btn btn-ghost btn-wide" data-act="leave">Quitter la partie</button>
    <button class="btn btn-ghost btn-wide" data-act="close-sheet">Fermer</button>`);
}

function openCredits() {
  openSheet(`<h2>Crédits et droits</h2>
    <p>Situations : textes écrits pour MDR.</p>
    <p>Memes : images célèbres d’Internet, dont les droits appartiennent à leurs auteurs. MDR ne les copie pas : elles s’affichent directement depuis les serveurs d’<a href="https://imgflip.com/memetemplates" target="_blank" rel="noopener">Imgflip</a>, de <a href="https://memegen.link" target="_blank" rel="noopener">memegen.link</a> et de <a href="https://memebo.at" target="_blank" rel="noopener">Memeboat</a>, via leurs API publiques.</p>
    <p>Aucune donnée n’est conservée après la partie : seulement ton pseudo, le temps de la salle.</p>
    <button class="btn btn-wide" data-act="close-sheet">Fermer</button>`);
}

// ── actions ───────────────────────────────────────────────
async function copy(text, done) {
  try {
    await navigator.clipboard.writeText(text);
    toast(done, 'good');
  } catch {
    openSheet(`<h2>Copie le lien</h2><input class="input" readonly value="${esc(text)}" onfocus="this.select()"><button class="btn btn-wide" data-act="close-sheet">Fermer</button>`);
  }
}

document.addEventListener('change', (e) => {
  const key = e.target.dataset?.config;
  if (!key) return;
  const value = e.target.type === 'checkbox' ? e.target.checked : Number(e.target.value);
  send({ t: 'config', config: { [key]: value } });
});

document.addEventListener('click', (e) => {
  const el = e.target.closest('[data-act]');
  if (!el || el.disabled) return;
  const act = el.dataset.act;
  const v = ui.view;
  switch (act) {
    case 'create':
    case 'join':
      e.preventDefault();
      homeAction(act);
      break;
    case 'select': {
      const r = v.round;
      ui.selected = ui.selected === el.dataset.id ? null : el.dataset.id;
      app.querySelectorAll('[data-act="select"]').forEach((b) => {
        const on = b.dataset.id === ui.selected;
        b.classList.toggle('is-selected', on);
        b.setAttribute('aria-pressed', String(on));
      });
      if (on(el) && !reduceMotion.matches) el.animate([{ transform: 'rotate(0) translateY(-8px) scale(1.06)' }, { transform: 'rotate(0) translateY(-8px) scale(1.02)' }], { duration: 220, easing: 'ease-out' });
      if (r.phase === 'pick') updatePickDock(r);
      else updateVoteDock(r);
      break;
    }
    case 'confirm-pick':
      if (ui.selected && send({ t: 'pick', cardId: ui.selected })) {
        ui.busy = true;
        updatePickDock(v.round);
      }
      break;
    case 'confirm-vote':
      if (ui.selected && send({ t: 'vote', aid: ui.selected })) {
        ui.busy = true;
        updateVoteDock(v.round);
      }
      break;
    case 'ready':
      send({ t: 'ready', value: true });
      break;
    case 'unready':
      send({ t: 'ready', value: false });
      break;
    case 'start':
    case 'next':
    case 'replay':
      send({ t: act });
      break;
    case 'pause':
    case 'resume':
    case 'skip':
      send({ t: act });
      closeSheet();
      break;
    case 'stop':
      openSheet(`<h2>Arrêter la partie ?</h2><p>Le classement actuel deviendra le classement final.</p>
        <button class="btn btn-gum btn-wide" data-act="stop-confirm">Arrêter la partie</button><button class="btn btn-ghost btn-wide" data-act="close-sheet">Continuer à jouer</button>`);
      break;
    case 'stop-confirm':
      send({ t: 'stop' });
      closeSheet();
      break;
    case 'leave':
      openSheet(`<h2>Quitter la partie ?</h2><p>${v?.status === 'playing' ? 'Tes points restent au classement, mais tu ne pourras plus revenir dans cette partie.' : 'Tu pourras rejoindre à nouveau avec le code.'}</p>
        <button class="btn btn-gum btn-wide" data-act="leave-confirm">Quitter</button><button class="btn btn-ghost btn-wide" data-act="close-sheet">Rester</button>`);
      break;
    case 'leave-confirm':
      closeSheet();
      if (!send({ t: 'leave' })) {
        endSession();
        goHome();
      }
      break;
    case 'kick':
      send({ t: 'kick', pid: el.dataset.id });
      break;
    case 'menu':
      openMenu();
      break;
    case 'zoom':
      openSheet(`<img class="zoom-img" src="${esc(el.dataset.src)}" alt="${esc(el.dataset.name)}" referrerpolicy="no-referrer"><button class="btn btn-wide" data-act="close-sheet">Fermer</button>`);
      break;
    case 'credits':
      openCredits();
      break;
    case 'close-sheet':
      closeSheet();
      break;
    case 'copy-code':
      copy(v.code, 'Code copié !');
      break;
    case 'share': {
      const url = inviteLink(v.code);
      if (navigator.share) navigator.share({ title: 'MDR', text: `Rejoins ma partie de MDR ! Code : ${v.code}`, url }).catch(() => {});
      else copy(url, 'Lien d’invitation copié !');
      break;
    }
    case 'retry':
      ui.retry = 0;
      connect();
      break;
    case 'reclaim':
      ui.conn = 'connecting';
      ui.mounted = null;
      connect();
      break;
    case 'home':
      goHome();
      break;
  }
});
const on = (el) => el.classList.contains('is-selected');

// Retour sur l'onglet ou retour du réseau : on se reconnecte tout de suite.
const wake = () => {
  if (ui.session && ui.conn === 'lost') {
    ui.retry = 0;
    connect();
  }
};
window.addEventListener('online', wake);
document.addEventListener('visibilitychange', () => document.visibilityState === 'visible' && wake());

// ── démarrage ─────────────────────────────────────────────
(function boot() {
  const code = (params.get('code') || '').toUpperCase();
  const saved = CODE_RE.test(code) ? store.get(sessionKey(code)) : null;
  if (saved?.token && SERVER) {
    ui.session = saved;
    app.innerHTML = '<p class="boot">Retour dans la salle…</p>';
    connect();
  } else {
    renderHome(code);
  }
})();
