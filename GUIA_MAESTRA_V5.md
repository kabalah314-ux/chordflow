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
7. **Regla dura de decisiones (Oscar, 2026-07-05):** una decisión D-* abierta **bloquea únicamente
   las piezas listadas en su "Bloquea exactamente:"** (en la sección donde vive la D-*); el resto de
   la sección puede avanzar. Antes de tocar una pieza bloqueada: preguntar a Oscar (con opciones y
   recomendación), registrar la respuesta en §13, y SOLO entonces abrir la tarea. Si Oscar no
   responde, se aparca ESA pieza y se sigue con otra — nunca se decide por él en una bifurcación
   de producto. Las "propuestas por defecto" NO se asumen: o Oscar las confirma o la pieza espera.
8. **Coherencia inter-sección:** antes de dar por cerrada una sección, repasar su fila y columna en
   el mapa de interconexiones (§14) y verificar que cada flujo que la toca sigue funcionando o
   queda actualizado. §14 es parte del contrato, no documentación decorativa.

### 0.2 Herencia: qué absorbe esta guía de V3/V4 (nada se pierde)

| Pendiente heredado | De dónde | Dónde vive ahora |
|---|---|---|
| Ensayo sincronizado realtime (`/clock`, Supabase Realtime) | V3-F6 | Futuro post-V5 (no re-priorizado; se retoma al acabar §3/§4) |
| `visibility` en perfil + onboarding viral + oEmbed título/autor | V3-F7 resto | §5 (Explorar/perfiles) y §2 (pulido) |
| EPK + página pública banda + RSVP + fans | V3-F8 | §5.6 (Descubrir) + §10 (Conciertos); RSVP/fans siguen ahí |
| Red acotada: directorio + `CollabPost` | V3-F10 | §5 entero (Explorar es su superset) |
| Monetización Stripe/Pro | V3-F11 | Post-V5 (sin cambios, `Band.plan` ya andamiado) |
| Storage Supabase (avatares/logos/archivos) | V3-F3 T-099 / V4-F6 T-153 | **✅ CONFIGURADO (2026-07-03**, bucket `media` + RLS; T-V5-06 hecho). `upload.js` es el módulo compartido para TODA subida nueva (fotos de material §5.4, futuras). Ya NO es bloqueante |
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
7. **Identidad visual real:** fotos de perfil, logo/fondo de banda — **✅ HECHO (T-V5-06,
   2026-07-03)**: Storage configurado (bucket `media` + RLS) y fotos implementadas vía `upload.js`.
   Ese módulo es la vía compartida para toda subida futura (material §5.4).
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
6. **T-V5-06 ✅ HECHO (2026-07-03) Identidad:** Storage configurado por Oscar (bucket `media`) →
   foto de perfil + logo y fondo de banda implementados (`upload.js`, `Band.cover_url`, `bfAvatar()`,
   validación anti-XSS de URLs). Detalle en `REGISTRO_DE_CAMBIOS.md`. Fotos de MATERIAL → §5.4.

### 2.4 DECISIONES §2 — ✅ CERRADAS (Oscar, 2026-07-03)

- **D-EST-1 ✅ Pulir a fondo la identidad actual** (oscuro+coral+IBM Plex): unificar sistemas,
  disciplina de tokens. NO se abre rediseño de marca.
- **D-EST-2 ✅ El player SIEMPRE oscuro** ("modo escenario"): se documenta y se fuerza con estilo
  propio; el editor y join SÍ respetan el tema claro (T-V5-04).
- **D-EST-3 ✅ Storage se configura YA** (Oscar guiado): desbloquea T-V5-06, §5.4 y §9.2.

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
  acelerante, patrón estándar, touch-friendly). (La "ruleta" presionable quedó **DESCARTADA por
  Oscar el 2026-07-05**: el press-and-hold de T-V5-09 cumple — ver §13.)
- **(5) Compás en la barra:** compás actual = `floor(beat / beats_por_compás) + 1` — client-side
  puro con el `time_signature` de (3). Mostrar "Compás 12" donde hoy "Beat: 47.0". (El e2e
  `test_player` referencia `#current-beat-display`: mantener id, cambiar contenido.)
- **(6) Foto→partitura (OCR):** input `capture=environment` → imagen a un **modelo de visión vía
  OpenRouter** (mismo patrón `importer.py`, prompt que devuelve el formato del editor) → precarga
  el editor para REVISAR antes de guardar (como el import por URL). ⚠️ Los modelos de visión
  gratuitos son flojos con manuscritos: empezar como **beta** con foto impresa/clara, medir calidad,
  y decidir si merece un modelo de pago. Punto de entrada doble: editor y repertorio de banda (§9.4).

### 3.3 DECISIONES §3 — ✅ CERRADAS (Oscar, 2026-07-03)

- **D-PLY-1 ✅ ×½/×2 por acorde + tap tempo por acorde.** El mini-control ×½/×2 es la base
  (parte/dobla el compás del acorde con un toque), Y ADEMÁS un modo "tap tempo por acorde": tocar
  la pantalla al ritmo para re-timear una sección. Ambos escriben los beats del `ChordMarker` (cambio
  de DATOS, el motor no se toca).
- **D-PLY-2 ✅ La cuenta atrás suena SOLO si el metrónomo está activado.** Con el metrónomo apagado,
  el pre-roll 4-3-2-1 es solo visual (silencioso). Persistir N (4/8) en localStorage.
- **D-PLY-3 ✅ Foto→partitura: beta con modelo gratuito de visión.** Coste 0, mismo patrón que el
  import por URL; se empieza con foto impresa/clara, se mide calidad y se decide luego si merece pago.

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

### 5.1 Estructura general — ✅ CERRADA (Oscar, 2026-07-05)

`biblioteca-global.html` evoluciona a **Explorar** con **5 pestañas**:

| Pestaña | Qué muestra | Quién aparece |
|---|---|---|
| **Músicos** | Músicos que buscan banda o están abiertos a propuestas | Perfiles con estado `busco_banda` o `abierto` (§5.2) |
| **Bandas** | Bandas que buscan uno o varios músicos (+ colaboraciones banda↔banda) | Bandas con anuncio activo (§5.5) |
| **Material** | Material en alquiler/préstamo entre músicos | Piezas publicadas desde "Mi material" (§5.4) |
| **Canciones** | La biblioteca global de partituras (V3-F9, YA EXISTE) | Partituras públicas del catálogo |
| **Descubrir** | La música original de las bandas de BandFlow | Originales publicados (§5.6) |

Reglas de la estructura:
- **Los nombres de pestaña de la UI son EXACTAMENTE: Músicos, Bandas, Material, Canciones,
  Descubrir** (los literales "Buscar músicos"/"Buscar banda" de conversaciones previas NO se usan
  en la UI).
- **Explorar (las 5 pestañas) requiere SESIÓN** — vive dentro del shell con login. Los endpoints
  `/explore/*` llevan `Depends(get_current_user)` pero devuelven SOLO proyección segura (defensa
  en profundidad). Lo único público sin login: `evento.html` (V3-F7) y la página pública de banda
  (§5.6). El plano público de Explorar sin login queda como iteración futura, no V5.
