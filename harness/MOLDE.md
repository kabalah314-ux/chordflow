# 🧬 MOLDE — Esqueleto reutilizable para futuras apps

> Documento de diseño y constancia. Explica **qué de ChordFlow es reutilizable**, cómo se
> extrae a un molde, y cómo nace un proyecto nuevo a partir de él.
> Tareas asociadas: **T-M01 … T-M06** en [`ROADMAP.md`](ROADMAP.md) (Fase M).
> Estado: **MOLDE EXTRAÍDO Y PLANTILLADO** (T-M02 + T-M03, 2026-06-13). El esqueleto vive en el
> repo hermano `../app-skeleton` (commits `e02b1b0`, `5e14adf`) con recurso `Item`; docs con huecos
> `{{...}}` y prefijo de env como una sola perilla (`env_prefix`). `run_checks` TODO VERDE recién
> copiado (doctor + ruff + 27 unit + 4 e2e). Inventario validado en T-M01. **Molde estable
> VERIFICADO** (T-M06): copia limpia vía `git archive` → run_checks TODO VERDE sin tocar nada.
> Pendiente: T-M04 (guía de uso, casi cubierta por README+MOLDE), T-M05 (cookiecutter, opcional).

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

> **Validado en T-M01 (2026-06-13)** contra el árbol real. Las filas marcadas «(nuevo desde el
> diseño)» se añadieron tras construir T-011/T-014/T-016/T-039/T-043/T-044.

### 2.1 Harness y raíz
| Archivo / carpeta | Capa | En el molde queda… |
|---|---|---|
| `harness/doctor.py` | **Universal** | igual (algún check parametrizado por nombre de app; añadir check de `/health`) |
| `harness/run_checks.py` | **Universal** | igual |
| `harness/ROADMAP.md` | **Universal (plantilla)** | Fase 0–2 genérica + huecos |
| `harness/TASKS.md` + `templates/` | **Universal** | igual |
| `harness/CHECKLIST_E2E.md` | **Universal (plantilla)** | solo filas genéricas (smoke, auth, CRUD) |
| `harness/MOLDE.md` | **Universal** | este documento (guía de uso del molde) |
| `CLAUDE.md` | **Universal (plantilla)** | huecos `{{APP_NAME}}`, `{{STACK}}`, `{{ENV_PREFIX}}` |
| `GUIA_MAESTRA.md` | **Plantilla** | esqueleto de secciones a rellenar |
| `pyproject.toml` | **Universal** | igual (ruff/black/pytest) |
| `requirements.txt` / `-dev.txt` | **Universal** | **pineado** (T-008); incluye `pydantic-settings`, `alembic` |
| `.gitignore` / `.gitattributes` | **Universal** | igual |
| `.env` / `.env.local` | **Universal** | `.env.example` con claves vacías (ver §4) |
| `alembic.ini` + `alembic/env.py` + `script.py.mako` | **Universal (nuevo)** | infra de migraciones (T-011); URL de `DATABASE_URL`, `render_as_batch` |
| `alembic/versions/*` | **Dominio (nuevo)** | el molde trae solo el baseline del `Item`, no los de `Song` |

### 2.2 Backend (`src/`)
| Archivo | Capa | En el molde queda… |
|---|---|---|
| `src/main.py` | **Universal (base)** | app FastAPI, CORS por env, static, `/config`, `/health`, **handler de errores global** (T-044) |
| `src/services/db.py` | **Universal** | engine + `get_db` + `PRAGMA foreign_keys` (T-003) |
| `src/services/config.py` | **Universal (nuevo)** | `Settings` pydantic-settings (T-016) — config validada. *(En el diseño se llamó `settings.py`; el real es `config.py`.)* |
| `src/services/logging_config.py` | **Universal (nuevo)** | `setup_logging()` una vez + stdout cloud (T-014) |
| `src/services/auth.py` | **Universal** | `get_current_user` con modo test + caché TTL/lock/degradación (agnóstico al IdP) |
| `src/services/auth_provider.py` | **Universal (nuevo)** | `AuthProvider` + `SupabaseAuthProvider` + factoría (T-043) |
| `src/services/models.py` | **Dominio** | reemplazar `Song/Section/...` por `Item` de ejemplo |
| `src/services/schemas.py` | **Dominio (patrón)** | `ItemBase/Create/Update/Response/Summary` |
| `src/api/songs_router.py` | **Dominio (patrón)** | → `items_router.py`: CRUD + auth + filtro por `owner_id` + soft delete + paginación |

