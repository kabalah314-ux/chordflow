/**
 * ChordFlow — Biblioteca unificada (T-077).
 * Lista TODAS mis canciones: personales (GET /songs/) + repertorio de cada una de mis bandas
 * (GET /bands/{id}/songs/), con filtro Todas·Personales·[banda] y búsqueda en vivo.
 * Las de banda son de solo lectura aquí (se reproducen; editar/quitar se hace en el espacio de banda).
 */

const elGrid = document.getElementById('song-grid');
const elSearch = document.getElementById('search-input');
const elFilters = document.getElementById('library-filters');

let allSongs = [];          // caché unificada (cada item lleva _scope/_label/_badge)
let currentFilter = 'all';  // 'all' | 'personal' | <bandId>
let collections = [];        // mis colecciones personales (resúmenes: id/name/song_count)
let currentCollection = null; // colección activa { id, name, songIds } o null (manda sobre el filtro)

// --- Carga inicial: personal + repertorios de banda en paralelo ---
async function fetchSongs() {
    try {
        const [personal, bands, cols] = await Promise.all([
            apiFetch('/songs/').then(r => (r.ok ? r.json() : [])),
            apiFetch('/bands/').then(r => (r.ok ? r.json() : [])),
            apiFetch('/collections/').then(r => (r.ok ? r.json() : [])),
        ]);
        collections = cols;
        const personalTagged = personal.map(s =>
            ({ ...s, _scope: 'personal', _label: 'Personal', _badge: '👤 Personal' }));

        const perBand = await Promise.all(bands.map(b =>
            apiFetch(`/bands/${b.id}/songs/`).then(r => (r.ok ? r.json() : []))
                .then(list => list.map(s =>
                    ({ ...s, _scope: 'band', _bandId: b.id, _label: b.name, _badge: '🎸 ' + b.name })))
        ));

        allSongs = personalTagged.concat(...perBand);
        buildFilters(bands);
        renderCollections();
        applyView();
    } catch (err) {
        console.error(err);
        elGrid.innerHTML = `<p class="loading-text">⚠️ No se pudo conectar con el servidor.</p>`;
    }
}

// --- Filtros (Todas · Personales · una por banda) ---
function buildFilters(bands) {
    if (!elFilters) return;
    const chips = [
        { key: 'all', label: 'Todas' },
        { key: 'personal', label: '👤 Personales' },
        ...bands.map(b => ({ key: b.id, label: '🎸 ' + b.name })),
    ];
    elFilters.innerHTML = chips.map(c =>
        `<button class="lib-filter${c.key === currentFilter ? ' active' : ''}" data-filter="${escapeHtml(c.key)}">${escapeHtml(c.label)}</button>`
    ).join('');
    elFilters.querySelectorAll('.lib-filter').forEach(btn =>
        btn.addEventListener('click', () => {
            currentFilter = btn.dataset.filter;
            currentCollection = null;   // elegir un filtro normal anula la colección activa
            elFilters.querySelectorAll('.lib-filter').forEach(b =>
                b.classList.toggle('active', b === btn));
            renderCollections();
            applyView();
        }));
}

// --- Colecciones personales: grupos temáticos de MIS canciones (sin orden) ---
function renderCollections() {
    const elC = document.getElementById('library-collections');
    if (!elC) return;
    const chips = collections.map(c =>
        `<button class="lib-filter${currentCollection && currentCollection.id === c.id ? ' active' : ''}" data-collection="${escapeHtml(c.id)}">${bfIcon('folder', { size: 14 })} ${escapeHtml(c.name)} <span style="opacity:.6;">${c.song_count}</span></button>`
    ).join('');
    const bar = currentCollection
        ? `<div style="display:flex;gap:.5rem;align-items:center;flex-wrap:wrap;margin-top:.5rem;">
               <span>${bfIcon('folder', { size: 16 })} <strong>${escapeHtml(currentCollection.name)}</strong></span>
               <button class="bf-btn bf-btn--sm" data-act="edit-col">${bfIcon('edit', { size: 16 })} Editar</button>
               <button class="bf-btn bf-btn--sm bf-btn--danger" data-act="del-col">${bfIcon('trash', { size: 16 })} Borrar</button>
           </div>`
        : '';
    elC.innerHTML = `
        <div style="display:flex;flex-wrap:wrap;gap:.4rem;align-items:center;margin:.25rem 0 1rem;">
            <span class="bf-muted" style="font-size:.85rem;">Colecciones:</span>
            ${chips || '<span style="opacity:.6;font-size:.85rem;">ninguna todavía</span>'}
            <button class="lib-filter" data-act="new-col" style="border-style:dashed;">${bfIcon('plus', { size: 14 })} Nueva colección</button>
        </div>${bar}`;
    elC.querySelectorAll('[data-collection]').forEach(btn =>
        btn.addEventListener('click', () => openCollectionView(btn.dataset.collection)));
    const nw = elC.querySelector('[data-act="new-col"]');
    if (nw) nw.addEventListener('click', () => openCollectionModal(null));
    const ed = elC.querySelector('[data-act="edit-col"]');
    if (ed) ed.addEventListener('click', () => openCollectionModal(currentCollection.id));
    const dl = elC.querySelector('[data-act="del-col"]');
    if (dl) dl.addEventListener('click', () => deleteCollection(currentCollection));
}

