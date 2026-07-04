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
// Bolita de posición (V3-F2, T-088)
const elProgressFill = document.getElementById("song-progress-fill");
const elProgressDot = document.getElementById("song-progress-dot");
const elSection = document.getElementById("current-section-display");

// Iconos SVG del reproductor (T-123): sustituyen los emoji estáticos del HTML por SVG de
// icons.js (`bfIcon` global, cargado antes que app.js). Se conservan los aria-label/title de cada
// botón (accesibilidad) y los ids; el motor (sync_engine.js) NO se toca. El play/pause se repinta
// además en engine.subscribe. Los glifos +/−/♭/♯ se quedan como texto (se leen mejor).
function paintPlayerIcons() {
    if (typeof bfIcon !== 'function') return;   // defensivo: sin icons.js, deja los emoji
    const byId = (id, name, label) => {
        const el = document.getElementById(id);
        if (el) el.innerHTML = bfIcon(name) + (label ? ' ' + label : '');
    };
    const byHref = (href, name) => {
        const el = document.querySelector(`.global-controls a[href="${href}"]`);
        if (el) el.innerHTML = bfIcon(name);
    };
    byId('btn-key-save', 'save');
    byId('btn-tuner', 'mic');
    byId('btn-reference', 'film');
    byId('btn-print', 'printer');
    byId('btn-metronome', 'drum');
    byId('btn-stop', 'stop');
    byId('btn-stage', 'maximize');
    byId('btn-play-pause', 'play', 'Play');     // estado inicial; subscribe lo actualiza al reproducir
    byHref('app.html', 'home');
    byHref('library.html', 'library');
    byHref('editor.html', 'plus');
}
paintPlayerIcons();

// Instanciar el motor
const engine = new SyncEngine();

// Estado de la canción y la transposición
let currentSong = null;
let transposeOffset = 0; // semitonos (-11..+11)
let lastAutoScrollChordId = null; // último acorde al que ancló el auto-scroll (T-019)
let sectionRanges = [];          // [{name, startBeat, endBeat}] para la bolita de posición (T-088)

// Rangos de beat por sección, derivados de la misma lógica de cursor que el motor
// (línea con beat_start o cursor acumulado). Sirve para mostrar la sección actual.
function computeSectionRanges(song) {
    const ranges = [];
    let cursor = 0;
    (song.sections || []).forEach(sec => {
        const start = cursor;
        (sec.lines || []).forEach(line => {
            const dur = line.beat_duration || 4.0;
            const ls = (line.beat_start !== null && line.beat_start !== undefined) ? line.beat_start : cursor;
            cursor = ls + dur;
        });
        ranges.push({ name: sec.name || '', startBeat: start, endBeat: cursor });
    });
    return ranges;
}

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
    // T-V5-07: en la barra se muestra el COMPÁS (no el beat crudo). El beat exacto queda en
    // `data-beat` (precisión interna + tests). Compás = ⌊beat / beats_por_compás⌋ + 1.
    const beatsPerBar = (currentSong && currentSong.time_signature_num) || 4;
    const measure = Math.floor(Math.max(0, state.currentBeat) / beatsPerBar) + 1;
    elCurrentBeat.dataset.beat = state.currentBeat.toFixed(2);
    elCurrentBeat.textContent = `Compás ${measure}`;

    // Bolita de posición (T-088): progreso global + sección actual, derivados del beat.
    const totalBeats = state.totalBeats || 1;
    const frac = Math.max(0, Math.min(1, state.currentBeat / totalBeats));
    if (elProgressFill) elProgressFill.style.width = (frac * 100) + '%';
    if (elProgressDot) elProgressDot.style.left = (frac * 100) + '%';
    if (elSection) {
        let secName = '';
        if (state.currentBeat > 0 && sectionRanges.length) {
            const r = sectionRanges.find(s => state.currentBeat >= s.startBeat && state.currentBeat < s.endBeat);
            secName = (r || sectionRanges[sectionRanges.length - 1]).name || '';
        }
        elSection.textContent = secName;
    }

    if (state.status === "playing") {
        elBtnPlayPause.innerHTML = bfIcon('pause') + " Pause";
        elBtnPlayPause.style.background = "var(--accent-hover)";
    } else {
        elBtnPlayPause.innerHTML = bfIcon('play') + " Play";
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

    // Auto-scroll ANCLADO al acorde activo (T-019). El mapeo lineal beat→píxel anterior se
    // desfasaba: los píxeles no son proporcionales a los beats (secciones de distinta densidad),
    // así que el acorde activo se iba quedando fuera de pantalla. Ahora seguimos al elemento del
    // acorde activo y lo mantenemos a ~1/3 de la altura visible (estilo teleprompter). Solo
    // reposicionamos cuando CAMBIA el acorde activo, para no pelear con el scroll suave.
    if (state.status === "playing" && state.activeChordId
            && state.activeChordId !== lastAutoScrollChordId) {
        const container = document.getElementById('score-container');
        const activeEl = document.getElementById(`chord-${state.activeChordId}`);
        if (activeEl) {
            const cRect = container.getBoundingClientRect();
            const eRect = activeEl.getBoundingClientRect();
            // Cuánto desplazar para llevar el acorde a 1/3 desde arriba (relativo al scroll real).
            const delta = (eRect.top - cRect.top) - container.clientHeight * 0.33;
            container.scrollTo({ top: Math.max(0, container.scrollTop + delta), behavior: 'smooth' });
            lastAutoScrollChordId = state.activeChordId;
        }
    }
});

