# CLAUDE.md — Reglas maestras de BandFlow

> Este archivo lo lee el agente (Claude Code) al empezar cada sesión.
> Es la **fuente de verdad operativa**: cómo trabajar, cómo verificar y qué nunca romper.
> Producto: **GIRO V2 a SaaS de gestión de bandas** (multi-tenant). La dirección y el detalle
> funcional son la fuente de verdad de producto:
> [GUIA_MAESTRA_V2.md](GUIA_MAESTRA_V2.md) (decisiones del giro) +
> [GUIA_MAESTRA_V2_FUNCIONAL.md](GUIA_MAESTRA_V2_FUNCIONAL.md) (las 14 áreas resueltas, roadmap
> 7–21, convenciones §C.4, detalle Fase 7 §C.5, diagrama §C.6).
> La [GUIA_MAESTRA.md](GUIA_MAESTRA.md) original describe el producto previo (teleprompter), que
> sigue siendo la "joya" intacta dentro del nuevo flujo.

---

## 1. Qué es esto

BandFlow es un **SaaS de gestión para bandas** (multi-tenant colaborativo): identidad de banda,
repertorio y setlists compartidos, agenda de eventos, finanzas con división y chat. La **joya
original** —teleprompter que reproduce acordes resaltando el activo según el BPM con auto-scroll—
sigue intacta dentro del flujo. Backend **FastAPI + SQLAlchemy** (SQLite local / Postgres en prod);
frontend **HTML/CSS/JS vanilla**; auth con **Supabase**.

**Estado (giro V2):** las **Fases 7–13 están COMPLETAS y EN PRODUCCIÓN** desde 2026-06-16 (app shell
BandFlow, espacio de banda con pestañas, vistas agregadas TÚ, biblioteca unificada, reskin y
rebranding visible). Lo nuevo arranca desde el roadmap **posterior a la Fase 13**. Ver las guías V2
y `harness/ROADMAP.md`. (El repo, la URL y los env siguen como `chordflow` — marca técnica, no de cara al usuario.)
⚠️ **Regla nueva de oro multi-tenant:** cada ruta de banda valida pertenencia+rol y filtra por
`band_id`; un fallo = fuga de datos entre bandas. Por eso **cada ruta de banda exige su test de
aislamiento** ("usuario ajeno → 403/404"), tan obligatorio como el doctor verde.

---

## 2. El bucle de trabajo (OBLIGATORIO)

Todo cambio sigue estos 7 pasos. No se salta ninguno.

1. **Elegir tarea** en `harness/ROADMAP.md` (la de mayor prioridad pendiente).
2. **Abrir la tarea** en `harness/TASKS.md` usando `harness/templates/TASK_TEMPLATE.md`.
3. **Implementar** respetando las convenciones (sección 4).
4. **Arrancar el doctor**: `python harness/doctor.py` → debe quedar **todo verde**.
5. **Verificar con Playwright**: escribir/actualizar el test que cubre el cambio en
   `tests/` y correr `python harness/run_checks.py` → verde.
6. **Registrar** en `REGISTRO_DE_CAMBIOS.md` (qué, por qué, cómo, verificación).
7. **Cerrar**: marcar `[x]` en `ROADMAP.md` y mover la tarea a "Hechas" en `TASKS.md`.

> **Regla de oro:** una tarea NO está terminada hasta que `doctor.py` está verde
> **y** existe un test automatizado que prueba el comportamiento nuevo.

### Revisión al cerrar una SECCIÓN/FASE (nuevo)

Además del bucle por tarea, **al terminar una sección/fase completa** (p. ej. la Fase 7) se hace
una **revisión de la app** para ver las integraciones hechas:

1. `python harness/revision.py <sección>` → muestra qué rutas API y páginas están integradas
   (✅) y cuáles faltan (⛔), más el checklist de esa sección.
2. `python harness/revision.py <sección> --serve` → arranca la app en modo test para
   **revisarla a ojo** en el navegador (incluida la verificación de **aislamiento multi-tenant**).
3. Anotar el veredicto en `harness/REVISIONES.md` (plantilla en `templates/REVISION_TEMPLATE.md`).

