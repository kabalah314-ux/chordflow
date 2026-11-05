# BandFlow

Gestión para bandas de música: agenda con asistencia y votación de fechas, repertorio y setlists,
reproductor de acordes que avanza solo al tempo (la "joya"), finanzas con reparto, chat, y una red
profesional (salas que publican bolos, profesionales, candidaturas con dossier).

- **Producción:** https://chordflow-ecru.vercel.app (Vercel + Supabase Auth + Postgres de Supabase).
- **Guía vigente:** [`GUIA_MAESTRA_V6.md`](GUIA_MAESTRA_V6.md) (qué y por qué) y
  [`GUIA_MAESTRA_V6_MANUAL.md`](GUIA_MAESTRA_V6_MANUAL.md) (paso a paso). Las anteriores son historial.
- **Normas de trabajo del agente:** [`CLAUDE.md`](CLAUDE.md). **Registro:** [`REGISTRO_DE_CAMBIOS.md`](REGISTRO_DE_CAMBIOS.md).

## Arrancar en local

```bash
python -m pip install -r requirements.txt -r requirements-dev.txt
python -m playwright install chromium
python -m uvicorn src.main:app --reload        # http://127.0.0.1:8000
python harness/doctor.py                        # salud del entorno + smoke
python harness/run_checks.py                    # lint + unit + e2e
```

Local usa SQLite (sin `DATABASE_URL`). Los tests arrancan la app en **modo test**
(`CHORDFLOW_TEST_MODE=1`, nunca en producción) con una base de datos temporal.

## Estructura

| Carpeta | Qué hay |
|---|---|
| `src/api/` | Routers FastAPI (una ruta de banda = guard de pertenencia + test de aislamiento) |
| `src/services/` | Modelos SQLAlchemy, schemas Pydantic, auth, config, servicios |
| `alembic/versions/` | Migraciones (aditivas; `alembic check` en los tests) |
| `static/` | Frontend vanilla (HTML/CSS/JS). Tras tocar JS/CSS: `python harness/cachebust.py` |
| `tests/unit`, `tests/e2e` | pytest + Playwright |
| `harness/` | doctor, run_checks, cachebust, revisiones, roadmap y tareas |

## Variables de entorno (Vercel)

`DATABASE_URL`, `SUPABASE_URL`, `SUPABASE_ANON_KEY`, `ALLOWED_ORIGINS`, `OPENROUTER_API_KEY`,
`OPENROUTER_MODEL`, `CRON_SECRET` (recordatorios diarios, V6). Nunca `CHORDFLOW_TEST_MODE`.

## Despliegue

Cada push a `main` despliega. Antes de fusionar una rama con migraciones:
`DATABASE_URL=<pooler de sesión, puerto 5432> python -m alembic upgrade head`.
