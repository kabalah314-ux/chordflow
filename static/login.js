/**
 * login.js — Lógica de la pantalla de login/registro.
 */
const elForm = document.getElementById('login-form');
const elEmail = document.getElementById('email');
const elPass = document.getElementById('password');
const elMsg = document.getElementById('login-msg');
const elBtnLogin = document.getElementById('btn-login');
const elBtnRegister = document.getElementById('btn-register');
const elBtnGoogle = document.getElementById('btn-google');

function showMsg(text, isError = true) {
    elMsg.textContent = text;
    elMsg.style.color = isError ? '#ff6b6b' : 'var(--accent-color)';
}

// Si ya hay sesión activa, ir directo a la biblioteca
(async () => {
    try {
        const s = await getSession();
        if (s) window.location.href = 'app.html';
    } catch (e) { /* sin conexión a Supabase: dejar el formulario */ }
})();

// Iniciar sesión (email + contraseña)
elForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    showMsg('Entrando…', false);
    try {
        const { error } = await signInEmail(elEmail.value, elPass.value);
        if (error) return showMsg(error.message);
        window.location.href = 'app.html';
    } catch (err) {
        showMsg('No se pudo conectar con el servidor de cuentas.');
    }
});

// Registrarse
elBtnRegister.addEventListener('click', async () => {
    if (!elEmail.value || !elPass.value) return showMsg('Rellena email y contraseña.');
    showMsg('Creando cuenta…', false);
    try {
        const { data, error } = await signUpEmail(elEmail.value, elPass.value);
        if (error) return showMsg(error.message);
        // Si el proyecto exige confirmación por email, no habrá sesión todavía
        if (data.session) {
            window.location.href = 'app.html';
        } else {
            showMsg('Cuenta creada. Revisa tu email para confirmarla y luego entra.', false);
        }
    } catch (err) {
        showMsg('No se pudo conectar con el servidor de cuentas.');
    }
});

// Entrar con Google
elBtnGoogle.addEventListener('click', async () => {
    try {
        const { error } = await signInGoogle();
        if (error) showMsg(error.message);
    } catch (err) {
        showMsg('Google no está disponible (¿proveedor sin configurar?).');
    }
});
