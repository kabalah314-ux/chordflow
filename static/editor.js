/**
 * CHORDFLOW EDITOR — Parser por Alineación
 * Sistema: Detecta líneas de acordes (encima) y las empareja con la línea de letra (debajo).
 * Permite pegar directamente desde Ultimate Guitar, LaCuerda.net, etc.
 */

// ─── Regex de acordes válidos ───────────────────────────────────────────────
// Reconoce acordes: Am, F#m7, C#7, G/B, Bb, Dmaj7, Em7b5, A7sus4, Cadd9, Csus2,
// y los que el regex viejo NO captaba: extensiones de 2 cifras (Cadd11, Cmaj13) y
// alteraciones encadenadas (Em7b5, A7sus4). El sufijo es una secuencia repetible de
// tokens: cualidad (maj/min/m/M/aug/dim/sus/add) o nº con alteración opcional (7, b5, #11),
// seguida de un bajo opcional (/G, /F#). Cada token es no vacío → sin backtracking patológico.
const CHORD_REGEX = /^[A-G][#b]?(maj|min|aug|dim|sus|add|m|M|\+|°|ø|[#b]?\d+)*(\/[A-G][#b]?)?$/;

/**
 * Determina si una sola palabra es un acorde.
 */
function isChord(word) {
    return CHORD_REGEX.test(word.trim());
}

/**
 * Determina si una línea completa es una "línea de acordes".
 * Criterio: ≥60% de sus palabras son acordes reconocibles y no es una línea de sección.
 */
function isChordLine(line) {
    const trimmed = line.trim();
    if (!trimmed) return false;
    // Las líneas de sección terminan en ':' — no son acordes
    if (trimmed.endsWith(':')) return false;
    // Líneas de Intro con formato `: Acorde : Acorde :` 
    if (trimmed.startsWith(':')) return false;

    const words = trimmed.split(/\s+/).filter(w => w.length > 0);
    if (words.length === 0) return false;

    const chordCount = words.filter(w => isChord(w)).length;
    // Si más del 60% de las palabras son acordes, es una línea de acordes
    return (chordCount / words.length) >= 0.6;
}

/**
 * Determina si una línea es una CUERDA de tablatura ASCII (una fila de un diagrama de tab).
 * Firma inequívoca: una corrida de ≥2 guiones y SOLO caracteres de tab — nombre de cuerda
 * (a-g/A-G), `|`, dígitos de traste, técnicas (h/p/b/r/s/t/x), ligados (/ \ ~ . ()), guiones y
 * espacios. Las letras de palabra normales (h,o,l,a…) la descartan, así no colisiona con la
 * letra ni con las líneas de acordes (que no llevan corridas de guiones).
 */
function isTabLine(line) {
    const t = (line || '').trim();
    if (t.length < 3) return false;
    if (!/--/.test(t)) return false;                          // corrida de guiones = firma de tab
    return /^[A-Ga-g#b|0-9\-hpbrstx/\\~.() ]+$/.test(t);      // solo caracteres de tablatura
}

/**
 * Detecta si una línea es de tipo Intro con el formato:  `: Acorde : Acorde :`
 */
function isIntroLine(line) {
    const trimmed = line.trim();
    return trimmed.startsWith(':') || trimmed.match(/^\s*:.*:.*$/);
}

/**
 * Parsea una línea de Intro tipo `: F#m : C#7 : D :` y extrae los acordes.
 */
function parseIntroLine(line, lineOrder) {
    const chords = [];
    // Quitar los dos puntos y separar por ellos
    const parts = line.split(':').map(p => p.trim()).filter(p => p.length > 0);
    let charPos = 0;
    parts.forEach(part => {
        const words = part.split(/\s+/).filter(w => w.length > 0);
        words.forEach(word => {
            if (isChord(word)) {
                chords.push({
                    chord_name: word,
                    char_position: charPos,
                    beat_offset: 0.0
                });
                charPos += word.length + 2; // separación estimada
            }
        });
    });

    return {
        order: lineOrder,
        type: 'chord_only',
        content: parts.join('  '),
        beat_start: 0,
        beat_duration: 4.0,
        chords: chords
    };
}

/**
 * Toma una línea de acordes y una línea de letra.
 * Mapea cada acorde a la posición de carácter exacta en la letra,
 * basándose en la columna donde aparece el acorde en la línea de arriba.
 */
function pairChordLineWithLyric(chordLine, lyricLine, lineOrder, beatStart) {
    const chords = [];

    // Encontrar cada acorde y su posición de columna en la línea de acordes
    let i = 0;
    while (i < chordLine.length) {
        // Saltar espacios
        if (chordLine[i] === ' ') { i++; continue; }

        // Intentar leer una palabra (posible acorde)
        let wordStart = i;
        while (i < chordLine.length && chordLine[i] !== ' ') i++;
        const word = chordLine.substring(wordStart, i);

        if (isChord(word)) {
            // La posición de columna del acorde = posición en la línea de letra
            // Clamp: si la letra es más corta que la línea de acordes, lo añadimos al final
            const charPos = Math.min(wordStart, lyricLine.length);
            chords.push({
                chord_name: word,
                char_position: charPos,
                beat_offset: 0.0
            });
        }
    }

    return {
        order: lineOrder,
        type: 'lyric',
        content: lyricLine,
        beat_start: beatStart,
        beat_duration: 4.0,
        chords: chords
    };
}

/**
 * Parsea una línea de acordes SIN letra debajo (acorde solo en su línea).
 * Ocurre cuando hay una línea de acordes pero la siguiente es otra sección o vacía.
 */
function parseOrphanChordLine(chordLine, lineOrder, beatStart) {
    const chords = [];
    let i = 0;
    while (i < chordLine.length) {
        if (chordLine[i] === ' ') { i++; continue; }
        let wordStart = i;
        while (i < chordLine.length && chordLine[i] !== ' ') i++;
        const word = chordLine.substring(wordStart, i);
        if (isChord(word)) {
            chords.push({
                chord_name: word,
                char_position: wordStart,
                beat_offset: 0.0
            });
        }
    }
    return {
        order: lineOrder,
        type: 'chord_only',
        content: '',
        beat_start: beatStart,
        beat_duration: 4.0,
        chords: chords
    };
}

/**
 * Función principal de parsing.
 * Recorre el texto línea a línea, detecta secciones, intros y pares de (Acorde / Letra).
 */
function parseRawText(text) {
    const rawLines = text.split('\n');
    const sections = [];

    let currentSection = null;
    let sectionOrder = 1;
    let lineOrder = 1;
    let globalBeatTracker = 0.0;

    const ensureSection = () => {
        if (!currentSection) {
            currentSection = {
                name: 'General',
                order: sectionOrder++,
                lines: []
            };
            sections.push(currentSection);
        }
    };

    let i = 0;
    while (i < rawLines.length) {
        const raw = rawLines[i];
        const trimmed = raw.trimEnd();

        // 1. Línea vacía — saltar
        if (!trimmed.trim()) { i++; continue; }

        // 2a. Sección con corchetes (Ultimate Guitar): "[Verso 1]", "[Chorus]", "[Intro]"
        const bracketMatch = trimmed.trim().match(/^\[(.+)\]$/);
        if (bracketMatch) {
            currentSection = {
                name: bracketMatch[1].trim(),
                order: sectionOrder++,
                lines: []
            };
            sections.push(currentSection);
            lineOrder = 1;
            i++;
            continue;
        }

        // 2b. Línea de sección con dos puntos (ej: "Verso 1:", "Coro:")
        if (trimmed.trim().endsWith(':') && !isIntroLine(trimmed) && trimmed.trim().split(/\s+/).length <= 4) {
            currentSection = {
                name: trimmed.trim().slice(0, -1).trim(),
                order: sectionOrder++,
                lines: []
            };
            sections.push(currentSection);
            lineOrder = 1;
            i++;
            continue;
        }

        // 3. Línea de Intro (formato : F#m : C#7 :)
        if (isIntroLine(trimmed)) {
            ensureSection();
            currentSection.lines.push(parseIntroLine(trimmed, lineOrder++));
            globalBeatTracker += 4.0;
            i++;
            continue;
        }

        // 3.5 Bloque de TABLATURA: una o varias cuerdas consecutivas → UNA sola línea type 'tab'.
        // El ASCII se guarda tal cual en `content` y el render lo pinta monoespaciado. La joya no se
        // toca: una tab no lleva acordes con id, así que el motor de sincronización la ignora.
        if (isTabLine(trimmed)) {
            ensureSection();
            const tabLines = [];
            while (i < rawLines.length && isTabLine(rawLines[i])) {
                tabLines.push(rawLines[i].replace(/\s+$/, ''));   // conserva la sangría izquierda
                i++;
            }
            currentSection.lines.push({
                order: lineOrder++,
                type: 'tab',
                content: tabLines.join('\n'),
                beat_start: globalBeatTracker,
                beat_duration: 4.0,
                chords: [],
                tab_strings: []
            });
            globalBeatTracker += 4.0;
            continue;
        }

        // 4. Línea de acordes — mirar si la siguiente es letra
        if (isChordLine(trimmed)) {
            ensureSection();
            const nextRaw = rawLines[i + 1];
            const nextTrimmed = nextRaw ? nextRaw.trimEnd() : '';

            // Si la siguiente línea existe, no está vacía y NO es acorde → es letra
            if (nextTrimmed.trim() && !isChordLine(nextTrimmed) && !nextTrimmed.trim().endsWith(':')) {
                // Par Acorde / Letra
                const parsedLine = pairChordLineWithLyric(raw, nextTrimmed, lineOrder++, globalBeatTracker);
                currentSection.lines.push(parsedLine);
                globalBeatTracker += 4.0;
                i += 2; // consumir ambas líneas
            } else {
                // Acorde suelto (sin letra debajo)
                currentSection.lines.push(parseOrphanChordLine(raw, lineOrder++, globalBeatTracker));
                globalBeatTracker += 4.0;
                i++;
            }
            continue;
        }

        // 5. Línea de letra pura (sin acorde encima)
        ensureSection();
        currentSection.lines.push({
            order: lineOrder++,
            type: 'lyric',
            content: trimmed.trim(),
            beat_start: globalBeatTracker,
            beat_duration: 4.0,
            chords: []
        });
        globalBeatTracker += 4.0;
        i++;
    }

    return sections;
}

// ─── Serializador inverso (Estructura → Texto "acordes sobre letra") ──────────
// Necesario para EDITAR: la canción se guarda estructurada, pero el editor
// trabaja con texto plano. Reconstruimos el texto a partir de la canción.

/**
 * Construye una línea de acordes colocando cada acorde en su char_position,
 * rellenando con espacios para mantener la alineación por columnas.
 */
function buildChordLine(chords) {
    let line = '';
    const sorted = [...chords].sort((a, b) => (a.char_position || 0) - (b.char_position || 0));
    sorted.forEach(ch => {
        const pos = ch.char_position || 0;
        if (line.length < pos) {
            line += ' '.repeat(pos - line.length);
        } else if (line.length > 0) {
            line += ' '; // evitar que dos acordes queden pegados
        }
        line += ch.chord_name;
    });
    return line;
}

/**
 * Convierte una canción (con secciones/líneas/acordes) al texto plano que
 * entiende el parser, para poder precargarlo en el textarea al editar.
 */
function songToRawText(song) {
    const out = [];
    (song.sections || []).forEach(sec => {
        if (sec.name) out.push(sec.name + ':');

        (sec.lines || []).forEach(line => {
            if (line.type === 'lyric') {
                if (line.chords && line.chords.length) out.push(buildChordLine(line.chords));
                out.push(line.content || '');
            } else if (line.type === 'chord_only') {
                if (line.chords && line.chords.length) {
                    out.push(line.chords.map(c => c.chord_name).join('  '));
                } else if (line.content) {
                    out.push(line.content);
                }
            } else if (line.type === 'tab') {
                if (line.content) out.push(line.content);   // ASCII de la tablatura (multilínea)
            } else if (line.content) {
                out.push(line.content);
            }
        });

        out.push(''); // línea en blanco entre secciones
    });
    return out.join('\n').trim();
}

// ─── Modo edición: precargar la canción si llega ?songId ──────────────────────
let editingSongId = null;

async function initEditor() {
    const songId = new URLSearchParams(window.location.search).get('songId');
    if (!songId) return; // Modo creación normal

    try {
        const res = await apiFetch(`/songs/${songId}`);
        if (!res.ok) throw new Error('No se pudo cargar la canción');
        const song = await res.json();

        editingSongId = song.id;
        document.getElementById('title').value = song.title || '';
        document.getElementById('artist').value = song.artist || '';
        document.getElementById('bpm').value = song.bpm || 120;
        const sigEl = document.getElementById('time-signature');   // T-V5-07: compás de la canción
        if (sigEl) sigEl.value = `${song.time_signature_num || 4}/${song.time_signature_den || 4}`;
        document.getElementById('reference-url').value = song.reference_url || '';
        document.getElementById('raw-text').value = songToRawText(song);
        updatePreview();
        updateReferencePreview();   // carátula si la canción ya trae enlace de referencia

        // Ajustar textos de la UI a "edición"
        document.querySelector('.song-info h1').textContent = 'Editar Partitura';
        document.querySelector('.song-info h2').textContent = song.title;
        document.getElementById('btn-save').innerHTML = bfIcon('save') + ' Guardar cambios';
    } catch (err) {
        console.error(err);
        toast('Error cargando la canción para editar: ' + err.message, 'error');
    }
}

// ─── Vista previa en vivo ─────────────────────────────────────────────────────
const elRawText = document.getElementById('raw-text');
const elPreview = document.getElementById('preview-content');

function updatePreview() {
    const text = elRawText.value;
    if (!text.trim()) {
        elPreview.innerHTML = '<p class="preview-empty">Pega aquí tu canción y verás cómo quedará…</p>';
        return;
    }
    const sections = parseRawText(text);
    if (!sections.length) {
        elPreview.innerHTML = '<p class="preview-empty">No se detectaron secciones todavía…</p>';
        return;
    }
    // renderScoreInto vive en score_render.js (mismo render que el reproductor)
    renderScoreInto(elPreview, { sections }, 0);
}

elRawText.addEventListener('input', updatePreview);

// ─── V3-F7 (oEmbed): carátula del vídeo de referencia al pegar el enlace ──────
const elRefUrl = document.getElementById('reference-url');
const elRefPreview = document.getElementById('reference-preview');

function updateReferencePreview() {
    if (!elRefUrl || !elRefPreview) return;
    const thumb = bfYoutubeThumb(elRefUrl.value.trim());
    if (thumb) {
        elRefPreview.innerHTML =
            `<a class="ref-thumb" href="${escapeHtml(elRefUrl.value.trim())}" target="_blank" rel="noopener noreferrer" title="Abrir en YouTube">
                <img src="${escapeHtml(thumb)}" alt="Carátula del vídeo de referencia" loading="lazy">
                <span class="ref-thumb__play">${bfIcon('play', { size: 22 })}</span>
            </a>`;
        elRefPreview.hidden = false;
    } else {
        elRefPreview.innerHTML = '';
        elRefPreview.hidden = true;
    }
}

if (elRefUrl) elRefUrl.addEventListener('input', updateReferencePreview);

// ─── Buscar canción por nombre con IA (T-162) ─────────────────────────────────
// Capa de preselección delante del import por URL: busca en CifraClub/LaCuerda, pinta
// candidatos y, al elegir uno, rellena el campo de URL y dispara el import de siempre.
const elImportSearch = document.getElementById('import-search');
const elBtnImportSearch = document.getElementById('btn-import-search');
const elImportSearchResults = document.getElementById('import-search-results');

function renderSearchResults(results) {
    if (!elImportSearchResults) return;
    if (!results.length) {
        elImportSearchResults.removeAttribute('role');   // mensaje suelto: no es un listbox.
        elImportSearchResults.innerHTML = '<li class="import-search-empty">Sin resultados. Prueba con otro nombre o pega el enlace abajo.</li>';
        elImportSearchResults.hidden = false;
        return;
    }
    // T-V5-05: listbox de opciones focables → conserva la semántica de lista/posición para lectores
    // de pantalla (role=button en cada <li> la rompía). Enter/Espacio activan la opción.
    elImportSearchResults.setAttribute('role', 'listbox');
    elImportSearchResults.setAttribute('aria-label', 'Resultados de la búsqueda');
    elImportSearchResults.innerHTML = results.map((r, i) => `
        <li class="import-search-item" data-idx="${i}" tabindex="0" role="option" aria-selected="false">
            <span class="import-search-title">${escapeHtml(r.title)}</span>
            ${r.artist ? `<span class="import-search-artist">${escapeHtml(r.artist)}</span>` : ''}
            ${r.source ? `<span class="import-search-source">${escapeHtml(r.source)}</span>` : ''}
        </li>`).join('');
    elImportSearchResults.hidden = false;
    elImportSearchResults.querySelectorAll('[data-idx]').forEach(li => {
        // T-V5-05: focable (tabindex/role) → se activa con click o con Enter/Espacio.
        const choose = () => {
            const r = results[parseInt(li.dataset.idx, 10)];
            if (!r) return;
            elImportUrl.value = r.url;
            elImportSearchResults.hidden = true;
            elBtnImport.click();   // dispara el import normal con la URL elegida
        };
        li.addEventListener('click', choose);
        li.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); choose(); }
        });
    });
}

