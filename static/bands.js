/**
 * bands.js — "Mis bandas" (bands.html): listar y crear bandas. Además exporta las funciones de
 * sección (loadRepertoire / loadBandSetlists / loadAgenda / loadFinance / initChat /
 * newBandSetlist…) que REUSA el espacio de banda con pestañas (band.html + band.js).
 * El detalle in-page legacy (openBand) se retiró: la ficha de banda vive en band.html.
 */
const elGrid = document.getElementById('bands-grid');
// `band.html` reutiliza las funciones de sección de este archivo pero NO tiene la rejilla ni el
// botón "nueva banda": por eso protegemos su init con comprobaciones de existencia.
const _btnNewBand = document.getElementById('btn-new-band');
if (_btnNewBand) _btnNewBand.addEventListener('click', createBand);

const ROLE_LABEL = { admin: 'Admin', member: 'Miembro', guest: 'Invitado' };

// ─── Lista de bandas ──────────────────────────────────────────────────────────
async function loadBands() {
    if (chatTimer) { clearInterval(chatTimer); chatTimer = null; }
    try {
        const res = await apiFetch('/bands/');
        if (!res.ok) throw new Error('http');
        const bands = await res.json();
        if (!bands.length) {
            elGrid.innerHTML = `<div class="empty-state"><div class="empty-icon">🎸</div>
                <h3>Aún no estás en ninguna banda</h3>
                <p>Crea una banda para compartir repertorio, agenda y cuentas, o pide a un admin que te pase un enlace de invitación.</p></div>`;
            return;
        }
        elGrid.innerHTML = bands.map(b => `
            <div class="song-card" data-id="${escapeHtml(b.id)}">
                <div class="card-main" data-act="open" style="cursor:pointer;">
                    <h3 class="card-title">${escapeHtml(b.name)}</h3>
                    <p class="card-artist">${ROLE_LABEL[b.role] || escapeHtml(b.role)} · ${b.member_count} ${b.member_count === 1 ? 'miembro' : 'miembros'}</p>
                </div>
            </div>`).join('');
        // La ficha de banda vive ahora en band.html (espacio de banda con pestañas, T-075).
        elGrid.querySelectorAll('.song-card').forEach(card =>
            card.querySelector('[data-act="open"]').addEventListener('click',
                () => { window.location.href = `band.html?id=${encodeURIComponent(card.dataset.id)}`; }));
    } catch (e) {
        elGrid.innerHTML = `<p class="loading-text">⚠️ No se pudieron cargar las bandas.</p>`;
    }
}

// ─── Crear banda ──────────────────────────────────────────────────────────────
async function createBand() {
    const name = await promptModal('¿Cómo se llama tu banda?', { okText: 'Crear', placeholder: 'Nombre de la banda' });
    if (!name) return;
    try {
        const res = await apiFetch('/bands/', {
            method: 'POST', headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name })
        });
        if (!res.ok) throw new Error('http');
        const band = await res.json();
        toast('Banda creada.', 'success');
        window.location.href = `band.html?id=${encodeURIComponent(band.id)}`;
    } catch (e) { toast('No se pudo crear la banda.', 'error'); }
}

// ─── Chat de banda (Fase 12) ──────────────────────────────────────────────────
let chatTimer = null;

function initChat(bandId, iAmAdmin) {
    if (chatTimer) { clearInterval(chatTimer); chatTimer = null; }
    const input = document.getElementById('chat-input');
    const send = document.getElementById('chat-send');
    const doSend = async () => {
        const body = input.value.trim();
        if (!body) return;
        input.value = '';
        try {
            const res = await apiFetch(`/bands/${bandId}/messages/`, {
                method: 'POST', headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ body })
            });
            if (!res.ok) throw new Error('http');
            loadChat(bandId, iAmAdmin);
        } catch (e) { toast('No se pudo enviar el mensaje.', 'error'); input.value = body; }
    };
    if (send) send.addEventListener('click', doSend);
    if (input) input.addEventListener('keydown', (e) => { if (e.key === 'Enter') doSend(); });
    loadChat(bandId, iAmAdmin);
    // Refresco periódico simple (tiempo real más adelante). Se detiene si salimos de la ficha.
    chatTimer = setInterval(() => {
        if (!document.getElementById('b-chat')) { clearInterval(chatTimer); chatTimer = null; return; }
        loadChat(bandId, iAmAdmin);
    }, 6000);
}

