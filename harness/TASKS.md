# 📌 ChordFlow — Tareas

> Una tarea activa a la vez (recomendado). Al cerrarla, moverla a "Hechas".
> Abrir tareas nuevas copiando `templates/TASK_TEMPLATE.md`.
> El backlog detallado vive en `ROADMAP.md`. Aquí se desarrollan las próximas a ejecutar.

---

## 🟢 En curso

_(ninguna — la siguiente recomendada es **T-003: fuga de huérfanos en PUT**)_

---

## 📋 Próximas (cola priorizada, ya detalladas)

### T-003 — Eliminar la fuga de filas huérfanas en PUT
- **Prioridad:** 🔴 · **Apertura:** 2026-06-13
- **Objetivo:** que editar una canción no deje `lines`/`chord_markers`/`tab_lines` huérfanos.
- **Causa raíz:** `db.query(Section).filter(...).delete()` es bulk delete → no dispara el
  cascade ORM `delete-orphan`; y SQLite no fuerza FKs por defecto.
- **Plan (elegir A o B):**
  - **A (recomendada):** borrar vía ORM para que cascade actúe:
    `db_song.sections.clear()` / iterar `db.delete(sec)` y `flush` antes de recrear.
  - **B:** activar `PRAGMA foreign_keys=ON` por conexión (event listener en `db.py`) +
    `ondelete="CASCADE"` en las FKs.
- **Archivos a tocar:** `src/api/songs_router.py` (y `src/services/db.py` si opción B).
- **Aceptación:**
  - [ ] Test unit: crear canción → contar filas en `chord_markers` → `PUT` con otra estructura
        → el total de `chord_markers` corresponde solo a la nueva (sin huérfanos).
  - [ ] `python harness/run_checks.py` verde.

### T-004 — CORS por lista explícita de orígenes
- **Prioridad:** 🔴 · **Apertura:** 2026-06-13
- **Objetivo:** quitar `allow_origins=["*"]` + `allow_credentials=True`.
- **Plan:** leer `CHORDFLOW_ALLOWED_ORIGINS` (coma-separada) en `main.py`; default seguro a
  `http://127.0.0.1:8000`. Documentar la var en `.env`.
- **Archivos a tocar:** `src/main.py`, `.env` (clave nueva, sin secreto).
- **Aceptación:**
  - [ ] Petición con `Origin` no permitido no recibe `access-control-allow-origin`.
  - [ ] Test unit con el `client` comprobando cabeceras CORS.
  - [ ] doctor verde (el smoke sigue funcionando en localhost).

### T-005 — Validación de token sin bloquear ni caer con Supabase
- **Prioridad:** 🔴 · **Apertura:** 2026-06-13
- **Objetivo:** no llamar a Supabase (red síncrona) en cada request; no caer si Supabase cae.
- **Plan (elegir):**
  - Caché en memoria `token → (user_id, expiry)` con TTL corto (p. ej. 60 s), o
  - Validación local del JWT (firma con el JWT secret de Supabase) — más robusto, más trabajo.
- **Archivos a tocar:** `src/services/auth.py`.
- **Aceptación:**
  - [ ] Test unit (mock de la llamada a Supabase): dos requests con el mismo token →
        la función de validación remota se invoca **una** vez.
  - [ ] Si la validación remota falla pero hay caché válida, la request pasa.
  - [ ] run_checks verde.

---

## ✅ Hechas

### T-002 — Arreglar XSS en el renderer (2026-06-13)
- Escapado en `score_render.js` (`escapeHtml` + `renderLyricWithChords` + `chordSpan`),
  cache-busting `?v=8`. Test J3 `test_render_escapa_letra_y_acorde_maliciosos`. run_checks verde.
- Extra: arreglado bug de cuelgue del `live_server` en `conftest.py` (pipe lleno → bloqueo),
  `test_editor` insensible a mayúsculas, lint (`is_(None)`, orden de imports).

### T-001 — Inicializar git + primer commit (2026-06-13)
- `git init` + commit inicial. Verificado: `.env.local`/`*.db` fuera de git.
  `.gitattributes` (EOL=LF) y `*.log` añadidos.

### T-000 — Montar el harness de funcionamiento
- **Objetivo:** sistema de trabajo ordenado (doctor, tests Playwright, roadmap, reglas).
- **Archivos:** `CLAUDE.md`, `harness/*`, `tests/*`, `pyproject.toml`, `requirements-dev.txt`,
  y modo test en `src/services/auth.py`, `src/main.py`, `static/auth.js`.
- **Criterio de aceptación:** `python harness/doctor.py` verde y `python harness/run_checks.py`
  ejecuta lint + unit + e2e.
- **Verificación:** doctor pasa todos los checks; smoke test E2E carga la app sin errores
  de consola; tests de API en verde.
