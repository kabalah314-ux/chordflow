/**
 * auth.js — Autenticación con Supabase (compartido por todas las páginas).
 * Requiere haber cargado antes el SDK de Supabase (window.supabase) por CDN.
 *
 * Expone helpers globales: requireAuth, getToken, apiFetch, signUp/InEmail,
 * signInGoogle, signOut, getUser.
 */

let _sbClient = null;
let _cfg = null;

// Config pública del backend (cacheada). Incluye test_mode.
async function getConfig() {
    if (!_cfg) _cfg = await (await fetch('/config')).json();
    return _cfg;
}

// Sesión de prueba usada solo cuando el backend está en modo test.
const TEST_SESSION = {
    access_token: 'test-token',
    user: { id: 'test-user-0000-0000-0000-000000000000', email: 'test@chordflow.local' }
};

// Crea (una vez) el cliente de Supabase con la config pública del backend
async function getSupabase() {
    if (_sbClient) return _sbClient;
    const cfg = await getConfig();
    if (!cfg.supabase_url || !cfg.supabase_anon_key) {
        throw new Error('Faltan credenciales de Supabase en el servidor (/config)');
    }
    _sbClient = window.supabase.createClient(cfg.supabase_url, cfg.supabase_anon_key, {
        auth: { persistSession: true, autoRefreshToken: true } // recuerda la sesión
    });
    return _sbClient;
}

async function getSession() {
    // En modo test no usamos Supabase: devolvemos una sesión de prueba.
    if ((await getConfig()).test_mode) return TEST_SESSION;
    const sb = await getSupabase();
    const { data } = await sb.auth.getSession();
    return data.session;
}

async function getToken() {
    const s = await getSession();
    return s ? s.access_token : null;
}

async function getUser() {
    const s = await getSession();
    return s ? s.user : null;
}

// Si no hay sesión, redirige al login. Devuelve la sesión si la hay.
async function requireAuth() {
    const s = await getSession();
    if (!s) {
        window.location.href = 'login.html';
        return null;
    }
    return s;
}

async function signUpEmail(email, password) {
    const sb = await getSupabase();
    return sb.auth.signUp({ email, password });
}

async function signInEmail(email, password) {
    const sb = await getSupabase();
    return sb.auth.signInWithPassword({ email, password });
}

async function signInGoogle() {
    const sb = await getSupabase();
    return sb.auth.signInWithOAuth({
        provider: 'google',
        options: { redirectTo: window.location.origin + '/static/library.html' }
    });
}

async function signOut() {
    if (!(await getConfig()).test_mode) {
        const sb = await getSupabase();
        await sb.auth.signOut();
    }
    window.location.href = 'login.html';
}

// fetch que añade automáticamente el token del usuario (para llamar a /songs)
async function apiFetch(url, opts = {}) {
    const token = await getToken();
    opts.headers = Object.assign({}, opts.headers, {
        'Authorization': 'Bearer ' + token
    });
    const res = await fetch(url, opts);
    // Token expirado o inválido: volver al login automáticamente (T-006).
    // En una página que ya es el login, no redirigimos para evitar bucles.
    if (res.status === 401 && !window.location.pathname.endsWith('login.html')) {
        window.location.href = 'login.html';
    }
    return res;
}
