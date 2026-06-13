# 🧬 MOLDE — Esqueleto reutilizable para futuras apps

> Documento de diseño y constancia. Explica **qué de ChordFlow es reutilizable**, cómo se
> extrae a un molde, y cómo nace un proyecto nuevo a partir de él.
> Tareas asociadas: **T-M01 … T-M06** en [`ROADMAP.md`](ROADMAP.md) (Fase M).
> Estado: **DISEÑO** (no ejecutado todavía). Pre-requisito para extraer: T-001…T-005 hechos.

---

## 1. Idea

Tu activo más valioso no es ChordFlow: es el **sistema de trabajo + el esqueleto técnico**.
El molde captura eso una sola vez para que cada proyecto nuevo arranque **estable, testeado y
con reglas claras** desde el minuto 1. Filosofía en dos capas:

- **Capa UNIVERSAL (el molde):** todo lo agnóstico al dominio. Se copia tal cual a cada app nueva.
- **Capa de DOMINIO (por proyecto):** los modelos, schemas, lógica y frontend concretos. Lo único
  que cambias en cada proyecto.

> Regla del molde: si un archivo menciona "song", "chord", "BPM" o cualquier concepto del producto,
> es **dominio**. Si solo sabe de "un recurso con dueño, CRUD, auth, tests", es **universal**.

---

## 2. Inventario: qué es universal y qué es por-proyecto

| Archivo / carpeta | Capa | En el molde queda… |
|---|---|---|
| `harness/doctor.py` | **Universal** | igual (algún check parametrizado por nombre de app) |
| `harness/run_checks.py` | **Universal** | igual |
| `harness/ROADMAP.md` | **Universal (plantilla)** | con la Fase 0–2 genérica + huecos |
| `harness/TASKS.md` + `templates/` | **Universal** | igual |
| `harness/CHECKLIST_E2E.md` | **Universal (plantilla)** | solo las filas genéricas (smoke, auth, CRUD) |
| `harness/MOLDE.md` | **Universal** | este documento (guía de uso del molde) |
| `CLAUDE.md` | **Universal (plantilla)** | con huecos `{{APP_NAME}}`, `{{STACK}}`, etc. |
| `GUIA_MAESTRA.md` | **Plantilla** | esqueleto de secciones a rellenar por proyecto |
| `pyproject.toml` | **Universal** | igual (ruff/black/pytest config) |
| `requirements.txt` / `-dev.txt` | **Universal** | **pineado** (deuda T-008 ya resuelta en el molde) |
| `.gitignore` | **Universal** | igual |
| `.env` / `.env.local` (ejemplos) | **Universal** | `.env.example` con claves vacías |
| `src/main.py` | **Universal (base)** | app FastAPI, CORS por env, static, `/config`, `/health` |
| `src/services/db.py` | **Universal** | engine + `get_db` + `PRAGMA foreign_keys` (T-003 ya resuelto) |
| `src/services/auth.py` | **Universal** | auth con modo test; Supabase **opcional/desacoplado** |
| `src/services/settings.py` | **Universal (nuevo)** | `pydantic-settings` (T-016) — config validada |
| `tests/conftest.py` | **Universal** | fixtures `client` + `live_server` + `api` + modo test |
| `tests/e2e/test_smoke.py` | **Universal** | smoke + auth 401 + `/config` |
| `tests/unit/test_*_resource.py` | **Plantilla** | CRUD + aislamiento por dueño sobre `Item` |
| `src/services/models.py` | **Dominio** | reemplazar `Song/Section/...` por tu modelo |
| `src/services/schemas.py` | **Dominio** | tus schemas |
| `src/api/*_router.py` | **Dominio (patrón)** | CRUD genérico de ejemplo (`items_router.py`) |
| `static/*` (player, editor, sync_engine, score_render, chord_shapes) | **Dominio** | tu UI |
| `static/auth.js` | **Universal** | igual (login, guards, `apiFetch`, modo test) |
| `static/style.css` (tokens base) | **Mixto** | extraer variables (`--accent`, glass) como base |

**Resumen del esqueleto que comparten TODAS las apps:**
1. El **harness** completo (doctor, run_checks, roadmap/tasks, checklist, plantillas).
2. El **bucle de trabajo** de `CLAUDE.md` (los 7 pasos) y la división GUIA vs CLAUDE.
3. El **arranque backend**: FastAPI + SQLAlchemy + `get_db` + settings + CORS por env + `/health`.
4. La **auth con modo test** (bypass por env var + usuario fijo) → tests sin proveedor externo.
5. El **scaffolding de tests** (conftest con server real y BD temporal, smoke + CRUD + aislamiento).
6. La **higiene**: `.gitignore`, pyproject (ruff/black/pytest), deps pineadas, `.env.example`.

