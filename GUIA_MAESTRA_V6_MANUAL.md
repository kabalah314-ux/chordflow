# 🎸 BandFlow — Guía Maestra V6 · Parte II: MANUAL paso a paso (para la IA ejecutora)

> **Qué es:** la receta de cada tarea `T-V6-NN` de la Parte I (`GUIA_MAESTRA_V6.md`, §10).
> Escrito para que una IA menos capaz (o una persona con poca experiencia) pueda hacerlo sin
> adivinar nada: qué archivos abrir, qué cambiar, con qué código, cómo comprobarlo y cómo
> cerrarlo. **La Parte I dice QUÉ y POR QUÉ; esta Parte II dice CÓMO.** Si algo de aquí
> contradice a la Parte I, manda la Parte I y se corrige aquí.
>
> **Estado:** nada está hecho. Las recetas describen cambios PROPUESTOS sobre el código del
> commit `d61f165` (2026-07-05). Si el código ha cambiado desde entonces, los números de línea
> pueden variar: busca por el fragmento de código que se cita, no por el número.

---

## 0. Antes de tocar nada (léelo entero una vez)

### 0.1 Cómo está hecho el proyecto en 10 líneas

1. **Backend** Python 3.12 + FastAPI + SQLAlchemy 2 + Alembic. Entra por `src/main.py`, que monta
   18 routers de `src/api/`. Los modelos (tablas) están en `src/services/models.py` y los esquemas
   de entrada/salida (Pydantic) en `src/services/schemas.py`.
2. **Auth**: Supabase. El front manda `Authorization: Bearer <jwt>`; el back lo valida en
   `src/services/auth.py` (`get_current_user`). Las rutas de banda usan `require_band_member` /
   `require_band_admin` de `src/services/band_auth.py`.
3. **Base de datos**: SQLite en local (`chordflow.db`), Postgres (Supabase) en producción. El
   esquema evoluciona con migraciones Alembic en `alembic/versions/`.
4. **Frontend**: HTML + CSS + JS "vanilla" en `static/` (16 páginas). Sin bundler ni npm. Cada
   página carga sus scripts con `<script src="x.js?v=hash">`. El hash lo escribe
   `python harness/cachebust.py`.
5. **Estilos**: `static/design-system.css` (tokens `--bf-*` y componentes `bf-*`, el sistema
   "bueno"), `static/shell.css` (lateral/topbar), `static/style.css` (legacy del reproductor y
   editor; se va a retirar por partes).
6. **Reproductor**: `static/index.html` + `app.js` + `sync_engine.js` (motor: NO SE TOCA salvo
   que la receta lo diga) + `score_render.js` (render; su contrato DOM no se toca).
7. **Tests**: `tests/unit/` (API con `TestClient`, rápidos) y `tests/e2e/` (Playwright, navegador
   real contra un servidor en modo test). `tests/conftest.py` tiene las fixtures.
8. **Modo test**: `CHORDFLOW_TEST_MODE=1` hace que todo el mundo sea el usuario de prueba
   `00000000-0000-0000-0000-000000000000` (sin Supabase). Solo para tests. Jamás en producción.
9. **Harness**: `python harness/doctor.py` (salud + smoke), `python harness/run_checks.py` (lint +
   unit + e2e = "definición de terminado"), `python harness/revision.py` (integraciones).
10. **Despliegue**: push a `main` → Vercel despliega automáticamente (`api/index.py` +
    `vercel.json`). Las migraciones a producción se aplican a mano (`alembic upgrade head` con la
    `DATABASE_URL` del pooler de sesión, puerto 5432) ANTES del push.

### 0.2 Preparar el entorno (una vez)

```bash
# 1) Clonar / abrir la carpeta del proyecto. En Windows, abrir una terminal en:
#    C:\Users\oscar\Documents\OOOX\03-Experiments\bandflow
# 2) Entorno virtual + dependencias
python -m venv .venv
.venv\Scripts\activate            # Windows   (Linux/Mac: source .venv/bin/activate)
python -m pip install -r requirements.txt -r requirements-dev.txt
python -m playwright install chromium
# 3) Variables de entorno: crear .env.local (NO se sube a git) con las claves públicas de Supabase
#    SUPABASE_URL=https://<ref>.supabase.co
#    SUPABASE_ANON_KEY=<anon key>
#    (sin DATABASE_URL → usa SQLite local chordflow.db)
# 4) Comprobar que todo arranca
python harness/doctor.py          # debe quedar TODO verde
# 5) Arrancar la app en local
python -m uvicorn src.main:app --reload     # http://127.0.0.1:8000
```

Para ver la app con datos de ejemplo sin cuenta de Supabase:

```bash
set CHORDFLOW_TEST_MODE=1 && set DATABASE_URL=sqlite:///./demo_bandflow.db   # Windows (cmd)
python harness/seed_demo.py
python -m uvicorn src.main:app --reload
# abrir http://127.0.0.1:8000/static/app.html  (entras como "Oscar (tú)" con la banda demo)
```

### 0.3 El ritual de CADA tarea (no te saltes pasos)

1. **Lee la receta entera** antes de escribir una línea. Lee también la fila de la tarea en la
   Parte I §10 y los hallazgos que cierra (Parte I §4).
2. **Abre la tarea** en `harness/TASKS.md` copiando `harness/templates/TASK_TEMPLATE.md`
   (título, objetivo, plan, archivos, criterio de aceptación).
3. **Crea una rama** `git checkout -b t-v6-NN-<nombre-corto>` (nunca trabajes en `main`).
4. **Implementa** siguiendo los pasos. Si un paso no encaja con el código que ves, PARA y
   anota la diferencia en TASKS.md; no improvises cambios grandes.
5. Si tocaste `.js` o `.css`: `python harness/cachebust.py`.
6. Si tocaste `src/services/models.py`: migración (§0.5).
7. `python harness/doctor.py` → verde.
8. **Escribe el test** que pide la receta (§0.4) y corre `python harness/run_checks.py --fast`
   (sin e2e) mientras desarrollas; al final `python harness/run_checks.py` completo → verde.
9. **Revisión visual** si la tarea toca UI: abre la página en tema oscuro **y** claro, en
   escritorio **y** a 390 px de ancho (DevTools → modo móvil). Haz una captura de cada una y
   guárdala en `harness/capturas/T-V6-NN/` (carpeta nueva; sí se sube a git, son pequeñas).
10. **Registra** en `REGISTRO_DE_CAMBIOS.md` (qué, por qué, cómo, verificación) y marca `[x]` en
    `harness/ROADMAP.md`; mueve la tarea a "Hechas" en TASKS.md.
11. **Commit** con el mensaje de la receta (formato `tipo(v6): T-V6-NN — qué`), uno por tarea.
12. **Despliegue**: si la tarea lleva migración, aplícala en producción ANTES de mergear (§0.5).
    Mergea a `main` solo con CI verde.

### 0.4 Cómo se escribe un test en este repo

**Unit (API, rápido)** — `tests/unit/test_<tema>.py`:

```python
import pytest
from tests.conftest import sample_song_payload

pytestmark = pytest.mark.unit

def test_algo_concreto(client):          # `client` = TestClient con BD limpia y usuario de prueba
    bid = client.post("/bands/", json={"name": "Mi banda"}).json()["id"]
    r = client.get(f"/bands/{bid}/songs/")
    assert r.status_code == 200
    assert r.json() == []
```

Para actuar como OTRO usuario (ajeno, invitado…), hoy se copia este helper (T-V6-27 lo convierte
en fixture):

```python
import contextlib
from src.main import app
from src.services.auth import get_current_user

@contextlib.contextmanager
def acting_as(user_id):
    app.dependency_overrides[get_current_user] = lambda: user_id
    try:
        yield
    finally:
        app.dependency_overrides.pop(get_current_user, None)

# uso:
with acting_as("99999999-9999-9999-9999-999999999999"):
    assert client.get(f"/bands/{bid}").status_code == 404
```

**E2E (navegador)** — `tests/e2e/test_<tema>.py`:

```python
import pytest

pytestmark = pytest.mark.e2e

def test_la_pagina_hace_x(page, live_server, api):
    # `api` = cliente HTTP autenticado para sembrar datos; `live_server` = URL base
    bid = api.post("/bands/", json={"name": "Banda e2e"}).json()["id"]
    page.goto(f"{live_server}/static/band.html?id={bid}")
    page.click('.bf-tab[data-tab="agenda"]')          # localiza por ids/clases, NUNCA por texto
    page.wait_for_selector("#b-agenda")                 # espera a un estado, no a un tiempo
    assert page.locator("#b-new-event").is_visible()
```

Reglas: localiza por `#id`, `.clase` o `[data-*]`; nunca `:has-text(...)` ni asserts sobre
texto visible (el copy cambia). No uses `page.wait_for_timeout(ms)`: espera a un selector o a
una respuesta (`page.wait_for_response`). Si necesitas IA o red externa, mockéala con
`page.route(...)` (mira `tests/e2e/test_editor.py` como ejemplo).

### 0.5 Cómo se hace una migración

```bash
# 1) Edita src/services/models.py (añade columnas/tablas; NUNCA borres sin tarea explícita)
# 2) Genera la migración
python -m alembic revision --autogenerate -m "t-v6-NN descripcion corta"
# 3) ABRE el archivo generado en alembic/versions/ y revísalo:
#    - solo debe contener lo que cambiaste
#    - en booleanos usa sa.false()/sa.true() como server_default, nunca sa.text('0')
#    - en SQLite los ALTER van en batch (ya configurado con render_as_batch)
# 4) Aplica en local y comprueba que no hay drift
python -m alembic upgrade head
python -m alembic check          # debe decir "No new upgrade operations detected"
# 5) Baja y sube una vez para probar el downgrade
python -m alembic downgrade -1 && python -m alembic upgrade head
# 6) En producción (ANTES del push a main), con la URL del POOLER DE SESIÓN (puerto 5432):
#    set DATABASE_URL=postgresql://...:5432/postgres    (solo en esa terminal; ciérrala después)
#    python -m alembic upgrade head
#    ⚠️ NO ejecutes pytest en esa misma terminal (T-V6-02 lo hace imposible, pero hasta entonces: cuidado)
```

### 0.6 Reglas de oro (si dudas, esto gana)

1. **No borres ni renombres `id`, clases `data-*` ni ids `#b-*`, `#sl-*`, `#btn-*`, `#tx-*`,
   `#ev-*`** que usan los tests (Anexo A de este manual lista cuáles usa cada test). Puedes
   cambiar el HTML de alrededor, los estilos y el texto.
2. **No toques `static/sync_engine.js`** ni las clases/ids que pinta `score_render.js`
   (`.chord-container`, `.chord-pill`, `.active`, `.line-lyric`, `.section-name`, `#chord-*`,
   `#score-*`) salvo que la receta diga explícitamente que sí.
3. **Escapa SIEMPRE** el texto del usuario antes de meterlo en `innerHTML`: `escapeHtml(x)`.
4. **Colores, radios, sombras y tamaños solo con tokens `--bf-*`.** Nada de `#hex`/`rgba(` nuevos
   fuera de `:root`.
5. **Nada de emoji** en botones, títulos, menús, placeholders o etiquetas. Usa `bfIcon('nombre')`.
   Emoji solo en texto que escribe el usuario.
6. **Toda ruta nueva de banda** lleva `Depends(require_band_member)` o `require_band_admin`, y un
   test "usuario ajeno → 404/403" y otro "guest → 403" si escribe.
7. **Nunca un secreto en el repo** (claves, contraseñas, tokens, emails personales). Ni en docs.
8. **Un commit por tarea.** Si te desvías para arreglar otra cosa, anótalo en TASKS.md como
   tarea nueva y sigue con la tuya.
9. **No cambies la API** (nombres de rutas, forma del JSON) sin que la receta lo diga: el front
   y los tests dependen de ella.
10. **Si no puedes verificar, no está hecho.** Un cambio sin test ni captura no se cierra.

### 0.7 Si algo falla

- **`doctor.py` rojo**: lee la primera línea roja; suele ser `.env.local` incompleto, puerto 8000
  ocupado o Playwright sin Chromium (`python -m playwright install chromium`).
- **Un e2e falla solo a veces** (flaky): mira si usa `wait_for_timeout`; cámbialo por una espera
  de selector/respuesta. Si no es tuyo, anótalo y sigue.
- **`alembic check` dice que hay cambios**: tu migración no refleja los modelos; regenera con
  `--autogenerate` sobre una BD limpia (`del chordflow.db` en local).
- **Windows y rutas**: usa `/` en Python (`Path`), y en bash de Windows cuidado con `set` vs
  `export`.
- **Necesitas decidir algo de producto**: no decidas tú. Escribe en TASKS.md "DECISIÓN PENDIENTE:
  <pregunta> · Opción A (recomendada): … · Opción B: …" y pasa a otra tarea que no dependa de ello.

### 0.8 Formato de los mensajes de commit

```
tipo(v6): T-V6-NN — qué se ha hecho en una línea

- detalle 1 (archivo o comportamiento)
- cierra: S-01, F-02   (ids de la Parte I §4)
- tests: tests/unit/test_x.py::test_y, tests/e2e/test_z.py
```

`tipo` ∈ `fix` (bug), `feat` (funcionalidad), `refactor`, `style` (solo CSS/visual), `test`,
`docs`, `chore` (infra/CI). Sin firmas de IA en el mensaje.

### 0.9 Mapa de recetas

| Fase | Recetas | Sección de este manual |
|---|---|---|
| F0 Emergencia | T-V6-01 … 09 | §1 |
| F1 Bugs altos | T-V6-10 … 19 | §2 |
| F2 Base técnica | T-V6-21 … 30 | §3 |
| F3 Sistema de diseño | T-V6-31 … 37 | §4 |
| F4 Páginas | T-V6-40 … 52 | §5 |
| F5 Móvil y reproductor | T-V6-55 … 59 | §6 |
| F6 Funcionalidades | T-V6-60 … 68 | §7 |
| F7 Infra | T-V6-70 … 75 | §8 |
| F9 Producto | T-V6-80 … 95 | §9 |
| F9b Red profesional | T-V6-96 … 100 | §10 |
| Anexos | A: anclas que usan los tests · B: plantillas de código | §11 |

---

## 1. Fase V6-F0 · Emergencia de seguridad y bugs críticos

> Orden obligatorio: T-V6-01 (solo cuando Oscar haya rotado las claves, Parte I §2) → 02 → 03 →
> 04 → 05 → 06 → 07 → 08 → 09. Cada una es un commit.

### T-V6-01 · Purgar credenciales del repo y evitar que vuelvan (S)

**Objetivo.** Que ni el árbol ni el historial de git contengan contraseñas, emails personales ni
tokens, y que CI falle si alguien vuelve a subir uno.

**Antes de empezar (bloqueante).** Oscar tiene que haber hecho los 4 pasos de la Parte I §2.1
(rotar la contraseña de Postgres, cambiar la de la cuenta, poner el repo en privado, revocar el
PAT). Pregúntale y no sigas sin confirmación: purgar el historial sin rotar no sirve de nada.

**Archivos.** `REGISTRO_DE_CAMBIOS.md`, `harness/TASKS.md`, `PENDIENTES_OSCAR.md`,
`harness/ROADMAP.md`, `tests/unit/test_identidad_imagenes.py`, `.github/workflows/ci.yml`,
`.gitleaks.toml` (nuevo), `.pre-commit-config.yaml` (nuevo, opcional).

**Pasos.**

1. Localiza los textos sensibles (sin imprimirlos enteros en ningún sitio):
   ```bash
   git grep -n -i "oscarn" -- "*.md"              # contraseña de Postgres (REGISTRO:1344, TASKS:35)
   git grep -n "oscarcon314@gmail.com" -- "*.md"  # cuenta de prod (TASKS:16 y otras menciones)
   git grep -n -E "kabalah|tu@email" -- "*.md"    # emails personales
   git grep -n "fwynfifvtthtpzpejfhb" .           # ref del proyecto Supabase (docs + un test)
   ```
2. En cada línea: sustituye el valor por `<rotada el 2026-11-xx>` (contraseñas) o `<email de
   Oscar>` (emails). No borres el contexto de la frase: solo el dato.
3. En `tests/unit/test_identidad_imagenes.py:20` cambia la URL con el ref real por una ficticia
   (`https://demo-project.supabase.co/storage/v1/object/public/media/...`). Comprueba que el test
   sigue verde (solo valida formato).
4. **Historial.** Instala `pip install git-filter-repo`. Crea `/tmp/replacements.txt` (fuera del
   repo) con una línea por secreto: `<secreto>==><rotado>`. Ejecuta
   `git filter-repo --replace-text /tmp/replacements.txt`. Esto reescribe TODO el historial:
   después hay que `git push --force` a `main` (git destructivo → **pide a Oscar que confirme el
   force push** y que nadie tenga clones sin sincronizar). Si Oscar prefiere no reescribir (el repo
   ya es privado y las claves están rotadas), déjalo anotado en TASKS.md y salta este paso.
5. **Gitleaks en CI.** En `.github/workflows/ci.yml` añade un job independiente ANTES de `checks`:
   ```yaml
     secrets:
       runs-on: ubuntu-latest
       steps:
         - uses: actions/checkout@v4
           with: { fetch-depth: 0 }
         - uses: gitleaks/gitleaks-action@v2   # (T-V6-21 lo fijará por SHA)
           env: { GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }} }
   ```
   y `.gitleaks.toml` en la raíz con una allowlist mínima (el ref del proyecto Supabase no es
   secreto, pero quítalo igualmente de los docs):
   ```toml
   [allowlist]
   paths = ['''harness/capturas/''']
   ```
6. (Opcional) `.pre-commit-config.yaml` con el hook `gitleaks` para que también pare en local.
7. Añade a `.gitignore`: `.env.*` y `!.env.example`; crea `.env.example` con las variables
   **sin valores** (`SUPABASE_URL=`, `SUPABASE_ANON_KEY=`, `DATABASE_URL=`, `OPENROUTER_API_KEY=`).

**Comprobación.** `git grep -n -i "oscarn"` no devuelve nada; `git log -p | grep -c "Oscarn"` es 0
(si se purgó); CI muestra el job `secrets` verde.

**Test.** No hay test de código; el job de gitleaks es la verificación permanente.

**Commit.** `chore(v6): T-V6-01 — purgar credenciales de docs/tests y activar gitleaks`

**No hagas.** No pegues los secretos en TASKS.md ni en el commit. No hagas `--force` sin el OK de
Oscar.

---

### T-V6-02 · Cerrojo del modo test y de la BD de tests (S)

**Objetivo.** Que sea imposible (1) arrancar producción con `CHORDFLOW_TEST_MODE=1` y (2) que
`pytest` toque una base de datos que no sea SQLite.

**Archivos.** `src/services/config.py`, `tests/conftest.py`, `tests/unit/test_band_auth.py`,
`harness/seed_demo.py`, `tests/unit/test_config.py`.

**Pasos.**

1. En `src/services/config.py`, dentro de `class Settings`, añade al final un validador:
   ```python
   import os
   from pydantic import model_validator

   class Settings(BaseSettings):
       ...
       @model_validator(mode="after")
       def _test_mode_solo_en_local(self):
           """Cerrojo (T-V6-02): el modo test solo es válido con SQLite y fuera de Vercel."""
           if self.chordflow_test_mode:
               en_vercel = bool(os.getenv("VERCEL"))
               es_sqlite = self.database_url.startswith("sqlite")
               if en_vercel or not es_sqlite:
                   raise ValueError(
                       "CHORDFLOW_TEST_MODE=1 solo se permite en local con SQLite (nunca en producción)"
                   )
           return self
   ```
   (`import os` va arriba con los demás imports; `model_validator` se importa de `pydantic`).
2. En `tests/conftest.py` sustituye la línea
   `os.environ.setdefault("DATABASE_URL", "sqlite:///./test_unit.db")` por:
   ```python
   # T-V6-02: los tests SIEMPRE usan su propio SQLite, aunque la shell tenga DATABASE_URL de prod.
   os.environ["DATABASE_URL"] = "sqlite:///./test_unit.db"
   ```
   y en la fixture `client`, antes de `Base.metadata.drop_all(bind=engine)`, añade:
   ```python
       assert engine.url.drivername.startswith("sqlite"), "Los tests solo corren contra SQLite"
   ```
3. Busca `setdefault("DATABASE_URL"` en `tests/unit/test_band_auth.py` (≈ línea 393) y
   `harness/seed_demo.py:21` y aplica el mismo criterio: en el test, asignación directa; en
   `seed_demo.py`, añade justo después de leer la URL:
   ```python
   if not os.environ["DATABASE_URL"].startswith("sqlite"):
       raise SystemExit("seed_demo.py solo siembra bases SQLite de demo (no producción)")
   ```
4. En `tests/unit/test_config.py` añade:
   ```python
   def test_modo_test_rechaza_postgres_y_vercel(monkeypatch):
       """T-V6-02: el cerrojo impide activar el modo test fuera de SQLite/local."""
       monkeypatch.delenv("VERCEL", raising=False)
       with pytest.raises(ValidationError):
           Settings(chordflow_test_mode=True, database_url="postgresql://u:p@h:5432/db", _env_file=None)
       monkeypatch.setenv("VERCEL", "1")
       with pytest.raises(ValidationError):
           Settings(chordflow_test_mode=True, database_url="sqlite:///./x.db", _env_file=None)
       monkeypatch.delenv("VERCEL", raising=False)
       assert Settings(chordflow_test_mode=True, database_url="sqlite:///./x.db", _env_file=None)
   ```

**Comprobación.** `python -m pytest tests/unit/test_config.py -q` verde; `doctor.py` verde;
`set DATABASE_URL=postgresql://x && python -m pytest tests/unit -q` **falla al arrancar** (eso es lo
que queremos) — restaura la variable después.

**Commit.** `fix(v6): T-V6-02 — cerrojo del modo test fuera de SQLite/local y BD de tests forzada`

---

### T-V6-03 · Service worker: cachear solo estáticos versionados (S)

**Objetivo.** Que el SW nunca sirva datos de la API desde caché (hoy cachea `/collections`), que
purgue versiones viejas y que al cerrar sesión no quede nada del usuario.

**Archivos.** `static/sw.js`, `static/auth.js`, `tests/e2e/test_sw_api_no_cache.py` (nuevo).

**Pasos.**

1. Sustituye el bloque `fetch` de `static/sw.js` (desde `self.addEventListener('fetch'` hasta el
   final) por:
   ```js
   const CACHE = 'bandflow-static-v3';   // cambia el nombre: se purga la caché anterior

   self.addEventListener('fetch', (e) => {
       const req = e.request;
       const url = new URL(req.url);
       if (req.method !== 'GET' || url.origin !== self.location.origin) return;

       // 1) HTML / navegaciones: red primero, caché solo como respaldo offline.
       if (req.mode === 'navigate' || url.pathname.endsWith('.html')) {
           e.respondWith(fetch(req).then((r) => {
               const c = r.clone();
               caches.open(CACHE).then((ca) => ca.put(req, c)).catch(() => {});
               return r;
           }).catch(() => caches.match(req)));
           return;
       }

       // 2) SOLO estáticos versionados por hash (/static/x.js?v=abcd) van cache-first.
       //    Todo lo demás (API, /config, /public, etc.) va SIEMPRE a la red: nunca se cachea.
       const esEstatico = url.pathname.startsWith('/static/') && url.searchParams.has('v');
       if (!esEstatico) return;

       e.respondWith(caches.match(req).then((hit) => hit || fetch(req).then((r) => {
           const c = r.clone();
           caches.open(CACHE).then(async (ca) => {
               await ca.put(req, c);
               // Purga: otras versiones (?v=) del mismo fichero.
               const keys = await ca.keys();
               for (const k of keys) {
                   const ku = new URL(k.url);
                   if (ku.pathname === url.pathname && ku.search !== url.search) await ca.delete(k);
               }
           }).catch(() => {});
           return r;
       })));
   });
   ```
   Mantén `install` y `activate` como están (ya borran cachés con otro nombre).
2. En `static/auth.js`, en `signOut()`, antes de `window.location.href = 'login.html'`:
   ```js
       try {   // T-V6-03: nada del usuario anterior queda en caché ni en storage local
           if ('caches' in window) {
               const keys = await caches.keys();
               await Promise.all(keys.map((k) => caches.delete(k)));
           }
           localStorage.removeItem('bf-theme');   // (opcional) preferencias de la sesión
       } catch (e) { /* sin caché: seguimos */ }
   ```
3. `python harness/cachebust.py`.
4. Test e2e nuevo `tests/e2e/test_sw_api_no_cache.py`:
   ```python
   import pytest
   pytestmark = pytest.mark.e2e

   def test_colecciones_no_se_sirven_desde_cache(page, live_server, api):
       page.goto(f"{live_server}/static/library.html")
       page.wait_for_selector("#library-collections")
       page.evaluate("navigator.serviceWorker.ready")          # el SW ya controla la página
       api.post("/collections/", json={"name": "Nueva via API", "song_ids": []})
       page.reload()
       page.wait_for_selector("#library-collections")
       # La colección recién creada debe aparecer: si el SW cacheara /collections/, no estaría.
       page.wait_for_function(
           "() => document.querySelector('#library-collections').textContent.includes('Nueva via API')")
   ```

**Comprobación.** En DevTools → Application → Cache Storage, tras navegar, solo hay entradas
`/static/*?v=` y `.html`; ninguna `/collections/`, `/songs/`, `/me/...`.

**Commit.** `fix(v6): T-V6-03 — SW cachea solo estáticos versionados; purga versiones; limpia al salir`

---

### T-V6-04 · Modales y toasts legibles en tema claro + escala de z-index (S)

**Objetivo.** Que `confirmModal`, `promptModal`, `alertModal` y los modales de bands/library se
lean en tema claro, y que un toast nunca quede debajo de un modal.

**Archivos.** `static/style.css`, `static/design-system.css`.

**Pasos.**

1. En `static/design-system.css`, dentro de `:root {` (bloque de tokens), añade:
   ```css
     /* Escala de z-index (T-V6-04): un solo sitio para el apilamiento */
     --bf-z-dropdown: 100;
     --bf-z-sticky:   200;
     --bf-z-overlay:  1000;
     --bf-z-dialog:   1010;
     --bf-z-toast:    1100;
   ```
2. En `static/style.css`, bloque `.toast` (≈ línea 1356): sustituye
   `background: rgba(30, 30, 40, 0.75);` por `background: var(--bf-surface, #16161b);`,
   `border: 1px solid rgba(255, 255, 255, 0.12);` por `border: 1px solid var(--bf-border-strong);`,
   `color: var(--text-primary, #fff);` por `color: var(--bf-text);`,
   `box-shadow: 0 8px 30px rgba(0, 0, 0, 0.35);` por `box-shadow: var(--bf-shadow);`.
   En `#toast-container` cambia `z-index: 9999;` por `z-index: var(--bf-z-toast);`.
3. Mismo bloque `.modal-card` (≈ 1390): `background: var(--bf-surface);`,
   `border: 1px solid var(--bf-border-strong);`, `box-shadow: var(--bf-shadow-lg);`. En
   `.modal-overlay`: `z-index: var(--bf-z-overlay);`. En `.modal-msg`: `color: var(--bf-text);`.