if (elBtnImportSearch) elBtnImportSearch.addEventListener('click', async () => {
    const q = elImportSearch.value.trim();
    if (!q) { toast('Escribe primero el nombre de la canción.', 'error'); return; }
    const labelOriginal = elBtnImportSearch.textContent;
    elBtnImportSearch.disabled = true;
    elBtnImportSearch.textContent = 'Buscando…';
    try {
        const res = await apiFetch('/import/search?q=' + encodeURIComponent(q));
        const data = await res.json().catch(() => ({}));
        if (!res.ok) {
            toast(data.detail || 'No se pudo buscar.', 'error');
            return;
        }
        renderSearchResults(data.results || []);
    } catch (err) {
        toast('Error de red al buscar.', 'error');
    } finally {
        elBtnImportSearch.disabled = false;
        elBtnImportSearch.textContent = labelOriginal;
    }
});
if (elImportSearch) elImportSearch.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') { e.preventDefault(); elBtnImportSearch.click(); }
});

// ─── Importar desde URL con IA (T-045) ────────────────────────────────────────
const elImportUrl = document.getElementById('import-url');
const elBtnImport = document.getElementById('btn-import');

if (elBtnImport) elBtnImport.addEventListener('click', async () => {
    const url = elImportUrl.value.trim();
    if (!url) { toast('Pega primero un enlace.', 'error'); return; }
    const labelOriginal = elBtnImport.textContent;
    elBtnImport.disabled = true;
    elBtnImport.textContent = 'Importando…';
    try {
        const res = await apiFetch('/import/', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ url })
        });
        const data = await res.json().catch(() => ({}));
        if (!res.ok) {
            toast(data.detail || 'No se pudo importar el enlace.', 'error');
            return;
        }
        elRawText.value = data.raw_text || '';
        updatePreview();
        toast('Partitura importada. Revísala antes de guardar.', 'success');
    } catch (err) {
        toast('Error de red al importar.', 'error');
    } finally {
        elBtnImport.disabled = false;
        elBtnImport.textContent = labelOriginal;
    }
});

