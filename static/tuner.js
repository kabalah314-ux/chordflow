/**
 * tuner.js — Afinador integrado (V3-F4, T-091).
 *
 * Detección de tono por autocorrelación (algoritmo clásico) sobre el micrófono (Web Audio API).
 * Todo client-side y gratis. La detección es una FUNCIÓN PURA (`bfDetectPitch`) — testeable con una
 * onda sintética sin micro — y el plumbing de micro/UI va aparte.
 *
 * Se auto-conecta a `#btn-tuner` (abrir/cerrar) y `#tuner-panel` en el reproductor. En la página
 * standalone `afinador.html` (T-161) no hay botón: el panel está siempre visible (sin toggle).
 */
(function () {
    const NOTE_NAMES = ['Do', 'Do#', 'Re', 'Re#', 'Mi', 'Fa', 'Fa#', 'Sol', 'Sol#', 'La', 'La#', 'Si'];

    // --- Detección de tono (autocorrelación). Devuelve Hz, o -1 si no hay señal clara. ---
    function autoCorrelate(buf, sampleRate) {
        const SIZE = buf.length;
        let rms = 0;
        for (let i = 0; i < SIZE; i++) rms += buf[i] * buf[i];
        rms = Math.sqrt(rms / SIZE);
        if (rms < 0.01) return -1;                 // demasiado silencio

        let r1 = 0, r2 = SIZE - 1;
        const thres = 0.2;
        for (let i = 0; i < SIZE / 2; i++) if (Math.abs(buf[i]) < thres) { r1 = i; break; }
        for (let i = 1; i < SIZE / 2; i++) if (Math.abs(buf[SIZE - i]) < thres) { r2 = SIZE - i; break; }
        const b = buf.slice(r1, r2);
        const n = b.length;

        const c = new Array(n).fill(0);
        for (let i = 0; i < n; i++) for (let j = 0; j < n - i; j++) c[i] += b[j] * b[j + i];

        let d = 0;
        while (d < n - 1 && c[d] > c[d + 1]) d++;   // saltar la cresta inicial
        let maxval = -1, maxpos = -1;
        for (let i = d; i < n; i++) if (c[i] > maxval) { maxval = c[i]; maxpos = i; }
        let T0 = maxpos;
        if (T0 <= 0) return -1;

        // Interpolación parabólica para afinar el periodo.
        const x1 = c[T0 - 1] || 0, x2 = c[T0] || 0, x3 = c[T0 + 1] || 0;
        const a = (x1 + x3 - 2 * x2) / 2, bb = (x3 - x1) / 2;
        if (a) T0 = T0 - bb / (2 * a);
        return sampleRate / T0;
    }

    // Hz → nota más cercana + desvío en cents (negativo = bajo, positivo = alto).
    function freqToNote(freq) {
        if (!freq || freq <= 0) return null;
        const midi = 12 * Math.log2(freq / 440) + 69;     // A4 = 440 Hz = MIDI 69
        const rounded = Math.round(midi);
        const cents = Math.round((midi - rounded) * 100);
        const name = NOTE_NAMES[((rounded % 12) + 12) % 12];
        const octave = Math.floor(rounded / 12) - 1;
        return { name, octave, cents, freq };
    }

    // Exponer las funciones puras (testeables sin micrófono).
    window.bfDetectPitch = autoCorrelate;
    window.bfFreqToNote = freqToNote;

    // --- UI + micrófono ---------------------------------------------------------
    const btn = document.getElementById('btn-tuner');
    const panel = document.getElementById('tuner-panel');
    if (!panel) return;                                // ni player ni afinador.html: no hacer nada
    const standalone = !btn;

    const elNote = document.getElementById('tuner-note');
    const elCents = document.getElementById('tuner-cents');
    const elNeedle = document.getElementById('tuner-needle');
    const elStart = document.getElementById('tuner-start');
    const elMsg = document.getElementById('tuner-msg');

    let audioCtx = null, analyser = null, rafId = null, stream = null, running = false;

    function setReadout(note) {
        if (!note) { elNote.textContent = '—'; elCents.textContent = ''; if (elNeedle) elNeedle.style.left = '50%'; return; }
        elNote.textContent = note.name + note.octave;
        elCents.textContent = (note.cents > 0 ? '+' : '') + note.cents + ' cents';
        const within = Math.abs(note.cents) <= 5;
        elNote.style.color = within ? 'var(--success-color, #2dd4a7)' : 'var(--accent-color)';
        if (elNeedle) elNeedle.style.left = Math.max(0, Math.min(100, 50 + note.cents)) + '%';
    }

    function loop() {
        if (!running || !analyser) return;
        const buf = new Float32Array(analyser.fftSize);
        analyser.getFloatTimeDomainData(buf);
        const freq = autoCorrelate(buf, audioCtx.sampleRate);
        if (freq > 0) setReadout(freqToNote(freq));
        rafId = requestAnimationFrame(loop);
    }

    async function startMic() {
        if (running) return;
        try {
            stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            audioCtx = new (window.AudioContext || window.webkitAudioContext)();
            const src = audioCtx.createMediaStreamSource(stream);
            analyser = audioCtx.createAnalyser();
            analyser.fftSize = 2048;
            src.connect(analyser);
            running = true;
            panel.classList.add('tuner-live');   // T-V5-05: la aguja pasa a estado "vivo".
            if (elMsg) elMsg.textContent = 'Toca una cuerda…';
            elStart.textContent = 'Detener';
            loop();
        } catch (e) {
            if (elMsg) elMsg.textContent = 'No se pudo acceder al micrófono.';
        }
    }

    function stopMic() {
        running = false;
        panel.classList.remove('tuner-live');   // T-V5-05: aguja de vuelta al reposo (atenuada).
        if (rafId) cancelAnimationFrame(rafId);
        if (stream) stream.getTracks().forEach(t => t.stop());
        if (audioCtx) { try { audioCtx.close(); } catch (e) { /* ya cerrado */ } }
        audioCtx = analyser = stream = null;
        elStart.textContent = 'Activar micrófono';
        setReadout(null);
    }

    function togglePanel() {
        const open = panel.style.display !== 'none';
        if (open) { panel.style.display = 'none'; stopMic(); }
        else { panel.style.display = ''; if (elMsg) elMsg.textContent = ''; }   // T-V5-05: sin copy redundante con el botón.
    }

    if (btn) btn.addEventListener('click', togglePanel);
    if (elStart) elStart.addEventListener('click', () => (running ? stopMic() : startMic()));
    const close = document.getElementById('tuner-close');
    if (close) close.addEventListener('click', togglePanel);

    // Standalone: el panel ya está visible en el HTML — arranca en reposo, sin copy redundante.
    if (standalone && elMsg) elMsg.textContent = '';
})();
