// util.js — utilidades compartidas del frontend de ChordFlow.
//
// Cargar ANTES que cualquier script que use estas funciones (library.js, score_render.js,
// chord_shapes.js). Define globales en `window` (la app usa scripts clásicos, sin módulos).

// ─── Seguridad: escapado de texto del usuario (anti-XSS) ─────────────────────
// Fuente ÚNICA de la verdad (antes duplicada en library.js y score_render.js → T-039).
// La letra, títulos y nombres de acorde vienen del usuario y se inyectan con innerHTML:
// SIEMPRE pasar por aquí antes de meterlos en el DOM. Escapa comillas además de <>&, así
// que es segura tanto en texto como dentro de atributos. Null-safe (null/undefined → '').
function escapeHtml(s) {
    return String(s == null ? '' : s)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#39;');
}

// ─── Identidad visual por banda: color + iniciales — fuente única (T-121) ────
// Derivados del id/nombre, reutilizables en avatar, tarjetas y etiquetas de banda.
// Antes: `hueFromId` encerrado en band.js e `initialsFrom` duplicado (band.js + shell.js).

// Hash determinista del id → matiz HSL 0-359 (misma banda → siempre el mismo color).
function bandHue(id) {
    let h = 0;
    const s = String(id);
    for (let i = 0; i < s.length; i++) h = (h * 31 + s.charCodeAt(i)) % 360;
    return h;
}

// Color HSL de la banda. s/l configurables; por defecto los del banner (55% 48%).
function bandColor(id, { s = 55, l = 48 } = {}) {
    return `hsl(${bandHue(id)} ${s}% ${l}%)`;
}

// 1-2 iniciales en mayúscula a partir de un nombre. Devuelve null si no hay nombre:
// el llamante decide el fallback (p. ej. '🎸' en el avatar de banda).
function initialsFrom(name) {
    const parts = String(name || '').trim().split(/\s+/).filter(Boolean);
    if (!parts.length) return null;
    return parts.slice(0, 2).map(w => w[0]).join('').toUpperCase();
}

// ─── Skeletons de carga (T-135) ──────────────────────────────────────────────
// `n` filas .bf-skeleton (clases en design-system.css) para dar sensación de respuesta inmediata
// mientras llega el fetch. Antes solo el Inicio tenía skeleton; ahora se reutiliza en todas las listas.
function bfSkeletonList(n = 3) {
    return Array.from({ length: Math.max(1, n) },
        () => '<div class="bf-skeleton bf-skeleton--card" style="margin-bottom:.6rem;"></div>').join('');
}

// Microinteracción "pop" (T-137): premia una acción con un breve rebote. Reinicia la animación si ya
// estaba puesta y se autolimpia al terminar (re-disparable). Respeta prefers-reduced-motion vía CSS.
function bfPop(el) {
    if (!el) return;
    el.classList.remove('bf-pop');
    void el.offsetWidth;   // fuerza reflow → reinicia la animación
    el.classList.add('bf-pop');
    el.addEventListener('animationend', () => el.classList.remove('bf-pop'), { once: true });
}

// ─── Toasts y modales (reemplazan alert()/confirm(), T-017) ──────────────────
// Lenguaje glassmorphism (clases en style.css). El texto del usuario SIEMPRE se escapa.

// Aviso no bloqueante que se autodescarta. type: 'info' | 'success' | 'error'.
function toast(message, type = 'info') {
    let cont = document.getElementById('toast-container');
    if (!cont) {
        cont = document.createElement('div');
        cont.id = 'toast-container';
        document.body.appendChild(cont);
    }
    const el = document.createElement('div');
    el.className = `toast toast-${type}`;
    el.setAttribute('role', type === 'error' ? 'alert' : 'status');
    el.innerHTML = escapeHtml(message);
    cont.appendChild(el);
    // Forzar reflow para la transición de entrada y programar la salida.
    requestAnimationFrame(() => el.classList.add('show'));
    setTimeout(() => {
        el.classList.remove('show');
        el.addEventListener('transitionend', () => el.remove(), { once: true });
        setTimeout(() => el.remove(), 400);  // fallback si no hay transitionend
    }, 3500);
}

// Modal de confirmación. Devuelve Promise<boolean> (true = aceptar). Reemplaza confirm().
function confirmModal(message, { okText = 'Aceptar', cancelText = 'Cancelar' } = {}) {
    return new Promise((resolve) => {
        const overlay = document.createElement('div');
        overlay.className = 'modal-overlay';
        overlay.innerHTML = `
            <div class="modal-card glass-panel" role="dialog" aria-modal="true">
                <p class="modal-msg">${escapeHtml(message)}</p>
                <div class="modal-actions">
                    <button class="secondary-btn" data-act="cancel">${escapeHtml(cancelText)}</button>
                    <button class="primary-btn danger" data-act="ok">${escapeHtml(okText)}</button>
                </div>
            </div>`;
        const close = (val) => {
            document.removeEventListener('keydown', onKey);
            overlay.remove();
            resolve(val);
        };
        const onKey = (e) => {
            if (e.key === 'Escape') close(false);
            if (e.key === 'Enter') close(true);
        };
        overlay.addEventListener('click', (e) => {
            if (e.target === overlay) close(false);           // clic fuera = cancelar
            const act = e.target.getAttribute('data-act');
            if (act === 'ok') close(true);
            if (act === 'cancel') close(false);
        });
        document.addEventListener('keydown', onKey);
        document.body.appendChild(overlay);
        const okBtn = overlay.querySelector('[data-act="ok"]');
        if (okBtn) okBtn.focus();
    });
}