// Abrir la vista de una colección: el grid muestra solo sus canciones (en orden).
async function openCollectionView(id) {
    try {
        const res = await apiFetch(`/collections/${id}`);
        if (!res.ok) throw new Error('http');
        const col = await res.json();
        currentCollection = { id: col.id, name: col.name, songIds: col.items.map(i => i.song_id) };
        elFilters.querySelectorAll('.lib-filter').forEach(b => b.classList.remove('active'));
        renderCollections();
        applyView();
    } catch (e) { toast('No se pudo abrir la colección.', 'error'); }
}

// Crear (id=null) o editar una colección: nombre + selección (checkboxes) de mis canciones personales.
async function openCollectionModal(id) {
    const editing = !!id;
    const personalSongs = allSongs.filter(s => s._scope === 'personal');
    if (!personalSongs.length) { toast('Primero crea alguna canción personal.', 'info'); return; }
    let existing = null;
    if (editing) {
        try {
            const r = await apiFetch(`/collections/${id}`);
            if (!r.ok) throw new Error('http');
            existing = await r.json();
        } catch (e) { toast('No se pudo cargar la colección.', 'error'); return; }
    }
    const checked = new Set(editing ? (existing.items || []).map(i => i.song_id) : []);
    const overlay = document.createElement('div');
    overlay.className = 'modal-overlay';
    overlay.innerHTML = `
        <div class="modal-card glass-panel" role="dialog" aria-modal="true" style="max-width:520px;">
            <p class="modal-msg">${editing ? 'Editar colección' : 'Nueva colección'}</p>
            <input type="text" id="col-name" class="search-box" placeholder="Nombre (p. ej. Acústico, Bodas…)" maxlength="255" value="${editing ? escapeHtml(existing.name) : ''}">
            <div id="col-picker" style="max-height:240px;overflow-y:auto;margin:.6rem 0;border:1px solid rgba(255,255,255,.12);border-radius:8px;padding:.4rem .6rem;">
                ${personalSongs.map(s => `
                    <label style="display:flex;gap:.5rem;align-items:center;padding:.3rem 0;cursor:pointer;">
                        <input type="checkbox" value="${escapeHtml(s.id)}" ${checked.has(s.id) ? 'checked' : ''}>
                        <span>${escapeHtml(s.title)} <small style="opacity:.6;">${escapeHtml(s.artist || '')}</small></span>
                    </label>`).join('')}
            </div>
            <div class="modal-actions">
                <button class="secondary-btn" data-act="cancel">Cancelar</button>
                <button class="primary-btn" data-act="ok">${editing ? 'Guardar' : 'Crear'}</button>
            </div>
        </div>`;
    const close = () => overlay.remove();
    overlay.addEventListener('click', async (e) => {
        if (e.target === overlay || e.target.getAttribute('data-act') === 'cancel') { close(); return; }
        if (e.target.getAttribute('data-act') !== 'ok') return;
        const name = overlay.querySelector('#col-name').value.trim();
        if (!name) { toast('Pon un nombre a la colección.', 'error'); return; }
        const song_ids = Array.from(overlay.querySelectorAll('#col-picker input:checked')).map(i => i.value);
        close();
        try {
            const res = await apiFetch(editing ? `/collections/${id}` : '/collections/', {
                method: editing ? 'PATCH' : 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name, song_ids }),
            });
            if (!res.ok) throw new Error('http');
            toast(editing ? 'Colección actualizada.' : 'Colección creada.', 'success');
            await reloadCollections();
            if (editing && currentCollection && currentCollection.id === id) openCollectionView(id);
        } catch (e) { toast('No se pudo guardar la colección.', 'error'); }
    });
    document.body.appendChild(overlay);
}

async function deleteCollection(col) {
    const ok = await confirmModal(`¿Borrar la colección "${col.name}"? (Tus canciones no se borran.)`,
        { okText: 'Borrar' });
    if (!ok) return;
    try {
        const res = await apiFetch(`/collections/${col.id}`, { method: 'DELETE' });
        if (!res.ok && res.status !== 204) throw new Error('http');
        currentCollection = null;
        await reloadCollections();
        applyView();
    } catch (e) { toast('No se pudo borrar la colección.', 'error'); }
}

async function reloadCollections() {
    try { collections = await (await apiFetch('/collections/')).json(); } catch (e) { /* mantener */ }
    renderCollections();
}

