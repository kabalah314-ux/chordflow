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
> **Estado:** 🟢 **V4-F1…F4 EJECUTADAS y desplegadas** + **F5 al 80% (8/10)**. Hechas y verificadas
> (`run_checks` verde): F1 (T-120…T-128 + T-124b), F2 (T-129…T-132), F3 (T-133…T-137), F4 (T-138…T-142),
> y de **F5**: T-143 (añadir-a), T-144 (buscador repertorio), T-145 (duplicar setlist), T-146 (banda en
> lateral), T-147 (login), T-148 (tour), T-149 (cifras tabulares), T-150 (modo claro legacy). **PENDIENTES
> de F5:** **T-151 (accesibilidad)** y **T-152 (caché por temporada)**. Luego **F6** (T-153…T-156, 🔌
> necesita config de Oscar). Decisiones cerradas: Resumen = Opción B · Inicio = Opción A.
>
> _Implementación V7 — 2026-06-25 (F1–F4 + F5 al 80% ejecutadas/desplegadas; falta T-151, T-152, F6)._

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

## Decisiones de diseño (cerradas con Oscar)

- **Resumen de banda → Opción B (dos columnas).** Izquierda: próximo evento (con confirmados + "¿Vas?")
  + último mensaje. Derecha: mi saldo + contadores (canciones/setlists/colecciones) + accesos rápidos.
  *"Adecuarla con lo más útil"* → libertad para mejorarla (cuenta atrás, etc.). → guía T-130.
- **Inicio → Opción A (hero protagonista).** Un hero a todo el ancho con el **próximo evento** (cuenta
  atrás + "¿Vas?"), y debajo una rejilla con saldo total, accesos rápidos y últimos mensajes. → guía T-131.
  *(Si más adelante se prefiere B "cuadrícula" o C "feed+lateral", solo cambia el render de `home.js`.)*

> **Retomar aquí (cuando toque EJECUTAR):** F1…F6 ya están desarrolladas. 1) llevar las tareas a
> `harness/ROADMAP.md` + `harness/TASKS.md`; 2) ejecutar **en orden F1 → F6**, tarea a tarea, con el
> bucle de oro (doctor + test + cachebust + deploy + verificación en vivo); 3) al cerrar cada fase,
> capturas antes/después y nota en `REGISTRO_DE_CAMBIOS.md`. **Empezar por T-120.**

---

## FASE V4-F2 — Paneles de control

> **Meta:** que cada pantalla **dé valor al entrar** (el mayor salto de percepción de la V4). Es el
> **único backend** de la V4 (dos endpoints/campos nuevos, **sin migración**: solo lecturas agregadas).
> **Depende de F1:** usa `bandColor`/`initialsFrom` (T-121) y `bfIcon` (T-122).
> **Orden (por dependencias):** T-129 (endpoint) → T-130 (Resumen) ; T-131 (Inicio) y T-132 (tarjeta de
> banda) en paralelo. **Regla de oro multi-tenant:** T-129 exige su test de aislamiento.

---

### T-129 — `GET /bands/{id}/summary` (el endpoint del Resumen)
**Objetivo.** Una sola ida y vuelta que devuelva todo lo que pinta el Resumen de banda, sin N+1 y con
aislamiento por pertenencia. **Backend puro** (el único *endpoint* nuevo de la V4).

**Pasos.**
1. **Schema** en `src/services/schemas.py` (junto a `BandSummary`, ~:305): nuevo `BandDashboard` con
   `next_event: Optional[EventSummary] = None` · `last_message: Optional[MessageOut] = None` ·
   `my_balance: Decimal = 0` · `counts: BandCounts` (sub-modelo `{songs:int, setlists:int,
   collections:int}`). Reusa `EventSummary` (ya trae `attendance`, `my_status`, `venue_name`) y
   `MessageOut` (trae `author_name`, `is_mine`) → cero schemas de datos nuevos.
