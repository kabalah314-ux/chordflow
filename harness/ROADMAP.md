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
- [x] 🟢 **Setlists/repertorios** — `Setlist`+`SetlistItem` (migración `3684ab6335e8`), API `/setlists`
      (CRUD, soft delete, filtra ajenas/borradas), página `setlists.html` (crear/ordenar/ver/borrar) y
      barra **anterior/siguiente** en el reproductor (`?setlist=&pos=`). Tests unit+e2e. EN VIVO.
- [x] **T-104** 🟢 **UI de tablaturas** — editor + render (2026-06-20). El parser (`editor.js`)
      detecta bloques de tab ASCII (`isTabLine` + agrupado de cuerdas) → una línea `type:"tab"` con el
      ASCII en `content`; round-trip en `songToRawText`. El render (`score_render.js`) los pinta en
      `<pre class="line-tab">` (`textContent`, anti-XSS) con estilo monoespaciado (`style.css`). La joya
      intacta (una tab no lleva acordes con id → el motor la ignora). Tests JS en `test_js_logic.py`
      (detección, no-colisión, render seguro, round-trip). run_checks VERDE (173 unit · 73 e2e).
      **Diferido:** tab "sincronizada" al beat (`TabLine.fret_sequence`) → encaja con V3-F6.
- [x] **T-045** 🟢 **Importar desde URL con IA** — **EN VIVO y verificado**. `POST /import/` (auth):
      lee la página (lector **Jina**, con fallback a **descarga directa + limpieza HTML** cuando Jina
      se rate-limitea desde datacenter) y una **IA gratuita por OpenRouter** (`openai/gpt-oss-120b:free`,
      configurable) extrae la partitura en el formato del editor → precarga el textarea. `importer.py`
      + `import_router.py` + botón en el editor. Tests `test_import.py` + e2e. Verificado en producción
      con CifraClub y e-chords (UG bloquea por Cloudflare incluso vía Jina). Coste 0.
- [x] **T-046** 🟢 **Login con Google** — **CONFIGURADO Y VERIFICADO** (2026-06-18). El código ya
      existía (`auth.js::signInGoogle`, botón en `login.html`, handler en `login.js`); solo faltaba la
      config externa. Hecho: (1) **Google Cloud** — proyecto + OAuth client ID "Web application"
      (Client ID `630184504034-…apps.googleusercontent.com`), orígenes JS (`chordflow-ecru.vercel.app`
      + `127.0.0.1:8000`) y redirect URI de Supabase (`https://fwynfifvtthtpzpejfhb.supabase.co/auth/v1/callback`).
      (2) **Supabase** — proveedor Google activado + `site_url` + `uri_allow_list` (prod + local)
      vía **Management API** (`PATCH /v1/projects/{ref}/config/auth`, `external_google_enabled=true`).
      Verificado: el OAuth devolvió un token válido autenticando a `oscarcon314@gmail.com` (provider
      `google`). Es config externa (Supabase), no cubierta por la suite. ⚠️ Revocar el PAT `sbp_` usado.
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

---

# 🎸→🏠 GIRO A SAAS DE BANDA (V2) — backlog activo

> Dirección de producto: `GUIA_MAESTRA_V2.md` + `GUIA_MAESTRA_V2_FUNCIONAL.md` (14 áreas resueltas,
> convenciones §C.4, detalle Fase 7 §C.5, diagrama §C.6). **Todo aditivo** (no rompe producción).
> Roadmap completo y priorizado en `GUIA_MAESTRA_V2_FUNCIONAL.md` §C.1 (Fases 7–13 núcleo, 14–21
> satélite). **Se empieza por la Fase 7** (todo lo demás cuelga de ella).
>
> 🔐 **Regla de oro multi-tenant:** cada ruta de banda valida pertenencia+rol y filtra por
> `band_id`. **Cada ruta exige su test de aislamiento** ("usuario ajeno → 403/404").
> 🔎 **Al cerrar la fase:** `python harness/revision.py fase7 --serve` + veredicto en `REVISIONES.md`.

## Fase 7 — Identidad + núcleo de banda (auth multi-tenant)

> Entidades: `MusicianProfile`, `Band`, `BandMembership`, `BandInvite`. Convenciones transversales
> en §C.4.3 (Decimal/divisa, soft-delete, índices `band_id`, timestamps UTC). `Song.band_id` y
> `Setlist.band_id` NO entran aquí (son Fases 8 y 9).

- [x] **T-048** 🔴 **Migración aditiva**: tablas `musician_profiles`, `bands`, `band_memberships`,
      `band_invites` + índices (`band_id` y FKs) + CHECK (`role`/`status`/`role_to_grant`) + único
      `(band_id, user_id)` + baja blanda (`status`/`left_at`). Migración `39fbdc0fff0f` solo aditiva;
      `alembic check` limpio (sin drift). Test `test_upgrade_crea_el_nucleo_de_banda`. Doctor + 50 unit
      verdes. ✅ Migración aplicada a Postgres prod (deploy 2026-06-16).
- [x] **T-049** 🟠 **Modelos + schemas**: modelos SQLAlchemy hechos en T-048. Schemas Pydantic de las
      4 entidades (`Band` Create/Update/Response/Summary, `BandMembershipResponse`/`MembershipRoleUpdate`,
      `BandInvite` Create/Response, `MusicianProfile`), con `role`/`status` como `Literal` alineados a
      las fuentes únicas `models.BAND_ROLES`/`MEMBERSHIP_STATUSES`. Test `test_schemas_banda` (8 casos,
      incl. alineación schema↔models). Doctor + ruff verdes.
