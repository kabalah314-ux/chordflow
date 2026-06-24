# GUÍA MAESTRA V4 — Implementación paso a paso

> **Qué es esto.** El plan ejecutable de la V4 (mejoras de experiencia y diseño). Convierte cada punto
> de `GUIA_MAESTRA_V4_UX.md` (V3) en **tareas T-NNN** con pasos concretos, test y verificación, en el
> **orden correcto de dependencias**. Se desarrolla **fase a fase, punto por punto**.
>
> **Cómo se ejecuta cada tarea (bucle de oro, CLAUDE.md §2):** abrir la tarea → implementar → `python
> harness/doctor.py` verde → test que la cubre → `python harness/cachebust.py` (tras tocar js/css) →
> `python harness/run_checks.py` verde → registrar en `REGISTRO_DE_CAMBIOS.md` → desplegar (push a
> `main`) → verificar en vivo. Cada tarea es **un commit/deploy** independiente y reversible.
>
> **Estado:** 🟢 **V4-F1 desarrollada (lista para ejecutar).** F2–F6 se desarrollarán a continuación.
>
> _Implementación V1 — 2026-06-24._

---

## FASE V4-F1 — Cimientos coherentes

> **Meta:** que la app se sienta "de una pieza" y con vida, sin tocar backend. Todo front/CSS.
> **Orden (por dependencias):** T-120 → T-121 → T-122 → T-123 → T-124 → T-125 → T-126 → T-127 → T-128.
> Las dos primeras son cimientos que usan las demás (tokens y helpers).

---

### T-120 — Unificar el token de acento (una sola fuente de verdad)
**Objetivo.** Que exista UN solo coral. `style.css` (legacy) hereda de los tokens `bf-*`. Efecto
secundario regalo: el **modo claro** empieza a funcionar en las páginas legacy.

**Pasos.**
1. En `static/style.css:11-14`, cambiar los valores literales por herencia:
   `--accent-color: var(--bf-primary);` · `--accent-hover: var(--bf-primary-hover);`
   `--chord-color: var(--bf-primary);` · `--chord-active-bg: var(--bf-accent-weak);`
2. Añadir un token de glow reutilizable en `design-system.css` (`:root` y tema claro):
   `--bf-accent-glow: rgba(255,107,74,.45);` (y su equivalente en `[data-theme="light"]`).
3. En `style.css`, sustituir los literales `#ff6b4a` / `rgba(255,107,74,…)` por `var(--accent-color)` o
   `var(--bf-accent-glow)` (sombras/glows en líneas ~145,165,266,288-289,295,348,356-357,477,555,576,
   739,809,916,1007,1033-1034 — confirmar con grep al implementar).
4. Borrar los fallbacks muertos verde-menta: `, #6ee7b7` en `style.css:653` y `:1094`.
5. **Pre-requisito:** asegurar que las páginas legacy que aún no cargan `design-system.css` lo carguen
   (para que `var(--bf-primary)` resuelva). Comprobar `index.html`, `editor.html`, `setlists.html`,
   `profile.html`, `login.html`; añadir `<link rel="stylesheet" href="design-system.css?v=…">` donde falte.
   *(Biblioteca/explorar ya lo cargan.)*

**Test.** e2e `test_acento_unificado_y_tema`: cargar una página legacy (p. ej. `setlists.html`), leer
`getComputedStyle(.primary-btn).backgroundColor` → coincide con el coral; togglear `data-theme="light"`
(via `document.documentElement.dataset.theme='light'`) y comprobar que cambia (ya no es el mismo oscuro).

**Verificación.** Doctor verde; en vivo, los botones legacy siguen coral y el modo claro no deja restos
naranjas mal contrastados. Riesgo bajo (solo color). **Notas:** ejecutar `cachebust` tras tocar css.

---

### T-121 — Helpers compartidos de identidad a `util.js`
**Objetivo.** Color e iniciales por banda reutilizables en avatar, tarjetas y etiquetas (hoy `hueFromId`
está encerrado en `band.js` y `initialsFrom` duplicado).

**Pasos.**
1. En `static/util.js` añadir globales:
   `bandHue(id)` (hash char-code → 0-359), `bandColor(id,{s=55,l=48})` → `hsl(...)`,
   `initialsFrom(name)` (1-2 iniciales, fallback 🎸).
