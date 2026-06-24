# GUÍA MAESTRA V4 — Experiencia de uso y diseño (V3: validada y optimizada)

> **Propósito.** Hacer BandFlow **fácil, directo, intuitivo y muy agradable** para cualquiera, cuidando
> coherencia, experiencia, diseño visual y diseño de interacción.
>
> **De dónde viene.** V1 (el QUÉ, estudio visual de 14 páginas) → V2 (el CÓMO) → **V3 (esta): tras
> investigar A FONDO el código real** (4 auditorías en paralelo de design-system+shell, reproductor,
> espacio de banda, e Inicio/`/me`/tarjetas). La V3 **valida, corrige y optimiza** cada punto con
> ficheros y líneas concretas, reparto cliente/servidor y notas de seguridad de tests.
>
> **Convenciones.** Prioridad 🔴 alto · 🟠 medio · 🟢 nice-to-have · 🔌 necesita config/infra.
> Tipo [F] · [V] · [I]. Esfuerzo **S** (≤½ día) · **M** (1 día) · **L** (varios). Todo aditivo + bucle
> de siempre (doctor + test + `cachebust` + deploy + verificación).
>
> _V3 — 2026-06-24._

---

## 0. Principios de diseño (no negociables)

1. **Un solo lenguaje de iconos:** SVG de `icons.js` (`bfIcon`). Cero emoji en chrome.
2. **Densidad cómoda:** contenedor más ancho + rejillas; nada de columna estrecha con medio pantallazo negro.
3. **Todo lo clicable lo parece:** hover (elevación + borde acento), `:focus-visible`, `cursor`.
4. **Movimiento con propósito:** transiciones 150–200 ms, `prefers-reduced-motion` respetado.
5. **Una sola fuente de verdad del acento:** coral `--bf-primary`; legacy hereda de ahí.
6. **Cada pantalla responde "¿y ahora qué?":** dato principal + acción principal siempre a la vista.

---

## 0.bis Realidad técnica (hallazgos de la investigación — leer antes de aplicar)

- **Dos universos de CSS.** (a) **Nuevo `bf-*`**: `design-system.css` + `shell.css`, tokenizado, con
  hover/focus/transición y **tema claro** — lo usan app/band/agenda/finanzas/chat/bands/explorar.
  (b) **Legacy `style.css`**: player, editor, biblioteca, **setlists**, perfil, login; define su PROPIO
  coral (`--accent-color:#ff6b4a`, `style.css:11-14`) **duplicando** `--bf-primary` (`design-system.css:38`),
  con docenas de `#ff6b4a`/`rgba(255,107,74,…)` **hardcodeados** y fallbacks muertos verde-menta
  (`#6ee7b7` en `style.css:653,1094`). **Optimización clave:** hacer que `style.css` herede
  (`--accent-color: var(--bf-primary)`, etc.) **arregla el modo claro en TODAS las páginas legacy
  gratis** y deja un solo acento. → Esto cumple a la vez los puntos 1.2-color, 7.2 y 7.4.
- **Sistema de iconos.** `bfIcon(name)` (`icons.js:36`) devuelve SVG Lucide con `currentColor`; 18
  iconos hoy (`home, library, calendar, wallet, chat, users, user, sun, moon, logout, settings, music,
  search, inbox, globe, star, download, menu`). Añadir más = pegar paths en `PATHS` (`icons.js:15`),
  sin build. **`icons.js` NO está cargado en `index.html` (player) ni `editor.html`** → hay que añadir
  el `<script>`. Faltan ~18 nombres: `play, pause, stop, plus, minus, save, printer, mic, film, drum
  (o timer), maximize, minimize, folder, arrow-left, edit, trash, x, note`. `bfEmpty` ya existe.
- **Reproductor — corrección de la V2:** **no hay icono "🐈 gato" ni "🔧 llave".** Los emoji reales
  son: arriba `💾`(guardar tono) `🎤`(afinador) `🎬`(vídeo ref.) `🖨️`(imprimir) `🏠 📚 ➕`; abajo
  `🥁`(**metrónomo** — el que parecía un gato) `⏹ ▶/⏸ ⛶`. Todos son emoji inline en `index.html`;
  `btn-play-pause` reescribe su `innerHTML` en `app.js:75/78`. Refresco visual = **0 cambios** en
  `sync_engine.js`/`score_render.js` (contrato DOM a respetar: clases `.chord-container/.chord-pill/
  .active/.line-lyric(.inactive)/.section-name` e ids `#chord-*`, `#score-*`, `#song-progress-*`, `#btn-*`).
