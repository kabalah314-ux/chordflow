# 🎸 BandFlow — Guía Maestra V5 · Pulido integral: la app profesional del músico

> ## 📌 ESTA ES LA GUÍA VIGENTE (única, para los dos ejes: producto + diseño)
> Creada el **2026-07-03** a partir del volcado de dirección de Oscar (WhatsApp 03/07 07:51, tres
> mensajes — transcrito ÍNTEGRO en esta guía, nada se pierde) + el **repaso integral de diseño del
> 2026-07-02** (3 auditorías de código en paralelo + navegación real de la app con datos demo en
> escritorio/móvil/claro/oscuro). Las guías anteriores (`GUIA_MAESTRA_V3.md`, `GUIA_MAESTRA_V4_UX.md`,
> `GUIA_MAESTRA_V4_IMPLEMENTACION.md`) quedan como **historial**; lo que tenían pendiente está
> **absorbido y re-ubicado** aquí (ver §0.2, tabla de herencia — nada se ha tirado).
>
> **Método de trabajo acordado con Oscar:** vamos **sección a sección**. Antes de implementar una
> sección se habla con Oscar lo que haga falta (esta guía marca las **DECISIONES ABIERTAS** de cada
> una), se cierran las decisiones (quedan registradas en la propia sección), se abren las tareas
> T-NNN en `harness/ROADMAP.md`/`TASKS.md`, y se ejecuta con el bucle de oro de `CLAUDE.md` §2.

---

## 0. Contexto para la IA ejecutora (leer SIEMPRE antes de tocar nada)

### 0.1 Reglas de oro (no negociables)

1. **Bucle de 7 pasos** de `CLAUDE.md` §2 en cada tarea: elegir tarea → abrirla en TASKS → implementar
   → `python harness/doctor.py` verde → test que la cubre + `python harness/run_checks.py` verde →
   registrar en `REGISTRO_DE_CAMBIOS.md` → cerrar en ROADMAP/TASKS. Tras tocar cualquier `.js`/`.css`:
   `python harness/cachebust.py`. Cada tarea = un commit desplegable e independiente.
2. **El motor NO se toca** sin una decisión explícita: `static/sync_engine.js` y el contrato DOM de
   `static/score_render.js` (clases `.chord-container/.chord-pill/.active/.line-lyric/.section-name`,
   ids `#chord-*`, `#score-*`, `#btn-*`). Todo lo del reproductor (§3) se hace ALREDEDOR del motor
   (datos, UI, controles), nunca dentro, salvo que la tarea diga lo contrario y tenga su plan.
3. **Multi-tenant:** toda ruta nueva de banda valida pertenencia+rol y filtra por `band_id`, y lleva
   su **test de aislamiento** (ajeno → 403/404). Toda ruta nueva de perfil filtra por `owner_id`.
   Todo dato que pase al plano público (Explorar) usa **proyección segura** (patrón `public_router.py`).
4. **XSS:** todo texto de usuario se escapa con `escapeHtml` antes del DOM (y en lo público, doble
   atención: bios, anuncios de material, notas).
5. Los e2e localizan por **ids/clases estables**, no por texto visible. Antes de renombrar un id o
   cambiar el texto de un botón, grep en `tests/e2e/`.
6. Migraciones: tras tocar `src/services/models.py` → `alembic revision --autogenerate` + revisar SQL
   + `alembic check` limpio. En prod se aplican por el pooler de sesión (5432) ANTES del push a main.

### 0.2 Herencia: qué absorbe esta guía de V3/V4 (nada se pierde)

| Pendiente heredado | De dónde | Dónde vive ahora |
|---|---|---|
| Ensayo sincronizado realtime (`/clock`, Supabase Realtime) | V3-F6 | Futuro post-V5 (no re-priorizado; se retoma al acabar §3/§4) |
| `visibility` en perfil + onboarding viral + oEmbed título/autor | V3-F7 resto | §5 (Explorar/perfiles) y §2 (pulido) |
| EPK + página pública banda + RSVP + fans | V3-F8 | §5.6 (Descubrir) + §10 (Conciertos); RSVP/fans siguen ahí |
| Red acotada: directorio + `CollabPost` | V3-F10 | §5 entero (Explorar es su superset) |
| Monetización Stripe/Pro | V3-F11 | Post-V5 (sin cambios, `Band.plan` ya andamiado) |
| Storage Supabase (avatares/logos/archivos) 🔌 | V3-F3 T-099 / V4-F6 T-153 | **Prerequisito transversal** de §2.3, §5.4, §9.2 — sigue BLOQUEADO en config de Oscar |
| Notificaciones/push 🔌 | V4-F6 T-155 | Post-V5 salvo que una sección lo exija antes |
| Loop A-B, tempo trainer, metrónomo lookahead | V3-F4 diferidos | §3 y §4 (el metrónomo nuevo los cubre en parte) |
| Mapa Leaflet en giras · ligar gasto real a gira | V3-F5 diferidos | §10 |

