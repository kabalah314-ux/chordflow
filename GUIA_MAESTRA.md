# 🎸 ChordFlow — Guía Maestra (Documento de Contexto)

> ⚠️ **HISTORIAL CERRADO — no es la guía vigente.** La dirección de producto actual está en
> [GUIA_MAESTRA_V3.md](GUIA_MAESTRA_V3.md) (léela primero). Este documento describe el producto
> original (teleprompter mono-usuario), previo al giro V2/V3; la "joya" que describe sigue intacta
> dentro del flujo actual, pero para saber "qué toca ahora" no hace falta abrir este archivo.
>
> Fuente de verdad para entender el proyecto de un vistazo. Actualizar cuando cambie la arquitectura.
> Última actualización: 2026-06-13 (auditoría completa de código — ver §12 Deuda técnica).
> Reglas operativas y bucle de trabajo: ver [CLAUDE.md](CLAUDE.md). Plan priorizado: [harness/ROADMAP.md](harness/ROADMAP.md).

---

## 1. ¿Qué es ChordFlow?

Aplicación web para **leer y reproducir partituras de acordes** (letra + acordes tipo Ultimate Guitar / LaCuerda.net) con un **reproductor sincronizado**: a medida que avanza el "beat" según el BPM, se resalta el acorde activo y la pantalla hace auto-scroll, como un teleprompter musical.

Tiene dos pantallas:
- **Reproductor** (`index.html`): muestra la canción y la reproduce resaltando acordes en tiempo real.
- **Editor** (`editor.html`): pegas texto plano de una web de partituras y el sistema lo parsea automáticamente a la estructura de datos.

Estado: **MVP / Fase 1**. Funcional pero con simplificaciones marcadas como `TODO` y "Fase futura".

---

## 2. Stack Tecnológico

| Capa | Tecnología |
|------|-----------|
| Backend | **Python + FastAPI** (REST) |
| ORM | **SQLAlchemy** |
| Validación | **Pydantic** |
| Servidor ASGI | **Uvicorn** |
| Base de datos | **SQLite** local (`chordflow.db`) — diseñado para migrar a PostgreSQL/Supabase |
| Frontend | **HTML + CSS + JavaScript vanilla** (ES6, sin framework) |
| Config | `python-dotenv` (`.env`, `.env.local`) |

Dependencias: ver `requirements.txt` (fastapi, uvicorn, sqlalchemy, pydantic, python-dotenv).

---

## 3. Estructura de Carpetas

```
app partituras/
├── GUIA_MAESTRA.md          ← este documento
├── .env                     ← config backend (DATABASE_URL, LOG_LEVEL)
├── .env.local               ← secretos Supabase (NO se commitea)
├── .gitignore
├── requirements.txt
├── chordflow.db             ← base de datos SQLite (ignorada por git)
├── test_api.py              ← script de prueba manual de la API (usa requests)
├── logs/                    ← logs de la app (app.log, ignorado por git)
├── directives/              ← SOPs (procedimientos / reglas del proyecto)
│   ├── chordflow_backend_SOP.md
│   ├── chordflow_frontend_SOP.md
│   └── configuracion_supabase_SOP.md
├── src/                     ← BACKEND
│   ├── main.py              ← app FastAPI, CORS, monta /static, incluye routers
│   ├── api/
│   │   └── songs_router.py  ← endpoints CRUD /songs
│   └── services/
│       ├── db.py            ← engine, SessionLocal, Base, get_db()
│       ├── models.py        ← modelos SQLAlchemy (tablas)
│       ├── schemas.py       ← schemas Pydantic (validación I/O)
│       └── auth.py          ← Supabase token → user_id + MODO TEST (bypass por env var)
├── harness/                 ← SISTEMA DE TRABAJO (doctor, run_checks, ROADMAP, TASKS, MOLDE)
├── tests/                   ← unit (API/lógica) + e2e (Playwright) + conftest (modo test, BD temporal)
└── static/                  ← FRONTEND (servido en /static)
    ├── library.html         ← biblioteca (pantalla de inicio, lista de canciones)
    ├── index.html           ← reproductor
    ├── editor.html          ← editor/importador (crear y editar) con vista previa
    ├── style.css            ← estilos (dark + glassmorphism, teal #00f2ff)
    ├── library.js           ← grid de canciones, búsqueda, borrar
    ├── app.js               ← orquestación reproductor (fetch → render → sync), scroll continuo, auto-save tempo
    ├── sync_engine.js       ← clase SyncEngine (motor de reproducción, sin DOM)
    ├── score_render.js      ← render compartido (player + preview) + transposición (transposeChord)
    ├── chord_shapes.js      ← diagramas de acordes (formas abiertas + cejillas móviles + SVG)
    └── editor.js            ← parser "acordes sobre letra" + serializador inverso + vista previa + POST/PUT

IMPORTANTE (cache): los .html referencian JS/CSS con `?v=N`. Al cambiar un .js/.css,
sube el número de versión en TODOS los .html que lo usan, o el navegador sirve la copia vieja.
```

