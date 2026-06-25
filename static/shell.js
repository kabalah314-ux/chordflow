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
        { label: 'Explorar',   icon: 'globe',    href: 'biblioteca-global.html' },
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
        const active = n.href === here ? ' aria-current="page"' : '';
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
            if (name) {
                const elName = document.getElementById('bf-prof-name');
                const elIni = document.getElementById('bf-prof-initials');
                if (elName) elName.textContent = name;
                const ini = initialsFrom(name);
                if (elIni && ini) elIni.textContent = ini;
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
                    <span class="bf-avatar bf-avatar--sm" style="background:${bandColor(b.id)};color:#fff;">${escapeHtml(initialsFrom(b.name) || '🎸')}</span>
                    <span class="bf-subnav-name">${escapeHtml(b.name)}</span></a>`;
            }).join('');
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
    }

    if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', mount);
    else mount();
})();
