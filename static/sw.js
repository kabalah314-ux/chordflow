/* Service Worker de ChordFlow (PWA, Fase 5).
 * Estrategia conservadora que NO pelea con el cache-busting por hash (T-022):
 *  - API/auth (songs, import, config, health, supabase…) → siempre red, nunca caché.
 *  - Navegaciones HTML → network-first (fresco online; caché como respaldo offline).
 *  - Estáticos (js/css/png con ?v=<hash>, inmutables) → cache-first.
 */
const CACHE = 'chordflow-shell-v1';

self.addEventListener('install', () => self.skipWaiting());

self.addEventListener('activate', (e) => {
    e.waitUntil(
        caches.keys()
            .then(keys => Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k))))
            .then(() => self.clients.claim())
    );
});

self.addEventListener('fetch', (e) => {
    const req = e.request;
    const url = new URL(req.url);

    // Solo gestionamos GET del mismo origen. POST/API externas (Supabase, OpenRouter, CDN) → red.
    if (req.method !== 'GET' || url.origin !== self.location.origin) return;
    // Endpoints dinámicos: nunca cachear (datos del usuario, auth, config).
    if (/^\/(songs|import|config|health)/.test(url.pathname)) return;

    // HTML / navegaciones: red primero, caché de respaldo si no hay conexión.
    if (req.mode === 'navigate' || url.pathname.endsWith('.html')) {
        e.respondWith(
            fetch(req)
                .then(r => { const c = r.clone(); caches.open(CACHE).then(ca => ca.put(req, c)); return r; })
                .catch(() => caches.match(req))
        );
        return;
    }

    // Estáticos (cache-busted por hash → inmutables): caché primero.
    e.respondWith(
        caches.match(req).then(hit => hit || fetch(req).then(r => {
            const c = r.clone();
            caches.open(CACHE).then(ca => ca.put(req, c));
            return r;
        }))
    );
});