// --- Aplica filtro + búsqueda y renderiza ---
function applyView() {
    let base;
    if (currentCollection) {
        const byId = Object.fromEntries(allSongs.map(s => [s.id, s]));
        base = currentCollection.songIds.map(id => byId[id]).filter(Boolean);  // sus canciones, en orden
    } else {
        base = currentFilter === 'all'
            ? allSongs
            : currentFilter === 'personal'
                ? allSongs.filter(s => s._scope === 'personal')
                : allSongs.filter(s => s._bandId === currentFilter);
    }
    const q = (elSearch.value || '').trim().toLowerCase();
    const list = q
        ? base.filter(s => (s.title || '').toLowerCase().includes(q)
            || (s.artist || '').toLowerCase().includes(q))
        : base;
    renderGrid(list, q);
}

// --- Render de las tarjetas ---
function renderGrid(songs, query) {
    elGrid.innerHTML = '';

    if (songs.length === 0) {
        if (query) {
            elGrid.innerHTML = `<p class="loading-text">Sin resultados para «${escapeHtml(query)}».</p>`;
        } else if (currentCollection) {
            elGrid.innerHTML = `<p class="loading-text">Esta colección está vacía. Pulsa «✏️ Editar» para añadir canciones.</p>`;
        } else if (currentFilter === 'personal' || (currentFilter === 'all' && allSongs.length === 0)) {
            // Onboarding: no tengo partituras personales (o ninguna en absoluto).
            elGrid.innerHTML = `
                <div class="empty-state">
                    <div class="empty-icon">🎸</div>
                    <h3>Aún no tienes partituras</h3>
                    <p>Crea tu primera canción pegando acordes desde Ultimate Guitar o LaCuerda.</p>
                    <a href="editor.html" class="primary-btn" style="text-decoration:none; margin-top:1rem;">➕ Crear mi primera partitura</a>
                </div>`;
        } else {
            elGrid.innerHTML = `<p class="loading-text">Esta banda aún no tiene canciones en su repertorio.</p>`;
        }
        return;
    }

    songs.forEach(song => {
        const card = document.createElement('div');
        card.className = 'song-card';
        card.dataset.id = song.id;
        const sectionCount = song.section_count ?? 0;
        const isPersonal = song._scope === 'personal';

        card.innerHTML = `
            ${isPersonal ? `<div class="card-actions">
                <button class="card-action-btn" data-act="edit" aria-label="Editar ${escapeHtml(song.title)}" title="Editar">${bfIcon('edit')}</button>
                <button class="card-action-btn danger" data-act="delete" aria-label="Borrar ${escapeHtml(song.title)}" title="Borrar">${bfIcon('trash')}</button>
            </div>` : ''}
            <div class="card-main">
                <h3 class="card-title">${escapeHtml(song.title)}</h3>
                <p class="card-artist">${escapeHtml(song.artist || 'Artista desconocido')}</p>
            </div>
            <div class="card-meta">
                <span class="meta-pill card-source">${escapeHtml(song._badge)}</span>
                <span class="meta-pill">${song.bpm || 120} BPM</span>
                <span class="meta-pill">${sectionCount} ${sectionCount === 1 ? 'sección' : 'secciones'}</span>
            </div>`;

        // Abrir el reproductor al pulsar la tarjeta (salvo en los botones de acción)
        card.addEventListener('click', (e) => {
            if (e.target.closest('.card-action-btn')) return;
            window.location.href = `index.html?songId=${song.id}`;
        });

        if (isPersonal) {
            card.querySelector('[data-act="edit"]').addEventListener('click', () => {
                window.location.href = `editor.html?songId=${song.id}`;
            });
            card.querySelector('[data-act="delete"]').addEventListener('click', () => deleteSong(song));
        }

        elGrid.appendChild(card);
    });
}

// --- Borrado de una canción PERSONAL ---
async function deleteSong(song) {
    const ok = await confirmModal(`¿Borrar "${song.title}"? Esta acción no se puede deshacer.`,
        { okText: 'Borrar', cancelText: 'Cancelar' });
    if (!ok) return;
    try {
        const res = await apiFetch(`/songs/${song.id}`, { method: 'DELETE' });
        if (!res.ok && res.status !== 204) throw new Error('Error al borrar');
        allSongs = allSongs.filter(s => s.id !== song.id);
        applyView();
    } catch (err) {
        console.error(err);
        toast('No se pudo borrar la canción: ' + err.message, 'error');
    }
}

// --- Búsqueda en vivo (respeta el filtro activo) ---
if (elSearch) elSearch.addEventListener('input', applyView);

// `escapeHtml` es global y vive en util.js (cargado antes que este script). Ver T-039.

// Mostrar usuario y cerrar sesión
const elUserEmail = document.getElementById('user-email');
const elBtnLogout = document.getElementById('btn-logout');
if (elBtnLogout) elBtnLogout.addEventListener('click', () => signOut());

// Iniciar: exigir sesión antes de cargar nada
(async () => {
    const session = await requireAuth();
    if (!session) return; // requireAuth ya redirige al login
    const user = session.user;
    if (elUserEmail && user) elUserEmail.textContent = user.email || '';
    fetchSongs();
})();