// --- Interacciones del usuario ---
// T-V5-08: el Play pasa por handlePlayPause() para intercalar la cuenta atrás cuando arranca
// desde el principio. La lógica de la cuenta atrás vive junto al metrónomo (más abajo).
elBtnPlayPause.addEventListener('click', () => handlePlayPause());

elBtnStop.addEventListener('click', () => {
    cancelCountIn();               // T-V5-08: Stop también aborta una cuenta atrás en curso
    engine.stop();
    lastAutoScrollChordId = null;  // reanclar desde el principio al volver a reproducir
    // Reset scroll
    document.getElementById('score-container').scrollTo({top: 0, behavior: 'smooth'});
});

// --- Modo Directo (V3-F4, T-089): escenario a pantalla completa, sin tocar el motor ---
const elBtnStage = document.getElementById('btn-stage');
function isStageMode() { return document.body.classList.contains('stage-mode'); }
function setStageButton() {
    if (!elBtnStage) return;
    const on = isStageMode();
    elBtnStage.setAttribute('aria-label', on ? 'Salir del Modo Directo' : 'Modo Directo (pantalla completa)');
    elBtnStage.title = on ? 'Salir del Modo Directo' : 'Modo Directo';
}
async function enterStage() {
    document.body.classList.add('stage-mode');
    setStageButton();
    // Pantalla completa real si el navegador lo permite (gesto del usuario). Opcional: el modo
    // funciona igual sin FS (p. ej. si el navegador lo bloquea).
    try { if (document.documentElement.requestFullscreen) await document.documentElement.requestFullscreen(); }
    catch (e) { /* fullscreen opcional */ }
}
function exitStage() {
    document.body.classList.remove('stage-mode');
    setStageButton();
    try { if (document.fullscreenElement && document.exitFullscreen) document.exitFullscreen(); }
    catch (e) { /* ignore */ }
}
if (elBtnStage) elBtnStage.addEventListener('click', () => (isStageMode() ? exitStage() : enterStage()));
// Salir del modo al abandonar pantalla completa (Esc del navegador) o con Escape si no se entró a FS.
document.addEventListener('fullscreenchange', () => {
    if (!document.fullscreenElement && isStageMode()) { document.body.classList.remove('stage-mode'); setStageButton(); }
});
document.addEventListener('keydown', (e) => { if (e.key === 'Escape' && isStageMode()) exitStage(); });

// --- Vídeo de referencia (V3-F4, T-090): YouTube embebido si la canción tiene reference_url ---
const elBtnReference = document.getElementById('btn-reference');
const elReferencePanel = document.getElementById('reference-panel');
const elReferenceEmbed = document.getElementById('reference-embed');
const elBtnReferenceClose = document.getElementById('btn-reference-close');