2. **Endpoint** en `src/api/bands_router.py` (espejo del patrón `me_router`):
   `@router.get("/{band_id}/summary", response_model=BandDashboard)` con
   `membership: BandMembership = Depends(require_band_member)` (esto **es** el aislamiento → ajeno = 403/404).
   - `next_event`: misma query que `me_router.get_dashboard` (`me_router.py:74-86`) pero con
     `Event.band_id == band_id`, `.limit(1)`; rellenar `attendance[]` con el bloque anti-N+1 de
     `me_router.py:163-177` y `my_status` con el de `:87-98`. Mapear a `EventSummary` (incluye
     `venue_name` si lo trae el modelo).
   - `last_message`: último mensaje del **chat general** (`Message.event_id.is_(None)`,
     `order_by(created_at.desc()).first()`), patrón `me_router.list_my_conversations` (`:226-233`);
     `is_mine = (author_id == user_id)`.
   - `my_balance`: `compute_balances(txs, settles, members)` filtrado a esta banda (calcado de
     `me_router.list_my_balances` `:199-208`) → `.get(user_id, 0)`.
   - `counts`: tres `func.count` (canciones/setlists/colecciones **activas** de la banda, mismos modelos
     y filtro `deleted_at IS NULL` que usan `band_songs_router`/`band_setlists_router`/
     `band_collections_router`). Confirmar nombres de modelo con grep al implementar.
3. `user_id` lo da `membership.user_id` (ya viene de la dependencia).

**Test.** unit `test_band_summary_aislamiento` (**regla de oro**): miembro de banda A pide
`/bands/{A}/summary` → 200 con la forma esperada; el **mismo usuario** pide `/bands/{B}/summary` (banda
ajena) → **403/404**. Y `test_band_summary_forma`: con seed (1 evento futuro + 1 mensaje + 1 movimiento),
`next_event`/`last_message` no nulos, `my_balance` numérico y `counts.songs == nº sembrado`.

**Verificación.** Doctor verde + `revision.py` (¡hay ruta nueva! → debe salir ✅ integrada). Sin
`cachebust` (no toca front). **Riesgo bajo:** solo lectura agregada, sin migración.

---

### T-130 — Resumen de banda útil (Opción B, dos columnas)
**Objetivo.** Sustituir el Resumen estático por el dashboard de la banda. **Depende de:** T-129.

**Pasos.**
1. En `static/band.js`: el panel `data-panel="resumen"` (hoy estático, `band.js:112-123`) pasa a un
   contenedor `<div id="b-summary"><p class="loading-text">Cargando…</p></div>`.
2. Sacar `'resumen'` del `Set` `loaded` (`band.js:236`) **no** basta (Resumen es la pestaña activa por
   defecto y `loadTab` solo dispara al hacer clic): llamar a `loadSummary(bandId, ctx)` directamente tras
   `renderShell` en `init` (`band.js:83-85`).
3. `loadSummary` hace `apiFetch('/bands/'+bandId+'/summary')` y pinta una rejilla **dos columnas**
   (`.bs-summary`, colapsa a 1 en móvil):
   - **Izquierda:** tarjeta "Próximo evento" (con **cuenta atrás** cliente desde `next_event.starts_at`,
     sala, tu estado 🟢/🟡/⚪ + botón "¿Vas?") reusando `attendeesLine`/`bookingLine` de `bands.js`; debajo
     "Último mensaje" reusando el render de `renderMessageList` (o una línea compacta).
   - **Derecha:** "Tu saldo" (`my_balance`, verde/rojo → enlace a la pestaña Finanzas) + **contadores**
     (`counts.songs/setlists/collections` con `bfIcon`) + accesos rápidos (botones a las pestañas).
4. Estilos `.bs-summary` (grid 2 col) en `design-system.css`; estados vacíos con `bfEmpty`.

**Test.** e2e `test_resumen_banda`: abrir `band.html?id=…` (pestaña Resumen activa) → existe `#b-summary`,
muestra "Próximo evento" y "Tu saldo"; el `data-tab="resumen"` sigue existiendo. Verificar que las otras
pestañas siguen cargando perezosamente (no se rompió `loadTab`).