4. `.toast-error { border-left: 4px solid var(--bf-danger); }`, `.toast-success { … var(--bf-success) }`,
   `.toast-info { … var(--bf-primary) }`. `.primary-btn.danger { background: var(--bf-danger); color: #fff; }`.
5. `python harness/cachebust.py`.

**Comprobación.** Con `localStorage.setItem('bf-theme','light')` en DevTools y recargando
`library.html`: borrar una canción abre un modal blanco con texto negro; lanza
`toast('hola','error')` en consola y se ve por encima de un modal abierto.

**Test.** Añade a `tests/e2e/test_tema_coherente.py`:
```python
def test_modal_legible_en_claro(page, live_server, api):
    page.goto(f"{live_server}/static/library.html")
    page.evaluate("localStorage.setItem('bf-theme','light')")
    page.reload()
    page.evaluate("window.confirmModal('¿Seguro?')")
    card = page.locator(".modal-card")
    bg = card.evaluate("el => getComputedStyle(el).backgroundColor")
    color = card.locator(".modal-msg").evaluate("el => getComputedStyle(el).color")
    assert bg != color and bg in ("rgb(255, 255, 255)", "rgb(250, 250, 248)")
```

**Commit.** `style(v6): T-V6-04 — modales y toasts con tokens (legibles en claro) y escala de z-index`

---

### T-V6-05 · El catálogo respeta la matriz de roles (S)

**Objetivo.** Que un `guest` no pueda publicar al catálogo ni importar al repertorio de banda.

**Archivos.** `src/api/catalog_router.py`, `tests/unit/test_api_catalog.py`.

**Pasos.**

1. En `catalog_router.py`, función `publish` (≈ línea 150-159), el bloque `else:` que consulta
   `BandMembership` solo mira `status == "active"`. Cámbialo para que también exija rol:
   ```python
       else:
           member = (db.query(BandMembership)
                     .join(Band, Band.id == BandMembership.band_id)
                     .filter(BandMembership.band_id == song.band_id,
                             BandMembership.user_id == user_id,
                             BandMembership.status == "active",
                             Band.deleted_at.is_(None)).first())
           if not member:
               raise HTTPException(status_code=403, detail="No perteneces a esa banda")
           if member.role == "guest":
               raise HTTPException(status_code=403, detail="Un invitado no puede publicar canciones de la banda")
   ```
   (añade `Band` al import de `..services.models` si no está).
2. En `import_score` (≈ 268-279) la consulta ya hace el join con `Band`; añade después del
   `if not member:` el mismo bloque `if member.role == "guest": raise HTTPException(403, …)`.
   Ojo: ahí la consulta pide `BandMembership.id`; cámbiala a `db.query(BandMembership)` para
   tener `.role`.
3. Tests en `tests/unit/test_api_catalog.py` (usa el helper `acting_as` del fichero o cópialo):
   ```python
   GUEST = "77777777-7777-7777-7777-777777777777"

   def _banda_con_guest(client):
       bid = client.post("/bands/", json={"name": "B"}).json()["id"]
       code = client.post(f"/bands/{bid}/invites", json={"role_to_grant": "guest"}).json()["code"]
       with acting_as(GUEST):
           client.post(f"/invites/{code}/accept")
       return bid

   def test_guest_no_publica_cancion_de_banda(client):
       bid = _banda_con_guest(client)
       song = client.post(f"/bands/{bid}/songs/", json=sample_song_payload()).json()
       with acting_as(GUEST):
           assert client.post("/catalog/publish", json={"song_id": song["id"]}).status_code == 403

   def test_guest_no_importa_al_repertorio(client):
       bid = _banda_con_guest(client)
       song = client.post("/songs/", json=sample_song_payload()).json()
       score_id = client.post("/catalog/publish", json={"song_id": song["id"]}).json()["id"]
       with acting_as(GUEST):
           r = client.post(f"/catalog/scores/{score_id}/import", json={"band_id": bid})
           assert r.status_code == 403
   ```
   (Comprueba en `catalog_router.py` el nombre exacto del campo que devuelve `publish`; si no es
   `id`, ajusta.)

**Commit.** `fix(v6): T-V6-05 — guest no puede publicar ni importar al catálogo en nombre de la banda`

---

### T-V6-06 · Importador seguro (allowlist, sin IP privadas, tope de bytes, presupuesto) + rate limit (M)

**Objetivo.** Cerrar el SSRF y la lectura sin tope del importador y limitar su uso por usuario.

**Archivos.** `src/services/importer.py`, `src/api/import_router.py`, `src/services/config.py`,
`src/services/ratelimit.py` (nuevo), `tests/unit/test_import.py`.

**Pasos.**

1. En `config.py` añade:
   ```python
       # Importador (T-V6-06)
       chordflow_import_allowed_hosts: str = "cifraclub.com,lacuerda.net,acordes.lacuerda.net,e-chords.com,ultimate-guitar.com,tabs.ultimate-guitar.com,chordify.net"
       chordflow_import_max_bytes: int = 2_000_000
       chordflow_import_budget_seconds: float = 22.0
       chordflow_import_daily_quota: int = 40     # importaciones con IA por usuario y día

       @property
       def import_allowed_hosts(self) -> list[str]:
           return [h.strip().lower() for h in self.chordflow_import_allowed_hosts.split(",") if h.strip()]
   ```
2. En `importer.py` crea, arriba, un validador y una descarga acotada, y úsalos en
   `_fetch_direct`, `_fetch_raw_html` y antes de llamar a Jina:
   ```python
   import ipaddress, socket, time
   from urllib.parse import urlparse

   class ImportError_(Exception): ...   # ya existe; reutiliza

   def validate_import_url(url: str) -> str:
       """Solo http(s) a hosts de la allowlist (o subdominios) que resuelvan a IP públicas."""
       p = urlparse(url)
       if p.scheme not in ("http", "https") or not p.hostname:
           raise ImportError_("URL no válida")
       host = p.hostname.lower()
       allowed = settings.import_allowed_hosts
       if not any(host == h or host.endswith("." + h) for h in allowed):
           raise ImportError_("Solo se puede importar desde: " + ", ".join(allowed))
       try:
           infos = socket.getaddrinfo(host, None)
       except socket.gaierror:
           raise ImportError_("No se pudo resolver el dominio")
       for info in infos:
           ip = ipaddress.ip_address(info[4][0])
           if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved or ip.is_multicast:
               raise ImportError_("Dominio no permitido")
       return url

   class _NoRedirectCrossHost(urllib.request.HTTPRedirectHandler):
       def redirect_request(self, req, fp, code, msg, headers, newurl):
           if urlparse(newurl).hostname != urlparse(req.full_url).hostname:
               raise ImportError_("Redirección a otro dominio no permitida")
           return super().redirect_request(req, fp, code, msg, headers, newurl)

   _opener = urllib.request.build_opener(_NoRedirectCrossHost())

   def _read_capped(resp, max_bytes: int) -> bytes:
       data = resp.read(max_bytes + 1)
       if len(data) > max_bytes:
           raise ImportError_("La página es demasiado grande")
       return data
   ```
   y en `_fetch_direct`/`_fetch_raw_html` cambia `urllib.request.urlopen(req, timeout=…)` por
   `_opener.open(req, timeout=…)` y `resp.read()` por `_read_capped(resp, settings.chordflow_import_max_bytes)`.
   En `import_from_url(url)` llama a `validate_import_url(url)` en la primera línea; en
   `fetch_page_text` también (Jina recibe la URL ya validada).
3. **Presupuesto de tiempo**: en `fetch_page_text` y `import_from_url` lleva un `deadline =
   time.monotonic() + settings.chordflow_import_budget_seconds` y pasa a cada llamada
   `timeout=max(1, min(x, deadline - time.monotonic()))`; si el presupuesto se agota, lanza
   `ImportError_("La importación tardó demasiado; prueba con otra fuente o pega el texto")`.
   Reduce los timeouts fijos (Jina 30→8 s, directo 25→8 s, LLM 45/60→12 s).
4. **Rate limit** simple sin dependencias (`src/services/ratelimit.py`):
   ```python
   import threading, time
   from collections import defaultdict, deque
   from fastapi import HTTPException

   _hits: dict[str, deque] = defaultdict(deque)
   _lock = threading.Lock()

   def check_rate(key: str, limit: int, window_s: int) -> None:
       """Lanza 429 si `key` supera `limit` peticiones en `window_s` segundos (memoria por instancia)."""
       now = time.monotonic()
       with _lock:
           q = _hits[key]
           while q and q[0] < now - window_s:
               q.popleft()
           if len(q) >= limit:
               raise HTTPException(status_code=429, detail="Demasiadas peticiones; espera un momento")
           q.append(now)
   ```
   En `import_router.py`, al principio de `import_song`, `import_photo` y `search`:
   `check_rate(f"import:{user_id}", limit=10, window_s=60)` y
   `check_rate(f"import-day:{user_id}", limit=settings.chordflow_import_daily_quota, window_s=86400)`.
   (Es por instancia serverless; T-V6-74 lo pasa a Postgres/KV. Ya corta el abuso básico.)
5. Tests en `tests/unit/test_import.py`:
   ```python
   from src.services.importer import validate_import_url, ImportError_

   @pytest.mark.parametrize("url", ["http://127.0.0.1/x", "http://localhost/x", "http://169.254.169.254/latest",
                                    "ftp://cifraclub.com/x", "https://evil.com/cifraclub.com"])
   def test_urls_prohibidas(url):
       with pytest.raises(ImportError_):
           validate_import_url(url)

   def test_url_permitida(monkeypatch):
       monkeypatch.setattr("src.services.importer.socket.getaddrinfo", lambda *a, **k: [(0, 0, 0, "", ("93.184.216.34", 0))])
       assert validate_import_url("https://www.cifraclub.com/oasis/wonderwall/") 

   def test_import_rate_limit(client, monkeypatch):
       monkeypatch.setattr("src.api.import_router.import_from_url", lambda url: "Am C G")
       for _ in range(10):
           client.post("/import/", json={"url": "https://www.cifraclub.com/a/b/"})
       assert client.post("/import/", json={"url": "https://www.cifraclub.com/a/b/"}).status_code == 429
   ```
   (Ajusta el nombre que `import_router` usa para la función importada si es distinto.)

**Comprobación.** Importar desde CifraClub sigue funcionando; `http://127.0.0.1:8000/health` como
URL de importación devuelve 400 con mensaje claro; la 11ª importación en un minuto da 429.

**Commit.** `fix(v6): T-V6-06 — importador con allowlist, sin IP privadas, lectura acotada, presupuesto y rate limit`

---

### T-V6-07 · `reference_url` solo http(s) (S)

**Archivos.** `src/services/schemas.py` (`SongBase.reference_url`, `SongUpdate.reference_url`),
`static/editor.js`, `tests/unit/test_api_songs.py`.

**Pasos.**

1. En `schemas.py` añade un validador reutilizable y úsalo en los dos campos:
   ```python
   from pydantic import field_validator

   def _solo_http(url: str | None) -> str | None:
       if url is None or url == "":
           return None
       if not url.lower().startswith(("http://", "https://")):
           raise ValueError("El enlace debe empezar por http:// o https://")
       return url

   class SongBase(BaseModel):
       ...
       @field_validator("reference_url")
       @classmethod
       def _ref_http(cls, v): return _solo_http(v)
   ```
   (igual en `SongUpdate`).
2. En `editor.js`, donde se lee el input del enlace antes de guardar, normaliza: si no empieza
   por `http`, muestra `toast('El enlace debe empezar por https://', 'error')` y no guardes.
3. Test: `POST /songs/` con `reference_url: "javascript:alert(1)"` → 422.

**Commit.** `fix(v6): T-V6-07 — reference_url solo acepta http(s)`

---

### T-V6-08 · Invitaciones con caducidad y usos por defecto, revocables y con contador atómico (S)

**Archivos.** `src/services/schemas.py`, `src/api/bands_router.py`, `src/api/invites_router.py`,
`src/services/models.py` (+ migración), `tests/unit/test_api_invites.py`.

**Pasos.**

1. `models.py`, clase `BandInvite`: añade `revoked_at = Column(DateTime, nullable=True)`.
   Migración (§0.5): `t-v6-08 band_invites.revoked_at`.
2. `schemas.py`, `BandInviteCreate`: `expires_in_days: int = Field(7, ge=1, le=90)` y
   `max_uses: Optional[int] = Field(20, ge=1, le=500)`; conserva `expires_at` opcional para
   compatibilidad (si viene, manda).
3. `bands_router.py`, `create_invite`: calcula
   `expires_at = payload.expires_at or (_utcnow() + timedelta(days=payload.expires_in_days))`.
   Añade la ruta de revocación:
   ```python
   @router.delete("/{band_id}/invites/{invite_id}", status_code=status.HTTP_204_NO_CONTENT)
   def revoke_invite(band_id: str, invite_id: str, db: Session = Depends(get_db),
                     membership: BandMembership = Depends(require_band_admin)):
       inv = db.query(BandInvite).filter(BandInvite.id == invite_id, BandInvite.band_id == band_id).first()
       if inv is None:
           raise HTTPException(status_code=404, detail="Invitación no encontrada")
       inv.revoked_at = _utcnow()
       db.commit()
   ```
4. `invites_router.py`, `_invalid_reason`: antes de comprobar la caducidad, `if invite.revoked_at
   is not None: return "revocada"`. En `accept_invite`, sustituye `invite.used_count += 1` por un
   incremento atómico:
   ```python
       from sqlalchemy import update
       cond = BandInvite.id == invite.id
       if invite.max_uses is not None:
           cond = cond & (BandInvite.used_count < invite.max_uses)
       res = db.execute(update(BandInvite).where(cond).values(used_count=BandInvite.used_count + 1))
       if res.rowcount == 0:
           db.rollback()
           raise HTTPException(status_code=410, detail="Invitación agotada")
   ```
   (haz esto ANTES de crear la membresía, y `db.commit()` después de ambas cosas).
5. Tests: por defecto `expires_at` ≈ hoy+7 y `max_uses == 20`; revocar → `GET /invites/{code}`
   devuelve `valid: false, reason: "revocada"` y aceptar → 400/410; ajeno al revocar → 404;
   con `max_uses=1`, dos aceptaciones (dos `acting_as` distintos) → la segunda 410.
6. Front (`static/bands.js:1235-1238`): no cambies nada todavía (la UI de invitaciones llega en
   T-V6-42e); solo comprueba que crear invitación sigue funcionando sin enviar `expires_at`.

**Commit.** `feat(v6): T-V6-08 — invitaciones con caducidad/usos por defecto, revocación y contador atómico`

---

### T-V6-09 · Parche móvil urgente (CSS, antes del rediseño) (M)

**Objetivo.** Que las cinco pantallas rotas en móvil sean usables ya, sin esperar a F4. Son
cambios de CSS (y uno de HTML) que después F3/F4 sustituyen; no inviertas más de un día.

**Archivos.** `static/style.css`, `static/join.html`, `static/band.js` (solo el composer del chat),
`tests/e2e/test_responsive_pwa.py`.

**Pasos.**

1. **Agenda de banda (V-01).** Al final de `style.css` añade:
   ```css
   /* T-V6-09: filas de agenda/repertorio en móvil → acciones debajo del texto */
   @media (max-width: 768px) {
     .setlist-song { flex-wrap: wrap; }
     .setlist-song .sl-title { flex: 1 1 100%; min-width: 0; }
     .setlist-song .att-buttons { flex: 1 1 100%; display: flex; flex-wrap: wrap; gap: .35rem; margin-top: .4rem; }
     .ev-status-sel { max-width: 100%; }
   }
   ```
2. **Reproductor (V-02).** En `style.css`, busca la regla de la letra (`.line-lyric` o el
   contenedor `#score-content`) y añade en el media query `(max-width: 820px)` existente:
   ```css
     #score-content { overflow-wrap: anywhere; font-size: clamp(1rem, 4.2vw, 1.25rem); }
     .chord-container { flex-wrap: wrap; }
     .top-bar .global-controls { flex-wrap: wrap; row-gap: .4rem; }
     .top-bar .control-group { max-width: 100%; }
   ```
   (si `.chord-container` usa `position:absolute` para los acordes, NO lo cambies: solo el wrap
   del contenedor de línea; el contrato DOM se mantiene).
3. **Join (V-03).** En `join.html`, envuelve el bloque del botón `#join-accept` en el mismo
   contenedor centrado que el título (`#join-box`) y añade `.join-box { text-align:center; max-width: 480px; margin: 2rem auto; }`
   `.join-box .primary-btn { margin: 1rem auto 0; display: inline-flex; }`. Quita el `🎸` del
   `h1` (déjalo como texto "Unirse a una banda").
4. **Chat (V-04).** En `band.js` (≈ 186-189) el composer: cambia `class="primary-btn"` del botón
   por `class="bf-btn bf-btn--primary"` y el input `class="search-box"` por `class="bf-input"`;
   el contenedor `style="display:flex; gap:.5rem; margin-top:.6rem;"` por
   `class="bf-row" style="gap:.5rem;margin-top:.6rem;align-items:stretch;"`. Si `.bf-input` no
   existe aún en `design-system.css`, añade una mínima:
   `.bf-input { height: 40px; padding: 0 .75rem; border: 1px solid var(--bf-border-strong); border-radius: var(--bf-radius); background: var(--bf-surface-2); color: var(--bf-text); flex: 1; }`
   Mantén los ids `#chat-input` y `#chat-send`.
5. **Biblioteca (F-08).** `@media (hover: none) { .song-card .card-actions { opacity: 1; } }`.
6. `python harness/cachebust.py`.
7. En `tests/e2e/test_responsive_pwa.py` amplía la lista de páginas del test de overflow
   horizontal para incluir `band.html?id=…` (con un evento sembrado vía `api`), `index.html?songId=…`
   y `join.html?code=…`, a 390 px: `page.set_viewport_size({"width": 390, "height": 844})` y
   `assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth + 1")`.

**Comprobación.** Capturas en 390 px de: agenda de banda, reproductor con una letra larga, join,
chat. Nada se corta ni se solapa.

**Commit.** `style(v6): T-V6-09 — parche móvil: agenda de banda, reproductor, join, chat, acciones de tarjeta`

---

## 2. Fase V6-F1 · Bugs altos y deuda que bloquea

### T-V6-10 · Chat de banda: render diferencial, auto-scroll, pausa en segundo plano, paginación (M)

**Objetivo.** Que el chat no salte al principio cada 6 s, que lo nuevo se vea, que no sondee con
la pestaña oculta y que la API no devuelva todo el historial cada vez.

**Archivos.** `src/api/messages_router.py`, `static/bands.js` (`initChat`, `loadChat`,
`renderMessageList`), `static/style.css` (`#b-chat` / `.chat-scroll`), `tests/unit/test_api_messages.py`,
`tests/e2e/test_chat.py`.

**Pasos — backend.**

1. En `list_messages` añade parámetros `after: Optional[str] = None` (id del último mensaje que
   el cliente ya tiene) y `limit: int = Query(50, ge=1, le=200)`:
   ```python
   if after:
       ref = db.query(Message.created_at).filter(Message.id == after, Message.band_id == band_id).scalar()
       if ref is not None:
           q = q.filter(Message.created_at > ref)
   rows = q.order_by(Message.created_at.asc()).limit(limit).all()
   ```
   Sin `after`, devuelve los **últimos** `limit` en orden ascendente (subconsulta con
   `order_by(created_at.desc()).limit(limit)` y luego invierte en Python). Los fijados se piden
   aparte: `GET …/messages/?pinned=1` devuelve solo `is_pinned` (máximo 20). Mantén la respuesta
   `List[MessageOut]` (el front actual sigue funcionando).
2. Test unit: con 60 mensajes, `GET …/messages/` devuelve 50 y el más nuevo al final; con
   `?after=<id del 50º>` devuelve 10; `?pinned=1` solo fijados.

**Pasos — frontend (`bands.js`).**

3. Estado del chat por banda: `let chatState = { lastId: null, ids: new Set() }`. `loadChat`
   pasa a pedir `?after=${lastId}` cuando ya hay mensajes y **añade** los nuevos al final del
   `<ul>` existente en vez de reemplazar `innerHTML` (crea los `<li>` con la misma plantilla de
   `renderMessageList` extraída a `messageItemHtml(m)`). Si no hay `<ul>`, render completo.
4. Auto-scroll: antes de añadir, calcula `const abajo = el.scrollTop + el.clientHeight >= el.scrollHeight - 24;`
   después de añadir, si `abajo` (o si el mensaje es mío) → `el.scrollTop = el.scrollHeight`.
   Al render inicial, scroll al final.
5. Pausa: `document.addEventListener('visibilitychange', () => { if (document.hidden) pararTimer(); else { reanudar(); loadChat(); } })`.
   Al cambiar de pestaña del espacio de banda (`band.js:604-613`), llama a `stopChat()` que hace
   `clearInterval`.
6. CSS: el contenedor `#b-chat` con `max-height: min(60vh, 520px); overflow-y: auto;` y
   `scroll-behavior: smooth` (respetando `prefers-reduced-motion`).
7. Fijados: pinta los fijados en una franja arriba (`#b-chat-pinned`) a partir de
   `?pinned=1`, no mezclados en la lista.

**Test e2e** (`test_chat.py`): siembra 30 mensajes vía `api`, abre la pestaña chat, comprueba
`scrollTop > 0` (está al final); envía uno nuevo por `api`, espera `wait_for_function` a que
aparezca el `li[data-id="<nuevo>"]` y comprueba que `scrollTop` no volvió a 0.

**Commit.** `fix(v6): T-V6-10 — chat de banda incremental (after/limit), auto-scroll, pausa en segundo plano`

---

### T-V6-11 · `/songs/` con orden estable y paginación; "Cargar más" en Biblioteca (S)

**Archivos.** `src/api/songs_router.py`, `static/library.js`, `tests/unit/test_api_songs.py`.

**Pasos.**

1. En `get_songs` añade `.order_by(Song.updated_at.desc(), Song.id.asc())` antes de
   `.offset(skip).limit(limit)`. Sube el default a `limit: int = Query(200, ge=1, le=500)`.
   Añade la cabecera `X-Total-Count` (`response.headers["X-Total-Count"] = str(total)`) con un
   `count()` de la misma consulta (inyecta `response: Response`).
2. En `library.js` `fetchSongs`: pide `/songs/?limit=200`; si `X-Total-Count` > 200, muestra un
   botón `#library-more` ("Cargar más") que pide `skip=200`, `400`… y concatena.
3. Haz lo mismo en `/bands/{id}/songs/` (`band_songs_router.py`): `order_by(Song.title.asc())`
   (el repertorio se lee alfabético) + `skip/limit` con default 500.
4. Test: crear 3 canciones con `updated_at` distintos (modifica una) y comprobar el orden;
   `?limit=2` devuelve 2 y `X-Total-Count: 3`.

**Commit.** `fix(v6): T-V6-11 — listados de canciones con ORDER BY, paginación y total`

---

### T-V6-12 · Eliminar N+1 en saldos y listados (S)

**Archivos.** `src/api/finance_router.py`, `src/api/bands_router.py`, `src/api/me_router.py`,
`src/api/setlists_router.py`, `src/api/band_setlists_router.py`, `src/api/collections_router.py`,
`src/api/band_collections_router.py`, `src/api/tours_router.py`.

**Pasos.**

1. En las tres consultas que cargan `Transaction` para `compute_balances` (finance_router ≈ 195,
   bands_router ≈ 211, me_router ≈ 203) añade `.options(selectinload(Transaction.splits))`
   (`from sqlalchemy.orm import selectinload`).
2. En los listados de setlists/colecciones, sustituye `song_count=len(s.items)` por un
   diccionario calculado con UNA consulta agregada (copia el patrón de `_song_counts` en
   `bands_router.py`):
   ```python
   counts = dict(db.query(SetlistItem.setlist_id, func.count(SetlistItem.id))
                 .filter(SetlistItem.setlist_id.in_(ids)).group_by(SetlistItem.setlist_id).all())
   ```
3. En `_to_response` de setlists (≈ 73) carga los ítems con `selectinload(SetlistItem.song)`.
4. Tours: `stop_count`/`total_budget` por agregado en una consulta.
5. Test de contador de queries (opcional pero recomendable): con `sqlalchemy.event.listen(engine,
   "before_cursor_execute", …)` cuenta las consultas de `GET /bands/{id}/balances` con 30
   movimientos y asevera `< 10`.

**Commit.** `perf(v6): T-V6-12 — selectinload de splits y contadores agregados (fin del N+1)`

---

### T-V6-13 · Serverless bien configurado: sin `create_all` en PG, pool mínimo, `maxDuration`, runtime (S)

**Archivos.** `src/main.py`, `src/services/db.py`, `vercel.json`, `runtime.txt` (nuevo),
`.vercelignore`.

**Pasos.**

1. `main.py`: envuelve el `create_all` en `if settings.database_url.startswith("sqlite"):` (en
   Postgres el esquema lo gestionan las migraciones; T-V6-71 lo automatiza).
2. `db.py`: tras calcular `engine_kwargs`, añade:
   ```python
   import os
   if not _is_sqlite and os.getenv("VERCEL"):
       from sqlalchemy.pool import NullPool
       engine_kwargs["poolclass"] = NullPool   # cada invocación abre/cierra; el pooler (6543) hace el pool real
   ```
3. `vercel.json`: añade `"functions": { "api/index.py": { "maxDuration": 30 } }` (30 en Hobby;
   60 si Oscar tiene Pro — preguntar). Si el `builds` antiguo no admite `functions`, migra a la
   configuración moderna (sin `builds`, con `rewrites` → `api/index.py`); verifica con un
   deploy de preview.
4. `runtime.txt` con `python-3.12` (o `requires-python = ">=3.12,<3.13"` en `pyproject.toml` y
   NO excluirlo en `.vercelignore`).
5. Comprueba en los logs de Vercel que el cold start baja (no aparece la reflexión de tablas).

**Commit.** `chore(v6): T-V6-13 — create_all solo en SQLite, NullPool en Vercel, maxDuration y runtime fijado`

---

### T-V6-14 · Tema aplicado en `<head>` en todas las páginas + `100dvh` (S)

**Archivos.** los 16 `static/*.html`, `static/shell.css`, `static/theme.js`.

**Pasos.**

1. En cada HTML del shell (app, bands, band, library, setlists, agenda, finanzas, chat, profile,
   afinador, biblioteca-global) y en `login.html`, `evento.html`, añade en `<head>`, justo
   después del `<meta name="viewport">`: `<script src="theme.js?v=…"></script>` (el hash lo pone
   `cachebust.py`). `editor.html` y `join.html` ya lo tienen. `index.html` NO (siempre oscuro).
2. En `shell.css` sustituye `100vh` por `100dvh` (3 sitios: ≈ 39, 52, 221) dejando un fallback:
   ```css
   height: 100vh; height: 100dvh;
   ```
3. `cachebust.py`. Test: en `test_tema_coherente.py`, con `bf-theme=light` en localStorage, abre
   `app.html` y comprueba `document.documentElement.getAttribute('data-theme') === 'light'`
   **antes** de que cargue `shell.js` (usa `page.add_init_script` para fijar el storage y lee el
   atributo en el evento `DOMContentLoaded` con `page.evaluate`).

**Commit.** `fix(v6): T-V6-14 — theme.js en head de todas las páginas (sin flash) y 100dvh`

---

### T-V6-15 · `apiJson()`: errores normalizados, estado de error ≠ vacío, botones con carga (M)