- **Límites comunes de `/explore/*`**: `limit` default 20 máx 50; `skip` ≥ 0; zona
  case-insensitive (ILIKE / `lower()` en SQLite).
- **Toda pieza de Explorar está asociada a un perfil** (de músico o de banda) — principio de Oscar.
- El **shell de pestañas se construye primero** (una tarea propia); cada pestaña es después una
  fase/tarea independiente.
- "Colaboraciones" NO es pestaña propia: sus anuncios (compartir cartel, buscar telonera,
  intercambio de local) viven DENTRO de la pestaña **Bandas** como un tipo más de anuncio (§5.5).
- Simetría clave (para que "todo tenga sentido"): **Músicos** es el escaparate del músico
  (su estado en el perfil), **Bandas** el de la banda (su anuncio), **Material** el de "Mi
  material". Nada se publica "desde Explorar": Explorar solo LISTA lo que cada uno activa en su
  propio espacio. Un solo flujo mental: *activo algo en lo mío → aparece en Explorar → me
  contactan → Chat*.

### 5.2 Perfil de músico 2.0 (prerequisito de todo §5) [V5-F4]

- **Estado — ✅ CERRADO (2026-07-05): 3 valores** en el perfil, visibles y filtrables:
  - `busco_banda` — "estoy buscando banda/proyecto para tocar" → aparece en Explorar>Músicos.
  - `abierto` — "no busco activamente pero escucho propuestas" → aparece en Explorar>Músicos
    con etiqueta propia (visualmente distinta de `busco_banda`).
  - `no_busco` — no aparece en Explorar. **Default.**
  - ("busco músicos" ya NO es estado del perfil personal: eso es el ANUNCIO de banda, §5.5.
  "Disponible para bolos" descartado de momento.)
- **Instrumentos asociados a bandas**: "toco guitarra y bajo en The Rooftops" → instrumentos
  generales del perfil (ya existe) + instrumentos POR MEMBRESÍA que se pintan como chips
  "🎸 en The Rooftops". ⚠️ Colisión: `band_memberships` YA TIENE `instrument` String(64)
  singular — EVOLUCIONAR: añadir `instruments` JSON + migración de datos que copie el valor
  actual como lista de 1; `instrument` queda deprecated (no borrar, no usar en código nuevo).
- **Contacto — ✅ D-EXP-1 CERRADA (2026-07-05): chat interno + WhatsApp opcional.** Botón
  "Contactar" en el perfil → abre un **DM interno** (modelo §8). Reglas de privacidad del
  teléfono: (1) el teléfono NUNCA aparece en los LISTADOS (`/explore/musicians|gear|bands`) —
  test de no-fuga con grep del JSON; (2) el enlace `wa.me` solo se sirve en el DETALLE de
  perfil/pieza a usuarios AUTENTICADOS y solo si el dueño hizo opt-in. El opt-in ES consentimiento
  a que su número sea visible para usuarios logueados (un enlace wa.me lo contiene por
  construcción; no se puede ocultar tras el clic — la UI del opt-in lo avisa con esa frase).
- **Matriz de visibilidad (precedencias explícitas):** (1) pestaña Músicos — manda
  `seeking_status` (estado activo = opt-in que prevalece sobre `visibility`); (2) publicar
  material o anuncio — implica exposición mínima inevitable (display_name + avatar + zona; la UI
  de publicar lo avisa con una línea); (3) página de perfil completa — gobernada por `visibility`
  (privado por defecto, hereda el pendiente V3-F7). Proyección segura siempre (nunca
  email/teléfono).
- **Zona — ✅ D-EXP-3 CERRADA (2026-07-05): texto libre** corto ("Murcia", "Madrid sur") — sin
  geocoding; el filtro busca por `contains` case-insensitive (ILIKE / `lower()` en SQLite).
- **Modelo (F4, migración aditiva sobre `musician_profiles`)**: `seeking_status` String(16)
  CHECK in ('busco_banda','abierto','no_busco') default 'no_busco' (valores en español =
  convención declarada de este campo) · `zone` String(120) NULL · `bio` Text NULL · `visibility`
  String(16) in ('private','public') default 'private' · `phone` String(32) NULL ·
  `whatsapp_optin` Boolean default false.
- **Presencia pública de BANDA (opt-in derivado):** una banda tiene presencia pública SOLO si
  anuncio activo ∨ originales publicados ∨ algún concierto `public`; los chips "en {banda}" del
  perfil solo muestran bandas con presencia pública. Test de no-fuga: banda sin nada publicado
  JAMÁS aparece en `/explore/*`.
- **El perfil público lista el material publicado**: sección "Material en alquiler" (piezas con
  `is_listed`, misma proyección segura de §5.4b) — enlace bidireccional pieza↔perfil del dueño.

### 5.3 Pestaña Músicos [V5-F5a]

Directorio filtrable de perfiles con estado `busco_banda`/`abierto`:
- **Filtros**: estado · instrumento · zona (texto). **Orden**: actividad reciente primero.
- **Tarjeta**: foto (Storage; fallback avatar de iniciales) · display_name · estado (badge de
  color) · instrumentos (chips, incl. "en {banda}") · zona → clic = perfil público → "Contactar"
  (DM + wa.me opcional, §5.2).
- Backend: `GET /explore/musicians` (proyección segura: id, display_name, avatar, estado,
  instrumentos, zona, bandas públicas — NADA más; paginado `skip/limit` acotado).
- 🔐 Test de no-fuga obligatorio: un perfil `no_busco` JAMÁS aparece; email/teléfono JAMÁS en la
  respuesta (grep del JSON).
- Vacío: `bfEmpty` con CTA "Pon tu estado en el perfil para aparecer aquí".

### 5.4 Material — sección personal "Mi material" + pestaña Explorar>Material [V5-F5c]

**✅ CERRADO (2026-07-05): "Mi material" es un item propio del menú lateral.** El ecosistema
tiene dos caras y un solo modelo:

**(a) Mi material (sección personal, en el lateral):**
- Tu inventario: subes cada pieza con **foto** (OPCIONAL — placeholder por tipo si no hay; UNA
  foto por pieza en V5; vía `upload.js`, que manda sus límites de tamaño), título, tipo
  (ampli, micro, pedal, instrumento, PA, luces, otro), descripción/estado físico y zona (texto
  libre, D-EXP-3 ✅).
- **Dos dimensiones INDEPENDIENTES por pieza** (no un único estado):
  - `is_listed` (bool) — ¿aparece en Explorar>Material? Botón **"Poner a alquilar / prestar"**
    (formulario corto: precio/día o "presto gratis", fianza opcional) lo activa; "Retirar" lo
    desactiva. La pieza siempre sigue en tu inventario.
  - `loan_status` (`libre` | `prestado`) — ¿la tienes tú o la tiene alguien? "Marcar prestada"
    abre el formulario de préstamo (a quién, desde cuándo) y **por defecto la des-lista**
    (checkbox "mantener anunciada" para el alquiler recurrente: pieza prestada que sigue
    anunciada). "Marcar devuelta" cierra el préstamo; la pieza conserva su `is_listed`.
  - Diagrama completo: privado → publicado → (contacto I-3) → prestado → devuelto →
    publicado/privado.
