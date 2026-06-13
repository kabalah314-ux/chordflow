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