**Objetivo.** Un único punto que hable con la API, con errores en castellano, y que todas las
listas distingan "no hay nada" de "no se pudo cargar".

**Archivos.** `static/auth.js` (o nuevo `static/api.js` cargado después de `auth.js` en las 16
páginas), `static/util.js`, `static/design-system.css`, todos los `*.js` que llaman a `apiFetch`.

**Pasos.**

1. Nuevo helper (en `auth.js`, debajo de `apiFetch`):
   ```js
   class ApiError extends Error {
       constructor(status, message, detail) { super(message); this.status = status; this.detail = detail; }
   }
   const API_MESSAGES = {
       400: 'La petición no es válida.', 401: 'Tu sesión ha caducado. Vuelve a entrar.',
       403: 'No tienes permiso para hacer esto.', 404: 'No lo encontramos (quizá se borró).',
       409: 'Ya existe o está en conflicto.', 410: 'Este enlace ya no es válido.',
       422: 'Revisa los datos del formulario.', 429: 'Demasiadas peticiones. Espera un momento.',
       500: 'Error en el servidor. Inténtalo de nuevo en un minuto.',
   };
   function apiErrorMessage(status, detail) {
       if (typeof detail === 'string' && detail && status < 500) return detail;   // mensajes propios del back (castellano)
       if (Array.isArray(detail) && detail[0] && detail[0].msg) return 'Revisa los datos: ' + detail[0].msg;
       return API_MESSAGES[status] || 'Algo ha fallado. Inténtalo de nuevo.';
   }
   async function apiJson(url, opts = {}) {
       if (opts.body && typeof opts.body !== 'string') {
           opts.body = JSON.stringify(opts.body);
           opts.headers = Object.assign({ 'Content-Type': 'application/json' }, opts.headers);
       }
       let res;
       try { res = await apiFetch(url, opts); }
       catch (e) { throw new ApiError(0, 'Sin conexión. Revisa tu red.', null); }
       if (res.status === 204) return null;
       const data = await res.json().catch(() => null);
       if (!res.ok) throw new ApiError(res.status, apiErrorMessage(res.status, data && data.detail), data && data.detail);
       return data;
   }
   ```
2. En `util.js` añade `bfErrorState(msg, retryFn)` que devuelve HTML de un estado de error con
   botón "Reintentar" (`<div class="bf-empty bf-empty--error" role="alert">…<button class="bf-btn bf-btn--sm" data-act="retry">Reintentar</button></div>`)
   y una función `bfBusy(btn, promiseFn)` que pone `btn.disabled = true; btn.classList.add('is-loading')`
   mientras dura la promesa y lo restaura siempre (`finally`). CSS: `.bf-btn.is-loading { opacity:.7; pointer-events:none; }`
   con un spinner por `::after`.
3. Migra las llamadas, fichero a fichero, en este orden (cada uno un commit pequeño si prefieres):
   `library.js` (`fetchSongs`: `r.ok ? r.json() : []` → `apiJson` y, en `catch`, `elGrid.innerHTML = bfErrorState(e.message, fetchSongs)`),
   `home.js`, `agenda.js`, `finanzas.js`, `chat.js`, `bands.js`, `band.js`, `setlists.js`,
   `profile.js`, `catalogo.js`, `editor.js` (sustituye `toast(data.detail || …)` por `toast(e.message, 'error')`),
   `app.js`, `join.js`, `evento.js`.
4. Botones de envío (`setlists.js:191`, `bands.js:972`, `catalogo.js:109,125`, `band.js:558`,
   `profile.js:69`, `login.js:26,39`): envuélvelos con `bfBusy(btn, () => …)`.
5. `cachebust.py`. Test e2e: con `page.route('**/songs/', r => r.fulfill({status:500, body:'{}'}))`,
   `library.html` muestra `.bf-empty--error` y NO el estado vacío de onboarding.

**Commit.** `refactor(v6): T-V6-15 — apiJson con errores normalizados, estados de error y botones con carga`

---

### T-V6-16 · Editor: guardia de cambios y publicación informada (S)

**Archivos.** `static/editor.html`, `static/editor.js`, `tests/e2e/test_editor.py`.

**Pasos.**

1. `editor.js`: `let dirty = false;` y en los `input`/`change` de `#title`, `#artist`, `#bpm`,
   `#raw-text`, `#reference-url`, `#time-signature`: `dirty = true`. Tras guardar con éxito:
   `dirty = false`.
   ```js
   window.addEventListener('beforeunload', (e) => { if (dirty) { e.preventDefault(); e.returnValue = ''; } });
   document.getElementById('btn-close')?.addEventListener('click', async (e) => {
       if (!dirty) return;
       e.preventDefault();
       if (await confirmModal('Tienes cambios sin guardar. ¿Salir igualmente?', { okText: 'Salir' })) { dirty = false; location.href = e.currentTarget.href; }
   });
   ```
   (usa el id/clase real del botón ❌ de `editor.html:27`).
2. Publicación (F-18): en `editor.html`, junto al botón guardar, añade
   `<label class="bf-check"><input type="checkbox" id="share-catalog" checked> Compartir en Explorar
   <span class="bf-faint">(solo letra y acordes; asegúrate de tener derecho a publicarlos)</span></label>`.
   El `checked` por defecto depende de D-V6-3 (recomendado: marcado). En `editor.js:604-614`
   condiciona el `POST /catalog/publish` a `document.getElementById('share-catalog').checked`.
   Si D-V6-23 (Explorar oculto) está activa, el checkbox se oculta y no se publica.
3. Test e2e: escribir en `#raw-text` y evaluar que `window.onbeforeunload`/el listener marca
   dirty (comprueba `page.evaluate("window.__bfDirty")` exponiendo `window.__bfDirty = () => dirty`);
   guardar con el checkbox desmarcado no llama a `/catalog/publish` (`page.route` que falla si se
   llama).

**Commit.** `fix(v6): T-V6-16 — editor con guardia de cambios y publicación en Explorar opcional e informada`

---

### T-V6-17 · Espacio no toca el BPM; metrónomo con scheduler lookahead (S)

**Archivos.** `static/app.js`, `static/metronome.js`, `tests/e2e/test_tempo.py`,
`tests/e2e/test_js_logic.py`.

**Pasos.**

1. `app.js` (≈ 274-280): en el listener de Espacio añade `if (tag === 'button' || tag === 'a') return;`
   (y lo mismo en el de pedales si aplica). Así, con el foco en +/−, Espacio ya no alterna
   play. Para que Espacio siga funcionando tras clicar un botón, el botón Play hace
   `btn.blur()` al pulsarse (`document.getElementById('btn-play-pause').addEventListener('click', e => e.currentTarget.blur())`).
2. `metronome.js`, clase `BfMetronome`: sustituye `start()` por un scheduler con *lookahead*:
   ```js
   start() {
       if (this.running) return;
       this._ensureCtx();
       this.running = true;
       this._beat = 0;
       this._nextTime = this.audioCtx.currentTime + 0.05;
       const LOOKAHEAD = 0.12, INTERVAL = 25;             // s programados por adelantado, ms de tick
       const tick = () => {
           if (!this.running) return;
           while (this._nextTime < this.audioCtx.currentTime + LOOKAHEAD) {
               const level = bfBeatAccent(this._beat, this.num, this.den);
               bfMetronomeClick(this.audioCtx, level, this._nextTime);   // ← acepta `when`
               const beatIdx = this._beat % this.num, delay = Math.max(0, (this._nextTime - this.audioCtx.currentTime) * 1000);
               if (this.onTick) setTimeout(() => this.onTick(beatIdx, level), delay);
               this._beat++;
               this._nextTime += 60 / this.bpm;
           }
           this._timer = setTimeout(tick, INTERVAL);
       };
       tick();
   }
   ```
   y en `bfMetronomeClick(ctx, level, when = ctx.currentTime)` usa `when` en `osc.start(when)` /
   `osc.stop(when + dur)` y en los `gain.setValueAtTime(…, when)`. Comprueba que el reproductor
   (`app.js:342 playClick`) sigue llamando a `bfMetronomeClick(audioCtx, level)` sin `when` (usa
   el default) — el motor del reproductor no cambia.
3. Tests: en `test_js_logic.py` añade una prueba de que `bfMetronomeClick` admite 3 argumentos
   sin lanzar; en `test_tempo.py`, foco en `#btn-bpm-up` + `Space` no cambia `#btn-play-pause`.

**Commit.** `fix(v6): T-V6-17 — Espacio no altera el BPM con foco en botones; metrónomo con lookahead`

---

### T-V6-18 · Contrato de fechas UTC de punta a punta (M)

**Objetivo.** Que una hora signifique lo mismo para todos los miembros y en el servidor.

**Decisión de diseño (fija):** el servidor **siempre** recibe y devuelve ISO-8601 con zona
(`2026-11-14T19:30:00Z`); guarda en UTC; el navegador convierte a hora local al mostrar.

**Archivos.** `src/services/schemas.py`, `src/services/models.py` (+ migración), routers que
comparan con `now`, `static/*.js` que construyen fechas, `tests/unit/test_api_events.py`.

**Pasos.**

1. `models.py`: todas las columnas `DateTime` pasan a `DateTime(timezone=True)`. Migración con
   `alembic revision --autogenerate` (en SQLite no cambia nada real; en Postgres convierte a
   `timestamptz` interpretando los valores actuales como UTC — revisa el SQL generado y añade
   `USING col AT TIME ZONE 'UTC'` si Alembic no lo pone).
2. `schemas.py`: un validador común aplicado a TODOS los campos `datetime` de entrada
   (`EventCreate/Update.starts_at/ends_at`, `TransactionCreate.date`, `SettlementCreate.date`,
   `TourBase.start_date/end_date`, `BandInviteCreate.expires_at`):
   ```python
   def _to_utc(v: datetime | None) -> datetime | None:
       if v is None: return None
       if v.tzinfo is None:      # naive → se asume UTC (el front ya envía con Z)
           return v.replace(tzinfo=timezone.utc)
       return v.astimezone(timezone.utc)
   ```
   Sustituye el `_to_naive_utc` actual por este y elimina `.replace(tzinfo=None)`.
   Configura la serialización con `Z`: en los modelos de respuesta usa
   `model_config = ConfigDict(from_attributes=True, json_encoders={datetime: lambda d: d.astimezone(timezone.utc).isoformat().replace('+00:00','Z')})`
   (o un `field_serializer` común si tu Pydantic lo prefiere).
3. Routers: cada `now = datetime.now(timezone.utc).replace(tzinfo=None)` pasa a
   `now = datetime.now(timezone.utc)` (bands_router, me_router, invites_router `_invalid_reason`
   simplifica su rama naive).
4. Front: donde se lee un `datetime-local` (`bands.js:723` y similares) envía
   `new Date(input.value).toISOString()`; donde se muestra, `new Date(iso)` ya convierte a local.
   Centraliza en `format.js` (T-V6-36) `toApiDate(localValue)` y `fromApiDate(iso)`.
5. Test: crea un evento con `starts_at: "2026-11-14T20:30:00+01:00"`; el GET devuelve
   `2026-11-14T19:30:00Z`; `/me/dashboard` lo lista como próximo cuando `now` está 1 h antes en
   otra zona (simula con `freezegun` o monkeypatch de `datetime.now` en el router).

**Commit.** `fix(v6): T-V6-18 — fechas tz-aware en UTC de punta a punta`

---

### T-V6-19 · Lote de correcciones backend medias (M)

Haz cada punto como un sub-commit si lo prefieres; cierra B-07, B-08, B-09, B-11, B-19, B-21,
B-22, B-23, B-27.

1. **`active_membership()` único (B-22).** En `src/services/band_auth.py`:
   ```python
   def active_membership(db, band_id: str, user_id: str) -> BandMembership | None:
       return (db.query(BandMembership).join(Band, Band.id == BandMembership.band_id)
               .filter(BandMembership.band_id == band_id, BandMembership.user_id == user_id,
                       BandMembership.status == "active", Band.deleted_at.is_(None)).first())
   ```
   y úsalo en `songs_router.py:30-40`, `setlists_router.py:24-34`, `catalog_router.py` (las dos de
   T-V6-05) y en `require_band_member`. Test: banda soft-borrada → sus canciones dan 404.
2. **Liquidaciones a ex-miembros (B-07).** En `finance_router.py` la validación de
   `from_user_id`/`to_user_id` acepta cualquier usuario con membresía `active` **o `left`** en la
   banda (consulta sin filtrar `status`). Test: miembro de baja con saldo −20 → liquidación OK y
   saldo 0.
3. **`reference_url` al copiar (B-08).** `band_songs_router.py:61-66`: añade `"reference_url"` a
   `_SONG_SCALAR_FIELDS`. Test de round-trip.
4. **Búsqueda normalizada (B-09).** `catalog_router.py:221-224`: `join(MusicalWork)` y filtra
   `MusicalWork.norm_title.like(like) | MusicalWork.norm_artist.like(like)`. Test: publicar
   "Canción" y buscar "cancion".
5. **Longitudes espejo (B-11).** Crea `src/services/limits.py` con constantes
   (`KEY_ROOT=4, CHORD_NAME=16, KEY_MODE=32, TUNING=32, INSTRUMENT=32, SECTION_NAME=64, COLOR_TAG=7,
   FORMAT_VERSION=8, ARTIST=255, ALBUM=255`) y úsalas en `models.py` (`String(limits.X)`) y en
   `schemas.py` (`Field(max_length=limits.X)`). Test: `key_root` de 5 letras → 422.
6. **dotenv (B-19).** `config.py`: `load_dotenv(".env.local", override=True)`.
7. **`plan` no editable (B-21).** Quita `plan` de `BandUpdate` (o ignóralo en el PATCH con un
   test que lo demuestre).
8. **`get_db` (B-23).** En `db.py`:
   ```python
   except HTTPException:
       raise
   except Exception as e:
       logger.error(...)
       raise
   ```
   (`from fastapi import HTTPException`).
9. **Perfil get-or-create (B-27).** `profile_router.py:27-32`: envuelve el `db.add/commit` en
   `try/except IntegrityError: db.rollback(); return db.get(MusicianProfile, user_id)`.

**Commit.** `fix(v6): T-V6-19 — lote backend: membresía única, liquidaciones ex-miembros, reference_url, búsqueda, límites, dotenv, plan, get_db, perfil`

---

## 3. Fase V6-F2 · Base técnica mínima

### T-V6-21 · CI como gate real (M)

**Archivos.** `.github/workflows/ci.yml`, ajustes del repo en GitHub (lo hace Oscar o la IA con
`gh` si tiene permisos).

**Pasos.**

1. Sustituye `ci.yml` por esta estructura (mantén el paso que crea el `.env` dummy):
   ```yaml
   name: CI
   on:
     pull_request:
     push:
       branches: [main]
   permissions:
     contents: read
   concurrency:
     group: ci-${{ github.ref }}
     cancel-in-progress: true
   jobs:
     secrets:        # (de T-V6-01)
       runs-on: ubuntu-latest
       steps:
         - uses: actions/checkout@<SHA de v4>
           with: { fetch-depth: 0 }
         - uses: gitleaks/gitleaks-action@<SHA de v2>
           env: { GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }} }
     lint-unit:
       runs-on: ubuntu-latest
       timeout-minutes: 10
       steps:
         - uses: actions/checkout@<SHA>
         - uses: actions/setup-python@<SHA de v5>
           with: { python-version: "3.12", cache: pip }
         - run: python -m pip install -r requirements.txt -r requirements-dev.txt
         - run: printf 'LOG_LEVEL=INFO\n' > .env && printf 'SUPABASE_URL=https://dummy.supabase.co\nSUPABASE_ANON_KEY=dummy\n' > .env.local
         - run: python -m ruff check .
         - run: python -m pip_audit -r requirements.txt     # (T-V6-22)
         - run: python -m pytest tests/unit -m unit -q
     e2e:
       runs-on: ubuntu-latest
       timeout-minutes: 20
       needs: lint-unit
       steps:
         - uses: actions/checkout@<SHA>
         - uses: actions/setup-python@<SHA>
           with: { python-version: "3.12", cache: pip }
         - run: python -m pip install -r requirements.txt -r requirements-dev.txt
         - run: python -m playwright install --with-deps chromium
         - run: printf 'LOG_LEVEL=INFO\n' > .env && printf 'SUPABASE_URL=https://dummy.supabase.co\nSUPABASE_ANON_KEY=dummy\n' > .env.local
         - run: python harness/doctor.py
         - run: python -m pytest tests/e2e -m e2e -q --tracing=retain-on-failure --output=test-results
         - uses: actions/upload-artifact@<SHA de v4>
           if: failure()
           with: { name: playwright-traces, path: test-results }
     migrations-pg:   # (T-V6-23 lo rellena)
       runs-on: ubuntu-latest
       ...
   ```
   Para los `<SHA>`: abre la página de releases de cada acción en GitHub y copia el commit SHA de
   la versión (no uses tags). Añade un comentario `# v4.x.y` al lado.
2. `tests/conftest.py`: en el teardown del `live_server` NO borres `test_e2e_server.log` cuando
   `os.getenv("CI")` (para subirlo como artefacto); añade su ruta al `upload-artifact`.
3. **Branch protection** (Oscar en GitHub → Settings → Branches → `main`): "Require status checks
   to pass" con `lint-unit` y `e2e`; "Require pull request before merging". Documenta en README.
4. Verifica: abre un PR con un fallo de lint a propósito → el PR queda bloqueado.

**Commit.** `chore(v6): T-V6-21 — CI por jobs, acciones por SHA, permisos mínimos, artefactos y gate en main`

---

### T-V6-22 · Lockfile, auditoría y Dependabot (S)

**Pasos.**

1. `pip install pip-tools pip-audit`. Renombra `requirements.txt` → `requirements.in` (con los
   pins actuales) y `requirements-dev.txt` → `requirements-dev.in` (pinea `pytest==…`,
   `pytest-playwright==…`, `playwright==…`, `httpx==…`, `ruff==…`, `black==…`, `pip-audit`,
   `pip-tools` a las versiones que tengas instaladas: `pip freeze | grep -i <nombre>`).
2. `pip-compile --generate-hashes requirements.in -o requirements.txt` y lo mismo para dev.
   Vercel sigue leyendo `requirements.txt` (ahora completo y con hashes).
3. `.github/dependabot.yml`:
   ```yaml
   version: 2
   updates:
     - package-ecosystem: pip
       directory: "/"
       schedule: { interval: weekly }
     - package-ecosystem: github-actions
       directory: "/"
       schedule: { interval: weekly }
   ```
4. `.gitignore`: `.env.*` y `!.env.example` (si no se hizo en T-V6-01).
5. Documenta en README: "para añadir una dependencia: editar `.in` y recompilar".

**Commit.** `chore(v6): T-V6-22 — requirements compilados con hashes, pip-audit y Dependabot`

---

### T-V6-23 · Migraciones reproducibles en Postgres + job de CI (M)

**Pasos.**

1. `alembic/versions/20260614_0226_147a6a78da86_…py`: cambia los dos
   `server_default=sa.text('0')` de columnas **booleanas** (`is_public` ≈ línea 39, y el otro
   ≈ 43 si es booleano) por `server_default=sa.false()`. Los de enteros (`120`, `4`, `1`) se
   quedan.
2. Prueba en local contra un Postgres de Docker: `docker run -e POSTGRES_PASSWORD=pg -p 5433:5432 postgres:16`
   y `DATABASE_URL=postgresql://postgres:pg@localhost:5433/postgres python -m alembic upgrade head`
   → `alembic check` → `alembic downgrade base` → `upgrade head`. Arregla lo que falle (también
   `Numeric`, `JSON`, CHECKs) hasta que las 20 pasen.
3. Job `migrations-pg` en `ci.yml`:
   ```yaml
     migrations-pg:
       runs-on: ubuntu-latest
       services:
         postgres:
           image: postgres:16
           env: { POSTGRES_PASSWORD: pg }
           ports: ["5432:5432"]
           options: >-
             --health-cmd "pg_isready" --health-interval 5s --health-timeout 5s --health-retries 10
       steps:
         - uses: actions/checkout@<SHA>
         - uses: actions/setup-python@<SHA>
           with: { python-version: "3.12", cache: pip }
         - run: python -m pip install -r requirements.txt -r requirements-dev.txt
         - env: { DATABASE_URL: postgresql://postgres:pg@localhost:5432/postgres }
           run: |
             python -m alembic upgrade head
             python -m alembic check
             python -m alembic downgrade base
             python -m alembic upgrade head
             python -m pytest tests/unit -m unit -q      # (T-V6-27 permite PG en unit: hasta entonces, omite esta línea)
   ```
4. `tests/unit/test_migrations.py`: añade un test marcado `@pytest.mark.skipif(not PG_URL)` que
   corre `upgrade head` contra `TEST_PG_URL` si está definida.

**Commit.** `fix(v6): T-V6-23 — migración 147a6a78da86 válida en Postgres y job de CI que la prueba`

---

### T-V6-24 · Estáticos servidos por Vercel, no por la función (M)

**Pasos.**

1. Crea `public/` en la raíz y **mueve** `static/` dentro: `public/static/…` (git mv). Actualiza
   las rutas: `src/main.py` (`_STATIC_DIR = … / "public" / "static"`), `harness/cachebust.py`
   (`STATIC = ROOT / "public" / "static"`), `harness/doctor.py`, `tests/` (busca `"static"` y
   `static/` en Python), `.vercelignore` (no excluir `public/`), `pyproject.toml` (ruff/black
   `extend-exclude` → `public/static`).
2. `vercel.json` (formato moderno):
   ```json
   {
     "functions": { "api/index.py": { "maxDuration": 30 } },
     "rewrites": [
       { "source": "/static/(.*)", "destination": "/static/$1" },
       { "source": "/(.*)", "destination": "/api/index.py" }
     ],
     "headers": [
       { "source": "/static/(.*)\\.(js|css|png|woff2)", "headers": [ { "key": "Cache-Control", "value": "public, max-age=31536000, immutable" } ] },
       { "source": "/static/(.*)\\.html", "headers": [ { "key": "Cache-Control", "value": "no-cache" } ] }
     ]
   }
   ```
   Vercel sirve `public/` como estático antes de las rewrites: `/static/x.js` lo sirve el CDN y
   nunca llega a Python. El `app.mount("/static", …)` se mantiene para local y tests.
3. Comprueba en un deploy de preview: `curl -I https://<preview>/static/app.html` → cabeceras
   `x-vercel-cache: HIT/MISS` y `cache-control` esperado; `/health` sigue respondiendo desde
   Python. Mide el cold start de `/health` antes y después y anótalo en el registro.
4. **Riesgo:** si Vercel no respeta `?v=` como clave distinta (sí lo hace), la caché inmutable
   serviría JS viejo tras un deploy. Verifica cambiando un `.js`, desplegando y pidiendo el nuevo
   `?v=`.

**Commit.** `chore(v6): T-V6-24 — estáticos en public/ servidos por Vercel con Cache-Control; la función solo API`

---

### T-V6-25 · Tooling de JS sin bundler: ESLint, typecheck y tests en Node (M)

**Pasos.**

1. `package.json` en la raíz:
   ```json
   {
     "name": "bandflow-frontend", "private": true, "type": "module",
     "scripts": {
       "lint": "eslint public/static --ext .js",
       "typecheck": "tsc -p jsconfig.json",
       "test": "vitest run",
       "check": "npm run lint && npm run typecheck && npm test"
     },
     "devDependencies": { "eslint": "^9", "@eslint/js": "^9", "globals": "^15", "typescript": "^5", "vitest": "^2", "jsdom": "^25" }
   }
   ```
   `npm install`; añade `node_modules/` al `.gitignore` y `package-lock.json` al repo.
2. `eslint.config.js` (flat config) con `@eslint/js` recommended + `globals.browser` + las
   globales propias del proyecto como `readonly` (`escapeHtml`, `bfIcon`, `apiFetch`, `toast`,
   `bandColor`, `initialsFrom`, `confirmModal`, `promptModal`, `bfAvatar`, `bfSkeletonList`,
   `bfEmpty`, `requireAuth`, `getToken`, `signOut`, `SyncEngine`, `renderScoreInto`,
   `transposeChord`, `bfMetronomeClick`, `bfBeatAccent`, `bfHoldRepeat`, `BfMetronome`…).
   Reglas que importan: `no-undef`, `no-unused-vars` (warn), `no-redeclare`, `eqeqeq`.
   Corrige lo que salga (habrá decenas de avisos de variables globales duplicadas: es el mapa
   de lo que T-V6-26 debe modular).
3. `jsconfig.json`: `{ "compilerOptions": { "checkJs": true, "noEmit": true, "target": "es2022", "lib": ["es2022","dom"], "allowJs": true, "strict": false }, "include": ["public/static/**/*.js"] }`.
   Al principio habrá errores; marca con `// @ts-check` solo los ficheros que vayas limpiando
   (empieza por `util.js`, `metronome.js`, `sync_engine.js`, `score_render.js`).
4. Tests en Node (`tests/js/*.test.js`, con Vitest + jsdom): como los ficheros son scripts
   clásicos (no exportan), carga el fuente con `fs.readFileSync` + `new Function` en un contexto
   jsdom **hasta** que T-V6-26 los convierta en módulos. Prueba: `transposeChord('Bb', 3) === 'Db'`,
   `parseRawText(SAMPLE)` (de `editor.js`) detecta `Am`, `freqToNote(440) → 'A4'`,
   `bfFinanceBySeason`, `initialsFrom('Oscar (tú)') === 'O'`.
5. `harness/run_checks.py`: añade el paso `("npm check (lint+typecheck+vitest)", ["npm", "run", "check"])`
   solo si `shutil.which("npm")` existe (para no romper máquinas sin Node). CI: añade
   `actions/setup-node` + `npm ci` + `npm run check` en el job `lint-unit`.
6. `tests/e2e/test_js_logic.py`: los casos que ahora cubra Vitest se eliminan de aquí (deja los
   que necesiten DOM real).

**Commit.** `chore(v6): T-V6-25 — ESLint, typecheck (checkJs) y Vitest para la lógica pura; integrado en run_checks`

---

### T-V6-26 · Módulos ES `core/` y `ui/` con doble export (M)

**Objetivo.** Empezar la modularización sin romper nada: los módulos nuevos **exportan** y además
**cuelgan de `window`** mientras existan scripts clásicos que los usen.

**Decisión previa (D-V6-2):** sin Vite. El versionado de `import` se resuelve con un **import map**
generado por `cachebust.py`.

**Pasos.**

1. Estructura nueva en `public/static/`:
   ```
   core/api.js       ← apiFetch, apiJson, ApiError (sale de auth.js)
   core/session.js   ← getConfig, getSession, requireAuth, caché por página de /profile/me y /bands/
   core/format.js    ← fmtMoney, fmtDate, fmtDateLong, toApiDate, fromApiDate  (T-V6-36)
   core/labels.js    ← ROLE_LABEL, ATT_LABEL, EVENT_TYPE_LABEL, EVENT_STATUS_LABEL, EV_ICON (nombres de icono)
   ui/dialog.js      ← bfDialog, confirmModal, promptModal, alertModal (T-V6-33)
   ui/toast.js       ← toast
   ui/menu.js        ← bfMenu (T-V6-32)
   ui/icons.js       ← bfIcon, bfApplyIcons (hoy icons.js)
   ```
   Cada módulo termina con un bloque de compatibilidad:
   ```js
   // Compat temporal: scripts clásicos siguen viendo estas funciones como globales.
   Object.assign(window, { apiFetch, apiJson, ApiError });
   ```
