/**
 * metronome.js — Metrónomo compartido (T-V5-12, V5-F3).
 *
 * UNA sola fuente para el "clic" y el acento por compás, para que el reproductor (app.js) y la
 * sección Afinador/Metrónomo (afinador.html) suenen EXACTAMENTE igual (guía §4: "el mismo metrónomo").
 *
 * - `bfMetronomeClick(audioCtx, level)`: genera el clic (Web Audio). level 2=acento fuerte (tiempo 1),
 *   1=acento medio (grupo de compás compuesto), 0=débil.
 * - `bfBeatAccent(beat, num, den)`: nivel de acento de un beat (0-indexado) según el compás.
 * - `BfMetronome`: metrónomo STANDALONE (su propio bucle a BPM) con tap-tempo, para la sección. El
 *   player NO usa el bucle (clica en los cruces de beat del motor), solo el clic y el acento.
 */

// Clic corto por oscilador. Distinto tono/volumen por nivel para que "suene distinto el 1".
function bfMetronomeClick(audioCtx, level) {
    if (!audioCtx) return;
    const osc = audioCtx.createOscillator();
    const gain = audioCtx.createGain();
    osc.connect(gain);
    gain.connect(audioCtx.destination);
    osc.frequency.value = level >= 2 ? 1500 : level === 1 ? 1200 : 900;
    const now = audioCtx.currentTime;
    const vol = level >= 2 ? 0.5 : level === 1 ? 0.4 : 0.3;
    gain.gain.setValueAtTime(vol, now);
    gain.gain.exponentialRampToValueAtTime(0.0001, now + 0.05);
    osc.start(now);
    osc.stop(now + 0.05);
}

// Nivel de acento de un beat dentro del compás: fuerte en el 1; en compás compuesto (denominador 8 y
// numerador múltiplo de 3, p. ej. 6/8, 9/8, 12/8) acento medio en cada grupo de 3; débil el resto.
function bfBeatAccent(beat, num, den) {
    const inBar = (((beat % num) + num) % num);
    if (inBar === 0) return 2;
    if (den === 8 && num % 3 === 0 && inBar % 3 === 0) return 1;
    return 0;
}

// Metrónomo standalone: su propio bucle a BPM (setTimeout), con tap-tempo y callback de tick (para el
// flash visual). El AudioContext se crea perezosamente en el primer arranque (gesto del usuario).
class BfMetronome {
    constructor() {
        this.audioCtx = null;
        this.bpm = 120;
        this.num = 4;
        this.den = 4;
        this.running = false;
        this.onTick = null;   // (beatEnCompas, nivelAcento) => void
        this._beat = 0;
        this._timer = null;
        this._taps = [];
    }

    setTempo(bpm) { this.bpm = Math.max(40, Math.min(240, Math.round(bpm))); return this.bpm; }
    setMeter(num, den) { this.num = num; this.den = den; }

    // Tap-tempo: promedia los intervalos entre toques recientes (olvida los de hace > 2 s).
    tap() {
        const now = performance.now();
        this._taps = this._taps.filter((t) => now - t < 2000);
        this._taps.push(now);
        if (this._taps.length >= 2) {
            let sum = 0;
            for (let i = 1; i < this._taps.length; i++) sum += this._taps[i] - this._taps[i - 1];
            const avg = sum / (this._taps.length - 1);
            if (avg > 0) this.setTempo(60000 / avg);
        }
        return this.bpm;
    }

    _ensureCtx() {
        if (!this.audioCtx) this.audioCtx = new (window.AudioContext || window.webkitAudioContext)();
    }

    start() {
        if (this.running) return;
        this._ensureCtx();
        this.running = true;
        this._beat = 0;
        const step = () => {
            if (!this.running) return;
            const level = bfBeatAccent(this._beat, this.num, this.den);
            bfMetronomeClick(this.audioCtx, level);
            if (this.onTick) this.onTick(this._beat % this.num, level);
            this._beat++;
            this._timer = setTimeout(step, 60000 / this.bpm);
        };
        step();
    }

    stop() {
        this.running = false;
        if (this._timer) { clearTimeout(this._timer); this._timer = null; }
    }

    toggle() { if (this.running) this.stop(); else this.start(); }
}

