/**
 * red.js — Explorar como hub de la red profesional (V6-F9b, GUIA_MAESTRA_V6 §9.9).
 *
 * Pestañas (con hash, se pueden enlazar): Bolos abiertos · Salas · Profesionales · Mensajes ·
 * Mis perfiles. "Canciones" lleva a la biblioteca global de siempre (biblioteca-global.html).
 *
 *  · Bolos abiertos (I-20): convocatorias de salas/bookers → "Postularnos" con el EPK de la banda.
 *  · Salas / Profesionales (I-24): directorio filtrable por zona y categoría → ficha.html.
 *  · Mensajes (I-3): conversaciones de la red (candidaturas, contactos) + valorar tras tratar.
 *  · Mis perfiles: alta de sala/profesional, convocatorias, candidaturas (elegir → concierto en la
 *    agenda de la banda) y calendario de sala (I-23).
 * Todo texto de usuario se escapa (escapeHtml); los enlaces del usuario los valida el backend.
 */
(function () {
    const root = document.getElementById('red');
    if (!root) return;

    const KIND = {
        venue: 'Sala / local', booker: 'Booker / manager', photographer: 'Fotografía', video: 'Vídeo',
        sound_tech: 'Técnico de sonido', light_tech: 'Técnico de luces', studio: 'Estudio de grabación',
        rehearsal_room: 'Local de ensayo', luthier: 'Luthier / reparación', design: 'Diseño / merch',
        press: 'Prensa / promo', teacher: 'Profesor/a', other: 'Otros servicios',
    };
    const DEAL = { fee: 'Caché fijo', door: 'Taquilla', percent: 'Porcentaje', free: 'Gratis + consumo', other: 'A convenir' };
    const APP_ST = { sent: 'Enviada', seen: 'Vista', shortlisted: 'Preseleccionada', chosen: 'Elegida', declined: 'Esta vez no' };
    const TABS = [
        { key: 'bolos', label: 'Bolos abiertos', icon: 'mic' },
        { key: 'salas', label: 'Salas', icon: 'map-pin' },
        { key: 'pros', label: 'Profesionales', icon: 'users' },
        { key: 'mensajes', label: 'Mensajes', icon: 'chat' },
        { key: 'mios', label: 'Mis perfiles', icon: 'user' },
    ];
    let myBands = [];        // [{id, name, role}]
    let current = null;

    const chips = (arr) => (arr || []).map(s => `<span class="bf-chip">${escapeHtml(s)}</span>`).join('');
    const stars = (avg, n) => n ? `<span class="rd-stars" title="${avg} de 5 · ${n} valoraciones">${bfIco('star', 13)} ${avg} <span class="bf-faint">(${n})</span></span>` : '';
    const verified = (v) => v ? `<span class="bf-badge bf-badge--ok" title="Verificada por BandFlow">${bfIco('check-circle', 12)} Verificada</span>` : '';
    const money = (x) => (x === null || x === undefined || x === '') ? '' : bfMoney(x);
    function debounce(fn, ms = 300) { let t; return (...a) => { clearTimeout(t); t = setTimeout(() => fn(...a), ms); }; }

    async function init() {
        if (!(await requireAuth())) return;
        try { myBands = await apiJson('/bands/'); } catch (e) { myBands = []; }
        root.innerHTML = `
            <div class="bf-row bf-row--between bf-wrap" style="gap:.5rem;">
                <div><h1 class="bf-h1">Explorar</h1>
                  <p class="bf-muted">Bolos que buscan banda, salas, y todo lo que un músico necesita cerca: fotografía, sonido, estudios, locales…</p></div>
                <a class="bf-btn bf-btn--sm" href="biblioteca-global.html">${bfIco('music', 15)} Canciones</a>
            </div>
            <div class="bf-tabs" role="tablist" style="margin:1rem 0;">
                ${TABS.map(t => `<button class="bf-tab" role="tab" data-tab="${t.key}" aria-selected="false" aria-controls="rd-panel">${bfIco(t.icon, 15)} ${t.label}</button>`).join('')}
            </div>
            <div id="rd-panel" role="tabpanel"></div>
            <p class="bf-faint rd-legal">BandFlow conecta a músicos, salas y profesionales; no intermedia pagos ni contratos.</p>`;
        root.querySelectorAll('.bf-tab').forEach(b => b.addEventListener('click', () => { location.hash = b.dataset.tab; }));
        window.addEventListener('hashchange', route);
        route();
    }

    function route() {
        const key = (location.hash || '#bolos').slice(1).split('/')[0];
        const tab = TABS.find(t => t.key === key) ? key : 'bolos';
        root.querySelectorAll('.bf-tab').forEach(b => b.setAttribute('aria-selected', b.dataset.tab === tab ? 'true' : 'false'));
        current = tab;
        const panel = document.getElementById('rd-panel');
        ({ bolos: renderCalls, salas: (p) => renderDirectory(p, 'venue'), pros: (p) => renderDirectory(p, 'pros'),
           mensajes: renderThreads, mios: renderMine })[tab](panel);
    }

    // ══ Bolos abiertos ════════════════════════════════════════════════════════
    function callCard(c, opts = {}) {
        const when = c.starts_at ? bfDateLong(c.starts_at) : (c.flexible_dates ? 'Fechas flexibles' : 'Fecha a convenir');
        const deal = [c.deal_type ? DEAL[c.deal_type] : '', c.fee ? money(c.fee) : '', c.conditions || ''].filter(Boolean).join(' · ');
        const applied = (c.my_applications || [])[0];
        return `<article class="bf-card rd-call" data-call="${escapeHtml(c.id)}">
            <div class="rd-call__head">
                <span class="rd-call__date">${bfIco('calendar', 14)} ${escapeHtml(when)}</span>
                ${c.deadline_at ? `<span class="bf-faint">Hasta el ${escapeHtml(bfDate(c.deadline_at))}</span>` : ''}
            </div>
            <h3 class="bf-h3">${escapeHtml(c.title)}</h3>
            <p class="rd-call__venue"><a href="ficha.html?id=${encodeURIComponent(c.pro_profile_id)}">${escapeHtml(c.venue_name || '')}</a> ${verified(c.venue_verified)}${c.zone ? ` · ${bfIco('map-pin', 12)} ${escapeHtml(c.zone)}` : ''}</p>
            ${c.format ? `<p class="bf-muted">${escapeHtml(c.format)}</p>` : ''}
            ${deal ? `<p class="rd-call__deal">${bfIco('banknote', 14)} ${escapeHtml(deal)}</p>` : ''}
            ${c.description ? `<p class="rd-call__desc">${escapeHtml(c.description)}</p>` : ''}
            <div class="rd-chips">${chips(c.styles)}</div>
            ${opts.owner ? '' : `<div class="rd-call__actions">
                ${applied ? `<span class="bf-badge">${bfIco('check', 12)} Postulados · ${escapeHtml(APP_ST[applied.status] || applied.status)}</span>`
                          : `<button class="bf-btn bf-btn--primary bf-btn--sm" data-act="apply">${bfIco('send', 14)} Postularnos</button>`}
                <button class="bf-btn bf-btn--sm bf-btn--ghost" data-act="share">${bfIco('share', 14)} Compartir</button>
            </div>`}
        </article>`;
    }

    async function renderCalls(panel) {
        panel.innerHTML = `
            <div class="rd-filters">
                <input class="bf-input" id="rd-zone" placeholder="Zona (ciudad, comarca…)" aria-label="Zona">
                <input class="bf-input" id="rd-style" placeholder="Estilo (rock, versiones…)" aria-label="Estilo">
                <input class="bf-input" id="rd-q" placeholder="Buscar" aria-label="Buscar">
            </div>
            <div id="rd-list" class="rd-grid"><p class="bf-muted">Cargando…</p></div>
            <div class="rd-more"><button class="bf-btn bf-btn--sm" id="rd-more" hidden>Cargar más</button></div>`;
        let offset = 0, ctrl = null;
        const load = async (append = false) => {
            if (ctrl) ctrl.abort();
            ctrl = new AbortController();
            const p = new URLSearchParams({ limit: 24, offset });
            ['zone', 'style', 'q'].forEach(k => { const v = panel.querySelector('#rd-' + k).value.trim(); if (v) p.set(k, v); });
            const list = panel.querySelector('#rd-list');
            let rows;
            const sig = ctrl.signal;
            try { rows = await apiJson('/public/gig-calls?' + p, { signal: sig }); }
            catch (e) { if (sig.aborted) return; list.innerHTML = '<p class="bf-muted">No se pudieron cargar los bolos.</p>'; return; }
            if (sig.aborted) return;
            // Para saber si mis bandas ya se postularon, pedimos la vista autenticada de cada una.
            rows = await Promise.all(rows.map(async c => { try { return await apiJson('/gig-calls/' + c.id); } catch (e) { return c; } }));
            const html = rows.map(c => callCard(c)).join('');
            if (append) list.insertAdjacentHTML('beforeend', html);
            else list.innerHTML = html || bfEmpty('mic', 'No hay bolos abiertos con esos filtros',
                'Cuando una sala publique una convocatoria en tu zona, aparecerá aquí. ¿Tienes una sala? Publica la tuya desde «Mis perfiles».');
            panel.querySelector('#rd-more').hidden = rows.length < 24;
            wireCalls(list, rows);
        };
        const reload = debounce(() => { offset = 0; load(false); });
        panel.querySelectorAll('.rd-filters input').forEach(i => i.addEventListener('input', reload));
        panel.querySelector('#rd-more').addEventListener('click', () => { offset += 24; load(true); });
        load(false);
    }

    function wireCalls(list, rows) {
        const byId = Object.fromEntries(rows.map(c => [c.id, c]));
        list.querySelectorAll('[data-call]').forEach(card => {
            if (card.dataset.wired) return; card.dataset.wired = '1';
            const c = byId[card.dataset.call];
            if (!c) return;
            const ap = card.querySelector('[data-act="apply"]');
            if (ap) ap.addEventListener('click', () => applyDialog(c));
            const sh = card.querySelector('[data-act="share"]');
            if (sh) sh.addEventListener('click', () => bfShare({ title: c.title, text: `Bolo abierto en ${c.venue_name}: «${c.title}»`, url: `${location.origin}/static/red.html#bolos` }));
        });
    }

    async function applyDialog(c) {
        const admin = myBands.filter(b => b.role === 'admin');
        if (!admin.length) {
            await bfDialog({ title: 'Postularnos', body: `<p>Para postularte necesitas ser admin de una banda.</p>
                <p class="bf-muted">Crea tu banda (o pide a su admin que lo haga) y vuelve aquí.</p>`,
                actions: [{ label: 'Ir a mis bandas', value: 'go', primary: true }, { label: 'Cerrar', value: null }] })
                .then(v => { if (v === 'go') location.href = 'bands.html'; });
            return;
        }
        const r = await bfDialog({
            title: `Postularnos · ${c.title}`,
            body: `<div class="bf-stack">
                <div><label class="bf-label" for="rd-a-band">Banda</label>
                  <select class="bf-input" id="rd-a-band">${admin.map(b => `<option value="${escapeHtml(b.id)}">${escapeHtml(b.name)}</option>`).join('')}</select></div>
                <div><label class="bf-label" for="rd-a-msg">Mensaje para ${escapeHtml(c.venue_name || 'la sala')}</label>
                  <textarea class="bf-textarea" id="rd-a-msg" rows="4" maxlength="2000" placeholder="Quiénes sois, qué tocáis, enlace a un vídeo en directo…"></textarea></div>
                <p class="bf-faint" style="font-size:.8rem;">Se envía también el dossier (EPK) de la banda. Edítalo en tu banda → Ajustes → Dossier.</p>
              </div>`,
            actions: [{ label: 'Cancelar', value: null }, { label: 'Enviar candidatura', primary: true,
                onClick: (root) => ({ band: root.querySelector('#rd-a-band').value, message: root.querySelector('#rd-a-msg').value.trim() }) }],
        });
        if (!r) return;
        try {
            await apiJson(`/bands/${encodeURIComponent(r.band)}/gig-applications`, { method: 'POST', body: { gig_call_id: c.id, message: r.message || null } });
            toast('Candidatura enviada. La sala la verá en su bandeja.', 'success');
            route();
        } catch (e) { toast(errorMessage(e, 'No se pudo enviar la candidatura.'), 'error'); }
    }

    // ══ Directorio (salas / profesionales) ════════════════════════════════════
    function proCard(p) {
        return `<a class="bf-card rd-pro" href="ficha.html?id=${encodeURIComponent(p.id)}">
            <div class="rd-pro__head">
                ${bfAvatar({ url: p.avatar_url, name: p.name, color: bandColor(p.id) })}
                <div style="min-width:0;">
                    <div class="rd-pro__name">${escapeHtml(p.name)} ${verified(p.verified)}</div>
                    <div class="bf-faint">${escapeHtml(KIND[p.kind] || p.kind)}${p.zone ? ' · ' + escapeHtml(p.zone) : ''}${p.capacity ? ` · ${p.capacity} pers.` : ''}</div>
                </div>
            </div>
            ${p.bio ? `<p class="rd-pro__bio">${escapeHtml(p.bio)}</p>` : ''}
            <div class="rd-chips">${chips((p.styles || []).concat(p.services || []).slice(0, 6))}</div>
            <div class="rd-pro__foot">${stars(p.rating_avg, p.rating_count)}${p.price_hint ? `<span class="bf-faint">${escapeHtml(p.price_hint)}</span>` : ''}${p.open_calls ? `<span class="bf-badge">${p.open_calls} ${p.open_calls === 1 ? 'bolo abierto' : 'bolos abiertos'}</span>` : ''}</div>
        </a>`;
    }

    async function renderDirectory(panel, mode) {
        const isVenue = mode === 'venue';
        panel.innerHTML = `
            <div class="rd-filters">
                <input class="bf-input" id="rd-zone" placeholder="Zona (ciudad, comarca…)" aria-label="Zona">
                ${isVenue ? '' : `<select class="bf-input" id="rd-kind" aria-label="Categoría"><option value="pros">Todas las categorías</option>
                    ${Object.entries(KIND).filter(([k]) => k !== 'venue').map(([k, l]) => `<option value="${k}">${l}</option>`).join('')}</select>`}
                <input class="bf-input" id="rd-q" placeholder="Buscar por nombre" aria-label="Buscar">
            </div>
            <div id="rd-list" class="rd-grid"><p class="bf-muted">Cargando…</p></div>
            <div class="rd-more"><button class="bf-btn bf-btn--sm" id="rd-more" hidden>Cargar más</button></div>`;
        let offset = 0, ctrl = null;
        const load = async (append = false) => {
            if (ctrl) ctrl.abort();
            ctrl = new AbortController();
            const p = new URLSearchParams({ limit: 24, offset, kind: isVenue ? 'venue' : panel.querySelector('#rd-kind').value });
            const z = panel.querySelector('#rd-zone').value.trim(), q = panel.querySelector('#rd-q').value.trim();
            if (z) p.set('zone', z);
            if (q) p.set('q', q);
            const list = panel.querySelector('#rd-list');
            let rows;
            const sig = ctrl.signal;
            try { rows = await apiJson('/public/pros?' + p, { signal: sig }); }
            catch (e) { if (sig.aborted) return; list.innerHTML = '<p class="bf-muted">No se pudo cargar el directorio.</p>'; return; }
            const html = rows.map(proCard).join('');
            if (append) list.insertAdjacentHTML('beforeend', html);
            else list.innerHTML = html || bfEmpty(isVenue ? 'map-pin' : 'users',
                isVenue ? 'Aún no hay salas en esa zona' : 'Aún no hay profesionales con esos filtros',
                '¿Conoces alguno? Invítale a crear su ficha gratis desde «Mis perfiles».');
            panel.querySelector('#rd-more').hidden = rows.length < 24;
        };
        const reload = debounce(() => { offset = 0; load(false); });
        panel.querySelectorAll('.rd-filters input, .rd-filters select').forEach(i => i.addEventListener('input', reload));
        panel.querySelector('#rd-more').addEventListener('click', () => { offset += 24; load(true); });
        load(false);
    }

    // ══ Mensajes ══════════════════════════════════════════════════════════════
    async function renderThreads(panel) {
        panel.innerHTML = `<div class="rd-inbox"><ul class="rd-threads" id="rd-threads"><li class="bf-muted">Cargando…</li></ul>
            <section class="rd-thread" id="rd-thread"><p class="bf-muted">Elige una conversación.</p></section></div>`;
        let threads;
        try { threads = await apiJson('/me/threads'); }
        catch (e) { panel.querySelector('#rd-threads').innerHTML = '<li class="bf-muted">No se pudieron cargar los mensajes.</li>'; return; }
        const ul = panel.querySelector('#rd-threads');
        if (!threads.length) {
            panel.querySelector('.rd-inbox').innerHTML = bfEmpty('chat', 'Sin conversaciones',
                'Aquí verás las candidaturas que envíes o recibas y los contactos con salas y profesionales.');
            return;
        }
        ul.innerHTML = threads.map(t => `<li><button class="rd-thread-item" data-thread="${escapeHtml(t.id)}">
            <strong>${escapeHtml(t.title)}</strong>${t.subtitle ? `<span class="bf-faint">${escapeHtml(t.subtitle)}</span>` : ''}
            <span class="rd-thread-item__last">${escapeHtml(t.last_message || '')}</span>
            <span class="bf-faint rd-thread-item__when">${escapeHtml(bfDate(t.last_message_at))}</span></button></li>`).join('');
        ul.querySelectorAll('[data-thread]').forEach(b => b.addEventListener('click', () => openThread(panel, b.dataset.thread)));
        const wanted = location.hash.split('/')[1];
        openThread(panel, wanted && threads.some(t => t.id === wanted) ? wanted : threads[0].id);
    }

    async function openThread(panel, tid) {
        panel.querySelectorAll('[data-thread]').forEach(b => b.classList.toggle('is-active', b.dataset.thread === tid));
        const box = panel.querySelector('#rd-thread');
        let t;
        try { t = await apiJson('/me/threads/' + encodeURIComponent(tid)); }
        catch (e) { box.innerHTML = '<p class="bf-muted">No se pudo abrir la conversación.</p>'; return; }
        box.innerHTML = `
            <header class="rd-thread__head"><div><strong>${escapeHtml(t.title)}</strong>${t.subtitle ? `<div class="bf-faint">${escapeHtml(t.subtitle)}</div>` : ''}</div>
                ${t.can_review ? `<button class="bf-btn bf-btn--sm" id="rd-review">${bfIco('star', 14)} Valorar</button>` : ''}</header>
            <div class="rd-msgs" id="rd-msgs">${t.messages.map(m => `<div class="rd-msg${m.mine ? ' rd-msg--mine' : ''}">
                ${m.mine ? '' : `<div class="rd-msg__who">${escapeHtml(m.author_name || '')}</div>`}
                <div class="rd-msg__body">${escapeHtml(m.body).replace(/\n/g, '<br>')}</div>
                <div class="rd-msg__when">${escapeHtml(bfDate(m.created_at))}</div></div>`).join('')}</div>
            <form class="bf-composer" id="rd-reply"><input class="bf-input" id="rd-reply-in" maxlength="4000" placeholder="Escribe…" aria-label="Respuesta">
                <button class="bf-btn bf-btn--primary" type="submit">${bfIco('send', 15)} Enviar</button></form>`;
        const msgs = box.querySelector('#rd-msgs');
        msgs.scrollTop = msgs.scrollHeight;
        box.querySelector('#rd-reply').addEventListener('submit', async (e) => {
            e.preventDefault();
            const inp = box.querySelector('#rd-reply-in');
            const body = inp.value.trim();
            if (!body) return;
            try { await apiJson(`/me/threads/${encodeURIComponent(tid)}/messages`, { method: 'POST', body: { body } }); openThread(panel, tid); }
            catch (err) { toast(errorMessage(err, 'No se pudo enviar.'), 'error'); }
        });
        const rv = box.querySelector('#rd-review');
        if (rv) rv.addEventListener('click', () => reviewDialog(t.review_target, t.title));
    }

    async function reviewDialog(target, name) {
        const r = await bfDialog({
            title: `Valorar a ${name}`,
            body: `<div class="bf-stack"><div class="rd-star-pick" role="radiogroup" aria-label="Puntuación">
                ${[1, 2, 3, 4, 5].map(n => `<label><input type="radio" name="rd-stars" value="${n}" ${n === 5 ? 'checked' : ''}> ${n}</label>`).join('')}</div>
                <textarea class="bf-textarea" id="rd-rv-body" rows="3" maxlength="500" placeholder="¿Qué tal fue? (opcional)"></textarea>
                <p class="bf-faint" style="font-size:.8rem;">Solo se puede valorar a quien has tratado por BandFlow. La valoración es pública.</p></div>`,
            actions: [{ label: 'Cancelar', value: null }, { label: 'Publicar', primary: true, onClick: (root) => ({
                stars: Number((root.querySelector('input[name="rd-stars"]:checked') || {}).value || 5),
                body: root.querySelector('#rd-rv-body').value.trim() || null }) }],
        });
        if (!r) return;
        const url = target.kind === 'pro' ? `/pros/${encodeURIComponent(target.id)}/reviews` : `/network/bands/${encodeURIComponent(target.id)}/reviews`;
        try { await apiJson(url, { method: 'POST', body: r }); toast('¡Gracias! Valoración publicada.', 'success'); }
        catch (e) { toast(errorMessage(e, 'No se pudo publicar.'), 'error'); }
    }

    // ══ Mis perfiles (sala / profesional) ═════════════════════════════════════
    async function renderMine(panel) {
        panel.innerHTML = '<p class="bf-muted">Cargando…</p>';
        let pros, calls;
        try { [pros, calls] = await Promise.all([apiJson('/me/pro-profiles'), apiJson('/me/gig-calls')]); }
        catch (e) { panel.innerHTML = '<p class="bf-muted">No se pudieron cargar tus perfiles.</p>'; return; }
        const appsOfBands = (await Promise.all(myBands.map(b => apiJson(`/bands/${b.id}/gig-applications`).catch(() => [])))).flat();
        panel.innerHTML = `
            <section class="bf-stack">
                <div class="bf-row bf-row--between bf-wrap"><h2 class="bf-h2">Mis perfiles en la red</h2>
                    <button class="bf-btn bf-btn--primary bf-btn--sm" id="rd-new-pro">${bfIco('plus', 15)} Añadir perfil de sala o profesional</button></div>
                ${pros.length ? `<div class="rd-grid">${pros.map(p => `<div class="bf-card rd-pro" data-pro="${escapeHtml(p.id)}">
                    <div class="rd-pro__head">${bfAvatar({ url: p.avatar_url, name: p.name, color: bandColor(p.id) })}
                      <div><div class="rd-pro__name">${escapeHtml(p.name)} ${verified(p.verified)}</div><div class="bf-faint">${escapeHtml(KIND[p.kind] || p.kind)}${p.zone ? ' · ' + escapeHtml(p.zone) : ''}${p.visibility !== 'public' ? ' · oculto del directorio' : ''}</div></div></div>
                    <div class="bf-row bf-wrap" style="gap:.4rem;margin-top:.6rem;">
                      <button class="bf-btn bf-btn--sm" data-act="edit">${bfIco('edit', 14)} Editar</button>
                      <a class="bf-btn bf-btn--sm bf-btn--ghost" href="ficha.html?id=${encodeURIComponent(p.id)}">Ver ficha</a>
                      ${['venue', 'booker'].includes(p.kind) ? `<button class="bf-btn bf-btn--sm bf-btn--primary" data-act="call">${bfIco('plus', 14)} Convocatoria</button>
                      <button class="bf-btn bf-btn--sm bf-btn--ghost" data-act="cal">${bfIco('calendar', 14)} Calendario</button>` : ''}
                    </div></div>`).join('')}</div>`
                : `<div class="bf-card">${bfEmpty('map-pin', '¿Tienes una sala o das servicios a músicos?', 'Crea tu ficha gratis: las bandas te encontrarán por zona y podrás publicar bolos y recibir candidaturas.')}</div>`}
            </section>
            ${calls.length ? `<section class="bf-stack" style="margin-top:1.5rem;"><h2 class="bf-h2">Mis convocatorias</h2>
                <div class="rd-grid">${calls.map(c => `<div class="rd-call-own" data-own-call="${escapeHtml(c.id)}">${callCard(c, { owner: true })}
                    <div class="bf-row bf-wrap rd-own-actions">
                        <button class="bf-btn bf-btn--sm bf-btn--primary" data-act="apps">${bfIco('users', 14)} Candidaturas (${c.applications || 0})</button>
                        ${c.status === 'open' ? `<button class="bf-btn bf-btn--sm" data-act="close">Cerrar</button>` : `<span class="bf-badge">${c.status === 'filled' ? 'Cubierta' : 'Cerrada'}</span>`}
                    </div></div>`).join('')}</div></section>` : ''}
            ${appsOfBands.length ? `<section class="bf-stack" style="margin-top:1.5rem;"><h2 class="bf-h2">Candidaturas de mis bandas</h2>
                <ul class="setlist-list">${appsOfBands.map(a => `<li class="setlist-song"><span class="sl-title">${escapeHtml(a.call_title || '')}
                    <small>${escapeHtml(a.band_name || '')} → ${escapeHtml(a.venue_name || '')}${a.starts_at ? ' · ' + escapeHtml(bfDate(a.starts_at)) : ''}</small></span>
                    <span class="bf-badge${a.status === 'chosen' ? ' bf-badge--ok' : ''}">${escapeHtml(APP_ST[a.status] || a.status)}</span></li>`).join('')}</ul></section>` : ''}`;
        panel.querySelector('#rd-new-pro').addEventListener('click', () => proDialog(null));
        const byPro = Object.fromEntries(pros.map(p => [p.id, p]));
        panel.querySelectorAll('[data-pro]').forEach(card => {
            const p = byPro[card.dataset.pro];
            card.querySelector('[data-act="edit"]').addEventListener('click', () => proDialog(p));
            const c = card.querySelector('[data-act="call"]');
            if (c) c.addEventListener('click', () => callDialog(p));
            const cal = card.querySelector('[data-act="cal"]');
            if (cal) cal.addEventListener('click', () => calendarDialog(p));
        });
        const byCall = Object.fromEntries(calls.map(c => [c.id, c]));
        panel.querySelectorAll('[data-own-call]').forEach(el => {
            const c = byCall[el.dataset.ownCall];
            el.querySelector('[data-act="apps"]').addEventListener('click', () => applicationsDialog(c));
            const cl = el.querySelector('[data-act="close"]');
            if (cl) cl.addEventListener('click', async () => {
                if (!(await confirmModal('¿Cerrar esta convocatoria? Dejará de aparecer en Bolos abiertos.', { okText: 'Cerrar' }))) return;
                try { await apiJson(`/me/gig-calls/${c.id}`, { method: 'PATCH', body: { status: 'closed' } }); route(); }
                catch (e) { toast(errorMessage(e), 'error'); }
            });
        });
    }

    const csv = (s) => (s || '').split(',').map(x => x.trim()).filter(Boolean);
    async function proDialog(p) {
        const isNew = !p;
        p = p || { kind: 'venue', visibility: 'public', deal_types: [] };
        const links = (p.links || []).map(l => `${l.label} | ${l.url}`).join('\n');
        const r = await bfDialog({
            title: isNew ? 'Nuevo perfil en la red' : `Editar · ${p.name}`,
            wide: true,
            body: `<div class="bf-stack">
                <div class="bf-form-grid">
                  <div><label class="bf-label" for="pf-kind">Qué eres</label>
                    <select class="bf-input" id="pf-kind" ${isNew ? '' : 'disabled'}>${Object.entries(KIND).map(([k, l]) => `<option value="${k}"${p.kind === k ? ' selected' : ''}>${l}</option>`).join('')}</select></div>
                  <div><label class="bf-label" for="pf-name">Nombre</label><input class="bf-input" id="pf-name" maxlength="255" value="${escapeHtml(p.name || '')}" autofocus></div>
                  <div><label class="bf-label" for="pf-zone">Zona</label><input class="bf-input" id="pf-zone" maxlength="255" placeholder="Barcelona, Vallès…" value="${escapeHtml(p.zone || '')}"></div>
                </div>
                <div><label class="bf-label" for="pf-bio">Presentación</label><textarea class="bf-textarea" id="pf-bio" rows="3" maxlength="4000">${escapeHtml(p.bio || '')}</textarea></div>
                <div class="bf-form-grid">
                  <div><label class="bf-label" for="pf-services">Servicios / estilos (separados por comas)</label><input class="bf-input" id="pf-services" value="${escapeHtml(((p.kind === 'venue' ? p.styles : p.services) || []).join(', '))}"></div>
                  <div><label class="bf-label" for="pf-price">Precio orientativo</label><input class="bf-input" id="pf-price" maxlength="255" placeholder="desde 150 € / bolo" value="${escapeHtml(p.price_hint || '')}"></div>
                </div>
                <fieldset class="pf-venue bf-stack" ${p.kind === 'venue' ? '' : 'hidden'}><legend class="bf-label">Datos de la sala</legend>
                  <div class="bf-form-grid">
                    <div><label class="bf-label" for="pf-cap">Aforo</label><input class="bf-input" type="number" min="0" id="pf-cap" value="${escapeHtml(p.capacity ?? '')}"></div>
                    <div><label class="bf-label" for="pf-addr">Dirección</label><input class="bf-input" id="pf-addr" maxlength="512" value="${escapeHtml(p.address || '')}"></div>
                  </div>
                  <div><span class="bf-label">Condiciones habituales</span><div class="bf-row bf-wrap" style="gap:.8rem;">${Object.entries(DEAL).map(([k, l]) => `<label><input type="checkbox" class="pf-deal" value="${k}" ${(p.deal_types || []).includes(k) ? 'checked' : ''}> ${l}</label>`).join('')}</div></div>
                  <div><label class="bf-label" for="pf-backline">Equipo / backline</label><textarea class="bf-textarea" id="pf-backline" rows="2" maxlength="4000">${escapeHtml(p.backline || '')}</textarea></div>
                </fieldset>
                <div><label class="bf-label" for="pf-links">Enlaces (uno por línea: «Instagram | https://…»)</label><textarea class="bf-textarea" id="pf-links" rows="2">${escapeHtml(links)}</textarea></div>
                <div class="bf-form-grid">
                  <div><label class="bf-label" for="pf-phone">Teléfono (opcional)</label><input class="bf-input" id="pf-phone" maxlength="64" value="${escapeHtml(p.phone || '')}"></div>
                  <div><label class="bf-label">&nbsp;</label><label><input type="checkbox" id="pf-showphone" ${p.show_phone ? 'checked' : ''}> Mostrarlo a usuarios con sesión</label></div>
                  <div><label class="bf-label">&nbsp;</label><label><input type="checkbox" id="pf-public" ${p.visibility === 'public' ? 'checked' : ''}> Aparecer en el directorio</label></div>
                </div>
              </div>`,
            onMount: (root) => {
                const kind = root.querySelector('#pf-kind');
                kind.addEventListener('change', () => { root.querySelector('.pf-venue').hidden = kind.value !== 'venue'; });
            },
            actions: [
                ...(isNew ? [] : [{ label: 'Borrar perfil', value: 'delete', danger: true }]),
                { label: 'Cancelar', value: null },
                { label: isNew ? 'Crear perfil' : 'Guardar', primary: true, onClick: (root) => {
                    const kind = root.querySelector('#pf-kind').value;
                    const name = root.querySelector('#pf-name').value.trim();
                    if (!name) { toast('Pon un nombre.', 'error'); return false; }
                    const tags = csv(root.querySelector('#pf-services').value);
                    const linksIn = root.querySelector('#pf-links').value.split('\n').map(l => l.split('|').map(x => x.trim()))
                        .filter(x => x[0] && x[1]).map(([label, url]) => ({ label, url }));
                    const cap = root.querySelector('#pf-cap').value;
                    return {
                        ...(isNew ? { kind } : {}), name, zone: root.querySelector('#pf-zone').value.trim() || null,
                        bio: root.querySelector('#pf-bio').value.trim() || null,
                        services: kind === 'venue' ? [] : tags, styles: kind === 'venue' ? tags : [],
                        price_hint: root.querySelector('#pf-price').value.trim() || null,
                        capacity: kind === 'venue' && cap !== '' ? Number(cap) : null,
                        address: kind === 'venue' ? (root.querySelector('#pf-addr').value.trim() || null) : null,
                        deal_types: kind === 'venue' ? [...root.querySelectorAll('.pf-deal:checked')].map(i => i.value) : [],
                        backline: kind === 'venue' ? (root.querySelector('#pf-backline').value.trim() || null) : null,
                        links: linksIn, phone: root.querySelector('#pf-phone').value.trim() || null,
                        show_phone: root.querySelector('#pf-showphone').checked,
                        visibility: root.querySelector('#pf-public').checked ? 'public' : 'unlisted',
                    };
                } },
            ],
        });
        if (!r) return;
        try {
            if (r === 'delete') {
                if (!(await confirmModal('¿Borrar este perfil? Sus convocatorias se cerrarán.', { okText: 'Borrar' }))) return;
                await apiJson(`/me/pro-profiles/${p.id}`, { method: 'DELETE' });
            } else if (isNew) {
                await apiJson('/me/pro-profiles', { method: 'POST', body: r });
                toast('Perfil creado. Ya apareces en Explorar.', 'success');
            } else {
                await apiJson(`/me/pro-profiles/${p.id}`, { method: 'PATCH', body: r });
                toast('Perfil guardado.', 'success');
            }
            route();
        } catch (e) { toast(errorMessage(e, 'No se pudo guardar el perfil.'), 'error'); }
    }

    async function callDialog(p) {
        const r = await bfDialog({
            title: `Nueva convocatoria · ${p.name}`,
            wide: true,
            body: `<div class="bf-stack">
                <div><label class="bf-label" for="gc-title">Qué buscáis</label><input class="bf-input" id="gc-title" maxlength="255" placeholder="Banda de versiones para el sábado 20" autofocus></div>
                <div class="bf-form-grid">
                  <div><label class="bf-label" for="gc-start">Fecha y hora</label><input class="bf-input" type="datetime-local" id="gc-start"></div>
                  <div><label class="bf-label" for="gc-deadline">Candidaturas hasta</label><input class="bf-input" type="datetime-local" id="gc-deadline"></div>
                  <div><label class="bf-label">&nbsp;</label><label><input type="checkbox" id="gc-flex"> Fechas flexibles</label></div>
                </div>
                <div class="bf-form-grid">
                  <div><label class="bf-label" for="gc-styles">Estilos (comas)</label><input class="bf-input" id="gc-styles" value="${escapeHtml((p.styles || []).join(', '))}"></div>
                  <div><label class="bf-label" for="gc-format">Formato</label><input class="bf-input" id="gc-format" maxlength="255" placeholder="2 pases de 45 min, trío…"></div>
                </div>
                <div class="bf-form-grid">
                  <div><label class="bf-label" for="gc-deal">Condiciones</label><select class="bf-input" id="gc-deal"><option value="">—</option>${Object.entries(DEAL).map(([k, l]) => `<option value="${k}">${l}</option>`).join('')}</select></div>
                  <div><label class="bf-label" for="gc-fee">Caché (€)</label><input class="bf-input" type="number" min="0" step="0.01" id="gc-fee"></div>
                  <div><label class="bf-label" for="gc-cond">Extras</label><input class="bf-input" id="gc-cond" maxlength="2000" placeholder="Cena + 2 consumiciones"></div>
                </div>
                <div><label class="bf-label" for="gc-desc">Detalles</label><textarea class="bf-textarea" id="gc-desc" rows="3" maxlength="4000"></textarea></div>
              </div>`,
            actions: [{ label: 'Cancelar', value: null }, { label: 'Publicar convocatoria', primary: true, onClick: (root) => {
                const title = root.querySelector('#gc-title').value.trim();
                if (!title) { toast('Pon un título.', 'error'); return false; }
                const fee = root.querySelector('#gc-fee').value;
                return { title, starts_at: bfFromLocalInput(root.querySelector('#gc-start').value),
                    deadline_at: bfFromLocalInput(root.querySelector('#gc-deadline').value),
                    flexible_dates: root.querySelector('#gc-flex').checked, styles: csv(root.querySelector('#gc-styles').value),
                    format: root.querySelector('#gc-format').value.trim() || null, deal_type: root.querySelector('#gc-deal').value || null,
                    fee: fee !== '' ? fee : null, conditions: root.querySelector('#gc-cond').value.trim() || null,
                    description: root.querySelector('#gc-desc').value.trim() || null };
            } }],
        });
        if (!r) return;
        try { await apiJson(`/me/pro-profiles/${p.id}/gig-calls`, { method: 'POST', body: r }); toast('Convocatoria publicada en Bolos abiertos.', 'success'); route(); }
        catch (e) { toast(errorMessage(e, 'No se pudo publicar.'), 'error'); }
    }

    async function applicationsDialog(c) {
        let apps;
        try { apps = await apiJson(`/me/gig-calls/${c.id}/applications`); }
        catch (e) { toast(errorMessage(e), 'error'); return; }
        const epk = (e) => !e ? '' : `<div class="rd-epk">${e.bio ? `<p>${escapeHtml(e.bio)}</p>` : ''}
            <p class="bf-faint">${[e.formation, e.zone, e.fee_hint].filter(Boolean).map(escapeHtml).join(' · ')}</p>
            <div class="rd-chips">${chips(e.styles)}</div>
            ${(e.links || []).map(l => `<a href="${escapeHtml(l.url)}" target="_blank" rel="noopener nofollow">${escapeHtml(l.label)}</a>`).join(' · ')}
            ${e.rider_notes ? `<p class="bf-faint">Rider: ${escapeHtml(e.rider_notes)}</p>` : ''}</div>`;
        await bfDialog({
            title: `Candidaturas · ${c.title}`,
            wide: true,
            body: apps.length ? `<ul class="rd-apps">${apps.map(a => `<li class="bf-card rd-app" data-app="${escapeHtml(a.id)}">
                <div class="bf-row bf-row--between bf-wrap"><strong>${escapeHtml(a.band_name || '')}</strong><span class="bf-badge">${escapeHtml(APP_ST[a.status] || a.status)}</span></div>
                ${a.message ? `<p class="rd-app__msg">${escapeHtml(a.message)}</p>` : ''}${epk(a.epk)}
                ${c.status === 'open' && a.status !== 'declined' ? `<div class="bf-row bf-wrap" style="gap:.4rem;">
                    <button class="bf-btn bf-btn--sm bf-btn--primary" data-act="choose">${bfIco('check', 14)} Elegir</button>
                    ${a.status !== 'shortlisted' ? `<button class="bf-btn bf-btn--sm" data-act="shortlisted">Preseleccionar</button>` : ''}
                    <button class="bf-btn bf-btn--sm bf-btn--ghost" data-act="declined">Esta vez no</button></div>` : ''}
              </li>`).join('')}</ul>`
              : '<p class="bf-muted">Aún no hay candidaturas. Comparte la convocatoria para que llegue a más bandas.</p>',
            onMount: (root, close) => {
                root.querySelectorAll('[data-app]').forEach(li => li.querySelectorAll('[data-act]').forEach(b => b.addEventListener('click', async () => {
                    const aid = li.dataset.app;
                    try {
                        if (b.dataset.act === 'choose') {
                            if (!(await confirmModal('¿Elegir a esta banda? El concierto se añade a su agenda y las demás candidaturas reciben un «esta vez no».', { okText: 'Elegir' }))) return;
                            await apiJson(`/me/gig-calls/${c.id}/applications/${aid}/choose`, { method: 'POST' });
                            toast('¡Hecho! La banda ya lo tiene en su agenda.', 'success');
                            close(null); route();
                        } else {
                            await apiJson(`/me/gig-calls/${c.id}/applications/${aid}`, { method: 'PATCH', body: { status: b.dataset.act } });
                            close(null); applicationsDialog(c);
                        }
                    } catch (e) { toast(errorMessage(e), 'error'); }
                })));
            },
            actions: [{ label: 'Cerrar', value: null }],
        });
    }

    async function calendarDialog(p) {
        let items;
        try { items = await apiJson(`/me/pro-profiles/${p.id}/calendar`); }
        catch (e) { toast(errorMessage(e), 'error'); return; }
        await bfDialog({
            title: `Calendario · ${p.name}`,
            body: items.length ? `<ul class="setlist-list">${items.map(i => `<li class="setlist-song"><span class="sl-title">${escapeHtml(i.title)}
                <small>${i.date ? escapeHtml(bfDateLong(i.date)) : 'Sin fecha'}${i.band_name ? ' · ' + escapeHtml(i.band_name) : ''}</small></span>
                <span class="bf-badge${i.kind === 'gig' ? ' bf-badge--ok' : ''}">${i.kind === 'gig' ? 'Bolo cerrado' : (i.status === 'open' ? 'Buscando banda' : 'Cerrada')}</span></li>`).join('')}</ul>`
                : '<p class="bf-muted">Sin fechas todavía. Publica una convocatoria para llenar el calendario.</p>',
            actions: [{ label: 'Cerrar', value: null }],
        });
    }

    init();
})();