- **Color por banda.** Ya existe `hueFromId` pero **encerrado** en el IIFE de `band.js:18` (no reusable),
  y `initialsFrom` está **duplicado** (`band.js:23` y `shell.js:89`). → Promoverlos a `util.js`
  (`bandColor(id)`, `bandHue(id)`, `initialsFrom(name)`), que se carga en todas partes. Base de 2.3, 3.1, 3.4.
- **Agregación.** `me_router.py` ya es el patrón de dashboard agregado (`/me/dashboard|events|balances|
  conversations`). Casi todo lo nuevo se resuelve **en cliente** con lo que ya devuelven. Adiciones de
  **servidor** reales y pequeñas (sin migración): (1) `GET /bands/{id}/summary` para el Resumen de banda;
  (2) `song_count` en `BandSummary` (`schemas.py:305`) + query agregada en `list_my_bands`
  (`bands_router.py:84`, patrón `_active_member_counts`); (3) opcional: rellenar `attendance[]` en
  `get_dashboard` (copiar el bloque anti-N+1 de `me_router.py:163-177`) para "quién va" en el hero.
- **Seguridad de tests (regla de oro de esta fase):** los e2e buscan por **selectores e ids estables**,
  no por texto/emoji visible. Conservar: clases `.song-card/.card-action-btn/.setlist-song/.ev-*`,
  ids `#b-*/#sl-*/#col-*/#ev-*/#btn-*`, atributos `data-tab/data-att/data-act`. Antes de cambiar
  `btn-play-pause` (texto "▶ Play"/"⏸"), revisar `tests/e2e`. Tras tocar js/css: `python harness/cachebust.py`.

---

## 1. Coherencia estructural y navegación

- **1.1** 🟠 [V] **Setlists dentro del shell.** **Cómo (M):** migrar `setlists.html` a `bf-shell`
  (espejo de `library.html`): cargar `design-system.css`+`shell.css`+`icons.js`+`shell.js`, envolver en
  `.bf-shell > main.bf-shell-main > .bf-page`, cabecera al patrón `bf-row--between`. `setlists.js` no
  cambia su lógica (mismos ids `#setlist-grid`/`#setlist-detail`/`#sl-*`); quitar la top-bar antigua y
  sus 🏠/📚. El test `test_setlists_accesible_desde_la_biblioteca` (busca `h1` con "Setlists") sigue ok.
- **1.2** 🟠 [V] **Terminología.** **Cómo (S):** decisión validada — la pestaña `data-tab="repertorio"`
  muestra colecciones **+ el pool**, así que: **label de pestaña → "Repertorio"** (= todas las canciones)
  y **sección interna → "Colecciones"**. Cambios SOLO de texto en `band.js:31,133,134,136` y
  `bands.js:951,953,960,967,973,1011,1020,1065,1073,1075`. **No tocar** `key:'repertorio'`/`data-tab`
  ni ids `b-collections`/`b-new-collection`. Ningún e2e asierta la cadena "Repertorio" → seguro.
- **1.3** 🟠 [V] **Iconos SVG en todo.** **Cómo (M):** (1) ampliar `PATHS` en `icons.js` con los ~18
  nombres que faltan (Lucide); (2) **cargar `icons.js`** en `index.html` y `editor.html` (hoy no está);
  (3) reemplazar emoji por `bfIcon('name')` en `index.html`/`app.js` (incl. `btn-play-pause`),
  `setlists.js`, `profile.js`, `library.js`, `catalogo.js`, y los botones de acción de `bands.js`.
  Tooltips (`title`+`aria-label`) en todos. `♭/♯/+/−` pueden quedarse como glifo (se leen mejor).
- **1.4** 🟠 [I] **Pestañas de banda en móvil.** **Cómo (S):** `.bf-tabs` ya tiene `overflow-x:auto`
  con scrollbar oculta (`design-system.css:248`); solo falta affordance → añadir `mask-image` (+
  `-webkit-`) con fade en ambos bordes y `scroll-snap-type:x proximity`. `scrollIntoView` de la pestaña
  activa en `band.js`. **Solo CSS** (+1 línea JS).
- **1.5** 🟢 [F] **Banda(s) en el lateral.** **Cómo (M):** sub-items bajo "Bandas" en `shell.js`
  (avatar `bandColor`+iniciales → `band.html?id=`). Reusa `GET /bands/`.

---

## 2. Paneles que dan valor de un vistazo

