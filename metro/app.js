/* Quai : itinéraires et panneaux de départ en temps réel (Île-de-France).
 * Données : PRIM (Île-de-France Mobilités) → Navitia pour la recherche et les itinéraires,
 * SIRI « stop-monitoring » pour les panneaux en temps réel (Navitia en secours).
 * Pas de build : un seul fichier, des vues rendues selon l'ancre (#/…) pour que le bouton retour marche. */
(() => {
  'use strict';

  const PRIM = 'https://prim.iledefrance-mobilites.fr/marketplace/';
  const CFG = window.METRO_CONFIG || {};
  const $app = document.getElementById('app');
  const REFRESH_MS = 30000;

  /* ───────────── stockage local (toujours protégé : navigation privée, etc.) ───────────── */
  const store = {
    get(k, d) { try { const v = localStorage.getItem('quai.' + k); return v == null ? d : JSON.parse(v); } catch { return d; } },
    set(k, v) { try { localStorage.setItem('quai.' + k, JSON.stringify(v)); } catch { /* rien */ } },
  };

  /* ───────────── utilitaires ───────────── */
  const esc = (s) => String(s ?? '').replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  const norm = (s) => String(s || '').normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase()
    .replace(/\(.*?\)/g, ' ').replace(/[^a-z0-9]+/g, ' ').trim();
  const pad = (n) => String(n).padStart(2, '0');
  const hhmm = (d) => d ? `${pad(d.getHours())}:${pad(d.getMinutes())}` : '';
  // Navitia : 20261115T145000 (heure locale de Paris)
  const navDate = (s) => {
    if (!s) return null;
    const m = /^(\d{4})(\d{2})(\d{2})T(\d{2})(\d{2})(\d{2})$/.exec(s);
    return m ? new Date(+m[1], +m[2] - 1, +m[3], +m[4], +m[5], +m[6]) : null;
  };
  const toNav = (d) => `${d.getFullYear()}${pad(d.getMonth() + 1)}${pad(d.getDate())}T${pad(d.getHours())}${pad(d.getMinutes())}00`;
  const mins = (d) => Math.round((d - Date.now()) / 60000);
  const durTxt = (s) => { const m = Math.round(s / 60); return m < 60 ? `${m} min` : `${Math.floor(m / 60)} h ${pad(m % 60)}`; };
  const lineKey = (id) => (String(id || '').match(/C\d{5}/) || [String(id || '')])[0];
  const areaNum = (id) => (String(id || '').match(/(\d+)$/) || [])[1];
  const qs = (o) => Object.entries(o).filter(([, v]) => v != null && v !== '').map(([k, v]) => `${encodeURIComponent(k)}=${encodeURIComponent(v)}`).join('&');
  const parseHash = () => {
    const h = location.hash.replace(/^#\/?/, '');
    const [path, q = ''] = h.split('?');
    return { path, q: Object.fromEntries(new URLSearchParams(q)) };
  };
  const go = (path, params) => { location.hash = '#/' + path + (params ? '?' + qs(params) : ''); };
  let toastTimer;
  function toast(msg) {
    let t = document.querySelector('.toast');
    if (!t) { t = document.createElement('div'); t.className = 'toast'; document.body.append(t); }
    t.textContent = msg; t.hidden = false;
    clearTimeout(toastTimer); toastTimer = setTimeout(() => { t.hidden = true; }, 2600);
  }

  /* ───────────── accès PRIM ───────────── */
  function settings() { return store.get('settings', {}); }
  function proxyUrl() {
    const s = settings();
    if (s.proxy) return s.proxy.replace(/\/+$/, '');
    if (CFG.proxy) return CFG.proxy.replace(/\/+$/, '');
    if (/^(localhost|127\.0\.0\.1)$/.test(location.hostname)) return 'http://127.0.0.1:8788';
    return '';
  }
  const configured = () => Boolean(settings().key || proxyUrl());

  class ApiError extends Error {}
  const memo = new Map(); // petite mémoire pour éviter de refaire la même requête à quelques secondes d'écart
  async function prim(path, params = {}, ttl = 0) {
    const sp = new URLSearchParams();
    Object.entries(params).forEach(([k, v]) => {
      if (v == null || v === '') return;
      (Array.isArray(v) ? v : [v]).forEach((x) => sp.append(k, x));
    });
    const s = settings();
    const query = sp.toString() ? '?' + sp : '';
    let url; const headers = { Accept: 'application/json' };
    if (s.key) { url = PRIM + path + query; headers.apiKey = s.key; }
    else if (proxyUrl()) url = proxyUrl() + '/prim/' + path + query;
    else throw new ApiError('config');
    const hit = memo.get(url);
    if (ttl && hit && Date.now() - hit.t < ttl * 1000) return hit.data;
    let r;
    try { r = await fetch(url, { headers }); } catch { throw new ApiError('Connexion impossible au service des horaires.'); }
    let data = null;
    try { data = await r.json(); } catch { /* corps vide */ }
    if (!r.ok) {
      if (r.status === 401 || r.status === 403) throw new ApiError('Clé PRIM refusée : vérifie-la dans les réglages.');
      if (r.status === 429) throw new ApiError('Trop de requêtes pour le moment, réessaie dans une minute.');
      const msg = data?.error?.message || data?.message || data?.error;
      // Navitia renvoie 404 quand il n'y a pas d'itinéraire : on laisse l'appelant gérer.
      if (r.status === 404 && data) return data;
      throw new ApiError(typeof msg === 'string' ? msg : `Erreur du service (${r.status}).`);
    }
    if (ttl) memo.set(url, { t: Date.now(), data });
    return data;
  }

  const nav = (p, params, ttl) => prim('v2/navitia/' + p, params, ttl);

  async function searchPlaces(q, onlyStops) {
    const d = await nav('places', { q, 'type[]': onlyStops ? ['stop_area'] : ['stop_area', 'address', 'poi'], count: 8, depth: 1 }, 300);
    return (d.places || []).map((p) => {
      const o = p[p.embedded_type] || {};
      const modes = (o.commercial_modes || []).map((m) => m.name);
      return { id: p.id, name: p.name, type: p.embedded_type, coord: o.coord, modes };
    });
  }

  async function nearbyStops(lon, lat) {
    const d = await nav(`coord/${lon};${lat}/places_nearby`, { 'type[]': 'stop_area', distance: 900, count: 12, depth: 1 }, 60);
    return (d.places_nearby || []).map((p) => ({
      id: p.id, name: p.name, distance: +p.distance,
      modes: (p.stop_area?.commercial_modes || []).map((m) => m.name),
    }));
  }

  const lineCache = new Map();
  async function stopInfo(id) {
    if (lineCache.has(id)) return lineCache.get(id);
    const p = Promise.all([
      nav(`stop_areas/${encodeURIComponent(id)}`, {}, 3600).catch(() => ({})),
      nav(`stop_areas/${encodeURIComponent(id)}/lines`, { count: 100, depth: 1 }, 3600).catch(() => ({})),
    ]).then(([a, l]) => ({
      name: a.stop_areas?.[0]?.name || '',
      coord: a.stop_areas?.[0]?.coord,
      lines: (l.lines || []).map(lineFromNav),
    }));
    lineCache.set(id, p);
    p.catch(() => lineCache.delete(id));
    return p;
  }

  function lineFromNav(l) {
    return {
      id: l.id, key: lineKey(l.id), code: l.code, name: l.name,
      color: l.color || '888888', text: l.text_color || 'FFFFFF',
      mode: l.commercial_mode?.name || '',
    };
  }

  // Panneau d'une gare : SIRI temps réel, sinon Navitia (temps réel si dispo, sinon théorique).
  async function boardFor(stopId) {
    const n = areaNum(stopId);
    let deps = null; let source = 'siri';
    if (n) {
      try {
        const d = await prim('stop-monitoring', { MonitoringRef: `STIF:StopArea:SP:${n}:` }, 15);
        const visits = d?.Siri?.ServiceDelivery?.StopMonitoringDelivery?.[0]?.MonitoredStopVisit;
        if (Array.isArray(visits) && visits.length) deps = visits.map(fromSiri).filter(Boolean);
      } catch (e) { if (e.message === 'config') throw e; }
    }
    if (!deps || !deps.length) {
      source = 'navitia';
      const d = await nav(`stop_areas/${encodeURIComponent(stopId)}/departures`, { count: 60, data_freshness: 'realtime', depth: 1 }, 15);
      deps = (d.departures || []).map(fromNavDeparture);
      if (deps.length && deps.every((x) => x.theoretical)) source = 'theorique';
    }
    const now = Date.now() - 60000;
    deps = deps.filter((x) => x.time && x.time >= now).sort((a, b) => a.time - b.time);
    return { deps, source, at: new Date() };
  }

  const v0 = (x) => (Array.isArray(x) ? x[0]?.value : x?.value) || '';
  function fromSiri(v) {
    const j = v.MonitoredVehicleJourney || {};
    const c = j.MonitoredCall || {};
    const exp = c.ExpectedDepartureTime || c.ExpectedArrivalTime;
    const aim = c.AimedDepartureTime || c.AimedArrivalTime;
    const time = new Date(exp || aim);
    if (isNaN(time)) return null;
    const status = String(c.DepartureStatus || c.ArrivalStatus || '').toLowerCase();
    return {
      line: lineKey(j.LineRef?.value),
      dest: v0(c.DestinationDisplay) || v0(j.DestinationName) || v0(j.DirectionName),
      mission: v0(j.JourneyNote) || v0(j.VehicleJourneyName) || '',
      platform: c.ArrivalPlatformName?.value || c.DeparturePlatformName?.value || '',
      time, aimed: aim ? new Date(aim) : null,
      atStop: Boolean(c.VehicleAtStop),
      cancelled: status === 'cancelled',
      departsHere: Boolean(c.ExpectedDepartureTime || c.AimedDepartureTime),
      long: [].concat(j.VehicleFeatureRef || []).some((f) => /long/i.test(f?.value || f)),
      short: [].concat(j.VehicleFeatureRef || []).some((f) => /short/i.test(f?.value || f)),
      theoretical: false,
    };
  }
  function fromNavDeparture(d) {
    const di = d.display_informations || {};
    const sdt = d.stop_date_time || {};
    const time = navDate(sdt.departure_date_time);
    const base = navDate(sdt.base_departure_date_time);
    const lineId = d.route?.line?.id || (di.links || []).find((l) => l.type === 'line')?.id || '';
    return {
      line: lineKey(lineId), dest: di.direction || '', mission: /^[A-Z]{4}$/.test(di.headsign || '') ? di.headsign : '',
      platform: '', time, aimed: base, atStop: false, cancelled: false, departsHere: true,
      theoretical: sdt.data_freshness !== 'realtime',
      navLine: { id: lineId, code: di.code, color: di.color, text: di.text_color, mode: di.commercial_mode },
    };
  }

  /* ───────────── affichage des lignes ───────────── */
  function badge(l) {
    if (!l) return '';
    const mode = norm(l.mode);
    const code = l.code || '?';
    const st = `background:#${esc(l.color || '888')};color:#${esc(l.text || 'fff')}`;
    let cls = 'badge'; let prefix = '';
    if (mode.includes('rer')) { cls += ' sq'; prefix = 'RER'; }
    else if (mode.includes('transilien') || mode.includes('train') || mode.includes('ter')) { cls += ' sq'; prefix = 'TRAIN'; }
    else if (mode.includes('tram')) { cls += ' pill'; prefix = ''; }
    else if (mode.includes('metro')) { prefix = 'M'; }
    else if (mode.includes('bus')) { cls += ' pill'; prefix = 'BUS'; }
    else if (mode.includes('cable')) { cls += ' pill'; prefix = 'C'; }
    else { cls += ' pill'; }
    return `<span class="lb">${prefix ? `<span class="mode">${prefix}</span>` : ''}<span class="${cls}" style="${st}">${esc(code)}</span></span>`;
  }
  const sectionLine = (s) => {
    const di = s.display_informations || {};
    const lineId = (s.links || []).find((l) => l.type === 'line')?.id || '';
    return { id: lineId, key: lineKey(lineId), code: di.code, color: di.color, text: di.text_color, mode: di.commercial_mode || di.physical_mode };
  };
  const walkIcon = '<svg viewBox="0 0 24 24" width="15" height="15" aria-hidden="true"><path fill="currentColor" d="M13.5 5.5a2 2 0 1 0 0-4 2 2 0 0 0 0 4ZM9.8 8.9 7 23h2.1l1.8-8 2.1 2v6h2v-7.5l-2.1-2 .6-3A7.3 7.3 0 0 0 19 13v-2c-1.9 0-3.5-1-4.3-2.4l-1-1.6A2 2 0 0 0 12 6c-.3 0-.5 0-.8.1L6 8.3V13h2V9.6l1.8-.7"/></svg>';

  /* ───────────── conseils de quai (où se mettre dans le train) ───────────── */
  let sharedTips = {};
  fetch('data/quais.json').then((r) => r.ok && r.json()).then((d) => { sharedTips = d?.conseils || {}; }).catch(() => {});
  const myTips = () => store.get('tips', {});
  const tipKey = (fromId, lineId, toId, purpose) => [fromId, lineKey(lineId), toId, purpose].join('|');
  const getTip = (k) => myTips()[k] || sharedTips[k] || null;
  function saveTip(k, v) { const t = myTips(); if (v) t[k] = v; else delete t[k]; store.set('tips', t); }
  const POS = { avant: 'à l’avant', milieu: 'au milieu', arriere: 'à l’arrière' };
  function trainSvg(pos) {
    const on = { avant: [0, 1], milieu: [2, 3], arriere: [4, 5] }[pos] || [];
    return `<span class="train" aria-hidden="true">${[0, 1, 2, 3, 4, 5].map((i) => `<i class="${on.includes(i) ? 'on' : ''}"></i>`).join('')}<span class="arrow">←</span></span>`;
  }
  // Le sens de la marche est vers la gauche du dessin : la voiture de tête est la première.

  /* ───────────── recherches récentes ───────────── */
  function remember(kind, item) {
    const list = store.get(kind, []).filter((x) => JSON.stringify(x) !== JSON.stringify(item));
    list.unshift(item); store.set(kind, list.slice(0, 8));
  }

  /* ───────────── champ avec suggestions ───────────── */
  function autocomplete(input, { onlyStops, onPick, extra }) {
    const box = document.createElement('div'); box.className = 'ac'; box.hidden = true;
    input.parentElement.append(box);
    let items = []; let sel = -1; let timer; let seq = 0;
    const close = () => { box.hidden = true; sel = -1; };
    const render = () => {
      box.innerHTML = items.map((p, i) => `<button type="button" data-i="${i}" class="${i === sel ? 'on' : ''}">
        <span>${esc(p.name)}</span><span class="kind">${esc(p.label || kindLabel(p))}</span></button>`).join('');
      box.hidden = !items.length;
    };
    input.addEventListener('input', () => {
      clearTimeout(timer);
      const q = input.value.trim();
      if (q.length < 2 || (extra && extra.skip?.(q))) { items = []; render(); return; }
      timer = setTimeout(async () => {
        const my = ++seq;
        try {
          const r = await searchPlaces(q, onlyStops);
          if (my === seq) { items = r; sel = -1; render(); }
        } catch (e) { if (e.message === 'config') showSetup(); }
      }, 220);
    });
    input.addEventListener('keydown', (e) => {
      if (box.hidden) return;
      if (e.key === 'ArrowDown') { sel = Math.min(items.length - 1, sel + 1); render(); e.preventDefault(); }
      else if (e.key === 'ArrowUp') { sel = Math.max(0, sel - 1); render(); e.preventDefault(); }
      else if (e.key === 'Enter' && sel >= 0) { e.preventDefault(); pick(sel); }
      else if (e.key === 'Escape') close();
    });
    box.addEventListener('mousedown', (e) => e.preventDefault());
    box.addEventListener('click', (e) => { const b = e.target.closest('button'); if (b) pick(+b.dataset.i); });
    input.addEventListener('blur', () => setTimeout(close, 150));
    function pick(i) { const p = items[i]; if (!p) return; input.value = p.name; close(); onPick(p); }
  }
  function kindLabel(p) {
    if (p.type === 'stop_area') return p.modes?.length ? p.modes.join(' · ') : 'Gare';
    if (p.type === 'address') return 'Adresse';
    if (p.type === 'poi') return 'Lieu';
    return '';
  }

  /* ───────────── position ───────────── */
  function locate() {
    return new Promise((res, rej) => {
      if (!navigator.geolocation) return rej(new Error('Géolocalisation indisponible sur cet appareil.'));
      navigator.geolocation.getCurrentPosition(
        (p) => res({ lon: p.coords.longitude.toFixed(6), lat: p.coords.latitude.toFixed(6) }),
        () => rej(new Error('Position refusée : autorise la localisation ou choisis un point de départ.')),
        { enableHighAccuracy: true, timeout: 12000, maximumAge: 60000 },
      );
    });
  }

  /* ───────────── phrase libre : « nation rer a vers marne la vallée » ───────────── */
  function parseQuick(text) {
    const t = text.trim();
    const m = t.split(/\s+(?:vers|direction|dir\.?|jusqu['’]?(?:à|a)|pour|->|→|>)\s+/i);
    if (m.length < 2) return null;
    let left = m[0]; const dest = m.slice(1).join(' ').trim();
    let line = null;
    const re = /(?:^|\s)(rer|ligne|lignes|m[ée]tro|m|tram(?:way)?|t|transilien|train|bus)\s*([a-z]|\d{1,3}\s?(?:bis|b|a)?)(?=\s|$)/i;
    const lm = re.exec(left);
    if (lm) {
      const kind = norm(lm[1]); let code = lm[2].replace(/\s/g, '').toUpperCase();
      let mode;
      if (kind === 'rer') mode = 'RER';
      else if (kind === 'metro' || kind === 'm') mode = 'Métro';
      else if (kind.startsWith('tram') || kind === 't') { mode = 'Tramway'; code = 'T' + code.toLowerCase(); }
      else if (kind === 'transilien' || kind === 'train') mode = 'Transilien';
      else if (kind === 'bus') mode = 'Bus';
      else mode = /^[A-E]$/.test(code) ? 'RER' : /^[A-Z]$/.test(code) ? 'Transilien' : 'Métro';
      if (mode === 'Métro') code = code.replace(/BIS|B$/, 'B');
      line = { mode, code };
      left = (left.slice(0, lm.index) + ' ' + left.slice(lm.index + lm[0].length)).trim();
    }
    left = left.replace(/^(de|depuis|à|a)\s+/i, '').trim();
    if (!left || !dest) return null;
    return { from: left, to: dest, line };
  }

  async function findLine({ mode, code }) {
    const d = await nav('pt_objects', { q: `${mode} ${code}`, 'type[]': 'line', count: 15, depth: 1 }, 3600);
    const lines = (d.pt_objects || []).map((o) => o.line).filter(Boolean).map(lineFromNav);
    const c = norm(code).replace(/\s/g, '');
    const want = norm(mode);
    return lines.find((l) => norm(l.code).replace(/\s/g, '') === c && norm(l.mode).includes(want.slice(0, 3)))
      || lines.find((l) => norm(l.code).replace(/\s/g, '') === c) || null;
  }

  async function runQuick(parsed, status) {
    status('Je cherche la gare et la destination…');
    const [from, to, line] = await Promise.all([
      searchPlaces(parsed.from, true).then((r) => r[0]),
      searchPlaces(parsed.to, false).then((r) => r[0]),
      parsed.line ? findLine(parsed.line).catch(() => null) : null,
    ]);
    if (!from) throw new ApiError(`Gare « ${parsed.from} » introuvable.`);
    if (!to) throw new ApiError(`Destination « ${parsed.to} » introuvable.`);
    if (line) {
      // La gare trouvée dessert-elle bien la ligne ? Sinon on prend une gare du même nom qui la dessert.
      let stop = from;
      const info = await stopInfo(from.id).catch(() => null);
      if (info && !info.lines.some((l) => l.key === line.key)) {
        const others = await searchPlaces(parsed.from, true);
        for (const o of others.slice(1, 6)) {
          const oi = await stopInfo(o.id).catch(() => null);
          if (oi?.lines.some((l) => l.key === line.key)) { stop = o; break; }
        }
      }
      remember('boards', { id: stop.id, name: stop.name, line: line.id, to: to.id, toName: to.name });
      go('panneau', { stop: stop.id, name: stop.name, line: line.id, to: to.id, toName: to.name });
    } else {
      remember('trips', { from: from.id, fromName: from.name, to: to.id, toName: to.name });
      go('trajet', { from: from.id, fromName: from.name, to: to.id, toName: to.name });
    }
  }

  /* ───────────── vue : accueil ───────────── */
  const home = { from: null, tab: 'trajet' };
  function viewHome() {
    const trips = store.get('trips', []);
    const boards = store.get('boards', []);
    $app.innerHTML = `
      <div class="search">
        <div class="tabs" role="tablist">
          <button role="tab" data-tab="trajet" aria-selected="${home.tab === 'trajet'}">Itinéraire</button>
          <button role="tab" data-tab="panneau" aria-selected="${home.tab === 'panneau'}">Panneau</button>
        </div>
        <form id="f-trip" ${home.tab !== 'trajet' ? 'hidden' : ''} autocomplete="off">
          <label class="field"><span>Où tu vas ?</span>
            <input class="input big" id="q-to" placeholder="Adresse, gare, lieu…" enterkeyhint="go">
          </label>
          <div class="from-line" id="from-line"></div>
          <label class="field" id="from-field" hidden><span>Départ</span>
            <input class="input" id="q-from" placeholder="Gare ou adresse de départ">
          </label>
          <div class="when-row">
            <span class="muted small">Départ</span>
            <input class="input" type="datetime-local" id="q-when" aria-label="Heure de départ">
            <button type="button" class="btn ghost small" id="q-now">Maintenant</button>
          </div>
          <div class="row-btns"><button class="btn" style="flex:1">Rechercher</button></div>
          <p class="hint">Astuce : écris <code>nation rer a vers val de fontenay</code> pour voir directement les prochains trains du bon quai.</p>
        </form>
        <form id="f-board" ${home.tab !== 'panneau' ? 'hidden' : ''} autocomplete="off">
          <label class="field"><span>Gare ou station</span>
            <input class="input big" id="q-stop" placeholder="Châtelet, Gare de Lyon, Nation…">
          </label>
          <div class="row-btns"><button type="button" class="btn ghost" id="near">Gares autour de moi</button></div>
          <div id="near-list"></div>
        </form>
      </div>
      <div id="home-msg"></div>
      ${trips.length ? `<h2 class="section-title">Trajets récents</h2><div class="chips">${trips.map((t) =>
        `<a class="chip" href="#/trajet?${qs(t)}"><span>${esc(t.fromName || 'Ma position')} → ${esc(t.toName)}</span></a>`).join('')}</div>` : ''}
      ${boards.length ? `<h2 class="section-title">Panneaux récents</h2><div class="chips">${boards.map((b) =>
        `<a class="chip" href="#/panneau?${qs(b)}"><span>${esc(b.name)}${b.toName ? ' → ' + esc(b.toName) : ''}</span></a>`).join('')}</div>` : ''}
    `;
    if (!configured()) showSetup();

    $app.querySelectorAll('[data-tab]').forEach((b) => b.addEventListener('click', () => { home.tab = b.dataset.tab; viewHome(); }));

    const fromLine = $app.querySelector('#from-line');
    const fromField = $app.querySelector('#from-field');
    const renderFrom = () => {
      fromLine.innerHTML = home.from
        ? `Départ : <b>${esc(home.from.name)}</b> <button type="button" class="linkish" id="ch-from">changer</button>`
        : `Départ : <b>ma position</b> <button type="button" class="linkish" id="ch-from">changer</button>`;
      fromLine.querySelector('#ch-from').onclick = () => { fromField.hidden = false; fromLine.hidden = true; $app.querySelector('#q-from').focus(); };
    };
    renderFrom();
    let toPick = null;
    const toInput = $app.querySelector('#q-to');
    autocomplete(toInput, { onPick: (p) => { toPick = p; }, extra: { skip: (q) => Boolean(parseQuick(q)) } });
    toInput.addEventListener('input', () => { toPick = null; });
    autocomplete($app.querySelector('#q-from'), { onPick: (p) => { home.from = p; fromField.hidden = true; fromLine.hidden = false; renderFrom(); } });
    const when = $app.querySelector('#q-when');
    $app.querySelector('#q-now').onclick = () => { when.value = ''; };

    $app.querySelector('#f-trip').addEventListener('submit', async (e) => {
      e.preventDefault();
      const msg = $app.querySelector('#home-msg');
      const status = (t) => { msg.innerHTML = `<div class="loading">${esc(t)}</div>`; };
      try {
        const text = toInput.value.trim();
        if (!text) return toInput.focus();
        const quick = !toPick && parseQuick(text);
        if (quick) return await runQuick(quick, status);
        let to = toPick;
        if (!to) { status('Je cherche la destination…'); to = (await searchPlaces(text, false))[0]; }
        if (!to) throw new ApiError(`« ${text} » introuvable.`);
        let from = home.from;
        if (!from) { status('Je te localise…'); const c = await locate(); from = { id: `${c.lon};${c.lat}`, name: '' }; }
        const params = { from: from.id, fromName: from.name, to: to.id, toName: to.name };
        if (when.value) params.when = toNav(new Date(when.value));
        if (from.name) remember('trips', { from: from.id, fromName: from.name, to: to.id, toName: to.name });
        else remember('trips', { to: to.id, toName: to.name });
        go('trajet', params);
      } catch (err) { showError(msg, err); }
    });

    const stopInput = $app.querySelector('#q-stop');
    autocomplete(stopInput, { onlyStops: true, onPick: (p) => { remember('boards', { id: p.id, name: p.name }); go('panneau', { stop: p.id, name: p.name }); } });
    $app.querySelector('#f-board').addEventListener('submit', async (e) => {
      e.preventDefault();
      const msg = $app.querySelector('#home-msg');
      try {
        const p = (await searchPlaces(stopInput.value.trim(), true))[0];
        if (!p) throw new ApiError('Gare introuvable.');
        remember('boards', { id: p.id, name: p.name }); go('panneau', { stop: p.id, name: p.name });
      } catch (err) { showError(msg, err); }
    });
    $app.querySelector('#near').onclick = async () => {
      const list = $app.querySelector('#near-list');
      list.innerHTML = '<div class="loading">Je cherche les gares proches…</div>';
      try {
        const c = await locate();
        const stops = (await nearbyStops(c.lon, c.lat)).filter((s) => !s.modes.length || s.modes.some((m) => !/bus/i.test(m)));
        list.innerHTML = stops.length ? `<div class="chips" style="margin-top:12px">${stops.map((s) =>
          `<a class="chip" href="#/panneau?${qs({ stop: s.id, name: s.name })}"><span>${esc(s.name)}</span><small class="muted">${s.distance} m</small></a>`).join('')}</div>`
          : '<p class="muted" style="margin-top:12px">Aucune gare à moins de 900 m.</p>';
      } catch (err) { showError(list, err); }
    };
  }

  function showError(el, err) {
    if (err?.message === 'config') { showSetup(); el.innerHTML = ''; return; }
    el.innerHTML = `<div class="notice err"><p>${esc(err?.message || 'Erreur inattendue.')}</p></div>`;
  }

  function showSetup() {
    const el = document.getElementById('home-msg') || $app;
    if (document.getElementById('setup')) return;
    const div = document.createElement('div');
    div.id = 'setup'; div.className = 'notice';
    div.innerHTML = `<h3>Une étape avant les horaires</h3>
      <p class="muted">Les départs en temps réel viennent de PRIM, le service gratuit d’Île-de-France Mobilités. Il faut une clé (une fois) :</p>
      <ol>
        <li>Crée un compte sur prim.iledefrance-mobilites.fr</li>
        <li>Mon compte → « Mon jeton » → génère la clé</li>
        <li>Colle-la dans les réglages de Quai</li>
      </ol>
      <div class="row-btns"><button class="btn" type="button">Ouvrir les réglages</button></div>`;
    div.querySelector('button').onclick = openSettings;
    el.prepend(div);
  }

  /* ───────────── vue : itinéraires ───────────── */
  const tripCache = new Map();
  async function fetchJourneys(q) {
    const key = qs({ from: q.from, to: q.to, when: q.when || '' });
    const c = tripCache.get(key);
    if (c && Date.now() - c.t < 60000) return c.data;
    const d = await nav('journeys', {
      from: q.from, to: q.to, datetime: q.when || toNav(new Date()), datetime_represents: 'departure',
      min_nb_journeys: 4, data_freshness: 'realtime', depth: 1,
    });
    tripCache.set(key, { t: Date.now(), data: d });
    return d;
  }

  async function viewTrip(q) {
    $app.innerHTML = `<a class="back" href="#/">← Nouvelle recherche</a>
      <div class="trip-head"><h1>${esc(q.fromName || 'Ma position')} → ${esc(q.toName || '')}</h1>
      <p class="muted">${q.when ? 'Départ à ' + hhmm(navDate(q.when)) : 'Départ maintenant'}</p></div>
      <div id="res"><div class="loading">Je calcule les itinéraires…</div></div>`;
    const res = $app.querySelector('#res');
    try {
      const d = await fetchJourneys(q);
      const js = (d.journeys || []).filter((j) => j.type !== 'non_pt_walk' || (j.sections || []).length);
      if (!js.length) {
        res.innerHTML = `<div class="notice err"><p>${esc(d.error?.message || 'Aucun itinéraire trouvé.')}</p></div>`;
        return;
      }
      if (q.i != null && js[+q.i]) return viewDetail(q, js[+q.i], d.disruptions || []);
      res.innerHTML = `<div class="journeys">${js.map((j, i) => journeyCard(j, i, q, d.disruptions || [])).join('')}</div>`;
    } catch (err) { showError(res, err); }
  }

  function ptSections(j) { return (j.sections || []).filter((s) => s.type === 'public_transport'); }
  function journeyCard(j, i, q, disrs) {
    const dep = navDate(j.departure_date_time); const arr = navDate(j.arrival_date_time);
    const pts = ptSections(j);
    const first = pts[0]; const firstT = first ? navDate(first.departure_date_time) : null;
    const walk = (j.sections || []).filter((s) => s.type === 'street_network' || s.type === 'transfer').reduce((a, s) => a + (s.duration || 0), 0);
    const chain = (j.sections || []).filter((s) => s.type === 'public_transport' || (s.type === 'street_network' && s.duration > 120))
      .map((s) => s.type === 'public_transport' ? badge(sectionLine(s)) : `<span class="walk">${walkIcon}${Math.round(s.duration / 60)}</span>`)
      .join('<span class="sep">›</span>');
    const hasDisr = pts.some((s) => sectionDisruptions(s, disrs).length);
    const m = firstT ? mins(firstT) : null;
    return `<a class="jcard" href="#/trajet?${qs({ ...q, i })}">
      <div class="jtop"><span class="jtime tnum">${hhmm(dep)} → ${hhmm(arr)}</span><span class="jdur">${durTxt(j.duration)}</span></div>
      <div class="jchain">${chain || '<span class="walk">' + walkIcon + ' à pied</span>'}</div>
      <div class="jfoot">
        <span>${first ? `${badgeText(first)} à <b>${esc(first.from?.name)}</b> ${m != null ? (m <= 0 ? '<span class="soon">maintenant</span>' : `<span class="soon">dans ${m} min</span>`) : ''}` : ''}</span>
        <span>${walk ? `${Math.round(walk / 60)} min à pied` : ''}${hasDisr ? ' · <span class="tag-warn">perturbation</span>' : ''}</span>
      </div></a>`;
  }
  const badgeText = (s) => { const l = sectionLine(s); return `${esc(l.mode || '')} ${esc(l.code || '')}`.trim(); };

  function sectionDisruptions(s, disrs) {
    const ids = new Set((s.display_informations?.links || []).concat(s.links || []).filter((l) => l.type === 'disruption').map((l) => l.id));
    return disrs.filter((d) => ids.has(d.id) || ids.has(d.disruption_id));
  }
  function disrHtml(d) {
    const effect = d.severity?.effect || '';
    const msgs = (d.messages || []);
    const title = msgs.find((m) => /titre|title/i.test(m.channel?.name || ''))?.text || d.severity?.name || 'Perturbation';
    const body = (msgs.find((m) => !/titre|title/i.test(m.channel?.name || '') && m.channel?.content_type !== 'text/html')
      || msgs.find((m) => !/titre|title/i.test(m.channel?.name || '')) || msgs[0])?.text || '';
    return `<div class="disr ${effect === 'NO_SERVICE' ? 'blocking' : ''}"><b>${esc(stripHtml(title))}</b>
      ${body && stripHtml(body) !== stripHtml(title) ? `<details><summary>Détails</summary>${esc(stripHtml(body))}</details>` : ''}</div>`;
  }
  const stripHtml = (s) => String(s || '').replace(/<[^>]+>/g, ' ').replace(/&nbsp;/g, ' ').replace(/\s+/g, ' ').trim();

  function viewDetail(q, j, disrs) {
    const secs = j.sections || [];
    const pts = ptSections(j);
    const res = $app.querySelector('#res');
    const back = { ...q }; delete back.i;
    $app.querySelector('.back').outerHTML = `<a class="back" href="#/trajet?${qs(back)}">← Tous les itinéraires</a>`;
    $app.querySelector('.trip-head p').innerHTML = `${hhmm(navDate(j.departure_date_time))} → ${hhmm(navDate(j.arrival_date_time))} · ${durTxt(j.duration)}`;

    let html = '<div class="steps">';
    secs.forEach((s) => {
      if (s.type === 'waiting') return;
      if (s.type === 'public_transport') {
        const l = sectionLine(s);
        const di = s.display_informations || {};
        const dep = navDate(s.departure_date_time); const depB = navDate(s.base_departure_date_time);
        const arr = navDate(s.arrival_date_time);
        const nStops = Math.max(0, (s.stop_date_times || []).length - 1);
        const idx = pts.indexOf(s);
        const next = pts[idx + 1];
        const fromId = s.from?.stop_point?.stop_area?.id || s.from?.id;
        const toId = s.to?.stop_point?.stop_area?.id || s.to?.id;
        const purpose = next ? 'corresp:' + lineKey(sectionLine(next).id) : 'sortie';
        const tk = tipKey(fromId, l.id, toId, purpose);
        const late = depB && dep && dep - depB >= 60000;
        html += `<div class="step" style="--c:#${esc(l.color || '888')}"><span class="dot"></span>
          <div class="stop-row"><b>${esc(s.from?.name)}</b><span class="t tnum">${late ? `<s>${hhmm(depB)}</s>` : ''}${hhmm(dep)}</span></div>
          <div class="leg">
            <div class="leg-head">${badge(l)}<span class="dir">Direction ${esc(di.direction || '')}</span></div>
            <div class="leg-sub">${di.headsign && di.headsign !== di.code ? `Mission <b>${esc(di.headsign)}</b> · ` : ''}${nStops} arrêt${nStops > 1 ? 's' : ''} · ${durTxt(s.duration)} · descends à <b>${esc(s.to?.name)}</b></div>
            ${sectionDisruptions(s, disrs).map(disrHtml).join('')}
            <div class="live" data-live="${esc(fromId)}" data-line="${esc(l.key)}" data-dir="${esc(di.direction || '')}"><span class="lbl">Prochains</span><span class="muted small">chargement…</span></div>
            <div class="tip" data-tip="${esc(tk)}" data-purpose="${esc(next ? `pour la correspondance ${badgeText(next)}` : 'pour la sortie')}"></div>
            <div class="leg-actions">
              <a class="btn ghost small" href="#/panneau?${qs({ stop: fromId, name: s.from?.stop_point?.stop_area?.name || s.from?.name, line: l.id, to: toId, toName: s.to?.name })}">Panneau en temps réel</a>
            </div>
          </div>
        </div>`;
        html += `<div class="step" style="--c:#${esc(l.color || '888')}"><span class="dot"></span>
          <div class="stop-row"><b>${esc(s.to?.name)}</b><span class="t tnum">${hhmm(arr)}</span></div><div style="height:14px"></div></div>`;
      } else if (s.type === 'street_network' || s.type === 'transfer' || s.type === 'crow_fly') {
        if (!s.duration) return;
        const what = s.type === 'transfer' ? 'Correspondance' : s.mode === 'bike' ? 'Vélo' : 'Marche';
        html += `<div class="step walkstep"><span class="dot"></span>
          <div class="walkline">${walkIcon} ${what} · ${durTxt(s.duration)}${s.to?.name && s.type !== 'transfer' ? ` jusqu’à ${esc(s.to.name)}` : ''}</div></div>`;
      }
    });
    html += '</div>';
    res.innerHTML = html;
    res.querySelectorAll('.tip').forEach(renderTip);
    loadLive(res);
  }

  async function loadLive(root) {
    const els = [...root.querySelectorAll('[data-live]')];
    await Promise.all(els.map(async (el) => {
      try {
        const b = await boardFor(el.dataset.live);
        const dir = norm(el.dataset.dir);
        const list = b.deps.filter((d) => d.line === el.dataset.line && !d.cancelled && d.departsHere)
          .filter((d) => !dir || sameDir(d.dest, dir)).slice(0, 3);
        el.innerHTML = '<span class="lbl">Prochains</span>' + (list.length
          ? list.map((d) => { const m = mins(d.time); const late = d.aimed && d.time - d.aimed >= 60000;
            return `<span class="pillt tnum ${late ? 'late' : ''}">${d.atStop ? 'à quai' : m <= 0 ? 'imminent' : m + ' min'}${d.platform ? ` <small>voie ${esc(d.platform)}</small>` : ''}</span>`; }).join('')
            + (b.source === 'siri' ? '' : '<span class="muted small">(horaires théoriques)</span>')
          : '<span class="muted small">pas de passage annoncé pour le moment</span>');
      } catch { el.innerHTML = '<span class="lbl">Prochains</span><span class="muted small">indisponible</span>'; }
    }));
  }

  // Deux libellés de destination désignent-ils le même terminus ?
  function sameDir(a, b) {
    const x = norm(a); const y = norm(b);
    if (!x || !y) return false;
    if (x === y || x.startsWith(y) || y.startsWith(x) || x.includes(y) || y.includes(x)) return true;
    const tx = new Set(x.split(' ').filter((w) => w.length > 3));
    return y.split(' ').filter((w) => w.length > 3).some((w) => tx.has(w));
  }

  function renderTip(el) {
    const k = el.dataset.tip; const tip = getTip(k); const purpose = el.dataset.purpose;
    if (tip && !el.dataset.edit) {
      el.innerHTML = `<div class="tip-row">${trainSvg(tip.pos)}
        <div class="tip-txt">Monte <b>${POS[tip.pos] || ''}</b> du train ${esc(purpose)}${tip.detail ? ` · ${esc(tip.detail)}` : ''}
        <button class="linkish small" type="button">modifier</button></div></div>`;
      el.querySelector('button').onclick = () => { el.dataset.edit = '1'; renderTip(el); };
      return;
    }
    if (!el.dataset.edit) {
      el.innerHTML = `<div class="tip-row"><span class="muted small">Où te mettre sur le quai ${esc(purpose)} ?</span>
        <button class="linkish small" type="button">ajouter un repère</button></div>`;
      el.querySelector('button').onclick = () => { el.dataset.edit = '1'; renderTip(el); };
      return;
    }
    let pos = tip?.pos || '';
    el.innerHTML = `<div class="tip-form">
      <div class="small muted">Dans le sens de la marche, ${esc(purpose)} :</div>
      <div class="pos-pick">${Object.entries({ avant: 'Avant', milieu: 'Milieu', arriere: 'Arrière' }).map(([v, t]) =>
        `<button type="button" data-pos="${v}" aria-pressed="${pos === v}">${t}</button>`).join('')}</div>
      <input class="input" placeholder="Voiture, porte, n° de sortie… (facultatif)" value="${esc(tip?.detail || '')}" maxlength="80">
      <div class="row-btns"><button type="button" class="btn small" data-act="save">Enregistrer</button>
      ${tip ? '<button type="button" class="btn ghost small" data-act="del">Supprimer</button>' : ''}
      <button type="button" class="btn ghost small" data-act="cancel">Annuler</button></div></div>`;
    el.querySelectorAll('[data-pos]').forEach((b) => b.onclick = () => {
      pos = b.dataset.pos; el.querySelectorAll('[data-pos]').forEach((x) => x.setAttribute('aria-pressed', x === b));
    });
    el.querySelector('[data-act="save"]').onclick = () => {
      if (!pos) return toast('Choisis avant, milieu ou arrière.');
      saveTip(k, { pos, detail: el.querySelector('input').value.trim() }); delete el.dataset.edit; renderTip(el); toast('Repère enregistré');
    };
    el.querySelector('[data-act="cancel"]').onclick = () => { delete el.dataset.edit; renderTip(el); };
    el.querySelector('[data-act="del"]')?.addEventListener('click', () => { saveTip(k, null); delete el.dataset.edit; renderTip(el); });
  }

  /* ───────────── vue : panneau de départs ───────────── */
  let boardTimer = null; let tickTimer = null;
  async function viewBoard(q) {
    const stop = q.stop;
    $app.innerHTML = `<a class="back" href="javascript:history.back()">← Retour</a>
      <div class="board-head"><div><h1 id="b-name">${esc(q.name || 'Gare')}</h1><div class="fresh" id="b-fresh">chargement…</div></div>
      <button class="btn ghost small" id="b-refresh">Actualiser</button></div>
      <div id="b-goal"></div>
      <div class="chips line-filter" id="b-lines"></div>
      <div class="board" id="b-board"><div class="loading" style="padding:22px 14px">Je lis le panneau…</div></div>`;
    if (history.length <= 1) $app.querySelector('.back').href = '#/';
    let filter = q.line ? lineKey(q.line) : '';
    let info = { lines: [] }; let data = null; let dirs = null; let goalArr = null;

    stopInfo(stop).then((i) => {
      info = i; if (i.name && !q.name) $app.querySelector('#b-name').textContent = i.name;
      renderLines(); render();
    }).catch(() => {});

    // Trajet direct jusqu'à la destination : directions valables et heure d'arrivée.
    if (q.to) {
      nav('journeys', {
        from: stop, to: q.to, datetime: toNav(new Date()), max_nb_transfers: 0, min_nb_journeys: 6, data_freshness: 'realtime', depth: 0,
        'allowed_id[]': q.line ? [q.line] : undefined,
      }, 30).then((d) => {
        const js = (d.journeys || []).filter((j) => ptSections(j).length === 1);
        dirs = [...new Set(js.map((j) => ptSections(j)[0].display_informations?.direction).filter(Boolean))];
        goalArr = js.map((j) => ({ dep: navDate(ptSections(j)[0].departure_date_time), arr: navDate(ptSections(j)[0].arrival_date_time), stopTo: ptSections(j)[0].to?.name }));
        if (!filter && js[0]) filter = lineKey(sectionLine(ptSections(js[0])[0]).id);
        renderLines(); render();
      }).catch(() => { dirs = []; render(); });
    }

    const lineOf = (key) => info.lines.find((l) => l.key === key) || data?.deps.find((d) => d.line === key)?.navLine;
    function renderLines() {
      const keys = [...new Set([...info.lines.filter((l) => !/bus/i.test(l.mode)).map((l) => l.key), ...(data?.deps || []).map((d) => d.line)])];
      const el = $app.querySelector('#b-lines'); if (!el) return;
      if (keys.length < 2) { el.innerHTML = ''; return; }
      el.innerHTML = `<button class="chip ${!filter ? 'on' : ''}" data-l="">Toutes</button>` + keys.map((k) => {
        const l = lineOf(k); return `<button class="chip ${filter === k ? 'on' : ''}" data-l="${esc(k)}">${l ? badge(l) : esc(k)}</button>`;
      }).join('');
      el.querySelectorAll('[data-l]').forEach((b) => b.onclick = () => { filter = b.dataset.l; renderLines(); render(); });
    }

    function render() {
      const board = $app.querySelector('#b-board'); if (!board || !data) return;
      const fresh = $app.querySelector('#b-fresh');
      const age = Math.round((Date.now() - data.at) / 1000);
      fresh.className = 'fresh' + (data.source === 'siri' ? '' : ' theo');
      fresh.textContent = (data.source === 'siri' ? 'Temps réel' : data.source === 'navitia' ? 'Temps réel (Navitia)' : 'Horaires théoriques')
        + ` · mis à jour ${age < 10 ? 'à l’instant' : `il y a ${age} s`}`;

      const here = norm(info.name || q.name);
      let deps = data.deps.filter((d) => !(here && d.dest && norm(d.dest) === here && !d.departsHere));
      // Pas d'arrivées de bus sur le panneau d'une gare ferrée, sauf si c'est un arrêt de bus.
      if (filter) deps = deps.filter((d) => d.line === filter);
      const match = (d) => dirs && dirs.length ? dirs.some((x) => sameDir(d.dest, x)) : null;

      const goal = $app.querySelector('#b-goal');
      if (q.to) {
        if (!dirs) goal.innerHTML = `<div class="goal">Je regarde quels trains vont à <b>${esc(q.toName || '')}</b>…</div>`;
        else if (!dirs.length) goal.innerHTML = `<div class="goal">Pas de train direct trouvé vers <b>${esc(q.toName || '')}</b> depuis cette gare.</div>`;
        else {
          const firstOk = deps.find((d) => match(d) && !d.cancelled);
          const g = firstOk && goalArr?.find((x) => x.dep && Math.abs(x.dep - firstOk.time) < 3 * 60000);
          goal.innerHTML = `<div class="goal">Pour <b>${esc(q.toName || '')}</b> : trains surlignés, direction ${dirs.map((x) => `<b>${esc(x)}</b>`).join(' ou ')}.
            ${firstOk ? `<br>Prochain : ${hhmm(firstOk.time)}${firstOk.platform ? `, voie ${esc(firstOk.platform)}` : ''}${g?.arr ? ` → arrivée vers <b>${hhmm(g.arr)}</b>` : ''}.` : ''}</div>`;
        }
      }

      if (!deps.length) { board.innerHTML = '<div class="empty">Aucun départ annoncé pour le moment.</div>'; return; }
      // Groupement par ligne quand on affiche tout.
      const groups = filter ? [[filter, deps]] : [...deps.reduce((m, d) => m.set(d.line, [...(m.get(d.line) || []), d]), new Map())];
      board.innerHTML = groups.map(([k, list]) => {
        const l = lineOf(k);
        return `${!filter ? `<div class="board-group">${l ? badge(l) : ''}<span>${esc(l?.name || '')}</span></div>` : ''}
          ${list.slice(0, filter ? 20 : 6).map((d) => depRow(d, l, match(d))).join('')}`;
      }).join('');
    }

    function depRow(d, l, ok) {
      const m = mins(d.time);
      const delay = d.aimed ? Math.round((d.time - d.aimed) / 60000) : 0;
      let big;
      if (d.cancelled) big = `${m} <small>min</small>`;
      else if (d.atStop) big = '<span class="at">À quai</span>';
      else if (m <= 0) big = '<span class="at">Imminent</span>';
      else if (m >= 60) big = hhmm(d.time);
      else big = `${m}<small>min</small>`;
      const cls = ['dep', d.cancelled ? 'cancel' : '', ok === true ? 'match' : ok === false ? 'nomatch' : ''].join(' ');
      return `<div class="${cls}">
        <span style="grid-row:1/span 2">${l ? badge(l) : ''}</span>
        <span class="dest">${esc(d.dest || '—')}</span>
        <span class="when tnum"><div class="m">${big}</div>
          <div class="h">${d.cancelled ? 'Supprimé' : delay >= 1 ? `<span class="late">+${delay} min</span> ${hhmm(d.time)}` : hhmm(d.time)}</div></span>
        <span class="meta">${d.mission ? `<span class="mission">${esc(d.mission)}</span>` : ''}${d.platform ? `<span class="voie">Voie ${esc(d.platform)}</span>` : ''}${d.long ? '<span>train long</span>' : d.short ? '<span>train court</span>' : ''}${ok === true ? '<span class="ok">✓ ton train</span>' : ''}${d.theoretical ? '<span>théorique</span>' : ''}</span>
      </div>`;
    }

    async function load() {
      try {
        data = await boardFor(stop);
        renderLines(); render();
      } catch (err) {
        const board = $app.querySelector('#b-board');
        if (board) showError(board, err);
        if (err.message === 'config') { $app.querySelector('#b-board').innerHTML = ''; const div = document.createElement('div'); div.id = 'home-msg'; $app.append(div); showSetup(); }
      }
    }
    $app.querySelector('#b-refresh').onclick = () => { memo.clear(); load(); };
    await load();
    boardTimer = setInterval(() => { if (!document.hidden) load(); }, REFRESH_MS);
    tickTimer = setInterval(render, 10000);
  }

  /* ───────────── réglages ───────────── */
  const dlg = document.getElementById('settings');
  function openSettings() {
    const s = settings();
    dlg.querySelector('#set-proxy').value = s.proxy || '';
    dlg.querySelector('#set-proxy').placeholder = CFG.proxy || 'https://metro-prim.…workers.dev';
    dlg.querySelector('#set-key').value = s.key || '';
    const n = Object.keys(myTips()).length;
    dlg.querySelector('#tips-count').textContent = `${n} repère${n > 1 ? 's' : ''} enregistré${n > 1 ? 's' : ''} sur cet appareil.`;
    dlg.showModal();
  }
  document.getElementById('btn-settings').onclick = openSettings;
  dlg.addEventListener('close', () => {
    if (dlg.returnValue !== 'save') return;
    store.set('settings', { proxy: dlg.querySelector('#set-proxy').value.trim(), key: dlg.querySelector('#set-key').value.trim() });
    memo.clear(); lineCache.clear(); tripCache.clear();
    toast('Réglages enregistrés'); route();
  });
  dlg.querySelector('#tips-export').onclick = async () => {
    const txt = JSON.stringify(myTips(), null, 2);
    try { await navigator.clipboard.writeText(txt); toast('Repères copiés'); } catch { prompt('Copie ce texte :', txt); }
  };
  dlg.querySelector('#tips-import').onclick = () => {
    const txt = prompt('Colle ici des repères (JSON) :');
    if (!txt) return;
    try {
      const obj = JSON.parse(txt);
      if (!obj || typeof obj !== 'object') throw new Error();
      store.set('tips', { ...myTips(), ...(obj.conseils || obj) }); toast('Repères importés');
      dlg.querySelector('#tips-count').textContent = `${Object.keys(myTips()).length} repères enregistrés sur cet appareil.`;
    } catch { toast('Texte invalide'); }
  };

  /* ───────────── routeur ───────────── */
  function route() {
    clearInterval(boardTimer); clearInterval(tickTimer);
    const { path, q } = parseHash();
    window.scrollTo(0, 0);
    if (path === 'trajet' && q.to) return viewTrip(q);
    if (path === 'panneau' && q.stop) return viewBoard(q);
    return viewHome();
  }
  window.addEventListener('hashchange', route);
  document.addEventListener('visibilitychange', () => { if (!document.hidden && parseHash().path === 'panneau') { memo.clear(); } });
  route();

  // Exposé pour les tests.
  window.__quai = { parseQuick, sameDir };
})();
