/**
 * shell.js — App shell de BandFlow (T-074, Fase 13, contexto TÚ).
 *
 * Inyecta el lateral fijo (marca + eyebrow "TÚ" + navegación + perfil + toggle de tema)
 * en cualquier página que contenga un contenedor `.bf-shell` con su `<main class="bf-shell-main">`.
 * Requiere haber cargado antes auth.js (requireAuth/apiFetch/signOut) y util.js (toast).
 *
 * El contexto BANDA (banner + pestañas) y el dashboard de Inicio llegan en T-075/T-076.
 */
(function () {
    // ── Tema (usa data-theme, que es lo que lee design-system.css) ──────────────
    const THEME_KEY = 'bf-theme';
    function currentTheme() { return localStorage.getItem(THEME_KEY) === 'light' ? 'light' : 'dark'; }
    function applyTheme(theme) {
        if (theme === 'light') document.documentElement.setAttribute('data-theme', 'light');
        else document.documentElement.removeAttribute('data-theme');
        const icon = document.getElementById('bf-theme-icon');
        const label = document.getElementById('bf-theme-label');
        // El botón ofrece el tema CONTRARIO al activo.
        if (icon) icon.innerHTML = bfIcon(theme === 'light' ? 'moon' : 'sun', { size: 18 });
        if (label) label.textContent = theme === 'light' ? 'Modo oscuro' : 'Modo claro';
    }
    function toggleTheme() {
        const next = currentTheme() === 'light' ? 'dark' : 'light';
        localStorage.setItem(THEME_KEY, next);
        applyTheme(next);
    }
    // Aplicar cuanto antes para minimizar el parpadeo.
    applyTheme(currentTheme());

    // ── Navegación (contexto TÚ). `soon`: página aún no construida (T-076..T-080). ──
    const NAV = [
        { label: 'Inicio',     icon: 'home',     href: 'app.html' },
        { label: 'Afinador / Metrónomo', icon: 'mic', href: 'afinador.html' },   // T-V5-13
        // V6-F9b: Explorar = hub de la red (bolos, salas, profesionales); Canciones = biblioteca global.
        { label: 'Explorar',   icon: 'globe',    href: 'red.html', also: ['biblioteca-global.html', 'ficha.html'] },
        { label: 'Biblioteca', icon: 'library',  href: 'library.html' },
        { label: 'Agenda',     icon: 'calendar', href: 'agenda.html' },
        { label: 'Finanzas',   icon: 'wallet',   href: 'finanzas.html' },
        { label: 'Chat',       icon: 'chat',     href: 'chat.html' },
        { label: 'Bandas',     icon: 'users',    href: 'bands.html' },
        { label: 'Perfil',     icon: 'user',     href: 'profile.html' },
    ];

    function currentPage() {
        return (location.pathname.split('/').pop() || 'app.html').toLowerCase();
    }

    function navItemHtml(n, here) {
        const inner = `<span class="bf-nav-icon">${bfIcon(n.icon)}</span><span>${escapeHtml(n.label)}</span>`;
        if (n.soon) {
            return `<button class="bf-nav-item" data-soon data-label="${escapeHtml(n.label)}">
                ${inner}<span class="bf-nav-soon">Pronto</span></button>`;
        }
        const active = (n.href === here || (n.also || []).includes(here)) ? ' aria-current="page"' : '';
        return `<a class="bf-nav-item" href="${n.href}"${active}>${inner}</a>`;
    }

    function buildSidebar() {
        const here = currentPage();
        const aside = document.createElement('aside');
        aside.className = 'bf-sidebar';
        aside.innerHTML = `
            <a class="bf-brand" href="app.html" aria-label="BandFlow — inicio">
                <span class="bf-brand-mark" aria-hidden="true"><span></span><span></span><span></span></span>
                <span class="bf-brand-name">BandFlow</span>
            </a>
            <button class="bf-nav-item bf-notif-btn" id="bf-search-btn" type="button" aria-label="Buscar (Ctrl K)">
                <span class="bf-nav-icon">${bfIcon('search')}</span><span>Buscar</span><kbd class="bf-kbd">Ctrl K</kbd>
            </button>
            <button class="bf-nav-item bf-notif-btn" id="bf-notif-btn" type="button" aria-label="Avisos">
                <span class="bf-nav-icon">${bfIcon('inbox')}</span><span>Avisos</span>
                <span class="bf-nav-badge" id="bf-notif-badge" hidden>0</span>
            </button>
            <div class="bf-eyebrow">Tú</div>
            <nav class="bf-sidebar-nav" aria-label="Navegación principal">
                ${NAV.map(n => navItemHtml(n, here) + (n.href === 'bands.html' ? '<div class="bf-subnav" id="bf-bands-subnav"></div>' : '')).join('')}
            </nav>
            <div class="bf-sidebar-foot">
                <a class="bf-profile-card" href="profile.html" title="Mi perfil">
                    <span class="bf-avatar" id="bf-prof-initials">··</span>
                    <span class="bf-profile-meta">
                        <span class="bf-profile-name" id="bf-prof-name">Tú</span>
                        <span class="bf-profile-sub">Mi perfil</span>
                    </span>
                    <span class="bf-nav-icon" style="margin-left:auto;color:var(--bf-text-faint)">${bfIcon('settings', { size: 18 })}</span>
                </a>
                <button class="bf-theme-toggle" id="bf-theme-btn" type="button">
                    <span class="bf-nav-icon" id="bf-theme-icon">${bfIcon('sun', { size: 18 })}</span><span id="bf-theme-label">Modo claro</span>
                </button>
                <button class="bf-theme-toggle" id="bf-logout" type="button" title="Cerrar sesión">
                    <span class="bf-nav-icon">${bfIcon('logout', { size: 18 })}</span><span>Cerrar sesión</span>
                </button>
            </div>`;
        return aside;
    }

    // `initialsFrom` es global (util.js, T-121); util.js se carga antes que shell.js en todas
    // las páginas del shell.

    async function loadProfile() {
        try {
            const res = await apiFetch('/profile/me');
            if (!res.ok) return;
            const me = await res.json();
            const name = (me.display_name || '').trim();
            const elName = document.getElementById('bf-prof-name');
            const elIni = document.getElementById('bf-prof-initials');
            if (name && elName) elName.textContent = name;
            if (elIni) {
                if (me.avatar_url) {
                    // Foto de perfil (T-V5-06): llena el círculo del lateral.
                    elIni.innerHTML = `<img class="bf-avatar__img" src="${escapeHtml(me.avatar_url)}" alt="" loading="lazy">`;
                } else {
                    const ini = initialsFrom(name);
                    if (ini) elIni.textContent = ini;
                }
            }
        } catch (e) { /* perfil opcional: el shell funciona sin nombre */ }
    }

    // Banda(s) en el lateral (T-146): sub-items bajo "Bandas" con avatar de color → band.html?id=.
    async function loadBandsNav() {
        const wrap = document.getElementById('bf-bands-subnav');
        if (!wrap) return;
        try {
            const res = await apiFetch('/bands/');
            if (!res.ok) return;
            const bands = await res.json();
            const onBand = currentPage() === 'band.html';
            const activeId = new URLSearchParams(location.search).get('id');
            wrap.innerHTML = bands.map(b => {
                const active = onBand && b.id === activeId ? ' active' : '';
                return `<a class="bf-subnav-item${active}" href="band.html?id=${encodeURIComponent(b.id)}" title="${escapeHtml(b.name)}">
                    <span class="bf-avatar bf-avatar--sm" style="background:${bandColor(b.id)};color:#fff;">${escapeHtml(initialsFrom(b.name) || 'B')}</span>
                    <span class="bf-subnav-name">${escapeHtml(b.name)}</span></a>`;
            }).join('');
            // T-V6-90: con UNA sola banda, sus secciones van directas en el lateral (menos clics).
            if (bands.length === 1) {
                const b = bands[0];
                const SEC = [['agenda', 'Agenda', 'calendar'], ['repertorio', 'Canciones', 'music'],
                             ['setlists', 'Setlists', 'list-music'], ['finanzas', 'Finanzas', 'wallet'], ['chat', 'Chat', 'chat']];
                wrap.insertAdjacentHTML('beforeend', `<div class="bf-subnav-sections">${SEC.map(([k, l, i]) =>
                    `<a class="bf-subnav-item bf-subnav-item--sec" href="band.html?id=${encodeURIComponent(b.id)}#${k}">${bfIcon(i, { size: 14 })}<span class="bf-subnav-name">${l}</span></a>`).join('')}</div>`);
            }
        } catch (e) { /* el lateral funciona sin las sub-bandas */ }
    }

    async function mount() {
        const shell = document.querySelector('.bf-shell');
        if (!shell) return;                 // página sin shell: no hacemos nada
        if (!(await requireAuth())) return; // sin sesión → requireAuth ya redirige a login

        const aside = buildSidebar();
        shell.insertBefore(aside, shell.firstChild);

        // Aplicar el tema otra vez ahora que existen el icono/label del botón.
        applyTheme(currentTheme());
        document.getElementById('bf-theme-btn').addEventListener('click', toggleTheme);
        const logoutBtn = document.getElementById('bf-logout');
        if (logoutBtn) logoutBtn.addEventListener('click', () => signOut());

        // Items "Pronto": avisan en vez de llevar a un 404.
        aside.querySelectorAll('.bf-nav-item[data-soon]').forEach(btn =>
            btn.addEventListener('click', () =>
                toast(`${btn.dataset.label}: próximamente.`, 'info')));

        // ── Drawer móvil: botón ☰ + backdrop ────────────────────────────────────
        // En ≤768px el lateral se oculta; el ☰ lo abre y el backdrop (o tocar un item) lo cierra.
        const hamb = document.createElement('button');
        hamb.className = 'bf-hamburger';
        hamb.type = 'button';
        hamb.setAttribute('aria-label', 'Abrir menú');
        hamb.innerHTML = bfIcon('menu', { size: 22 });
        const backdrop = document.createElement('div');
        backdrop.className = 'bf-backdrop';
        shell.appendChild(backdrop);
        shell.appendChild(hamb);
        const closeNav = () => shell.classList.remove('bf-nav-open');
        hamb.addEventListener('click', () => shell.classList.add('bf-nav-open'));
        backdrop.addEventListener('click', closeNav);
        // Tocar un enlace/elemento de navegación también cierra el drawer.
        aside.addEventListener('click', (e) => { if (e.target.closest('a, .bf-nav-item')) closeNav(); });

        loadProfile();
        loadBandsNav();
        wireNotifications();
        wireSearch();
    }

    // ── T-V6-67: búsqueda global (Ctrl/Cmd + K) ─────────────────────────────────
    const PAGES = [
        { title: 'Inicio', href: 'app.html' }, { title: 'Agenda', href: 'agenda.html' },
        { title: 'Finanzas', href: 'finanzas.html' }, { title: 'Chat', href: 'chat.html' },
        { title: 'Mis bandas', href: 'bands.html' }, { title: 'Biblioteca', href: 'library.html' },
        { title: 'Setlists', href: 'setlists.html' }, { title: 'Explorar: bolos abiertos', href: 'red.html#bolos' },
        { title: 'Explorar: salas', href: 'red.html#salas' }, { title: 'Explorar: profesionales', href: 'red.html#pros' },
        { title: 'Mensajes de Explorar', href: 'red.html#mensajes' }, { title: 'Nueva canción', href: 'editor.html' },
        { title: 'Afinador y metrónomo', href: 'afinador.html' }, { title: 'Mi perfil', href: 'profile.html' },
    ];
    const KIND_ICON = { band: 'users', song: 'music', setlist: 'list-music', event: 'calendar', page: 'arrow-up-right' };
    const KIND_TXT = { band: 'Banda', song: 'Canción', setlist: 'Setlist', event: 'Evento', page: 'Ir a' };
    let paletteOpen = false;
    async function openPalette() {
        if (paletteOpen) return;
        paletteOpen = true;
        let ctrl = null, results = [], sel = 0;
        await bfDialog({
            title: 'Buscar',
            body: `<input class="bf-input" id="bf-pal-q" placeholder="Canciones, setlists, eventos, bandas… o una página" autocomplete="off" autofocus aria-label="Buscar" aria-controls="bf-pal-list">
                   <ul class="bf-pal" id="bf-pal-list" role="listbox"></ul>`,
            actions: [],
            onMount: (root, close) => {
                const q = root.querySelector('#bf-pal-q'), ul = root.querySelector('#bf-pal-list');
                const paint = () => {
                    ul.innerHTML = results.map((r, i) => `<li role="option" aria-selected="${i === sel}"><a href="${escapeHtml(r.href)}" class="${i === sel ? 'is-sel' : ''}">
                        <span class="bf-pal__icon">${bfIcon(KIND_ICON[r.kind] || 'search', { size: 16 })}</span>
                        <span class="bf-pal__text"><strong>${escapeHtml(r.title)}</strong><span class="bf-faint">${escapeHtml(r.subtitle || KIND_TXT[r.kind] || '')}</span></span></a></li>`).join('')
                        || (q.value.trim() ? '<li class="bf-muted" style="padding:.6rem;">Sin resultados.</li>' : '');
                };
                const run = async () => {
                    const term = q.value.trim().toLowerCase();
                    const pages = PAGES.filter(p => !term || p.title.toLowerCase().includes(term)).slice(0, term ? 4 : 8)
                        .map(p => ({ kind: 'page', title: p.title, href: p.href }));
                    results = pages; sel = 0; paint();
                    if (term.length < 2) return;
                    if (ctrl) ctrl.abort();
                    ctrl = new AbortController();
                    const sig = ctrl.signal;
                    try {
                        const res = await apiFetch('/me/search?q=' + encodeURIComponent(term), { signal: sig });
                        if (!res.ok || sig.aborted) return;
                        results = (await res.json()).concat(pages); sel = 0; paint();
                    } catch (e) { /* abortado o sin red */ }
                };
                let t;
                q.addEventListener('input', () => { clearTimeout(t); t = setTimeout(run, 180); });
                q.addEventListener('keydown', (e) => {
                    if (e.key === 'ArrowDown') { e.preventDefault(); sel = Math.min(results.length - 1, sel + 1); paint(); }
                    if (e.key === 'ArrowUp') { e.preventDefault(); sel = Math.max(0, sel - 1); paint(); }
                    if (e.key === 'Enter' && results[sel]) { e.preventDefault(); close(null); location.href = results[sel].href; }
                });
                run();
            },
        });
        paletteOpen = false;
    }
    function wireSearch() {
        const btn = document.getElementById('bf-search-btn');
        if (btn) btn.addEventListener('click', openPalette);
        document.addEventListener('keydown', (e) => {
            if ((e.ctrlKey || e.metaKey) && (e.key === 'k' || e.key === 'K')) { e.preventDefault(); openPalette(); }
        });
    }

    // ── T-V6-61: centro de avisos (campana con contador) ─────────────────────────
    async function refreshBadge() {
        try {
            const res = await apiFetch('/me/notifications');
            if (!res.ok) return null;
            const data = await res.json();
            const b = document.getElementById('bf-notif-badge');
            if (b) { b.hidden = !data.unread; b.textContent = data.unread > 99 ? '99+' : String(data.unread); }
            return data;
        } catch (e) { return null; }
    }
    function wireNotifications() {
        const btn = document.getElementById('bf-notif-btn');
        if (!btn) return;
        refreshBadge();
        setInterval(() => { if (document.visibilityState === 'visible') refreshBadge(); }, 60000);
        btn.addEventListener('click', async () => {
            const data = await refreshBadge();
            if (!data) { toast('No se pudieron cargar los avisos.', 'error'); return; }
            const ICON = { event: 'calendar', poll: 'calendar', note: 'note', gig_application: 'mic',
                           gig_chosen: 'check-circle', message: 'chat' };
            const safeLink = (l) => (l && /^[a-z0-9_-]+\.html([?#][^\s"'<>]*)?$/i.test(l)) ? l : null;
            await bfDialog({
                title: 'Avisos',
                body: data.items.length ? `<ul class="bf-notifs">${data.items.map(n => {
                    const link = safeLink(n.link);
                    const inner = `<span class="bf-notifs__icon">${bfIcon(ICON[n.kind] || 'inbox', { size: 16 })}</span>
                        <span class="bf-notifs__text"><strong>${escapeHtml(n.title)}</strong>${n.body ? `<span>${escapeHtml(n.body)}</span>` : ''}
                        <span class="bf-faint">${escapeHtml(bfDate(n.created_at))}</span></span>`;
                    return `<li class="${n.read_at ? '' : 'is-unread'}">${link ? `<a href="${escapeHtml(link)}">${inner}</a>` : `<div>${inner}</div>`}</li>`;
                }).join('')}</ul>` : bfEmpty('inbox', 'Nada nuevo', 'Aquí verás eventos nuevos, votaciones, candidaturas y mensajes.'),
                actions: [{ label: 'Cerrar', value: null }],
            });
            if (data.unread) {
                try { await apiFetch('/me/notifications/read-all', { method: 'POST' }); } catch (e) { /* luego */ }
                refreshBadge();
            }
        });
    }

    if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', mount);
    else mount();
})();
