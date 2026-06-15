# 📌 ChordFlow — Tareas

> Una tarea activa a la vez (recomendado). Al cerrarla, moverla a "Hechas".
> Abrir tareas nuevas copiando `templates/TASK_TEMPLATE.md`.
> Backlog completo y priorizado en `ROADMAP.md`. Diseño del molde en `MOLDE.md`.
> **Última sincronización: 2026-06-15.**

---

## 🚀 EN PRODUCCIÓN: https://chordflow-ecru.vercel.app

La app está **desplegada y en vivo** (Vercel + Supabase auth + Postgres). Repo GitHub privado
`kabalah314-ux/chordflow` (rama `main`, auto-deploy en cada push). Cuenta de prueba:
`oscarcon314@gmail.com` / `Chordflow2026!`. Detalle en REGISTRO §"Estado actual".

CLIs ya logueadas en la máquina: `gh` y `vercel` (ambas `kabalah314-ux`). Secretos en `.env.local`
(gitignored): Supabase, `DATABASE_URL` Postgres, `OPENROUTER_API_KEY`.

---

## 🟢 En curso

_(ninguna)_

---

## ▶️ Siguiente recomendado (para el próximo hilo)

Toda la deuda de calidad (T-001…T-047 salvo las 3 de abajo) y el despliegue están cerrados. Quedan:

1. 🟢 **Tablaturas** (UI de `TabLine`, ya modelado): editor para meter tabs + render en la partitura.
   Es la última feature grande de Fase 5. Autónoma (código → test → deploy).
2. 🔵 **T-046 Login con Google** — requiere acción del usuario: crear OAuth en Google Cloud + activar
   el provider en Supabase (redirect `https://fwynfifvtthtpzpejfhb.supabase.co/auth/v1/callback`).
   El botón ya está en el front. Pasos en `ROADMAP.md`.
3. ✉️ **T-047 Emails con marca** — Supabase → Authentication → Email Templates (acción del usuario).
4. 🛠️ **Pulir detalles** (lo que pidió el usuario tras las features): repaso fino de UX/textos/estados.

> ⚠️ `run_checks` puede fallar el e2e de forma intermitente (T-042); reintentar.
> ⚠️ Seguridad: rotar `sb_secret_` y contraseña de Postgres (compartidas en chat).
> 🧬 El molde vive en el repo hermano `../app-skeleton` (extraído, plantillado, verificado + cookiecutter).
> 🤖 Importar con IA usa OpenRouter gratuito (`OPENROUTER_MODEL`); si el modelo se satura, cambiarlo
> por otro `:free` en las env vars de Vercel.

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

**Seguridad menor:** T-030 SRI en el CDN de Supabase · T-032 auditoría service_role · T-031 ventana
de gracia del caché de token acotada (TTL+gracia, no ilimitada).

**UX:** T-041 avisos de fallo de carga · T-021 a11y · T-017 toasts/modales · T-022 cache-busting
automático por hash. **Sync:** T-019 auto-scroll anclado · T-040 findActiveChord casos borde.
**Molde (Fase M completa):** T-M01..M06 + guía de uso + generador `create_app.py`.

**Fase 6 (despliegue):** Paso 1 Supabase · Paso 2 Postgres · Paso 3 Vercel — **app en vivo**.

**Fase 5 (producto, EN VIVO):** T-045 importar desde URL con IA (OpenRouter gratuito + Jina) ·
responsive móvil/tablet · PWA instalable · export PDF · **setlists/repertorios** (CRUD + reproducir
en orden con barra ◀▶ en el reproductor).

> Estado de calidad ChordFlow: ~49 unit + ~30 e2e en verde (algunas parametrizadas). Alembic head
> `3684ab6335e8` (local + Postgres producción). **App desplegada y verificada en vivo.**
> Pendiente: Tablaturas (🟢), Google login (🔵 acción usuario), emails con marca (✉️), pulir detalles.