async function loadChat(bandId, iAmAdmin) {
    const el = document.getElementById('b-chat');
    if (!el) return;
    let msgs;
    try {
        const res = await apiFetch(`/bands/${bandId}/messages/`);
        if (!res.ok) throw new Error('http');
        msgs = await res.json();
    } catch (e) { el.innerHTML = '<p class="loading-text">⚠️ No se pudo cargar el chat.</p>'; return; }

    if (!msgs.length) { el.innerHTML = '<p class="loading-text">Aún no hay mensajes. ¡Rompe el hielo!</p>'; return; }
    el.innerHTML = `<ul class="setlist-list">${msgs.map(m => `
        <li class="setlist-song ${m.is_pinned ? 'msg-pinned' : ''}" data-id="${escapeHtml(m.id)}">
            <span class="sl-title">${m.is_pinned ? '📌 ' : ''}<strong>${escapeHtml(m.author_name || 'Alguien')}</strong>: ${escapeHtml(m.body)}
                ${m.edited_at ? '<small>(editado)</small>' : ''}</span>
            <span class="msg-actions">
                ${iAmAdmin ? `<button class="setlist-item-btn" data-act="pin" title="${m.is_pinned ? 'Desfijar' : 'Fijar como nota'}">${m.is_pinned ? '📌' : '📍'}</button>` : ''}
                ${(m.is_mine || iAmAdmin) ? `<button class="setlist-item-btn danger" data-act="del" aria-label="Borrar" title="Borrar">🗑️</button>` : ''}
            </span>
        </li>`).join('')}</ul>`;

    el.querySelectorAll('.setlist-song').forEach(li => {
        const mid = li.dataset.id;
        const pin = li.querySelector('[data-act="pin"]');
        if (pin) pin.addEventListener('click', async () => {
            const isPinned = li.classList.contains('msg-pinned');
            try {
                const res = await apiFetch(`/bands/${bandId}/messages/${mid}/pin`, {
                    method: 'PATCH', headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ is_pinned: !isPinned })
                });
                if (!res.ok) throw new Error('http');
                loadChat(bandId, iAmAdmin);
            } catch (e) { toast('No se pudo fijar el mensaje.', 'error'); }
        });
        const del = li.querySelector('[data-act="del"]');
        if (del) del.addEventListener('click', async () => {
            const ok = await confirmModal('¿Borrar este mensaje?', { okText: 'Borrar' });
            if (!ok) return;
            try {
                const res = await apiFetch(`/bands/${bandId}/messages/${mid}`, { method: 'DELETE' });
                if (!res.ok && res.status !== 204) throw new Error('http');
                loadChat(bandId, iAmAdmin);
            } catch (e) { toast('No se pudo borrar el mensaje.', 'error'); }
        });
    });
}

// ─── Finanzas ─────────────────────────────────────────────────────────────────
function fmtMoney(x) { return `${Number(x).toFixed(2)} €`; }

async function loadFinance(bandId, iAmAdmin) {
    const el = document.getElementById('b-finance');
    if (!el) return;
    let balances, txs;
    try {
        const [rb, rt] = await Promise.all([
            apiFetch(`/bands/${bandId}/balances`), apiFetch(`/bands/${bandId}/transactions`)]);
        if (!rb.ok || !rt.ok) throw new Error('http');
        balances = await rb.json();
        txs = await rt.json();
    } catch (e) { el.innerHTML = '<p class="loading-text">⚠️ No se pudieron cargar las finanzas.</p>'; return; }

    const balRows = balances.map(b => {
        const v = Number(b.balance);
        const cls = v > 0 ? 'bal-pos' : (v < 0 ? 'bal-neg' : '');
        const label = v > 0 ? 'le deben' : (v < 0 ? 'debe' : 'al día');
        return `<li class="setlist-song">
            <span class="sl-title">${b.is_fund ? '🏦 ' : ''}${escapeHtml(b.display_name || b.participant)}</span>
            <span class="${cls}">${fmtMoney(v)} <small>${label}</small></span></li>`;
    }).join('') || '<li><small>Sin saldos.</small></li>';

    const txRows = txs.map(t => `
        <li class="setlist-song" data-id="${escapeHtml(t.id)}">
            <span class="sl-title">${t.type === 'income' ? '➕' : '➖'} ${escapeHtml(t.description || (t.type === 'income' ? 'Ingreso' : 'Gasto'))}
                <small>${fmtMoney(t.amount)}${t.category ? ' · ' + escapeHtml(t.category) : ''}</small></span>
            ${iAmAdmin ? `<button class="setlist-item-btn danger" data-act="del" aria-label="Borrar movimiento" title="Borrar">🗑️</button>` : ''}
        </li>`).join('') || '<li><small>Sin movimientos todavía.</small></li>';

    el.innerHTML = `
        <h5>Saldos</h5><ul class="setlist-list">${balRows}</ul>
        <h5>Movimientos</h5><ul class="setlist-list" id="b-tx-list">${txRows}</ul>`;

    if (iAmAdmin) el.querySelectorAll('#b-tx-list .setlist-song').forEach(li => {
        const del = li.querySelector('[data-act="del"]');
        if (del) del.addEventListener('click', async () => {
            const ok = await confirmModal('¿Borrar este movimiento?', { okText: 'Borrar' });
            if (!ok) return;
            try {
                const res = await apiFetch(`/bands/${bandId}/transactions/${li.dataset.id}`, { method: 'DELETE' });
                if (!res.ok && res.status !== 204) throw new Error('http');
                loadFinance(bandId, iAmAdmin);
            } catch (e) { toast('No se pudo borrar el movimiento.', 'error'); }
        });
    });
}

