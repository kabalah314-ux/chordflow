/* Service Worker de ChordFlow (PWA, Fase 5).
 * Estrategia conservadora que NO pelea con el cache-busting por hash (T-022):
 *  - Navegaciones HTML → network-first (fresco online; caché como respaldo offline).
 *  - SOLO estáticos versionados (/static/x.js?v=<hash>) → cache-first (+ purga de versiones viejas).
 *  - TODO lo demás (API, /config, /public…) → red, nunca caché (lista blanca, no negra: T-V6-03;
 *    antes una lista negra olvidó /collections y servía datos rancios / de otro usuario).
 */
const CACHE = 'bandflow-static-v3';   // T-V6-03: nombre nuevo → activate purga la caché anterior

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
    if (req.method !== 'GET' || url.origin !== self.location.origin) return;

    // 1) HTML / navegaciones: red primero, caché solo como respaldo offline.
    if (req.mode === 'navigate' || url.pathname.endsWith('.html')) {
        e.respondWith(
            fetch(req).then((r) => {
                const c = r.clone();
                caches.open(CACHE).then((ca) => ca.put(req, c)).catch(() => {});
                return r;
            }).catch(() => caches.match(req))
        );
        return;
    }

    // 2) Solo estáticos versionados por hash van cache-first. El resto, siempre a la red.
    const esEstatico = url.pathname.startsWith('/static/') && url.searchParams.has('v');
    if (!esEstatico) return;

    e.respondWith(
        caches.match(req).then((hit) => hit || fetch(req).then((r) => {
            const c = r.clone();
            caches.open(CACHE).then(async (ca) => {
                await ca.put(req, c);
                // Purga: otras versiones (?v=) del mismo fichero (la caché no crece con cada deploy).
                const keys = await ca.keys();
                for (const k of keys) {
                    const ku = new URL(k.url);
                    if (ku.pathname === url.pathname && ku.search !== url.search) await ca.delete(k);
                }
            }).catch(() => {});
            return r;
        }))
    );
});
