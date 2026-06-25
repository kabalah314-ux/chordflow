/**
 * setlists.js — Setlists: crear, ver, reproducir en orden y borrar (Fase 5).
 */
const elGrid = document.getElementById('setlist-grid');
const elDetail = document.getElementById('setlist-detail');
const elBtnNew = document.getElementById('btn-new-setlist');

elBtnNew.addEventListener('click', () => openEditor());

function showGrid() { elDetail.style.display = 'none'; elGrid.style.display = ''; }
function showDetail() { elGrid.style.display = 'none'; elDetail.style.display = ''; }

// ─── Lista de setlists ─────────────────────────────────────────────────────
async function loadSetlists() {
    showGrid();
    try {
        const res = await apiFetch('/setlists/');
        if (!res.ok) throw new Error('http');
        const setlists = await res.json();
        if (!setlists.length) {
            elGrid.innerHTML = `<div class="empty-state"><div class="empty-icon">🎼</div>
                <h3>Aún no tienes setlists</h3>
                <p>Crea uno para agrupar canciones y tocarlas en orden en tus bolos.</p></div>`;
            return;
        }
        elGrid.innerHTML = setlists.map(sl => `
            <div class="song-card" data-id="${escapeHtml(sl.id)}">
                <div class="card-actions">
                    <button class="card-action-btn" data-act="edit" aria-label="Editar ${escapeHtml(sl.name)}" title="Editar">${bfIcon('edit')}</button>
                    <button class="card-action-btn danger" data-act="del" aria-label="Borrar ${escapeHtml(sl.name)}" title="Borrar">${bfIcon('trash')}</button>
                </div>
                <div class="card-main" data-act="open" style="cursor:pointer;">
                    <h3 class="card-title">${escapeHtml(sl.name)}</h3>
                    <p class="card-artist">${sl.song_count} ${sl.song_count === 1 ? 'canción' : 'canciones'}</p>
                </div>
            </div>`).join('');
        elGrid.querySelectorAll('.song-card').forEach(card => {
            const id = card.dataset.id;
            card.querySelector('[data-act="open"]').addEventListener('click', () => openSetlist(id));
            card.querySelector('[data-act="edit"]').addEventListener('click', (e) => {
                e.stopPropagation();
                openEditor(id);
            });
            card.querySelector('[data-act="del"]').addEventListener('click', (e) => {
                e.stopPropagation();
                const name = card.querySelector('.card-title').textContent;
                deleteSetlist(id, name);
            });
        });
    } catch (e) {
        elGrid.innerHTML = `<p class="loading-text">⚠️ No se pudieron cargar los setlists.</p>`;
    }
}

async function deleteSetlist(id, name) {
    const ok = await confirmModal(`¿Borrar el setlist "${name}"?`, { okText: 'Borrar' });
    if (!ok) return;
    try {
        const res = await apiFetch(`/setlists/${id}`, { method: 'DELETE' });
        if (!res.ok && res.status !== 204) throw new Error('http');
        loadSetlists();
    } catch (e) { toast('No se pudo borrar el setlist.', 'error'); }
}

