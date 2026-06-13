/**
 * score_render.js — Render compartido de partituras + transposición.
 * Lo usan tanto el reproductor (app.js) como la vista previa del editor (editor.js),
 * para que lo que ves al pegar sea EXACTAMENTE lo que verás al tocar.
 *
 * No depende del DOM global: recibe el contenedor donde pintar.
 */

// ─── Transposición ───────────────────────────────────────────────────────────
const SCALE = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B'];
const NOTE_INDEX = {
    'C': 0, 'B#': 0, 'C#': 1, 'Db': 1, 'D': 2, 'D#': 3, 'Eb': 3,
    'E': 4, 'Fb': 4, 'F': 5, 'E#': 5, 'F#': 6, 'Gb': 6, 'G': 7,
    'G#': 8, 'Ab': 8, 'A': 9, 'A#': 10, 'Bb': 10, 'B': 11, 'Cb': 11
};

function transposeNote(note, semis) {
    const idx = NOTE_INDEX[note];
    if (idx === undefined) return note;
    return SCALE[(((idx + semis) % 12) + 12) % 12];
}

// Transpone un acorde preservando sufijo (m7, sus4…) y bajo (G/B → A/C#)
function transposeChord(chord, semis) {
    if (!semis) return chord;
    return chord.split('/').map(part => {
        const m = part.match(/^([A-G][#b]?)(.*)$/);
        if (!m) return part;
        return transposeNote(m[1], semis) + m[2];
    }).join('/');
}

// `escapeHtml` (anti-XSS) es global y vive en util.js, cargado antes que este script.
// Fuente única de la verdad; antes estaba duplicada aquí y en library.js (ver T-039).

/**
 * Construye el HTML de una línea de letra con sus acordes flotando en su columna.
 * Clave: las posiciones (char_position) son índices del texto ORIGINAL, así que
 * escapamos cada segmento de texto por separado e insertamos solo HTML de acorde
 * ya saneado (chordSpan). Así el escapado no descuadra la alineación.
 */
function renderLyricWithChords(content, chords, transposeOffset) {
    content = content || '';
    const sorted = [...(chords || [])].sort((a, b) => (a.char_position || 0) - (b.char_position || 0));
    let html = '';
    let cursor = 0;
    sorted.forEach(chord => {
        let pos = Math.min(Math.max(chord.char_position || 0, 0), content.length);
        if (pos < cursor) pos = cursor; // dos acordes en la misma columna: no retroceder
        html += escapeHtml(content.substring(cursor, pos));
        html += chordSpan(chord, transposeOffset);
        cursor = pos;
    });
    html += escapeHtml(content.substring(cursor));
    return html;
}

// ─── Render de la partitura ──────────────────────────────────────────────────
/**
 * Pinta una canción (o el resultado del parser {sections:[...]}) dentro de un
 * contenedor. Los acordes sin `id` (vista previa) simplemente no llevan id.
 *
 * @param {HTMLElement} container  Donde inyectar el HTML
 * @param {Object} song            { sections: [...] }
 * @param {number} transposeOffset Semitonos a transponer (0 = original)
 */
function renderScoreInto(container, song, transposeOffset = 0) {
    container.innerHTML = '';
    if (!song || !song.sections) return;

    song.sections.forEach(sec => {
        const secDiv = document.createElement('div');
        secDiv.className = 'section-block';

        if (sec.name) {
            const secName = document.createElement('div');
            secName.className = 'section-name';
            secName.textContent = sec.name;
            secDiv.appendChild(secName);
        }

        if (!sec.lines) {
            container.appendChild(secDiv);
            return;
        }

        // ── Iterar con lookahead para fusionar chord_only + lyric ──
        let i = 0;
        const lines = sec.lines;
        while (i < lines.length) {
            const line = lines[i];

            // Caso A: línea de acordes (chord_only)
            if (line.type === 'chord_only') {
                const nextLine = lines[i + 1];
                const nextIsLyric = nextLine && nextLine.type === 'lyric';

                if (nextIsLyric && (nextLine.chords || []).length === 0) {
                    // Fusionar: acordes encima de la letra siguiente
                    const lineDiv = document.createElement('div');
                    lineDiv.className = 'line-lyric';
                    lineDiv.innerHTML = renderLyricWithChords(nextLine.content, line.chords || [], transposeOffset);
                    secDiv.appendChild(lineDiv);
                    i += 2;
                } else {
                    // Chord_only puro (Intro): fila de pills
                    const lineDiv = document.createElement('div');
                    lineDiv.className = 'line-chord-only';

                    if (line.chords && line.chords.length > 0) {
                        line.chords.forEach(chord => lineDiv.appendChild(chordPill(chord.chord_name, chord.id, transposeOffset)));
                    } else if (line.content) {
                        line.content.replace(/:/g, ' ').split(/\s+/).filter(w => w.length > 0)
                            .forEach(word => lineDiv.appendChild(chordPill(word, null, transposeOffset)));
                    }

                    secDiv.appendChild(lineDiv);
                    i++;
                }

            // Caso B: línea de letra con acordes incrustados
            } else if (line.type === 'lyric') {
                const lineDiv = document.createElement('div');
                lineDiv.className = 'line-lyric';
                lineDiv.innerHTML = renderLyricWithChords(line.content, line.chords || [], transposeOffset);
                secDiv.appendChild(lineDiv);
                i++;

            } else {
                i++;
            }
        }

        container.appendChild(secDiv);
    });
}

// Acorde flotante (span) — devuelve HTML string para inyectar en la letra.
// chord_name viene del usuario: escapar tanto en el texto visible como en data-orig.
function chordSpan(chord, transposeOffset) {
    const idAttr = chord.id ? ` id="chord-${escapeHtml(chord.id)}"` : '';
    const orig = chord.chord_name || '';
    const shown = transposeChord(orig, transposeOffset);
    return `<span${idAttr} class="chord-container" data-orig="${escapeHtml(orig)}">${escapeHtml(shown)}</span>`;
}

// Pill de acorde (Intro) — devuelve un elemento
function chordPill(name, id, transposeOffset) {
    const pill = document.createElement('span');
    pill.className = 'chord-pill';
    if (id) pill.id = `chord-${id}`;
    pill.dataset.orig = name;
    pill.textContent = transposeChord(name, transposeOffset);
    return pill;
}