2. En `static/band.js`: sustituir el `hueFromId` local (`band.js:18-22,80`) por `bandColor(bandId)` y
   usar el `initialsFrom` global (quitar el duplicado `band.js:23-26`).
3. En `static/shell.js`: usar el `initialsFrom` global (quitar el duplicado `shell.js:89-93`).

**Test.** e2e/JS `test_helpers_identidad`: `page.evaluate` comprueba `typeof bandColor==='function'`,
que `bandColor('x')===bandColor('x')` (determinista) y que `bandColor('a')!==bandColor('b')`, y que
`initialsFrom('Los Demo Riff')==='LD'`.

**Verificación.** El banner de banda sigue mostrando el mismo avatar de color (sin regresión). Doctor +
cachebust.

---

### T-122 — Ampliar `icons.js` y cargarlo donde falta
**Objetivo.** Tener todos los iconos SVG necesarios y `bfIcon` disponible en TODAS las páginas.

**Pasos.**
1. En `static/icons.js`, añadir a `PATHS` los trazos Lucide (viewBox 24×24, MIT) de: `play, pause, stop,
   plus, minus, save, printer, mic, film, drum (o timer), maximize, minimize, folder, arrow-left, edit
   (pencil), trash, x, note (pencil-line)`.
2. Añadir `<script src="icons.js?v=…">` (antes de `app.js`/su script) en `static/index.html` y
   `static/editor.html` (hoy NO lo cargan). Verificar que las demás páginas legacy que vayan a usar
   `bfIcon` (`setlists.html`, `profile.html`) también lo carguen.

**Test.** e2e `test_iconos_disponibles`: en el reproductor (`index.html?...`) `page.evaluate("typeof
bfIcon")==='function'` y `bfIcon('play')` contiene `<svg`; idem `editor.html`.

**Verificación.** No hay regresión visual aún (solo se cargan defs). Doctor + cachebust.

---

### T-123 — Iconos SVG en el reproductor (la joya)
**Objetivo.** Cambiar los 11 emoji del player por SVG con tooltips, sin tocar el motor.
**Depende de:** T-122.

**Pasos.**
1. En `static/index.html`, sustituir el contenido emoji de cada botón por `bfIcon`:
   - Top: `btn-key-save` 💾→`save`, `btn-tuner` 🎤→`mic`, `btn-reference` 🎬→`film`, `btn-print`
     🖨️→`printer`, navegación 🏠→`home` 📚→`library` ➕→`plus`. (`+/−/♭/♯` se quedan como glifo.)
   - Bottom: `btn-metronome` 🥁→`drum`/`timer`, `btn-stop` ⏹→`stop`, `btn-stage` ⛶→`maximize`.
2. `btn-play-pause`: en `static/app.js:75,78` cambiar el `innerHTML` a `${bfIcon('pause')} Pause` /
   `${bfIcon('play')} Play` (mantener el texto " Play"/" Pause" si un test lo asierta — comprobar
   `tests/e2e` antes; si lo asierta, conservar la palabra junto al icono).
3. Mantener `aria-label`/`title` existentes en cada botón (los SVG ya van `aria-hidden`).

**Test.** e2e `test_player_iconos_svg`: el reproductor carga; los botones de control contienen `<svg>`
(no emoji); `#btn-play-pause` sigue arrancando la reproducción (clic → `Beat` avanza / aria-pressed).

**Verificación.** Reproductor en vivo: iconos limpios, tooltips, play/stop/stage funcionan. **Riesgo:**
un e2e que busque el texto "▶"/"⏸" — revisar `tests/e2e/test_modo_directo*`/player antes. cachebust.

---

### T-124 — Iconos SVG en el resto (setlists, perfil, biblioteca, catálogo) + "quitar ≠ borrar"
**Objetivo.** Erradicar los emoji de chrome restantes y diferenciar quitar (neutro) de borrar (rojo).
**Depende de:** T-122.

**Pasos.**
1. Reemplazar emoji por `bfIcon` en: `static/setlists.js` (✏️→`edit`, 🗑️→`trash`, ➕→`plus`, ✕→`x`,
   📝→`note`, 💾→`save`, ⚠️ se puede dejar en mensajes), `static/profile.js` (💾→`save`),
   `static/library.js` (✏️→`edit`, 🗑️→`trash`, 📁→`folder`, ➕→`plus`, 👤/🎸 badges: valorar mantener
   como texto del badge —los tests leen el texto— o icono+texto), `static/catalogo.js` (⬇→`download`,
   etc.).
