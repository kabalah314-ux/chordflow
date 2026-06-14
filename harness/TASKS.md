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

1. **Fase M (cierre)**: **T-M04** guía de uso del molde (en gran parte ya en README + MOLDE.md);
   **T-M05** cookiecutter (🟢 opcional). El molde ya es estable y verificado (T-M06).
2. **Calidad/UX restante**: T-017 toasts, T-020 parser regex, T-040 sync, T-038 refactor backend,
   T-018 bemoles, T-019 auto-scroll, T-021 a11y, T-022 cache-bust auto.
3. **Seguridad menor**: T-030 SRI, T-031 ventana de gracia del caché, T-032 auditar service_role.

> ⚠️ `run_checks` puede fallar el e2e de forma intermitente (T-042); reintentar. Ver CHECKLIST.
> 🧬 El molde vive en el repo hermano `../app-skeleton` (commits `e02b1b0`, `5e14adf`, `31e450f`).

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
T-025 `/health` liveness · T-039 `escapeHtml` consolidado en `util.js` · T-044 backend base del
molde (handler de errores global → cierra los 4 pilares) · T-043 auth desacoplada (provider enchufable).

**Fase M (molde):** T-M01 inventario validado · T-M02 `app-skeleton/` creado · T-M03 docs
plantilladas + prefijo env como una perilla · T-M06 molde estable verificado (copia limpia verde).

**Fase 4 (CI):** T-023 GitHub Actions (`.github/workflows/ci.yml`, run_checks en cada push/PR).

**Integridad de datos:** T-034 owner_id NOT NULL · T-035 Line.type (Literal+CHECK) · T-036
server_default — migración batch `147a6a78da86` (alembic check limpio).

**Refactor/parser:** T-038 `_append_sections` (fin de duplicación) · T-020 CHORD_REGEX reescrito
(add11/maj13/sus2/Em7b5/A7sus4) · T-018 transposición con bemoles (doble escala).

> Estado de calidad ChordFlow: 36 unit + 20 e2e en verde. Molde: 27 unit + 4 e2e en verde.
> Git: 27+ commits. **Molde EXTRAÍDO, PLANTILLADO y VERIFICADO** en `../app-skeleton`. CI listo.
> Pendiente: T-M04 (casi cubierta), T-M05 (opcional) + cola 🟡 de UX/sync/seguridad menor.
> Flakiness e2e (T-042) resuelta. Alembic (T-011) operativo; T-033 (cascade DB) ya cerrado.