> Una **fase no se da por cerrada** hasta tener su revisión con veredicto ✅ en `REVISIONES.md`
> (junto al doctor verde y los tests).

---

## 3. Comandos

```bash
# Instalar dependencias (una vez)
python -m pip install -r requirements.txt
python -m pip install -r requirements-dev.txt
python -m playwright install chromium

# Arrancar la app (desarrollo)
python -m uvicorn src.main:app --reload
#   Biblioteca:  http://127.0.0.1:8000/static/library.html

# Comprobar salud del entorno + smoke test (el "iniciador")
python harness/doctor.py

# Suite completa de calidad (lint + unit + e2e)
python harness/run_checks.py

# Revisión de integraciones por sección (al cerrar una fase) + verla en el navegador
python harness/revision.py                 # resumen: qué hay integrado y qué falta
python harness/revision.py fase7 --serve   # detalle de una sección + arrancar la app

# Solo una capa
python -m pytest tests/unit -m unit
python -m pytest tests/e2e  -m e2e
python -m ruff check .
python -m black .

# Migraciones de esquema (Alembic, T-011). La URL sale de DATABASE_URL.
python -m alembic upgrade head                 # aplicar migraciones a la BD
python -m alembic revision --autogenerate -m "mensaje"   # crear migración desde los modelos
python -m alembic check                        # ¿hay drift entre modelos y migraciones?
python -m alembic stamp head                   # marcar una BD existente como "al día" (adopción)
```

> ⚠️ Tras tocar `src/services/models.py`: crear una migración (`revision --autogenerate`),
> revisar el SQL generado y correr `alembic check` (debe decir "no new upgrade operations").
> SQLite necesita `render_as_batch` (ya configurado en `env.py`) para `ALTER TABLE`.

---

## 4. Convenciones que NUNCA se rompen

### Backend (`src/`)
- Endpoints en `src/api/`, lógica y datos en `src/services/`.
- Errores → `HTTPException` con código HTTP estándar (400/401/404/500).
- **Logging** con `logging` a `logs/app.log`. Nunca `print()` para diagnóstico.
- Secretos en `.env` / `.env.local`. La `service_role` key **jamás** al frontend ni a git.
- Toda ruta de `/songs` exige `Depends(get_current_user)` y filtra por `owner_id`.

### Frontend (`static/`)
- **Cache-busting AUTOMÁTICO (T-022)**: el `?v=` de los `.html` es un **hash del contenido**.
  Tras cambiar un `.js`/`.css`, ejecutar **`python harness/cachebust.py`** (reescribe los `?v=`).
  El test `test_cache_busting_al_dia` falla si te olvidas → ya no se sube el número a mano.
- `score_render.js` es el **único** renderer de partituras (player + preview del editor).
- El motor (`sync_engine.js`) trabaja con **ids** de acorde, no nombres → transposición
  y diagramas no afectan la sincronización.
- **Escapar siempre** el texto del usuario antes de meterlo en el DOM (XSS).

---

## 5. Modo test (cómo los tests entran sin Supabase)

La app exige login. Para automatizar, existe un **modo test** activado por variable de
entorno; en producción está apagado y el comportamiento es el normal.

- Backend: si `CHORDFLOW_TEST_MODE=1`, `get_current_user` devuelve un usuario fijo de
  prueba sin llamar a Supabase. `/config` expone `test_mode: true`.
- Frontend: `auth.js` lee `/config`; si `test_mode`, devuelve una sesión de prueba y no
  usa el SDK de Supabase (login, guards y `apiFetch` funcionan igual).
- Usuario de prueba: `id = 00000000-0000-0000-0000-000000000000` (UUID nil, 36 chars: cabe en
  `VARCHAR(36)` también en Postgres).

El harness (`doctor.py`, `conftest.py`) arranca el servidor con este flag y una **BD
temporal** (`DATABASE_URL` apuntando a un sqlite desechable), nunca tocando `chordflow.db`.

⚠️ **El modo test JAMÁS debe activarse en producción.** Es solo para tests locales/CI.