// Modal con un input de texto. Devuelve Promise<string|null> (null = cancelar/​vacío).
// Reemplaza prompt(). El texto del usuario se escapa; el valor devuelto va trim().
function promptModal(message, { okText = 'Aceptar', cancelText = 'Cancelar', placeholder = '', value = '' } = {}) {
    return new Promise((resolve) => {
        const overlay = document.createElement('div');
        overlay.className = 'modal-overlay';
        overlay.innerHTML = `
            <div class="modal-card glass-panel" role="dialog" aria-modal="true">
                <p class="modal-msg">${escapeHtml(message)}</p>
                <input type="text" class="search-box" data-act="input"
                       placeholder="${escapeHtml(placeholder)}" value="${escapeHtml(value)}">
                <div class="modal-actions">
                    <button class="secondary-btn" data-act="cancel">${escapeHtml(cancelText)}</button>
                    <button class="primary-btn" data-act="ok">${escapeHtml(okText)}</button>
                </div>
            </div>`;
        const input = overlay.querySelector('[data-act="input"]');
        const close = (val) => {
            document.removeEventListener('keydown', onKey);
            overlay.remove();
            resolve(val);
        };
        const submit = () => { const v = input.value.trim(); close(v || null); };
        const onKey = (e) => {
            if (e.key === 'Escape') close(null);
            if (e.key === 'Enter') submit();
        };
        overlay.addEventListener('click', (e) => {
            if (e.target === overlay) close(null);
            const act = e.target.getAttribute('data-act');
            if (act === 'ok') submit();
            if (act === 'cancel') close(null);
        });
        document.addEventListener('keydown', onKey);
        document.body.appendChild(overlay);
        input.focus();
    });
}

// Modal informativo (un solo botón). Permite HTML controlado (NO escapado): el llamante es
// responsable de escapar cualquier dato de usuario que interpole. Devuelve Promise<void>.
function alertModal(html, { okText = 'Aceptar' } = {}) {
    return new Promise((resolve) => {
        const overlay = document.createElement('div');
        overlay.className = 'modal-overlay';
        overlay.innerHTML = `
            <div class="modal-card glass-panel" role="dialog" aria-modal="true">
                <div class="modal-msg">${html}</div>
                <div class="modal-actions">
                    <button class="primary-btn" data-act="ok">${escapeHtml(okText)}</button>
                </div>
            </div>`;
        const close = () => {
            document.removeEventListener('keydown', onKey);
            overlay.remove();
            resolve();
        };
        const onKey = (e) => { if (e.key === 'Escape' || e.key === 'Enter') close(); };
        overlay.addEventListener('click', (e) => {
            if (e.target === overlay || e.target.getAttribute('data-act') === 'ok') close();
        });
        document.addEventListener('keydown', onKey);
        document.body.appendChild(overlay);
        const okBtn = overlay.querySelector('[data-act="ok"]');
        if (okBtn) okBtn.focus();
    });
}

/**
 * T-152 — Agrega movimientos por temporada (año natural) para una visión económica por temporada.
 * Función PURA y testeable: no toca el DOM ni la red; el llamador formatea los importes.
 * Devuelve `[{ year, income, expense, net }]` ordenado del año más reciente al más antiguo.
 * Usa `date` (o `created_at` como respaldo); ignora movimientos sin fecha válida.
 */
function bfFinanceBySeason(txs) {
    const by = {};
    (txs || []).forEach((t) => {
        const raw = t && (t.date || t.created_at);
        if (!raw) return;
        const year = new Date(raw).getFullYear();
        if (!Number.isFinite(year)) return;
        if (!by[year]) by[year] = { year, income: 0, expense: 0, net: 0 };
        const amt = Number(t.amount) || 0;
        if (t.type === 'income') by[year].income += amt;
        else by[year].expense += amt;
    });
    return Object.values(by)
        .map((s) => ({ ...s, net: s.income - s.expense }))
        .sort((a, b) => b.year - a.year);
}

/**
 * V3-F7 (oEmbed) — Carátula de YouTube a partir de un enlace, sin red ni CORS.
 * `bfYoutubeId` extrae el id de vídeo (11 chars) de las formas comunes de URL; `bfYoutubeThumb`
 * construye la URL de la miniatura (determinista: img.youtube.com). Devuelven null si no es YouTube.
 */
function bfYoutubeId(url) {
    if (!url) return null;
    const m = String(url).match(
        /(?:youtube\.com\/(?:watch\?(?:.*&)?v=|embed\/|shorts\/)|youtu\.be\/)([A-Za-z0-9_-]{11})/);
    return m ? m[1] : null;
}

function bfYoutubeThumb(url) {
    const id = bfYoutubeId(url);
    return id ? `https://img.youtube.com/vi/${id}/hqdefault.jpg` : null;
}
