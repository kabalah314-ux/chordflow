/**
 * profile.js — Mi perfil de músico.
 * T-154 (V4-F6, parte cliente): identidad — avatar, mis bandas como chips con rol (GET /bands/) e
 * instrumentos como chips — además del formulario de edición (nombre + instrumentos).
 * T-V5-06 (Storage): foto de perfil real — "Cambiar foto" sube a Supabase Storage (upload.js) y
 * guarda `avatar_url` vía PUT /profile/me (parche parcial).
 */
const elForm = document.getElementById('profile-form');
const ROLE_LABEL = { admin: 'Admin', member: 'Miembro', guest: 'Invitado' };

async function init() {
    await requireAuth();
    let p;
    try {
        const res = await apiFetch('/profile/me');
        if (!res.ok) throw new Error('http');
        p = await res.json();
    } catch (e) { elForm.innerHTML = '<p class="loading-text">No se pudo cargar el perfil.</p>'; return; }

    let bands = [];
    try {
        const rb = await apiFetch('/bands/');   // mis bandas con mi rol; el cuerpo del perfil funciona sin ellas
        if (rb.ok) bands = await rb.json();
    } catch (e) { /* opcional */ }

    render(p, bands);
}

function render(p, bands) {
    const name = (p.display_name || '').trim();
    const instruments = Array.isArray(p.instruments) ? p.instruments : [];
    const color = bandColor(p.id || name || 'músico');

    const bandChips = bands.length ? bands.map(b => `
        <a class="pf-band-chip" href="band.html?id=${encodeURIComponent(b.id)}" title="${escapeHtml(b.name)}">
            <span class="bf-avatar bf-avatar--sm" style="background:${bandColor(b.id)};color:#fff;">${escapeHtml(initialsFrom(b.name) || 'B')}</span>
            <span class="pf-band-chip__name">${escapeHtml(b.name)}</span>
            <span class="bf-badge bf-badge--${b.role}">${ROLE_LABEL[b.role] || escapeHtml(b.role)}</span>
        </a>`).join('')
        : bfEmpty('users', 'Aún no estás en ninguna banda', 'Crea una o únete con un enlace de invitación.');

    const instChips = instruments.length
        ? instruments.map(i => `<span class="bf-badge pf-inst-chip">${escapeHtml(i)}</span>`).join('')
        : '<p class="bf-muted">Aún no has añadido instrumentos.</p>';

    elForm.innerHTML = `
        <div class="pf-identity">
            ${bfAvatar({ url: p.avatar_url, name: name || 'músico', color, extraCls: 'bf-avatar--lg' })}
            <div class="pf-identity__meta">
                <h2 class="pf-name">${name ? escapeHtml(name) : 'Sin nombre todavía'}</h2>
                <p class="bf-muted">${bands.length} ${bands.length === 1 ? 'banda' : 'bandas'} · ${instruments.length} ${instruments.length === 1 ? 'instrumento' : 'instrumentos'}</p>
                <button type="button" class="bf-btn bf-btn--sm bf-btn--ghost" id="pf-photo">${bfIcon('user', { size: 14 })} ${p.avatar_url ? 'Cambiar foto' : 'Añadir foto'}</button>
            </div>
        </div>

        <h3 class="pf-section-title">Mis bandas</h3>
        <div class="pf-band-list" id="pf-bands">${bandChips}</div>

        <h3 class="pf-section-title">Instrumentos</h3>
        <div class="pf-chip-row" id="pf-instruments">${instChips}</div>

        <h3 class="pf-section-title">Editar</h3>
        <label class="field-label" for="pf-name">Nombre visible</label>
        <input type="text" id="pf-name" class="search-box" placeholder="Cómo te ven tus compañeros" value="${escapeHtml(name)}">
        <label class="field-label" for="pf-inst">Instrumentos <small>(separados por comas)</small></label>
        <input type="text" id="pf-inst" class="search-box" placeholder="guitarra, voz, teclado" value="${escapeHtml(instruments.join(', '))}">
        <div class="form-actions"><button id="pf-save" class="primary-btn">${bfIcon('save')} Guardar perfil</button></div>

        <h3 class="pf-section-title">En la red</h3>
        <p class="bf-muted">¿Tienes una sala o das servicios a músicos (foto, sonido, estudio…)? Crea tu ficha y aparece en Explorar.</p>
        <div class="bf-row bf-wrap" style="gap:.5rem;"><a class="bf-btn" href="red.html#mios">${bfIcon('map-pin', { size: 15 })} Mis perfiles en la red</a></div>

        <h3 class="pf-section-title">Cuenta</h3>
        <div class="bf-row bf-wrap" style="gap:.5rem;">
            <button type="button" class="bf-btn" id="pf-cal">${bfIcon('calendar', { size: 15 })} Ver mis eventos en mi calendario</button>
            <button type="button" class="bf-btn" id="pf-export">${bfIcon('download', { size: 15 })} Descargar mis datos</button>
            <button type="button" class="bf-btn bf-btn--danger" id="pf-delete">${bfIcon('trash', { size: 15 })} Borrar mi cuenta</button>
        </div>
        <div class="bf-row bf-wrap" style="gap:.5rem;margin-top:.5rem;">
            <button type="button" class="bf-btn bf-btn--sm" id="pf-pass">Cambiar contraseña</button>
            <button type="button" class="bf-btn bf-btn--sm" id="pf-email">Cambiar email</button>
            <button type="button" class="bf-btn bf-btn--sm bf-btn--ghost" id="pf-signout-all">Cerrar sesión en todos los dispositivos</button>
        </div>`;

    document.getElementById('pf-save').addEventListener('click', () => save(p, bands));
    // T-V6-50: cuenta (Supabase Auth). En modo test no hay Supabase real.
    const sbOrWarn = async () => {
        if ((await getConfig()).test_mode) { toast('No disponible en modo test.', 'info'); return null; }
        return getSupabase();
    };
    document.getElementById('pf-pass').addEventListener('click', async () => {
        const v = await bfDialog({ title: 'Cambiar contraseña',
            body: `<div class="bf-stack"><label class="bf-label" for="pf-np">Nueva contraseña (mínimo 6)</label><input class="bf-input" type="password" id="pf-np" autocomplete="new-password"></div>`,
            actions: [{ label: 'Cancelar', value: null }, { label: 'Guardar', primary: true, onClick: (root) => {
                const x = root.querySelector('#pf-np').value; if (x.length < 6) { toast('Mínimo 6 caracteres.', 'error'); return false; } return x; } }] });
        if (!v) return;
        const sb = await sbOrWarn(); if (!sb) return;
        const { error } = await sb.auth.updateUser({ password: v });
        toast(error ? (error.message || 'No se pudo cambiar.') : 'Contraseña cambiada.', error ? 'error' : 'success');
    });
    document.getElementById('pf-email').addEventListener('click', async () => {
        const v = await promptModal('Nuevo email (te llegará un enlace para confirmarlo)', { okText: 'Cambiar' });
        if (!v) return;
        const sb = await sbOrWarn(); if (!sb) return;
        const { error } = await sb.auth.updateUser({ email: v });
        toast(error ? (error.message || 'No se pudo cambiar.') : 'Revisa tu bandeja para confirmar el email nuevo.', error ? 'error' : 'success');
    });
    document.getElementById('pf-signout-all').addEventListener('click', async () => {
        if (!(await confirmModal('¿Cerrar la sesión en todos tus dispositivos (también en este)?', { okText: 'Cerrar sesiones' }))) return;
        const sb = await sbOrWarn(); if (!sb) return;
        try { await sb.auth.signOut({ scope: 'global' }); } catch (e) { /* sigue */ }
        location.href = 'login.html';
    });

    // T-V6-62 / T-V6-65: calendario, exportar y borrar cuenta
    document.getElementById('pf-cal').addEventListener('click', () => bfSubscribeCalendar());
    document.getElementById('pf-export').addEventListener('click', async () => {
        try {
            const res = await apiFetch('/me/export');
            if (!res.ok) throw new Error('http');
            const blob = new Blob([JSON.stringify(await res.json(), null, 2)], { type: 'application/json' });
            const a = document.createElement('a');
            a.href = URL.createObjectURL(blob);
            a.download = `bandflow-mis-datos-${new Date().toISOString().slice(0, 10)}.json`;
            document.body.appendChild(a); a.click(); a.remove();
            setTimeout(() => URL.revokeObjectURL(a.href), 2000);
        } catch (e) { toast('No se pudieron exportar tus datos.', 'error'); }
    });
    document.getElementById('pf-delete').addEventListener('click', async () => {
        const v = await bfDialog({
            title: 'Borrar mi cuenta',
            body: `<div class="bf-stack"><p>Se borran tus canciones y setlists personales, tus fichas de la red y tu nombre. Sales de tus bandas: si eras el único admin, el admin pasa al miembro más antiguo (y si estabas solo, la banda se archiva).</p>
                <p class="bf-muted">Lo que compartiste con tus bandas (canciones del repertorio, mensajes, movimientos) se queda en la banda. Descarga antes tus datos si los quieres.</p>
                <label class="bf-label" for="pf-del-confirm">Escribe BORRAR para confirmar</label><input class="bf-input" id="pf-del-confirm" autocomplete="off"></div>`,
            actions: [{ label: 'Cancelar', value: null }, { label: 'Borrar mi cuenta', danger: true,
                onClick: (root) => root.querySelector('#pf-del-confirm').value.trim().toUpperCase() === 'BORRAR' ? 'ok' : (toast('Escribe BORRAR.', 'error'), false) }],
        });
        if (v !== 'ok') return;
        try {
            const res = await apiFetch('/me/delete-account', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ confirm: 'BORRAR' }) });
            if (!res.ok) throw new Error('http');
            toast('Tu cuenta se ha borrado. ¡Hasta pronto!', 'success');
            setTimeout(() => signOut(), 1200);
        } catch (e) { toast('No se pudo borrar la cuenta.', 'error'); }
    });

    // Foto de perfil (T-V5-06): subir a Storage y guardar solo avatar_url (parche parcial).
    document.getElementById('pf-photo').addEventListener('click', () =>
        bfPickAndUploadImage('avatar', 512, async (url) => {
            const res = await apiFetch('/profile/me', {
                method: 'PUT', headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ avatar_url: url })
            });
            if (!res.ok) { toast('No se pudo guardar la foto.', 'error'); return; }
            toast('Foto de perfil actualizada.', 'success');
            render({ ...p, avatar_url: url }, bands);
        }));
}

async function save(p, bands) {
    const display_name = document.getElementById('pf-name').value.trim();
    const instruments = document.getElementById('pf-inst').value
        .split(',').map(s => s.trim()).filter(Boolean);
    try {
        const res = await apiFetch('/profile/me', {
            method: 'PUT', headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ display_name: display_name || null, instruments })
        });
        if (!res.ok) throw new Error('http');
        toast('Perfil guardado.', 'success');
        render({ ...p, display_name: display_name || null, instruments }, bands);  // refrescar avatar/chips
    } catch (e) { toast('No se pudo guardar el perfil.', 'error'); }
}

init();