**Verificación.** Resumen con vida (no el bloque "Sobre la banda" estático). Doctor + cachebust + e2e.

---

### T-131 — Inicio = panel de control (Opción A, hero protagonista)
**Objetivo.** Que el Inicio responda "¿y ahora qué?" de un vistazo. **Casi todo cliente.**

**Pasos.**
1. En `static/home.js`, añadir `apiFetch('/me/balances')` al `Promise.all` (`home.js:60-61`).
2. Render (rama "con bandas", `home.js:95-116`) en **Opción A**:
   - **HERO a todo el ancho** = `data.upcoming_events[0]`: título + tipo (`EV_ICON`), **cuenta atrás**
     (cliente desde `starts_at`), sala/etiqueta de banda, tu asistencia (`my_status`→🟢/🟡/⚪) y botón
     **"¿Vas?"** (POST a asistencia, el mismo endpoint que los `att-btn` de la agenda). Acento coral,
     tipografía grande. Si no hay eventos → hero "Sin bolos a la vista" con CTA.
   - **Debajo, rejilla `.bf-grid`:** (a) **Saldo total** = `Σ /me/balances` (verde/rojo → Finanzas);
     (b) **Accesos rápidos** (reusar el patrón `step(...)` del onboarding, `home.js:76-92`);
     (c) **Últimos mensajes** compactos (`recent_messages`, reusar `msgItem`).
3. *(Opcional servidor, sin migración):* rellenar `attendance[]` en `me_router.get_dashboard` copiando el
   bloque anti-N+1 de `me_router.py:163-177` → permite mostrar "quién va" en el hero. Marcar como mejora.

**Test.** e2e `test_inicio_panel`: con seed (≥1 evento futuro), `#home` muestra el hero con cuenta atrás
(un nodo con el tiempo restante) y una tarjeta de "Saldo"; el onboarding sin-bandas (`home.js:75-94`)
sigue intacto cuando no hay bandas (reutiliza el test existente de primeros pasos).

**Verificación.** Inicio "cuartel general": dato principal (próximo bolo) + acción ("¿Vas?") arriba.
Doctor + cachebust + e2e.

---

### T-132 — Tarjeta de banda rica ("Mis bandas") + `song_count`
**Objetivo.** Que `bands.html` deje de ser texto plano: avatar de color, próximo evento y nº de canciones.
**Única adición de servidor #2** (campo agregado, sin migración).

**Pasos.**
1. **Backend:** añadir `song_count: int = 0` a `BandSummary` (`schemas.py:305-315`) y rellenarlo en
   `list_my_bands` (`bands_router.py:84-95`) con un helper `_song_counts(db, band_ids)` (calcado de
   `_active_member_counts`, `bands_router.py:37-47`, agrupando por `band_id`).
2. **Front `bands.js loadBands` (`:16-42`):** cada tarjeta con **avatar** (`bandColor(b.id)` +
   `initialsFrom(b.name)`, de `util.js`/T-121), **próximo evento** (agrupar un `apiFetch('/me/dashboard')`
   por `band_id`, cliente) y **`b.song_count` canciones** junto a `member_count`.
3. **2.3b empty-state ilustrado:** sustituir el `empty-state` actual (`bands.js:23-25`) por `bfEmpty` con
   **dos CTA**: "Crear banda" (`createBand`) y "Tengo un código" (a la pantalla de unirse).

**Test.** unit `test_bandsummary_song_count`: seed con N canciones de banda → `GET /bands/` devuelve
`song_count == N`. e2e: la tarjeta de banda muestra el avatar (`.bf-avatar`/inicial) y el nº de canciones;
`test_bands_ui` (crear) sigue verde (usa ids/nombres).

**Verificación.** "Mis bandas" con identidad visual y datos útiles. Doctor + cachebust. (Aislamiento: ya
inherente — `list_my_bands` solo devuelve mis bandas.)

---