### 0.3 Mapa de archivos que esta guía toca más

Backend: `src/api/*` (routers), `src/services/models.py` (+migraciones), `schemas.py`, `band_auth.py`.
Frontend: `static/design-system.css` + `shell.css` (sistema), `style.css` (legacy a extinguir §2),
`shell.js` (lateral), `icons.js` (`bfIcon`), `util.js` (helpers), por página: `home.js`, `band.js`+
`bands.js`, `agenda.js`, `finanzas.js`, `chat.js`, `library.js`, `catalogo.js`, `profile.js`,
`editor.js`, `app.js` (player), `tuner.js`, `setlists.js`, `evento.js`, `join.js`.

---

## 1. Visión V5 en una frase

De "SaaS de gestión que se ve amateur" a **"la app profesional del músico: bonita de verdad, un
reproductor de directo serio, y una red práctica (músicos, material, colaboraciones, música de
bandas reales) donde cada sección se alimenta de las demás con coherencia"**.

Orden macro (detalle en §12): **1º estética global** (Oscar: "primero cómo mejorar la estética"),
después reproductor y afinador/metrónomo (la joya), después perfil→Explorar (la red), después
Chat/Bandas/Agenda, y **Finanzas AL FINAL** (Oscar: "no lo pulimos hasta que esté todo lo demás
hecho, ya que tenemos que dar todo contexto").

---

## 2. Estética global — de "cutre" a profesional 🔴 [V5-F1, EMPEZAR AQUÍ]

### 2.1 Diagnóstico (investigación real del código, 2026-07-02)

Cómo está hecha hoy: **dos universos de CSS conviviendo**. (a) El sistema nuevo `bf-*`
(`design-system.css` + `shell.css`): tokenizado, tema claro/oscuro, hover/focus — lo usan las
páginas del shell. (b) El legacy `style.css` (glassmorphism del producto original): player, editor,
login, join, y **componentes sueltos reutilizados dentro de páginas nuevas**. La sensación "cutre"
viene sobre todo de esa mezcla: dos estilos de botón, dos de tarjeta, emojis como iconos en mitad
de una UI con SVG, y páginas que no respetan el tema. Hallazgos concretos y verificados:

**Bugs visibles (arreglar lo primero):**
- 🔴 `initialsFrom('Oscar (tú)')` devuelve **"O("** — el avatar del lateral muestra "O(" en TODAS
  las páginas. Falta filtrar caracteres no alfabéticos en `util.js` (función `initialsFrom`).
- 🔴 **Buscador de Biblioteca ilegible en modo claro**: `.search-box` (`style.css:976`) tiene
  `background: rgba(0,0,0,0.5)` hardcodeado + texto que en claro resuelve oscuro → barra negra con
  texto invisible. Tokenizar fondo/borde.
- 🔴 Copy con referencia interna de desarrollo visible al usuario: "(T-091)" en `afinador.html`.

**Emoji usados como icono de UI (sustituir por `bfIcon`, ~25 sitios):** `editor.html` (💾 guardar
:86, ❌ cerrar :24, 🔎 :53, ✨ :63, 👁 :78) y `editor.js:375` (💾 dinámico) y `editor.js` (▶ en
`.ref-thumb__play`); `bands.js` (🔗 Invitar :113, ➕ en :135,144,153,163,169,178,197, 🗑️ Borrar
banda :218, ➕/➖ movimientos :283, 💾 :946, 🎵 Crear setlist :1130); `home.js` accesos rápidos y
primeros pasos (🎸👥🌍📅💶 :106-108,150-152); `library.js:221` (➕), `library.html:27-28`,
`setlists.html:27` (➕) y su h1 (🎵), `bands.html:26` (➕ Nueva banda), `join.html:20` (🎸),
h1 de `catalogo.js:173` (🌍) y `afinador.html:21` (🎤). **Nota:** el player (`index.html`) tiene
emojis en el HTML pero `app.js paintPlayerIcons()` los sustituye por SVG en runtime — eso está BIEN
(fallback progresivo), no tocarlo. Los emoji como CONTENIDO (tipos de evento en agenda, toasts,
mensajes de chat, `evento.html` público) son aceptables y se quedan.
- Todos los nombres usados en `bfIcon(...)` existen en `icons.js` (verificado, sin iconos rotos).

**Dos sistemas de componentes (unificar):**
- Botones: `.primary-btn/.secondary-btn` (legacy) vs `.bf-btn--primary/--ghost`. Editor, login y el
  afinador nuevo usan SOLO legacy pese a cargar `design-system.css`.
- Tarjetas: `.song-card` (radius 12px, padding 1.2rem, hover -3px) vs `.bf-card` (16px, 1.5rem,
  -2px). Se nota al pasar de Biblioteca al resto.
- Grids: `.song-grid` vs `.bf-grid` (duplicados conceptuales).

**Tema claro incompleto:**
- `index.html` (player), `editor.html` y `join.html` **nunca aplican** `bf-theme` (no cargan
  `shell.js` ni leen localStorage) → siempre oscuros. Para el player puede ser DECISIÓN ("modo
  escenario siempre oscuro") — si se decide así, documentarlo y forzarlo con estilo propio; el
  editor y join deben respetar el tema.
- `--bg-panel` (`style.css:10`) hardcodeado oscuro; `style.css:990` un rgba coral sin token;
  `.ev-status--confirmed/--cancelled` (`style.css:259-260`) con verdes/rojos propios (#5db075,
  #e0606a) en vez de `--bf-success`/`--bf-danger`.

**Detalles de pulido detectados navegando:**
- Avatar de conversación en Chat gris plano ("L") — no usa `bandColor()` como el lateral.
- Afinador: panel estrecho pegado a la izquierda en escritorio, mensaje redundante ("Pulsa para
  activar el micrófono." + botón "Activar micrófono"), aguja suelta sin estado idle.
- Editor móvil: input de búsqueda más estrecho que su botón; el ❌ de cerrar con subrayado de enlace.
- `.import-search-item` sin outline de foco visible.
- Banner-hint de `band.html` lista pestañas desactualizadas (no menciona Giras).
- `evento.html` (pública) sin CTA claro de vuelta/registro.
- Páginas dinámicas sin `<h1>` en el DOM estático (accesibilidad, menor).
- Lo que YA está bien (no tocar): agenda/finanzas/chat/espacio de banda limpios y coherentes,
  iconos SVG del player, empty states con `bfEmpty`, acento tokenizado en las páginas del shell.

### 2.2 Dirección visual para "muy profesional" (conclusiones)

1. **Un solo sistema.** Extinguir la mezcla: converger `.song-card`→tokens de `.bf-card`,
   `.primary-btn/.secondary-btn`→`.bf-btn`, `.song-grid`→`.bf-grid`, y que `style.css` quede solo
   para lo específico del player/editor. La consistencia ES la profesionalidad.
2. **Disciplina tipográfica.** IBM Plex ya es buena elección; aplicar escala única (tokens
   `--bf-fs-*`), pesos coherentes, cifras tabulares en números (ya en T-149), labels uppercase con
   letter-spacing solo donde toca.
3. **Espaciado y aire.** Rejilla de 4px (tokens ya existen) aplicada sin excepciones; padding de
   tarjeta único; más blanco entre bloques; contenedores `--wide` en todos los listados.
4. **Color con disciplina.** Base oscura + coral + semánticos y nada más; colores de banda SIEMPRE
   vía `bandColor()`; matar los hardcodeados que quedan (lista §2.1).
5. **Profundidad y estados.** Sistema único de elevación (sombras token), hover/focus/active en TODO
   lo clicable, skeletons en toda carga, transiciones 150-200ms con `prefers-reduced-motion`.
6. **Iconografía 100% SVG** (barrido §2.1) con `title`+`aria-label`.
7. **Identidad visual real:** fotos de perfil, logo/fondo de banda (→ necesita Storage 🔌), página
   de login con más marca. Sin fotos, la app siempre parecerá una demo — **este es el mayor salto
   de percepción disponible** y está bloqueado solo por config de Supabase de Oscar.
8. **Un tema por contexto:** app = claro/oscuro a elección; player = decisión de Oscar (§2.4).

### 2.3 Plan de tareas V5-F1 (orden de ejecución)

> Cada línea se abre como T-NNN en ROADMAP al arrancar la fase. S/M = esfuerzo.

1. **T-V5-01 (S) Bugs visibles:** `initialsFrom` filtra no-letras (+unit test con "Oscar (tú)")·
   `.search-box` tokenizada (+e2e modo claro) · quitar "(T-091)" del copy de afinador.
2. **T-V5-02 (M) Barrido emoji→bfIcon** con la lista de §2.1 (por archivo, un commit). Respetar
   los aceptables-como-contenido. e2e: ningún emoji en `<button>`/nav del shell.
3. **T-V5-03 (M) Unificar componentes:** `.song-card` y `.setlist-song` heredan tokens de tarjeta;
   `.primary-btn/.secondary-btn` → alias visual de `.bf-btn` (mismos tokens) sin romper ids/clases
   de tests; `.song-grid` = `.bf-grid`.
4. **T-V5-04 (S) Tema coherente:** editor y join aplican `bf-theme`; decisión player (§2.4)
   aplicada; `--bg-panel`, `style.css:990` y `.ev-status-*` tokenizados.
5. **T-V5-05 (S) Detalles:** avatar chat con `bandColor` · afinador centrado+copy limpio · focus
   `.import-search-item` · hint de pestañas actualizado · editor móvil (input/❌) · CTA en
   `evento.html` · h1 estáticos.
6. **T-V5-06 (M, 🔌 tras Storage) Identidad:** subida de avatar de perfil y logo+fondo de banda
   (bucket + políticas por banda + UI). Se especifica al desbloquear Storage.

### 2.4 DECISIONES ABIERTAS §2 (para Oscar)

- **D-EST-1:** ¿Pulir a fondo la identidad actual (oscuro+coral, recomendado: barato y ya hay
  sistema) o rediseño más ambicioso (paleta/marca nuevas)?
- **D-EST-2:** ¿El player se queda SIEMPRE oscuro como "modo escenario" (recomendado) o respeta el
  tema claro?
- **D-EST-3:** ¿Configuramos Supabase Storage ya (te guío, ~15 min) para desbloquear fotos/fondos?

---

## 3. Reproductor (la joya) — directo serio 🔴 [V5-F2]

### 3.1 Lo pedido por Oscar (íntegro)

1. **Compases:** el metrónomo va a negras; por defecto **cada acorde dura un compás de 4 negras**,
   pero no siempre (puede durar 2, etc.). Como saberlo desde las webs de acordes es poco fiable,
   se adopta la **medida estándar: acorde = 4 negras de serie**, con una manera **original y útil
   de verdad** de ajustar el ritmo (subir/bajar la duración) donde no encaje.
2. **Cuenta atrás al darle a Play**, configurable a **4 u 8 golpes** de aviso.
3. **Metrónomo con tipos de compás**: 2/4, 3/4, 4/4, 6/8… (sonando distinto: acento en el 1).
4. **Tempo más ágil:** ruleta presionable que sube/baja, o mantener pulsado +/− acelera el cambio.
5. **Abajo, en vez de "Beat", mostrar el COMPÁS** (idealmente el compás en el que estás; si medirlo
   bien se complica, al menos el número de compás transcurrido ya vale).
6. **Foto de un papel → partitura** (hacer una fotografía a una hoja con acordes/letra y que se
   convierta al formato del editor).
7. Mejor estética (cae dentro de §2/V5-F1).

### 3.2 Cómo hacerlo SIN tocar el motor (análisis técnico)

- **(1) Duración por acorde:** el motor ya trabaja con beats por `ChordMarker`; esto es un cambio de
  DATOS, no de motor. Al guardar/importar sin timing explícito: cada acorde = 4 beats. En el editor
  (vista previa): tocar un acorde abre un mini-control **×½ / ×2** (4→2→8 beats) — esa es la manera
  "original y simple": no se editan números, se parte o dobla el compás del acorde con un toque.
  Persistir en el modelo existente; `alembic check`; el player no cambia.
- **(2) Cuenta atrás:** antes de `engine.start()`, overlay grande 4-3-2-1 sincronizado con N clicks
  del metrónomo al BPM actual (N=4 u 8, ajuste junto al metrónomo, persistido en localStorage).
  Sin tocar el motor: es un pre-roll en `app.js`.
- **(3) Compases del metrónomo:** el click actual (`app.js`) gana selector 2/4 · 3/4 · 4/4 · 6/8:
  acento (frecuencia/volumen distinto) en el tiempo 1 y subdivisión en 6/8. Guardar por canción
  (campo `Song.time_signature`, migración aditiva) con default 4/4.
- **(4) Tempo ágil:** mantener pulsado +/− repite con aceleración (pointerdown + setInterval
  acelerante, patrón estándar, touch-friendly). La "ruleta" queda como alternativa si esto no
  convence a Oscar en uso real.
- **(5) Compás en la barra:** compás actual = `floor(beat / beats_por_compás) + 1` — client-side
  puro con el `time_signature` de (3). Mostrar "Compás 12" donde hoy "Beat: 47.0". (El e2e
  `test_player` referencia `#current-beat-display`: mantener id, cambiar contenido.)
- **(6) Foto→partitura (OCR):** input `capture=environment` → imagen a un **modelo de visión vía
  OpenRouter** (mismo patrón `importer.py`, prompt que devuelve el formato del editor) → precarga
  el editor para REVISAR antes de guardar (como el import por URL). ⚠️ Los modelos de visión
  gratuitos son flojos con manuscritos: empezar como **beta** con foto impresa/clara, medir calidad,
  y decidir si merece un modelo de pago. Punto de entrada doble: editor y repertorio de banda (§9.4).

### 3.3 DECISIONES ABIERTAS §3

- **D-PLY-1:** ¿el ajuste ×½/×2 por acorde te vale como "manera original", o quieres además un modo
  "tap tempo por acorde" (tocar la pantalla al ritmo para re-timear una sección)?
- **D-PLY-2:** ¿la cuenta atrás suena siempre o solo si el metrónomo está activado?
- **D-PLY-3 (para (6)):** ¿beta con modelo gratuito asumiendo fallos, o probamos directamente uno
  de pago barato con visión buena?

---

## 4. Afinador + Metrónomo — sección propia "con mimo" 🟠 [V5-F3]

- La entrada del menú pasa de "Afinador" a **"Afinador / Metrónomo"** (misma página, dos paneles o
  pestañas): afinador profesional (aguja fluida, indicador afinado/alto/bajo grande, selector de
  referencia A4=440, nombres de nota grandes) + **metrónomo standalone** con lo de §3.2(3): BPM con
  press-and-hold, compases 2/4·3/4·4/4·6/8, acento visual (flash) y sonoro, tap-tempo.
- Reutiliza `bfDetectPitch`/`bfFreqToNote` (no duplicar) y el click-engine del player (extraer a un
  módulo `metronome.js` compartido para que player y sección usen EL MISMO metrónomo).
- Diseño al nivel del resto tras V5-F1 (tokens, tarjeta centrada, móvil primero).

---

## 5. Explorar — el hub de la red 🔴 [V5-F4/F5, el corazón funcional de V5]

> Principio de Oscar: **toda pieza de Explorar está asociada a un perfil** (de músico o de banda).
> Y Biblioteca (§6) es su espejo personal. Sub-secciones como pestañas dentro de Explorar:

### 5.1 Estructura general

`biblioteca-global.html` evoluciona a **Explorar** con pestañas: **Músicos · Canciones · Material ·
Colaboraciones · Descubrir**. "Canciones" es la actual biblioteca global (V3-F9, ya hecha). Cada
pestaña es una fase/tarea independiente; el shell de pestañas se hace primero.

### 5.2 Perfil de músico 2.0 (prerequisito de todo §5) [V5-F4]

- **Estado** visible y filtrable: `busco_musicos` ("estoy montando banda/busco gente") ·
  `abierto` ("abierto a escuchar propuestas") · `no_busco`. Propuestas mías a valorar por Oscar:
  `busco_banda` (soy músico buscando banda) y `disponible_bolos` (sustituciones/refuerzos puntuales).
- **Instrumentos asociados a bandas**: "toco guitarra y bajo en The Rooftops" → instrumentos
  generales del perfil (ya existe) + instrumentos POR MEMBRESÍA (`BandMembership.instruments`,
  migración aditiva) que se pintan como chips "🎸 en The Rooftops".
- **Contacto:** botón "Contactar" en el perfil. Decisión abierta D-EXP-1 (mensaje interno vs
  WhatsApp `wa.me` — el teléfono en el perfil expone privacidad; ver preguntas).
- `visibility` en el perfil (hereda el pendiente V3-F7): privado por defecto, opt-in a aparecer en
  Explorar. Proyección segura (nunca email/teléfono sin consentimiento explícito).

### 5.3 Pestaña Músicos [V5-F5a]

Directorio filtrable (estado, instrumento, zona) de perfiles opt-in → tarjeta con foto (Storage 🔌;
mientras tanto avatar de iniciales), estado, instrumentos/bandas → perfil público → contactar.
Backend: `GET /explore/musicians` (proyección segura, paginado). Test de no-fuga: un perfil
`no_busco`+privado JAMÁS aparece.

### 5.4 Pestaña Material (alquilar/prestar entre músicos) [V5-F5c]

Anuncios de material: `GearItem` (dueño=perfil o banda, título, tipo, foto 🔌Storage, precio/día o
"presto gratis", fianza, zona, estado activo/pausado) + contacto igual que músicos. El estado de
"prestado a quién / qué me han prestado" alimenta Finanzas personales (§11) y Biblioteca (§6).
⚠️ Legal light: BandFlow solo conecta, no gestiona pagos ni responsabilidad (texto claro en la UI).

### 5.5 Pestaña Colaboraciones (entre bandas) [V5-F5d]

Hereda `CollabPost` de V3-F10: anuncios de banda→banda ("compartimos cartel el 12/09", "buscamos
telonera", "intercambio de sala de ensayo"). Publicado por admin en nombre de la banda; responde
otro admin. Tipos cerrados + texto libre. Se cruza con §10 (conciertos).

### 5.6 Pestaña Descubrir (la música de las bandas de BandFlow) [V5-F5b]

- Las bandas **suben sus canciones originales** (letra+acordes que no están en ningún otro sitio) →
  los demás músicos pueden verlas y TOCARLAS con la joya. Reusa el catálogo (V3-F9,
  `MusicalWork/PublicScore`) añadiendo `is_original`+`band_id` (proyección segura) y una **página
  pública de banda** (nombre, foto 🔌, sus originales, próximos conciertos `unlisted/public`).
- **Futuro (registrado, no ahora):** reproducir el audio de la canción (YouTube embebido u otra
  fuente) sincronizado con la partitura — `Song.reference_url` ya existe y es la semilla.

### 5.7 DECISIONES ABIERTAS §5

- **D-EXP-1:** contacto músico-músico: ¿mensaje interno, WhatsApp, o interno + WhatsApp opcional
  si el perfil lo activa? (afecta a Chat §8 y privacidad)
- **D-EXP-2:** ¿los dos estados extra que propongo (`busco_banda`, `disponible_bolos`) entran?
- **D-EXP-3:** ¿"zona" del perfil/material = texto libre (ciudad) o algo más estructurado?
- **D-EXP-4:** orden de las pestañas dentro de F5: propongo Músicos → Descubrir → Colaboraciones →
  Material (Material el último porque sin Storage no tiene fotos). ¿OK?

---

## 6. Biblioteca — el espejo personal de Explorar 🟠 [V5-F8]

Oscar: "la biblioteca es un seguido de exploración, pero con las cosas tuyas personales".
- **Mis canciones**: lo actual (partituras propias + de bandas), organizadas **por proyectos
  propios** (las colecciones personales ya existen → renombrar/elevar a "Proyectos" si Oscar quiere).
- **Mis contactos**: músicos con los que has contactado (cuando exista contacto §5.2) — p. ej. "en
  septiembre contacté con X" → lista con fecha/contexto y acceso a su perfil.
- **Guardados**: canciones de Descubrir/Canciones que te guardas, material que sigues.
- Se especifica fino cuando §5 esté cerrado (depende de qué genere "contactos" y "guardados").

---

## 7. Agenda — calendario de verdad 🟠 [V5-F6]

- Vista **calendario mensual** (rejilla, puntos/chips por evento con color de banda `bandColor`) +
  debajo **vista semanal** (lista por día con horas). TODO lo que tenga fecha/hora aparece:
  eventos de todas las bandas, propuestas pendientes (§9.5), fechas de notas de pizarra (§9.3).
- Client-side puro sobre `/me/events` (ya agrega todas las bandas): componente `bf-calendar`
  reutilizable — **el mismo componente se usa en la agenda de banda (§9.5) y en el Resumen (§9.2)**.
  Sin dependencias externas (nada de FullCalendar; rejilla CSS propia con los tokens).
- La lista actual no se tira: es la vista "Próximos" (toggle Lista/Calendario, persistido).

---

## 8. Chat — reestructura (lo más delicado según Oscar) 🟠 [V5-F7]

- **Dos grandes grupos** en la página de Chat: **Mis bandas** y **Contactos** (músicos de §5).
  Cada conversación con **etiqueta de color**: color de banda (`bandColor`) para las de banda,
  color neutro/etiqueta "músico" para contactos personales. Que se distinga de un vistazo qué chat
  de qué banda estás usando.
- **Chat dentro de banda — propuesta (Oscar preguntó):** el chat de banda VIVE en la sección Chat
  global (grupo "Mis bandas"); la pestaña Chat del espacio de banda se sustituye por un
  **atajo/preview** (último mensaje + "Ir al chat", como ya hace el Resumen). Ventaja: un solo
  sitio donde hablar, cero duplicación de UI, y las notificaciones apuntan a un único lugar. Los
  hilos por evento siguen accesibles desde la agenda. → **D-CHT-1 a confirmar por Oscar.**
- El backend actual (`messages` por banda) sirve para bandas; los DM de contactos necesitan modelo
  nuevo (conversación 1-a-1 entre perfiles) SI D-EXP-1 elige mensajería interna.

---

## 9. Bandas — espacio de banda 2.0 🔴 [V5-F9, la sección más gorda]

### 9.1 Lista "Mis bandas"

- Pestañas/acciones: **Mis bandas** + botón/pestaña **"Unirme a banda"** que lleva al explorador
  (Explorar→Músicos/Descubrir con filtro de bandas buscando gente, o al flujo de código de
  invitación actual — ambas puertas). Diseño de tarjetas más bonito (ya rico desde T-132; se
  repasa con la estética V5-F1).

### 9.2 Identidad de banda y miembros (🔌 Storage para fotos)

- **Miembros**: nada de letras sueltas — **nombre de usuario elegido** (display_name, ya existe) +
  **foto de perfil** (Storage). El propietario/admin puede además poner **imagen de fondo** en la
  cabecera del espacio de banda (banner tipo cover). Sin Storage: avatar de iniciales con
  `bandColor` correcto y cover con degradado del color de banda (queda digno mientras tanto).

### 9.3 Pizarra / Notas de banda (NUEVO, sección propia + widget en Resumen)

- Una **pizarra compartida**: cualquier miembro apunta pendientes ("ensayar puente de X",
  "comprar cuerdas") en cualquier momento; toda la banda lo ve. Notas **pinneables** y con **fecha
  opcional** (si tiene fecha, aparece en la agenda/calendario). Marcar como hecho.
- Modelo: `BandNote(band_id, author_id, body, is_pinned, due_date, done_at, created_at)` +
  migración + router con pertenencia + **test de aislamiento** + CRUD simple. Pestaña propia
  "Pizarra" + widget en Resumen (§9.6). (No confundir con las notas fijadas del chat: la pizarra
  es tareas/apuntes, el chat es conversación.)

### 9.4 Repertorio de banda

- **Estado de preparación por canción y usuario** (lo pedía Oscar y estaba en V4 §"estado de
  preparación"): cada miembro marca cada canción como `pendiente` ("no la sé") / `mejorando`
  ("me falta") / `dominada` ("la llevo bien"). Es PRIVADO por defecto; el usuario puede
  **publicarlo a la banda** si quiere. Modelo `SongStatus(band_song_id, user_id, status, shared)`.
  En el repertorio: marcador de 3 estados por canción; en Resumen: **diagrama** (barras/donut) con
  tu progreso (y el de la banda con los compartidos).
- **Crear canción desde el repertorio** (abajo del listado): botón que abre el editor en contexto
  de banda (escribir, importar por nombre/URL — T-162/T-163 — o **foto→partitura** §3.2(6)).

### 9.5 Agenda de banda con PROPUESTAS

- Misma agenda/calendario que la personal (§7, mismo componente) pero de la banda.
- **Flujo nuevo de propuesta:** un miembro **propone** un evento → los miembros marcan si les va
  bien (reutiliza el modelo de asistencia como votación previa) → cuando el admin confirma, pasa
  al calendario oficial. `Event.status` gana el estado `proposed` (el pipeline de booking ya
  existe, es aditivo). Las propuestas pendientes se ven en Resumen y en la agenda con estilo
  "fantasma".

### 9.6 Resumen de banda (nuevo orden, de arriba a abajo — literal de Oscar)

1. **Calendario general de la banda** (componente §7 en mini).
2. **Pizarra**: tareas/notas pendientes (widget de §9.3, pinneadas primero).
3. **Estado económico**: tu saldo en la banda (debes/te deben) + resumen de quién debe a quién.
4. **Diagrama del repertorio**: canciones dominadas / mejorando / pendientes (§9.4).

### 9.7 Finanzas de banda — estudio completo [se pule en §11, AL FINAL]

Registrado lo pedido: estructura por un lado la economía del grupo (gastos generales **mensuales**
tipo local de ensayo y **puntuales**), por otro lo del usuario en relación con la banda (+/−).
Pensar en TODO lo que una banda gasta (estudio completo en esa fase, con el contexto del resto).

### 9.8 Chat de banda → ver §8 (propuesta: atajo al chat global). Giras → ver §10.

---

## 10. Conciertos (antes "Giras") — organiza tu concierto 🟠 [V5-F10]

- Reenfoque de Oscar: antes que giras completas, **ayudar a organizar UN concierto**. Un asistente
  guiado ("Organiza tu concierto") que va preguntando: ¿en qué sala tocaréis o queréis tocar?
  ¿qué condiciones piden/pedís (caché, entrada, %)? ¿quién pone el material/backline? ¿cómo movéis
  los instrumentos? ¿horarios (prueba de sonido, apertura)? → genera el `Event(type=concert)` con
  **checklist** por concierto (`EventChecklistItem`: ítem, responsable, hecho) + resumen imprimible.
- Aporta valor real: la checklist y el reparto de responsabilidades es lo que las bandas llevan en
  notas sueltas. Se cruza con Salas (`Venue`, ya existe), booking pipeline (ya existe), pizarra
  (§9.3) y finanzas del evento (caché ya existe en T-115).
- **Giras** (agrupar varios conciertos, ya hay modelos `Tour/TourStop` de V3-F5) se re-presentan
  DESPUÉS encima de esto, como "varios conciertos encadenados + presupuesto".

---

## 11. Finanzas — integral, AL FINAL (instrucción explícita de Oscar) [V5-F11]

No se pule hasta tener el resto (necesita el contexto de material prestado, conciertos, pizarra…).
Queda registrado el esquema pedido: **secciones separadas** — (a) **Personales**: quién te debe,
qué material tienes prestado/anunciado (de §5.4), tus saldos con cada banda; (b) **De banda**:
economía del grupo (gastos mensuales/puntuales, local, caché de bolos) + lo del usuario respecto
a la banda (+/−). Con calendario de pagos recurrentes si encaja. Estudio completo al llegar aquí.

---

## 12. Orden de fases V5 y dependencias

| Fase | Qué | Depende de |
|---|---|---|
| **V5-F1** 🔴 | Estética global (§2.3: bugs → emoji → componentes → tema → detalles) | — |
| **V5-F2** 🔴 | Reproductor (§3: datos 4-negras + ×½/×2, countdown, compases metrónomo, tempo hold, compás display; OCR como beta al final) | F1 |
| **V5-F3** 🟠 | Afinador/Metrónomo sección (§4, extrae `metronome.js` de F2) | F2 |
| **V5-F4** 🔴 | Perfil 2.0 (§5.2: estado, instrumentos/banda, visibility, contacto) | decisión D-EXP-1 |
| **V5-F5** 🔴 | Explorar por pestañas (§5.3-5.6: a Músicos, b Descubrir, c Material 🔌, d Colaboraciones) | F4 (y Storage para fotos) |
| **V5-F6** 🟠 | Agenda calendario mensual+semanal (§7, componente `bf-calendar`) | F1 |
| **V5-F7** 🟠 | Chat 2.0 (§8: grupos, etiquetas, DM si procede) | F4/F5a |
| **V5-F8** 🟠 | Biblioteca espejo (§6) | F5 |
| **V5-F9** 🔴 | Bandas 2.0 (§9: pizarra, estado repertorio, propuestas, resumen nuevo, identidad 🔌) | F1, F6 (calendario) |
| **V5-F10** 🟠 | Conciertos wizard (§10) | F9 |
| **V5-F11** 🟠 | Finanzas integral (§11) | TODO lo anterior (orden de Oscar) |
| Transversal 🔌 | **Storage** (fotos perfil/banda/material) — bloqueado en config de Oscar | — |

> El orden F6-F9 es ajustable con Oscar al cerrar cada sección; F1→F2→F3 y F11-último son fijos.

---

## 13. Registro de decisiones por sección (se rellena al ir hablando)

| Fecha | Sección | Decisión | Detalle |
|---|---|---|---|
| 2026-07-03 | Global | V5 abierta; método sección-a-sección | Este documento |
| _(pendiente)_ | §2 | D-EST-1/2/3 | |
| _(pendiente)_ | §3 | D-PLY-1/2/3 | |
| _(pendiente)_ | §5 | D-EXP-1/2/3/4 | |
| _(pendiente)_ | §8 | D-CHT-1 (chat de banda = atajo al global) | |

> **Estado:** V5 recién abierta (2026-07-03). Siguiente paso: Oscar responde la primera ronda de
> decisiones (D-EST-1/2/3 y D-CHT-1/D-EXP-1) y arrancamos **V5-F1 (estética)** por el bucle de oro.
