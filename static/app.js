// Referencias del DOM
const elSongTitle = document.getElementById("song-title");
const elSongArtist = document.getElementById("song-artist");
const elBpmValue = document.getElementById("bpm-value");
const elBtnBpmUp = document.getElementById("btn-bpm-up");
const elBtnBpmDown = document.getElementById("btn-bpm-down");
const elBtnPlayPause = document.getElementById("btn-play-pause");
const elBtnStop = document.getElementById("btn-stop");
const elCurrentBeat = document.getElementById("current-beat-display");
const elScoreContent = document.getElementById("score-content");

// Instanciar el motor
const engine = new SyncEngine();

// Estado de la canción y la transposición
let currentSong = null;
let transposeOffset = 0; // semitonos (-11..+11)

// La lógica de transposición (transposeChord) y el render (renderScoreInto)
// viven en score_render.js, compartido con la vista previa del editor.

// Aplica la transposición visual a todos los acordes ya renderizados
function applyTranspose() {
    document.querySelectorAll('[data-orig]').forEach(el => {
        el.textContent = transposeChord(el.dataset.orig, transposeOffset);
    });
    const elKey = document.getElementById('key-value');
    if (elKey) elKey.textContent = (transposeOffset > 0 ? '+' : '') + transposeOffset;
}

// --- Suscripción a cambios del motor ---
engine.subscribe((state) => {
    // Actualizar controles
    elBpmValue.textContent = state.bpm;
    elCurrentBeat.textContent = `Beat: ${state.currentBeat.toFixed(1)}`;
    
    if (state.status === "playing") {
        elBtnPlayPause.innerHTML = "⏸ Pause";
        elBtnPlayPause.style.background = "var(--accent-hover)";
    } else {
        elBtnPlayPause.innerHTML = "▶ Play";
        elBtnPlayPause.style.background = "var(--accent-color)";
    }

    // Actualizar acordes activos en el DOM (acordes flotantes Y pills del Intro)
    document.querySelectorAll('.chord-container.active, .chord-pill.active').forEach(el => {
        el.classList.remove('active');
    });
    
    if (state.activeChordId) {
        const activeEl = document.getElementById(`chord-${state.activeChordId}`);
        if (activeEl) activeEl.classList.add('active');
    }

    // Auto-scroll continuo tipo teleprompter:
    // la partitura baja suave y constante según el progreso de la canción,
    // así no hay saltos y se sigue cómodamente mientras se toca.
    if (state.status === "playing" && state.totalBeats) {
        const container = document.getElementById('score-container');
        const maxScroll = container.scrollHeight - container.clientHeight;
        if (maxScroll > 0) {
            const progress = Math.min(state.currentBeat / state.totalBeats, 1);
            // Escribimos scrollTop directamente cada frame (rAF) → descenso fluido
            container.scrollTop = progress * maxScroll;
        }
    }
});

// --- Interacciones del usuario ---
elBtnPlayPause.addEventListener('click', () => {
    if (engine.state.status === "playing") {
        engine.pause();
    } else {
        engine.play();
    }
});

elBtnStop.addEventListener('click', () => {
    engine.stop();
    // Reset scroll
    document.getElementById('score-container').scrollTo({top: 0, behavior: 'smooth'});
});

// Atajo de teclado: la barra espaciadora alterna play/pausa (T-021). Se ignora si el foco
// está en un campo de texto, para no romper la escritura.
document.addEventListener('keydown', (e) => {
    if (e.code !== 'Space' && e.key !== ' ') return;
    const tag = (e.target.tagName || '').toLowerCase();
    if (tag === 'input' || tag === 'textarea' || e.target.isContentEditable) return;
    e.preventDefault();  // evita el scroll por defecto de la barra espaciadora
    if (engine.state.status === 'playing') engine.pause();
    else engine.play();
});

// Guardado automático del tempo (debounce): la canción recuerda el último BPM elegido.
let bpmSaveTimer = null;
function scheduleBpmSave() {
    if (!currentSong) return;
    clearTimeout(bpmSaveTimer);
    bpmSaveTimer = setTimeout(async () => {
        try {
            const res = await apiFetch(`/songs/${currentSong.id}`, {
                method: 'PATCH',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ bpm: engine.state.bpm })
            });
            if (res.ok) currentSong.bpm = engine.state.bpm;
        } catch (e) {
            console.error('No se pudo guardar el tempo', e);
        }
    }, 1000);
}