### Cierre de V4-F2
- Doctor + `run_checks` verdes · **`revision.py` SÍ aplica** (ruta nueva `/bands/{id}/summary` → debe
  salir ✅) · test de **aislamiento** de T-129 obligatorio · registro en `REGISTRO_DE_CAMBIOS.md`.
- Resultado: Inicio y Resumen dan valor al entrar; "Mis bandas" con identidad. **Base lista para F3.**

---

## FASE V4-F3 — Tarjetas, densidad y carga

> **Meta:** que las listas respiren, las tarjetas inviten a la acción y nada parezca "colgado" al cargar.
> **Solo front/CSS.** **Orden:** T-136 (ancho, lo usan las demás) → T-133 → T-135 → T-134 → T-137.

---

### T-133 — Tarjeta de canción con play + franja de fuente
**Objetivo.** Reproducir desde la tarjeta y distinguir de un vistazo personal vs. banda.

**Pasos.**
1. En `static/library.js renderGrid` (`:228-264`): añadir un botón **▶ flotante** `.card-play` (clon de
   `.card-action-btn`, revelado en hover, **abajo-derecha** para no chocar con `.card-actions` de
   arriba-derecha) que navega a `index.html?songId=${song.id}` (mismo destino que el clic de tarjeta).
2. **Franja de color por fuente:** variable `--card-accent` por tarjeta
   (`isPersonal ? var(--accent-color) : bandColor(song._bandId)`) + `.song-card::before` (barra de 4px a
   la izquierda) en `static/style.css` (bloque `.song-card`, `:946-1037`).
3. **Mantener** el `_badge` como **texto** en `#song-grid` (no convertir a icono): el test
   `test_library.py:80` lee esa cadena.

**Test.** e2e `test_card_play`: en la biblioteca, una `.song-card` contiene `.card-play`; clic →
navega al reproductor (`index.html?songId=`). `test_library` (badges, edit/delete) sigue verde.

**Verificación.** Biblioteca más "viva" y reproducible en un clic. Doctor + cachebust + e2e.

---

### T-134 — Agenda más limpia (acciones en "⋯")
**Objetivo.** Quitar ruido de la fila de evento sin perder funciones.

**Pasos.**
1. En `static/bands.js` (fila de agenda, ~`:510-521`): mover **solo** `🗑️ data-act="del"` a un menú
   **"⋯"** (popover). **Sin riesgo:** ningún e2e usa ese botón.
2. **Mantener visibles:** los 3 `att-btn` (asistencia), el `💬` de hilo y el `select.ev-status-sel`
   (moverlo obligaría a tocar `test_booking_pipeline…`). Mismos nodos/clases dentro del popover.

**Test.** e2e `test_agenda_menu`: la fila tiene un disparador "⋯"; al abrirlo aparece `data-act="del"`;
los `att-btn` siguen visibles fuera del menú. `test_booking_pipeline` sigue verde.

**Verificación.** Agenda legible; borrar queda a un clic de distancia. Doctor + cachebust.

---

### T-135 — Skeletons en todas las cargas
**Objetivo.** Sensación de respuesta inmediata en todo (hoy solo el Inicio tiene skeleton).

**Pasos.**
1. Helper global `bfSkeletonList(n=3)` en `util.js` (devuelve `n` filas `.bf-skeleton`), espejo del
   skeleton de `home.js:40-52`.
2. Aplicarlo antes de cada `apiFetch` de lista: secciones de `band.js`/`bands.js`
   (repertorio/agenda/finanzas/giras), agregadas (`agenda.js`/`finanzas.js`/`chat.js`) y `library.js`.

**Test.** e2e `test_skeletons`: interceptar/retrasar una respuesta y comprobar que aparece `.bf-skeleton`
antes de los datos en, p. ej., la biblioteca. (O aserción de que el helper inserta `.bf-skeleton`.)

**Verificación.** Cero "saltos" en blanco al cargar. Doctor + cachebust.

---

