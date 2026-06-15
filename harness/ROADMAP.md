# 🗺️ ChordFlow — ROADMAP de Calidad

> Hoja de ruta priorizada. Se trabaja de arriba abajo. Marcar `[x]` al cerrar.
> Cada tarea cerrada debe tener: doctor verde + test que la cubre + entrada en REGISTRO_DE_CAMBIOS.
> Leyenda: 🔴 crítico · 🟠 alto · 🟡 medio · 🟢 feature
> Las tareas tienen **ID** (T-NNN) para abrirlas en `TASKS.md` y referenciarlas en el registro.
> Última revisión del plan: 2026-06-13 (tras estudio completo del código).

---

## Fase 0 — Red de seguridad
- [x] **T-001** 🔴 **Inicializar git** y primer commit. Verificado: `.env.local` y `*.db` no
      trackeados. + `.gitattributes` (EOL) y `*.log` en `.gitignore`.
- [x] 🔴 Montar el harness (doctor, tests, roadmap). *(T-000, hecho)*
- [x] 🟠 Modo test (bypass de auth por env var) para verificar con Playwright. *(hecho)*

## Fase 1 — Seguridad (🔴 antes de moldear nada)
- [x] **T-002** 🔴 **XSS en el renderer** (`score_render.js`). Resuelto con `escapeHtml()` +
      `renderLyricWithChords()` (escapa letra por segmentos preservando alineación) y `chordSpan`
      escapando `chord_name` en texto y `data-orig`. Test J3 + `?v=8`. run_checks verde.
- [x] **T-003** 🔴 **Fuga de filas huérfanas en `PUT`**. Resuelto: borrado vía ORM (cascade
      `delete-orphan`) + `PRAGMA foreign_keys=ON` por conexión. Test `test_put_no_deja_filas_huerfanas`.
- [x] **T-004** 🔴 **CORS explícito**. `CHORDFLOW_ALLOWED_ORIGINS` (default localhost).
      Test `test_cors_restringe_origenes`.
- [x] **T-005** 🔴 **Validación de token cacheada**. Caché TTL en memoria + degradación elegante
      si Supabase cae. Tests `test_validacion_de_token_se_cachea` y `..._sobrevive_caida_de_supabase`.
- [x] **T-006** 🟠 **`apiFetch` maneja 401** (`auth.js`): si el backend responde 401, redirige a
      `login.html`. Test E2E `test_apifetch_redirige_a_login_en_401`. Cache-bust `auth.js?v=11`.

## Fase 2 — Base mantenible
- [x] **T-007** 🟠 **Pydantic v2**: `orm_mode`→`ConfigDict(from_attributes=True)` (5×) y
      `.dict()`→`.model_dump()` (11×). DeprecationWarnings de Pydantic eliminados.
- [x] **T-008** 🟠 **Dependencias pineadas** en `requirements.txt` (versiones probadas en Py3.12).
- [x] **T-009** 🟠 **`datetime.utcnow()`→`_utcnow()` (tz-aware)** en `models.py`.
- [x] **T-010** 🟠 **N+1 en `GET /songs/`** resuelto: `SongSummary` ligero (metadatos + `section_count`,
      sin `sections`) → pydantic no toca la relación; `section_count` vía UNA query agregada
      (`func.count`+`group_by`) → O(1) queries. Frontend usa `section_count` (`library.js?v=10`).
      Test `test_listado_es_ligero_sin_estructura`.
- [x] **T-011** 🟠 **Alembic** para migraciones: `alembic/` + `env.py` (URL de `DATABASE_URL`,
      `target_metadata=Base.metadata`, `render_as_batch=True` para SQLite) + baseline `fefcd5a0b14a`
      (5 tablas + índices T-012). `create_all` sigue para bootstrap; Alembic para evolucionar la BD
      real (adoptar con `alembic stamp head`). Tests `tests/unit/test_migrations.py`. **Desbloquea
      T-033/34/35/36.**
- [x] **T-012** 🟠 **Índices** en `Song.owner_id`, `Song.deleted_at` y las 4 FKs (`index=True`).
      (Aplica a BD nuevas; la existente requerirá la migración de T-011.)
