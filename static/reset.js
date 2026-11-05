/**
 * reset.js — Recuperar contraseña (T-V6-40). Se llega desde el email de Supabase: el SDK lee el
 * token del enlace y abre una sesión de recuperación; aquí se elige la contraseña nueva.
 */
(function () {
    const form = document.getElementById('reset-form');
    const msg = document.getElementById('reset-msg');
    const say = (t, err = true) => { msg.textContent = t; msg.style.color = err ? 'var(--bf-danger, #ff6b6b)' : 'var(--accent-color)'; };
    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        const a = document.getElementById('new-pass').value, b = document.getElementById('new-pass2').value;
        if (a.length < 6) return say('Mínimo 6 caracteres.');
        if (a !== b) return say('Las dos contraseñas no coinciden.');
        try {
            const sb = await getSupabase();
            const { data } = await sb.auth.getSession();
            if (!data.session) return say('El enlace ha caducado. Pide otro desde «¿Has olvidado la contraseña?».');
            const { error } = await sb.auth.updateUser({ password: a });
            if (error) return say(error.message || 'No se pudo cambiar la contraseña.');
            say('Contraseña cambiada. Entrando…', false);
            setTimeout(() => { location.href = 'app.html'; }, 900);
        } catch (err) { say('No se pudo conectar con el servidor de cuentas.'); }
    });
})();
