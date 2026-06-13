// util.js — utilidades compartidas del frontend de ChordFlow.
//
// Cargar ANTES que cualquier script que use estas funciones (library.js, score_render.js,
// chord_shapes.js). Define globales en `window` (la app usa scripts clásicos, sin módulos).

// ─── Seguridad: escapado de texto del usuario (anti-XSS) ─────────────────────
// Fuente ÚNICA de la verdad (antes duplicada en library.js y score_render.js → T-039).
// La letra, títulos y nombres de acorde vienen del usuario y se inyectan con innerHTML:
// SIEMPRE pasar por aquí antes de meterlos en el DOM. Escapa comillas además de <>&, así
// que es segura tanto en texto como dentro de atributos. Null-safe (null/undefined → '').
function escapeHtml(s) {
    return String(s == null ? '' : s)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#39;');
}