2. `cachebust.py`: además de los `?v=`, genera en cada HTML un
   `<script type="importmap">{"imports":{"/static/core/api.js":"/static/core/api.js?v=<hash>", …}}</script>`
   (una entrada por módulo) y reescribe los `import` internos para usar los specifiers
   **sin** `?v=` (la import map los resuelve). El test `test_cache_busting_al_dia` debe cubrir
   también la import map.
3. En cada HTML: antes de los scripts clásicos, `<script type="module" src="core/boot.js?v=…"></script>`
   donde `boot.js` importa los módulos y expone las globales. Como los módulos se ejecutan
   diferidos, los scripts clásicos que usan esas globales en el arranque deben esperar: envuelve
   su `mount()` en `window.addEventListener('bf:ready', …)` que `boot.js` dispara al final.
   (Alternativa más simple: convierte también esos scripts a `type="module"` e importa lo que
   necesiten; hazlo página a página.)
4. Orden de conversión de las páginas a módulos (sin cambiar ids): app → agenda → chat →
   finanzas → bands/band → library/setlists → profile → catalogo → join/evento/login →
   editor → index (último, con sus e2e completos).
5. Verifica con `npm run check` y la suite e2e completa tras cada página.

**Commit (por página).** `refactor(v6): T-V6-26 — <página> a módulos ES (core/ui con doble export)`

---

### T-V6-27 · Gates de aislamiento y de rol derivados de `app.routes`; fixtures; tests herméticos (M)

**Pasos.**

1. `tests/conftest.py`: añade las fixtures
   ```python
   STRANGER = "99999999-9999-9999-9999-999999999999"

   @pytest.fixture()
   def acting_as():
       from src.main import app
       from src.services.auth import get_current_user
       @contextlib.contextmanager
       def _as(user_id):
           app.dependency_overrides[get_current_user] = lambda: user_id
           try: yield
           finally: app.dependency_overrides.pop(get_current_user, None)
       return _as
   ```
   y sustituye las 11 copias de `acting_as` en `tests/unit/*.py` por la fixture.
2. Reescribe `tests/unit/test_aislamiento_parametrizado.py`:
   ```python
   from fastapi.routing import APIRoute
   from src.main import app

   def rutas_de_banda():
       for r in app.routes:
           if isinstance(r, APIRoute) and "{band_id}" in r.path:
               for m in r.methods - {"HEAD", "OPTIONS"}:
                   yield m, r.path, r

   @pytest.mark.parametrize("method,path,route", list(rutas_de_banda()), ids=lambda x: str(x)[:60])
   def test_ruta_de_banda_exige_guard_y_aisla(client, acting_as, method, path, route):
       nombres = {d.call.__name__ for d in route.dependant.dependencies}
       assert nombres & {"require_band_member", "require_band_admin"}, f"{method} {path} sin guard"
       bid = client.post("/bands/", json={"name": "B"}).json()["id"]
       url = path.replace("{band_id}", bid)
       for k in ("{setlist_id}","{event_id}","{song_id}","{tx_id}","{settlement_id}","{message_id}","{tour_id}","{stop_id}","{line_id}","{venue_id}","{collection_id}","{user_id}","{invite_id}"):
           url = url.replace(k, "00000000-0000-0000-0000-000000000001")
       with acting_as(STRANGER):
           assert client.request(method, url, json={}).status_code in (403, 404)
       # El dueño NO recibe 404 por la banda (puede recibir 404 por el sub-recurso inexistente, 422, 400…)
       assert client.request(method, url, json={}).status_code != 403
   ```
   (La aserción del dueño demuestra que la ruta existe para él; afina si alguna devuelve 403
   legítimo por rol.)
3. Gate de rol: mismo recorrido para `POST/PUT/PATCH/DELETE`, creando un miembro `guest`
   (invitación con `role_to_grant: guest` aceptada con `acting_as(GUEST)`) → debe dar 403 salvo
   las rutas marcadas en una lista blanca (`POST …/messages/` y `…/attendance`, que un guest sí
   puede usar).
4. SQLite en memoria: en `conftest.py`, `os.environ["DATABASE_URL"] = "sqlite://"` y en `db.py`
   usa `poolclass=StaticPool, connect_args={"check_same_thread": False}` cuando la URL es
   `sqlite://` (sin fichero). Los tests pasan a tardar menos.
5. `pytest-randomly` en `requirements-dev.in`; corre la suite 3 veces; arregla dependencias de
   orden que aparezcan (normalmente `wipe_*` que faltan).
6. e2e herméticos: en `conftest.py`, fixture `page` que hace
   `page.route(re.compile(r"https://(fonts\.googleapis\.com|fonts\.gstatic\.com|cdn\.jsdelivr\.net)/.*"), lambda r: r.abort())`
   (hasta que T-V6-31 autoaloje fuentes y el SDK). Sustituye los `wait_for_timeout` que queden por
   esperas de selector/respuesta.

**Commit.** `test(v6): T-V6-27 — gates de aislamiento y rol derivados de app.routes, fixtures, SQLite en memoria, e2e herméticos`

---

### T-V6-28 · JWT verificado localmente con JWKS (M)

**Pasos.**

1. `requirements.in`: `PyJWT[crypto]==2.9.0` (o la última 2.x). Recompila.
2. Nuevo `src/services/auth_provider.py` → clase `SupabaseJwksProvider`:
   ```python
   import jwt, time, threading
   from jwt import PyJWKClient

   class SupabaseJwksProvider:
       def __init__(self, url, anon_key, timeout=5.0):
           self._jwks = PyJWKClient(f"{url}/auth/v1/.well-known/jwks.json", cache_keys=True, lifespan=3600)
           self._fallback = SupabaseAuthProvider(url, anon_key, timeout)
       def validate(self, token: str) -> dict | None:
           try:
               key = self._jwks.get_signing_key_from_jwt(token).key
               claims = jwt.decode(token, key, algorithms=["ES256", "RS256"], audience="authenticated",
                                   options={"require": ["exp", "sub"]})
               return {"id": claims["sub"]}
           except jwt.ExpiredSignatureError:
               return None                       # expirado: 401, sin preguntar a Supabase
           except jwt.PyJWKClientError:
               return self._fallback.validate(token)   # kid desconocido / JWKS inaccesible → remoto
           except jwt.InvalidTokenError:
               return None
   ```
   (Si el proyecto de Supabase aún firma con HS256 y secreto compartido, el JWKS no tendrá
   claves: Oscar debe migrar a "JWT signing keys" en el panel de Supabase — Settings → JWT keys.
   Hasta entonces, mantén el proveedor remoto.)
3. `build_auth_provider`: `name == "supabase-jwks"` → el nuevo; `settings.chordflow_auth_provider`
   por defecto `"supabase-jwks"`.
4. `auth.py`: con verificación local ya no hace falta la caché por token para rendimiento, pero
   déjala (reduce coste de firma); la **ventana de gracia** solo se aplica cuando `validate`
   lanzó un error de red (haz que el proveedor devuelva `None` en "rechazado" y lance
   `AuthUnavailable` en "no se pudo comprobar"), no cuando el token es inválido.
5. Tests: genera un par de claves ES256 en el test, publica un JWKS falso con `monkeypatch` del
   `PyJWKClient`, firma un token válido / expirado / con `aud` incorrecta y comprueba 200/401/401.

**Commit.** `feat(v6): T-V6-28 — verificación local de JWT con JWKS (fallback remoto solo ante kid desconocido)`

---

### T-V6-29 · Observabilidad: request-id, logs JSON, Sentry, uptime (S)

**Pasos.**

1. Middleware en `main.py`:
   ```python
   import uuid, time
   @app.middleware("http")
   async def request_context(request, call_next):
       rid = request.headers.get("x-request-id") or uuid.uuid4().hex[:12]
       t0 = time.perf_counter()
       response = await call_next(request)
       response.headers["X-Request-ID"] = rid
       logger.info("req", extra={"rid": rid, "method": request.method, "path": request.url.path,
                                 "status": response.status_code, "ms": round((time.perf_counter()-t0)*1000)})
       return response
   ```
2. `logging_config.py`: formateador JSON (una línea por evento con `ts, level, logger, msg,
   rid, method, path, status, ms`) cuando `CHORDFLOW_LOG_STDOUT=1` (que será el valor en Vercel).
3. Sentry: `sentry-sdk[fastapi]` en `requirements.in`; en `main.py`
   `if settings.sentry_dsn: sentry_sdk.init(dsn=settings.sentry_dsn, traces_sample_rate=0.1, environment=os.getenv("VERCEL_ENV","local"))`.
   Front: `public/static/core/errors.js` que registra `window.onerror` y `unhandledrejection` y
   los manda a `POST /client-errors` (endpoint propio, rate-limited, que reenvía a Sentry) — así
   no hace falta cargar el SDK de Sentry en el navegador.
4. UptimeRobot (Oscar): monitor HTTP a `https://<dominio>/health` cada 5 min con aviso por email.
5. Variables en Vercel: `CHORDFLOW_LOG_STDOUT=1`, `SENTRY_DSN=…`.

**Commit.** `chore(v6): T-V6-29 — X-Request-ID, logs JSON, Sentry back y errores de cliente`

---

### T-V6-30 · README, SECURITY, CHANGELOG, archivo de guías y limpieza de docs (S)

**Pasos.**

1. `README.md` (máx. 60 líneas): qué es BandFlow, stack, cómo arrancar (§0.2 de este manual
   resumido), cómo probar, cómo desplegar, dónde está cada cosa (enlaces a Parte I/II, CLAUDE.md,
   ROADMAP), estado de producción.
2. `SECURITY.md`: cómo reportar, política de secretos, rotación.
3. `CHANGELOG.md`: formato Keep a Changelog; primera entrada "Unreleased" con las T-V6 cerradas.
4. Mueve `GUIA_MAESTRA.md`, `_V2*`, `_V3`, `_V4_*` y `directives/` a `docs/archive/` (git mv) y
   deja en su sitio un `docs/archive/README.md` que diga que son historial. `harness/MOLDE.md`
   también.
5. `docs/adr/0001-auth-supabase.md`, `0002-multi-tenant.md`, `0003-serverless-vercel.md`,
   `0004-fechas-utc.md`, `0005-sistema-de-diseno.md`, `0006-esm-sin-bundler.md` (una página cada
   uno: contexto, decisión, consecuencias).
6. Corrige las contradicciones de la Parte I §13.D (head de prod, repo privado, migraciones,
   `revision.py` → o se actualiza o se retira la regla de `CLAUDE.md` §2 "revisión por sección").
7. `CLAUDE.md`: cabecera que apunte a `GUIA_MAESTRA_V6.md` (cómo) + `GUIA_MAESTRA_V5.md` (qué),
   mapa rápido con `core/`, `ui/`, `public/static`, y la regla "no emoji / no hex" en §4.

**Commit.** `docs(v6): T-V6-30 — README, SECURITY, CHANGELOG, ADRs, guías archivadas y contradicciones corregidas`

---

## 4. Fase V6-F3 · Sistema de diseño 2.0

> Regla de la fase: **no cambies ids ni `data-*`** (Anexo A). Cambias clases de estilo, estructura
> interna y CSS. Cada tarea termina con capturas en oscuro/claro y escritorio/móvil.

### T-V6-31 · Tokens nuevos, fuentes autoalojadas, escala tipográfica (M)

**Pasos.**

1. **Fuentes.** Descarga IBM Plex Sans (400/500/600/700) e IBM Plex Mono (400/500/600) en
   `woff2` desde el repo oficial de IBM Plex (licencia OFL) a `public/static/fonts/`. En
   `design-system.css` sustituye el `@import url('https://fonts.googleapis.com/…')` por:
   ```css
   @font-face { font-family: 'IBM Plex Sans'; font-weight: 400; font-display: swap; src: url('fonts/IBMPlexSans-Regular.woff2') format('woff2'); }
   /* …500, 600, 700 y las tres de Mono… */
   ```
   Quita el `@import` duplicado de `style.css:2`, el `<link>` de `evento.html:12` y los `<link>`
   a Inter/Roboto de las 11 páginas (grep `fonts.googleapis`). En cada HTML añade
   `<link rel="preload" href="fonts/IBMPlexSans-Regular.woff2" as="font" type="font/woff2" crossorigin>`.
2. **Tokens.** En `:root` de `design-system.css` añade (y en el bloque `[data-theme="light"]` solo
   los que cambian de color):
   ```css
     --bf-fs-3xl: 2.25rem;  --bf-lh-tight: 1.2;  --bf-lh-base: 1.5;
     --bf-z-dropdown: 100; --bf-z-sticky: 200; --bf-z-overlay: 1000; --bf-z-dialog: 1010; --bf-z-toast: 1100;
     --bf-control-sm: 32px; --bf-control: 40px; --bf-control-lg: 48px;
     --bf-row-h: 56px; --bf-content-max: 1120px; --bf-content-wide: 1400px;
     --bf-focus-ring: 0 0 0 3px var(--bf-accent-weak);
     /* paleta de banda/usuario (8 fijos) */
     --bf-band-1: #ff6b4a; --bf-band-2: #2dd4a7; --bf-band-3: #60a5fa; --bf-band-4: #f5c518;
     --bf-band-5: #c084fc; --bf-band-6: #fb7185; --bf-band-7: #34d399; --bf-band-8: #f97316;
   ```
   Radios: deja `--bf-radius-sm: 6px; --bf-radius: 10px; --bf-radius-lg: 16px; --bf-radius-full`
   y elimina usos de otros radios al migrar (T-V6-37).
3. **Escala.** Sustituye en `design-system.css`/`shell.css` cualquier `font-size` que no sea un
   token por el token más cercano. `style.css` se hace en T-V6-37. Los `h1/h2/h3` de todas las
   páginas usan `.bf-h1/.bf-h2/.bf-h3`.
4. `util.js`: `bandColor(id)` pasa a devolver `var(--bf-band-N)` con `N = (hash(id) % 8) + 1` y
   se añade `userColor(userId)` con el mismo mecanismo; `bfAvatar` usa `userColor` cuando recibe
   `userId` (el perfil, el lateral y Miembros pasan el `user_id` → mismo color en todas partes).
5. `test_design_system.py`: sustituye las aserciones de color exacto por "los tokens de esta
   lista existen" (es el test de reglas de D-V6-12).

**Commit.** `style(v6): T-V6-31 — fuentes autoalojadas, tokens de escala/z-index/control/paleta, color estable de usuario`

---

### T-V6-32 · Componentes canónicos (L)

**Entregable:** `public/static/_components.html` (página de muestra, sin shell, fuera del menú)
con TODOS los componentes en oscuro y claro, más el CSS en `design-system.css` (o un nuevo
`components.css` cargado detrás).

**Pasos (en este orden; cada bloque es un sub-commit):**

1. **Botón.** Añade tamaños y estados a `.bf-btn`: altura fija `height: var(--bf-control)`,
   `--sm` 32 px, `--lg` 48 px, `--secondary` (borde `--bf-border-strong`, fondo transparente),
   `.is-loading` (spinner `::after`, `pointer-events:none`), `[disabled]` (opacity .5). **Unifica
   el legacy**: en `style.css` cambia las reglas de `.primary-btn` y `.secondary-btn` para que
   hereden exactamente los tokens de `.bf-btn`/`--primary`/`--secondary` (misma altura, radio
   `--bf-radius`, sin píldora, texto `--bf-on-primary`). El reproductor queda igual de funcional
   pero coherente. `.icon-btn` → mismas medidas que `.bf-btn--icon` (40×40).
2. **Segmented control.**
   ```css
   .bf-segmented { display:inline-flex; background: var(--bf-surface-2); border:1px solid var(--bf-border); border-radius: var(--bf-radius); padding:2px; }
   .bf-segmented > button { height: calc(var(--bf-control-sm) - 4px); padding:0 .7rem; border:0; background:transparent; color: var(--bf-text-muted); border-radius: calc(var(--bf-radius) - 2px); font: inherit; font-size: var(--bf-fs-sm); cursor:pointer; display:inline-flex; align-items:center; gap:.35rem; }
   .bf-segmented > button[aria-pressed="true"] { background: var(--bf-surface); color: var(--bf-text); box-shadow: var(--bf-shadow-sm); }
   .bf-segmented > button[aria-pressed="true"].is-yes { color: var(--bf-success); }
   .bf-segmented > button[aria-pressed="true"].is-maybe { color: var(--bf-warning); }
   .bf-segmented > button[aria-pressed="true"].is-no { color: var(--bf-danger); }
   ```
   JS: `bfSegmented(el, onChange)` que gestiona `aria-pressed` y teclado (flechas).
   **Importante:** los botones de asistencia conservan `class="att-btn"` y `data-att="yes|maybe|no"`
   (los usan los tests); solo se añaden las clases nuevas.
3. **Menú ⋯** (`ui/menu.js`): `bfMenu(anchorBtn, items)` donde `items = [{label, icon, onClick, danger}]`;
   popover posicionado bajo el botón (`position: fixed` + cálculo con `getBoundingClientRect`),
   `role="menu"`, flechas/Escape/clic fuera, `z-index: var(--bf-z-dropdown)`, tema. Sustituye a
   `.ev-more-menu`.
4. **Fila.** Nuevo bloque (no reutilices `.bf-row`, que hoy es un flex genérico; llama al nuevo
   `.bf-item`):
   ```css
   .bf-item { display:flex; align-items:center; gap: var(--bf-space-3); min-height: var(--bf-row-h); padding: var(--bf-space-2) var(--bf-space-3); border-bottom:1px solid var(--bf-border); }
   .bf-item:hover { background: var(--bf-hover); }
   .bf-item__lead { flex: 0 0 auto; display:flex; align-items:center; color: var(--bf-text-muted); }
   .bf-item__main { flex:1 1 auto; min-width:0; }
   .bf-item__title { font-weight: var(--bf-fw-medium); overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
   .bf-item__meta { font-size: var(--bf-fs-sm); color: var(--bf-text-muted); display:flex; gap:.5rem; flex-wrap:wrap; }
   .bf-item__trail { flex:0 0 auto; display:flex; align-items:center; gap: var(--bf-space-2); }
   @media (max-width: 768px) { .bf-item { flex-wrap: wrap; } .bf-item__trail { flex-basis:100%; justify-content:flex-end; } }
   ```
5. **Tarjeta.** A `.bf-card` añade `--cover` (cabecera de 96 px con `background: linear-gradient(135deg, var(--band), color-mix(in srgb, var(--band) 60%, black))` o imagen) y `--stat`
   (valor grande + etiqueta). Toda tarjeta clicable lleva un `<a class="bf-card__link">` que
   cubre el título (teclado).
6. **Campo.** `.bf-field { display:grid; gap:.35rem; margin-bottom: var(--bf-space-4); }`,
   `.bf-label` (xs, uppercase opcional NO: sentence case, `--bf-text-muted`), `.bf-input/.bf-select/
   .bf-textarea` a `height: var(--bf-control)` (textarea auto), `.bf-select` con flecha SVG en
   `background-image` y `appearance:none`, `.bf-help` (xs muted), `.bf-error` (xs danger),
   `.bf-input[aria-invalid="true"]` borde danger. `.bf-check` (checkbox con label).
7. **Buscador.** `.bf-search` = `.bf-input` con icono `search` a la izquierda (`padding-left: 2.2rem`)
   y botón limpiar.
8. **Pestañas.** A `.bf-tabs/.bf-tab` añade `role` correcto, `aria-controls`, contador
   `.bf-tab__count`, scroll horizontal con máscara `mask-image: linear-gradient(90deg, #000 90%, transparent)`
   en móvil, y navegación por flechas (JS en `ui/tabs.js`).
9. **Badge / chip.** `.bf-badge` sin `text-transform`; `.bf-chip` (filtro) con `aria-pressed`,
   `.bf-chip__dot` (color de banda) y `.bf-chip--removable`.
10. **Avatar.** `bfAvatar({url, name, userId, bandId, size})` con `--xs 24 / --sm 32 / 40 / --lg 56 / --xl 80`
    y `.bf-avatar-stack` (solapados, borde del fondo).
11. **Toast** (`ui/toast.js`): `toast(message, type, {action:{label, onClick}})`, `aria-live`,
    `z-index: var(--bf-z-toast)`.
12. **Estados.** `bfEmpty({icon, title, text, cta})` (ya existe, añade `cta`), `bfErrorState(msg, retry)`
    (de T-V6-15), `.bf-skeleton` ya existe.
13. **Cabecera de página.** `.bf-page-header { display:flex; align-items:flex-end; justify-content:space-between; gap:1rem; margin-bottom: var(--bf-space-5); }`
    con `.bf-page-header__title` (h1) y `__actions`.
14. **Topbar móvil.** En `shell.js`, junto al ☰, pinta `<div class="bf-topbar__title">` con el
    `document.title` sin el prefijo "BandFlow — " y un hueco `#bf-topbar-action` donde cada página
    puede mover su acción primaria en móvil.
15. **KPI, importe, fecha.** `.bf-stat` (valor `--bf-fs-2xl` mono tabular + etiqueta sm muted),
    `.bf-amount` (`--pos/--neg/--zero`, mono), `.bf-date` (`title` con fecha larga).
16. **Calendario y drawer** se construyen en T-V6-62 y T-V6-42b respectivamente, pero reserva
    ya las clases (`.bf-calendar`, `.bf-drawer`) en la página de muestra como "pendiente".

**Comprobación.** `_components.html` revisado en los dos temas y a 390 px; `npm run check` verde;
suite e2e completa verde (no se han tocado ids).

**Commit (por bloque).** `style(v6): T-V6-32 — componente <nombre>`

---

### T-V6-33 · `bfDialog()` único y migración de los 9 modales (M)

**Pasos.**

1. `ui/dialog.js`:
   ```js
   export function bfDialog({ title, body, actions = [], size = 'md', onClose }) {
       const prev = document.activeElement;
       const overlay = document.createElement('div');
       overlay.className = 'bf-overlay';
       overlay.innerHTML = `
         <div class="bf-dialog bf-dialog--${size}" role="dialog" aria-modal="true" aria-labelledby="bfd-title">
           <header class="bf-dialog__head"><h2 id="bfd-title" class="bf-h2">${escapeHtml(title)}</h2>
             <button class="bf-btn bf-btn--ghost bf-btn--icon" data-act="close" aria-label="Cerrar">${bfIcon('x')}</button></header>
           <div class="bf-dialog__body"></div>
           <footer class="bf-dialog__foot"></footer>
         </div>`;
       const bodyEl = overlay.querySelector('.bf-dialog__body');
       if (typeof body === 'string') bodyEl.innerHTML = body; else bodyEl.appendChild(body);
       const foot = overlay.querySelector('.bf-dialog__foot');
       actions.forEach(a => {
           const b = document.createElement('button');
           b.className = `bf-btn ${a.primary ? 'bf-btn--primary' : a.danger ? 'bf-btn--danger' : 'bf-btn--secondary'}`;
           b.textContent = a.label; b.type = 'button';
           b.addEventListener('click', async () => { const r = await a.onClick?.(api); if (r !== false) api.close(a.value); });
           foot.appendChild(b);
       });
       const focusables = () => overlay.querySelectorAll('button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])');
       function onKey(e) {
           if (e.key === 'Escape') return api.close();
           if (e.key === 'Tab') { const f = focusables(); if (!f.length) return;
               const first = f[0], last = f[f.length - 1];
               if (e.shiftKey && document.activeElement === first) { e.preventDefault(); last.focus(); }
               else if (!e.shiftKey && document.activeElement === last) { e.preventDefault(); first.focus(); } }
       }
       const api = { el: overlay, close(value) { document.removeEventListener('keydown', onKey); overlay.remove(); onClose?.(value); prev?.focus?.(); } };
       overlay.addEventListener('click', e => { if (e.target === overlay || e.target.closest('[data-act="close"]')) api.close(); });
       document.addEventListener('keydown', onKey);
       document.body.appendChild(overlay);
       (overlay.querySelector('[autofocus]') || overlay.querySelector('.bf-dialog__foot .bf-btn--secondary') || focusables()[0])?.focus();
       return api;
   }
   ```
   CSS: `.bf-overlay` (fixed, `z-index: var(--bf-z-overlay)`, fondo `rgba(0,0,0,.55)`),
   `.bf-dialog` (`--bf-surface`, radio lg, sombra lg, `max-height: 90dvh`, grid head/body/foot
   con body scrollable, `width: min(100% - 2rem, 480px)`; `--lg` 720 px; en ≤ 768 px: hoja
   inferior `position:fixed; bottom:0; border-radius: lg lg 0 0; width:100%`).
2. Reimplementa `confirmModal/promptModal/alertModal` sobre `bfDialog` conservando su firma y
   sus Promises (los tests usan `.modal-card`/`.modal-overlay`: añade ESAS clases como alias en
   los elementos nuevos — `className = 'bf-overlay modal-overlay'`, `'bf-dialog modal-card'` —
   hasta que T-V6-27/58 actualice los tests). `confirm` enfoca **Cancelar**; Enter no confirma.
3. Migra los 7 modales de `bands.js` (invitar, nuevo evento, nuevo movimiento, liquidar, nueva
   sala, nuevo setlist/colección, nueva gira) y los 2 de `library.js`: su contenido pasa a un
   `body` con `.bf-field` y los ids de los inputs **no cambian** (`#ev-title`, `#tx-amount`…).
4. "Deshacer": en quitar canción de setlist (`setlists.js:247`, `band.js:425,432`) no confirmes;
   quita y muestra `toast('Canción quitada', 'info', {action:{label:'Deshacer', onClick: reponer}})`.

**Commit.** `refactor(v6): T-V6-33 — bfDialog único (focus trap, Escape, hoja inferior) y modales migrados`

---

### T-V6-34 · Barrido emoji → `bfIcon` (M)

**Pasos.**

1. Lista exacta de ocurrencias:
   ```bash
   grep -nP "[\x{1F300}-\x{1FAFF}\x{2600}-\x{27BF}]" public/static/*.html public/static/*.js > /tmp/emoji.txt
   ```
   (157 líneas). Trabaja fichero a fichero por este orden: `bands.js` (46), `catalogo.js`,
   `index.html`, `home.js`, `agenda.js`, `library.js`, `join.js`, `app.js`, `setlists.js`,
   `evento.js`, `band.js`, `editor.html`, resto.
2. Para cada emoji usa la tabla de la Parte I §13.A. Patrón: `'🎼 ' + titulo` →
   `bfIcon('list-music', {size:16}) + ' ' + titulo`. Si el icono no existe en `icons.js`,
   añádelo (SVG de Lucide, `viewBox="0 0 24 24"`, `stroke="currentColor"`, `fill="none"`,
   `stroke-width="2"`), con el nombre en kebab-case.
3. Casos especiales: los emoji de **contenido de usuario** (cuerpo de mensajes, nombres) se
   quedan. Los de `index.html` que `paintPlayerIcons()` sustituye en runtime: sustitúyelos en el
   HTML por el SVG directamente y elimina `paintPlayerIcons()` (menos JS, sin parpadeo). El `👋`
   del saludo y los textos de ayuda que citan botones (`library.js:213`, `setlists.js:148`,
   `bands.js:962`) se reescriben sin emoji.
