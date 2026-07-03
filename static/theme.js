/**
 * theme.js — Aplica el tema claro/oscuro elegido en el shell a páginas que NO llevan shell
 * pero que SÍ deben respetarlo (editor, join). Lee la MISMA clave localStorage `bf-theme`
 * que usa `shell.js` y fija `data-theme` en <html> cuanto antes (design-system.css lo lee).
 *
 * Va en <head> para minimizar el parpadeo (se aplica antes del primer pintado).
 *
 * ⚠️ NO se carga en el reproductor (`index.html`): la joya es "modo escenario", SIEMPRE oscura
 * (decisión D-EST-2, GUIA_MAESTRA_V5 §2.4). Ausencia de este script = tema por defecto (oscuro).
 */
(function () {
    try {
        var t = localStorage.getItem('bf-theme');
        if (t === 'light') document.documentElement.setAttribute('data-theme', 'light');
        else document.documentElement.removeAttribute('data-theme');
    } catch (e) {
        /* localStorage no disponible (modo privado estricto): se queda en el tema por defecto. */
    }
})();