- [x] **T-013** 🟡 **Soft delete real** en `DELETE`: marca `deleted_at` en vez de `db.delete`
      (las lecturas ya filtraban `deleted_at IS NULL`); 2º DELETE → 404. `is_public`: se mantiene
      filtrado solo-por-dueño; exponer públicas se difiere a Fase 5 (feature, no bug).
      Test `test_delete_es_soft`.
- [x] **T-014** 🟡 **Logging unificado**: `basicConfig` fuera de `db.py` (librería) y de `main.py`.
      Nuevo `services/logging_config.py::setup_logging()` (idempotente) llamado UNA vez en `main.py`;
      destino seleccionable (fichero o stdout con `CHORDFLOW_LOG_STDOUT=1`, cloud-friendly).
      Test `tests/unit/test_logging_config.py`.
- [x] **T-015** 🟡 **`test_api.py` legacy eliminado** (script manual con `requests`, redundante
      con el harness).
- [x] **T-016** 🟡 **`pydantic-settings`**: `src/services/config.py::Settings` (singleton `settings`)
      con tipos/defaults/validación fail-fast. Migrados `db.py`/`auth.py`/`main.py`/`logging_config.py`.
      `alembic/env.py` sigue leyendo `DATABASE_URL` fresco (no el singleton). Test `test_config.py`.
      Dep `pydantic-settings==2.14.1`.

## Fase 3 — Calidad percibida
- [x] **T-017** 🟡 `alert()`/`confirm()` → `toast()`/`confirmModal()` en `util.js` (glassmorphism,
      escapan texto, Promise para el modal). 5 usos migrados. Test `test_borrar_usa_modal_y_elimina`.
- [x] **T-018** 🟡 **Transposición con bemoles**: doble escala (SCALE_SHARP/FLAT); preserva el estilo
      de la raíz original (bemol→bemoles). `Bb`+3→`Db` (antes `C#`). Test `test_transpose_respeta_bemoles`.
      `score_render.js?v=10`.
- [x] **T-019** 🟡 **Auto-scroll anclado al acorde activo**: sigue el elemento DOM del acorde activo
      (1/3 de la altura, teleprompter) en vez del mapeo lineal beat→píxel. Test
      `test_autoscroll_mantiene_visible_el_acorde_activo`. `app.js?v=14`.
- [x] **T-020** 🟡 **Parser**: `CHORD_REGEX` reescrito (sufijo como secuencia repetible de
      cualidad/nº+alteración + bajo) → ahora capta `add11`, `maj13`, `sus2`, `Em7b5`, `A7sus4`.
      Test e2e `test_ischord_reconoce_acordes_extendidos`. `editor.js?v=10`.
- [x] **T-021** 🟡 Accesibilidad: `aria-label` en botones de emoji (reproductor + tarjetas) y atajo
      **Espacio = play/pausa** (ignora inputs). Test `test_accesibilidad_aria_y_atajo_espacio`.
      `app.js?v=12`, `library.js?v=12`.
- [x] **T-022** 🟡 Cache-busting automático: `harness/cachebust.py` reescribe `?v=<sha256[:8]>` por
      contenido; `test_cache_busting_al_dia` falla si está desfasado. Fin del `?v=N` manual.

## Fase 4 — CI / profesionalización
- [x] **T-023** 🟠 **GitHub Actions** (`.github/workflows/ci.yml`): Python 3.12 → deps + playwright
      chromium → `run_checks.py` en cada push/PR. CI crea `.env` dummy (secretos gitignoreados; modo
      test no usa Supabase). Verificado en local con entorno CI simulado; se activa al publicar en GitHub.
- [x] **T-024** 🟡 **Validación de rangos en schemas** con `Field(...)`: `bpm` 20–400, `year` 0–3000,
      compás 1–32, `capo` 0–24, `title` 1–255. Test `test_validacion_de_rangos` (422).
- [x] **T-025** 🟡 **Endpoint `/health`** (liveness) → `{"status":"ok"}`, sin deps ni auth,
      separado de `/config`. Test `test_health_es_liveness`. (Pilar de T-044.)

## Fase A — Hallazgos de la auditoría multi-agente (2026-06-13)

> Producidos por el workflow `auditoria-profunda-chordflow` (8 finders + verificación).
> La verificación/síntesis se cortó por límite de sesión, así que estos hallazgos vienen de
> los finders y se confirmarán/afinarán al abordarlos. Los 3 primeros ya están **verificados a
> mano y arreglados**.