// Registrar movimiento (admin): tipo, descripción, importe, pagador. Reparto a partes iguales.
async function newTransaction(bandId, members) {
    const payerOptions = members.map(m => `<option value="${escapeHtml(m.user_id)}">${escapeHtml(m.display_name || m.user_id)}</option>`).join('')
        + '<option value="__fund__">🏦 Fondo común</option>';
    // Filas del reparto personalizado: una por miembro activo (id estable en data-uid).
    const splitRows = members.map(m => `
        <div class="split-row">
            <span class="split-name">${escapeHtml(m.display_name || m.user_id)}</span>
            <input type="number" class="search-box split-amount" data-uid="${escapeHtml(m.user_id)}"
                   min="0" step="0.01" placeholder="0.00">
        </div>`).join('');
    const overlay = document.createElement('div');
    overlay.className = 'modal-overlay';
    overlay.innerHTML = `
        <div class="modal-card glass-panel" role="dialog" aria-modal="true">
            <p class="modal-msg">Nuevo movimiento</p>
            <select id="tx-type" class="search-box">
                <option value="expense">➖ Gasto</option>
                <option value="income">➕ Ingreso</option>
            </select>
            <input type="text" id="tx-desc" class="search-box" placeholder="Descripción (p. ej. Local de ensayo)">
            <input type="number" id="tx-amount" class="search-box" placeholder="Importe (€)" min="0.01" step="0.01">
            <label class="field-label">¿Quién pagó/cobró?</label>
            <select id="tx-payer" class="search-box">${payerOptions}</select>
            <label class="field-label">Reparto entre miembros</label>
            <select id="tx-split-mode" class="search-box">
                <option value="equal">A partes iguales</option>
                <option value="custom">Personalizado…</option>
            </select>
            <div id="tx-splits" style="display:none;">
                ${splitRows}
                <p class="split-sum" id="tx-split-sum"></p>
            </div>
            <div class="modal-actions">
                <button class="secondary-btn" data-act="cancel">Cancelar</button>
                <button class="primary-btn" data-act="ok">Registrar</button>
            </div>
        </div>`;

    const elMode = overlay.querySelector('#tx-split-mode');
    const elSplits = overlay.querySelector('#tx-splits');
    const elAmount = overlay.querySelector('#tx-amount');
    const elSum = overlay.querySelector('#tx-split-sum');
    const splitInputs = () => Array.from(overlay.querySelectorAll('.split-amount'));
    const sumSplits = () => splitInputs().reduce((acc, i) => acc + (parseFloat(i.value) || 0), 0);
    const refreshSum = () => {
        const total = parseFloat(elAmount.value) || 0;
        const asign = sumSplits();
        const ok = total > 0 && Math.abs(asign - total) < 0.005;
        elSum.textContent = `Asignado ${asign.toFixed(2)} € de ${total.toFixed(2)} €` + (ok ? '  ✓' : '');
        elSum.style.color = ok ? '#5db075' : 'var(--text-secondary)';
    };
    // Al pasar a "personalizado", prerrellena a partes iguales (céntimos a los primeros) como
    // punto de partida editable; el usuario ajusta cada importe.
    elMode.addEventListener('change', () => {
        const custom = elMode.value === 'custom';
        elSplits.style.display = custom ? '' : 'none';
        if (custom) {
            const cents = Math.round((parseFloat(elAmount.value) || 0) * 100);
            const n = splitInputs().length;
            if (cents > 0 && n) {
                const base = Math.floor(cents / n), rem = cents - base * n;
                splitInputs().forEach((inp, idx) => { inp.value = ((base + (idx < rem ? 1 : 0)) / 100).toFixed(2); });
            }
            refreshSum();
        }
    });
    elSplits.addEventListener('input', refreshSum);
    elAmount.addEventListener('input', () => { if (elMode.value === 'custom') refreshSum(); });

    const close = () => overlay.remove();
    overlay.addEventListener('click', async (e) => {
        if (e.target === overlay || e.target.getAttribute('data-act') === 'cancel') { close(); return; }
        if (e.target.getAttribute('data-act') !== 'ok') return;
        const amount = parseFloat(elAmount.value);
        if (!(amount > 0)) { toast('Pon un importe válido.', 'error'); return; }
        const payer = overlay.querySelector('#tx-payer').value;
        const body = {
            type: overlay.querySelector('#tx-type').value,
            description: overlay.querySelector('#tx-desc').value.trim() || null,
            amount: amount.toFixed(2),
        };
        if (payer === '__fund__') body.paid_by_fund = true; else body.paid_by = payer;
        // Reparto personalizado: una parte por miembro con importe > 0; la Σ debe cuadrar con el
        // total (el backend lo revalida y rechaza si no cuadra).
        if (elMode.value === 'custom') {
            const splits = splitInputs()
                .map(i => ({ user_id: i.dataset.uid, amount: parseFloat(i.value) || 0 }))
                .filter(s => s.amount > 0);
            const suma = splits.reduce((a, s) => a + s.amount, 0);
            if (!splits.length || Math.abs(suma - amount) >= 0.005) {
                toast(`Las partes (${suma.toFixed(2)} €) deben sumar el total (${amount.toFixed(2)} €).`, 'error');
                return;
            }
            body.splits = splits.map(s => ({ user_id: s.user_id, share_amount: s.amount.toFixed(2) }));
        }
        close();
        try {
            const res = await apiFetch(`/bands/${bandId}/transactions`, {
                method: 'POST', headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(body)
            });
            if (!res.ok) throw new Error('http');
            toast('Movimiento registrado.', 'success');
            loadFinance(bandId, true);
        } catch (e) { toast('No se pudo registrar el movimiento.', 'error'); }
    });
    document.body.appendChild(overlay);
}