// ─── Crear / editar setlist ──────────────────────────────────────────────────
// Sin `setlistId` crea (POST); con `setlistId` edita (PATCH), precargando nombre + canciones + notas.
async function openEditor(setlistId = null) {
    const editing = !!setlistId;
    showDetail();
    elDetail.innerHTML = `<p class="loading-text">Cargando tus canciones…</p>`;
    let songs = [];
    let existing = null;
    try {
        const reqs = [apiFetch('/songs/')];
        if (editing) reqs.push(apiFetch(`/setlists/${setlistId}`));
        const [rSongs, rSl] = await Promise.all(reqs);
        songs = await rSongs.json();
        if (editing) {
            if (!rSl.ok) throw new Error('http');
            existing = await rSl.json();
        }
    } catch (e) { elDetail.innerHTML = '<p class="loading-text">⚠️ Error cargando datos.</p>'; return; }

    const selected = editing ? (existing.items || []).map(it => it.song_id) : []; // ids en orden
    const notes = {};   // song_id → apunte, persiste entre re-renders
    if (editing) (existing.items || []).forEach(it => { if (it.note) notes[it.song_id] = it.note; });
    const byId = Object.fromEntries(songs.map(s => [s.id, s]));

    elDetail.innerHTML = `
        <div class="setlist-editor">
            <a href="#" id="sl-back" class="back-link">← Volver</a>
            <h3>${editing ? 'Editar setlist' : 'Nuevo setlist'}</h3>
            <input type="text" id="sl-name" class="search-box" placeholder="Nombre del setlist (p. ej. Bolo sábado)" value="${editing ? escapeHtml(existing.name) : ''}">
            <div class="setlist-cols">
                <div>
                    <h4>Canciones disponibles</h4>
                    <ul id="sl-available" class="setlist-list"></ul>
                </div>
                <div>
                    <h4>En el setlist (en orden)</h4>
                    <ul id="sl-selected" class="setlist-list"></ul>
                </div>
            </div>
            <div class="form-actions"><button id="sl-save" class="primary-btn">${bfIcon('save')} ${editing ? 'Guardar cambios' : 'Crear setlist'}</button></div>
        </div>`;
    document.getElementById('sl-back').addEventListener('click', (e) => { e.preventDefault(); loadSetlists(); });

    const elAvail = document.getElementById('sl-available');
    const elSel = document.getElementById('sl-selected');

    function renderAvail() {
        elAvail.innerHTML = songs.map(s => `
            <li><button class="setlist-item-btn" data-id="${escapeHtml(s.id)}" ${selected.includes(s.id) ? 'disabled' : ''}>
                ${bfIcon('plus')} ${escapeHtml(s.title)} <small>${escapeHtml(s.artist || '')}</small></button></li>`).join('')
            || '<li><small>No tienes canciones todavía.</small></li>';
        elAvail.querySelectorAll('button[data-id]').forEach(b =>
            b.addEventListener('click', () => { selected.push(b.dataset.id); renderAll(); }));
    }
    function renderSel() {
        elSel.innerHTML = selected.map((id, i) => `
            <li class="sl-sel-row" data-sid="${escapeHtml(id)}">
                <button class="sl-drag" aria-label="Reordenar" title="Arrastra para reordenar">⠿</button>
                <span>${i + 1}. ${escapeHtml(byId[id]?.title || id)}</span>
                <input type="text" class="search-box sl-note" data-note="${escapeHtml(id)}" maxlength="255"
                       placeholder="Apunte (capo 2, acústica…)" value="${escapeHtml(notes[id] || '')}">
                <button class="setlist-item-btn" data-rm="${escapeHtml(id)}" aria-label="Quitar" title="Quitar">${bfIcon('x')}</button></li>`).join('')
            || '<li><small>Pulsa ➕ para añadir canciones.</small></li>';
        elSel.querySelectorAll('.sl-note').forEach(inp =>
            inp.addEventListener('input', () => { notes[inp.dataset.note] = inp.value; }));
        elSel.querySelectorAll('button[data-rm]').forEach(b =>
            b.addEventListener('click', () => {
                const idx = selected.indexOf(b.dataset.rm); if (idx > -1) selected.splice(idx, 1); renderAll();
            }));
        wireSelDrag();
    }
    // Reordenar arrastrando (T-140): pointer events (ratón + táctil), sin librerías. El arrastre se sigue
    // a nivel de `document` (robusto, sin setPointerCapture); durante el arrastre se mueve el nodo en el
    // DOM y al soltar se sincroniza `selected` desde el orden del DOM y se repinta.
    function wireSelDrag() {
        elSel.querySelectorAll('.sl-drag').forEach(handle => {
            handle.addEventListener('pointerdown', (e) => {
                const row = e.target.closest('.sl-sel-row');
                if (!row) return;
                e.preventDefault();
                row.classList.add('dragging');
                const onMove = (ev) => {
                    const y = ev.clientY;
                    const after = [...elSel.querySelectorAll('.sl-sel-row:not(.dragging)')].find(r => {
                        const box = r.getBoundingClientRect();
                        return y < box.top + box.height / 2;
                    });
                    if (after) elSel.insertBefore(row, after);
                    else elSel.appendChild(row);
                };
                const onUp = () => {
                    document.removeEventListener('pointermove', onMove);
                    row.classList.remove('dragging');
                    const order = [...elSel.querySelectorAll('.sl-sel-row')].map(r => r.dataset.sid).filter(Boolean);
                    if (order.length) { selected.length = 0; selected.push(...order); }
                    renderAll();   // re-numera y reasocia notas
                };
                document.addEventListener('pointermove', onMove);
                document.addEventListener('pointerup', onUp, { once: true });
            });
        });
    }
    function renderAll() { renderAvail(); renderSel(); }
    renderAll();

    document.getElementById('sl-save').addEventListener('click', async () => {
        const name = document.getElementById('sl-name').value.trim();
        if (!name) { toast('Pon un nombre al setlist.', 'error'); return; }
        try {
            const items = selected.map(id => ({ song_id: id, note: (notes[id] || '').trim() || null }));
            const res = await apiFetch(
                editing ? `/setlists/${setlistId}` : '/setlists/',
                { method: editing ? 'PATCH' : 'POST',
                  headers: { 'Content-Type': 'application/json' },
                  body: JSON.stringify({ name, items }) });
            if (!res.ok) throw new Error('http');
            toast(editing ? 'Setlist actualizado.' : 'Setlist creado.', 'success');
            loadSetlists();
        } catch (e) { toast(editing ? 'No se pudo actualizar el setlist.' : 'No se pudo crear el setlist.', 'error'); }
    });
}