**🔴 Arreglados ya:**
- [x] **T-026** 🔴 **XSS de 2º orden en el popup de diagramas** (`chord_shapes.js` inyectaba `name`
      sin escapar; `name` = `textContent` decodificado). Escapado. Test `test_popup_diagrama_escapa_nombre_malicioso`.
- [x] **T-027** 🔴 **404→400 en `PUT`/`POST`**: el `except Exception` ancho tragaba el `HTTPException`.
      Añadido `except HTTPException: raise`. **Hardening** (de la verificación): el `except Exception`
      ahora responde **500 genérico** (antes 400 con `str(e)` → filtraba internals). Test `test_put_inexistente_devuelve_404`.
- [x] **T-028** 🟠 **`_token_cache` sin cota + concurrencia** (memory leak de T-005). Cota dura
      `TOKEN_CACHE_MAX` **y `threading.Lock`** en `_cache_set` (la verificación adversaria encontró
      que sin lock, iterar el dict mientras otro hilo del threadpool inserta lanzaba
      `RuntimeError: dictionary changed size` → HTTP 500). Tests `test_token_cache_tiene_cota_de_tamano`
      y `test_cache_set_seguro_bajo_concurrencia`.

**🟠 Seguridad / robustez (pendientes):**
- [x] **T-029** 🟠 Cabeceras de seguridad vía middleware (X-Content-Type-Options, X-Frame-Options,
      Referrer-Policy, Permissions-Policy). CSP queda pendiente (sub-tarea: requiere afinar inline).
      Test `test_cabeceras_de_seguridad`.
- [x] **T-030** 🟡 **SRI** en el CDN de Supabase: versión fijada `@2.108.1/dist/umd/supabase.js` +
      `integrity` (sha384) + `crossorigin` en las 4 HTML. Verificado por el doctor (modo normal
      ejecuta `createClient`). ⚠️ subir versión = recalcular hash.
- [x] **T-031** 🟡 Ventana de gracia del caché de token **acotada** a `expiry + CHORDFLOW_TOKEN_GRACE`
      (default 300s); pasada la ventana → 401 + purga. Exposición de token revocado: TTL+gracia, no
      ilimitada. Tests `..._sobrevive_caida_de_supabase` (actualizado) + `..._fuera_de_la_ventana_de_gracia`.
- [x] **T-032** 🟡 Auditado: la `service_role` key no se usa en código (Settings `extra=ignore` la
      descarta), no hay `.env` trackeado, el historial no la filtra, y `/config` solo da las 3 claves
      públicas. Guards `test_config_no_expone_service_role` + `test_settings_ignora_la_service_role_key`.

**🟠 Integridad de datos (pendientes, encajan con Alembic T-011):**
- [x] **T-033** 🟠 FKs con `ondelete="CASCADE"` a nivel DB (las 4) + migración `dac91229a048`
      (batch mode con naming_convention para soltar FKs sin nombre). Defensa en profundidad sobre
      el cascade ORM (T-003). Test `test_cascade_a_nivel_db` (borrado con SQL directo).
- [x] **T-034** 🟡 `owner_id` → `NOT NULL` (la auth es obligatoria). Migración `147a6a78da86`.
      Test `test_owner_id_not_null_en_bd`.
- [x] **T-035** 🟡 `Line.type` restringido: `Literal` en schema (422) + CHECK `ck_lines_type` en BD
      (fuente única `models.LINE_TYPES`). Tests `test_line_type_invalido_da_422` / `test_check_line_type_en_bd`.
- [x] **T-036** 🟡 `server_default` en BD para los defaults escalares (songs + sections), no solo en
      Python (timestamps siguen Python-side). Test `test_server_default_en_bd`.

**🟠 API / backend (pendientes):**
- [x] **T-037** 🟠 Paginación acotada: `skip` `Query(ge=0)`, `limit` `Query(ge=1, le=500)` → 422
      fuera de rango. Test `test_paginacion_acotada`.
- [x] **T-038** 🟡 `create_song`/`update_song` extraen el armado de estructura a `_append_sections`
      (fin de ~16 líneas duplicadas). Refactor puro; cubierto por los tests CRUD/PUT existentes.

**🟡 Frontend (pendientes):**
- [x] **T-039** 🟡 `escapeHtml` consolidado en `static/util.js` (global canónica, segura en atributos
      + null-safe). Eliminadas las 2 copias divergentes; `util.js?v=1` cargado antes de sus dependientes
      en las 3 HTML (`library.js v11`, `score_render.js v9`). Cubierto por los e2e de XSS existentes.