- **2.1** 🔴 [V/F] **Inicio = panel de control.** **Cómo (M, casi todo cliente):** en `home.js` añadir
  `apiFetch('/me/balances')` al `Promise.all` (`home.js:60`). Render en rejilla: (a) **hero del próximo
  evento** = `dashboard.upcoming_events[0]` con **cuenta atrás** (cliente desde `starts_at`), sala, y tu
  asistencia (`my_status`→🟢/🟡/⚪) + botón "¿Vas?"; (b) **saldo total** = `Σ /me/balances` (verde/rojo →
  Finanzas); (c) **accesos rápidos** (reusar patrón del onboarding `home.js:76-92`); (d) últimos mensajes
  compactos. *(Opcional servidor: rellenar `attendance[]` en `get_dashboard` para "quién va" en el hero.)*
- **2.2** 🔴 [V/F] **Resumen de banda útil.** **Cómo (M):** hoy es **estático** (`band.js:112-123`,
  excluido de carga en `band.js:236`). Añadir **`GET /bands/{id}/summary`** (patrón `me_router`, 1 ida y
  vuelta, sin N+1): `{ next_event(+attendance,my_status), last_message, my_balance/deudores,
  counts:{songs,setlists,collections} }` con `Depends(require_band_member)` + **test de aislamiento**
  (regla de oro). En `band.js`: sacar `'resumen'` del `loaded` Set y pintar el dashboard reusando
  `attendeesLine`/`bookingLine`/`renderMessageList`. *(Reusa schemas `EventSummary/MessageOut/BalanceOut/
  CollectionSummary`.)*
- **2.3** 🟠 [V/F] **Tarjeta de banda rica ("Mis bandas").** **Cómo (S/M):** en `bands.js loadBands`,
  avatar `bandColor(b.id)`+`initialsFrom` (cliente), **próximo evento** agrupando `/me/dashboard` por
  `band_id` (cliente), y **nº de canciones** = única adición servidor: `song_count` en `BandSummary`
  (`schemas.py:305`) + query agregada en `list_my_bands` (patrón `_active_member_counts`, `bands_router.py:37`).
  **2.3b** empty-state ilustrado con CTA (crear / código).
- **2.4** 🟢 [V/F] **Perfil con cuerpo.** **Cómo (S):** avatar (iniciales/color), **mis bandas** (chips
  con rol, de `/bands/`), instrumentos como **chips**. Avatar subido → 🔌 Storage (V4-F6).

---

## 3. Tarjetas, listas y densidad

- **3.1** 🟠 [V/I] **Tarjeta de canción con play.** **Cómo (M):** en `library.js renderGrid`
  (`library.js:235-264`) + `style.css:946-1037`: botón **▶ flotante** `.card-play` (clon de
  `.card-action-btn`, hover-reveal, abajo-dcha para no chocar con `.card-actions` top-dcha); franja de
  color por fuente vía `--card-accent` (`isPersonal ? var(--accent-color) : bandColor(_bandId)`) +
  `.song-card::before` (4px izq.). Datos ya presentes (`_scope/_bandId`). **Mantener** el `_badge` como
  texto en `#song-grid` (test `test_library.py:80`).
- **3.2** 🟠 [I] **Agenda más limpia.** **Cómo (S/M):** fila en `bands.js:510-521`. **Sin riesgo:** mover
  SOLO `🗑️ data-act="del"` a un menú **"⋯"** (ningún e2e lo usa). Mantener visibles asistencia (3
  `att-btn`) + `💬 thread`. El `select.ev-status-sel` mejor dejarlo visible (moverlo obliga a tocar
  `test_booking_pipeline…`). Mismos nodos/clases dentro del popover.
- **3.3** 🟢 [V] **Quitar ≠ borrar.** **Cómo (S):** "quitar de lista" con icono neutro (gris); rojo solo
  para borrado real. Ajuste de clases en `bands.js`/`setlists.js`/`library.js`.
- **3.4** 🟠 [V] **Color de banda consistente.** **Cómo (S):** promover `hueFromId`→`util.js` como
  `bandColor`/`bandHue` + consolidar `initialsFrom` (hoy duplicado en `band.js:23` y `shell.js:89`).
  Usar en avatar del banner, tarjeta de "Mis bandas" y etiquetas de banda (Inicio/Agenda/Chat).

---

## 4. Interacción y "vida"

- **4.1** 🔴 [I] **Hover/active/focus unificados.** **Cómo (S):** el nuevo sistema casi lo tiene; **falta**:
  hover en `.bf-list-item` (usar token `--bf-hover`, ya existe), y **`:focus-visible`** en lo legacy
  (`.song-card` —tiene hover pero no focus—, `.setlist-song` —no tiene nada—, `.icon-btn/.card-action-btn/
  .primary-btn/.secondary-btn`). Un único bloque de foco accesible reutilizado. Igualar el "lift"
  (cards suben 2px vs 3px).
