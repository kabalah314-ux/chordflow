/**
 * catalogo.js — Biblioteca global (Explorar) en `biblioteca-global.html` (V3-F9, T-103).
 *
 * El reclamo de la app (D9): buscar entre muchos artistas; si no está, "ponla aquí" (→ editor, que
 * la publica por defecto). Ver una partitura (preview con la letra recortada), importarla a tu banda
 * o a tus partituras, valorarla y comentarla. Reusa score_render.js para el preview.
 *
 * Seguridad: TODO texto de usuario (título/artista/publicador/comentarios) se escapa con escapeHtml
 * antes de ir al DOM (hallazgo H2 de la revisión ultracode). El `body` de comentarios nunca usa innerHTML crudo.
 */
(function () {
    const root = document.getElementById('catalog');
    if (!root) return;

    let myBands = [];

    function stars(avg, count) {
        const full = Math.round(Number(avg) || 0);
        const s = '★★★★★'.slice(0, full) + '☆☆☆☆☆'.slice(0, 5 - full);
        return `<span title="${Number(avg || 0).toFixed(1)} de 5">${s}</span> <span class="bf-faint">(${count || 0})</span>`;
    }

    function scoreCard(s) {
        return `<li class="setlist-song" data-score="${escapeHtml(s.id)}" style="cursor:pointer;">
            <span class="sl-title">${escapeHtml(s.title)}
                <small>${escapeHtml(s.artist || 'Artista desconocido')} · por ${escapeHtml(s.publisher_name || 'anónimo')}</small></span>
            <span class="bf-faint" style="font-size:var(--bf-fs-xs);">${stars(s.rating_avg, s.rating_count)} · ⬇ ${s.import_count || 0}</span>
        </li>`;
    }

    async function search(q) {
        const list = document.getElementById('cat-results');
        if (!list) return;
        list.innerHTML = '<li><small>Buscando…</small></li>';
        try {
            const res = await apiFetch('/catalog/search?q=' + encodeURIComponent(q || ''));
            if (!res.ok) throw new Error('http');
            const scores = await res.json();
            if (!scores.length) {
                list.innerHTML = `<li>${bfEmpty('globe', q ? 'No encontramos esa canción' : 'El catálogo está empezando',
                    '¿No está la que buscas? <a href="editor.html">Añádela aquí</a> y la subes para todos.')}</li>`;
                return;
            }
            list.innerHTML = scores.map(scoreCard).join('');
            list.querySelectorAll('[data-score]').forEach(li =>
                li.addEventListener('click', () => openDetail(li.dataset.score)));
        } catch (e) {
            list.innerHTML = '<li><small>No se pudo cargar el catálogo.</small></li>';
        }
    }

    async function openDetail(id) {
        let d;
        try {
            const res = await apiFetch(`/catalog/scores/${encodeURIComponent(id)}`);
            if (!res.ok) throw new Error('http');
            d = await res.json();
        } catch (e) { toast('No se pudo abrir la partitura.', 'error'); return; }

        const bandOpts = ['<option value="">Mis partituras (personal)</option>']
            .concat(myBands.map(b => `<option value="${escapeHtml(b.id)}">🎸 ${escapeHtml(b.name)}</option>`)).join('');

        root.innerHTML = `
            <button class="bf-btn bf-btn--sm bf-btn--ghost" id="cat-back" style="margin-bottom:.6rem;">← Explorar</button>
            <div class="bf-band-banner" style="margin-bottom:1rem;">
                <div class="bf-grow" style="min-width:0;">
                    <div class="bf-band-banner__name">${escapeHtml(d.title)}</div>
                    <div class="bf-band-banner__meta">${escapeHtml(d.artist || 'Artista desconocido')} · por ${escapeHtml(d.publisher_name || 'anónimo')} · ${stars(d.rating_avg, d.rating_count)} · ⬇ ${d.import_count || 0}</div>
                </div>
            </div>

            <div class="bf-card bf-stack" style="margin-bottom:1rem;">
                <div class="bf-row bf-wrap" style="gap:.5rem;">
                    <select class="bf-select" id="cat-import-dest" style="max-width:240px;">${bandOpts}</select>
                    <button class="bf-btn bf-btn--primary" id="cat-import">⬇ Importar</button>
                </div>
                <p class="bf-faint" style="font-size:var(--bf-fs-xs);">Al importar obtienes la versión completa (con toda la letra) en tu espacio.</p>
            </div>

            <div class="bf-card" style="margin-bottom:1rem;">
                <h3 class="bf-h3" style="margin-bottom:.5rem;">Tu valoración</h3>
                <div id="cat-stars" class="cat-stars" style="font-size:1.6rem;cursor:pointer;letter-spacing:.15rem;"></div>
                <p class="bf-faint" style="font-size:var(--bf-fs-xs);">¿Es fiel y está completa? Tu voto ayuda a destacar las mejores versiones.</p>
            </div>

            <div class="bf-card" style="margin-bottom:1rem;">
                <h3 class="bf-h3" style="margin-bottom:.5rem;">Vista previa <span class="bf-faint" style="font-size:var(--bf-fs-xs);font-weight:400;">(letra recortada — impórtala para la completa)</span></h3>
                <div id="cat-preview" class="preview-content"></div>
            </div>

            <div class="bf-card bf-stack">
                <h3 class="bf-h3">Comentarios</h3>
                <ul class="setlist-list" id="cat-comments"></ul>
                <div class="bf-row" style="gap:.4rem;">
                    <input class="bf-input" id="cat-comment-input" placeholder="Aporta algo (¿falta un acorde?)…" maxlength="2000">
                    <button class="bf-btn bf-btn--sm bf-btn--primary" id="cat-comment-send">Enviar</button>
                </div>
            </div>`;

        document.getElementById('cat-back').addEventListener('click', renderShell);

        // Preview con la partitura recortada (reusa el render de la joya).
        try { renderScoreInto(document.getElementById('cat-preview'), { sections: d.sections || [] }, 0); }
        catch (e) { document.getElementById('cat-preview').innerHTML = '<p class="bf-faint">Sin vista previa.</p>'; }

        renderStars(id, d.my_rating || 0);
        renderComments(d.comments || []);

        document.getElementById('cat-import').addEventListener('click', async () => {
            const bandId = document.getElementById('cat-import-dest').value || null;
            try {
                const res = await apiFetch(`/catalog/scores/${encodeURIComponent(id)}/import`, {
                    method: 'POST', headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ band_id: bandId }) });
                if (!res.ok) throw new Error('http');
                const out = await res.json();
                toast('Importada a tu espacio ✅', 'success');
                if (out.song_id && !bandId) {
                    setTimeout(() => { window.location.href = `index.html?songId=${out.song_id}`; }, 700);
                }
            } catch (e) { toast('No se pudo importar.', 'error'); }
        });

        const cSend = document.getElementById('cat-comment-send');
        cSend.addEventListener('click', async () => {
            const inp = document.getElementById('cat-comment-input');
            const body = inp.value.trim();
            if (!body) return;
            try {
                const res = await apiFetch(`/catalog/scores/${encodeURIComponent(id)}/comments`, {
                    method: 'POST', headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ body }) });
                if (!res.ok) throw new Error('http');
                inp.value = '';
                openDetail(id);   // recargar para ver el comentario
            } catch (e) { toast('No se pudo comentar.', 'error'); }
        });
    }

    function renderStars(id, mine) {
        const el = document.getElementById('cat-stars');
        if (!el) return;
        el.innerHTML = [1, 2, 3, 4, 5].map(n =>
            `<span data-star="${n}" style="color:${n <= mine ? 'var(--accent-color)' : 'var(--text-secondary)'}">★</span>`).join('');
        el.querySelectorAll('[data-star]').forEach(s => s.addEventListener('click', async () => {
            const stars_ = parseInt(s.dataset.star, 10);
            try {
                const res = await apiFetch(`/catalog/scores/${encodeURIComponent(id)}/rating`, {
                    method: 'PUT', headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ stars: stars_ }) });
                if (!res.ok) throw new Error('http');
                renderStars(id, stars_);
                toast('¡Gracias por tu valoración!', 'success');
            } catch (e) { toast('No se pudo valorar.', 'error'); }
        }));
    }

    function renderComments(comments) {
        const el = document.getElementById('cat-comments');
        if (!el) return;
        if (!comments.length) { el.innerHTML = '<li><small>Sé el primero en comentar.</small></li>'; return; }
        el.innerHTML = comments.map(c => `
            <li class="setlist-song">
                <span class="sl-title">${escapeHtml(c.author_name || 'Anónimo')}
                    <small>${escapeHtml(c.body)}</small></span>
            </li>`).join('');
    }

    function renderShell() {
        root.innerHTML = `
            <div class="bf-stack">
                <div>
                    <h1 class="bf-h1">Explorar 🌍</h1>
                    <p class="bf-muted">El catálogo abierto de BandFlow: busca entre artistas y canciones que sube la comunidad.</p>
                </div>
                <div class="bf-row bf-wrap" style="gap:.5rem;">
                    <input class="bf-input" id="cat-search" placeholder="Busca por canción o artista…" style="max-width:340px;">
                    <button class="bf-btn bf-btn--primary" id="cat-search-btn">Buscar</button>
                    <a class="bf-btn" href="editor.html">➕ ¿No la encuentras? Ponla aquí</a>
                </div>
                <ul class="setlist-list" id="cat-results"></ul>
            </div>`;
        const inp = document.getElementById('cat-search');
        const go = () => search(inp.value.trim());
        document.getElementById('cat-search-btn').addEventListener('click', go);
        inp.addEventListener('keydown', e => { if (e.key === 'Enter') go(); });
        search('');   // carga inicial: lo más popular
    }

    async function init() {
        if (!(await requireAuth())) return;
        try {
            const r = await apiFetch('/bands/');
            if (r.ok) myBands = await r.json();
        } catch (e) { /* importar a personal sigue funcionando */ }
        renderShell();
    }

    init();
})();
