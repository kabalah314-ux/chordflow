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


    let allEvents = [];
    let currentBand = 'all';
    let view = 'list';   // T-V6-62: 'list' | 'month' 

    function fmtDate(iso) { return bfDate(iso, 'Sin fecha'); }   // T-V6-36

    // Resumen discreto de confirmados ("✅ Ana, Luis · 🤔 2"); '' si nadie respondió. Nombres escapados.
    function attendeesText(e) {
        const att = Array.isArray(e.attendance) ? e.attendance : [];
        const html = bfAttendees(e);   // T-V6-34: iconos SVG en vez de emojis
        return html ? `<span class="ev-attendees" style="display:block;">${html}</span>` : '';
    }

    function eventRow(e) {
        return `<a class="bf-list-item" href="band.html?id=${encodeURIComponent(e.band_id)}"
                   style="text-decoration:none;color:inherit;">
            <span class="bf-badge">${escapeHtml(e.band_name)}</span>
            <span class="bf-grow">${bfEventIcon(e.type)} ${escapeHtml(e.title)}
                <span class="bf-faint">· ${escapeHtml(fmtDate(e.starts_at))}</span>
                ${attendeesText(e)}</span>
            ${e.my_status ? `<span class="bf-badge bf-badge--att">${attHtml(e.my_status, 12)}</span>` : ''}
        </a>`;
    }

    // T-V6-47: próximos agrupados por semana ("Esta semana", "La semana que viene", "Semana del 14 dic")
    function weekStart(d) { const x = new Date(d); x.setHours(0, 0, 0, 0); x.setDate(x.getDate() - ((x.getDay() + 6) % 7)); return x; }
    function groupByWeek(evs) {
        const thisW = weekStart(new Date()).getTime();
        const groups = [];
        evs.slice().sort((a, b) => new Date(a.starts_at) - new Date(b.starts_at)).forEach(e => {
            const w = weekStart(e.starts_at).getTime();
            let g = groups.find(x => x.w === w);
            if (!g) { g = { w, items: [] }; groups.push(g); }
            g.items.push(e);
        });
        const label = (w) => w === thisW ? 'Esta semana' : (w === thisW + 7 * 864e5 ? 'La semana que viene'
            : 'Semana del ' + new Date(w).toLocaleDateString(BF_LOCALE, { day: 'numeric', month: 'short' }));
        return groups.map(g => `<div class="agenda-week"><h3 class="agenda-week__title">${escapeHtml(label(g.w))}</h3>${g.items.map(eventRow).join('')}</div>`).join('');
    }

    // T-V6-47: crear un evento desde la agenda general eligiendo la banda (solo bandas donde soy admin)
    async function newEventAnyBand() {
        let bands = [];
        try { bands = (await apiJson('/bands/')).filter(b => b.role === 'admin'); } catch (e) { bands = []; }
        if (!bands.length) { toast('Solo un admin de la banda puede crear eventos.', 'info'); return; }
        const r = await bfDialog({
            title: 'Nuevo evento',
            body: `<div class="bf-stack">
                <div><label class="bf-label" for="ag-band">Banda</label><select class="bf-input" id="ag-band">${bands.map(b => `<option value="${escapeHtml(b.id)}">${escapeHtml(b.name)}</option>`).join('')}</select></div>
                <div class="bf-form-grid">
                  <div><label class="bf-label" for="ag-type">Tipo</label><select class="bf-input" id="ag-type"><option value="rehearsal">Ensayo</option><option value="concert">Concierto</option><option value="other">Otro</option></select></div>
                  <div><label class="bf-label" for="ag-when">Fecha y hora</label><input class="bf-input" type="datetime-local" id="ag-when"></div>
                </div>
                <div><label class="bf-label" for="ag-title">Título</label><input class="bf-input" id="ag-title" maxlength="255" placeholder="Ensayo general" autofocus></div>
                <div><label class="bf-label" for="ag-loc">Lugar</label><input class="bf-input" id="ag-loc" maxlength="255"></div>
              </div>`,
            actions: [{ label: 'Cancelar', value: null }, { label: 'Crear', primary: true, onClick: (root) => {
                const title = root.querySelector('#ag-title').value.trim();
                if (!title) { toast('Pon un título.', 'error'); return false; }
                return { band: root.querySelector('#ag-band').value, body: { type: root.querySelector('#ag-type').value, title,
                    starts_at: bfFromLocalInput(root.querySelector('#ag-when').value), location: root.querySelector('#ag-loc').value.trim() || null } };
            } }],
        });
        if (!r) return;
        try { await apiJson(`/bands/${encodeURIComponent(r.band)}/events/`, { method: 'POST', body: r.body }); toast('Evento creado. La banda recibirá un aviso.', 'success'); load(); }
        catch (e) { toast(errorMessage(e, 'No se pudo crear el evento.'), 'error'); }
    }

    function render() {
        if (!allEvents.length) {
            el.innerHTML = `
                <div class="bf-stack">
                    <div><h1 class="bf-h1">Agenda</h1></div>
                    <div class="bf-card">${bfEmpty('calendar', 'Tu agenda está vacía',
                        'No tienes eventos en ninguna banda. Entra en una banda para crear ensayos o conciertos.',
                        { cta: { label: 'Ir a Bandas', href: 'bands.html' } })}</div>
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
        const chips = chip('all', 'Todas') + bands.map(([id, name]) => chip(id, name)).join('');

        el.innerHTML = `
            <div class="bf-stack">
                <div class="bf-row bf-row--between bf-wrap" style="gap:.5rem;">
                    <div><h1 class="bf-h1">Agenda</h1>
                    <p class="bf-muted">Ensayos y conciertos de todas tus bandas.</p></div>
                    <div class="bf-row bf-wrap" style="gap:.4rem;">
                        <div class="bf-segmented" role="group" aria-label="Vista">
                            <button class="bf-btn bf-btn--sm${view === 'list' ? ' bf-btn--primary' : ''}" data-view="list" aria-pressed="${view === 'list'}">${bfIco('list', 14)} Lista</button>
                            <button class="bf-btn bf-btn--sm${view === 'month' ? ' bf-btn--primary' : ''}" data-view="month" aria-pressed="${view === 'month'}">${bfIco('calendar', 14)} Mes</button>
                        </div>
                        <button class="bf-btn bf-btn--sm" id="agenda-subscribe">${bfIco('calendar', 14)} En mi calendario</button>
                        <button class="bf-btn bf-btn--sm bf-btn--primary" id="agenda-new">${bfIco('plus', 14)} Nuevo evento</button>
                    </div>
                </div>
                <div class="bf-row bf-wrap" id="agenda-filters">${chips}</div>
                ${view === 'month' ? '<div class="bf-card" id="agenda-month"></div>' : ''}
                <div class="bf-card"${view === 'month' ? ' hidden' : ''}>
                    <h2 class="bf-h3" style="margin-bottom:.75rem;">Próximos</h2>
                    ${upcoming.length
                        ? `<div class="bf-list" id="agenda-upcoming">${groupByWeek(upcoming)}</div>`
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
        el.querySelectorAll('[data-view]').forEach(b => b.addEventListener('click', () => { view = b.dataset.view; render(); }));
        el.querySelector('#agenda-subscribe').addEventListener('click', () => bfSubscribeCalendar());
        el.querySelector('#agenda-new').addEventListener('click', newEventAnyBand);
        const month = el.querySelector('#agenda-month');
        if (month) bfCalendar(month, base.map(e => ({ ...e, href: `band.html?id=${encodeURIComponent(e.band_id)}` })));
    }

    async function load() {
        if (!(await requireAuth())) return;
        el.innerHTML = bfSkeletonList(4);   // skeleton mientras carga (T-135)
        try {
            const r = await apiFetch('/me/events');
            if (!r.ok) throw new Error('http');
            allEvents = await r.json();
        } catch (e) {
            el.innerHTML = '<p class="bf-muted">No se pudo cargar la agenda. Inténtalo de nuevo.</p>';
            return;
        }
        render();
    }

    load();
})();