- [x] **T-050** 🔴 **Auth multi-tenant**: `src/services/band_auth.py` con `require_band_member`
      (ajeno/baja/banda-borrada→404) y `require_band_admin` (no-admin→403, compone sobre member→ ajeno
      sigue 404). Devuelven el `BandMembership` para reusar el rol. Test `test_band_auth` (7 casos:
      matriz completa de aislamiento). **Base del aislamiento — la regla de oro.** 65 unit verdes.
- [x] **T-051** 🟠 **Endpoints banda**: `src/api/bands_router.py` — POST crear (creador→admin),
      GET listar "mis bandas" (con mi rol + nº miembros, 1 query agregada), GET ver
      (`require_band_member`), PATCH editar y DELETE soft delete (`require_band_admin`). Registrado en
      `main.py`. Test `test_api_bands` (CRUD completo + **aislamiento por ruta**: ajeno→404 en
      ver/editar/borrar + no la lista). 68 unit verdes.
- [x] **T-052** 🟠 **Endpoints membresía**: `/bands/{id}/members` (listar con nombre real), cambiar
      rol, dar de baja (**baja blanda** `status='left'`+`left_at`), reactivar. Salvaguarda "nunca sin
      admin". Test `test_api_memberships` (baja corta acceso pero conserva histórico; aislamiento).
- [x] **T-053** 🟠 **Invitaciones por código**: `POST /bands/{id}/invites` (admin, código
      `secrets.token_urlsafe`); `GET /invites/{code}` previsualiza; `POST /invites/{code}/accept` crea/
      reactiva `BandMembership`; caducidad/usos máximos. Test `test_api_invites` (aceptar/caducada/
      agotada/ya-miembro 409).
- [x] **T-054** 🟡 **Perfil músico**: `GET/PUT /profile/me` (`MusicianProfile`, autocreación en 1er
      acceso). Test `test_api_profile`: el nombre real aparece en la lista de miembros (no UUID).
- [x] **T-055** 🟢 **Frontend**: `bands.html`/`bands.js` (Mis bandas: lista+crear+detalle con
      miembros+invitar), `join.html`/`join.js` (aceptar por enlace), `profile.html`/`profile.js`.
      `promptModal`/`alertModal` en `util.js`; enlace en biblioteca; SW excluye rutas dinámicas;
      `cachebust.py` + 7 filas en `CHECKLIST_E2E.md`. e2e `test_bands_ui` (3 casos).
- [x] **T-056** 🔴 **Cierre de fase**: `run_checks` **TODO VERDE** (doctor 10/10 · ruff · 83 unit ·
      38 e2e, incl. aislamiento por ruta) + **revisión de sección** `revision.py fase7` ✅ completa
      (3/3 rutas · 3/3 páginas) con veredicto ✅ en `REVISIONES.md`. Registro en `REGISTRO_DE_CAMBIOS.md`.
      ✅ Migración aplicada a Postgres prod (deploy 2026-06-16).

## Fases 8–21 (se detallan en T-NNN al aprobarse cada una)

> Orden y dependencias en `GUIA_MAESTRA_V2_FUNCIONAL.md` §C.1.

- [x] **Fase 8** 🟢 Repertorio de banda (`Song.band_id`, copiar de personal). Área 1. **COMPLETA**:
  - [x] **T-057** 🔴 Migración aditiva `Song.band_id` (nullable, FK `bands` ondelete CASCADE, index) —
        migración `908a0a3875b1` (batch, FK nombrada `fk_songs_band_id_bands`), `alembic check` limpio.
  - [x] **T-058** 🟠 Repertorio backend: `band_songs_router.py` (`/bands/{id}/songs`: listar/crear/
        **copiar** de personal/quitar). `/songs/` personales excluyen `band_id`; `/songs/{id}` (lectura
        y escritura) autoriza a miembros de banda (guest solo lee). Test `test_api_band_songs` (6 casos:
        separación personal/banda, copia independiente, reproductor por pertenencia, miembro edita/guest
        no, quitar, aislamiento).
  - [x] **T-059** 🟢 Repertorio frontend: en la ficha de banda (`bands.js`) — listar, ▶ reproducir,
        copiar de mis partituras (modal selector) y quitar. e2e `test_bands_ui` (copiar al repertorio).
  - [x] **Cierre**: `run_checks` TODO VERDE (89 unit + 39 e2e) · `revision.py fase8` ✅ completa ·
        veredicto en `REVISIONES.md`. ✅ Migración aplicada a Postgres prod (deploy 2026-06-16).
