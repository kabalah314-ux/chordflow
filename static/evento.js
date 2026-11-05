/**
 * evento.js — Página PÚBLICA de un evento compartido por enlace (V3-F7).
 * Autónoma: sin auth, sin shell, sin dependencias. Hace fetch a /public/events/{id} (plano público,
 * proyección segura) y pinta la info no sensible + el reclamo "Hecho con BandFlow" (gancho viral).
 */
(function () {
    const card = document.getElementById('pub-card');

    const esc = (s) => String(s == null ? '' : s).replace(/[&<>"']/g, (c) =>
        ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));

    const TYPE = { concert: 'Concierto', rehearsal: 'Ensayo', other: 'Evento' };

    // T-V5-05: CTA claro (gancho viral) — invita al visitante a usar la app.
    const CTA = `<div class="pub-cta">
            <p class="pub-cta__note">¿Tu banda también toca en directo?</p>
            <a class="pub-cta__btn" href="app.html">Organízalo con BandFlow — gratis</a>
        </div>`;

    function fmtDate(iso) {
        if (!iso) return '';
        const d = new Date(iso);
        if (isNaN(d.getTime())) return '';
        try {
            return d.toLocaleString('es-ES', {
                weekday: 'long', day: 'numeric', month: 'long', year: 'numeric',
                hour: '2-digit', minute: '2-digit',
            });
        } catch (e) { return d.toISOString().slice(0, 16).replace('T', ' '); }
    }

    function render(ev) {
        const place = [ev.venue_name, ev.city].filter(Boolean).join(' · ') || ev.location || '';
        card.innerHTML =
            `<span class="pub-type">${esc(TYPE[ev.type] || TYPE.other)}</span>
             <h1 class="pub-title">${esc(ev.title)}</h1>
             <p class="pub-band">${esc(ev.band_name)}</p>
             ${ev.starts_at ? `<p class="pub-date">${esc(fmtDate(ev.starts_at))}</p>` : ''}
             ${place ? `<p class="pub-place">${esc(place)}</p>` : ''}
             <div class="pub-actions">
                ${ev.starts_at ? `<a class="bf-btn" href="/public/events/${encodeURIComponent(ev.id)}/ics">Añadir a mi calendario</a>` : ''}
                <button class="bf-btn" id="pub-share" type="button">Compartir</button>
             </div>
             ${CTA}`;
        document.title = `${ev.title} — BandFlow`;
        // T-V6-52: compartir (Web Share → copiar)
        const sh = document.getElementById('pub-share');
        if (sh) sh.addEventListener('click', async () => {
            const data = { title: ev.title, text: `${ev.title} · ${ev.band_name}`, url: location.href };
            try { if (navigator.share) { await navigator.share(data); return; } } catch (e) { return; }
            try { await navigator.clipboard.writeText(location.href); sh.textContent = 'Enlace copiado'; }
            catch (e) { window.open('https://wa.me/?text=' + encodeURIComponent(data.text + ' ' + data.url), '_blank', 'noopener'); }
        });
    }

    function notFound() {
        card.innerHTML =
            `<h1 class="pub-title">Evento no disponible</h1>
             <p class="bf-muted">Este enlace no existe o el evento ya no se comparte.</p>
             ${CTA}`;
    }

    const id = new URLSearchParams(location.search).get('id');
    if (!id) { notFound(); return; }

    fetch('/public/events/' + encodeURIComponent(id))
        .then((r) => { if (!r.ok) throw new Error('not-available'); return r.json(); })
        .then(render)
        .catch(notFound);
})();
