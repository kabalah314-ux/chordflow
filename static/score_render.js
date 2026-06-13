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
                    let contentHTML = nextLine.content || '';

                    const sortedChords = [...(line.chords || [])].sort((a, b) => b.char_position - a.char_position);
                    sortedChords.forEach(chord => {
                        const pos = Math.min(chord.char_position || 0, contentHTML.length);
                        contentHTML = contentHTML.substring(0, pos) + chordSpan(chord, transposeOffset) + contentHTML.substring(pos);
                    });

                    lineDiv.innerHTML = contentHTML;
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
                let contentHTML = line.content || '';

                if (line.chords && line.chords.length > 0) {
                    const sortedChords = [...line.chords].sort((a, b) => b.char_position - a.char_position);
                    sortedChords.forEach(chord => {
                        const pos = chord.char_position || 0;
                        contentHTML = contentHTML.substring(0, pos) + chordSpan(chord, transposeOffset) + contentHTML.substring(pos);
                    });
                }

                lineDiv.innerHTML = contentHTML;
                secDiv.appendChild(lineDiv);
                i++;

            } else {
                i++;
            }
        }

        container.appendChild(secDiv);
    });
}

// Acorde flotante (span) — devuelve HTML string para inyectar en la letra
function chordSpan(chord, transposeOffset) {
    const idAttr = chord.id ? ` id="chord-${chord.id}"` : '';
    return `<span${idAttr} class="chord-container" data-orig="${chord.chord_name}">${transposeChord(chord.chord_name, transposeOffset)}</span>`;
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
