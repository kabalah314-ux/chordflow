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
- [ ] **T-017** 🟡 Reemplazar `alert()`/`confirm()` por toasts/modales (lenguaje glassmorphism).
- [ ] **T-018** 🟡 **Transposición con bemoles correctos** (hoy siempre sostenidos: a Bb muestra A#).
- [ ] **T-019** 🟡 **Auto-scroll anclado al acorde activo** (hoy mapeo lineal beat→píxel, se desfasa).
- [ ] **T-020** 🟡 **Parser**: `CHORD_REGEX` solo capta un dígito (`(\d)?`) → no parsea `add11`,
      `maj13`, `sus2`. Ampliar regex y cubrir con test.
- [ ] **T-021** 🟡 Accesibilidad: `aria-label` en botones de emoji + atajos (Espacio=play).
- [ ] **T-022** 🟡 Cache-busting automático (hash de contenido) en lugar de `?v=N` manual.

## Fase 4 — CI / profesionalización
- [ ] **T-023** 🟠 **GitHub Actions**: correr `python harness/run_checks.py` en cada push/PR.
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
- [ ] **T-030** 🟡 Sin **SRI** en el `<script>` del CDN de Supabase (integrity + crossorigin).
- [ ] **T-031** 🟡 Degradación del caché de token (T-005) puede dejar pasar un token **revocado**
      mientras dure la caché → acotar la ventana de gracia / invalidación.
- [ ] **T-032** 🟡 Verificar que la `service_role` key nunca se sirve ni se commitea (auditar `/config`
      y el historial); documentar.

**🟠 Integridad de datos (pendientes, encajan con Alembic T-011):**
- [x] **T-033** 🟠 FKs con `ondelete="CASCADE"` a nivel DB (las 4) + migración `dac91229a048`
      (batch mode con naming_convention para soltar FKs sin nombre). Defensa en profundidad sobre
      el cascade ORM (T-003). Test `test_cascade_a_nivel_db` (borrado con SQL directo).
- [ ] **T-034** 🟡 `owner_id` nullable → `NOT NULL` cuando la auth sea obligatoria.
- [ ] **T-035** 🟡 `Line.type` sin restricción (Enum/CHECK) y columnas JSON sin validar.
- [ ] **T-036** 🟡 Defaults solo en Python, no `server_default` en la DB.

**🟠 API / backend (pendientes):**
- [x] **T-037** 🟠 Paginación acotada: `skip` `Query(ge=0)`, `limit` `Query(ge=1, le=500)` → 422
      fuera de rango. Test `test_paginacion_acotada`.
- [ ] **T-038** 🟡 `create_song`/`update_song` duplican el armado de la estructura → extraer helper.

**🟡 Frontend (pendientes):**
- [x] **T-039** 🟡 `escapeHtml` consolidado en `static/util.js` (global canónica, segura en atributos
      + null-safe). Eliminadas las 2 copias divergentes; `util.js?v=1` cargado antes de sus dependientes
      en las 3 HTML (`library.js v11`, `score_render.js v9`). Cubierto por los e2e de XSS existentes.
- [ ] **T-040** 🟡 Parser/sync: revisar casos borde de `isChordLine`, desalineación de acordes y
      `findActiveChord` (último acorde / reset).
- [ ] **T-041** 🟡 Fallos de carga inicial silenciosos en el frontend (avisar al usuario).

**🟡 Tests (pendientes):**
- [~] **T-042** 🟡 **Flakiness e2e resuelta** (3 carreras): timeout httpx de la fixture `api` 5→30 s;
      deadline de arranque del `live_server` 25→45 s; y `test_apifetch_redirige_a_login_en_401`
      reescrito determinista (caché de `/config` + rebote de `login.js`, vía `framenavigated`).
      Pasó 5/5 en repetición. **Pendiente** del alcance original (no bloqueante): cobertura de
      `sync_engine.js`/`chord_shapes.js`, caminos negativos de API y medición de cobertura.

**🧬 Molde (van a `MOLDE.md` / Fase M):**
- [ ] **T-043** 🟠 Desacoplar `auth.py` de Supabase (provider enchufable) y parametrizar el prefijo
      de env vars (`CHORDFLOW_*`).
- [x] **T-044** 🟠 Backend base del molde — **4 pilares técnicos completos**: `/health` (T-025),
      handler de errores global (`@app.exception_handler(Exception)` → 500 genérico, sin filtrar
      internals; test `test_handler_global_500_no_filtra_internals`), logging único (T-014),
      `Settings` pydantic-settings (T-016). README/plantillas del molde → se materializan en T-M02.

## Fase 5 — Diferenciación de producto
- [ ] 🟢 PWA + offline · 🟢 Setlists/repertorios · 🟢 Export PDF · 🟢 UI de tablaturas
      (`TabLine` ya modelado) · 🟢 Responsive/tablet · 🟢 Migrar SQLite → Postgres/Supabase.

---

## Fase M — El MOLDE (esqueleto reutilizable para otras apps)

> Objetivo: extraer de ChordFlow lo agnóstico al dominio y dejar un molde estable.
> Detalle del diseño en [`harness/MOLDE.md`](MOLDE.md). **Pre-requisito: T-001 a T-005 hechos**
> (no se moldean bugs). Ver `MOLDE.md` para qué es universal y qué es por-proyecto.

- [ ] **T-M01** 🟠 Validar el inventario universal vs por-proyecto (tabla en `MOLDE.md`).
- [ ] **T-M02** 🟠 Crear `app-skeleton/` con el esqueleto agnóstico (harness + `src` base +
      `tests` scaffold + config), usando un recurso de ejemplo genérico (`Item`) en vez de `Song`.
- [ ] **T-M03** 🟡 Plantillar `CLAUDE.md` y `GUIA_MAESTRA.md` con huecos `{{APP_NAME}}`, etc.
- [ ] **T-M04** 🟡 `MOLDE.md` → guía de uso del molde (cómo nace un proyecto nuevo desde él).
- [ ] **T-M05** 🟢 (Opcional) `create_app.py` tipo cookiecutter que rellene los huecos solo.
- [ ] **T-M06** 🟡 Criterio de molde estable: generar un proyecto vacío desde el molde y que
      `python harness/doctor.py` quede **verde sin tocar nada**.