2. **Quitar ≠ borrar (punto 3.3):** los botones de "quitar de la lista" (repertorio/colección/setlist)
   pasan a icono neutro (`x`/`minus`, color secundario); el rojo (`danger`) queda SOLO para borrado real
   (soft delete). Ajustar clases en `bands.js`/`setlists.js`/`library.js`.

**Test.** Reutilizar/ampliar los e2e existentes (`test_library`, `test_setlists_ui`, `test_bands_ui`)
para que sigan verdes con los nuevos selectores (los `data-act`/clases no cambian → deberían pasar);
añadir una aserción de que un botón "quitar" no tiene la clase `danger`.

**Verificación.** Las páginas se ven coherentes (cero emoji de chrome). Doctor + cachebust. **Nota:**
conservar el texto de los badges de fuente en `#song-grid` (test `test_library.py:80`).

---

### T-125 — `setlists.html` dentro del shell
**Objetivo.** Que los Setlists usen el lateral como el resto (hoy usa la top-bar antigua).

**Pasos.**
1. Reescribir el `<body>` de `static/setlists.html` al patrón shell (espejo de `library.html`):
   `<div class="bf-shell"><main class="bf-shell-main"><div class="bf-page">`; cabecera con
   `bf-row bf-row--between` (título "🎵 Setlists" → con `bfIcon('music')` + "Setlists", y botón
   "➕ Nuevo setlist"). Quitar la top-bar antigua y los enlaces 🏠/📚 (los da el lateral).
2. Cargar en el `<head>`/scripts: `design-system.css`, `shell.css`, y antes de `setlists.js`:
   `icons.js`, `shell.js` (+ `util.js`, `auth.js` que ya están).
3. `setlists.js` no cambia de lógica (usa `#setlist-grid`/`#setlist-detail`/`#sl-*`); revisar que el
   contenedor del grid/detalle siga existiendo con esos ids dentro del `.bf-page`.

**Test.** Ampliar `test_setlists_accesible_desde_la_biblioteca` (ya existe): además de `h1` "Setlists",
comprobar que existe `.bf-shell` y el lateral (`.bf-nav-item`), y que crear/ver un setlist sigue
funcionando (reutiliza `test_setlists_ui`).

**Verificación.** Setlists con lateral, coherente con Biblioteca. Doctor + cachebust + e2e.

---

### T-126 — Terminología: pestaña "Repertorio" + sección "Colecciones"
**Objetivo.** Quitar la ambigüedad: la pestaña (que muestra el pool + las colecciones) se llama
**"Repertorio"**; los grupos temáticos, **"Colecciones"**.

**Pasos.** Cambios SOLO de texto visible (no tocar `key:'repertorio'`/`data-tab` ni ids):
1. `static/band.js`: `:31` label de pestaña `'Repertorios'`→`'Repertorio'`; `:133` `<h3>`
   `Repertorios`→`Colecciones`; `:134` botón `➕ Nuevo repertorio`→`➕ Nueva colección`; `:136` texto de
   ayuda (ya menciona "agrupar por tema") — ajustar a "Colecciones".
2. `static/bands.js`: textos de colecciones en `:951,953,960,967,973,1011,1020,1065,1073,1075`
   ("repertorio(s)"→"colección/colecciones", back-link "← Volver a Colecciones", prompts/toasts).
3. NO tocar: `loadRepertoire`/`#b-repertoire`/"Todas las canciones" (eso es el pool, correcto).

**Test.** e2e `test_terminologia_colecciones`: en `band.html` pestaña Repertorio, la sección dice
"Colecciones" y el botón "Nueva colección"; `data-tab="repertorio"` sigue existiendo (no romper).
Verificar que `test_bands_ui` (crear colección) sigue verde (usa ids/nombres, no la palabra).

**Verificación.** Banda: "Repertorio" (pestaña) con "Colecciones" dentro; coherente con la Biblioteca
personal. Doctor + cachebust.

---