// Registrar liquidación (admin): de quién, a quién (o fondo), importe.
async function newSettlement(bandId, members) {
    const memberOpts = members.map(m => `<option value="${escapeHtml(m.user_id)}">${escapeHtml(m.display_name || m.user_id)}</option>`).join('');
    const overlay = document.createElement('div');
    overlay.className = 'modal-overlay';
    overlay.innerHTML = `
        <div class="modal-card glass-panel" role="dialog" aria-modal="true">
            <p class="modal-msg">Registrar liquidación (pago real)</p>
            <label class="field-label">Paga</label>
            <select id="st-from" class="search-box">${memberOpts}</select>
            <label class="field-label">Recibe</label>
            <select id="st-to" class="search-box">${memberOpts}<option value="__fund__">🏦 Fondo común</option></select>
            <input type="number" id="st-amount" class="search-box" placeholder="Importe (€)" min="0.01" step="0.01">
            <div class="modal-actions">
                <button class="secondary-btn" data-act="cancel">Cancelar</button>
                <button class="primary-btn" data-act="ok">Registrar</button>
            </div>
        </div>`;
    const close = () => overlay.remove();
    overlay.addEventListener('click', async (e) => {
        if (e.target === overlay || e.target.getAttribute('data-act') === 'cancel') { close(); return; }
        if (e.target.getAttribute('data-act') !== 'ok') return;
        const amount = parseFloat(overlay.querySelector('#st-amount').value);
        if (!(amount > 0)) { toast('Pon un importe válido.', 'error'); return; }
        const from = overlay.querySelector('#st-from').value;
        const to = overlay.querySelector('#st-to').value;
        const body = { from_user_id: from, amount: amount.toFixed(2) };
        if (to === '__fund__') body.to_fund = true; else body.to_user_id = to;
        if (to !== '__fund__' && to === from) { toast('El que paga y el que recibe no pueden ser el mismo.', 'error'); return; }
        close();
        try {
            const res = await apiFetch(`/bands/${bandId}/settlements`, {
                method: 'POST', headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(body)
            });
            if (!res.ok) throw new Error('http');
            toast('Liquidación registrada.', 'success');
            loadFinance(bandId, true);
        } catch (e) { toast('No se pudo registrar la liquidación.', 'error'); }
    });
    document.body.appendChild(overlay);
}

