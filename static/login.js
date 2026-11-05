/**
 * login.js — Entrar / crear cuenta (T-V6-40): pestañas, mostrar contraseña, recuperar contraseña
 * (email de Supabase → reset.html) y vuelta a la página que se quería abrir (bfTakeNext).
 */
const elForm = document.getElementById('login-form');
const elEmail = document.getElementById('email');
const elPass = document.getElementById('password');
const elMsg = document.getElementById('login-msg');
const elBtnLogin = document.getElementById('btn-login');
const elBtnRegister = document.getElementById('btn-register');
const elBtnGoogle = document.getElementById('btn-google');
let mode = 'login';

function showMsg(text, isError = true) {
    elMsg.textContent = text;
    elMsg.style.color = isError ? 'var(--bf-danger, #ff6b6b)' : 'var(--accent-color)';
}

// Mensajes de Supabase en castellano (los más comunes)
function authError(err) {
    const m = (err && err.message || '').toLowerCase();
    if (m.includes('invalid login')) return 'Email o contraseña incorrectos.';
    if (m.includes('email not confirmed')) return 'Confirma tu email (revisa tu bandeja) y vuelve a entrar.';
    if (m.includes('already registered')) return 'Ya hay una cuenta con ese email. Entra o recupera la contraseña.';
    if (m.includes('password')) return 'La contraseña debe tener al menos 6 caracteres.';
    if (m.includes('rate limit')) return 'Demasiados intentos. Espera un momento.';
    return (err && err.message) || 'No se pudo completar. Inténtalo de nuevo.';
}

function setMode(m) {
    mode = m;
    document.querySelectorAll('.login-tabs [data-mode]').forEach(b => {
        const on = b.dataset.mode === m;
        b.classList.toggle('bf-btn--primary', on);
        b.setAttribute('aria-selected', on ? 'true' : 'false');
    });
    elBtnLogin.textContent = m === 'login' ? 'Entrar' : 'Crear cuenta';
    elPass.autocomplete = m === 'login' ? 'current-password' : 'new-password';
    document.getElementById('pw-hint').hidden = m === 'login';
    document.getElementById('btn-forgot').hidden = m !== 'login';
    showMsg('', false);
}
document.querySelectorAll('.login-tabs [data-mode]').forEach(b => b.addEventListener('click', () => setMode(b.dataset.mode)));

// Mostrar/ocultar contraseña
const pwToggle = document.getElementById('pw-toggle');
pwToggle.addEventListener('click', () => {
    const show = elPass.type === 'password';
    elPass.type = show ? 'text' : 'password';
    pwToggle.textContent = show ? 'Ocultar' : 'Ver';
    pwToggle.setAttribute('aria-pressed', show ? 'true' : 'false');
    pwToggle.setAttribute('aria-label', show ? 'Ocultar contraseña' : 'Mostrar contraseña');
});

// Si ya hay sesión activa, ir directo (a donde se iba, o al inicio)
(async () => {
    try {
        const s = await getSession();
        if (s) window.location.href = bfTakeNext();
    } catch (e) { /* sin conexión a Supabase: dejar el formulario */ }
})();

elForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    if (!elEmail.value || !elPass.value) return showMsg('Rellena email y contraseña.');
    elBtnLogin.disabled = true;
    try {
        if (mode === 'login') {
            showMsg('Entrando…', false);
            const { error } = await signInEmail(elEmail.value, elPass.value);
            if (error) return showMsg(authError(error));
            window.location.href = bfTakeNext();
        } else {
            showMsg('Creando cuenta…', false);
            const { data, error } = await signUpEmail(elEmail.value, elPass.value);
            if (error) return showMsg(authError(error));
            if (data.session) window.location.href = bfTakeNext();
            else showMsg('Cuenta creada. Revisa tu email para confirmarla y luego entra.', false);
        }
    } catch (err) {
        showMsg('No se pudo conectar con el servidor de cuentas.');
    } finally {
        elBtnLogin.disabled = false;
    }
});

// Compatibilidad: el botón antiguo "Crear cuenta" sigue funcionando si alguien lo muestra
elBtnRegister.addEventListener('click', () => { setMode('register'); elForm.requestSubmit(); });

// Recuperar contraseña
document.getElementById('btn-forgot').addEventListener('click', async () => {
    if (!elEmail.value) { showMsg('Escribe tu email arriba y vuelve a pulsar.'); elEmail.focus(); return; }
    try {
        const sb = await getSupabase();
        const { error } = await sb.auth.resetPasswordForEmail(elEmail.value, {
            redirectTo: window.location.origin + '/static/reset.html' });
        if (error) return showMsg(authError(error));
        showMsg('Te hemos enviado un email para elegir una contraseña nueva.', false);
    } catch (err) { showMsg('No se pudo enviar el email ahora mismo.'); }
});

// Entrar con Google
elBtnGoogle.addEventListener('click', async () => {
    try {
        const { error } = await signInGoogle();
        if (error) showMsg(authError(error));
    } catch (err) {
        showMsg('Google no está disponible (¿proveedor sin configurar?).');
    }
});
