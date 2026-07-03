# 📋 ChordFlow — Registro de Cambios (Bitácora de desarrollo)

> Documento vivo. Registra **qué** se hizo, **por qué** y **cómo** (archivos tocados y verificación).
> Para el contexto general del proyecto, ver [GUIA_MAESTRA.md](GUIA_MAESTRA.md).
> Última actualización: 2026-07-03

Leyenda de estado: ✅ hecho y verificado · 🟡 en curso · ⏳ pendiente

---

## 🎨 V5-F1 · T-V5-04/05 — Tema coherente + convergencia de botones + detalles (2026-07-03) ✅ · CIERRA V5-F1

**Qué (T-V5-04, tema coherente):**
1. **`theme.js` nuevo** ([static/theme.js](static/theme.js)): aplica `data-theme` desde la misma clave
   `localStorage['bf-theme']` que usa el shell, en `editor.html` y `join.html` (que no llevan lateral
   pero SÍ deben respetar el tema). Va en `<head>` para evitar el parpadeo. El **reproductor**
   (`index.html`) NO lo carga a propósito → SIEMPRE oscuro (decisión **D-EST-2**, "modo escenario");
   se documenta con un comentario en su `<head>`.
2. **Fondos legacy tokenizados** ([style.css](static/style.css)): `--bg-panel` con override claro
   (`:root[data-theme="light"]`) para que el cristal de la top-bar se aclare; `.editor-content`,
   `.input-group input/textarea` y `.editor-split textarea` pasan de `rgba(0,0,0,.5)`/`rgba(20,20,25,.8)`
   **fijos** a `var(--bf-surface)`/`var(--bf-surface-2)` → el editor es **legible en claro** (antes:
   texto casi-negro sobre caja negra = invisible). `.ev-status--confirmed/--cancelled` a
   `--bf-success`/`--bf-danger`; `.icon-btn` sin subrayado de enlace.
3. **Convergencia de botones legacy**: `.primary-btn`/`.secondary-btn` adoptan el look de `.bf-btn`
   (radio, padding, tokens) SOLO bajo `body.bf-legacy-themed` (editor/join). El reproductor comparte
   esas clases para la joya y NO lleva la clase → **intacto**.

**Qué (T-V5-05, detalles):**
- **Chat**: avatar de conversación coloreado por banda (`bandColor` + iniciales), como el lateral
  ([chat.js](static/chat.js)).
- **Editor**: resultados de importación **focables por teclado** con patrón `listbox`/`option`
  (`tabindex`/`role`/`aria-selected`) + activación con Enter/Espacio + foco visible; input de búsqueda
  a lo ancho en móvil; ❌ cancelar como icono SVG ([editor.js](static/editor.js), [editor.html](static/editor.html)).
- **Afinador**: aguja **atenuada en reposo** (`#tuner-panel.tuner-live` la enciende al escuchar), tarjeta
  centrada, copy sin redundancia con el botón ([tuner.js](static/tuner.js), [afinador.html](static/afinador.html)).
- **evento.html público**: **CTA** claro de registro ("Organízalo con BandFlow — gratis") en ambos
  estados ([evento.js](static/evento.js)). Hint de pestañas de banda actualizado (Miembros/Giras)
  ([band.js](static/band.js)). `<h1>` estático en Inicio/Agenda/Finanzas/Chat (accesibilidad).

**Por qué:** cierre de V5-F1 (`GUIA_MAESTRA_V5.md` §2.3–2.4): "un solo sistema" + "un tema por contexto"
(app claro/oscuro; player siempre oscuro).

**Verificación:** `run_checks` **TODO VERDE** (doctor 10/10 · ruff · unit + e2e). Tests nuevos:
`test_tema_coherente.py` (editor/join aplican tema, **player siempre oscuro**, inputs legibles en claro,
botones convergen solo en editor, ev-status tokenizado), `test_detalles_pulido.py` (avatar chat,
listbox focable + Enter, aguja idle, CTA de evento) y `test_accesibilidad_h1.py`. **Revisión adversarial
multi-agente** (9 agentes) del diff → 3 hallazgos: los 2 de tema (inputs/panel del editor ilegibles en
claro) se detectaron ya en la **verificación visual con el navegador** y se arreglaron antes del cierre;
el 3º (a11y: `role=button` rompía la semántica de lista) resuelto con `listbox`/`option`. Verificado a
ojo en el navegador: editor claro/oscuro coherente, afinador centrado, CTA de evento, avatar de chat.
`cachebust` al día. Sin migración.

---

## 🎨 V5-F1 · T-V5-03 — Unificar tarjetas y grids con el sistema nuevo (2026-07-03) ✅

**Qué:** las tarjetas de las listas legacy (`.song-card` — Biblioteca, Bandas, Explorar) tenían un
look distinto al del resto de la app (`.bf-card`): radio 12 vs 16px, padding 1.2 vs 1.5rem, sin
sombra base, y un "lift" de -3 vs -2px al pasar el ratón. Se notaba al saltar de una sección a otra.
Ahora `.song-card` usa **los mismos tokens** que `.bf-card` (`--bf-radius-lg`, `--bf-space-5`,
`--bf-shadow-sm`, hover `translateY(-2px)` + `--bf-shadow`) conservando su layout (columna,
min-height, franja de color por fuente) y el borde de acento al hover (refuerza que abre el player).
`.song-grid` alinea su `gap` a `--bf-space-4` (como `.bf-grid`).

**Por qué:** V5-F1 §2.3 — "la consistencia ES la profesionalidad". Un solo lenguaje de tarjeta.

**Verificación:** en el navegador, `.song-card` computa radio 16px, padding 24px, sombra del token
y el grid gap 16px (idénticos a `.bf-card`/`.bf-grid`), en claro y oscuro, sin errores de consola.
`run_checks` TODO VERDE. `cachebust` al día. Sin migración.

> **Botones legacy** (`.primary-btn`/`.secondary-btn`): NO se tocan aquí porque el **reproductor**
> los comparte (riesgo para la joya). Su convergencia se hará en T-V5-04 al pulir editor/login,
> con overrides por página que no afecten a las clases compartidas del player.

---

## 🎨 V5-F1 · T-V5-01 — Bugs visibles de estética (2026-07-03) ✅

**Qué:** arreglados los dos bugs visibles que quedaban del repaso de diseño (el tercero,
`initialsFrom` "O(", ya cayó con T-V5-06):
1. **Buscador ilegible en modo claro.** `.search-box` ([style.css](static/style.css)) tenía
   `background: rgba(0,0,0,0.5)` **hardcodeado** → en tema claro quedaba una barra casi-negra con
   texto oscuro (invisible). Ahora hereda `--bf-surface-2`/`--bf-border`/`--bf-accent-glow` del
   design-system (funciona en claro y oscuro) + `::placeholder` tokenizado.
2. **Texto interno de desarrollo visible al usuario.** Quitado el "(T-091)" del copy de
   [afinador.html](static/afinador.html).

**Por qué:** primer paso de V5-F1 (estética profesional, `GUIA_MAESTRA_V5.md` §2.3): los bugs
visibles primero, antes del barrido de iconos y la unificación de componentes.

**Verificación:** e2e `test_buscador_biblioteca_legible_en_claro` ([test_modo_claro_legacy.py](tests/e2e/test_modo_claro_legacy.py))
— el fondo del buscador adapta al tema y su suma RGB en claro es alta (no la barra negra de antes) +
verificado en el navegador (fondo `rgb(250,250,248)` con texto oscuro en claro, `rgb(28,28,35)` con
texto claro en oscuro). `run_checks` TODO VERDE. `cachebust` al día. Sin migración.

---

## 🎨 V5-F1 · T-V5-02 — Barrido de emojis-icono → SVG (2026-07-03) ✅

**Qué:** los emojis usados como **icono de botón/acción** se sustituyen por iconos SVG (`bfIcon`),
para un lenguaje visual único y profesional. Los emojis que son **contenido** (tipos de evento en
la agenda, chips de estado ⏰/🔗, mensajes de chat, decoración de `<h1>`, opciones de `<select>`
que no admiten SVG) se conservan.

**Cómo:**
- **Helper declarativo nuevo `bfApplyIcons()`** en [icons.js](static/icons.js): cualquier elemento
  con `data-icon="nombre"` recibe el SVG al principio, al cargar el DOM (idempotente). Así los
  botones **estáticos** en HTML no necesitan tocar el JS de su página. Icono `link` añadido a `PATHS`.
- **Botones estáticos** (`data-icon`): "Nueva banda" ([bands.html](static/bands.html)), "Setlists"/
  "Nueva partitura" ([library.html](static/library.html)), "Nuevo setlist" ([setlists.html](static/setlists.html)),
  "Guardar y Reproducir" ([editor.html](static/editor.html)), botón "Mis bandas" de
  [join.html](static/join.html) (que además ahora carga `icons.js` + `design-system.css`).
- **Botones generados por JS** (`bfIcon(...)`): Invitar 🔗→link, Nueva colección/setlist/evento/sala/
  gira/movimiento/"Copiar de mis partituras" ➕→plus, Borrar banda 🗑️→trash, Liquidar 💸→wallet,
  Guardar/Crear setlist 💾→save, "Crear setlist con estas" 🎵→music ([band.js](static/band.js),
  [bands.js](static/bands.js)); accesos rápidos y "primeros pasos" del Inicio 🎸👥🌍📅💶→iconos
  ([home.js](static/home.js), `step()` reescrito); "Crear mi primera partitura" ➕ ([library.js](static/library.js));
  ▶ del overlay de la miniatura de YouTube ([editor.js](static/editor.js)) + "Guardar cambios".
- **Se dejan como están (justificado):** los emojis del reproductor (`index.html`) los sustituye
  `paintPlayerIcons()` en runtime (fallback progresivo, la guía dice no tocarlos); glifos
  tipográficos `♭ ♯ ◀ ▶ ← ⠿` (se leen mejor que un SVG); chips de estado y contenido de chat.

**Verificación:** verificado en el navegador (data-icon inyecta 1 SVG por botón, texto limpio sin
emoji, alineación por el `gap` de flex; sin errores de consola) + los e2e localizan por id/clase
(no por el emoji), así que siguen pasando. `run_checks` TODO VERDE. `cachebust` al día. Sin migración.

---

## 📸 V5 · T-V5-06 — Identidad con imágenes: foto de perfil + logo y fondo de banda (2026-07-03) ✅ (código) · ⏳ migración a prod

**Qué:** primeras IMÁGENES reales de la app (V5 §2.3-T-V5-06, tras configurar Oscar el bucket
`media` de Supabase Storage): **foto de perfil** (se ve en Mi perfil, en el lateral del shell y en
los miembros de banda), **logo de banda** (círculo del banner + tarjeta de "Mis bandas") e
**imagen de fondo** de la cabecera del espacio de banda (con velo oscuro para legibilidad).

**Por qué:** "sin fotos la app siempre parecerá una demo" (repaso 2026-07-02); Oscar pidió
explícitamente miembros con nombre+foto y fondo de banda (V5 §9.2). Storage quedó configurado por
Oscar (bucket `media` público en lectura; RLS: escribir solo en `/{uid}/...`).

**Cómo:**
- **Subida client-side** ([upload.js](static/upload.js) nuevo): redimensiona en canvas (512px
  avatares / 1600px fondos, JPEG 0.85), sube a `media/{uid}/{kind}-{ts}.jpg` con el JWT del usuario
  (cumple la RLS) y devuelve la URL pública. En modo test rechaza con mensaje claro (los tests
  cubren el contrato de la URL, no la subida).
- **Backend:** columna nueva `Band.cover_url` (migración aditiva `37fb00af7e5c`, batch;
  `alembic check` limpio) + `cover_url` en `BandUpdate/BandResponse` + `avatar_url` del músico en
  `GET /bands/{id}/members` (mismo outerjoin, sin N+1). **Validador `_validate_image_url`** en las
  ENTRADAS (perfil y banda): https obligatorio y sin `"' \\()<>` → una URL guardada jamás puede
  escapar de un `src="…"` ni de un `url("…")` en CSS (defensa XSS/CSS-injection); `""` → NULL.
- **Frontend:** helper único `bfAvatar()` en [util.js](static/util.js) (foto si hay URL; si no,
  iniciales+color — usado por perfil, banner, miembros y tarjetas de banda). De regalo, **fix del
  repaso**: `initialsFrom('Oscar (tú)')` ahora da "O", no "O(" (filtra palabras que no empiezan por
  letra/número). Botones "Añadir/Cambiar foto" en el perfil y "Subir logo / Subir fondo" en
  Ajustes de banda (solo admin). CSS `.bf-avatar__img` + `.bf-band-banner--cover` (velo).

**Verificación:** unit [test_identidad_imagenes.py](tests/unit/test_identidad_imagenes.py) (cover
por admin, aislamiento ajeno→403/404, 4 URLs maliciosas→422, avatar en miembros, ""→NULL) + e2e
[test_identidad_imagenes.py](tests/e2e/test_identidad_imagenes.py) (foto en perfil+lateral, banner
con logo y fondo `--cover`, miembros con cara, iniciales sin paréntesis) + verificación visual en
el preview (banner con velo y nombre en blanco legible, miembros mixtos foto/iniciales).
`run_checks` TODO VERDE. `cachebust` al día.

> ✅ **Migración `37fb00af7e5c` APLICADA a Postgres prod** (2026-07-03, pooler 5432; `alembic
> current` = head). Nota de la sesión: un agente de revisión hizo `git stash` del working tree a
> mitad de suite (fallos "imposibles" en tests ajenos); recuperado con `git stash pop` y suite
> TODO VERDE después. Lección registrada en memoria: commitear antes de lanzar workflows.
>
> **Fix post-revisión adversarial (1 hallazgo confirmado):** recomprimir a JPEG aplastaba la
> transparencia a NEGRO (logos PNG típicos) → `upload.js` ahora exporta PNG cuando el original
> tiene alfa (PNG/WebP/GIF/SVG) y JPEG solo para fotos; extensión y contentType acordes.

---

## 🕷️ T-163 — Buscar e importar SIN IA para CifraClub/LaCuerda (2026-07-02) ✅

**Qué:** T-162 (buscar por nombre) y el import por URL (T-045) llamaban a OpenRouter en **cada**
búsqueda/import. Ahora, para CifraClub y LaCuerda, se extraen título/artista/acordes/letra con
**regex puro sobre el HTML crudo** — sin tocar el lector Jina ni el modelo. El flujo con IA queda
como **red de seguridad**: entra solo si el dominio no tiene parser propio, o si el parser no
encuentra nada fiable (sitio caído, cambio de estructura...).

**Por qué:** pedido directo de Oscar (2026-07-02) para "encontrar la manera que requiera menos IA
externa por API" — menos coste, menos latencia, menos dependencia de un servicio externo para dos
sitios que ya se usan constantemente. Antes de tocar código se **verificó a mano** (con `curl`)
la estructura real de ambos sitios en vez de asumir que un scraper "obvio" funcionaría:
- **CifraClub** es una Next.js app, pero tanto la búsqueda como la ficha de canción son HTML
  estático servido en la primera respuesta (nada de JS necesario). Los acordes van en
  `<b data-chord-name="Em7">` (atributo semántico, no una clase CSS hasheada — esas SÍ cambian en
  cada build suyo, se descartó anclar ahí) dentro de un `<pre>`, un `<div>` por línea separado por
  saltos de línea reales. Los resultados de búsqueda tienen un ancla muy estable: el `alt` de la
  carátula ("Portada de la canción "X", de Y").