elBtnBpmUp.addEventListener('click', () => { engine.setBpm(engine.state.bpm + 1); scheduleBpmSave(); });
elBtnBpmDown.addEventListener('click', () => { engine.setBpm(engine.state.bpm - 1); scheduleBpmSave(); });

// --- Metrónomo (Web Audio API) ---
let metronomeOn = false;
let audioCtx = null;
let lastClickedBeat = -1; // último beat entero al que ya sonó el clic
const elBtnMetronome = document.getElementById('btn-metronome');

function playClick(isAccent) {
    if (!audioCtx) return;
    const osc = audioCtx.createOscillator();
    const gain = audioCtx.createGain();
    osc.connect(gain);
    gain.connect(audioCtx.destination);

    // Acento (primer tiempo del compás) más agudo y fuerte
    osc.frequency.value = isAccent ? 1500 : 900;
    const now = audioCtx.currentTime;
    const vol = isAccent ? 0.5 : 0.3;
    gain.gain.setValueAtTime(vol, now);
    gain.gain.exponentialRampToValueAtTime(0.0001, now + 0.05); // clic corto
    osc.start(now);
    osc.stop(now + 0.05);
}

if (elBtnMetronome) elBtnMetronome.addEventListener('click', () => {
    metronomeOn = !metronomeOn;
    // El AudioContext debe crearse tras un gesto del usuario
    if (metronomeOn && !audioCtx) {
        audioCtx = new (window.AudioContext || window.webkitAudioContext)();
    }
    elBtnMetronome.style.background = metronomeOn ? 'var(--accent-color)' : 'rgba(255,255,255,0.08)';
    elBtnMetronome.style.color = metronomeOn ? '#000' : 'var(--text-primary)';
});

// Hook al motor: en cada cruce de beat entero, sonar el clic (si está activo y reproduciendo)
engine.subscribe((state) => {
    if (!metronomeOn || state.status !== 'playing') {
        if (state.status !== 'playing') lastClickedBeat = -1;
        return;
    }
    const beat = Math.floor(state.currentBeat);
    if (beat >= 0 && beat !== lastClickedBeat) {
        lastClickedBeat = beat;
        const beatsPerBar = (currentSong && currentSong.time_signature_num) || 4;
        playClick(beat % beatsPerBar === 0);
    }
});

// --- Carga de datos inicial desde la API ---
async function fetchAndRenderSong() {
    try {
        const urlParams = new URLSearchParams(window.location.search);
        const songId = urlParams.get('songId');

        let song = null;

        if (songId) {
            const res = await apiFetch(`/songs/${songId}`);
            if (res.status === 404) throw new Error("NOT_FOUND");
            if (!res.ok) throw new Error("Error fetching specific song");
            song = await res.json();
        } else {
            const res = await apiFetch("/songs/");
            if (!res.ok) throw new Error("Error fetching songs");
            const songs = await res.json();

            if (songs.length === 0) {
                elSongTitle.textContent = "No hay canciones. Pulsa el botón + para crear una.";
                return;
            }
            // El listado /songs/ es ligero (SongSummary) y NO trae la estructura
            // sections→lines→chords (T-010). Para reproducir la primera canción por
            // defecto necesitamos el DETALLE completo, no el resumen.
            const detRes = await apiFetch(`/songs/${songs[0].id}`);
            if (!detRes.ok) throw new Error("Error fetching default song detail");
            song = await detRes.json();
        }
        
        currentSong = song;
        transposeOffset = 0;
        elSongTitle.textContent = song.title;
        elSongArtist.textContent = song.artist || "Artista Desconocido";

        renderScoreInto(elScoreContent, song, transposeOffset);
        applyTranspose();
        engine.loadSong(song);

    } catch (err) {
        // Antes el fallo de carga era casi silencioso (mensaje técnico solo en el título y la
        // partitura en blanco). Ahora avisamos en el área principal y distinguimos 404 de
        // fallo de conexión, con una salida a la biblioteca (T-041).
        console.error(err);
        const notFound = err && err.message === "NOT_FOUND";
        elSongTitle.textContent = notFound ? "Canción no encontrada" : "No se pudo cargar la canción";
        elSongArtist.textContent = "";
        elScoreContent.innerHTML = `
            <div class="empty-state">
                <div class="empty-icon">${notFound ? "🔍" : "⚠️"}</div>
                <h3>${notFound ? "No encontramos esta canción" : "No se pudo cargar la canción"}</h3>
                <p>${notFound ? "Quizá fue borrada." : "Revisa tu conexión e inténtalo de nuevo."}</p>
                <a href="library.html" class="primary-btn" style="text-decoration:none; margin-top:1rem;">← Volver a la biblioteca</a>
            </div>`;
    }
}