### 2.3 Frontend (`static/`)
| Archivo | Capa | En el molde queda… |
|---|---|---|
| `static/auth.js` | **Universal** | login, guards, `apiFetch` (401→login), modo test |
| `static/util.js` | **Universal (nuevo)** | `escapeHtml` canónico (T-039) |
| `static/login.html` + `login.js` | **Universal (plantilla)** | flujo de login (branding aparte) |
| `static/style.css` | **Mixto** | extraer tokens (`--accent`, glass) como base estética opcional |
| `static/library.*`, `index.html`, `editor.*`, `app.js`, `sync_engine.js`, `score_render.js`, `chord_shapes.js` | **Dominio** | la UI de partituras NO va al molde |

### 2.4 Tests
| Archivo | Capa | En el molde queda… |
|---|---|---|
| `tests/conftest.py` | **Universal** | fixtures `client` + `live_server` + `api` + modo test + BD temporal |
| `tests/unit/test_security.py` | **Universal** | CORS, caché de token, cabeceras, handler global |
| `tests/unit/test_config.py` | **Universal (nuevo)** | validación de `Settings` |
| `tests/unit/test_logging_config.py` | **Universal (nuevo)** | logging único + stdout |
| `tests/unit/test_auth_provider.py` | **Universal (nuevo)** | provider enchufable |
| `tests/unit/test_migrations.py` | **Universal (infra)** | `upgrade head` + `check` (sobre el esquema del `Item`) |
| `tests/e2e/test_smoke.py` | **Universal** | carga sin errores JS + 401 + `/config` |
| `tests/unit/test_api_songs.py` | **Plantilla** | → `test_items.py`: CRUD + aislamiento por dueño + soft delete |
| `tests/e2e/test_{editor,js_logic,library,player}.py` | **Dominio** | tests de la UI de partituras |

**Resumen del esqueleto que comparten TODAS las apps:**
1. El **harness** completo (doctor, run_checks, roadmap/tasks, checklist, plantillas).
2. El **bucle de trabajo** de `CLAUDE.md` (los 7 pasos) y la división GUIA vs CLAUDE.
3. El **arranque backend**: FastAPI + SQLAlchemy + `get_db` + `Settings` + logging único + CORS por
   env + `/health` + handler de errores global + migraciones Alembic.
4. La **auth con modo test** + **proveedor de identidad enchufable** (Supabase como una impl).
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
├── CLAUDE.md                 # plantilla con {{APP_NAME}}, {{DESCRIPTION}}, {{STACK}}, {{ENV_PREFIX}}
├── GUIA_MAESTRA.md           # esqueleto de secciones
├── REGISTRO_DE_CAMBIOS.md    # vacío con cabecera
├── .gitignore  .gitattributes
├── .env.example              # DATABASE_URL, LOG_LEVEL, {{PREFIX}}_LOG_STDOUT,
│                             #   {{PREFIX}}_ALLOWED_ORIGINS, {{PREFIX}}_AUTH_PROVIDER,
│                             #   {{PREFIX}}_TOKEN_TTL, SUPABASE_URL/ANON_KEY…
├── pyproject.toml
├── requirements.txt          # PINEADO (incluye pydantic-settings, alembic)
├── requirements-dev.txt      # PINEADO
├── alembic.ini  alembic/      # env.py (URL de DATABASE_URL, batch) + versions/ con baseline de Item
├── harness/                  # doctor, run_checks, ROADMAP, TASKS, CHECKLIST, MOLDE, templates/
├── src/
│   ├── main.py               # app + CORS(env) + static + /config + /health + handler errores global
│   ├── api/
│   │   └── items_router.py   # CRUD de ejemplo (Item): auth + filtro owner + soft delete + paginación
│   └── services/
│       ├── config.py         # pydantic-settings (Settings validado)
│       ├── logging_config.py # setup_logging() una vez + stdout cloud
│       ├── db.py             # engine + get_db + PRAGMA foreign_keys ON
│       ├── auth.py           # get_current_user con modo test + caché (agnóstico al IdP)
│       ├── auth_provider.py  # AuthProvider + SupabaseAuthProvider + factoría
│       ├── models.py         # Item de ejemplo (id, owner_id, deleted_at, timestamps)
│       └── schemas.py        # ItemBase/Create/Update/Response + ItemSummary
├── static/
│   ├── auth.js  util.js      # universal (apiFetch/guards/modo test; escapeHtml)
│   ├── login.html  login.js  # flujo de login (branding aparte)
│   └── style.css             # tokens base (opcional)
└── tests/
    ├── conftest.py           # fixtures universales
    ├── unit/
    │   ├── test_items.py     # CRUD + aislamiento por dueño + soft delete
    │   ├── test_security.py  test_config.py  test_logging_config.py  test_auth_provider.py
    │   └── test_migrations.py
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