- **LaCuerda: hallazgo real, no solo arquitectura.** Su buscador por defecto (`exp=` sin más)
  devuelve el conteo ("N resultados") pero la lista viene **vacía** — se carga por JS que ni el
  HTML crudo ni el lector Jina llegan a ejecutar/esperar. Con `canc=1&ord=0&ini=0` ("buscar en
  Canciones") SÍ llega la lista completa en HTML estático. El nombre de archivo real de cada
  canción va en el array `fns` embebido en la página, pero en **orden inverso** al de las filas/
  al array `hds` — verificado con una canción real (`acordes.lacuerda.net/suenio_inmoral/oasis`
  responde 200; emparejar por índice directo habría dado una URL rota). La ficha de canción de
  LaCuerda es HTML4 clásico, acordes en `<A>Am</A>` dentro de un `<pre>`, sin sorpresas.

**Cómo:** en [importer.py](src/services/importer.py): `_fetch_raw_html` (descarga simple, sin
Jina) + un parser por sitio (`_parse_cifraclub_search`/`_song`, `_parse_lacuerda_search`/`_song`)
+ registro `_SITE_ADAPTERS` por dominio (`_adapter_for_host`). `search_song()` prueba primero los
parsers propios de los dos dominios; si ninguno da resultados, cae a `_search_song_via_llm`
(la implementación de T-162, renombrada, intacta). `import_from_url()` prueba el parser propio del
dominio de la URL; si no hay adaptador o no extrae nada, cae al flujo `fetch_page_text`+
`extract_chords` de siempre (T-045, intacto). `_parse_cifraclub_search` además filtra por
relevancia (alguna palabra de la búsqueda en título/artista) porque esa página mezcla los
resultados reales con una barra de "tendencias" con el mismo marcado.

**Verificación:** unit en [test_import.py](tests/unit/test_import.py) — cada parser probado con
**fixtures HTML recortadas pero fieles** (fragmentos reales de las páginas, no inventados),
incluido el caso del orden invertido de `fns` con una URL real conocida, sitios con estructura
rota (longitudes que no cuadran → no arriesga un enlace equivocado), y que ni `search_song` ni
`import_from_url` llaman a la IA cuando el parser propio ya respondió (aserción que revienta si
alguien reintroduce esa llamada). `run_checks` TODO VERDE (229 unit · 139 e2e). `cachebust` no
aplica (solo backend).
**Sin migración.**

**Diferido:** más sitios con parser propio (Ultimate Guitar, e-chords...) si el flujo con IA
resulta demasiado usado en la práctica.

---

## 🔎 T-162 — Buscar canción por nombre en el editor (con IA) (2026-07-01) ✅

**Qué:** en vez de pegar el enlace de CifraClub/LaCuerda, el usuario escribe el **nombre de la
canción** (y opcionalmente el artista) en un buscador nuevo del editor; la IA consulta ambos sitios y
devuelve una **preselección de candidatos** (título/artista/origen) para elegir antes de importar.

**Por qué:** pedido directo de Oscar (2026-07-01, ver `GUIA_MAESTRA_V3.md` §8.2) para agilizar la
búsqueda: hoy hay que ir a buscar el enlace fuera de la app y volver a pegarlo.

**Cómo:**
- **Backend:** `search_song()` nuevo en [importer.py](src/services/importer.py) — construye la URL de
  búsqueda de CifraClub y LaCuerda, reutiliza el **mismo lector Jina** ya usado para la extracción
  (preserva los enlaces como markdown `[texto](url)`, imprescindible para sacar las URLs candidatas), y
  pide a OpenRouter (prompt nuevo `_SEARCH_SYSTEM_PROMPT`, distinto del de extracción) que devuelva un
  **array JSON estructurado** `{title, artist, url}` a partir del texto de resultados de cada sitio. Si
  un sitio falla no rompe la búsqueda (best-effort); solo lanza `ImportError_` si fallan todos. Nuevo
  endpoint `GET /import/search?q=` en [import_router.py](src/api/import_router.py) (mismo
  `Depends(get_current_user)` que el resto de `/songs`).
- **Frontend:** campo **"Buscar canción por nombre"** en [editor.html](static/editor.html), por encima
  del campo de URL existente (que se mantiene como alternativa manual). [editor.js](static/editor.js)
  pinta tarjetas con título/artista/origen (todo escapado con `escapeHtml`); al elegir una se rellena el
  campo de URL y se dispara el import normal (`import_from_url`) — **capa de preselección delante del
  import ya existente**, no un flujo nuevo. CSS `.import-search-*` en [style.css](static/style.css).

**Verificación:** unit en [test_import.py](tests/unit/test_import.py) (contrato del endpoint + auth +
`search_song` con fetch/OpenRouter mockeados, incluida la combinación de sitios y el fallo total) + e2e
en [test_editor.py](tests/e2e/test_editor.py) (buscar → tarjetas → elegir rellena URL e importa; sin
resultados → mensaje). `run_checks` **TODO VERDE (216 unit · 139 e2e)**. `cachebust` al día. **Sin
migración.**

**Diferido (no bloquea):** más sitios que CifraClub/LaCuerda, caché de búsquedas repetidas,
rate-limit del endpoint (cada búsqueda cuesta una llamada a OpenRouter — vigilar cuota gratuita).

---

## 🎤 T-161 — Afinador como sección propia del menú principal (2026-07-01) ✅

**Qué:** nuevo ítem **"Afinador"** en la navegación lateral, justo debajo de "Inicio" → página
standalone `afinador.html` con el mismo panel de detección de tono del reproductor, sin tener que
abrir antes una canción.

**Por qué:** pedido directo de Oscar (2026-07-01, ver `GUIA_MAESTRA_V3.md` §8.1); el afinador (T-091)
solo vivía dentro del player.

**Cómo:** ítem nuevo en `NAV` de [shell.js](static/shell.js) (`Inicio` → `Afinador` → `Explorar`…).
Página nueva [afinador.html](static/afinador.html) (shell + los mismos ids que usa `tuner.js`:
`#tuner-panel`/`#tuner-note`/`#tuner-cents`/`#tuner-needle`/`#tuner-start`/`#tuner-msg`, sin duplicar la
detección por autocorrelación). [tuner.js](static/tuner.js) ahora soporta **modo standalone**: si no
existe `#btn-tuner` (no hay botón que abra/cierre), el panel ya viene visible en el HTML y no aplica el
toggle — el botón dentro del player sigue funcionando igual que antes. Icono `mic` (ya existía en
`icons.js`).

**Verificación:** e2e en [test_shell.py](tests/e2e/test_shell.py) (el ítem está justo bajo "Inicio" y
navega a `afinador.html`; en la página standalone no hay `#btn-tuner`, el panel está visible y la
detección de 440 Hz → La4 sigue funcionando). `run_checks` **TODO VERDE (216 unit · 139 e2e)**.
`cachebust` al día. **Sin migración.**

---

## 🎬 V3-F7 · T-160 — oEmbed: carátula al pegar el enlace de referencia (2026-06-25) ✅ (código)

**Qué:** al pegar un enlace de **YouTube** en el editor (campo "Enlace de referencia"), aparece su
**carátula** (miniatura) en vivo. Confirma de un vistazo que es el vídeo correcto.

**Por qué:** "carátula al pegar URL" (V3-F7) — enriquece el repertorio sin coste. Se usa la miniatura
**determinista** de `img.youtube.com/vi/{id}/hqdefault.jpg` derivada del id del vídeo → **sin red, sin
CORS, sin backend**. (El título/autor vía proxy oEmbed real queda como follow-up.)

**Cómo:** helpers puros `bfYoutubeId`/`bfYoutubeThumb` en [util.js](static/util.js); preview
`#reference-preview` en [editor.html](static/editor.html) que [editor.js](static/editor.js) actualiza al
escribir (y al cargar una canción con referencia). CSS `.ref-thumb` en [style.css](static/style.css).
**Sin migración.**

**Verificación:** e2e [test_oembed_caratula.py](tests/e2e/test_oembed_caratula.py) (carátula con
`watch?v=` y `youtu.be`, y se oculta con un enlace no-YouTube). `run_checks` **TODO VERDE**
(208 unit · 135 e2e). `cachebust` al día.

> ⏳ Va en la misma rama que T-157…T-159 (apilado sobre la migración), así que **se despliega junto** con
> ellos cuando se aplique la migración `6323c5929bfc` a Postgres prod. No necesita migración por sí mismo.

---

## 🔗 V3-F7 · T-157/158/159 — Compartir un evento por enlace público (`unlisted`) (2026-06-25) ✅ (código) · ⏳ migración a prod

**Qué:** primer **efecto red** (D1): un admin comparte un evento por un **enlace público** (sin login).
Introduce el **eje `visibility`** (`private` por defecto / `unlisted` / `public`) y un **plano público**
separado con proyección **segura**.

**Por qué:** abre la app al exterior sin tocar lo privado — "comparte tu bolo" → quien abre el enlace ve
BandFlow ("Hecho con BandFlow", gancho de onboarding viral). Cumple la regla de oro pública: **una fila
privada jamás aparece en `/public`** y nunca se filtran datos sensibles (caché, contacto, notas, setlist).

**Cómo:**
- **Backend:** `Event.visibility` (modelo + CHECK `ck_events_visibility`) + **migración aditiva**
  `6323c5929bfc` (batch SQLite/Postgres; `alembic check` "no new operations"). `Visibility` en
  `EventUpdate`/`EventResponse`/`EventSummary`. Nuevo [public_router.py](src/api/public_router.py)
  (`GET /public/events/{id}`, **sin auth**): sirve solo `unlisted`/`public`, devuelve
  `PublicEventResponse` (id/tipo/título/fechas/banda/sala/ciudad/lugar) — **nada sensible**.
- **Frontend:** menú "⋯" de la agenda (admin) → **Compartir enlace** (PATCH a `unlisted` + copia el
  enlace + insignia 🔗) / **Copiar enlace** / **Dejar de compartir** ([bands.js](static/bands.js)).
  Página pública autónoma [evento.html](static/evento.html)+[evento.js](static/evento.js) (sin shell ni
  login; fetch directo a `/public/...`). SW deja de cachear `/public`.

**Verificación:** unit [test_api_public.py](tests/unit/test_api_public.py) (4: unlisted/privado/borrado/
inexistente + **proyección segura sin fugas**) + e2e [test_compartir_evento.py](tests/e2e/test_compartir_evento.py)
(3: compartir desde la agenda, página pública segura, privado→no accesible). `run_checks` **TODO VERDE**
(208 unit · 134 e2e). `cachebust` al día.

> ⏳ **Deploy pendiente de un paso:** esta entrega **lleva migración** (`6323c5929bfc`). El código está en
> la rama pero **NO se ha empujado a `main`**: subirlo sin aplicar la migración a Postgres rompería la
> agenda en producción (columna inexistente). **Aplicar primero la migración a Postgres** (pooler de
> sesión, 5432) y luego push → deploy. Resto de F7 (perfil público, onboarding viral, oEmbed) por hacer.

---

## 👤 V4-F6 · T-154 — Perfil con cuerpo (parte cliente, sin Storage) (2026-06-25) ✅

**Qué:** el perfil deja de ser un formulario pelado y muestra **identidad**: avatar de iniciales/color
(T-121), **mis bandas como chips con rol** (de `GET /bands/`) e **instrumentos como chips**, además del
formulario de edición de siempre.

**Por qué:** adelanto de F6 que **no depende de config de Oscar** (la subida de avatar real es T-153 →
Storage). Da cuerpo y sensación de identidad al perfil ya mismo.

**Cómo:** [profile.js](static/profile.js) reescrito: `render(p, bands)` pinta `.pf-identity` (avatar
`bf-avatar--lg` con `bandColor(p.id)`/`initialsFrom`), `#pf-bands` (chips `.pf-band-chip` con
`.bf-badge--{rol}`; estado vacío con `bfEmpty` si no hay bandas) y `#pf-instruments` (chips `.bf-badge`).
**Se conservan los ids del formulario** (`#pf-name`/`#pf-inst`/`#pf-save`) → el test de edición sigue
verde; tras guardar, re-render para refrescar avatar/chips. CSS nuevo en [style.css](static/style.css)
(`.pf-identity`, `.pf-band-chip`, `.pf-chip-row`…). **Sin backend ni migración.**

**Verificación:** e2e [test_perfil_cuerpo.py](tests/e2e/test_perfil_cuerpo.py) (2): avatar "AM" + chip de
banda con badge Admin + 2 instrumentos + form prerrellenado; y estado vacío sin bandas. `run_checks`
**TODO VERDE** (204 unit · 131 e2e). `cachebust` al día.

> Resto de **V4-F6** sigue 🔌 pendiente de config de Oscar: **T-153** (avatares/logos → Supabase Storage),
> **T-155** (notificaciones → infra de envío). **T-156** (EPK/realtime) es V3.

---

## 📅 V4-F5 · T-152 — Caché por temporada (agregación por fechas) (2026-06-25) ✅ — cierra F5

**Qué:** la sección **Finanzas** de la banda gana un bloque "**Por temporada**": agrega los movimientos
por **año natural** (ingresos / gastos / neto) para una visión económica por temporada, junto a la ya
existente "caché por gira".

**Por qué:** las finanzas se veían como una lista plana de movimientos; faltaba la lectura agregada por
periodo (cierra el punto 8.7 de la guía V4). El dato de fecha ya estaba en cada movimiento (`Transaction.date`).

**Cómo:** función **pura y testeable** `bfFinanceBySeason(txs)` en `util.js` (agrupa por
`new Date(date).getFullYear()`, ignora movimientos sin fecha, ordena descendente). `bands.js`
(`loadFinance`) la usa para pintar `#b-seasons` entre Saldos y Movimientos, formateando con `fmtMoney`.
**Agregación 100% cliente, sin backend ni migración.**

**Verificación:** e2e `test_cache_temporada.py` (2): con movimientos en 2024 y 2025 aparecen dos
temporadas separadas y ordenadas (neto correcto); y la función pura separa por año e ignora los sin
fecha. `run_checks` **TODO VERDE** (204 unit · 129 e2e). `cachebust` al día.

> 🏁 **Con T-152 queda CERRADA V4-F5.** Pendiente solo **V4-F6** (🔌 Storage/notificaciones/realtime, requiere config de Oscar).

---

## ♿ V4-F5 · T-151 — Accesibilidad (remate) (2026-06-25) ✅

**Qué:** pasada de accesibilidad sobre los cuatro frentes de la tarea: contraste de grises secundarios,
foco de teclado visible donde faltaba, objetivos táctiles ≥44px en dedo, y `aria-label` en los botones
solo-icono.

**Por qué:** la app ya tenía la base (foco accesible de T-127, `aria-label` en el reproductor de T-021,
44px táctiles en móvil), pero quedaban huecos: el gris `--bf-text-faint` no llegaba a AA, los controles
del lateral (tema/cerrar sesión) no mostraban foco, y varios botones generados por JS (▶ play, 📌 fijar,
💬 hilo) sólo tenían `title` (soporte irregular en lectores).

**Cómo:**
- **Contraste** (`design-system.css`): `--bf-text-faint` oscuro `#6a6a76`→`#82828e` (≈5.1:1 sobre el
  fondo, antes 3.7) y claro `#8c8c96`→`#6f6f7a` (≈4.5:1). Texto secundario AA.
- **Foco visible**: `shell.css` añade `:focus-visible` a `.bf-theme-toggle` (tema/logout del lateral);
  `style.css` suma `.google-btn` y los cierres del player (`.reference-panel__close`) al bloque de foco.
- **Táctil ≥44px**: `@media (pointer: coarse)` en `style.css` (`.icon-btn`/`.card-action-btn` 44×44;
  `.setlist-item-btn`/`.lib-filter`/`.card-play`/`.att-btn` min-height 44) y en `design-system.css`
  (`.bf-btn`/`.bf-tab`/`.bf-nav-item` min-height 44). El ratón mantiene el tamaño compacto.
- **`aria-label`**: 6 botones solo-icono — `bands.js` (pin/desfijar, hilo de evento, ▶ de setlist ×2 y
  de colección) y `setlists.js` (▶ de canción).

**Verificación:** test e2e `test_accesibilidad.py` (4): el ▶ de setlist tiene `aria-label`; el contraste
`--bf-text-faint/--bf-bg` calculado en el navegador es ≥4.5:1; todo `<button>` del reproductor tiene
nombre accesible; el toggle de tema del lateral tiene regla `:focus-visible` con outline. `run_checks`
**TODO VERDE** (204 unit · 127 e2e). `cachebust` al día.

---

## 🧩 V4-F5 · T-149 — Cifras tabulares en los displays numéricos (2026-06-25) ✅

**Qué:** refinamiento tipográfico — los números del reproductor (beat, BPM, tono) usan
`font-variant-numeric: tabular-nums` para que no "bailen" al cambiar de cifra. *(La unificación de
fuentes a IBM Plex y la escala de tokens ya venían de F1.)* `style.css` (`.bpm-display`,
`#current-beat-display`, `#bpm-value`, `#key-value`, `.section-chip`). Test e2e
`test_cifras_tabulares_en_el_reproductor`. Doctor verde + e2e en verde. `cachebust` al día.

---

## 🧩 V4-F5 · T-150 — Modo claro a la par (remate en legacy) (2026-06-25) ✅

**Qué:** que el contenido legacy (no solo el shell) se vea bien en **modo claro**.

**Por qué:** T-120 hizo heredar el ACENTO, pero el texto y los fondos de `style.css` seguían oscuros
literales → en claro, las tarjetas de la Biblioteca/Setlists quedaban oscuras y el texto poco legible.

**Cómo/Verificación:** `style.css`: los tokens `--text-primary`/`--text-secondary`/`--bg-dark` **heredan**
de `--bf-text`/`--bf-text-muted`/`--bf-bg` (con fallback oscuro); `.song-card` usa
`var(--bf-surface-2)`/`var(--bf-border)`. Así el contenido legacy adapta texto y fondo al claro. Test e2e
`test_tarjeta_legacy_adapta_al_claro` (al togglear `data-theme=light`, color y fondo de la tarjeta
cambian). Doctor verde + e2e (claro + library + player) **en verde**. `cachebust` al día.

---

## 🧩 V4-F5 · T-148 — Tour la primera vez en una banda (2026-06-25) ✅

**Qué:** orientar al recién llegado a un espacio de banda.

**Cómo/Verificación:** solo front. `band.js`: `maybeShowTour()` (tras `renderShell`) inserta, la **1ª
vez** (guardado en `localStorage` `bf-band-tour`), un aviso bajo las pestañas con qué hay en cada una;
se descarta con "Entendido" y no vuelve. `design-system.css`: `.bf-tour-tip`. Test e2e
`test_tour_primera_vez_y_no_repite` (aparece, se descarta, no reaparece al recargar). Doctor verde + e2e
(tour + band_space + resumen) **en verde**. `cachebust` al día.

---

## 🧩 V4-F5 · T-147 — Login pulido (2026-06-25) ✅

**Qué:** primera impresión a la altura del producto: el claim refleja la **gestión de banda**, no el
teleprompter antiguo.

**Cómo/Verificación:** `login.html`: el sub-claim pasa de "Tus partituras, en cualquier dispositivo" a
**"Gestiona tu banda: repertorio, bolos y cuentas — en un solo sitio."**. El **modo oscuro coherente** ya
llegó con T-120 (login.html carga `design-system.css` → el acento resuelve al coral). Botón de Google ya
prominente. Test e2e `test_login_claim_y_google_en_html` (sobre el HTML servido: el login redirige en modo
test). Doctor verde + e2e **en verde**. *(OAuth real se prueba en producción.)* `cachebust` al día.

---

## 🧩 V4-F5 · T-143 — "Añadir a colección" desde la tarjeta (2026-06-25) ✅

**Qué:** meter una canción personal en una o varias colecciones sin entrar a editarlas.

**Cómo/Verificación:** solo front. `library.js`: botón "añadir a colección" en la tarjeta personal →
`openAddToCollection(song)` (modal con **checkboxes** de mis colecciones); al confirmar, por cada
colección marcada hace `GET` + `PATCH /collections/{id}` con `song_ids` + la canción (idempotente).
`style.css`: `.add-to-list`/`.add-to-row`. Test e2e `test_anadir_cancion_a_coleccion` (la canción queda
en la colección vía API). Doctor verde + e2e (añadir-a + `test_library`) **en verde**. `cachebust` al día.

---

## 🧩 V4-F5 · T-145 — Duplicar un setlist (2026-06-25) ✅

**Qué:** partir de una copia en vez de empezar de cero.

**Cómo/Verificación:** solo front. `icons.js`: icono `copy`. `setlists.js`: botón "duplicar" en la
tarjeta → `duplicateSetlist(id)` (GET el setlist + POST una copia "<nombre> (copia)" con sus canciones y
notas). Test e2e `test_duplicar_setlist` (la copia aparece y tiene el mismo contenido vía API). Doctor
verde + e2e (duplicar + `test_setlists_ui`) **en verde**. `cachebust` al día.

---

## 🧩 V4-F5 · T-144 — Buscador en el repertorio de banda (2026-06-25) ✅

**Qué:** filtrar listas largas de canciones en la pestaña Repertorio.

**Cómo/Verificación:** solo front. `bands.js`: `ensureRepertoireSearch()` inserta (una vez) una caja
`#b-rep-search` sobre `#b-repertoire`; al teclear, **filtro cliente** que oculta las filas que no casan
por título/artista. Test e2e `test_buscador_repertorio_filtra`. Doctor verde + e2e (buscador +
`test_bands_ui`) **en verde**. `cachebust` al día.

---

## 🧩 V4-F5 · T-146 — Banda(s) en el lateral (2026-06-25) ✅

**Qué:** arranca **V4-F5 (funcionalidad y remate)**. Saltar a una banda desde el shell, sin pasar por
"Mis bandas".

**Cómo/Verificación:** solo front. `shell.js`: bajo el item "Bandas" se inyecta `#bf-bands-subnav` y
`loadBandsNav()` (reusa `GET /bands/`) lista mis bandas con **avatar de color** (`bandColor`+iniciales) →
`band.html?id=`; resalta la banda activa. `shell.css`: `.bf-subnav`/`.bf-subnav-item`/`.bf-avatar--sm`.
Test e2e `test_banda_en_lateral`. Doctor verde + e2e (lateral + shell + band_space) **en verde**.
`cachebust` al día.

---

## 🎸 V4-F4 · T-140 — Reordenar el setlist arrastrando (2026-06-25) ✅ — cierra F4

**Qué:** reordenar las canciones de un setlist **arrastrando**, con ratón y táctil, sin librerías.

**Cómo/Verificación:** solo front. `setlists.js` (`renderSel`): cada fila gana `data-sid` + un **asa**
`.sl-drag` (⠿); `wireSelDrag` sigue el arrastre a nivel de **`document`** (pointerdown→pointermove/pointerup,
sin `setPointerCapture` — más robusto y compatible con Playwright/táctil), mueve el nodo en el DOM y al
soltar sincroniza `selected` desde el orden del DOM + repinta (re-numera). El `PATCH`/`POST` ya acepta el
orden. `style.css`: `.sl-drag` (`touch-action:none`, clave para táctil) + `.dragging`.
- Test e2e `test_reordenar_setlist_arrastrando` (arrastra la 2ª sobre la 1ª → orden invertido persiste vía
  API). `test_setlists_ui` (crear/notas/quitar) sigue verde. Doctor verde + e2e **en verde**. `cachebust`
  al día. **Cierra V4-F4.**

---

## 🎸 V4-F4 · T-142 — Estados vacíos con CTA (2026-06-25) ✅

**Qué:** que ningún estado vacío sea un callejón sin salida: siempre con una acción clara.

**Cómo/Verificación:** `icons.js`: `bfEmpty` gana `opts.cta = { label, href }` (botón primario;
retrocompatible). Aplicado a los vacíos agregados de **Agenda** y **Finanzas** (CTA "Ir a Bandas"). Test
e2e `test_agenda_vacia_con_cta`. Doctor verde + e2e (vacíos + agenda + finanzas) **en verde**. `cachebust`
al día. *(Los empty-states de bandas/biblioteca/setlists ya tenían CTA propios de tareas anteriores.)*

---

## 🎸 V4-F4 · T-141 — Hoja de atajos del reproductor (2026-06-25) ✅

**Qué:** descubribilidad de los atajos de teclado del reproductor.

**Cómo/Verificación:** `index.html`: botón **"?"** (`#btn-shortcuts`, `.tool-btn`) en la zona de
navegación. `app.js`: al pulsarlo, `alertModal` con la tabla de atajos (Espacio = play/pausa; Av/Re Pág
y flechas = páginas/setlist; Esc = salir del directo). `style.css`: estilo de `kbd`/`.shortcuts-table`.
Cierra con Esc/clic fuera (lo da `alertModal`). Test e2e `test_atajos_modal`. Doctor verde + e2e
(atajos + player + top-bar) **en verde**. `cachebust` al día.

---

## 🎸 V4-F4 · T-139 — Escenario más espectacular (solo CSS) (2026-06-25) ✅

**Qué:** el Modo Directo (`.stage-mode`) se lee mejor desde lejos: líneas inactivas más apagadas, línea
activa realzada, acordes con más presencia y la bolita de progreso pulsando.

**Cómo/Verificación:** solo `style.css`, **sin tocar el motor**. Amplía `.stage-mode`: inactivas
`opacity:.22`, `.line-lyric:has(.chord-container.active)` con realce (blanco + glow), acordes
`font-weight:700` + glow en el activo, y `@keyframes stage-dot-pulse` en `.song-progress__dot`. Guard
`prefers-reduced-motion`. Test e2e `test_escenario_realce_y_bolita_pulsante` (bolita con animación
`stage-dot-pulse`, inactivas <0.3). Doctor verde + e2e (escenario + player, incl. `test_modo_directo`)
**en verde**. `cachebust` al día.

---

## 🎸 V4-F4 · T-138 — Top-bar del reproductor ordenada (2026-06-25) ✅

**Qué:** arranca **V4-F4 (la joya en directo)**. La barra superior del reproductor pasa de botones con
estilos inline a **3 zonas** (transporte/tempo · herramientas · navegación) con separadores y clase
`.tool-btn`. **El motor no se toca** (contrato DOM intacto).

**Cómo/Verificación:** solo `index.html` + `style.css`.
- `index.html`: los controles se agrupan en `.tb-zone` (×3) con `.tb-sep` entre zonas; los botones de
  herramienta/navegación usan `primary-btn square tool-btn` (sin estilo inline de fondo). Se conservan
  **todos** los ids, `aria-label`/`title` y los `href` (los usa `app.js paintPlayerIcons`).
- `style.css`: `.global-controls` (`flex-wrap`), `.tb-zone`, `.tb-sep`, `.tool-btn`. **Móvil:** los
  controles bajan de línea (flex-wrap) y se ocultan los separadores (alternativa robusta al menú
  colapsable, para no arriesgar la joya).
- Test e2e `test_topbar_player_ordenada` (3 zonas, `.tool-btn`, sin fondo inline, aria intactos, SVG
  presente). Doctor verde + e2e (top-bar + player + iconos) **en verde**. `cachebust` al día.

---

## 🗂️ V4-F3 · T-137 — Microinteracciones (pop) con propósito (2026-06-25) ✅ — cierra F3

**Qué:** premiar las acciones con un micro-feedback, respetando `prefers-reduced-motion`.

**Cómo/Verificación:** solo front. `design-system.css`: keyframes `bf-pop` (rebote) y `bf-flash`
(destello de `--bf-accent-weak`) + clases `.bf-pop`/`.bf-flash` + guard `@media (prefers-reduced-motion:
reduce)`. `util.js`: helper `bfPop(el)` (reinicia + autolimpia). Aplicado a los botones **"¿Vas?"** del
Resumen de banda (`band.js`) y del Inicio (`home.js`). Test e2e `test_microinteraccion_pop_y_reduced_motion`
(anima con `bf-pop`; con reduced-motion `animation-name: none`). Doctor verde + e2e (micro + resumen +
home) **en verde**. `cachebust` al día. **Cierra V4-F3.**

---

## 🗂️ V4-F3 · T-134 — Agenda más limpia: borrar en menú "⋯" (2026-06-25) ✅

**Qué:** quitar ruido de la fila de evento sin perder funciones: solo el **borrar** se esconde tras un
menú **"⋯"**; asistencia, hilo y estado de booking siguen visibles.

**Cómo/Verificación:** solo front. `icons.js`: icono `more` (3 puntos). `bands.js` (fila de agenda): el
`data-act="del"` pasa a vivir dentro de `.ev-more-menu` (oculto), revelado por un botón `data-act="more"`.
`style.css`: `.ev-more`/`.ev-more-menu` (popover) **+ `.ev-more-menu[hidden]{display:none}`** (el
`display:flex` de autor ganaba al `[hidden]` del navegador — cazado por el test). Test e2e
`test_agenda_menu_oculta_borrar` (asistencia visible, borrar oculto hasta abrir ⋯). Doctor verde + e2e
(menú + `test_bands_ui`/`test_band_space`) **en verde**. `cachebust` al día.

---

## 🗂️ V4-F3 · T-135 — Skeletons de carga en todas las listas (2026-06-25) ✅

**Qué:** sensación de respuesta inmediata en todas las listas (antes solo el Inicio tenía skeleton).

**Cómo/Verificación:** solo front. `util.js`: helper global `bfSkeletonList(n=3)` (n filas
`.bf-skeleton--card`). Aplicado **antes del fetch** en la Biblioteca (`library.js fetchSongs`) y en las
vistas agregadas **Agenda/Finanzas/Chat** (`agenda.js`/`finanzas.js`/`chat.js` `load()`). Test e2e
`test_bf_skeleton_list_helper` (helper determinista). Doctor verde + e2e (skeletons + agregadas) **en
verde**. `cachebust` al día.

---

## 🗂️ V4-F3 · T-133 — Tarjeta de canción con ▶ + franja de color por fuente (2026-06-25) ✅

**Qué:** la Biblioteca se vuelve más viva y reproducible en un clic: ▶ flotante (hover-reveal) + franja
de color que distingue personal vs. banda de un vistazo.

**Cómo/Verificación:** solo front.
- `library.js renderGrid`: botón `.card-play` (abajo-dcha) que abre `index.html?songId=…` (burbujea al
  handler de la tarjeta) + `card.style.setProperty('--card-accent', isPersonal ? var(--accent-color) :
  bandColor(_bandId))`. Se conserva el `_badge` como **texto** (test `test_library`).
- `style.css`: `.song-card::before` (barra 4px izq. con `--card-accent`, radios heredados) y `.card-play`
  (botón circular coral, hover-reveal + `:focus-visible`).
- Test e2e `test_card_play_y_franja_de_color` (▶ existe, `--card-accent` puesto, badge sigue texto, clic
  abre el reproductor). Doctor verde + e2e (card-play + library) **en verde**. `cachebust` al día.

---

## 🗂️ V4-F3 · T-136 — Aprovechar el ancho en los listados (`.bf-page--wide`) (2026-06-25) ✅

**Qué:** arranca **V4-F3 (tarjetas, densidad y carga)**. Los listados respiran: `.bf-page` sigue a 920px
para lectura/formularios, y un modificador **`.bf-page--wide` (~1180px)** ensancha los listados.

**Cómo/Verificación:** solo CSS/HTML. `shell.css`: `.bf-page--wide { max-width: 1180px; }`. Aplicado a
**Inicio** (`app.html`), **Bandas** (`bands.html`), **Explorar** (`biblioteca-global.html`) y
**Biblioteca** (`library.html`). *(La utilidad `.bf-grid` ya se adelantó en T-131.)* Test e2e
`test_bf_page_wide_es_mas_ancho`. Doctor verde + e2e (ancho + home + library) **en verde**. `cachebust` al día.

---

## 🎛️ V4-F2 · T-132 — Tarjeta de banda rica en "Mis bandas" + `song_count` (2026-06-25) ✅

**Qué:** las tarjetas de `bands.html` dejan de ser texto plano: **avatar de color** + iniciales,
rol/miembros/**nº de canciones** y **próximo evento**. Empty-state ilustrado con 2 CTA. Cierra la F2.

**Cómo/Verificación:**
- **Backend (única adición #2, sin migración):** `song_count: int` en `BandSummary` (`schemas.py`) +
  helper `_song_counts(db, band_ids)` (calcado de `_active_member_counts`, agregado por `Song.band_id`)
  rellenado en `list_my_bands`.
- **Front (`bands.js loadBands`):** `/bands/` + `/me/dashboard` en paralelo → avatar `bandColor(b.id)`
  + `initialsFrom`, `member_count`·`song_count`, y el próximo evento agrupando el dashboard por
  `band_id`. Empty-state con `bfEmpty('users', …)` + botones "Crear banda" / "Tengo un código"
  (`join.html`). `design-system.css`: `.band-card__head`/`.band-card__next`.
- Se conservan los selectores `.song-card`/`.card-main[data-act="open"]`/`.card-title` (tests intactos).
- Tests: unit `test_list_my_bands_incluye_song_count` (0 → 2); e2e `test_tarjeta_banda_avatar_y_song_count`
  (avatar + "1 canción" + abre). Doctor + ruff + unit + e2e (`test_bands_ui` incl.) **en verde**.

---

## 🎛️ V4-F2 · T-131 — Inicio = panel de control (Opción A, hero) (2026-06-25) ✅

**Qué:** el Inicio (`app.html`) deja de ser dos listas y pasa a un **panel de control con hero
protagonista**: el próximo bolo manda arriba, y debajo una rejilla con saldo total, accesos rápidos y
últimos mensajes. **Casi todo cliente.**

**Cómo/Verificación:** solo front (`home.js` + `design-system.css`).
- `home.js`: añade `apiFetch('/me/balances')` al `Promise.all`. Render Opción A:
  - **HERO** = `upcoming_events[0]`: cuenta atrás cliente, etiqueta de banda + fecha, y botones **"¿Vas?"**
    (`bf-btn`; el activo es `bf-btn--primary`) que hacen `PUT …/attendance` y recargan; + "Abrir banda".
    Sin eventos → hero "Sin bolos a la vista" con CTA.
  - **Rejilla `.bf-grid`:** "Tu saldo total" = Σ `/me/balances` (verde/rojo → Finanzas), "Accesos rápidos"
    (helper `step` compartido con el onboarding) y "Últimos mensajes" (`#home-messages`).
  - **Importante:** `app.html` NO carga `style.css` → el hero usa SOLO clases `bf-*` (no `.att-btn`).
- `design-system.css`: `.home-hero*` + se adelanta la utilidad **`.bf-grid`** (la usan T-131/T-132; T-136
  añadirá `.bf-page--wide`).
- Test e2e `test_home.py` actualizado (`test_home_hero_saldo_y_mensajes`: hero + evento + "Tu saldo
  total" + mensajes + "¿Vas?" marca "Voy"); el onboarding sin bandas sigue intacto. Doctor verde + e2e
  **en verde**. `cachebust` al día.

---

## 🎛️ V4-F2 · T-130 — Resumen de banda útil (Opción B) (2026-06-24) ✅

**Qué:** el Resumen de banda deja de ser un bloque estático ("Sobre la banda") y pasa a un **dashboard
de dos columnas** que da valor al entrar. Consume `GET /bands/{id}/summary` (T-129).

**Cómo/Verificación:** solo front (`band.js` + `design-system.css`).
- `band.js`: el panel `data-panel="resumen"` pasa a un contenedor `#b-summary`; `loadSummary(bandId,ctx)`
  hace el fetch y pinta la rejilla `.bs-summary`. Se saca `'resumen'` del `Set loaded` y se añade su caso
  a `loadTab` (recarga al reabrir); además se llama en `init` (es la pestaña activa por defecto).
  - **Izquierda:** "Próximo evento" (cuenta atrás cliente + `fmtDate` + `bookingLine` + `attendeesLine` +
    botones **"¿Vas?"** que hacen `PUT …/attendance` y recargan) y "Último mensaje".
  - **Derecha:** "Tu saldo" (verde/rojo, clic → Finanzas) y contadores canciones/setlists/colecciones
    (con `bfIcon`, clic → su pestaña). Reusa helpers globales de `bands.js` (EVENT_ICON/ATT_LABEL/
    attendeesLine/bookingLine/fmtDate).
- `design-system.css`: `.bs-summary` (grid 2 col, colapsa a 1 en móvil), `.bs-count`, saldo coloreado.
- Test e2e `test_resumen_banda_dashboard` (carga la rejilla, muestra el evento + "Tu saldo", "¿Vas?"
  marca "Voy" y recarga, acceso rápido cambia de pestaña). Doctor verde + e2e (resumen + band_space)
  **en verde**. `cachebust` al día.

---

## 🎛️ V4-F2 · T-129 — Endpoint `GET /bands/{id}/summary` (Resumen de banda) (2026-06-24) ✅

**Qué:** arranca la **V4-F2 (paneles de control)**. Un endpoint que devuelve TODO el Resumen de banda
en una sola ida y vuelta, sin N+1 y con aislamiento multi-tenant. **Único endpoint nuevo de la V4.**

**Por qué:** el Resumen de banda era estático; para hacerlo útil (T-130) hace falta un agregado:
próximo evento + último mensaje + mi saldo + contadores.

**Cómo/Verificación:** backend, **sin migración** (solo lecturas).
- `schemas.py`: `BandDashboard` (`next_event: EventSummary?`, `last_message: MessageOut?`,
  `my_balance: Decimal`, `counts: BandCounts{songs,setlists,collections}`) — **reusa** `EventSummary`/
  `MessageOut`, cero schemas de datos nuevos.
- `bands_router.py`: `GET /{band_id}/summary` con `Depends(require_band_member)`. Próximo evento
  (espejo de `events_router.list_events`: `EventSummary.model_validate` + asistencia anti-N+1 +
  `my_status` + `venue_name`), último mensaje del chat general, `my_balance` vía `compute_balances`,
  y contadores con `func.count` sobre `Song`/`Setlist`/`SongCollection` (`band_id` + `deleted_at IS NULL`).
- **Aislamiento (regla de oro):** la ruta se añadió al gate transversal `test_aislamiento_parametrizado`
  (`("GET","/bands/{bid}/summary")`) → un usuario ajeno recibe **403/404**. Test de forma
  `test_api_band_summary.py` (próximo evento, último mensaje `is_mine`, saldo 0, `counts`; vacío;
  excluye eventos pasados). Doctor verde + ruff + **24 unit** verdes.

---

## 🎨 V4-F1 · T-128 — Pestañas de banda: fade + scroll-snap en móvil (2026-06-24) ✅

**Qué:** que en móvil se intuya que hay más pestañas a la derecha del espacio de banda.

**Cómo/Verificación:** `design-system.css` + 1 línea en `band.js`.
- `.bf-tabs`: `scroll-snap-type: x proximity`; `.bf-tab`: `scroll-snap-align: start`; y en
  `@media (max-width:768px)` un `mask-image` (+ `-webkit-`) con **fade en ambos bordes** (16px).
- `band.js`: al activar una pestaña, `tab.scrollIntoView({ inline:'nearest', block:'nearest' })`.
- Test e2e `test_pestanas_fade_movil` (viewport 390px: `.bf-tabs` con `mask-image` ≠ none, desborda,
  y las pestañas siguen clicándose). Doctor verde + e2e (pestañas + band_space + responsive) **en verde**.

---

## 🎨 V4-F1 · T-127 — Hover/foco/transiciones unificados (2026-06-24) ✅

**Qué:** que todo lo clicable lo parezca y se sienta fluido (hover, foco por teclado, transición).

**Por qué:** el sistema `bf-*` ya tenía hover/foco/transición, pero faltaban: el hover de
`.bf-list-item`, el **`:focus-visible`** en lo legacy (`style.css`) y la animación de modales.

**Cómo/Verificación:** solo CSS.
- `design-system.css`: `.bf-list-item` gana `transition` + `:hover` (fondo `--bf-surface-3`, borde
  `--bf-border-strong`).
- `style.css` (legacy): bloque **`:focus-visible`** accesible reutilizado (`.song-card`, `.setlist-song`,
  `.icon-btn`, `.card-action-btn`, `.setlist-item-btn`, `.primary-btn`, `.secondary-btn`, `.lib-filter`
  → `outline: 2px solid var(--accent-color)`); hover+transición en `.setlist-song` (antes estática);
  **aparición suave de modales** (`modal-fade`/`modal-pop`) con guard `prefers-reduced-motion`.
- Test e2e `test_bf_list_item_hover_cambia_fondo` (`tests/e2e/test_interaccion.py`). Doctor verde + e2e
  (interacción + home + shell) **en verde**. `cachebust` al día.

---

## 🎨 V4-F1 · T-124b — Iconos SVG + "quitar ≠ borrar" en `bands.js` (espacio de banda) (2026-06-24) ✅

**Qué:** cerrar el barrido de iconos en el **espacio de banda** (`bands.js`), que T-124 había dejado
fuera, para que F1 quede coherente de verdad en la pantalla más usada.

**Cómo/Verificación:** solo `static/bands.js`.
- Botones de acción → `bfIcon`: borrar mensaje/movimiento/evento/sala/setlist/colección (🗑️→`trash`,
  conservan `danger`), editar sala/setlist (✏️→`edit`), reproducir (▶→`play`), hilo de evento (💬→`chat`),
  exportar CSV (⬇️→`download`), añadir (➕→`plus`).
- **Quitar ≠ borrar:** los tres "quitar" (setlist de banda `data-rm`, repertorio y colección
  `data-act="rm"`) pasan de `danger` (rojo) a **neutro** con icono `x`.
- **Contenido (se deja):** indicadores de tipo/estado (`EVENT_ICON` 🎼🎤, `ATT_LABEL` ✅🤔❌, ➕/➖ de
  importes, 📌 de mensaje fijado, 📍 de sala, 🎵 de evento), `<option>` (no admiten SVG) y el 💬 del
  título del modal de hilo.
- Verificación: regresión amplia del espacio de banda **en verde** (`test_bands_ui`, `test_chat`,
  `test_agenda`, `test_finanzas`, `test_band_space` — usan selectores `data-act`/`data-rm`/ids).
  Doctor verde. `cachebust` al día.

---

## 🎨 V4-F1 · T-126 — Terminología: pestaña "Repertorio" + sección "Colecciones" (2026-06-24) ✅

**Qué:** quitar la ambigüedad de "Repertorios". La **pestaña** (que muestra el pool + las colecciones)
se llama **"Repertorio"**; los grupos temáticos, **"Colecciones"**.

**Por qué:** "Repertorios" (pestaña de banda) chocaba con los Setlists y con las "Colecciones" personales
de la Biblioteca; el mismo concepto (grupo temático) tenía dos nombres.

**Cómo/Verificación:** SOLO texto visible (no se tocan `key:'repertorio'`/`data-tab` ni los ids
`b-collections`/`b-new-collection`, ni el pool "Todas las canciones"/`#b-repertoire`).
- `band.js`: label de pestaña `Repertorios`→`Repertorio`; `<h3>` `Repertorios`→`Colecciones`; botón
  `➕ Nuevo repertorio`→`➕ Nueva colección`.
- `bands.js`: 14 cadenas de colección (toasts, prompts, back-link "← Volver a Colecciones",
  aria-labels, vacíos) `repertorio→colección`. **Se conserva** "Añadir del repertorio" (eso es el pool).
- Test e2e `test_terminologia_repertorio_colecciones` (pestaña "Repertorio", sección "Colecciones",
  botón "Nueva colección", `data-tab="repertorio"` intacto, pool "Todas las canciones" intacto).
  `test_bands_ui` (crear colección) sigue verde. Doctor verde + e2e **en verde**. `cachebust` al día.

---

## 🎨 V4-F1 · T-125 — `setlists.html` dentro del shell (2026-06-24) ✅

**Qué:** los Setlists usan el **lateral** como el resto de la app (antes: top-bar antigua con 🏠/📚).

**Por qué:** coherencia estructural — `setlists.html` era la única página de "contenido propio" que aún
vivía fuera del shell, con su barra superior y enlaces duplicados que ya da el lateral.

**Cómo/Verificación:** solo `setlists.html` (la lógica de `setlists.js` no cambia).
- `<body>` reescrito al patrón shell (espejo de `library.html`): `.bf-shell > main.bf-shell-main >
  .bf-page`, cabecera `bf-row bf-row--between` con "🎵 Setlists" + botón `#btn-new-setlist`
  ("➕ Nuevo setlist", ahora `bf-btn--primary`). Quitada la top-bar antigua y sus 🏠/📚 (los da el lateral).
- `<head>`/scripts del shell: `shell.css`, `shell.js` (+ `icons.js`, ya en T-124). Se conservan los ids
  `#setlist-grid`/`#setlist-detail`/`#btn-new-setlist` que usa `setlists.js`.
- Test: `test_setlists_accesible_desde_la_biblioteca` ampliado (existe `.bf-shell` y `.bf-nav-item`);
  `test_setlists_ui` (crear/ver/editar) sigue verde. Doctor verde + e2e **en verde**. `cachebust` al día.

---

## 🎨 V4-F1 · T-124 — Iconos SVG en el resto + "quitar ≠ borrar" (2026-06-24) ✅

**Qué:** erradicar los emoji de **chrome** (botones de acción) de setlists/perfil/biblioteca/catálogo y
diferenciar **quitar** (neutro) de **borrar** (rojo).

**Cómo/Verificación:** solo front.
- `setlists.js`: ✏️→`edit`, 🗑️→`trash` (borrar setlist, **danger**), 💾→`save`, ➕→`plus`, ▶→`play`,
  📝→`note`. **Quitar ≠ borrar:** los botones "quitar de la lista" (`data-rm`, `data-act="rm"`) pasan de
  `setlist-item-btn danger` (rojo) a **neutro** con icono `x`. `setlists.html`: carga `icons.js`.
- `library.js`: ✏️→`edit`, 🗑️→`trash` (borrar, **danger**), ➕→`plus`, 📁→`folder` (chips/colección).
- `profile.js`: 💾→`save`. `catalogo.js`: ⬇→`download` (importar), ➕→`plus`.
- **Se deja como CONTENIDO** (no chrome): los badges de fuente `👤 Personal`/`🎸 Banda` (los e2e leen su
  texto, `test_library`), los emoji en `<option>` (no admiten SVG), los contadores `⬇ N`, el 🌍 del título
  "Explorar" y los `empty-icon` (se rehacen en T-142).
- Test e2e `test_setlists_iconos_y_quitar_no_es_borrar` (botones con `<svg>`; `data-rm` sin `danger`;
  borrar conserva `danger`). Doctor verde + e2e (iconos + setlists + library + catálogo) **en verde**.
  Selectores intactos (`data-act`/`data-rm`/`data-collection`/ids). `cachebust` al día.

---

## 🎨 V4-F1 · T-123 — Iconos SVG en el reproductor (la joya) (2026-06-24) ✅

**Qué:** los 11 emoji del reproductor pasan a SVG de `icons.js`, con tooltips y sin tocar el motor.

**Por qué:** subir el nivel visual de la pantalla estrella (la joya) sin riesgo: el contrato DOM de
`sync_engine.js`/`score_render.js` no cambia.

**Cómo/Verificación:** solo `static/app.js` (lógica), `index.html` ya cargaba `icons.js` (T-122).
- `paintPlayerIcons()` en `app.js` repinta al cargar el `innerHTML` de cada botón con `bfIcon`:
  💾→`save` · 🎤→`mic` · 🎬→`film` · 🖨️→`printer` · 🥁→`drum` · ⏹→`stop` · ⛶→`maximize`, y la
  navegación 🏠→`home` · 📚→`library` · ➕→`plus`. `+/−/♭/♯` se quedan como glifo.
- `btn-play-pause`: `engine.subscribe` ahora pinta `bfIcon('pause') + ' Pause'` / `bfIcon('play') +
  ' Play'` (`app.js:75/78`); estado inicial pintado en `paintPlayerIcons`.
- Se conservan **todos** los `aria-label`/`title` e ids (accesibilidad; ningún e2e dependía del emoji).
- Test e2e `test_player_iconos_svg` (`tests/e2e/test_iconos.py`): cada botón de control tiene `<svg>`,
  `aria-label` intacto y el play sigue arrancando la reproducción. Doctor verde + e2e (iconos + player
  completo) **en verde**. `cachebust` al día.

---

## 🎨 V4-F1 · T-122 — Ampliar `icons.js` + cargarlo en player/editor (2026-06-24) ✅

**Qué:** todos los iconos SVG que necesita la V4 disponibles, y `bfIcon` en TODAS las páginas.

**Por qué:** faltaban ~18 trazos (play, pause, stop, plus, minus, save, printer, mic, film, drum, timer,
maximize, minimize, folder, arrow-left, edit, trash, x, note) y **`icons.js` no se cargaba en
`index.html` (reproductor) ni `editor.html`** → sin él no se pueden sustituir los emoji por SVG
(T-123/T-124).

**Cómo/Verificación:** solo front, **aditivo** (aún no cambia nada visible).
- `icons.js`: 19 entradas nuevas en `PATHS` (Lucide, MIT, viewBox 24×24).
- `index.html` y `editor.html`: `<script src="icons.js">` (tras `auth.js`, antes de `app.js`/`editor.js`).
- Test e2e `test_iconos.py`: `typeof bfIcon==='function'` en player y editor; `bfIcon('play'|'pause'|
  'stop'|…)` contiene `<svg`. Doctor verde + e2e (iconos + regresión player/editor) **en verde**.
  `cachebust` al día.

---

## 🎨 V4-F1 · T-121 — Helpers de identidad de banda a `util.js` (2026-06-24) ✅

**Qué:** color e iniciales por banda como **fuente única** y reutilizable.

**Por qué:** `hueFromId` estaba **encerrado** en el IIFE de `band.js` (no reutilizable) e `initialsFrom`
**duplicado** (`band.js` + `shell.js`), con dos fallbacks distintos para nombre vacío (`'🎸'` vs `null`).
Las tarjetas, avatares y etiquetas de banda de la V4 (Inicio, "Mis bandas", Resumen) necesitan el mismo
color/iniciales en todas partes.

**Cómo/Verificación:** solo front.
- `util.js`: nuevos globales `bandHue(id)` (hash char-code → 0-359), `bandColor(id,{s=55,l=48})` →
  `hsl(...)` (por defecto 55% 48%, idéntico al banner → sin regresión), `initialsFrom(name)` (1-2
  iniciales o `null` si no hay nombre; el llamante decide el fallback).
- `band.js`: quita el `hueFromId`/`initialsFrom` locales; usa `bandColor(bandId)` y
  `initialsFrom(band.name) || '🎸'`.
- `shell.js`: quita su `initialsFrom` local (usa el global; `util.js` se carga antes que `shell.js` en
  todas las páginas del shell — verificado).
- Test e2e `test_helpers_identidad_en_util` (`tests/e2e/test_js_logic.py`): los 3 son funciones globales,
  `bandColor` determinista, formato HSL correcto, `initialsFrom('Los Demo Riff')==='LD'`, `null` en vacío.
  Doctor verde + e2e (helpers + regresión band/shell) **en verde**. `cachebust` al día.

---

## 🎨 V4-F1 · T-120 — Un solo acento (+ modo claro legacy gratis) (2026-06-24) ✅

**Qué:** primera tarea de la **V4 (experiencia + diseño)**. Se unifica el color de acento en UNA sola
fuente de verdad y, de regalo, **el modo claro empieza a funcionar en las páginas legacy**.

**Por qué:** había **dos** corales duplicados —`--accent-color:#ff6b4a` en `style.css` (player, editor,
biblioteca, setlists, perfil, login) y `--bf-primary` en `design-system.css` (resto)— más docenas de
`#ff6b4a`/`rgba(255,107,74,…)` hardcodeados y fallbacks muertos verde-menta (`#6ee7b7`). Recolorar la app
obligaba a tocar dos sitios y el tema claro no llegaba al legacy.

**Cómo/Verificación:** solo front/CSS.
- `style.css:11-14` → los tokens de acento **heredan** de `--bf-*` con fallback coral:
  `--accent-color: var(--bf-primary, #ff6b4a)` (+ hover/chord/chord-active-bg). Como `.primary-btn`,
  `.icon-btn`, acordes, etc. ya usan `var(--accent-color)`, **todos** recoloran y adaptan al claro por
  herencia.
- **Prerrequisito:** se carga `design-system.css` en las 4 páginas legacy que no lo tenían
  (`index.html`, `editor.html`, `setlists.html`, `login.html`) para que `var(--bf-primary)` resuelva.
- Token reutilizable `--bf-accent-glow` en `design-system.css` (`:root` + tema claro); usado en el pulso
  del `song-progress__dot`. Borrados los fallbacks muertos `#6ee7b7` (`style.css:653,1094`).
- Test e2e `test_acento_unificado_y_tema` (`tests/e2e/test_acento_tema.py`): en `setlists.html` (legacy),
  el acento resuelve al coral (`rgb(255,107,74)`) y al togglear `data-theme="light"` **cambia**
  (`rgb(238,85,48)`). `cachebust` al día. **Doctor verde (10/10)** + e2e del cambio y de regresión
  (player/setlists/editor) **en verde**.

**Nota:** los glows decorativos restantes (varias alfas) se dejan como literales coral —siguen
funcionando— para no alterar intensidades; tokenización fina diferida. Riesgo bajo (solo color).

---

## 🧭 Pulido de coherencia UX — el recorrido del músico (2026-06-24) ✅

**Qué:** auditoría poniéndome en la piel de un músico que abre la app por primera vez, + arreglo de los
dos puntos de fricción más graves que encontré:
1. **Setlists personales rescatados.** `setlists.html` estaba **huérfana** (ningún enlace de la app
   llevaba a ella desde que se introdujo el shell en Fase 13) y **mal titulada "Repertorios"** aunque
   contiene setlists (orden de bolo) → chocaba con los "Repertorios" de banda y las "Colecciones".
   Ahora: renombrada a **"Setlists"** en toda la página (título, cabecera, botones, textos y
   `setlists.js`) y **accesible desde la Biblioteca** (botón "🎵 Setlists" en la cabecera).
2. **Onboarding del Inicio.** Un usuario sin bandas aterrizaba en un panel band-céntrico vacío sin saber
   qué hacer. Ahora, si no estás en ninguna banda, el Inicio muestra **"Primeros pasos"** con 3 acciones
   claras (añadir canción → Biblioteca · crear/unirse a banda → Bandas · explorar → catálogo global).

**Por qué:** que la app tenga más sentido y sea más fácil de usar desde el minuto uno: ninguna función
debería ser inalcanzable, ningún término debería significar dos cosas, y el recién llegado debe saber
qué hacer.

**Cómo/Verificación:** solo frontend.
- `setlists.html`/`setlists.js`: "Repertorios/repertorio" → "Setlists/setlist" (IDs/clases ya eran
  `setlist-*`, rename de texto seguro). `library.html`: botón "🎵 Setlists" → `setlists.html`.
- `home.js`: carga `/bands`; si está vacío, pinta el panel de primeros pasos (`#home-onboarding`).
- Tests: e2e `test_setlists_accesible_desde_la_biblioteca` + `test_inicio_onboarding_sin_bandas`
  (+ helper `wipe_bands` en conftest). `cachebust` al día. run_checks **TODO VERDE**.

**Diferido (coherencia menor):** unificar "Repertorios" (banda) vs "Colecciones" (personal) para el
mismo concepto de grupo temático; reskin de `setlists.html` al shell (hoy usa la top-bar antigua).

---

## 📁 Colecciones PERSONALES en la Biblioteca (2026-06-24) ✅

**Qué:** la Biblioteca (`library.html`) gana **colecciones personales**: grupos temáticos de TUS
canciones ("Acústico", "Bodas"…), el equivalente personal de los Repertorios de banda. Una fila de
"Colecciones" con chips + "➕ Nueva colección"; al activar un chip el grid muestra solo sus canciones;
se puede editar (✏️ nombre + selección de canciones) y borrar. Cierra el diferido de T-114. **Ubicación
decidida con Oscar:** dentro de Biblioteca (el único hub personal de canciones en el lateral).

**Por qué:** organizar el repertorio personal por tema, igual que ya podían las bandas.

**Cómo/Verificación:** aditivo.
- **Modelo:** `SongCollection` pasa a soportar lo personal como `Setlist` (`band_id` nullable +
  `owner_id`). Migración `b6434fe1096d` (batch: add `owner_id` + `band_id` nullable + índice),
  `alembic check` limpio. ✅ Aplicada a Postgres prod (2026-06-24).
- **Backend:** `collections_router.py` (`/collections` CRUD, owner-scoped; las canciones solo MÍAS y
  personales —`owner_id` + `band_id` NULL—; ajeno → 404). Schemas `Collection*` con `band_id` opcional.
  Registrado en `main.py`.
- **Frontend:** `library.js` carga `/collections`, pinta la fila de colecciones, modal crear/editar
  (nombre + checkboxes de mis canciones), vista filtrada por colección y borrado (nombres escapados).
- **Tests:** unit `test_api_collections_personal` (CRUD, solo-mis-canciones, aislamiento ajeno→404)
  + e2e `test_coleccion_personal_en_la_biblioteca`. `cachebust` al día. run_checks **TODO VERDE**.

---

## 📅 Confirmados de asistencia en la agenda AGREGADA (2026-06-24) ✅

**Qué:** la agenda agregada del contexto TÚ (`agenda.html`, `GET /me/events`) muestra ahora, bajo cada
evento, una línea discreta de **quién ha confirmado** ("✅ Ana, Luis · 🤔 2"), igual que la agenda de
cada banda. Cierra el diferido de la cola #4 ("confirmados en la agenda agregada").

**Por qué:** ver de un vistazo quién va a cada bolo/ensayo de TODAS tus bandas sin entrar en cada una.

**Cómo/Verificación:** aditivo, sin migración.
- **Backend:** `DashboardEvent` gana `attendance: List[AttendanceOut]`; `me_router.list_my_events` la
  surte con **UNA query agregada** (`EventAttendance` ⨝ `MusicianProfile` por nombre real, sin N+1),
  igual que `events_router`. Aislamiento intacto (solo mis bandas activas).
- **Frontend:** `agenda.js` añade `attendeesText(e)` (mismo resumen que `bands.js`, nombres escapados).
- **Tests:** unit `test_me_events_incluye_confirmados` + e2e `test_agenda_agregada_muestra_confirmados`.
  `cachebust` al día. run_checks **TODO VERDE**.

---

## 🎵 Notas (y edición completa) en los setlists PERSONALES (2026-06-24) ✅

**Qué:** los repertorios personales (`setlists.html`) ganan **apunte por canción** ("capo 2",
"acústica") y **edición completa**: el botón ✏️ en cada tarjeta abre el editor prerrellenado
(nombre + canciones + notas) y guarda con `PATCH`; el detalle muestra la nota (📝). Antes solo se podía
crear, ver y quitar canciones (sin notas ni edición). Cierra el diferido "notas en setlists personales"
de T-110 y da **paridad** con los setlists de banda.

**Por qué:** simetría con los setlists de banda (que ya tenían notas y edición) y carencia real: no se
podía corregir un repertorio personal ni anotar nada.

**Cómo/Verificación:**
- **Backend** (`setlists_router.py`): create/update honran `items:[{song_id,note}]` (antes solo
  `song_ids`); `_set_items` reescrito para persistir la nota + `_pairs_from_payload` (mismo patrón que
  los de banda). El schema ya tenía `items` y `_to_response` ya devolvía `note`.
- **Frontend** (`setlists.js`): `openCreate`→`openEditor(setlistId)` (crea/edita, con input de nota por
  canción); botón ✏️ en las tarjetas; el detalle pinta la nota; **fix de bug latente**: quitar una
  canción ahora envía `items` → **preserva las notas** de las demás (con `song_ids` las borraba).
- **Tests:** unit `test_setlist_personal_con_notas` (create+patch con notas, orden) + e2e
  `test_editar_repertorio_personal_con_nota`. `cachebust` al día. run_checks **TODO VERDE**.

---

## 🎵 Editar un setlist de banda desde la UI (2026-06-24) ✅

**Qué:** la pestaña Setlists gana un botón **✏️ Editar** (no-guest) que abre el editor de setlist
**prerrellenado** (nombre + canciones en orden + apuntes por canción); al guardar hace `PATCH` y
refresca. Antes solo se podía crear/borrar (para corregir había que recrear). Cierra el diferido de
T-110 ("editar notas de un setlist existente") y, de paso, permite renombrar/reordenar/añadir-quitar.

**Por qué:** carencia obvia (mismo dolor que las salas): no poder editar un setlist obligaba a borrarlo
y rehacerlo. El backend ya tenía el `PATCH` (Fase 9/T-110); solo faltaba exponerlo en el front.

**Cómo/Verificación:** **solo frontend** (`bands.js`). `newBandSetlist` se generalizó a crear/editar:
con `opts.setlistId` carga el setlist (GET en paralelo con el repertorio), precarga nombre + canciones
(en orden) + notas, y guarda con `PATCH` (`items:[{song_id,note}]`, que el backend filtra al repertorio).
`loadBandSetlists` añade el botón ✏️ con handler autocontenido (toggle lista/editor con los ids de
`band.html`, sin tocar `band.js`). Valores escapados (XSS). e2e `test_editar_setlist_de_banda` (abre
prerrellenado → cambia nombre y nota → PATCH, sin duplicar). `cachebust` al día. run_checks **TODO VERDE**.

---

## 💶 Fase 14 — Resumen de caché por gira (2026-06-23) ✅

**Qué:** cada **gira** (pestaña Giras) muestra ahora el **caché total de sus conciertos** (Σ del `fee`
de los conciertos ligados a las paradas), en el detalle ("Caché conciertos: X") y en la fila de la lista
(💶, si > 0). Complementa el "Presupuesto estimado" (gasto previsto) con el ingreso por caché.

**Por qué:** cierra un diferido de Fase 14 ("resumen de caché por gira") y da valor financiero a las
giras reutilizando datos que ya existen (el `fee` de T-115) — sin migración.

**Cómo/Verificación:** **sin migración** (campo calculado). `TourResponse`/`TourSummary` ganan
`total_fee`; `tours_router._to_response` lo suma al cargar los eventos ligados (filtra borrados) y
`list_tours` lo calcula con **UNA query agregada** (`sum(Event.fee)` join `TourStop`, group by gira →
sin N+1). Front `band.js` (`tourRow` + banner del detalle, escapado). unit
`test_cache_por_gira_suma_el_fee_de_los_conciertos` (suma 500+300.50; ignora conciertos sin caché y
paradas sin concierto; detalle y lista). `cachebust` al día. run_checks **TODO VERDE**.

---

## 🏟️ Fase 14 — Editar una sala (Venue) desde la UI (2026-06-23) ✅

**Qué:** la sección "Salas" (pestaña Agenda) gana un botón **✏️ Editar** (solo admin) que abre el modal
de sala con los datos **prerrellenados**; al guardar hace `PATCH` y refresca la lista. Completa el CRUD
de salas de cara al usuario (antes solo crear/borrar). Cierra un diferido de T-116.

**Por qué:** las salas se reutilizan entre conciertos; no poder corregir aforo/ciudad/contacto sin
borrar y recrear era una carencia obvia.

**Cómo/Verificación:** **solo frontend** (`bands.js`) — el backend ya tenía `PATCH /bands/{id}/venues/{vid}`
(admin, cubierto por `test_api_venues`: editar/aislamiento). `newVenue` se generalizó a modal
**crear/editar** (`opts.venue` → PATCH; envía los 4 campos, `null` si vacíos, para poder también limpiar
ciudad/aforo/contacto — el POST descarta los `null`) y `loadVenues` añade el botón ✏️ (valores escapados
en `value=`, anti-XSS). e2e `test_editar_sala_desde_la_ui` (abre el modal prerrellenado → renombra →
la lista refleja el cambio). `cachebust` al día (`band.html`/`bands.html`). **De paso:** arreglado un
test caducado (`test_home` usaba fecha hardcodeada `2026-06-20`, ya pasada → ahora fecha futura
**dinámica** `now()+2d`, no vuelve a caducar). run_checks **TODO VERDE**.

---

## 🚀 Despliegue a producción + rotación de contraseña de Postgres (2026-06-23) ✅

**Qué:** se desplegó a producción todo el código pendiente (commits `539930a..26c6b3b`: T-114
Repertorios, T-115 booking, T-116 Salas, fixes) y se aplicaron a Postgres prod las **3 migraciones
pendientes** (`5481a965f5fb` colecciones, `c341c9bbb0ba` booking, `91d60406fb92` salas). Oscar **reseteó
la contraseña de la BD de Supabase**; se actualizó la `DATABASE_URL` de Vercel y se verificó todo en vivo.

**Por qué (causa raíz del "Vercel BLOCKED"):** durante varios días los deploys salían `state: BLOCKED`
y se creía que era el **tope del plan free**. **Era falso.** La causa real: **Vercel (Hobby) bloquea
los builds de commits cuyo autor de git no es el dueño de la cuenta.** Los commits recientes se hicieron
con identidad placeholder `Tu Nombre <tu@email.com>` (GitHub `marjosavi481`) → bloqueados; los de
`kabalah314-ux <kabalah314@gmail.com>` construyen bien (por eso el repo hermano `brokenheartos`, mismo
team, sí desplegaba). Diagnóstico: comparar `githubCommitAuthorEmail` de los deploys READY vs BLOCKED.

**Cómo/Verificación:**
1. **Migraciones:** `DATABASE_URL=<session-pooler-5432>` (host real `aws-1-eu-central-1.pooler.supabase.com`,
   ¡no `aws-0`!) → `alembic upgrade head`. Prod pasó de `e9f1a2b3c4d5` a `91d60406fb92`. La URL se
   **construyó solo con la contraseña** (no hace falta pedir la cadena entera).
2. **Vercel env:** `vercel env rm/add DATABASE_URL production` con la pw nueva (transaction pooler 6543).
3. **Desbloqueo + deploy:** commit vacío con autor correcto (`git commit --allow-empty`) + `git push
   origin main` → auto-deploy **READY en 9s** (commit `559029a`). Prod pasó a servir `shell.css?v=56a6ffa1`.
4. **Verificación end-to-end en vivo:** login real Supabase (cuenta de prueba) → `GET /songs/` **200**
   (3 canciones) → **BD conecta con la pw nueva**; `/bands/{id}/collections` (T-114) y `/venues` (T-116)
   **200** (migraciones operativas, sin 500). `/health` 200, `test_mode:false`.

**Pendiente de Oscar (seguridad):** rotar las claves compartidas en chat (la pw de Postgres
`Oscarnuria314!` quedó en el historial del chat) cuando se pueda; revocar PAT `sbp_` si sigue vivo.

---

## 📍 T-116 — Salas (Venue) reutilizables, enlazadas al concierto — Fase 14 (2026-06-21)

**Qué:** la banda puede tener **salas** propias (nombre, ciudad, aforo, contacto) que se **reutilizan**
entre conciertos. En la pestaña **Agenda** hay una sección "Salas" (el admin las crea/borra) y, al crear
un **concierto**, un selector de sala. En la agenda, el concierto muestra **📍 nombre de la sala** en su
línea de booking (junto al caché/contacto).

**Por qué:** avance de roadmap (Fase 14, booking). El `location` libre del evento no se reutilizaba ni
guardaba datos (aforo, contacto técnico). Un `Venue` propio permite reusar la sala y centralizar su info,
base para futuros informes/mapa.

**Cómo/Verificación:** aditivo.
- **Modelo:** `Venue` (band_id, name, address, city, capacity, contact, notes, soft-delete) +
  `Event.venue_id` (FK SET NULL, solo conciertos). Migración `91d60406fb92` (FK nombrada
  `fk_events_venue_id_venues`), `alembic check` sin drift.
- **Backend:** `venues_router.py` (`/bands/{id}/venues` CRUD; **admin** gestiona, miembros leen;
  aislamiento + gate parametrizado T-098). `events_router` valida la sala (`_validate_venue`: solo
  conciertos + de la banda → 400) y **denormaliza `venue_name`** en la agenda (lista, UNA query) y el
  detalle.
- **Frontend:** sección "Salas" en la pestaña Agenda + `loadVenues`/`newVenue` en `bands.js` + selector
  de sala en el modal de concierto + `📍` en `bookingLine`. Escapado (XSS). **Fix de UX:** `.modal-card`
  con `max-height:90vh; overflow-y:auto` (modales altos ya no dejan los botones fuera de pantalla).
- **Tests:** unit `test_api_venues.py` (6: admin/miembro/guest, enlace a concierto, solo-conciertos +
  sala-de-la-banda → 400, aislamiento) + e2e `test_sala_venue_reutilizable_en_concierto`. Verificado en
  navegador (Sala Apolo · Barcelona · 600 pers. → concierto con 📍). Doctor verde, ruff limpio,
  `cachebust` al día. **Diferido:** editar sala (capacidad/dirección) desde la UI; mapa; P&L por sala.

---

## 🎵 Pulido T-114 — crear un setlist desde una colección (2026-06-21)

**Qué:** en el detalle de un repertorio (colección) hay un botón **"🎵 Crear setlist con estas"** que
genera un **setlist** (orden de bolo) con las canciones de la colección. Pide el nombre (prerrelleno con
el de la colección) y lo crea en la pestaña Setlists.

**Por qué:** cierra el bucle **Repertorio→Setlist** que motivó la diferenciación (T-114): organizas las
canciones por tema y, cuando hay bolo, sacas de ahí el orden concreto. Era el "diferido" más útil.

**Cómo/Verificación:** solo frontend (`bands.js`, en `openCollection`): reusa `POST /bands/{id}/setlists`
con los `song_ids` de la colección (sin backend nuevo). e2e `test_crear_setlist_desde_una_coleccion`
(colección → botón → el setlist aparece en Setlists). Verificado en navegador. ruff limpio, `cachebust`
al día.

---

## 📇 T-115 — Campos de booking en el concierto (contacto + caché) — Fase 14 (2026-06-21)

**Qué:** un **concierto** guarda ahora **contacto del promotor** (nombre + teléfono/email) y **caché**
(`fee`, en la divisa de la banda). En el alta de evento, al elegir "Concierto" aparecen esos campos
(opcionales); en la **agenda** se muestra una línea discreta `💶 450.00 · 📇 Promotora Marta` bajo el
concierto (solo si tiene datos; nunca en ensayos).

**Por qué:** continúa la **Fase 14 (Booking, Área 10)** con la parte accionable sin infra de email: el
funnel de booking (T-111) ahora tiene a quién contactar y cuánto se cobra, que es lo que falta para
gestionar un bolo de verdad. (T-113 `EmailTemplate` sigue pendiente: necesita envío real.)

**Cómo/Verificación:** aditivo.
- **Modelo:** `Event.contact_name`/`contact_phone`/`fee` (`Numeric(10,2)`). Migración `c341c9bbb0ba`
  (batch add_column), `alembic check` sin drift.
- **Schemas:** añadidos a `EventCreate`/`EventUpdate`/`EventResponse` (+ `contact_name`/`fee` en
  `EventSummary` para la agenda; el teléfono queda en el detalle). `fee` valida `ge=0` → caché negativo
  **422**. El router no cambia: usa `**model_dump()`/`setattr` genéricos (admin-only ya vigente).
- **Frontend:** campos en el modal de evento (visibles solo en conciertos) + helper `bookingLine` en
  `bands.js` + `.ev-booking` en `style.css`. Nombres escapados (XSS).
- **Tests:** unit `test_booking_fields_contacto_y_cache` (persistencia detalle+lista, admin-only, 422
  negativo) + e2e `test_concierto_con_booking_contacto_y_cache`. Verificado en navegador (Bolo Sala
  Apolo: "💶 450.00 · 📇 Promotora Marta"). Doctor verde, ruff limpio, `cachebust` al día. **Diferido:**
  `Venue` como modelo propio; resumen de caché por gira/temporada; recordatorios de booking por email.

---

## 📁 T-114 — Repertorios (colecciones temáticas) — diferenciar Repertorio vs Setlist (2026-06-21)

**Qué:** la pestaña de banda **"Repertorio" pasa a "Repertorios"**: ahora puedes crear **varias listas
nombradas** ("Acústico", "Cañero", "Bodas"…) que **agrupan** canciones del repertorio por tema. Debajo
sigue **"Todas las canciones"** (el pool de la banda, donde se copian/quitan). Los **Setlists** quedan
intactos y diferenciados (el **orden** concreto de un bolo, con notas por canción T-110).

**Por qué:** puntos #2 y #3 de la cola de Oscar. Repertorio (pool plano) y Setlist (lista ordenada) se
solapaban. Decisión de producto: **diferenciar** → *repertorio/colección* = agrupación temática **sin
orden**; *setlist* = orden de concierto. Una canción puede estar en **varias** colecciones.

**Cómo/Verificación:** todo **aditivo** (no toca songs/setlists).
- **Modelo:** `SongCollection` (band_id, name, soft-delete) + `SongCollectionItem` (collection_id,
  song_id, position; único `(collection_id, song_id)`). Migración `5481a965f5fb` (batch, FK CASCADE,
  índices band_id/FKs). `alembic check` sin drift.
- **Backend:** `band_collections_router.py` → `/bands/{id}/collections` CRUD (miembros gestionan, guest
  solo lee), canciones validadas contra el repertorio de la banda. Aislamiento por `require_band_member`
  + filtro `band_id`; añadidas las 2 rutas al **gate de aislamiento parametrizado** (T-098).
- **Frontend:** pestaña "Repertorios" en `band.html`/`band.js` (sección colecciones + pool) + `bands.js`
  (`loadCollections`/`openCollection`/`newCollection`: crear por nombre, abrir, añadir/quitar del pool,
  ▶ reproducir, borrar). Nombres escapados (XSS).
- **Tests:** unit `test_api_collections.py` (8: CRUD, solo-repertorio, multi-colección sin duplicar,
  guest no edita, **diferenciación de setlist**, aislamiento) + gate parametrizado (18 rutas) + e2e
  `test_crear_repertorio_coleccion_y_anadir_cancion`. Verificado en navegador (crear "Acústico" + añadir
  Wonderwall). Doctor verde, ruff limpio, `cachebust` al día. **Diferido:** reordenar dentro de la
  colección; crear un setlist directamente desde una colección; colecciones personales.

---

## 👥 Agenda — confirmados por evento (quién va) (2026-06-21)

**Qué:** cada evento de la agenda de banda muestra, **de forma discreta** bajo el título, **quién ha
confirmado** asistencia: una línea `✅ Ana, Luis · 🤔 2` (nombres de los que van + cuántos dicen
"quizás"). Si nadie ha respondido aún, no se muestra nada (no mete ruido).

**Por qué:** era el punto #4 de la cola de correcciones de Oscar. La info de asistencia existía
(`EventAttendance`, voy/no/quizás) pero **solo se exponía en el detalle** del evento; en la **lista**
(que es la que usa la agenda) no venía → no había forma de ver los confirmados de un vistazo.

**Cómo/Verificación:** (1) **backend** — `EventSummary.attendance` nuevo y `list_events`
(`events_router.py`) lo surte con **UNA query agregada** (join a `MusicianProfile` por nombre real,
agrupado por evento en Python → sin N+1), mismo patrón que el detalle. (2) **frontend** — helper
`attendeesLine(e)` en `bands.js` (escapa los nombres, XSS) + `.ev-attendees` discreto en `style.css`,
insertado en el render de cada evento de `loadAgenda`. Verificado en navegador (banda demo: el ensayo
muestra "✅ Oscar (tú), Ana · 🤔 1"; el concierto sin respuestas, nada). Tests: unit
`test_listar_y_marcar_asistencia` ampliado (la lista trae `attendance`) + e2e
`test_agenda_muestra_quien_ha_confirmado` (sin respuestas no hay línea; al marcar "Voy" aparece el ✅).
`cachebust` al día. **Diferido (no bloquea):** sección plegable con el detalle completo (no voy / sin
responder); confirmados en la agenda **agregada** (`/me/events`, que hoy solo trae mi asistencia).

---

## 🩹 fix(shell) — el marco blanco lateral: hardening del fondo en `html` (2026-06-21)

**Qué:** el fondo de la app ahora va en **`html` Y `body`** (`html, body { background: var(--bf-bg) }`),
no solo en `body`. Antes el `<html>` quedaba transparente: cualquier hueco o el **rebote de scroll**
(overscroll/rubber-band de macOS) dejaba ver el **blanco por defecto del `<html>`** → reaparecía el
"marco/línea lateral" que Oscar reportaba que **seguía** apareciendo.

**Por qué:** el `fix(shell)` anterior (2026-06-20) reseteó `body{margin:0}` y eso resolvió el marco de
las páginas sin `style.css`. **Reinvestigado con Playwright contra el local** (todas las páginas del
shell, modo oscuro y claro): el marco ya **no se reproduce** en local. La razón de que Oscar lo siguiera
viendo es que **el fix no está desplegado** — el commit vive en `main` local pero **Vercel está BLOCKED**
(tope del plan free) y producción aún sirve el `shell.css` viejo (`?v=f583ba6a`, sin el reset). Aun así
se añade este blindaje para que **ninguna fuente residual** (overscroll, páginas cortas) lo pueda revivir.

**Cómo/Verificación:** una línea en `shell.css` (fondo en `html, body`). Verificado en navegador:
`getComputedStyle(html).backgroundColor` = `#0d0d10` (oscuro) / `#f5f5f2` (claro), nunca transparente
ni blanco, y coincide con el del `body`. Test `test_shell_sin_margen_blanco_del_body` **reforzado**
(ahora exige que el `html` tenga fondo propio ≠ transparente/blanco y == al del body). `cachebust` al
día (`shell.css?v=56a6ffa1`). Doctor 10/10, tests del shell **8/8 verdes**, ruff limpio. **Pendiente
para que Oscar lo vea: desplegar** (Vercel desbloqueado → Redeploy, o el dominio).

---

## 📱 fix(shell) — drawer móvil + línea blanca de los márgenes (2026-06-20)

**Qué:** dos arreglos de UI reportados:
1. **Lateral móvil → drawer.** En ≤768px el lateral pasaba a **barra inferior**; ahora es un **drawer
   deslizante**: oculto por defecto, se abre con el botón **☰** (arriba-izquierda) y se cierra tocando
   el **backdrop** o un item de navegación. Conserva el lateral completo (marca + nav + perfil + tema).
2. **Línea/marco blanco en los márgenes.** Las páginas que **no cargan `style.css`** (inicio, agenda,
   finanzas, chat) mostraban un marco claro: el `<body>` traía el **margin 8px** por defecto del
   navegador y fondo transparente → se veía el fondo claro del `html`. `shell.css` ahora resetea
   `html, body { margin: 0 }` y `body { background: var(--bf-bg) }` (lo cargan las 9 páginas del shell).

**Por qué:** UX en móvil (un menú lateral de verdad, no una barra que "se va abajo") y coherencia
visual (el marco claro afeaba varias secciones; quedaba bien solo en Explorar/Bandas/Perfil, que sí
cargan `style.css`).

**Cómo/Verificación:** `icons.js` (icono `menu`), `shell.css` (reset del body + `.bf-hamburger`/
`.bf-backdrop` + media query ≤768px reescrita a drawer), `shell.js` (inyecta ☰ + backdrop + toggle
`.bf-nav-open`, cierra al tocar fuera o un item). Verificado en navegador (móvil 390px: el drawer abre
con ☰ y cierra con el backdrop; desktop: `body margin 0` + fondo oscuro, sin marco). e2e
`test_shell_drawer_movil_abre_y_cierra` + `test_shell_sin_margen_blanco_del_body`. `run_checks` VERDE.

---

## 🔔 T-112 — Recordatorios in-app de la agenda (Fase 14) (2026-06-20)

**Qué:** la agenda marca con **⏰ Pronto** los eventos en los próximos 7 días y muestra un resumen
**🔔 N en booking sin confirmar** (eventos en el funnel `lead`/`contacted`/`negotiating`). Todo
calculado en el cliente sobre los eventos que ya carga la agenda.

**Por qué:** continúa la Fase 14 (Booking) con la parte de **recordatorios que NO necesita infra de
envío**. Da visibilidad de un vistazo a lo inminente y a los "deals" de booking abiertos, que es
justo lo accionable del funnel.

**Cómo/Verificación:** solo frontend en `loadAgenda` (`isSoon` + `enBooking`) + CSS `.ev-soon`/
`.agenda-booking-note`. e2e `test_recordatorios_agenda_pronto_y_booking` (evento a 1 día → "Pronto";
un lead → "en booking sin confirmar"). `run_checks` TODO VERDE (174 unit · 81 e2e [+1]). **Diferido:**
recordatorios **por email/push reales** (necesitan infra de envío — Supabase/email, junto a T-047 y
T-113 `EmailTemplate`).

---

## 📇 T-111 — Pipeline de booking en la agenda (`Event.status`) — arranca la Fase 14 (2026-06-20)

**Qué:** la agenda muestra el **estado de booking** de cada evento (badge: Lead · Contactado ·
Negociando · Confirmado · Hecho · Cancelado) y el **admin lo mueve por el funnel** con un selector por
evento (PATCH `status`). El alta de evento permite elegir el **estado inicial** (p. ej. crear un
concierto como "Lead" para arrancar el booking).

**Por qué:** `Event.status` y los 6 estados ya existían en el modelo (CHECK `ck_events_status`) y eran
editables por la API (admin), pero la UI solo mostraba "cancelado" y no dejaba gestionar el funnel.
Es la primera rebanada de la **Fase 14 (Booking, Área 10)**.

**Cómo/Verificación:** solo frontend (badge + selector admin + estado en el alta); backend ya listo
(`update_event` con `require_band_admin`, `status` validado por `Literal`/CHECK). `EVENT_STATUS_LABEL`/
`EVENT_STATUS_ORDER` + CSS `.ev-status`. e2e `test_booking_pipeline_cambiar_estado_de_evento` (crear
como lead → mover a confirmed → el badge cambia). `run_checks` TODO VERDE (174 unit · 80 e2e [+1]).
**Resto de Fase 14 pendiente:** recordatorios (T-112), `EmailTemplate` (T-113), campos de booking
(contacto, caché/fee, `Venue`).

---

## 🎼 T-110 — Apunte por canción en el setlist (`SetlistItem.note`) (2026-06-20)

**Qué:** los setlists de banda admiten una **nota por canción** ("capo 2", "acústica", "aquí hablo al
público"). El editor (`newBandSetlist`) tiene un input por canción seleccionada; se envía
`items:[{song_id, note}]`; el **reproductor** muestra el apunte de la canción actual en la barra del
setlist (`.sl-nav-note`).

**Por qué:** el modelo `SetlistItem.note` y la lectura (`SetlistItemOut.note`) existían desde la Fase
9, pero **no había vía de escritura** (el create solo tomaba `song_ids`) → la nota nunca se podía
rellenar. Es el último hueco "modelo-ya-existe-falta-UI". Útil para recordatorios en directo.

**Cómo/Verificación:** schema `SetlistItemIn` + `items` opcional en `SetlistCreate/Update`
(backward-compat con `song_ids`); `band_setlists_router` persiste la nota (`_set_band_items` con
pares, **filtrando al repertorio** de la banda y conservando posición/nota). Sin migración (la columna
ya existía). unit `test_setlist_de_banda_con_apunte_por_cancion` (round-trip + compat) + e2e
end-to-end (editor → reproductor) + **revisión adversarial** (compatibilidad/aislamiento/XSS/
correctitud) **sin hallazgos**. `run_checks` TODO VERDE. **Diferido:** notas en setlists *personales*
(editor) y editar las notas de un setlist ya creado.

---

## 📤 T-109 — Export CSV de finanzas (cliente) (2026-06-20)

**Qué:** botón **⬇️ CSV** en la sección Finanzas que descarga un CSV de los movimientos (Fecha,
Tipo, Descripción, Importe, Categoría, Evento, Pagado por), generado **100% en el cliente** (Blob +
BOM UTF-8 para Excel; celdas entre comillas con escape). Disponible a cualquier miembro que ve las
finanzas.

**Por qué:** las bandas necesitan llevar sus cuentas fuera (Excel/gestoría). Sin backend ni rutas
nuevas → cero superficie de aislamiento; compone con T-106/T-108.

**Cómo/Verificación:** e2e `test_exportar_finanzas_csv` (descarga real con `expect_download`,
verifica la cabecera y el movimiento en el contenido). `run_checks` TODO VERDE (doctor · ruff · 173
unit · 77 e2e [+1]). **Diferido:** filtros/rango de fechas, export por evento/gira.

---

## 🔗 T-108 — Ligar un movimiento de finanzas a un evento (UI) (2026-06-20)

**Qué:** el modal "Movimiento" (`bands.js::newTransaction`) añade un selector **"Evento (opcional)"**
que carga los eventos de la banda; al registrar envía `event_id`. `loadFinance` muestra la etiqueta
**🎵 {evento}** en cada movimiento ligado (carga los eventos junto a saldos/movimientos).

**Por qué:** `finance_router` ya aceptaba y validaba `event_id` (que el evento sea de la banda) desde
la Fase 11, pero la UI no lo exponía → no se podía saber el coste/ingreso de un **bolo concreto**.
Es la base para un P&L por evento. Compone con T-106 (reparto) y T-107 (hilo por evento).

**Cómo/Verificación:** e2e `test_ligar_movimiento_a_evento` (elegir evento → registrar → la etiqueta
del evento aparece en el movimiento). Título del evento **escapado** en `<option>` y en la etiqueta.
`cachebust` al día; `run_checks` TODO VERDE (doctor · ruff · 173 unit · 76 e2e [+1]). **Diferido:**
resumen/P&L por evento, export CSV, cuotas recurrentes.

---

## 💬 T-107 — Hilo de discusión por evento (chat) (2026-06-20)

**Qué:** cada evento de la agenda (`band.html`, pestaña Agenda) abre un **modal con su hilo de
mensajes** (botón 💬 por evento). Para no duplicar el render del chat, se extrajo `renderMessageList`
(lista + fijar/borrar) y ahora lo reusan **el chat general** (`loadChat`) y el nuevo
`openEventThread`. Los mensajes del hilo llevan `event_id`.

**Por qué:** `messages_router` ya soportaba `?event_id=` (chat general vs hilo de evento) desde la
Fase 12, pero la UI solo exponía el chat general → discutir un **bolo/ensayo concreto** era imposible
desde la app. Aditivo, sin rutas nuevas (reusa endpoints ya con guard de pertenencia).

**Cómo/Verificación:** e2e `test_hilo_de_discusion_por_evento` (abrir el hilo del evento, publicar,
ver el mensaje) + el e2e del chat general sigue verde (confirma que el refactor no rompe nada). CSS
`.thread-list` (modal scrollable). `cachebust` al día; `run_checks` TODO VERDE (doctor · ruff · 173
unit · 75 e2e [+1]). **Revisión adversarial** (3 lentes, solo lectura): aislamiento multi-tenant ✅ y
XSS/escapado ✅ **sin hallazgos**. **Diferido:** hilo embebido en la pestaña (no modal), notificaciones.

---

## 💶 T-106 — Reparto personalizado de gastos en la UI (finanzas) (2026-06-20)

**Qué:** el modal "Movimiento" (`bands.js::newTransaction`) ahora ofrece **A partes iguales /
Personalizado**. En personalizado pinta una fila por miembro activo (la prerrellena a partes iguales
como punto de partida editable), valida **en vivo** que la Σ cuadre con el total (indicador ✓) y
envía `splits:[{user_id, share_amount}]`.

**Por qué:** `finance_router` ya aceptaba y validaba `splits` desde la Fase 11, pero la UI solo
mandaba el reparto por defecto (a partes iguales) → era una capacidad **inalcanzable** desde la app.
Las bandas que reparten desigual (alguien adelanta más, partes distintas) ya pueden registrarlo.

**Cómo/Verificación:** e2e `test_reparto_personalizado_en_movimiento` (elegir personalizado → fila
prerrellena al total → ✓ → registrar con `splits` → backend acepta). El test del reparto igual sigue
verde. CSS `.split-row`/`.split-name`/`.split-sum`. `cachebust` al día. `run_checks` TODO VERDE
(doctor 10/10 · ruff · 173 unit · 74 e2e [+1]). Incluye `fix(conftest)`: deadline del `live_server`
45→90s (en máquina lenta/cargada el arranque tardaba >45s → ERRORs en cascada de los e2e; mismo
criterio que T-042/doctor). **Diferido:** export CSV, ligar el movimiento a un evento desde la UI,
cuotas recurrentes.

---

## 🧹 T-105 — Limpieza: retirado el detalle de banda in-page legacy (openBand) (2026-06-20)

**Qué:** eliminado el código muerto del detalle de banda dentro de `bands.js` (`openBand`, ~91
líneas) y sus huérfanos (`showGrid`/`showDetail`/`elDetail`), el markup `#band-detail` de
`bands.html`, y los fallbacks a `elDetail`/`openBand` en `newBandSetlist` (su único llamador vivo es
`band.js`, que siempre pasa `container`+`onDone`). Cabecera de `bands.js` actualizada.

**Por qué:** desde la Fase 13 (T-075) la ficha de banda vive en `band.html` (espacio con pestañas);
el detalle in-page de `bands.js` quedó sin uso (la grid navega a `band.html`). Era la deuda "retirar
openBand muerto" anotada como pulido opcional en T-081. Menos código muerto = menos confusión.

**Cómo/Verificación:** ningún test dependía del detalle legacy; las 10 funciones de sección +
`initChat` que `band.js` reusa siguen intactas; `node --check` de `bands.js` OK. `cachebust.py` al
día; `run_checks.py` TODO VERDE (doctor 10/10 · ruff · 173 unit · 73 e2e). **Pendiente (opcional):**
conversión completa de las páginas legacy a componentes `bf-*` (refactor visual grande, aparte).

---

## 🩺 fix(doctor) — deadline de arranque del server 25→45 s (2026-06-20)

**Qué:** `harness/doctor.py::wait_until_up` ahora espera 45 s (antes 25) a que el server responda.

**Por qué:** en esta máquina el arranque en frío de uvicorn + el import de la app tarda ~26 s, justo
por encima de los 25 s → el doctor daba un falso negativo ("el servidor no respondió") aunque la app
estaba sana (`/health` 200 medido a los 26 s; el check de navegador, posterior, sí la veía arriba).
Mismo criterio que el deadline del `live_server` de los e2e (subido en T-042).

**Cómo/Verificación:** doctor 10/10 verde de forma estable tras el cambio.

---

## 🎸 T-104 — UI de tablaturas (editor + render) (2026-06-20)

**Qué:** la app ya muestra y edita TABLATURAS. El modelo (`TabLine`) y la API existían desde el giro,
pero el frontend no las tocaba (el parser las leía como letra y el render las descartaba en su `else`).
Ahora:
- **Parser** (`editor.js`): `isTabLine()` reconoce una cuerda de tab ASCII (corrida de ≥2 guiones +
  solo caracteres de tab); `parseRawText` agrupa las cuerdas consecutivas en UNA línea `type:"tab"` con
  el ASCII en `content`. `songToRawText` la reemite → round-trip al editar.
- **Render** (`score_render.js`): una línea `tab` se pinta como `<pre class="line-tab">` con
  `textContent` (escapa solo → anti-XSS). Mismo render en el reproductor y en la vista previa del editor.
- **Estilo** (`style.css`): `.line-tab` monoespaciado, borde coral, `overflow-x:auto` en móvil.

**Por qué:** era la deuda 🟢 más antigua de Fase 5. Las tabs son esenciales para riffs/punteos que no
caben en "acordes sobre letra". Aditivo: no toca la joya — una tab no lleva acordes con id, así que el
motor de sincronización la ignora.

**Cómo/Verificación:** 4 tests JS en navegador real (`tests/e2e/test_js_logic.py`): detección del
bloque, no-colisión con letra/acordes/intro, render seguro (escapa `<img onerror>`) y round-trip del
editor. `cachebust.py` al día; `run_checks.py` TODO VERDE (doctor 10/10 · ruff · 173 unit · 73 e2e).
Prueba visual capturada. **Diferido:** tab "sincronizada" al beat (resaltado por tiempo) con el modelo
estructurado `TabLine.fret_sequence` — encaja con V3-F6; por ahora el ASCII vive en `content` (fuente única).

---

## ✅ Verificado — las 4 migraciones V3 ya están aplicadas en Postgres prod (2026-06-20)

**Qué:** confirmado que producción (`fwynfifvtthtpzpejfhb`) está en el head de Alembic
`e9f1a2b3c4d5` (el head local más reciente), con todos los objetos V3 físicamente presentes:
`songs.reference_url` (T-090); tablas `tours`/`tour_stops`/`tour_budget_lines` (T-093); `bands.plan`
(T-097); y `musical_works`/`public_scores`/`score_ratings`/`score_comments` (V3-F9/T-100).

**Por qué:** el `ROADMAP.md`, `TASKS.md` y `PENDIENTES_OSCAR.md` §6 arrastraban avisos
"⚠️ Migración pendiente en Postgres prod" que **ya no eran ciertos** — las 4 se aplicaron al
desplegar el commit `c3a70d7 feat(v3)`. Mantenerlos arriesgaba intentar re-aplicarlas por error.

**Cómo/Verificación:** consulta de **solo lectura** al Postgres de prod vía el MCP de Supabase
(`SELECT` sobre `alembic_version` + `information_schema`); **sin cambios en la BD**. Actualizados los
avisos obsoletos en `ROADMAP.md`, `TASKS.md` y `PENDIENTES_OSCAR.md` §6.

---

## 🛠️ fix(cachebust) — `?v=` independiente del fin de línea (CRLF/LF) (2026-06-20)

**Qué:** `harness/cachebust.py::_hash` ahora normaliza el fin de línea (CRLF/CR→LF) antes de
calcular el `sha256[:8]`. Reescritos los `?v=` de `auth.js` en los 14 `static/*.html` al hash LF
correcto (`55a0092d`→`32867392`).

**Por qué:** los `?v=` de `auth.js` se habían generado desde una copia **CRLF** (Windows), pero el
repo es **LF** (`.gitattributes: * text=auto eol=lf`). El hash era sensible al EOL, así que
`test_cache_busting_al_dia` **fallaba en cualquier checkout LF** — este Mac y, sobre todo, el **CI
de Linux** (que estaba en rojo sin que se notara). Normalizar el EOL hace que el `?v=` sea idéntico
en Windows/Mac/Linux y elimina la clase de error para siempre.

**Cómo/Verificación:** `run_checks.py` **TODO VERDE** (doctor 10/10 · ruff · 173 unit · 69 e2e) en
un entorno LF recién montado (venv Python 3.12 + deps + Playwright chromium). Solo cambia `auth.js`
(el resto de assets ya coincidían).

---

## 🔐 T-046 — Login con Google (OAuth) CONFIGURADO Y VERIFICADO (2026-06-18)

**Qué:** activado el inicio de sesión con Google. El **código ya estaba** desde antes
(`auth.js::signInGoogle` con `signInWithOAuth({provider:'google', redirectTo:.../app.html})`, botón
"Entrar con Google" en `login.html`, handler en `login.js`); lo único que faltaba era la
**configuración externa del proveedor**, que no vive en el repo:

1. **Google Cloud Console** — proyecto nuevo + credencial *OAuth client ID* (tipo "Web application"):
   - Client ID: `630184504034-bra6igkkrje527klmhms2m06vvfbpun1.apps.googleusercontent.com`.
   - Orígenes JavaScript autorizados: `https://chordflow-ecru.vercel.app` y `http://127.0.0.1:8000`.
   - Redirect URI autorizada: `https://fwynfifvtthtpzpejfhb.supabase.co/auth/v1/callback` (callback de Supabase).
2. **Supabase** — activado el proveedor Google + URLs de retorno, vía **Management API** (no por panel):
   `PATCH https://api.supabase.com/v1/projects/fwynfifvtthtpzpejfhb/config/auth` con
   `external_google_enabled=true`, `external_google_client_id`, `external_google_secret`,
   `site_url=https://chordflow-ecru.vercel.app` y
   `uri_allow_list=".../static/app.html, http://127.0.0.1:8000/static/app.html"` (prod + local).

**Por qué:** era una de las deudas de Fase 5 (`PENDIENTES_OSCAR.md` §2) que requería acción de Oscar
en Google Cloud + Supabase. Reduce fricción de registro/login.

**Cómo/Verificación:** probado en local (`uvicorn` con `/config` `test_mode:false` → Supabase real).
El flujo OAuth completó: Google autenticó a `oscarcon314@gmail.com` (app_metadata `provider: google`)
y devolvió un `access_token` válido a `app.html`. (Un primer intento falló solo porque el servidor
local de fondo se había caído al volver de Google — relanzado de forma persistente y reverificado;
en producción no aplica.) Es **configuración externa de Supabase**, no cubrible por la suite local;
el botón/flujo del front ya estaban cubiertos. ⚠️ Pendiente de Oscar: **revocar el Personal Access
Token `sbp_` de Supabase** usado para el `PATCH` (quedó expuesto en chat).

---

## 🌍 V3 — Red musical con plano público (arranque 2026-06-17)

Aprobada la dirección **V3** (`GUIA_MAESTRA_V3.md`): el salto de "SaaS aislado" a "red musical con
un plano público opt-in". 8 decisiones de fondo cerradas con Oscar (D1–D8) tras un análisis
multiagente. Orden de fases V3-F1→F11 en la guía §6. **Todo aditivo; la V2 (en producción) no se
toca.** Se empieza por **V3-F1 (diseño)** porque es gratis, transversal y sube la percepción de todo.

### 🎨 V3-F1 · T-084 — Estados de UI base en el sistema de diseño (2026-06-17)

**Qué:** añadidos a `static/design-system.css` los estados que separan un "demo" de un "producto",
todos con prefijo `bf-` (no colisionan con el player ni tocan rutas/`band_id`):
- **Deshabilitado:** `.bf-btn:disabled`/`[disabled]`/`[aria-disabled]` (opacidad + `not-allowed`) e
  inputs `:disabled`.
- **Cargando:** `.bf-spinner` reutilizable + botón `[data-loading="true"]` que oculta el texto y
  pinta el spinner (keyframe nuevo `bf-spin`).
- **Skeleton:** `.bf-skeleton` (+ `--text`/`--title`/`--card`) reusando el keyframe `bf-pulse`.
- **Empty state:** `.bf-empty` (icono + título + texto) para listas/vistas vacías.
- **Foco accesible:** `:focus-visible` en `.bf-card--interactive`/`.bf-nav-item`/`.bf-tab`/`.bf-list-item`.
- **Datos:** `.bf-num` (mono + `tabular-nums`) para importes/BPM/contadores.

**Por qué:** la app ya hace mucho, pero le faltaban los estados intermedios (carga, vacío,
deshabilitado) que dan sensación de producto terminado. Es la base de T-087 (aplicarlos a las vistas
agregadas) y del resto de V3-F1.

**Cómo/Verificación:** test `test_design_system_tiene_estados_de_ui` (asserta los 8 estados nuevos);
`cachebust.py` reescrito (8 HTML); `run_checks.py` **TODO VERDE** (doctor 10/10 · ruff · **140 unit**
[+1] · 57 e2e).

### 🎨 V3-F1 · T-085 — Iconos SVG (Lucide auto-alojado) (2026-06-17)

**Qué:** nuevo `static/icons.js` con `bfIcon(name, {size})` que devuelve SVG inline (trazos de
Lucide, MIT) heredando `currentColor`. Cargado **antes de `shell.js`** en las 8 páginas con shell.
El lateral pasa de emojis a iconos SVG: navegación (home/library/calendar/wallet/chat/users/user),
toggle de tema (sun/moon), ajustes (settings) y cerrar sesión (logout). CSS `.bf-nav-icon` ajustado
para centrar el SVG.

**Por qué:** los emojis eran lo que más "amateur" hacía ver la interfaz; los iconos SVG coherentes
son el quick win nº1 de profesionalidad. **Auto-alojado** (no CDN) para respetar el hardening del
proyecto (las CDN se fijan con SRI) y no añadir dependencias externas.

**Cómo/Verificación:** e2e `test_shell_nav_usa_iconos_svg` (≥7 SVG en la nav + `window.bfIcon`
existe y devuelve `<svg>`); `cachebust.py` al día (`icons.js` cargado en las 8 páginas);
`run_checks.py` **TODO VERDE** (doctor 10/10 · ruff · 140 unit · **58 e2e** [+1]).

### 🎨 V3-F1 · T-086 — Teleprompter espectacular (solo CSS) (2026-06-17)

**Qué:** realce visual de la joya en `static/style.css`, **sin tocar** la lógica
(`sync_engine.js`/`score_render.js` por ids/BPM): el acorde activo (`.chord-container.active` y
`.line-chord-only .chord-pill.active`) "respira" con un **glow coral pulsante**
(`@keyframes chord-pulse`, 1.2 s) sobre el scale ya existente; guard `prefers-reduced-motion`
(animación off). Las líneas inactivas pasan de `opacity 0.5 → 0.4` para más contraste teleprompter.

**Por qué:** el teleprompter es la joya del producto; un acorde activo que destaca con vida le da el
toque "producto" sin reescribir nada. El modo escenario/fullscreen (que sí lleva JS) se hará en
**V3-F4 (Modo Directo)**, su sitio natural.

**Cómo/Verificación:** e2e `test_acorde_activo_tiene_glow` (tras reproducir, el `box-shadow`
computado del acorde activo ≠ `none`); los tests del player existentes siguen verdes (render
intacto). `cachebust.py` al día; `run_checks.py` **TODO VERDE** (doctor 10/10 · ruff · 140 unit ·
**59 e2e** [+1]).

### 🎨 V3-F1 · T-087 — Empty states + skeletons en las vistas agregadas + cierre de V3-F1 (2026-06-17)

**Qué:** nuevo helper `window.bfEmpty(icon, title, text, {id})` en `static/icons.js` que genera el
componente `.bf-empty` (de T-084) con icono SVG. Aplicado a los estados vacíos de las vistas
agregadas del contexto TÚ: **Inicio** (sin eventos / sin mensajes), **Agenda** (agenda vacía),
**Finanzas** (sin cuentas) y **Chat** (sin conversaciones). **Inicio** ahora pinta un **skeleton**
(`.bf-skeleton`) mientras carga, en vez de un texto "Cargando…".

**Por qué:** cierra el círculo de T-084 (definir los estados) aplicándolos donde se ven; los empty
states con icono y el skeleton de carga son lo que da sensación de "producto terminado".

**Cómo/Verificación:** e2e `test_ui_helper_empty_state` (el helper genera `.bf-empty` + `<svg>`;
DB-independiente porque el `live_server` e2e comparte BD de sesión y un "vacío real" sería frágil);
los tests de las vistas (camino con datos) siguen verdes. `cachebust.py` al día; `run_checks.py`
**TODO VERDE** (doctor 10/10 · ruff · 140 unit · **60 e2e** [+1]).

**✅ V3-F1 (pulido de diseño profesional) COMPLETA** — T-084 (estados de UI), T-085 (iconos SVG
Lucide auto-alojados), T-086 (teleprompter espectacular), T-087 (empty states + skeletons). Todo
aditivo, `bf-`-prefijado o solo-CSS; la joya y las rutas intactas. Es una fase de **pulido
transversal de front** (sin rutas nuevas) → no aplica `revision.py`. Siguiente: **V3-F2** (mapa de
estructura + bolita de posición, modo solitario).

### 🎯 V3-F2 · T-088 — Bolita de posición (client-side, modo solitario) (2026-06-17)

**Qué:** indicador de posición en la canción dentro del reproductor: una **barra de progreso**
(`#song-progress` con relleno + dot luminoso en el borde superior de la barra inferior) y la
**sección actual** (`#current-section-display`). Todo derivado del **timeline de beats que la
canción ya tiene** (`state.currentBeat`/`state.totalBeats` del motor), calculado en `app.js`
(controlador) + estilos en `style.css`. **`sync_engine.js` y `score_render.js` (la joya) no se
tocan**; `computeSectionRanges()` replica la misma lógica de cursor del motor para ubicar la sección.

**Por qué:** era la parte de la "idea 2" de Oscar que mejora la joya **para todos sin infraestructura
ni coste** (modo solitario). Decisión de implementación: hacerla **client-side** sobre los beats
existentes en vez de crear ya las entidades `ArrangementMap`/`ArrangementSegment` — esas solo hacen
falta cuando una canción importada no trae buenos tiempos, y encajan mejor junto al **sync de ensayo
(V3-F6)**, donde el re-timing aporta de verdad. **Diferido y anotado**, no descartado.

**Cómo/Verificación:** e2e `test_bolita_de_posicion_avanza` (tras reproducir, el relleno pasa de 0%
y se muestra la sección); los tests del player existentes siguen verdes (motor intacto).
`cachebust.py` al día; `run_checks.py` **TODO VERDE** (doctor 10/10 · ruff · 140 unit · **61 e2e** [+1]).

### 🎤 V3-F4 · T-089 — Modo Directo (escenario a pantalla completa) (2026-06-17)

**Qué:** botón ⛶ en el reproductor que activa el **Modo Directo**: añade la clase `stage-mode` al
`<body>` (oculta la barra superior, agranda la letra y los acordes, máximo contraste de escenario) y
entra en **pantalla completa** (Fullscreen API). Funciona aunque el navegador bloquee el fullscreen
(la clase es independiente). Sale con el propio botón, con **Esc** o al abandonar el fullscreen.
`index.html` (botón) + `style.css` (`.stage-mode …`) + `app.js` (toggle/Fullscreen/Esc). **La joya
(`sync_engine.js`/`score_render.js`) no se toca.**

**Por qué:** es la herramienta de directo/ensayo más visible y la que más "enamora" en el escenario;
y es client-side y gratis.

**Cómo/Verificación:** e2e `test_modo_directo_alterna_y_oculta_barra` (al activar: `stage-mode`
presente, barra superior `display:none`, letra >24px; al desactivar: vuelve todo). `cachebust.py`
al día; `run_checks.py` **TODO VERDE** (doctor 10/10 · ruff · 140 unit · **62 e2e** [+1]).

### 🎬 V3-F4 · T-090 — Vídeo de referencia (YouTube) en el reproductor (2026-06-17)

**Qué:** campo nuevo **`Song.reference_url`** (enlace YouTube/Spotify) + su uso en el player:
- **Backend:** columna `reference_url String(512) nullable` en el modelo `Song`, en `SongBase`/
  `SongUpdate` (Pydantic) y **migración aditiva** `b3f1a9c2d4e5` (batch mode). `alembic check` sin
  drift (validado por `tests/unit/test_migrations.py` en BD limpia).
- **Editor:** input "Enlace de referencia (YouTube)" que se carga y se guarda con la canción.
- **Player:** botón 🎬 (visible solo si la canción tiene un enlace de YouTube válido) que abre un
  **panel flotante** con el vídeo embebido (`youtube.com/embed/<id>`, id parseado y validado por
  regex `[A-Za-z0-9_-]{11}` → seguro). v1 = referencia manual (no sincronizada al beat; la sincronía
  fina con audio se valoró en la guía V3 §2.3 y depende de Storage/realtime).

**Por qué:** "escuchar el original mientras lees la partitura" es una de las peticiones de Oscar
(idea 2) y un quick win client-side y gratis.

**Cómo/Verificación:** e2e `test_video_de_referencia_youtube` (botón visible + iframe con el id) y
`test_sin_referencia_no_hay_boton`. `cachebust.py` al día; `run_checks.py` **TODO VERDE** (doctor
10/10 · ruff · 140 unit · **64 e2e** [+2]). ⚠️ **Pendiente: aplicar la migración a Postgres prod**
(en local aplicada; las migraciones a prod las hace Oscar en el deploy, como en el resto del giro).

### 🎸 V3-F4 · T-091 (afinador) + T-092 (pasapáginas) + cierre de V3-F4 (2026-06-17)

**T-092 — Pasapáginas / pedalera:** las teclas de avance/retroceso que envían los pedales Bluetooth
(PageDown/PageUp y flechas) pasan de canción dentro de un setlist o, si no hay setlist, hacen scroll
de una página en la partitura. Manos libres en el atril; se ignora en campos de texto. `app.js`.
e2e `test_pasapaginas_hace_scroll`.

**T-091 — Afinador integrado** (`static/tuner.js`): detección de tono por **autocorrelación**
expuesta como **función pura** (`window.bfDetectPitch` + `window.bfFreqToNote`) — testeable con una
onda sintética **sin micrófono** — y, aparte, el plumbing de micro (Web Audio `getUserMedia` →
`AnalyserNode` → bucle rAF) con un panel en el player que muestra nota, cents y una aguja. Botón 🎤.
e2e `test_afinador_detecta_y_abre` (440 Hz → La4 + apertura/cierre del panel).

**✅ V3-F4 (quick wins de directo) COMPLETA** — Modo Directo (T-089), vídeo de referencia (T-090),
afinador (T-091), pasapáginas (T-092). Todo client-side y gratis; la joya intacta. Diferido a V3-F6:
loop A-B / tempo trainer y metrónomo *lookahead* (requieren seek/bucle en el motor).
`run_checks.py` **TODO VERDE** (doctor 10/10 · ruff · 140 unit · **66 e2e** [+2]).

### 🚌 V3-F5 · T-093/094/095 — Backend de giras (2026-06-17)

**Qué:** módulo nuevo de **gestión de giras** (backend), aislado por `band_id`:
- **Modelos** `Tour` (nombre, status `planning|active|done|cancelled`, fechas, notas, soft-delete),
  `TourStop` (parada de la ruta, opcionalmente ligada a un `Event(concert)` de la banda, `position`,
  ciudad, notas) y `TourBudgetLine` (presupuesto **estimado**; el gasto real sigue en `Transaction`).
  Enum `TOUR_STATUSES`. **Migración aditiva** `c5d7e9f1a2b3` (3 tablas + índices `band_id`/FKs + CHECK,
  batch). `alembic check` sin drift (validado en BD limpia por `test_migrations`).
- **Router** `tours_router.py` (`/bands/{id}/tours` + `/stops` + `/budget`): crear/editar/borrar gira y
  paradas/líneas **solo admin**; miembros listan/ven. Las paradas que ligan un evento **validan que
  sea de esta banda** (400 si es ajeno). El detalle enriquece cada parada con el título/fecha del
  evento y calcula el **presupuesto total**. Registrado en `main.py`.

**Por qué:** la gira es un módulo de alto valor y **aislado** (no toca la capa pública), por eso se
adelanta en la V3 (decisión D4). No duplica Agenda ni Finanzas: las **agrega** (paradas = conciertos
existentes; presupuesto = estimación que luego se contrasta con los `Transaction` reales).

**Cómo/Verificación:** `test_api_tours` (5 casos: admin crea/miembro no, paradas ligadas + evento
ajeno 400 + posiciones, presupuesto suma total, CRUD admin/miembro 403, **aislamiento** ajeno→404 en
cada ruta). `run_checks.py` **TODO VERDE** (doctor 10/10 · ruff · **145 unit** [+5] · 66 e2e).
⚠️ **Pendiente: aplicar la migración a Postgres prod.** Falta el **frontend** (T-096: pestaña Giras).

### 🚌 V3-F5 · T-096 — Frontend de giras + cierre de V3-F5 (2026-06-17)

**Qué:** pestaña **Giras** en el espacio de banda (`band.js`, autocontenida): lista de giras (nombre,
estado, nº de paradas, presupuesto total), **crear gira** (admin, `promptModal`), y **detalle** con la
**ruta** (paradas, cada una con su ciudad y el concierto ligado de la banda) y el **presupuesto** con
total y categorías. Admin añade/quita paradas (eligiendo un concierto de la agenda o solo ciudad) y
líneas de presupuesto; miembros lo ven en solo lectura.

**Por qué:** completa la gestión de giras (la parte visible) sobre el backend de T-093/095.

**Cómo/Verificación:** e2e `test_band_space_giras` (crear gira por UI + abrir detalle con ruta y
presupuesto). `cachebust.py` al día; `run_checks.py` **TODO VERDE** (doctor 10/10 · ruff · 145 unit ·
**67 e2e** [+1]).

**✅ V3-F5 (gestión de giras) COMPLETA.** Diferido (anotado, no bloquea): **mapa Leaflet+OSM** (para
no añadir una CDN nueva sin SRI ahora), ligar el gasto real (`Transaction`) a la gira desde la UI, y
la co-organización con otra banda (Opción 0 informativa). ⚠️ **Pendiente: aplicar la migración de
giras a Postgres prod** en el próximo deploy.

### 🧱 V3-F3 · T-097 (`Band.plan`) + T-098 (gate de aislamiento) (2026-06-17)

**T-097 — Andamiaje de planes SaaS** (D8, sin cobro): columna `Band.plan` ('free'|'pro', default
'free') + enum `BAND_PLANS` + **migración aditiva** `d7e9f1a2b3c4`. Expuesto en `BandResponse` y
`BandSummary`; un **admin** lo cambia vía `PATCH /bands/{id}` (validado por `Literal BandPlan`;
inválido→422). La validación vive en la capa API (sin CHECK de BD para no recrear la tabla `bands`,
muy referenciada). Test `test_band_plan` (default free, admin cambia a pro, aparece en "mis bandas",
inválido 422, miembro 403). Prepara la monetización sin retrofit por fase.

**T-098 — Gate de aislamiento parametrizado**: `test_aislamiento_parametrizado.py` recorre **16 rutas
de banda** (bandas, miembros, repertorio, setlists, agenda, finanzas, mensajes, giras) y exige que un
usuario **ajeno** reciba 403/404. Es una red de seguridad transversal sobre la "regla de oro": si
alguien añade una ruta de banda y olvida el guard, este test lo caza.

**Verificación:** `run_checks.py` **TODO VERDE** (doctor 10/10 · ruff · **163 unit** [+18] · 67 e2e).
⚠️ **Pendiente: aplicar la migración de `plan` a Postgres prod.**

**Límite alcanzado:** con esto se completa **toda la parte de la V3 que es código y gratis**. Lo que
queda (Storage, Realtime, capa pública/biblioteca global/red, pagos) **requiere configuración de
Supabase/Stripe por parte de Oscar** — ver `PENDIENTES_OSCAR.md`.

### 🌍 V3-F9 · Biblioteca global (catálogo público) — backend + revisión ultracode (2026-06-17)

**Qué (T-100/101):** el **reclamo de la app** (D9). Modelos `MusicalWork` (canción abstracta) +
`PublicScore` (versión publicada, snapshot independiente) + `ScoreRating` + `ScoreComment`, en un
**plano de datos SEPARADO** (copia desacoplada, D1). Migración `e9f1a2b3c4d5`. Router `/catalog`:
**publicar** ("ponla aquí"), **buscar**, **detalle** (con la partitura para el visor), **importar**
a banda/personal, **valorar** (1–5), **comentar**. Test `test_api_catalog`.

**Revisión ultracode (T-102):** workflow adversarial multi-agente (33 agentes, ~1.4M tokens, 20
hallazgos confirmados). Aplicado:
- **C1 (crítico, D2):** la vista pública (`GET /catalog/scores/{id}`) ahora **recorta la letra**
  (`_public_sections`, umbral `_LYRIC_PREVIEW`); el `content_json` guarda la letra completa y solo se
  entrega **al importar**. Test `test_letra_recortada_en_publico_completa_al_importar`.
- **H1/M1/M2:** snapshot COMPLETO para round-trip exacto (tabs `tab_strings`, `repeat_count`,
  `color_tag`, `display_hint`, y `reference_url` como columna). Test de round-trip de `reference_url`.
- **H3/M4:** `try/except` con rollback+log en escrituras; **carrera de `MusicalWork`** (SELECT-then-
  INSERT) resuelta con `IntegrityError`→re-SELECT.
- **H4 (D9):** no republicar la misma canción (`source_song_id`→409). Test `test_no_republicar…`.
- **M3:** `rating_avg` como `Decimal` (coherente con finanzas). **L1:** import valida banda no borrada.
  **M6/L2:** índice compuesto `(status, deleted_at)` + `updated_at`.
- **Diferido (anotado):** XSS escaping (se hará en el frontend, que aún no existe), rate-limit/moderación
  de comentarios. El **umbral de recorte de letra** es decisión legal de Oscar (ajustable).

**Verificación:** `run_checks.py` **TODO VERDE** (doctor 10/10 · ruff · **177 unit** · 67 e2e).
⚠️ **Pendiente: aplicar la migración del catálogo a Postgres prod.** Falta el **frontend** (T-103).

### 🌍 V3-F9 · T-103 — Frontend de la biblioteca global + cierre de V3-F9 (2026-06-17)

**Qué:** `static/biblioteca-global.html` + `catalogo.js` (sección **Explorar** del shell): buscador
del catálogo, el reclamo **"¿no la encuentras? ponla aquí"** (→ editor), **detalle** con vista previa
de la partitura (reusa `score_render.js`, con la **letra recortada**), **importar** a una banda mía o
a mis partituras, **valorar** (estrellas) y **comentar**. Nuevo item **"Explorar"** (icono globo) en
el lateral (`shell.js`). **D9 por defecto:** al guardar una canción NUEVA en el editor (`editor.js`),
se **publica automáticamente** al catálogo (best-effort, no bloquea el guardado). Todo el texto de
usuario va **escapado** (cierra el hallazgo H2 de la revisión).

**Por qué:** completa la pieza que para Oscar es la más importante (la visión global) y la deja usable
de punta a punta: añadir una canción la sube al catálogo, y cualquiera la busca/importa.

**Cómo/Verificación:** e2e `test_catalogo` (buscar + abrir detalle con importar/estrellas; "Explorar"
navega desde el lateral). `cachebust.py` al día; `run_checks.py` **TODO VERDE** (doctor 10/10 · ruff ·
**177 unit** · **71 e2e** [+4]).

**✅ V3-F9 (biblioteca global) COMPLETA** — backend + revisión ultracode + frontend. Diferido (próxima
revisión/pulido): navegación pública SIN login + SEO (necesita el plano público/Supabase), moderación,
importar directo a banda desde la tarjeta, afinar el umbral de recorte de letra.

---

## 🚀 Estado actual (2026-06-16) — EN PRODUCCIÓN: giro V2 completo (BandFlow)

**En vivo (https://chordflow-ecru.vercel.app): TODO el giro V2** — Fase 5/6 (teleprompter, import IA,
PWA, PDF, setlists) **+ Fases 7–13** (bandas multi-tenant: repertorio, setlists, agenda, finanzas,
chat · app shell BandFlow · vistas agregadas · reskin · rebranding). Desplegado el 2026-06-16
(commit `29bd505`): push a `main` → Vercel (deployment READY) + **6 migraciones aplicadas** a la
Postgres de producción (head `7022a3162284`). Verificado: `/health` ok, `manifest`=BandFlow.
Pendiente solo: **comprobación a ojo del flujo logueado** + **rotar secretos** (`PENDIENTES_OSCAR.md`).

- **Despliegue (Fase 6):** repo GitHub privado `kabalah314-ux/chordflow` (rama `main`, auto-deploy en
  cada push) · **Vercel** (`api/index.py` ASGI + `vercel.json` + `.vercelignore`) · **Supabase** para
  auth (proyecto `fwynfifvtthtpzpejfhb`, claves nuevas `sb_publishable_/sb_secret_`) · **Postgres de
  Supabase** como BD (pooler eu-central-1; local sigue en SQLite). Env vars en Vercel: `DATABASE_URL`
  (pooler 6543), `SUPABASE_URL/ANON_KEY`, `CHORDFLOW_LOG_STDOUT=1`, `OPENROUTER_API_KEY/MODEL`.
  Login real verificado; cuenta de prueba `oscarcon314@gmail.com` / `Chordflow2026!`.
- **Features de producto (Fase 5) EN VIVO:** importar desde URL con IA (T-045, OpenRouter gratuito
  `openai/gpt-oss-120b:free` + lector Jina con fallback a descarga directa), responsive móvil/tablet,
  PWA instalable (manifest+SW), export PDF (impresión), y **setlists/repertorios** (crear/ordenar/
  reproducir en orden con barra ◀▶ en el reproductor).
- **Calidad:** `run_checks.py` TODO VERDE. Migraciones Alembic: en **producción** el head es
  `3684ab6335e8` (Fase 5/6); las **6 migraciones del giro V2** están aplicadas **solo en local**
  (SQLite), pendientes de la Postgres de producción.
- **Pendiente (siguiente hilo):** 🟢 **Tablaturas** (UI de `TabLine`) · 🔵 **T-046 Google login**
  (requiere crear OAuth en Google Cloud + activar en Supabase — pasos en el ROADMAP) · ✉️ **T-047
  emails con marca** (Supabase Email Templates). Detalle de cada feature más abajo (Fase 5/6 y T-045).
- ⚠️ **Seguridad:** rotar la `sb_secret_` y la contraseña de Postgres (se compartieron en chat).

### 🧹 Revisión de coherencia (2026-06-16, previo a Fase 13)

Revisión general de la app antes del reskin. Arreglado:
- **Alcance de "EN PRODUCCIÓN" sincronizado:** el titular de `REGISTRO`/`TASKS` daba a entender que
  todo (incl. el giro V2) estaba en vivo. Aclarado: en producción está **Fase 5/6**; el **núcleo V2
  (Fases 7–12)** está en local, pendiente de push + migraciones a Postgres prod.
- **Salida de `join.html` sin código (`join.js`):** los estados sin acción (falta code / 404 /
  caducada / error) ahora muestran un enlace **«🎸 Ir a mis bandas»** (antes solo se escapaba por el
  icono de cabecera). e2e `test_join_sin_codigo_ofrece_salida`. Doctor 10/10 · `cachebust` al día.
- **Pendiente de decisión (no es bug):** marca **ChordFlow → BandFlow** (rebrand visible = T-082) y
  navegación común (la resuelve el shell T-074). Anotado para la Fase 13.

### 🎨 Fase 13 · Fase A — Tokens BandFlow (actualiza T-073) (2026-06-16)

**Qué:** reescritos los tokens de `static/design-system.css` al look del prototipo BandFlow, según
la spec maestra `harness/diseno/BANDFLOW_SPEC.md` §2 (extraída por workflow del prototipo de Claude
Design). **Solo tokens**: ninguna página adopta aún `bf-*` (eso es el shell, T-074).
- **Acento:** azul `#6c8cff` → **naranja coral `#ff6b4a`** (claro `#ee5530`); focus de inputs recoloreado.
- **Tokens nuevos:** `--bf-accent-weak`, `--bf-hover`, y `*-weak` de success/danger/warning.
- **Tipografía:** Inter/Roboto Mono → **IBM Plex Sans + IBM Plex Mono** (`@import` autocontenido en el
  propio CSS); `--bf-fw-bold` 800→700.
- **Superficies/texto/bordes/sombras** ajustados a la paleta (oscuro casi-negro `#0d0d10`, claro hueso
  `#f5f5f2`); sombras a 2 niveles tematizados. Lateral 248→252px. Añadidos keyframes `bf-fade/pulse/eq`.
- **Tema:** se conserva `:root[data-theme="light"]` (decisión de Oscar) — no se migra a `data-bf-theme`.
**Por qué:** fundación visual única; al reescribir tokens, todo lo que use `bf-*` hereda el aspecto.
**Verificación:** doctor 10/10 · `test_design_system.py` (3, incl. `…adopta_paleta_bandflow`) verde ·
CSS balanceado (64/64) · `@import` antes de toda regla · `cachebust` (design-system.css aún sin enlazar).

### 🧭 Fase 13 · T-074 — App shell (contexto TÚ) (2026-06-16)

**Qué:** cascarón autenticado de BandFlow. Nuevos `static/shell.js` + `static/shell.css` +
`static/app.html` (anfitriona). `shell.js` inyecta el **lateral fijo** en cualquier página con
`.bf-shell`: marca (logo coral con ecualizador `bf-eq` + wordmark "BandFlow"), eyebrow **TÚ**,
**navegación** (Inicio·Biblioteca·Agenda·Finanzas·Chat·Bandas·Perfil) con item activo
(`aria-current`), tarjeta de **perfil** (nombre real vía `GET /profile/me`, iniciales derivadas) y
**toggle de tema** (`data-theme`, persistido en `localStorage`). Responsive: ≤768px → barra inferior.
- **Páginas aún no construidas** (Agenda/Finanzas/Chat, T-078/079/080) salen como items **«Pronto»**
  que avisan con toast en vez de llevar a un 404. Inicio (app.html) es placeholder hasta T-076.
- **`app.html`** es la **primera página que enlaza `design-system.css`** y usa clases `bf-*` →
  estrena el look BandFlow en pantalla (verificado por captura en tema oscuro y claro).
- **Marca:** las superficies nuevas de la Fase 13 nacen como **BandFlow**; las páginas legacy
  siguen "ChordFlow" hasta el barrido de T-082.
**Por qué:** unifica la navegación (antes dispersa por página) y da el contexto multi-tenant TÚ.
**Verificación:** e2e `test_shell.py` (4: aparece+marca activo, navega a Bandas, item "Pronto" no
navega, toggle de tema) · doctor 10/10 · `cachebust --check` al día · ruff limpio.

**Pendiente (siguiente):** T-075 (contexto BANDA: banner + pestañas, refactor de `bands.js`). El
shell deja el hueco del banner condicional ya previsto en la spec §3.

### 🔌 T-074b — Shell como entrada por defecto + enlazado desde legacy (2026-06-16)

El shell ya no es una página huérfana: ahora es el **punto de entrada** y es **alcanzable** desde
las páginas existentes (resuelve el apunte que quedó abierto en T-074).
- **Entrada por defecto:** `GET /` (`main.py`) y los rebotes post-login (`login.js`: email/registro/
  sesión activa; `auth.js`: `redirectTo` de Google OAuth) ahora van a **`app.html`** (antes `library.html`).
- **Vuelta desde legacy:** añadido enlace **🏠 Inicio → `app.html`** en la nav de `library`, `bands`,
  `setlists`, `profile` e `index` (reproductor). `editor`/`join` se dejan (modos puntuales).
- **PWA:** `manifest.json` `start_url` `/static/library.html` → **`/static/app.html`** (la app
  instalada abre el shell). `name`/`theme_color` "ChordFlow" se difieren al rebrand T-082.
- Chequeos ajustados: `doctor.py` ("GET / redirige al inicio (app shell)"), `test_smoke.py`
  (carga `app.html` sin errores JS + comentario del rebote actualizado).
- Incidental: arreglado orden de imports (ruff I001) en `harness/seed_demo.py` (preexistente, dejaba
  `run_checks` en rojo).
**⚠️ Implicación de producción:** al desplegar, la pantalla de entrada pasa a ser el shell BandFlow
(Inicio aún placeholder hasta T-076, pero es un hub con nav + accesos directos, y auth-gated igual
que antes). La transición visual shell(BandFlow)→páginas legacy(ChordFlow) se cierra en el reskin T-081.
**Verificación:** `run_checks.py` **TODO VERDE** (doctor 10/10 · ruff · 125 unit · 49 e2e) ·
`GET /` → 307 → `/static/app.html` (TestClient) · `cachebust --check` al día.

### 🎛️ T-075 — Espacio de banda en el shell (incrementos 1-3) (2026-06-16)

Nuevo `static/band.html` + `static/band.js`: banner de banda + **pestañas** (Miembros·Repertorio·
Setlists·Agenda·Finanzas·Chat) dentro del shell BandFlow. Decisión: **vista nueva en paralelo**, sin
tocar el detalle in-page de `bands.html` (que mantiene sus e2e).
- **Reúso sin duplicar:** `band.js` reutiliza las funciones globales de `bands.js`
  (`loadRepertoire`/`loadBandSetlists`/`loadAgenda`/`loadFinance`/`initChat`/`copyFromPersonal`/
  `newEvent`/`newTransaction`/`newSettlement`/`generateInvite`); los paneles usan los mismos ids
  (`#b-repertoire`, `#b-agenda`…). Carga **perezosa** por pestaña.
- **`bands.js` hecho reutilizable:** guardado el init (la rejilla/botón pueden no existir) → se puede
  incluir en `band.html` sin auto-arrancar `loadBands()`.
- **Puente no rompedor:** enlace «🎛️ Nueva vista» en el detalle legacy → `band.html?id=`.
- **Banner:** color derivado de `band_id` (el modelo no expone color; spec §gap #1). Badge de rol,
  contador de miembros, botón Invitar (admin), «← Mis bandas».
- **band.html** enlaza `style.css`+Inter (contenido reusado + modales) **y** `design-system.css`+
  `shell.css` (shell/banner/pestañas) — puente de CSS durante la migración (reskin del contenido = T-081).
- **Diferido (incremento 4):** desacoplar el **editor "crear setlist"** (`newBandSetlist`, atado a
  `elDetail`/`openBand`) y rerutar la lista de `bands.html` → `band.html` (con actualización de sus e2e).
**Verificación:** `run_checks.py` **TODO VERDE** (doctor · ruff · 125 unit · 52 e2e). Nuevo e2e
`test_band_space.py` (3: banner+pestañas, pestaña reusa repertorio, id inválido → error elegante).
Verificado en captura (banner + pestaña Repertorio reusando `loadRepertoire`).

### 🎛️ T-075 — Espacio de banda (incremento 4: integración + Resumen/Ajustes) ✅ (2026-06-16)

Cierra T-075. La ficha de banda **es ya** `band.html` (en el shell):
- **Editor «crear setlist» desacoplado:** `newBandSetlist(bandId, {container, onDone})` — por defecto
  conserva el flujo legacy (`elDetail`/`openBand`, su e2e intacto), y `band.js` lo integra en la
  pestaña Setlists (editor en su propio contenedor, vuelve recargando la lista).
- **Reruteo:** la lista de `bands.html` y `createBand` ahora navegan a **`band.html?id=`** (la rejilla
  «Mis bandas» sigue en `bands.html`; el detalle in-page legacy queda sin usar → se retira en T-081).
- **Pestañas nuevas:** **Resumen** (descripción + contadores) y **Ajustes** (admin: editar
  nombre/descripción vía `PATCH /bands/{id}`, borrar banda vía `DELETE`). Total 8 pestañas.
- **Shell:** la tarjeta de perfil del lateral ya muestra el nombre real (`GET /profile/me`).
- **Tests migrados:** los 6 e2e de `test_bands_ui.py` que abrían el detalle in-page ahora siguen el
  flujo `band.html` (mismos ids reusados → cambio mecánico: navegar + clic de pestaña).
**Verificación:** `run_checks.py` **TODO VERDE** (doctor · ruff · 125 unit · 52 e2e). Verificado en
captura (pestaña Ajustes con form `bf-*` + perfil "Dani Vega" en el lateral).

### 🏠 T-076 — Inicio (dashboard agregado) ✅ (2026-06-16)

El placeholder de `app.html` es ya un **dashboard real** que agrega TODAS mis bandas.
- **Backend nuevo:** `src/api/me_router.py` → `GET /me/dashboard` (registrado en `main.py`). Devuelve
  **próximos eventos** (futuros, no cancelados, ordenados por fecha, con mi asistencia) y **últimos
  mensajes**, ambos con **etiqueta de banda**. Schemas `DashboardEvent/Message/Response`.
- **Aislamiento (regla de oro):** solo consulta bandas donde soy miembro **activo** → una banda
  ajena nunca aparece. Test dedicado `test_dashboard_aislamiento_excluye_banda_ajena`.
- **Front:** `static/home.js` (nuevo; `app.js` ya existe para el reproductor) pinta saludo + dos
  tarjetas (eventos/mensajes) con `bf-*`; cada item enlaza a `band.html?id=`. `app.html` lo monta.
- **PWA:** añadido `me` al regex de endpoints dinámicos de `sw.js` (no cachear datos de `/me/...`).
**Verificación:** `run_checks.py` **TODO VERDE** (doctor · ruff · **129 unit** · **53 e2e**). Nuevos
`test_api_dashboard.py` (4: vacío, agrega con etiqueta, excluye pasados, **aislamiento**) y
`test_home.py` (1, e2e). Verificado en captura (2 bandas agregadas, ordenadas por fecha).

### 📚 T-077 — Biblioteca unificada ✅ (2026-06-16)

`library.js` ahora une **canciones personales** (`GET /songs/`) + **repertorio de cada una de mis
bandas** (`GET /bands/{id}/songs/`), con **filtro Todas·Personales·[banda]** y búsqueda en vivo.
- Cada tarjeta lleva un **badge de fuente** (👤 Personal / 🎸 nombre de banda).
- Las de banda son **solo lectura** aquí (se reproducen; editar/quitar se hace en el espacio de
  banda) → sin botones editar/borrar; las personales conservan ambos.
- Estados vacíos por filtro (onboarding en Personales sin partituras; «sin resultados» en búsqueda).
- **Solo frontend** (`library.html`+`library.js`+`style.css` chips de filtro). Sigue en look legacy
  ChordFlow hasta el reskin T-081.
**Verificación:** `run_checks.py` **TODO VERDE** (129 unit · **54 e2e**). `test_library.py`: 2 casos
adaptados al modelo unificado (vacío→filtro Personales; borrar→sin asumir grid vacío) + nuevo
`test_biblioteca_unificada_filtra_por_banda`. Verificado en captura (personal + banda con badges).

### 📅 T-078 — Agenda agregada ✅ (2026-06-16)

Agenda del contexto TÚ: todos los eventos de mis bandas en una vista, con etiqueta y filtro.
- **Backend:** `GET /me/events` (`me_router.py`) → TODOS los eventos (próximos + pasados, excl.
  cancelados) de mis bandas activas, con etiqueta y mi asistencia. Reusa schema `DashboardEvent` y
  el helper `_my_band_names` (extraído, DRY con el dashboard). **Aislado** (solo mis bandas activas).
- **Front:** `agenda.html` (host shell) + `agenda.js`: separa Próximos/Pasados, **filtro por banda**
  (chips `bf-btn`), badge de banda + mi asistencia; cada evento enlaza a `band.html`. Marcar
  asistencia/crear se hace en el espacio de banda.
- **Shell:** el item «Agenda» del lateral ya no es «Pronto» → enlaza a `agenda.html`.
**Verificación:** `run_checks.py` **TODO VERDE** (**132 unit** · **57 e2e**). Nuevos: unit
`test_me_events_*` (agregación con etiqueta + **aislamiento**), e2e `test_agenda.py` (próximos+pasados
+filtro) y `test_shell_agenda_navega`.

### 💶 T-079 — Finanzas agregada ✅ (2026-06-16)

`GET /me/balances` (`me_router.py`, reusa `compute_balances` y `_my_band_names`, **aislado**) →
mi saldo neto en cada banda. Front `finanzas.html` + `finanzas.js`: lista por banda con color
(verde te-deben / rojo debes / al-día), enlace a `band.html`. «Finanzas» ya no es «Pronto» en el
lateral. Schema `MyBandBalance`. unit `test_me_balances_lista_mis_bandas_aislado` + e2e
`test_finanzas.py`. `run_checks` VERDE.

### 🔬 Revisión ultracode de los endpoints `/me/*` + fixes (2026-06-16)

Workflow adversarial (19 agentes: 4 lentes → verificación de cada hallazgo → síntesis). **Veredicto:
sin fuga de aislamiento multi-tenant; listo.** 14 hallazgos, 11 confirmados (2 bugs reales + huecos
de cobertura). **Arreglado:**
- **#1 (TZ, medium):** `field_validator` en `EventCreate`/`EventUpdate` normaliza `starts_at`/`ends_at`
  aware→naive-UTC (`_to_naive_utc` en `schemas.py`); evita desfase de inputs con offset ≠ UTC.
- **#2 (coherencia, medium):** el dashboard solo incluye chat general — añadido `Message.event_id.is_(None)`
  a `recent_messages` (los comentarios de hilo de evento ya no se mezclan).
- **#3 (regresión aislamiento):** tests nuevos para miembro `status='left'` y banda borrada
  (antes solo se probaba el "no miembro").
- **#5 (cancelados):** test de que eventos `cancelled` no aparecen en dashboard ni `/me/events`.
- **#6 (UX):** `agenda.js` separa eventos «Sin fecha» en su propia sección (no bajo «Pasados»).
- **#7 (robustez):** `library.js` guarda el listener si faltan ids.
- Huecos de cobertura menores (#4/#8/#10/#11) anotados; no bloquean.
**Verificación:** `run_checks.py` **TODO VERDE** (doctor · ruff · **137 unit** · **58 e2e**).

### 💬 T-080 — Chat agregado ✅ (2026-06-16)

`GET /me/conversations` (`me_router.py`, aislado) → una conversación por banda (chat general) con
su último mensaje; bandas con mensajes primero. Front `chat.html` + `chat.js`: lista con avatar de
banda + preview del último mensaje; entrar abre el chat en `band.html`. «Chat» ya no es «Pronto»
→ **el lateral ya no tiene ningún item pendiente** (todas las secciones existen). Schema
`MyConversation`. unit `test_me_conversations_*` + e2e `test_chat.py`. Quitado el test obsoleto
`test_shell_items_pronto` (ya no hay items `data-soon`). `run_checks` **TODO VERDE**.

### 🎨 T-081 — Reskin de páginas legacy ✅ (2026-06-16)

Re-tematizado `static/style.css` a la paleta BandFlow: acento **cian → coral** (`--accent-color`,
`--chord-color` y los 14 literales `rgba(0,242,255,…)` → coral), fondo casi-negro `#0d0d10`, texto
`#ededf1`, y **IBM Plex** (Sans/Mono) vía `@import` (como el design-system). Así **todas** las
páginas legacy (login, biblioteca, editor, reproductor, setlists, bandas, perfil, join) adoptan el
look BandFlow **sin reescribir markup ni tocar la joya** (`sync_engine.js`/`score_render.js` intactos;
solo cambia el color del acorde activo). Verificado en captura: el reproductor en coral + IBM Plex,
funcionando. e2e `test_player`/`test_library`/`test_smoke` verdes.
**Alcance:** reskin por TOKENS (las páginas conservan su estructura glassmorphism). La conversión
completa a `bf-*`/flat de cada página y retirar el `openBand` muerto de `bands.js` quedan como pulido
opcional (no bloquean).

### 🏷️ T-082 — Rebranding BandFlow (visible) ✅ (2026-06-16)

Marca visible **ChordFlow → BandFlow**: `<title>` y `<h1>` de las 8 páginas legacy, `manifest.json`
(`name`/`short_name`), y `theme-color` unificado a `#0d0d10`. La **marca técnica se difiere** a
propósito (título de la API `FastAPI(title="ChordFlow API")`, clave del SW `chordflow-shell-v1`,
env vars `CHORDFLOW_*`, repo `chordflow`, comentarios). Test `test_rebrand.py` (grep: sin "ChordFlow"
visible en HTML + manifest = BandFlow). Actualizado `test_responsive_pwa` (manifest name). `run_checks`
**TODO VERDE**.

### 🏁 T-083 — Cierre de la Fase 13 ✅ (2026-06-16)

Fase 13 cerrada. Añadida la sección `fase13` a `harness/revision.py` y ejecutada: **✅ completa**
(1/1 rutas `/me` · 5/5 páginas del shell). Veredicto registrado en `harness/REVISIONES.md` (incluye
el resultado de la revisión adversarial ultracode de `/me/*`). **`run_checks.py` TODO VERDE**
(doctor 10/10 · ruff · **139 unit** · **57 e2e**).

**Resumen de la Fase 13** (todo en local, sin desplegar): sistema de diseño BandFlow (coral + IBM
Plex) · app shell con nav TÚ + tema · espacio de banda con banner y 8 pestañas · vistas agregadas
Inicio/Agenda/Finanzas/Chat (endpoints `/me/*` aislados) · biblioteca unificada · reskin de las
páginas legacy · rebranding visible a BandFlow.

**Pendiente de Oscar (no Fase 13):** desplegar el V2 — `push` a `main` + aplicar las 6 migraciones
del giro a la Postgres de producción (`PENDIENTES_OSCAR.md`). Diferido (pulido, no bloquea): reskin
profundo a `bf-*`/flat de cada página, retirar `openBand` muerto, saldo total agregado, UI del hilo
de evento.

### 🧩 Coherencia del shell — biblioteca/bandas/perfil envueltas en el shell (2026-06-17)

Tras desplegar, Oscar notó que el formato "saltaba" entre páginas con lateral (Inicio/Agenda/…) y las
legacy con top-bar (Biblioteca/Bandas). Arreglado: `library.html`, `bands.html` y `profile.html` ahora
usan el **shell BandFlow** (`.bf-shell` + `shell.js` → lateral con nav, perfil y tema), con cabecera
propia dentro del `main` (título + acción). Se conservan todos los ids de contenido (search-input,
library-filters, song-grid, bands-grid, btn-new-band, profile-form) → tests intactos. Añadido botón
**«Cerrar sesión»** al pie del shell (antes solo estaba en la top-bar legacy). Así los **7 destinos del
lateral** comparten chrome. Setlists/editor/reproductor (pantallas de tarea enfocada) mantienen su
cabecera propia a propósito. e2e (library/bands/shell/responsive) verdes · `run_checks` TODO VERDE.

---

## Índice
1. [Bloque A — Arreglos del motor de sincronización](#bloque-a)
2. [Bloque B1 — Biblioteca de canciones](#bloque-b1)
3. [Bloque B2 — Editar y borrar](#bloque-b2)
4. [Bloque B3 — Transposición de acordes](#bloque-b3)
5. [Bloque C — Importador robusto + vista previa](#bloque-c)
6. [Bloque D — Scroll continuo (teleprompter)](#bloque-d)
7. [Bloque E — Auto-guardar tempo](#bloque-e)
8. [Bloque F — Metrónomo](#bloque-f)
9. [Bloque G — Diagramas de acordes](#bloque-g)
10. [Bloque H — Multiusuario con Supabase](#bloque-h) 🟡
11. [Notas técnicas recurrentes](#notas)

---

<a name="bloque-a"></a>
## 1. Bloque A — Arreglos del motor de sincronización ✅

**Por qué:** al probar la app, el corazón del producto (resaltar el acorde que suena) fallaba en 3 casos.

**Qué se arregló:**
- **Pills del Intro quedaban encendidas para siempre.** El limpiador de resaltado solo borraba `.chord-container`, no las pills `.chord-pill`.
- **El Intro no resaltaba en secuencia.** Acordes tipo `: F#m : C#7 :` compartían el beat 0, así que solo se encendía el último.
- **Canciones sin timing no sonaban.** Wonderwall tenía los acordes pegados en beat 0 → no se resaltaba nada.

**Cómo:**
- `static/app.js`: el selector de limpieza ahora cubre `.chord-container.active, .chord-pill.active`.
- `static/sync_engine.js` (`loadSong`): se reescribió el cálculo del beat absoluto. Si una línea no trae `beat_start`, usa un **cursor acumulado** (fallback); si varios acordes comparten el mismo offset, los **reparte uniformemente** dentro de la duración de la línea. Una sola pieza central que hace reproducible **cualquier** canción.

**Verificación:** en navegador, Wonderwall y Love resaltan acordes en secuencia; 0 pills pegadas tras Stop; sin errores de consola.

---

<a name="bloque-b1"></a>
## 2. Bloque B1 — Biblioteca de canciones ✅

**Por qué:** solo se veía la primera canción; no había forma de elegir otra desde la UI.

**Qué:** pantalla de inicio con todas las canciones en tarjetas (título, artista, BPM, nº de secciones), búsqueda en vivo, estado vacío y navegación.

**Cómo:**
- Nuevos: `static/library.html`, `static/library.js`.
- `static/style.css`: estilos de tarjetas (`.song-grid`, `.song-card`, hover teal).
- `static/index.html`: botón 📚 a la biblioteca.
- `static/editor.html`: enlaces de cancelar/guardar vuelven a la biblioteca.
- `src/main.py`: la raíz `/` ahora **redirige** a `/static/library.html` (entrada natural).
- Los títulos se escapan (`escapeHtml`) para evitar inyección de HTML.

**Verificación:** se listan las 2 canciones, la búsqueda filtra, el click abre el reproductor correcto.

---

<a name="bloque-b2"></a>
## 3. Bloque B2 — Editar y borrar ✅

**Por qué:** la API ya tenía PUT/DELETE pero el frontend no los usaba.

**Qué:**
- **Borrar** desde la tarjeta (con confirmación), refresca la grilla al instante.
- **Editar** una canción existente.

**Cómo:**
- `static/library.js`: tarjetas con acciones ✏️/🗑️ (de `<a>` a `<div>` para no anidar enlaces), función `deleteSong` (DELETE).
- `static/editor.js`: **serializador inverso** `songToRawText` + `buildChordLine` (reconstruye el texto "acordes sobre letra" desde la estructura guardada); modo edición detecta `?songId`, precarga y guarda con **PUT** (mantiene el mismo id).
- `static/style.css`: estilos de los botones de acción.

**Verificación:** borrar elimina de la DB; editar precarga datos correctos y el PUT conserva el id (probado cambiando BPM 70→75).

**Decisión del usuario:** se hizo borrar primero (más rápido) y luego editar.

---

<a name="bloque-b3"></a>
## 4. Bloque B3 — Transposición de acordes ✅

**Por qué:** adaptar el tono a la voz/capo es una feature estrella en apps de partituras.

**Decisión del usuario:** transposición **visual en vivo + opción de guardar**.

**Qué:** controles ♭ / ♯ y 💾 en el reproductor; sube/baja todos los acordes por semitonos; opción de guardar el tono.

**Cómo:**
- `static/app.js`: `transposeChord` (maneja alteraciones, sufijos como `m7`/`sus4`, y acordes con bajo `G/B → A/C#`), `applyTranspose` (re-pinta usando `data-orig`), botones, y guardar con **PUT** (recarga con nuevos ids). No afecta la sincronización porque el motor usa **ids**, no nombres.
- `static/index.html`: control de Tono en la top bar.

**Verificación:** 8 casos de transposición correctos; reproducción sigue resaltando; guardar persiste y resetea el offset.

---

<a name="bloque-c"></a>
## 5. Bloque C — Importador robusto + vista previa ✅

**Por qué:** pegar de internet era confuso. Investigación: el formato de LaCuerda/manual ya funcionaba, pero **Ultimate Guitar** (secciones con `[corchetes]`) se rompía, y no había feedback al pegar.

**Decisión del usuario:** parser robusto **+ vista previa en vivo**.

**Qué:**
- El parser reconoce secciones de Ultimate Guitar (`[Verso 1]`), además de `Verso:` y manual.
- **Vista previa en vivo** junto al textarea: al pegar, se ve cómo quedará (mismo render que el reproductor).

**Cómo:**
- Nuevo `static/score_render.js`: render **compartido** (`renderScoreInto`) + transposición, usado por reproductor y editor (elimina duplicación). `app.js` quedó como consumidor.
- `static/editor.js`: detección de `[corchetes]` en `parseRawText`; `updatePreview` al escribir.
- `static/editor.html`: layout en dos columnas (textarea + panel de vista previa).
- `static/style.css`: estilos del split y la vista previa.

**Verificación:** pegando formato Ultimate Guitar real, detecta secciones e imprime acordes sobre letra en el preview, idéntico al reproductor.

---

<a name="bloque-d"></a>
## 6. Bloque D — Scroll continuo (teleprompter) ✅

**Por qué:** el usuario quiere que la canción baje a ritmo cómodo para seguirla tocando sin tocar la pantalla. El scroll antiguo "saltaba" de acorde en acorde.

**Qué:** la partitura desciende **suave y constante** según el progreso de la canción.

**Cómo:**
- `static/sync_engine.js` (`loadSong`): calcula `state.totalBeats`.
- `static/app.js` (`subscribe`): el scroll se basa en `currentBeat / totalBeats` y se escribe `scrollTop` cada frame (rAF).
- `static/style.css`: se quitó `scroll-behavior: smooth` de `#score-container` (peleaba con la escritura por frame).

**Verificación:** el scroll avanza proporcional al beat (descenso fluido).

**Bug cazado de paso:** el reproductor cargaba `style.css?v=4` (cacheado, aún con `scroll-behavior: smooth`); se subió la versión.

---

<a name="bloque-e"></a>
## 7. Bloque E — Auto-guardar tempo ✅

**Por qué:** cada canción debe recordar el último tempo elegido.

**Decisión del usuario:** guardado **automático** (sin botón).

**Qué:** al cambiar el BPM en el reproductor, se guarda solo; al recargar abre con su último tempo.

**Cómo:**
- `src/services/schemas.py`: nuevo `SongUpdate` (campos opcionales).
- `src/api/songs_router.py`: nuevo endpoint **`PATCH /songs/{id}`** que actualiza solo metadatos (bpm…) **sin recrear la estructura** (a diferencia del PUT).
- `static/app.js`: auto-guardado con **debounce** al pulsar +/- de BPM.

**Verificación:** subir a 80 BPM, recargar → abre a 80; id y secciones intactos.

---

<a name="bloque-f"></a>
## 8. Bloque F — Metrónomo ✅

**Por qué:** refuerza seguir el ritmo cómodamente; encaja con el scroll al tempo.

**Qué:** botón 🥁 en el reproductor; clic por beat con **acento en el primer tiempo** del compás.

**Cómo:**
- `static/app.js`: Web Audio API (`playClick`), detección de cruces de beat entero en el `subscribe`, acento según `time_signature_num`. AudioContext se crea tras el primer click (gesto del usuario).
- `static/index.html`: botón del metrónomo.

**Verificación:** patrón de frecuencias `acento-normal-normal-normal` correcto en 4/4.

---

<a name="bloque-g"></a>
## 9. Bloque G — Diagramas de acordes ✅

**Por qué:** ver la digitación al tocar un acorde.

**Decisión del usuario:** diagrama **al pulsar un acorde** + **cobertura total**.

**Qué:** al pulsar cualquier acorde, popup con su diagrama (SVG). Funciona con acordes abiertos y transpuestos.

**Cómo:**
- Nuevo `static/chord_shapes.js`: diccionario de acordes abiertos + **formas móviles** (cejilla E-shape/A-shape) para mayor, menor, 7, m7, maj7 en las 12 tonalidades; elige la posición más cómoda; renderiza **SVG** (cuerdas, trastes, cejuela, puntos, ○/×, barra de cejilla). Acordes raros (sus/dim/aug) → "sin diagrama".
- `static/app.js`: popup con delegación de click en `.chord-container`/`.chord-pill`; cierra al clicar fuera o con Escape.
- `static/style.css`: estilos del popup; cursor pointer en acordes.

**Verificación:** acordes abiertos, cejillas (F#m, Bb usa traste 1), transpuestos y "sin diagrama" para sus/dim; popup abre/cierra. Sin errores.

---

<a name="bloque-h"></a>
## 10. Bloque H — Multiusuario con Supabase 🟡 (en curso)

**Por qué:** cada usuario debe registrarse y ver/editar **solo sus** canciones, con sesión recordada.

**Decisiones del usuario:** login **email+contraseña Y Google**, **sesión persistente**, y **plan detallado primero** (ver `.claude/plans/unified-marinating-swing.md`).

**Enfoque elegido (para desbloquear sin secretos extra):**
- El backend valida el token preguntando a Supabase (`/auth/v1/user`) con la **anon key** ya disponible → **no hace falta el JWT secret**.
- Se mantiene **SQLite por ahora** (la propiedad por usuario funciona igual); la migración a Postgres queda como paso posterior.

**Hecho hasta ahora:**
- **Backend:**
  - Nuevo `src/services/auth.py`: dependencia `get_current_user` (valida Bearer token vía Supabase, devuelve `user_id`). Carga `.env` y `.env.local`.
  - `src/main.py`: endpoint público `GET /config` (devuelve `supabase_url` + `anon_key`; **nunca** la service_role).
  - `src/api/songs_router.py`: todas las rutas exigen `Depends(get_current_user)`; `create` fija `owner_id`; get/get_one/put/patch/delete **filtran por `owner_id`** (resuelve el TODO de filtrado por dueño).
- **Frontend:**
  - Nuevo `static/auth.js`: cliente Supabase desde `/config`, helpers (`signUpEmail`, `signInEmail`, `signInGoogle`, `signOut`, `getSession`, `getToken`, `requireAuth`, `apiFetch`) con `persistSession: true`.
  - Nuevos `static/login.html` + `static/login.js`: formulario email/contraseña + botón Google.
  - **Guards de sesión** en `library.js`, `app.js`, `editor.js` (si no hay sesión → redirige a login).
  - Todas las llamadas a `/songs` pasan por **`apiFetch`** (añade `Authorization: Bearer`).
  - UI de usuario (email + botón cerrar sesión) en la biblioteca.
  - `static/style.css`: estilos del login y de la caja de usuario.

**Verificado (estático):**
- Backend arranca; `GET /songs` sin token → **401**; con token falso → 401; `/config` responde.
- La pantalla de login renderiza; el **guard redirige** a login cuando no hay sesión.

**⚠️ BLOQUEO ACTUAL:** el proyecto de Supabase de `.env.local` **no resuelve por DNS** (`nqewibtmewemlqaxriko.supabase.co`). Causa probable: **proyecto gratuito pausado** por inactividad (los proyectos free de Supabase se pausan y su subdominio deja de resolver). Además hay un posible **typo**: la URL usa `...bt...` pero el `ref` de la anon key es `...bd...`.
  - **Acción pendiente del usuario:** reactivar el proyecto en el dashboard de Supabase (o crear uno nuevo) y confirmar `SUPABASE_URL` + `SUPABASE_ANON_KEY` correctas en `.env.local`. Para Google: habilitar el proveedor y añadir la redirect URL.

**Pendiente (cuando el proyecto esté activo):**
- Verificación end-to-end: registrar usuario, crear canción, segundo usuario ve biblioteca vacía, sesión persiste al recargar, login con Google.
- (Posterior) migrar la DB a Postgres de Supabase.
- (Datos) las 2 canciones actuales tienen `owner_id` nulo → no aparecerán para ningún usuario hasta asignarlas.

---

<a name="bloque-i"></a>
## Bloque I — Auditoría + endurecimiento (Fase de calidad)

> Tras estudio completo del código (2026-06-13). Plan en `harness/ROADMAP.md`.

### ✅ T-001 — Control de versiones
- **Qué:** `git init` + primer commit del estado completo (app + harness + tests + docs).
- **Por qué:** red de seguridad mínima; poder volver atrás.
- **Cómo / verificación:** `git ls-files` confirma que `.env.local` y `*.db` **no** están
  trackeados. Añadido `.gitattributes` (normaliza EOL a LF) y `*.log` al `.gitignore`.

### ✅ T-002 — Arreglo de XSS en el renderer
- **Qué:** la letra (`line.content`) y el `chord_name` del usuario se inyectaban con `innerHTML`
  sin escapar (reproductor y vista previa del editor) → ejecución de JS arbitrario.
- **Cómo:**
  - `static/score_render.js`: nuevo `escapeHtml()` + `renderLyricWithChords()` que escapa cada
    segmento de letra por separado e inserta solo HTML de acorde saneado (preserva la alineación
    por columnas, que depende de `char_position` sobre el texto original). `chordSpan` ahora escapa
    `chord_name` en el texto visible **y** en el atributo `data-orig`.
  - Cache-busting `score_render.js?v=8` en `index.html` y `editor.html`.
- **Verificación:** test nuevo `tests/e2e/test_js_logic.py::test_render_escapa_letra_y_acorde_maliciosos`
  (payload `<img onerror>` → no se crea `<img>`, no se dispara, letra escapada). Fila **J3** en el
  CHECKLIST. `run_checks.py` **TODO VERDE**.

### ✅ Robustez del harness (descubierto al activar Playwright)
- **Bug del `live_server` (`tests/conftest.py`):** uvicorn arrancaba con `stdout=PIPE` sin que nadie
  lo vaciara → el buffer del pipe del SO se llenaba con los logs y el servidor se **bloqueaba** a
  mitad del suite e2e (cascada de `ReadTimeout`). Arreglado volcando la salida a un fichero temporal
  + `--no-access-log`. También: `test_editor.py` comparaba la sección sensible a mayúsculas, pero el
  CSS la pone en uppercase → ahora compara con `.lower()`.
- Lint: `ruff --fix` (orden de imports en `harness/`) y `Song.deleted_at == None` →
  `.is_(None)` (forma correcta en SQLAlchemy, además contenta a E711).

### ✅ T-003 — Fin de la fuga de filas huérfanas en PUT
- **Qué:** `PUT /songs/{id}` borraba las secciones con bulk `query(...).delete()`, que no dispara
  el cascade ORM; con las FKs de SQLite desactivadas, `lines`/`chord_markers`/`tab_lines` quedaban
  huérfanos en cada edición (la BD crecía sin límite).
- **Cómo:** borrado vía ORM (`for sec in db_song.sections: db.delete(sec); db.flush()`) para que
  el cascade `delete-orphan` actúe. Defensa en profundidad: `PRAGMA foreign_keys=ON` por conexión
  en `db.py` (event listener).
- **Verificación:** `tests/unit/test_api_songs.py::test_put_no_deja_filas_huerfanas` (editar 2 veces
  y comprobar que sections/lines/chords no crecen).

### ✅ T-004 — CORS por lista explícita de orígenes
- **Qué:** `allow_origins=["*"]` + `allow_credentials=True` (inseguro e inconsistente).
- **Cómo:** `main.py` lee `CHORDFLOW_ALLOWED_ORIGINS` (coma-separada); default a localhost.
  Documentada la var en `.env`. El frontend es same-origin, así que no afecta al uso normal.
- **Verificación:** `tests/unit/test_security.py::test_cors_restringe_origenes`.

### ✅ T-005 — Caché de validación de token (no depender de Supabase en cada request)
- **Qué:** `auth.py` validaba el token con una llamada de red **síncrona a Supabase en cada
  request** → latencia y caída total si Supabase caía.
- **Cómo:** caché en memoria `token → (user_id, expiry)` con TTL (`CHORDFLOW_TOKEN_TTL`, 60 s).
  Caché válida no llama a Supabase; si la validación remota falla pero hay caché, degradación
  elegante (la request pasa).
- **Verificación:** `test_validacion_de_token_se_cachea` (valida una sola vez) y
  `test_token_en_cache_sobrevive_caida_de_supabase`.

> **Hito:** los 5 críticos de la auditoría (T-001…T-005) cerrados. `run_checks.py` TODO VERDE.

### ✅ T-007/T-008/T-009 — Modernización del backend
- **Pydantic v2:** `orm_mode`→`ConfigDict(from_attributes=True)` (5×, `schemas.py`),
  `.dict()`→`.model_dump()` (11×, `songs_router.py`).
- **Deps pineadas:** `requirements.txt` con versiones probadas en Py3.12.
- **datetime tz-aware:** `datetime.utcnow()`→`_utcnow()` (UTC) en `models.py`.
- **Efecto:** desaparecen los `DeprecationWarning` de Pydantic y datetime.

### ✅ T-006 — `apiFetch` maneja el 401
- **Qué/por qué:** si el token expira, las llamadas fallaban en silencio. Ahora `apiFetch`
  (`auth.js`) detecta `401` y redirige a `login.html` (evita bucle si ya estás en login).
- **Cómo:** cache-busting `auth.js?v=11` en los 4 `.html`.
- **Verificación:** E2E `test_apifetch_redirige_a_login_en_401` (fila S4 del CHECKLIST).

### ✅ T-015 — Limpieza
- Eliminado `test_api.py` (script manual legacy con `requests`, redundante con el harness).

> **Estado (ultracode):** lanzada en paralelo una auditoría multi-agente (8 dimensiones +
> verificación adversaria) cuyos hallazgos confirmados se fundirán en el ROADMAP (T-026+).

### ✅ T-012 / T-024 — Índices + validación de rangos
- Índices (`index=True`) en `owner_id`, `deleted_at` y las 4 FKs. `Field(...)` de rangos en
  schemas (bpm 20–400, year 0–3000, compás 1–32, capo 0–24, title 1–255) → 422 fuera de rango.

### ✅ T-026 / T-027 / T-028 — Hallazgos críticos de la auditoría multi-agente
> La auditoría (workflow de 8 finders) se quedó sin límite de sesión en la verificación, pero los
> finders destaparon 3 bugs reales nuevos que verifiqué a mano y arreglé:
- **T-026 — XSS de 2º orden en el popup de diagramas:** `chord_shapes.js::renderChordDiagramSVG`
  inyectaba `name` con `innerHTML` sin escapar, y `name` = `el.textContent` (acorde **decodificado**)
  → un acorde malicioso ejecutaba JS al pulsarlo. Escapado con `escapeHtml`. Cache-bust `chord_shapes.js?v=9`.
- **T-027 — 404 degradado a 400:** el `except Exception` ancho de `create_song`/`update_song`
  capturaba el `HTTPException(404)`. Añadido `except HTTPException: raise`.
- **T-028 — `_token_cache` sin cota:** la caché de T-005 crecía sin límite. Cota dura `TOKEN_CACHE_MAX`.
- **Verificación:** tests J4, A4, A5 y SEC3. `run_checks.py` TODO VERDE.
- El resto de hallazgos (cabeceras de seguridad, SRI, ON DELETE, paginación, consolidar escapeHtml,
  cobertura, desacoplar auth para el molde…) quedaron registrados en `ROADMAP.md` Fase A (T-029…T-044).

### ✅ T-029 / T-037 + endurecimiento (verificación adversaria lean)
> Un segundo workflow (3 agentes) verificó los fixes T-026/27/28. T-026 y T-027 correctos;
> **T-028 estaba incompleto** (bug de concurrencia) → arreglado. También cerró 2 items de Fase A.
- **T-028 (concurrencia):** `_cache_set` iteraba el dict mientras otro hilo del threadpool de
  uvicorn insertaba → `RuntimeError: dictionary changed size during iteration` (HTTP 500 a
  usuarios válidos) + la cota se saltaba por TOCTOU. Arreglado con `threading.Lock`.
  Test `test_cache_set_seguro_bajo_concurrencia`.
- **T-027 (hardening):** el `except Exception` de create/update ya no degrada a 400 con `str(e)`
  (filtraba internos) → **500 genérico**.
- **T-029:** middleware de cabeceras de seguridad (`X-Content-Type-Options`, `X-Frame-Options`,
  `Referrer-Policy`, `Permissions-Policy`). CSP pendiente. Test `test_cabeceras_de_seguridad`.
- **T-037:** paginación acotada (`skip` ge=0, `limit` 1–500) → 422. Test `test_paginacion_acotada`.
- **Verificación:** 13 unit + 17 e2e verde. ⚠️ e2e con flakiness intermitente (T-042).

### ✅ T-010 / T-042 — Listado ligero (fin del N+1) + flakiness e2e

> **Por qué:** `GET /songs/` serializaba `SongResponse` (con `sections→lines→chords`), forzando
> un lazy-load de toda la jerarquía **por cada canción** del listado → N+1. Y el harness e2e
> fallaba de forma intermitente por timeouts (T-042).

- **T-010 (N+1):** nuevo schema `SongSummary` (metadatos planos + `section_count`, **sin** la
  relación `sections`), así pydantic nunca toca esa relación al serializar el listado. El nº de
  secciones se obtiene con **una sola query agregada** (`func.count` + `group_by`) para toda la
  página, no una por canción → de O(N) a O(1) queries. Archivos: `src/services/schemas.py`
  (`SongSummary`), `src/api/songs_router.py` (`get_songs` → `List[SongSummary]`).
  - **Frontend (2 consumidores del listado):** `static/library.js` usa `song.section_count` en vez
    de `song.sections.length`. Y `static/app.js` (reproductor sin `?songId`, que cargaba `songs[0]`
    del listado como canción completa) ahora pide el **detalle** `/songs/{id}` antes de renderizar
    —si no, al abrir `index.html` sin parámetro la partitura salía vacía y sin acordes—. Esta
    **regresión la cazó la revisión adversaria multi-agente del diff**, no estaba en el plan inicial.
    Cache-bust `library.js?v=10`, `app.js?v=10`.
  - **Tests:** `test_listado_es_ligero_sin_estructura` (listado sin `sections`, con `section_count`;
    el detalle sí trae la estructura) + e2e `test_carga_por_defecto_sin_songId` (abrir el player sin
    `?songId` carga la 1ª canción **con acordes** — cubre la regresión de `app.js`).
- **T-042 (flakiness e2e):** se atacaron 3 carreras reales del harness:
  1. Fixture `api`: timeout httpx por defecto (5 s) → `ReadTimeout` intermitente. Ahora 30 s.
  2. `live_server`: deadline de arranque 25 s → fallos en cascada bajo carga (varias suites). Ahora 45 s.
  3. `test_apifetch_redirige_a_login_en_401`: doble carrera —caché de `/config` sin poblar al
     sobreescribir `fetch`, y `login.js` que **rebota** a `library.html` si hay sesión (modo test
     siempre la tiene)—. Reescrito determinista: calienta la caché con `getToken()` y comprueba que
     la navegación **pasó por** `login.html` (no que se quede), capturando `framenavigated`.
- **Verificación:** `doctor.py` verde + `run_checks.py` **TODO VERDE** (14 unit + 18 e2e); el e2e
  antes flaky pasó 5/5 en repetición. Revisión adversaria multi-agente del diff antes de cerrar.

### ✅ T-011 — Alembic (migraciones de esquema)

> **Por qué:** hasta ahora el esquema se creaba con `Base.metadata.create_all`, que **solo crea
> tablas que faltan**: nunca aplica cambios a columnas/índices/constraints existentes. Sin una
> herramienta de migraciones no se podían abordar T-033 (`ON DELETE CASCADE`), T-034 (`NOT NULL`),
> T-036 (`server_default`), etc. — todo el cluster de integridad de datos quedaba bloqueado.

- **Infra:** `alembic.ini` + `alembic/env.py` + `alembic/script.py.mako` + `alembic/versions/`.
  `env.py` lee la URL de **`DATABASE_URL`** (misma fuente y default que `db.py`), usa
  `target_metadata = Base.metadata` (importando los modelos) para `--autogenerate`, y activa
  **`render_as_batch=True`** — imprescindible en SQLite, que no soporta la mayoría de `ALTER TABLE`
  y necesita recrear la tabla por debajo (lo usarán T-033/34/36).
- **Baseline `fefcd5a0b14a`:** migración inicial autogenerada que crea las 5 tablas + los índices
  de T-012, en orden de dependencia de FKs. `alembic check` confirma que está **en sincronía** con
  los modelos (sin diffs).
- **Coexistencia con `create_all`:** la app (`main.py`) y el harness siguen usando `create_all`
  para arrancar rápido sobre BD temporales/nuevas; Alembic es la vía para **evolucionar** una BD
  real. ⚠️ Para adoptar Alembic sobre una `chordflow.db` ya existente (creada con `create_all`, sin
  tabla `alembic_version`): `alembic stamp head` (marcarla al día) **en vez de** `upgrade head`
  (que intentaría recrear tablas ya presentes).
- **Gotcha resuelto:** un `PRAGMA foreign_keys=ON` manual en `env.py` (online) abría una transacción
  que descuadraba el commit del *stamp* de versión en SQLAlchemy 2.0 → las tablas se creaban pero
  `alembic_version` quedaba **vacía**. Se quitó (batch mode no lo necesita).
- **Deps:** `alembic==1.14.1` + `Mako==1.3.12` pineadas en `requirements.txt`. `alembic/versions/`
  excluido de ruff/black (código generado).
- **Tests:** `tests/unit/test_migrations.py` — `upgrade head` crea el esquema completo (5 tablas +
  índices + `alembic_version`) y `alembic check` no detecta drift modelos↔migraciones.
- **Verificación:** `run_checks.py` **TODO VERDE** (16 unit + 18 e2e).

### ✅ T-033 — FKs con `ON DELETE CASCADE` a nivel de BD

> **Por qué:** hasta ahora el borrado en cascada vivía solo en el ORM (`delete-orphan`) + el
> `PRAGMA foreign_keys=ON`. Si alguien borraba una fila padre con **SQL directo** (un script, una
> migración futura, una consola), las hijas quedaban huérfanas. T-033 lo blinda a nivel de esquema.

- **Modelos:** las 4 FKs (`sections.song_id`, `lines.section_id`, `chord_markers.line_id`,
  `tab_lines.line_id`) ahora llevan `ondelete="CASCADE"`. Las BD nuevas (create_all / tests) ya
  nacen con la cascada.
- **Migración `dac91229a048`:** aplica el cambio a BD existentes. SQLite no permite `ALTER` de una
  FK → `batch_alter_table` recrea la tabla. **Gotcha clave:** para *soltar* una FK sin nombre en
  batch mode hace falta un `naming_convention`; sin él `drop_constraint(None)` es un no-op y la tabla
  se recreaba **conservando la FK vieja sin `ondelete`** (lo detecté inspeccionando el DDL real:
  `FOREIGN KEY(song_id) REFERENCES songs (id)` sin cascada). Con el naming convention, las 4 FKs
  quedan con `ondelete=CASCADE` y `alembic check` no detecta drift.
- **Test:** `test_cascade_a_nivel_db` borra la canción padre con `DELETE FROM songs` crudo (sin pasar
  por el cascade ORM) y verifica que `sections/lines/chord_markers/tab_lines` quedan a 0.
- **Verificación:** `run_checks.py` **TODO VERDE** (17 unit + 18 e2e).

### ✅ T-014 — Logging unificado (configurado una sola vez) + opción stdout cloud-friendly

> **Por qué:** `db.py` (módulo de **librería**) llamaba a `logging.basicConfig`, y `main.py` repetía
> la misma config. Configurar el logging raíz desde una librería es un anti-patrón: quien importe
> `db.py` (tests, Alembic, scripts) hereda handlers que no pidió, y la doble config arriesga líneas
> duplicadas. Además, escribir siempre a `logs/app.log` no sirve en cloud (contenedores efímeros),
> donde la plataforma captura **stdout**.

- **Nuevo `src/services/logging_config.py`:** `setup_logging()` monta el logger raíz **una sola vez**.
  Idempotente (cierra y reemplaza handlers previos → no duplica líneas ni deja ficheros abiertos).
  Respeta `LOG_LEVEL` (default `INFO`).
- **Destino seleccionable:** por defecto `FileHandler` a `logs/app.log`; con `CHORDFLOW_LOG_STDOUT=1`
  va a stdout (cloud-friendly). El formato se conserva (`%(asctime)s - %(name)s - %(levelname)s ...`).
- **`main.py`:** sustituye su bloque `basicConfig` por `setup_logging()` (llamado al importar la app,
  antes de `create_all`). `db.py`: eliminado su `basicConfig`/`makedirs`; ahora solo
  `logging.getLogger(__name__)`, como debe hacer una librería. `auth.py` ya era correcto.
- **Tests:** `tests/unit/test_logging_config.py` — stdout cuando la var está activa (sin abrir
  fichero), `FileHandler` por defecto, idempotencia (1 handler tras N llamadas) y guardia de
  regresión (`basicConfig(` no aparece en `db.py`).
- **Verificación:** `run_checks.py` **TODO VERDE** (21 unit + 18 e2e).

### ✅ T-013 — Soft delete real en `DELETE /songs/{id}`

> **Por qué:** la columna `deleted_at` existía y **todas** las lecturas (list/get/put/patch) ya
> filtraban `deleted_at IS NULL`, pero `delete_song` hacía **hard delete** (`db.delete`). Es decir,
> la mitad del patrón soft-delete estaba implementada y la otra lo contradecía: un borrado era
> irreversible pese a toda la infraestructura para no serlo.

- **`delete_song`:** ahora marca `deleted_at = _utcnow()` (tz-aware, T-009) en vez de borrar la fila.
  La canción desaparece de la app pero la fila y su estructura se **conservan** (recuperable/auditable).
- **Idempotencia:** el filtro del DELETE incluye `deleted_at IS NULL`, así que un **segundo** DELETE
  sobre una canción ya borrada → **404** (no 204). Añadido `except HTTPException: raise` para no
  convertir ese 404 en 500.
- **`is_public`:** decisión documentada → se mantiene el filtrado **solo por dueño** en todas las
  lecturas. Exponer canciones públicas (a otros usuarios / sin auth) es una **feature de producto**
  (Fase 5: compartir/setlists), no un arreglo de calidad; se difiere para no meter scope ni una
  superficie de acceso nueva sin diseño.
- **Test:** `test_delete_es_soft` — tras DELETE la fila sigue en la BD con `deleted_at` puesto, es
  invisible para GET/list, y un 2º DELETE da 404. Los tests existentes (`test_crud_completo`) siguen
  pasando: comprobaban “desaparece de GET/list”, que el soft delete también cumple.
- **Verificación:** `run_checks.py` **TODO VERDE** (22 unit + 18 e2e).

### ✅ T-016 — `Settings` validado con pydantic-settings (fin de los `os.getenv` sueltos)

> **Por qué:** la config vivía en `os.getenv` dispersos por `db.py`, `auth.py`, `main.py` y
> `logging_config.py`, sin tipos ni validación: un `CHORDFLOW_TOKEN_TTL` mal puesto reventaba tarde
> (en un `int(...)` en runtime) y no había un sitio único que documentara qué variables existen.

- **Nuevo `src/services/config.py`:** clase `Settings(BaseSettings)` + singleton `settings`. Reúne
  `DATABASE_URL`, `SUPABASE_URL/ANON_KEY`, `CHORDFLOW_TEST_MODE`, `CHORDFLOW_TOKEN_TTL`,
  `CHORDFLOW_TOKEN_CACHE_MAX`, `CHORDFLOW_ALLOWED_ORIGINS`, `LOG_LEVEL`, `CHORDFLOW_LOG_STDOUT`,
  con tipos, defaults y validación **fail-fast** al arrancar. `env_file=(.env, .env.local)` +
  `load_dotenv()` (este último para poblar también `os.environ`, del que depende `alembic/env.py`).
  Propiedad `allowed_origins_list` (parseo coma-separado → lista).
- **Consumidores migrados:** `db.py` (`settings.database_url`), `auth.py` (supabase/test_mode/ttl/
  cache_max — manteniendo los **nombres de módulo** `TEST_MODE`/`TOKEN_CACHE_MAX`/... porque
  `test_security` les hace monkeypatch), `main.py` (`settings.allowed_origins_list`),
  `logging_config.py` (`settings.log_level`/`chordflow_log_stdout`).
- **Decisión:** `alembic/env.py` sigue leyendo `os.getenv("DATABASE_URL")` **fresco** (no el
  singleton): cada migración corre en su contexto y `test_migrations` cambia la BD por env var.
  Atarlo al singleton (leído una vez) habría usado la BD equivocada.
- **Tests ajustados:** `test_logging_config` ahora hace monkeypatch sobre `settings` (el destino se
  lee del singleton, no de `os.environ` en cada llamada). **Nuevo** `test_config.py`: tipos desde el
  entorno, parseo de orígenes y `ValidationError` ante un TTL no numérico.
- **Deps:** `pydantic-settings==2.14.1` pineada en `requirements.txt`.
- **Verificación:** `run_checks.py` **TODO VERDE** (25 unit + 18 e2e).

### ✅ T-025 — Endpoint `/health` (liveness) separado de `/config`

> **Por qué:** no había un health check propio; los uptime checks/orquestadores tendrían que pegar
> a `/config` (que expone config pública del frontend, no es un health check) o a `/` (redirección).

- **`GET /health`** → `{"status": "ok"}`. Liveness **barato y sin dependencias** (no toca la BD ni
  Supabase) para consultarlo a alta frecuencia sin coste; sin auth. Tercer/último pilar de T-044.
- **Test:** `test_health_es_liveness` — 200 con el cuerpo esperado y sin filtrar config sensible.
- **Verificación:** `run_checks.py` **TODO VERDE** (26 unit + 18 e2e).

### ✅ T-039 — `escapeHtml` consolidado en `static/util.js` (fuente única)

> **Por qué:** `escapeHtml` estaba **duplicado** (en `library.js` y `score_render.js`) y `chord_shapes.js`
> dependía de "alguna" global. Peor: las dos copias **no eran iguales** — la de `library.js`
> (`div.textContent → innerHTML`) NO escapaba comillas, así que no era segura en contexto de atributo.
> Duplicar una función de seguridad es justo donde no quieres divergencia.

- **Nuevo `static/util.js`:** define la global `escapeHtml` canónica (la versión `replace` de
  `score_render`, que escapa también `"`/`'` → segura en texto **y** atributos; null-safe). Fuente única.
- **Eliminadas** las dos definiciones locales; `library.js`/`score_render.js`/`chord_shapes.js` usan la
  global de `util.js`.
- **Cache-busting (CLAUDE.md §4):** `util.js?v=1` añadido **antes** de sus dependientes en
  `library.html`, `index.html` y `editor.html`; subidos los que cambiaron: `library.js v10→11`,
  `score_render.js v8→9` (en index **y** editor). `chord_shapes.js` sin cambios (sigue en v9).
- **Cobertura:** los e2e existentes ya ejercen los 3 consumidores tras la consolidación —
  `test_render_escapa_letra_y_acorde_maliciosos` (editor.html→score_render),
  `test_popup_diagrama_escapa_nombre_malicioso` (index.html→chord_shapes) y los de biblioteca
  (library.html→library.js). Todos en verde.
- **Verificación:** `run_checks.py` **TODO VERDE** (26 unit + 18 e2e).

### ✅ T-044 — Backend base del molde: handler de errores global (cierra los 4 pilares)

> **Por qué:** T-044 reúne lo agnóstico-al-dominio que todo backend del molde necesita. Tres pilares
> ya estaban (logging único T-014, `Settings` T-016, `/health` T-025); faltaba un **handler de errores
> global** como red de seguridad: hoy cada endpoint envuelve su lógica en try/except, pero una
> excepción en una **dependencia** o middleware (fuera de esos try) llegaría a Starlette y, en debug,
> podría exponer la traza.

- **`@app.exception_handler(Exception)`** en `main.py`: registra la excepción con traza (`exc_info`)
  y responde **500 genérico** (`{"detail": "Error interno del servidor"}`) — nunca `str(e)` al cliente
  (misma política anti-fuga que el hardening de T-027). Las `HTTPException` (401/404/422...) siguen
  manejadas por FastAPI con su código propio, no pasan por aquí.
- **Test:** `test_handler_global_500_no_filtra_internals` — vía `dependency_overrides` se fuerza un
  `RuntimeError` con un mensaje "secreto" en una dependencia; se verifica 500, cuerpo genérico y que
  el mensaje interno **no** aparece en la respuesta. (`TestClient(raise_server_exceptions=False)`.)
- **Estado de T-044:** los **4 pilares técnicos** del backend base del molde quedan completos
  (T-014 + T-016 + T-025 + handler global). El README/plantillas del molde se materializa al extraer
  `app-skeleton/` (T-M02), no aquí.
- **Verificación:** `run_checks.py` **TODO VERDE** (27 unit + 18 e2e).

### ✅ T-043 — `auth.py` desacoplado de Supabase (proveedor de identidad enchufable)

> **Por qué:** la lógica valiosa y reutilizable de `auth.py` —caché TTL, lock de concurrencia,
> degradación elegante si el IdP cae (T-005/T-028)— estaba **soldada** a la llamada concreta a
> Supabase. Para el molde, ese núcleo debe servir con cualquier backend de identidad.

- **Nuevo `src/services/auth_provider.py`:** `AuthProvider` (Protocol con `validate(token) -> dict|None`),
  `SupabaseAuthProvider` (la lógica de `/auth/v1/user` que antes vivía inline en `auth.py`) y la
  factoría `build_auth_provider(settings)` que elige por `CHORDFLOW_AUTH_PROVIDER` (default `supabase`,
  **fail-fast** ante un nombre desconocido).
- **`auth.py` agnóstico:** `_validate_token(token)` delega en `_provider.validate(token)`; toda la
  caché/TTL/lock/degradación se queda igual y ya **no sabe** que detrás hay Supabase. Migrados el
  import (fuera `json`/`urllib`) y el seam interno.
- **Tests:** los de caché (T-005/T-028) ahora hacen monkeypatch del seam genérico `_validate_token`.
  **Nuevo** `test_auth_provider.py`: factoría (default + desconocido→`ValueError`), Supabase sin
  credenciales → None, y `test_auth_es_agnostico_al_provider` (inyecta un `FakeProvider` y
  `get_current_user` devuelve su user_id sin tocar la caché).
- **Alcance:** la 2ª mitad de T-043 ("parametrizar el prefijo `CHORDFLOW_*`") se **difiere** a la
  plantilla del molde (T-M03): cambiar el prefijo es un hueco de templating, no un cambio de runtime
  de ChordFlow, y tocar los nombres de los settings ahora solo añadiría riesgo sin valor aquí.
- **Verificación:** `run_checks.py` **TODO VERDE** (30 unit + 18 e2e).

### ✅ T-M01 — Inventario del molde validado contra el árbol real

> **Por qué:** la tabla universal-vs-dominio de `MOLDE.md` se escribió en fase de diseño; desde
> entonces el código creció (T-011 Alembic, T-014 logging, T-016 `config.py`, T-039 `util.js`,
> T-043 `auth_provider.py`, T-044 handler global). Antes de extraer `app-skeleton/` (T-M02) hay que
> asegurar que el inventario refleja la realidad, o el molde nacería incompleto.

- **Validación:** listado del árbol real (`src/`, `static/`, `tests/`, `harness/`, `alembic/`, raíz)
  y cotejo fila a fila. Hallazgos corregidos en `MOLDE.md`:
  - `settings.py` del diseño **es** `config.py` en el real → reconciliado.
  - Añadidos como **Universal (nuevo)**: `logging_config.py`, `auth_provider.py`, `static/util.js`,
    `alembic.ini`+`env.py`+`script.py.mako`, y los tests `test_config/logging_config/auth_provider`.
  - `static/login.html`+`login.js` reclasificados **Universal (plantilla)** (faltaban).
  - `alembic/versions/*` marcados **Dominio** (el molde trae solo el baseline del `Item`).
  - `src/main.py`: añadidos `/health` y el handler de errores global a su descripción.
- **`MOLDE.md`:** tabla §2 reescrita en 4 sub-tablas (harness/raíz, backend, frontend, tests) y la
  estructura §4 de `app-skeleton/` actualizada a los nombres reales. Estado del doc → «inventario
  validado», pre-requisitos técnicos (T-043/T-044) marcados cumplidos.
- **Verificación:** tarea de diseño/documentación, sin cambio de runtime → `doctor.py` **verde**
  (10/10); el "test" es el cotejo del inventario contra el árbol real.

### ✅ T-M02 — `app-skeleton/` creado (molde reutilizable extraído)

> **Por qué:** es el objetivo de fondo de la Fase M — capturar de una vez el esqueleto técnico +
> sistema de trabajo, para que cada app nueva arranque estable y testeada desde el minuto 1.

- **Ubicación:** carpeta/repo hermano `../app-skeleton` (fuera de este repo; `git init` propio,
  commit `e02b1b0`). Decisión del usuario: backend completo + recurso `Item`, repo aparte.
- **Qué contiene (todo agnóstico al dominio):**
  - **Harness** completo: `doctor.py` (relajado: IdP opcional, `.env.example`, `/health`, `/items` 401),
    `run_checks.py`, ROADMAP/TASKS/CHECKLIST/MOLDE genéricos + plantilla de tarea.
  - **Backend base** (los 4 pilares de T-044): `config.py` (Settings), `logging_config.py`,
    `main.py` (CORS env + cabeceras + `/health` + `/config` + **handler de errores global**),
    `db.py` (PRAGMA FK).
  - **Auth** con modo test + `auth_provider.py` (AuthProvider enchufable, Supabase de ejemplo).
  - **Recurso de ejemplo `Item`** (reemplaza a `Song`): modelo (owner_id/deleted_at/timestamps/JSON),
    schemas (Create/Update/Response/Summary), router CRUD (auth + filtro dueño + soft delete +
    paginación), migración Alembic baseline.
  - **Frontend universal:** `auth.js`, `util.js` (escapeHtml), `login.*`, `index.*` de ejemplo
    (demuestra requireAuth + apiFetch + escapeHtml), `style.css` con tokens base.
  - **Higiene:** `.gitignore`, `.gitattributes`, `pyproject.toml`, deps **pineadas** (incl.
    pydantic-settings + alembic), `.env.example` con prefijo neutral `APP_`.
- **Prefijo de env vars:** neutral `APP_` (concreto y funcional). Parametrizarlo a `{{ENV_PREFIX}}`
  queda para T-M03 (huecos solo en docs, no en código → el molde sigue corriendo).
- **Verificación (criterio T-M06 esencialmente cumplido):** `run_checks.py` del esqueleto **TODO
  VERDE** recién creado, sin tocar dominio — doctor (10/10) + ruff + **26 unit** + **4 e2e**.
  Dos tropiezos resueltos en el camino: faltaba `alembic.ini` (lo añadí) y un orden de imports
  (ruff --fix).

### ✅ T-M03 — Plantillar docs + parametrizar el prefijo de env vars (en `../app-skeleton`)

> **Por qué:** cierra la 2ª mitad de T-043 (parametrizar `CHORDFLOW_*`) y deja el molde listo para
> renombrar a cualquier proyecto. Hecho en el repo hermano `../app-skeleton` (commit `5e14adf`).

- **Prefijo como UNA sola perilla:** `config.py` ahora usa `env_prefix="APP_"` (pydantic-settings)
  en vez de repetir `app_` en cada campo. Los campos pierden el sufijo (`settings.test_mode`,
  `settings.token_ttl`, ...). Los nombres **estándar** (`DATABASE_URL`, `LOG_LEVEL`, `SUPABASE_*`)
  van por `validation_alias` → SIN prefijo (no deben llevarlo). Renombrar el prefijo del proyecto =
  cambiar esa línea + los literales `APP_*` del `.env.example`/`conftest`/`doctor` (documentado).
- **Consumidores y tests** migrados a los nombres nuevos; **nuevo** `test_nombres_estandar_sin_prefijo`
  (verifica que DATABASE_URL/LOG_LEVEL se leen sin prefijo).
- **Docs plantilladas:** `CLAUDE.md`/`GUIA_MAESTRA.md`/ROADMAP/TASKS/CHECKLIST con huecos
  `{{APP_NAME}}`/`{{DESCRIPTION}}`/`{{STACK}}`/`{{ENV_PREFIX}}` (solo en docs; el código nunca lleva
  huecos, así el molde siempre corre). `MOLDE.md` §4 **Personalización**: receta exacta de las 3
  sustituciones (nombre, prefijo, recurso `Item`).
- **Verificación:** `run_checks.py` del esqueleto **TODO VERDE** (27 unit + 4 e2e).

### ✅ T-M06 — Criterio de molde estable verificado (prueba de copia real)

> **Por qué:** la garantía de fondo del molde es que un proyecto recién nacido de él arranque verde
> sin tocar nada. Hasta ahora el esqueleto pasaba verde *in situ*; faltaba la prueba con una **copia
> fresca**, que es como lo usaría un proyecto nuevo.

- **Prueba:** `git archive HEAD` del molde → extraído a una carpeta nueva y limpia (45 ficheros,
  **sin** `.git`/`__pycache__`/`*.db`/logs, confirmado) → `python harness/run_checks.py` ahí **sin
  modificar nada**.
- **Resultado:** **TODO VERDE** — doctor (10/10) + ruff + 27 unit + 4 e2e. El molde es estable.
  Carpeta de prueba eliminada tras verificar. Anotado en `../app-skeleton/harness/MOLDE.md`
  (commit `31e450f`).

### ✅ T-023 — GitHub Actions (CI en cada push/PR)

> **Por qué:** profesionaliza el repo — la "definición de terminado" (`run_checks.py`) deja de
> depender de que alguien la corra a mano; CI la ejecuta en cada push y PR.

- **`.github/workflows/ci.yml`:** Ubuntu + Python 3.12 (cache pip) → instala `requirements` +
  `requirements-dev` → `playwright install --with-deps chromium` → `python harness/run_checks.py`
  (doctor + ruff + unit + e2e). Timeout 20 min.
- **Gotcha del doctor en CI:** el doctor exige `.env`/`.env.local` con claves de Supabase
  presentes, pero los secretos están gitignoreados. Como los tests corren en **modo test** (no
  llaman a Supabase) y el 401-sin-token y el smoke no dependen del IdP real, el workflow crea
  `.env`/`.env.local` con valores **placeholder** antes de correr los checks.
- **Verificación:** simulé el entorno de CI en local (respaldé mis `.env` reales, los reemplacé por
  los dummy del workflow, corrí el doctor → **verde 10/10** incluido el smoke de navegador, y
  restauré los reales). YAML validado (`yaml.safe_load`: 1 job, 6 steps). La ejecución real en
  GitHub Actions se activará al publicar el repo (hoy no hay remoto configurado).

### ✅ T-034 + T-035 + T-036 — Integridad de datos a nivel de BD (migración `147a6a78da86`)

> **Por qué:** los modelos confiaban en Python para defaults y validación, dejando la BD
> "blanda": un INSERT por SQL directo podía crear una canción sin dueño, con un `Line.type`
> inventado o sin los defaults. Una sola migración batch lo blinda en el esquema.

- **T-034 — `owner_id` NOT NULL:** la auth es obligatoria y el router siempre asigna dueño; ahora
  el esquema lo exige. Test `test_owner_id_not_null_en_bd` (INSERT directo sin owner_id →
  `IntegrityError`).
- **T-035 — `Line.type` restringido:** validación de **schema** (`Literal[...]` en `LineBase` →
  **422** al usuario) + **CHECK** `ck_lines_type` en BD (defensa en profundidad). La lista vive en
  `models.LINE_TYPES` (fuente única: el CHECK se construye de ahí). Tests
  `test_line_type_invalido_da_422` y `test_check_line_type_en_bd` (INSERT directo con type basura →
  `IntegrityError`).
- **T-036 — `server_default`:** `bpm/time_signature_num/den/capo/format_version/is_public`
  (songs) y `repeat_count` (sections) llevan `server_default`, así un INSERT por SQL directo recibe
  los defaults desde la BD, no solo desde Python. Timestamps siguen Python-side (tz-aware, evita
  drift con `func.now()`). Test `test_server_default_en_bd`.
- **Migración:** autogenerate detectó el NOT NULL; añadí a mano los `server_default` (no se comparan,
  `compare_server_default` off → sin drift) y el CHECK (SQLite no lo autodetecta). `alembic check`:
  **"No new upgrade operations detected"**. El cascade FK de T-033 sobrevive a la recreación batch
  de `lines` (verificado). ⚠️ El NOT NULL asume que no hay filas con owner_id NULL (la API siempre
  lo asigna).
- **Verificación:** `run_checks.py` **TODO VERDE** (36 unit + 18 e2e); nuevo `tests/unit/test_integridad.py`.

### ✅ T-038 — Extraer helper de armado de estructura (`_append_sections`)

> **Por qué:** `create_song` y `update_song` repetían **verbatim** el triple bucle que arma
> secciones→líneas→acordes/tabs (~16 líneas duplicadas). Un cambio en la estructura obligaba a
> tocar dos sitios y arriesgaba que divergieran.

- **`_append_sections(db_song, sections)`** en `songs_router.py`: construye la jerarquía sobre
  `db_song` apoyándose en los cascades del ORM; no hace commit (la transacción la controla el
  endpoint). `create_song` y `update_song` ahora lo invocan.
- **Refactor puro** (comportamiento idéntico), cubierto por los tests existentes: `test_crud_completo`
  (create con estructura anidada) y `test_put_no_deja_filas_huerfanas` (update la recrea sin fugas).
- **Verificación:** `run_checks.py` **TODO VERDE** (36 unit + 18 e2e).

### ✅ T-020 — Parser de acordes: regex que capta extensiones y alteraciones

> **Por qué:** `CHORD_REGEX` tenía `(m|maj|...)?(\d)?` → **una sola** cualidad y **un solo** dígito.
> No parseaba `add11`/`maj13` (2 cifras) y —pese a lo que decía su comentario— tampoco `Em7b5` ni
> `A7sus4` (cualidad + nº + alteración encadenados). Al pegar de Ultimate Guitar/LaCuerda, esas
> líneas no se detectaban como acordes y el emparejamiento letra↔acorde fallaba.

- **Nuevo regex:** sufijo como **secuencia repetible** de tokens —cualidad (`maj|min|m|M|aug|dim|
  sus|add|+|°|ø`) o número con alteración opcional (`[#b]?\d+`: `7`, `b5`, `#11`, `13`)— + bajo
  opcional (`/G`, `/F#`). Cada token es no vacío → sin backtracking patológico.
- **Cobertura:** `test_ischord_reconoce_acordes_extendidos` (e2e) — valida `add11/maj13/sus2/m7b5/
  7sus4/C13/...` como acordes y descarta palabras normales (`Hola`, `Bad`, `Age`, `Casa`, ...).
- **Cache-busting:** `editor.js v9→v10` en `editor.html` (único que lo referencia).
- **Verificación:** `run_checks.py` **TODO VERDE** (36 unit + 19 e2e).

### ✅ T-018 — Transposición con bemoles correctos

> **Por qué:** `transposeChord` usaba una única escala de **sostenidos**, así que un acorde con
> bemol acababa mal escrito (transponer `Bb` +3 daba `C#` en vez de `Db`). Suena igual pero al
> músico le chirría leer una canción en bemoles salpicada de sostenidos.

- **Doble escala:** `SCALE_SHARP` / `SCALE_FLAT`. `transposeNote(note, semis, preferFlats)` elige.
- **Heurística:** se preserva el estilo de la **raíz original** —con bemol → bemoles; con sostenido
  o natural → sostenidos (comportamiento histórico, no rompe los casos existentes)—. Cada parte del
  acorde (raíz y bajo de `Bb/Db`) conserva su propio estilo. Limitación conocida: una raíz natural
  que cae en tecla negra usa sostenidos (no hay tracking de tonalidad por acorde).
- **Cobertura:** `test_transpose_respeta_bemoles` (e2e) — `Bb`+3→`Db`, `Eb`-2→`Db`, `Bbm7`+3→`Dbm7`,
  `F/Bb`+3→`G#/Db`; y `test_transpose_sube_y_baja_semitonos` sigue verde (naturales→sostenidos).
- **Cache-busting:** `score_render.js v9→v10` en `index.html` y `editor.html`.
- **Verificación:** `run_checks.py` **TODO VERDE** (36 unit + 19 e2e).

### ✅ T-030 — SRI en el `<script>` del CDN de Supabase

> **Por qué:** las 4 páginas cargaban `@supabase/supabase-js@2` (rango **mutable**) sin `integrity`.
> Si el CDN sirviera un bundle alterado (compromiso de supply-chain), el navegador lo ejecutaría sin
> rechistar — y la app maneja tokens de auth.

- **Versión fijada + SRI:** `@2` → `@2.108.1/dist/umd/supabase.js` (inmutable) con
  `integrity="sha384-EjUdIVmzWliPzdzhxZ9ZoO0etXLKWuUPUftAGxP6qH6Lm4oLwoLaJR0Ba4pIDiDL"` y
  `crossorigin="anonymous"`, en `login.html`, `library.html`, `index.html` y `editor.html`. El hash
  se calculó del fichero real que sirve jsDelivr (`openssl dgst -sha384`).
- **Verificación:** el `doctor` (modo **normal**, no test) ejecuta `window.supabase.createClient` al
  cargar `login.html` en su smoke de navegador; si el SRI bloqueara el script o faltara el global,
  saltaría un error JS. **doctor verde** ⇒ el bundle fijado pasa el integrity y expone el global.
  (Los e2e en modo test no tocan el CDN, por eso la cobertura efectiva es el doctor.)
- ⚠️ **Mantenimiento:** subir la versión de supabase-js obliga a **recalcular** el hash SRI.
- **Verificación:** `run_checks.py` **TODO VERDE** (36 unit + 20 e2e).

### ✅ T-032 — Auditoría: la `service_role` key nunca se sirve ni se commitea

> **Por qué:** la service_role key salta RLS; filtrarla (por `/config` o en git) sería crítico.

- **Auditoría (resultado limpio):**
  - El **código** nunca lee una service_role key: `config.py` no define ese campo y usa
    `extra="ignore"`, así que aunque `.env.local` traiga `SUPABASE_SERVICE_ROLE_KEY`, Settings la
    descarta y nunca entra a la app. Todas las menciones en el repo son **documentación/comentarios**
    (CLAUDE, GUIA, SOP), no valores.
  - `git ls-files` confirma que **ningún `.env`** está trackeado; `git log -S service_role` no revela
    ningún **valor** filtrado (solo líneas de docs que usan el término).
  - `/config` solo devuelve `supabase_url` + `supabase_anon_key` + `test_mode`.
- **Guards de regresión (tests):** `test_config_no_expone_service_role` (las claves de `/config` son
  EXACTAMENTE las 3 públicas; el cuerpo no menciona `service_role`) y
  `test_settings_ignora_la_service_role_key` (inyectar `SUPABASE_SERVICE_ROLE_KEY` en el entorno no
  crea atributo ni aparece en `model_dump_json`).
- **Verificación:** `run_checks.py` **TODO VERDE** (38 unit + 20 e2e).

### ✅ T-031 — Ventana de gracia acotada en el caché de token

> **Por qué:** la degradación elegante de T-005 (si Supabase cae, se honra la caché) era
> **ilimitada**: `if cached: return cached[0]` sin tope temporal. Como `_validate_token` devuelve
> `None` tanto si el IdP está caído como si el token fue **revocado**, un token revocado seguía
> pasando indefinidamente mientras su entrada viviera en la caché.

- **Acotado:** la gracia solo aplica dentro de una ventana `expiry + TOKEN_GRACE_SECONDS`
  (`chordflow_token_grace`, default **300s**). Pasada esa ventana, aunque el IdP falle, se
  responde **401** y se **purga** la entrada vieja. Exposición máxima de un token revocado:
  TTL + gracia (≈6 min con los defaults), no "para siempre".
- **Tests:** `test_token_en_cache_sobrevive_caida_de_supabase` actualizado (caché expirada hace 10s,
  dentro de gracia → pasa) y **nuevo** `test_token_fuera_de_la_ventana_de_gracia_se_rechaza`
  (expirada hace 1000s → 401 + entrada purgada).
- **Verificación:** `run_checks.py` **TODO VERDE** (39 unit + 20 e2e).

### ✅ T-041 — Avisar al usuario ante fallos de carga inicial (player)

> **Por qué:** `library.js` y `editor.js` ya avisaban, pero el **reproductor** (`app.js`) ante un
> fallo de carga ponía un mensaje técnico ("Error de conexión con FastAPI") **solo en el título** y
> dejaba el área de partitura **en blanco** — el usuario se quedaba sin saber qué pasó ni cómo salir.

- **`app.js`:** ahora distingue **404** (canción no encontrada/borrada → 🔍 "No encontramos esta
  canción") de **fallo de conexión** (⚠️ "Revisa tu conexión…"), y pinta el aviso en el **área
  principal** (`#score-content`) con un botón **← Volver a la biblioteca**. Mensajes estáticos (sin
  riesgo XSS).
- **Test:** `test_songid_inexistente_avisa_al_usuario` (e2e) — abrir `index.html?songId=no-existe`
  muestra el aviso + la salida a la biblioteca; el título ya no filtra "FastAPI".
- **Cache-busting:** `app.js v10→v11` en `index.html`.
- **Verificación:** `run_checks.py` **TODO VERDE** (39 unit + 21 e2e).

### ✅ T-021 — Accesibilidad: aria-label + atajo Espacio=play

- **`aria-label`** en todos los botones de emoji/icono del reproductor (BPM ±, tono ♭♯💾, 📚, ➕,
  🥁, ⏹, ▶) y en los botones de tarjeta de la biblioteca (✏️/🗑️, con el título de la canción).
- **Atajo de teclado:** la **barra espaciadora** alterna play/pausa (`app.js`), ignorada si el foco
  está en un input/textarea para no romper la escritura; `preventDefault` evita el scroll por defecto.
- **Test:** `test_accesibilidad_aria_y_atajo_espacio` (e2e) — comprueba `aria-label` en varios botones
  y que Espacio arranca la reproducción.
- **Cache-busting:** `app.js v11→v12`, `library.js v11→v12`.
- **Verificación:** `run_checks.py` **TODO VERDE** (39 unit + 22 e2e).

### ✅ T-017 — Toasts y modales en vez de `alert()`/`confirm()`

> **Por qué:** los `alert`/`confirm` nativos rompen el lenguaje glassmorphism, bloquean el hilo y se
> ven "de sistema". Había 1 `confirm` (borrado) y 4 `alert` repartidos por library/editor/app.

- **`util.js`** (compartido, ya cargado antes que el resto): `toast(msg, type)` —aviso no bloqueante
  autodescartable, `info/success/error`, `role=alert/status`— y `confirmModal(msg, opts)` —modal con
  overlay que devuelve `Promise<boolean>`, cierra con Esc/Enter/clic fuera, enfoca el botón OK—.
  Ambos **escapan** el texto del usuario.
- **CSS glassmorphism** en `style.css` (`.toast*`, `.modal-overlay`, `.modal-card`, `.primary-btn.danger`).
- **Reemplazos:** `library.js` (confirm→`confirmModal`, alert→`toast`), `editor.js` (2 alert→toast),
  `app.js` (1 alert→toast).
- **Test:** `test_borrar_usa_modal_y_elimina` (e2e) — el borrado abre el modal propio y al aceptar la
  tarjeta desaparece.
- **Cache-busting:** `style.css→v10` (4 HTML), `util.js→v2` (3), `app.js→v13`, `library.js→v13`,
  `editor.js→v11`.
- **Verificación:** `run_checks.py` **TODO VERDE** (39 unit + 23 e2e).

### ✅ T-019 — Auto-scroll anclado al acorde activo

> **Por qué:** el auto-scroll mapeaba `currentBeat/totalBeats → scrollTop` (lineal). Como los píxeles
> NO son proporcionales a los beats (secciones de distinta densidad de líneas), el acorde activo se
> desfasaba y acababa fuera de pantalla justo cuando hay que leerlo.

- **`app.js`:** ahora seguimos el **elemento DOM del acorde activo** y lo llevamos a ~1/3 de la
  altura visible (teleprompter), vía `getBoundingClientRect` (robusto frente a offsetParent). Solo se
  reposiciona cuando **cambia** el acorde activo (`lastAutoScrollChordId`), para no pelear con el
  scroll suave; se resetea en Stop.
- **Test:** `test_autoscroll_mantiene_visible_el_acorde_activo` (e2e) — con una canción larga (8
  secciones × 4 líneas), tras reproducir el acorde `.active` queda dentro del viewport del contenedor
  y `scrollTop > 0`.
- **Cache-busting:** `app.js v13→v14`.
- **Verificación:** `run_checks.py` **TODO VERDE** (39 unit + 24 e2e).

### ✅ T-040 — Casos borde de `findActiveChord` (sync)

> **Por qué:** el intervalo semiabierto `[start, nextStart)` con `nextStart = start+duration` para
> el último acorde lo apagaba antes de tiempo (la parte final quedaba sin acorde resaltado), y los
> empates de beat de inicio podían "saltarse" un acorde.

- **`sync_engine.js`:** `findActiveChord` ahora devuelve el **último acorde cuyo inicio ya pasó**
  (lista ordenada). Esto resuelve a la vez: **último acorde** persiste hasta el final; **empates**
  (gana el último); **reset** (antes del primer acorde → null).
- **Test:** `tests/e2e/test_sync_engine.py` (unit-en-navegador con `SyncEngine` global) —
  `test_findactivechord_casos_borde` (reset/avance/persistencia) y `test_findactivechord_empate_de_inicio`.
- **Cache-busting:** `sync_engine.js v7→v8`.
- **Verificación:** `run_checks.py` **TODO VERDE** (39 unit + 26 e2e).

### ✅ Fase 6 — Despliegue (Supabase + Postgres + Vercel)

> **Paso 1 (Supabase):** proyecto nuevo `fwynfifvtthtpzpejfhb` (el anterior fue borrado → DNS NXDOMAIN).
> Claves nuevas de Supabase (`sb_publishable_` pública / `sb_secret_` secreta, no usada por la app).
> Login real verificado (registro + login navegador + `/songs/` 200). Confirmación de email: el alta
> por web requiere confirmar (o desactivar "Confirm email" en el panel); las cuentas existentes se
> pueden confirmar vía admin API.
> **Paso 2 (Postgres):** `psycopg2-binary`; `render_as_batch` solo en SQLite; `pool_pre_ping` en
> Postgres; `env.py` escapa `%` (passwords con caracteres especiales). Esquema creado con `create_all`
> + `alembic stamp/upgrade`. **2 bugs de portabilidad corregidos:** `is_public` server_default `0`→
> `false` (Postgres rechaza int en boolean) y `TEST_USER_ID` 37→36 chars (cabe en VARCHAR(36)). Conexión
> por **pooler** (la directa `db.<ref>` es IPv6-only y no resuelve): host `aws-1-eu-central-1.pooler.
> supabase.com`, user `postgres.<ref>`, 5432 sesión (migraciones) / 6543 transacción (runtime).
> **Paso 3 (Vercel):** `api/index.py` (reutiliza `src.main:app`), `vercel.json` (@vercel/python +
> includeFiles static/**), `.vercelignore` (excluye tests/harness/alembic/pyproject — su `uv` peta
> sin `[project]`). `main.py`: ruta de `static/` ABSOLUTA + `create_all` en try/except. `logging_config`:
> fallback a stdout si el FS es de solo lectura. Verificado en vivo: login + CRUD (Vercel→Postgres).

### ✅ Fase 5 — Responsive + PWA + Export PDF

- **Responsive móvil/tablet:** media queries 820/480px en `style.css` — barras superior/inferior
  envuelven, editor y formularios se apilan, partitura con scroll horizontal, targets táctiles ≥44px,
  rejilla a 1 columna en móvil. Test `test_responsive_pwa::test_sin_scroll_horizontal_en_movil` (4 páginas).
- **PWA instalable:** `manifest.json` + iconos 192/512 (`static/icons/`) + `sw.js` (service worker:
  API nunca cacheada, HTML network-first, estáticos cache-first porque van con hash de T-022).
  Registrado en `auth.js`; `<link rel=manifest>`+theme-color+apple-touch-icon en las 4 HTML.
- **Export PDF:** botón 🖨️ en el reproductor → `window.print()` + `@media print` (solo la partitura
  en B/N, sin controles, sin cortar secciones entre páginas). Respeta la transposición actual.
  Test `test_player::test_export_pdf_oculta_controles` (emula media print).

### ✅ Fase 5 — Setlists / repertorios

- **Modelos:** `Setlist` (name, owner_id NOT NULL, timestamps, soft delete) + `SetlistItem`
  (setlist_id/song_id FK ondelete CASCADE, position). Migración `3684ab6335e8` (alembic check limpio).
- **API `/setlists/`** (auth, owner-filtered): list (con `song_count`), create (valida que las
  `song_ids` sean del usuario y no borradas, preservando orden), get (omite canciones borradas),
  patch (renombrar / reemplazar+reordenar canciones), delete (soft).
- **Frontend:** `setlists.html`+`setlists.js` (crear con selección ordenada, ver, quitar canción,
  borrar) + enlace **🎼 Repertorios** en la biblioteca. **Reproductor:** barra `#setlist-nav` con
  anterior/siguiente y posición cuando se abre con `?setlist=&pos=`.
- **Tests:** `test_setlists.py` (unit: CRUD, filtrado de ajenas/borradas, soft delete, 401) +
  `test_setlists_ui.py` (e2e: crear con canciones y verlo). Verificado EN VIVO (Vercel→Postgres).

### ✅ T-045 — Importar partitura desde URL con IA (EN VIVO, verificado)

> Estado final: **funcionando en producción** (https://chordflow-ecru.vercel.app). Modelo gratuito
> `openai/gpt-oss-120b:free` (el llama-3.3 free estaba saturado upstream). **Gotcha del deploy:** el
> lector Jina sin key se rate-limitea desde las IPs de datacenter de Vercel (devolvía "sin partitura")
> → añadido **fallback de descarga directa + limpieza de HTML** en `fetch_page_text`, que sí funciona
> desde Vercel. `OPENROUTER_API_KEY`/`OPENROUTER_MODEL` en `.env.local` y en Vercel (producción).
> Verificado en vivo con CifraClub y e-chords; Ultimate Guitar bloquea por Cloudflare (avisado en la UI).
> (Detalle de implementación abajo.)

### T-045 (detalle de implementación)

> **Por qué:** que el usuario pegue un enlace y la app saque la partitura sola. Decisión del usuario:
> proveedor de IA **gratuito** (OpenRouter, tarea simple) + lector **Jina** para sortear JS/anti-bot.

- **Backend:** `src/services/importer.py` (lector Jina `r.jina.ai` por urllib → texto; OpenRouter
  chat/completions por urllib → partitura en el formato del editor). `src/api/import_router.py`:
  `POST /import/` con auth, `HttpUrl` (422 si inválida), errores → 502 con mensaje de usuario.
- **Config (T-016):** `OPENROUTER_API_KEY` (gratis), `OPENROUTER_MODEL` (default
  `meta-llama/llama-3.3-free`), `OPENROUTER_BASE_URL`, `CHORDFLOW_READER_URL`,
  `CHORDFLOW_IMPORT_MAX_CHARS` (tope de tokens). Sin nuevas deps (todo por urllib stdlib).
- **Frontend:** input de URL + botón "Importar con IA" en el editor → `apiFetch('/import/')` →
  rellena el textarea + vista previa + toast. El usuario revisa antes de guardar.
- **Tests:** `tests/unit/test_import.py` (IA mockeada: 200, 422 URL inválida, 502 error, 401 sin
  token) + e2e `test_importar_desde_url_rellena_el_editor` (ruta `/import/` mockeada con Playwright).
- **Verificación:** `run_checks.py` **TODO VERDE** (44 unit + 24 e2e) con la IA mockeada. **Pendiente:**
  poner `OPENROUTER_API_KEY` real (local + Vercel) y probar con un enlace de verdad.

### ✅ T-022 — Cache-busting automático por hash de contenido

> **Por qué:** el `?v=N` manual obligaba a recordar subir el número en **todos** los `.html` al tocar
> un `.js`/`.css` (mordió varias veces). Error humano clásico y silencioso.

- **`harness/cachebust.py`:** reescribe el `?v=` de cada asset **local** de `static/*.html` con un
  `sha256[:8]` de su contenido (ignora URLs http(s): CDN/fuentes). Modo `--check` (no escribe; sale 1
  si algún `?v=` está desfasado) + modo aplicar.
- **Aplicado:** todos los `?v=N` manuales → `?v=<hash>`.
- **Enforcement:** `test_cache_busting_al_dia` (unit) corre `check()` → `run_checks` **falla** si se
  edita un asset sin reejecutar el script. Se acabó la clase de error.
- **CLAUDE.md** §4 actualizado: la regla ahora es "ejecutar `cachebust.py`".
- **Verificación:** `run_checks.py` **TODO VERDE** (40 unit + 26 e2e).

### ✅ T-M04 + T-M05 — Guía de uso del molde + generador `create_app.py` (en `../app-skeleton`)

> **Por qué:** cerrar la Fase M con (1) una guía clara de cómo nace un proyecto desde el molde y
> (2) el cookiecutter que automatiza los huecos. Hecho en el repo hermano `../app-skeleton`
> (commit `1efcf67`).

- **T-M04:** `harness/MOLDE.md` §5 "Guía de uso paso a paso" — dos caminos (automático con
  `create_app.py` vs manual con `git archive`), de cero a la primera tarea del bucle. README ya
  cubría el resumen; ahora la guía es explícita y completa.
- **T-M05:** `create_app.py` (cookiecutter ligero): copia el esqueleto (excluye `.git`/caches/`*.db`
  y el meta-test), rellena `{{APP_NAME}}/{{DESCRIPTION}}/{{STACK}}/{{ENV_PREFIX}}` en los docs y
  renombra el prefijo de env `APP_` → el elegido en **código, config y tests** (no en los nombres
  estándar `DATABASE_URL`/`SUPABASE_*`). `argparse`, no interactivo.
- **Verificación (end-to-end):** generé un proyecto real (`--prefix DEMO`) y su `run_checks.py`
  quedó **TODO VERDE** (doctor + ruff + unit + 4 e2e) **sin tocar dominio** — el modo test renombrado
  (`DEMO_TEST_MODE`) funciona en navegador. Tests `test_create_app.py` en el molde. **Fase M COMPLETA.**

---

<a name="bloque-v2"></a>
## Bloque V2 — Giro a SaaS de gestión de bandas (Fase 7+)

> Dirección de producto en `GUIA_MAESTRA_V2.md` + `GUIA_MAESTRA_V2_FUNCIONAL.md` (14 áreas resueltas,
> convenciones §C.4.3, detalle Fase 7 §C.5). **Todo aditivo** (no rompe producción). La joya
> (reproductor + `sync_engine.js`/`score_render.js`) queda intacta.

### T-048 — Migración aditiva: núcleo de identidad de banda ✅ (local; falta aplicar a Postgres)

**Qué:** primeras 4 tablas del giro multi-tenant — `musician_profiles`, `bands`, `band_memberships`,
`band_invites`.

**Por qué:** es la **fundación** de la que cuelga todo el giro (Fases 8–21). Sin romper nada de lo
existente (`songs`/`setlists`/… no se tocan). `Song.band_id`/`Setlist.band_id` NO entran aquí (son
Fases 8 y 9).

**Cómo:**
- `src/services/models.py`: 4 modelos nuevos siguiendo las **convenciones §C.4.3**:
  - Índice en `band_id` y en las FKs (rendimiento + consultas de aislamiento); timestamps en UTC.
  - **Soft-delete** (`deleted_at`) en `Band` (tiene histórico/valor).
  - `BandMembership`: `role` (`admin|member|guest`), `status` (`active|left`) + `left_at` (**baja
    blanda**: la fila permanece para el histórico), único `(band_id, user_id)`.
  - CHECK de BD para `role`/`status`/`role_to_grant` (fuentes únicas `BAND_ROLES`/`MEMBERSHIP_STATUSES`,
    mismo patrón que `LINE_TYPES`).
  - `MusicianProfile.id` = user_id de Supabase (no se genera) → nombres reales en vez de UUIDs.
  - FKs `bands.id` con `ondelete=CASCADE` + relaciones ORM `cascade=all, delete-orphan`.
- `alembic/versions/…_39fbdc0fff0f_core_de_banda_identidad_t_048.py`: migración **autogenerada y
  revisada** — **solo aditiva** (4 `CREATE TABLE` + índices/CHECK/FK/unique; nada destructivo). Down
  revision `3684ab6335e8`.
- `tests/unit/test_migrations.py::test_upgrade_crea_el_nucleo_de_banda`: cubre que `upgrade head` crea
  las 4 tablas + índices `band_id` + único `(band_id, user_id)`, y que las tablas existentes siguen.

**Nota de proceso:** el autogenerate inicial salió contaminado porque el `chordflow.db` local es un
`create_all` antiguo (precede a T-012/T-033/T-034). Se regeneró comparando contra una **BD temporal
construida por las migraciones** → migración limpia con solo las 4 tablas.

**Verificación:** `alembic check` → *No new upgrade operations detected* (sin drift) · `doctor.py`
verde (10/10) · 50/50 unit verdes (incl. los 3 de migración).

**Pendiente de despliegue:** aplicar a la Postgres de producción con el **pooler 5432** (o `alembic
stamp 39fbdc0fff0f` tras el `create_all` del próximo deploy). **No se ha tocado producción todavía.**

### T-049 — Schemas Pydantic del núcleo de banda ✅

**Qué:** schemas de entrada/salida de las 4 entidades de T-048.

**Cómo:** en `src/services/schemas.py`: `MusicianProfileUpsert/Response`, `BandCreate/Update/Response`,
`BandSummary` (banda + mi rol + nº de miembros para "Mis bandas"), `BandMembershipResponse`
(con `display_name` para mostrar nombres reales) + `MembershipRoleUpdate`, `BandInviteCreate/Response`.
`role`/`status` validados con `Literal` (mismo patrón que `LineBase.type`).

**Verificación:** `tests/unit/test_schemas_banda.py` (8 casos): roles válidos/ inválidos, default
`member`, `max_uses ≥ 1`, y un test que comprueba que los `Literal` **siguen alineados** con
`models.BAND_ROLES`/`MEMBERSHIP_STATUSES` (validación de schema y CHECK de BD nunca divergen).
Doctor verde, ruff limpio.

### T-050 — Auth multi-tenant (base del aislamiento) ✅ 🔴

**Qué:** las dos dependencias FastAPI que blindan el **aislamiento entre bandas** — la mayor
superficie de riesgo del giro (una fuga = ver datos de una banda ajena).

**Por qué:** todo recurso de banda (Fases 8–21) debe validar pertenencia+rol antes de tocar nada.
Centralizar esto en dos dependencias reutilizables evita repetir (y olvidar) el chequeo ruta a ruta.

**Cómo:** `src/services/band_auth.py`:
- `require_band_member(band_id)`: consulta `BandMembership` **activo** join `Band` no borrada; si no
  hay → **404** (a un ajeno no se le confirma ni la existencia de la banda). Miembro de baja
  (`status='left'`) o banda con soft-delete → 404 también. Devuelve el `BandMembership` (con rol).
- `require_band_admin`: **compone** sobre `require_band_member` (FastAPI resuelve `band_id` de la
  ruta para la dependencia anidada) y exige `role=='admin'`, si no → **403**. Un ajeno sigue
  obteniendo 404 antes que 403 (no distingue "no eres admin" de "no existe").

**Verificación:** `tests/unit/test_band_auth.py` (7 casos) monta una mini-app con dos rutas guardadas
y controla el usuario actuante vía `dependency_overrides`. Matriz completa: miembro→200, ajeno→404,
no-admin en ruta admin→403, admin→200, ajeno en ruta admin→404 (no 403), baja→404, banda borrada→404.
**65 unit verdes**, ruff limpio, doctor 10/10.

### T-051 — Endpoints de banda (CRUD + aislamiento) ✅

**Qué:** primer router del giro, `src/api/bands_router.py` (montado en `main.py`):
- `POST /bands/` → crea la banda y mete al creador como `admin` (su primera membresía activa). 201.
- `GET /bands/` → "mis bandas" (membresía activa, banda no borrada) con **mi rol** y **nº de
  miembros**; el conteo va en **una query agregada** (`group_by`) para evitar N+1 (patrón T-010).
- `GET /bands/{id}` → ver (cualquier miembro activo, vía `require_band_member`).
- `PATCH /bands/{id}` → editar (solo admin, `require_band_admin`; `exclude_unset` para parche parcial).
- `DELETE /bands/{id}` → **soft delete** (solo admin); las membresías permanecen (histórico). 204.

**Verificación:** `tests/unit/test_api_bands.py`: CRUD completo como creador-admin (crear→listar con
rol/contador→ver→editar→borrar→ya no aparece/404) + **test de aislamiento por ruta** (un ajeno, vía
override de `get_current_user`, recibe 404 en ver/editar/borrar y no la lista; la banda queda intacta
para su dueño) + nombre vacío→422. **68 unit verdes**, ruff limpio, doctor 10/10.

### T-052 — Endpoints de membresía ✅

**Qué:** gestión de miembros en `bands_router.py`: `GET /bands/{id}/members` (lista TODOS, incl. de
baja, con `display_name` del perfil + `is_me`), `PATCH .../{user_id}` (cambiar rol),
`DELETE .../{user_id}` (**baja blanda**: `status='left'`+`left_at`), `POST .../{user_id}/reactivate`.
**Salvaguarda:** no se puede degradar/dar de baja al **último admin** activo (la banda nunca queda
sin administrador). **Verificación:** `test_api_memberships` (6 casos): nombre real, cambiar rol,
baja corta acceso pero conserva histórico + reactivar recupera acceso, no-sin-admin (400),
aislamiento (ajeno→404), miembro normal no cambia roles (403).

### T-053 — Invitaciones por código ✅

**Qué:** unirse a una banda por enlace, sin depender de emails (§8). `POST /bands/{id}/invites`
(admin; código `secrets.token_urlsafe(16)`), `GET /bands/{id}/invites` (listar, admin). Router nuevo
`invites_router.py`: `GET /invites/{code}` previsualiza (nombre de banda + rol + validez, sin exponer
datos sensibles) y `POST /invites/{code}/accept` crea la `BandMembership` (o **reactiva** la del que
estaba de baja con el rol de la invitación) y consume un uso. Validez = banda no borrada + no caducada
(`expires_at`) + no agotada (`used_count<max_uses`); comparación de fecha robusta a naive/aware.
**Verificación:** `test_api_invites` (6 casos): generar+previsualizar+aceptar (entra y ve la banda),
2º accept→409, caducada→400, agotada por `max_uses`→400, solo admin genera (ajeno→404), código
inexistente→404.

### T-054 — Perfil del músico ✅

**Qué:** `profile_router.py` — `GET /profile/me` (crea el perfil vacío la 1ª vez: "autorelleno en
primer login") y `PUT /profile/me` (display_name, instruments, avatar_url; parche parcial). El perfil
da el **nombre real** que sustituye al UUID en la lista de miembros. **Verificación:**
`test_api_profile` (3 casos): GET autocrea, PUT edita y persiste, el nombre aparece en `/members`.

### T-055 — Frontend del núcleo de banda ✅

**Qué:** primeras pantallas del giro (vanilla, mismos patrones que setlists):
- `bands.html`/`bands.js`: **Mis bandas** (lista con rol+nº miembros, crear vía `promptModal`),
  **detalle** de banda (miembros activos + antiguos, nombre real) e **invitar por enlace** (genera
  invitación, copia el link `join.html?code=…` al portapapeles y lo muestra).
- `join.html`/`join.js`: abrir un enlace de invitación → previsualiza (banda + rol + validez) y
  **unirse**; gestiona 404/409/caducada.
- `profile.html`/`profile.js`: editar nombre visible e instrumentos.
- `util.js`: nuevos `promptModal` (input) y `alertModal` (informativo) en el estilo de `confirmModal`
  (reemplazan `prompt()`/`alert()`, coherente con T-017). Enlace **🎸 Mis bandas** en la biblioteca.
- `sw.js`: el service worker **excluye de caché** las rutas dinámicas nuevas (`/bands`, `/invites`,
  `/profile`, y de paso `/setlists` que faltaba) → nunca sirve datos de usuario cacheados.
- `cachebust.py` ejecutado (hashes `?v=` al día) + 7 filas (B1–B7) en `CHECKLIST_E2E.md`.

**Verificación:** e2e `test_bands_ui` (3 casos, navegador real): crear banda y verme como Admin con
mi nombre de perfil + generar invitación con enlace `join.html?code=` + previsualizarlo; la banda
aparece en la rejilla; editar perfil persiste al recargar.

### T-056 — Cierre de la Fase 7 ✅

**Qué:** verificación integral y revisión de sección.
- `run_checks.py` **TODO VERDE**: doctor 10/10 · ruff · **83 unit** · **38 e2e** (incluye aislamiento
  por cada ruta de banda — la regla de oro).
- `revision.py fase7` → **✅ completa** (3/3 rutas `/bands`,`/invites`,`/profile` · 3/3 páginas
  `bands.html`,`join.html`,`profile.html`); actualizado el mapa de la fase7 a lo realmente integrado.
- Veredicto ✅ anotado en `harness/REVISIONES.md` (con trazabilidad de cada ítem del checklist a su
  test). Decisiones de producto cerradas: **nombre = BandFlow** (rebranding en Fase 13), **EUR**.

**Pendiente (no bloquea la fase, requiere acción de Oscar — ver `PENDIENTES_OSCAR.md`):** aplicar la
migración a **Postgres de producción** (pooler 5432) y el **push a `main`** (auto-deploy). En local
todo verde y aplicado.

> **🏁 Fase 7 (Identidad + núcleo de banda) COMPLETA.** Base multi-tenant lista: identidad, bandas,
> membresía con baja blanda, invitaciones por código, perfil — con aislamiento blindado y probado.
> Siguiente: **Fase 8 (Repertorio de banda — `Song.band_id`)**.

---

## Bloque V2-F8 — Fase 8: Repertorio de banda

### T-057 — Migración `Song.band_id` ✅

**Qué/Por qué:** `Song` gana `band_id` (nullable, FK `bands` ondelete CASCADE, index): NULL = canción
personal; con valor = está en el repertorio de esa banda. Aditivo, no rompe nada (las canciones
actuales quedan personales). **Cómo:** migración `908a0a3875b1` (batch mode; FK **nombrada**
`fk_songs_band_id_bands` porque `env.py` tiene `naming_convention` y el FK anónimo fallaba).
`alembic check` limpio (sin drift). `band_id` añadido a `SongResponse`/`SongSummary`.

### T-058 — Repertorio de banda (backend) ✅

**Qué:** `band_songs_router.py` con prefijo `/bands/{band_id}/songs`: listar (miembros), crear nueva
(miembros, no guest), **copiar** una personal a la banda (copia profunda independiente, decisión §7)
y quitar (soft delete). **Cambios en `songs_router.py`** (sin romper lo personal):
- `GET /songs/` (personales) ahora filtra también `band_id IS NULL` → las de banda no se mezclan.
- `GET/PUT/PATCH/DELETE /songs/{id}` usan un helper `_get_song_authorized` que autoriza: personal →
  debe ser del `owner_id` (mismo 404 de antes); de banda → **miembro activo** (ajeno→404), y para
  **escritura** un `guest`→403. Así el **reproductor (la joya) abre canciones de banda** a sus
  miembros sin tocar el comportamiento personal.

**Verificación:** `test_api_band_songs` (6 casos): separación personal/banda, copia independiente
(editar la copia no toca la personal), reproductor por pertenencia (miembro 200 / ajeno 404), miembro
edita / guest 403 (pero lee), quitar (soft delete), aislamiento completo (ajeno→404).

### T-059 — Repertorio de banda (frontend) ✅

**Qué:** en la ficha de banda (`bands.js`/`bands.html`): sección **📚 Repertorio** que lista las
canciones, **▶ reproduce** (abre el reproductor con la canción de banda), permite **copiar** una de
mis partituras (modal selector propio → `POST .../songs/copy`) y **quitar** del repertorio. Un guest
ve el repertorio pero no los botones de edición. `cachebust.py` ejecutado.

**Verificación:** e2e `test_bands_ui::test_copiar_cancion_personal_al_repertorio_de_banda` (navegador
real: abrir banda → copiar "Tema Personal" → aparece en el repertorio). **run_checks TODO VERDE:
89 unit + 39 e2e.** Revisión `revision.py fase8` ✅ completa; veredicto en `REVISIONES.md`.

**Diferido (no bloquea, anotado):** metadatos ricos de Área 1 (`status`/`tags`/notas/`reference_url`/
`duration_seconds`) y crear canción nueva de banda desde el editor.

> **🏁 Fase 8 (Repertorio de banda) COMPLETA.** Cada banda tiene su repertorio compartido por copia,
> reproducible por sus miembros, con aislamiento probado. Siguiente: **Fase 9 (Setlists de banda)**.

---

## Bloque V2-F9 — Fase 9: Setlists de banda

### T-060 — Migración `Setlist.band_id` + `SetlistItem.note` ✅

**Qué/Por qué:** `Setlist` gana `band_id` (nullable, FK `bands` CASCADE, index): NULL = personal; con
valor = setlist de esa banda. `SetlistItem` gana `note` (Text) para apuntes por canción (Área 3 #27).
Aditivo. **Cómo:** migración `95eddae092db` (batch; FK nombrada `fk_setlists_band_id_bands`).
`alembic check` limpio. `band_id`/`note` añadidos a los schemas de salida.

### T-061 — Setlists de banda (backend) ✅

**Qué:** `band_setlists_router.py` (`/bands/{band_id}/setlists`, CRUD). Las canciones de un setlist de
banda **solo pueden ser del repertorio de esa banda** (`_valid_band_song_ids` filtra por `band_id`).
**Cambios en `setlists_router.py`** (personales intactos): `GET /setlists/` excluye `band_id`;
`GET /setlists/{id}` (reproductor) autoriza al dueño (personal) o a un miembro activo (banda),
ajeno→404; `PATCH`/`DELETE /setlists/{id}` quedan **estrictamente personales** (`band_id IS NULL`) →
los de banda se editan en su router (guest→403). Reusa `_to_response` para no divergir.

**Verificación:** `test_api_band_setlists` (6 casos): crear desde repertorio (orden respetado, no sale
en personales), filtra canciones fuera del repertorio, reproductor por pertenencia (miembro 200 /
ajeno 404), guest no edita (403) pero ve, editar+borrar (soft delete), aislamiento completo.

### T-062 — Setlists de banda (frontend) ✅

**Qué:** sección **🎵 Setlists** en la ficha de banda (`bands.js`): listar (con nº de canciones),
**▶ reproducir en orden** (abre el reproductor con `?setlist=&pos=`, barra ◀▶), **crear** desde el
repertorio (editor *available/selected* con orden) y **borrar**. Guest sin botones de edición.
`cachebust.py` ejecutado.

**Verificación:** e2e `test_bands_ui::test_crear_setlist_de_banda_desde_la_ui` (navegador real: abrir
banda → nuevo setlist → elegir del repertorio → guardar → aparece). **run_checks TODO VERDE: 95 unit +
40 e2e.** Revisión `revision.py fase9` ✅ completa.

**Diferido (no bloquea):** editar la `note` por canción del setlist (columna + salida ya listas;
falta UI/endpoint para fijarla).

> **🏁 Fase 9 (Setlists de banda) COMPLETA.** Cada banda arma setlists reutilizables desde su
> repertorio, reproducibles en orden por sus miembros, con los personales preservados y aislamiento
> probado. Siguiente: **Fase 10 (Agenda — eventos)**.

---

## Bloque V2-F10 — Fase 10: Agenda (eventos) [núcleo]

### T-063 — Migración `events` + `event_attendance` ✅

**Qué:** dos tablas nuevas. `events` (id, band_id, **type** rehearsal|concert|other, title,
starts_at/ends_at, location, notes, **status** pipeline lead…cancelled default confirmed, **setlist_id**
FK SET NULL, created_by, soft-delete) y `event_attendance` (event_id, user_id, **status** yes|no|maybe,
único `(event_id,user_id)`). CHECK para type/status/attendance (fuentes únicas `EVENT_TYPES`/
`EVENT_STATUSES`/`ATTENDANCE_STATUSES`). Migración `22c7ea96b921`, `alembic check` limpio.

### T-064 — Agenda backend ✅

**Qué:** `events_router.py` (`/bands/{id}/events`). **Decisión §2.8:** crear/editar/borrar =
`require_band_admin`; listar/ver/asistencia = `require_band_member` (asistencia también para guest).
`PUT .../{eid}/attendance` hace upsert de mi voy/no voy/quizás. El **setlist solo se adjunta a
conciertos** y debe ser de la banda (`_validate_setlist` → 400 si no). La lista trae `my_status`; el
detalle, la asistencia de todos con nombre real. **Verificación:** `test_api_events` (6 casos): admin
crea/miembro no (403), asistencia (cambia de idea), guest asiste, setlist validado (tipo+banda, 400),
editar/borrar solo admin, aislamiento (ajeno→404 en todo).

### T-065 — Agenda frontend ✅

**Qué:** sección **📅 Agenda** en la ficha de banda (`bands.js`): eventos separados en **próximos/
pasados**, botones de **asistencia** (✅ Voy / 🤔 Quizás / ❌ No voy) que resaltan mi elección, y
**crear evento** (solo admin: modal con tipo/título/fecha y, si es concierto, selector de setlist de
la banda). Estilos `.att-btn.active` en `style.css`. `cachebust.py` ejecutado.

**Verificación:** e2e `test_bands_ui::test_crear_evento_y_marcar_asistencia_en_la_ui` (navegador real:
crear ensayo con fecha → aparece en la agenda → marcar "Voy" → se resalta). **run_checks TODO VERDE:
101 unit + 41 e2e.** Revisión `revision.py fase10` ✅ completa.

**Diferido (Áreas 2/3/4, no bloquea):** `EventSong` (orden del día), `Venue`, `BandResource`,
checklist pre-bolo con responsable, campos de concierto (cronograma/soundcheck), logística; el
pipeline de booking (lead→confirmed) se explota en la Fase 14.

> **🏁 Fase 10 (Agenda — núcleo) COMPLETA.** La banda gestiona ensayos y conciertos con asistencia,
> y adjunta setlists a los conciertos, con aislamiento probado. Siguiente: **Fase 11 (Finanzas con
> división)**.

---

## Bloque V2-F11 — Fase 11: Finanzas con división (Splitwise)

### T-066 — Migración finanzas + `Band.currency` ✅

**Qué:** `transactions` (type expense|income, amount Decimal(10,2), paid_by, **paid_by_fund**, event_id
SET NULL, soft-delete), `transaction_splits` (user_id|**to_fund**, share_amount), `settlements`
(from/to_user|**to_fund**, amount, soft-delete) + `Band.currency` (default **EUR**, §C.4.3). El fondo
es un participante virtual (flags), no una tabla. Migración `84c9ca4f7b64`, `alembic check` limpio.

### T-067 — Servicio único de balances ✅ 🔴 (la zona de mayor riesgo)

**Qué:** `services/balances.py` — **función pura** `compute_balances(transactions, settlements,
member_ids)` + `equal_split_amounts`. Fórmula Splitwise: gasto → pagador +amount, partes −share;
ingreso → pagador −amount, partes +share; liquidación → +from/−to; fondo como participante. Todo en
`Decimal` a céntimos; el último split absorbe el redondeo. **Invariante: la suma de saldos = 0.**

**Verificación:** `test_balances` (6 casos, sin BD): **el ejemplo exacto de la guía** (ingreso 400 +
gasto 60 → A −315, B +145, C/D +85, cuadra a 0), aportación al fondo, gasto pagado por el fondo,
liquidación que acerca a cero, reparto 100/3 con céntimos que igual cuadra. Aislada y exhaustiva
porque es donde más fácil se cuela un bug.

### T-068 — Finanzas backend ✅

**Qué:** `finance_router.py` (`/bands/{id}/transactions|balances|settlements`). Registrar/borrar/
liquidar = `require_band_admin`; ver = `require_band_member` (matriz §C.2). Al crear un movimiento:
valida el pagador (miembro activo o fondo), el evento (de la banda), y el reparto (cada parte de un
miembro activo y **Σ partes == amount**, si no → 400); si no se envían `splits`, **reparto a partes
iguales** entre miembros activos. Borrado financiero = soft delete (nunca duro). `/balances` delega en
el servicio único. **Verificación:** `test_api_finance` (8): reparto por defecto + balances cuadran,
Σ≠total→400, pagador no-miembro→400, ingreso+liquidación a cero, aportación al fondo, solo-admin,
soft delete recalcula, aislamiento (ajeno→404 en todo).

### T-069 — Finanzas frontend ✅

**Qué:** sección **💶 Finanzas** en la ficha de banda (`bands.js`): **panel de saldos** (verde "le
deben" / rojo "debe" / "al día", con el 🏦 fondo), **registrar movimiento** (admin: tipo/descr/importe/
pagador, reparto a partes iguales), **liquidar** (admin: de quién → a quién/fondo) y **lista de
movimientos** con borrado. Estilos `.bal-pos`/`.bal-neg`. `cachebust.py` ejecutado.

**Verificación:** e2e `test_bands_ui::test_registrar_movimiento_y_ver_saldos_en_la_ui` (navegador real).
**run_checks TODO VERDE: 115 unit + 42 e2e.** Revisión `revision.py fase11` ✅ completa.

**Diferido (no bloquea):** editor de **reparto personalizado** en la UI (el backend ya acepta `splits`);
informes/export CSV; cuotas recurrentes; ligar un movimiento a un evento desde la UI.

> **🏁 Fase 11 (Finanzas con división) COMPLETA.** La banda lleva sus cuentas estilo Splitwise con
> saldo neto por miembro + fondo que **cuadra a cero**, reparto y liquidaciones, todo solo-admin y con
> aislamiento probado. Siguiente: **Fase 12 (Comunicación — chat + notas + notificaciones)**.

---

## Bloque V2-F12 — Fase 12: Comunicación (chat + notas) [núcleo]

### T-070 — Migración `messages` ✅

**Qué:** tabla `messages` (band_id, **event_id** null=chat general / valor=hilo del evento, author_id,
body, **is_pinned** = nota, created_at, edited_at, soft delete). Índices `band_id`/`event_id`.
Migración `7022a3162284`, `alembic check` limpio.

### T-071 — Chat backend ✅

**Qué:** `messages_router.py` (`/bands/{id}/messages`). Publicar = cualquier miembro activo (incl.
**guest**, matriz §C.2); listar = chat general (sin `event_id`) o **hilo** (`?event_id=`), con los
**fijados primero**. Editar = solo el autor (marca `edited_at`). Borrar = el autor el suyo, **admin
cualquiera** (soft delete). **Fijar/desfijar nota** = solo admin. Hilo a un evento de otra banda → 400.
**Verificación:** `test_api_messages` (7): publicar/listar, guest escribe, editar+borrar propio,
no-ajeno-salvo-admin, fijar solo admin (aparece arriba), hilo separado del general, aislamiento.

### T-072 — Chat frontend ✅

**Qué:** sección **💬 Chat** en la ficha de banda (`bands.js`): lista de mensajes con **refresco
periódico** (cada 6 s; el timer se detiene al salir de la ficha), enviar (input + Enter), **fijar**
nota (admin, 📌 arriba) y **borrar** (autor o admin). Estilos `.msg-pinned`. `cachebust.py` ejecutado.

**Verificación:** e2e `test_bands_ui::test_enviar_mensaje_en_el_chat_de_banda` (navegador real).
**run_checks TODO VERDE: 122 unit + 43 e2e.** Revisión `revision.py fase12` ✅ completa.

**Diferido (no bloquea):** UI del **hilo por evento** (el backend ya lo soporta vía `?event_id=`);
`Poll`/encuestas, `Notification`/campana, @menciones; tiempo real (Supabase Realtime) sin tocar modelo.

> **🏁 Fase 12 (Comunicación — núcleo) COMPLETA.** La banda habla por un chat general con notas
> fijadas e hilos por evento (backend), con refresco periódico y aislamiento probado. **Con esto se
> cierra el NÚCLEO del giro (Fases 7–12).** Siguiente: **Fase 13 (Shell nueva + perfil + pulido +
> rebranding a BandFlow)**.

---

## Bloque V2-F13 — Fase 13: App shell (nav TÚ/BANDA) + sistema de diseño + rebranding

> **Rumbo (2026-06-16):** rediseño visual a app profesional con **lateral fijo** y **dos contextos**:
> **TÚ** (cockpit agregado de todas mis bandas) y **BANDA** (espacio de gestión con banner + pestañas,
> todo con scope a su `band_id`). Spec en `GUIA_MAESTRA_V2.md` §3 reescrito + §10. **Reskin sobre el
> stack actual** (HTML/CSS/JS vanilla); la joya (`sync_engine.js`/`score_render.js`) no se toca.
> Orden de tareas (T-073…T-083): fundación (diseño → shell) → vistas agregadas → reskin → marca.

### T-073 — Sistema de diseño (`design-system.css`) ✅

**Qué:** fundación visual única `static/design-system.css` — **tokens** (superficies y texto oscuro/
claro vía `:root[data-theme="light"]`, **acento como perilla única** `--bf-primary`, tipografía,
espaciado 4px, radios, sombras, métricas del shell) + **componentes base** (botón, card, input, badge
de rol, tabs, lista, avatar, `nav-item`, **banner de banda**, saldo +/−, utilidades).

**Por qué:** todo el reskin (shell T-074, espacio de banda T-075, vistas agregadas, joya) se apoya en
una sola fuente de aspecto; cuando lleguen los diseños de Claude Design se reescriben los tokens y los
componentes se actualizan solos.

**Cómo:** clases con prefijo **`bf-`** para **no colisionar** con `style.css` ni con el player (las
páginas actuales siguen intactas hasta el reskin de T-081). Self-contained, aún sin cablear a HTML.

**Verificación:** `tests/unit/test_design_system.py` (se sirve como `text/css` + declara tokens y
componentes clave). **Doctor 10/10 verde.**

---

<a name="notas"></a>
## 11. Notas técnicas recurrentes

- **Cache-busting:** los `.html` referencian JS/CSS con `?v=N`. **Al cambiar un .js/.css hay que subir el número en TODOS los .html que lo usan**, o el navegador sirve la copia vieja. Versiones actuales (2026-06-14): `style.css?v=10`, `auth.js?v=11`, `util.js?v=2` (T-017), `library.js?v=13`, `app.js?v=14`, `score_render.js?v=10`, `chord_shapes.js?v=9`, `editor.js?v=11`, `sync_engine.js?v=8`. **`util.js` debe cargarse ANTES** que library/score_render/chord_shapes (define la global `escapeHtml`). (Pendiente T-022: automatizar con hash.)
- **Secretos:** `.env` y `.env.local` están en `.gitignore`. La `service_role` key **nunca** debe ir al frontend ni a git.
- **Arquitectura de render:** `score_render.js` es la única fuente de verdad del render de partituras (reproductor + vista previa del editor).
- **Sincronización:** el motor (`sync_engine.js`) trabaja por **ids** de acorde, por eso transposición y diagramas no la afectan.
