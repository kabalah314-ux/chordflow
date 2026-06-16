/**
 * join.js — Aceptar una invitación de banda por enlace (?code=...). Fase 7.
 * Previsualiza (nombre + rol + validez) y, al confirmar, llama a /invites/{code}/accept.
 */
const elBox = document.getElementById('join-box');
const ROLE_LABEL = { admin: 'administrador/a', member: 'miembro', guest: 'invitado/a' };

// Salida común para los estados sin acción (enlace inválido/caducado/error): sin esto, el
// usuario quedaba en un callejón salvo por el icono de la cabecera (T-coherencia).
const BACK_LINK = '<a href="bands.html" class="primary-btn" style="text-decoration:none; margin-top:1rem; display:inline-block;">🎸 Ir a mis bandas</a>';

function getCode() {
    return new URLSearchParams(location.search).get('code');
}

async function init() {
    await requireAuth();
    const code = getCode();
    if (!code) { elBox.innerHTML = `<div class="empty-icon">🔗</div><h3>Enlace inválido</h3><p>Falta el código de invitación.</p>${BACK_LINK}`; return; }

    let prev;
    try {
        const res = await apiFetch(`/invites/${encodeURIComponent(code)}`);
        if (res.status === 404) { elBox.innerHTML = `<div class="empty-icon">🔍</div><h3>Invitación no encontrada</h3><p>El enlace no existe o fue revocado.</p>${BACK_LINK}`; return; }
        if (!res.ok) throw new Error('http');
        prev = await res.json();
    } catch (e) { elBox.innerHTML = `<p class="loading-text">⚠️ No se pudo comprobar la invitación.</p>${BACK_LINK}`; return; }

    if (!prev.valid) {
        elBox.innerHTML = `<div class="empty-icon">🚫</div>
            <h3>Invitación no disponible</h3>
            <p>Esta invitación está <strong>${escapeHtml(prev.reason || 'no disponible')}</strong>. Pide una nueva a un admin de la banda.</p>${BACK_LINK}`;
        return;
    }

    elBox.innerHTML = `
        <div class="empty-icon">🎸</div>
        <h3>Te han invitado a <em>${escapeHtml(prev.band_name)}</em></h3>
        <p>Entrarás como <strong>${ROLE_LABEL[prev.role_to_grant] || escapeHtml(prev.role_to_grant)}</strong>.</p>
        <button id="join-accept" class="primary-btn">✅ Unirme a la banda</button>`;
    document.getElementById('join-accept').addEventListener('click', () => accept(code));
}

async function accept(code) {
    const btn = document.getElementById('join-accept');
    if (btn) btn.disabled = true;
    try {
        const res = await apiFetch(`/invites/${encodeURIComponent(code)}/accept`, { method: 'POST' });
        if (res.status === 409) { toast('Ya eras miembro de esta banda.', 'info'); location.href = 'bands.html'; return; }
        if (!res.ok) throw new Error('http');
        const m = await res.json();
        toast('¡Bienvenido a la banda!', 'success');
        location.href = `bands.html`;
    } catch (e) {
        toast('No se pudo aceptar la invitación.', 'error');
        if (btn) btn.disabled = false;
    }
}

init();