4. Test de reglas (`tests/unit/test_design_rules.py`, nuevo; sustituye a `test_terminologia`/
   `test_rebrand` en lo que solapen): lee los HTML/JS y falla si hay un emoji dentro de
   `<button`, `<h1-3`, `placeholder="`, `aria-label="` o en las plantillas de `bfIcon`-less nav.
   Implementación: regex sobre el texto fuente, lista blanca de ficheros de tests.

**Commit.** `style(v6): T-V6-34 — cero emoji como icono: bfIcon en botones, títulos, placeholders y filas`

---

### T-V6-35 · Tema claro completo: tokens en todo + check automático (M)

**Pasos.**

1. Inventario:
   ```bash
   grep -nE "#[0-9a-fA-F]{3,6}\b|rgba?\(" public/static/style.css | grep -v "^\s*--" > /tmp/colores.txt   # 164 líneas
   grep -nE "#[0-9a-fA-F]{6}\b|rgba?\(" public/static/*.js
   ```
2. Para cada línea: ¿es fondo? → `--bf-surface(-2/-3)`; ¿borde? → `--bf-border(-strong)`;
   ¿texto? → `--bf-text(-muted/-faint)`; ¿acento? → `--bf-primary`; ¿estado? →
   `--bf-success/--bf-danger/--bf-warning/--bf-info` (y `-weak` para fondos); ¿sombra? →
   `--bf-shadow(-sm/-lg)`; ¿blanco translúcido para hover? → `--bf-hover`. Si no encaja en
   ninguno, crea un token nuevo en `:root` (y su valor claro) — nunca dejes el literal.
3. Tokens inexistentes: `--border-color`, `--surface-color`, `--success-color` → sustituye por
   `--bf-border`, `--bf-surface`, `--bf-success` (7 sitios en `style.css` + `tuner.js:119`).
4. `.bf-badge { text-transform: none; }` (F-29). `.bal-pos/.bal-neg` → `.bf-amount--positive/--negative`
   (ya existen). `.setlist-item-btn` → `bf-btn bf-btn--sm bf-btn--icon` (mantén la clase vieja
   como alias si un test la usa; Anexo A).
5. **Check automático** `harness/check_styles.py` (lo llama `run_checks.py`): falla si en
   `public/static/**/*.css` hay `#hex`/`rgba(` fuera de bloques `:root`/`[data-theme]`, o en
   `*.js` cualquier `#hex`. Permite una lista blanca explícita en el propio script (p. ej. el
   negro del modo escenario del reproductor).
6. Recorre las 16 páginas en claro y haz capturas; corrige lo que quede.

**Commit.** `style(v6): T-V6-35 — tema claro completo, cero colores fuera de tokens, check en CI`

---

### T-V6-36 · `format.js` y `labels.js` únicos (S)

**`core/format.js`:**
```js
const LOCALE = 'es-ES';
export function fmtMoney(n, currency = 'EUR') {
    const v = Number(n || 0);
    return new Intl.NumberFormat(LOCALE, { style: 'currency', currency }).format(v);   // "−160,00 €"
}
const rtf = new Intl.RelativeTimeFormat(LOCALE, { numeric: 'auto' });
export function fmtDate(iso, { relative = true } = {}) {
    if (!iso) return '';
    const d = new Date(iso), now = new Date();
    const days = Math.round((d - now) / 86400000);
    if (relative && Math.abs(days) <= 6) {
        const when = rtf.format(days, 'day');                       // "mañana", "en 3 días", "ayer"
        return `${when} ${d.toLocaleTimeString(LOCALE, { hour: '2-digit', minute: '2-digit' })}`;
    }
    return d.toLocaleDateString(LOCALE, { weekday: 'short', day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' });
}
export function fmtDateLong(iso) { return new Date(iso).toLocaleDateString(LOCALE, { weekday: 'long', day: 'numeric', month: 'long', hour: '2-digit', minute: '2-digit' }); }
export function toApiDate(localValue) { return localValue ? new Date(localValue).toISOString() : null; }   // de <input type=datetime-local>
export function toInputValue(iso) { const d = new Date(iso); const p = n => String(n).padStart(2, '0'); return `${d.getFullYear()}-${p(d.getMonth()+1)}-${p(d.getDate())}T${p(d.getHours())}:${p(d.getMinutes())}`; }
Object.assign(window, { fmtMoney, fmtDate, fmtDateLong, toApiDate, toInputValue });
```

**`core/labels.js`:** `ROLE_LABEL = {admin:'Administrador', member:'Miembro', guest:'Invitado'}`,
`ATT_LABEL = {yes:'Voy', maybe:'Quizás', no:'No voy'}`, `EVENT_TYPE_LABEL = {rehearsal:'Ensayo',
concert:'Concierto', other:'Otro'}`, `EVENT_STATUS_LABEL = {lead:'Contacto', contacted:'Hablando',
negotiating:'Negociando', confirmed:'Confirmado', done:'Hecho', cancelled:'Cancelado'}`,
`EVENT_ICON = {rehearsal:'music', concert:'mic', other:'pin'}` (nombres de `bfIcon`).

**Pasos.** Borra las copias (`home.js:14,33`, `agenda.js:18`, `bands.js:216,510`, `band.js:35`,
`finanzas.js:12`, `evento.js:9,20`, `join.js:6`, `profile.js:9`) y usa estas. Sustituye todo
`toFixed(2) + ' €'` por `fmtMoney(x, band.currency || 'EUR')`. Vitest para las 5 funciones.

**Commit.** `refactor(v6): T-V6-36 — format.js (Intl es-ES) y labels.js únicos`

---

### T-V6-37 · Retirar `style.css` por partes (M)

**Pasos.**

1. Crea `public/static/components.css` (lo que de `style.css` es componente ya migrado a
   tokens: tarjetas de canción, listas, modales → ya en `bf-*`), `player.css` (solo lo que usa
   `index.html`: `.top-bar`, `.bottom-bar`, `.score-*`, `.chord-*`, `.stage-mode`, countin,
   reference-panel, tuner-panel) y `editor.css` (solo editor). Mueve bloque a bloque con `git mv`
   mental: copia, borra del origen, prueba.
2. Cada página carga solo lo suyo: shell → `design-system.css` + `components.css` + `shell.css`;
   `index.html` → `design-system.css` + `player.css`; `editor.html` → `design-system.css` +
   `components.css` + `editor.css`; `login/join/evento` → `design-system.css` + `components.css`.
3. Elimina los ~150 `style=""` inline de las plantillas JS: sustitúyelos por utilidades
   `.bf-stack--sm/md/lg` (gap vertical 8/16/24), `.bf-ml-auto`, `.bf-text-sm`, `.bf-hidden`,
   `.bf-mt-2…6`. (grep `style="` en `*.js` hasta que queden solo los `style` de color de banda
   calculados — que también pueden pasar a `style="--band: …"` con una clase.)
4. Al final `style.css` queda vacío → se borra junto con sus referencias; `test_cache_busting`
   y `cachebust.py` no necesitan cambios.

**Commit (por página).** `style(v6): T-V6-37 — <página> sin style.css ni estilos inline`

---

## 5. Fase V6-F4 · Páginas, una a una

> Plantilla de cada receta: **Conserva** (ids/clases que usan los tests, Anexo A) · **Datos**
> (endpoints) · **Estructura** (HTML objetivo) · **Pasos** · **Test**. El diseño objetivo detallado
> está en la Parte I §5.3; aquí va lo ejecutable. Usa SIEMPRE los componentes de §4 (F3): nada
> de CSS nuevo específico de página salvo layout.

### T-V6-40 · Login + recuperar contraseña + legal (M)

**Conserva.** `#login-form`, `#email`, `#password`, `#btn-login`, `#btn-register`, `#btn-google`,
`#login-msg` (los usan `login.js` y `test_login.py`/`test_smoke.py` por string).

**Estructura (`login.html`).**
```html
<main class="auth">
  <section class="auth__hero">            <!-- oculta en < 900 px -->
    <a class="bf-brand" href="/"><span class="bf-brand-mark">…svg…</span><span class="bf-brand-name">BandFlow</span></a>
    <h1 class="bf-h1">Tu banda, lista para tocar.</h1>
    <ul class="auth__bullets">
      <li>${bfIcon('music')} Letra y acordes en el escenario, a tu tono</li>
      <li>${bfIcon('calendar')} Ensayos y bolos con quién viene</li>
      <li>${bfIcon('wallet')} Cuentas claras sin discusiones</li>
    </ul>
  </section>
  <section class="auth__panel bf-card">
    <div class="bf-tabs" role="tablist"><button class="bf-tab" data-tab="in" aria-selected="true">Entrar</button><button class="bf-tab" data-tab="up">Crear cuenta</button></div>
    <form id="login-form" novalidate>
      <div class="bf-field"><label class="bf-label" for="email">Email</label><input class="bf-input" id="email" type="email" autocomplete="email" required></div>
      <div class="bf-field"><label class="bf-label" for="password">Contraseña</label>
        <div class="auth__pw"><input class="bf-input" id="password" type="password" minlength="8" autocomplete="current-password" required><button type="button" class="bf-btn bf-btn--ghost bf-btn--icon" id="pw-toggle" aria-label="Mostrar contraseña">${bfIcon('eye')}</button></div>
        <p class="bf-error" id="login-msg" aria-live="polite"></p></div>
      <div class="bf-field auth__only-up" hidden><label class="bf-label" for="password2">Repite la contraseña</label><input class="bf-input" id="password2" type="password"></div>
      <button class="bf-btn bf-btn--primary bf-btn--lg" id="btn-login" type="submit">Entrar</button>
      <button class="bf-btn bf-btn--primary bf-btn--lg" id="btn-register" type="button" hidden>Crear cuenta</button>
      <a class="auth__forgot" href="reset.html" id="link-forgot">¿Olvidaste la contraseña?</a>
    </form>
    <div class="auth__divider"><span>o</span></div>
    <button class="bf-btn bf-btn--secondary bf-btn--lg auth__google" id="btn-google" type="button"><svg …logo Google oficial 18px…></svg> Continuar con Google</button>
    <p class="bf-faint auth__legal">Al continuar aceptas los <a href="terminos.html">Términos</a> y la <a href="privacidad.html">Privacidad</a>.</p>
  </section>
</main>
```
**Pasos.**
1. Reescribe `login.html` con la estructura; `login.js`: pestañas (muestra/oculta `#password2` y
   alterna qué botón se ve), validación con `form.checkValidity()` también en "Crear cuenta"
   (F-37), `#pw-toggle` cambia `type`, mensajes en castellano (`error.message` de Supabase →
   mapa: `Invalid login credentials` → "Email o contraseña incorrectos").
2. `reset.html` + `reset.js`: formulario de email → `sb.auth.resetPasswordForEmail(email, { redirectTo: origin + '/static/reset.html#update' })`;
   si la URL trae `#update` (Supabase redirige con sesión de recuperación), muestra "Nueva
   contraseña" → `sb.auth.updateUser({ password })` → a `app.html`. Añade `resetPassword` y
   `updatePassword` en `core/session.js`/`auth.js`.
3. `terminos.html` y `privacidad.html`: texto base (Oscar lo revisa) con el layout de
   `evento.html` (sin shell). Enlázalos también en el pie del lateral.
4. Si venimos de `join.html?code=X` sin sesión, `login.html?next=/static/join.html?code=X` y
   tras entrar/crear cuenta redirige a `next` (valida que empiece por `/static/`).
5. Quita el `<link>` a Inter/Roboto y el emoji del logo. `theme.js` en head.

**Test.** `test_login.py`: existen `#link-forgot`, pestaña "Crear cuenta" muestra `#password2`;
`reset.html` carga y tiene `#reset-form`. (Sin Supabase real: el modo test redirige a `app.html`
si hay sesión; para probar la página, usa `page.route('/config', …test_mode:false…)` y stub del
SDK como en `tests/e2e/test_smoke.py` si existe, o comprueba el HTML por fetch.)

**Commit.** `feat(v6): T-V6-40 — login rediseñado, recuperar contraseña, legal, next= tras entrar`

---

### T-V6-41 · Join (S)

**Conserva.** `#join-box`, `#join-accept`. **Datos.** `GET /invites/{code}` (hasta T-V6-80, que
añade el preview público con más datos).

**Pasos.** `join.html` sin la cabecera de reproductor: `theme.js` en head, `design-system.css` +
`components.css`, un `<main class="auth">` centrado con `<section id="join-box" class="bf-card">`:
avatar de banda (`bfAvatar({bandId, name, size:'xl'})`), `h1` "Te han invitado a {banda}",
"Entrarás como {rol}", `#join-accept` (`bf-btn--primary bf-btn--lg`), y debajo "¿No eres tú?
Cerrar sesión". Estados: `valid:false` → icono `alert-circle`, texto por `reason`
(expirada/agotada/revocada/banda no disponible) y enlace "Pedir otro enlace al administrador"
(`mailto:`-less: solo texto). Sin sesión → `login.html?next=…`. `join.js` usa `apiJson`.

**Test.** `test_bands_ui.py` ya cubre aceptar; añade: invitación revocada → `#join-accept` no
existe y se ve `.bf-empty--error`.

**Commit.** `feat(v6): T-V6-41 — join rediseñado con estados`

---

### T-V6-42a · Espacio de banda: cabecera, pestañas con contador y hash, onboarding único (S)

**Conserva.** `.bf-band-banner`, `.bf-tabs`, `.bf-tab[data-tab]`, `.bs-panel[data-panel]`,
`#bs-panels`, `#bs-invite`, `#b-summary`, `#bf-tour-ok`, `.bf-tour-tip`.

**Pasos.**
1. Cabecera: `.bf-band-banner` pasa a `bf-card bf-card--cover` con `--band: ${bandColor(id)}`;
   cover = `cover_url` o degradado; avatar `--lg` solapado; acciones a la derecha: "Invitar"
   (admin), "Tocar" (si hay setlists: abre el último usado) y ⋯ (Ajustes, Salir de la banda).
2. Pestañas: añade `aria-controls`, contador `(${n})` en Miembros/Repertorio/Setlists/Agenda
   usando `/bands/{id}/summary` (`counts`) + `member_count`; al hacer clic:
   `history.replaceState(null, '', '#' + key)`; al cargar, lee `location.hash` y activa esa
   pestaña; `window.addEventListener('hashchange', …)`. Cambia los enlaces de `home.js:55-59`,
   `agenda.js:39`, `chat.js:23` para incluir `#chat`/`#agenda`.
3. Onboarding: el banner `.bf-tour-tip` solo se muestra si `!profile.onboarding_done` (campo
   nuevo `MusicianProfile.flags JSON` con `{"band_tour_done": true}` que se escribe con
   `PUT /profile/me` al pulsar `#bf-tour-ok`); migración aditiva. Se muestra UNA vez, solo en
   Resumen.
4. Orden de pestañas según D-V6-4 (si no está decidida, no cambies el orden).

**Test.** `test_band_space.py`: `band.html?id=X#agenda` abre la pestaña agenda; pulsar
`#bf-tour-ok` y recargar → no aparece `.bf-tour-tip`.

**Commit.** `feat(v6): T-V6-42a — cabecera con cover, pestañas con contador y hash, onboarding una sola vez`

---

### T-V6-42b · Agenda de banda (M)

**Conserva.** `#b-agenda`, `#b-new-event`, `#ev-title`, `#ev-type`, `#ev-date`, `#ev-fee`,
`#ev-contact`, `#ev-venue`, `.setlist-song[data-id]` (alias en la fila nueva), `.att-btn[data-att]`,
`[data-act="thread|share|unshare|copy-link|del|more"]`, `.ev-more-menu` (alias), `#b-venues`,
`#b-new-venue`, `#v-name`, `#v-city`.

**Datos.** `GET /bands/{id}/events/`, `POST`, `PATCH /{eid}`, `DELETE`, `PUT /{eid}/attendance`,
`GET /{eid}` (detalle), `GET …/messages/?event_id=` (hilo), `GET/POST …/venues/`.

**Estructura.**
```html
<div class="bf-page-header"><h2 class="bf-h2">Agenda</h2>
  <div class="bf-page-header__actions"><div class="bf-segmented" id="ag-view"><button aria-pressed="true" data-view="list">Lista</button><button data-view="cal">Calendario</button></div>
  <button class="bf-btn bf-btn--primary" id="b-new-event">${bfIcon('plus')} Nuevo evento</button></div></div>
<div id="b-agenda">
  <h3 class="bf-eyebrow">Próximos</h3>
  <ul class="bf-list" id="ag-upcoming"> <!-- una .bf-item.setlist-song por evento --> </ul>
  <h3 class="bf-eyebrow">Pasados</h3> <ul class="bf-list" id="ag-past"></ul>
</div>
<aside class="bf-drawer" id="ev-drawer" hidden> <!-- detalle del evento --> </aside>
```
Fila: `__lead` = icono de tipo (`EVENT_ICON`) con color por tipo; `__main` = título +
`__meta` (fecha `bf-date`, sala, badge de estado); `__trail` = `bf-segmented` de asistencia
(3 botones `.att-btn` con `data-att`, clases `is-yes/is-maybe/is-no`) + botón ⋯ (`data-act="more"`)
que abre `bfMenu` con: Ver detalle · Hilo (`thread`) · Compartir enlace (`share`/`unshare`/
`copy-link`) · Cambiar estado (submenú con los 6 estados, solo admin) · Editar · Borrar (`del`, danger).

**Pasos.**
1. Reescribe el render de `bands.js:543-561` con la fila nueva (conserva clases/`data-*`).
2. `bf-drawer` (nuevo en `ui/drawer.js`): panel lateral de 420 px (hoja inferior en móvil) con
   cabecera (título, tipo, estado), bloques: Cuándo/Dónde (sala, dirección, mapa), Booking
   (contacto, teléfono, caché — solo miembros no-guest), Asistencia (lista con avatares),
   Setlist (enlace "Tocar"), Notas, Hilo de chat (reusa el render de mensajes de T-V6-10 con
   `event_id`). Clic en la fila (fuera de los botones) abre el drawer.
3. El `<select>` de estado desaparece de la fila (vive en el menú ⋯ y en el drawer como
   `bf-select`).
4. Salas: el bloque `#b-venues` pasa a Ajustes (sub-bloque "Salas de la banda") y en el formulario
   de evento el `#ev-venue` es un `bf-select` con "+ Nueva sala" al final (abre `bfDialog`).
5. Formulario de evento en `bfDialog` con `.bf-field` (ids iguales): tipo (segmented), título,
   fecha/hora (`datetime-local` → `toApiDate`), sala, setlist (solo concierto), notas; sección
   "Booking" plegable (contacto, teléfono, caché, visibilidad).
6. "Lista/Calendario": el calendario llega en T-V6-62; hasta entonces el toggle muestra "Pronto".

**Test.** `test_agenda_menu.py` y `test_bands_ui.py` siguen verdes; añade: clic en la fila abre
`#ev-drawer` con el título; a 390 px, `.bf-item__trail` queda bajo el texto (bounding boxes).

**Commit.** `feat(v6): T-V6-42b — agenda de banda con filas limpias, asistencia segmented, menú y panel de detalle`

---

### T-V6-42c · Chat de banda (M)

**Conserva.** `#b-chat`, `#chat-input`, `#chat-send`, `.setlist-song[data-id]` (alias en
`.bf-msg`), `[data-act="pin|del"]`, `#thread-list`, `#thread-input`.

**Estructura.** `#b-chat` = `<div id="b-chat-pinned">` (franja colapsable con los fijados) +
`<ol class="bf-chat" id="b-chat-list">` donde cada mensaje es
`<li class="bf-msg setlist-song ${m.is_mine?'bf-msg--mine':''}" data-id>` con avatar (solo en el
primero de una ráfaga del mismo autor), nombre, hora (`bf-date`), cuerpo, y ⋯ (`pin` admin,
Editar propio → `PATCH`, `del`). Separadores de día (`<li class="bf-chat__day">Hoy</li>`).
Composer: `<form class="bf-composer"><textarea id="chat-input" rows="1"></textarea><button id="chat-send" class="bf-btn bf-btn--primary bf-btn--icon">${bfIcon('send')}</button></form>`;
Enter envía, Shift+Enter salto, autosize del textarea, estado "enviando" (mensaje optimista con
opacidad hasta la respuesta).

**Pasos.** Reescribe `renderMessageList`/`initChat` (ya incremental tras T-V6-10) con la
plantilla nueva; el hilo de evento (`#thread-list/#thread-input`) usa el mismo componente dentro
del drawer de T-V6-42b.

**Test.** `test_chat.py`: enviar con Enter añade `.bf-msg--mine`; mensaje de otro autor
(sembrado por API con `acting_as`… en e2e no hay: usa dos mensajes míos y comprueba agrupación
por `.bf-msg__avatar` solo en el primero).

**Commit.** `feat(v6): T-V6-42c — chat de banda con agrupación, avatares, hora, fijados y composer`

---

### T-V6-42d · Repertorio y setlists de banda (M)

**Conserva.** `#b-repertoire`, `#b-add-song`, `#b-rep-search`, `.filter`, `#b-collections`,
`#b-collections-wrap`, `#b-new-collection`, `#col-*`, `#copy-list`, `#b-setlists`,
`#b-setlist-list-wrap`, `#b-new-setlist`, `#b-setlist-editor`, `#sl-name`, `#sl-available`,
`#sl-selected`, `#sl-save`, `[data-act]`, `[data-add]`, `[data-rm]`, `[data-id]`, `.song-card` (alias).

**Datos.** `GET/POST/DELETE /bands/{id}/songs/`, `POST …/songs/copy`, setlists y colecciones de
banda; `GET /songs/{id}` para meta (tono/BPM ya vienen en el summary: `key_root`, `bpm`, `capo`).

**Pasos.**
1. Cabecera: `bf-search` (`#b-rep-search`) + orden (`bf-select`: Título · Recientes · Tono) +
   botón "Añadir canción" (`#b-add-song`) que abre `bfMenu`: Nueva (→ `editor.html?band=ID`),
   Importar (→ `editor.html?band=ID&import=1`), Copiar de mi biblioteca (abre el modal actual
   `#copy-list`).
2. Lista: `.bf-item.song-card[data-id]` con `__lead` = tono grande (mono, `key_root` o "—"),
   `__main` = título + meta (artista · BPM · capo · "añadida por X"), `__trail` = ▶ Tocar
   (`data-act="play"`) + ⋯ (Editar `data-act="edit"`, Añadir a setlist, Quitar `data-rm` con
   deshacer). Colecciones como `bf-chip` arriba (`#b-collections`), con "+ Nueva colección".
3. Setlists: tarjetas `bf-card--interactive` (`#b-setlists`) con nombre, nº canciones, duración
   estimada (`Σ duration_sec || 210 s`), `bf-btn--primary` "Tocar" (`index.html?songId=…&setlist=…`)
   y ⋯ (Editar → `#b-setlist-editor`, Duplicar, Exportar PDF → T-V6-63, Borrar). Editor de setlist:
   dos columnas (`#sl-available` / `#sl-selected`) con arrastrar y nota por canción como hasta
   ahora, pero con `.bf-item` y botones `bf-btn--icon`.
4. Semáforo de preparación: deja un hueco `__lead` secundario (`.bf-item__status`) vacío; lo
   rellena T-V6-83.

**Test.** `test_bands_ui.py`, `test_buscador_repertorio.py`, `test_terminologia.py` verdes; añade
"Añadir canción → menú con 3 opciones" y "duración estimada visible en la tarjeta de setlist".

**Commit.** `feat(v6): T-V6-42d — repertorio con meta y menú, setlists como tarjetas con duración`

---

### T-V6-42e · Miembros, invitaciones, salir de la banda (M)

**Conserva.** `#b-members`, `#bs-invite`. **Datos (existen, sin UI):** `PATCH/DELETE
/bands/{id}/members/{uid}`, `POST …/reactivate`, `GET /bands/{id}/invites`, `DELETE …/invites/{iid}`
(T-V6-08). **Nuevo backend:** `POST /bands/{id}/leave` (miembro activo se da de baja a sí mismo;
si es el único admin → 409 "Nombra otro administrador antes de salir"); `POST
/bands/{id}/members/{uid}/transfer-admin` (opcional: `PATCH role` ya sirve).

**Pasos.**
1. Lista de miembros: `.bf-item` con `bfAvatar({userId, url, name})`, nombre, chips de
   instrumentos (`membership.instrument` hoy singular), badge de rol; para admin: ⋯ con Hacer
   admin / Hacer miembro / Hacer invitado (`PATCH`), Dar de baja (`DELETE`, confirm), Reactivar
   (si `status='left'`, sección "Antiguos miembros" plegada).
2. Bloque "Invitaciones" (solo admin): lista (`GET …/invites`) con código, rol, usos/máx,
   caduca, botones Copiar enlace (`navigator.clipboard`), Compartir (T-V6-80 `bfShare`),
   Revocar (`DELETE`, confirm). Botón "Nueva invitación" con `bfDialog` (rol, días, usos).
3. Para mí: botón "Salir de la banda" en ⋯ de la cabecera y al final de Miembros → confirm →
   `POST /bands/{id}/leave` → `bands.html`.
4. Backend `leave`: en `bands_router.py`, reutiliza la lógica de `DELETE /members/{uid}` con
   `uid = membership.user_id` y la comprobación de último admin (`SELECT … FOR UPDATE` en PG).
   Tests: salir OK; único admin → 409; tras salir, `GET /bands/{id}` → 404 para mí.

**Commit.** `feat(v6): T-V6-42e — gestión de miembros e invitaciones desde la UI, salir de la banda`

---

### T-V6-42f · Finanzas de banda (M)

**Conserva.** `#b-finance`, `#b-new-tx`, `#b-tx-list`, `#tx-amount`, `#tx-desc`, `#tx-event`,
`#tx-split-mode`, `#tx-splits`, `#tx-split-sum`, `#b-settle`, `#b-export-csv`, `.csv`, `#b-seasons`.

**Pasos.**
1. Saldos: `.bf-item` por participante con avatar, nombre, `bf-amount` (`fmtMoney`), y texto
   "le deben"/"debe"; "Fondo" con icono `landmark`. Botón "Liquidar" abre `bfDialog` con la
   **propuesta mínima** (algoritmo: ordena deudores y acreedores, empareja greedy; lista de
   pagos sugeridos con botón "Registrar" cada uno → `POST /settlements`).
2. Movimientos: filtros `bf-chip` (Todos · Gastos · Ingresos · por evento · por mes) y lista
   `.bf-item` con icono de tipo (flecha verde/roja), descripción, meta (fecha · categoría ·
   evento · "pagó X" · "entre N"), importe, ⋯ (Ver reparto, Borrar). Liquidaciones listadas
   debajo (`GET …/settlements`, con Borrar).
3. Desglose por evento (D-FIN-1): agrupación "Por evento" que suma ingresos/gastos de cada
   `event_id` y muestra "quién debe a quién" solo con los movimientos de ese evento (filtro en
   cliente sobre `compute_balances`-like en JS, o endpoint `GET …/balances?event_id=`).
4. Gráfico de barras por mes (SVG propio, 12 barras, tokens): ingresos vs gastos.
5. Formato: `fmtMoney(x, band.currency)`. Emojis fuera.

