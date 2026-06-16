/**
 * band.js — Espacio de banda (contexto BANDA) en el shell BandFlow (T-075).
 *
 * Monta banner + pestañas dentro de `band.html`. NO reescribe la lógica de cada sección:
 * REUSA las funciones globales de `bands.js` (cargado antes): loadRepertoire, loadBandSetlists,
 * loadAgenda, loadFinance, initChat, copyFromPersonal, newEvent, newTransaction, newSettlement,
 * newBandSetlist (desacoplado vía opts), generateInvite, ROLE_LABEL. Por eso los paneles usan los
 * MISMOS ids del DOM que esas funciones esperan (#b-repertoire, #b-setlists, #b-agenda, #b-finance,
 * #b-chat, #chat-input/#chat-send).
 */
(function () {
    const elSpace = document.getElementById('band-space');
    if (!elSpace) return;

    const bandId = new URLSearchParams(location.search).get('id');

    // Color de banda derivado del id (el backend no expone color hoy — ver BANDFLOW_SPEC §gap #1).
    function hueFromId(s) {
        let h = 0;
        for (let i = 0; i < String(s).length; i++) h = (h * 31 + s.charCodeAt(i)) % 360;
        return h;
    }
    function initialsFrom(name) {
        const parts = String(name || '').trim().split(/\s+/).filter(Boolean);
        return parts.length ? parts.slice(0, 2).map(w => w[0]).join('').toUpperCase() : '🎸';
    }

    const TABS = [
        { key: 'resumen',    label: 'Resumen' },
        { key: 'miembros',   label: 'Miembros' },
        { key: 'repertorio', label: 'Repertorio' },
        { key: 'setlists',   label: 'Setlists' },
        { key: 'agenda',     label: 'Agenda' },
        { key: 'finanzas',   label: 'Finanzas' },
        { key: 'chat',       label: 'Chat' },
        { key: 'ajustes',    label: 'Ajustes' },
    ];

    function errorView(msg) {
        elSpace.innerHTML = `
            <a class="bf-btn bf-btn--sm bf-btn--ghost" href="bands.html">← Mis bandas</a>
            <div class="bf-card" style="margin-top:1rem;">
                <h2 class="bf-h3">No se pudo abrir la banda</h2>
                <p class="bf-muted" style="margin-top:.5rem;">${escapeHtml(msg)}</p>
            </div>`;
    }

    async function init() {
        if (!bandId) { errorView('Falta el identificador de la banda.'); return; }
        if (!(await requireAuth())) return;

        let band, members;
        try {
            const [rb, rm] = await Promise.all([
                apiFetch(`/bands/${bandId}`), apiFetch(`/bands/${bandId}/members`)]);
            if (rb.status === 403 || rb.status === 404) {
                errorView('No tienes acceso a esta banda o no existe.'); return;
            }
            if (!rb.ok || !rm.ok) throw new Error('http');
            band = await rb.json();
            members = await rm.json();
        } catch (e) { errorView('Inténtalo de nuevo en un momento.'); return; }

        const active = members.filter(m => m.status === 'active');
        const ctx = {
            iAmAdmin: active.some(m => m.role === 'admin' && m.is_me),
            iAmGuest: active.some(m => m.is_me && m.role === 'guest'),
            myRole: (active.find(m => m.is_me) || {}).role || 'member',
            accent: `hsl(${hueFromId(bandId)} 55% 48%)`,
        };

        renderShell(band, active, ctx);
        renderMembers(active);
        wire(band, active, ctx);
    }

    function renderShell(band, active, ctx) {
        const ini = initialsFrom(band.name);
        const roleLabel = ROLE_LABEL[ctx.myRole] || ctx.myRole;
        const desc = (band.description || '').trim();
        elSpace.innerHTML = `
            <a class="bf-btn bf-btn--sm bf-btn--ghost" href="bands.html" style="margin-bottom:.75rem;">← Mis bandas</a>
            <div class="bf-band-banner">
                <span class="bf-avatar bf-avatar--lg" style="background:${ctx.accent};color:#fff;">${escapeHtml(ini)}</span>
                <div class="bf-grow" style="min-width:0;">
                    <div class="bf-band-banner__name">${escapeHtml(band.name)}</div>
                    <div class="bf-band-banner__meta">
                        <span class="bf-badge bf-badge--${ctx.myRole}">${escapeHtml(roleLabel)}</span>
                        · ${active.length} ${active.length === 1 ? 'miembro' : 'miembros'}
                    </div>
                </div>
                ${ctx.iAmAdmin ? `<button class="bf-btn bf-btn--sm bf-btn--primary" id="bs-invite">🔗 Invitar</button>` : ''}
            </div>

            <div class="bf-tabs" role="tablist" style="margin:1rem 0;">
                ${TABS.map((t, i) => `<button class="bf-tab" role="tab" data-tab="${t.key}"
                    aria-selected="${i === 0 ? 'true' : 'false'}">${escapeHtml(t.label)}</button>`).join('')}
            </div>

            <div id="bs-panels">
                <div class="bs-panel" data-panel="resumen">
                    <div class="bf-card bf-stack">
                        <div>
                            <h3 class="bf-h3">Sobre la banda</h3>
                            <p class="bf-muted" style="margin-top:.4rem;">${desc ? escapeHtml(desc) : 'Sin descripción todavía.'}</p>
                        </div>
                        <div class="bf-row bf-wrap">
                            <span class="bf-badge">${active.length} ${active.length === 1 ? 'miembro' : 'miembros'}</span>
                            <span class="bf-badge bf-badge--${ctx.myRole}">Tú: ${escapeHtml(roleLabel)}</span>
                        </div>
                    </div>
                </div>

                <div class="bs-panel" data-panel="miembros" hidden>
                    <ul class="setlist-list" id="b-members"></ul>
                </div>

                <div class="bs-panel" data-panel="repertorio" hidden>
                    <div class="bf-row bf-row--between" style="margin-bottom:.6rem;">
                        <h3 class="bf-h3">Repertorio</h3>
                        ${ctx.iAmGuest ? '' : `<button class="bf-btn bf-btn--sm bf-btn--primary" id="b-add-song">➕ Copiar de mis partituras</button>`}
                    </div>
                    <ul class="setlist-list" id="b-repertoire"><li><small>Cargando…</small></li></ul>
                </div>

                <div class="bs-panel" data-panel="setlists" hidden>
                    <div id="b-setlist-list-wrap">
                        <div class="bf-row bf-row--between" style="margin-bottom:.6rem;">
                            <h3 class="bf-h3">Setlists</h3>
                            ${ctx.iAmGuest ? '' : `<button class="bf-btn bf-btn--sm bf-btn--primary" id="b-new-setlist">➕ Nuevo setlist</button>`}
                        </div>
                        <ul class="setlist-list" id="b-setlists"><li><small>Cargando…</small></li></ul>
                    </div>
                    <div id="b-setlist-editor" hidden></div>
                </div>

                <div class="bs-panel" data-panel="agenda" hidden>
                    <div class="bf-row bf-row--between" style="margin-bottom:.6rem;">
                        <h3 class="bf-h3">Agenda</h3>
                        ${ctx.iAmAdmin ? `<button class="bf-btn bf-btn--sm bf-btn--primary" id="b-new-event">➕ Nuevo evento</button>` : ''}
                    </div>
                    <div id="b-agenda"><p class="loading-text">Cargando…</p></div>
                </div>

                <div class="bs-panel" data-panel="finanzas" hidden>
                    <div class="bf-row bf-row--between" style="margin-bottom:.6rem;">
                        <h3 class="bf-h3">Finanzas</h3>
                        ${ctx.iAmAdmin ? `<span class="bf-row">
                            <button class="bf-btn bf-btn--sm bf-btn--primary" id="b-new-tx">➕ Movimiento</button>
                            <button class="bf-btn bf-btn--sm" id="b-settle">💸 Liquidar</button>
                        </span>` : ''}
                    </div>
                    <div id="b-finance"><p class="loading-text">Cargando…</p></div>
                </div>

                <div class="bs-panel" data-panel="chat" hidden>
                    <div id="b-chat"></div>
                    <div style="display:flex; gap:.5rem; margin-top:.6rem;">
                        <input type="text" id="chat-input" class="search-box" placeholder="Escribe un mensaje…" maxlength="4000">
                        <button id="chat-send" class="primary-btn">Enviar</button>
                    </div>
                </div>

                <div class="bs-panel" data-panel="ajustes" hidden>
                    ${ctx.iAmAdmin ? `
                        <div class="bf-card bf-stack">
                            <h3 class="bf-h3">Ajustes de la banda</h3>
                            <div>
                                <label class="bf-label" for="set-name">Nombre</label>
                                <input class="bf-input" id="set-name" value="${escapeHtml(band.name)}" maxlength="255">
                            </div>
                            <div>
                                <label class="bf-label" for="set-desc">Descripción</label>
                                <textarea class="bf-textarea" id="set-desc" rows="3" placeholder="¿De qué va la banda?">${escapeHtml(desc)}</textarea>
                            </div>
                            <div class="bf-row"><button class="bf-btn bf-btn--primary" id="set-save">Guardar cambios</button></div>
                            <hr style="border:none;border-top:1px solid var(--bf-border);margin:.3rem 0;">
                            <div><button class="bf-btn bf-btn--danger" id="set-delete">🗑️ Borrar banda</button></div>
                        </div>`
                        : `<div class="bf-card"><p class="bf-muted">Solo un admin puede editar la banda.</p></div>`}
                </div>
            </div>`;
    }

    function renderMembers(active) {
        const el = document.getElementById('b-members');
        if (!el) return;
        el.innerHTML = active.map(m => `
            <li class="setlist-song">
                <span class="sl-title">${escapeHtml(m.display_name || m.user_id)}
                    <small>${ROLE_LABEL[m.role] || escapeHtml(m.role)}${m.instrument ? ' · ' + escapeHtml(m.instrument) : ''}</small></span>
            </li>`).join('') || '<li><small>Sin miembros activos.</small></li>';
    }

    // Carga perezosa: las pestañas con datos remotos se cargan la primera vez que se abren.
    // resumen/miembros/ajustes ya se pintan en renderShell.
    const loaded = new Set(['resumen', 'miembros', 'ajustes']);
    function loadTab(key, ctx) {
        if (loaded.has(key)) return;
        loaded.add(key);
        if (key === 'repertorio') loadRepertoire(bandId, !ctx.iAmGuest);
        else if (key === 'setlists') loadBandSetlists(bandId, !ctx.iAmGuest);
        else if (key === 'agenda') loadAgenda(bandId, ctx.iAmAdmin);
        else if (key === 'finanzas') loadFinance(bandId, ctx.iAmAdmin);
        else if (key === 'chat') initChat(bandId, ctx.iAmAdmin);
    }

    function wire(band, active, ctx) {
        const invite = document.getElementById('bs-invite');
        if (invite) invite.addEventListener('click', () => generateInvite(bandId));
        const addSong = document.getElementById('b-add-song');
        if (addSong) addSong.addEventListener('click', () => copyFromPersonal(bandId));
        const newEv = document.getElementById('b-new-event');
        if (newEv) newEv.addEventListener('click', () => newEvent(bandId));
        const newTx = document.getElementById('b-new-tx');
        if (newTx) newTx.addEventListener('click', () => newTransaction(bandId, active));
        const settle = document.getElementById('b-settle');
        if (settle) settle.addEventListener('click', () => newSettlement(bandId, active));

        // Crear setlist: reusa newBandSetlist (desacoplado) en un contenedor de la pestaña.
        const newSL = document.getElementById('b-new-setlist');
        if (newSL) newSL.addEventListener('click', () => {
            const listWrap = document.getElementById('b-setlist-list-wrap');
            const editor = document.getElementById('b-setlist-editor');
            listWrap.hidden = true; editor.hidden = false;
            newBandSetlist(bandId, {
                container: editor,
                onDone: () => {
                    editor.hidden = true; editor.innerHTML = '';
                    listWrap.hidden = false;
                    loadBandSetlists(bandId, !ctx.iAmGuest);
                },
            });
        });

        // Ajustes (admin): editar nombre/descripción y borrar banda.
        const setSave = document.getElementById('set-save');
        if (setSave) setSave.addEventListener('click', async () => {
            const name = document.getElementById('set-name').value.trim();
            if (!name) { toast('El nombre no puede estar vacío.', 'error'); return; }
            const description = document.getElementById('set-desc').value.trim();
            try {
                const res = await apiFetch(`/bands/${bandId}`, {
                    method: 'PATCH', headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ name, description: description || null }),
                });
                if (!res.ok) throw new Error('http');
                const updated = await res.json();
                const elName = elSpace.querySelector('.bf-band-banner__name');
                if (elName) elName.textContent = updated.name;
                toast('Cambios guardados.', 'success');
            } catch (e) { toast('No se pudieron guardar los cambios.', 'error'); }
        });
        const setDel = document.getElementById('set-delete');
        if (setDel) setDel.addEventListener('click', async () => {
            const ok = await confirmModal(`¿Borrar la banda "${band.name}"? Esta acción no se puede deshacer.`,
                { okText: 'Borrar banda' });
            if (!ok) return;
            try {
                const res = await apiFetch(`/bands/${bandId}`, { method: 'DELETE' });
                if (!res.ok && res.status !== 204) throw new Error('http');
                toast('Banda borrada.', 'success');
                window.location.href = 'bands.html';
            } catch (e) { toast('No se pudo borrar la banda.', 'error'); }
        });

        const tabs = Array.from(elSpace.querySelectorAll('.bf-tab'));
        const panels = Array.from(elSpace.querySelectorAll('.bs-panel'));
        tabs.forEach(tab => tab.addEventListener('click', () => {
            const key = tab.dataset.tab;
            tabs.forEach(t => t.setAttribute('aria-selected', t === tab ? 'true' : 'false'));
            panels.forEach(p => { p.hidden = p.dataset.panel !== key; });
            loadTab(key, ctx);
        }));
    }

    init();
})();