- [x] **Fase 9** 🟢 Setlists de banda (`Setlist.band_id`, `SetlistItem.note`). **COMPLETA**:
  - [x] **T-060** 🔴 Migración aditiva `Setlist.band_id` (FK CASCADE, index) + `SetlistItem.note`
        (Text) — migración `95eddae092db` (FK nombrada), `alembic check` limpio.
  - [x] **T-061** 🟠 Setlists de banda backend: `band_setlists_router.py` (`/bands/{id}/setlists`
        CRUD; las canciones se sacan del **repertorio de la banda**, `_valid_band_song_ids`). `/setlists/`
        personal excluye `band_id`; `/setlists/{id}` (reproductor) autoriza a miembros; patch/delete
        personales estrictos. Test `test_api_band_setlists` (6: desde repertorio, filtra ajenas,
        reproductor por pertenencia, guest 403, editar/borrar, aislamiento).
  - [x] **T-062** 🟢 Setlists de banda frontend: sección 🎵 Setlists en la ficha de banda (`bands.js`)
        — listar, ▶ reproducir en orden (◀▶), crear desde el repertorio (editor available/selected),
        borrar. e2e `test_bands_ui` (crear setlist desde la UI).
  - [x] **Cierre**: `run_checks` TODO VERDE (95 unit + 40 e2e) · `revision.py fase9` ✅ completa ·
        veredicto en `REVISIONES.md`. ✅ Migración aplicada a Postgres prod (deploy 2026-06-16).
  - [x] **T-110** 🟢 **Apunte por canción** (`SetlistItem.note`) en la UI (2026-06-20): el modelo y la
        lectura existían, pero NO había vía de escritura. Schema `SetlistItemIn`+`items` (compat con
        `song_ids`), `band_setlists_router` persiste la nota (filtrada al repertorio), input por canción
        en el editor y apunte en la barra del reproductor. unit + e2e end-to-end + revisión adversarial
        (compat/aislamiento/XSS/correctitud) ✅. VERDE.
  - [x] **Editar un setlist desde la UI** (2026-06-24): botón ✏️ → editor prerrellenado (nombre +
        canciones + notas) → `PATCH`. Solo frontend (`bands.js`, `newBandSetlist` crea/edita). e2e
        `test_editar_setlist_de_banda`. Cierra el diferido "editar notas".
  - [x] **Notas + edición en setlists PERSONALES** (2026-06-24): `setlists.html` gana apunte por canción
        y edición (✏️ → editor prerrellenado → `PATCH`); backend honra `items` (antes solo `song_ids`);
        fix: quitar canción preserva notas. unit `test_setlist_personal_con_notas` + e2e
        `test_editar_repertorio_personal_con_nota`. Cierra el diferido "notas en setlists personales".
- [x] **Fase 10** 🟢 Agenda (`Event`, `EventAttendance`). Áreas 2, 3, 4. **NÚCLEO COMPLETO**:
  - [x] **T-063** 🔴 Migración aditiva `events` + `event_attendance` (`22c7ea96b921`): tipo
        (rehearsal|concert|other), status-pipeline, `setlist_id` (SET NULL), CHECK + único
        `(event_id,user_id)`. `alembic check` limpio.
  - [x] **T-064** 🟠 Agenda backend: `events_router.py` (`/bands/{id}/events`): crear/editar/borrar
        **solo admin**, listar/ver miembros, `PUT .../attendance` (voy/no voy/quizás, incl. guest).
        Setlist solo en conciertos y de la banda. Test `test_api_events` (6: admin crea/miembro no,
        asistencia, guest asiste, setlist validado, editar/borrar admin, aislamiento).
  - [x] **T-065** 🟢 Agenda frontend: sección 📅 Agenda en la ficha de banda (`bands.js`) —
        próximos/pasados, crear evento (admin; tipo/título/fecha/setlist), botones de asistencia.
        e2e `test_bands_ui` (crear evento + marcar asistencia).
  - [x] **Cierre**: `run_checks` TODO VERDE (101 unit + 41 e2e) · `revision.py fase10` ✅ · `REVISIONES.md`.
  - **Diferido (Áreas 2/3/4, no bloquea):** `EventSong` (orden del día), `Venue`, `BandResource`,
    checklist con responsable, campos de concierto (cronograma), logística. Pipeline de booking → Fase 14.
- [x] **Fase 11** 🟢 Finanzas con división (`Transaction`/`Split`, `Settlement`, fondo). Áreas 4, 6. **COMPLETA**:
  - [x] **T-066** 🔴 Migración `transactions`+`transaction_splits`+`settlements` + `Band.currency` (EUR)
        (`84c9ca4f7b64`): Decimal(10,2), flags fondo (`paid_by_fund`/`to_fund`), soft-delete financiero,
        CHECK tipo. `alembic check` limpio.
  - [x] **T-067** 🔴 **Servicio único de balances** `services/balances.py` (función pura): gasto/ingreso/
        fondo/liquidación, reparto con céntimos al último, **invariante cuadra-a-cero**. Test
        `test_balances` (6: ejemplo de la guía, fondo, liquidación, remanente — todos a cero).
  - [x] **T-068** 🟠 Finanzas backend `finance_router.py` (`/bands/{id}/transactions|balances|settlements`):
        registrar (**solo admin**, reparto por defecto a partes iguales, valida pagador/partes/Σ),
        listar/ver (miembros), soft delete, balances, liquidaciones. Test `test_api_finance` (8).
  - [x] **T-069** 🟢 Finanzas frontend: sección 💶 Finanzas en la ficha (`bands.js`) — panel de saldos
        (verde/rojo), registrar movimiento, liquidar, lista de movimientos. e2e `test_bands_ui`.
  - [x] **Cierre**: `run_checks` TODO VERDE (115 unit + 42 e2e) · `revision.py fase11` ✅ · `REVISIONES.md`.
  - [x] **T-106** 🟢 **Reparto personalizado en la UI** (2026-06-20): el modal de movimiento ofrece
        "A partes iguales / Personalizado" (fila por miembro, prerrelleno, valida Σ, envía `splits`).
        El backend ya lo aceptaba (Fase 11). e2e `test_reparto_personalizado_en_movimiento`. VERDE.
  - [x] **T-108** 🟢 **Ligar movimiento a evento desde la UI** (2026-06-20): selector "Evento (opcional)"
        en el modal de movimiento (envía `event_id`) + etiqueta 🎵 del evento en cada movimiento ligado.
        Backend ya validaba `event_id` (Fase 11). e2e `test_ligar_movimiento_a_evento`. VERDE.
  - [x] **T-109** 🟢 **Export CSV de finanzas** (2026-06-20): botón ⬇️ CSV que descarga los movimientos
        (cliente, Blob + BOM UTF-8). e2e `test_exportar_finanzas_csv` (descarga real). VERDE.
  - **Diferido (no bloquea):** cuotas recurrentes; resumen/P&L por evento; filtros de fecha en el CSV.