// --- Repetición al mantener pulsado (mismo patrón que el BPM del player, T-V5-09) -------------
// Toque corto = un paso; mantener = repite acelerando (400→35 ms). Teclado: Enter/Espacio = un paso.
function bfHoldRepeat(btn, fire) {
    let timer = null;
    function stop() { if (timer) { clearTimeout(timer); timer = null; } }
    btn.addEventListener('pointerdown', (e) => {
        if (e.button && e.button !== 0) return;    // solo botón principal / toque (ignora clic derecho)
        stop();
        fire();                                    // primer cambio inmediato (cubre el toque corto)
        let wait = 400;                            // la 1ª repetición tarda: un tap normal no repite
        (function step() {
            timer = setTimeout(() => {
                fire();
                wait = Math.max(35, wait * 0.8);   // …y acelera mientras se mantiene pulsado
                step();
            }, wait);
        })();
    });
    ['pointerup', 'pointerleave', 'pointercancel'].forEach((ev) => btn.addEventListener(ev, stop));
    btn.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); fire(); }
    });
}

// --- Panel standalone (T-V5-13, afinador.html) ------------------------------------------------
// Mismo patrón que tuner.js: si la página no tiene el panel, no hacer nada (el player carga este
// archivo solo por el clic/acento compartidos de arriba).
(function () {
    const panel = document.getElementById('metro-panel');
    if (!panel) return;

    const elBpm = document.getElementById('metro-bpm');
    const elMeter = document.getElementById('metro-meter');
    const elStart = document.getElementById('metro-start');
    const elTap = document.getElementById('metro-tap');
    const elBeats = document.getElementById('metro-beats');

    const m = new BfMetronome();
    window.bfMetro = m;   // expuesto para consola y tests (como bfDetectPitch en tuner.js)

    // BPM y compás persistidos en el dispositivo (como la cuenta atrás del player, T-V5-08).
    const BPM_KEY = 'bf-metro-bpm', METER_KEY = 'bf-metro-meter';
    const savedBpm = parseInt(localStorage.getItem(BPM_KEY), 10);
    if (!Number.isNaN(savedBpm)) m.setTempo(savedBpm);
    const savedMeter = localStorage.getItem(METER_KEY);
    if (savedMeter && /^\d+\/\d+$/.test(savedMeter)) {
        const [n, d] = savedMeter.split('/');
        m.setMeter(parseInt(n, 10), parseInt(d, 10));
    }
    elMeter.value = m.num + '/' + m.den;

    function renderBpm() {
        elBpm.textContent = m.bpm;
        localStorage.setItem(BPM_KEY, String(m.bpm));
    }

    // Un punto por beat del compás; `onTick` ilumina el activo (el 1, acentuado, brilla más).
    function renderPips() {
        elBeats.innerHTML = '';
        for (let i = 0; i < m.num; i++) {
            const dot = document.createElement('span');
            dot.className = 'metro-pip';
            elBeats.appendChild(dot);
        }
    }

    m.onTick = (beatInBar, level) => {
        const pips = elBeats.children;
        for (let i = 0; i < pips.length; i++) {
            pips[i].classList.toggle('metro-pip--on', i === beatInBar);
            pips[i].classList.toggle('metro-pip--accent', i === beatInBar && level >= 2);
        }
    };

    bfHoldRepeat(document.getElementById('metro-down'), () => { m.setTempo(m.bpm - 1); renderBpm(); });
    bfHoldRepeat(document.getElementById('metro-up'), () => { m.setTempo(m.bpm + 1); renderBpm(); });

    elMeter.addEventListener('change', () => {
        const [n, d] = elMeter.value.split('/');
        m.setMeter(parseInt(n, 10), parseInt(d, 10));
        localStorage.setItem(METER_KEY, elMeter.value);
        renderPips();
    });

    elTap.addEventListener('click', () => { m.tap(); renderBpm(); });

    elStart.addEventListener('click', () => {
        m.toggle();
        elStart.textContent = m.running ? 'Parar' : 'Iniciar';
        elStart.classList.toggle('metro-running', m.running);
        if (!m.running) renderPips();   // reposo: puntos apagados
    });

    renderBpm();
    renderPips();
})();