---

## 4. Modelo de Datos (jerarquía anidada)

Estructura relacional en cascada (`models.py`). Borrado en cascada padre→hijo.

```
Song (canción)
 └── Section (Intro, Verso, Coro…)      order, repeat_count, color_tag
      └── Line (línea)                   type: lyric|tab|chord_only|comment|spacer
           ├── ChordMarker (acorde)      chord_name, char_position, beat_offset, duration_beats
           └── TabLine (tablatura)       string_number, fret_sequence (JSON)
```

**Claves del modelo:**
- IDs son **UUID** en `String(36)` (generados con `uuid.uuid4()`).
- Campos complejos (`display_hint`, `finger_diagram`, `barre`, `muted_strings`, `fret_sequence`, `tags`) se guardan como **columnas JSON**.
- `Song` tiene campos para **soft delete** (`deleted_at`) y futuro multiusuario (`owner_id`, `is_public`) — aún no implementados del todo.
- Metadatos musicales en Song: `bpm`, `time_signature_num/den`, `key_root/mode`, `tuning`, `capo`, `instrument`.

**Campos clave para la sincronización:**
- `Line.beat_start` → en qué beat absoluto empieza la línea.
- `ChordMarker.beat_offset` → desfase del acorde dentro de la línea.
- `ChordMarker.char_position` → columna de carácter donde se pinta el acorde sobre la letra.
- Beat absoluto de un acorde = `line.beat_start + chord.beat_offset`.

---

## 5. API REST (Backend)

Definida en `src/api/songs_router.py`, prefijo `/songs`. Toda respuesta usa schemas Pydantic anidados.

| Método | Ruta | Descripción |
|--------|------|-------------|
| `GET` | `/songs/` | Lista paginada (skip/limit). Filtra `deleted_at == None`. |
| `GET` | `/songs/{id}` | Detalle completo anidado (secciones→líneas→acordes). |
| `POST` | `/songs/` | Crea canción completa desde payload anidado. Devuelve 201. |
| `PUT` | `/songs/{id}` | Actualiza: **borra todas las secciones y las recrea** (nuevos ids). Para editar canción o guardar transposición. |
| `PATCH` | `/songs/{id}` | Actualización **parcial de metadatos** (bpm, key, capo…) **sin tocar la estructura**. Usado por el auto-guardado de tempo. Schema `SongUpdate`. |
| `DELETE` | `/songs/{id}` | **Hard delete** (a pesar de que la DB soporta soft delete). |
| `GET` | `/` | Mensaje de bienvenida (en `main.py`). |

**Convenciones del backend (ver `chordflow_backend_SOP.md`):**
- Errores → códigos HTTP estándar (400, 404, 500) con `HTTPException`.
- Logging obligatorio con la librería `logging` → `logs/app.log`. Nunca solo `print()`.
- Modularidad: `src/api` = endpoints, `src/services` = lógica + DB.
- Secretos en `.env` / `.env.local`.
- Auth: toda ruta de `/songs` exige `Depends(get_current_user)` y filtra por `owner_id`.
- ⚠️ CORS abierto (`allow_origins=["*"]`) — **deuda técnica**, ver §12 / T-004.

---

## 6. Frontend — Reproductor

### `sync_engine.js` — `class SyncEngine` (motor puro, SIN DOM)
- Patrón **Observer**: `subscribe(callback)` → recibe el `state` en cada cambio.
- `loadSong(song)`: aplana todos los acordes en `flatChords` con su `absoluteBeatStart` y `duration`, ordenados cronológicamente.
- Controles: `play()`, `pause()`, `stop()`, `setBpm(n)` (clamp 40–240).
- Bucle con `requestAnimationFrame` (`tick`): calcula `currentBeat` a partir del tiempo real transcurrido y el BPM, y determina el acorde activo (`findActiveChord`, búsqueda lineal — nota: para muchos acordes haría falta binaria).
- Un acorde está activo desde su inicio hasta el inicio del siguiente.

### `app.js` — orquestación (Fetch → Render → Sync)
- Lee `?songId=` de la URL; si no, carga la primera canción de `/songs/`.
- `renderScore(song)`: construye el DOM. Lógica especial de **fusión**: una línea `chord_only` seguida de una `lyric` se fusionan para pintar los acordes flotando encima de la letra. `chord_only` puro (Intro) se pinta como fila de "pills".
- Se suscribe al engine: actualiza BPM/beat, marca `.active` el acorde sonando y hace **auto-scroll suave** para mantener el acorde activo cerca del ancla (35% desde arriba).