- [x] **Fase 12** 🟢 Comunicación (`Message`). Área 7. **NÚCLEO COMPLETO**:
  - [x] **T-070** 🔴 Migración `messages` (`7022a3162284`): `event_id` null=chat general / valor=hilo,
        `is_pinned` (notas), soft delete, índices `band_id`/`event_id`. `alembic check` limpio.
  - [x] **T-071** 🟠 Chat backend `messages_router.py` (`/bands/{id}/messages`): publicar (miembros,
        incl. guest), listar (chat general o hilo `?event_id=`, fijados primero), editar el propio,
        borrar (autor/admin), **fijar nota** (solo admin). Test `test_api_messages` (7).
  - [x] **T-072** 🟢 Chat frontend: sección 💬 Chat en la ficha (`bands.js`) — lista con refresco
        periódico (6 s), enviar, fijar (admin), borrar (autor/admin). e2e `test_bands_ui`.
  - [x] **Cierre**: `run_checks` TODO VERDE (122 unit + 43 e2e) · `revision.py fase12` ✅ · `REVISIONES.md`.
  - [x] **T-107** 🟢 **UI del hilo por evento** (2026-06-20): botón 💬 por evento en la agenda abre un
        modal con el hilo de mensajes (`?event_id=`). Refactor `renderMessageList` compartido (chat +
        hilos). e2e `test_hilo_de_discusion_por_evento`. Revisión adversarial (aislamiento+XSS) ✅. VERDE.
  - **Diferido (no bloquea):** `Poll`/encuestas, `Notification`/campana, @menciones; tiempo real
    (Supabase Realtime); hilo embebido en la pestaña (no modal).
