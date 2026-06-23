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
        { key: 'repertorio', label: 'Repertorios' },
        { key: 'setlists',   label: 'Setlists' },
        { key: 'agenda',     label: 'Agenda' },
        { key: 'finanzas',   label: 'Finanzas' },
        { key: 'chat',       label: 'Chat' },
        { key: 'giras',      label: 'Giras' },
        { key: 'ajustes',    label: 'Ajustes' },
    ];

    const TOUR_STATUS = {
        planning: 'En preparación', active: 'En gira', done: 'Terminada', cancelled: 'Cancelada',
    };
    function money(x) { return Number(x || 0).toFixed(2) + ' €'; }
    function fmtDay(iso) {
        if (!iso) return '';
        const d = new Date(iso);
        return isNaN(d) ? '' : d.toLocaleDateString('es-ES', { day: 'numeric', month: 'short' });
    }

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
                    <!-- Repertorios: colecciones temáticas de canciones (T-114) -->
                    <div id="b-collections-wrap">
                        <div class="bf-row bf-row--between" style="margin-bottom:.3rem;">
                            <h3 class="bf-h3">Repertorios</h3>
                            ${ctx.iAmGuest ? '' : `<button class="bf-btn bf-btn--sm bf-btn--primary" id="b-new-collection">➕ Nuevo repertorio</button>`}
                        </div>
                        <p class="bf-muted" style="margin:.1rem 0 .6rem;font-size:.82rem;">Agrupa tus canciones por tema (acústico, cañero, bodas…). Para el orden de un bolo, usa los <b>Setlists</b>.</p>
                        <ul class="setlist-list" id="b-collections"><li><small>Cargando…</small></li></ul>
                    </div>
                    <div id="b-collection-detail" hidden></div>
                    <!-- Pool: todas las canciones de la banda -->
                    <div class="bf-row bf-row--between" style="margin:1.4rem 0 .6rem;">
                        <h3 class="bf-h3">Todas las canciones</h3>
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
                    <!-- Salas reutilizables (T-116): infraestructura de booking, gestionada por admin. -->
                    <div class="bf-row bf-row--between" style="margin:1.6rem 0 .6rem;">
                        <h3 class="bf-h3">Salas</h3>
                        ${ctx.iAmAdmin ? `<button class="bf-btn bf-btn--sm" id="b-new-venue">➕ Nueva sala</button>` : ''}
                    </div>
                    <ul class="setlist-list" id="b-venues"><li><small>Cargando…</small></li></ul>
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

                <div class="bs-panel" data-panel="giras" hidden>
                    <div id="b-tours-list-wrap">
                        <div class="bf-row bf-row--between" style="margin-bottom:.6rem;">
                            <h3 class="bf-h3">Giras</h3>
                            ${ctx.iAmAdmin ? `<button class="bf-btn bf-btn--sm bf-btn--primary" id="b-new-tour">➕ Nueva gira</button>` : ''}
                        </div>
                        <div id="b-tours"><p class="loading-text">Cargando…</p></div>
                    </div>
                    <div id="b-tour-detail" hidden></div>
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
        if (key === 'repertorio') { loadRepertoire(bandId, !ctx.iAmGuest); loadCollections(bandId, !ctx.iAmGuest); }
        else if (key === 'setlists') loadBandSetlists(bandId, !ctx.iAmGuest);
        else if (key === 'agenda') { loadAgenda(bandId, ctx.iAmAdmin); loadVenues(bandId, ctx.iAmAdmin); }
        else if (key === 'finanzas') loadFinance(bandId, ctx.iAmAdmin);
        else if (key === 'chat') initChat(bandId, ctx.iAmAdmin);
        else if (key === 'giras') loadTours(ctx.iAmAdmin);
    }

    // ── Giras (V3-F5, T-096) ────────────────────────────────────────────────
    async function loadTours(isAdmin) {
        const wrap = document.getElementById('b-tours');
        if (!wrap) return;
        try {
            const res = await apiFetch(`/bands/${bandId}/tours`);
            if (!res.ok) throw new Error('http');
            const tours = await res.json();
            if (!tours.length) {
                wrap.innerHTML = bfEmpty('calendar', 'Sin giras todavía',
                    isAdmin ? 'Crea tu primera gira para planificar la ruta y el presupuesto.'
                            : 'Aún no hay giras planificadas.');
                return;
            }
            wrap.innerHTML = `<ul class="setlist-list">${tours.map(tourRow).join('')}</ul>`;
            wrap.querySelectorAll('[data-tour]').forEach(li =>
                li.addEventListener('click', () => openTour(li.dataset.tour, isAdmin)));
        } catch (e) {
            wrap.innerHTML = '<p class="loading-text">No se pudieron cargar las giras.</p>';
        }
    }

    function tourRow(t) {
        const dates = t.start_date
            ? `<small>${fmtDay(t.start_date)}${t.end_date ? ' – ' + fmtDay(t.end_date) : ''}</small>` : '';
        return `<li class="setlist-song" data-tour="${escapeHtml(t.id)}" style="cursor:pointer;">
            <span class="sl-title">${escapeHtml(t.name)}
                <small>${escapeHtml(TOUR_STATUS[t.status] || t.status)} · ${t.stop_count} ${t.stop_count === 1 ? 'parada' : 'paradas'} · ${money(t.total_budget)}${Number(t.total_fee) > 0 ? ' · 💶 ' + money(t.total_fee) + ' caché' : ''}</small></span>
            ${dates}
        </li>`;
    }

    async function openTour(tourId, isAdmin) {
        const listWrap = document.getElementById('b-tours-list-wrap');
        const detail = document.getElementById('b-tour-detail');
        listWrap.hidden = true; detail.hidden = false;
        detail.innerHTML = '<p class="loading-text">Cargando gira…</p>';
        let tour, concerts = [];
        try {
            const [rt, re] = await Promise.all([
                apiFetch(`/bands/${bandId}/tours/${tourId}`),
                apiFetch(`/bands/${bandId}/events`)]);
            if (!rt.ok) throw new Error('http');
            tour = await rt.json();
            if (re.ok) concerts = (await re.json()).filter(e => e.type === 'concert');
        } catch (e) { detail.innerHTML = '<p class="loading-text">No se pudo abrir la gira.</p>'; return; }
        renderTourDetail(detail, tour, concerts, isAdmin);
    }

    function backToTours(isAdmin) {
        document.getElementById('b-tour-detail').hidden = true;
        document.getElementById('b-tours-list-wrap').hidden = false;
        loadTours(isAdmin);
    }

    function renderTourDetail(detail, tour, concerts, isAdmin) {
        const stops = (tour.stops || []).map(s => `
            <li class="setlist-song">
                <span class="sl-title">${escapeHtml(s.city || s.event_title || 'Parada')}
                    <small>${s.event_title ? '🎤 ' + escapeHtml(s.event_title) : 'sin concierto ligado'}${s.event_starts_at ? ' · ' + fmtDay(s.event_starts_at) : ''}</small></span>
                ${isAdmin ? `<button class="bf-btn bf-btn--sm bf-btn--danger" data-del-stop="${escapeHtml(s.id)}">Quitar</button>` : ''}
            </li>`).join('') || '<li><small>Sin paradas todavía.</small></li>';

        const budget = (tour.budget_lines || []).map(b => `
            <li class="setlist-song">
                <span class="sl-title">${escapeHtml(b.concept)}<small>${b.category ? escapeHtml(b.category) : 'sin categoría'}</small></span>
                <span class="bf-num">${money(b.estimated_amount)}</span>
                ${isAdmin ? `<button class="bf-btn bf-btn--sm bf-btn--danger" data-del-line="${escapeHtml(b.id)}">Quitar</button>` : ''}
            </li>`).join('') || '<li><small>Sin líneas de presupuesto.</small></li>';

        const concertOpts = ['<option value="">— Parada sin concierto —</option>']
            .concat(concerts.map(c => `<option value="${escapeHtml(c.id)}">${escapeHtml(c.title)}</option>`)).join('');

        detail.innerHTML = `
            <button class="bf-btn bf-btn--sm bf-btn--ghost" id="b-tour-back" style="margin-bottom:.6rem;">← Giras</button>
            <div class="bf-band-banner" style="margin-bottom:1rem;">
                <div class="bf-grow">
                    <div class="bf-band-banner__name">${escapeHtml(tour.name)}</div>
                    <div class="bf-band-banner__meta">${escapeHtml(TOUR_STATUS[tour.status] || tour.status)} · Presupuesto estimado: <span class="bf-num">${money(tour.total_budget)}</span> · Caché conciertos: <span class="bf-num">${money(tour.total_fee)}</span></div>
                </div>
            </div>

            <div class="bf-card bf-stack" style="margin-bottom:1rem;">
                <h3 class="bf-h3">Ruta (${(tour.stops || []).length})</h3>
                <ul class="setlist-list">${stops}</ul>
                ${isAdmin ? `<div class="bf-row bf-wrap" style="gap:.4rem;">
                    <input class="bf-input" id="b-stop-city" placeholder="Ciudad" style="max-width:140px;">
                    <select class="bf-select" id="b-stop-event" style="max-width:200px;">${concertOpts}</select>
                    <button class="bf-btn bf-btn--sm bf-btn--primary" id="b-add-stop">Añadir parada</button>
                </div>` : ''}
            </div>

            <div class="bf-card bf-stack">
                <h3 class="bf-h3">Presupuesto</h3>
                <ul class="setlist-list">${budget}</ul>
                ${isAdmin ? `<div class="bf-row bf-wrap" style="gap:.4rem;">
                    <input class="bf-input" id="b-line-concept" placeholder="Concepto" style="max-width:160px;">
                    <input class="bf-input bf-num" id="b-line-amount" type="number" min="0" step="0.01" placeholder="0.00" style="max-width:100px;">
                    <button class="bf-btn bf-btn--sm bf-btn--primary" id="b-add-line">Añadir línea</button>
                </div>` : ''}
            </div>`;

        document.getElementById('b-tour-back').addEventListener('click', () => backToTours(isAdmin));
        const reopen = () => openTour(tour.id, isAdmin);

        const addStop = document.getElementById('b-add-stop');
        if (addStop) addStop.addEventListener('click', async () => {
            const city = document.getElementById('b-stop-city').value.trim();
            const eventId = document.getElementById('b-stop-event').value || null;
            if (!city && !eventId) { toast('Indica una ciudad o un concierto.', 'error'); return; }
            await postTour(`/bands/${bandId}/tours/${tour.id}/stops`,
                { city: city || null, event_id: eventId }, reopen);
        });
        const addLine = document.getElementById('b-add-line');
        if (addLine) addLine.addEventListener('click', async () => {
            const concept = document.getElementById('b-line-concept').value.trim();
            const amount = document.getElementById('b-line-amount').value;
            if (!concept || amount === '') { toast('Concepto e importe son obligatorios.', 'error'); return; }
            await postTour(`/bands/${bandId}/tours/${tour.id}/budget`,
                { concept, estimated_amount: amount }, reopen);
        });
        detail.querySelectorAll('[data-del-stop]').forEach(b => b.addEventListener('click', () =>
            delTour(`/bands/${bandId}/tours/${tour.id}/stops/${b.dataset.delStop}`, reopen)));
        detail.querySelectorAll('[data-del-line]').forEach(b => b.addEventListener('click', () =>
            delTour(`/bands/${bandId}/tours/${tour.id}/budget/${b.dataset.delLine}`, reopen)));
    }

    async function postTour(url, body, onDone) {
        try {
            const res = await apiFetch(url, {
                method: 'POST', headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(body) });
            if (!res.ok) throw new Error('http');
            onDone();
        } catch (e) { toast('No se pudo guardar.', 'error'); }
    }
    async function delTour(url, onDone) {
        try {
            const res = await apiFetch(url, { method: 'DELETE' });
            if (!res.ok && res.status !== 204) throw new Error('http');
            onDone();
        } catch (e) { toast('No se pudo quitar.', 'error'); }
    }

    function wire(band, active, ctx) {
        const invite = document.getElementById('bs-invite');
        if (invite) invite.addEventListener('click', () => generateInvite(bandId));
        const addSong = document.getElementById('b-add-song');
        if (addSong) addSong.addEventListener('click', () => copyFromPersonal(bandId));
        const newColl = document.getElementById('b-new-collection');
        if (newColl) newColl.addEventListener('click', () =>
            newCollection(bandId, { onDone: () => loadCollections(bandId, !ctx.iAmGuest) }));
        const newEv = document.getElementById('b-new-event');
        if (newEv) newEv.addEventListener('click', () => newEvent(bandId));
        const newVen = document.getElementById('b-new-venue');
        if (newVen) newVen.addEventListener('click', () =>
            newVenue(bandId, { onDone: () => loadVenues(bandId, ctx.iAmAdmin) }));
        const newTx = document.getElementById('b-new-tx');
        if (newTx) newTx.addEventListener('click', () => newTransaction(bandId, active));
        const newTour = document.getElementById('b-new-tour');
        if (newTour) newTour.addEventListener('click', async () => {
            const name = await promptModal('¿Cómo se llama la gira?',
                { okText: 'Crear', placeholder: 'Ej: Gira Verano 2026' });
            if (!name || !name.trim()) return;
            try {
                const res = await apiFetch(`/bands/${bandId}/tours`, {
                    method: 'POST', headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ name: name.trim() }) });
                if (!res.ok) throw new Error('http');
                loadTours(ctx.iAmAdmin);
            } catch (e) { toast('No se pudo crear la gira.', 'error'); }
        });
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