// ─── Ver / reproducir un setlist ───────────────────────────────────────────
async function openSetlist(id) {
    showDetail();
    elDetail.innerHTML = `<p class="loading-text">Cargando…</p>`;
    let sl;
    try {
        const res = await apiFetch(`/setlists/${id}`);
        if (!res.ok) throw new Error('http');
        sl = await res.json();
    } catch (e) { elDetail.innerHTML = '<p class="loading-text">⚠️ No se pudo abrir el setlist.</p>'; return; }

    const rows = sl.items.map((it, i) => `
        <li class="setlist-song" data-id="${escapeHtml(it.song_id)}" data-pos="${i}">
            <span class="sl-num">${i + 1}</span>
            <span class="sl-title">${escapeHtml(it.title)} <small>${escapeHtml(it.artist || '')}</small>${it.note ? `<br><small class="sl-note-view">${bfIcon('note', { size: 14 })} ${escapeHtml(it.note)}</small>` : ''}</span>
            <button class="setlist-item-btn" data-act="play" title="Reproducir">${bfIcon('play')}</button>
            <button class="setlist-item-btn" data-act="rm" aria-label="Quitar del setlist" title="Quitar">${bfIcon('x')}</button>
        </li>`).join('') || '<li><small>Este setlist está vacío. Edítalo para añadir canciones.</small></li>';

    elDetail.innerHTML = `
        <div class="setlist-editor">
            <a href="#" id="sl-back" class="back-link">← Volver</a>
            <div class="setlist-detail-head">
                <h3>${escapeHtml(sl.name)}</h3>
                ${sl.items.length ? `<button id="sl-playall" class="primary-btn">${bfIcon('play')} Reproducir todo</button>` : ''}
            </div>
            <ul class="setlist-list">${rows}</ul>
        </div>`;
    document.getElementById('sl-back').addEventListener('click', (e) => { e.preventDefault(); loadSetlists(); });

    const playAt = (songId, pos) => {
        window.location.href = `index.html?songId=${encodeURIComponent(songId)}&setlist=${encodeURIComponent(id)}&pos=${pos}`;
    };
    const playAll = document.getElementById('sl-playall');
    if (playAll) playAll.addEventListener('click', () => playAt(sl.items[0].song_id, 0));

    elDetail.querySelectorAll('.setlist-song').forEach(li => {
        const songId = li.dataset.id, pos = parseInt(li.dataset.pos, 10);
        li.querySelector('[data-act="play"]').addEventListener('click', () => playAt(songId, pos));
        li.querySelector('[data-act="rm"]').addEventListener('click', async () => {
            // Enviar items (no song_ids) para PRESERVAR las notas de las demás canciones.
            const items = sl.items.filter(x => x.song_id !== songId)
                .map(x => ({ song_id: x.song_id, note: x.note || null }));
            try {
                const res = await apiFetch(`/setlists/${id}`, {
                    method: 'PATCH', headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ items })
                });
                if (!res.ok) throw new Error('http');
                openSetlist(id);
            } catch (e) { toast('No se pudo quitar la canción.', 'error'); }
        });
    });
}

// ─── Logout opcional reutilizando auth ───────────────────────────────────────
(async () => { await requireAuth(); loadSetlists(); })();