- [x] **Fase 13** ✅ (2026-06-16) App shell (nav TÚ/BANDA) + sistema de diseño + rebranding BandFlow. Spec de UX:
  `GUIA_MAESTRA_V2.md` §3 (contexto TÚ agregado + contexto BANDA con banner y pestañas) y §10.
  **Reskin sobre el stack actual** (HTML/CSS/JS vanilla), no se reescribe a otro framework. La joya
  (`sync_engine.js`/`score_render.js`) no se toca. Orden: fundación (diseño → shell) → vistas
  agregadas → reskin → marca. 🔐 Las vistas agregadas exigen su test de aislamiento ("solo MIS bandas").
  - [x] **T-073** 🟠 **Sistema de diseño** `static/design-system.css`: tokens (paleta oscura/clara,
        tipografía, espaciado, radios, sombras) + componentes base (botón, card, input, badge de rol,
        tabs, lista, avatar, `nav-item`, banner de banda). Self-contained (prefijo `bf-`), no colisiona
        con el player. Test `test_design_system.py` (se sirve + declara tokens/componentes). Doctor 10/10.
        ↳ **Fase A (2026-06-16):** tokens reescritos al look **BandFlow** (acento coral `#ff6b4a`,
        IBM Plex, tokens `*-weak`/`hover`, keyframes) según `harness/diseno/BANDFLOW_SPEC.md` §2. Tema
        `data-theme`. Test ampliado (`…adopta_paleta_bandflow`). **Solo tokens; ninguna página usa `bf-*` aún.**
  - [x] **T-074** 🟠 **App shell — contexto TÚ**: `static/shell.js` inyecta el **lateral fijo**
        (Inicio·Biblioteca·Agenda·Finanzas·Chat·Bandas·Perfil); marca activo; móvil → nav
        inferior. e2e: el lateral aparece y navega entre secciones. ✅ (2026-06-16) `shell.js`+
        `shell.css`+`app.html` (anfitriona, 1ª página con `design-system.css`/`bf-*`). Items de
        páginas futuras → «Pronto» (toast). Tema `data-theme`. e2e `test_shell.py` (4). Doctor 10/10.
  - [x] **T-075** 🟠 **Espacio de banda — contexto BANDA**: **banner** (avatar + tu rol) + **pestañas**
        (Resumen·Miembros·Repertorio·Setlists·Agenda·Finanzas·Chat·Ajustes). Refactor del detalle de
        banda a `band.html`+`band.js` (en el shell), REUSANDO los loaders de `bands.js`. ✅ (2026-06-16)
        Las 8 pestañas; editor «crear setlist» desacoplado; lista `bands.html`/`createBand` → `band.html`;
        Ajustes admin (PATCH/DELETE banda). e2e `test_band_space.py` (3) + 6 e2e de `bands_ui` migrados.
        **Nota:** el detalle in-page legacy de `bands.js` (`openBand`) queda sin uso → se retira en T-081.
  - [x] **T-076** 🟠 **Inicio (dashboard agregado)**: endpoint agregado + dashboard en `app.html`.
        ✅ (2026-06-16) `GET /me/dashboard` (`me_router.py`): próximos eventos + últimos mensajes de
        **todas mis bandas** con etiqueta, **aislado** (solo bandas activas mías). Front `home.js`.
        `sw.js` no cachea `/me`. unit `test_api_dashboard.py` (4, incl. aislamiento) + e2e `test_home.py`.
        (El saldo agregado por banda se implementó en **T-079**: `GET /me/balances`.)
  - [x] **T-077** 🟠 **Biblioteca unificada**: todas las canciones (personal + banda) con **buscador** y
        filtro **Todas·Personales·[banda]**. ✅ (2026-06-16) `library.js` une `/songs/` + repertorio de
        cada banda; badge de fuente por tarjeta; de banda solo-lectura. e2e `test_biblioteca_unificada…`
        + 2 casos adaptados. **Diferido:** mostrar también los setlists al elegir banda (va a `band.html`).
  - [x] **T-078** 🟠 **Agenda agregada**: todos los eventos de mis bandas con **etiqueta de banda** +
        filtro. ✅ (2026-06-16) `GET /me/events` (`me_router.py`, aislado) + `agenda.html`/`agenda.js`
        (próximos/pasados + filtro por banda). Agenda ya no es «Pronto» en el lateral. unit
        `test_me_events_*` (incl. aislamiento) + e2e `test_agenda.py`. Revisión ultracode adversarial.
  - [x] **T-079** 🟠 **Finanzas agregada**: **mi saldo por banda** (debes/te deben) + entrada al detalle.
        ✅ (2026-06-16) `GET /me/balances` (`me_router.py`, reusa `compute_balances`, aislado) +
        `finanzas.html`/`finanzas.js` (saldo por banda con color). Finanzas ya no «Pronto». unit
        `test_me_balances…` + e2e `test_finanzas`. Revisión ultracode de `/me/*` aplicada (TZ, event_id,
        tests de aislamiento left/borrada + cancelados).
  - [x] **T-080** 🟠 **Chat agregado**: lista de conversaciones (una por banda); entrar abre el chat de
        esa banda. ✅ (2026-06-16) `GET /me/conversations` (aislado) + `chat.html`/`chat.js`. Chat ya
        no «Pronto» → lateral sin pendientes. unit `test_me_conversations_*` + e2e `test_chat`.
  - [x] **T-081** 🟢 **Reskin de la joya y páginas restantes** al sistema de diseño, **sin tocar**
        `sync_engine.js`/`score_render.js`. ✅ (2026-06-16) Re-tematizado `style.css` a la paleta BandFlow
        (acento coral, fondo `#0d0d10`, IBM Plex vía `@import`) → todas las legacy adoptan el look.
        Player verificado funcionando en captura. **Reskin por tokens** (estructura intacta).
        ↳ **T-105 (2026-06-20):** retirado el detalle in-page legacy muerto (`openBand` + `#band-detail`
        + `showGrid`/`showDetail`/`elDetail`) de `bands.js`/`bands.html`; la ficha de banda vive solo en
        `band.html`. run_checks VERDE. **Pendiente (opcional):** conversión completa a `bf-*` de las legacy.
  - [x] **T-082** 🟢 **Rebranding BandFlow** (visible): títulos, `manifest`, `theme-color`, textos
        ChordFlow→BandFlow. ✅ (2026-06-16) 8 HTML + manifest; `theme-color` `#0d0d10`. Marca técnica
        diferida (API title, SW key, env, repo). Test `test_rebrand.py` (grep sin "ChordFlow" visible).
  - [x] **T-083** 🔴 **Cierre de fase**: `run_checks` TODO VERDE + `revision.py fase13` + veredicto en
        `REVISIONES.md` + `REGISTRO_DE_CAMBIOS.md`. ✅ (2026-06-16) Revisión fase13 ✅ completa (1/1 rutas
        · 5/5 páginas) + veredicto en `REVISIONES.md`. `run_checks` VERDE (139 unit · 57 e2e).
- [~] **Fase 14** 🟢 Booking (pipeline `Event.status` + recordatorios + `EmailTemplate`). Área 10. **EN CURSO:**
  - [x] **T-111** 🟢 **Pipeline en la agenda** (2026-06-20): badge de estado por evento + selector de
        admin para mover el funnel (lead→…→done/cancelled vía PATCH `status`) + estado inicial en el alta.
        Backend ya listo (admin-only, `status` con CHECK/Literal). e2e
        `test_booking_pipeline_cambiar_estado_de_evento`. run_checks VERDE.
  - [x] **T-112** 🟡 **Recordatorios in-app** (2026-06-20): "⏰ Pronto" para eventos en los próximos 7
        días + resumen "🔔 N en booking sin confirmar" en la agenda (cliente). e2e. VERDE. Diferido:
        recordatorios por email/push reales (necesitan infra de envío).
  - [x] **T-115** 🟢 **Campos de booking en el concierto** (2026-06-21): `Event.contact_name`/
        `contact_phone`/`fee` (migración `c341c9bbb0ba`, `alembic check` limpio); campos en el modal de
        evento (solo conciertos) + línea discreta `💶 caché · 📇 contacto` en la agenda. Schemas
        (Create/Update/Response + Summary), `fee` ge=0 → 422. Router sin cambios (model_dump genérico,
        admin-only). unit `test_booking_fields_contacto_y_cache` + e2e. VERDE. ✅ Migración `c341c9bbb0ba`
        aplicada a Postgres prod (deploy 2026-06-23).
  - [x] **T-116** 🟢 **Salas (Venue) reutilizables** (2026-06-21): `Venue` (band_id, name, city, capacity,
        contact, notes) + `Event.venue_id` (FK SET NULL, migración `91d60406fb92`). `venues_router` (CRUD,
        admin gestiona, miembros leen, aislamiento + gate T-098); `events_router` valida la sala (solo
        conciertos + de la banda) y denormaliza `venue_name`. UI: sección "Salas" en Agenda + selector en
        el modal de concierto + `📍` en la agenda. Fix UX: `.modal-card` scrollable. unit
        `test_api_venues` (6) + e2e. VERDE. ✅ Migración `91d60406fb92` aplicada a Postgres prod (deploy 2026-06-23).
  - [x] **Editar sala desde la UI** (2026-06-23, completa T-116): botón ✏️ en la sección Salas → abre el
        modal prerrellenado → `PATCH`. Solo frontend (`bands.js`, `newVenue` crea/edita). e2e
        `test_editar_sala_desde_la_ui`. run_checks VERDE.
  - [x] **Resumen de caché por gira** (2026-06-23): cada gira suma el `fee` de sus conciertos ligados
        (`total_fee` en `TourResponse`/`TourSummary`; `list_tours` con 1 query agregada, sin N+1; UI en
        detalle + fila). unit `test_cache_por_gira_suma_el_fee_de_los_conciertos`. Sin migración. VERDE.
  - [ ] **T-113** 🟢 `EmailTemplate` (plantillas de email de booking; encaja con T-047 emails con marca).
  - [ ] Diferido: resumen de caché por temporada; mapa de salas.