// ─── Agenda (eventos) ─────────────────────────────────────────────────────────
const EVENT_ICON = { rehearsal: '🎼', concert: '🎤', other: '📌' };
const EVENT_TYPE_LABEL = { rehearsal: 'Ensayo', concert: 'Concierto', other: 'Otro' };
const ATT_LABEL = { yes: '✅ Voy', maybe: '🤔 Quizás', no: '❌ No voy' };

function fmtDate(iso) {
    if (!iso) return 'Sin fecha';
    const d = new Date(iso);
    if (isNaN(d)) return 'Sin fecha';
    return d.toLocaleString('es-ES', { weekday: 'short', day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' });
}

async function loadAgenda(bandId, iAmAdmin) {
    const el = document.getElementById('b-agenda');
    if (!el) return;
    let events;
    try {
        const res = await apiFetch(`/bands/${bandId}/events/`);
        if (!res.ok) throw new Error('http');
        events = await res.json();
    } catch (e) { el.innerHTML = '<p class="loading-text">⚠️ No se pudo cargar la agenda.</p>'; return; }

    if (!events.length) {
        el.innerHTML = '<p class="loading-text">Sin eventos. ' + (iAmAdmin ? 'Crea un ensayo o concierto.' : 'Un admin puede crear eventos.') + '</p>';
        return;
    }
    const now = Date.now();
    const upcoming = events.filter(e => e.starts_at && new Date(e.starts_at).getTime() >= now);
    const past = events.filter(e => !e.starts_at || new Date(e.starts_at).getTime() < now);

    const row = (e) => `
        <li class="setlist-song" data-id="${escapeHtml(e.id)}">
            <span class="sl-title">${EVENT_ICON[e.type] || '📌'} ${escapeHtml(e.title)}
                <small>${EVENT_TYPE_LABEL[e.type] || ''} · ${escapeHtml(fmtDate(e.starts_at))}${e.status === 'cancelled' ? ' · ❌ cancelado' : ''}</small></span>
            <span class="att-buttons">
                ${['yes', 'maybe', 'no'].map(s => `<button class="setlist-item-btn att-btn${e.my_status === s ? ' active' : ''}" data-att="${s}" title="${ATT_LABEL[s]}">${ATT_LABEL[s]}</button>`).join('')}
                ${iAmAdmin ? `<button class="setlist-item-btn danger" data-act="del" aria-label="Borrar evento" title="Borrar">🗑️</button>` : ''}
            </span>
        </li>`;
    el.innerHTML = `
        ${upcoming.length ? `<h5>Próximos</h5><ul class="setlist-list">${upcoming.map(row).join('')}</ul>` : ''}
        ${past.length ? `<h5>Pasados</h5><ul class="setlist-list">${past.map(row).join('')}</ul>` : ''}`;

    el.querySelectorAll('.setlist-song').forEach(li => {
        const eid = li.dataset.id;
        li.querySelectorAll('[data-att]').forEach(b =>
            b.addEventListener('click', () => setAttendance(bandId, eid, b.dataset.att, iAmAdmin)));
        const del = li.querySelector('[data-act="del"]');
        if (del) del.addEventListener('click', async () => {
            const ok = await confirmModal('¿Borrar este evento?', { okText: 'Borrar' });
            if (!ok) return;
            try {
                const res = await apiFetch(`/bands/${bandId}/events/${eid}`, { method: 'DELETE' });
                if (!res.ok && res.status !== 204) throw new Error('http');
                loadAgenda(bandId, iAmAdmin);
            } catch (e) { toast('No se pudo borrar el evento.', 'error'); }
        });
    });
}

async function setAttendance(bandId, eventId, status, iAmAdmin) {
    try {
        const res = await apiFetch(`/bands/${bandId}/events/${eventId}/attendance`, {
            method: 'PUT', headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ status })
        });
        if (!res.ok) throw new Error('http');
        loadAgenda(bandId, iAmAdmin);
    } catch (e) { toast('No se pudo guardar tu asistencia.', 'error'); }
}