### T-136 — Aprovechar el ancho + utilidad `.bf-grid`
**Objetivo.** Romper la "columna estrecha con medio pantallazo negro" en los listados.

**Pasos.**
1. En `static/shell.css` (`.bf-page`, `:210`): mantener `max-width:920px` para lectura/formularios y
   añadir modificador **`.bf-page--wide`** (~1120–1200px) para listados.
2. Nueva utilidad **`.bf-grid`** en `design-system.css`: `display:grid;
   grid-template-columns:repeat(auto-fill,minmax(260px,1fr)); gap:var(--bf-space-4);` (espejo de
   `.song-grid`). Aplicar `bf-page--wide`+`.bf-grid` en Inicio (T-131), Bandas (T-132), Explorar.

**Test.** e2e `test_ancho_listados`: `getComputedStyle('.bf-page--wide').maxWidth` > 920px; el Inicio usa
`.bf-grid` (varias columnas en viewport ancho).

**Verificación.** Listados con densidad cómoda, sin regresión en formularios. Doctor + cachebust.

---

### T-137 — Microinteracciones (pop/flash) con propósito
**Objetivo.** Premiar las acciones (añadir, guardar, "Voy") con un micro-feedback.

**Pasos.**
1. En `static/design-system.css`: keyframes cortos `bf-pop` (escala 1→1.04→1) y `bf-flash` (destello de
   `--bf-accent-weak`), ambos con guard `@media (prefers-reduced-motion: reduce)` (imitar `chord-pulse`).
2. Disparar `bf-pop`/`bf-flash` al añadir a colección/setlist, al guardar y al marcar asistencia ("Voy").

**Test.** e2e `test_microinteraccion`: tras una acción (p. ej. marcar "Voy"), el nodo recibe la clase de
animación; con `prefers-reduced-motion` no se anima (computed `animation-name: none`).

**Verificación.** La app "responde" al tacto sin marear. Doctor + cachebust.

---

### Cierre de V4-F3
- `run_checks` verde por tarea · capturas antes/después de biblioteca/agenda · registro. **Base para F4.**

---

## FASE V4-F4 — La joya en directo

> **Meta:** que el reproductor y el escenario estén a la altura del resto. **CSS + algo de JS; el motor
> (`sync_engine.js`/`score_render.js`) NO se toca** (respetar el contrato DOM de §0.bis de la guía UX).
> **Orden:** T-138 → T-139 → T-140 → T-141 → T-142.

---

### T-138 — Top-bar del reproductor ordenada
**Objetivo.** Quitar los estilos inline y agrupar los controles en zonas claras.

**Pasos.**
1. En `static/index.html` (`:22-44`): mover los `style="…"` inline de los botones a una clase **`.tool-btn`**
   en `style.css`. Agrupar en **3 zonas** con separadores: *transporte/tempo* (BPM, tono, 💾) ·
   *herramientas* (afinador, vídeo, imprimir) · *navegación* (home, biblioteca, ➕).
2. **Móvil:** colapsar herramientas+navegación tras un botón `menu` (ya en `icons.js`); deja visible el
   transporte. (Depende de los iconos SVG de T-123.)

**Test.** e2e `test_topbar_player`: el reproductor carga; los botones de herramienta tienen `.tool-btn`
(no `style` inline) y siguen con su `aria-label`/`title`; en viewport móvil aparece el disparador `menu`.

**Verificación.** Top-bar limpia y agrupada; sin regresión de controles. Doctor + cachebust. **Riesgo:**
revisar que ningún e2e dependa del `style` inline.

---

### T-139 — Escenario más espectacular (solo CSS)
**Objetivo.** Que el "Modo Directo" se lea desde lejos y con poca luz. **Sin tocar el motor.**

**Pasos.**
1. Ampliar `.stage-mode` en `static/style.css` (`:441-451`): acordes más grandes y con más contraste;
   líneas inactivas a `opacity:.25`; realce de la línea activa (`:has(.chord-container.active)`); glow
   pulsante en `.song-progress__dot`.
