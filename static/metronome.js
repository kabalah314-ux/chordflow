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