// Crear evento (solo admin): tipo, título, fecha y (si concierto) setlist opcional.
async function newEvent(bandId) {
    let setlists = [];
    try { setlists = await (await apiFetch(`/bands/${bandId}/setlists/`)).json(); } catch (_) { setlists = []; }

    const overlay = document.createElement('div');
    overlay.className = 'modal-overlay';
    overlay.innerHTML = `
        <div class="modal-card glass-panel" role="dialog" aria-modal="true">
            <p class="modal-msg">Nuevo evento</p>
            <select id="ev-type" class="search-box">
                <option value="rehearsal">🎼 Ensayo</option>
                <option value="concert">🎤 Concierto</option>
                <option value="other">📌 Otro</option>
            </select>
            <input type="text" id="ev-title" class="search-box" placeholder="Título (p. ej. Ensayo jueves)">
            <input type="datetime-local" id="ev-date" class="search-box">
            <div id="ev-setlist-wrap" style="display:none;">
                <select id="ev-setlist" class="search-box">
                    <option value="">— Sin setlist —</option>
                    ${setlists.map(s => `<option value="${escapeHtml(s.id)}">${escapeHtml(s.name)}</option>`).join('')}
                </select>
            </div>
            <div class="modal-actions">
                <button class="secondary-btn" data-act="cancel">Cancelar</button>
                <button class="primary-btn" data-act="ok">Crear</button>
            </div>
        </div>`;
    const elType = overlay.querySelector('#ev-type');
    const elSlWrap = overlay.querySelector('#ev-setlist-wrap');
    elType.addEventListener('change', () => { elSlWrap.style.display = elType.value === 'concert' ? '' : 'none'; });
    const close = () => overlay.remove();
    overlay.addEventListener('click', async (e) => {
        if (e.target === overlay || e.target.getAttribute('data-act') === 'cancel') { close(); return; }
        if (e.target.getAttribute('data-act') !== 'ok') return;
        const title = overlay.querySelector('#ev-title').value.trim();
        if (!title) { toast('Pon un título al evento.', 'error'); return; }
        const type = elType.value;
        const dateVal = overlay.querySelector('#ev-date').value;
        const body = { type, title };
        if (dateVal) body.starts_at = dateVal;
        const slId = overlay.querySelector('#ev-setlist')?.value;
        if (type === 'concert' && slId) body.setlist_id = slId;
        close();
        try {
            const res = await apiFetch(`/bands/${bandId}/events/`, {
                method: 'POST', headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(body)
            });
            if (!res.ok) throw new Error('http');
            toast('Evento creado.', 'success');
            loadAgenda(bandId, true);
        } catch (e) { toast('No se pudo crear el evento.', 'error'); }
    });
    document.body.appendChild(overlay);
}

// ─── Setlists de la banda ─────────────────────────────────────────────────────
async function loadBandSetlists(bandId, canEdit) {
    const el = document.getElementById('b-setlists');
    if (!el) return;
    let setlists;
    try {
        const res = await apiFetch(`/bands/${bandId}/setlists/`);
        if (!res.ok) throw new Error('http');
        setlists = await res.json();
    } catch (e) { el.innerHTML = '<li><small>⚠️ No se pudieron cargar los setlists.</small></li>'; return; }

    if (!setlists.length) {
        el.innerHTML = '<li><small>Sin setlists todavía. Crea uno con las canciones del repertorio.</small></li>';
        return;
    }
    el.innerHTML = setlists.map(sl => `
        <li class="setlist-song" data-id="${escapeHtml(sl.id)}">
            <span class="sl-title">${escapeHtml(sl.name)} <small>${sl.song_count} ${sl.song_count === 1 ? 'canción' : 'canciones'}</small></span>
            <button class="setlist-item-btn" data-act="play" title="Reproducir en orden">▶</button>
            ${canEdit ? `<button class="setlist-item-btn danger" data-act="del" aria-label="Borrar setlist" title="Borrar">🗑️</button>` : ''}
        </li>`).join('');
    el.querySelectorAll('.setlist-song').forEach(li => {
        const sid = li.dataset.id;
        li.querySelector('[data-act="play"]').addEventListener('click', () => playBandSetlist(bandId, sid));
        const del = li.querySelector('[data-act="del"]');
        if (del) del.addEventListener('click', async () => {
            const ok = await confirmModal('¿Borrar este setlist?', { okText: 'Borrar' });
            if (!ok) return;
            try {
                const res = await apiFetch(`/bands/${bandId}/setlists/${sid}`, { method: 'DELETE' });
                if (!res.ok && res.status !== 204) throw new Error('http');
                loadBandSetlists(bandId, canEdit);
            } catch (e) { toast('No se pudo borrar el setlist.', 'error'); }
        });
    });
}

