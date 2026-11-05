/**
 * band_tools.js — Funciones de banda V6-F9 sobre el espacio de banda (band.html).
 *
 *  · Semáforo del repertorio (T-V6-83): marcador por canción en Repertorio + progreso en Resumen.
 *  · Pizarra (T-V6-92): pendientes compartidos con responsable/fecha, widget en Resumen.
 *  · Votación de fechas (T-V6-82): bloque en Agenda; enlace público votar.html para quien no
 *    tenga cuenta; "Confirmar" crea el evento con las asistencias ya rellenas.
 *  · Hoja del bolo (T-V6-86): horarios, dirección, backline, checklist y enlace de solo lectura.
 *
 * No toca bands.js por dentro: escucha `bf:repertoire` / `bf:agenda` (que bands.js emite al
 * terminar de pintar) y band.js llama a `BandTools.summary(...)`. Todo texto de usuario se escapa.
 */
(function () {
    const BT = {};
    window.BandTools = BT;

    const ST = {
        pending:   { label: 'No me la sé', short: 'Pendiente', icon: 'alert-circle' },
        improving: { label: 'Mejorando',   short: 'Mejorando', icon: 'clock' },
        mastered:  { label: 'La domino',   short: 'Dominada',  icon: 'check-circle' },
    };
    const ST_ORDER = ['pending', 'improving', 'mastered'];

    let membersCache = { bandId: null, list: [] };
    async function members(bandId) {
        if (membersCache.bandId === bandId) return membersCache.list;
        try {
            const res = await apiFetch(`/bands/${bandId}/members`);
            const list = res.ok ? (await res.json()).filter(m => m.status === 'active') : [];
            membersCache = { bandId, list };
        } catch (e) { membersCache = { bandId, list: [] }; }
        return membersCache.list;
    }
    function memberOptions(list, selected) {
        return `<option value="">— Sin responsable —</option>` + list.map(m =>
            `<option value="${escapeHtml(m.user_id)}"${m.user_id === selected ? ' selected' : ''}>${escapeHtml(m.display_name || 'Miembro')}${m.is_me ? ' (yo)' : ''}</option>`).join('');
    }
    async function jsonOrThrow(res) {
        if (!res.ok) {
            let msg = 'http';
            try { msg = (await res.json()).detail || msg; } catch (e) { /* sin cuerpo */ }
            throw new Error(typeof msg === 'string' ? msg : 'http');
        }
        return res.status === 204 ? null : res.json();
    }
    const J = (method, body) => ({ method, headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) });

    // ══ Semáforo ══════════════════════════════════════════════════════════════
    function progressBar(t, total) {
        const n = Math.max(total, 1);
        const pct = (k) => Math.round(((t[k] || 0) / n) * 100);
        return `<div class="bt-progress" role="img" aria-label="${t.mastered || 0} dominadas, ${t.improving || 0} mejorando, ${t.pending || 0} pendientes">
            <span class="bt-progress__seg bt-st--mastered" style="width:${pct('mastered')}%"></span>
            <span class="bt-progress__seg bt-st--improving" style="width:${pct('improving')}%"></span>
            <span class="bt-progress__seg bt-st--pending" style="width:${pct('pending')}%"></span>
        </div>
        <div class="bt-legend">${ST_ORDER.slice().reverse().map(k => `<span><i class="bt-dot bt-st--${k}"></i>${ST[k].short} ${t[k] || 0}</span>`).join('')}</div>`;
    }

    async function decorateRepertoire(bandId) {
        const list = document.getElementById('b-repertoire');
        if (!list) return;
        let board;
        try { board = await jsonOrThrow(await apiFetch(`/bands/${bandId}/song-status`)); }
        catch (e) { return; }
        const mine = Object.fromEntries((board.mine || []).map(r => [r.song_id, r]));
        // Barra de "cómo llevo el repertorio" sobre la lista
        let head = document.getElementById('bt-rep-progress');
        if (!head) {
            head = document.createElement('div');
            head.id = 'bt-rep-progress';
            head.className = 'bt-rep-progress';
            list.parentNode.insertBefore(head, list);
        }
        head.innerHTML = `<div class="bf-row bf-row--between bf-wrap"><strong>Cómo llevo el repertorio</strong>
            <label class="bf-faint bt-share-toggle"><input type="checkbox" id="bt-share-all"> Compartir mi progreso con la banda</label></div>
            ${progressBar(board.totals_mine || {}, board.songs_total || 0)}`;
        const anyShared = (board.mine || []).some(r => r.shared);
        const chk = head.querySelector('#bt-share-all');
        chk.checked = anyShared;
        chk.addEventListener('change', async () => {
            // Comparte (o deja de compartir) todos mis marcadores de una vez.
            try {
                await Promise.all((board.mine || []).map(r => apiFetch(`/bands/${bandId}/songs/${r.song_id}/status`,
                    J('PUT', { status: r.status, shared: chk.checked }))));
                toast(chk.checked ? 'Tu progreso ahora lo ve la banda.' : 'Tu progreso vuelve a ser privado.', 'success');
            } catch (e) { toast('No se pudo cambiar.', 'error'); }
        });

        list.querySelectorAll('.setlist-song[data-id]').forEach(li => {
            if (li.querySelector('.bt-status')) return;
            const sid = li.dataset.id;
            const cur = (mine[sid] || {}).status || 'pending';
            const btn = document.createElement('button');
            btn.className = `setlist-item-btn bt-status bt-st--${cur}`;
            btn.dataset.status = cur;
            const paint = (s) => {
                btn.className = `setlist-item-btn bt-status bt-st--${s}`;
                btn.dataset.status = s;
                btn.title = `${ST[s].label} (pulsa para cambiar)`;
                btn.setAttribute('aria-label', `Mi preparación: ${ST[s].label}. Cambiar`);
                btn.innerHTML = `<i class="bt-dot bt-st--${s}"></i><span class="bt-status__txt">${ST[s].short}</span>`;
            };
            paint(cur);
            btn.addEventListener('click', async (ev) => {
                ev.stopPropagation();
                const next = ST_ORDER[(ST_ORDER.indexOf(btn.dataset.status) + 1) % 3];
                const prev = btn.dataset.status;
                paint(next);
                try {
                    const r = await jsonOrThrow(await apiFetch(`/bands/${bandId}/songs/${sid}/status`,
                        J('PUT', { status: next, shared: chk.checked || undefined })));
                    mine[sid] = r;
                    if (!board.mine.find(x => x.song_id === sid)) board.mine.push(r);
                    else board.mine = board.mine.map(x => x.song_id === sid ? r : x);
                    const t = { pending: 0, improving: 0, mastered: 0 };
                    list.querySelectorAll('.bt-status').forEach(b => { t[b.dataset.status]++; });
                    const bar = head.querySelector('.bt-progress');
                    const legend = head.querySelector('.bt-legend');
                    const tmp = document.createElement('div');
                    tmp.innerHTML = progressBar(t, board.songs_total || 0);
                    bar.replaceWith(tmp.firstElementChild);
                    legend.replaceWith(tmp.lastElementChild);
                } catch (e) { paint(prev); toast('No se pudo guardar.', 'error'); }
            });
            const play = li.querySelector('[data-act="play"]');
            li.insertBefore(btn, play || null);
        });
    }
    document.addEventListener('bf:repertoire', (e) => decorateRepertoire(e.detail.bandId));

    // ══ Pizarra ═══════════════════════════════════════════════════════════════
    function noteRow(n, ctx) {
        const due = n.due_date ? `<span class="bf-badge">${bfIco('calendar', 12)} ${escapeHtml(bfDate(n.due_date))}</span>` : '';
        const who = n.assignee_name ? `<span class="bf-faint">→ ${escapeHtml(n.assignee_name)}</span>` : '';
        return `<li class="bt-note${n.done_at ? ' is-done' : ''}${n.is_pinned ? ' is-pinned' : ''}" data-note="${escapeHtml(n.id)}">
            <button class="bt-note__check" data-act="done" aria-label="${n.done_at ? 'Marcar como pendiente' : 'Marcar como hecho'}" ${ctx.iAmGuest ? 'disabled' : ''}>${n.done_at ? bfIco('check-circle', 18) : '<i class="bt-circle"></i>'}</button>
            <div class="bt-note__body">
                <div class="bt-note__text">${n.is_pinned ? bfIco('pin', 12) + ' ' : ''}${escapeHtml(n.body)}</div>
                <div class="bt-note__meta">${due}${who}<span class="bf-faint">${escapeHtml(n.author_name || '')}</span></div>
            </div>
            ${ctx.iAmGuest ? '' : `<button class="bf-icon-btn" data-act="edit" aria-label="Editar nota">${bfIco('edit', 15)}</button>`}
        </li>`;
    }

    async function renderBoard(bandId, ctx, box, showDone = false) {
        let notes = [];
        try { notes = await jsonOrThrow(await apiFetch(`/bands/${bandId}/notes${showDone ? '?include_done=true' : ''}`)); }
        catch (e) { box.innerHTML = '<p class="bf-muted">No se pudo cargar la pizarra.</p>'; return; }
        box.innerHTML = `
            <div class="bf-row bf-row--between"><h3 class="bf-h3">${bfIco('note', 18)} Pizarra</h3>
              <label class="bf-faint" style="font-size:var(--bf-fs-xs);"><input type="checkbox" id="bt-show-done" ${showDone ? 'checked' : ''}> Ver hechas</label></div>
            ${ctx.iAmGuest ? '' : `<form class="bt-note-add" id="bt-note-add">
                <input class="bf-input" id="bt-note-input" maxlength="2000" placeholder="Apunta algo: «ensayar el puente de…», «comprar cuerdas»" aria-label="Nueva nota">
                <button class="bf-btn bf-btn--primary bf-btn--sm" type="submit">${bfIco('plus', 15)} Añadir</button>
              </form>`}
            ${notes.length ? `<ul class="bt-notes">${notes.map(n => noteRow(n, ctx)).join('')}</ul>`
                           : `<p class="bf-muted" style="margin-top:.4rem;">Nada pendiente. ${ctx.iAmGuest ? '' : 'Lo que apuntéis aquí lo ve toda la banda.'}</p>`}`;
        const byId = Object.fromEntries(notes.map(n => [n.id, n]));
        box.querySelector('#bt-show-done').addEventListener('change', (e) => renderBoard(bandId, ctx, box, e.target.checked));
        const form = box.querySelector('#bt-note-add');
        if (form) form.addEventListener('submit', async (e) => {
            e.preventDefault();
            const inp = box.querySelector('#bt-note-input');
            const body = inp.value.trim();
            if (!body) return;
            try {
                await jsonOrThrow(await apiFetch(`/bands/${bandId}/notes`, J('POST', { body })));
                renderBoard(bandId, ctx, box, showDone);
            } catch (err) { toast('No se pudo guardar la nota.', 'error'); }
        });
        box.querySelectorAll('[data-note]').forEach(li => {
            const n = byId[li.dataset.note];
            const done = li.querySelector('[data-act="done"]');
            if (done && !done.disabled) done.addEventListener('click', async () => {
                try {
                    await jsonOrThrow(await apiFetch(`/bands/${bandId}/notes/${n.id}`, J('PATCH', { done: !n.done_at })));
                    renderBoard(bandId, ctx, box, showDone);
                } catch (e) { toast('No se pudo actualizar.', 'error'); }
            });
            const ed = li.querySelector('[data-act="edit"]');
            if (ed) ed.addEventListener('click', () => editNote(bandId, ctx, n, () => renderBoard(bandId, ctx, box, showDone)));
        });
    }

    async function editNote(bandId, ctx, n, after) {
        const list = await members(bandId);
        const r = await bfDialog({
            title: 'Editar nota',
            body: `<div class="bf-stack">
                <div><label class="bf-label" for="bt-n-body">Texto</label>
                  <textarea class="bf-textarea" id="bt-n-body" rows="3" maxlength="2000">${escapeHtml(n.body)}</textarea></div>
                <div class="bf-form-grid">
                  <div><label class="bf-label" for="bt-n-who">Responsable</label>
                    <select class="bf-input" id="bt-n-who">${memberOptions(list, n.assignee_id)}</select></div>
                  <div><label class="bf-label" for="bt-n-due">Fecha (opcional)</label>
                    <input class="bf-input" type="datetime-local" id="bt-n-due" value="${escapeHtml(bfLocalInput(n.due_date))}"></div>
                </div>
                <label><input type="checkbox" id="bt-n-pin" ${n.is_pinned ? 'checked' : ''}> Fijar arriba</label>
              </div>`,
            actions: [
                { label: 'Borrar', value: 'delete', danger: true },
                { label: 'Cancelar', value: null },
                { label: 'Guardar', primary: true, onClick: (root) => ({
                    body: root.querySelector('#bt-n-body').value.trim(),
                    assignee_id: root.querySelector('#bt-n-who').value || null,
                    due_date: bfFromLocalInput(root.querySelector('#bt-n-due').value),
                    is_pinned: root.querySelector('#bt-n-pin').checked,
                }) },
            ],
        });
        if (!r) return;
        try {
            if (r === 'delete') {
                await jsonOrThrow(await apiFetch(`/bands/${bandId}/notes/${n.id}`, { method: 'DELETE' }));
            } else {
                if (!r.body) { toast('La nota no puede quedar vacía.', 'error'); return; }
                await jsonOrThrow(await apiFetch(`/bands/${bandId}/notes/${n.id}`, J('PATCH', r)));
            }
            after();
        } catch (e) { toast(e.message && e.message !== 'http' ? e.message : 'No se pudo guardar.', 'error'); }
    }

    // ══ Resumen: pizarra + preparación ════════════════════════════════════════
    BT.summary = async function (bandId, ctx, el) {
        if (!el) return;
        let wrap = el.querySelector('#bt-summary');
        if (!wrap) {
            wrap = document.createElement('div');
            wrap.id = 'bt-summary';
            wrap.className = 'bs-summary bt-summary';
            wrap.innerHTML = `<div class="bs-summary__col"><div class="bf-card" id="bt-board"></div></div>
                              <div class="bs-summary__col"><div class="bf-card bf-stack" id="bt-prep"></div><div class="bf-card bf-stack" id="bt-polls-mini" hidden></div></div>`;
            el.appendChild(wrap);
        }
        renderBoard(bandId, ctx, wrap.querySelector('#bt-board'));
        const prep = wrap.querySelector('#bt-prep');
        try {
            const b = await jsonOrThrow(await apiFetch(`/bands/${bandId}/song-status`));
            prep.innerHTML = `<h3 class="bf-h3">Preparación del repertorio</h3>
                ${b.songs_total ? `<p class="bf-faint" style="font-size:.8rem;">Tú</p>${progressBar(b.totals_mine, b.songs_total)}
                <p class="bf-faint" style="font-size:.8rem;margin-top:.5rem;">La banda (lo compartido)</p>${progressBar(b.totals_band, Object.values(b.totals_band).reduce((a, c) => a + c, 0))}
                <div><button class="bf-btn bf-btn--sm" data-go-tab="repertorio">Marcar canciones →</button></div>`
                : '<p class="bf-muted">Cuando haya canciones en el repertorio, aquí verás cuántas os sabéis.</p>'}`;
            const go = prep.querySelector('[data-go-tab]');
            if (go) go.addEventListener('click', () => { const t = document.querySelector('.bf-tab[data-tab="repertorio"]'); if (t) t.click(); });
        } catch (e) { prep.innerHTML = '<p class="bf-muted">No se pudo cargar la preparación.</p>'; }
        // Votaciones abiertas (atajo a la agenda)
        try {
            const polls = (await jsonOrThrow(await apiFetch(`/bands/${bandId}/polls`))).filter(p => p.status === 'open');
            const mini = wrap.querySelector('#bt-polls-mini');
            if (polls.length) {
                mini.hidden = false;
                mini.innerHTML = `<h3 class="bf-h3">${bfIco('calendar', 18)} Votaciones abiertas</h3>
                    <ul class="bt-mini-list">${polls.map(p => `<li>${escapeHtml(p.title)} <span class="bf-faint">· faltan ${p.pending.length}</span></li>`).join('')}</ul>
                    <div><button class="bf-btn bf-btn--sm" data-go-agenda>Votar en la Agenda →</button></div>`;
                mini.querySelector('[data-go-agenda]').addEventListener('click', () => { const t = document.querySelector('.bf-tab[data-tab="agenda"]'); if (t) t.click(); });
            }
        } catch (e) { /* opcional */ }
    };

    // ══ Votación de fechas ════════════════════════════════════════════════════
    function pollUrl(p) { return `${location.origin}/static/votar.html?t=${encodeURIComponent(p.token)}`; }
    const ATT_TXT = { yes: 'Sí', maybe: 'Quizás', no: 'No' };

    function pollCard(p, me, ctx) {
        const canClose = p.status === 'open' && !ctx.iAmGuest;
        const best = p.options.reduce((a, o) => (!a || o.yes * 2 + o.maybe > a.yes * 2 + a.maybe) ? o : a, null);
        return `<div class="bf-card bt-poll" data-poll="${escapeHtml(p.id)}">
            <div class="bf-row bf-row--between bf-wrap">
                <div><strong>${bfEventIcon(p.type, 16)} ${escapeHtml(p.title)}</strong>
                    ${p.status === 'closed' ? '<span class="bf-badge">Cerrada</span>' : `<span class="bf-faint"> · faltan ${p.pending.length}${p.pending.length ? ': ' + escapeHtml(p.pending.join(', ')) : ''}</span>`}</div>
                ${p.status === 'open' ? `<button class="bf-btn bf-btn--sm" data-act="share">${bfIco('share', 14)} Compartir</button>` : ''}
            </div>
            <table class="bt-poll__table"><tbody>
            ${p.options.map(o => `<tr data-opt="${escapeHtml(o.id)}"${best && o.id === best.id && p.status === 'open' ? ' class="is-best"' : ''}>
                <th scope="row">${escapeHtml(bfDate(o.starts_at))}</th>
                <td class="bt-poll__counts"><span class="ev-going">${bfIco('check', 12)} ${o.yes}</span> <span class="ev-maybe">${bfIco('help-circle', 12)} ${o.maybe}</span></td>
                <td class="bt-poll__mine">${p.status === 'open' ? ['yes', 'maybe', 'no'].map(s =>
                    `<button class="setlist-item-btn att-btn${o.votes[me] === s ? ' active' : ''}" data-vote="${s}" aria-label="${ATT_TXT[s]} para ${escapeHtml(bfDate(o.starts_at))}">${ATT_TXT[s]}</button>`).join('')
                    : (o.votes[me] ? ATT_TXT[o.votes[me]] : '')}</td>
                ${canClose ? `<td><button class="bf-btn bf-btn--sm" data-act="confirm">Confirmar</button></td>` : ''}
            </tr>`).join('')}
            </tbody></table>
            ${p.status === 'closed' && p.event_id ? '<p class="bf-faint" style="font-size:.8rem;">Convertida en evento de la agenda.</p>' : ''}
        </div>`;
    }

    async function loadPolls(bandId, ctx) {
        const box = document.getElementById('bt-polls');
        if (!box) return;
        let polls = [], list = [];
        try {
            [polls, list] = await Promise.all([jsonOrThrow(await apiFetch(`/bands/${bandId}/polls`)), members(bandId)]);
        } catch (e) { box.innerHTML = '<p class="bf-muted">No se pudieron cargar las votaciones.</p>'; return; }
        const me = (list.find(m => m.is_me) || {}).user_id;
        const open = polls.filter(p => p.status === 'open');
        const closed = polls.filter(p => p.status !== 'open').slice(0, 3);
        box.innerHTML = `
            <div class="bf-row bf-row--between" style="margin-bottom:.5rem;">
                <h3 class="bf-h3">Votar fechas</h3>
                ${ctx.iAmGuest ? '' : `<button class="bf-btn bf-btn--sm bf-btn--primary" id="bt-new-poll">${bfIco('plus', 15)} Proponer fechas</button>`}
            </div>
            ${open.length ? open.map(p => pollCard(p, me, ctx)).join('') : '<p class="bf-muted">¿No sabéis qué día ensayar? Propón varias fechas y que cada uno vote (también por WhatsApp, sin cuenta).</p>'}
            ${closed.length ? `<details class="bt-closed"><summary class="bf-faint">Votaciones cerradas</summary>${closed.map(p => pollCard(p, me, ctx)).join('')}</details>` : ''}`;
        const nb = box.querySelector('#bt-new-poll');
        if (nb) nb.addEventListener('click', () => newPoll(bandId, ctx));
        const byId = Object.fromEntries(polls.map(p => [p.id, p]));
        box.querySelectorAll('[data-poll]').forEach(card => {
            const p = byId[card.dataset.poll];
            const sh = card.querySelector('[data-act="share"]');
            if (sh) sh.addEventListener('click', () => bfShare({ title: p.title, text: `Vota qué día te va para «${p.title}»:`, url: pollUrl(p) }));
            card.querySelectorAll('[data-opt]').forEach(tr => {
                const oid = tr.dataset.opt;
                tr.querySelectorAll('[data-vote]').forEach(b => b.addEventListener('click', async () => {
                    try {
                        await jsonOrThrow(await apiFetch(`/bands/${bandId}/polls/${p.id}/votes`,
                            J('PUT', { votes: [{ option_id: oid, status: b.dataset.vote }] })));
                        loadPolls(bandId, ctx);
                    } catch (e) { toast('No se pudo guardar tu voto.', 'error'); }
                }));
                const cf = tr.querySelector('[data-act="confirm"]');
                if (cf) cf.addEventListener('click', async () => {
                    const opt = p.options.find(o => o.id === oid);
                    const ok = await confirmModal(`¿Confirmar «${p.title}» el ${bfDate(opt.starts_at)}? Se crea el evento y se cierra la votación.`, { okText: 'Confirmar' });
                    if (!ok) return;
                    try {
                        await jsonOrThrow(await apiFetch(`/bands/${bandId}/polls/${p.id}/confirm`, J('POST', { option_id: oid })));
                        toast('Evento creado en la agenda.', 'success');
                        loadPolls(bandId, ctx);
                        if (typeof loadAgenda === 'function') loadAgenda(bandId, ctx.iAmAdmin);
                    } catch (e) { toast(e.message && e.message !== 'http' ? e.message : 'No se pudo confirmar.', 'error'); }
                });
            });
        });
    }

    async function newPoll(bandId, ctx) {
        const optRow = (v = '') => `<div class="bt-opt-row"><input class="bf-input" type="datetime-local" value="${escapeHtml(v)}" aria-label="Fecha y hora"><button type="button" class="bf-icon-btn" data-rm aria-label="Quitar fecha">${bfIco('x', 15)}</button></div>`;
        const r = await bfDialog({
            title: 'Proponer fechas',
            body: `<div class="bf-stack">
                <div><label class="bf-label" for="bt-p-title">¿Para qué?</label>
                  <input class="bf-input" id="bt-p-title" maxlength="255" placeholder="Ensayo antes del bolo" autofocus></div>
                <div class="bf-form-grid">
                  <div><label class="bf-label" for="bt-p-type">Tipo</label>
                    <select class="bf-input" id="bt-p-type"><option value="rehearsal">Ensayo</option><option value="concert">Concierto</option><option value="other">Otro</option></select></div>
                  <div><label class="bf-label" for="bt-p-loc">Lugar (opcional)</label>
                    <input class="bf-input" id="bt-p-loc" maxlength="255"></div>
                </div>
                <div><span class="bf-label">Fechas posibles</span><div id="bt-p-opts">${optRow()}${optRow()}</div>
                  <button type="button" class="bf-btn bf-btn--sm" id="bt-p-more">${bfIco('plus', 14)} Otra fecha</button></div>
              </div>`,
            onMount: (root) => {
                const opts = root.querySelector('#bt-p-opts');
                root.querySelector('#bt-p-more').addEventListener('click', () => {
                    if (opts.children.length >= 20) return;
                    opts.insertAdjacentHTML('beforeend', optRow());
                });
                opts.addEventListener('click', (e) => {
                    const rm = e.target.closest('[data-rm]');
                    if (rm && opts.children.length > 1) rm.parentElement.remove();
                });
            },
            actions: [
                { label: 'Cancelar', value: null },
                { label: 'Crear votación', primary: true, onClick: (root) => {
                    const title = root.querySelector('#bt-p-title').value.trim();
                    const options = [...root.querySelectorAll('#bt-p-opts input')].map(i => i.value).filter(Boolean)
                        .map(v => ({ starts_at: bfFromLocalInput(v) }));
                    if (!title || !options.length) { toast('Pon un título y al menos una fecha.', 'error'); return false; }
                    return { title, type: root.querySelector('#bt-p-type').value,
                             location: root.querySelector('#bt-p-loc').value.trim() || null, options };
                } },
            ],
        });
        if (!r) return;
        try {
            const p = await jsonOrThrow(await apiFetch(`/bands/${bandId}/polls`, J('POST', r)));
            loadPolls(bandId, ctx);
            bfShare({ title: p.title, text: `Vota qué día te va para «${p.title}»:`, url: pollUrl(p) });
        } catch (e) { toast('No se pudo crear la votación.', 'error'); }
    }

    // ══ Hoja del bolo ═════════════════════════════════════════════════════════
    async function openSheet(bandId, eid, ctx) {
        let ev, items, list;
        try {
            [ev, items, list] = await Promise.all([
                jsonOrThrow(await apiFetch(`/bands/${bandId}/events/${eid}`)),
                jsonOrThrow(await apiFetch(`/bands/${bandId}/events/${eid}/checklist`)),
                members(bandId)]);
        } catch (e) { toast('No se pudo abrir la hoja del bolo.', 'error'); return; }
        const names = Object.fromEntries(list.map(m => [m.user_id, m.display_name || 'Miembro']));
        const ro = !ctx.iAmAdmin;
        const f = (id, label, val, type = 'datetime-local') => `<div><label class="bf-label" for="${id}">${label}</label>
            <input class="bf-input" type="${type}" id="${id}" value="${escapeHtml(type === 'datetime-local' ? bfLocalInput(val) : (val || ''))}" ${ro ? 'disabled' : ''}></div>`;
        const itemRow = (it) => `<li class="bt-note${it.done_at ? ' is-done' : ''}" data-item="${escapeHtml(it.id)}">
            <button class="bt-note__check" data-act="toggle" aria-label="${it.done_at ? 'Desmarcar' : 'Marcar hecho'}" ${ctx.iAmGuest ? 'disabled' : ''}>${it.done_at ? bfIco('check-circle', 18) : '<i class="bt-circle"></i>'}</button>
            <div class="bt-note__body"><div class="bt-note__text">${escapeHtml(it.text)}</div>${it.assignee_id ? `<div class="bt-note__meta bf-faint">→ ${escapeHtml(names[it.assignee_id] || '')}</div>` : ''}</div>
            ${ctx.iAmGuest ? '' : `<button class="bf-icon-btn" data-act="rm" aria-label="Quitar">${bfIco('x', 15)}</button>`}
        </li>`;
        const r = await bfDialog({
            title: `Hoja del bolo · ${ev.title}`,
            wide: true,
            body: `<div class="bf-stack">
                <div class="bf-form-grid">
                    ${f('bt-s-load', 'Carga / llegada', ev.load_in_at)}
                    ${f('bt-s-sound', 'Prueba de sonido', ev.soundcheck_at)}
                    ${f('bt-s-doors', 'Apertura de puertas', ev.doors_at)}
                    ${f('bt-s-set', 'Salimos a tocar', ev.set_at || ev.starts_at)}
                </div>
                ${f('bt-s-addr', 'Dirección', ev.address || ev.location || '', 'text')}
                <div><label class="bf-label" for="bt-s-park">Aparcamiento / acceso</label>
                    <textarea class="bf-textarea" id="bt-s-park" rows="2" ${ro ? 'disabled' : ''}>${escapeHtml(ev.parking_notes || '')}</textarea></div>
                <div><label class="bf-label" for="bt-s-back">Backline / técnica</label>
                    <textarea class="bf-textarea" id="bt-s-back" rows="2" ${ro ? 'disabled' : ''} placeholder="Qué pone la sala, qué llevamos nosotros">${escapeHtml(ev.backline_notes || '')}</textarea></div>
                <div>
                    <span class="bf-label">Checklist</span>
                    <ul class="bt-notes" id="bt-s-items">${items.map(itemRow).join('') || ''}</ul>
                    ${ctx.iAmGuest ? '' : `<div class="bt-note-add">
                        <input class="bf-input" id="bt-s-newitem" maxlength="255" placeholder="Llevar DI, cable de repuesto…" aria-label="Nuevo elemento">
                        <select class="bf-input" id="bt-s-newwho" aria-label="Responsable" style="max-width:12rem;">${memberOptions(list, null)}</select>
                        <button type="button" class="bf-btn bf-btn--sm" id="bt-s-additem">${bfIco('plus', 14)} Añadir</button></div>`}
                </div>
                ${ctx.iAmAdmin ? `<div class="bf-row bf-wrap" style="gap:.5rem;">
                    <button type="button" class="bf-btn bf-btn--sm" id="bt-s-share">${bfIco('share', 14)} Compartir hoja (solo lectura)</button>
                    ${ev.sheet_token ? `<button type="button" class="bf-btn bf-btn--sm bf-btn--ghost" id="bt-s-revoke">Desactivar enlace</button>` : ''}
                  </div>` : ''}
              </div>`,
            onMount: (root) => {
                const ul = root.querySelector('#bt-s-items');
                const wireItems = () => ul.querySelectorAll('[data-item]').forEach(li => {
                    if (li.dataset.wired) return; li.dataset.wired = '1';
                    const iid = li.dataset.item;
                    const tg = li.querySelector('[data-act="toggle"]');
                    if (tg && !tg.disabled) tg.addEventListener('click', async () => {
                        try {
                            const it = await jsonOrThrow(await apiFetch(`/bands/${bandId}/events/${eid}/checklist/${iid}`,
                                J('PATCH', { done: !li.classList.contains('is-done') })));
                            li.outerHTML = itemRow(it); wireItems();
                        } catch (e) { toast('No se pudo actualizar.', 'error'); }
                    });
                    const rm = li.querySelector('[data-act="rm"]');
                    if (rm) rm.addEventListener('click', async () => {
                        try {
                            await jsonOrThrow(await apiFetch(`/bands/${bandId}/events/${eid}/checklist/${iid}`, { method: 'DELETE' }));
                            li.remove();
                        } catch (e) { toast('No se pudo quitar.', 'error'); }
                    });
                });
                wireItems();
                const add = root.querySelector('#bt-s-additem');
                const addItem = async () => {
                    const inp = root.querySelector('#bt-s-newitem');
                    const text = inp.value.trim();
                    if (!text) return;
                    try {
                        const it = await jsonOrThrow(await apiFetch(`/bands/${bandId}/events/${eid}/checklist`,
                            J('POST', { text, assignee_id: root.querySelector('#bt-s-newwho').value || null })));
                        ul.insertAdjacentHTML('beforeend', itemRow(it)); wireItems();
                        inp.value = ''; inp.focus();
                    } catch (e) { toast('No se pudo añadir.', 'error'); }
                };
                if (add) {
                    add.addEventListener('click', addItem);
                    root.querySelector('#bt-s-newitem').addEventListener('keydown', (e) => { if (e.key === 'Enter') { e.preventDefault(); addItem(); } });
                }
                const sh = root.querySelector('#bt-s-share');
                if (sh) sh.addEventListener('click', async () => {
                    try {
                        const t = await jsonOrThrow(await apiFetch(`/bands/${bandId}/events/${eid}/sheet-token`, { method: 'POST' }));
                        bfShare({ title: `Hoja del bolo · ${ev.title}`, text: `Horarios y detalles de «${ev.title}»:`,
                                  url: `${location.origin}/static/bolo.html?t=${encodeURIComponent(t.token)}` });
                    } catch (e) { toast('No se pudo crear el enlace.', 'error'); }
                });
                const rv = root.querySelector('#bt-s-revoke');
                if (rv) rv.addEventListener('click', async () => {
                    try {
                        await jsonOrThrow(await apiFetch(`/bands/${bandId}/events/${eid}/sheet-token`, { method: 'DELETE' }));
                        rv.remove(); toast('Enlace desactivado.', 'success');
                    } catch (e) { toast('No se pudo desactivar.', 'error'); }
                });
            },
            actions: ro ? [{ label: 'Cerrar', value: null }] : [
                { label: 'Cerrar', value: null },
                { label: 'Guardar horarios', primary: true, onClick: (root) => ({
                    load_in_at: bfFromLocalInput(root.querySelector('#bt-s-load').value),
                    soundcheck_at: bfFromLocalInput(root.querySelector('#bt-s-sound').value),
                    doors_at: bfFromLocalInput(root.querySelector('#bt-s-doors').value),
                    set_at: bfFromLocalInput(root.querySelector('#bt-s-set').value),
                    address: root.querySelector('#bt-s-addr').value.trim() || null,
                    parking_notes: root.querySelector('#bt-s-park').value.trim() || null,
                    backline_notes: root.querySelector('#bt-s-back').value.trim() || null,
                }) },
            ],
        });
        if (!r || ro) return;
        try {
            await jsonOrThrow(await apiFetch(`/bands/${bandId}/events/${eid}`, J('PATCH', r)));
            toast('Hoja del bolo guardada.', 'success');
        } catch (e) { toast('No se pudo guardar la hoja.', 'error'); }
    }
    BT.openSheet = openSheet;

    // La Agenda de banda: bloque de votaciones + botón "Hoja" en cada evento.
    document.addEventListener('bf:agenda', (e) => {
        const bandId = e.detail.bandId;
        const ctx = BT.ctx || { iAmAdmin: !!e.detail.iAmAdmin, iAmGuest: false };
        const agenda = document.getElementById('b-agenda');
        if (!agenda) return;
        let box = document.getElementById('bt-polls');
        if (!box) {
            box = document.createElement('div');
            box.id = 'bt-polls';
            box.className = 'bt-polls';
            agenda.parentNode.insertBefore(box, agenda);
            loadPolls(bandId, ctx);
        }
        agenda.querySelectorAll('.setlist-song[data-id]').forEach(li => {
            if (li.querySelector('[data-act="sheet"]')) return;
            const btn = document.createElement('button');
            btn.className = 'setlist-item-btn';
            btn.dataset.act = 'sheet';
            btn.title = 'Hoja del bolo: horarios, dirección, checklist';
            btn.setAttribute('aria-label', 'Hoja del bolo');
            btn.innerHTML = bfIco('list', 16);
            btn.addEventListener('click', (ev) => { ev.stopPropagation(); openSheet(bandId, li.dataset.id, ctx); });
            const thread = li.querySelector('[data-act="thread"]');
            if (thread) thread.insertAdjacentElement('afterend', btn);
        });
    });
    BT.loadPolls = loadPolls;

    // ══ Dossier (EPK) de la banda (T-V6-98) ═══════════════════════════════════
    BT.epk = async function (bandId, ctx) {
        const box = document.getElementById('bt-epk');
        if (!box) return;
        let e, apps = [];
        try {
            [e, apps] = await Promise.all([jsonOrThrow(await apiFetch(`/bands/${bandId}/epk`)),
                jsonOrThrow(await apiFetch(`/bands/${bandId}/gig-applications`)).catch(() => [])]);
        } catch (err) { box.innerHTML = '<p class="bf-muted">No se pudo cargar el dossier.</p>'; return; }
        const ro = !ctx.iAmAdmin;
        const linkTxt = (e.links || []).map(l => `${l.label} | ${l.url}`).join('\n');
        const APP = { sent: 'Enviada', seen: 'Vista', shortlisted: 'Preseleccionada', chosen: 'Elegida', declined: 'Esta vez no' };
        box.innerHTML = `
            <div class="bf-row bf-row--between bf-wrap"><h3 class="bf-h3">Dossier de la banda (EPK)</h3>
                <a class="bf-btn bf-btn--sm" href="red.html#bolos">${bfIco('mic', 14)} Buscar bolos</a></div>
            <p class="bf-muted" style="font-size:.85rem;">Lo que ven las salas cuando os postuláis a un bolo y, si lo hacéis público, cualquiera en vuestra página.</p>
            <div><label class="bf-label" for="epk-bio">Presentación</label><textarea class="bf-textarea" id="epk-bio" rows="3" maxlength="4000" ${ro ? 'disabled' : ''}>${escapeHtml(e.bio || '')}</textarea></div>
            <div class="bf-form-grid">
                <div><label class="bf-label" for="epk-styles">Estilos (comas)</label><input class="bf-input" id="epk-styles" value="${escapeHtml((e.styles || []).join(', '))}" ${ro ? 'disabled' : ''}></div>
                <div><label class="bf-label" for="epk-form">Formación</label><input class="bf-input" id="epk-form" maxlength="64" placeholder="Trío, banda de 5…" value="${escapeHtml(e.formation || '')}" ${ro ? 'disabled' : ''}></div>
                <div><label class="bf-label" for="epk-zone">Zona</label><input class="bf-input" id="epk-zone" maxlength="255" value="${escapeHtml(e.zone || '')}" ${ro ? 'disabled' : ''}></div>
                <div><label class="bf-label" for="epk-fee">Caché orientativo</label><input class="bf-input" id="epk-fee" maxlength="255" placeholder="Desde 300 €" value="${escapeHtml(e.fee_hint || '')}" ${ro ? 'disabled' : ''}></div>
            </div>
            <div><label class="bf-label" for="epk-links">Enlaces (uno por línea: «YouTube | https://…»)</label><textarea class="bf-textarea" id="epk-links" rows="2" ${ro ? 'disabled' : ''}>${escapeHtml(linkTxt)}</textarea></div>
            <div><label class="bf-label" for="epk-rider">Rider básico (solo lo ven las salas a las que os postuláis)</label><textarea class="bf-textarea" id="epk-rider" rows="2" maxlength="4000" ${ro ? 'disabled' : ''}>${escapeHtml(e.rider_notes || '')}</textarea></div>
            <label><input type="checkbox" id="epk-public" ${e.is_public ? 'checked' : ''} ${ro ? 'disabled' : ''}> Página pública de la banda (la pueden ver salas y profesionales)</label>
            <div class="bf-row bf-wrap" style="gap:.5rem;">
                ${ro ? '' : `<button class="bf-btn bf-btn--primary" id="epk-save">Guardar dossier</button>`}
                ${e.is_public ? `<a class="bf-btn bf-btn--ghost" href="ficha.html?banda=${encodeURIComponent(bandId)}" target="_blank" rel="noopener">Ver página pública</a>` : ''}
            </div>
            ${apps.length ? `<h3 class="bf-h3" style="margin-top:.8rem;">Candidaturas</h3><ul class="setlist-list">${apps.map(a => `<li class="setlist-song"><span class="sl-title">${escapeHtml(a.call_title || '')}
                <small>${escapeHtml(a.venue_name || '')}${a.starts_at ? ' · ' + escapeHtml(bfDate(a.starts_at)) : ''}</small></span><span class="bf-badge">${escapeHtml(APP[a.status] || a.status)}</span></li>`).join('')}</ul>` : ''}`;
        const save = box.querySelector('#epk-save');
        if (save) save.addEventListener('click', async () => {
            const csv = (v) => v.split(',').map(x => x.trim()).filter(Boolean);
            const body = {
                bio: box.querySelector('#epk-bio').value.trim() || null,
                styles: csv(box.querySelector('#epk-styles').value),
                formation: box.querySelector('#epk-form').value.trim() || null,
                zone: box.querySelector('#epk-zone').value.trim() || null,
                fee_hint: box.querySelector('#epk-fee').value.trim() || null,
                rider_notes: box.querySelector('#epk-rider').value.trim() || null,
                links: box.querySelector('#epk-links').value.split('\n').map(l => l.split('|').map(x => x.trim()))
                    .filter(x => x[0] && x[1]).map(([label, url]) => ({ label, url })),
                is_public: box.querySelector('#epk-public').checked,
            };
            try {
                await jsonOrThrow(await apiFetch(`/bands/${bandId}/epk`, J('PUT', body)));
                toast('Dossier guardado.', 'success');
                BT.epk(bandId, ctx);
            } catch (err) { toast(err.message && err.message !== 'http' ? 'Revisa los enlaces: deben empezar por https://' : 'No se pudo guardar.', 'error'); }
        });
    };
})();
