# 📋 ChordFlow — Registro de Cambios (Bitácora de desarrollo)

> Documento vivo. Registra **qué** se hizo, **por qué** y **cómo** (archivos tocados y verificación).
> Para el contexto general del proyecto, ver [GUIA_MAESTRA.md](GUIA_MAESTRA.md).
> Última actualización: 2026-06-06

Leyenda de estado: ✅ hecho y verificado · 🟡 en curso · ⏳ pendiente

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

---

<a name="notas"></a>
## 11. Notas técnicas recurrentes

- **Cache-busting:** los `.html` referencian JS/CSS con `?v=N`. **Al cambiar un .js/.css hay que subir el número en TODOS los .html que lo usan**, o el navegador sirve la copia vieja. Versiones actuales (2026-06-13): `auth.js?v=11`, `library.js?v=10`, `app.js?v=10`, `score_render.js?v=8`, `chord_shapes.js?v=9`; el resto en `v=9`. (Pendiente T-022: automatizar con hash.)
- **Secretos:** `.env` y `.env.local` están en `.gitignore`. La `service_role` key **nunca** debe ir al frontend ni a git.
- **Arquitectura de render:** `score_render.js` es la única fuente de verdad del render de partituras (reproductor + vista previa del editor).
- **Sincronización:** el motor (`sync_engine.js`) trabaja por **ids** de acorde, por eso transposición y diagramas no la afectan.
