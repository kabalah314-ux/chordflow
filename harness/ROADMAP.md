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
- [ ] **T-010** 🟠 **N+1 en `GET /songs/`**: la lista usa `SongResponse` anidado (sections→lines→
      chords) → lazy-load por canción. Crear `SongSummary` ligero (sin estructura) para el listado.
      → Test: el JSON de `/songs/` no trae `sections`.
- [ ] **T-011** 🟠 **Alembic** para migraciones (hoy solo `create_all`, no aplica cambios de esquema).
- [x] **T-012** 🟠 **Índices** en `Song.owner_id`, `Song.deleted_at` y las 4 FKs (`index=True`).
      (Aplica a BD nuevas; la existente requerirá la migración de T-011.)
- [ ] **T-013** 🟡 **Soft delete real** en `DELETE` (hoy hard delete pese a existir `deleted_at`)
      y decidir el comportamiento de `is_public` (hoy `get_song` filtra siempre por dueño).
- [ ] **T-014** 🟡 **Unificar logging**: quitar `basicConfig` de `db.py` (módulo de librería);
      configurarlo una sola vez en `main.py` y permitir log a stdout (cloud-friendly).
- [x] **T-015** 🟡 **`test_api.py` legacy eliminado** (script manual con `requests`, redundante
      con el harness).
- [ ] **T-016** 🟡 **`pydantic-settings`**: un objeto `Settings` validado en vez de `os.getenv`
      sueltos repartidos por `db.py`/`auth.py`/`main.py`.

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
- [ ] **T-025** 🟡 **Endpoint `/health`** real (liveness) separado de `/config`.

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
- [ ] **T-033** 🟠 FKs sin `ondelete="CASCADE"` a nivel DB (hoy solo cascade ORM + PRAGMA).
- [ ] **T-034** 🟡 `owner_id` nullable → `NOT NULL` cuando la auth sea obligatoria.
- [ ] **T-035** 🟡 `Line.type` sin restricción (Enum/CHECK) y columnas JSON sin validar.
- [ ] **T-036** 🟡 Defaults solo en Python, no `server_default` en la DB.

**🟠 API / backend (pendientes):**
- [x] **T-037** 🟠 Paginación acotada: `skip` `Query(ge=0)`, `limit` `Query(ge=1, le=500)` → 422
      fuera de rango. Test `test_paginacion_acotada`.
- [ ] **T-038** 🟡 `create_song`/`update_song` duplican el armado de la estructura → extraer helper.

**🟡 Frontend (pendientes):**
- [ ] **T-039** 🟡 Consolidar `escapeHtml` (duplicado en `library.js`, `score_render.js`, + uso en
      `chord_shapes.js`) en un `static/util.js` compartido.
- [ ] **T-040** 🟡 Parser/sync: revisar casos borde de `isChordLine`, desalineación de acordes y
      `findActiveChord` (último acorde / reset).
- [ ] **T-041** 🟡 Fallos de carga inicial silenciosos en el frontend (avisar al usuario).

**🟡 Tests (pendientes):**
- [ ] **T-042** 🟡 Cobertura: `sync_engine.js`, `chord_shapes.js`, caminos negativos de la API y
      errores de red sin test; añadir medición de cobertura.

**🧬 Molde (van a `MOLDE.md` / Fase M):**
- [ ] **T-043** 🟠 Desacoplar `auth.py` de Supabase (provider enchufable) y parametrizar el prefijo
      de env vars (`CHORDFLOW_*`).
- [ ] **T-044** 🟠 Backend base del molde: `/health` (T-025), handler de errores global, logging
      configurado **una vez** (T-014), `Settings` con pydantic-settings (T-016), README/plantillas.

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
