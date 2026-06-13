/**
 * ChordFlow — Biblioteca
 * Lista todas las canciones como tarjetas y permite abrir el reproductor.
 */

const elGrid = document.getElementById('song-grid');
const elSearch = document.getElementById('search-input');

let allSongs = []; // Caché local para filtrar sin volver a pedir a la API

// --- Carga inicial ---
async function fetchSongs() {
    try {
        const res = await apiFetch('/songs/');
        if (!res.ok) throw new Error('Error al cargar canciones');
        allSongs = await res.json();
        renderGrid(allSongs);
    } catch (err) {
        console.error(err);
        elGrid.innerHTML = `<p class="loading-text">⚠️ No se pudo conectar con el servidor.</p>`;
    }
}

// --- Render de las tarjetas ---
function renderGrid(songs) {
    elGrid.innerHTML = '';

    if (songs.length === 0) {
        elGrid.innerHTML = `
            <div class="empty-state">
                <div class="empty-icon">🎸</div>
                <h3>Aún no tienes partituras</h3>
                <p>Crea tu primera canción pegando acordes desde Ultimate Guitar o LaCuerda.</p>
                <a href="editor.html" class="primary-btn" style="text-decoration:none; margin-top:1rem;">➕ Crear mi primera partitura</a>
            </div>`;
        return;
    }

    songs.forEach(song => {
        const card = document.createElement('div');
        card.className = 'song-card';
        card.dataset.id = song.id;

        // El listado /songs/ es ligero (SongSummary): trae `section_count`, no la
        // estructura `sections` (T-010). Fallback a 0 si no viniera.
        const sectionCount = song.section_count ?? 0;

        card.innerHTML = `
            <div class="card-actions">
                <button class="card-action-btn" data-act="edit" title="Editar">✏️</button>
                <button class="card-action-btn danger" data-act="delete" title="Borrar">🗑️</button>
            </div>
            <div class="card-main">
                <h3 class="card-title">${escapeHtml(song.title)}</h3>
                <p class="card-artist">${escapeHtml(song.artist || 'Artista desconocido')}</p>
            </div>
            <div class="card-meta">
                <span class="meta-pill">${song.bpm || 120} BPM</span>
                <span class="meta-pill">${sectionCount} ${sectionCount === 1 ? 'sección' : 'secciones'}</span>
            </div>`;

        // Abrir el reproductor al pulsar la tarjeta (salvo en los botones de acción)
        card.addEventListener('click', (e) => {
            if (e.target.closest('.card-action-btn')) return;
            window.location.href = `index.html?songId=${song.id}`;
        });

        // Editar
        card.querySelector('[data-act="edit"]').addEventListener('click', () => {
            window.location.href = `editor.html?songId=${song.id}`;
        });

        // Borrar
        card.querySelector('[data-act="delete"]').addEventListener('click', () => {
            deleteSong(song);
        });

        elGrid.appendChild(card);
    });
}

// --- Borrado de una canción ---
async function deleteSong(song) {
    const ok = confirm(`¿Borrar "${song.title}"?\nEsta acción no se puede deshacer.`);
    if (!ok) return;

    try {
        const res = await apiFetch(`/songs/${song.id}`, { method: 'DELETE' });
        if (!res.ok && res.status !== 204) throw new Error('Error al borrar');

        // Quitar de la caché local y re-renderizar respetando el filtro actual
        allSongs = allSongs.filter(s => s.id !== song.id);
        const q = elSearch.value.trim().toLowerCase();
        const list = q
            ? allSongs.filter(s => (s.title || '').toLowerCase().includes(q) || (s.artist || '').toLowerCase().includes(q))
            : allSongs;
        renderGrid(list);
    } catch (err) {
        console.error(err);
        alert('No se pudo borrar la canción: ' + err.message);
    }
}

// --- Búsqueda en vivo ---
elSearch.addEventListener('input', () => {
    const q = elSearch.value.trim().toLowerCase();
    if (!q) {
        renderGrid(allSongs);
        return;
    }
    const filtered = allSongs.filter(s =>
        (s.title || '').toLowerCase().includes(q) ||
        (s.artist || '').toLowerCase().includes(q)
    );
    renderGrid(filtered);
});

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
