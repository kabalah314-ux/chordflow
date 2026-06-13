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
- [ ] **T-003** 🔴 **Fuga de filas huérfanas en `PUT`** (`songs_router.py:95`). El bulk
      `db.query(Section).delete()` NO dispara el cascade ORM y SQLite no fuerza FKs → `lines`,
      `chord_markers` y `tab_lines` quedan huérfanos en cada edición. Arreglar con **una** de:
      (a) `PRAGMA foreign_keys=ON` por conexión + `ON DELETE CASCADE`, o (b) borrar vía ORM
      (`for sec in db_song.sections: db.delete(sec)`) para que cascade actúe.
      → Test: editar una canción dos veces y comprobar que `chord_markers` no acumula huérfanos.
- [ ] **T-004** 🔴 **CORS explícito**. Sustituir `allow_origins=["*"]` + `allow_credentials=True`
      por lista de orígenes vía `CHORDFLOW_ALLOWED_ORIGINS` (coma-separada). → Test: petición con
      `Origin` no permitido no recibe cabecera CORS.
- [ ] **T-005** 🔴 **Validación de token sin bloquear ni depender de Supabase en cada request**
      (`auth.py`). Hoy `urllib.urlopen` síncrono por request: latencia + caída total si Supabase cae.
      Cachear el resultado (TTL corto, p. ej. 60 s) o validar el JWT localmente con el secret.
      → Test: dos requests seguidas con el mismo token solo llaman a Supabase una vez (mock).
- [ ] **T-006** 🟠 **`apiFetch` maneja 401** (`auth.js`): si el backend responde 401, redirigir
      a `login.html` automáticamente. → Test E2E: token inválido → acaba en login.

## Fase 2 — Base mantenible
- [ ] **T-007** 🟠 **Migrar a Pydantic v2**: `orm_mode`→`from_attributes`, `.dict()`→`.model_dump()`
      en `schemas.py`, `songs_router.py`. Quita los DeprecationWarning.
- [ ] **T-008** 🟠 **Pinear dependencias** en `requirements.txt` (hoy sin versiones).
      Congelar versiones probadas (`pip freeze` filtrado).
- [ ] **T-009** 🟠 **`datetime.utcnow()`→`datetime.now(timezone.utc)`** (`models.py`).
- [ ] **T-010** 🟠 **N+1 en `GET /songs/`**: la lista usa `SongResponse` anidado (sections→lines→
      chords) → lazy-load por canción. Crear `SongSummary` ligero (sin estructura) para el listado.
      → Test: el JSON de `/songs/` no trae `sections`.
- [ ] **T-011** 🟠 **Alembic** para migraciones (hoy solo `create_all`, no aplica cambios de esquema).
- [ ] **T-012** 🟠 **Índices** en `Song.owner_id`, `Song.deleted_at` y las FKs (`index=True`).
- [ ] **T-013** 🟡 **Soft delete real** en `DELETE` (hoy hard delete pese a existir `deleted_at`)
      y decidir el comportamiento de `is_public` (hoy `get_song` filtra siempre por dueño).
- [ ] **T-014** 🟡 **Unificar logging**: quitar `basicConfig` de `db.py` (módulo de librería);
      configurarlo una sola vez en `main.py` y permitir log a stdout (cloud-friendly).
- [ ] **T-015** 🟡 **Limpiar `test_api.py`** de la raíz (script manual viejo, usa `requests` no
      declarado, redundante con el harness). Eliminar o mover a `scripts/`.
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
- [ ] **T-024** 🟡 **Validación de rangos en schemas** (`bpm` 40–240, `year` razonable) con `Field(...)`.
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
