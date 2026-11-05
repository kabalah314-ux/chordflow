/**
 * ficha.js — Ficha pública de sala/profesional (`?id=`) o de banda con dossier público (`?banda=`)
 * (V6-F9b, I-16/I-21/I-22/I-24). Se ve sin sesión; con sesión: Contactar / Proponernos, Valorar
 * (si hubo trato) y Reportar. Nunca muestra el teléfono en público (lo decide el backend).
 */
(function () {
    const card = document.getElementById('pub-card');
    const qs = new URLSearchParams(location.search);
    const proId = qs.get('id'), bandId = qs.get('banda');
    const KIND = {
        venue: 'Sala / local', booker: 'Booker / manager', photographer: 'Fotografía', video: 'Vídeo',
        sound_tech: 'Técnico de sonido', light_tech: 'Técnico de luces', studio: 'Estudio de grabación',
        rehearsal_room: 'Local de ensayo', luthier: 'Luthier / reparación', design: 'Diseño / merch',
        press: 'Prensa / promo', teacher: 'Profesor/a', other: 'Otros servicios',
    };
    const DEAL = { fee: 'Caché fijo', door: 'Taquilla', percent: 'Porcentaje', free: 'Gratis + consumo', other: 'A convenir' };
    let session = null;

    const chips = (arr) => (arr || []).map(s => `<span class="bf-chip">${escapeHtml(s)}</span>`).join('');
    const links = (arr) => (arr || []).map(l => `<a class="bf-btn bf-btn--sm bf-btn--ghost" href="${escapeHtml(l.url)}" target="_blank" rel="noopener nofollow">${escapeHtml(l.label)}</a>`).join(' ');
    const photos = (arr) => (arr || []).length ? `<div class="fc-photos">${arr.map(u => `<img src="${escapeHtml(u)}" alt="" loading="lazy">`).join('')}</div>` : '';
    const reviews = (rs) => rs.length ? `<h2 class="sheet-h">Valoraciones</h2><ul class="fc-reviews">${rs.map(r => `<li>
        <strong>${'★'.repeat(r.stars)}${'☆'.repeat(5 - r.stars)}</strong> <span class="bf-faint">${escapeHtml(r.author_name || '')}</span>
        ${r.body ? `<p>${escapeHtml(r.body)}</p>` : ''}</li>`).join('')}</ul>` : '';

    function notFound() {
        card.innerHTML = `<h1 class="pub-title">Ficha no disponible</h1><p class="bf-muted">No existe o su dueño la ha retirado.</p>
            <a class="pub-cta__btn" href="red.html">Ver salas y profesionales</a>`;
    }

    async function contact(url, title, placeholder, bands) {
        if (!session) { location.href = 'login.html'; return; }
        const r = await bfDialog({
            title,
            body: `<div class="bf-stack">
                ${bands && bands.length ? `<div><label class="bf-label" for="fc-as">En nombre de</label>
                  <select class="bf-input" id="fc-as"><option value="">Solo yo</option>${bands.map(b => `<option value="${escapeHtml(b.id)}">${escapeHtml(b.name)}</option>`).join('')}</select></div>` : ''}
                <textarea class="bf-textarea" id="fc-msg" rows="5" maxlength="4000" placeholder="${escapeHtml(placeholder)}" autofocus></textarea></div>`,
            actions: [{ label: 'Cancelar', value: null }, { label: 'Enviar', primary: true, onClick: (root) => {
                const body = root.querySelector('#fc-msg').value.trim();
                if (!body) { toast('Escribe un mensaje.', 'error'); return false; }
                const as = root.querySelector('#fc-as');
                return { body, as_band_id: as && as.value ? as.value : null };
            } }],
        });
        if (!r) return;
        try {
            const t = await apiJson(url, { method: 'POST', body: r });
            toast('Mensaje enviado.', 'success');
            location.href = `red.html#mensajes/${encodeURIComponent(t.id)}`;
        } catch (e) { toast(errorMessage(e, 'No se pudo enviar.'), 'error'); }
    }

    async function report(kind, id) {
        if (!session) { location.href = 'login.html'; return; }
        const reason = await promptModal('¿Qué pasa con esta ficha? (perfil falso, spam, contenido inapropiado…)', { okText: 'Reportar' });
        if (!reason) return;
        try { await apiJson('/reports', { method: 'POST', body: { target_kind: kind, target_id: id, reason } }); toast('Gracias. Lo revisaremos.', 'success'); }
        catch (e) { toast(errorMessage(e), 'error'); }
    }

    async function renderPro() {
        let p;
        try {
            const res = session ? await apiFetch('/pros/' + encodeURIComponent(proId)) : await fetch('/public/pros/' + encodeURIComponent(proId));
            if (!res.ok) throw new Error('na');
            p = await res.json();
        } catch (e) { notFound(); return; }
        let calls = [];
        if (p.kind === 'venue' || p.kind === 'booker') {
            try { calls = (await (await fetch('/public/gig-calls?limit=50&q=' + encodeURIComponent(p.name))).json()).filter(c => c.pro_profile_id === p.id); } catch (e) { calls = []; }
        }
        let myBands = [];
        if (session) { try { myBands = await apiJson('/bands/'); } catch (e) { myBands = []; } }
        document.title = `${p.name} — BandFlow`;
        card.innerHTML = `
            <span class="pub-type">${escapeHtml(KIND[p.kind] || p.kind)}${p.verified ? ' · Verificada' : ''}</span>
            <h1 class="pub-title">${escapeHtml(p.name)}</h1>
            <p class="pub-band">${[p.zone, p.capacity ? `Aforo ${p.capacity}` : '', p.price_hint].filter(Boolean).map(escapeHtml).join(' · ')}
               ${p.rating_count ? ` · ★ ${p.rating_avg} (${p.rating_count})` : ''}</p>
            ${photos(p.photos)}
            ${p.bio ? `<p style="white-space:pre-line;">${escapeHtml(p.bio)}</p>` : ''}
            <div class="rd-chips">${chips((p.styles || []).concat(p.services || []))}</div>
            ${p.deal_types && p.deal_types.length ? `<p class="bf-muted">Condiciones habituales: ${p.deal_types.map(d => escapeHtml(DEAL[d] || d)).join(', ')}</p>` : ''}
            ${p.backline ? `<h2 class="sheet-h">Equipo</h2><p style="white-space:pre-line;">${escapeHtml(p.backline)}</p>` : ''}
            ${p.address ? `<p>${escapeHtml(p.address)} · <a href="https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(p.address)}" target="_blank" rel="noopener">Mapa</a></p>` : ''}
            ${p.phone ? `<p>Teléfono: <a href="tel:${escapeHtml(p.phone)}">${escapeHtml(p.phone)}</a></p>` : ''}
            <div class="bf-row bf-wrap" style="gap:.4rem;margin:.8rem 0;">${links(p.links)}</div>
            ${calls.length ? `<h2 class="sheet-h">Bolos abiertos</h2><ul class="fc-calls">${calls.map(c => `<li><a href="red.html#bolos">${escapeHtml(c.title)}</a>
                <span class="bf-faint">${c.starts_at ? escapeHtml(bfDate(c.starts_at)) : 'Fecha a convenir'}</span></li>`).join('')}</ul>` : ''}
            <div class="bf-row bf-wrap" style="gap:.5rem;margin-top:1rem;">
                ${p.is_mine ? `<a class="bf-btn bf-btn--primary" href="red.html#mios">Editar mi ficha</a>` : `
                <button class="bf-btn bf-btn--primary" id="fc-contact">${p.kind === 'venue' ? 'Proponer a mi banda' : 'Contactar'}</button>
                <button class="bf-btn bf-btn--sm bf-btn--ghost" id="fc-report">Reportar</button>`}
                <button class="bf-btn bf-btn--sm" id="fc-share">Compartir</button>
            </div>
            ${reviews(p.reviews)}
            ${session ? '' : `<div class="pub-cta"><p class="pub-cta__note">¿Tienes banda? Encuentra bolos y profesionales cerca.</p>
                <a class="pub-cta__btn" href="login.html">Entrar en BandFlow — gratis</a></div>`}
            <p class="bf-faint rd-legal">BandFlow conecta, no intermedia pagos ni contratos.</p>`;
        const c = document.getElementById('fc-contact');
        if (c) c.addEventListener('click', () => contact(`/pros/${encodeURIComponent(p.id)}/contact`,
            p.kind === 'venue' ? `Proponer a ${p.name}` : `Contactar con ${p.name}`,
            p.kind === 'venue' ? 'Somos…, tocamos…, os proponemos fechas…' : 'Hola, necesitamos…', myBands));
        const rp = document.getElementById('fc-report');
        if (rp) rp.addEventListener('click', () => report('pro', p.id));
        document.getElementById('fc-share').addEventListener('click', () => bfShare({ title: p.name, text: `${p.name} en BandFlow`, url: location.href }));
    }

    async function renderBand() {
        let b;
        try {
            const res = await fetch('/public/bands/' + encodeURIComponent(bandId));
            if (!res.ok) throw new Error('na');
            b = await res.json();
        } catch (e) { notFound(); return; }
        const e = b.epk || {};
        document.title = `${b.name} — BandFlow`;
        card.innerHTML = `
            <span class="pub-type">Banda${e.formation ? ' · ' + escapeHtml(e.formation) : ''}</span>
            <h1 class="pub-title">${escapeHtml(b.name)}</h1>
            <p class="pub-band">${[e.zone, e.fee_hint].filter(Boolean).map(escapeHtml).join(' · ')}${b.rating_count ? ` · ★ ${b.rating_avg} (${b.rating_count})` : ''}</p>
            ${photos(e.photos)}
            ${e.bio ? `<p style="white-space:pre-line;">${escapeHtml(e.bio)}</p>` : ''}
            <div class="rd-chips">${chips(e.styles)}</div>
            <div class="bf-row bf-wrap" style="gap:.4rem;margin:.8rem 0;">${links(e.links)}</div>
            ${b.upcoming.length ? `<h2 class="sheet-h">Próximos conciertos</h2><ul class="fc-calls">${b.upcoming.map(ev => `<li><a href="evento.html?id=${encodeURIComponent(ev.id)}">${escapeHtml(ev.title)}</a>
                <span class="bf-faint">${escapeHtml(bfDate(ev.starts_at))}</span></li>`).join('')}</ul>` : ''}
            <div class="bf-row bf-wrap" style="gap:.5rem;margin-top:1rem;">
                <button class="bf-btn bf-btn--primary" id="fc-contact">Contactar con la banda</button>
                <button class="bf-btn bf-btn--sm bf-btn--ghost" id="fc-report">Reportar</button>
                <button class="bf-btn bf-btn--sm" id="fc-share">Compartir</button>
            </div>
            ${reviews(b.reviews)}
            <p class="bf-faint rd-legal">BandFlow conecta, no intermedia pagos ni contratos.</p>`;
        document.getElementById('fc-contact').addEventListener('click', () => contact(`/network/bands/${encodeURIComponent(b.id)}/contact`,
            `Contactar con ${b.name}`, 'Hola, os escribimos desde…'));
        document.getElementById('fc-report').addEventListener('click', () => report('band', b.id));
        document.getElementById('fc-share').addEventListener('click', () => bfShare({ title: b.name, text: `${b.name} en BandFlow`, url: location.href }));
    }

    (async () => {
        try { session = await getSession(); } catch (e) { session = null; }
        if (proId) renderPro();
        else if (bandId) renderBand();
        else notFound();
    })();
})();
