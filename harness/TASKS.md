# 📌 ChordFlow — Tareas

> Una tarea activa a la vez (recomendado). Al cerrarla, moverla a "Hechas".
> Abrir tareas nuevas copiando `templates/TASK_TEMPLATE.md`.
> El backlog detallado vive en `ROADMAP.md`. Aquí se desarrollan las próximas a ejecutar.

---

## 🟢 En curso

_(ninguna — los 5 críticos cerrados. Siguiente: Fase 2 del ROADMAP **o** empezar el MOLDE.)_

---

## 📋 Próximas

La cola de críticos está vacía. Elegir la siguiente de `ROADMAP.md`:
- **Fase 2** (base mantenible): T-007 Pydantic v2 · T-008 deps pineadas · T-010 N+1 en listado · …
- **Fase M** (el molde): T-M01 inventario · T-M02 crear `app-skeleton/`. Ver `MOLDE.md`.
  Ya se cumple el pre-requisito (T-001…T-005 hechos).

---

## ✅ Hechas

### T-005 — Caché de validación de token (2026-06-13)
- Caché TTL en memoria (`CHORDFLOW_TOKEN_TTL`) + degradación elegante si Supabase cae.
  `auth.py`. Tests en `test_security.py`.

### T-004 — CORS por lista explícita (2026-06-13)
- `CHORDFLOW_ALLOWED_ORIGINS` en `main.py` (default localhost). Test en `test_security.py`.

### T-003 — Fin de la fuga de huérfanos en PUT (2026-06-13)
- Borrado vía ORM (cascade) + `PRAGMA foreign_keys=ON`. `songs_router.py`, `db.py`.
  Test `test_put_no_deja_filas_huerfanas`.

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