- [x] **T-040** 🟡 Sync: `findActiveChord` reescrito (el último acorde cuyo inicio ya pasó) → arregla
      persistencia del último acorde, empates de inicio y reset. Tests `test_sync_engine.py`.
      `sync_engine.js?v=8`. (isChordLine/desalineación revisados: OK con la cobertura de T-020.)
- [x] **T-041** 🟡 Fallos de carga del reproductor: `app.js` avisa en el área principal,
      distingue 404 vs conexión, con salida a la biblioteca (antes: mensaje técnico solo en el título).
      Test `test_songid_inexistente_avisa_al_usuario`. `app.js?v=11`.

**🟡 Tests (pendientes):**
- [~] **T-042** 🟡 **Flakiness e2e resuelta** (3 carreras): timeout httpx de la fixture `api` 5→30 s;
      deadline de arranque del `live_server` 25→45 s; y `test_apifetch_redirige_a_login_en_401`
      reescrito determinista (caché de `/config` + rebote de `login.js`, vía `framenavigated`).
      Pasó 5/5 en repetición. **Pendiente** del alcance original (no bloqueante): cobertura de
      `sync_engine.js`/`chord_shapes.js`, caminos negativos de API y medición de cobertura.

**🧬 Molde (van a `MOLDE.md` / Fase M):**
- [x] **T-043** 🟠 `auth.py` desacoplado: `auth_provider.py` (`AuthProvider` Protocol +
      `SupabaseAuthProvider` + factoría por `CHORDFLOW_AUTH_PROVIDER`). El núcleo (caché/TTL/lock/
      degradación) es agnóstico. Tests `test_auth_provider.py`. **Parametrizar el prefijo `CHORDFLOW_*`
      → diferido a T-M03** (hueco de templating del molde, no runtime de ChordFlow).
- [x] **T-044** 🟠 Backend base del molde — **4 pilares técnicos completos**: `/health` (T-025),
      handler de errores global (`@app.exception_handler(Exception)` → 500 genérico, sin filtrar
      internals; test `test_handler_global_500_no_filtra_internals`), logging único (T-014),
      `Settings` pydantic-settings (T-016). README/plantillas del molde → se materializan en T-M02.

## Fase 5 — Diferenciación de producto
- [x] 🟢 **Responsive móvil/tablet** — media queries (820/480px); barras envuelven, editor/formularios
      apilados, partitura con scroll-x, targets táctiles. Test `test_responsive_pwa` (sin overflow).
- [x] 🟢 **PWA instalable** — manifest + iconos 192/512 + service worker (API no cacheada, HTML
      network-first, estáticos cache-first por hash). Registrado en `auth.js`.
- [x] 🟢 **Export PDF** — botón en el reproductor → `window.print()` + `@media print` (solo la
      partitura, B/N). Test `test_export_pdf_oculta_controles`.
- [x] 🟢 **Migrar SQLite → Postgres/Supabase** — hecho en Fase 6 (Paso 2).
- [ ] 🟢 **Setlists/repertorios** — pendiente (feature grande: entidad + CRUD + UI + reproducir en orden).
- [ ] 🟢 **UI de tablaturas** (`TabLine` ya modelado) — pendiente (editor + render de tabs).
- [x] **T-045** 🟢 **Importar desde URL con IA** — **EN VIVO y verificado**. `POST /import/` (auth):
      lee la página (lector **Jina**, con fallback a **descarga directa + limpieza HTML** cuando Jina
      se rate-limitea desde datacenter) y una **IA gratuita por OpenRouter** (`openai/gpt-oss-120b:free`,
      configurable) extrae la partitura en el formato del editor → precarga el textarea. `importer.py`
      + `import_router.py` + botón en el editor. Tests `test_import.py` + e2e. Verificado en producción
      con CifraClub y e-chords (UG bloquea por Cloudflare incluso vía Jina). Coste 0.
- [ ] **T-046** 🟢 **Login con Google**: configurar OAuth (credenciales en Google Cloud + activar el
      provider Google en Supabase con el redirect URI del proyecto). El botón ya existe en el front.
- [ ] **T-047** 🟢 **Personalizar emails de auth** (Supabase → Email Templates: marca ChordFlow) y
      afinar los mensajes propios del front (`login.js`).