- **Modelo**: `GearItem(owner_id, title, kind, photo_url, description, zone, is_listed,
  loan_status, price_day, is_free, deposit, created_at)` + **`GearLoan`** para los préstamos con
  histórico: `GearLoan(gear_item_id, borrower_user_id String(36) NULL — FK a usuario si el
  contacto vino por I-3, borrower_name String(120) NULL — texto libre, price_day, deposit,
  started_at, ended_at NULL, notes)`; al menos uno de los dos `borrower_*` obligatorio. Cada
  préstamo = una fila. Migración aditiva + router owner-scoped (ajeno→404) + test de aislamiento.
- **Reparto por fases**: `GearLoan` se crea en F5c y se rellena al marcar prestado/devuelta (solo
  estado, sin UI de pagos); **Finanzas>Personal (§11.3, F11) LEE de `GearLoan`** — no del estado
  de la pieza — y ahí se cierra I-4.

**(b) Pestaña Explorar>Material:**
- Lista SOLO las piezas `publicado` (proyección segura: sin datos del dueño más allá de
  display_name/avatar/zona).
- **Filtros**: tipo · zona · precio (gratis/de pago). **Tarjeta**: foto grande, título, tipo,
  precio/día o "Gratis", zona, dueño → clic = detalle → **"Contactar"** (mismo flujo §5.2: DM
  interno + wa.me opcional del dueño).
- ⚠️ Legal light: BandFlow solo conecta — no gestiona pagos, envíos ni responsabilidad (texto
  claro y visible en la UI de publicar y de contactar).
- 🔐 Tests: pieza `privado` JAMÁS en `/explore/gear`; solo el dueño puede editar/publicar/retirar.

### 5.5 Pestaña Bandas (buscan músicos + colaboraciones) [V5-F5d]

**✅ CERRADO (2026-07-05):** la pestaña Bandas muestra **anuncios de banda**, de dos tipos:

**(a) "Buscamos músico(s)"** (lo nuevo que pidió Oscar):
- La banda publica desde su espacio (§9) un anuncio: **qué instrumento(s)** busca (uno o varios:
  "bajista", "bajista y voz") + texto libre corto (estilo, frecuencia de ensayos, zona).
- En Explorar>Bandas: tarjeta con logo/nombre de banda, instrumentos buscados (chips), zona,
  texto → clic = detalle/página de banda → **"Contactar"** (DM al admin que publicó; wa.me
  opcional igual que perfiles).
- Al desactivar el anuncio, la banda desaparece de la pestaña.
- Modelo: `BandOpening(band_id, instruments, body, zone, is_active, created_by, created_at)`
  (o campos en `Band` si se decide 1 anuncio máx por banda — ver D-BND-2 en §5.7) + aislamiento.
- ⛳ Interconexión: la pestaña **"Unirme a banda"** de §9.1 aterriza AQUÍ (Explorar>Bandas).
- **✅ D-BND-1 (2026-07-05): SOLO el admin** publica/edita/desactiva el anuncio (como las
  colaboraciones: en nombre de la banda).

**(b) Colaboraciones banda↔banda** (hereda `CollabPost` de V3-F10, fusionado aquí):
- Anuncios "compartimos cartel el 12/09", "buscamos telonera", "intercambio de local".
  Tipos cerrados + texto libre. Publica un admin en nombre de la banda; responde otro admin
  (DM entre admins). Se cruza con §10 (conciertos).
- En la pestaña se distinguen por un badge de tipo ("Buscan músico" / "Colaboración").

### 5.6 Pestaña Descubrir (la música de las bandas de BandFlow) [V5-F5b]

- Las bandas **suben sus canciones originales** (letra+acordes que no están en ningún otro sitio) →
  los demás músicos pueden verlas y TOCARLAS con la joya. Reusa el catálogo (V3-F9).
- **Modelo:** `is_original` Boolean default false + `band_id` String(36) NULL index van en
  **`PublicScore`** (la unidad publicada; `MusicalWork` no se toca). Publica cualquier **ADMIN**
  de la banda desde el repertorio (§9.4), nunca "desde Explorar" (regla §5.1).
- **Página pública de banda (ENTRA EN F5b** — Descubrir sin página de banda es un flujo a
  medias, regla §14.2.7): `static/banda.html?id=…` sin login (patrón `evento.html`),
  `GET /public/bands/{id}` con proyección segura: nombre, avatar/cover, bio, originales
  publicados, próximos conciertos `public/unlisted` con RSVP, anuncio activo si lo hay (§9.9),
  botón Contactar→I-3.
- **"Tocar" ≠ guardar**: "tocar" abre el player en modo solo-lectura sobre la partitura pública
  (sin copia, sin persistir tempo/transposición — reutiliza el flujo del catálogo V3-F9);
  "Guardar en Biblioteca" (I-5) es el paso opt-in para tenerla editable en una carpeta (§6).
- **Futuro (registrado, no ahora):** reproducir el audio de la canción (YouTube embebido u otra
  fuente) sincronizado con la partitura — `Song.reference_url` ya existe y es la semilla.
  (El caso "músico individual sube su original sin banda" también queda para esta iteración
  futura, ligado al perfil — anotado para no perderse.)

### 5.7 DECISIONES §5 — estado (2026-07-05)

- **D-EXP-1 ✅ CERRADA**: contacto = **chat interno + WhatsApp opcional** (perfil añade teléfono
  y lo activa; nunca expuesto por defecto).
