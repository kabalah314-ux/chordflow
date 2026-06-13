# 📌 ChordFlow — Tareas

> Una tarea activa a la vez (recomendado). Al cerrarla, moverla a "Hechas".
> Abrir tareas nuevas copiando `templates/TASK_TEMPLATE.md`.
> Backlog completo y priorizado en `ROADMAP.md`. Diseño del molde en `MOLDE.md`.
> **Última sincronización: 2026-06-13.**

---

## 🟢 En curso

_(ninguna)_

---

## ▶️ Siguiente recomendado

La cola de críticos y la mayoría de los 🟠 altos están cerrados. Elegir de `ROADMAP.md`:

1. **Integridad de datos (Alembic ya operativo)**: T-034 `owner_id NOT NULL` (cuando la auth sea
   obligatoria), T-035 `Line.type` Enum/CHECK, T-036 `server_default` — vía migración batch.
2. **Fase A / 2**: T-039 consolidar `escapeHtml` en `static/util.js`.
3. **Fase M (molde)**: T-M02 `app-skeleton/`, T-043/T-044 (desacoplar auth + backend base).
3. **Fase M (el molde)**: T-M02 crear `app-skeleton/`. Pre-requisito (críticos) ya cumplido.
   T-043/T-044 (desacoplar auth + backend base) alimentan el molde.

> ⚠️ `run_checks` puede fallar el e2e de forma intermitente (T-042); reintentar. Ver CHECKLIST.

---

## ✅ Hechas (resumen; detalle en REGISTRO_DE_CAMBIOS.md y ROADMAP.md)

**Fase 0–1 (críticos):** T-000 harness · T-001 git · T-002 XSS en el render · T-003 fin de la
fuga de huérfanos (PUT) · T-004 CORS explícito · T-005 caché de token.

**Fase 2 (base mantenible):** T-006 `apiFetch` 401 · T-007 Pydantic v2 · T-008 deps pineadas ·
T-009 datetime tz-aware · T-010 listado ligero `SongSummary` (fin del N+1) · T-011 Alembic ·
T-012 índices · T-015 limpieza `test_api.py` · T-024 validación de rangos.

**Fase A (auditoría multi-agente):** T-026 XSS en popup de diagramas · T-027 404→400 + hardening
500 · T-028 caché de token (cota + lock de concurrencia) · T-029 cabeceras de seguridad ·
T-033 FKs ON DELETE CASCADE a nivel DB · T-037 paginación acotada.

**Fase 2 (continuación):** T-014 logging unificado (`setup_logging()` una vez + stdout cloud-friendly) ·
T-013 soft delete real (`deleted_at`, 2º DELETE → 404) · T-016 `Settings` con pydantic-settings ·
T-025 `/health` liveness.

> Estado de calidad: 26 unit + 18 e2e en verde. Git: 15+ commits. `run_checks.py` TODO VERDE.
> Pilares de T-044 (molde backend) ya en su sitio: logging único (T-014), Settings (T-016),
> `/health` (T-025). Falta el handler de errores global.
> Flakiness e2e (T-042) resuelta. Alembic (T-011) operativo; T-033 (cascade DB) ya cerrado.
