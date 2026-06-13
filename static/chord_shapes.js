/**
 * chord_shapes.js — Diagramas de acordes de guitarra.
 *
 * getChordShape(nombre) → { frets: [6], baseFret } o null
 *   frets: array de 6 (de la 6ª cuerda/Mi grave a la 1ª/Mi agudo).
 *          -1 = muteada (x), 0 = al aire, n = traste absoluto.
 *
 * Estrategia de cobertura total:
 *   1. Diccionario de acordes ABIERTOS comunes (sonido y digitación reales).
 *   2. Si no está, se genera con FORMAS MÓVILES (cejilla) tipo E-shape / A-shape,
 *      cubriendo mayor, menor, 7, m7 y maj7 en las 12 tonalidades.
 *
 * renderChordDiagramSVG(shape, nombre) → string SVG.
 */

// Semitono de cada nota (0 = C)
const SHAPE_NOTE_INDEX = {
    'C': 0, 'B#': 0, 'C#': 1, 'Db': 1, 'D': 2, 'D#': 3, 'Eb': 3,
    'E': 4, 'Fb': 4, 'F': 5, 'E#': 5, 'F#': 6, 'Gb': 6, 'G': 7,
    'G#': 8, 'Ab': 8, 'A': 9, 'A#': 10, 'Bb': 10, 'B': 11, 'Cb': 11
};

// ─── Acordes abiertos (digitaciones reales) ──────────────────────────────────
// Orden: [6ª(Mi), 5ª(La), 4ª(Re), 3ª(Sol), 2ª(Si), 1ª(Mi)]
const OPEN_CHORDS = {
    'C':     [-1, 3, 2, 0, 1, 0],
    'Cmaj7': [-1, 3, 2, 0, 0, 0],
    'C7':    [-1, 3, 2, 3, 1, 0],
    'A':     [-1, 0, 2, 2, 2, 0],
    'Am':    [-1, 0, 2, 2, 1, 0],
    'A7':    [-1, 0, 2, 0, 2, 0],
    'Am7':   [-1, 0, 2, 0, 1, 0],
    'Amaj7': [-1, 0, 2, 1, 2, 0],
    'G':     [3, 2, 0, 0, 0, 3],
    'G7':    [3, 2, 0, 0, 0, 1],
    'Gmaj7': [3, 2, 0, 0, 0, 2],
    'E':     [0, 2, 2, 1, 0, 0],
    'Em':    [0, 2, 2, 0, 0, 0],
    'E7':    [0, 2, 0, 1, 0, 0],
    'Em7':   [0, 2, 0, 0, 0, 0],
    'Emaj7': [0, 2, 1, 1, 0, 0],
    'D':     [-1, -1, 0, 2, 3, 2],
    'Dm':    [-1, -1, 0, 2, 3, 1],
    'D7':    [-1, -1, 0, 2, 1, 2],
    'Dm7':   [-1, -1, 0, 2, 1, 1],
    'Dmaj7': [-1, -1, 0, 2, 2, 2],
    'F':     [1, 3, 3, 2, 1, 1],   // cejilla en I (E-shape)
    'Fmaj7': [-1, -1, 3, 2, 1, 0],
    'B7':    [-1, 2, 1, 2, 0, 2]
};

// ─── Formas móviles (offsets relativos al traste de cejilla b) ───────────────
// E-shape: raíz en 6ª cuerda. A-shape: raíz en 5ª (6ª muteada).
const MOVABLE = {
    E: {
        major: b => [b, b + 2, b + 2, b + 1, b, b],
        minor: b => [b, b + 2, b + 2, b, b, b],
        dom7:  b => [b, b + 2, b, b + 1, b, b],
        m7:    b => [b, b + 2, b, b, b, b],
        maj7:  b => [b, b + 2, b + 1, b + 1, b, b]
    },
    A: {
        major: b => [-1, b, b + 2, b + 2, b + 2, b],
        minor: b => [-1, b, b + 2, b + 2, b + 1, b],
        dom7:  b => [-1, b, b + 2, b, b + 2, b],
        m7:    b => [-1, b, b + 2, b, b + 1, b],
        maj7:  b => [-1, b, b + 2, b + 1, b + 2, b]
    }
};

// Identifica la "calidad" del acorde a partir del sufijo
function parseQuality(suffix) {
    const s = suffix.trim();
    if (/^(maj7|M7|Δ7?)$/.test(s)) return 'maj7';
    if (/^(m7|min7|-7)$/.test(s)) return 'm7';
    if (/^7$/.test(s)) return 'dom7';
    if (/^(m|min|-)$/.test(s)) return 'minor';
    if (s === '' || /^(maj|M)$/.test(s)) return 'major';
    return null; // sus, dim, aug, add, 9… → sin forma móvil fiable (v1)
}

/**
 * Devuelve la forma de un acorde, o null si no se puede representar.
 */