### `index.html` / `style.css`
- UI dark nativa (`#0a0a0a`) + **glassmorphism** (`backdrop-filter: blur`) + acento **teal `#00f2ff`**.
- Tipografía: Inter (UI) + Roboto Mono (acordes/partitura). **La fuente monoespaciada es crítica** para alinear acordes sobre letra.
- Acorde activo: escala suave + glow.

---

## 7. Frontend — Editor / Importador (`editor.js`)

El editor permite **pegar texto plano** de Ultimate Guitar / LaCuerda y lo convierte a la estructura anidada. Paradigma: **"Acordes sobre Letra"** (la línea de acordes va encima de la línea de letra, alineada por columnas).

**Reglas del parser (`parseRawText`):**
1. **Línea vacía** → se salta.
2. **Sección**: termina en `:` y tiene ≤4 palabras (ej. `Verso 1:`, `Coro:`).
3. **Intro**: formato `: F#m : C#7 : D :` → `chord_only`.
4. **Línea de acordes**: ≥60% de sus palabras matchean el regex de acordes. Si la línea siguiente es letra → se emparejan (acorde queda ligado al `char_position` de columna). Si no → acorde huérfano (`chord_only`).
5. **Línea de letra pura** → `lyric` sin acordes.

**Regex de acordes:**
```js
/^[A-G]([#b])?(m|maj|min|aug|dim|sus|add)?(\d)?(\/[A-G]([#b])?)?$/
```
Reconoce: `Am`, `F#m7`, `C#7`, `G/B`, `Bb`, `Dmaj7`, `A7sus4`, etc.

Al guardar: `POST /songs/` y redirige a `index.html?songId={id}`.

**Trampa conocida:** el formato antiguo `[Acorde]Letra` (inline) fue **abandonado**; solo se soporta "acordes sobre letra". Por eso el `textarea` **debe** usar fuente monoespaciada.

---

## 8. Configuración y Secretos

- **`.env`** (backend, sí versionable salvo regla): `DATABASE_URL=sqlite:///./chordflow.db`, `LOG_LEVEL=INFO`.
- **`.env.local`** (NO se commitea, está en `.gitignore`): credenciales Supabase (`SUPABASE_URL`, `SUPABASE_ANON_KEY`, `SUPABASE_SERVICE_ROLE_KEY`).
- ⚠️ La `service_role` key salta RLS: **nunca** exponer al frontend ni a repos públicos (ver `configuracion_supabase_SOP.md`).
- Supabase **ya está integrado para autenticación**: `auth.py` valida el Bearer token contra
  `/auth/v1/user` y devuelve el `user_id`; el frontend (`auth.js`) usa el SDK por CDN. Los **datos**
  siguen en **SQLite local** (`chordflow.db`); migrar el almacenamiento a Postgres/Supabase sigue
  pendiente. ⚠️ La validación de token llama a Supabase en **cada request** (bloqueante) — deuda
  técnica, ver §12 / T-005.

> ⚠️ Nota: las claves de Supabase están actualmente en `.env.local` en texto plano dentro del repo local. Como `.env.local` está en `.gitignore`, no debería subirse, pero conviene confirmar que nunca se haya commiteado.

---

## 9. Cómo Ejecutar

```powershell
# 1. Instalar dependencias
pip install -r requirements.txt

# 2. Arrancar el servidor (desde la raíz del proyecto)
uvicorn src.main:app --reload

# 3. Abrir el reproductor
#    http://127.0.0.1:8000/static/index.html
#    Editor: http://127.0.0.1:8000/static/editor.html

# 4. (Opcional) Probar la API
python test_api.py
```

La DB SQLite y las tablas se crean solas al arrancar (`Base.metadata.create_all` en `main.py`).

---

## 10. Estado Actual y Roadmap (TODOs detectados en el código)