// ─── Formulario ─────────────────────────────────────────────────────────────
document.getElementById('song-form').addEventListener('submit', async (e) => {
    e.preventDefault();

    const title = document.getElementById('title').value;
    const artist = document.getElementById('artist').value;
    const bpm = parseInt(document.getElementById('bpm').value, 10);
    const referenceUrl = document.getElementById('reference-url').value.trim();
    const rawText = document.getElementById('raw-text').value;
    // T-V5-07: compás elegido (num/den). El select ofrece 2/4·3/4·4/4·6/8; default 4/4.
    const sigVal = (document.getElementById('time-signature') || {}).value || '4/4';
    const [tsNum, tsDen] = sigVal.split('/').map((n) => parseInt(n, 10) || 4);

    const sections = parseRawText(rawText);

    const payload = { title, artist, bpm, time_signature_num: tsNum, time_signature_den: tsDen, sections };
    if (referenceUrl) payload.reference_url = referenceUrl;

    // PUT si estamos editando, POST si es nueva
    const isEditing = !!editingSongId;
    const url = isEditing ? `/songs/${editingSongId}` : '/songs/';
    const method = isEditing ? 'PUT' : 'POST';

    const btnSave = document.getElementById('btn-save');
    const originalLabel = btnSave.innerHTML;

    try {
        btnSave.disabled = true;
        btnSave.innerHTML = 'Guardando...';

        const res = await apiFetch(url, {
            method,
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        if (!res.ok) {
            const errData = await res.json().catch(() => ({}));
            throw new Error(errData.detail || 'Error al guardar la canción');
        }

        const data = await res.json();
        // D9: al AÑADIR una canción nueva se sube al catálogo global por defecto ("ponla aquí").
        // Best-effort: si el catálogo falla (o ya está publicada), no bloquea el guardado.
        if (!isEditing) {
            try {
                await apiFetch('/catalog/publish', {
                    method: 'POST', headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ song_id: data.id }),
                });
            } catch (e) { /* el catálogo es opcional para el guardado */ }
        }
        window.location.href = `index.html?songId=${data.id}`;

    } catch (err) {
        toast('Ocurrió un error: ' + err.message, 'error');
        btnSave.disabled = false;
        btnSave.innerHTML = originalLabel;
    }
});

// Iniciar: exigir sesión; luego detectar modo edición
(async () => {
    const session = await requireAuth();
    if (session) initEditor();
})();