function youtubeId(url) {
    if (!url) return null;
    const m = String(url).match(
        /(?:youtube\.com\/(?:watch\?(?:.*&)?v=|embed\/|shorts\/)|youtu\.be\/)([A-Za-z0-9_-]{11})/);
    return m ? m[1] : null;
}
function closeReference() {
    if (elReferencePanel) elReferencePanel.style.display = 'none';
    if (elReferenceEmbed) elReferenceEmbed.innerHTML = '';  // quitar el iframe detiene la reproducción
}
function setupReference(song) {
    closeReference();
    const hasYt = !!(song && youtubeId(song.reference_url));
    if (elBtnReference) elBtnReference.style.display = hasYt ? '' : 'none';
}
function toggleReference() {
    if (!elReferencePanel || !elReferenceEmbed) return;
    if (elReferencePanel.style.display !== 'none') { closeReference(); return; }
    const id = currentSong && youtubeId(currentSong.reference_url);
    if (!id) return;   // id validado por regex ([A-Za-z0-9_-]{11}) → seguro para el src
    elReferenceEmbed.innerHTML =
        `<iframe src="https://www.youtube.com/embed/${id}" title="Vídeo de referencia" ` +
        `allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" ` +
        `allowfullscreen></iframe>`;
    elReferencePanel.style.display = '';
}
if (elBtnReference) elBtnReference.addEventListener('click', toggleReference);
if (elBtnReferenceClose) elBtnReferenceClose.addEventListener('click', closeReference);

// Exportar a PDF: imprime la partitura actual (con su transposición) → "Guardar como PDF" del
// navegador. Los estilos @media print muestran solo la partitura en blanco/negro (Fase 5).
const elBtnPrint = document.getElementById('btn-print');
if (elBtnPrint) elBtnPrint.addEventListener('click', () => window.print());

// Hoja de atajos (T-141): "?" abre un modal con los atajos de teclado del reproductor.
const elBtnShortcuts = document.getElementById('btn-shortcuts');
if (elBtnShortcuts) elBtnShortcuts.addEventListener('click', () => {
    alertModal(`<h3 style="margin:0 0 .8rem;">Atajos de teclado</h3>
        <table class="shortcuts-table">
            <tr><td><kbd>Espacio</kbd></td><td>Reproducir / Pausar</td></tr>
            <tr><td><kbd>Av Pág</kbd> · <kbd>→</kbd></td><td>Pasar página (o siguiente en el setlist)</td></tr>
            <tr><td><kbd>Re Pág</kbd> · <kbd>←</kbd></td><td>Página anterior (o anterior en el setlist)</td></tr>
            <tr><td><kbd>Esc</kbd></td><td>Salir del Modo Directo</td></tr>
        </table>`, { okText: 'Entendido' });
});

// Barra de repertorio: si se llega con ?setlist=<id>, muestra anterior/siguiente y la posición.
async function setupSetlistNav() {
    const params = new URLSearchParams(window.location.search);
    const setlistId = params.get('setlist');
    const elNav = document.getElementById('setlist-nav');
    if (!setlistId || !elNav) return;
    try {
        const res = await apiFetch(`/setlists/${setlistId}`);
        if (!res.ok) return;
        const sl = await res.json();
        const ids = sl.items.map(i => i.song_id);
        const curId = params.get('songId');
        let pos = parseInt(params.get('pos'), 10);
        if (isNaN(pos) || ids[pos] !== curId) pos = ids.indexOf(curId);  // recalcular si no cuadra
        if (pos < 0) return;
        const note = (sl.items[pos] || {}).note;   // apunte de la canción actual (T-110)
        const go = (p) => { window.location.href =
            `index.html?songId=${encodeURIComponent(ids[p])}&setlist=${encodeURIComponent(setlistId)}&pos=${p}`; };
        const prevDis = pos <= 0 ? 'disabled' : '';
        const nextDis = pos >= ids.length - 1 ? 'disabled' : '';
        elNav.innerHTML = `
            <button id="sl-prev" class="secondary-btn" ${prevDis} aria-label="Canción anterior">◀</button>
            <span class="sl-nav-label">🎼 ${escapeHtml(sl.name)} · ${pos + 1}/${ids.length}</span>
            ${note ? `<span class="sl-nav-note" title="Apunte de la canción">📝 ${escapeHtml(note)}</span>` : ''}
            <button id="sl-next" class="secondary-btn" ${nextDis} aria-label="Siguiente canción">▶</button>`;
        elNav.style.display = 'flex';
        const p = document.getElementById('sl-prev'); if (p && !prevDis) p.addEventListener('click', () => go(pos - 1));
        const n = document.getElementById('sl-next'); if (n && !nextDis) n.addEventListener('click', () => go(pos + 1));
    } catch (e) { /* sin barra si falla */ }
}
setupSetlistNav();

