/**
 * SyncEngine - Motor de sincronización para ChordFlow
 * Es un módulo independiente del DOM que calcula en qué beat estamos 
 * y qué elementos deberían estar activos.
 */
class SyncEngine {
    constructor() {
        this.state = {
            status: "idle", // idle | playing | paused
            currentBeat: 0.0,
            bpm: 120,
            tempoMultiplier: 1.0,
            startTimestamp: 0,
            pausedAtBeat: 0.0,
            
            song: null,
            flatChords: [], // Lista plana de todos los acordes con su beat absoluto
            
            activeChordId: null
        };
        
        this.animationFrameId = null;
        this.listeners = [];
        
        // Bindings
        this.tick = this.tick.bind(this);
    }

    // --- Observer Pattern ---
    subscribe(callback) {
        this.listeners.push(callback);
        return () => {
            this.listeners = this.listeners.filter(cb => cb !== callback);
        };
    }

    emitUpdate() {
        this.listeners.forEach(cb => cb(this.state));
    }

    // --- Carga de datos ---
    loadSong(songData) {
        this.state.song = songData;
        this.state.bpm = songData.bpm || 120;
        this.state.currentBeat = 0.0;
        this.state.pausedAtBeat = 0.0;
        this.state.status = "idle";
        
        // Aplanar acordes para búsqueda rápida.
        // Calculamos un beat absoluto robusto:
        //  - Si la línea no trae beat_start, usamos un cursor acumulado (fallback).
        //  - Si todos los acordes de la línea comparten el mismo offset (caso típico
        //    del Intro `: F#m : C#7 :` o de varias columnas sin tiempos), los repartimos
        //    uniformemente para que cada uno se resalte en su turno.
        this.state.flatChords = [];
        let beatCursor = 0.0;
        if (songData.sections) {
            songData.sections.forEach(sec => {
                if (!sec.lines) return;
                sec.lines.forEach(line => {
                    const lineDuration = line.beat_duration || 4.0;
                    const lineBeatStart = (line.beat_start !== null && line.beat_start !== undefined)
                        ? line.beat_start
                        : beatCursor;

                    const chords = line.chords || [];
                    const offsets = chords.map(c => c.beat_offset || 0);
                    const allSameOffset = offsets.every(o => o === offsets[0]);

                    chords.forEach((chord, idx) => {
                        let absStart;
                        if (allSameOffset && chords.length > 1) {
                            // Repartir uniformemente dentro de la duración de la línea
                            absStart = lineBeatStart + (idx * (lineDuration / chords.length));
                        } else {
                            absStart = lineBeatStart + (chord.beat_offset || 0);
                        }
                        this.state.flatChords.push({
                            id: chord.id,
                            absoluteBeatStart: absStart,
                            duration: chord.duration_beats || (lineDuration / Math.max(chords.length, 1))
                        });
                    });

                    beatCursor = lineBeatStart + lineDuration;
                });
            });
        }
        
        // Ordenar cronológicamente
        this.state.flatChords.sort((a, b) => a.absoluteBeatStart - b.absoluteBeatStart);

        // Duración total de la canción en beats (para el scroll continuo tipo teleprompter)
        this.state.totalBeats = Math.max(beatCursor, 1);

        this.emitUpdate();
    }

    // --- Controles de reproducción ---
    play() {
        if (this.state.status === "playing") return;
        if (!this.state.song) return;

        this.state.status = "playing";
        this.state.startTimestamp = performance.now();
        this.animationFrameId = requestAnimationFrame(this.tick);
        this.emitUpdate();
    }

    pause() {
        if (this.state.status !== "playing") return;
        
        this.state.status = "paused";
        this.state.pausedAtBeat = this.state.currentBeat;
        if (this.animationFrameId) cancelAnimationFrame(this.animationFrameId);
        this.emitUpdate();
    }

    stop() {
        this.state.status = "idle";
        this.state.currentBeat = 0.0;
        this.state.pausedAtBeat = 0.0;
        this.state.activeChordId = null;
        if (this.animationFrameId) cancelAnimationFrame(this.animationFrameId);
        this.emitUpdate();
    }

    setBpm(newBpm) {
        // Si estamos reproduciendo, necesitamos ajustar el startTimestamp para que la posición no salte
        if (this.state.status === "playing") {
            this.state.pausedAtBeat = this.state.currentBeat;
            this.state.startTimestamp = performance.now();
        }
        this.state.bpm = Math.max(40, Math.min(240, newBpm));
        this.emitUpdate();
    }

    // --- El Bucle Principal ---
    tick(timestamp) {
        if (this.state.status !== "playing") return;

        const elapsedMs = timestamp - this.state.startTimestamp;
        const elapsedSec = elapsedMs / 1000;
        const beatsPerSec = (this.state.bpm * this.state.tempoMultiplier) / 60;
        
        this.state.currentBeat = this.state.pausedAtBeat + (elapsedSec * beatsPerSec);

        // Buscar acorde activo
        const newActiveChordId = this.findActiveChord(this.state.currentBeat);
        
        let changed = false;
        if (newActiveChordId !== this.state.activeChordId) {
            this.state.activeChordId = newActiveChordId;
            changed = true;
        }

        // Siempre emitimos update para que el DOM pueda actualizar el currentBeat (reloj) o el scroll
        this.emitUpdate();
        
        this.animationFrameId = requestAnimationFrame(this.tick);
    }

    findActiveChord(currentBeat) {
        // El acorde activo es el ÚLTIMO cuyo inicio ya ha pasado (los acordes están ordenados
        // por beat). Esta formulación arregla varios casos borde frente al intervalo semiabierto
        // anterior (T-040):
        //  - ÚLTIMO acorde: permanece activo hasta el final de la canción (antes se apagaba en
        //    start+duration, dejando la parte final sin acorde resaltado).
        //  - EMPATES (dos acordes con el mismo beat de inicio): gana el último, no se "saltan".
        //  - RESET: antes del primer acorde no hay activo (devuelve null).
        // En un caso real con miles de acordes usaríamos búsqueda binaria; para el MVP, iterar.
        let activeId = null;
        for (let i = 0; i < this.state.flatChords.length; i++) {
            const chord = this.state.flatChords[i];
            if (currentBeat >= chord.absoluteBeatStart) {
                activeId = chord.id;        // su inicio ya pasó → candidato
            } else {
                break;                       // ordenados: los siguientes empiezan más tarde
            }
        }
        return activeId;
    }
}