**Test.** `test_finanzas.py`/`test_bands_ui.py` verdes; añade: "Liquidar" muestra la propuesta
con la suma correcta para el seed (−160 / +80 / +80 → 2 pagos de 80).

**Commit.** `feat(v6): T-V6-42f — finanzas de banda: saldos con liquidación sugerida, movimientos con filtros, desglose por evento, gráfico`

---

### T-V6-42g · Giras (S)

**Conserva.** `#b-tours`, `#b-new-tour`, `#b-tour-detail`, `#b-tour-back`, `[data-tour]`,
`#b-add-stop`, `#b-stop-*`, `#b-add-line`, `#b-line-*`, `#b-tours-list-wrap`.
Tarjeta por gira (fechas, nº paradas, presupuesto vs caché con barra) y detalle con timeline
vertical de paradas; Editar/Borrar (`PATCH/DELETE …/tours/{tid}`). Si D-V6-22 se aprueba, esta
pestaña se convierte en el agrupador de Agenda en T-V6-90; haz solo el mínimo visual aquí.

**Commit.** `style(v6): T-V6-42g — giras con tarjetas y timeline`

---

### T-V6-43 · Inicio (M)

**Conserva.** `#home`, `#home-att[data-band][data-ev]`, `.att-btn`/`[data-att]`, `#home-messages`,
`#home-onboarding`, `.home-hero`. **Datos.** `/me/dashboard`, `/me/balances`, `/bands/`,
`/profile/me`, `/me/events` (si hace falta "esta semana"); nuevo campo opcional en
`/me/dashboard`: `counts: {songs, pending_responses}` (añádelo en `me_router`).

**Estructura.**
```html
<div class="bf-page bf-page--wide" id="home">
  <div class="bf-page-header"><div><h1 class="bf-h1">Hola, Oscar</h1><p class="bf-muted" id="home-date">jueves, 5 de noviembre</p></div></div>
  <section class="home-hero bf-card bf-card--cover" style="--band:…">  <!-- próximo evento -->
    <div class="home-hero__when">en 2 días</div><h2>Ensayo general</h2><div class="home-hero__meta">…</div>
    <div id="home-att" class="bf-segmented" data-band data-ev>…3 .att-btn…</div>
    <div class="home-hero__actions"><a class="bf-btn bf-btn--primary">Tocar setlist</a><a class="bf-btn bf-btn--secondary">Ver evento</a></div>
  </section>
  <div class="bf-grid home-kpis"> 4 × .bf-stat (próximo bolo en N días · canciones · pendientes de responder · saldo total) </div>
  <div class="home-cols">
    <section class="bf-card"><h3 class="bf-h3">Esta semana</h3><ul class="bf-list" id="home-week"></ul></section>
    <section class="bf-card"><h3 class="bf-h3">Actividad reciente</h3><ul class="bf-list" id="home-messages"></ul></section>
  </div>
</div>
```
**Pasos.** Asistencia in-page: `PUT …/attendance` y actualiza el `aria-pressed` sin recargar
(`home.js` hoy recarga todo). Estado sin banda: `#home-onboarding` con dos `bf-card--interactive`
grandes (Crear banda / Tengo un código). Quita "Accesos rápidos". `fmtMoney`/`fmtDate`.

**Test.** `test_home.py` verde + "marcar asistencia no navega (misma URL) y cambia `aria-pressed`".

**Commit.** `feat(v6): T-V6-43 — inicio con KPIs, esta semana, actividad y asistencia sin recargar`

---

### T-V6-44 · Mis bandas (M)

**Conserva.** `#bands-grid`, `#btn-new-band`, `.song-card.card-main[data-act="open"]` (alias),
`.bf-avatar`. Tarjetas `bf-card--cover` de altura fija (`min-height: 220px`) con cover, avatar,
nombre, rol, próximo evento, `bf-avatar-stack` de miembros (necesita `GET /bands/{id}/members`
por banda: hazlo perezoso o añade `member_avatars` (máx. 4) a `BandSummary` en `bands_router`),
contadores. Cabecera: "Nueva banda" + "Unirme con código" (`promptModal` → `join.html?code=`).
Vacío: `bfEmpty` con las dos acciones.

**Commit.** `feat(v6): T-V6-44 — mis bandas con tarjetas ricas y unirme con código`

---

### T-V6-45 · Biblioteca y setlists personales (M)

**Conserva (library).** `#search-input`, `#library-filters`, `.lib-filter[data-filter]`,
`#library-collections`, `[data-collection]`, `#song-grid`, `.song-card`, `.card-action-btn`,
`.card-play`, `[data-act]`, `#col-picker`, `#col-name`, `.add-to-list`, `.add-to-row[data-cid]`,
`.empty-state` (alias de `bf-empty`). **Conserva (setlists).** `#setlist-grid`, `#setlist-detail`,
`#btn-new-setlist`, `#sl-*`, `#sl-playall`, `.song-card[data-id]`, `[data-act]`, `[data-rm]`, `[data-sid]`.

**Pasos.** Cabecera con `bf-search` + toggle grid/lista + orden; filtros como `bf-chip` con punto
de color; tarjetas `song-card bf-card--interactive` con meta (tono · BPM · capo), badge de origen,
`.card-play` siempre visible en móvil y ⋯ (`card-action-btn`): Editar, Añadir a setlist, Copiar a
banda, Mover a colección, Borrar. "Cargar más" (T-V6-11). Setlists: mismas tarjetas que en banda
(T-V6-42d) y vista detalle con `history.pushState('#'+id)`.

**Commit.** `feat(v6): T-V6-45 — biblioteca y setlists personales con tarjetas, filtros y acciones visibles`

---

### T-V6-46 · Editor (M)

**Conserva.** `#song-form`, `#title`, `#artist`, `#bpm`, `#time-signature`, `#reference-url`,
`#reference-preview`, `#raw-text`, `#preview-content`, `#btn-save`, `#btn-import`, `#import-url`,
`#btn-import-search`, `#import-search`, `#import-search-results`, `.import-search-item`,
`.import-search-empty`, `#import-photo`, `.join`.

**Estructura.** Cabecera fija (título de página + ❌ con guardia) · tarjeta "Datos" con rejilla
de 4 columnas: título, artista, tono (`bf-select` con 24 tonos: C … B, Cm … Bm; nuevo campo que
ya existe en el modelo `key_root/key_mode`), capo (0–12), BPM, compás, afinación, enlace de
referencia · botón "Importar" (`#btn-import-open`) que abre `bfDialog` grande con `bf-tabs`:
Buscar (`#import-search` + `#btn-import-search` + `#import-search-results`), Enlace (`#import-url`
+ `#btn-import`), Foto (`#import-photo`) — los ids se conservan dentro del diálogo · área de
trabajo: `#raw-text` y `#preview-content` a la misma altura (`grid-template-columns: 1fr 1fr`,
apilado en móvil) · barra inferior fija con "Compartir en Explorar" (T-V6-16), "Guardar"
(`#btn-save`) y "Guardar y tocar".

**Pasos.** Mueve los bloques de importación al diálogo (sin cambiar su JS); añade tono/capo al
payload (`key_root`, `key_mode`, `capo`) y al render de la cabecera del reproductor; Ctrl+S
guarda; textarea y preview con `--bf-font-mono`. `?band=ID` → al guardar crea en
`/bands/{id}/songs/`; `?import=1` abre el diálogo al cargar.

**Test.** `test_editor.py`/`test_compas.py`/`test_oembed_caratula.py` verdes (los ids viven ahora
dentro del diálogo: los tests deben abrirlo primero con `#btn-import-open` — actualízalos en el
mismo commit).

**Commit.** `feat(v6): T-V6-46 — editor con metadatos completos, importar en diálogo y barra de guardado`

---

### T-V6-47 · Agenda TÚ (M)

**Conserva.** `#agenda`, `#agenda-filters[data-band]`, `#agenda-upcoming`, `#agenda-past`,
`.att-btn[data-att]` (si se añade asistencia en línea). Lista agrupada por semana
("Esta semana", "Próxima", "Más adelante", "Pasados"), filas `.bf-item` con punto de color de
banda y badge de banda **en la meta** (no en columna), asistencia `bf-segmented` in-page,
"Nuevo evento" → `bfDialog` con selector de banda (solo bandas donde no soy guest) y el mismo
formulario que T-V6-42b. Toggle Lista/Calendario (calendario en T-V6-62).

**Commit.** `feat(v6): T-V6-47 — agenda personal agrupada por semana, crear evento y asistencia en línea`

---

### T-V6-48 · Finanzas TÚ (S)

**Conserva.** `#finanzas-list`. Cabecera con 3 `bf-stat` (te deben · debes · neto) a partir de
`/me/balances`; lista por banda con `bf-amount` y botón "Ver"/"Liquidar" (abre el diálogo de
liquidación de esa banda); últimos movimientos de todas las bandas (nuevo `GET /me/transactions?limit=20`
en `me_router` con aislamiento por `_my_band_names`).

**Commit.** `feat(v6): T-V6-48 — finanzas personales con resumen y últimos movimientos`

---

### T-V6-49 · Chat TÚ en dos columnas (M)

**Conserva.** `#chat-list`. Layout `.chat-layout { display:grid; grid-template-columns: 320px 1fr; }`
(móvil: lista → hilo con botón atrás): izquierda conversaciones (`/me/conversations`, ya con
grupos "Mis bandas"/"Otros contactos" previstos: pinta solo el primero hasta V5-F7), derecha
el componente de hilo de T-V6-42c con `bandId` de la seleccionada (`?band=` en la URL).
No-leídos: `last_at > localStorage['bf-chat-seen:'+bandId]` → punto en la lista y
`.bf-nav-badge` en el lateral (`shell.js` consulta `/me/conversations` una vez).

**Commit.** `feat(v6): T-V6-49 — chat personal a dos columnas con no-leídos`

---

### T-V6-50 · Perfil y cuenta (M)

**Conserva.** `.pf-identity`, `.pf-name`, `#pf-name`, `#pf-inst`, `#pf-instruments`, `#pf-bands`,
`#pf-photo`, `#pf-save`, `#bf-prof-initials` (lateral). Instrumentos como chips seleccionables
(`INSTRUMENTS = ['voz','guitarra','bajo','batería','teclado','piano','saxo','trompeta','violín','percusión','DJ','otro']`
+ campo libre) que escriben en el `#pf-inst` oculto (los tests leen ese input). Sección "Cuenta":
email (solo lectura + "Cambiar" → `sb.auth.updateUser({email})`), "Cambiar contraseña"
(`updateUser({password})`), "Cerrar otras sesiones" (`signOut({scope:'others'})`), tema,
notificaciones (T-V6-60), "Exportar mis datos"/"Borrar cuenta" (T-V6-65, de momento ocultos).

**Commit.** `feat(v6): T-V6-50 — perfil con chips de instrumentos y sección cuenta`

---

### T-V6-51 · Afinador / Metrónomo (S)

**Conserva.** `#tuner-panel`, `#tuner-note`, `#tuner-status`, `#tuner-a4`, `#tuner-msg`,
`#tuner-needle`, `#metro-panel`, `#metro-bpm`, `#metro-up`, `#metro-down`, `#metro-start`,
`#metro-meter`, `.metro-pip(--on)`. Dos `bf-card` grandes centradas (`max-width: 920px`), nota
"—" a `--bf-fs-3xl` en reposo, escala ±50 cents bajo la aguja, botón de micrófono con estado
(`is-loading` mientras pide permiso), presets de BPM (60/80/100/120/140), `bf-select` para La4 y
compás. Si D-V6-24: el ítem del lateral se mueve al pie como "Herramientas".

**Commit.** `style(v6): T-V6-51 — afinador y metrónomo centrados y con estados`

---

### T-V6-52 · Explorar provisional y evento público (S)

**Conserva.** `#cat-search`, `#cat-search-btn`, `#cat-results`, `[data-score]`, `#cat-stars`,
`[data-star]`, `#cat-import`, `#cat-back`; `.pub-card`, `.pub-title`, `.pub-brand`, `.pub-cta__btn`.
Explorar: tarjetas `bf-card--interactive` con título, artista, tono/BPM, "por X", estrellas como
`<button data-star aria-label="N estrellas">`; búsqueda con `AbortController` + debounce 250 ms;
paginación "Cargar más". Evento público: `theme.js`, `bf-card` con avatar/cover de banda
(`/public/events/{id}` → añade `band_avatar_url`, `band_cover_url` en la proyección), botones
"Añadir al calendario" (genera `.ics` en cliente) y "Compartir" (`bfShare`, T-V6-80).

**Commit.** `style(v6): T-V6-52 — explorar con tarjetas y búsqueda robusta; evento público con calendario y compartir`

---

## 6. Fase V6-F5 · Móvil y reproductor

### T-V6-55 · Reproductor: toolbar compacta, tamaño de letra, sección actual, cuenta atrás con etiqueta, tempo por usuario (M)

**Conserva.** Todos los ids de `index.html` listados en el Anexo A (`#btn-bpm-up/down`,
`#bpm-value`, `#btn-key-up/down/save`, `#key-value`, `#btn-tuner`, `#btn-print`, `#btn-reference`,
`#btn-shortcuts`, `#btn-countin`, `#btn-metronome`, `#btn-stop`, `#btn-play-pause`, `#btn-stage`,
`#current-section-display`, `#current-beat-display[data-beat]`, `#score-container`,
`#score-content`, `#song-title`, `#song-artist`, `#tuner-panel`, `#tuner-close`, `#reference-embed`,
`#countin-overlay`, `#countin-num`, `.top-bar`, `.bottom-bar`, `.stage-mode`, `.chord-container`,
`.line-lyric`). El motor y `score_render.js` no se tocan.

**Pasos.**
1. **Toolbar.** `.top-bar`: izquierda título/artista (+ tono y capo como `bf-badge` mono);
   centro BPM y Tono como hoy en ≥ 820 px; en móvil, BPM y Tono se convierten en dos botones
   (`#bpm-value` y `#key-value` siguen existiendo, dentro de un popover `bf-menu` que contiene
   los +/−). Derecha: `#btn-tuner` y un ⋯ (`bfMenu`) con Imprimir (`#btn-print` se mueve dentro
   pero mantiene id), Vídeo de referencia (`#btn-reference`), Atajos (`#btn-shortcuts`), Inicio,
   Biblioteca, Editar esta canción (`editor.html?songId=`). Máximo 2 filas en móvil.
2. **Tamaño de letra.** Botones A−/A+ (`#btn-font-down/up`) que cambian
   `document.documentElement.style.setProperty('--score-scale', x)` (0.8–1.6) y `#score-content { font-size: calc(1rem * var(--score-scale, 1)); }`;
   persistido en `localStorage['bf-score-scale']`. El motor usa ids, no píxeles: no afecta a la
   sincronización; el auto-scroll (T-019) se ancla al acorde activo, así que también funciona.
3. **Sección actual.** `#current-section-display` ya existe: muestra "Estribillo · compás 12";
   al tocarlo abre un `bfMenu` con las secciones (`computeSectionRanges`) y salta
   (`engine.seek`? NO existe → usa `engine.stop()` + `engine.state.pausedAtBeat = inicio` +
   `engine.play()`; si eso toca el motor, deja la navegación como "scroll a la sección" sin
   cambiar el beat: `document.getElementById('section-<id>').scrollIntoView()`).
4. **Cuenta atrás.** `#btn-countin` muestra `bfIcon('timer')` + "4"/"8"/"off" y `aria-label`
   ya existente.
5. **Tempo por usuario (D-V6-9).** `scheduleBpmSave` deja de hacer `PATCH /songs/{id}`; guarda
   en `localStorage['bf-bpm:'+song.id]` y al cargar la canción aplica ese valor si existe. Nuevo
   botón en el popover de BPM: "Guardar como tempo de la banda" (hace el PATCH; solo si no eres
   guest). Test: cambiar BPM y recargar mantiene el BPM local y NO cambió `song.bpm` en la API.
6. `100dvh` en `#app`/`#score-container`; `overflow-wrap:anywhere` en `.line-lyric` (de T-V6-09).

**Commit.** `feat(v6): T-V6-55 — reproductor con toolbar compacta, tamaño de letra, sección actual y tempo por usuario`

---

### T-V6-56 · Modo setlist sin recarga + parada al final (M) — excepciones al motor

**Pasos.**
1. **Siguiente canción in-page.** En `app.js`, `setupSetlistNav` deja de hacer
   `window.location.href = …`; crea `async function loadSongById(id)` que: `engine.stop()`,
   `const song = await apiJson('/songs/'+id)`, `currentSong = song; transposeOffset = 0;`
   `elSongTitle.textContent = …; renderScoreInto(elScoreContent, song, 0); applyTranspose();
   engine.loadSong(song); sectionRanges = computeSectionRanges(song); setupReference(song);
   history.replaceState(null, '', '?songId='+id+'&setlist='+setlistId+'&pos='+pos)` y repinta la
   barra. Prefetch: tras cargar, `apiJson('/songs/'+ids[pos+1])` guardado en un `Map` para que
   "Siguiente" sea instantáneo. Barra inferior: "Siguiente: Zombie (84 BPM)" (`#sl-next` ya
   existe).
2. **Parada al final (motor, excepción autorizada).** En `sync_engine.js`, `loadSong` calcula
   `this.state.totalBeats` = max(`beat_abs + duration_beats`) de `flatChords` (o `song.duration_beats`
   si viene). En `tick()`, tras calcular `currentBeat`: `if (this.state.totalBeats && this.state.currentBeat >= this.state.totalBeats + 4) { this.stop(); this.emitUpdate(); if (this.onEnd) this.onEnd(); return; }`.
   `app.js` registra `engine.onEnd = () => { if (hay siguiente) mostrar botón grande "Siguiente
   canción" en la barra inferior (no auto-avanzar: el músico decide) }`.
   Tests: `test_sync_engine.py` → con una canción de 8 beats a 240 BPM, tras ~3 s
   `engine.state.status === 'idle'` y `onEnd` llamado; `test_player.py` sigue verde.
3. Actualiza `tests/e2e/test_setlists_ui.py`/`test_player.py` donde esperaban navegación
   (`page.wait_for_url`) → ahora `wait_for_function` sobre `#song-title`.

**Commit.** `feat(v6): T-V6-56 — modo setlist sin recarga con prefetch; el motor para al final (onEnd)`

---

### T-V6-57 · Pantalla encendida, offline de la última lista, manifest e icono (S)

**Pasos.**
1. `wakeLock`: al pulsar Play (y en modo escenario) `navigator.wakeLock?.request('screen')`;
   liberar en stop; re-pedir en `visibilitychange` visible. Sin soporte → nada.
2. Offline: `core/offline.js` con IndexedDB (`bandflow-offline`, store `songs` {id, json, savedAt}
   y `setlists`). Al abrir una canción/setlist en el reproductor se guarda; `fetchAndRenderSong`
   y `loadSongById` intentan la red y, si falla (`ApiError.status === 0`), leen de IndexedDB y
   muestran un `bf-badge` "Sin conexión · copia guardada". El SW ya cachea `index.html` y los
   estáticos (network-first con respaldo), así que la página abre offline.
3. `manifest.json`: `name: "BandFlow"`, `short_name`, `description` nueva, `start_url: "/static/app.html"`,
   `theme_color` acorde al tema (déjalo oscuro; `theme-color` dinámico en `theme.js` con
   `<meta name="theme-color">` por tema), icono **coral** (regenera `icon-192/512.png` desde el
   SVG del `bf-brand-mark` con fondo `#ff6b4a`), `display: standalone`.
4. Quita `apple-mobile-web-app-capable` → `mobile-web-app-capable`.

**Test.** e2e: abrir canción → `page.context.set_offline(True)` → recargar → `#song-title` muestra
la canción y el badge "Sin conexión".

**Commit.** `feat(v6): T-V6-57 — wakeLock, modo offline de la última canción/setlist, manifest e icono coral`

---

### T-V6-58 · Pasada móvil completa (M)

**Pasos.**
1. `tests/e2e/test_responsive_pwa.py`: parametriza las **16 páginas** (con datos sembrados por
   `api` para band/index/editor/join/evento) a 390×844 y 768×1024: sin overflow horizontal
   (`scrollWidth <= innerWidth + 1`), sin elementos interactivos < 44 px (`getBoundingClientRect`
   de `button, a.bf-btn, input`), topbar con título visible.
2. Topbar móvil (`shell.js`): título de página + hueco de acción; cada página mueve su botón
   primario (`.bf-page-header__actions > .bf-btn--primary`) al hueco en ≤ 768 px (JS: `matchMedia`).
3. Diálogos como hoja inferior (ya en `bfDialog`), menús ⋯ como hoja inferior en móvil (`bfMenu`
   detecta `pointer: coarse` + ancho < 768).
4. Pestañas de banda con desvanecido lateral y pestaña activa centrada (`scrollIntoView({inline:'center'})`).
5. Revisa capturas de las 16 páginas en móvil, oscuro y claro; corrige.

**Commit.** `style(v6): T-V6-58 — pasada móvil: tests de overflow/targets en 16 páginas, topbar, hojas inferiores`

---

### T-V6-59 · Accesibilidad (M)

**Pasos.**
1. `pip install axe-playwright-python` (o `playwright-axe`); en `tests/e2e/test_a11y.py`,
   para cada página: `results = axe.run(page)`; asevera 0 violaciones `critical`/`serious`
   (lista blanca temporal documentada para lo que no se pueda arreglar ya).
2. Tarjetas/filas clicables: `<a class="bf-card__link">` o `<button>` reales (`bands.js:45-60`,
   `library.js:230-259`, `setlists.js:33-40`, `catalogo.js`, `band.js:390`); borra `.song-card:focus-visible`
   muerta.
3. Pestañas: `role="tab"`, `aria-controls`, `tabindex` roving, flechas; ☰ con `aria-expanded`,
   Escape cierra, foco al primer ítem; `:focus-visible` en `.bf-subnav-item, .bf-profile-card,
   .bf-brand, .bf-hamburger, .att-btn, .sl-drag, .pf-band-chip, .add-to-row`.
4. Labels reales en todos los inputs (`#ev-date` y los de modales); `<h1>` en `band.html`
   (visualmente oculto si hace falta: `.bf-visually-hidden`); jerarquía `h2 > h3` sin `h5`.
5. Contraste: `--bf-text-faint` sobre `--bf-surface-2` → sube a 4.5:1 (ajusta el token).

**Commit.** `fix(v6): T-V6-59 — accesibilidad: axe en CI, teclado en tarjetas/pestañas/menús, labels, foco visible`

---

## 7. Fase V6-F6 · Funcionalidades que faltan

### T-V6-60 · Email transaccional (M)

**Decisión previa:** D-V6-7 (proveedor) y D-V6-8 (dominio para el remitente).

**Pasos.**
1. Tabla `notification_prefs(user_id PK, email_events bool default true, email_reminders bool
   default true, email_finance bool default true, email_chat_pins bool default false)` + migración.
   `GET/PUT /profile/me/notifications`.
2. Envío: `src/services/mailer.py` con `send_email(to, subject, html, text)` vía API HTTP del
   proveedor (Resend: `POST https://api.resend.com/emails` con `RESEND_API_KEY`). En tests, un
   `FakeMailer` que guarda en memoria (`settings.mailer = "fake"`).
3. Plantillas (Jinja2 ya es dependencia de Alembic vía Mako — usa `string.Template` o Jinja2) en
   `src/templates/email/*.html`: `invite_accepted`, `event_created`, `event_changed`,
   `event_reminder`, `transaction_affects_you`. Marca BandFlow, botón, pie con "Gestionar
   avisos".
4. Disparadores (en los routers, tras `commit`, en `BackgroundTasks` de FastAPI): aceptar
   invitación → a los admins; crear/cambiar evento → a miembros activos (no al autor); crear
   movimiento con splits → a los implicados.
5. Recordatorio 24 h: endpoint `POST /internal/cron/reminders` protegido por cabecera
   `X-Cron-Secret` (env) que busca eventos `starts_at` entre +23 h y +25 h sin `reminder_sent_at`
   (columna nueva) y envía; lo llama un **Vercel Cron** (`vercel.json` → `"crons":[{"path":"/internal/cron/reminders","schedule":"0 * * * *"}]`).
6. Direcciones: el email del usuario viene de Supabase (`auth.users`): guarda `email` en
   `musician_profiles` al primer login (`profile_router` lo recibe del JWT en T-V6-28:
   claim `email`).
7. Tests: unit con `FakeMailer` (se envía a quien toca, respeta prefs); el cron encuentra el
   evento y marca `reminder_sent_at`.

**Commit.** `feat(v6): T-V6-60 — emails transaccionales (invitación, eventos, movimientos, recordatorio 24 h) con preferencias`

---

### T-V6-61 · Centro de notificaciones y no-leídos (M)

Tabla `notifications(id, user_id, band_id, kind, ref_id, title, body, created_at, read_at)` +
migración; se escribe en los mismos disparadores de T-V6-60 (y en mensajes fijados). API:
`GET /me/notifications?unread=1`, `POST /me/notifications/read` (ids). UI: campana en la topbar
(`shell.js`) con contador, panel `bf-drawer` con la lista agrupada por día; clic marca leída y
navega (`band.html?id=…#agenda`). No-leídos de chat por `last_at` (T-V6-49).

**Commit.** `feat(v6): T-V6-61 — centro de notificaciones in-app`

---

### T-V6-62 · `bf-calendar` + Agenda calendario + `.ics` (M)

**Pasos.**
1. `ui/calendar.js`: `bfCalendar(el, { items, month, onSelect })` con `items = [{kind, id,
   band_id, title, date, status}]` (contrato V5 §7); rejilla mensual (CSS grid 7 col, semana
   empieza en lunes, `Intl` para nombres), puntos por `bandColor`, estilo fantasma para
   `kind='proposal'`, punto secundario para `note`; cabecera con mes anterior/siguiente/hoy;
   vista semanal (lista por día) debajo en móvil. Sin dependencias.
2. `/me/events` → acepta `from`/`to` y devuelve items tipados (`kind:'event'`); agenda de banda
   usa `/bands/{id}/events/?from&to`.
3. Toggle Lista/Calendario en Agenda TÚ y de banda, persistido en `localStorage`.
4. `.ics`: `GET /public/events/{id}.ics` (solo `visibility != private`) y `GET /bands/{id}/calendar.ics?token=`
   (token por banda en `bands.calendar_token`, regenerable en Ajustes) → `text/calendar` con
   VEVENT por evento confirmado; botón "Suscribirse en Google/Apple Calendar" con la URL.
5. Tests: unit del `.ics` (contiene `BEGIN:VEVENT`, UID estable, `DTSTART` en UTC); Vitest de
   la rejilla (noviembre 2026 empieza en domingo → primera celda = lunes 26 oct).

**Commit.** `feat(v6): T-V6-62 — calendario propio en agenda personal y de banda; exportación/suscripción .ics`

---

### T-V6-63 · Exportar/imprimir setlist y compartir por enlace (M)

1. `GET /setlists/{id}/print` y `GET /bands/{id}/setlists/{sid}/print` → HTML imprimible
   (plantilla `print_setlist.html`: título, fecha, lista numerada con tono/BPM/nota, opcional
   "con canciones" = cada canción con letra y acordes vía el render del catálogo en servidor —
   si no hay render en servidor, abre `index.html?setlist=…&print=1` que pinta todas las
   canciones en una página y llama a `window.print()`). CSS `@media print` ya existe en
   `style.css:820` → muévelo a `print.css`.
