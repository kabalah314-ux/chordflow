/**
 * setlist.js — Setlist PÚBLICO de solo lectura (T-V6-63): para el técnico de sonido, la sala o un
 * sustituto. Letra grande, imprimible para pegar en el suelo. Sin notas internas.
 */
(function () {
    const card = document.getElementById('pub-card');
    const esc = (s) => String(s == null ? '' : s).replace(/[&<>"']/g, (c) =>
        ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
    const dur = (s) => s ? `${Math.floor(s / 60)}:${String(s % 60).padStart(2, '0')}` : '';
    const total = (s) => { if (!s) return ''; const h = Math.floor(s / 3600), m = Math.round((s % 3600) / 60); return h ? `${h} h ${m} min` : `${m} min`; };

    function notFound() {
        card.innerHTML = `<h1 class="pub-title">Setlist no disponible</h1><p class="bf-muted">El enlace no existe o la banda lo ha desactivado.</p>`;
    }
    function render(sl) {
        document.title = `${sl.name} — Setlist`;
        card.innerHTML = `
            <span class="pub-type">Setlist${sl.band_name ? ' · ' + esc(sl.band_name) : ''}</span>
            <h1 class="pub-title">${esc(sl.name)}</h1>
            <p class="pub-band">${sl.items.length} canciones${sl.duration_sec ? ' · ' + total(sl.duration_sec) : ''}</p>
            <ol class="pub-setlist">${sl.items.map(i => `<li><span class="pub-setlist__title">${esc(i.title)}</span>
                <span class="pub-setlist__meta">${[i.key, i.bpm ? i.bpm + ' bpm' : '', dur(i.duration_sec)].filter(Boolean).map(esc).join(' · ')}</span></li>`).join('')}</ol>
            <div class="sheet-actions no-print"><button class="bf-btn" id="sl-print">Imprimir</button></div>`;
        document.getElementById('sl-print').addEventListener('click', () => window.print());
    }
    const t = new URLSearchParams(location.search).get('t');
    if (!t) { notFound(); return; }
    fetch('/public/setlists/' + encodeURIComponent(t))
        .then((r) => { if (!r.ok) throw new Error('na'); return r.json(); })
        .then(render).catch(notFound);
})();