- **D-EXP-2 ✅ CERRADA**: estados del músico = `busco_banda` · `abierto` · `no_busco` (el "busco
  músicos" es el anuncio de la BANDA; "disponible para bolos" descartado de momento).
- **D-EXP-4 ✅ CERRADA**: pestañas = **Músicos · Bandas · Material · Canciones · Descubrir**
  (Colaboraciones fusionada en Bandas).
- **D-BND-1 ✅ CERRADA (2026-07-05)**: SOLO el admin publica/edita/desactiva el anuncio.
- **D-EXP-3 ✅ CERRADA (2026-07-05)**: zona = **texto libre** (filtro por `contains`).
- **D-BND-2 ⏳ ABIERTA**: ¿1 anuncio máximo por banda (campos en `Band`) o varios (`BandOpening`
  como filas)? (recomendado: 1 activo por banda, tabla propia para histórico).
  **Bloquea exactamente:** el modelo y permisos del anuncio → la tarea T-V5-26 (pestaña Bandas,
  F5d). NO bloquea F5a/b/c ni F4.

### 5.8 Plan de tareas V5-F4/F5 (el equivalente a la lista T-V5-01..06 de F1)

> Se abren como T-NNN en ROADMAP al arrancar. S/M/L = esfuerzo. Orden de ejecución = orden de lista.

1. **T-V5-20 (M) Perfil 2.0**: migración aditiva de `musician_profiles` (campos de §5.2) +
   `band_memberships.instruments` (evolución del singular) + UI del perfil (estado con 3 valores,
   zona, bio, teléfono+opt-in WhatsApp con su aviso, instrumentos por banda) + proyección pública.
2. **T-V5-21 (S) DM base** (§8): modelo + router + grupo mínimo "Otros contactos" en Chat.
3. **T-V5-22 (S) Shell de Explorar**: `biblioteca-global.html` SE CONSERVA como archivo (no
   romper URLs/tests) pero gana la barra de 5 pestañas; la vista actual pasa a ser la pestaña
   "Canciones"; título y lateral pasan a "Explorar".
4. **T-V5-23 (M) Pestaña Músicos** (§5.3) con test de no-fuga + test de flujo I-1.
5. **T-V5-24 (M) Descubrir + página pública de banda** (§5.6) + flujo I-6/I-16.
6. **T-V5-25 (L) Mi material + pestaña Material** (§5.4, sin decisiones abiertas) + flujo I-4.
7. **T-V5-26 (M) Pestaña Bandas** (§5.5) — ⏳ BLOQUEADA por D-BND-2 (preguntar antes de abrir).

**Criterio de "hecho" por pestaña:** filtros funcionando · tarjeta según spec · empty state
`bfEmpty` con CTA · test de no-fuga · test de flujo I-N correspondiente · móvil revisado.

---

## 6. Biblioteca — carpetas ✅ (Oscar, 2026-07-05) 🟠 [V5-F8]

**✅ CERRADO (2026-07-05): la Biblioteca se organiza por CARPETAS.** Estructura:

1. **Personales** — TODAS tus canciones (las tuyas + las que te has guardado de
   Canciones/Descubrir), divisibles en **carpetas que el usuario crea y nombra libremente**
   ("Acústicas", "Proyecto X", "Para aprender"…). Una canción puede vivir en varias carpetas
   (relación N:M). Las **colecciones personales ya existentes** (`SongCollection` con `owner_id`,
   T-114) SON la semilla de estas carpetas: se renombran/elevan a "carpetas" — no se crea un
   modelo paralelo, se evoluciona el que hay.
2. **Mis setlists** — **✅ D-BIB-3 (2026-07-05): bloque propio** para tus setlists PERSONALES de
   siempre (se crean/editan aquí como hasta ahora — `setlists.html`/su flujo se integra o enlaza
   desde este bloque; nada se rompe).
3. **Setlists abiertos** — dentro salen **los setlists de cada banda activa** que tengas.
   "Banda activa" = `band_memberships.status='active'` (ya existe; baja blanda con `'left'`) Y
   `bands.deleted_at IS NULL` — no crear flags nuevos. **✅ D-BIB-2 (2026-07-05): solo ver y
   ▶ tocar** — editar se queda en el espacio de banda (una sola fuente de edición, regla §14.2.3).
4. **➕ "Añadir nueva"** — botón siempre visible para crear una carpeta nueva (nombre libre).

Detalles de comportamiento:
- "Guardarse" una canción desde Explorar>Canciones o Descubrir → elige carpeta (o "Sin carpeta",
  raíz de Personales). El guardado es una COPIA personal (como el import actual del catálogo:
  editable sin tocar el original) — coherente con lo que ya hace V3-F9.
- El buscador y el filtro por banda actuales de la Biblioteca se conservan por encima de las
  carpetas (buscar no debe obligar a navegar carpetas).
- **✅ D-BIB-1 (2026-07-05): los CONTACTOS viven SOLO en Chat>Otros contactos (§8)** — la
  Biblioteca queda exclusivamente para música (sin carpeta "Mis contactos").
- Modelo: evolución de `SongCollection` (añadir `parent_id` NULL para sub-carpetas SOLO si Oscar
  lo pide; de inicio un nivel es suficiente y más simple) + N:M ya existente. **Alcance:** la
  evolución SongCollection→carpetas afecta SOLO a las filas con `owner_id` (`band_id` NULL); las
  colecciones de banda (T-114) no cambian.
- 🔐 Owner-scoped estricto (ajeno→404) + test de aislamiento; "Setlists abiertos" exige
  membresía activa (test: baja de banda → sus setlists desaparecen de la Biblioteca).

---

## 7. Agenda — calendario de verdad 🟠 [V5-F6]

- Vista **calendario mensual** (rejilla, puntos/chips por evento con color de banda `bandColor`) +
  debajo **vista semanal** (lista por día con horas). TODO lo que tenga fecha/hora aparece:
  eventos de todas las bandas, propuestas pendientes (§9.5), fechas de notas de pizarra (§9.3).
- **Contrato tipado**: `/me/events` evoluciona a items `{kind: 'event'|'proposal'|'note'|'checklist',
  id, band_id, title, date, status…}`. En F6 solo emite `kind='event'`; F9 AÑADE `proposal`
  (eventos `status='proposed'` de tus bandas) y `note` (`BandNote` con `due_date` sin `done_at`);
  F10 añade `checklist`. **`bf-calendar` se escribe desde F6 contra ese contrato** (estilo
  fantasma para `proposal`, punto secundario para `note`) → F9/F10 no tocan el componente. Mismo
  contrato para la agenda de banda filtrada por `band_id`. Componente `bf-calendar` reutilizable —
  **el mismo se usa en la agenda de banda (§9.5) y en el Resumen (§9.6)**. Sin dependencias
  externas (nada de FullCalendar; rejilla CSS propia con los tokens).
- La lista actual no se tira: es la vista "Próximos" (toggle Lista/Calendario, persistido).

---

## 8. Chat — reestructura (lo más delicado según Oscar) 🟠 [V5-F7]

- **✅ CERRADO (2026-07-05): dos grandes grupos, CLAROS y visibles** en la página de Chat:
  **"Mis bandas"** y **"Otros contactos"**. Aclaración de Oscar: como hay contactos dentro de tus
  bandas Y también contactas con músicos que buscan banda o que alquilan material, la separación
  tiene que verse clarísima — sección de mis bandas y sección de otros contactos. SIN
  sub-etiquetas extra dentro de "Otros contactos" (no hace falta música/otro-nivel).
- **Etiquetas de color**: cada conversación de banda con su `bandColor` (se distingue de un
  vistazo qué chat de qué banda usas); los contactos con avatar/color neutro de perfil.
- **"Otros contactos" = los DM internos** creados al "Contactar" desde Explorar (D-EXP-1 ✅:
  chat interno + WhatsApp opcional). Cada conversación enlaza al perfil del contacto y muestra
  el CONTEXTO de origen ("por tu anuncio de material: Ampli Fender", "sobre: buscáis bajista") —
  la primera línea del DM lleva ese contexto automático (§14, interconexión I-3).
- **Chat dentro de banda — ✅ D-CHT-1 CERRADA (2026-07-03):** el chat de banda VIVE en la
  sección Chat global (grupo "Mis bandas"); la pestaña Chat del espacio de banda se sustituye por
  un **atajo/preview** (último mensaje + "Ir al chat", como ya hace el Resumen). Un solo sitio
  donde hablar, cero duplicación de UI. Los hilos por evento siguen accesibles desde la agenda.
- **Modelo DM (nuevo)**: `Conversation(id, kind='dm', created_at)` + `ConversationMember(conversation_id,
  user_id)` (2 filas) + `DirectMessage(conversation_id, author_id, body, context_ref, created_at,
  deleted_at)` — o el equivalente mínimo que el implementador justifique. 🔐 Solo los 2 miembros
  leen/escriben (ajeno→404, test de aislamiento); XSS escapado; sin realtime en V5 (refresco
  periódico como el chat de banda, 6s).
- **Alcance de "DM base" (entra en V5-F4, rompe la circularidad F4→F5a→F7):** modelo de arriba +
  router (`POST /dm/{user_id}` crea-o-reabre, `GET/POST /dm/{conversation_id}/messages`) + en la
  página de Chat actual un grupo mínimo "Otros contactos" (lista plana + hilo, refresco 6 s, sin
  pulir). Con esto I-3 e I-13 quedan completos desde F4/F5a. **V5-F7 NO añade funcionalidad de
  DM**: reordena la página (grupos claros, colores de banda, preview en el espacio de banda).
- **Semántica del DM (I-3/I-13):** SIEMPRE 1 conversación por par de usuarios. Contactar de nuevo
  por otro origen NO crea conversación: reabre la existente e inserta un **mensaje-sistema de
  contexto** — por eso `context_ref` vive en el MENSAJE, no en la conversación. Formato JSON:
  `{kind: 'gear'|'opening'|'collab'|'profile'|'score', id, label}`; la UI pinta "(sobre: {label})"
  con enlace al detalle. El DM es INDEPENDIENTE de su origen: si el perfil pasa a `no_busco`, la
  pieza se retira o el anuncio se desactiva, la conversación NO se borra ni bloquea (solo deja de
  poder iniciarse desde Explorar); si `context_ref` apunta a algo retirado, se pinta el label sin
  enlace. Los tests de I-3 aseveran `kind`+`id`, no texto visible.
- `/me/conversations` (vista agregada actual) evoluciona para devolver AMBOS grupos ya separados.

---

## 9. Bandas — espacio de banda 2.0 🔴 [V5-F9, la sección más gorda]

### 9.1 Lista "Mis bandas"

- Pestañas/acciones: **Mis bandas** + botón/pestaña **"Unirme a banda"** que lleva a
  **Explorar>Bandas** (bandas que buscan músicos, §5.5 — interconexión I-10) y mantiene también
  el flujo de código de invitación actual — ambas puertas. Posición del botón: **libre** ("como
  quede mejor", Oscar 2026-07-05). Diseño de tarjetas más bonito (ya rico desde T-132; se
  repasa con la estética V5-F1).

### 9.2 Identidad de banda y miembros (✅ Storage listo; fotos hechas en T-V5-06)

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
- **Flujo nuevo de propuesta (I-15):** **cualquier miembro activo** crea el evento con
  `status='proposed'` (añadir a `EVENT_STATUSES` — ⚠️ OJO: existe el CheckConstraint
  `ck_events_status`; la migración debe RECREARLO con `render_as_batch`, NO es aditiva sin más) →
  los miembros marcan si les va bien (**la votación ES `EventAttendance` normal** — yes/no/maybe —
  sobre el `proposed`) → **solo un admin** confirma (`proposed→confirmed`) o descarta
  (`proposed→cancelled`; queda histórico). El autor puede editar/cancelar su propuesta mientras
  esté `proposed`. Las propuestas pendientes se ven en Resumen y en las agendas (banda + personal
  de cada miembro) con estilo "fantasma" (contrato `kind='proposal'` de §7).
  Tests: proponer→votar→confirmar→aparece sin estilo fantasma en `/me/events` de otro miembro;
  permisos: miembro no-admin crea propuesta OK pero NO puede confirmarla.

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

### 9.9 Anuncios de la banda ("buscamos músicos" + colaboraciones)

- El anuncio se **publica/edita desde la pestaña Ajustes** del espacio de banda, bloque
  "Anuncio: buscamos músicos" (el Resumen §9.6 solo lo MUESTRA con enlace a Ajustes — sin
  alterar los 4 bloques literales de Oscar). Solo admin (D-BND-1 ✅).
- Los anuncios **NO caducan** en V5 (se desactivan a mano); la tarjeta en Explorar muestra
  "hace X días" con el `updated_at`. Orden en Explorar>Bandas: `updated_at` del anuncio desc.
  (Orden en Explorar>Músicos: `updated_at` de `musician_profiles` desc.)
- **Cierre del círculo "unirse" (I-16b):** en un DM originado por un anuncio de banda, el admin
  tiene botón **"Invitar a la banda"** que genera el `BandInvite` existente → membresía.
  Test de flujo: anuncio → DM → invitación → miembro.

---

## 10. Conciertos (antes "Giras") — organiza tu concierto 🟠 [V5-F10]

- Reenfoque de Oscar: antes que giras completas, **ayudar a organizar UN concierto**. Un asistente
  guiado ("Organiza tu concierto") que va preguntando: ¿en qué sala tocaréis o queréis tocar?
  ¿qué condiciones piden/pedís (caché, entrada, %)? ¿quién pone el material/backline? ¿cómo movéis
  los instrumentos? ¿horarios (prueba de sonido, apertura)? → genera el `Event(type=concert)` con
  **checklist** por concierto (`EventChecklistItem`: ítem, responsable, hecho, `due_date`
  DateTime NULL — si tiene fecha aparece en el calendario vía I-8, contrato de §7) + resumen
  imprimible.
- Aporta valor real: la checklist y el reparto de responsabilidades es lo que las bandas llevan en
  notas sueltas. Se cruza con Salas (`Venue`, ya existe), booking pipeline (ya existe), pizarra
  (§9.3) y finanzas del evento (caché ya existe en T-115).
- **Giras** (agrupar varios conciertos, ya hay modelos `Tour/TourStop` de V3-F5) se re-presentan
  DESPUÉS encima de esto, como "varios conciertos encadenados + presupuesto".

---

## 11. Finanzas — integral, AL FINAL (instrucción explícita de Oscar) [V5-F11]

No se pule hasta tener el resto (necesita el contexto de material prestado, conciertos, pizarra…).

**✅ Esquema CERRADO (Oscar, 2026-07-05):** "Finanzas recoge TODO el movimiento económico dentro
de la app y te da un **resumen de todo**", dividido en:

1. **Resumen global** (arriba): tu posición total de un vistazo — suma de saldos con todas las
   bandas + estado de tu material (alquilado/prestado) + últimos movimientos.
2. **Bandas**: eliges una banda → **quién debe dinero a quién** (los balances por banda ya
   existentes, mejor presentados) **✅ D-FIN-1 (2026-07-05): CON desglose por evento/bolo**
   además del total (los movimientos ya se ligan a eventos T-108 → se agrupan: "quién debe a
   quién del concierto X"). Gastos del grupo: generales **mensuales** (local de ensayo…) y
   **puntuales**.
3. **Personal**: el **material** — **✅ D-FIN-2 (2026-07-05): en AMBAS direcciones** — lo tuyo
   prestado/alquilado a otros (sale solo de `GearLoan`, §5.4) Y lo que TÚ tienes alquilado de
   otros (aparece automáticamente cuando el dueño te marca como prestatario en la app:
   `GearLoan.borrower_user_id` = tú → la misma tabla sirve las dos caras) + **lo que has pagado
   o te han pagado** + "hay que ver qué más" (se completa en su fase con todo el contexto).

Estudio completo al llegar aquí (Oscar: pensar TODO lo que una banda gasta). Con calendario de
pagos recurrentes si encaja (cruza con Agenda §7 si tiene fechas).

---

## 12. Orden de fases V5 y dependencias

| Fase | Qué | Depende de |
|---|---|---|
| **V5-F1** 🔴 | Estética global (§2.3: bugs → emoji → componentes → tema → detalles) | — |
| **V5-F2** 🔴 | Reproductor (§3: datos 4-negras + ×½/×2, countdown, compases metrónomo, tempo hold, compás display; OCR como beta al final) | F1 |
| **V5-F3** 🟠 | Afinador/Metrónomo sección (§4, extrae `metronome.js` de F2) | F2 |
| **V5-F4** 🔴 | Perfil 2.0 (§5.2: estado busco_banda/abierto/no_busco, instrumentos/banda, visibility, DM base) | decisiones ✅ cerradas 2026-07-05 |
| **V5-F5** 🔴 | Explorar 5 pestañas (§5.1 ✅: a Músicos, b Descubrir, c **Mi material**+Material, d Bandas [buscan músicos+colaboraciones]) | F4 (Storage ✅ listo) |
| **V5-F6** 🟠 | Agenda calendario mensual+semanal (§7, componente `bf-calendar`) | F1 |
| **V5-F7** 🟠 | Chat 2.0 (§8 ✅: grupos "Mis bandas"/"Otros contactos", etiquetas color, DM interno) | F4/F5a |
| **V5-F8a** 🟠 | Biblioteca por carpetas (§6 ✅: Personales+carpetas, Mis setlists, Setlists abiertos, añadir) | — (puede adelantarse) |
| **V5-F8b** 🟠 | Selector de carpeta al "Guardar" desde Explorar (I-5) | F5 |
| **V5-F9** 🔴 | Bandas 2.0 (§9: pizarra, estado repertorio, propuestas, resumen nuevo, identidad 🔌) | F1, F6 (calendario) |
| **V5-F10** 🟠 | Conciertos wizard (§10) | F9 |
| **V5-F11** 🟠 | Finanzas integral (§11) | TODO lo anterior (orden de Oscar) |
| Transversal ✅ | **Storage** CONFIGURADO (2026-07-03) — fotos de perfil/banda hechas (T-V5-06); material usa el mismo `upload.js` | — |

> El orden F6-F9 es ajustable con Oscar al cerrar cada sección; F1→F2→F3 y F11-último son fijos.

---

## 13. Registro de decisiones por sección (se rellena al ir hablando)

| Fecha | Sección | Decisión | Detalle |
|---|---|---|---|
| 2026-07-03 | Global | V5 abierta; método sección-a-sección | Este documento |
| 2026-07-03 | §2 | **D-EST-1 ✅** pulir la identidad actual (no rediseño de marca) | oscuro+coral+IBM Plex a fondo |
| 2026-07-03 | §2 | **D-EST-2 ✅** player siempre oscuro (modo escenario) | editor/join sí siguen el tema |
| 2026-07-03 | §2 | **D-EST-3 ✅** Storage se configura ya (Oscar guiado) | bucket + políticas → desbloquea fotos |
| 2026-07-03 | §8 | **D-CHT-1 ✅** chat de banda = atajo al Chat global | pestaña de banda pasa a preview |
| 2026-07-03 | §2 | **Storage configurado + T-V5-06 HECHO** | bucket `media` + RLS por Oscar; fotos de perfil/logo/fondo implementadas (detalle en REGISTRO) |
| 2026-07-03 | §3 | **D-PLY-1 ✅** ×½/×2 por acorde **+ tap tempo** por acorde | ambos escriben beats del ChordMarker (motor intacto) |
| 2026-07-03 | §3 | **D-PLY-2 ✅** la cuenta atrás suena **solo si el metrónomo está activado** | con metrónomo off = pre-roll solo visual; N (4/8) en localStorage |
| 2026-07-03 | §3 | **D-PLY-3 ✅** foto→partitura **beta con modelo gratuito** de visión | coste 0, patrón de import por URL; empezar con foto clara |
| 2026-07-03 | §3 | **Metrónomo 6/8 ✅ subdividido** (T-V5-07) | 6 clics/compás: acento fuerte en el 1, medio en el 4 (no "en 2") |
| 2026-07-03 | §5 | D-EXP-1/2/3/4 abiertas al crear la guía — **SUPERADA**: todas cerradas el 2026-07-05 (ver filas de esa fecha) | **Inventario vivo de abiertas: solo D-BND-2** (¿1 anuncio máx por banda? — bloquea únicamente T-V5-26) |
| 2026-07-05 | §3 | **Ruleta de tempo DESCARTADA** ("no importa, déjalo") | el press-and-hold (T-V5-09, hecho) cumple; la ruleta no se construye |
| 2026-07-05 | §3 | **Compases atípicos descartados de momento** ("olvida esto") | solo 2/4 · 3/4 · 4/4 · 6/8 |
| 2026-07-05 | §5 | **Explorar reestructurado** (palabras de Oscar): subsecciones **Buscar músicos** (perfiles que han puesto que buscan banda) · **Buscar banda** (NUEVA: bandas que buscan uno o varios músicos, y qué tipo de músico) · **Material** (alquilar/prestar) [SUPERSEDIDA por D-EXP-4 en esta misma tabla: estructura final de 5 pestañas en §5.1] | + **nueva sección personal "Mi material"**: subes el material del que dispones con foto (amplis, micros, lo que sea) y desde ahí se publica a alquiler/préstamo → aparece en Explorar>Material. Definir lista y filtros (§14) |
| 2026-07-05 | §6 | **Biblioteca por CARPETAS**: (1) Personales — todas las guardadas y tuyas, divisibles en **carpetas libres** que el usuario crea y nombra como quiera; (2) **Setlists abiertos** — los setlists de cada banda activa que tengas; (3) botón **"Añadir nueva"** (carpeta) | reemplaza el esquema anterior "Mis canciones/Mis contactos/Guardados" |
| 2026-07-05 | §8 | **Chat: dos grupos CLAROS y visibles — "Mis bandas" y "Otros contactos"** | otros contactos = músicos contactados vía Explorar (buscar banda/músicos, material). SIN sub-etiquetas música/otro-nivel: la separación que pedía Oscar es bandas vs. resto |
| 2026-07-05 | §9 | "Unirme a banda": **posición libre** ("como quede mejor") | se decide en diseño |
| 2026-07-05 | §11 | **Finanzas = TODO el movimiento económico de la app + resumen global**, dividida en: **Bandas** (eliges banda → quién debe a quién dentro de cada proyecto) y **Personal** (material alquilado, lo pagado/cobrado; resto por definir en su fase) | sigue siendo AL FINAL |
| 2026-07-05 | Global | **MODO GUÍA (orden de Oscar): parar de programar** y dedicar el esfuerzo EXCLUSIVAMENTE a esta guía: hiperdetallada, con el contexto de toda la app y las **interconexiones entre secciones** (§14 nueva) | "que cualquier IA pueda programar algo que todo tenga sentido" |
| 2026-07-05 | §5 | **D-EXP-4 ✅ Explorar = 5 pestañas: Músicos · Bandas · Material · Canciones · Descubrir** | Colaboraciones NO es pestaña propia: se FUSIONA dentro de "Bandas" (anuncios de banda: buscamos músico / buscamos telonera / compartir cartel…) |
| 2026-07-05 | §5 | **"Mi material" = item propio en el menú lateral** ("sí, pero piensa bien que tenga todo sentido") | validar coherencia total en §14: enlaces con Explorar>Material, Finanzas>Personal y Perfil |
| 2026-07-05 | §5/§8 | **D-EXP-1 ✅ Contacto = chat interno + WhatsApp opcional** | "Contactar" abre DM interno (alimenta Chat>Otros contactos); botón WhatsApp SOLO si el perfil añade teléfono y lo activa. Privacidad por defecto |
| 2026-07-05 | §5 | **D-EXP-2 ✅ Estados del músico: `busco_banda` · `abierto` · `no_busco`** | "busco músicos" deja de ser estado personal → es el ANUNCIO de la banda (pestaña Bandas de Explorar, §5.5). Sin "disponible para bolos" de momento |
| 2026-07-05 | §6/§8 | **D-BIB-1 ✅ Los contactos viven SOLO en Chat>Otros contactos** | la Biblioteca queda solo para música (carpetas + setlists abiertos); sin carpeta "Mis contactos" |
| 2026-07-05 | §6 | **D-BIB-2 ✅ Setlists abiertos = solo ver y ▶ tocar** | editar se queda en el espacio de banda (una sola fuente de edición, regla §14.2.3) |
| 2026-07-05 | §5/§9 | **D-BND-1 ✅ Solo el ADMIN publica/edita/desactiva el anuncio "buscamos músico"** | igual que las colaboraciones (publica admin en nombre de la banda) |
| 2026-07-05 | §11 | **D-FIN-1 ✅ Finanzas>Bandas con desglose POR EVENTO además del total de banda** | "quién debe a quién" de la banda + agrupable por evento/bolo (los movimientos ya se ligan a eventos, T-108) |
| 2026-07-05 | §5 | **D-EXP-3 ✅ Zona = texto libre** ("Murcia", "Madrid sur") | filtro por `contains` case-insensitive; sin geocoding. Estructurar más = iteración futura |
| 2026-07-05 | §6 | **D-BIB-3 ✅ Los setlists personales = bloque propio "Mis setlists"** en la Biblioteca | se crean/editan ahí como hasta ahora; NO se fusionan con las carpetas |
| 2026-07-05 | §11 | **D-FIN-2 ✅ Material en Finanzas>Personal en AMBAS direcciones** | lo tuyo prestado a otros + lo que tú tienes alquilado de otros (automático vía `GearLoan.borrower_user_id`) |
| 2026-07-05 | Global | **Verificación adversarial de la guía aplicada** (3 lentes: fidelidad, coherencia, "IA menos capaz" — 23 arreglos) | Storage ya-no-bloqueado ×4, regla 7 granular, DM base en F4, máquina de estados del material + `GearLoan`, wa.me solo en detalle con opt-in, plan de tareas §5.8, contrato tipado del calendario, I-15/I-16, §9.9 anuncios |

> **Estado:** V5 abierta y primera ronda de decisiones CERRADA (2026-07-03). **V5-F1 (estética)
> desbloqueada y lista para arrancar** por el bucle de oro; en paralelo, Oscar configura Supabase
> Storage (guiado) para desbloquear T-V5-06/identidad.
> **2026-07-05:** V5-F1/F2(-T-V5-10)/F3 COMPLETAS y en prod. Segunda ronda de decisiones cerrada
> (Explorar 5 pestañas, Mi material, contacto, estados, Biblioteca carpetas, Chat 2 grupos,
> Finanzas). **MODO GUÍA activo**: se detiene el desarrollo para hiperdetallar esta guía (§14).

---

## 14. Mapa de interconexiones — cómo se conecta todo (Oscar, 2026-07-05)

> Oscar: "si tengo un producto en mis materiales tiene que tener un botón de ponerlo a alquilar,
> y si se da a ese botón tiene que entrar en la lista de explorar de alquiler de materiales…
> todo este tipo de interconexiones tienen que estar bien hechas y ser coherentes".
> Esta sección es EL CONTRATO de coherencia: cada flujo se implementa entero o no se implementa
> (nunca a medias), y al cerrar una sección se repasan los flujos que la tocan (§0.1 regla 8).

### 14.1 Los flujos, uno a uno

**I-1 · Perfil → Explorar>Músicos**
`MusicianProfile.estado` = `busco_banda`|`abierto` → el perfil APARECE en Explorar>Músicos (con
proyección segura); `no_busco` → desaparece. El estado se cambia SOLO en Perfil (§5.2). No hay
"publicarse" desde Explorar. Efecto colateral: el badge de estado se ve también en el perfil
público. Test de flujo: cambiar estado → aparece/desaparece de `/explore/musicians`.

**I-2 · Espacio de banda → Explorar>Bandas**
El admin activa el anuncio "buscamos músico(s)" (instrumentos+texto) en **Ajustes de banda
(§9.9)** → la banda APARECE en Explorar>Bandas (orden: `updated_at` desc); al desactivar,
desaparece. Las colaboraciones (`CollabPost`) siguen el mismo patrón (publica admin → aparece
con badge "Colaboración"). El círculo se cierra con I-16b (invitar desde el DM).
Test de flujo: activar → listada; desactivar → fuera.

**I-3 · Explorar (cualquier pestaña) → Chat>Otros contactos**
Botón "Contactar" (en músico, banda o material) → crea/abre un **DM interno** con
`context_ref` del origen ("sobre: Ampli Fender", "sobre: buscáis bajista") → la conversación
queda en Chat>"Otros contactos" para AMBOS. Si el destinatario activó WhatsApp, botón wa.me
adicional (no sustituye el DM). Regla: TODO contacto de la red pasa por aquí — no se inventan
otros canales por pestaña. Test de flujo: contactar desde material → DM con contexto visible
para los dos.

**I-4 · Mi material → Explorar>Material → Finanzas>Personal** (el ejemplo canónico de Oscar)
(1) Subes pieza en **Mi material** (foto opcional + datos; `is_listed=false`). (2) Botón "Poner a
alquilar/prestar" (+precio/gratis/fianza) → `is_listed=true` → APARECE en Explorar>Material con
los filtros de §5.4(b). (3) Alguien contacta → I-3 (DM con contexto de la pieza). (4) Si la
prestas/alquilas → "Marcar prestada" crea una fila **`GearLoan`** (a quién — usuario de la app o
texto libre —, desde cuándo, precio) y por defecto la des-lista (checkbox "mantener anunciada"
para alquiler recurrente). (5) "Marcar devuelta" → `GearLoan.ended_at`, la pieza conserva su
`is_listed`. (6) **Finanzas>Personal (§11.3) LEE de `GearLoan`** — ambas direcciones (D-FIN-2):
lo tuyo prestado y lo que tú tienes de otros (`borrower_user_id` = tú). (7) "Retirar" →
`is_listed=false`, fuera de Explorar; la pieza y su histórico de préstamos se conservan.
La lista de Explorar SOLO tiene piezas `is_listed`. Test de flujo completo (incluida la
devolución): subir→publicar→listada→prestar→en finanzas→devolver→retirar→fuera.
El perfil público del dueño lista sus piezas `is_listed` (§5.2) — enlace bidireccional.

**I-5 · Explorar>Canciones / Descubrir → Biblioteca (carpetas)**
"Guardar" una partitura pública u original → copia personal en **Biblioteca>Personales**, con
selector de carpeta al guardar (o raíz). La copia es editable sin tocar el original (patrón
V3-F9 ya existente). Test: guardar → aparece en la carpeta elegida.

**I-6 · Repertorio de banda → Explorar>Descubrir**
La banda publica un original desde su repertorio (§9.4) → aparece en Descubrir y en su página
pública de banda. Se publica desde el repertorio, NUNCA desde Explorar (regla §5.1).

**I-7 · Setlists de banda → Biblioteca>Setlists abiertos**
Automático: ser **miembro activo** de una banda hace que sus setlists aparezcan en
Biblioteca>"Setlists abiertos" (solo ver/▶ tocar, D-BIB-2). Darse de baja de la banda → sus
setlists desaparecen. Test de aislamiento específico (§6).

**I-8 · Pizarra / Propuestas / Checklist → Agenda (calendario)**
TODO lo que tenga fecha aparece en el calendario (§7): eventos confirmados, **propuestas de
evento** (§9.5, estilo "fantasma" hasta confirmarse), **notas de pizarra con due_date** (§9.3)
y (cuando exista) ítems de checklist de concierto con fecha (§10). Un solo componente
`bf-calendar` para agenda personal, agenda de banda y Resumen.

**I-9 · Conciertos (wizard) → Evento + Checklist + Finanzas de banda**
El asistente "Organiza tu concierto" (§10) genera `Event(type=concert)` + checklist con
responsables; el caché/costes del evento alimentan Finanzas>Bandas (los movimientos ya se ligan
a eventos, T-108). El pipeline de booking existente es el estado del evento.

**I-10 · Bandas>"Unirme a banda" → Explorar>Bandas**
La pestaña/botón "Unirme a banda" de §9.1 lleva a **Explorar>Bandas** (bandas que buscan gente)
además de mantener el flujo por código de invitación. Es la MISMA lista de I-2, no una copia.

**I-11 · Foto→partitura (una sola función, tres puertas)**
`POST /import/photo` (T-V5-11, hecho) se usa desde: el editor personal (hecho), "crear canción"
del repertorio de banda (§9.4) y donde el wizard/checklist lo pida. Una única implementación.

**I-12 · Afinador/Metrónomo compartido (patrón de referencia, HECHO)**
`metronome.js` = una sola fuente de clic/acento para player y sección (T-V5-12/13/14). Este es
el patrón a imitar en todo lo compartido (calendario `bf-calendar`, upload `upload.js`,
avatares `bfAvatar`).

**I-13 · Chat>Otros contactos → Perfil**
Cada DM enlaza al perfil del contacto (y desde el perfil se reabre el DM existente — no se
duplican conversaciones: 1 conversación por par de usuarios).

**I-14 · Estado del repertorio → Resumen de banda**
`SongStatus` por miembro (§9.4, privado por defecto) alimenta el diagrama del Resumen (§9.6):
el tuyo siempre; el de la banda solo con los compartidos.

**I-15 · Propuesta de evento → votación → calendario oficial**
Disparador: un miembro activo crea `Event(status='proposed')` (§9.5). Efecto: aparece en estilo
"fantasma" en la agenda de banda, en la personal de cada miembro (`kind='proposal'`, §7) y en el
Resumen; los miembros votan con `EventAttendance` (yes/no/maybe). Cierre: un admin confirma
(`→confirmed`, entra al calendario oficial) o descarta (`→cancelled`, queda histórico).
Test de flujo: proponer→votar→confirmar→visible sin fantasma en `/me/events` de otro miembro.

**I-16 · Página pública de banda (el escaparate exterior)**
`GET /public/bands/{id}` + `banda.html` sin login (§5.6): nombre, foto/cover, bio, originales
(Descubrir), próximos conciertos public/unlisted con RSVP, anuncio activo (§9.9), Contactar→I-3.
Se llega desde: Descubrir (cada original enlaza a su banda), Explorar>Bandas (la tarjeta del
anuncio) y los chips "en {banda}" de perfiles (solo bandas con presencia pública, §5.2).
**I-16b · Cierre del círculo "unirse":** en un DM originado por anuncio de banda, el admin tiene
botón "Invitar a la banda" → `BandInvite` existente → membresía. Test: anuncio→DM→invitación→miembro.

### 14.2 Reglas transversales de coherencia (para la IA ejecutora)

1. **Se publica desde lo propio, se descubre en Explorar** (perfil→Músicos, banda→Bandas,
   Mi material→Material, repertorio→Descubrir). Explorar no tiene botones de "crear".
2. **Todo contacto acaba en el MISMO sitio**: DM interno con contexto (I-3). WhatsApp es un
   extra opt-in, nunca el canal primario.
3. **Una sola fuente de edición por cosa** (setlists se editan en banda; originales en el
   repertorio; el guardado de Biblioteca es copia personal editable).
4. **Todo lo que tenga fecha aparece en el calendario** (I-8), con el mismo componente.
5. **Módulos compartidos, no duplicados** (I-11/I-12): si dos sitios hacen lo mismo, se extrae.
6. **Proyección segura en TODO lo público** + test de no-fuga por pestaña de Explorar.
7. **Cada flujo I-N se implementa completo** (con su test de flujo end-to-end) o se aparca
   completo. Nunca "la mitad del flujo". Convención: cada flujo tiene UN e2e
   `tests/e2e/test_flow_iNN_*.py`, escrito en la ÚLTIMA tarea que completa el flujo y requisito
   de cierre de esa tarea (paso 5 del bucle); la sección no se cierra sin todos sus I-N en verde.

### 14.3 Cambios en el menú lateral (consecuencia de lo anterior)

Lateral queda: Inicio · Afinador/Metrónomo · Explorar · Biblioteca · **Mi material** (nuevo,
§5.4a) · Agenda · Finanzas · Chat · Bandas · Perfil. (Posición exacta de "Mi material" a decidir
en diseño — cerca de Biblioteca por afinidad "cosas mías". Si el lateral se siente largo en
móvil, propuesta alternativa: Mi material como pestaña dentro de Biblioteca — PREGUNTAR a Oscar
solo si el diseño lo pide.)