## Fase 6 — Despliegue (Supabase + Vercel)
- [x] **Paso 1** — Proyecto Supabase nuevo (`fwynfifvtthtpzpejfhb`) + login real verificado
      (registro/login navegador + `/songs/` 200 autenticado). Claves nuevas `sb_publishable_`/`sb_secret_`.
- [x] **Paso 2** — BD en **Postgres de Supabase** verificada: driver `psycopg2`, `render_as_batch`
      solo SQLite, `pool_pre_ping`. Esquema creado (`create_all` + `alembic stamp head`) en
      eu-central-1; CRUD de la app verde contra Postgres. Bugs de portabilidad corregidos
      (bool `false`, `%` en env.py, TEST_USER_ID 36 chars). Pooler sesión 5432 (migraciones) /
      transacción 6543 (runtime serverless). Falta: poner `DATABASE_URL` en Vercel (Paso 3).
- [x] **Paso 3** — **Desplegado en Vercel** ✅ https://chordflow-ecru.vercel.app (repo
      github.com/kabalah314-ux/chordflow, privado). `api/index.py` (ASGI) + `vercel.json`
      (@vercel/python, includeFiles static/**) + `.vercelignore` (excluye pyproject.toml→usa
      requirements.txt). Env vars de producción (DATABASE_URL pooler 6543, SUPABASE_URL/ANON_KEY,
      CHORDFLOW_LOG_STDOUT=1). Verificado en vivo: /health, /config, estáticos, 401 sin token, y
      **login real + crear/leer canción (Vercel→Postgres) 201**. Pendiente opcional: dominio propio
      + `CHORDFLOW_ALLOWED_ORIGINS` al dominio.

---

## Fase M — El MOLDE (esqueleto reutilizable para otras apps)

> Objetivo: extraer de ChordFlow lo agnóstico al dominio y dejar un molde estable.
> Detalle del diseño en [`harness/MOLDE.md`](MOLDE.md). **Pre-requisito: T-001 a T-005 hechos**
> (no se moldean bugs). Ver `MOLDE.md` para qué es universal y qué es por-proyecto.

- [x] **T-M01** 🟠 Inventario universal vs por-proyecto **validado** contra el árbol real (`MOLDE.md`
      §2 reescrita en 4 sub-tablas + §4 actualizada). Reconciliado `settings.py`→`config.py`; añadidos
      `logging_config.py`/`auth_provider.py`/`util.js`/`alembic`/`login.*` y sus tests.
- [x] **T-M02** 🟠 `app-skeleton/` creado (repo hermano `../app-skeleton`, commit `e02b1b0`):
      harness + backend base (Settings/logging/health/handler) + auth enchufable + recurso `Item`
      (CRUD/soft delete/paginación) + Alembic baseline + frontend universal. `run_checks` TODO VERDE
      recién copiado (doctor + ruff + 26 unit + 4 e2e). Prefijo `APP_` (→ `{{ENV_PREFIX}}` en T-M03).
- [x] **T-M03** 🟡 Docs plantilladas (`{{APP_NAME}}/{{DESCRIPTION}}/{{STACK}}/{{ENV_PREFIX}}`) +
      prefijo de env como **una sola perilla** (`env_prefix="APP_"` en `config.py`; estándar por
      `validation_alias`). `MOLDE.md` §4 con la receta de personalización. En `../app-skeleton`
      (commit `5e14adf`); run_checks TODO VERDE (27 unit + 4 e2e).
- [x] **T-M04** 🟡 `MOLDE.md` §5: guía de uso paso a paso (camino automático vs manual, de cero a la
      primera tarea). En `../app-skeleton` (commit `1efcf67`).
- [x] **T-M05** 🟢 `create_app.py` (cookiecutter): copia + rellena `{{...}}` + renombra el prefijo env.
      Verificado generando un proyecto real (`--prefix DEMO`) → `run_checks` TODO VERDE. **Fase M completa.**
- [x] **T-M06** 🟡 Criterio de molde estable **verificado**: `git archive` del molde → carpeta nueva
      limpia (45 ficheros) → `run_checks.py` **TODO VERDE sin tocar nada** (doctor + ruff + 27 unit +
      4 e2e). Anotado en `../app-skeleton/harness/MOLDE.md` (commit `31e450f`).