// Atajo de teclado: la barra espaciadora alterna play/pausa (T-021). Se ignora si el foco
// está en un campo de texto, para no romper la escritura.
document.addEventListener('keydown', (e) => {
    if (e.code !== 'Space' && e.key !== ' ') return;
    const tag = (e.target.tagName || '').toLowerCase();
    if (tag === 'input' || tag === 'textarea' || e.target.isContentEditable) return;
    e.preventDefault();  // evita el scroll por defecto de la barra espaciadora
    handlePlayPause();
});

// Pasapáginas / pedalera (V3-F4, T-092): las teclas de avance/retroceso que envían los pedales
// Bluetooth (PageDown/PageUp o flechas) pasan de canción dentro de un setlist o, si no hay setlist,
// hacen scroll de "una página" en la partitura. Manos libres en el atril. Se ignora en campos de texto.
document.addEventListener('keydown', (e) => {
    const tag = (e.target.tagName || '').toLowerCase();
    if (tag === 'input' || tag === 'textarea' || e.target.isContentEditable) return;
    const fwd = e.key === 'PageDown' || e.key === 'ArrowRight';
    const back = e.key === 'PageUp' || e.key === 'ArrowLeft';
    if (!fwd && !back) return;
    const navBtn = document.getElementById(fwd ? 'sl-next' : 'sl-prev');
    if (navBtn && !navBtn.disabled) {   // pasar de canción en el setlist
        e.preventDefault();
        navBtn.click();
        return;
    }
    const container = document.getElementById('score-container');
    if (container) {                    // o avanzar "una página" en la partitura
        e.preventDefault();
        const page = container.clientHeight * 0.85;
        container.scrollBy({ top: fwd ? page : -page, behavior: 'smooth' });
    }
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

// T-V5-09: mantener pulsado +/− acelera el cambio de BPM (press-and-hold, touch-friendly). Un toque
// corto sigue siendo ±1; al mantener, repite acelerando. El motor ya acota el BPM a [40, 240].
function bumpBpm(delta) { engine.setBpm(engine.state.bpm + delta); scheduleBpmSave(); }

function holdRepeatBpm(btn, delta) {
    let timer = null;
    function stop() { if (timer) { clearTimeout(timer); timer = null; } }
    btn.addEventListener('pointerdown', (e) => {
        if (e.button && e.button !== 0) return;    // solo botón principal / toque (ignora clic derecho)
        stop();
        bumpBpm(delta);                            // primer cambio inmediato (cubre el toque corto)
        let wait = 400;                            // la 1ª repetición tarda: un tap normal no repite
        (function step() {
            timer = setTimeout(() => {
                bumpBpm(delta);
                wait = Math.max(35, wait * 0.8);   // …y acelera mientras se mantiene pulsado
                step();
            }, wait);
        })();
    });
    ['pointerup', 'pointerleave', 'pointercancel'].forEach((ev) => btn.addEventListener(ev, stop));
    // Accesibilidad por teclado: Enter/Espacio = un solo paso (sin repetición).
    btn.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); bumpBpm(delta); }
    });
}
holdRepeatBpm(elBtnBpmUp, 1);
holdRepeatBpm(elBtnBpmDown, -1);

// --- Metrónomo (Web Audio API) ---
let metronomeOn = false;
let audioCtx = null;
let lastClickedBeat = -1; // último beat entero al que ya sonó el clic
const elBtnMetronome = document.getElementById('btn-metronome');

// T-V5-12: el clic y el acento por compás viven en `metronome.js` (compartido con la sección
// Afinador/Metrónomo). `playClick` es un alias fino sobre `bfMetronomeClick` con el audioCtx del player.
function playClick(level) { bfMetronomeClick(audioCtx, level); }

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
        const num = (currentSong && currentSong.time_signature_num) || 4;
        const den = (currentSong && currentSong.time_signature_den) || 4;
        playClick(bfBeatAccent(beat, num, den));   // acento por compás (compartido, T-V5-12)
    }
});

