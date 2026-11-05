/**
 * bolo.js — Hoja del bolo PÚBLICA de solo lectura (T-V6-86): horarios, dirección, backline,
 * setlist y checklist, para técnicos/sala sin cuenta. Imprimible. Sin caché ni contactos.
 */
(function () {
    const card = document.getElementById('pub-card');
    const esc = (s) => String(s == null ? '' : s).replace(/[&<>"']/g, (c) =>
        ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
    const day = (iso) => { const d = new Date(iso); return isNaN(d) ? '' : d.toLocaleDateString('es-ES', { weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' }); };
    const hour = (iso) => { const d = new Date(iso); return isNaN(d) ? '' : d.toLocaleTimeString('es-ES', { hour: '2-digit', minute: '2-digit' }); };
    const nl = (s) => esc(s).replace(/\n/g, '<br>');

    function notFound() {
        card.innerHTML = `<h1 class="pub-title">Hoja no disponible</h1>
            <p class="bf-muted">El enlace no existe o la banda lo ha desactivado.</p>`;
    }

    function render(s) {
        const times = [['Carga / llegada', s.load_in_at], ['Prueba de sonido', s.soundcheck_at],
                       ['Puertas', s.doors_at], ['Concierto', s.set_at || s.starts_at]].filter(t => t[1]);
        card.innerHTML = `
            <span class="pub-type">Hoja del bolo</span>
            <h1 class="pub-title">${esc(s.title)}</h1>
            <p class="pub-band">${esc(s.band_name)}${s.starts_at ? ' · ' + esc(day(s.starts_at)) : ''}</p>
            ${times.length ? `<table class="sheet-times"><tbody>${times.map(t => `<tr><th scope="row">${t[0]}</th><td>${esc(hour(t[1]))}</td></tr>`).join('')}</tbody></table>` : ''}
            ${s.venue_name || s.address ? `<h2 class="sheet-h">Dónde</h2><p>${esc(s.venue_name || '')}${s.venue_name && s.address ? '<br>' : ''}${esc(s.address || '')}
                ${s.address ? `<br><a href="https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(s.address)}" target="_blank" rel="noopener">Abrir en el mapa</a>` : ''}</p>` : ''}
            ${s.parking_notes ? `<h2 class="sheet-h">Aparcamiento / acceso</h2><p>${nl(s.parking_notes)}</p>` : ''}
            ${s.backline_notes ? `<h2 class="sheet-h">Backline / técnica</h2><p>${nl(s.backline_notes)}</p>` : ''}
            ${s.setlist.length ? `<h2 class="sheet-h">Setlist</h2><ol class="sheet-setlist">${s.setlist.map(t => `<li>${esc(t)}</li>`).join('')}</ol>` : ''}
            ${s.checklist.length ? `<h2 class="sheet-h">Checklist</h2><ul class="sheet-check">${s.checklist.map(i => `<li class="${i.done_at ? 'is-done' : ''}">${i.done_at ? '☑' : '☐'} ${esc(i.text)}</li>`).join('')}</ul>` : ''}
            <div class="sheet-actions no-print"><button class="bf-btn" id="sheet-print">Imprimir</button></div>`;
        document.title = `${s.title} — Hoja del bolo`;
        document.getElementById('sheet-print').addEventListener('click', () => window.print());
    }

    const t = new URLSearchParams(location.search).get('t');
    if (!t) { notFound(); return; }
    fetch('/public/gig-sheets/' + encodeURIComponent(t))
        .then((r) => { if (!r.ok) throw new Error('na'); return r.json(); })
        .then(render)
        .catch(notFound);
})();