async function playBandSetlist(bandId, setlistId) {
    try {
        const res = await apiFetch(`/bands/${bandId}/setlists/${setlistId}`);
        const sl = await res.json();
        if (!sl.items || !sl.items.length) { toast('Ese setlist está vacío.', 'info'); return; }
        const first = sl.items[0].song_id;
        window.location.href = `index.html?songId=${encodeURIComponent(first)}&setlist=${encodeURIComponent(setlistId)}&pos=0`;
    } catch (e) { toast('No se pudo abrir el setlist.', 'error'); }
}

// Editor de setlist de banda: elige del repertorio en orden y guarda.
async function newBandSetlist(bandId, opts = {}) {
    // band.html pasa su propio `container` (dónde pintar el editor) y `onDone` (qué hacer al
    // guardar/cancelar) para integrarlo en la pestaña Setlists. Es el único llamador vivo.
    const target = opts.container;
    const onDone = opts.onDone || (() => {});
    if (!target) return;   // sin contenedor no hay dónde pintar (el detalle legacy ya no existe)
    let repertoire = [];
    try {
        const res = await apiFetch(`/bands/${bandId}/songs/`);
        repertoire = await res.json();
    } catch (e) { toast('No se pudo cargar el repertorio.', 'error'); return; }
    if (!repertoire.length) { toast('Primero añade canciones al repertorio de la banda.', 'info'); return; }

    const selected = [];
    const byId = Object.fromEntries(repertoire.map(s => [s.id, s]));
    target.innerHTML = `
        <div class="setlist-editor">
            <a href="#" id="sl-back" class="back-link">← Volver a la banda</a>
            <h3>Nuevo setlist de banda</h3>
            <input type="text" id="sl-name" class="search-box" placeholder="Nombre (p. ej. Bolo sábado)">
            <div class="setlist-cols">
                <div><h4>Repertorio</h4><ul id="sl-available" class="setlist-list"></ul></div>
                <div><h4>En el setlist (en orden)</h4><ul id="sl-selected" class="setlist-list"></ul></div>
            </div>
            <div class="form-actions"><button id="sl-save" class="primary-btn">💾 Crear setlist</button></div>
        </div>`;
    document.getElementById('sl-back').addEventListener('click', (e) => { e.preventDefault(); onDone(); });

    const elAvail = document.getElementById('sl-available');
    const elSel = document.getElementById('sl-selected');
    function render() {
        elAvail.innerHTML = repertoire.map(s => `
            <li><button class="setlist-item-btn" data-id="${escapeHtml(s.id)}" ${selected.includes(s.id) ? 'disabled' : ''}>
                ➕ ${escapeHtml(s.title)} <small>${escapeHtml(s.artist || '')}</small></button></li>`).join('');
        elAvail.querySelectorAll('button[data-id]').forEach(b =>
            b.addEventListener('click', () => { selected.push(b.dataset.id); render(); }));
        elSel.innerHTML = selected.map((id, i) => `
            <li><span>${i + 1}. ${escapeHtml(byId[id]?.title || id)}</span>
                <button class="setlist-item-btn danger" data-rm="${escapeHtml(id)}" aria-label="Quitar">✕</button></li>`).join('')
            || '<li><small>Pulsa ➕ para añadir canciones.</small></li>';
        elSel.querySelectorAll('button[data-rm]').forEach(b =>
            b.addEventListener('click', () => {
                const i = selected.indexOf(b.dataset.rm); if (i > -1) selected.splice(i, 1); render();
            }));
    }
    render();

    document.getElementById('sl-save').addEventListener('click', async () => {
        const name = document.getElementById('sl-name').value.trim();
        if (!name) { toast('Pon un nombre al setlist.', 'error'); return; }
        try {
            const res = await apiFetch(`/bands/${bandId}/setlists/`, {
                method: 'POST', headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name, song_ids: selected })
            });
            if (!res.ok) throw new Error('http');
            toast('Setlist creado.', 'success');
            onDone();
        } catch (e) { toast('No se pudo crear el setlist.', 'error'); }
    });
}

