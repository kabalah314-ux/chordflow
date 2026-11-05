/**
 * join.js — Invitación de banda por enlace (?code=...). Fase 7 + T-V6-41/80.
 *
 * La previsualización es PÚBLICA: quien abre el enlace ve la banda (logo, miembros, canciones,
 * próximo bolo público) ANTES de tener cuenta. Al pulsar "Unirme": con sesión acepta; sin sesión
 * le lleva a entrar/crear cuenta y VUELVE aquí (bfSaveNext/bfTakeNext de auth.js).
 */
const elBox = document.getElementById('join-box');
const ROLE_LABEL = { admin: 'administrador/a', member: 'miembro', guest: 'invitado/a' };
const BACK_LINK = '<a href="bands.html" class="bf-btn" style="margin-top:1rem;">Ir a mis bandas</a>';

function getCode() {
    return new URLSearchParams(location.search).get('code');
}

function stateView(icon, title, text) {
    elBox.innerHTML = `<div class="empty-icon">${bfIco(icon, 40)}</div><h1 class="bf-h2">${escapeHtml(title)}</h1><p>${text}</p>${BACK_LINK}`;
}

async function init() {
    const code = getCode();
    if (!code) { stateView('link', 'Enlace inválido', 'Falta el código de invitación.'); return; }

    let prev, session = null;
    try { session = await getSession(); } catch (e) { session = null; }
    try {
        const res = await fetch(`/invites/${encodeURIComponent(code)}`);
        if (res.status === 404) { stateView('search', 'Invitación no encontrada', 'El enlace no existe o fue revocado.'); return; }
        if (!res.ok) throw new Error('http');
        prev = await res.json();
    } catch (e) { stateView('alert-circle', 'No se pudo comprobar la invitación', 'Revisa tu conexión e inténtalo de nuevo.'); return; }

    if (!prev.valid) {
        stateView('alert-circle', 'Invitación no disponible',
            `Esta invitación está <strong>${escapeHtml(prev.reason || 'no disponible')}</strong>. Pide una nueva a un admin de la banda.`);
        return;
    }

    const ev = prev.next_public_event;
    const who = (prev.member_names || []).length
        ? `${prev.member_names.map(escapeHtml).join(', ')}${prev.member_count > prev.member_names.length ? ' y más' : ''}`
        : `${prev.member_count} ${prev.member_count === 1 ? 'miembro' : 'miembros'}`;
    const coverStyle = prev.cover_url ? ` style='background-image:url("${prev.cover_url}")'` : '';
    elBox.innerHTML = `
        <div class="bf-band-banner${prev.cover_url ? ' bf-band-banner--cover' : ''} join-banner"${coverStyle}>
            ${bfAvatar({ url: prev.avatar_url, name: prev.band_name, color: bandColor(prev.band_id), extraCls: 'bf-avatar--lg' })}
            <div class="bf-grow" style="min-width:0;"><div class="bf-band-banner__name">${escapeHtml(prev.band_name)}</div>
                <div class="bf-band-banner__meta">${who} · ${prev.song_count} ${prev.song_count === 1 ? 'canción' : 'canciones'}</div></div>
        </div>
        <h1 class="bf-h2" style="margin-top:1rem;">Te han invitado a <em>${escapeHtml(prev.band_name)}</em></h1>
        <p>Entrarás como <strong>${ROLE_LABEL[prev.role_to_grant] || escapeHtml(prev.role_to_grant)}</strong>: agenda, setlists, canciones y chat de la banda en un sitio.</p>
        ${ev ? `<p class="bf-muted">${bfEventIcon(ev.type, 15)} Próximo: <strong>${escapeHtml(ev.title)}</strong> · ${escapeHtml(bfDateLong(ev.starts_at))}</p>` : ''}
        <button id="join-accept" class="bf-btn bf-btn--primary bf-btn--lg" style="margin-top:.8rem;">${session ? 'Unirme a la banda' : 'Entrar o crear cuenta para unirme'}</button>
        ${session ? '' : '<p class="bf-faint" style="margin-top:.5rem;font-size:.85rem;">Es gratis. Al entrar volverás aquí para confirmar.</p>'}`;
    document.getElementById('join-accept').addEventListener('click', () => {
        if (!session) { bfSaveNext(); location.href = 'login.html'; return; }
        accept(code);
    });
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
        location.href = `band.html?id=${encodeURIComponent(m.band_id)}`;
    } catch (e) {
        toast('No se pudo aceptar la invitación.', 'error');
        if (btn) btn.disabled = false;
    }
}

init();