---

## 5.bis Despliegue (EN PRODUCCIÓN)

La app está **en vivo con el giro V2 COMPLETO** (Fases 5/6 + 7–13, marca **BandFlow** visible):
https://chordflow-ecru.vercel.app — **Vercel** (`api/index.py` ASGI + `vercel.json`) + **Supabase**
(auth) + **Postgres de Supabase** (BD, head `7022a3162284`). Repo GitHub privado
`kabalah314-ux/chordflow` rama `main` → **auto-deploy en cada push**. Local sigue en **SQLite**
(sin `DATABASE_URL` en `.env.local`); producción usa Postgres vía env vars de Vercel.

- Migraciones a Postgres: aplicar con el **pooler de sesión** (puerto 5432); el runtime usa el de
  **transacción** (6543). La conexión directa `db.<ref>.supabase.co` es IPv6-only y no resuelve.
- `OPENROUTER_API_KEY`/`OPENROUTER_MODEL` (importar con IA), `OPENROUTER_MODEL` gratuito configurable.
- Detalle y estado en `REGISTRO_DE_CAMBIOS.md` §"Estado actual" y en `harness/TASKS.md`.

---

## 6. Mapa rápido

| Necesito… | Archivo |
|-----------|---------|
| Dirección de producto **vigente (V3)** | `GUIA_MAESTRA_V3.md` (red musical + plano público; D1–D8; fases V3-F1→F11) |
| Dirección de producto (giro V2, base) | `GUIA_MAESTRA_V2.md` + `GUIA_MAESTRA_V2_FUNCIONAL.md` |
| Iconos SVG / helpers de UI | `static/icons.js` (`bfIcon`, `bfEmpty`) |
| Hoja de ruta priorizada | `harness/ROADMAP.md` |
| Tarea en curso | `harness/TASKS.md` |
| Qué flujos deben funcionar siempre | `harness/CHECKLIST_E2E.md` |
| Comprobar que todo arranca | `harness/doctor.py` |
| Correr toda la calidad | `harness/run_checks.py` |
| Revisar integraciones por sección + ver la app | `harness/revision.py` |
| Registro de revisiones por sección | `harness/REVISIONES.md` |
| Endpoints (canciones) | `src/api/songs_router.py` |
| Endpoints (repertorios) | `src/api/setlists_router.py` |
| Endpoints (bandas / invitar / perfil) | `src/api/bands_router.py` · `invites_router.py` · `profile_router.py` |
| Endpoints (repertorio/setlists de banda) | `src/api/band_songs_router.py` · `band_setlists_router.py` |
| Endpoints (agenda / finanzas / chat) | `src/api/events_router.py` · `finance_router.py` · `messages_router.py` |
| Endpoints (vistas agregadas TÚ) | `src/api/me_router.py` (`/me/dashboard·events·balances·conversations`) |
| Auth multi-tenant / cálculo de saldos | `src/services/band_auth.py` · `src/services/balances.py` |
| App shell + sistema de diseño | `static/shell.js` · `shell.css` · `design-system.css` |
| Inicio / espacio de banda / agregadas (front) | `static/app.html`+`home.js` · `band.html`+`band.js` · `agenda/finanzas/chat.js` |
| Importar desde URL con IA | `src/api/import_router.py` + `src/services/importer.py` |
| Tablas / columnas | `src/services/models.py` |
| Validación / forma JSON | `src/services/schemas.py` |
| Config validada (env) | `src/services/config.py` |
| Reproducción / sincronización | `static/sync_engine.js` |
| Render del player + preview | `static/score_render.js` |
| Parser de importación / editor | `static/editor.js` |
| Repertorios (front) | `static/setlists.html` / `static/setlists.js` |
| Cache-busting (hash) | `harness/cachebust.py` (ejecutar tras tocar js/css) |
| PWA | `static/manifest.json` / `static/sw.js` |
| Auth (front) | `static/auth.js` / Auth (back) `src/services/auth.py` + `auth_provider.py` |
| Despliegue (Vercel) | `vercel.json` / `api/index.py` / `.vercelignore` |
