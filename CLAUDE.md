# CLAUDE.md — Reglas maestras de ChordFlow

> Este archivo lo lee el agente (Claude Code) al empezar cada sesión.
> Es la **fuente de verdad operativa**: cómo trabajar, cómo verificar y qué nunca romper.
> Para entender la arquitectura del producto, ver [GUIA_MAESTRA.md](GUIA_MAESTRA.md).

---

## 1. Qué es esto

ChordFlow es un teleprompter musical: reproduce partituras de acordes resaltando el
acorde activo según el BPM, con auto-scroll. Backend **FastAPI + SQLAlchemy + SQLite**;
frontend **HTML/CSS/JS vanilla**; auth con **Supabase**.

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

# Solo una capa
python -m pytest tests/unit -m unit
python -m pytest tests/e2e  -m e2e
python -m ruff check .
python -m black .
```

---

## 4. Convenciones que NUNCA se rompen

### Backend (`src/`)
- Endpoints en `src/api/`, lógica y datos en `src/services/`.
- Errores → `HTTPException` con código HTTP estándar (400/401/404/500).
- **Logging** con `logging` a `logs/app.log`. Nunca `print()` para diagnóstico.
- Secretos en `.env` / `.env.local`. La `service_role` key **jamás** al frontend ni a git.
- Toda ruta de `/songs` exige `Depends(get_current_user)` y filtra por `owner_id`.

### Frontend (`static/`)
- **Cache-busting `?v=N`**: al cambiar un `.js` o `.css`, subir el número de versión en
  **TODOS** los `.html` que lo referencian, o el navegador sirve la copia vieja.
  (Ya mordió 2 veces. Verificar con grep antes de cerrar la tarea.)
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
- Usuario de prueba: `id = test-user-0000-0000-0000-000000000000`.

El harness (`doctor.py`, `conftest.py`) arranca el servidor con este flag y una **BD
temporal** (`DATABASE_URL` apuntando a un sqlite desechable), nunca tocando `chordflow.db`.

⚠️ **El modo test JAMÁS debe activarse en producción.** Es solo para tests locales/CI.

---

## 6. Mapa rápido

| Necesito… | Archivo |
|-----------|---------|
| Hoja de ruta priorizada | `harness/ROADMAP.md` |
| Tarea en curso | `harness/TASKS.md` |
| Qué flujos deben funcionar siempre | `harness/CHECKLIST_E2E.md` |
| Comprobar que todo arranca | `harness/doctor.py` |
| Correr toda la calidad | `harness/run_checks.py` |
| Endpoints | `src/api/songs_router.py` |
| Tablas / columnas | `src/services/models.py` |
| Validación / forma JSON | `src/services/schemas.py` |
| Reproducción / sincronización | `static/sync_engine.js` |
| Render del player + preview | `static/score_render.js` |
| Parser de importación | `static/editor.js` |
| Auth (front) | `static/auth.js` / Auth (back) `src/services/auth.py` |