2. **Modo alto contraste** (clase o `data-theme`) para escenarios con poca luz. Respetar
   `prefers-reduced-motion` en el glow.

**Test.** e2e `test_escenario`: activar `#btn-stage` → el contenedor toma `.stage-mode`; computed de una
línea inactiva `opacity≈.25` y la activa mayor. (No comprobar el motor, solo CSS.)

**Verificación.** Directo legible y vistoso; sincronización intacta (contrato DOM respetado). cachebust.

---

### T-140 — Drag & drop para reordenar el setlist
**Objetivo.** Reordenar canciones del setlist arrastrando (touch-friendly).

**Pasos.**
1. En el editor de setlist (`#sl-selected`, `setlists.js`/`bands.js`): pointer events para reordenar el
   array `selected` + `render()`. El `PATCH` de setlist **ya acepta el orden** (no hay backend nuevo).
2. Soporte táctil (pointer events, no HTML5 DnD) y fallback con botones ▲▼ accesibles.

**Test.** e2e `test_reordenar_setlist`: simular arrastre de la 2ª canción a la 1ª → el orden enviado en el
PATCH cambia; recargar mantiene el orden.

**Verificación.** Reordenar fluido en escritorio y móvil. Doctor + cachebust + e2e.

---

### T-141 — Hoja de atajos del reproductor
**Objetivo.** Descubribilidad de los atajos de teclado.

**Pasos.**
1. Botón "?" en la top-bar del reproductor → modal (`.modal-card`) con la lista de atajos (espacio =
   play/pausa, etc.). Cerrar con `Esc`/clic fuera.

**Test.** e2e `test_atajos`: clic en "?" abre el modal con la lista; `Esc` lo cierra.

**Verificación.** Atajos a la vista. Doctor + cachebust.

---

### T-142 — Vacíos con CTA en todas partes
**Objetivo.** Ningún estado vacío "muerto": siempre dice qué hacer.

**Pasos.**
1. Auditar los empty-states restantes y usar `bfEmpty(icon, título, texto, {cta})` con acción clara
   (crear, importar, invitar…). Cubrir biblioteca, setlists, colecciones, agenda, finanzas, chat.

**Test.** e2e `test_vacios_cta`: forzar una lista vacía (seed sin datos) → aparece el empty-state con un
botón/enlace de acción.

**Verificación.** Recorrido sin callejones sin salida. Doctor + cachebust.

---

### Cierre de V4-F4
- `run_checks` verde · revisar el reproductor/escenario a ojo (seed_demo + Playwright) · registro. → F5.

---

## FASE V4-F5 — Funcionalidad y remate

> **Meta:** cerrar funciones que faltan y pulir el acabado fino. Mezcla de [F] cliente y CSS. **Sin
> migración.** **Orden sugerido:** T-143 → T-144 → T-145 → T-146 → T-147 → T-148 → T-149 → T-150 → T-151
> → T-152 (independientes en su mayoría; agrupar por sesión).

---

### T-143 — "Añadir a colección/setlist" desde la tarjeta
**Objetivo.** Meter una canción en una colección/setlist sin entrar a editarla.

**Pasos.** Botón en `.card-actions` (o en el menú de la tarjeta) → modal con **checkboxes** de las
colecciones/setlists de la banda → `PATCH` de pertenencia (los endpoints ya existen). Toast + `bf-pop`.

**Test.** e2e `test_anadir_a`: desde una tarjeta, abrir el modal, marcar una colección, guardar → la
canción aparece en esa colección.

**Verificación.** Flujo de "organizar" mucho más rápido. Doctor + cachebust + e2e.

---

### T-144 — Buscadores (repertorio de banda y setlists)
**Objetivo.** Filtrar listas largas. **Filtro cliente** (sin backend).

**Pasos.** Caja de búsqueda (espejo de la de `library.js`, `:283-284`) sobre `#b-repertoire` y la lista de
setlists; filtra por título/artista en cliente.

**Test.** e2e `test_buscador_repertorio`: escribir en la caja reduce las filas mostradas a las que casan.