---

## 3. Alcance recomendado del molde

Decisión (puedes ajustarla): el molde será **"backend genérico con auth desacoplada"**, no un
clon exacto de ChordFlow. Motivos:
- El harness y el backend base sirven a **cualquier** app web tuya.
- Atar el molde a Supabase limita; mejor **auth como pieza enchufable** (modo test siempre;
  Supabase como una implementación opcional que se activa por env var).
- El frontend de ChordFlow (partituras) es 100% dominio → **no** va al molde, salvo `auth.js` y los
  tokens de estilo (glassmorphism) como base estética opcional.

Así, el molde cubre el **80% repetitivo** (estructura, tests, auth, config, reglas) y cada app
aporta solo su dominio.

---

## 4. Estructura propuesta de `app-skeleton/`

```
app-skeleton/
├── CLAUDE.md                 # plantilla con {{APP_NAME}}, {{DESCRIPTION}}, {{STACK}}
├── GUIA_MAESTRA.md           # esqueleto de secciones
├── REGISTRO_DE_CAMBIOS.md    # vacío con cabecera
├── .gitignore
├── .env.example              # DATABASE_URL, LOG_LEVEL, CHORDFLOW_ALLOWED_ORIGINS, AUTH_PROVIDER…
├── pyproject.toml
├── requirements.txt          # PINEADO
├── requirements-dev.txt      # PINEADO
├── harness/                  # doctor, run_checks, ROADMAP, TASKS, CHECKLIST, MOLDE, templates/
├── src/
│   ├── main.py               # app + CORS(env) + static + /config + /health
│   ├── api/
│   │   └── items_router.py   # CRUD genérico de ejemplo (Item) con auth + filtro por owner
│   └── services/
│       ├── settings.py       # pydantic-settings (config validada)
│       ├── db.py             # engine + get_db + PRAGMA foreign_keys ON
│       ├── auth.py           # get_current_user con modo test + provider enchufable
│       ├── models.py         # Item de ejemplo (id, owner_id, deleted_at, timestamps)
│       └── schemas.py        # ItemBase/Create/Update/Response + ItemSummary
├── static/
│   ├── auth.js               # universal
│   └── style.css             # tokens base (opcional)
└── tests/
    ├── conftest.py           # fixtures universales
    ├── unit/test_items.py    # CRUD + aislamiento por dueño
    └── e2e/test_smoke.py     # carga sin errores + 401 + /config
```

El recurso de ejemplo `Item` demuestra el patrón completo (modelo con `owner_id`/`deleted_at`/
timestamps, schemas, router CRUD con auth, tests) sin acoplarse a ningún dominio. En una app nueva
se renombra `Item` → tu entidad y se construye desde ahí.

---

## 5. Cómo nace un proyecto nuevo desde el molde

1. Copiar `app-skeleton/` → `mi-app-nueva/`.
2. Rellenar los huecos `{{...}}` de `CLAUDE.md` y `GUIA_MAESTRA.md` (nombre, descripción, stack).
3. `python -m pip install -r requirements.txt -r requirements-dev.txt`.
4. `python harness/doctor.py` → **debe quedar verde sin tocar código** (criterio T-M06).
5. Renombrar `Item` → tu entidad de dominio en `models/schemas/router` y sus tests.
6. Empezar el bucle de trabajo de `CLAUDE.md` desde la primera tarea del ROADMAP.

---

## 6. Formato del molde: dos caminos

- **(A) Repo plantilla** *(recomendado para empezar)*: `app-skeleton/` que se copia a mano.
  Cero magia, cero mantenimiento, funciona ya. → tareas T-M02…T-M04.
- **(B) `create_app.py` tipo cookiecutter** *(después)*: un script pregunta nombre/descr./auth y
  genera el proyecto con los huecos rellenos. Más cómodo a escala. → tarea T-M05 (opcional).

Recomendación: hacer **(A)** primero (valor inmediato), y subir a **(B)** cuando tengas 2–3 apps y
el patrón esté probado.

---

## 7. Cómo evoluciona el molde (el bucle que pediste)

Cada vez que en **cualquier** proyecto descubras un patrón bueno y genérico (como tu "modo test"),
**promuévelo al molde**: añádelo a `app-skeleton/` y anota una línea en su `REGISTRO_DE_CAMBIOS`.
Así el molde "saca lo mejor de cada proyecto" y mejora con el tiempo, en vez de quedarse fijo.

> Criterio de **molde estable** (T-M06): proyecto recién generado desde el molde → `doctor.py`
> verde y `run_checks.py` (al menos unit + smoke) verde, **sin escribir una línea de dominio**.