2. Compartir: `setlists.share_token` (nullable) + `POST …/setlists/{sid}/share` (genera) /
   `DELETE` (revoca) + `GET /public/setlists/{token}` con proyección (nombre, canciones con
   título/artista/tono/BPM; sin notas internas) + `setlist.html?t=` pública con botón "Abrir en
   BandFlow". `bfShare` en la tarjeta de setlist.

**Commit.** `feat(v6): T-V6-63 — setlist imprimible/PDF y compartible por enlace de solo lectura`

---

### T-V6-64 · Onboarding (M)

1. Sin banda: `#home-onboarding` con dos tarjetas grandes y un tercer enlace "Prueba con una
   canción de ejemplo" (`POST /songs/sample` crea una canción demo libre de derechos — letra
   propia escrita para BandFlow, 2 secciones).
2. Asistente de banda (`bfDialog` de 3 pasos tras crear): nombre + color (paleta de 8) →
   invitar (crea invitación 7 días y muestra enlace + `bfShare` WhatsApp) → primera canción
   (Nueva / Importar / Copiar). Progreso en el Resumen (`bf-card` "Primeros pasos" con 3 checks)
   hasta completarlo; se puede cerrar.
3. Tour de 4 puntos (`.bf-tour-tip` reutilizado) la primera vez en Inicio: Agenda, Canciones,
   Chat, Tocar. Persistido en `profile.flags`.

**Commit.** `feat(v6): T-V6-64 — onboarding: primer uso sin banda, asistente de banda y tour`

---

### T-V6-65 · Cuenta: borrar, exportar, verificación, emails de auth (M)

1. `GET /profile/me/export` → JSON con perfil, canciones personales, setlists personales,
   membresías (ids y nombres) y mensajes propios.
2. `DELETE /profile/me` → 409 si es único admin de alguna banda (lista de bandas en `detail`);
   si no: anonimiza perfil (`display_name="Usuario eliminado"`, `avatar_url=null`), marca
   membresías `left`, soft-borra canciones/setlists personales, y llama a Supabase Admin API
   (`DELETE /auth/v1/admin/users/{id}` con `service_role` **solo desde el servidor**, env
   `SUPABASE_SERVICE_ROLE_KEY` en Vercel; jamás en el repo ni en `/config`). Cierra sesión.
3. Verificación de email: Oscar activa "Confirm email" en Supabase; `login.js` muestra el
   mensaje; plantillas de email de auth con marca (Supabase → Email Templates: Oscar pega el
   HTML que dejes en `docs/email-templates/`).
4. UI en Perfil > Cuenta (T-V6-50): "Exportar mis datos" (descarga) y "Borrar cuenta" (confirm
   con escribir "BORRAR").

**Commit.** `feat(v6): T-V6-65 — exportar y borrar cuenta, verificación de email, plantillas de auth con marca`

---

### T-V6-66 · Moderación del catálogo y aviso de derechos (S)

`PATCH /catalog/scores/{id}/status` (`hidden`/`removed`, solo `settings.admin_user_ids`),
`DELETE /catalog/scores/{id}/comments/{cid}` (autor o admin), `POST /catalog/scores/{id}/report`
(tabla `reports(kind, ref_id, reporter_id, reason, created_at)` + email a Oscar). Aviso al
publicar (T-V6-16) y enlace "Reportar" en el detalle.

**Commit.** `feat(v6): T-V6-66 — moderación mínima del catálogo y reportes`

---

### T-V6-67 · Búsqueda global y atajos (S)

`Ctrl+K` abre `bfDialog` con `bf-search`; busca en cliente sobre `/songs/`, setlists, `/me/events`,
miembros (cacheados en `core/session.js`) con un `scoring` simple (prefijo > contiene); Enter
navega. Hoja de atajos `?` (ya existe en el reproductor: extiéndela al shell).

**Commit.** `feat(v6): T-V6-67 — búsqueda global Ctrl+K y hoja de atajos`

---

### T-V6-68 · Landing pública y páginas de error (S)

`public/index.html` (sin shell): hero con claim, 3 bloques de valor, capturas (de
`harness/capturas/`), CTA "Empezar gratis" → `login.html`, pie legal. `/` deja de redirigir a
`app.html` **solo si no hay sesión** (el redirect lo hace `index.html` con `getSession()`; el
backend sirve `index.html` en `/`). `404.html`/`500.html` con marca; FastAPI devuelve `404.html`
para rutas desconocidas que acepten HTML.

**Commit.** `feat(v6): T-V6-68 — landing pública y páginas 404/500`

---

## 8. Fase V6-F7 · Infra y operación

### T-V6-70 · Staging y previews (M)
Oscar crea el proyecto Supabase "bandflow-staging" (gratis) y aplica `alembic upgrade head`.
En Vercel: `DATABASE_URL`, `SUPABASE_URL`, `SUPABASE_ANON_KEY` del staging en el entorno
**Preview**; producción sigue con los suyos. Supabase staging: Auth → URL de redirect con el
patrón `https://*-kabalah314-ux.vercel.app/**`. Workflow `smoke.yml` (on `deployment_status`
success): `curl /health`, `curl /static/app.html` 200, y un Playwright mínimo contra la URL del
deploy con una cuenta de prueba de staging (secretos de GitHub).

**Commit.** `chore(v6): T-V6-70 — staging en previews y smoke post-deploy`

### T-V6-71 · Migración automática en el deploy (M)
Workflow `deploy.yml` en `push: main`: `alembic upgrade head` contra **producción** con
`DATABASE_URL_MIGRATIONS` (pooler de sesión 5432) desde secretos de GitHub → si falla, para;
si va bien, `vercel deploy --prod` con el token de Vercel (y desactivar el auto-deploy de Git en
Vercel para que solo despliegue el workflow). Para previews: `alembic upgrade head` contra
staging en el workflow de PR. Documenta el rollback: `vercel rollback` + `alembic downgrade -1`.

**Commit.** `chore(v6): T-V6-71 — migraciones automáticas antes de promover; deploy desde workflow`

### T-V6-72 · Backups y runbook (S)
Workflow `backup.yml` (cron diario 03:00 UTC): `pg_dump --no-owner` por el pooler de sesión →
`gzip` → sube como artefacto cifrado (retención 30 días) o a un bucket privado de Supabase
Storage (`backups/`, política solo `service_role`). `docs/runbook.md`: restaurar en staging una
vez por trimestre (comando `psql < dump`), rollback de deploy, rotación de secretos, qué hacer
si Supabase cae (modo gracia) y contactos.

**Commit.** `chore(v6): T-V6-72 — backups diarios y runbook`

### T-V6-73 · Dominio, HSTS y CSP (S)
Oscar añade el dominio en Vercel y Supabase (redirects). `main.py`: cabecera
`Strict-Transport-Security: max-age=31536000; includeSubDomains` solo si `request.url.scheme ==
'https'` y host ≠ localhost; `Content-Security-Policy` con `default-src 'self'; script-src 'self'
'nonce-<n>'; style-src 'self' 'nonce-<n>'; img-src 'self' https://<ref>.supabase.co data:;
connect-src 'self' https://<ref>.supabase.co https://openrouter.ai; font-src 'self'; frame-src
https://www.youtube-nocookie.com`. El nonce se inyecta en los HTML servidos (plantilla simple que
sustituye `{{nonce}}` en los `<script>`/`<style>` inline; los estilos inline eliminados en
T-V6-37 lo hacen posible). Quita `onclick` inline (`bands.js:1245`). Renombrar repo (D-V6-13)
si Oscar quiere.

**Commit.** `chore(v6): T-V6-73 — dominio propio, HSTS y CSP con nonce`

### T-V6-74 · Rate limiting completo y cuotas de IA (S)
Sustituye el limitador en memoria de T-V6-06 por uno con **Postgres** (tabla `rate_hits(key,
window_start, count)` con `UPSERT`) o Vercel KV; aplica a `/invites/*` (20/min por IP),
`/public/*` (60/min por IP), `/catalog/*` (30/min por usuario), `/import/*` (10/min + cuota
diaria configurable). IP real: `X-Forwarded-For` (primer valor) en Vercel.

**Commit.** `feat(v6): T-V6-74 — rate limiting persistente por usuario/IP y cuotas de IA`

### T-V6-75 · Índices y limpieza (S)
Migración con índices: `ix_events_band_starts (band_id, starts_at)`, `ix_messages_band_event_created
(band_id, event_id, created_at)`, `ix_transactions_event (event_id)`, `ix_events_setlist`,
`ix_events_venue`, `ix_songs_owner_band_deleted (owner_id, band_id, deleted_at)`. Expón
`Band.currency` en `BandResponse/BandUpdate`. Deja las columnas muertas (`Song.is_public`…) para
una migración de borrado posterior, documentada en el ADR de datos.

**Commit.** `perf(v6): T-V6-75 — índices compuestos para las consultas reales; moneda de banda expuesta`

---

## 9. Fase V6-F9 · Producto: lo que hará que los músicos la quieran

> Todas las tareas siguen el mismo esqueleto: **modelo + migración → router con guard y tests de
> aislamiento/rol → UI con componentes de F3 → test de flujo e2e**. Las decisiones D-V6-20…26
> deben estar cerradas (Parte I §11).

### T-V6-80 · Invitación con preview público + `bfShare` (M)

**Backend.**
1. `GET /public/invites/{code}` (sin auth, en `public_router.py`) → `PublicInvitePreview{band_name,
   band_avatar_url, band_cover_url, member_count, song_count, next_event: {title, starts_at,
   venue_name}|null, role_to_grant, valid, reason}`. Solo datos de la banda que la propia banda
   ya expone en eventos públicos; **nunca** emails, teléfonos ni nombres de miembros. Rate limit
   20/min por IP. Test de no-fuga: el JSON no contiene `@` ni `user_id`.
2. `GET /invites/{code}` existente se mantiene (lo usa `join.js` con sesión).

**Frontend.**
3. `core/share.js`:
   ```js
   export async function bfShare({ title, text, url }) {
       if (navigator.share) { try { await navigator.share({ title, text, url }); return true; } catch (e) { if (e.name === 'AbortError') return false; } }
       const wa = `https://wa.me/?text=${encodeURIComponent(text + '\n' + url)}`;
       window.open(wa, '_blank', 'noopener');          // fallback: WhatsApp web/app
       return true;
   }
   export async function bfCopy(text) { try { await navigator.clipboard.writeText(text); toast('Enlace copiado', 'success'); } catch { prompt('Copia el enlace', text); } }
   ```
4. `join.html` (T-V6-41) usa el preview público ANTES de pedir sesión: cover, avatar, nombre,
   "3 miembros · 12 canciones · próximo bolo: Sala Caracol, 14 nov" y el botón "Unirme" →
   si no hay sesión, `login.html?next=`.
5. Botón **Compartir** (icono `share`) en: invitación (texto: "Únete a {banda} en BandFlow:
   {url}"), evento compartido ("{banda} toca en {sala} el {fecha}: {url}"), setlist compartido
   (T-V6-63), hoja del bolo (T-V6-86), votación (T-V6-82).

**Test e2e.** `GET /public/invites/{code}` → la página muestra `.join-preview` con el nombre
de la banda sin sesión (usa `page.route('/config', …test_mode:false…)` + stub del SDK).

**Commit.** `feat(v6): T-V6-80 — invitación con preview público y compartir por WhatsApp/Web Share`

---

### T-V6-81 · Vista por miembro de la canción (M)

1. Modelo `SongMemberPref(song_id FK, user_id, transpose int default 0, capo int|null,
   view_mode in ('full','lyrics','chords','structure') default 'full', font_scale numeric
   default 1.0, updated_at)` con `UniqueConstraint(song_id, user_id)`; migración.
2. Router: `GET/PUT /songs/{id}/my-view` (owner-scoped por `user_id`; la canción debe ser mía
   o de una banda donde soy miembro activo: reutiliza `active_membership`). Test: ajeno → 404;
   mi pref no afecta a la de otro usuario.
3. Reproductor: al cargar la canción, `apiJson('/songs/'+id+'/my-view')` → aplica
   `transposeOffset = pref.transpose` (ya existe la transposición en cliente: `changeTranspose`),
   `--score-scale`, y el **modo de vista**: `lyrics` oculta `.chord-pill` (`#score-content.view-lyrics .chord-container .chord-pill { display:none }`
   — CSS, el DOM del motor no cambia), `chords` oculta `.line-lyric`, `structure` muestra solo
   nombres de sección con su nº de compases (calculado de `sectionRanges`). El botón
   `#btn-key-save` pasa a "Guardar mi tono" (`PUT my-view`) y el menú ofrece "Guardar como tono
   de la banda" (el `PATCH /songs` actual, solo no-guest). Capo: campo en el popover de Tono
   que muestra los acordes transpuestos para esa cejilla (`transposeChord(name, -capo)` en la
   vista, sin cambiar los datos).
4. Selector "Mi vista" (`bf-segmented` en la barra inferior o en el menú ⋯): Todo · Letra ·
   Acordes · Estructura; persiste en la pref.

**Test.** Unit del router; e2e: cambiar a "Letra" oculta `.chord-pill` y recargar mantiene la vista.

**Commit.** `feat(v6): T-V6-81 — vista por miembro: mi tono, cejilla, modo de vista y tamaño`

---

### T-V6-82 · Votación de fechas sin cuenta (L)

**Modelo.** `DatePoll(id, band_id, title, kind in ('rehearsal','concert','other'), notes,
created_by, status in ('open','confirmed','cancelled'), confirmed_option_id|null, event_id|null,
created_at, closes_at|null)`; `DatePollOption(id, poll_id, starts_at, ends_at|null, position)`;
`DatePollVote(id, poll_id, option_id, member_user_id, status in ('yes','maybe','no'),
voted_at)` con `Unique(option_id, member_user_id)`; `DatePollToken(id, poll_id, member_user_id,
token String(64) unique, created_at)` (un token por miembro y votación: el enlace identifica al
votante sin cuenta). Migración.

**Backend.**
- `POST /bands/{id}/polls` (miembro no-guest): crea poll + opciones (1–6) + un token por miembro
  activo. `GET /bands/{id}/polls`, `GET /bands/{id}/polls/{pid}` (con tabla de votos),
  `POST /bands/{id}/polls/{pid}/confirm {option_id}` (admin): crea `Event` con `starts_at` de la
  opción y `EventAttendance` por cada voto `yes/maybe/no`; marca `confirmed`; `DELETE` cancela.
  Guards + tests de aislamiento/rol.
- Público: `GET /public/polls/{token}` → `{band_name, title, options[], my_votes, members: [{name, votes}]}`
  (nombres de miembros SÍ, porque es el contexto de la banda; emails no); `POST /public/polls/{token}/votes
  {option_id, status}`. Rate limit por IP. El token es de un miembro: solo vota por él.
- Votar con sesión: `POST /bands/{id}/polls/{pid}/votes` (miembro).

**Frontend.**
- Agenda de banda: botón "Proponer fechas" → `bfDialog`: tipo, título, 1–6 opciones
  (fecha+hora), notas → crea → pantalla de la votación con **tabla** (filas = miembros, columnas
  = opciones, celdas Sí/Quizás/No) + botón "Compartir por WhatsApp" (texto: "¿Cuándo ensayamos?
  Vota aquí: {url del token de cada miembro}" — una URL por miembro: el diálogo muestra la
  lista "copiar enlace de Ana / de Luis" y un botón "Enviar a todos" que abre `wa.me` con el
  mensaje genérico + instrucciones; D-V6-21 detalla si se envía uno por persona).
- `votar.html?t=` (sin shell, `theme.js`): cabecera con banda y título, tarjeta por opción con
  `bf-segmented` Sí/Quizás/No, resumen "3 de 4 han votado", y CTA "Entrar en BandFlow". Sin
  cuenta.
- Agenda y Resumen: las votaciones abiertas aparecen como ítems `kind='proposal'` (estilo
  fantasma en `bf-calendar`), con "Confirmar" para admin.

**Test de flujo e2e.** Crear votación → votar por token (sin sesión, `page.route` del config a
`test_mode:false` no es necesario: `votar.html` no usa auth) → confirmar → el evento aparece en
`/me/events` con `my_status` del voto.

**Commit.** `feat(v6): T-V6-82 — votación de fechas con enlace por miembro sin cuenta y confirmación a evento`

---

### T-V6-83 · Semáforo del repertorio (M)

1. `SongStatus(id, song_id FK, user_id, status in ('pending','improving','ready') default
   'pending', shared bool default false, updated_at)` `Unique(song_id, user_id)`; migración.
2. `PUT /bands/{id}/songs/{sid}/my-status {status, shared}`; `GET /bands/{id}/songs/` añade
   `my_status` y, si `shared`, `band_status: {ready: n, improving: n, pending: n}`;
   `GET /bands/{id}/summary` añade `readiness: {mine: {...}, band: {...}}`;
   `GET /me/dashboard` añade `next_event_missing: n` (canciones del setlist del próximo
   concierto que no tengo en `ready`).
3. UI: en cada fila del repertorio `bf-segmented` compacto de 3 (icono `circle` gris /
   `circle-dot` ámbar / `check-circle` verde) con `title`; en Resumen, `bf-stat` + barra
   apilada (SVG) "Tu progreso" y "La banda"; en Inicio: "Para {evento} te faltan N canciones"
   con enlace al repertorio filtrado.

**Commit.** `feat(v6): T-V6-83 — semáforo del repertorio por miembro y progreso en resumen e inicio`

---

### T-V6-84 · Modo ensayo (L)

1. Página `ensayo.html?band=&event=` (shell oculto, estilo escenario claro/oscuro): columna
   izquierda = lista de canciones a repasar (orden: setlist del próximo concierto, luego
   `improving`, luego `pending`; cada una con semáforo, cronómetro y botones Tocar / Apunte /
   Grabar / Hecha); derecha = cronómetro total y "Apuntes de hoy".
2. `RehearsalSession(id, band_id, event_id|null, started_at, ended_at|null, started_by)` +
   `RehearsalSongLog(session_id, song_id, seconds, done, note)`; migración; router con guard.
3. "Apunte" → `BandNote` (T-V6-92) con `source='rehearsal'`; "Grabar" → T-V6-85 (`attachments`
   con `song_id`, `event_id`); "Hecha" → marca `done` y ofrece subir el semáforo.
4. "Terminar ensayo" → `POST …/rehearsals/{id}/finish` genera el resumen ("Ensayo de 1 h 40:
   6 canciones, 2 apuntes, 1 grabación") y lo publica como mensaje de chat (`Message` con
   `author_id` del que cierra y cuerpo con enlaces).
5. Entrada: botón "Empezar ensayo" en el drawer de un evento `rehearsal` (hoy o pasado 2 h).

**Commit.** `feat(v6): T-V6-84 — modo ensayo con lista de repaso, cronómetro, apuntes, grabaciones y resumen al chat`

---

### T-V6-85 · Adjuntos: PDF de partitura, audio e imágenes + grabadora (L)

1. `Attachment(id, owner_id, band_id|null, song_id|null, event_id|null, kind in ('pdf','audio',
   'image'), storage_path, title, mime, size_bytes, duration_sec|null, created_at, deleted_at)`;
   migración. Router `/attachments` (POST metadatos tras subir, GET por song/event, DELETE
   propio o admin) con `active_membership` cuando hay `band_id`. Límites: 15 MB pdf/imagen,
   25 MB audio.
2. Storage: `upload.js` ya sube a `media/{uid}/…`; para adjuntos de banda usa la ruta
   `media/bands/{band_id}/{uuid}` y **política RLS** en Supabase Storage que permita escribir
   solo a miembros (Oscar aplica el SQL que dejes en `docs/storage-policies.sql`: comprueba
   `band_memberships` vía `auth.uid()`). Lectura: pública con URL firmada de 1 h
   (`createSignedUrl`) si Oscar prefiere no exponer PDFs; decisión en D-V6-25.
3. Grabadora (`ui/recorder.js`): `MediaRecorder` (webm/opus; en iOS `audio/mp4`), botón
   grabar/parar con tiempo, preview, "Guardar en la canción".
4. Reproductor: si la canción tiene un adjunto `pdf`, botón "Partitura PDF" que muestra el PDF
   (`<iframe>` o `pdf.js` autoalojado) a pantalla completa con paso de página por pedal
   (PageDown) — el motor no interviene (sin auto-scroll). Si solo hay PDF y no acordes, el
   reproductor abre directamente el PDF.
5. Editor/Repertorio: "Adjuntar PDF" en el ⋯ de la canción; lista de adjuntos en el drawer del
   evento (fotos del bolo, rider).

**Commit.** `feat(v6): T-V6-85 — adjuntos (PDF, audio, imagen) con grabadora y visor de PDF en el reproductor`

---

### T-V6-86 · Hoja del bolo (M)

1. Columnas en `events`: `load_in_at, soundcheck_at, doors_at, set_at (DateTime tz)`, `address
   String(512)`, `parking_notes Text`, `backline_notes Text`, `sheet_token String(64)|null`.
   `EventChecklistItem(id, event_id, text, assignee_user_id|null, due_date|null, done_at|null,
   position)`. Migración.
2. Router: campos en `EventUpdate/Response`; `GET/POST/PATCH/DELETE …/events/{eid}/checklist`;
   `POST …/events/{eid}/sheet-token` (genera/regenera; admin); `GET /public/gig-sheet/{token}`
   (proyección: todo lo logístico, setlist con títulos; sin teléfono salvo opt-in explícito
   `share_contact bool`).
3. UI: en el drawer del evento (concierto), pestaña "Hoja del bolo" con los horarios en una
   línea de tiempo (carga → prueba → puertas → set), dirección con enlace a mapas
   (`https://maps.google.com/?q=`), checklist con responsable (avatar) y "hecho", y botones
   "Imprimir" y "Compartir por WhatsApp" (`bolo.html?t=`).
4. `bolo.html?t=` pública e imprimible (`@media print`), con `theme.js`.
5. Los ítems de checklist con `due_date` aparecen en el calendario (`kind='checklist'`, T-V6-62).

**Commit.** `feat(v6): T-V6-86 — hoja del bolo con horarios, logística, checklist y página pública imprimible`

---

### T-V6-87 · Modo práctica (M)

1. `sections.ref_start_sec Integer|null` (marca de tiempo del vídeo de referencia por sección);
   editor: campo pequeño junto al nombre de sección (o "Marcar ahora" mientras suena el vídeo).
2. Reproductor: botón "Práctica" (menú ⋯) que muestra una barra: sección A → B (selects), tempo
   50–100 % (usa `engine.state.tempoMultiplier` ya existente), "Repetir" (al llegar al final de
   B, `engine.stop()` + volver al inicio de A: igual que la parada de T-V6-56, pero reanudando
   en `pausedAtBeat = inicioA` — mismo tipo de excepción al motor, documentada), y "Vídeo desde
   la sección" (`reference-embed` con `?start=ref_start_sec`).

**Commit.** `feat(v6): T-V6-87 — modo práctica: bucle por secciones, tempo reducido y referencia por sección`

---

### T-V6-88 · Setlist inteligente y duración (S)

1. `songs.duration_sec Integer|null` (editor: campo mm:ss; si falta, se estima: 210 s).
   `SetlistResponse.total_sec` y `SetlistSummary.total_sec` (suma con estimación).
2. `core/setlist_smart.js`: `suggestOrder(songs)` → arranque con BPM alto, alterna energía
   (BPM) evitando 3 lentas seguidas, agrupa tonos cercanos (círculo de quintas: distancia ≤ 2),
   cierra fuerte; `warnings(order)` → ["3 canciones en Mi seguidas", "2 baladas seguidas"].
   Vitest con 10 canciones.
3. Editor de setlist: botón "Sugerir orden" (aplica y permite deshacer) y avisos bajo la lista;
   duración total en la cabecera.

**Commit.** `feat(v6): T-V6-88 — duración de canciones/setlists y sugerencia de orden`

---

### T-V6-89 · Recordatorios con respuesta por enlace (M)

Extiende T-V6-60: el email de recordatorio lleva dos enlaces `GET /public/rsvp/{token}?status=yes|no`
(tabla `rsvp_tokens(token, event_id, user_id, used_at)`, un solo uso, 48 h) que registran la
asistencia y muestran una página de confirmación con "Abrir en BandFlow". Resumen a admins
48 h antes: "faltan 2 por responder" (solo si hay no respondidos).

**Commit.** `feat(v6): T-V6-89 — recordatorios con respuesta de asistencia por enlace`

---

### T-V6-90 · Una banda = inicio en la banda; 7 pestañas; Giras agrupación; Explorar tras bandera (M)

1. `shell.js`: tras `/bands/`, si `bands.length === 1` y la página es `app.html`, redirige a
   `band.html?id=…#resumen` (una vez por sesión; `?all=1` fuerza Inicio TÚ). El lateral con 1
   banda muestra las pestañas de la banda como ítems (Resumen, Canciones, Agenda, Chat,
   Finanzas, Miembros, Ajustes) + "Mis canciones" + Perfil; con ≥ 2, el lateral actual.
2. Pestañas de banda: Resumen · Canciones (sub-pestañas Repertorio / Setlists / Colecciones) ·
   Agenda · Chat · Finanzas · Miembros · Ajustes. Los paneles `data-panel="repertorio|setlists"`
   se conservan dentro de "Canciones" (los tests siguen encontrándolos); `data-tab="giras"`
   desaparece: su contenido pasa a Agenda como filtro "Giras" (`#b-tours` sigue existiendo
   dentro del panel de agenda).
3. Explorar: `settings.chordflow_explore_enabled` (default `False`) → `/config` lo expone; el
   lateral solo lo pinta si es `true`; `editor` no publica si está apagado.
4. Afinador/Metrónomo → pie del lateral como "Herramientas" (D-V6-24).
5. Tests: `test_shell.py` con 1 banda → redirección; con 2 → lateral TÚ.

**Commit.** `feat(v6): T-V6-90 — navegación centrada en la banda, 7 pestañas, giras en agenda, explorar tras bandera`

---

### T-V6-91 · Importar desde texto de WhatsApp / PDF; modo solo letra (S)

Diálogo "Importar" (T-V6-46) gana la pestaña "Pegar texto" (el `#raw-text` ya parsea acordes;
añade un botón "Es solo letra" que marca `view_mode` por defecto `lyrics` para la canción) y
"PDF": `pdf.js` autoalojado extrae el texto (`getTextContent`) página a página y lo vuelca en
`#raw-text` (si no hay texto — PDF escaneado — ofrece adjuntarlo como partitura PDF, T-V6-85).

**Commit.** `feat(v6): T-V6-91 — importar desde texto pegado o PDF; canciones solo letra`

---

### T-V6-92 · Pizarra de banda (M)

`BandNote(id, band_id, author_id, body, is_pinned, due_date|null, done_at|null, assignee_user_id|null,
source in ('manual','rehearsal'), created_at)`; migración; `GET/POST/PATCH/DELETE /bands/{id}/notes`
con guard (guest solo lee). UI: pestaña en Canciones? No: **bloque en Resumen** ("Pizarra",
pinneados primero, añadir rápido con Enter, marcar hecho, asignar, fecha) + vista completa en
Agenda > "Pendientes". Items con `due_date` → calendario (`kind='note'`).

**Commit.** `feat(v6): T-V6-92 — pizarra de banda`

