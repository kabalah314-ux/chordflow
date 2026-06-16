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

    function fmtMoney(x) { return Number(x).toFixed(2) + ' €'; }

    function balanceRow(b) {
        const v = Number(b.balance);
        const cls = v > 0 ? 'bf-amount--positive' : (v < 0 ? 'bf-amount--negative' : 'bf-muted');
        const label = v > 0 ? 'te deben' : (v < 0 ? 'debes' : 'al día');
        return `<a class="bf-list-item" href="band.html?id=${encodeURIComponent(b.band_id)}"
                   style="text-decoration:none;color:inherit;">
            <span class="bf-grow">🎸 ${escapeHtml(b.band_name)}</span>
            <span class="${cls}">${fmtMoney(Math.abs(v))} <span class="bf-faint">${label}</span></span>
        </a>`;
    }

    async function load() {
        if (!(await requireAuth())) return;
        let balances;
        try {
            const r = await apiFetch('/me/balances');
            if (!r.ok) throw new Error('http');
            balances = await r.json();
        } catch (e) {
            el.innerHTML = '<p class="bf-muted">⚠️ No se pudieron cargar tus finanzas. Inténtalo de nuevo.</p>';
            return;
        }
        el.innerHTML = `
            <div class="bf-stack">
                <div>
                    <h1 class="bf-h1">Finanzas</h1>
                    <p class="bf-muted">Tu saldo en cada banda.</p>
                </div>
                <div class="bf-card">
                    ${balances.length
                        ? `<div class="bf-list" id="finanzas-list">${balances.map(balanceRow).join('')}</div>`
                        : `<p class="bf-muted" id="finanzas-list">No estás en ninguna banda con cuentas.
                            <a href="bands.html">Entra en una banda</a>.</p>`}
                </div>
            </div>`;
    }

    load();
})();
