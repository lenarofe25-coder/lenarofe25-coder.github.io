/* Planner E6 — rendu des pages, sauvegarde locale, progression. */
(() => {
const { BLOCS, METHOD, R, GAPS, DAYS, COMPETENCES, EXAMS, E6 } = window.PLANNER;
const STORE = 'planner-e6-sisr-v1';
const PRINT_MODE = new URLSearchParams(location.search).has('vierge'); // version vierge (PDF)

/* ───────── icônes (traits fins) ───────── */
const P = {
  net: '<circle cx="12" cy="5" r="2.2"/><circle cx="5" cy="19" r="2.2"/><circle cx="19" cy="19" r="2.2"/><path d="M12 7.2v4.3m0 0-5.4 5.6M12 11.5l5.4 5.6"/>',
  win: '<rect x="3.5" y="3.5" width="7.4" height="7.4" rx="1.2"/><rect x="13.1" y="3.5" width="7.4" height="7.4" rx="1.2"/><rect x="3.5" y="13.1" width="7.4" height="7.4" rx="1.2"/><rect x="13.1" y="13.1" width="7.4" height="7.4" rx="1.2"/>',
  term: '<rect x="3" y="4.5" width="18" height="15" rx="2.2"/><path d="m7 10 3 2.5L7 15m5.5 0H17"/>',
  layers: '<path d="M12 3.5 3 8l9 4.5L21 8z"/><path d="m3 12.3 9 4.5 9-4.5"/><path d="m3 16.3 9 4.5 9-4.5"/>',
  rack: '<rect x="4" y="3.5" width="16" height="6.5" rx="1.4"/><rect x="4" y="14" width="16" height="6.5" rx="1.4"/><path d="M7.5 6.75h.01M7.5 17.25h.01M11 6.75h5.5M11 17.25h5.5M12 10v4"/>',
  wrench: '<path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z"/>',
  flask: '<path d="M10 2.5v7a2 2 0 0 1-.2.9l-5 10.1a1 1 0 0 0 .9 1.5h12.6a1 1 0 0 0 .9-1.5l-5-10.1a2 2 0 0 1-.2-.9v-7"/><path d="M8.5 2.5h7M7 16h10"/>',
  target: '<circle cx="12" cy="12" r="9"/><circle cx="12" cy="12" r="5"/><circle cx="12" cy="12" r="1.2"/>',
  mic: '<rect x="9" y="3" width="6" height="11" rx="3"/><path d="M5.5 11a6.5 6.5 0 0 0 13 0M12 17.5V21m-3 0h6"/>',
  moon: '<path d="M20 14.5A8 8 0 1 1 9.5 4a6.5 6.5 0 0 0 10.5 10.5z"/>',
  exam: '<path d="M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8z"/><path d="M14 3v5h5M9 14.5l2 2 4-4"/>',
  book: '<path d="M5 18.5V5a1.5 1.5 0 0 1 1.5-1.5H19v15H6.5A1.5 1.5 0 0 0 5 20a1.5 1.5 0 0 0 1.5 1.5H19"/>',
  doc: '<path d="M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8z"/><path d="M14 3v5h5M9 13h6M9 17h6"/>',
  pencil: '<path d="M4 20h4L19 9l-4-4L4 16z"/><path d="m13.5 6.5 4 4"/>',
  quiz: '<circle cx="12" cy="12" r="9"/><path d="M9.6 9.4a2.5 2.5 0 1 1 3.4 2.4c-.6.3-1 .8-1 1.5v.4M12 16.8h.01"/>',
  list: '<path d="M9.5 6.5H20M9.5 12H20M9.5 17.5H20"/><path d="m3.8 6.4 1.1 1.1 2-2.1M3.8 11.9l1.1 1.1 2-2.1M3.8 17.4l1.1 1.1 2-2.1"/>',
  link: '<path d="M10 13.5a4.5 4.5 0 0 0 6.4.4l2.6-2.6a4.5 4.5 0 0 0-6.4-6.4l-1.2 1.2"/><path d="M14 10.5a4.5 4.5 0 0 0-6.4-.4L5 12.7a4.5 4.5 0 0 0 6.4 6.4l1.2-1.2"/>',
  star: '<path d="m12 3.5 2.6 5.4 5.9.8-4.3 4.1 1 5.8L12 16.9l-5.2 2.7 1-5.8-4.3-4.1 5.9-.8z"/>',
  alert: '<path d="M12 4 2.8 19.5h18.4z"/><path d="M12 10v4.2M12 17h.01"/>',
  redo: '<path d="M3.5 12a8.5 8.5 0 1 0 2.6-6.1L3.5 8.5"/><path d="M3.5 3.5v5h5"/>',
  clock: '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3.2 2"/>',
  chart: '<path d="M4 20V4M4 20h16"/><path d="M8 16v-4M12 16V8M16 16v-6"/>',
  print: '<path d="M7 9V3.5h10V9"/><rect x="3.5" y="9" width="17" height="8" rx="1.8"/><path d="M7 14.5h10v6H7z"/>',
  down: '<path d="M12 4v11m-4.5-4.5L12 15l4.5-4.5M5 20h14"/>',
  up: '<path d="M12 15V4M7.5 8.5 12 4l4.5 4.5M5 20h14"/>',
  reset: '<path d="M3.5 12a8.5 8.5 0 1 0 2.6-6.1L3.5 8.5"/><path d="M3.5 3.5v5h5"/>',
  check: '<path d="m5 12.5 4.5 4.5L19 7.5"/>',
  users: '<circle cx="9" cy="8" r="3.2"/><path d="M3 20a6 6 0 0 1 12 0"/><path d="M16 5.2a3 3 0 0 1 0 5.6M21 20a6 6 0 0 0-3.5-5.4"/>',
};
const ico = (n, cls = '') => `<svg class="${cls}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${P[n] || ''}</svg>`;
const typeIcon = y => /TP/.test(y) ? 'flask' : /Exercice/.test(y) ? 'pencil' : /Quiz/.test(y) && !/Cours/.test(y) ? 'quiz' : /Documentation/.test(y) ? 'doc' : 'book';
const LVL = { 1: 'Débutant', 2: 'Intermédiaire', 3: 'Avancé' };
const bloc = id => BLOCS.find(b => b.id === id);
const bcolor = id => `var(--b${id})`;
const esc = s => String(s).replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
const shortUrl = u => u.replace(/^https?:\/\//, '').replace(/\/$/, '');

/* ───────── état (localStorage, tolérant aux erreurs) ───────── */
let S = {};
if (!PRINT_MODE) { try { S = JSON.parse(localStorage.getItem(STORE) || '{}') || {}; } catch { S = {}; } }
const save = () => { if (PRINT_MODE) return; try { localStorage.setItem(STORE, JSON.stringify(S)); } catch {} };

/* ───────── petits composants ───────── */
const chip = (id, cls = '') => { const b = bloc(id); return `<span class="chip ${cls}" style="--c:${bcolor(id)}"><i>${id}</i>${esc(b.name)}</span>`; };
const ck = (k, label, { b = '', cls = '', html = false, radio = null, value = '' } = {}) => {
  const attrs = radio
    ? `type="radio" name="${radio}" value="${esc(value)}" data-k="${radio}"`
    : `type="checkbox" data-k="${k}"`;
  return `<label class="ck ${radio ? 'radio' : ''} ${cls}"><input ${attrs} ${b !== '' ? `data-b="${b}"` : ''}><span class="t"><span class="lbl">${html ? label : esc(label)}</span></span></label>`;
};
const writeZone = (k, title, icon) => `<div class="write">${title ? `<div class="wtitle">${ico(icon)}${title}</div>` : ''}<textarea data-k="${k}" aria-label="${esc(title)}" spellcheck="true"></textarea></div>`;
const score = (k, on = 20) => `<span class="score"><input type="text" inputmode="decimal" maxlength="4" data-k="${k}" aria-label="Note"><b>/ ${on}</b></span>`;
const foot = label => `<div class="pfoot"><span><b>Planner E6</b> · BTS SIO option SISR</span><span>${label}</span><span class="pn"></span></div>`;
const head = ({ eyebrow, title, sub = '', meta = '' }) => `<header class="phead"><div><div class="eyebrow">${eyebrow}</div><h2 class="ptitle">${title}</h2>${sub ? `<div class="psub">${sub}</div>` : ''}</div><div class="hmeta">${meta}</div></header>`;

/* dates */
const dayIndex = d => (d.week - 1) * 7 + ['Lundi', 'Mardi', 'Mercredi', 'Jeudi', 'Vendredi', 'Samedi', 'Dimanche'].indexOf(d.dow);
function dateFor(d) {
  if (!S.start) return '';
  const base = new Date(S.start + 'T12:00:00');
  if (isNaN(base)) return '';
  base.setDate(base.getDate() + dayIndex(d));
  return base.toLocaleDateString('fr-FR', { weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' });
}
const dateBox = d => `<div class="datebox"><span>Date</span><b data-date="${d.key}"></b></div>`;

/* blocs associés à un élément de jour */
const itemBlocs = (d, ch) => {
  if (ch && ch.b !== undefined) return [].concat(ch.b);
  return d.bloc ? [d.bloc] : [];
};
const bAttr = arr => arr.join(' ');

const workDays = DAYS.filter(d => d.kind === 'work');
const workNum = d => workDays.indexOf(d) + 1;

/* ───────── pages ───────── */
function pageCover() {
  return `<section class="page cover" id="couverture" data-label="Couverture">
  <div class="body">
    <div>
      <div class="eyebrow">BTS SIO · option SISR · épreuve E6</div>
      <h1>Planner de révision<br><em>Administration des systèmes et des réseaux</em></h1>
      <p class="lede">Deux semaines pour reprendre les six blocs, s’entraîner sur des cas concrets et passer deux BTS blancs dans les conditions de l’épreuve pratique et orale.</p>
      <div class="owner">
        <div class="datebox"><span>Prénom et nom</span><b><input class="plain" data-k="owner" aria-label="Prénom et nom"></b></div>
        <div class="datebox"><span>Début des révisions (lundi)</span><b data-start></b></div>
      </div>
      <div class="goal"><b>Mon objectif : 15/20 minimum sur chaque bloc.</b><span>Un bloc est validé quand j’obtiens au moins 15/20, que je sais expliquer chaque notion à l’oral et réaliser les manipulations.</span></div>
      <div class="blocs6">${BLOCS.map(b => `<div><span class="n" style="--c:${bcolor(b.id)}">${ico(b.icon)}</span>${b.id} · ${esc(b.name)}</div>`).join('')}</div>
    </div>
    <div class="col">
      <div class="card white">
        <div class="ctitle">${ico('list')}Mode d’emploi d’une journée</div>
        <ol class="steps">
          <li><span><b>Matin — comprendre.</b> Lis le cours complet puis la fiche de révision ; coche chaque chapitre vu.</span></li>
          <li><span><b>Fin de matinée — s’exercer.</b> Exercices facile, intermédiaire puis difficile, sans regarder le corrigé.</span></li>
          <li><span><b>Après-midi — pratiquer.</b> Réalise l’exercice pratique sur ta maquette (Packet Tracer, VM, Proxmox).</span></li>
          <li><span><b>Fin d’après-midi — vérifier.</b> Quiz express noté sur 20, puis corrigés en fin de planner.</span></li>
          <li><span><b>Soir — bilan.</b> Remplis tes zones de notes, ton niveau de maîtrise et la page de suivi.</span></li>
        </ol>
      </div>
      <div class="card sky e6box">
        <div class="ctitle">${ico('exam')}L’épreuve E6 en bref</div>
        ${E6.map(p => `<p>${p}</p>`).join('')}
        <p class="src">Format décrit par les documents d’établissement consultés. Vérifie les modalités exactes dans la circulaire nationale de ta session.</p>
      </div>
      <div class="card">
        <div class="ctitle">${ico('link')}Légende des ressources</div>
        <div class="legend">
          <div><span class="tag lvl-1">Débutant</span>premier contact</div>
          <div><span class="tag type">Cours</span>apprendre</div>
          <div><span class="tag lvl-2">Intermédiaire</span>consolider</div>
          <div><span class="tag type">TP</span>manipuler</div>
          <div><span class="tag lvl-3">Avancé</span>approfondir</div>
          <div><span class="tag type">Documentation</span>référence officielle</div>
        </div>
      </div>
    </div>
  </div>${foot('Couverture')}</section>`;
}

function dayCell(d) {
  const date = `<div class="dd" data-date="${d.key}"></div>`;
  if (d.kind === 'rest') {
    return `<div class="day rest"><div class="dn"><b>${d.dow}</b><span>S${d.week}</span></div>${ico('moon')}<h4>Repos</h4><p>Aucune révision. Déconnecte, dors, bouge : c’est aussi ça, réussir.</p></div>`;
  }
  if (d.kind === 'exam') {
    const e = EXAMS[d.exam];
    return `<a class="day exam" href="#bts${d.exam}"><div class="dn"><b>${d.dow}</b><span>S${d.week}</span></div>${date}
      <span class="chip">${ico('exam')}${e.title}</span>
      <h4>${d.exam === 1 ? 'Blocs 1 à 4' : 'Les 6 blocs'}</h4>
      <ul><li>Cas pratique professionnel</li><li>Questions techniques</li>${d.exam === 2 ? '<li>Manipulations + oral</li>' : '<li>Explication orale</li>'}<li>Correction et note /20</li></ul>
      <div class="foot"><div class="bar"><i data-prog="exam${d.exam}"></i></div></div></a>`;
  }
  const tag = d.bloc ? chip(d.bloc) : `<span class="chip soft"><i>${ico(d.icon)}</i>Les 6 blocs</span>`;
  return `<a class="day" href="#${d.key}"><div class="dn"><b>${d.dow}</b><span>J${workNum(d)}</span></div>${date}
    ${tag}<h4>${esc(d.title)}${d.part ? ` <span style="font-weight:500;color:var(--muted)">· ${d.part}</span>` : ''}</h4>
    <ul>${d.chapters.map(c => `<li>${esc(c.t)}</li>`).join('')}</ul>
    <div class="foot"><div class="bar"><i data-prog="${d.key}"></i></div></div></a>`;
}

function pageOverview() {
  const w = n => DAYS.filter(d => d.week === n).map(dayCell).join('');
  return `<section class="page overview" id="planning" data-label="Vue d’ensemble">
  ${head({ eyebrow: 'Planning', title: 'Deux semaines, <em>six blocs</em>, deux BTS blancs', meta: `<div class="ovlegend"><span class="chip soft"><i>${ico('book')}</i>Jour de révision</span><span class="chip gold"><i>${ico('exam')}</i>BTS blanc</span><span class="chip line"><i>${ico('moon')}</i>Repos</span></div>` })}
  <div class="body">
    <div class="wk"><h3>Semaine 1</h3><span>Apprendre les blocs 1 à 4 · BTS blanc n°1 le dimanche</span></div>
    <div class="week">${w(1)}</div>
    <div class="wk"><h3>Semaine 2</h3><span>Blocs 5 et 6, pratique, révisions ciblées · BTS blanc n°2 le dimanche</span></div>
    <div class="week">${w(2)}</div>
  </div>${foot('Vue d’ensemble')}</section>`;
}

function pageDayA(d) {
  const n = workNum(d);
  const blocsOfDay = d.bloc ? [d.bloc] : d.blocs;
  const chips = d.bloc ? chip(d.bloc) : blocsOfDay.map(b => chip(b, 'soft')).join(' ');
  const progs = d.chapters.map((c, i) => {
    const bs = itemBlocs(d, c);
    const tagB = c.b !== undefined ? ` <span style="font-weight:500;color:var(--faint);font-size:6.6pt">· bloc ${[].concat(c.b).join(' et ')}</span>` : '';
    return ck(`${d.key}.ch${i}`, `<span class="lbl">${esc(c.t)}${tagB}</span><span class="key">${esc(c.k)}</span>`, { b: bAttr(bs), html: true });
  }).join('');
  const meth = METHOD.map((m, i) => ck(`${d.key}.m${i}`, m, { b: bAttr(itemBlocs(d)) })).join('');
  const lv = { f: ['Facile', 1], i: ['Intermédiaire', 2], d: ['Difficile', 3], p: ['Pratique', 4] };
  const exos = Object.entries(lv).map(([k, [name, dots]]) => `<div class="exo ${k === 'p' ? 'tp' : ''}">
      <div class="lv">${k === 'p' ? ico('flask', 'tpi') : `<span class="dots">${[1, 2, 3].map(x => `<b class="${x <= dots ? 'on' : ''}"></b>`).join('')}</span>`}${name}${ck(`${d.key}.x${k}`, '', { b: bAttr(itemBlocs(d)) })}</div>
      <p>${d.exos[k]}</p></div>`).join('');
  const title = `${d.dow} — <em>${esc(d.title)}</em>${d.part ? ` · ${d.part}` : ''}`;
  return `<section class="page dayA" id="${d.key}" data-label="S${d.week} · ${d.dow}">
  ${head({ eyebrow: `Semaine ${d.week} · Jour ${n} sur 10${d.bloc ? ` · Bloc ${d.bloc}` : ''}`, title, sub: chips,
      meta: `${dateBox(d)}<div class="dayprog"><span>Progression <em data-count="${d.key}"></em></span><div class="bar"><i data-prog="${d.key}"></i></div></div>` })}
  <div class="body">
    <div class="col">
      <div class="card white grow"><div class="ctitle">${ico('book')}Au programme<span class="aside">je coche quand c’est vu</span></div><div class="prog">${progs}</div></div>
      <div class="card"><div class="ctitle">${ico('list')}Méthode du jour</div><div class="method">${meth}</div></div>
    </div>
    <div class="col">
      <div class="card grow"><div class="ctitle">${ico('pencil')}Exercices<span class="aside">corrigés en fin de planner</span></div><div class="exos">${exos}</div></div>
      <div class="card white"><div class="ctitle">${ico('quiz')}Quiz express<span class="aside">4 points par question</span></div>
        <div style="display:flex;gap:5mm;align-items:flex-end"><ol class="quiz" style="flex:1">${d.quiz.map(q => `<li><span>${q}</span></li>`).join('')}</ol>
        <div class="score" style="flex-direction:column;align-items:flex-end;gap:1mm"><span style="font-size:6.4pt;letter-spacing:.14em;text-transform:uppercase;color:var(--faint);font-weight:600">Ma note</span>${score(`${d.key}.quiz`)}</div></div>
      </div>
    </div>
  </div>${foot(`S${d.week} · ${d.dow} · programme`)}</section>`;
}

function resItem(id) {
  const r = R[id];
  if (!r) { console.warn('ressource inconnue', id); return ''; }
  return `<li><span class="ico">${ico(typeIcon(r.y))}</span><div>
    <div class="rt"><a href="${r.u}" target="_blank" rel="noopener">${esc(r.t)}</a></div>
    <div class="rs">${esc(r.s)}</div>
    <div class="tags"><span class="tag lvl-${r.n}">${LVL[r.n]}</span>${r.y.split(' + ').map(t => `<span class="tag type">${t}</span>`).join('')}<span class="tag lang">${r.src} · ${r.lang}</span></div>
    <div class="url">${esc(shortUrl(r.u))}</div></div></li>`;
}

function pageDayB(d) {
  const mastery = ['Découverte', 'Fragile', 'Solide', 'Maîtrisé'].map(m => ck('', m, { radio: `${d.key}.lvl`, value: m })).join('');
  return `<section class="page dayB" id="${d.key}-b" data-label="S${d.week} · ${d.dow} (suite)">
  ${head({ eyebrow: `Semaine ${d.week} · Jour ${workNum(d)} · suite`, title: `Ressources <em>&amp;</em> bilan`, sub: `${d.dow} — ${esc(d.title)}${d.part ? ` · ${d.part}` : ''}`, meta: dateBox(d) })}
  <div class="body">
    <div class="card white"><div class="ctitle">${ico('link')}Ressources du jour<span class="aside">titre cliquable · niveau · type · source · lien direct</span></div><ul class="res">${d.res.map(resItem).join('')}</ul></div>
    <div class="wrow">
      <div class="card white">${writeZone(`${d.key}.notes`, 'Mes notes', 'pencil')}</div>
      <div class="card white">${writeZone(`${d.key}.flou`, 'Ce que je n’ai pas compris', 'quiz')}</div>
      <div class="card white">${writeZone(`${d.key}.retra`, 'À retravailler', 'redo')}</div>
      <div class="card gold bilan">
        <div class="ctitle">${ico('check')}Bilan de la journée</div>
        <span class="k">Note au quiz</span>${score(`${d.key}.quiz`)}
        <span class="k">Niveau de maîtrise</span><div class="mastery">${mastery}</div>
        <span class="k">En une phrase</span><textarea class="mini" data-k="${d.key}.bilan" aria-label="Bilan de la journée"></textarea>
      </div>
    </div>
  </div>${foot(`S${d.week} · ${d.dow} · ressources et bilan`)}</section>`;
}

function examDay(n) { return DAYS.find(d => d.exam === n); }

function pageExamA(n) {
  const e = EXAMS[n], d = examDay(n);
  const total = e.missions.reduce((s, m) => s + m.p, 0) + e.oralPts;
  const missions = e.missions.map((m, i) => `<div class="mission"><span class="num">${i + 1}</span><div><h5>${esc(m.t)} ${chip(m.b, 'soft')}</h5><p>${m.d}</p></div><span class="pts">${m.p} pts</span></div>`).join('');
  return `<section class="page examA" id="bts${n}" data-label="${e.title} · sujet">
  ${head({ eyebrow: `Dimanche · semaine ${d.week} · mise en situation professionnelle`, title: `${e.title} — <em>${n === 1 ? 'blocs 1 à 4' : 'les 6 blocs'}</em>`, sub: 'Épreuve pratique et orale simulée : cas d’entreprise, manipulations, explication orale. Conditions réelles : chronomètre, maquette prête, pas de corrigé.', meta: `<div class="dayprog"><span>Avancement <em data-count="exam${n}"></em></span><div class="bar gold"><i data-prog="exam${n}"></i></div></div>` })}
  <div class="infos">
    <div class="info"><span>Date</span><b data-date="${d.key}">&nbsp;</b></div>
    <div class="info"><span>Durée</span><b>${e.duree}</b></div>
    <div class="info"><span>Blocs concernés</span><div class="chips">${e.blocs.map(b => chip(b)).join('')}</div></div>
    <div class="info"><span>Évaluation</span><b>Note sur 20 · barème sur ${total} points</b></div>
  </div>
  <div class="body">
    <div class="card white"><div class="ctitle">${ico('users')}Contexte</div><div class="ctxgrid">${e.ctx.map(c => `<p class="ctx">${c}</p>`).join('')}</div></div>
    <div class="card white"><div class="ctitle">${ico('list')}Cas pratique — missions<span class="aside">${e.missions.length} missions · + ${e.oralPts} pts d’oral</span></div><div class="missions">${missions}</div></div>
    <div class="card"><div class="ctitle">${ico('clock')}Déroulé — coche chaque phase terminée</div><div class="timeline">${e.timeline.map((t, i) => `<div style="--w:${t.w}"><b>${ck(`exam${n}.step${i}`, t.t, { cls: 'examitem' })}</b><span>${t.d}</span></div>`).join('')}</div></div>
  </div>${foot(`${e.title} · sujet`)}</section>
  <section class="page examQ" id="bts${n}-questions" data-label="${e.title} · questions et oral">
  ${head({ eyebrow: `${e.title} · suite du sujet`, title: `Questions techniques, <em>manipulations et oral</em>`, sub: 'Réponds à voix haute, comme devant la commission, puis note l’essentiel dans le brouillon.' })}
  <div class="body">
    <div class="col">
      <div class="card white"><div class="ctitle">${ico('quiz')}Questions techniques</div><ol class="qlist">${e.questions.map(q => `<li><span>${q}</span></li>`).join('')}</ol></div>
      ${e.manips ? `<div class="card sky"><div class="ctitle">${ico('flask')}Manipulations pratiques à réaliser devant le jury</div><div class="method">${e.manips.map((m, i) => ck(`exam${n}.manip${i}`, m, { cls: 'examitem' })).join('')}</div></div>` : ''}
      <div class="card gold"><div class="ctitle">${ico('mic')}Préparation orale</div><ol class="qlist">${e.oral.map(q => `<li><span>${q}</span></li>`).join('')}</ol></div>
    </div>
    <div class="card white">${writeZone(`exam${n}.brouillon`, 'Brouillon et notes de préparation', 'pencil')}</div>
  </div>${foot(`${e.title} · questions et oral`)}</section>`;
}

function pageExamB(n) {
  const e = EXAMS[n];
  const total = e.correction.reduce((s, c) => s + c.p, 0);
  const blocks = e.correction.map(c => `<div class="corr"><h5>${esc(c.t)}<span class="pts">/ ${c.p}</span></h5>${c.code ? `<pre>${esc(c.code)}</pre>` : ''}<ul>${c.items.map(i => `<li>${i}</li>`).join('')}</ul></div>`);
  const per = Math.ceil(blocks.length / 3);
  const cols = [0, 1, 2].map(i => `<div class="card white">${blocks.slice(i * per, i * per + per).join('')}${i === 2 ? `<div class="corr"><h5>Total<span class="pts">/ ${total}</span></h5><ul><li>Note ramenée sur 20. Bloc validé à partir de 15/20, à condition d’avoir su expliquer et manipuler.</li></ul></div>` : ''}</div>`).join('');
  return `<section class="page examB" id="bts${n}-corrige" data-label="${e.title} · corrigé">
  ${head({ eyebrow: `${e.title} · à lire après l’épreuve`, title: 'Correction détaillée <em>et barème</em>', sub: 'Compare point par point, puis reporte ta note et tes erreurs sur la page bilan.' })}
  <div class="body">${cols}</div>${foot(`${e.title} · correction`)}</section>`;
}

function pageExamC(n) {
  const e = EXAMS[n];
  const rows = COMPETENCES.map((g, gi) => `<tr class="grp"><td colspan="4">${esc(g.g)}</td></tr>${g.items.map((it, ii) => `<tr><td>${esc(it)}</td>${['Non acquis', 'En cours', 'Acquis'].map(v => `<td class="c">${ck('', '', { radio: `exam${n}.c${gi}_${ii}`, value: v })}</td>`).join('')}</tr>`).join('')}`).join('');
  return `<section class="page examC" id="bts${n}-bilan" data-label="${e.title} · bilan">
  ${head({ eyebrow: `${e.title} · bilan`, title: 'Mes résultats <em>et mon plan d’action</em>', meta: `${dateBox(examDay(n))}` })}
  <div class="body">
    <div class="col">
      <div class="card gold"><div class="bignote"><div class="n"><input type="text" inputmode="decimal" maxlength="4" data-k="exam${n}.note" aria-label="Note obtenue"><span>/ 20</span></div><p><b style="color:var(--navy)">Note obtenue.</b><br>Objectif : 15/20 minimum.<br>Reporte-la sur la page de suivi.</p></div></div>
      <div class="card white grow"><div class="ctitle">${ico('check')}Compétences évaluées</div>
        <table class="comp"><thead><tr><th>Compétence</th><th>Non acquis</th><th>En cours</th><th>Acquis</th></tr></thead><tbody>${rows}</tbody></table></div>
    </div>
    <div class="right">
      <div class="card white">${writeZone(`exam${n}.forts`, 'Points forts', 'star')}</div>
      <div class="card white">${writeZone(`exam${n}.erreurs`, 'Erreurs commises', 'alert')}</div>
      <div class="card white">${writeZone(`exam${n}.retra`, 'Notions à retravailler', 'redo')}</div>
      <div class="card sky"><div class="ctitle">${ico('target')}Blocs à reprendre en priorité</div><div class="method" style="grid-template-columns:1fr 1fr 1fr">${e.blocs.map(b => ck(`exam${n}.rev${b}`, `${b} · ${bloc(b).name}`)).join('')}</div></div>
    </div>
  </div>${foot(`${e.title} · bilan`)}</section>`;
}

function pageTrack() {
  const rows = BLOCS.map(b => `<div class="trow">
    <div><div class="bname"><span class="n" style="--c:${bcolor(b.id)}">${ico(b.icon)}</span><div><b>${b.id} · ${esc(b.name)}</b><small>${b.days}</small></div></div></div>
    <div><div class="chaps">${b.chapters.map(esc).join(' · ')}</div><div class="bar"><i data-prog="b${b.id}"></i></div><div class="pcount"><span>Progression des tâches</span><em data-count="b${b.id}"></em></div></div>
    <div class="status">${['Non commencé', 'En cours', 'Maîtrisé'].map(v => ck('', v, { radio: `b${b.id}.status`, value: v })).join('')}</div>
    <div class="lastnote">${score(`b${b.id}.note`)}</div>
    <div class="valid">${ck(`b${b.id}.v1`, 'Note ≥ 15/20')}${ck(`b${b.id}.v2`, 'Je sais expliquer')}${ck(`b${b.id}.v3`, 'Je sais manipuler')}</div>
    <div><textarea data-k="b${b.id}.com" aria-label="Commentaires bloc ${b.id}"></textarea></div>
  </div>`).join('');
  return `<section class="page track" id="suivi" data-label="Suivi de progression">
  ${head({ eyebrow: 'Suivi de progression', title: 'Où j’en suis, <em>bloc par bloc</em>', sub: 'La barre avance toute seule quand tu coches tes tâches. Le reste, c’est toi qui le décides — honnêtement.' })}
  <div class="body">
    <div class="ttable">
      <div class="trow th"><div>Bloc</div><div>Chapitres et progression</div><div>Statut</div><div>Dernier test</div><div>Validation du bloc</div><div>Commentaires</div></div>
      ${rows}
    </div>
    <div class="tsum">
      <div class="card sky"><div class="ctitle">${ico('chart')}Progression globale</div><div class="big"><span data-pct="all">0</span><small>%</small></div><div class="bar"><i data-prog="all"></i></div></div>
      <div class="card white"><div class="ctitle">${ico('exam')}BTS blanc n°1</div><div class="big">${score('exam1.note')}</div></div>
      <div class="card white"><div class="ctitle">${ico('exam')}BTS blanc n°2</div><div class="big">${score('exam2.note')}</div></div>
      <div class="card gold"><div class="ctitle">${ico('target')}Règle de validation</div><p class="rule-goal">Un bloc est <b>maîtrisé</b> quand les trois cases sont cochées : au moins <b>15/20</b>, je sais <b>expliquer</b> les notions, je sais <b>réaliser</b> les manipulations.</p></div>
    </div>
  </div>${foot('Suivi de progression')}</section>`;
}

/* pages « à flux » : remplies dynamiquement puis découpées en feuilles */
function flowShell(kind, id, n, headerHtml, label, cols) {
  return `<section class="page ${kind}" ${n === 0 ? `id="${id}"` : ''} data-label="${label}">${headerHtml}<div class="body">${Array.from({ length: cols }, () => '<div class="colstack"></div>').join('')}</div>${foot(label)}</section>`;
}

function catalogItems() {
  const items = [];
  BLOCS.forEach(b => {
    const list = Object.entries(R).filter(([, r]) => r.b === b.id);
    items.push({ kind: 'h', html: `<div class="rgroup"><h3><span class="n" style="--c:${bcolor(b.id)}">${ico(b.icon)}</span>Bloc ${b.id} · ${esc(b.name)} <span style="margin-left:auto;font-weight:500;letter-spacing:.04em;text-transform:none;color:var(--faint)">${list.length} ressources</span></h3></div>`, b });
    list.forEach(([, r]) => items.push({ kind: 'r', b, html: `<table class="rtab"><tr>
      <td class="t"><a href="${r.u}" target="_blank" rel="noopener">${esc(r.t)}</a><span class="url">${esc(shortUrl(r.u))}</span></td>
      <td class="s">${esc(r.s)}<br><span style="color:var(--faint)">${esc(r.src)} · ${r.lang}</span></td>
      <td class="m"><span class="tag lvl-${r.n}">${LVL[r.n]}</span><br>${r.y.split(' + ').map(t => `<span class="tag type">${t}</span>`).join('')}</td></tr></table>` }));
  });
  items.push({ kind: 'x', html: `<div class="card gold" style="margin-top:2mm"><div class="ctitle">${ico('alert')}Sujets sans ressource fiable trouvée</div>${GAPS.map(g => `<p class="note-warn" style="margin-bottom:1.4mm">${g}</p>`).join('')}</div>` });
  return items;
}

function answerItems() {
  return workDays.map(d => ({ kind: 'a', html: `<div class="ans"><h4>${d.bloc ? chip(d.bloc) : `<span class="chip soft"><i>${ico(d.icon)}</i>${esc(d.title)}</span>`}<span>S${d.week} · ${d.dow}</span></h4>
    <ol>${d.answers.map(a => `<li><span>${a}</span></li>`).join('')}</ol>
    <div class="ex"><p><b>Facile —</b> ${d.exoAns.f}</p><p><b>Intermédiaire —</b> ${d.exoAns.i}</p><p><b>Difficile —</b> ${d.exoAns.d}</p></div></div>` }));
}

function flow(container, { kind, id, label, header, cols, items, contHeader }) {
  // remplit colonne après colonne ; ouvre une nouvelle feuille quand tout déborde
  const pages = [];
  const newPage = () => {
    const tmp = document.createElement('div');
    tmp.innerHTML = flowShell(kind, id, pages.length, pages.length ? contHeader : header, label, cols);
    const pg = tmp.firstElementChild;
    container.appendChild(pg);
    pages.push(pg);
    return [...pg.querySelectorAll('.colstack')];
  };
  let colsEl = newPage(), ci = 0;
  const overflow = el => el.scrollHeight > el.clientHeight + 1;
  for (let k = 0; k < items.length; k++) {
    const it = items[k];
    const node = document.createElement('div');
    node.innerHTML = it.html;
    const el = node.firstElementChild;
    colsEl[ci].appendChild(el);
    // un titre de groupe ne reste jamais seul en bas de colonne
    let probe = null;
    if (it.kind === 'h' && items[k + 1]) { const n2 = document.createElement('div'); n2.innerHTML = items[k + 1].html; probe = n2.firstElementChild; colsEl[ci].appendChild(probe); }
    const tooBig = overflow(colsEl[ci]);
    if (probe) probe.remove();
    if (tooBig && colsEl[ci].children.length > 1) {
      el.remove();
      ci++;
      if (ci >= colsEl.length) { colsEl = newPage(); ci = 0; }
      if (it.kind === 'r') { // rappel du bloc en haut de la nouvelle colonne
        const h = items.find(x => x.kind === 'h' && x.b === it.b);
        const hn = document.createElement('div'); hn.innerHTML = h.html.replace('</h3>', ' </h3>').replace(/(Bloc \d+ · [^<]+)/, '$1 (suite)');
        colsEl[ci].appendChild(hn.firstElementChild);
      }
      colsEl[ci].appendChild(el);
    }
  }
  return pages;
}

/* ───────── assemblage ───────── */
const root = document.getElementById('sheets');
let html = pageCover() + pageOverview();
DAYS.forEach(d => {
  if (d.kind === 'work') html += pageDayA(d) + pageDayB(d);
  if (d.kind === 'exam') html += pageExamA(d.exam) + pageExamB(d.exam) + pageExamC(d.exam);
});
html += pageTrack();
root.innerHTML = html;

/* ───────── liaison des champs ───────── */
const fields = () => root.querySelectorAll('[data-k]');
function hydrate() {
  fields().forEach(el => {
    const k = el.dataset.k;
    if (el.type === 'checkbox') el.checked = !!S[k];
    else if (el.type === 'radio') el.checked = S[k] === el.value;
    else el.value = S[k] || '';
  });
  refreshDates();
  refreshProgress();
}
root.addEventListener('input', e => {
  const el = e.target, k = el.dataset && el.dataset.k;
  if (!k) return;
  if (el.type === 'checkbox') S[k] = el.checked;
  else if (el.type === 'radio') { if (el.checked) S[k] = el.value; }
  else S[k] = el.value;
  if (!S[k]) delete S[k];
  // synchronise les doublons (même note affichée à deux endroits)
  root.querySelectorAll(`[data-k="${CSS.escape(k)}"]`).forEach(o => {
    if (o === el) return;
    if (o.type === 'checkbox') o.checked = !!S[k];
    else if (o.type === 'radio') o.checked = S[k] === o.value;
    else o.value = S[k] || '';
  });
  save();
  refreshProgress();
});

function refreshDates() {
  document.querySelectorAll('[data-date]').forEach(el => {
    const d = DAYS.find(x => x.key === el.dataset.date);
    const s = dateFor(d);
    el.textContent = s ? s.charAt(0).toUpperCase() + s.slice(1) : ' ';
  });
  document.querySelectorAll('[data-start]').forEach(el => {
    el.textContent = S.start ? new Date(S.start + 'T12:00:00').toLocaleDateString('fr-FR', { day: 'numeric', month: 'long', year: 'numeric' }) : ' ';
  });
}

function setProg(key, done, total) {
  const pct = total ? Math.round(done / total * 100) : 0;
  document.querySelectorAll(`[data-prog="${key}"]`).forEach(i => { i.style.width = pct + '%'; });
  document.querySelectorAll(`[data-count="${key}"]`).forEach(i => { i.textContent = `${done}/${total}`; });
  document.querySelectorAll(`[data-pct="${key}"]`).forEach(i => { i.textContent = pct; });
  return pct;
}
function refreshProgress() {
  const boxes = [...root.querySelectorAll('input[type=checkbox][data-k]')];
  const uniq = new Map();
  boxes.forEach(b => uniq.set(b.dataset.k, b));
  const all = [...uniq.values()];
  DAYS.forEach(d => {
    if (d.kind === 'work') { const mine = all.filter(b => b.dataset.k.startsWith(d.key + '.')); setProg(d.key, mine.filter(b => b.checked).length, mine.length); }
    if (d.kind === 'exam') {
      const mine = all.filter(b => b.dataset.k.startsWith(`exam${d.exam}.`) && /\.(step|manip)\d/.test(b.dataset.k));
      setProg(`exam${d.exam}`, mine.filter(b => b.checked).length, mine.length);
    }
  });
  BLOCS.forEach(b => {
    const mine = all.filter(x => (x.dataset.b || '').split(' ').includes(String(b.id)));
    setProg(`b${b.id}`, mine.filter(x => x.checked).length, mine.length);
  });
  const dayBoxes = all.filter(b => /^s\dd\d\./.test(b.dataset.k));
  const pct = setProg('all', dayBoxes.filter(b => b.checked).length, dayBoxes.length);
  const g = document.getElementById('gpct'); if (g) g.textContent = pct + ' %';
  const gb = document.getElementById('gbar'); if (gb) gb.style.width = pct + '%';
}

/* ───────── pages à flux, numérotation, finitions ───────── */
async function layout() {
  try { await document.fonts.ready; } catch {}
  document.documentElement.classList.add('measuring');
  flow(root, {
    kind: 'catalog', id: 'ressources', label: 'Ressources', cols: 2, items: catalogItems(),
    header: head({ eyebrow: 'Ressources de révision', title: 'Toutes les ressources, <em>bloc par bloc</em>', sub: 'Chaque lien a été ouvert et contrôlé le 26/11/2026 (page existante, contenu conforme). Clique sur le titre pour ouvrir la ressource.' }),
    contHeader: head({ eyebrow: 'Ressources de révision · suite', title: 'Ressources <em>(suite)</em>' }),
  });
  flow(root, {
    kind: 'answers', id: 'corriges', label: 'Corrigés', cols: 3, items: answerItems(),
    header: head({ eyebrow: 'Corrigés', title: 'Quiz express <em>et exercices</em>', sub: 'À ouvrir seulement après avoir cherché. Les numéros correspondent aux questions du quiz de chaque jour.' }),
    contHeader: head({ eyebrow: 'Corrigés · suite', title: 'Quiz express <em>et exercices (suite)</em>' }),
  });
  document.documentElement.classList.remove('measuring');
  const pages = [...root.querySelectorAll('.page')];
  pages.forEach((p, i) => { const pn = p.querySelector('.pn'); if (pn) pn.textContent = `p. ${i + 1} / ${pages.length}`; });
  hydrate();
  buildNav();
  document.documentElement.dataset.ready = '1';
}

function buildNav() {
  const nav = document.getElementById('nav');
  if (!nav) return;
  const links = [['planning', 'Planning'], ['s1d1', 'Semaine 1'], ['bts1', 'BTS blanc 1'], ['s2d1', 'Semaine 2'], ['bts2', 'BTS blanc 2'], ['suivi', 'Suivi'], ['ressources', 'Ressources'], ['corriges', 'Corrigés']];
  nav.innerHTML = links.map(([id, t]) => `<a href="#${id}">${t}</a>`).join('');
  const io = new IntersectionObserver(es => es.forEach(e => {
    if (!e.isIntersecting) return;
    const id = e.target.id;
    nav.querySelectorAll('a').forEach(a => a.classList.toggle('on', a.getAttribute('href') === '#' + id));
  }), { rootMargin: '-40% 0px -55% 0px' });
  links.forEach(([id]) => { const el = document.getElementById(id); if (el) io.observe(el); });
}

/* ───────── barre d'outils ───────── */
const startInput = document.getElementById('start');
if (startInput) {
  startInput.value = S.start || '';
  startInput.addEventListener('change', () => {
    S.start = startInput.value || undefined;
    if (!S.start) delete S.start;
    save(); refreshDates();
  });
}
document.getElementById('btn-print')?.addEventListener('click', () => window.print());
document.getElementById('btn-export')?.addEventListener('click', () => {
  const blob = new Blob([JSON.stringify(S, null, 2)], { type: 'application/json' });
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = `planner-e6-sauvegarde-${new Date().toISOString().slice(0, 10)}.json`;
  document.body.appendChild(a); a.click(); a.remove();
  setTimeout(() => URL.revokeObjectURL(a.href), 2000);
});
document.getElementById('file-import')?.addEventListener('change', async e => {
  const f = e.target.files[0]; if (!f) return;
  try {
    const data = JSON.parse(await f.text());
    if (typeof data !== 'object' || Array.isArray(data)) throw new Error('format');
    S = data; save(); if (startInput) startInput.value = S.start || ''; hydrate();
    flash(e.target.closest('label'), 'Importé ✓');
  } catch { flash(e.target.closest('label'), 'Fichier invalide'); }
  e.target.value = '';
});
// confirmation en deux clics (pas de boîte de dialogue : elle est bloquée dans certains lecteurs)
let resetArmed = null;
document.getElementById('btn-reset')?.addEventListener('click', ev => {
  const btn = ev.currentTarget;
  if (!resetArmed) {
    btn.textContent = 'Cliquer encore pour tout effacer';
    btn.classList.add('danger');
    resetArmed = setTimeout(() => { resetArmed = null; btn.textContent = 'Réinitialiser'; btn.classList.remove('danger'); }, 4000);
    return;
  }
  clearTimeout(resetArmed); resetArmed = null;
  S = {}; save(); if (startInput) startInput.value = ''; hydrate();
  btn.classList.remove('danger'); flash(btn, 'Effacé', 'Réinitialiser');
});
function flash(el, msg, back) {
  if (!el) return;
  const txt = back || el.firstChild.textContent;
  el.firstChild.textContent = msg;
  setTimeout(() => { el.firstChild.textContent = txt; }, 2200);
}

if (PRINT_MODE) document.documentElement.classList.add('vierge');
layout();
})();
