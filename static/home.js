/**
 * home.js — Dashboard de Inicio en `app.html` (Fase 13, T-076).
 *
 * Agrega próximos eventos + últimos mensajes de TODAS mis bandas vía `GET /me/dashboard`
 * (cada item con su etiqueta de banda). Requiere auth.js (apiFetch/requireAuth) y util.js
 * (escapeHtml). El shell (shell.js) ya pinta el lateral.
 */
(function () {
    const el = document.getElementById('home');
    if (!el) return;

    const EV_ICON = { rehearsal: '🎼', concert: '🎤', other: '📌' };

    function fmtDate(iso) {
        if (!iso) return '';
        const d = new Date(iso);
        if (isNaN(d)) return '';
        return d.toLocaleString('es-ES',
            { weekday: 'short', day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' });
    }

    function eventItem(e) {
        return `<a class="bf-list-item" href="band.html?id=${encodeURIComponent(e.band_id)}"
                   style="text-decoration:none;color:inherit;">
            <span class="bf-badge">${escapeHtml(e.band_name)}</span>
            <span class="bf-grow">${EV_ICON[e.type] || '📌'} ${escapeHtml(e.title)}
                <span class="bf-faint">· ${escapeHtml(fmtDate(e.starts_at))}</span></span>
        </a>`;
    }

    function msgItem(m) {
        return `<a class="bf-list-item" href="band.html?id=${encodeURIComponent(m.band_id)}"
                   style="text-decoration:none;color:inherit;">
            <span class="bf-badge">${escapeHtml(m.band_name)}</span>
            <span class="bf-grow">${m.is_pinned ? '📌 ' : ''}<strong>${escapeHtml(m.author_name || 'Alguien')}</strong>: ${escapeHtml(m.body)}</span>
        </a>`;
    }

    async function load() {
        if (!(await requireAuth())) return;
        let data, name = '';
        try {
            const [rd, rp] = await Promise.all([apiFetch('/me/dashboard'), apiFetch('/profile/me')]);
            if (!rd.ok) throw new Error('http');
            data = await rd.json();
            if (rp.ok) { const me = await rp.json(); name = (me.display_name || '').trim(); }
        } catch (e) {
            el.innerHTML = '<p class="bf-muted">⚠️ No se pudo cargar tu inicio. Inténtalo de nuevo.</p>';
            return;
        }
        const events = data.upcoming_events || [];
        const msgs = data.recent_messages || [];
        el.innerHTML = `
            <div class="bf-stack">
                <div>
                    <h1 class="bf-h1">Hola${name ? ', ' + escapeHtml(name) : ''} 👋</h1>
                    <p class="bf-muted">Lo último de tus bandas.</p>
                </div>
                <div class="bf-card">
                    <h2 class="bf-h3" style="margin-bottom:.75rem;">📅 Próximos eventos</h2>
                    ${events.length
                        ? `<div class="bf-list" id="home-events">${events.map(eventItem).join('')}</div>`
                        : `<p class="bf-muted" id="home-events">No tienes eventos próximos. <a href="bands.html">Crea uno en tu banda</a>.</p>`}
                </div>
                <div class="bf-card">
                    <h2 class="bf-h3" style="margin-bottom:.75rem;">💬 Últimos mensajes</h2>
                    ${msgs.length
                        ? `<div class="bf-list" id="home-messages">${msgs.map(msgItem).join('')}</div>`
                        : `<p class="bf-muted" id="home-messages">Sin mensajes recientes.</p>`}
                </div>
            </div>`;
    }

    load();
})();
