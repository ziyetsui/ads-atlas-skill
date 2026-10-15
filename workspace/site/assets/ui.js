(function () {
// Atlas brief UI helpers: sticky top bar with section anchors, cover renderer, number formatting.

const SECTIONS = [
  { id: 'product', label: '我的产品' },
  { id: 'competitors', label: '锁定竞品' },
  { id: 'hits', label: '竞品爆款' },
  { id: 'teardown', label: '爆款拆解' },
  { id: 'playbook', label: '规律与落地' },
];

// One-page brief: anchors to <section id>, scroll-spy marks the section in view.
// `{ home: true }` renders the Atlas home bar: brand + theme toggle only, no section nav.
function topBar({ home = false } = {}) {
  const el = document.createElement('header');
  el.className = 'atlas-top';
  el.innerHTML = home
    ? `<a class="brand" href="./">Atlas</a><span class="crumb" style="color:var(--ink-2)">竞品爆款 Brief</span><span style="flex:1"></span>`
    : `
    <a class="brand" href="../" title="所有 Brief">Atlas</a>
    <span class="crumb" style="color:var(--ink-3)">/</span>
    <span class="crumb" style="color:var(--ink-2)">${window.ATLAS.product.name} · 竞品爆款 Brief</span>
    <nav class="steps" aria-label="Brief 章节">
      ${SECTIONS.map((s) => `<a href="#${s.id}" data-sec="${s.id}">${s.label}</a>`).join('')}
    </nav>`;
  document.body.prepend(el);

  // Light / dark toggle. No stored choice → follow the system; a click pins the opposite of what's showing.
  const root = document.documentElement;
  const sys = matchMedia('(prefers-color-scheme: dark)');
  const isDark = () => root.dataset.theme ? root.dataset.theme === 'dark' : sys.matches;
  const SUN = '<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" aria-hidden="true"><circle cx="8" cy="8" r="3"/><path d="M8 1.5v1.2M8 13.3v1.2M1.5 8h1.2M13.3 8h1.2M3.4 3.4l.85.85M11.75 11.75l.85.85M3.4 12.6l.85-.85M11.75 4.25l.85-.85"/></svg>';
  const MOON = '<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linejoin="round" aria-hidden="true"><path d="M13.5 9.6A5.5 5.5 0 0 1 6.4 2.5a5.5 5.5 0 1 0 7.1 7.1Z"/></svg>';
  const btn = document.createElement('button');
  btn.type = 'button';
  btn.className = 'theme-btn';
  const paint = () => {
    const d = isDark();
    btn.innerHTML = d ? SUN : MOON;
    btn.setAttribute('aria-label', d ? '切换到浅色模式' : '切换到深色模式');
    btn.title = d ? '浅色模式' : '深色模式';
  };
  btn.addEventListener('click', () => {
    const next = isDark() ? 'light' : 'dark';
    root.classList.add('theme-switching');
    root.dataset.theme = next;
    try { localStorage.setItem('atlas-theme', next); } catch {}
    paint();
    requestAnimationFrame(() => requestAnimationFrame(() => root.classList.remove('theme-switching')));
  });
  sys.addEventListener('change', paint);
  el.append(btn);
  paint();
  if (home) return;

  const nav = el.querySelector('.steps');
  const links = [...nav.querySelectorAll('a')];
  let cur = null;
  const set = (id) => {
    if (id === cur) return;
    cur = id;
    links.forEach((a) => (a.dataset.sec === id ? a.setAttribute('aria-current', 'true') : a.removeAttribute('aria-current')));
    const a = links.find((x) => x.dataset.sec === id);
    // keep the active link visible in the (horizontally scrollable) nav without moving the page
    if (a && nav.scrollWidth > nav.clientWidth) nav.scrollTo({ left: a.offsetLeft - nav.offsetLeft - 8 });
  };
  const secs = SECTIONS.map((s) => document.getElementById(s.id)).filter(Boolean);
  const io = new IntersectionObserver((es) => es.forEach((e) => e.isIntersecting && set(e.target.id)), { rootMargin: '-40% 0px -55% 0px' });
  secs.forEach((s) => io.observe(s));
  addEventListener('scroll', () => {
    if (innerHeight + scrollY >= document.documentElement.scrollHeight - 4) set(secs[secs.length - 1].id);
    else if (scrollY < 40) set(secs[0].id);
  }, { passive: true });
  set(secs[0].id);
}

// Simulated 3:4 note cover. `n` is a note from data.js.
const attr = (t) => String(t || '').replace(/&/g, '&amp;').replace(/"/g, '&quot;').replace(/</g, '&lt;');
const dur = (s) => `${Math.floor(s / 60)}:${String(Math.round(s % 60)).padStart(2, '0')}`;

// `play: false` when the cover sits inside a link — pair it with playLink(n) next to the other actions.
function fmt(v) {
  if (v >= 10000) return (v / 10000).toFixed(v >= 100000 ? 0 : 1).replace(/\.0$/, '') + '万';
  return v.toLocaleString('zh-CN');
}

// Structured "how we got here" strip above a quadrant chart: 池子 → 怎么筛 → 结果 → 共性.
// rows: [{ k: '池子', v: html }, ...]; the last row is the takeaway and gets the accent rail.
function summary(rows, label = '筛选逻辑') {
  return `<ol class="sum" aria-label="${label}">${rows.map((r, i) => `<li class="sum-step${i === rows.length - 1 ? ' sum-key' : ''}">
      <span class="sum-k"><span class="sum-n num">${i + 1}</span>${r.k}</span>
      <div class="sum-v">${r.v}</div></li>`).join('')}</ol>`;
}

// Is there anything to open in the page? video file, or the post's images.
const viewable = (n) => !!(n.video || (n.images && n.images.length));
const viewLabel = (n) => n.video ? dur(n.video.durationSec) : `${n.images.length} 图`;

function cover(n, { tag = true, play = true } = {}) {
  if (n.img) {
    const label = n.pct != null ? `榜内 ${Math.round(n.pct)}%` : '';
    const isV = !!n.video;
    const badge = viewable(n)
      ? (play
        ? `<button type="button" class="cover-playbtn" data-view="${n.id}" aria-label="${isV ? '播放视频' : '看图文'}（${viewLabel(n)}）：${attr(n.title)}"><span class="pb-dot${isV ? '' : ' pb-dot-img'}" aria-hidden="true">${isV ? '▶' : GALLERY_ICON}</span><span class="pb-dur num">${viewLabel(n)}</span></button>`
        : `<span class="cover-play cover-play-live" aria-label="${isV ? '可播放视频' : '可看图文'}">${isV ? '▶' : GALLERY_ICON}</span>`)
      : (n.type === '视频' ? '<span class="cover-play" aria-label="视频">▶</span>' : '');
    return `<div class="cover-wrap"><div class="cover cover-photo">
      <img src="${n.img}" alt="${attr(n.title)}" loading="lazy" decoding="async">
      ${badge}
      ${tag && label ? `<span class="cover-tag num">${label}</span>` : ''}
    </div></div>`;
  }
  const [c1, c2, fg] = window.ATLAS.palettes[n.pal % window.ATLAS.palettes.length];
  return `<div class="cover-wrap"><div class="cover" style="--c1:${c1};--c2:${c2};--cfg:${fg}">
    ${n.person ? '<span class="cover-figure" aria-hidden="true"></span>' : ''}
    <div class="cover-text">${n.cover}</div>
    ${n.type === '视频' ? '<span class="cover-play" aria-label="视频">▶</span>' : ''}
    ${tag ? `<span class="cover-tag num">♥ ${fmt(n.likes)}</span>` : ''}
  </div></div>`;
}
const GALLERY_ICON = '<svg viewBox="0 0 16 16" width="15" height="15" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true"><rect x="2" y="3" width="12" height="10" rx="2"/><path d="m2.5 11 3.5-3.5 3 3 2-2 2.5 2.5"/></svg>';

// Inline open link for rows where the cover itself sits inside another link.
function playLink(n) {
  if (!viewable(n)) return '';
  return `<button type="button" class="play-link" data-view="${n.id}">${n.video ? '▶ 播放' : '看图文'} <span class="num">${viewLabel(n)}</span></button>`;
}

const stats = (n) => [['赞', n.likes], ['藏', n.collects], ['评', n.comments]].filter(([, v]) => v != null).map(([k, v]) => `${k} <span class="num">${fmt(v)}</span>`).join(' · ');

let dlg = null, lastFocus = null;
function shell() {
  if (dlg) return dlg;
  dlg = document.createElement('dialog');
  dlg.className = 'atlas-player';
  dlg.addEventListener('click', (e) => { if (e.target === dlg || e.target.closest('.ap-close')) dlg.close(); });
  dlg.addEventListener('close', () => {
    if (dlg.open) return; // close fires async: another note may already be open in this dialog
    const v = dlg.querySelector('video');
    if (v) { v.pause(); v.removeAttribute('src'); v.load(); }
    lastFocus?.focus?.();
  });
  document.body.append(dlg);
  return dlg;
}

// One viewer for both: a video plays; an image post becomes a swipeable gallery. Body text sits under either.
function openViewer(n) {
  shell();
  lastFocus = document.activeElement;
  const isV = !!n.video;
  dlg.setAttribute('aria-label', `${isV ? '视频' : '图文'}：${n.title}`);
  const media = isV
    ? `<video src="${n.video.src}" poster="${n.video.poster || n.img}" controls playsinline autoplay preload="metadata"></video>`
    : `<div class="ag">
        <div class="ag-track" tabindex="0" aria-label="图片，左右滑动或用方向键翻页">${n.images.map((im, i) => `<figure class="ag-slide"><img src="${im.src}" alt="第 ${i + 1} 张，共 ${n.images.length} 张" ${i > 1 ? 'loading="lazy"' : ''} decoding="async" width="${im.w}" height="${im.h}"></figure>`).join('')}</div>
        ${n.images.length > 1 ? `<button type="button" class="ag-nav ag-prev" aria-label="上一张">‹</button><button type="button" class="ag-nav ag-next" aria-label="下一张">›</button><span class="ag-count num" aria-live="polite">1 / ${n.images.length}</span>` : ''}
      </div>`;
  dlg.innerHTML = `<div class="ap-box">
      ${media}
      <div class="ap-bar">
        <div class="ap-meta"><p class="ap-t">${attr(n.title)}</p><p class="ap-m">${attr(n.account)}${isV ? ` · <span class="num">${dur(n.video.durationSec)}</span>` : ''}${stats(n) ? ` · ${stats(n)}` : ''}</p></div>
        <a class="ap-ext" href="${n.url}" target="_blank" rel="noopener">看原文 ↗</a>
        <button type="button" class="ap-close" aria-label="关闭">✕</button>
      </div>
      ${n.body ? `<div class="ap-body">${attr(n.body).replace(/\n/g, '<br>')}</div>` : ''}
    </div>`;
  const box = dlg.querySelector('.ap-box');
  // Fit the dialog to the media's own aspect ratio so there are no side bars.
  const fit = (ar) => {
    const maxW = Math.min(innerWidth * 0.92, 980), maxH = innerHeight * (n.body ? 0.72 : 0.86) - 64;
    box.style.width = Math.max(Math.min(maxW, maxH * ar), Math.min(maxW, 340)) + 'px';
  };
  if (isV) {
    const v = dlg.querySelector('video');
    fit(n.aspect || 0.5625);
    v.addEventListener('loadedmetadata', () => v.videoWidth && fit(v.videoWidth / v.videoHeight), { once: true });
  } else {
    fit(n.images[0].w / n.images[0].h);
    const track = dlg.querySelector('.ag-track'), count = dlg.querySelector('.ag-count');
    const go = (d) => track.scrollBy({ left: d * track.clientWidth, behavior: matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth' });
    dlg.querySelector('.ag-prev')?.addEventListener('click', () => go(-1));
    dlg.querySelector('.ag-next')?.addEventListener('click', () => go(1));
    track.addEventListener('keydown', (e) => { if (e.key === 'ArrowRight') { e.preventDefault(); go(1); } if (e.key === 'ArrowLeft') { e.preventDefault(); go(-1); } });
    track.addEventListener('scroll', () => { if (count) count.textContent = `${Math.round(track.scrollLeft / track.clientWidth) + 1} / ${n.images.length}`; }, { passive: true });
  }
  dlg.showModal();
  (dlg.querySelector('.ag-track') || dlg.querySelector('.ap-close')).focus({ preventScroll: true });
}

// Capture phase so an open control wins over any card / section click handler around it.
document.addEventListener('click', (e) => {
  const b = e.target.closest('[data-view],[data-video]');
  if (!b) return;
  const n = window.ATLAS.notes[b.dataset.view || b.dataset.video];
  if (!n || !viewable(n)) return;
  e.preventDefault(); e.stopPropagation();
  openViewer(n);
}, true);

// Product names can be Latin (Ancher) inside Chinese copy: pad the CJK–Latin seam with a space.
// side: 'both' | 'left' | 'right' — use 'right' at the start of a label, 'left' at the end of a sentence.
function nm(name, side = 'both') {
  const latin = /[A-Za-z0-9]/;
  const l = side !== 'right' && latin.test(name[0]) ? ' ' : '';
  const r = side !== 'left' && latin.test(name[name.length - 1]) ? ' ' : '';
  return l + name + r;
}

window.AtlasUI = { topBar, cover, fmt, playLink, summary, nm };
})();