- **4.2** 🟠 [I] **Transiciones suaves.** **Cómo (S):** subrayado deslizante en `.bf-tab`, fade+scale en
  `.modal-overlay/.modal-card`, aparición de listas. Token `--bf-transition`. Guard `prefers-reduced-motion`.
- **4.3** 🟠 [I] **Microinteracciones.** **Cómo (M):** keyframes `bf-pop`/`bf-flash` en `design-system.css`;
  animar al añadir/guardar y al marcar "Voy". (`chord-pulse` ya respeta reduced-motion: imitar guard.)
- **4.4** 🟠 [I] **Skeletons en todo.** **Cómo (S):** helper `bfSkeletonList(n)`; aplicar `.bf-skeleton`
  en band (giras/agenda/finanzas/repertorio), agenda/finanzas/chat agregadas y biblioteca (hoy solo Inicio).
- **4.5** 🟢 [I/F] **Drag & drop reordenar setlist.** **Cómo (M):** en `#sl-selected` (editor de setlist),
  pointer events → reordenar `selected` + `render()`. El PATCH ya acepta el orden. Touch-friendly.
- **4.6** 🟢 [I] **Hoja de atajos.** **Cómo (S):** botón "?" en el reproductor → modal con atajos.

---

## 5. La joya — reproductor en directo

- **5.1** 🔴 [V] **Iconos del reproductor a SVG.** **Cómo (M):** cargar `icons.js` en `index.html`;
  añadir paths Lucide; sustituir los 11 emoji (top: 💾🎤🎬🖨️🏠📚➕ · bottom: 🥁⏹▶/⏸⛶) por `bfIcon`
  con tooltips. Cuidado con `app.js:75/78` (innerHTML de play/pause) y revisar e2e por el texto "Play".
- **5.2** 🟠 [V] **Top-bar ordenada.** **Cómo (M):** mover los `style="…"` inline (`index.html:38-43`) a
  una clase `.tool-btn`; agrupar en 3 zonas (transporte/tempo · herramientas · navegación) con
  separadores; en móvil colapsar herramientas/navegación tras un `menu` (ya en icons.js).
- **5.3** 🟠 [V/I] **Escenario más espectacular (solo CSS).** **Cómo (M):** ampliar `.stage-mode`
  (`style.css:441-451`): acordes más grandes/contraste, inactivas a `opacity:.25`, realce de la línea
  activa (`:has(.chord-container.active)`), glow pulsante en `.song-progress__dot`, y **modo alto
  contraste** (clase/`data-theme`) para poca luz. Sin tocar el motor. Respetar `prefers-reduced-motion`.
- **5.4** 🟢 [F] **Loop A-B / metrónomo lookahead / autoscroll fino.** Tocan el motor → **V3-F6**, no V4.

---

## 6. Onboarding y primera impresión

- **6.1** ✅ [F] **Inicio sin bandas → "Primeros pasos"** (hecho). Encaja con el rediseño 2.1.
- **6.2** 🟠 [V] **Login pulido.** **Cómo (S/M):** `login.html`/`login.js` (legacy `style.css`): branding,
  claim ("Gestiona tu banda: repertorio, bolos y cuentas"), botón Google prominente, modo oscuro coherente
  (se beneficia de la unificación de tokens 0.bis).
- **6.3** 🟢 [F] **Tour la 1ª vez en una banda.** **Cómo (M):** tooltips secuenciales + `localStorage`.
- **6.4** 🟢 [V] **Vacíos con CTA.** **Cómo (S):** auditar empty-states; usar `bfEmpty(...,{cta})` siempre.

---

## 7. Sistema de diseño y acabado fino

- **7.1** 🟠 [V] **Aprovechar el ancho.** **Cómo (M):** `.bf-page` hoy `max-width:920px` (`shell.css:210`)
  → **decisión validada:** mantener 920 para lectura/formularios y añadir modificador **`.bf-page--wide`
  (~1120-1200px)** para listados; nueva utilidad `.bf-grid` (`repeat(auto-fill,minmax(260px,1fr))`,
  espejo de `.song-grid`) para Inicio/Bandas/Explorar.
- **7.2** 🟢 [V] **Un solo acento (ver 0.bis).** **Cómo (S):** `style.css:11-14` → `var(--bf-*)`; sustituir
  literales `#ff6b4a`/`rgba(255,107,74,…)` por tokens; borrar fallbacks `#6ee7b7`. **Desbloquea modo
  claro en legacy** (7.4) de regalo.
- **7.3** 🟢 [V] **Escala tipográfica.** **Cómo (S):** revisar tokens de tamaño/peso y aplicarlos donde
  haya valores sueltos.
