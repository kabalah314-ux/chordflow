/**
 * profile.js — Mi perfil de músico (Fase 7): nombre visible e instrumentos.
 * El nombre real se muestra luego en la lista de miembros de cada banda (en vez del UUID).
 */
const elForm = document.getElementById('profile-form');

async function init() {
    await requireAuth();
    let p;
    try {
        const res = await apiFetch('/profile/me');
        if (!res.ok) throw new Error('http');
        p = await res.json();
    } catch (e) { elForm.innerHTML = '<p class="loading-text">⚠️ No se pudo cargar el perfil.</p>'; return; }

    const instruments = Array.isArray(p.instruments) ? p.instruments.join(', ') : '';
    elForm.innerHTML = `
        <h3>Datos públicos en tus bandas</h3>
        <label class="field-label" for="pf-name">Nombre visible</label>
        <input type="text" id="pf-name" class="search-box" placeholder="Cómo te ven tus compañeros" value="${escapeHtml(p.display_name || '')}">
        <label class="field-label" for="pf-inst">Instrumentos <small>(separados por comas)</small></label>
        <input type="text" id="pf-inst" class="search-box" placeholder="guitarra, voz, teclado" value="${escapeHtml(instruments)}">
        <div class="form-actions"><button id="pf-save" class="primary-btn">${bfIcon('save')} Guardar perfil</button></div>`;
    document.getElementById('pf-save').addEventListener('click', save);
}

async function save() {
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
    } catch (e) { toast('No se pudo guardar el perfil.', 'error'); }
}

init();
