/**
 * votar.js — Votación de fechas PÚBLICA (T-V6-82). Sin cuenta: eliges tu nombre de la lista de
 * miembros y marcas Sí / Quizás / No en cada fecha. El enlace (token) lo comparte la banda.
 * Autónoma (sin auth.js/util.js). Todo texto se escapa.
 */
(function () {
    const card = document.getElementById('pub-card');
    const esc = (s) => String(s == null ? '' : s).replace(/[&<>"']/g, (c) =>
        ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
    const fmt = (iso) => {
        const d = new Date(iso);
        return isNaN(d) ? '' : d.toLocaleString('es-ES', { weekday: 'long', day: 'numeric', month: 'long', hour: '2-digit', minute: '2-digit' });
    };
    const LABEL = { yes: 'Sí', maybe: 'Quizás', no: 'No' };
    const token = new URLSearchParams(location.search).get('t');
    const KEY = 'bf-voter-' + token;
    let poll = null;
    let me = null;
    try { me = localStorage.getItem(KEY); } catch (e) { /* sin storage */ }

    function notFound() {
        card.innerHTML = `<h1 class="pub-title">Votación no disponible</h1>
            <p class="bf-muted">El enlace no existe o la banda la ha borrado.</p>`;
    }

    function render() {
        const p = poll;
        const closed = p.status !== 'open';
        const member = p.members.find(m => m.user_id === me);
        card.innerHTML = `
            <span class="pub-type">Votación de fechas</span>
            <h1 class="pub-title">${esc(p.title)}</h1>
            <p class="pub-band">${esc(p.band_name || '')}${p.location ? ' · ' + esc(p.location) : ''}</p>
            ${closed ? '<p class="pub-notice">La votación está cerrada: la banda ya ha elegido fecha.</p>' : `
            <label class="bf-label" for="vt-who">¿Quién eres?</label>
            <select class="bf-input" id="vt-who">
                <option value="">Elige tu nombre…</option>
                ${p.members.map(m => `<option value="${esc(m.user_id)}"${m.user_id === me ? ' selected' : ''}>${esc(m.display_name)}</option>`).join('')}
            </select>`}
            <div class="vt-options">
            ${p.options.map(o => `
                <div class="vt-opt" data-opt="${esc(o.id)}">
                    <div class="vt-opt__date">${esc(fmt(o.starts_at))}</div>
                    <div class="vt-opt__counts"><span class="ev-going">Sí ${o.yes}</span> · <span class="ev-maybe">Quizás ${o.maybe}</span> · No ${o.no}</div>
                    ${closed ? '' : `<div class="vt-opt__btns" role="group" aria-label="Tu respuesta para ${esc(fmt(o.starts_at))}">
                        ${['yes', 'maybe', 'no'].map(s => `<button class="bf-btn bf-btn--sm${member && o.votes[me] === s ? ' bf-btn--primary' : ''}" data-vote="${s}" ${member ? '' : 'disabled'}>${LABEL[s]}</button>`).join('')}
                    </div>`}
                </div>`).join('')}
            </div>
            ${p.pending.length && !closed ? `<p class="bf-faint" style="margin-top:.8rem;">Faltan por votar: ${esc(p.pending.join(', '))}</p>` : ''}
            <div class="pub-cta"><p class="pub-cta__note">¿Tu banda aún organiza los ensayos por WhatsApp?</p>
                <a class="pub-cta__btn" href="app.html">Organízala con BandFlow — gratis</a></div>`;
        const who = document.getElementById('vt-who');
        if (who) who.addEventListener('change', () => {
            me = who.value || null;
            try { if (me) localStorage.setItem(KEY, me); } catch (e) { /* sin storage */ }
            render();
        });
        card.querySelectorAll('[data-opt]').forEach(div => div.querySelectorAll('[data-vote]').forEach(b =>
            b.addEventListener('click', () => vote(div.dataset.opt, b.dataset.vote))));
    }

    async function vote(optionId, status) {
        if (!me) return;
        try {
            const r = await fetch('/public/polls/' + encodeURIComponent(token) + '/votes', {
                method: 'PUT', headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ user_id: me, votes: [{ option_id: optionId, status }] }),
            });
            if (!r.ok) throw new Error(String(r.status));
            poll = await r.json();
            render();
        } catch (e) {
            const n = document.createElement('p');
            n.className = 'pub-notice'; n.textContent = 'No se pudo guardar tu voto. Inténtalo de nuevo.';
            card.prepend(n);
        }
    }

    if (!token) { notFound(); return; }
    fetch('/public/polls/' + encodeURIComponent(token))
        .then((r) => { if (!r.ok) throw new Error('na'); return r.json(); })
        .then((p) => { poll = p; document.title = `${p.title} — Votar fechas`; render(); })
        .catch(notFound);
})();