- **7.4** 🟢 [V] **Modo claro a la par.** **Cómo (S):** sale casi gratis con 7.2; auditar páginas legacy en
  `data-theme="light"` y corregir restos.
- **7.5** 🟢 [♿] **Accesibilidad.** **Cómo (M):** contraste de grises secundarios, foco visible (4.1),
  objetivos táctiles ≥44px, `aria-label` en iconos. Apoyo en skill `design:accessibility-review`.

---

## 8. Funcionalidad detectada

- **8.1** 🟢 [F] **"Añadir a colección/setlist" desde la tarjeta** de canción (modal con checkboxes → PATCH).
- **8.2** 🟢 [F] **Buscador** en repertorio de banda y en setlists (filtro cliente).
- **8.3** 🟢 [F] **Reordenar** dentro de colección/setlist (ver 4.5).
- **8.4** 🔌 [F] **Avatar/logo de banda y perfil** (Storage + `logo_url`/`avatar_url` + migración). V4-F6.
- **8.5** 🔌 [F] **Notificaciones/recordatorios** (email/push). V4-F6.
- **8.6** 🔌 [F] **Página pública/EPK (V3-F8)** y **ensayo en tiempo real (V3-F6).** Fuera de V4.
- **8.7** 🟢 [F] **Caché por temporada** (agregación por fechas).
- **8.8** 🟢 [F] **Duplicar** canción/setlist/colección.

---

## 9. Plan por fases (validado)

> **Reparto:** ~90% **cliente/CSS**. Servidor nuevo (sin migración): `GET /bands/{id}/summary` (2.2),
> `song_count` en `BandSummary` (2.3), opcional `attendance[]` en `/me/dashboard` (2.1). Cada fase = T-NNN
> en `TASKS.md` con doctor + test + cachebust + deploy + verificación.

- **V4-F1 — Cimientos coherentes (S/M, solo front/CSS; arregla mucho de golpe):**
  7.2/0.bis **unificar token de acento** (→ modo claro legacy gratis) · 1.3 **iconos SVG** (incl. cargar
  `icons.js` en player/editor + reproductor 5.1) · 1.1 **setlists al shell** · 1.2 **terminología** ·
  3.4 **`bandColor`/`initialsFrom` a `util.js`** · 4.1 **hover/focus** · 4.2 transiciones · 1.4 fade en
  pestañas · 3.3 quitar≠borrar. → *La app se siente "de una pieza" y con vida.*
- **V4-F2 — Paneles de control (M; el mayor salto de percepción):**
  2.2 **`/bands/{id}/summary` + Resumen útil** · 2.1 **Inicio panel de control** · 2.3 **tarjeta de banda
  rica** (+`song_count`) + 2.3b empty-state. → *Cada pantalla da valor al entrar.*
- **V4-F3 — Tarjetas, densidad y carga (S/M, front):**
  3.1 **tarjeta de canción con play** · 3.2 agenda más limpia (⋯) · 4.4 skeletons en todo · 7.1 ancho +
  `.bf-grid` · 4.3 microinteracciones.
- **V4-F4 — La joya en directo (M, CSS + algo de JS):**
  5.2 top-bar ordenada · 5.3 escenario espectacular · 4.5 drag&drop setlist · 4.6 atajos · 6.4 vacíos con CTA.
- **V4-F5 — Funcionalidad y remate (S/M):**
  8.1 añadir-a desde tarjeta · 8.2 buscadores · 8.8 duplicar · 1.5 banda en lateral · 6.2 login · 6.3 tour ·
  7.3 tipografía · 7.4 modo claro (remate) · 7.5 accesibilidad · 8.7 caché por temporada.
- **V4-F6 — Lo que necesita tu config (🔌):** 8.4 avatares/logos (Storage) · 2.4 avatar perfil · 8.5
  notificaciones · 8.6 EPK/realtime (V3).

> **Confianza:** todo lo de F1–F5 está **verificado contra el código** (ficheros, líneas, contratos DOM,
> selectores de test). Riesgo de regresión bajo si se respetan las notas de §0.bis. **Recomendación:
> empezar por V4-F1** (rápida, sin backend, y arregla la sensación general) seguida de V4-F2.

---

## 10. Proceso

1. **(Esta V3.)** Oscar la repasa y da OK / ajusta prioridades.
2. **Aplicar fase a fase** con el bucle de siempre. Cada tarea: test que la cubre + deploy + verificación en vivo.
3. Si algún punto 🔴 necesita decisión de diseño fino (p. ej. el layout del Resumen o del hero del Inicio),
   lo bocetamos antes de implementar.