// --- Controles de transposición (tono) ---
const elKeyDown = document.getElementById('btn-key-down');
const elKeyUp = document.getElementById('btn-key-up');
const elKeySave = document.getElementById('btn-key-save');

function changeTranspose(delta) {
    transposeOffset = Math.max(-11, Math.min(11, transposeOffset + delta));
    applyTranspose();
}

if (elKeyUp) elKeyUp.addEventListener('click', () => changeTranspose(1));
if (elKeyDown) elKeyDown.addEventListener('click', () => changeTranspose(-1));

// Guardar el tono transpuesto de forma permanente (PUT)
if (elKeySave) elKeySave.addEventListener('click', async () => {
    if (!currentSong || transposeOffset === 0) return;

    // Copia profunda y transposición de todos los nombres de acorde
    const payload = JSON.parse(JSON.stringify(currentSong));
    (payload.sections || []).forEach(sec =>
        (sec.lines || []).forEach(line =>
            (line.chords || []).forEach(c => {
                c.chord_name = transposeChord(c.chord_name, transposeOffset);
            })
        )
    );

    try {
        elKeySave.disabled = true;
        const res = await apiFetch(`/songs/${currentSong.id}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        if (!res.ok) throw new Error('Error al guardar el tono');

        // El PUT recrea la estructura (nuevos ids): recargamos con la respuesta
        const data = await res.json();
        currentSong = data;
        transposeOffset = 0;
        renderScoreInto(elScoreContent, data, transposeOffset);
        applyTranspose();
        engine.loadSong(data);
    } catch (err) {
        console.error(err);
        toast('No se pudo guardar el tono: ' + err.message, 'error');
    } finally {
        elKeySave.disabled = false;
    }
});

// --- Diagramas de acordes (popup al pulsar un acorde) ---
const diagramPopup = document.createElement('div');
diagramPopup.className = 'chord-diagram-popup';
diagramPopup.style.display = 'none';
document.body.appendChild(diagramPopup);

function showChordDiagram(name, anchorEl) {
    const shape = getChordShape(name);
    diagramPopup.innerHTML = renderChordDiagramSVG(shape, name);
    diagramPopup.style.display = 'block';

    // Posicionar encima del acorde, centrado y dentro de la pantalla
    const rect = anchorEl.getBoundingClientRect();
    const pw = diagramPopup.offsetWidth;
    const ph = diagramPopup.offsetHeight;
    let left = rect.left + rect.width / 2 - pw / 2;
    let top = rect.top - ph - 8;
    if (top < 8) top = rect.bottom + 8;       // si no cabe arriba, ponerlo debajo
    left = Math.max(8, Math.min(left, window.innerWidth - pw - 8));
    diagramPopup.style.left = `${left}px`;
    diagramPopup.style.top = `${top}px`;
}

function hideChordDiagram() {
    diagramPopup.style.display = 'none';
}

// Delegación: clic sobre cualquier acorde (flotante o pill) abre su diagrama
elScoreContent.addEventListener('click', (e) => {
    const el = e.target.closest('.chord-container, .chord-pill');
    if (!el) return;
    e.stopPropagation();
    showChordDiagram(el.textContent.trim(), el);
});

// Cerrar al pulsar fuera o con Escape
document.addEventListener('click', (e) => {
    if (!diagramPopup.contains(e.target) && !e.target.closest('.chord-container, .chord-pill')) {
        hideChordDiagram();
    }
});
document.addEventListener('keydown', (e) => { if (e.key === 'Escape') hideChordDiagram(); });

// Iniciar: exigir sesión antes de cargar la canción
(async () => {
    const session = await requireAuth();
    if (session) fetchAndRenderSong();
})();