**Hecho (Fase 1 / MVP):**
- CRUD completo de canciones con estructura anidada.
- Reproductor con sincronización por beat + auto-scroll.
- Editor con parser automático "acordes sobre letra".
- **Biblioteca** (`library.html`): lista de canciones con búsqueda en vivo, estado vacío y acciones.
- **Editar** canción existente: el editor reconstruye el texto raw desde la estructura (`songToRawText`) y guarda con `PUT` (mismo id).
- **Borrar** canción desde la biblioteca (con confirmación).
- **Transposición de acordes** (±semitono) en el reproductor: visual en vivo (`transposeChord`) y opción de guardar el tono con `PUT`. La sincronización no se ve afectada porque el motor usa ids, no nombres.
- Motor de sync robusto: `loadSong` reparte beats cuando faltan y distribuye acordes que comparten beat (Intro), así toda canción es reproducible.
- **Importador robusto + vista previa en vivo**: el parser entiende secciones de Ultimate Guitar (`[Verso 1]`), LaCuerda y manual (`Verso 1:`). El editor muestra una vista previa en tiempo real (mismo render que el reproductor, vía `score_render.js`).
- **Scroll continuo tipo teleprompter**: la partitura desciende suave y proporcional al progreso (`currentBeat / totalBeats`), sin saltos. (Nota: mapeo lineal beat→píxel; el contenedor NO debe tener `scroll-behavior: smooth`.)
- **Auto-guardado del tempo**: al cambiar el BPM en el reproductor se persiste solo (debounce + `PATCH`). Al recargar, la canción abre con su último tempo.
- **Metrónomo**: botón 🥁 en el reproductor (Web Audio API). Clic por beat con acento en el primer tiempo del compás (`time_signature_num`).
- **Diagramas de acordes**: al pulsar cualquier acorde se abre un popup con su digitación (SVG). Cobertura total vía `chord_shapes.js` (acordes abiertos + cejillas móviles E/A-shape para mayor, menor, 7, m7, maj7 en las 12 tonalidades; respeta la transposición). Acordes raros (sus/dim/aug) muestran "sin diagrama".

**Pendiente / simplificaciones:**
- Autenticación multiusuario **ya activa**: `/songs` filtra por `owner_id` (modo test lo bypassa).
  Falta decidir el comportamiento de `is_public` (hoy `get_song` filtra siempre por dueño).
- `PUT`: recrea toda la estructura (nuevos ids en cada guardado) en vez de hacer diff.
  ⚠️ Además, hoy **deja filas huérfanas** en cada edición (bug T-003, ver §12).
- `DELETE`: hard delete aunque hay `deleted_at` para soft delete.
- `findActiveChord`: búsqueda lineal; convendría binaria con muchos acordes.
- Integración real con Supabase/PostgreSQL (hoy solo SQLite).
- Tablaturas (`TabLine`) modeladas pero sin UI de render/edición visible.
- Metrónomo/claqueta audible (idea pendiente, encaja con el concepto).

---

## 11. Mapa Rápido "Quiero tocar X → mira aquí"

| Necesito… | Archivo |
|-----------|---------|
| Cambiar/añadir endpoints | `src/api/songs_router.py` |
| Cambiar tablas / columnas | `src/services/models.py` |
| Cambiar validación / forma del JSON | `src/services/schemas.py` |
| Config de DB / sesiones | `src/services/db.py` |
| Arranque, CORS, montaje static | `src/main.py` |
| Lógica de reproducción/sincronización | `static/sync_engine.js` |
| Render del reproductor / auto-scroll | `static/app.js` |
| Parser de importación de partituras | `static/editor.js` |
| Estilos / colores / glassmorphism | `static/style.css` |
| Reglas backend | `directives/chordflow_backend_SOP.md` |
| Reglas frontend / parser | `directives/chordflow_frontend_SOP.md` |
| Procedimiento Supabase | `directives/configuracion_supabase_SOP.md` |
| Plan priorizado / tareas | `harness/ROADMAP.md` · `harness/TASKS.md` |
| Diseño del molde reutilizable | `harness/MOLDE.md` |
```

---

## 12. Deuda técnica y estado de calidad (auditoría 2026-06-13)

**Estado:** tras el estudio inicial + una **auditoría multi-agente** (workflow de 8 finders), se han
cerrado **todos los críticos y la mayoría de los altos**. Plan e historial con IDs T-NNN en
**[`harness/ROADMAP.md`](harness/ROADMAP.md)**; bitácora en `REGISTRO_DE_CAMBIOS.md`.

**✅ Ya resueltos:** T-001 git · T-002 XSS en el render · T-003 fuga de huérfanos (PUT) · T-004 CORS ·
T-005 caché de token · T-006 `apiFetch` 401 · T-007 Pydantic v2 · T-008 deps pineadas · T-009 datetime ·
T-012 índices · T-015 limpieza · T-024 validación de rangos · **T-026 XSS en popup de diagramas** ·
**T-027 404→400 + 500 genérico** · **T-028 caché de token (cota + lock de concurrencia)** ·
T-029 cabeceras de seguridad · T-037 paginación acotada.

**⏳ Pendiente (ver ROADMAP):** T-010 N+1 en `GET /songs/` · T-011 Alembic · T-013 soft delete real ·
T-014 logging unificado · T-016 pydantic-settings · T-030 SRI · T-031 caché y tokens revocados ·
T-033 `ON DELETE CASCADE` · T-039 consolidar `escapeHtml` · **T-042 flakiness del e2e** · UX (T-017–022) ·
T-023 CI · y la **Fase M (molde)** con T-043/T-044 (desacoplar auth + backend base).

> Lo que está **bien** y conviene preservar (y moldear): separación `api`/`services`, motor de sync
> sin DOM, render compartido player↔editor, modo test con BD temporal, y el harness completo.
