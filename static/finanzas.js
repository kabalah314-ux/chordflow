/**
 * finanzas.js — Finanzas agregadas del contexto TÚ (Fase 13, T-079) en `finanzas.html`.
 *
 * Muestra MI saldo neto en cada una de mis bandas vía `GET /me/balances` (positivo = me deben,
 * negativo = debo). El detalle (movimientos, liquidar) se hace en el espacio de banda (`band.html`).
 * bf-* + util.js (escapeHtml).
 */
(function () {
    const el = document.getElementById('finanzas');
    if (!el) return;

    function fmtMoney(x) { return bfMoney(x); }   // T-V6-36

    function balanceRow(b) {
        const v = Number(b.balance);
        const cls = v > 0 ? 'bf-amount--positive' : (v < 0 ? 'bf-amount--negative' : 'bf-muted');
        const label = v > 0 ? 'te deben' : (v < 0 ? 'debes' : 'al día');
        return `<a class="bf-list-item" href="band.html?id=${encodeURIComponent(b.band_id)}"
                   style="text-decoration:none;color:inherit;">
            <span class="bf-grow">${escapeHtml(b.band_name)}</span>
            <span class="${cls}">${fmtMoney(Math.abs(v))} <span class="bf-faint">${label}</span></span>
        </a>`;
    }

    async function load() {
        if (!(await requireAuth())) return;
        el.innerHTML = bfSkeletonList(4);   // skeleton mientras carga (T-135)
        let balances;
        try {
            const r = await apiFetch('/me/balances');
            if (!r.ok) throw new Error('http');
            balances = await r.json();
        } catch (e) {
            el.innerHTML = '<p class="bf-muted">No se pudieron cargar tus finanzas. Inténtalo de nuevo.</p>';
            return;
        }
        // T-V6-48: resumen global + últimos movimientos de todas mis bandas
        const pos = balances.reduce((a, b) => a + Math.max(0, Number(b.balance) || 0), 0);
        const neg = balances.reduce((a, b) => a + Math.min(0, Number(b.balance) || 0), 0);
        el.innerHTML = `
            <div class="bf-stack">
                <div>
                    <h1 class="bf-h1">Finanzas</h1>
                    <p class="bf-muted">Tu saldo en cada banda.</p>
                </div>
                ${balances.length ? `<div class="fin-kpis">
                    <div class="bf-card"><span class="bf-faint">Te deben</span><strong class="bf-amount--positive">${fmtMoney(pos)}</strong></div>
                    <div class="bf-card"><span class="bf-faint">Debes</span><strong class="bf-amount--negative">${fmtMoney(Math.abs(neg))}</strong></div>
                    <div class="bf-card"><span class="bf-faint">Neto</span><strong>${fmtMoney(pos + neg)}</strong></div>
                </div>` : ''}
                <div class="bf-card">
                    ${balances.length
                        ? `<div class="bf-list" id="finanzas-list">${balances.map(balanceRow).join('')}</div>`
                        : bfEmpty('wallet', 'Sin cuentas todavía',
                            'No estás en ninguna banda con cuentas.',
                            { id: 'finanzas-list', cta: { label: 'Ir a Bandas', href: 'bands.html' } })}
                </div>
                ${balances.length ? '<div class="bf-card bf-stack" id="fin-moves"><h2 class="bf-h3">Últimos movimientos</h2><p class="bf-muted">Cargando…</p></div>' : ''}
            </div>`;
        // Enlaces de cada banda directos a su pestaña de Finanzas (para liquidar)
        el.querySelectorAll('#finanzas-list a[href^="band.html"]').forEach(a => { a.href += '#finanzas'; });
        if (balances.length) loadMoves(balances);
    }

    async function loadMoves(balances) {
        const box = document.getElementById('fin-moves');
        if (!box) return;
        const lists = await Promise.all(balances.slice(0, 8).map(async b => {
            try { const r = await apiFetch(`/bands/${encodeURIComponent(b.band_id)}/transactions`); return r.ok ? (await r.json()).map(t => ({ ...t, band_name: b.band_name, band_id: b.band_id })) : []; }
            catch (e) { return []; }
        }));
        const moves = lists.flat().sort((a, b) => new Date(b.date || b.created_at) - new Date(a.date || a.created_at)).slice(0, 12);
        box.innerHTML = `<h2 class="bf-h3">Últimos movimientos</h2>` + (moves.length
            ? `<div class="bf-list">${moves.map(t => `<a class="bf-list-item" href="band.html?id=${encodeURIComponent(t.band_id)}#finanzas" style="text-decoration:none;color:inherit;">
                <span class="bf-badge">${escapeHtml(t.band_name)}</span>
                <span class="bf-grow">${escapeHtml(t.description || (t.type === 'income' ? 'Ingreso' : 'Gasto'))} <span class="bf-faint">· ${escapeHtml(bfDate(t.date || t.created_at))}</span></span>
                <span class="${t.type === 'income' ? 'bf-amount--positive' : 'bf-amount--negative'}">${t.type === 'income' ? '+' : '−'}${fmtMoney(t.amount)}</span></a>`).join('')}</div>`
            : '<p class="bf-muted">Sin movimientos todavía.</p>');
    }

    load();
})();
