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
        // T-V5-05: avatar coloreado por banda (como el lateral), no un gris plano.
        return `<a class="bf-list-item" href="band.html?id=${encodeURIComponent(c.band_id)}"
                   style="text-decoration:none;color:inherit;">
            <span class="bf-avatar" aria-hidden="true" style="background:${bandColor(c.band_id)};color:#fff;">${escapeHtml(initialsFrom(c.band_name) || 'B')}</span>
            <span class="bf-grow" style="min-width:0;">
                <span style="font-weight:var(--bf-fw-semibold);">${escapeHtml(c.band_name)}</span>
                <span class="bf-muted" style="display:block;font-size:var(--bf-fs-sm);overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">${preview}</span>
            </span>
            ${c.last_at ? `<span class="bf-faint" style="font-size:var(--bf-fs-xs);">${escapeHtml(fmtWhen(c.last_at))}</span>` : ''}
        </a>`;
    }

    async function load() {
        if (!(await requireAuth())) return;
        el.innerHTML = bfSkeletonList(4);   // skeleton mientras carga (T-135)
        let convs;
        try {
            const r = await apiFetch('/me/conversations');
            if (!r.ok) throw new Error('http');
            convs = await r.json();
        } catch (e) {
            el.innerHTML = '<p class="bf-muted">No se pudieron cargar tus conversaciones. Inténtalo de nuevo.</p>';
            return;
        }
        el.innerHTML = `
            <div class="bf-stack">
                <div class="bf-row bf-row--between bf-wrap">
                    <div><h1 class="bf-h1">Chat</h1>
                    <p class="bf-muted">Una conversación por banda.</p></div>
                    <a class="bf-btn bf-btn--sm" href="red.html#mensajes">${bfIco('globe', 14)} Mensajes de Explorar</a>
                </div>
                <div class="chat-two">
                    <div class="bf-card chat-two__list">
                        ${convs.length
                            ? `<div class="bf-list" id="chat-list">${convs.map(convRow).join('')}</div>`
                            : bfEmpty('chat', 'Sin conversaciones',
                                'No estás en ninguna banda. <a href="bands.html">Crea o únete a una</a> para chatear.',
                                { id: 'chat-list' })}
                    </div>
                    <section class="bf-card chat-two__pane" id="chat-pane" aria-live="polite">
                        <p class="bf-muted">Elige una banda para leer y escribir aquí mismo.</p>
                    </section>
                </div>
            </div>`;
        // T-V6-49: en pantallas anchas, la conversación se abre al lado (en móvil, en la banda).
        const wide = () => window.matchMedia('(min-width: 900px)').matches;
        el.querySelectorAll('#chat-list a[href^="band.html"]').forEach(a => a.addEventListener('click', (e) => {
            if (!wide()) return;
            e.preventDefault();
            el.querySelectorAll('#chat-list a').forEach(x => x.classList.toggle('is-active', x === a));
            const bid = new URL(a.href, location.href).searchParams.get('id');
            openPane(bid, (convs.find(c => c.band_id === bid) || {}).band_name || '');
        }));
        if (wide() && convs.length) {
            const first = el.querySelector('#chat-list a[href^="band.html"]');
            if (first) first.click();
        }
    }

    let paneTimer = null;
    async function openPane(bandId, name) {
        const pane = document.getElementById('chat-pane');
        clearInterval(paneTimer);
        pane.innerHTML = `<header class="chat-two__head"><strong>${escapeHtml(name)}</strong>
                <a class="bf-btn bf-btn--sm bf-btn--ghost" href="band.html?id=${encodeURIComponent(bandId)}#chat">Abrir en la banda</a></header>
            <ul class="chat-two__msgs" id="chat-pane-msgs"><li class="bf-muted">Cargando…</li></ul>
            <form class="bf-composer" id="chat-pane-form"><input class="bf-input" id="chat-pane-in" maxlength="4000" placeholder="Escribe un mensaje…" aria-label="Mensaje">
                <button class="bf-btn bf-btn--primary" type="submit">${bfIco('send', 15)} Enviar</button></form>`;
        const ul = pane.querySelector('#chat-pane-msgs');
        const paint = async () => {
            let msgs = [];
            try { const r = await apiFetch(`/bands/${encodeURIComponent(bandId)}/messages/`); if (r.ok) msgs = await r.json(); } catch (e) { return; }
            const atBottom = ul.scrollTop + ul.clientHeight >= ul.scrollHeight - 24;
            ul.innerHTML = msgs.filter(m => !m.event_id).map(m => `<li class="chat-two__msg${m.is_mine ? ' is-mine' : ''}">
                ${m.is_mine ? '' : `<span class="chat-two__who">${escapeHtml(m.author_name || 'Alguien')}</span>`}
                <span class="chat-two__body">${escapeHtml(m.body).replace(/\n/g, '<br>')}</span>
                <span class="chat-two__when">${escapeHtml(bfDate(m.created_at))}</span></li>`).join('') || '<li class="bf-muted">Sin mensajes todavía.</li>';
            if (atBottom || !ul.dataset.loaded) ul.scrollTop = ul.scrollHeight;
            ul.dataset.loaded = '1';
        };
        await paint();
        paneTimer = setInterval(() => { if (document.visibilityState === 'visible' && document.getElementById('chat-pane-msgs') === ul) paint(); else if (!document.body.contains(ul)) clearInterval(paneTimer); }, 6000);
        pane.querySelector('#chat-pane-form').addEventListener('submit', async (e) => {
            e.preventDefault();
            const inp = pane.querySelector('#chat-pane-in');
            const body = inp.value.trim();
            if (!body) return;
            inp.value = '';
            try {
                const r = await apiFetch(`/bands/${encodeURIComponent(bandId)}/messages/`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ body }) });
                if (!r.ok) throw new Error('http');
                ul.dataset.loaded = '';
                paint();
            } catch (err) { toast('No se pudo enviar.', 'error'); inp.value = body; }
        });
    }

    load();
})();