// ─── Repertorio de la banda ───────────────────────────────────────────────────
async function loadRepertoire(bandId, canEdit) {
    const elRep = document.getElementById('b-repertoire');
    if (!elRep) return;
    let songs;
    try {
        const res = await apiFetch(`/bands/${bandId}/songs/`);
        if (!res.ok) throw new Error('http');
        songs = await res.json();
    } catch (e) { elRep.innerHTML = '<li><small>⚠️ No se pudo cargar el repertorio.</small></li>'; return; }

    if (!songs.length) {
        elRep.innerHTML = '<li><small>Repertorio vacío. Copia canciones de tus partituras.</small></li>';
        return;
    }
    elRep.innerHTML = songs.map(s => `
        <li class="setlist-song" data-id="${escapeHtml(s.id)}">
            <span class="sl-title">${escapeHtml(s.title)} <small>${escapeHtml(s.artist || '')}</small></span>
            <button class="setlist-item-btn" data-act="play" title="Reproducir">▶</button>
            ${canEdit ? `<button class="setlist-item-btn danger" data-act="rm" aria-label="Quitar del repertorio" title="Quitar">✕</button>` : ''}
        </li>`).join('');
    elRep.querySelectorAll('.setlist-song').forEach(li => {
        const sid = li.dataset.id;
        li.querySelector('[data-act="play"]').addEventListener('click', () => {
            window.location.href = `index.html?songId=${encodeURIComponent(sid)}`;
        });
        const rm = li.querySelector('[data-act="rm"]');
        if (rm) rm.addEventListener('click', async () => {
            const ok = await confirmModal('¿Quitar esta canción del repertorio de la banda?', { okText: 'Quitar' });
            if (!ok) return;
            try {
                const res = await apiFetch(`/bands/${bandId}/songs/${sid}`, { method: 'DELETE' });
                if (!res.ok && res.status !== 204) throw new Error('http');
                loadRepertoire(bandId, canEdit);
            } catch (e) { toast('No se pudo quitar la canción.', 'error'); }
        });
    });
}

// Copiar una canción personal al repertorio de la banda (decisión §7: por copia).
async function copyFromPersonal(bandId) {
    let songs = [];
    try {
        const res = await apiFetch('/songs/');
        songs = await res.json();
    } catch (e) { toast('No se pudieron cargar tus partituras.', 'error'); return; }
    if (!songs.length) { toast('No tienes partituras personales para copiar.', 'info'); return; }

    // Modal selector propio (no reutilizamos alertModal porque cierra al primer clic).
    const overlay = document.createElement('div');
    overlay.className = 'modal-overlay';
    overlay.innerHTML = `
        <div class="modal-card glass-panel" role="dialog" aria-modal="true">
            <p class="modal-msg">Elige una canción para copiar al repertorio:</p>
            <ul class="setlist-list" id="copy-list">${songs.map(s => `
                <li><button class="setlist-item-btn" data-id="${escapeHtml(s.id)}">
                    ➕ ${escapeHtml(s.title)} <small>${escapeHtml(s.artist || '')}</small></button></li>`).join('')}</ul>
            <div class="modal-actions"><button class="secondary-btn" data-act="cancel">Cerrar</button></div>
        </div>`;
    const close = () => overlay.remove();
    overlay.addEventListener('click', async (e) => {
        if (e.target === overlay || e.target.getAttribute('data-act') === 'cancel') { close(); return; }
        const btn = e.target.closest('button[data-id]');
        if (!btn) return;
        close();
        try {
            const res = await apiFetch(`/bands/${bandId}/songs/copy`, {
                method: 'POST', headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ song_id: btn.dataset.id })
            });
            if (!res.ok) throw new Error('http');
            toast('Canción copiada al repertorio.', 'success');
            loadRepertoire(bandId, true);
        } catch (e) { toast('No se pudo copiar la canción.', 'error'); }
    });
    document.body.appendChild(overlay);
}

// ─── Invitar por código ───────────────────────────────────────────────────────
async function generateInvite(bandId) {
    try {
        const res = await apiFetch(`/bands/${bandId}/invites`, {
            method: 'POST', headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ role_to_grant: 'member' })
        });
        if (!res.ok) throw new Error('http');
        const inv = await res.json();
        const link = `${location.origin}/static/join.html?code=${encodeURIComponent(inv.code)}`;
        try { await navigator.clipboard.writeText(link); toast('Enlace copiado al portapapeles.', 'success'); }
        catch (_) { /* clipboard puede fallar sin gesto/https */ }
        await alertModal(`Comparte este enlace para que se unan a la banda:<br><br>
            <input class="search-box" readonly value="${escapeHtml(link)}" onclick="this.select()">`, { okText: 'Hecho' });
    } catch (e) { toast('No se pudo generar la invitación.', 'error'); }
}

// Auto-arranque SOLO en la lista de bandas (bands.html). En band.html lo gobierna band.js.
if (elGrid) { (async () => { await requireAuth(); loadBands(); })(); }