---

### T-V6-93 · Resumen de temporada (S)

`GET /bands/{id}/season-summary?year=` → `{concerts_done, total_fee, expenses, per_member_share,
top_songs: [{title, times}], months: [...]}` (de eventos `done`, movimientos y setlists usados en
conciertos). Tarjeta en Finanzas y en Resumen (diciembre/enero destacada); "Compartir como
imagen": render a `<canvas>` (texto + barras con tokens) → `toBlob` → `bfShare` con archivo si
`navigator.canShare({files})`, si no descarga PNG.

**Commit.** `feat(v6): T-V6-93 — resumen de temporada compartible`

---

### T-V6-94 · Feedback in-app y eventos de producto (S)

`Feedback(id, user_id, page, body, screenshot_path|null, created_at)` + `POST /feedback`
(rate limit 5/día) + email a Oscar; botón "¿Algo falla?" en el pie del lateral (`bfDialog` con
texto y captura opcional vía `html2canvas` autoalojado o solo texto). `product_events(id,
user_id, band_id, kind, created_at)` + `POST /events/track` (lista cerrada de `kind`:
`band_created, song_added, setlist_played, stage_opened, event_created, attendance_set,
invite_accepted, poll_created`) llamado desde los flujos; consulta semanal en `docs/metrics.sql`.

**Commit.** `feat(v6): T-V6-94 — feedback in-app y eventos de producto`

---

### T-V6-95 · Gastos recurrentes (S)

`RecurringTransaction(id, band_id, description, amount, category, day_of_month, split_mode
('equal'|'custom'), splits JSON, active, last_run_month)`; `GET/POST/PATCH/DELETE
/bands/{id}/recurring`; el cron de T-V6-60 crea el `Transaction` del mes el día indicado y
notifica. UI en Finanzas: "Gastos fijos" con "Local de ensayo · 60 € · día 1 · entre 3".

**Commit.** `feat(v6): T-V6-95 — gastos recurrentes con reparto por defecto`

---

## 10. Fase V6-F9b · Red profesional: salas, convocatorias y profesionales

> Prerrequisitos: D-V6-27/28/29 cerradas; DM base de la V5 (`T-V5-21`) implementado (el
> "Contactar" de todas las fichas abre un DM con `context_ref`). Si el DM no existe aún, el botón
> "Contactar" muestra el teléfono/WhatsApp **solo con opt-in** y el email nunca.

### T-V6-96 · Perfiles de sala y profesional + fichas públicas + Explorar (L)

1. **Modelo** (Parte I §9.9.4): `ProProfile`, `VenueProfile` (1:1 con `ProProfile` de `kind='venue'`),
   `plan` String default `'free'`. Migración. Reutiliza `visibility` ('private'|'public'),
   `zone` texto libre, `phone` + `whatsapp_optin`.
2. **Router `/pro`** (owner-scoped): `GET /pro/mine`, `POST /pro` (crea; un usuario puede tener
   varios), `PATCH/DELETE /pro/{id}` (solo dueño → ajeno 404), subida de fotos vía `upload.js`
   a `media/{uid}/pro/…`.
3. **Explorar** (`GET /explore/venues`, `/explore/pros?kind=&zone=&q=`): `limit` ≤ 50, orden
   `updated_at desc`, solo `visibility='public'`, **proyección segura** `{id, kind, name, zone,
   avatar/cover, services, price_hint, verified, rating_avg, rating_count}` — nunca `phone` ni
   `user_id`. Test de no-fuga por grep del JSON.
4. **Fichas públicas** `sala.html?id=` y `pro.html?id=` (`GET /public/pros/{id}`: igual que la
   proyección + bio, fotos, enlaces, condiciones, backline, aforo; teléfono/WhatsApp solo si
   `whatsapp_optin` y el visitante tiene sesión → `GET /pro/{id}/contact` autenticado).
5. **UI de alta**: Perfil > "Mis perfiles profesionales" → "Añadir perfil" (`bfDialog` de 2
   pasos: tipo (D-V6-29) → datos); vista de edición con subida de fotos y preview de la ficha.
6. **Explorar UI**: dos grupos de pestañas (D-V6-27). Tarjetas `bf-card--cover` con foto,
   nombre, categoría, zona, badge "verificada", valoración; filtros `bf-chip` (categoría) +
   `bf-search` (zona/nombre); paginación "Cargar más". "Contactar" → DM (V5 I-3) con
   `context_ref: {kind:'pro', id, label}`.
7. Lateral: Explorar visible si `chordflow_explore_enabled` (T-V6-90) **o** si
   `chordflow_pro_network_enabled` (bandera nueva para encender solo este bloque primero).

**Tests.** Unit: CRUD owner-scoped, ajeno 404, `private` no aparece en `/explore/*`, no-fuga.
E2E: alta de un perfil de sala → aparece en Explorar > Salas → ficha pública abre sin sesión.

**Commit.** `feat(v6): T-V6-96 — perfiles de sala y profesional, fichas públicas y explorar de la red profesional`

---

### T-V6-97 · Convocatorias de bolos y candidaturas → evento (L)

1. **Modelo**: `GigCall`, `GigApplication` (Parte I §9.9.4) + `band_epk` mínimo si T-V6-98 no
   está (campos `bio, styles, links, fee_hint` en `bands` sirven de arranque). Migración.
2. **Router**: `POST/GET/PATCH /pro/{venue_id}/calls` (dueño de la sala), `GET /explore/calls?zone=&style=&from=`
   (abiertas, proyección segura: sala, fecha, estilo, condiciones, fee si la sala marcó
   `show_fee`), `POST /bands/{band_id}/applications {call_id, message}` (admin de la banda; una
   por banda y convocatoria → 409), `GET /pro/{venue_id}/calls/{cid}/applications` (dueño),
   `PATCH …/applications/{aid} {status}` (dueño: `seen|shortlisted|chosen|declined`), y al pasar
   a `chosen`: crea `Event(type='concert', status='negotiating', starts_at=call.starts_at,
   venue_name=sala, fee=call.fee, created_by=band admin que se postuló, visibility='private')`
   en la banda + `Venue` privada de la banda si no existe (match por nombre+ciudad) + mensaje
   de sistema en el DM; el resto de candidaturas `sent/seen/shortlisted` → `declined` + DM
   automático "Esta vez no ha podido ser". Guards: dueño de sala vs admin de banda; tests de
   aislamiento en ambos lados.
3. **UI sala**: en la ficha propia, "Convocatorias" con crear (`bfDialog`: fecha o rango,
   estilos, formato, condiciones, fee + "mostrar caché", fecha límite) y **tablero** de
   candidaturas (columnas Nuevas / Vistas / Finalistas / Elegida) con la tarjeta EPK de cada
   banda y botones.
4. **UI banda**: Explorar > Bolos abiertos (tarjetas: sala, ciudad, fecha, condiciones, "N
   candidaturas") → "Postularnos" (`bfDialog`: elige banda si tienes varias, mensaje, vista
   previa del EPK) → estado visible en Agenda > "Candidaturas" (ítems `kind='application'`).
   Al ser elegida: notificación (T-V6-61) + el evento aparece en la agenda con el pipeline de
   booking.
5. **Inicio**: tarjeta "Bolos abiertos cerca de ti" (3) si la banda tiene zona.

**Test de flujo e2e (I-20).** Sala crea convocatoria → banda se postula → sala elige → la banda
tiene un `Event` `negotiating` con la sala; las otras candidaturas quedan `declined`.

**Commit.** `feat(v6): T-V6-97 — convocatorias de bolos, candidaturas con EPK y conversión a evento`

---

### T-V6-98 · EPK de banda, página pública ampliada y "Proponernos" (M)

1. `BandEpk(band_id PK, bio, styles JSON, formation, zone, links JSON, photos JSON, fee_hint,
   rider_notes, is_public bool, updated_at)`; migración; `GET/PUT /bands/{id}/epk` (admin
   escribe, miembros leen).
2. Ajustes de banda: sección "EPK / cómo nos ven" con los campos, subida de 1–6 fotos, enlaces
   (vídeo, Spotify, redes) y vista previa de la página pública.
3. `banda.html?id=` (V5 I-16): bio, fotos, enlaces, estilos, próximos conciertos públicos,
   originales (cuando exista Descubrir), anuncio activo, "Contactar" y, para salas, "Invitar a
   tocar" (abre DM con `context_ref: {kind:'band'}`). `GET /public/bands/{id}` solo si `is_public`.
4. Desde la ficha de una sala: botón "Proponernos" (admin de banda) → DM con el EPK adjunto
   (`context_ref: {kind:'venue'}` + enlace a `banda.html`).

**Commit.** `feat(v6): T-V6-98 — EPK de banda, página pública y proponerse a una sala`

---

### T-V6-99 · Valoraciones, reportes, verificación y anti-spam (M)

1. `Review(id, from_user_id, to_pro_profile_id|null, to_band_id|null, stars 1..5, body ≤ 500,
   event_id|null, created_at)` `Unique(from_user_id, to_pro_profile_id, to_band_id)`; regla
   servidor: solo si existe un DM entre ambos o un evento confirmado que los una (consulta
   previa; si no → 403 "Solo puedes valorar a quien has tratado").
2. `rating_avg/rating_count` desnormalizados en `pro_profiles`/`band_epk` (recalcula al
   insertar).
3. Reportar (`POST /reports` de T-V6-66 ampliado a `kind in ('pro','call','band','score','comment')`).
4. Verificación: `verified_at` lo pone un admin de BandFlow (`settings.admin_user_ids`) desde
   un endpoint `PATCH /admin/pros/{id}/verify` + página mínima `admin.html` (solo para esos
   ids) con la cola de perfiles nuevos y reportes.
5. Anti-spam: perfiles con < 7 días: máximo 5 "Contactar" al día; rate limit en `/explore/*` y
   `/public/*` (T-V6-74).

**Commit.** `feat(v6): T-V6-99 — valoraciones con relación previa, reportes, verificación y límites`

---

### T-V6-100 · Calendario de sala (S)

`GET /pro/{venue_id}/calendar` → items `kind='call'|'event'` (convocatorias abiertas + eventos
confirmados donde `Event.venue_profile_id = venue`); pinta `bfCalendar` en la ficha propia de la
sala (y una versión pública con solo fechas ocupadas/libres si `show_calendar`). Al confirmar
un bolo desde una candidatura, `Event.venue_profile_id` se rellena (columna nueva, nullable).

**Commit.** `feat(v6): T-V6-100 — calendario de sala`

---

## 11. Anexos

### 11.A Anclas que usan los tests e2e (ids, clases y `data-*` por fichero de test)

> Generado con un script sobre `tests/e2e/*.py` (commit `d61f165`). Regla: antes de renombrar
> cualquier id/clase/`data-*` de esta lista, actualiza el test en el mismo commit. Para
> regenerarlo: `python harness/anclas_tests.py` (créalo copiando el script de abajo).

```text
test_accesibilidad.py | páginas: app.html, index.html, setlists.html
  ids: #bf-theme-btn
  clases: .chord-container .setlist-item-btn .song-card
  data: data-act
test_acento_tema.py | páginas: setlists.html
  ids: 
  clases: 
  data: 
test_afinador2.py | páginas: afinador.html
  ids: #tuner-a4 #tuner-note #tuner-status
  clases: 
  data: 
test_agenda.py | páginas: agenda.html
  ids: #agenda-filters #agenda-past #agenda-upcoming
  clases: 
  data: data-band
test_agenda_menu.py | páginas: band.html
  ids: 
  clases: .att-btn .bf-tab .ev-more-menu .setlist-song
  data: data-act data-tab
test_anadir_a.py | páginas: library.html
  ids: 
  clases: .add-to-list .add-to-row .modal-card .song-card .toast
  data: data-act data-cid
test_ancho.py | páginas: app.html
  ids: 
  clases: .bf-page--wide
  data: 
test_atajos.py | páginas: index.html
  ids: #btn-shortcuts
  clases: .chord-container .modal-card .modal-overlay
  data: 
test_band_space.py | páginas: band.html
  ids: #b-add-song #b-new-tour #b-repertoire #b-tour-detail #b-tours
  clases: .bf-band-banner .bf-tab .bf-tabs .bs-panel .modal-overlay
  data: data-act data-panel data-tab data-tour
test_banda_lateral.py | páginas: app.html
  ids: #bf-bands-subnav
  clases: .bf-avatar
  data: 
test_bands_ui.py | páginas: bands.html, index.html, join.html, profile.html
  ids: #b-add-song #b-agenda #b-chat #b-collections #b-export-csv #b-finance #b-new-collection #b-new-event #b-new-setlist #b-new-tx #b-repertoire #b-setlists #b-tx-list #b-venues #bands-grid #bs-invite #btn-new-band #chat-input #chat-send #col-available #col-songs #col-to-setlist #copy-list #ev-contact #ev-date #ev-fee #ev-title #ev-type #ev-venue #join-accept #join-box #pf-inst #pf-name #pf-save #setlist-nav #sl-available #sl-name #sl-save #sl-selected #thread-input #thread-list #tx-amount #tx-desc #tx-event #tx-split-mode #tx-split-sum #tx-splits #v-city #v-name
  clases: .bf-band-banner .bf-tab .bs-panel .csv .modal-overlay .song-card
  data: data-act data-add data-att data-id data-panel data-rm data-tab
test_buscador_repertorio.py | páginas: band.html
  ids: #b-rep-search #b-repertoire
  clases: .bf-tab .filter
  data: data-tab
test_cache_temporada.py | páginas: band.html
  ids: #b-seasons
  clases: .bf-tab
  data: data-tab
test_card_play.py | páginas: library.html
  ids: 
  clases: .card-play .song-card
  data: 
test_catalogo.py | páginas: app.html, biblioteca-global.html
  ids: #cat-back #cat-import #cat-results #cat-search #cat-search-btn #cat-stars
  clases: .bf-band-banner .bf-sidebar
  data: data-score data-star
test_chat.py | páginas: chat.html
  ids: #chat-list
  clases: 
  data: 
test_compartir_evento.py | páginas: band.html, evento.html
  ids: 
  clases: .bf-tab .modal-overlay .pub-brand .pub-card .pub-title .setlist-song
  data: data-act data-id data-tab
test_compas.py | páginas: editor.html, index.html
  ids: #btn-save #current-beat-display #raw-text #time-signature #title
  clases: .chord-container
  data: 
test_cuenta_atras.py | páginas: index.html
  ids: #btn-countin #btn-play-pause #countin-num #countin-overlay #current-beat-display #score-container
  clases: .chord-container
  data: 
test_detalles_pulido.py | páginas: afinador.html, chat.html, editor.html, evento.html
  ids: #btn-import-search #chat-list #import-search #import-search-results #tuner-msg #tuner-needle
  clases: .import-search-item .pub-cta__btn
  data: 
test_duplicar.py | páginas: setlists.html
  ids: 
  clases: .song-card
  data: data-act
test_editor.py | páginas: editor.html
  ids: #btn-import #btn-import-search #btn-save #import-photo #import-search #import-url #preview-content #raw-text #title
  clases: .import-search-empty .import-search-item .join
  data: 
test_escenario.py | páginas: index.html
  ids: #btn-countin #btn-play-pause #btn-stage #score-container
  clases: .chord-container .stage-mode
  data: 
test_finanzas.py | páginas: finanzas.html
  ids: #finanzas-list
  clases: 
  data: 
test_home.py | páginas: app.html
  ids: #home #home-att #home-messages #home-onboarding
  clases: .home-hero
  data: data-att
test_iconos.py | páginas: editor.html, index.html, setlists.html
  ids: #btn-countin #btn-key-save #btn-metronome #btn-play-pause #btn-print #btn-stage #btn-stop #btn-tuner #current-beat-display #score-container #sl-selected
  clases: .chord-container .song-card
  data: data-act data-rm
test_identidad_imagenes.py | páginas: app.html, band.html, profile.html
  ids: #b-members #bf-prof-initials #pf-photo #set-cover #set-logo
  clases: .bf-band-banner .bf-sidebar .bf-tab .pf-identity
  data: data-tab
test_interaccion.py | páginas: app.html
  ids: #home-onboarding
  clases: 
  data: 
test_js_logic.py | páginas: editor.html, index.html
  ids: 
  clases: 
  data: 
test_library.py | páginas: library.html
  ids: #col-name #col-picker #library-collections #search-input #song-grid
  clases: .bf-nav-item .bf-shell .card-action-btn .empty-state .lib-filter .modal-card .modal-overlay .song-card
  data: data-act data-collection data-filter
test_login.py | páginas: login.html
  ids: 
  clases: 
  data: 
test_metronomo_seccion.py | páginas: afinador.html
  ids: #metro-bpm #metro-down #metro-meter #metro-panel #metro-start #metro-up #tuner-panel
  clases: .bf-sidebar .metro-pip .metro-pip--on
  data: 
test_microinteraccion.py | páginas: app.html
  ids: 
  clases: 
  data: 
test_modo_claro_legacy.py | páginas: library.html
  ids: #search-input
  clases: .song-card
  data: 
test_oembed_caratula.py | páginas: editor.html
  ids: #reference-preview #reference-url
  clases: 
  data: 
test_perfil_cuerpo.py | páginas: profile.html
  ids: #pf-bands #pf-inst #pf-instruments #pf-name
  clases: .pf-identity .pf-name
  data: 
test_pestanas_movil.py | páginas: band.html
  ids: 
  clases: .bf-tab .bf-tabs
  data: data-tab
test_player.py | páginas: index.html
  ids: #btn-bpm-up #btn-countin #btn-key-save #btn-key-up #btn-play-pause #btn-print #btn-reference #btn-stage #btn-stop #btn-tuner #current-beat-display #current-section-display #key-value #reference-embed #score-container #score-content #song-title #tuner-close #tuner-panel
  clases: .bottom-bar .chord-container .empty-state .line-lyric .top-bar
  data: 
test_reordenar_setlist.py | páginas: setlists.html
  ids: #btn-new-setlist #sl-available #sl-name #sl-save #sl-selected
  clases: .song-card
  data: data-id data-sid
test_responsive_pwa.py | páginas: editor.html, index.html, library.html, login.html
  ids: 
  clases: 
  data: 
test_resumen_banda.py | páginas: band.html
  ids: #b-summary #bs-att
  clases: .bf-tab .bs-summary
  data: data-att data-go data-tab
test_setlists_ui.py | páginas: setlists.html
  ids: #btn-new-setlist #setlist-detail #setlist-grid #sl-available #sl-name #sl-playall #sl-save #sl-selected
  clases: .song-card
  data: data-act data-id data-rm
test_shell.py | páginas: afinador.html, agenda.html, app.html
  ids: #bf-theme-btn #btn-tuner #tuner-panel
  clases: .bf-backdrop .bf-hamburger .bf-nav-item .bf-shell .bf-sidebar .bf-sidebar-nav
  data: 
test_skeletons.py | páginas: agenda.html
  ids: 
  clases: 
  data: 
test_smoke.py | páginas: app.html, editor.html, library.html, login.html
  ids: 
  clases: 
  data: 
test_sync_engine.py | páginas: index.html
  ids: 
  clases: 
  data: 
test_tarjeta_banda.py | páginas: bands.html
  ids: 
  clases: .bf-avatar .card-main .song-card
  data: data-act
test_tema_coherente.py | páginas: editor.html, index.html, join.html
  ids: 
  clases: .top-bar
  data: 
test_tempo.py | páginas: index.html
  ids: #bpm-value #btn-bpm-down #btn-bpm-up
  clases: .chord-container
  data: 
test_terminologia.py | páginas: band.html
  ids: #b-new-collection
  clases: .bf-tab
  data: data-panel data-tab
test_tipografia.py | páginas: index.html
  ids: 
  clases: .chord-container
  data: 
test_topbar_player.py | páginas: index.html
  ids: #btn-key-save #btn-print #btn-tuner
  clases: .chord-container .top-bar
  data: 
test_tour.py | páginas: band.html
  ids: #bf-tour-ok
  clases: .bf-tabs .bf-tour-tip
  data: 
test_vacios_cta.py | páginas: agenda.html
  ids: #agenda
  clases: 
  data:
```

Script para regenerarlo (`harness/anclas_tests.py`):

```python
import re, glob
for f in sorted(glob.glob('tests/e2e/*.py')):
    s = open(f, encoding='utf-8').read()
    pages = sorted(set(re.findall(r"static/([a-z\-]+\.html)", s)))
    ids = sorted(set(re.findall(r"""['"](#[A-Za-z][\w-]*)""", s)))
    cls = sorted(set(re.findall(r"""['"](\.[a-z][\w-]*(?:__[\w-]+)?)""", s)))
    data = sorted(set(re.findall(r"""\[(data-[\w-]+)""", s)))
    print(f"{f.split('/')[-1]} | páginas: {', '.join(pages) or '-'}\n  ids: {' '.join(ids)}\n  clases: {' '.join(cls)}\n  data: {' '.join(data)}")
```

### 11.B Plantillas de código

**B.1 Router de banda con guard (copia para cualquier recurso nuevo de banda).**

```python
"""<recurso> de banda (T-V6-NN)."""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ..services.band_auth import require_band_admin, require_band_member
from ..services.db import get_db
from ..services.models import BandMembership, <Modelo>, _utcnow
from ..services.schemas import <ModeloCreate>, <ModeloResponse>

router = APIRouter(prefix="/bands/{band_id}/<recurso>", tags=["<recurso>"])

def _deny_guests(m: BandMembership) -> None:
    if m.role == "guest":
        raise HTTPException(status_code=403, detail="Un invitado no puede editar esto")

@router.get("/", response_model=List[<ModeloResponse>])
def list_items(band_id: str, db: Session = Depends(get_db), m: BandMembership = Depends(require_band_member)):
    return db.query(<Modelo>).filter(<Modelo>.band_id == band_id, <Modelo>.deleted_at.is_(None)).order_by(<Modelo>.created_at.desc()).limit(200).all()

@router.post("/", response_model=<ModeloResponse>, status_code=status.HTTP_201_CREATED)
def create_item(band_id: str, payload: <ModeloCreate>, db: Session = Depends(get_db), m: BandMembership = Depends(require_band_member)):
    _deny_guests(m)
    obj = <Modelo>(band_id=band_id, created_by=m.user_id, **payload.model_dump())
    db.add(obj); db.commit(); db.refresh(obj)
    return obj

@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_item(band_id: str, item_id: str, db: Session = Depends(get_db), m: BandMembership = Depends(require_band_admin)):
    obj = db.query(<Modelo>).filter(<Modelo>.id == item_id, <Modelo>.band_id == band_id, <Modelo>.deleted_at.is_(None)).first()
    if obj is None:
        raise HTTPException(status_code=404, detail="No encontrado")
    obj.deleted_at = _utcnow(); db.commit()
```
Después: `app.include_router(...)` en `src/main.py`, y los tests de aislamiento/rol se recogen
solos (T-V6-27) — añade el test funcional del recurso.

**B.2 Modelo + migración.**

```python
class <Modelo>(Base):
    __tablename__ = "<tabla>"
    id = Column(String(36), primary_key=True, default=generate_uuid)
    band_id = Column(String(36), ForeignKey("bands.id", ondelete="CASCADE"), nullable=False, index=True)
    created_by = Column(String(36), nullable=False)
    created_at = Column(DateTime(timezone=True), default=_utcnow, nullable=False)
    deleted_at = Column(DateTime(timezone=True), nullable=True, index=True)
```
`python -m alembic revision --autogenerate -m "t-v6-NN <tabla>"` → revisar → `upgrade head` →
`check` → `downgrade -1` → `upgrade head`.

**B.3 Test unit de recurso.**

```python
import pytest
pytestmark = pytest.mark.unit
STRANGER = "99999999-9999-9999-9999-999999999999"

def test_crud_y_aislamiento(client, acting_as):
    bid = client.post("/bands/", json={"name": "B"}).json()["id"]
    r = client.post(f"/bands/{bid}/<recurso>/", json={...}); assert r.status_code == 201
    iid = r.json()["id"]
    assert len(client.get(f"/bands/{bid}/<recurso>/").json()) == 1
    with acting_as(STRANGER):
        assert client.get(f"/bands/{bid}/<recurso>/").status_code == 404
        assert client.delete(f"/bands/{bid}/<recurso>/{iid}").status_code == 404
    assert client.delete(f"/bands/{bid}/<recurso>/{iid}").status_code == 204
    assert client.get(f"/bands/{bid}/<recurso>/").json() == []
```

**B.4 Test e2e de página.**

```python
import pytest
pytestmark = pytest.mark.e2e

def test_<flujo>(page, live_server, api):
    bid = api.post("/bands/", json={"name": "Banda e2e"}).json()["id"]
    page.goto(f"{live_server}/static/band.html?id={bid}#<tab>")
    page.wait_for_selector("#<panel-id>")
    page.click("#<boton>")
    page.fill("#<input>", "valor")
    with page.expect_response(lambda r: "/<recurso>/" in r.url and r.request.method == "POST") as resp:
        page.click(".bf-dialog .bf-btn--primary")
    assert resp.value.status == 201
    page.wait_for_selector("#<lista> .bf-item")
```

**B.5 Componente de UI (módulo).**

```js
// ui/<nombre>.js — <qué hace>. Sin dependencias; tokens de design-system.css.
import { bfIcon } from './icons.js';
export function bf<Nombre>(el, opts = {}) {
    // 1) pinta DOM con clases bf-*; 2) cablea eventos (teclado incluido); 3) devuelve API { update, destroy }
}
Object.assign(window, { bf<Nombre> });   // compat temporal con scripts clásicos
```

**B.6 Entrada de `REGISTRO_DE_CAMBIOS.md`.**

```markdown
### T-V6-NN — <título> (AAAA-MM-DD)
- **Qué:** <una frase>
- **Por qué:** cierra <IDs de la Parte I §4> / Parte I §<sección>
- **Cómo:** <archivos y decisión técnica en 2–3 líneas>
- **Verificación:** doctor ✅ · unit N ✅ · e2e N ✅ · capturas `harness/capturas/T-V6-NN/`
- **Pendiente/decisiones:** <si queda algo>
```

### 11.C Checklist final antes de cerrar cualquier tarea

- [ ] Hice solo lo que pedía la receta (lo demás, anotado como tarea nueva).
- [ ] Ningún id/clase/`data-*` del Anexo A cambiado sin actualizar su test.
- [ ] Cero emoji nuevos como icono; cero `#hex`/`rgba(` fuera de `:root`; cero `style=""` nuevos.
- [ ] Texto de usuario escapado con `escapeHtml`.
- [ ] Ruta nueva de banda → guard + test ajeno + test guest.
- [ ] Migración revisada, `alembic check` limpio, downgrade probado.
- [ ] `cachebust.py` ejecutado si toqué js/css.
- [ ] `doctor.py` ✅ · `run_checks.py` ✅ · `npm run check` ✅ (si existe).
- [ ] Capturas oscuro/claro × escritorio/390 px en `harness/capturas/T-V6-NN/` (si hay UI).
- [ ] REGISTRO, ROADMAP y TASKS actualizados; commit con el formato de §0.8.
- [ ] Si lleva migración: aplicada en producción antes de mergear.

---

*Fin de la Parte II. Si una receta no cuadra con el código que tienes delante, la Parte I manda
y este manual se corrige: anota la diferencia en `harness/TASKS.md` y en el REGISTRO.*