function getChordShape(name) {
    if (!name) return null;
    // Ignorar el bajo de los acordes con barra (G/B → usamos G para el diagrama)
    const base = name.split('/')[0].trim();

    // 1) Acorde abierto conocido
    if (OPEN_CHORDS[base]) {
        return { frets: OPEN_CHORDS[base].slice(), baseFret: 1 };
    }

    // 2) Forma móvil
    const m = base.match(/^([A-G][#b]?)(.*)$/);
    if (!m) return null;
    const root = SHAPE_NOTE_INDEX[m[1]];
    const quality = parseQuality(m[2]);
    if (root === undefined || !quality) return null;

    // Traste de cejilla para E-shape (raíz en 6ª, Mi=4) y A-shape (raíz en 5ª, La=9)
    let fE = (root - 4 + 12) % 12;
    let fA = (root - 9 + 12) % 12;
    if (fE === 0) fE = 12;
    if (fA === 0) fA = 12;

    // Elegir la forma con el traste más bajo (más cómoda)
    let shape, frets;
    if (fE <= fA) {
        frets = MOVABLE.E[quality](fE);
    } else {
        frets = MOVABLE.A[quality](fA);
    }

    return { frets, baseFret: Math.min(...frets.filter(f => f > 0)) };
}

// ─── Render SVG ──────────────────────────────────────────────────────────────
function renderChordDiagramSVG(shape, name) {
    // El nombre llega como texto del usuario (chord_name) y se inyecta con innerHTML
    // en el popup → escapar para evitar XSS de segundo orden. escapeHtml vive en
    // score_render.js, que index.html carga antes que este archivo.
    const safeName = (typeof escapeHtml === 'function') ? escapeHtml(name) : String(name);
    if (!shape) {
        return `<div class="diagram-none">Sin diagrama para <b>${safeName}</b></div>`;
    }

    const frets = shape.frets;
    const played = frets.filter(f => f > 0);
    const maxFret = played.length ? Math.max(...played) : 0;
    const minFret = played.length ? Math.min(...played) : 0;

    // Ventana de trastes: si todo cabe en los primeros 4, mostramos posición abierta (con cejuela)
    const startFret = maxFret <= 4 ? 0 : minFret;
    const FRETS = 5;

    const ML = 22, MT = 28, SG = 16, FG = 22;
    const W = ML * 2 + 5 * SG;
    const H = MT + FRETS * FG + 16;
    const sx = i => ML + i * SG;          // x de la cuerda i (0 = 6ª/grave)
    const fy = j => MT + j * FG;          // y de la línea de traste j

    let svg = `<svg width="${W}" height="${H}" viewBox="0 0 ${W} ${H}" xmlns="http://www.w3.org/2000/svg">`;

    // Cejuela (nut) gruesa solo en posición abierta
    if (startFret === 0) {
        svg += `<rect x="${sx(0)}" y="${MT - 3}" width="${5 * SG}" height="4" fill="#fff"/>`;
    } else {
        // Etiqueta del traste inicial
        svg += `<text x="${sx(5) + 8}" y="${fy(0) + 14}" fill="#a0a0a0" font-size="11" font-family="monospace">${startFret}</text>`;
    }

    // Trastes horizontales
    for (let j = 0; j <= FRETS; j++) {
        svg += `<line x1="${sx(0)}" y1="${fy(j)}" x2="${sx(5)}" y2="${fy(j)}" stroke="#666" stroke-width="1"/>`;
    }
    // Cuerdas verticales
    for (let i = 0; i < 6; i++) {
        svg += `<line x1="${sx(i)}" y1="${fy(0)}" x2="${sx(i)}" y2="${fy(FRETS)}" stroke="#888" stroke-width="1"/>`;
    }

    // Cejilla: si ≥3 cuerdas comparten el traste más bajo, dibujar barra
    const barreFret = minFret;
    const barreStrings = frets.map((f, i) => (f === barreFret ? i : -1)).filter(i => i >= 0);
    if (barreStrings.length >= 3 && barreFret > 0) {
        const y = fy(barreFret - startFret - 0.5);
        svg += `<rect x="${sx(Math.min(...barreStrings)) - 5}" y="${y - 5}" width="${(Math.max(...barreStrings) - Math.min(...barreStrings)) * SG + 10}" height="10" rx="5" fill="var(--accent-color)"/>`;
    }

    // Marcadores por cuerda
    frets.forEach((f, i) => {
        const x = sx(i);
        if (f === -1) {
            svg += `<text x="${x}" y="${MT - 8}" fill="#a0a0a0" font-size="12" text-anchor="middle" font-family="monospace">×</text>`;
        } else if (f === 0) {
            svg += `<circle cx="${x}" cy="${MT - 12}" r="4" fill="none" stroke="#a0a0a0" stroke-width="1.2"/>`;
        } else {
            const y = fy(f - startFret - 0.5);
            svg += `<circle cx="${x}" cy="${y}" r="5.5" fill="var(--accent-color)"/>`;
        }
    });

    svg += `</svg>`;
    return `<div class="diagram-name">${safeName}</div>${svg}`;
}