// --- Cuenta atrás (pre-roll) antes de reproducir (T-V5-08) ---------------------
// Al darle a Play DESDE EL PRINCIPIO (motor en 'idle') se cuentan N golpes al BPM actual y luego
// arranca. N es configurable (apagada · 4 · 8) con el botón de al lado del metrónomo, persistido en el
// dispositivo. La cuenta SUENA sólo si el metrónomo está activado (D-PLY-2); si no, es sólo visual.
const COUNTIN_KEY = 'bf-countin';
const COUNTIN_STEPS = [0, 4, 8];   // ciclo del botón
const _savedCountIn = parseInt(localStorage.getItem(COUNTIN_KEY), 10);
// Default 4 golpes (elección de Oscar): un compás de aviso antes de arrancar. El botón la cambia a 8
// o la apaga (–), y la elección se recuerda en el dispositivo.
let countInBeats = COUNTIN_STEPS.includes(_savedCountIn) ? _savedCountIn : 4;
let countInTimer = null;

const elBtnCountIn = document.getElementById('btn-countin');
const elCountInOverlay = document.getElementById('countin-overlay');
const elCountInNum = document.getElementById('countin-num');

function paintCountInBtn() {
    if (!elBtnCountIn) return;
    elBtnCountIn.textContent = countInBeats > 0 ? String(countInBeats) : '–';
    const desc = countInBeats > 0 ? `${countInBeats} golpes` : 'apagada';
    elBtnCountIn.title = `Cuenta atrás antes del Play: ${desc} (clic para cambiar)`;
    elBtnCountIn.setAttribute('aria-label', `Cuenta atrás antes de reproducir: ${desc}`);
    // Estado activo como el metrónomo: fondo coral + texto oscuro (indicador claro de "encendido").
    elBtnCountIn.style.background = countInBeats > 0 ? 'var(--accent-color)' : 'rgba(255,255,255,0.08)';
    elBtnCountIn.style.color = countInBeats > 0 ? '#000' : 'var(--text-primary)';
}
paintCountInBtn();

if (elBtnCountIn) elBtnCountIn.addEventListener('click', () => {
    const i = COUNTIN_STEPS.indexOf(countInBeats);
    countInBeats = COUNTIN_STEPS[(i + 1) % COUNTIN_STEPS.length];
    localStorage.setItem(COUNTIN_KEY, String(countInBeats));
    paintCountInBtn();
});

function showCountInNum(n) {
    if (!elCountInOverlay || !elCountInNum) return;
    elCountInNum.textContent = String(n);
    elCountInOverlay.hidden = false;
    elCountInNum.style.animation = 'none';   // re-lanza el "pop" en cada número
    void elCountInNum.offsetWidth;
    elCountInNum.style.animation = '';
}

function cancelCountIn() {
    if (countInTimer) { clearTimeout(countInTimer); countInTimer = null; }
    if (elCountInOverlay) elCountInOverlay.hidden = true;
}

function runCountIn(done) {
    const interval = 60000 / (engine.state.bpm || 120);   // ms por golpe, al BPM actual
    let n = countInBeats;
    const tick = () => {
        if (n <= 0) { cancelCountIn(); done(); return; }
        showCountInNum(n);
        if (metronomeOn) playClick(n === countInBeats ? 2 : 0);   // suena sólo con metrónomo (D-PLY-2)
        n--;
        countInTimer = setTimeout(tick, interval);
    };
    tick();
}

// Enrutado del Play: pausa si suena; aborta la cuenta si está en curso; cuenta atrás si arranca desde
// el principio (motor 'idle' y N>0); si no, arranca directo (reanudar desde pausa, o cuenta apagada).
function handlePlayPause() {
    if (countInTimer) { cancelCountIn(); return; }
    if (engine.state.status === 'playing') { engine.pause(); return; }
    if (engine.state.status === 'idle' && countInBeats > 0) runCountIn(() => engine.play());
    else engine.play();
}

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
        sectionRanges = computeSectionRanges(song);
        setupReference(song);

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
        sectionRanges = computeSectionRanges(data);
        setupReference(data);
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