- [x] **T-114** 🟢 **Repertorios (colecciones temáticas)** — diferenciar Repertorio vs Setlist
      (2026-06-21, cola de Oscar #2/#3). La pestaña "Repertorio" pasa a "Repertorios": varias listas
      nombradas que agrupan canciones del pool ("Acústico", "Cañero", "Bodas"…), SIN orden; los Setlists
      siguen siendo el orden de un bolo (con notas T-110). Aditivo: `SongCollection`/`SongCollectionItem`
      (migración `5481a965f5fb`, `alembic check` limpio) + `band_collections_router.py` (CRUD, miembros
      gestionan/guest lee, aislamiento + gate parametrizado T-098) + UI (`band.js`/`bands.js`). unit
      `test_api_collections` (8) + e2e `test_crear_repertorio_coleccion_y_anadir_cancion`. VERDE.
      ↳ **Pulido (2026-06-21):** **crear un setlist desde una colección** (botón "🎵 Crear setlist con
      estas" en el detalle → genera un setlist con esas canciones; cierra el bucle Repertorio→Setlist).
      e2e `test_crear_setlist_desde_una_coleccion`. ✅ Migración `5481a965f5fb` aplicada a Postgres prod
      (deploy 2026-06-23).
      ↳ **Colecciones PERSONALES (2026-06-24):** llevadas a la **Biblioteca** (decisión de Oscar).
      `SongCollection` con `band_id` nullable + `owner_id` (migración `b6434fe1096d`, aplicada a prod);
      `collections_router` (`/collections`, owner-scoped, ajeno→404); UI en `library.js` (fila de
      colecciones + modal crear/editar + filtrar el grid). unit `test_api_collections_personal` + e2e
      `test_coleccion_personal_en_la_biblioteca`. **Diferido:** reordenar dentro de la colección.

---

# 🎸→🌍 V3 — RED MUSICAL CON PLANO PÚBLICO (backlog activo)

> Dirección de producto: `GUIA_MAESTRA_V3.md` (8 decisiones cerradas D1–D8 + orden V3-F1→F11).
> El giro: de "SaaS aislado" a "red musical con un plano público opt-in". **Todo aditivo; la V2
> (Fases 7–13, en producción) no se toca.** Se empieza por **V3-F1 (diseño)** porque es gratis,
> transversal y sube la percepción de todo lo demás.
>
> 🔐 La regla de oro multi-tenant sigue vigente; lo público será una **capa separada opt-in** con
> su **propio** test ("fila privada jamás aparece en `/public`"), distinto del de aislamiento de banda.

## V3-F1 — Pulido de diseño profesional (D7)

> CSS sobre el sistema de diseño ya existente (`design-system.css`, prefijo `bf-`). **Sin framework**
> (única dependencia aceptada: Lucide, iconos SVG). No toca rutas ni `band_id`. La joya
> (`sync_engine.js`/`score_render.js`) no se toca por dentro: el "teleprompter espectacular" es solo CSS.

- [x] **T-084** 🟢 **Estados de UI base** en `design-system.css`: deshabilitado (botón/input),
      cargando (`.bf-spinner` + botón `[data-loading]`), `.bf-skeleton`, `.bf-empty` (empty state),
      foco accesible (`:focus-visible` en card/nav/tab/list) y `.bf-num` (cifras tabulares). Todo
      `bf-`, aditivo. Test `test_design_system_tiene_estados_de_ui`. `cachebust` al día. run_checks
      TODO VERDE (140 unit · 57 e2e).
- [x] **T-085** 🟢 **Iconos SVG (Lucide)**: helper auto-alojado `static/icons.js` (`bfIcon(name)`,
      trazos Lucide MIT, `currentColor`, cero dependencia externa) cargado antes de `shell.js` en las
      8 páginas con shell. El lateral (nav + tema + ajustes + cerrar sesión) usa SVG en vez de emojis.
      e2e `test_shell_nav_usa_iconos_svg`. `cachebust` al día. run_checks TODO VERDE (140 unit · 58 e2e).
- [x] **T-086** 🟢 **Teleprompter espectacular**: acorde activo con **glow coral pulsante**
      (`@keyframes chord-pulse`, guard `prefers-reduced-motion`) + más contraste teleprompter
      (líneas inactivas 0.5→0.4). **Solo CSS** en `style.css`; la lógica de la joya (ids/BPM) intacta.
      e2e `test_acorde_activo_tiene_glow` (box-shadow computado ≠ none). run_checks TODO VERDE
      (140 unit · 59 e2e). ↳ Modo escenario/fullscreen → se hace en **V3-F4 (Modo Directo)** (lleva JS).
- [x] **T-087** 🟢 **Empty states + skeletons aplicados** a las vistas agregadas: helper
      `bfEmpty(icon,title,text)` en `icons.js`; Inicio/Agenda/Finanzas/Chat usan `.bf-empty` (con
      icono SVG) en sus estados vacíos; Inicio muestra **skeleton** (`.bf-skeleton`) mientras carga.
      e2e `test_ui_helper_empty_state`. run_checks TODO VERDE (140 unit · 60 e2e).
- [x] **Cierre V3-F1**: `run_checks` TODO VERDE (140 unit · 60 e2e) en cada tarea. Fase de pulido
      transversal de diseño (solo front, sin rutas nuevas) → no requiere `revision.py` (que cubre
      integración de rutas/páginas de banda). **V3-F1 COMPLETA.** Siguiente: V3-F2.

## V3-F2 → V3-F11 (se detallan en T-NNN al aprobar cada fase)

> Orden y razonamiento en `GUIA_MAESTRA_V3.md` §6.

- [~] **V3-F2** 🟢 Mapa de estructura + bolita de posición, **modo solitario** (mejora la joya, sin infra). **Núcleo (bolita) COMPLETO:**
  - [x] **T-088** 🟢 **Bolita de posición** (client-side, cero backend): barra de progreso
        (#song-progress) + dot + **sección actual**, derivadas del timeline de beats que ya existe
        (`state.currentBeat`/`totalBeats`). Hecho en `app.js` (controlador) + `style.css`; **el motor
        `sync_engine.js` no se toca**. e2e `test_bolita_de_posicion_avanza`. run_checks TODO VERDE
        (140 unit · 61 e2e).
  - [ ] **Diferido — Mapa de estructura persistido** (`ArrangementMap`/`ArrangementSegment` + modo
        "tap para aprender"): solo necesario cuando una canción NO trae buenos tiempos (imports web);
        para canciones del editor el timeline de beats ya basta. Se hará junto a **V3-F6** (sync de
        ensayo), donde el re-timing aporta de verdad y comparte el modelo de sala.
- [~] **V3-F3** 🟡 Habilitadores. **Parte de código (gratis) COMPLETA:**
  - [x] **T-097** 🟢 **Andamiaje `Band.plan`** (Free/Pro, sin cobrar, D8): columna `Band.plan` +
        enum `BAND_PLANS` + migración `d7e9f1a2b3c4` + expuesto en `BandResponse`/`BandSummary` +
        editable por admin vía PATCH (Literal `BandPlan`, inválido→422). Test `test_band_plan`.
        run_checks VERDE. ✅ Migración aplicada en Postgres prod (head `e9f1a2b3c4d5`).
  - [x] **T-098** 🟢 **Gate de aislamiento parametrizado**: `test_aislamiento_parametrizado.py`
        recorre 16 rutas de banda y exige que un ajeno reciba 403/404 (caza fugas si alguien añade
        una ruta sin guard). 163 unit · 67 e2e VERDE.
  - [ ] **T-099** 🟡 **Storage (Supabase) — BLOQUEADO: necesita configuración de Oscar** (crear
        bucket(s) + políticas por banda + env vars). Es el prerequisito de audio propio del ensayo,
        grabadora, fotos/EPK/merch y transcripción IA.
- [x] **V3-F4** 🟢 Quick wins de directo (client-side, sin coste). **COMPLETA:**
  - [x] **T-089** 🟢 **Modo Directo** (escenario a pantalla completa): botón en el player que añade
        `stage-mode` (oculta la barra superior, letra grande, máximo contraste) + Fullscreen API
        (con fallback si el navegador lo bloquea) + salida con Esc. Solo CSS/JS de control en
        `index.html`/`style.css`/`app.js`; el motor no se toca. e2e `test_modo_directo_alterna_y_oculta_barra`.
        run_checks TODO VERDE (140 unit · 62 e2e).
  - [x] **T-090** 🟢 **Vídeo de referencia (YouTube)**: campo nuevo `Song.reference_url` (modelo +
        schema + migración aditiva `b3f1a9c2d4e5`, batch) + input en el editor + botón 🎬 en el player
        que embebe el YouTube (id parseado del enlace). e2e `test_video_de_referencia_youtube` +
        `test_sin_referencia_no_hay_boton`. run_checks TODO VERDE (140 unit · 64 e2e). ✅ Migración
        aplicada a Postgres prod (head `e9f1a2b3c4d5`).
  - [x] **T-091** 🟢 **Afinador integrado** (`tuner.js`): detección de tono por **autocorrelación**
        (función pura `bfDetectPitch`, testeable con onda sintética) + micro (Web Audio) + panel con
        nota/cents/aguja en el player. e2e `test_afinador_detecta_y_abre` (440 Hz → La4 + UI).
        run_checks TODO VERDE (140 unit · 66 e2e).
  - [x] **T-092** 🟢 **Pasapáginas / pedalera**: PageDown/PageUp y flechas (las teclas que envían los
        pedales Bluetooth) pasan de canción en un setlist o hacen scroll de una página en la partitura
        (manos libres, se ignora en campos de texto). e2e `test_pasapaginas_hace_scroll`. run_checks
        TODO VERDE (140 unit · 65 e2e).
  - [ ] **Diferido** — Loop A-B / tempo trainer y **metrónomo *lookahead***: requieren añadir *seek*/
        bucle al motor → se hacen junto a **V3-F6** (sync de ensayo), para no tocar la joya ahora.
- [x] **V3-F5** 🟢 Gestión de giras (`Tour`/`TourStop`/`TourBudgetLine`). **COMPLETA:**
  - [x] **T-093** 🔴 Modelos `Tour`/`TourStop`/`TourBudgetLine` + enum `TOUR_STATUSES` + migración
        aditiva `c5d7e9f1a2b3` (3 tablas, índices `band_id`/FKs, CHECK status, batch). `alembic check`
        sin drift (validado por `test_migrations`). ✅ Migración aplicada a Postgres prod.
  - [x] **T-094** 🟠 Schemas Pydantic (Tour Create/Update/Response/Summary, Stop, BudgetLine).
  - [x] **T-095** 🟠 `tours_router.py` (`/bands/{id}/tours` + `/stops` + `/budget`): CRUD gira
        (admin), paradas ligadas a conciertos de la banda (valida pertenencia del evento), presupuesto
        con total, miembros leen. Registrado en `main.py`. Test `test_api_tours` (5 casos: admin/miembro,
        paradas, presupuesto, CRUD, **aislamiento por ruta** ajeno→404). run_checks VERDE (145 unit · 66 e2e).
  - [x] **T-096** 🟢 Frontend: pestaña **Giras** en `band.html` (autocontenida): lista + crear gira
        (admin), detalle con **ruta** (paradas ligadas a conciertos de la banda) y **presupuesto** con
        total, añadir/quitar paradas y líneas (admin). e2e `test_band_space_giras`. run_checks VERDE
        (145 unit · 67 e2e). ✅ Migración aplicada en Postgres prod.
  - **Diferido:** **mapa Leaflet+OSM** (evita meter CDN nueva ahora; sin SRI); ligar gasto real
        (`Transaction`) a la gira desde la UI; co-organización con otra banda (Opción 0 informativa).
- [ ] **V3-F6** 🟠 Realtime + sala de ensayo sincronizada (Supabase Realtime + `/clock`; sincronía visual + metrónomo, D5/D6).
- [ ] **V3-F7** 🟢 Efecto red sin copyright: compartir `unlisted` + onboarding viral + oEmbed (introduce el eje `visibility`).
- [ ] **V3-F8** 🟢 EPK + página pública + perfil indexable + RSVP + seguir/fans (entra el rol usuario-fan + RLS).
- [x] **V3-F9** 🟢 Biblioteca global — **EL RECLAMO** (D9: contribución por defecto). **COMPLETA (backend + revisión + frontend):**
  - [x] **T-100** 🔴 Modelos `MusicalWork`/`PublicScore`/`ScoreRating`/`ScoreComment` + migración
        `e9f1a2b3c4d5` (plano de datos SEPARADO, copia desacoplada). `alembic check` sin drift.
  - [x] **T-101** 🟠 `catalog_router.py` (`/catalog`): publicar ("ponla aquí"), buscar, detalle,
        importar (banda/personal), valorar (1–5), comentar. Registrado en `main.py`. Test
        `test_api_catalog` (10 casos incl. propiedad/pertenencia y round-trip).
  - [x] **T-102** 🔴 **Revisión ultracode aplicada** (33 agentes, 20 hallazgos confirmados): C1
        **letra recortada en público / completa al importar** (D2); round-trip COMPLETO (tabs,
        repeat/color/hint, `reference_url`); dedup de publicación (D9, source_song_id→409); try/except
        + carrera de `MusicalWork`; `rating_avg` Decimal; import valida banda no borrada; índice
        compuesto + `updated_at`. Diferido: XSS escaping (en el frontend), rate-limit de comentarios.
        run_checks TODO VERDE (177 unit · 67 e2e). ✅ Migración aplicada en Postgres prod.
  - [x] **T-103** 🟢 **Frontend**: `biblioteca-global.html`+`catalogo.js` (Explorar): buscar, reclamo
        "ponla aquí" (→ editor, que **publica por defecto**, D9), detalle con **preview de letra
        recortada** (reusa `score_render`), **importar** a banda/personal, **valorar** (estrellas) y
        **comentar** (todo escapado, H2). Item "Explorar" (icono globo) en el lateral del shell. e2e
        `test_catalogo` (buscar/abrir + nav). run_checks TODO VERDE (177 unit · 71 e2e).
  - **Diferido:** navegación pública SIN login + SEO (necesita el plano público/Supabase), moderación.
- [ ] **V3-F10** 🟢 Red acotada (D3): directorio público + bolsa de colaboraciones (`CollabPost`), sin DM.
- [ ] **V3-F11** 🟡 Monetización de pago (Stripe/Pro) cuando Storage + web pública den el gancho.
- [ ] **Fase 15** 🟡 Almacenamiento (Supabase Storage) — subida real de archivos. Transversal.
- [ ] **Fase 16** 🟢 Promoción + EPK + `Contact`. Área 9.
- [ ] **Fase 17** 🟢 Página pública + Fans (`FanSubscriber`, `FanMessage`). Área 14.
- [ ] **Fase 18** 🟡 Inventario (`InventoryItem`). Área 5.
- [ ] **Fase 19** 🟡 Producción (`Project`, `Task` genérica). Área 11.
- [ ] **Fase 20** 🟡 Merch (`MerchProduct`/`MerchVariant`). Área 13.
- [ ] **Fase 21** ⚪ Legal/administrativo (fiscales banda + documentos). Área 12.
