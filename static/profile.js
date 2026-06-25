/**
 * profile.js — Mi perfil de músico.
 * T-154 (V4-F6, parte cliente sin Storage): el perfil muestra identidad — avatar de iniciales/color
 * (T-121), mis bandas como chips con rol (GET /bands/) e instrumentos como chips — además del
 * formulario de edición (nombre + instrumentos). La subida de avatar real depende de T-153 (Storage).
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
    } catch (e) { elForm.innerHTML = '<p class="loading-text">⚠️ No se pudo cargar el perfil.</p>'; return; }

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
    const initials = initialsFrom(name) || '🎸';
    const color = bandColor(p.id || name || 'músico');

    const bandChips = bands.length ? bands.map(b => `
        <a class="pf-band-chip" href="band.html?id=${encodeURIComponent(b.id)}" title="${escapeHtml(b.name)}">
            <span class="bf-avatar bf-avatar--sm" style="background:${bandColor(b.id)};color:#fff;">${escapeHtml(initialsFrom(b.name) || '🎸')}</span>
            <span class="pf-band-chip__name">${escapeHtml(b.name)}</span>
            <span class="bf-badge bf-badge--${b.role}">${ROLE_LABEL[b.role] || escapeHtml(b.role)}</span>
        </a>`).join('')
        : bfEmpty('users', 'Aún no estás en ninguna banda', 'Crea una o únete con un enlace de invitación.');

    const instChips = instruments.length
        ? instruments.map(i => `<span class="bf-badge pf-inst-chip">${escapeHtml(i)}</span>`).join('')
        : '<p class="bf-muted">Aún no has añadido instrumentos.</p>';

    elForm.innerHTML = `
        <div class="pf-identity">
            <span class="bf-avatar bf-avatar--lg" style="background:${color};color:#fff;">${escapeHtml(initials)}</span>
            <div class="pf-identity__meta">
                <h2 class="pf-name">${name ? escapeHtml(name) : 'Sin nombre todavía'}</h2>
                <p class="bf-muted">${bands.length} ${bands.length === 1 ? 'banda' : 'bandas'} · ${instruments.length} ${instruments.length === 1 ? 'instrumento' : 'instrumentos'}</p>
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
        <div class="form-actions"><button id="pf-save" class="primary-btn">${bfIcon('save')} Guardar perfil</button></div>`;

    document.getElementById('pf-save').addEventListener('click', () => save(p, bands));
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
