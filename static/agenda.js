/**
 * agenda.js — Agenda agregada del contexto TÚ (Fase 13, T-078) en `agenda.html`.
 *
 * Lista TODOS los eventos (próximos y pasados) de mis bandas vía `GET /me/events`, con etiqueta
 * de banda y mi asistencia, filtrables por banda. Marcar asistencia / crear eventos se hace en el
 * espacio de banda (`band.html`); aquí cada evento enlaza a su banda. bf-* + util.js (escapeHtml).
 */
(function () {
    const el = document.getElementById('agenda');
    if (!el) return;

    const EV_ICON = { rehearsal: '🎼', concert: '🎤', other: '📌' };
    const ATT = { yes: '✅ Voy', maybe: '🤔 Quizás', no: '❌ No voy' };

    let allEvents = [];
    let currentBand = 'all';

    function fmtDate(iso) {
        if (!iso) return 'Sin fecha';
        const d = new Date(iso);
        if (isNaN(d)) return 'Sin fecha';
        return d.toLocaleString('es-ES',
            { weekday: 'short', day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' });
    }

    function eventRow(e) {
        return `<a class="bf-list-item" href="band.html?id=${encodeURIComponent(e.band_id)}"
                   style="text-decoration:none;color:inherit;">
            <span class="bf-badge">${escapeHtml(e.band_name)}</span>
            <span class="bf-grow">${EV_ICON[e.type] || '📌'} ${escapeHtml(e.title)}
                <span class="bf-faint">· ${escapeHtml(fmtDate(e.starts_at))}</span></span>
            ${e.my_status ? `<span class="bf-badge">${ATT[e.my_status] || ''}</span>` : ''}
        </a>`;
    }

    function render() {
        if (!allEvents.length) {
            el.innerHTML = `
                <div class="bf-stack">
                    <div><h1 class="bf-h1">Agenda</h1></div>
                    <div class="bf-card">${bfEmpty('calendar', 'Tu agenda está vacía',
                        'No tienes eventos en ninguna banda. <a href="bands.html">Entra en una banda</a> para crear ensayos o conciertos.')}</div>
                </div>`;
            return;
        }
        const base = currentBand === 'all'
            ? allEvents
            : allEvents.filter(e => e.band_id === currentBand);
        const now = Date.now();
        const dated = base.filter(e => e.starts_at && !isNaN(new Date(e.starts_at).getTime()));
        const undated = base.filter(e => !e.starts_at || isNaN(new Date(e.starts_at).getTime()));
        const upcoming = dated.filter(e => new Date(e.starts_at).getTime() >= now);
        const past = dated.filter(e => new Date(e.starts_at).getTime() < now)
            .sort((a, b) => new Date(b.starts_at) - new Date(a.starts_at));   // recientes primero

        // Chips de filtro: Todas + una por banda con eventos (orden de aparición).
        const bands = [...new Map(allEvents.map(e => [e.band_id, e.band_name])).entries()];
        const chip = (key, label) =>
            `<button class="bf-btn bf-btn--sm${key === currentBand ? ' bf-btn--primary' : ''}" data-band="${escapeHtml(key)}">${escapeHtml(label)}</button>`;
        const chips = chip('all', 'Todas') + bands.map(([id, name]) => chip(id, '🎸 ' + name)).join('');

        el.innerHTML = `
            <div class="bf-stack">
                <div>
                    <h1 class="bf-h1">Agenda</h1>
                    <p class="bf-muted">Ensayos y conciertos de todas tus bandas.</p>
                </div>
                <div class="bf-row bf-wrap" id="agenda-filters">${chips}</div>
                <div class="bf-card">
                    <h2 class="bf-h3" style="margin-bottom:.75rem;">Próximos</h2>
                    ${upcoming.length
                        ? `<div class="bf-list" id="agenda-upcoming">${upcoming.map(eventRow).join('')}</div>`
                        : `<p class="bf-muted" id="agenda-upcoming">No hay eventos próximos.</p>`}
                </div>
                ${past.length
                    ? `<div class="bf-card"><h2 class="bf-h3" style="margin-bottom:.75rem;">Pasados</h2>
                        <div class="bf-list" id="agenda-past">${past.map(eventRow).join('')}</div></div>`
                    : ''}
                ${undated.length
                    ? `<div class="bf-card"><h2 class="bf-h3" style="margin-bottom:.75rem;">Sin fecha</h2>
                        <div class="bf-list" id="agenda-undated">${undated.map(eventRow).join('')}</div></div>`
                    : ''}
            </div>`;

        el.querySelectorAll('#agenda-filters [data-band]').forEach(btn =>
            btn.addEventListener('click', () => { currentBand = btn.dataset.band; render(); }));
    }

    async function load() {
        if (!(await requireAuth())) return;
        try {
            const r = await apiFetch('/me/events');
            if (!r.ok) throw new Error('http');
            allEvents = await r.json();
        } catch (e) {
            el.innerHTML = '<p class="bf-muted">⚠️ No se pudo cargar la agenda. Inténtalo de nuevo.</p>';
            return;
        }
        render();
    }

    load();
})();
