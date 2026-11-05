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
    user: { id: '00000000-0000-0000-0000-000000000000', email: 'test@chordflow.local' }
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
        options: { redirectTo: window.location.origin + '/static/app.html' }
    });
}

async function signOut() {
    if (!(await getConfig()).test_mode) {
        const sb = await getSupabase();
        await sb.auth.signOut();
    }
    try {   // T-V6-03: nada del usuario anterior queda en la caché del service worker
        if ('caches' in window) {
            const keys = await caches.keys();
            await Promise.all(keys.map((k) => caches.delete(k)));
        }
    } catch (e) { /* sin Cache API: seguimos */ }
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

// ─── T-V6-15: llamadas a la API con errores normalizados ────────────────────────
// `apiJson(url, opts)` = apiFetch + JSON + errores en castellano. Lanza `ApiError` con
// `.status` y un `.message` apto para el usuario (nunca "[object Object]" ni texto técnico).
class ApiError extends Error {
    constructor(status, message, detail) { super(message); this.status = status; this.detail = detail; }
}
const API_MESSAGES = {
    0: 'Sin conexión. Revisa tu red e inténtalo de nuevo.',
    400: 'La petición no es válida.',
    401: 'Tu sesión ha caducado. Vuelve a entrar.',
    403: 'No tienes permiso para hacer esto.',
    404: 'No lo encontramos (quizá se borró).',
    409: 'Ya existe o está en conflicto.',
    410: 'Este enlace ya no es válido.',
    413: 'Es demasiado grande.',
    422: 'Revisa los datos del formulario.',
    429: 'Demasiadas peticiones seguidas. Espera un momento.',
    502: 'El servicio externo no respondió. Inténtalo de nuevo o prueba otra fuente.',
};
// Traduce el `detail` de FastAPI: texto propio del backend (ya en castellano) o lista de errores
// de validación de Pydantic (422) → frase legible.
function apiErrorMessage(status, detail) {
    if (typeof detail === 'string' && detail && status < 500) return detail;
    if (typeof detail === 'string' && detail && status === 502) return detail;
    if (Array.isArray(detail) && detail.length && detail[0] && detail[0].msg) {
        const campo = (detail[0].loc || []).filter(x => x !== 'body').join('.');
        return 'Revisa los datos' + (campo ? ` (${campo})` : '') + ': ' + detail[0].msg;
    }
    return API_MESSAGES[status] || (status >= 500 ? 'Error en el servidor. Inténtalo de nuevo en un momento.'
                                                 : 'Algo ha fallado. Inténtalo de nuevo.');
}
async function apiJson(url, opts = {}) {
    const o = Object.assign({}, opts);
    if (o.body !== undefined && typeof o.body !== 'string' && !(o.body instanceof FormData)) {
        o.body = JSON.stringify(o.body);
        o.headers = Object.assign({ 'Content-Type': 'application/json' }, o.headers);
    }
    let res;
    try { res = await apiFetch(url, o); }
    catch (e) { throw new ApiError(0, API_MESSAGES[0], null); }
    if (res.status === 204) return null;
    const data = await res.json().catch(() => null);
    if (!res.ok) throw new ApiError(res.status, apiErrorMessage(res.status, data && data.detail), data && data.detail);
    return data;
}
// Mensaje para el usuario de cualquier error (ApiError o Error genérico).
function errorMessage(err, fallback = 'Algo ha fallado. Inténtalo de nuevo.') {
    return (err && err instanceof ApiError && err.message) ? err.message : fallback;
}

// ─── PWA: registrar el service worker (instalable + carga offline del shell) ──
if ('serviceWorker' in navigator) {
    window.addEventListener('load', () => {
        navigator.serviceWorker.register('/static/sw.js').catch(() => { /* sin SW: la app va igual */ });
    });
}