**Verificación.** Repertorios grandes manejables. Doctor + cachebust.

---

### T-145 — Duplicar canción/setlist/colección
**Objetivo.** Partir de una copia en vez de empezar de cero.

**Pasos.** Acción "Duplicar" (menú de tarjeta/lista) → POST que crea una copia (sufijo "(copia)"). Evaluar
si reusa endpoints existentes o necesita uno fino por recurso (sin migración).

**Test.** e2e `test_duplicar`: duplicar un setlist crea otro con el mismo contenido y nombre "(copia)".

**Verificación.** Ahorro de trabajo repetido. Doctor + (cachebust si toca front) + test.

---

### T-146 — Banda(s) en el lateral
**Objetivo.** Saltar a una banda desde el shell, sin pasar por "Mis bandas".

**Pasos.** En `static/shell.js`: sub-items bajo "Bandas" (avatar `bandColor`+iniciales → `band.html?id=`),
reusando `GET /bands/`. Colapsable; resalta la banda activa.

**Test.** e2e `test_banda_lateral`: el lateral lista mis bandas; clic abre `band.html?id=…`.

**Verificación.** Navegación entre bandas en un clic. Doctor + cachebust.

---

### T-147 — Login pulido
**Objetivo.** Primera impresión a la altura (legacy `style.css`).

