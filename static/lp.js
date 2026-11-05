/** lp.js — Portada pública (T-V6-68): con sesión, directo a la app. */
(async function () {
    try {
        if (new URLSearchParams(location.search).has('ver')) return;   // ?ver = ver la portada igualmente
        if (await getSession()) location.replace('app.html');
    } catch (e) { /* sin Supabase: se queda la portada */ }
})();
