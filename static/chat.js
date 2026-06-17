/**
 * chat.js — Chat agregado del contexto TÚ (Fase 13, T-080) en `chat.html`.
 *
 * Lista una conversación por banda (chat general) vía `GET /me/conversations`, con el último
 * mensaje; entrar abre el chat de esa banda en `band.html`. bf-* + util.js (escapeHtml).
 */
(function () {
    const el = document.getElementById('chat');
    if (!el) return;

    function fmtWhen(iso) {
        if (!iso) return '';
        const d = new Date(iso);
        if (isNaN(d)) return '';
        return d.toLocaleDateString('es-ES', { day: 'numeric', month: 'short' });
    }

    function convRow(c) {
        const preview = c.last_body
            ? `<strong>${escapeHtml(c.last_author || 'Alguien')}</strong>: ${escapeHtml(c.last_body)}`
            : '<span class="bf-faint">Sin mensajes aún — rompe el hielo</span>';
        return `<a class="bf-list-item" href="band.html?id=${encodeURIComponent(c.band_id)}"
                   style="text-decoration:none;color:inherit;">
            <span class="bf-avatar" aria-hidden="true">${escapeHtml((c.band_name[0] || '🎸').toUpperCase())}</span>
            <span class="bf-grow" style="min-width:0;">
                <span style="font-weight:var(--bf-fw-semibold);">${escapeHtml(c.band_name)}</span>
                <span class="bf-muted" style="display:block;font-size:var(--bf-fs-sm);overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">${preview}</span>
            </span>
            ${c.last_at ? `<span class="bf-faint" style="font-size:var(--bf-fs-xs);">${escapeHtml(fmtWhen(c.last_at))}</span>` : ''}
        </a>`;
    }

    async function load() {
        if (!(await requireAuth())) return;
        let convs;
        try {
            const r = await apiFetch('/me/conversations');
            if (!r.ok) throw new Error('http');
            convs = await r.json();
        } catch (e) {
            el.innerHTML = '<p class="bf-muted">⚠️ No se pudieron cargar tus conversaciones. Inténtalo de nuevo.</p>';
            return;
        }
        el.innerHTML = `
            <div class="bf-stack">
                <div>
                    <h1 class="bf-h1">Chat</h1>
                    <p class="bf-muted">Una conversación por banda.</p>
                </div>
                <div class="bf-card">
                    ${convs.length
                        ? `<div class="bf-list" id="chat-list">${convs.map(convRow).join('')}</div>`
                        : bfEmpty('chat', 'Sin conversaciones',
                            'No estás en ninguna banda. <a href="bands.html">Crea o únete a una</a> para chatear.',
                            { id: 'chat-list' })}
                </div>
            </div>`;
    }

    load();
})();