**Pasos.** `login.html`/`login.js`: branding BandFlow, claim ("Gestiona tu banda: repertorio, bolos y
cuentas"), botón Google prominente, modo oscuro coherente (se beneficia de la unificación de tokens, T-120).

**Test.** e2e `test_login_branding`: la pantalla de login muestra el claim y el botón de Google; el modo
claro/oscuro no deja restos.

**Verificación.** Login que da confianza. Doctor + cachebust. *(Verificar OAuth en prod — el server local
no llega al navegador.)*

---

### T-148 — Tour la primera vez en una banda
**Objetivo.** Orientar al recién llegado a una banda.

**Pasos.** Tooltips secuenciales (banner → pestañas → acción principal) con `localStorage` para no
repetir. Botón "saltar".

**Test.** e2e `test_tour`: primera visita muestra el primer tooltip; "saltar" lo cierra y marca
`localStorage`; segunda visita no lo muestra.

**Verificación.** Onboarding de banda claro. Doctor + cachebust.

---

### T-149 — Escala tipográfica consistente
**Objetivo.** Quitar tamaños/pesos sueltos; usar tokens.

**Pasos.** Revisar `--bf-fs-*`/`--bf-fw-*` (`design-system.css:58-67`) y aplicarlos donde haya valores
literales (legacy incluido). Sin cambios de layout.

**Test.** (visual/lint) revisión a ojo + grep de tamaños literales en CSS reducido. No suele necesitar e2e.

**Verificación.** Jerarquía tipográfica uniforme. Doctor + cachebust.

---

### T-150 — Modo claro a la par (remate)
**Objetivo.** Cerrar los restos del tema claro en legacy (la base llegó gratis con T-120).

**Pasos.** Auditar páginas legacy con `data-theme="light"` (player, editor, biblioteca, setlists, perfil,
login) y corregir contrastes/restos naranjas.

**Test.** e2e `test_tema_claro_legacy`: togglear `data-theme="light"` en una página legacy → fondos/textos
con contraste correcto (sin restos oscuros).

**Verificación.** Tema claro usable en toda la app. Doctor + cachebust.

---

### T-151 — Accesibilidad (remate)
**Objetivo.** Contraste, foco, objetivos táctiles y `aria` al día.

**Pasos.** Contraste de grises secundarios, foco visible (apoya en T-127), objetivos táctiles ≥44px,
`aria-label` en todos los iconos. Apoyo en la skill `design:accessibility-review`.

**Test.** e2e/axe: una pasada de accesibilidad sin violaciones críticas en las páginas principales.

**Verificación.** App utilizable con teclado/lector. Doctor + cachebust.

---

### T-152 — Caché por temporada (agregación por fechas)
**Objetivo.** Resumen de caja agrupado por temporada/fechas (cierra 8.7).

**Pasos.** Agregación cliente sobre lo que ya devuelven finanzas/eventos; vista por temporada. Sin
migración. (Detalle a concretar al implementar.)

**Test.** unit/e2e `test_cache_temporada`: con seed de movimientos en dos temporadas, la agregación las
separa correctamente.

**Verificación.** Visión económica por gira/temporada. Doctor + (cachebust si toca front).

---

### Cierre de V4-F5
- `run_checks` verde · registro · revisión a ojo de login/lateral/tour. → Queda solo lo que necesita config.

---

## FASE V4-F6 — Lo que necesita tu config (🔌)

> **Meta:** lo que **depende de infraestructura/credenciales** (Supabase Storage, envío de
> notificaciones, realtime). **Requiere migración** (campos de URL) y decisiones de Oscar. Va al final
> a propósito: nada de F1–F5 lo necesita.

---

### T-153 — Avatares/logos de banda y perfil (Storage) 🔌
**Objetivo.** Subir imagen de banda y de perfil.

**Pasos.** Bucket en **Supabase Storage** + `logo_url`/`avatar_url` (ya hay `avatar_url` en banda y
perfil; confirmar) + **migración** si falta algún campo (`alembic revision --autogenerate`, revisar SQL,
`alembic check`). Subida desde Ajustes de banda y Perfil; fallback al avatar de color (T-121) si no hay
imagen. **Aplicar migración a Postgres** con el pooler de sesión (5432).

**Test.** unit `test_logo_url`: PATCH de banda con `logo_url` lo persiste; e2e: la imagen se muestra en el
banner si existe, si no el avatar de color. **+ test de aislamiento** si se añade ruta de subida.

**Verificación.** Doctor + `alembic check` "no new operations" + `revision.py` + verificación en prod.

---

### T-154 — Perfil con cuerpo
**Objetivo.** Que el perfil muestre identidad: avatar, mis bandas, instrumentos.

**Pasos.** En `profile.html`/`profile.js`: avatar (iniciales/color de T-121, o imagen de T-153), **mis
bandas** como chips con rol (de `GET /bands/`), instrumentos como **chips**. (Parte cliente; la subida de
avatar depende de T-153.)

**Test.** e2e `test_perfil_cuerpo`: el perfil muestra el avatar, los chips de bandas y de instrumentos.

**Verificación.** Perfil con personalidad. Doctor + cachebust.

---

### T-155 — Notificaciones / recordatorios 🔌
**Objetivo.** Avisar de eventos próximos / mensajes (email o push).

**Pasos.** Decidir canal (email vía proveedor / push PWA). Backend de envío + preferencias por usuario
(migración para opt-in). Reusar los recordatorios in-app existentes (T-112) como disparador.

**Test.** unit del disparador (a quién/cuándo notifica) con el envío *mockeado*; **+ aislamiento** en
cualquier ruta nueva.

**Verificación.** Avisos fiables sin spam. Doctor + `alembic check` + prod. **Requiere credenciales.**

---

### T-156 — EPK público / ensayo en tiempo real (punteros) 🔌
**Objetivo.** Dejar anotada la frontera con V3 (fuera del alcance de V4).

**Pasos.** **No implementar en V4.** La **página pública/EPK** es **V3-F8** y el **ensayo en tiempo real**
es **V3-F6** (ver `GUIA_MAESTRA_V3.md`). Este punto solo enlaza esas fases para no perder el hilo.

**Verificación.** N/A (puntero de roadmap).

---

### Cierre de V4-F6 (y de la V4)
- Cada 🔌 con su migración aplicada a Postgres + `revision.py` ✅ + verificación **en producción**.
- Con F1–F6 cerradas, la V4 (experiencia + diseño) queda completa: app coherente, con paneles que dan
  valor, tarjetas vivas, la joya espectacular, funciones rematadas y la capa que depende de tu config.