### T-127 — Estados hover/active/focus + transiciones unificados
**Objetivo.** Que todo lo clicable lo parezca y se sienta fluido.

**Pasos.**
1. En `static/design-system.css`:
   - Hover para `.bf-list-item` (hoy no tiene): `background: var(--bf-hover); border-color:
     var(--bf-border-strong); transition: var(--bf-transition);` + `cursor:pointer`.
   - Igualar el "lift" de cards (token `--bf-lift: translateY(-2px)`), usado por `.bf-card--interactive`
     y `.song-card`.
   - Subrayado deslizante en `.bf-tab` (transición de `border`/`transform`).
   - Fade+scale en `.modal-overlay`/`.modal-card` (keyframes cortos) + guard `prefers-reduced-motion`.
2. En `static/style.css` (legacy): añadir un bloque `:focus-visible` accesible reutilizado para
   `.song-card, .setlist-song, .icon-btn, .card-action-btn, .primary-btn, .secondary-btn, .lib-filter`
   (`outline: 2px solid var(--accent-color); outline-offset: 2px;`); hover+transición para
   `.setlist-song` (hoy estática).

**Test.** e2e `test_estados_interaccion`: enfocar por teclado (`page.keyboard`) una `.song-card` y
comprobar `outline` ≠ none (`:focus-visible`); hover sobre una `.bf-list-item` cambia el fondo. (Usar
`getComputedStyle`.)

**Verificación.** Navegación por teclado visible; hover por todas partes; modales con transición.
Respetar reduced-motion. Doctor + cachebust.

---

### T-128 — Pestañas de banda: fade + scroll-snap en móvil
**Objetivo.** Que en móvil se vea que hay más pestañas a la derecha.

**Pasos.**
1. En `static/design-system.css` `.bf-tabs` (`:243-264`): añadir
   `-webkit-mask-image`/`mask-image: linear-gradient(to right, transparent 0, #000 16px, #000
   calc(100% - 16px), transparent 100%);` y `scroll-snap-type: x proximity;` + `.bf-tab{
   scroll-snap-align: start; }`.
2. En `static/band.js`, al activar una pestaña, `el.scrollIntoView({inline:'nearest'})` para que la
   activa quede a la vista.

**Test.** e2e `test_pestanas_fade_movil`: en viewport móvil (390px), `.bf-tabs` tiene `mask-image` no
vacío (computed) y `scrollWidth > clientWidth` (hay scroll). Verificar que las pestañas siguen
clicándose (reutiliza `test_band_space`).

**Verificación.** En móvil se intuye el scroll; clic de pestañas ok. Doctor + cachebust.

---

### Cierre de V4-F1
- `run_checks` TODO VERDE en cada tarea · `revision.py` no aplica (no hay rutas nuevas; es front) ·
  registro en `REGISTRO_DE_CAMBIOS.md` · capturas de antes/después (re-usar el flujo de seed_demo +
  Playwright del estudio visual) para confirmar el salto de coherencia.
- Resultado esperado: cero emoji de chrome, un solo acento (+ modo claro legacy), setlists en el shell,
  terminología clara, y toda la UI con hover/foco/transiciones. **Base lista para F2.**

---

## FASES V4-F2 … V4-F6 — (por desarrollar)

> Se desarrollarán con el mismo nivel de detalle (tarea a tarea) a continuación. Resumen de lo que
> traerán (detalle en `GUIA_MAESTRA_V4_UX.md` V3 §9):
> - **V4-F2 — Paneles de control:** `GET /bands/{id}/summary` + Resumen útil · Inicio panel de control ·
>   tarjeta de banda rica (+`song_count`). *(Único backend de la V4, sin migración.)*
> - **V4-F3 — Tarjetas, densidad y carga:** tarjeta de canción con play · agenda más limpia (⋯) ·
>   skeletons en todo · ancho + `.bf-grid` · microinteracciones.
> - **V4-F4 — La joya en directo:** top-bar ordenada · escenario espectacular · drag&drop setlist · atajos.
> - **V4-F5 — Funcionalidad y remate:** añadir-a desde tarjeta · buscadores · duplicar · banda en lateral ·
>   login · tour · tipografía · modo claro (remate) · accesibilidad · caché por temporada.
> - **V4-F6 — Config (🔌):** avatares/logos (Storage) · notificaciones · EPK/realtime.
