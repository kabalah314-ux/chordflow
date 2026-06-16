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

// --- Carga inicial: personal + repertorios de banda en paralelo ---
async function fetchSongs() {
    try {
        const [personal, bands] = await Promise.all([
            apiFetch('/songs/').then(r => (r.ok ? r.json() : [])),
            apiFetch('/bands/').then(r => (r.ok ? r.json() : [])),
        ]);
        const personalTagged = personal.map(s =>
            ({ ...s, _scope: 'personal', _label: 'Personal', _badge: '👤 Personal' }));

        const perBand = await Promise.all(bands.map(b =>
            apiFetch(`/bands/${b.id}/songs/`).then(r => (r.ok ? r.json() : []))
                .then(list => list.map(s =>
                    ({ ...s, _scope: 'band', _bandId: b.id, _label: b.name, _badge: '🎸 ' + b.name })))
        ));

        allSongs = personalTagged.concat(...perBand);
        buildFilters(bands);
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
            elFilters.querySelectorAll('.lib-filter').forEach(b =>
                b.classList.toggle('active', b === btn));
            applyView();
        }));
}

// --- Aplica filtro + búsqueda y renderiza ---
function applyView() {
    const base = currentFilter === 'all'
        ? allSongs
        : currentFilter === 'personal'
            ? allSongs.filter(s => s._scope === 'personal')
            : allSongs.filter(s => s._bandId === currentFilter);
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
                <button class="card-action-btn" data-act="edit" aria-label="Editar ${escapeHtml(song.title)}" title="Editar">✏️</button>
                <button class="card-action-btn danger" data-act="delete" aria-label="Borrar ${escapeHtml(song.title)}" title="Borrar">🗑️</button>
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
