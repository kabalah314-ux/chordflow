/**
 * home.js — Dashboard de Inicio en `app.html` (Fase 13, T-076).
 *
 * Agrega próximos eventos + últimos mensajes de TODAS mis bandas vía `GET /me/dashboard`
 * (cada item con su etiqueta de banda). Requiere auth.js (apiFetch/requireAuth) y util.js
 * (escapeHtml). El shell (shell.js) ya pinta el lateral.
 */
(function () {
    const el = document.getElementById('home');
    if (!el) return;

    const EV_ICON = { rehearsal: '🎼', concert: '🎤', other: '📌' };

    function fmtDate(iso) {
        if (!iso) return '';
        const d = new Date(iso);
        if (isNaN(d)) return '';
        return d.toLocaleString('es-ES',
            { weekday: 'short', day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' });
    }

    // Cuenta atrás compacta hasta una fecha (cliente).
    function hCountdown(iso) {
        if (!iso) return '';
        const ms = new Date(iso).getTime() - Date.now();
        if (isNaN(ms)) return '';
        if (ms < 0) return 'ahora';
        const d = Math.floor(ms / 86400000), h = Math.floor((ms % 86400000) / 3600000);
        if (d >= 1) return `en ${d} ${d === 1 ? 'día' : 'días'}`;
        const m = Math.floor((ms % 3600000) / 60000);
        return h >= 1 ? `en ${h} h ${m} min` : `en ${m} min`;
    }
    function hMoney(x) { return Number(x || 0).toFixed(2) + ' €'; }
    const H_ATT = { yes: '✅ Voy', maybe: '🤔 Quizás', no: '❌ No voy' };

    // Fila de "acceso/paso" reutilizable (onboarding y accesos rápidos).
    function step(href, icon, title, hint) {
        return `<a class="bf-list-item" href="${href}" style="text-decoration:none;color:inherit;">
            <span class="bf-grow">${icon} <strong>${title}</strong>${hint ? ` <span class="bf-faint">— ${hint}</span>` : ''}</span>
            <span class="bf-faint">→</span></a>`;
    }

    function eventItem(e) {
        return `<a class="bf-list-item" href="band.html?id=${encodeURIComponent(e.band_id)}"
                   style="text-decoration:none;color:inherit;">
            <span class="bf-badge">${escapeHtml(e.band_name)}</span>
            <span class="bf-grow">${EV_ICON[e.type] || '📌'} ${escapeHtml(e.title)}
                <span class="bf-faint">· ${escapeHtml(fmtDate(e.starts_at))}</span></span>
        </a>`;
    }

    function msgItem(m) {
        return `<a class="bf-list-item" href="band.html?id=${encodeURIComponent(m.band_id)}"
                   style="text-decoration:none;color:inherit;">
            <span class="bf-badge">${escapeHtml(m.band_name)}</span>
            <span class="bf-grow">${m.is_pinned ? '📌 ' : ''}<strong>${escapeHtml(m.author_name || 'Alguien')}</strong>: ${escapeHtml(m.body)}</span>
        </a>`;
    }

    // Skeleton mientras carga (T-087): da sensación de respuesta inmediata.
    function renderSkeleton() {
        el.innerHTML = `
            <div class="bf-stack">
                <div><div class="bf-skeleton bf-skeleton--title"></div></div>
                <div class="bf-card">
                    <div class="bf-skeleton bf-skeleton--text" style="width:50%"></div>
                    <div class="bf-skeleton bf-skeleton--card" style="margin-top:.75rem"></div>
                </div>
                <div class="bf-card">
                    <div class="bf-skeleton bf-skeleton--text" style="width:40%"></div>
                    <div class="bf-skeleton bf-skeleton--card" style="margin-top:.75rem"></div>
                </div>
            </div>`;
    }

    async function load() {
        renderSkeleton();
        if (!(await requireAuth())) return;
        let data, name = '', bands = [], balances = [];
        try {
            const [rd, rp, rb, rbal] = await Promise.all([
                apiFetch('/me/dashboard'), apiFetch('/profile/me'),
                apiFetch('/bands/'), apiFetch('/me/balances')]);
            if (!rd.ok) throw new Error('http');
            data = await rd.json();
            if (rp.ok) { const me = await rp.json(); name = (me.display_name || '').trim(); }
            if (rb.ok) bands = await rb.json();
            if (rbal.ok) balances = await rbal.json();
        } catch (e) {
            el.innerHTML = '<p class="bf-muted">⚠️ No se pudo cargar tu inicio. Inténtalo de nuevo.</p>';
            return;
        }
        const events = data.upcoming_events || [];
        const msgs = data.recent_messages || [];

        // Primeros pasos: si aún no estás en ninguna banda, guía al recién llegado con acciones
        // claras en vez de un panel vacío y band-céntrico que no sabe qué hacer.
        if (!bands.length) {
            el.innerHTML = `
                <div class="bf-stack">
                    <div>
                        <h1 class="bf-h1">¡Te damos la bienvenida${name ? ', ' + escapeHtml(name) : ''}! 👋</h1>
                        <p class="bf-muted">BandFlow es tu cuartel general como músico. Empieza por aquí:</p>
                    </div>
                    <div class="bf-card"><div class="bf-list" id="home-onboarding">
                        ${step('library.html', '🎸', 'Añade tu primera canción', 'pega acordes o impórtalos de internet')}
                        ${step('bands.html', '👥', 'Crea o únete a una banda', 'repertorio, agenda y cuentas compartidos')}
                        ${step('biblioteca-global.html', '🌍', 'Explora la biblioteca global', 'miles de partituras de la comunidad')}
                    </div></div>
                </div>`;
            return;
        }
        // Inicio = panel de control (Opción A, hero protagonista): el próximo bolo manda, y debajo
        // una rejilla con saldo total, accesos rápidos y últimos mensajes.
        const next = events[0];
        const totalBal = balances.reduce((a, b) => a + Number(b.balance || 0), 0);
        const balCls = totalBal > 0 ? 'pos' : (totalBal < 0 ? 'neg' : '');

        const hero = next ? `
            <div class="home-hero">
                <div class="home-hero__when">${escapeHtml(hCountdown(next.starts_at))}</div>
                <div class="home-hero__title">${EV_ICON[next.type] || '📌'} ${escapeHtml(next.title)}</div>
                <div class="home-hero__meta">
                    <span class="bf-badge">${escapeHtml(next.band_name)}</span>
                    <span class="bf-faint">· ${escapeHtml(fmtDate(next.starts_at))}</span>
                </div>
                <div class="home-hero__att" id="home-att" data-band="${escapeHtml(next.band_id)}" data-ev="${escapeHtml(next.id)}">
                    <span class="bf-faint" style="font-size:.82rem;">¿Vas?</span>
                    ${['yes', 'maybe', 'no'].map(s => `<button class="bf-btn bf-btn--sm${next.my_status === s ? ' bf-btn--primary' : ''}" data-att="${s}">${H_ATT[s]}</button>`).join('')}
                    <a class="bf-btn bf-btn--sm" href="band.html?id=${encodeURIComponent(next.band_id)}" style="text-decoration:none;margin-left:auto;">Abrir banda →</a>
                </div>
            </div>` : `
            <div class="home-hero home-hero--empty">
                <div class="home-hero__title">Sin bolos a la vista 🎸</div>
                <p class="bf-muted" style="margin-top:.3rem;">No tienes eventos próximos. <a href="bands.html">Crea uno en tu banda</a>.</p>
            </div>`;

        const balanceCard = `
            <a class="bf-card bs-summary__balance bs-summary__balance--${balCls}" href="finanzas.html"
               style="text-decoration:none;color:inherit;display:block;">
                <h2 class="bf-h3">Tu saldo total</h2>
                <div class="bs-summary__amount">${hMoney(totalBal)}</div>
                <p class="bf-faint" style="font-size:.78rem;">${totalBal > 0 ? 'Te deben' : (totalBal < 0 ? 'Debes' : 'Estás en paz')} · ver Finanzas →</p>
            </a>`;

        const quickCard = `
            <div class="bf-card bf-stack">
                <h2 class="bf-h3">Accesos rápidos</h2>
                <div class="bf-list">
                    ${step('agenda.html', '📅', 'Agenda', 'tus próximos bolos y ensayos')}
                    ${step('finanzas.html', '💶', 'Finanzas', 'saldos y movimientos')}
                    ${step('library.html', '🎸', 'Biblioteca', 'tus canciones y las de tus bandas')}
                </div>
            </div>`;

        const msgCard = `
            <div class="bf-card bf-stack">
                <h2 class="bf-h3">Últimos mensajes</h2>
                ${msgs.length
                    ? `<div class="bf-list" id="home-messages">${msgs.slice(0, 5).map(msgItem).join('')}</div>`
                    : bfEmpty('chat', 'Sin mensajes',
                        'Aún no hay mensajes recientes en tus bandas.', { id: 'home-messages' })}
            </div>`;

        el.innerHTML = `
            <div class="bf-stack">
                <div>
                    <h1 class="bf-h1">Hola${name ? ', ' + escapeHtml(name) : ''} 👋</h1>
                    <p class="bf-muted">Tu cuartel general.</p>
                </div>
                ${hero}
                <div class="bf-grid">${balanceCard}${quickCard}${msgCard}</div>
            </div>`;

        // "¿Vas?" del hero: marca asistencia (PUT) y recarga el Inicio.
        const att = document.getElementById('home-att');
        if (att) att.querySelectorAll('[data-att]').forEach(b => b.addEventListener('click', async () => {
            bfPop(b);   // microinteracción (T-137)
            try {
                const res = await apiFetch(`/bands/${att.dataset.band}/events/${att.dataset.ev}/attendance`, {
                    method: 'PUT', headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ status: b.dataset.att }) });
                if (!res.ok) throw new Error('http');
                load();
            } catch (e) { toast('No se pudo guardar tu asistencia.', 'error'); }
        }));
    }

    load();
})();
