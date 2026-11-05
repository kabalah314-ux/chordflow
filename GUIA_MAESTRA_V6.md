# 🎸 BandFlow — Guía Maestra V6 · Parte I: auditoría profunda, visión de producto y plan

> **Fecha:** 2026-11-05 · **Estado:** PROPUESTA — no se ha tocado una sola línea de código.
> **Base analizada:** repo `kabalah314-ux/chordflow`, rama `main`, commit `d61f165` (2026-07-05),
> copia local en `Documents\OOOX\03-Experiments\bandflow`.
>
> **Para qué sirve:** es el plan completo para pasar de "funciona pero se nota amateur" a
> "app profesional que los músicos quieren usar": bugs reales encontrados, diagnóstico visual con
> la app navegada de verdad, sistema de diseño 2.0, funcionalidades que faltan, **visión de
> producto (§9)**, arquitectura, infra y una hoja de ruta por fases con tareas numeradas
> (`T-V6-NN`).
>
> **La guía tiene dos partes:** esta (Parte I: el QUÉ y el POR QUÉ) y
> **`GUIA_MAESTRA_V6_MANUAL.md`** (Parte II: el CÓMO — una receta paso a paso por cada tarea
> `T-V6-NN`, escrita para que una IA menos capaz pueda ejecutarla sin ayuda). Las dos van juntas:
> aquí se decide, allí se ejecuta.
>
> **Relación con la V5:** `GUIA_MAESTRA_V5.md` sigue siendo la **dirección de producto**
> (Explorar, Mi material, Chat 2.0, Bandas 2.0, Conciertos, Finanzas integral). Esta V6 no la
> sustituye: es la **capa de calidad y profesionalización** que hay que poner DEBAJO antes de
> seguir construyendo la V5 encima (si no, cada sección nueva hereda los mismos problemas).
> Cuando Oscar la apruebe, `CLAUDE.md` debe apuntar a las dos: V6 para "cómo tiene que estar
> hecho" y V5 para "qué construir después".

---

## 0. Cómo leer y usar esta guía

### 0.1 Método del análisis (de dónde sale todo lo que hay aquí)

1. **Lectura completa del código** (34.372 líneas: `src/`, `static/`, `tests/`, `harness/`,
   `alembic/`, CI, Vercel y las 8 guías/registros).
2. **Tres revisiones independientes en paralelo** con lentes distintas: backend (seguridad,
   multi-tenant, datos, rendimiento), frontend (JS, CSS, UX, accesibilidad, PWA) e ingeniería
   (tests, CI/CD, despliegue, migraciones, secretos, documentación). Cada hallazgo cita
   `archivo:línea`; los más graves se han verificado a mano una segunda vez.
3. **Navegación real de la app** con datos de ejemplo (banda con 3 miembros, repertorio,
   setlist, agenda, finanzas, chat): **79 capturas** en escritorio (1366 px) y móvil (390 px),
   tema oscuro y claro, incluidas las 9 pestañas del espacio de banda. De ahí sale el
   diagnóstico visual (§5) — no es opinión, son pantallas vistas.
4. **Cruce documentación ↔ código** para detectar lo que las guías dan por hecho y no está.

Lo que NO se ha podido hacer: ejecutar la suite de tests ni el backend (entorno sin
`fastapi`/`sqlalchemy` ni red para instalarlos). Todo lo de tests es análisis estático.

### 0.2 Reglas para la IA ejecutora (no negociables, heredan de `CLAUDE.md`)

1. **Bucle de 7 pasos** de `CLAUDE.md` §2 por tarea: elegir → abrir en `TASKS.md` → implementar →
   `doctor.py` verde → test que la cubre + `run_checks.py` verde → registrar → cerrar. Tras tocar
   `.js`/`.css`: `python harness/cachebust.py`.
2. **Una tarea = un commit desplegable.** Nunca mezclar rediseño visual con cambios de
   comportamiento en el mismo commit.
3. **El motor no se toca** (`static/sync_engine.js`, contrato DOM de `score_render.js`) salvo
   tarea explícita con plan (§7.9 lista las únicas excepciones propuestas).
4. **Los e2e localizan por ids/clases**: al rediseñar una página se conservan los `id` y las
   clases `data-*`/`#b-*` que usan los tests; se cambian estilos y estructura interna, no
   anclas. Antes de renombrar: `grep -rn "<id>" tests/e2e/`.
5. **Multi-tenant**: toda ruta de banda nueva lleva `require_band_member/admin` + test de
   aislamiento. Esta guía además exige **test de rol** (`guest` → 403) en toda ruta de escritura.
6. **Nada de emoji como icono.** Solo `bfIcon()` (SVG). Los emoji solo se permiten en contenido
   escrito por el usuario.
7. **Nada de color fuera de tokens** (`--bf-*`). Un `#hex`/`rgba` nuevo fuera de `:root` es un
   fallo de revisión (se propone un check automático en §8.5).
8. **Decisiones abiertas (D-V6-\*, §11)**: bloquean solo la pieza que listan; el resto avanza.

### 0.3 Leyenda

- Severidad: 🔴 crítico (seguridad, pérdida de datos o función rota) · 🟠 alto · 🟡 medio · 🟢 bajo.
- Esfuerzo: **S** (≤ medio día) · **M** (1–2 días) · **L** (3–5 días) · **XL** (más de una semana).
- Prefijos de hallazgo: `S-` seguridad · `B-` backend · `F-` frontend · `V-` visual/UX · `Q-`
  calidad/infra · `D-` documentación. Tareas: `T-V6-NN`.

---

## 1. Resumen ejecutivo

### 1.1 Veredicto en diez líneas

1. **La base técnica es mejor que su aspecto.** Aislamiento multi-tenant bien resuelto
   (`band_auth.py`), finanzas con `Decimal` e invariante Σ=0, soft-delete coherente, XSS
   escapado con disciplina, 405 tests, CI, migraciones. Es un proyecto serio.
2. **La impresión de "amateur" tiene causas concretas y arreglables**: emojis como iconos
   (157 en html/js), dos sistemas de componentes conviviendo (legacy `style.css` vs `bf-*`),
   controles nativos sin estilo, páginas medio vacías en escritorio, listas sobrecargadas con 7
   controles por fila, formato de dinero "−160.00 €", avatar del mismo usuario de distinto
   color según la página, y un login con botones píldora y un emoji de logo.
3. **Hay 5 bugs críticos reales**: credenciales en un repo público, service worker que cachea
   datos personales (`/collections`), modales/toasts ilegibles en tema claro, chat de banda que
   salta al principio cada 6 segundos, y `pytest` capaz de borrar producción si la shell tiene
   `DATABASE_URL` de prod.
4. **El móvil está roto en las pantallas que más se usan sobre el escenario/ensayo**: la agenda
   de banda es ilegible, la letra del reproductor se corta por la derecha, el chat tiene un botón
   Enviar gigante y no se puede editar/borrar desde la Biblioteca (acciones solo-hover).
5. **Faltan piezas que cualquier SaaS da por hechas**: recuperar contraseña, caducar/revocar
   invitaciones, salir de una banda, gestionar miembros desde la UI (los endpoints existen y no
   tienen pantalla), notificaciones por email, exportar/imprimir un setlist, calendario.
6. **Infra**: todo el tráfico (hasta cada PNG) pasa por la función Python; no hay staging, ni
   backups, ni Sentry, ni gate de CI antes del auto-deploy, ni lockfile.
7. **Documentación**: 713 KB en 8 guías + registro de 3.645 líneas; sin README; varias
   contradicciones entre lo que dicen y lo que hay (§13.D).
8. **Recomendación**: parar la V5 F4+ unas semanas, ejecutar V6-F0→F5 (seguridad, bugs, base
   técnica, sistema de diseño, páginas, móvil), después F9 (producto: invitación pública,
   votación de fechas, vista por miembro, PDF/grabadora, modo ensayo, hoja del bolo — §9) y
   retomar la V5 sobre esa base. Es menos trabajo total que seguir y rehacer después.
9. Esfuerzo total estimado de V6-F0→F9: **≈ 19 semanas-persona** (11–12 semanas de calendario
   con una IA en front y otra en back en paralelo) con Oscar decidiendo; las fases están
   ordenadas para que cada una deje la app mejor y desplegable.
10. Nada de esto requiere cambiar de stack: FastAPI + vanilla JS siguen valiendo. Sí requiere
    disciplina (tokens, componentes, tests por ruta) y tres herramientas nuevas (lint JS,
    Sentry, lockfile).

### 1.2 Nota por área (1–10) y objetivo

| Área | Hoy | Por qué | Objetivo V6 |
|---|---|---|---|
| Seguridad | **4** | Secretos en repo público; SSRF en importar; sin rate limit; modo test sin cerrojo; invitaciones eternas | 8 |
| Backend (código) | **7** | Aislamiento sólido, Decimal, soft-delete; pero lógica en routers, N+1, sin paginación, fechas ambiguas | 8,5 |
| Datos / migraciones | **6** | 20 migraciones lineales; pero `create_all` en arranque, migración 3/20 no válida en Postgres, sin backups | 8 |
| Frontend (código) | **5** | Sin módulos, 240 globales, helpers ×4, `bands.js` de 1.250 líneas, SW con bug, sin lint | 8 |
| Diseño visual | **5** | Tokens buenos; ejecución mezclada: emoji, legacy, 40 tamaños de fuente, tema claro a medias | 9 |
| UX / flujos | **5** | Flujos completos pero densos; móvil roto en agenda/player/chat; sin onboarding ni recuperar contraseña | 8,5 |
| Accesibilidad | **4** | Tarjetas sin teclado, modales sin focus trap, pestañas sin aria, labels con placeholder | 7,5 |
| Tests | **7** | 405 tests, gate de aislamiento; pero 11 rutas sin test, 30 % tests de estilo, e2e no herméticos | 8,5 |
| CI/CD e infra | **4** | CI existe pero no es gate; sin staging/backups/observabilidad; estáticos por lambda | 8 |
| Documentación | **6** | Exhaustiva pero pesada, con contradicciones y sin README | 8 |

### 1.3 Los 12 problemas que más pesan (orden de impacto)

1. 🔴 Contraseña de Postgres y credenciales de la cuenta de producción en el repo **público** (§2).
2. 🔴 El service worker cachea `/collections` → datos rancios y, en dispositivo compartido, del usuario anterior (F-01).
3. 🔴 Modales y toasts ilegibles en tema claro: afecta a confirmar borrados, crear evento, movimiento, etc. (F-02).
4. 🔴 Chat de banda: la lista se reemplaza entera cada 6 s y el scroll salta al principio; con >8 mensajes lo nuevo queda oculto (F-03).
5. 🔴 Móvil: agenda de banda ilegible y letra del reproductor cortada (V-01, V-02).
6. 🟠 Importar por URL = SSRF + lectura sin tope + sin límite de uso del LLM (S-04, S-05).
7. 🟠 Un `guest` puede crear canciones en la banda y publicar al catálogo público vía `/catalog` (B-01).
8. 🟠 Biblioteca personal truncada a 100 canciones sin orden estable (B-06).
9. 🟠 Invitaciones sin caducidad ni revocación; un enlace filtrado vale para siempre (S-07).
10. 🟠 Sin recuperar contraseña, sin salir de banda, sin gestión de miembros en UI (§7).
11. 🟠 Dos sistemas visuales + 157 emojis + 40 tamaños de fuente = sensación amateur (§5, §6).
12. 🟠 Auto-deploy a producción sin que CI sea gate; sin staging ni backups (Q-05…Q-08).

### 1.4 Lo que está bien y hay que conservar

- `band_auth.py` (404 antes que 403, baja blanda, soft-delete) usado en las 57 rutas de banda.
- `balances.py`: Decimal cuantizado, último absorbe céntimos, Σ=0, tests sólidos.
- Proyección segura en `/public` con test que busca campos sensibles en el JSON crudo.
- Handler global 500 sin filtrar internos; cabeceras básicas; CORS explícito; `/config` sin `service_role`.
- Caché de token con lock y cota; SRI en el SDK de Supabase; validación anti-XSS de URLs de imagen.
- `escapeHtml` aplicado con disciplina en todo el front; `bfIcon/bfEmpty/bfAvatar/bfSkeletonList`.
- Tokens de `design-system.css` (oscuro/claro, hover/focus/disabled); drawer móvil; `prefers-reduced-motion`; targets de 44 px con `pointer:coarse`.
- Cache-busting por hash con test; estrategia general del SW (API fuera, HTML network-first).
- `metronome.js` compartido (patrón a imitar); `upload.js` con resize en cliente y alfa preservado.
- 168 e2e que localizan por ids; IA mockeada en tests de importación.

---

## 2. 🚨 Acciones inmediatas de Oscar (antes de cualquier tarea de código)

> Estas no las puede hacer la IA: son tus cuentas. Son 20 minutos y cierran el riesgo más grave
> de toda la auditoría.

### 2.1 Credenciales en el repo público (S-01, S-02) — HOY

GitHub muestra `kabalah314-ux/chordflow` como **público** (aunque `CLAUDE.md` §5.bis diga
"privado"). Dentro, en texto claro y también en el historial de git:

| Dónde | Qué |
|---|---|
| `REGISTRO_DE_CAMBIOS.md:1344` y `harness/TASKS.md:35` | contraseña de Postgres (Supabase) |
| `harness/TASKS.md:16` | email + contraseña de la cuenta de producción de BandFlow |
| `PENDIENTES_OSCAR.md`, `ROADMAP.md`, `REGISTRO` (varias líneas) | emails personales y referencia del proyecto Supabase (riesgo bajo, pero sobra) |

Pasos, en este orden:

1. **Supabase → Settings → Database → Reset database password.** Copiar la nueva en Vercel →
   Settings → Environment Variables → `DATABASE_URL` → Redeploy. (La app no se cae: el runtime
   lee la env de Vercel.)
2. **Cambiar la contraseña** de la cuenta `oscarc…@gmail.com` en BandFlow (y en Google si era la
   misma). Si tiene sesiones abiertas, Supabase → Authentication → Users → cerrar sesiones.
3. **GitHub → repo → Settings → Danger zone → Change visibility → Private.**
4. **Revocar el PAT `sbp_`** de Supabase (sigue marcado pendiente en `PENDIENTES_OSCAR.md` desde
   junio): supabase.com/dashboard/account/tokens.
5. (Después, tarea `T-V6-01` de la IA) borrar esas líneas de los tres ficheros, purgar el
   historial con `git filter-repo` y activar `gitleaks` en CI para que no vuelva a pasar.

### 2.2 Otras acciones tuyas (no urgentes, pero solo tú puedes)

- Vercel: confirmar el plan (Hobby/Pro) para fijar `maxDuration` del importador (§8.4).
- Supabase: decidir si creas un **segundo proyecto "staging"** gratuito (§8.4, D-V6-6).
- Sentry: crear cuenta gratuita y pasar el DSN cuando llegue `T-V6-29`.
- Dominio propio (`bandflow.es`/`.app`): no es técnico, pero una URL `chordflow-ecru.vercel.app`
  resta profesionalidad; la guía asume que llegará (D-V6-8).

---

## 3. Inventario real de la app (para ubicarse en 5 minutos)

### 3.1 Qué es hoy BandFlow (en una frase por pieza)

SaaS para bandas: **identidad de banda** (miembros con rol admin/member/guest, invitaciones por
código), **repertorio** compartido y personal (canciones con letra+acordes, colecciones),
**setlists** (de banda y personales), **agenda** (ensayos/conciertos con asistencia, salas, pipeline
de booking, compartir evento público), **finanzas** (gastos/ingresos con reparto, fondo común,
liquidaciones, saldos), **chat** de banda (con hilos por evento y mensajes fijados), **giras**
(paradas + presupuesto), **catálogo público** de partituras (publicar/importar/valorar/comentar),
**importar** desde CifraClub/LaCuerda/URL/foto con IA, y la "joya": **reproductor-teleprompter**
con metrónomo, cuenta atrás, transposición, diagramas y afinador.

### 3.2 Páginas (16 HTML en `static/`)

| Página | Para qué | Shell | Estilos | Tema claro | Veredicto visual |
|---|---|---|---|---|---|
| `login.html` | Entrar / crear cuenta / Google | no | legacy | siempre oscuro | Rehacer |
| `app.html` (Inicio) | Dashboard TÚ: próximo evento, saldo, mensajes | sí | bf | ok | Mejorar |
| `bands.html` | Mis bandas | sí | mixto | parcial | Mejorar |
| `band.html` | Espacio de banda: 9 pestañas | sí | **mixto** (shell bf, contenido legacy) | **roto** en listas/modales | Rehacer contenido |
| `library.html` | Biblioteca (partituras + repertorios de bandas) | sí | mixto | chips invisibles | Mejorar |
| `setlists.html` | Setlists personales | sí | mixto | parcial | Mejorar |
| `editor.html` | Crear/editar partitura + importar | no | legacy convergido | ok | Reorganizar |
| `index.html` | Reproductor (modo escenario) | no | legacy | n/a (siempre oscuro) | Pulir + móvil |
| `agenda.html` | Agenda agregada TÚ | sí | bf | ok | Rehacer (calendario) |
| `finanzas.html` | Saldos TÚ | sí | bf | ok | Rehacer (casi vacía) |
| `chat.html` | Conversaciones TÚ | sí | bf | ok | Rehacer (2 columnas) |
| `profile.html` | Perfil | sí | mixto | parcial | Rehacer |
| `afinador.html` | Afinador / Metrónomo | sí | mixto | ok | Pulir |
| `biblioteca-global.html` | Explorar (catálogo) | sí | mixto | parcial | Rehacer (V5 §5) |
| `evento.html` | Evento público compartido | no | legacy | siempre oscuro | Pulir |
| `join.html` | Aceptar invitación | no | legacy | ok | Rehacer (bug de layout) |

### 3.3 API (18 routers, 96 endpoints)

| Router | Prefijo | Nº | Qué hace |
|---|---|---|---|
| `songs_router` | `/songs` | 6 | CRUD de canción personal (o de banda por `band_id`) |
| `import_router` | `/import` | 3 | URL / foto / buscar por nombre → texto para el editor (IA) |
| `setlists_router` | `/setlists` | 5 | setlists personales |
| `collections_router` | `/collections` | 5 | colecciones personales |
| `bands_router` | `/bands` | 12 | banda, resumen, miembros (rol/baja/reactivar), invitaciones |
| `invites_router` | `/invites` | 2 | previsualizar (sin auth) + aceptar |
| `profile_router` | `/profile` | 2 | perfil propio |
| `band_songs_router` | `/bands/{id}/songs` | 4 | repertorio de banda, copiar desde personal |
| `band_setlists_router` | `/bands/{id}/setlists` | 5 | setlists de banda |
| `band_collections_router` | `/bands/{id}/collections` | 5 | colecciones de banda |
| `events_router` | `/bands/{id}/events` | 6 | agenda + asistencia |
| `venues_router` | `/bands/{id}/venues` | 5 | salas |
| `finance_router` | `/bands/{id}` | 8 | movimientos, saldos, liquidaciones |
| `messages_router` | `/bands/{id}/messages` | 5 | chat, hilos por evento, fijar |
| `me_router` | `/me` | 4 | dashboard/events/balances/conversations agregados |
| `tours_router` | `/bands/{id}/tours` | 9 | giras, paradas, presupuesto |
| `catalog_router` | `/catalog` | 6 | publicar/buscar/importar/valorar/comentar |
| `public_router` | `/public` | 1 | evento compartido sin auth |

Raíz: `/` (redirige a `app.html`), `/health`, `/config`.

### 3.4 Datos (26 tablas)

`songs · sections · lines · chord_markers · tab_lines · setlists · setlist_items · song_collections ·
song_collection_items · musician_profiles · bands · band_memberships · band_invites · events ·
event_attendance · venues · transactions · transaction_splits · settlements · messages · tours ·
tour_stops · tour_budget_lines · musical_works · public_scores · score_ratings · score_comments`.
Soft-delete (`deleted_at`) en casi todo; CHECK constraints para enums; FKs con CASCADE/SET NULL;
`DateTime` **naive** (UTC por convención — ver B-10). 20 migraciones Alembic lineales.

### 3.5 Auth y multi-tenant (cómo funciona hoy)

- Front: Supabase JS (CDN) gestiona la sesión; `apiFetch` añade `Authorization: Bearer`.
- Back: `get_current_user` valida el token **llamando a Supabase** (`GET /auth/v1/user`) con caché
  en memoria (TTL 60 s + gracia 300 s). No se verifica el JWT localmente.
- Banda: `require_band_member` (404 al ajeno) / `require_band_admin` (403 al no-admin); el rol
  `guest` se deniega a mano con `_deny_guests` en cada router (y se olvidó en `/catalog`, B-01).
- Modo test (`CHORDFLOW_TEST_MODE=1`): todo el mundo es el usuario nil. Sin cerrojo que impida
  activarlo en producción (S-03).

### 3.6 Endpoints sin pantalla y pantallas sin endpoint

**Existen en la API y el front NO los usa** (funcionalidad "gratis" a la que solo falta UI):
`PATCH /bands/{id}/members/{uid}` (cambiar rol) · `DELETE …/members/{uid}` (baja) ·
`POST …/members/{uid}/reactivate` · `GET /bands/{id}/invites` (listar invitaciones) ·
`GET …/settlements` y `DELETE …/settlements/{sid}` (las liquidaciones se crean pero no se ven ni
se borran) · `PATCH/DELETE …/tours/{tid}` (editar/borrar gira) · `PATCH …/messages/{mid}` (editar
mensaje) · `GET …/venues/{vid}` · `GET …/transactions/{tid}` · `skip/limit` de `GET /songs/`.

**El front llama y no existe:** nada. Solo variantes sin barra final (`/bands/{id}/events`,
`/tours`, `/messages`) que resuelven con un 307 extra por petición (B-25).

---

## 4. Catálogo de bugs y defectos encontrados

> Cada entrada: **dónde** (archivo:línea) · **qué pasa** · **arreglo**. Los IDs se usan en la hoja
> de ruta (§10). Están verificados en el código; los marcados ✔️ además se han visto reproducidos
> en la navegación con datos demo.

### 4.1 🔴 Críticos

| ID | Dónde | Qué pasa | Arreglo |
|---|---|---|---|
| **S-01** | `REGISTRO_DE_CAMBIOS.md:1344`, `harness/TASKS.md:35` (+ historial git) | Contraseña de Postgres en claro en un repo **público** | §2.1; borrar líneas; `git filter-repo`; `gitleaks` en CI y pre-commit |
| **S-02** | `harness/TASKS.md:16` | Email + contraseña de la cuenta de producción | §2.1 |
| **F-01** ✔️ | `static/sw.js:26` | El regex de "no cachear" (`songs\|setlists\|bands\|…\|public`) omite `collections` → `GET /collections/` y `/collections/{id}` (`library.js:24,101,119,180,323`) caen en cache-first (`sw.js:39-45`): tras crear/editar una colección la lista vuelve rancia; en un dispositivo compartido el siguiente usuario ve las del anterior. Ya pasó con `/catalog`, `/tours` y `/me` (REGISTRO:2180) | Invertir la política: cache-first **solo** para `/static/**` con `?v=`; todo lo demás red. `caches.delete()` al cerrar sesión. Test e2e: crear colección → recargar → aparece |
| **F-02** ✔️ | `static/style.css:1361-1366` (toast), `:1395-1404` (modal) | Fondo `rgba(30,30,40,.75/.85)` fijo + texto `var(--text-primary)` que en tema claro es `#1a1a20` → **texto oscuro sobre cristal oscuro** en confirmar borrado, crear evento, movimiento, invitar, etc. | `background: var(--bf-surface)`, borde y sombra por tokens; un único `bfDialog()` (§6.3) |
| **F-03** ✔️ | `static/bands.js:106-109, 117`; `src/api/messages_router.py:59`; `style.css:1571` | Chat de banda: cada 6 s se reemplaza el `<ul>` entero → el scroll vuelve arriba; mensajes en orden ascendente dentro de `max-height:320px` → lo nuevo queda oculto abajo; sigue sondeando en segundo plano | Render diferencial por id, auto-scroll al final (si el usuario estaba abajo), `visibilitychange` para pausar, parar al cambiar de pestaña; paginar por cursor (B-13) |
| **F-04** | `static/style.css:1353` (toasts `z-index:9999`) vs `:1385` (overlay `10000`) | Los errores de validación que dejan el modal abierto (`bands.js:393,453,719,819`, `library.js:148`) salen **debajo** del modal | Toasts a `10010` o mensaje inline dentro del modal (mejor) |
| **Q-01** | `tests/conftest.py:28` (`os.environ.setdefault("DATABASE_URL", …)`), `:49` (`drop_all`), `test_band_auth.py:393`, `seed_demo.py:21` | Si la shell tiene exportada la `DATABASE_URL` del pooler (como piden `CLAUDE.md` §3 y V5 §0.1.6 para migrar), `pytest` hace `drop_all` **sobre producción** | `os.environ["DATABASE_URL"] = …` forzado + `assert engine.url.drivername.startswith("sqlite")` en conftest; SQLite en memoria con `StaticPool` |
| **V-01** ✔️ | `static/bands.js:543-561` + `style.css:809` (sin regla responsive para `.att-buttons`) | **Móvil**: fila de evento en la agenda de banda con 7 controles a la derecha → el texto queda en una columna de ~60 px, palabra por línea, botones solapando la fecha. Ilegible | Nuevo componente fila (§6.3 `bf-row`): en < 768 px las acciones pasan debajo; asistencia como segmented control; estado y menú ⋯ |
| **V-02** ✔️ | `static/index.html` / `style.css:746-760` | **Móvil**: la letra del reproductor se corta por la derecha (sin wrap ni escalado) y el control de tono queda fuera de la topbar | `overflow-wrap`, tamaño de fuente fluido (`clamp`), toolbar compacta en 2 filas máximo; test de overflow horizontal en el player en 390 px |

### 4.2 🟠 Altos

**Seguridad**

| ID | Dónde | Qué pasa | Arreglo |
|---|---|---|---|
| **S-03** | `src/services/auth.py:63-64`, `config.py:39` | `CHORDFLOW_TEST_MODE=1` por error en Vercel = toda la app abierta como un único usuario | En `Settings`: `ValueError` si `chordflow_test_mode` y (`VERCEL` en env o `DATABASE_URL` no es sqlite). Test |
| **S-04** | `src/api/import_router.py:20` (`HttpUrl` cualquiera), `importer.py:110-124` (`urlopen` directo, `resp.read()` sin tope, sigue redirecciones) | **SSRF**: el servidor descarga cualquier URL (incluidas internas/privadas) y devuelve el contenido al usuario/LLM; una respuesta enorme agota memoria antes del recorte a 16k | Allowlist de dominios (cifraclub, lacuerda, e-chords, ug…), resolver DNS y rechazar rangos privados, `Content-Length` máximo + lectura acotada, no seguir redirects a otro host |
| **S-05** | `import_router.py:42-84` | `/import/*` consume OpenRouter/Jina (coste y cuota) sin límite por usuario; `GET /invites/{code}` y `/public/events/{id}` sin auth ni límite | Rate limiting (`slowapi`) por `user_id`/IP; cuota diaria de importaciones con IA por usuario |
| **S-06** | `src/services/schemas.py:116` + `static/editor.js:414` | `reference_url` sin validar protocolo y pintada como `href`: un miembro guarda `javascript:…youtube.com/...`, otro clica la carátula → XSS almacenado (requiere clic) | Exigir `^https?://` en servidor (`AnyHttpUrl`) y en cliente |
| **S-07** | `static/bands.js:1235-1238`, `schemas.py:366-369`, `bands_router.py:375-414` | Invitaciones sin caducidad ni límite de usos por defecto y **sin forma de revocarlas**; un enlace filtrado por WhatsApp (incluso con `role_to_grant=admin`) vale para siempre | Default servidor 7 días / 20 usos; `DELETE /bands/{id}/invites/{iid}` (+ `revoked_at`); UI de lista y revocación (§7.3) |
| **S-08** | `src/main.py:77-86` | Sin CSP ni HSTS propio (CSP "pendiente" desde T-029) | CSP con nonce para inline (retirar `onclick` inline de `bands.js:1245`); HSTS cuando haya dominio propio |
| **S-09** | `src/services/auth.py:26-31, 86-88` | Revocación de sesión retrasada: un token aceptado 60 s tras logout/cambio de contraseña y hasta 300 s más si Supabase falla; no distingue "rechazado" de "caído" | Verificar JWT **localmente** con JWKS (`exp`, `aud=authenticated`); gracia solo ante error de red; adiós a la llamada remota por request |

**Backend**

| ID | Dónde | Qué pasa | Arreglo |
|---|---|---|---|
| **B-01** | `src/api/catalog_router.py:150-159` (`publish`), `:268-279` (`import_score`) | Solo comprueban `status == "active"`, sin rol: un `guest` crea canciones en el repertorio (salta `_deny_guests`) y **publica arreglos privados de la banda en el catálogo público** | Reutilizar `require_band_member` + `_deny_guests` (o exigir admin para publicar); tests `guest → 403` |
| **B-02** | `models.py:507-509` (`splits` lazy), `balances.py:64`, `finance_router.py:195-199`, `bands_router.py:211-215`, `me_router.py:203-207` | **N+1** en saldos: 100 movimientos × 3 bandas ≈ 300 queries por carga del Inicio, a través de pgbouncer | `.options(selectinload(Transaction.splits))` en las tres consultas |
| **B-06** | `songs_router.py:90, 98-101` + `library.js:22`, `bands.js:1197`, `setlists.js:95` | `/songs/` corta en 100 **sin `ORDER BY`** y el front no pagina → con >100 canciones desaparecen al azar (Postgres no garantiza orden) | `order_by(updated_at.desc())`; paginar en el front o devolver `total`; subir el default |
| **B-12** | `src/main.py:40-43`, `db.py:24` | `create_all` en cada cold start contra Postgres (reflexión de 26 tablas; puede crear tablas fuera de Alembic → drift silencioso); `QueuePool` por instancia serverless hacia el pooler | `create_all` solo si la URL es sqlite; `poolclass=NullPool` (o `pool_size=1, max_overflow=0`) cuando `VERCEL` |
| **B-20** | `importer.py:62,106,113,123,259`; `vercel.json` sin `maxDuration` | Timeouts encadenados (30+25+45–60 s) por encima del tiempo máximo de la función → importaciones que mueren a medias | Presupuesto total ≤ 25 s (o el `maxDuration` del plan), timeouts cortos, respuesta clara al agotar |

**Frontend / UX**

| ID | Dónde | Qué pasa | Arreglo |
|---|---|---|---|
| **F-05** | `auth.js:14,31`, `shell.js:136`, `home.js:80` | Si falla `/config` o el CDN de jsDelivr (punto único de fallo), promesa rechazada en silencio → "Cargando…" infinito | Self-host del SDK de Supabase (como `icons.js`); `try/catch` en `mount()` con estado de error + reintentar |
| **F-06** | `static/editor.html:27`, `editor.js` | Editor sin guardia de cambios: el ❌ o un F5 descartan todo lo pegado/importado sin avisar | Flag `dirty` + `beforeunload` + confirmación en el enlace de cerrar |
| **F-07** | `library.js:22-24,30-31` | Un 500 en `/songs/` se convierte en `[]` → el usuario ve "Aún no tienes partituras" (onboarding) en vez de un error | `apiJson()` que lance; estado de error con botón reintentar (§6.3 EmptyState/ErrorState) |
| **F-08** ✔️ | `style.css:1211-1223` (`.card-actions{opacity:0}`), `library.js:256-259` | **Móvil**: acciones solo-hover → no se puede editar/borrar desde la Biblioteca; tocar navega | Acciones visibles con `@media (hover:none)` o menú ⋯ en la tarjeta |
| **F-09** ✔️ | `style.css:810-816` (`.setlist-item-btn`), `:1165-1182` (`.lib-filter`), `:1512-1526` (`.ev-more-menu`), `:1564-1565` (`.bal-pos/.bal-neg`) | Tema claro roto en el espacio de banda: botones fantasma blancos, chips invisibles, popover oscuro fijo, saldos verde/rojo pastel a ≈1.6:1 sobre blanco | Migrar a `.bf-btn--sm/--icon`, `.bf-amount--*`, tokens; prohibir `rgba(255,255,255,…)` fuera de `:root` |
| **F-10** | `style.css:1146` (`.search-box{margin-bottom:2rem}`) usado como input genérico en `bands.js:332-350,439-442,674-699,805-808`, `profile.js:64,66`, `setlists.js:114`; `.field-label` no existe en ningún CSS | Modales el doble de altos de lo necesario (de ahí el `max-height:90vh`), labels sin estilo | `.bf-field/.bf-label/.bf-input/.bf-select/.bf-textarea` (§6.3) |
| **F-11** | `static/metronome.js:86` | Metrónomo con `setTimeout`: deriva acumulada y throttling a 1 s en pestaña de fondo | Scheduler *lookahead* sobre `audioCtx.currentTime` (patrón estándar; estaba diferido en V3-F4) |
| **F-12** | `metronome.js:118-120`, `app.js:274-280` | Con el foco en +/− (tras clicar), la barra espaciadora suma 1 BPM **y** alterna play | Excluir `button` del atajo o `stopPropagation` |
| **F-13** | `band.js:252-263`; `home.js:55-59`, `agenda.js:39`, `chat.js:23` | Pestañas del espacio de banda no direccionables: "Últimos mensajes" aterriza en Resumen; F5 pierde la pestaña | `#chat`/`#agenda` en la URL + `hashchange`; enlaces con hash |
| **F-14** | `shell.css:39,52,221` | `100vh + overflow:hidden`: en iOS Safari la barra inferior tapa el final del contenido | `100dvh` / `min-height` |
| **F-15** | `editor.js:479,512,547,600,617`; `library.js:285`, `app.js:546` | "[object Object]" al usuario (un 422 trae `detail` como array); mensajes técnicos ("Ocurrió un error: Error al guardar…") | `apiJson()` central que normalice `ApiError{status, message}` con textos en castellano |
| **F-16** | `bands.js:45-60`, `library.js:230-259`, `setlists.js:33-40`, `catalogo.js:24,45,143-145`, `band.js:390` | Navegación principal **sin teclado**: tarjetas y filas `div/li` clicables sin `tabindex/role/Enter`; `.song-card:focus-visible` es regla muerta | `<a>`/`<button>` reales dentro de la tarjeta |
| **F-17** | `bands.js:168-213,327-428,433-471,669-748,800-842,1203-1230`, `library.js:125-164` | 7 modales sin focus trap, sin Escape, sin devolver el foco | Un único `bfDialog()` (§6.3) |
| **F-18** | `editor.js:604-614` | Toda canción **nueva se publica en el catálogo público sin aviso** (decisión D9) — el usuario no lo sabe; letras con copyright | Checkbox "Compartir en Explorar" (default según D-V6-3) + aviso de derechos |
| **F-19** | `app.js:256-257`, `setlists.js:239` | Cambiar de canción dentro de un setlist = **recarga completa** (SDK + `/config` + sesión + fetch) entre temas en el escenario | Cargar la siguiente in-page (`fetch` + `renderScoreInto` + `engine.loadSong`) con prefetch de la siguiente |
| **F-20** ✔️ | `shell.js:29` (tema al final del body); `theme.js` solo en `editor.html:16`, `join.html:13` | Flash oscuro→claro en todas las páginas del shell | `theme.js` inline en el `<head>` de las 16 páginas |
| **V-03** ✔️ | `static/join.html` / `style.css` | **Escritorio**: el botón "Unirme a la banda" aparece descolocado a la izquierda, fuera del bloque centrado (primera impresión de un invitado) | Rehacer `join.html` con `bf-card` centrada (§5.3) |
| **V-04** ✔️ | `band.js:192` + estilos legacy del composer | Botón "Enviar" del chat de banda de ≈90–115 px de alto en escritorio y móvil | Composer con `bf-input` + `bf-btn` de 40 px, Enter envía, Shift+Enter salto |

**Calidad / infra**

| ID | Dónde | Qué pasa | Arreglo |
|---|---|---|---|
| **Q-02** | `alembic/versions/20260614_0226_147a6a78da86…py:39,43` (`server_default=sa.text('0')` en booleanos) | La cadena de migraciones **no es reproducible en Postgres** (rechaza int en boolean); prod se creó con `create_all`+`stamp`. Un staging desde cero falla en la migración 3/20 | Corregir la migración (`sa.false()`); job de CI con Postgres: `upgrade head` + `check` + `downgrade base` |
| **Q-03** | `.github/workflows/ci.yml`; `CLAUDE.md:162` | Auto-deploy a producción en cada push a `main` **sin que CI sea gate** (el commit `7c8863d wip… (SIN VERIFICAR)` llegó a prod) | Branch protection + required status check; o deploy desde workflow tras verde |
| **Q-04** | — | **Sin backups** (Supabase free no los hace) ni runbook de rollback; `downgrade()` jamás probado en Postgres | `pg_dump` diario por GitHub Action a Storage/artefacto; prueba de restauración trimestral; runbook |
| **Q-05** | `vercel.json:3-12`, `main.py:91-92` | **Todo el tráfico estático pasa por la lambda** (cada CSS/JS/PNG = invocación con cold start, sin `Cache-Control`) | `/static/(.*)` a hosting estático de Vercel con `Cache-Control: immutable` para `?v=`; la función solo para la API |
| **Q-06** | `logging_config.py:33-37`, `main.py:57-63` | **Observabilidad nula**: `logs/app.log` imposible en FS read-only (cae a stdout sin formato), sin request-id, sin Sentry, sin uptime check | Sentry (free) + middleware `X-Request-ID` + logs JSON a stdout + UptimeRobot a `/health` |
| **Q-07** | `requirements.txt` (9 pins; transitivas flotan), `requirements-dev.txt` (`>=`), sin `runtime.txt` | Sin lockfile ni auditoría; `ruff` nuevo puede romper CI solo; Vercel elige su Python por defecto (CI usa 3.12) | `uv lock`/`pip-compile --generate-hashes`, `pip-audit` en CI, Dependabot, `runtime.txt` |
| **Q-08** | — | **Sin entornos**: solo prod; previews de Vercel sin `DATABASE_URL` → rotas; e2e contra SQLite | Supabase staging (o branching) + env de preview + smoke post-deploy |

### 4.3 🟡 Medios

**Backend**

- **B-07** `finance_router.py:95-96,112-114,226-227` vs `balances.py:56`: las liquidaciones solo aceptan miembros activos, pero los saldos incluyen a ex-miembros → una baja con saldo ≠ 0 deja la banda **sin poder cuadrar nunca**. Aceptar en liquidaciones a cualquier `user_id` con membresía (activa o `left`).
- **B-08** `band_songs_router.py:61-66`: copiar una canción a la banda **pierde `reference_url`** (`_SONG_SCALAR_FIELDS` no la incluye). Añadir + test de round-trip.
- **B-09** `catalog_router.py:221-224`: la búsqueda del catálogo filtra `lower(title)` con el término sin acentos → "Canción" no se encuentra con "cancion"; `MusicalWork.norm_title/norm_artist` (indexadas) sin uso. Buscar por `norm_*`.
- **B-10** Fechas: el front envía `datetime-local` sin zona (`bands.js:723`), el back compara con `now` naive UTC (`bands_router.py:157,167`, `me_router.py:73,81`) y devuelve sin `Z`, que el front parsea como local (`bands.js:512`). `_to_naive_utc` solo se aplica a eventos; `TransactionCreate.date`, `SettlementCreate.date`, `TourBase.start/end_date`, `BandInviteCreate.expires_at` pierden el offset. **Contrato UTC**: `DateTime(timezone=True)` (o serializar con `Z`), validador común, front con `toISOString()`, test cruzando zonas.
- **B-11** Longitudes: `models.py` `String(4)` para `key_root`, `String(16)` `chord_name`, 32 para `key_mode/tuning/instrument`, 64 `Section.name`, 7 `color_tag`… y `schemas.py` sin `max_length` espejo → SQLite trunca en silencio, **Postgres lanza 500**. Constantes compartidas + test en PG.
- **B-13** `messages_router.py:55-60`: historial completo sin `limit`/cursor cada 6 s. `?after=<id>&limit=50`.
- **B-14** Agregados sin límite: `/me/events` carga todos los eventos+asistencias de todas las bandas; `/transactions`, `/settlements`, `/bands/{id}/songs/` sin paginación. Rango por defecto (±90 días) y `limit/offset` con orden estable.
- **B-15** N+1 por relaciones lazy en listados: `setlists_router.py:95`, `band_setlists_router.py:87`, `collections_router.py:96`, `band_collections_router.py:100`, `tours_router.py:109-110`; `_to_response` hace `it.song` por ítem. Subquery `count()` agrupada + `selectinload`.
- **B-16** Contadores no atómicos: `invites_router.py:110` (`used_count += 1`: dos aceptaciones simultáneas superan `max_uses`), `catalog_router.py:288`, `bands_router.py:324-329` (dos admins degradándose a la vez dejan la banda sin admin). `UPDATE … WHERE used_count < max_uses` + `rowcount`; `SELECT … FOR UPDATE`.
- **B-19** `config.py:16-17`: `load_dotenv()` + `load_dotenv(".env.local")` sin `override` → en `os.environ` gana `.env`, en `Settings` gana `.env.local`; `alembic/env.py:32` lee `os.getenv` → **las migraciones pueden ir a otra BD que la app**. `override=True` o que `env.py` importe `settings`.
- **B-21** `schemas.py:308`, `bands_router.py:240-242`: `plan` (free/pro) editable por cualquier admin. Excluir del PATCH hasta que exista facturación.
- **B-22** `songs_router.py:30-40`, `setlists_router.py:24-34`, `catalog_router.py:154-158`: comprueban membresía sin `Band.deleted_at` → canciones/setlists de una banda borrada siguen abiertos por URL. Helper único `active_membership()` con join a `Band`.
- **B-23** `db.py:43-45`: registra como ERROR con traza cada `HTTPException` (FastAPI propaga al `yield`). `except HTTPException: raise`.

**Frontend**

- **F-21** `sw.js:7,39-45`: la caché `chordflow-shell-v2` nunca purga assets `?v=` antiguos (crece con cada deploy); `cache.put` sin await/catch.
- **F-22** PWA: sin datos offline (toda página acaba en "No se pudo cargar"); `manifest.json:4` describe el producto viejo; **icono verde menta vs marca coral**; `apple-mobile-web-app-capable` obsoleto; `theme-color` fijo. Para una app de escenario: cachear última canción/setlist en IndexedDB (§7.9).
- **F-23** Helpers duplicados: `fmtDate` ×4, dinero ×4, `EV_ICON` ×3, etiquetas de asistencia ×4, `ROLE_LABEL` ×3 con textos distintos ("administrador/a" vs "Admin"), `youtubeId` vs `bfYoutubeId`, `esc` vs `escapeHtml`. Un `format.js` y un `labels.js`.
- **F-24** Dinero con `toFixed(2)+' €'` y 0 usos de `Intl` → "-160.00 €". `Intl.NumberFormat('es-ES',{style:'currency',currency:band.currency})` → "−160,00 €".
- **F-25** ~240 globales de script clásico (`app.js` 66, `bands.js` 43, `editor.js` 27…); `elGrid` y `ROLE_LABEL` declarados en 3 archivos → cualquier co-carga futura es `SyntaxError`. Módulos ES (§8.2).
- **F-26** `localStorage` sin try/catch en `shell.js:13,25`, `app.js:375,400`, `band.js:85,96`, `metronome.js:141-179`, `tuner.js:89,95`: con almacenamiento bloqueado el lateral no se monta.
- **F-27** `catalogo.js:31-50`: búsqueda sin `AbortController` ni debounce (carrera: llega antes la respuesta vieja); Enter en el comentario no envía.
- **F-28** Doble envío sin estado de carga: `setlists.js:191`, `bands.js:972`, `catalogo.js:109,125`, `band.js:558`, `profile.js:69`, `login.js:26,39`. Botón con `loading` + `disabled`.
- **F-29** `design-system.css:220` `.bf-badge{text-transform:capitalize}` reescribe nombres de banda escritos por el usuario.
- **F-30** Tokens que no existen: `--border-color`, `--surface-color`, `--success-color` (`style.css:417,464,478,524,905,915,927`, `tuner.js:119`) → siempre el fallback oscuro.
- **F-31** Colores hardcodeados: `style.css` 54 hex + 110 rgba fuera de `:root`; en JS `app.js:350-351,392-393`, `login.js:14`, `bands.js:368`, `library.js:131`; `.toast-error/.toast-success` (#ff6b6b/#51cf66).
- **F-32** Fuentes: `<link>` a Inter + Roboto Mono en 11 páginas que ningún CSS usa; IBM Plex importada dos veces (`design-system.css:19`, `style.css:2`) + `<link>` en `evento.html:12` → cadena render-blocking y GDPR (Google Fonts remoto). Self-host.
- **F-33** `app.js:307-322`: el autosave de BPM **reescribe el BPM compartido de la canción de banda para todos** (y falla en silencio para `guest`). Guardar tempo por usuario (localStorage) o pedir confirmación.
- **F-34** `sync_engine.js:139-161`: el motor no para al final (rAF y "Compás N" siguen indefinidamente). *(Excepción permitida al motor: añadir parada al llegar a `totalBeats`, con test.)*
- **F-35** Rendimiento: `engine.subscribe` hace 2 `querySelectorAll` + escrituras por frame (`app.js:116-118`); el editor re-parsea toda la canción por tecla (`editor.js:403`) y la biblioteca re-pinta por tecla (`library.js:341`) sin debounce; afinador O(n²) con n=2048 por frame (`tuner.js:29-30,132`).
- **F-36** Peticiones repetidas por página: `/bands/` y `/profile/me` en `shell.js:95,119` y otra vez en `home.js:83-85`, `library.js:23`, `profile.js:15-22`, `catalogo.js:193`. Caché de sesión por página (`core/session.js`).
- **F-37** `login.js:39-41`: "Crear cuenta" salta `required/minlength` del formulario; sin confirmación de contraseña ni medidor.
- **F-38** `util.js:120-133`: `confirmModal` enfoca el botón **destructivo** y Enter confirma; "Quitar" sin confirmación en `setlists.js:247`, `band.js:425,432`. Foco en Cancelar; deshacer (toast con "Deshacer" 5 s) para quitar de setlist.

**Calidad / infra / docs**

- **Q-09** `tests/unit/test_aislamiento_parametrizado.py:32-54,65`: el gate es una **lista manual de 21 de 57 rutas** (37 %); su docstring dice que las recorre todas. 11 rutas sin ningún test de aislamiento (§13.C). Derivar de `app.routes` e introspeccionar `route.dependant` exigiendo `require_band_*`; comprobar que el dueño NO recibe 404.
- **Q-10** `ci.yml`: acciones por tag (no SHA), sin `permissions:`, sin `concurrency`, `push: ["**"]` + `pull_request` duplica runs, sin artefactos de fallo (trazas Playwright; `conftest.py:155-160` borra el log del servidor en teardown), un solo job, sin cobertura, e2e que cargan `fonts.googleapis.com`/`cdn.jsdelivr.net` con `networkidle` (no herméticos). CI ≈10–15 min por push con timeout de 20.
- **Q-11** Suite: `acting_as` copiado en 11 ficheros; 19 `wait_for_timeout` (p. ej. `test_player.py:71,124,170` miden avance de beat tras 0,9–2,5 s → flaky bajo carga); 68 `:has-text` + 73 asserts sobre texto visible (contradice V5 §0.1.5); 17 e2e hacen `wipe_*` sobre la única BD (orden-dependientes); ~30 % de tests son de estilo/wording (`test_design_system` exige `#ff6b4a`, `test_terminologia`, `test_tipografia`, `test_ancho`…) → **cambiar un color rompe CI**; `test_js_logic.py` arranca Chromium para probar funciones puras.
- **Q-12** `.vercelignore:4` excluye `pyproject.toml`; `uvicorn`, `alembic`, `Mako` en el bundle de runtime (innecesarios).
- **Q-13** `.gitignore:9-10` solo `.env`/`.env.local` → `.env.production` se colaría. `.env.*` + `!.env.example`.
- **Q-14** Multi-tenant solo en app: el backend conecta como `postgres` (RLS ignorado); bucket `media` público. Hoy no es urgente (el front no habla con PostgREST), pero planificar RLS mínimo y revisar políticas de Storage antes de abrir datos al público (V5 §5).
- **Q-15** `doctor.py:149-152` repite el patrón `subprocess.PIPE` que `conftest.py:108-112` documenta como bloqueo en Windows.
- **Q-16** `tests/unit/test_identidad_imagenes.py:20` hardcodea el ref del proyecto Supabase de prod.
- **Q-17** Unit tests solo sobre SQLite: CHECK/`nullslast`/`Numeric` difieren en Postgres; el drift real nunca se prueba.

### 4.4 🟢 Bajos (lista corta; detalle en los informes de origen)

- **B-24** Barra final inconsistente (`finance` sin `/`, el resto con `/`; el front llama sin barra → 307 extra). Unificar sin barra.
- **B-25** REST: `DELETE /members/{uid}` devuelve 200+body vs 204 en otros; "recurso ajeno" 400 (`events_router.py:65,78`) vs 404; invitación caducada 400 (mejor 410).
- **B-26** OpenAPI: título "ChordFlow API… Partituras y Acordes" (`main.py:45-49`), sin `/v1`, sin respuestas 401/403/404 documentadas, tag `dashboard` para `/me`, `/docs` público.
- **B-27** `profile_router.py:27-32`: get-or-create sin `IntegrityError` → 500 ocasional en el primer login con dos peticiones concurrentes.
- **B-28** Columnas/estados muertos: `Band.currency` nunca expuesto; `Song.is_public/source_type/source_file_path/format_version/duration_beats` sin uso; `PublicScore.status hidden/removed` y `ScoreComment.deleted_at` sin endpoint → **no hay moderación del catálogo**.
- **B-29** Un miembro no puede abandonar una banda por sí mismo (`bands_router.py:336-354`, solo admin).
- **B-30** Setlist personal admite canciones de banda (`setlists_router.py:42-43` sin `band_id IS NULL`), a diferencia de colecciones.
- **B-31** Duplicación: `_append_sections` ×2, `_deny_guests` ×3, `_valid_*_song_ids/_set_items/_to_response` ×4; imports cruzados entre routers.
- **B-32** Índices que faltan para las consultas reales: `events(band_id, starts_at)`, `messages(band_id, event_id, created_at)`, `transactions.event_id`, `events.setlist_id/venue_id`, `songs(owner_id, band_id, deleted_at)`.
- **B-33** Máquina de estados de eventos libre: `done→lead` permitido, `ends_at < starts_at` sin validar, pipeline `lead/contacted` en ensayos.
- **B-34** `catalog_router.py:162-165`: duplicados evitados solo por `publisher_id` (dos miembros publican la misma canción dos veces); `:291-294` convierte cualquier excepción en 400.
- **B-35** `ScoreCommentOut.user_id` e `InvitePreview.band_id` exponen UUIDs innecesarios.
- **B-36** `logging_config.py:35` `FileHandler` sin rotación en local; `Numeric` en SQLite se guarda como float.
- **F-39** `library.js:346-348` código muerto (`#user-email`, `#btn-logout`); `.user-box` (`style.css:1106-1119`); drag sin `pointercancel` (`setlists.js:176-184`); `cover_url` sin escapar en `style` (`band.js:104`, viene validada del backend, pero conviene escapar).
- **F-40** A11y menor: pestañas sin `aria-controls/tabpanel/flechas` (`band.js:119-122,604-613`); ☰ sin `aria-expanded`/Escape; sin `:focus-visible` en `.bf-subnav-item, .bf-profile-card, .bf-brand, .bf-hamburger, .att-btn…`; `band.html` sin `<h1>`; `h5` bajo `h3`; `ev-date` sin label; `--bf-text-faint` sobre `--bf-surface-2` ≈ 4.4:1.
- **Q-18** Migraciones con ids escritos a mano (`b3f1a9c2d4e5`…): funciona, pero delata edición manual.
- **D-01…D-11** Contradicciones docs↔código (§13.D) y datos personales en docs.

---

## 5. Diagnóstico visual y de UX: por qué no parece profesional (y cómo se arregla)

> Fuente: navegación real con datos demo (79 capturas). Cada punto nombra la pantalla donde se ve.

### 5.1 Las 12 causas raíz

1. **Emojis como iconos y como estructura.** 157 en html/js. Se ven en títulos (`🎵 Setlists`,
   `Explorar 🌍`, `🎸 BandFlow` en el login y en join), en botones (`✅ Voy · 🤔 Quizás · ❌ No voy`
   en Inicio, Resumen y Agenda; `📌` fijar; `✅ Unirme a la banda`), en placeholders (`🔍 Buscar…`),
   en filas (`🎼`, `🎤`, `⏰ Pronto`, `🔗 Enlace`, `📍`, `💶`, `📞`, `🏦 Fondo`, `📅 Temporada`,
   `➖/➕` movimientos, `📁` colecciones, `👤 Personal`/`🎸 banda` en chips). Cada sistema (Windows,
   Android, iOS) los dibuja distinto, pesan más que el texto y rompen la línea de iconos SVG
   Lucide que ya existe. **Es la causa nº 1 de la sensación amateur.**
   → Mapa emoji→`bfIcon` en §13.A y regla 6 de §0.2.

2. **Dos lenguajes visuales en la misma pantalla.** Botones píldora de 30 px con texto negro
   (`.primary-btn`, login/join/perfil/setlists/chat) junto a `.bf-btn` rectangulares; chips
   monoespaciadas coral en Biblioteca junto a `bf-badge`; listas `.setlist-song` con botones
   fantasma (`.setlist-item-btn`, sin altura fija, blanco translúcido) en Repertorio, Setlists,
   Agenda, Finanzas y Chat de banda, bajo tarjetas `bf-card` con 1,5 rem de aire. 114 clases
   legacy solo en `band.html`.
   → §6.3: un componente por concepto y retirada de `style.css` por partes.

3. **Controles nativos sin estilo** dentro de una UI oscura: el `<select>` de estado de evento
   (Agenda de banda), el de compás (editor, afinador) y el de La4 salen como cajas blancas del
   sistema. → `bf-select` con flecha SVG y tema.

4. **Páginas medio vacías en escritorio.** Bandas, Setlists, Finanzas TÚ, Chat TÚ, Agenda TÚ,
   Explorar, Afinador, Miembros y Giras usan el 30–40 % superior de la pantalla y el resto es
   fondo. No es "aire": es falta de estructura secundaria (KPIs, filtros, actividad, detalle).
   → §5.3 define qué va en cada página para que tenga cuerpo sin recargar.

5. **Filas sobrecargadas.** La agenda de banda muestra por evento: emoji + título + tipo + fecha +
   badge de estado + "Pronto" + "Enlace" + asistentes + sala + caché + contacto + 3 botones de
   asistencia + chat + `<select>` + menú ⋯ (hasta 7 controles). Es la fila más usada de la app.
   → Fila de 56 px con lo esencial; asistencia como *segmented control*; detalle en panel.

6. **Destructivo al lado de primario.** `✕`/🗑 junto a ▶ en repertorio, setlists, movimientos,
   mensajes y salas, al mismo tamaño y a un clic. Sin deshacer.
   → Secundarias y destructivas al menú ⋯; "Deshacer" en toast 5 s para quitar/archivar.

7. **Tipografía sin escala.** ~40 valores de `font-size` (19× 0.85rem, 12× 0.9rem, 7× 0.72rem,
   13.5px, 11.5px…) frente a 6 tokens; se piden pesos 800 que no se cargan; `h3` del tamaño del
   texto; `h5` en mayúsculas. Encabezados de sección en Perfil ("MIS BANDAS", "INSTRUMENTOS",
   "EDITAR") enormes para lo que encabezan.
   → §6.5: escala cerrada y jerarquía única.

8. **Tema claro a medias.** Chips de filtro invisibles en Biblioteca; botones fantasma
   "Quizás/No voy" invisibles en el Resumen; badge Admin amarillo sobre crema; modales y toasts
   oscuros (F-02); popover ⋯ oscuro; saldos verde/rojo pastel. Y un flash oscuro→claro al cargar
   cada página (F-20).
   → Tokens en todo, prohibición de `#hex`/`rgba` fuera de `:root`, `theme.js` en `<head>`.

9. **Identidad descuidada.** Avatar del mismo usuario **coral** en el lateral y **verde** en Perfil
   y Miembros; icono PWA verde menta frente a marca coral; login con emoji en vez del logo SVG
   del shell y con "G" tipográfica como botón de Google; fuentes Inter/Roboto descargadas y no
   usadas; textarea del editor en Roboto Mono y la preview en Plex Mono; logo con ecualizador en
   movimiento perpetuo (`shell.css:88-90`).
   → Un color por usuario (hash estable), icono coral, logo SVG en todas partes, Google oficial.

10. **Formatos.** Dinero "-160.00 €" / "-134.50 €" (punto, signo ASCII, cero usos de `Intl`);
    fechas sí localizadas. Pequeño, pero lo ve cualquiera en Finanzas e Inicio.
    → `Intl.NumberFormat('es-ES', {style:'currency'})`: "−160,00 €".

11. **Ritmo y espaciado.** ~150 `style=""` inline (`margin-bottom:.3rem/.6rem/1.4rem/1.6rem…`)
    en plantillas JS impiden corregir nada globalmente; tarjeta dentro de tarjeta en Agenda,
    Finanzas y Chat TÚ (doble borde); tarjetas de banda de distinta altura; huecos irregulares
    entre campos del editor en móvil.
    → Rejilla de 8 px, utilidades `.bf-stack--sm/md/lg`, cero inline.

12. **Copy.** Title Case ("Crear Partitura", "Título de la Canción"), inglés ("Player", "Play/
    Pause", "Lead"), términos cruzados ("Setlists" / "Repertorios" en `CLAUDE.md` / pestaña
    "Giras" cuando la guía dice "Conciertos"), textos que citan botones que ya no existen
    ("Pulsa «✏️ Editar»"), mensajes técnicos ("Ocurrió un error: Error al guardar la canción",
    "[object Object]"), un banner "👋 Todo lo de tu banda está en estas pestañas…" que se repite
    en las 9 pestañas hasta pulsar Entendido.
    → Glosario (§6.10), *sentence case*, `apiJson` que traduce errores, onboarding de una sola
    vez y no por pestaña.

### 5.2 Bugs de layout vistos navegando (resumen; detalle en §4)

| # | Pantalla | Qué se ve | ID |
|---|---|---|---|
| 1 | Móvil · Agenda de banda | Texto en columna de 60 px, botones solapando la fecha | V-01 |
| 2 | Móvil · Reproductor | Letra cortada por la derecha; control de tono fuera de la topbar | V-02 |
| 3 | Escritorio · Join | Botón "Unirme" descolocado fuera del bloque centrado | V-03 |
| 4 | Chat de banda (escritorio y móvil) | Botón Enviar gigante, desalineado del input | V-04 |
| 5 | Móvil · Agenda TÚ | Badge de banda en columna propia, texto estrujado | F-… (misma causa que V-01) |
| 6 | Claro · Biblioteca | Chips de filtro y "Nueva colección" sin borde ni fondo | F-09 |
| 7 | Claro · Resumen de banda | Botones ghost invisibles; badge Admin con poco contraste | F-09 |
| 8 | Claro · Cualquier modal/toast | Texto oscuro sobre fondo oscuro | F-02 |
| 9 | Móvil · Editor | Huecos irregulares entre BPM / Compás / Enlace | §5.1.11 |
| 10 | Escritorio · Reproductor | Botón coral "4" sin etiqueta (cuenta atrás) | §5.3 |
| 11 | Escritorio · Bandas | Tarjetas de altura distinta según el texto | §5.1.11 |
| 12 | Escritorio · Login | Emoji-logo, botones píldora, "G" como icono | §5.3 |

### 5.3 Página a página: estado actual → diseño objetivo

Formato: **Hoy** (lo visto) · **Problemas** · **Objetivo** (qué tiene que haber al cerrar V6-F4).
Los ids/clases que usan los e2e se conservan; se cambia la estructura interna y el estilo.

#### Login (`login.html`) — rehacer
- **Hoy:** tarjeta centrada con `🎸 BandFlow`, dos campos, botones píldora "Entrar"/"Crear
  cuenta" en el mismo formulario, "G Entrar con Google". Sin recuperar contraseña, sin legal, sin
  propuesta de valor. Siempre oscuro. Carga Inter/Roboto que no usa.
- **Problemas:** primera impresión amateur; crear cuenta salta la validación nativa; nada que
  explique qué es la app a quien llega por un enlace de invitación.
- **Objetivo:** layout a dos columnas en escritorio (izquierda: logo SVG, claim en una frase,
  3 bullets con icono — repertorio, bolos, cuentas —; derecha: formulario) y una columna en
  móvil. Pestañas "Entrar / Crear cuenta" (no dos botones en un form). Botón Google con el logo
  oficial. "¿Olvidaste la contraseña?" (Supabase `resetPasswordForEmail` + página `reset.html`).
  Mostrar/ocultar contraseña. Mensajes de error en castellano bajo el campo. Enlaces a
  Términos y Privacidad. Respeta el tema. Sin emoji.

#### Join (`join.html`) — rehacer
- **Hoy:** cabecera de reproductor para una página de un botón; `🎸` como hero; botón
  descolocado en escritorio (V-03).
- **Objetivo:** tarjeta centrada con logo/cover de la banda, nombre, "Te han invitado como
  miembro", avatares de miembros (3 + "+N"), un botón primario "Unirme a la banda". Si no hay
  sesión: "Entrar" / "Crear cuenta" conservando el código (`?code=` → `login.html?next=join…`).
  Estados: inválida / caducada / agotada con texto claro y CTA "Pedir otro enlace".

#### Inicio (`app.html`) — mejorar
- **Hoy:** saludo con 👋, evento destacado con emoji, tres tarjetas de alturas distintas (saldo,
  accesos rápidos, mensajes) y la mitad inferior vacía. "Accesos rápidos" duplica el lateral.
- **Objetivo:** cabecera "Hola, Oscar" + fecha; **fila de KPIs** (próximo bolo en N días ·
  canciones en repertorio · pendientes de responder · saldo total); **"Esta semana"** (lista de
  eventos de todas las bandas con asistencia como segmented control, sin recargar la página al
  responder); **actividad reciente** (mensajes, canciones nuevas, movimientos) con avatar y
  banda; **"Para hoy"** (si hay evento hoy: Tocar setlist, ver sala, quién viene). Sin accesos
  rápidos redundantes. Estado vacío para usuario sin banda: dos tarjetas grandes "Crear banda" /
  "Tengo un código de invitación".

#### Mis bandas (`bands.html`) — mejorar
- **Hoy:** dos tarjetas pequeñas de altura desigual; 70 % de la pantalla vacía.
- **Objetivo:** tarjetas con **cover** (foto o degradado del color de banda), logo, nombre, rol,
  próximo evento, avatares de miembros apilados, 2 contadores (canciones, setlists), altura
  fija. Botón "Nueva banda" y "Unirme con código" en la cabecera. Estado vacío ilustrado (SVG
  propio, no emoji).

#### Espacio de banda (`band.html`) — rehacer contenido, conservar estructura
- **Cabecera:** cover (foto o degradado del color de banda) a toda anchura, logo solapado, nombre,
  rol, miembros, acciones contextuales (Invitar, Tocar setlist, ⋯). Hoy el banner sin cover es
  una caja plana.
- **Pestañas:** 9 en una fila. En móvil hacen scroll horizontal sin indicador. Objetivo: pestañas
  con contador (Miembros 3 · Repertorio 12), scroll con desvanecido en los bordes en móvil, y
  URL con hash (F-13). Orden propuesto: Resumen · Repertorio · Setlists · Agenda · Finanzas ·
  Chat · Miembros · Giras · Ajustes (lo más usado primero; D-V6-4 para confirmar).
- **Banner de onboarding:** solo la primera vez que se entra a un espacio de banda, una sola vez
  en total (no por pestaña) y con cierre que persista en servidor (perfil) no solo en
  localStorage.
- **Resumen:** hoy: evento + saldo + último mensaje + 3 contadores, columna derecha corta.
  Objetivo (hereda V5 §9.6): calendario mini del mes · pizarra (V5) · estado económico ·
  progreso del repertorio; mientras V5-F9 no exista: evento próximo con asistencia, saldo con
  "quién debe a quién" en 3 líneas, últimos 3 mensajes, contadores. Alturas alineadas.
- **Miembros:** hoy lista plana sin acciones. Objetivo: lista con avatar (color estable), nombre,
  instrumentos como chips, rol como badge; para admin: menú ⋯ (cambiar rol, dar de baja,
  reactivar) usando los endpoints que ya existen (§3.6); bloque "Invitaciones" con la lista de
  códigos activos, usos, caducidad, copiar enlace y **revocar** (S-07). "Salir de la banda" para
  el propio usuario (B-29).
- **Repertorio:** hoy el CTA principal es "Copiar de mis partituras" y cada fila tiene ▶ y ✕.
  Objetivo: un botón "Añadir canción" con menú (Nueva · Importar por enlace/nombre/foto · Copiar
  de mi biblioteca); filas con título, artista, **tono · BPM · capo** como meta discreta, quién la
  añadió, y a la derecha ▶ Tocar + ⋯ (Editar, Quitar con deshacer, Añadir a setlist); buscador y
  orden (A–Z, recientes, tono). Colecciones como chips arriba. Estado de preparación por miembro
  (V5 §9.4) encaja aquí cuando llegue.
- **Setlists:** hoy una fila con 3 botones. Objetivo: tarjetas con nombre, nº canciones,
  **duración estimada** (suma de duraciones si existen; si no, 3,5 min × canciones), último
  concierto donde se usó, botón grande "Tocar" y ⋯ (Editar, Duplicar, Exportar PDF, Borrar).
  Editor de setlist con arrastrar, nota por canción y "Añadir desde repertorio" en panel lateral.
- **Agenda de banda:** la pestaña más rota (V-01). Objetivo: toggle Lista / Calendario mensual
  (componente `bf-calendar`, V5 §7); filas de 56 px: icono de tipo (SVG), título, fecha relativa
  y absoluta, sala, badge de estado; a la derecha asistencia **segmented** (Voy · Quizás · No) y
  ⋯ (Hilo, Compartir, Editar, Cambiar estado, Borrar). Clic en la fila → **panel de detalle**
  (lateral en escritorio, hoja inferior en móvil) con todo lo demás (booking, caché, contacto,
  asistentes, setlist, notas, hilo de chat). Las **Salas** salen de Agenda a un sub-bloque de
  Ajustes o a su propio desplegable al crear concierto.
- **Finanzas de banda:** estructura correcta. Objetivo: formato `Intl`, "quién pagó" y "en cuántas
  partes" en cada movimiento, filtro por evento/mes/categoría, **desglose por evento** (V5 D-FIN-1),
  listado de liquidaciones (endpoint existe, UI no) con borrar, gráfico simple de barras por mes
  (SVG propio), "Liquidar" que proponga el mínimo de pagos. Mover 🏦/📅/➖/➕ a iconos.
- **Chat de banda:** hoy filas "Nombre: texto" sin hora ni avatar; Enviar gigante (V-04); scroll
  que salta (F-03). Objetivo: mensajes agrupados por día y por autor consecutivo, avatar, hora,
  propios a la derecha (o resaltados), fijados en una franja superior colapsable, hilos de evento
  como "contexto" encima del composer, composer de 40 px con Enter envía, estado "enviando",
  editar/borrar propios desde ⋯, carga por cursor, pausa en segundo plano. (V5 §8 lo convierte en
  atajo al Chat global — compatible: el componente de hilo es el mismo.)
- **Giras:** fila mínima. Objetivo: tarjeta con fechas, paradas como timeline vertical,
  presupuesto vs caché, estado; editar/borrar gira (endpoints existen). Se re-presenta como
  "Conciertos" cuando llegue V5 §10.
- **Ajustes:** ya es la referencia visual de la app. Añadir: color de banda elegible, moneda,
  zona horaria por defecto, anuncio "buscamos músico" (V5 §9.9), zona de peligro separada.

#### Biblioteca (`library.html`) — mejorar
- **Hoy:** chips monoespaciadas coral con emoji, tarjetas con barra lateral de color sin acciones
  visibles (solo hover, F-08), sin orden, sin arte.
- **Objetivo:** cabecera con buscador y toggle grid/lista; filtros como `bf-chip` (Todas ·
  Personales · por banda con su punto de color); tarjetas con título, artista, meta discreta
  (tono · BPM · capo), origen (badge de banda), y acciones siempre visibles en móvil: ▶ y ⋯
  (Editar, Añadir a setlist, Copiar a banda, Mover a carpeta, Borrar). Orden (recientes, A–Z,
  artista). Paginación o "cargar más" (B-06). Estado de error distinto del estado vacío (F-07).
  Las **carpetas** de V5 §6 se construyen sobre estos filtros.

#### Setlists personales (`setlists.html`) — mejorar
- Igual patrón que los setlists de banda (tarjetas, duración, Tocar, exportar PDF). Quitar el 🎵
  del h1. Vista de edición con historial (`history.pushState`) para que atrás funcione.

#### Editor (`editor.html`) — reorganizar
- **Hoy:** cabecera con título/artista/BPM/compás/enlace y tres bloques "con IA" apilados
  (buscar por nombre · pegar enlace · foto) con copy largo, labels en mayúsculas con emoji, y
  abajo textarea + preview. Faltan tono, capo y afinación en la cabecera. Sin guardia de cambios
  (F-06). Publica al catálogo sin avisar (F-18).
- **Objetivo:** cabecera con **todos** los metadatos (título, artista, tono, capo, BPM, compás,
  afinación, enlace de referencia) en una rejilla de 2 filas; un único botón "Importar" que abre
  un diálogo con tres pestañas (Buscar · Enlace · Foto) y el copy de ayuda dentro; textarea y
  preview a la misma altura con divisor arrastrable; barra inferior fija con "Guardar", "Guardar y
  tocar" y checkbox "Compartir en Explorar". `beforeunload`. Atajo Ctrl+S. Mismo monoespaciado en
  textarea y preview.

#### Reproductor (`index.html`) — pulir y arreglar móvil
- **Hoy:** base buena (modo escenario, acordes coral, barra inferior con Play). Problemas: letra
  cortada en móvil (V-02), toolbar con 11 controles en 2–3 filas en móvil, botón coral "4" sin
  etiqueta, no para al final (F-34), recarga completa entre canciones de un setlist (F-19), el
  autosave de BPM pisa el BPM de la banda (F-33), sin control de tamaño de letra, sin indicador
  de sección.
- **Objetivo:** topbar compacta (título/artista a la izquierda; BPM y tono como *popovers* en
  móvil; menú ⋯ con imprimir, diagramas, afinador, ayuda); **tamaño de letra** A−/A+ persistido;
  **sección actual** en la barra inferior ("Estribillo · Compás 12"); navegación entre secciones
  (toque en el nombre); cuenta atrás con icono + "4"; wrap de letra en móvil; modo setlist con
  "Siguiente: Zombie" y cambio in-page; parada al final con "Siguiente canción"; tempo por
  usuario (no se escribe en la canción compartida sin confirmación). Motor intacto salvo F-34.

#### Agenda TÚ (`agenda.html`) — rehacer
- **Hoy:** lista dentro de una tarjeta, emojis, sin crear, badge de banda que rompe el móvil.
- **Objetivo:** cabecera con "Nuevo evento" (elige banda); toggle Lista / Calendario mensual
  (`bf-calendar`, con punto del color de cada banda); lista agrupada por semana ("Esta semana",
  "Próxima semana", "Más adelante") con filas de 56 px; filtro por banda como chips; asistencia
  en línea sin recargar; exportar `.ics` / suscribirse al calendario (§7.5).

#### Finanzas TÚ (`finanzas.html`) — rehacer
- **Hoy:** dos filas. **Objetivo:** resumen global (saldo total, te deben / debes, por banda),
  últimos movimientos de todas las bandas, "liquidar" desde aquí, y cuando llegue V5 §11 el
  bloque Personal (material). Gráfico simple.

#### Chat TÚ (`chat.html`) — rehacer
- **Hoy:** lista de enlaces. **Objetivo:** dos columnas (conversaciones | hilo) como cualquier
  chat; no-leídos con `.bf-nav-badge` (ya definido y sin usar) en el lateral; grupos "Mis bandas"
  / "Otros contactos" (V5 §8) listos desde el diseño.

#### Perfil (`profile.html`) — rehacer
- **Hoy:** avatar verde (coral en el lateral), encabezados enormes, "Instrumentos (separados por
  comas)", botón píldora junto a `bf-btn`.
- **Objetivo:** tarjeta de identidad (foto, nombre, instrumentos como chips seleccionables de una
  lista con "otro"), bandas con rol, y una sección **Cuenta**: email, cambiar contraseña, idioma,
  tema, notificaciones, exportar mis datos, borrar cuenta (§7.1). Campos de V5 §5.2 (estado,
  zona, bio, WhatsApp) encajan aquí.

#### Afinador / Metrónomo (`afinador.html`) — pulir
- Centrar y agrandar las dos tarjetas; nota grande "—" en reposo; aguja con escala ±50 cents;
  botón de micrófono con estado; metrónomo con scheduler correcto (F-11), acento visual grande,
  presets de BPM, subdivisiones.

#### Explorar (`biblioteca-global.html`) — rehacer (V5 §5)
- Quitar 🌍; mientras no llegue V5-F5, al menos: tarjetas en vez de filas, estrellas accesibles,
  paginación, búsqueda con debounce/abort (F-27), página de detalle con "Tocar" y "Guardar".

#### Evento público (`evento.html`) — pulir
- Cover/logo de banda, "Añadir al calendario" (.ics), enlace a mapa, compartir (Web Share API),
  CTA de registro ya existe. Sin emoji. Tema según sistema.

---

## 6. Sistema de diseño 2.0 (especificación)

> Se conserva la identidad decidida en V5 (D-EST-1: oscuro + coral + IBM Plex). Lo que cambia es
> la **disciplina**: un solo sistema, tokens para todo, componentes nombrados y una regla de
> entrada (nada nuevo fuera del sistema).

### 6.1 Principios

1. **Un concepto, un componente.** No hay "botón del player" y "botón del shell": hay `bf-btn`
   con variantes. `style.css` se vacía por partes hasta quedar solo `player.css` y `editor.css`.
2. **Tokens o nada.** Todo color, radio, sombra, espaciado y tamaño de fuente sale de `--bf-*`.
   Un grep en CI falla si aparece `#hex`/`rgba(` fuera de `:root` (§8.5).
3. **Jerarquía antes que decoración.** Cada página tiene: cabecera (título + acción primaria),
   bloque principal, bloques secundarios. Una sola acción primaria coral por vista.
4. **Densidad de herramienta, no de folleto.** Listas de 48–56 px, tarjetas de 16–20 px de
   padding, 8 px de rejilla. El aire se pone entre bloques, no dentro de cada fila.
5. **Móvil es el escenario.** El reproductor, la agenda y el chat se usan en el móvil en el
   local de ensayo: cada componente se diseña primero a 390 px.
6. **Iconografía SVG (Lucide) al 100 %**, 16/20/24 px, `aria-label` en los botones de solo icono.
7. **Estados siempre**: hover, focus-visible, active, disabled, loading, empty, error, skeleton.
8. **Motion discreto**: 120–200 ms, `prefers-reduced-motion`; nada en movimiento perpetuo.

### 6.2 Tokens: lo que hay y lo que falta

Ya existen en `design-system.css` y se conservan: superficies, texto, acento, semánticos, roles,
fuentes, 6 tamaños, 4 pesos, 7 espaciados, 4 radios, 3 sombras, transición. Añadir:

| Grupo | Tokens nuevos | Para qué |
|---|---|---|
| Tipografía | `--bf-fs-3xl: 2.25rem` (hero/BPM), `--bf-lh-tight: 1.2`, `--bf-lh-base: 1.5` | cerrar la escala a 7 tamaños y 2 interlineados |
| Radios | reducir a 3: `sm 6` · `md 10` · `lg 16` (+ `full`) | hoy hay 24 radios distintos; las píldoras desaparecen salvo chips/badges |
| Z-index | `--bf-z-dropdown: 100` · `--bf-z-sticky: 200` · `--bf-z-overlay: 1000` · `--bf-z-dialog: 1010` · `--bf-z-toast: 1100` | fin de los 9999/10000 sueltos (F-04) |
| Tamaños de control | `--bf-control-sm: 32px` · `--bf-control: 40px` · `--bf-control-lg: 48px` | botones, inputs y filas comparten altura |
| Layout | `--bf-row-h: 56px` · `--bf-content-max: 1120px` · `--bf-content-wide: 1400px` | listas y contenedores |
| Color de banda | `--bf-band-1…8` (paleta de 8 fijos) | `bandColor()` elige por hash del id; el usuario puede elegir uno en Ajustes |
| Color de usuario | mismo mecanismo (hash del `user_id`) | el avatar de Oscar es del mismo color en todas las páginas |
| Focus | `--bf-focus-ring: 0 0 0 3px var(--bf-accent-weak)` | anillo único |

Tokens legacy a eliminar tras migrar: `--bg-panel`, `--accent-color`, `--text-primary/secondary`
y los tres que **no existen** y hoy siempre caen al fallback (`--border-color`, `--surface-color`,
`--success-color`).

### 6.3 Componentes canónicos (cada uno con su clase, variantes y estados)

| Componente | Clase | Variantes / notas |
|---|---|---|
| Botón | `bf-btn` | `--primary` (uno por vista), `--secondary` (borde), `--ghost`, `--danger`; tamaños `--sm 32` / `40` / `--lg 48`; `--icon` (cuadrado); estado `is-loading` (spinner, `disabled`) |
| Botón de icono | `bf-btn --icon` | 40×40 (32 en filas densas), `aria-label` obligatorio, tooltip por `title` |
| Segmented control | `bf-segmented` | asistencia Voy/Quizás/No; toggles Lista/Calendario, Grid/Lista; `role=radiogroup` |
| Menú ⋯ | `bf-menu` | popover con teclado (flechas, Escape), tema, `--danger` para destructivas; sustituye a `.ev-more-menu` |
| Fila de lista | `bf-row` | 56 px: `__lead` (icono/avatar) · `__main` (título + meta) · `__trail` (acciones); en < 768 px `__trail` baja a una segunda línea o se colapsa en ⋯. Sustituye a `.setlist-song` |
| Tarjeta | `bf-card` | `--interactive` (hover lift, `<a>` interno para teclado), `--cover` (cabecera con imagen/degradado), `--stat` (KPI) |
| Diálogo | `bf-dialog` (`bfDialog()` en `ui/dialog.js`) | focus trap, Escape, devolución de foco, cabecera/pie fijos, cuerpo con scroll, tamaños `sm/md/lg`, hoja inferior en móvil; `confirm()` con foco en Cancelar |
| Campo | `bf-field` + `bf-label` + `bf-input` / `bf-select` / `bf-textarea` + `bf-help` + `bf-error` | 40 px, tema, `:invalid` solo tras tocar, select con flecha SVG; sustituye a `.search-box` como input genérico |
| Buscador | `bf-search` | input con icono SVG dentro, botón limpiar, debounce 250 ms |
| Pestañas | `bf-tabs` | `role=tablist`, `aria-controls`, flechas, contador opcional, scroll con desvanecido en móvil, hash en URL |
| Badge | `bf-badge` | `--admin/--member/--guest`, `--success/--warning/--danger/--info`, sin `text-transform` (F-29) |
| Chip | `bf-chip` | filtro seleccionable (`aria-pressed`), con punto de color de banda, con ✕ para quitar |
| Avatar | `bf-avatar` (`bfAvatar()`) | foto o iniciales, color por hash, tamaños 24/32/40/56/80, `--stack` para apilar |
| Toast | `bf-toast` (`ui/toast.js`) | `--success/--error/--info`, acción opcional ("Deshacer"), `aria-live`, z-index token, nunca bajo un diálogo |
| Estado vacío | `bf-empty` (`bfEmpty()`) | icono SVG grande, título, texto, CTA; **distinto** de… |
| Estado de error | `bf-error-state` | icono, "No se pudo cargar", botón Reintentar; lo usa `apiJson` |
| Skeleton | `bf-skeleton` | ya existe; usar en todas las listas |
| Cabecera de página | `bf-page-header` | título, subtítulo, acciones a la derecha; en móvil el título va a la topbar |
| Topbar móvil | `bf-topbar` | ☰ + título de la página + acción primaria; hoy solo hay ☰ |
| KPI | `bf-stat` | valor grande (mono, tabular), etiqueta, delta opcional |
| Calendario | `bf-calendar` | mensual + semanal, puntos por color de banda, contrato tipado de V5 §7 |
| Panel de detalle | `bf-drawer` | lateral en escritorio, hoja inferior en móvil (detalle de evento, canción) |
| Importe | `bf-amount` | `Intl` es-ES, `--pos/--neg/--zero`, mono tabular |
| Fecha | `bf-date` | relativa ("en 2 días") + absoluta en `title`; `fmtDate` único |

### 6.4 Iconografía

Lucide SVG vía `bfIcon(name, {size})`. Reglas: 16 px en texto/badges, 20 px en botones y filas,
24 px en topbar/cabeceras, 48 px en estados vacíos. Mapa emoji→icono en §13.A. Emoji permitido
**solo** en contenido escrito por el usuario (mensajes, notas, nombres).

### 6.5 Tipografía

- **IBM Plex Sans** (UI) e **IBM Plex Mono** (acordes, importes, BPM), **autoalojadas** en
  `static/fonts/` con `font-display: swap` y `preload` del regular (adiós Google Fonts: GDPR y
  render-blocking). Quitar Inter/Roboto de las 11 páginas.
- Escala cerrada: `xs 12` · `sm 14` · `base 16` · `lg 18` · `xl 22` · `2xl 28` · `3xl 36`.
  Jerarquía: h1 2xl bold · h2 xl semibold · h3 lg semibold · cuerpo base · meta sm muted ·
  eyebrow xs uppercase tracking 0.06em (solo para etiquetas de sección, nunca para h2/h3).
- Pesos 400/500/600/700. Números con `font-variant-numeric: tabular-nums`.
- *Sentence case* en todo ("Nueva partitura", no "Nueva Partitura").

### 6.6 Formatos (un `format.js`)

- `fmtMoney(n, currency)` → `Intl.NumberFormat('es-ES', {style:'currency', currency})` (−160,00 €).
- `fmtDate(d)` → relativa si < 7 días ("hoy 21:00", "mañana", "en 3 días") + absoluta en `title`;
  `fmtDateLong` para detalle ("sábado 14 de noviembre, 20:30").
- Zona horaria del usuario (`Intl.DateTimeFormat().resolvedOptions().timeZone`) sobre fechas UTC
  del servidor (B-10).

### 6.7 Tema claro/oscuro

- `theme.js` inline en el `<head>` de las 16 páginas (F-20); el reproductor fuerza oscuro con su
  propio `data-theme="dark"` (D-EST-2 se mantiene).
- Cada componente se revisa en los dos temas antes de cerrar su tarea (captura en el PR).
- Check automático: ningún `#hex` ni `rgba(` fuera de `:root` en `static/**.css` ni en `.js`.

### 6.8 Móvil

- Breakpoints: 480 / 768 / 1024. Topbar con título y acción. Lateral como drawer (ya existe).
- Patrones: `bf-row__trail` baja de línea o se colapsa en ⋯; tablas → tarjetas; diálogos → hoja
  inferior; pestañas con scroll y desvanecido; targets ≥ 44 px (ya en `pointer:coarse`).
- Reproductor: toolbar de 2 filas máximo, letra con `clamp()` y wrap, pantalla completa.
- Test de overflow horizontal en **todas** las páginas a 390 px (hoy solo 4, Q-10).
- `100dvh` en vez de `100vh` (F-14).

### 6.9 Accesibilidad mínima exigible

Foco visible en todo lo interactivo; tarjetas y filas navegables por teclado (`<a>`/`<button>`
reales); diálogos con focus trap y Escape; pestañas con `aria-controls`; `aria-expanded` en ☰ y
menús; labels reales (no solo placeholder); contraste AA (ya casi); `aria-live` en toasts;
`<h1>` en todas las páginas; `lang="es"`. Una pasada de `axe` (Playwright) por página en CI.

### 6.10 Copy y glosario (15 términos)

| Término único | No usar |
|---|---|
| Canción | partitura (salvo "importar partitura" como acción), score |
| Repertorio (de banda) / Mis canciones (personal) | biblioteca global, mis partituras |
| Setlist | repertorio (en el sentido de lista), lista |
| Colección (de canciones) / Carpeta (V5 §6, cuando exista) | — |
| Ensayo / Concierto / Otro | bolo (solo en copy informal), gig |
| Sala | venue, local (local = de ensayo) |
| Asistencia: Voy / Quizás / No voy | asisto, sí/no |
| Estado de concierto: Contacto · Hablando · Negociando · Confirmado · Hecho · Cancelado | Lead, Contactado |
| Movimiento (gasto / ingreso) | transacción |
| Liquidación | settlement, pago |
| Fondo común | fund, bote |
| Reproducir / Tocar (en escenario) | Play/Pause (solo el icono) |
| Explorar | biblioteca global, catálogo (interno) |
| Invitación (enlace / código) | invite |
| Administrador · Miembro · Invitado | admin (solo en badges cortos), guest |

Mensajes de error siempre en castellano y accionables ("No se pudo guardar la canción. Revisa la
conexión y vuelve a intentarlo."), nunca el texto del servidor tal cual.

---

## 7. Funcionalidades: lo que falta para un SaaS profesional

> Separado en "imprescindible" (sin esto no es profesional), "esperable" (lo dan por hecho los
> usuarios de apps similares) y "diferenciador". Lo de V5 no se repite aquí; se referencia.

### 7.1 Cuenta y acceso — imprescindible
- **Recuperar contraseña** (Supabase `resetPasswordForEmail` + `reset.html`).
- **Verificación de email** activada y pantalla "revisa tu correo".
- **Cambiar email / contraseña** desde Perfil > Cuenta.
- **Cerrar otras sesiones** (Supabase `signOut({scope:'others'})`).
- **Borrar cuenta** (GDPR): anonimizar perfil, salir de bandas (si es único admin, exigir
  transferir), borrar canciones personales; **exportar mis datos** (JSON).
- Emails de auth con marca BandFlow (T-047 pendiente desde junio).
- Páginas de **Términos**, **Privacidad** y aviso de cookies (mínimo legal en la UE).

### 7.2 Onboarding — imprescindible
- Primer uso sin banda: pantalla de dos caminos (Crear banda / Tengo un código) + "Explora con
  una canción de ejemplo" (seed de 1 canción demo personal).
- Al crear banda: asistente de 3 pasos (nombre y color → invitar (enlace listo para WhatsApp) →
  añadir primera canción). Progreso visible en el Resumen hasta completarlo.
- Tour de 4 puntos la primera vez (reemplaza al banner repetido por pestaña).

### 7.3 Gestión de banda — imprescindible
- UI de **miembros** (rol, baja, reactivar) sobre los endpoints existentes; **salir de la banda**
  (B-29) con transferencia de admin si es el único.
- **Invitaciones**: lista, usos, caducidad por defecto 7 días, revocar (S-07), compartir por
  WhatsApp/copiar.
- **Transferir propiedad** / último admin no puede degradarse (B-16).
- Color de banda elegible; moneda (ya en modelo, sin UI, B-28); zona horaria.

### 7.4 Repertorio y setlists — esperable
- Metadatos visibles (tono, capo, BPM, duración); duración estimada del setlist.
- **Exportar / imprimir** setlist (PDF del orden + notas; y "pack" con todas las canciones) —
  lo que hoy las bandas hacen en una hoja.
- **Compartir setlist** por enlace de solo lectura (proyección segura, como el evento público).
- Añadir a setlist desde cualquier lista de canciones; duplicar setlist (existe en personal).
- Estado de preparación por miembro y publicar originales: V5 §9.4 / §5.6.

### 7.5 Agenda — esperable
- Calendario mensual/semanal (`bf-calendar`, V5 §7) en TÚ y en banda.
- **Crear evento desde Agenda TÚ** eligiendo banda.
- **Exportar .ics** por evento y **suscripción** al calendario de la banda (URL con token) →
  Google/Apple Calendar.
- Recordatorio por email 24 h antes (§7.8); propuestas con votación: V5 §9.5.

### 7.6 Finanzas — esperable
- Formato `Intl`, quién pagó, filtros, desglose por evento (V5 D-FIN-1), liquidaciones listables
  y borrables, **sugerencia de liquidación mínima** (algoritmo de deudas simplificadas), exportar
  CSV (existe) y PDF resumen por temporada; gastos recurrentes (local mensual) como plantilla.

### 7.7 Chat — esperable
- Dos columnas, no-leídos, paginación por cursor, editar propios (endpoint existe), realtime
  (Supabase Realtime) cuando llegue V5-F7; hasta entonces polling con `visibilitychange`.

### 7.8 Notificaciones — imprescindible (hoy no existe ninguna)
- **Email transaccional** (Supabase Edge Function + Resend/Postmark gratuito): invitación
  aceptada, evento nuevo/cambiado, recordatorio 24 h, propuesta pendiente, movimiento que te
  afecta, mensaje fijado. Preferencias por tipo en Perfil.
- **Centro de notificaciones** in-app (campana en topbar; tabla `notifications(user_id, kind,
  ref, read_at)`).
- Push PWA (V4 T-155) después.

### 7.9 Reproductor — diferenciador (la joya)
- Tamaño de letra; sección actual y navegación por secciones; modo setlist in-page con
  "siguiente" y prefetch; parada al final; cuenta atrás con etiqueta; tempo por usuario;
  **offline de la última canción/setlist** (IndexedDB) para el local sin cobertura; pantalla
  siempre encendida (`wakeLock`); pedal Bluetooth = teclas PageDown/Espacio (ya hay atajos).
  Únicas excepciones al motor: parada en `totalBeats` (F-34) y `loadSong` sin recarga (F-19),
  cada una con su test.

### 7.10 Explorar / red — V5 §5 (sin cambios de alcance; se construye sobre el sistema 2.0)

### 7.11 Confianza y legal — imprescindible antes de crecer
- Aviso de derechos al publicar en Explorar (letras con copyright) + opción de no publicar
  (F-18); **moderación** mínima: ocultar/retirar partitura y borrar comentario (estados ya en el
  modelo, B-28); reportar contenido.

### 7.12 Landing pública y página de banda — esperable
- `index` público (hoy `/` redirige al login): qué es, capturas, CTA. Página pública de banda
  (V5 §5.6 / I-16) es la pieza viral junto a `evento.html`.

### 7.13 Monetización — más adelante
- `Band.plan` bloqueado hasta Stripe (B-21). Límites del plan Free definidos en servidor
  (p. ej. 1 banda / 50 canciones) solo cuando haya algo que vender (V3-F11).

### 7.14 Transversales — esperable
- Búsqueda global (Ctrl+K: canciones, setlists, eventos, miembros).
- Atajos documentados (`?`).
- i18n preparada (strings en un `es.json`; catalán/inglés después).
- Página 404/500 con marca; `/docs` de la API protegido o solo en local.

---

## 8. Arquitectura y calidad técnica (plan)

### 8.1 Backend

1. **Capa de servicios**: `services/<dominio>.py` (bands, members, invites, songs, setlists,
   events, finance, messages, catalog) con la lógica que hoy vive en routers (validación de
   reparto, copia profunda, get-or-create, agregados). Routers = parsear, autorizar, llamar,
   serializar. Elimina las 4 copias de `_set_items/_to_response/_valid_*` (B-31).
2. **`active_membership(db, band_id, user_id)` único** con join a `Band.deleted_at` y matriz de
   roles explícita (`can_edit_repertoire`, `can_publish`, `is_admin`) usada por **todas** las
   rutas, incluido `/catalog` (B-01, B-22).
3. **Contrato de fechas UTC** (B-10): columnas `DateTime(timezone=True)`, validador común,
   serialización con `Z`, front con `toISOString()`; test que cruza zonas.
4. **Validación espejo** (B-11): longitudes como constantes compartidas entre `models.py` y
   `schemas.py`; dividir ambos ficheros por dominio.
5. **JWT local** con JWKS de Supabase (`exp`, `aud=authenticated`), caché de claves; Supabase
   remoto solo como fallback ante `kid` desconocido; gracia solo ante error de red (S-09).
6. **Rate limiting y cuotas** (`slowapi` o middleware propio sobre Postgres/KV): `/import/*`,
   `/invites/*`, `/public/*`, `/catalog/*` (S-05).
7. **Importador seguro** (S-04): allowlist de hosts, rechazo de IP privadas tras resolver DNS,
   tope de bytes, sin redirects a otro host, presupuesto de tiempo total (B-20).
8. **Paginación y orden estable** en todos los listados (B-06, B-13, B-14) con `limit/cursor`.
9. **N+1**: `selectinload` de `splits`, `items.song`, contadores por subquery (B-02, B-15).
10. **Índices** compuestos para las consultas reales (B-32) en una migración.
11. **Serverless**: sin `create_all` en PG, `NullPool`, `maxDuration`, estáticos fuera (B-12,
    Q-05, B-20).
12. **Atomicidad**: `UPDATE … WHERE` con `rowcount` en contadores; `FOR UPDATE` en el conteo de
    admins (B-16); `IntegrityError` en get-or-create (B-27).
13. **API limpia**: rutas sin barra final, códigos coherentes (204/404/410), OpenAPI con título,
    `/v1` opcional, respuestas de error documentadas, `/docs` solo fuera de prod (B-24…B-26).
14. **Observabilidad**: `X-Request-ID`, logs JSON a stdout, Sentry, `user_id/band_id` en el log,
    silenciar 4xx en `get_db` (Q-06, B-23).

### 8.2 Frontend (sin cambiar de stack)

1. **Módulos ES** (`<script type="module">`): `core/api.js` (`apiJson()` con `ApiError{status,
   message}`, 401, timeout, `AbortSignal`), `core/session.js` (caché por página de `/config`,
   `/profile/me`, `/bands/`), `ui/dialog.js`, `ui/toast.js`, `ui/menu.js`, `ui/icons.js`,
   `format.js`, `labels.js` (ROLE_LABEL, ATT_LABEL, EVENT_* únicos), `features/<página>.js`.
   `window.*` solo como shim temporal durante la migración.
2. **CSS por capas**: `tokens.css` → `base.css` → `components.css` → `shell.css` →
   `player.css` / `editor.css`. `style.css` desaparece por partes.
3. **Trocear `bands.js`** (1.250 líneas) por feature del espacio de banda manteniendo ids `#b-*`.
4. **Service worker**: lista blanca de cacheable (`/static/*` con `?v=`), purga de hashes
   viejos, `caches.delete` en logout, `visibilitychange` para el polling (F-01, F-21).
5. **Herramientas**: `package.json` con ESLint (flat config), `tsc --checkJs` + JSDoc (typecheck
   sin compilar), Vitest/`node --test` para módulos puros (`parseRawText`, `SyncEngine`,
   `transposeChord`, `freqToNote`, `bfFinanceBySeason`, `format`). Se integra en
   `harness/run_checks.py`.
6. **Cache-busting con ESM**: los `import './x.js'` no llevan `?v=` → generar un **import map**
   desde `cachebust.py` (o pasar a Vite). **Decidir antes de migrar** (D-V6-2).
7. **Opción Vite** (multi-page, salida `static/dist` servida por `StaticFiles`, Supabase como
   dependencia npm sin CDN): hashing y CSS por entrada automáticos, pero Node en el pipeline
   (CI, `doctor.py`, Vercel `npm run build`). Pros/contras en D-V6-2; la guía recomienda
   **empezar sin Vite** (pasos 1–4) y decidir al llegar al paso 5.
8. **Orden de migración que menos rompe** (los e2e localizan por ids): herramientas y bugs
   🔴/🟠 → `util/icons/auth/upload` a ESM con doble export → shell y páginas 100 % bf (app,
   agenda, chat, finanzas) → bands/band/library/setlists/profile/catalogo → reproductor y editor
   al final (joya, más e2e).

### 8.3 Datos y migraciones

1. Corregir `147a6a78da86` (`sa.false()`), job de CI con Postgres: `upgrade head` + `check` +
   `downgrade base` (Q-02, Q-17).
2. Quitar `create_all` en PG; **migración automática en deploy** (workflow: `alembic upgrade
   head` contra el pooler de sesión antes de promover el deployment) (B-12, D-11).
3. **Backups**: `pg_dump` diario por GitHub Action a Storage privado o artefacto; restauración
   probada; runbook de rollback (Vercel instant rollback + `alembic downgrade -1`) (Q-04).
4. `load_dotenv(".env.local", override=True)` o `env.py` leyendo `settings` (B-19).
5. Datos: `Band.currency` expuesto; limpiar columnas muertas en una migración de limpieza cuando
   toque (B-28).

### 8.4 Infra / DevOps

1. **Estáticos fuera de la lambda**: `vercel.json` con `/static/(.*)` a archivos estáticos +
   `Cache-Control: public, max-age=31536000, immutable` para `?v=`; la función solo `/api`-like
   (Q-05).
2. **`maxDuration`** explícito y `runtime.txt`/`requires-python` 3.12 (Q-07, B-20).
3. **Lockfile** (`uv lock` o `pip-compile --generate-hashes`), `requirements-dev` pineado,
   `pip-audit` + Dependabot (Q-07).
4. **CI como gate**: SHA-pin de acciones, `permissions: read`, `concurrency`, jobs separados
   (lint+unit < 3 min / e2e / migraciones PG), artefactos de Playwright y log del servidor en
   fallo, `gitleaks`, branch protection con required check **antes** del auto-deploy (Q-03,
   Q-10).
5. **Entornos**: Supabase staging (D-V6-6) + env de preview en Vercel + smoke post-deploy
   (`/health`, login de cuenta de prueba, una página) (Q-08).
6. **Observabilidad**: Sentry (back y front), UptimeRobot a `/health`, alerta de 5xx (Q-06).
7. **Dominio propio** + HSTS + CSP con nonce (S-08, D-V6-8).
8. **Storage**: revisar políticas del bucket `media` (público en lectura es aceptable para
   avatares; no para recibos futuros) (Q-14).

### 8.5 Tests y verificación

1. **Gate de aislamiento derivado de `app.routes`** (Q-09): para cada ruta con `{band_id}`,
   ajeno → 404/403 **y** dueño → no-404; además **gate de rol**: `guest` → 403 en toda ruta de
   escritura.
2. `acting_as` como fixture en `conftest.py`; SQLite en memoria con `StaticPool`; `pytest-randomly`
   para destapar orden-dependencia; `wipe_*` por test, no compartido.
3. **e2e herméticos**: `page.route` para CDN/fonts (o fuentes autoalojadas), sin `networkidle`
   contra internet; `wait_for_timeout` sustituido por esperas de estado; localizar por ids.
4. **Podar tests de estilo**: `test_design_system` (color exacto), `test_terminologia`,
   `test_tipografia`, `test_ancho`… se convierten en **un** test de reglas del sistema (tokens
   definidos, cero `#hex` fuera de `:root`, cero emoji en `<button>`/nav, `theme.js` en head)
   y en capturas de referencia opcionales (`toHaveScreenshot`) solo de componentes.
5. **Tests de JS puros en Node** (Vitest): motor, parser, transposición, formato, finanzas por
   temporada; `test_js_logic.py` deja de arrancar Chromium.
6. **Axe** por página en e2e (a11y crítica = fallo).
7. **Contrato en Postgres** en CI (truncamientos, `Numeric`, CHECK) (Q-17).
8. Mantener el doctor y `run_checks.py` como "definición de hecho" (ya funcionan).

### 8.6 Documentación y gobernanza

1. **README.md** (10 líneas: qué es, arrancar, probar, desplegar) + **SECURITY.md** +
   **CHANGELOG.md** semántico por release (el REGISTRO sigue como diario, no como changelog).
2. **`docs/adr/`**: una decisión por fichero (auth, multi-tenant, serverless, fechas UTC,
   sistema de diseño, ESM vs Vite). Las guías V1–V4 y `directives/` pasan a `docs/archive/`
   (contienen datos obsoletos: teal, Inter, "ChordFlow", SOP de otro proyecto).
3. **Limpiar datos personales y credenciales** de `REGISTRO`, `TASKS`, `PENDIENTES`, `ROADMAP`
   (S-01, S-02, D-xx) y el ref de Supabase del test (Q-16).
4. **Corregir contradicciones** (§13.D): head de prod, estado de migraciones, `revision.py`
   (o retirar la regla de `CLAUDE.md` que nadie cumple), fechas de "última actualización".
5. `CLAUDE.md`: apuntar a V6 (cómo) + V5 (qué); actualizar el mapa rápido con los módulos
   nuevos (`core/`, `ui/`, `format.js`).

---

## 9. Visión de producto V6: la app que los músicos querrán usar

> Oscar pidió libertad para proponer lo que haga a BandFlow **realmente útil**. Esta sección es
> esa propuesta. Donde cambia algo decidido en la V5 lo marca con una decisión `D-V6-2x` (§11):
> nada se asume sin su visto bueno. Las piezas nuevas tienen tarea en la fase **V6-F9** (§10).

### 9.1 El diagnóstico de producto en tres frases

1. BandFlow ya tiene **casi todas las funciones** de las apps comerciales de bandas (BandHelper,
   OnSong, Set List Maker…): repertorio, setlists, agenda con asistencia, finanzas con reparto,
   chat, teleprompter. No le faltan funciones: le falta **estar organizada alrededor de lo que el
   músico necesita hacer** en vez de alrededor de las tablas de la base de datos.
2. Un músico no quiere "gestionar su banda". Quiere **llegar al bolo preparado, tener la letra y
   los acordes delante, no perder dinero y cuadrar fechas sin 40 mensajes de WhatsApp**.
3. Hoy la app pide demasiado antes de dar algo: cuenta, banda, importar, configurar… y compite con
   WhatsApp en vez de apoyarse en él. **La app gana cuando lo importante funciona sin fricción y
   WhatsApp es la puerta de entrada, no el rival.**

### 9.2 Promesa y posicionamiento

**"Tu banda, lista para tocar."** Tres promesas, en este orden:

1. **En el escenario:** la letra y los acordes que necesitas, en tu tono, con letra grande, sin
   cobertura y sin que nada pueda fallar.
2. **Antes del bolo:** quién viene, qué tocamos, qué nos falta por ensayar y toda la logística en
   una hoja que se comparte por WhatsApp.
3. **Después:** cuentas claras sin discusiones.

Todo lo demás (red de músicos, material, catálogo) es crecimiento posterior, no la promesa.

### 9.3 Principios de producto (los que deciden cuando hay duda)

1. **Dos toques hasta la canción.** Desde cualquier sitio, "Tocar" está a ≤ 2 toques (Inicio →
   próximo bolo → Tocar setlist).
2. **Lo importante funciona sin cuenta.** Ver un evento, un setlist, votar una fecha o aceptar una
   invitación se puede hacer desde un enlace; la cuenta llega cuando el músico quiere participar.
   (Siempre con proyección segura: nada privado en lo público.)
3. **WhatsApp es un aliado.** Cada objeto importante tiene "Compartir por WhatsApp" con un texto
   ya escrito y un enlace que abre algo útil sin registro.
4. **Una banda = un espacio.** La mayoría tendrá una sola banda: la app abre directamente en ella.
   Las vistas agregadas "TÚ" solo aparecen cuando hay dos o más bandas.
5. **Cada miembro ve la canción a su manera.** El cantante quiere letra grande y su tono; el
   guitarrista acordes y cejilla; el batería estructura y tempo. La canción es compartida; la
   **vista** es personal.
6. **El escenario es sagrado.** Modo escenario: offline, pantalla encendida, nada que recargue,
   nada que pida permisos, nada que pueda abrir un diálogo.
7. **Menos pero mejor.** Lo que no sirve a las tres promesas se simplifica o se esconde hasta que
   haya masa crítica (§9.7).

### 9.4 Mapa de la app propuesto (navegación)

**Lateral (contexto personal, cuando hay 2+ bandas):** Inicio · Agenda · Canciones (mis canciones +
mis setlists + carpetas) · Chat · Finanzas · **Bandas** (con sub-ítems) · Perfil. Abajo:
Herramientas (afinador/metrónomo) · tema · salir.

**Con una sola banda:** el lateral muestra directamente el espacio de esa banda (Inicio de banda,
Canciones, Agenda, Chat, Finanzas, Miembros, Ajustes) y "Mis canciones" como ítem; nada de
"TÚ" duplicado. (D-V6-20)

**Espacio de banda: 7 pestañas** (hoy 9): Resumen · Canciones (repertorio + setlists + carpetas
como sub-pestañas) · Agenda · Chat · Finanzas · Miembros · Ajustes. Giras deja de ser pestaña
(§9.7); Setlists vive dentro de Canciones. (D-V6-20)

**Explorar** se apaga en el lateral (bandera de configuración, sin borrar código) hasta que
tenga un imán real: se **enciende con la red profesional** — Salas · Bolos abiertos ·
Profesionales (§9.9, D-V6-27) — y después se añaden las pestañas de la V5 (Músicos, Bandas,
Material, Canciones, Descubrir).

### 9.5 Los diez momentos del músico (y qué hace BandFlow en cada uno)

| # | Momento | Hoy | Propuesta V6 |
|---|---|---|---|
| 1 | **"Me invitan a una banda"** | Enlace → login → unirse (página rota en escritorio) | Enlace → **página pública de la invitación** (logo, nombre, próximo bolo, nº de canciones) → "Unirme" → crear cuenta en 20 s → aterrizas en la banda con el próximo evento y el setlist. Texto de WhatsApp preparado para el admin. (T-V6-80) |
| 2 | **"¿Cuándo ensayamos?"** | Crear evento y preguntar por WhatsApp | **Votación de fechas**: el admin propone 2–4 opciones, se comparte por WhatsApp, cada miembro vota desde el enlace (sin cuenta, con su token), se confirma la mejor → evento + recordatorio. Generaliza las "propuestas" de V5 §9.5. (T-V6-82, D-V6-21) |
| 3 | **"¿Qué tocamos?"** | Setlist = lista de nombres | Setlist con **tono, BPM, duración y total**; "Setlist inteligente" sugiere orden (arranque fuerte, curva de tempo, tonos cercanos) y avisa de dos lentas seguidas. (T-V6-88) |
| 4 | **"Tengo que aprenderme 5 temas"** | Nada | **Semáforo** por canción y miembro (V5 §9.4: pendiente / mejorando / dominada) + "Para el jueves te faltan 2" en Inicio + **modo práctica** en el reproductor: vídeo de referencia por sección, bucle A–B, tempo al 70 %. (T-V6-83, T-V6-87) |
| 5 | **"Ensayo"** | Chat | **Modo ensayo**: desde el evento, lista de lo que toca repasar (semáforo + setlist), cronómetro por canción, grabar 30 s del puente con el móvil, apuntes que van a la pizarra; al acabar, resumen automático al chat. (T-V6-84, T-V6-85, T-V6-92) |
| 6 | **"Día del bolo"** | Evento con campos sueltos | **Hoja del bolo**: carga, prueba, puertas, hora de set, dirección con mapa, contacto, caché, quién lleva qué (checklist con responsable), setlist. Una página imprimible y compartible por WhatsApp. Es el asistente de V5 §10 convertido en el objeto que las bandas ya llevan en notas sueltas. (T-V6-86) |
| 7 | **"En el escenario"** | Reproductor bueno pero con letra cortada en móvil y recargas | Modo escenario definitivo: **mi tono / mi cejilla / mi vista** (letra · acordes · estructura), siguiente canción sin recarga, pedal, offline de la última lista, pantalla encendida, letra grande. (T-V6-81, T-V6-55…57) |
| 8 | **"Hemos cobrado 300 €"** | Finanzas correctas pero frías | Ingreso ligado al bolo → reparto por defecto de la banda → "quién debe a quién" en una línea → **"Liquidar" propone los mínimos pagos** → resumen de temporada ("12 bolos, 2.400 € de caché, 60 € por cabeza al mes de local"). (T-V6-42f, T-V6-93, T-V6-95) |
| 9 | **"Buscamos bajista"** | Nada | V5 §5 (Explorar) cuando haya base de usuarios; mientras, anuncio en la página pública de banda. |
| 10 | **"Se va un miembro"** | Solo lo puede sacar un admin; su saldo se queda colgado | "Salir de la banda" + transferencia de admin + cierre de saldo (liquidación a ex-miembro). (T-V6-42e, B-07) |

### 9.6 Funcionalidades nuevas propuestas (fase V6-F9)

Ordenadas por impacto/esfuerzo. Todas se construyen sobre el sistema de diseño de §6 y respetan
§0.2. Las que tocan modelo llevan migración aditiva.

| Tarea | Esf. | Qué | Por qué importa |
|---|---|---|---|
| **T-V6-80** | M | **Invitación con preview público + compartir por WhatsApp**: `GET /public/invites/{code}` (proyección: nombre, logo, nº miembros, próximo evento público, nº canciones); `join.html` la muestra antes de pedir cuenta; helper `bfShare({title, text, url})` (Web Share API con fallback a `wa.me`) usado en invitación, evento, setlist, hoja del bolo, votación | La invitación pasa de "formulario" a "escaparate": convierte |
| **T-V6-81** | M | **Vista por miembro de la canción**: tabla `song_member_prefs(song_id, user_id, transpose, capo, view_mode, font_scale)`; en el reproductor "Mi tono" (no toca la canción compartida), "Mi vista" (letra · acordes · estructura con compases), tamaño de letra. `Song.key_root` sigue siendo el tono de la banda | Cada músico ve lo suyo; fin de las copias "versión de Ana" |
| **T-V6-82** | L | **Votación de fechas sin cuenta**: `date_polls`, `date_poll_options`, `date_poll_votes(member_id, token)`; crear desde Agenda de banda; página pública `votar.html?t=` con los nombres de los miembros y botones Sí/Quizás/No por opción; "Confirmar" convierte la opción en evento con asistencias ya rellenas. Una propuesta de V5 §9.5 = votación con una sola opción | Resuelve el dolor nº 1 de cualquier banda |
| **T-V6-83** | M | **Semáforo del repertorio** (V5 `SongStatus`): marcador por canción en Repertorio, diagrama en Resumen, "te faltan N para {evento}" en Inicio | Motiva y hace útil el repertorio |
| **T-V6-84** | L | **Modo ensayo**: desde un evento `rehearsal` → "Empezar ensayo": lista (canciones del setlist del próximo bolo primero, luego las `mejorando`), cronómetro por canción, botón "Apunte" (→ pizarra), botón "Grabar" (→ adjunto de la canción), "Tocar" abre el reproductor; al terminar: resumen (qué se tocó, apuntes, grabaciones) publicado en el chat | Convierte el ensayo en progreso visible |
| **T-V6-85** | L | **Adjuntos y grabadora**: tabla `attachments(id, owner_id, band_id, song_id?, event_id?, kind audio/pdf/image, storage_path, title, duration_sec, created_at)`; subida vía `upload.js` (Storage ya configurado, políticas por banda); grabadora con `MediaRecorder` en móvil; **PDF de partitura por canción** visible en el reproductor (muchas bandas ya tienen sus PDFs: sin esto no migran) | Quita la barrera "ya tengo mis PDFs" |
| **T-V6-86** | M | **Hoja del bolo**: campos en `events` (`load_in_at`, `soundcheck_at`, `doors_at`, `set_at`, `address`, `parking_notes`, `backline_notes`) + `event_checklist_items(event_id, text, assignee_id, done_at, due_date)`; página `bolo.html?t=` con token de solo lectura, imprimible; "Compartir por WhatsApp". Es V5 §10 sin asistente: primero el objeto, el asistente después | Lo que hoy va en notas sueltas |
| **T-V6-87** | M | **Modo práctica** en el reproductor: `sections.ref_start_sec` (marca de tiempo del vídeo de referencia por sección), bucle A–B por secciones, tempo al 50–100 % (`tempoMultiplier` ya existe en el motor), cuenta atrás; no toca el motor | El músico aprende con la app, no solo la usa en el bolo |
| **T-V6-88** | S | **Setlist inteligente**: `Song.duration_sec` (editable; estimado si falta), total del setlist, sugerencia de orden en cliente (energía por BPM, cercanía de tonos, alternancia), avisos ("3 canciones en Mi seguidas") | Diferenciador barato |
| **T-V6-89** | M | **Recordatorios con respuesta**: email 24 h antes con botones Voy / No voy (enlace con token de un solo uso) y resumen a los admins "faltan 2 por responder" | Asistencia sin perseguir a nadie |
| **T-V6-90** | M | **Una banda = inicio en la banda** (D-V6-20): si el usuario tiene 1 banda, Inicio es el Resumen de la banda y el lateral muestra sus pestañas; las vistas TÚ aparecen con ≥ 2 bandas; Giras → agrupación en Agenda; Setlists dentro de Canciones; Explorar tras bandera | Menos pantallas vacías, menos confusión |
| **T-V6-91** | S | **Importar desde texto de WhatsApp/PDF**: pegar texto (ya hay parser), extraer texto de un PDF en cliente (`pdf.js`), modo "solo letra" para cantantes | Entrar con lo que ya tienen |
| **T-V6-92** | M | **Pizarra de banda** (V5 §9.3 `BandNote`) adelantada: pendientes con responsable, fecha opcional (→ agenda), fijar, hecho; widget en Resumen | La necesitan el modo ensayo y la hoja del bolo |
| **T-V6-93** | S | **Resumen de temporada**: bolos, caché total, gasto por cabeza, canciones más tocadas (de setlists de conciertos `done`), gráfico simple; compartible como imagen | Retención y orgullo de banda |
| **T-V6-94** | S | **Feedback in-app**: botón "¿Algo falla?" (captura de pantalla opcional + texto → tabla `feedback` + email a Oscar) | Oír a los músicos desde el día 1 |
| **T-V6-95** | S | **Gastos recurrentes**: plantilla de movimiento (local mensual) con reparto por defecto de la banda; recordatorio mensual | El 80 % de los gastos de una banda |

### 9.7 Lo que se simplifica o se esconde (y por qué)

| Qué | Hoy | Propuesta | Decisión |
|---|---|---|---|
| Giras | Pestaña propia con modelo completo | Pasa a ser una **agrupación de conciertos en Agenda** ("Añadir a gira") con el presupuesto en la hoja de cada bolo; el modelo `Tour` se conserva | D-V6-22 |
| Explorar / catálogo | Ítem del lateral; toda canción nueva se publica sola | Oculto tras bandera hasta que llegue la red profesional (§9.9), que es el imán; publicar es opt-out visible (D-V6-3); las pestañas de la V5 se añaden después | D-V6-23 → D-V6-27 |
| Afinador / Metrónomo | Segundo ítem del lateral | "Herramientas" al final del lateral + acceso desde el reproductor (ya existe) | D-V6-24 |
| Colecciones personales | Concepto paralelo a setlists | Se convierten en **carpetas** (V5 §6, ya decidido) | — |
| Vistas TÚ con 1 banda | Agenda/Finanzas/Chat casi vacías | Solo con 2+ bandas; con 1 banda, la app ES la banda | D-V6-20 |
| Pestañas del espacio de banda | 9 | 7 (Canciones agrupa repertorio + setlists + carpetas) | D-V6-20 |
| Rol `guest` | Existe sin pantalla | Se mantiene (útil para técnicos/sustitutos: ven setlists y agenda, no editan) | — |

### 9.8 Cómo sabremos que funciona (métricas desde el día 1)

- **Activación**: % de bandas nuevas que en 7 días tienen ≥ 3 miembros, ≥ 5 canciones y 1 evento.
- **Tiempo hasta la primera canción** tocada en el reproductor: objetivo < 3 minutos desde el registro.
- **Asistencia respondida**: % de eventos con todas las respuestas 48 h antes.
- **Uso en escenario**: % de conciertos `done` en los que se abrió el modo escenario.
- **Retención a 30 días** por banda (no por usuario).
- **Feedback**: nº de "¿Algo falla?" por semana y tiempo de respuesta.

Implementación mínima: eventos de producto en una tabla `product_events(user_id, band_id, kind,
created_at)` y una consulta semanal; nada de terceros al principio.

### 9.9 Red profesional: salas, convocatorias de bolos y profesionales (idea de Oscar, 2026-11-05)

**La idea:** un espacio donde los **bares y salas que buscan bandas**, los **bookers y managers**
y todos los **profesionales que un músico necesita** (fotógrafos, vídeo, técnicos de sonido y
luces, estudios de grabación, locales de ensayo, luthiers y reparación, diseño/merch, prensa y
promo, profesores) tengan perfil y se pueda contactar con ellos desde la app.

**Por qué es la pieza que faltaba:** la red de la V5 (§5: Músicos · Bandas · Material · Canciones
· Descubrir) conecta músicos entre sí, pero **el imán que atrae a las bandas son los bolos**. Si
las salas publican fechas, las bandas entran a buscarlas; si las bandas están, los profesionales
quieren estar. Es el efecto red que le faltaba a Explorar — y la vía de monetización más natural
(§9.9.6).

#### 9.9.1 Actores y tipos de cuenta

Una misma cuenta puede tener varios **perfiles**: músico (ya existe), banda (ya existe), **sala**
y **profesional**. No se crean "tipos de usuario" distintos: se añaden perfiles sobre el mismo
`user_id`, y Explorar lista perfiles, no usuarios.

| Perfil | Quién | Qué publica | Qué busca |
|---|---|---|---|
| **Sala / local** | bares, salas de conciertos, festivales, salas de ensayo que programan | ficha (aforo, estilo, equipo/backline, condiciones habituales: caché / taquilla / porcentaje / gratis+consumo), fotos, zona; **convocatorias** ("buscamos banda de versiones para el 20/12, 2×45 min, 300 € + cena") | bandas |
| **Booker / manager** | quien programa o representa | ficha (zonas, estilos, salas con las que trabaja, bandas que representa — opcional) | bandas y salas |
| **Profesional** | fotógrafo, vídeo, técnico de sonido/luces, estudio, local de ensayo, luthier, diseño/merch, prensa, profesor | ficha por **categoría** con servicios, tarifas orientativas, zona, portfolio (enlaces/fotos), disponibilidad | bandas y músicos |
| **Banda** (ya existe) | | **EPK mínimo**: bio, fotos, 1–3 enlaces (vídeo, Spotify), estilos, zona, formato (dúo/trío/banda), caché orientativo, rider básico (V3-F8 lo contemplaba) | bolos y servicios |

#### 9.9.2 Flujos nuevos (interconexiones, estilo V5 §14)

- **I-20 · Convocatoria → bolo.** La sala publica una convocatoria (fecha o rango, estilo,
  formato, condiciones, fecha límite) → aparece en Explorar > **Bolos abiertos** (y en el Inicio
  de las bandas que encajen por zona/estilo) → la banda **se postula** con su EPK y un mensaje →
  la sala ve las candidaturas en un tablero, abre DM (I-3) → al **elegir** una, se crea el
  `Event(type=concert)` en la agenda de la banda con el pipeline de booking ya existente
  (`lead → … → confirmed`) y la sala queda enlazada (`Venue` global ↔ `Event.venue_id`). Las
  demás candidaturas reciben un "esta vez no" automático. Test de flujo completo.
- **I-21 · Banda → sala (sin convocatoria).** Desde la ficha de una sala: "Proponernos" → DM con
  contexto (`context_ref: {kind:'venue'}`) + EPK adjunto. La sala puede marcar "interesados" para
  futuras fechas.
- **I-22 · Profesional ↔ banda.** "Contactar" desde la ficha (I-3) con contexto del servicio;
  tras un trabajo, **valoración mutua** (1–5 + comentario corto) visible en la ficha. Las
  valoraciones solo se pueden dejar si hubo un DM/evento entre ambos (anti-spam).
- **I-23 · Sala ↔ agenda.** La sala tiene **su propio calendario** (fechas programadas, libres,
  convocatorias); un bolo confirmado aparece en la agenda de la banda y en la de la sala. Es el
  mismo componente `bf-calendar`.
- **I-24 · Directorio local.** Todo se filtra por **zona** (texto libre, D-EXP-3) y por categoría;
  orden por actividad reciente; la ficha enlaza a la página pública (sala/profesional) sin login,
  igual que `evento.html` y la página pública de banda (I-16).

#### 9.9.3 Dónde vive en la app

Explorar pasa a tener dos grupos de pestañas (D-V6-27):

- **Personas y sitios:** Músicos · Bandas · **Salas** · **Profesionales** · **Bolos abiertos**
- **Música y material:** Canciones · Descubrir · Material

Y en el espacio de banda: pestaña **Agenda → "Buscar bolo"** (atajo a Bolos abiertos filtrado por
la zona de la banda) y en Ajustes el **EPK** de la banda (lo que ven salas y profesionales).

**Secuencia de lanzamiento recomendada (cambia D-V6-23):** Explorar se enciende **primero con
Salas + Bolos abiertos + Profesionales** (el imán) y las pestañas de la V5 se añaden después.
Sin salas no hay razón para entrar en Explorar; con 20 salas de una ciudad, sí.

#### 9.9.4 Modelo de datos (aditivo, migraciones separadas)

- `pro_profiles(id, user_id, kind ∈ {venue, booker, photographer, video, sound_tech, light_tech,
  studio, rehearsal_room, luthier, design, press, teacher, other}, name, bio, zone, services JSON,
  price_hint, links JSON, photos JSON, phone, whatsapp_optin, visibility, verified_at, created_at,
  updated_at)` — un usuario puede tener varios (una sala y un técnico, por ejemplo).
- `venue_profiles(pro_profile_id PK/FK, capacity, styles JSON, backline JSON, deal_types JSON
  ∈ {fee, door, percent, free}, typical_fee, address, city, map_url, opening_notes)`.
- `gig_calls(id, venue_profile_id, title, starts_at, ends_at?, flexible_dates bool, styles JSON,
  format, deal_type, fee, conditions, deadline_at, status ∈ {open, closed, filled}, created_at)`.
- `gig_applications(id, gig_call_id, band_id, message, epk_snapshot JSON, status ∈ {sent, seen,
  shortlisted, chosen, declined}, created_at)` — única por (call, band).
- `band_epk(band_id PK, bio, styles JSON, formation, zone, links JSON, photos JSON, fee_hint,
  rider_notes, updated_at)`.
- `reviews(id, from_user_id, to_pro_profile_id?, to_band_id?, stars, body, event_id?, created_at)`
  con regla anti-spam (relación previa obligatoria).
- Reutiliza: DM (`context_ref` con `kind: 'venue' | 'pro' | 'gig_call'`), `Event` + pipeline de
  booking, `Venue` (la sala global enlaza a la `Venue` privada de cada banda al confirmar), zona
  texto libre, proyección segura y tests de no-fuga (teléfono jamás en listados).

#### 9.9.5 Confianza y moderación (obligatorio antes de abrir)

Verificación ligera de salas (badge "verificada" tras comprobar web/teléfono por Oscar al
principio; después, por documento), reportar perfil/convocatoria, ocultar/retirar (estados ya
previstos en el catálogo), valoraciones solo con relación previa, aviso legal "BandFlow conecta,
no intermedia pagos" (mismo texto que Material, V5 §5.4), y límite de contactos diarios por
perfil nuevo (anti-spam).

#### 9.9.6 Monetización (más adelante, pero diseñada desde ahora)

Las salas y profesionales son quienes pueden pagar: **convocatoria destacada**, **perfil
destacado por zona**, y a medio plazo un **plan Sala** (calendario, convocatorias ilimitadas,
candidaturas con EPK). Las bandas y músicos siguen gratis (la base del efecto red). `Band.plan`
y la tabla de perfiles llevan el campo `plan` desde el principio, sin cobrar (D-V6-28).

#### 9.9.7 Tareas (F9b, después de T-V6-80..90 y de la pestaña Bandas de V5 o en paralelo)

| Tarea | Esf. | Qué |
|---|---|---|
| **T-V6-96** | L | Perfiles profesionales y de sala: modelo + router owner-scoped + fichas públicas (`sala.html?id=`, `pro.html?id=`) + alta desde Perfil ("Añadir perfil de sala / profesional") + Explorar > Salas y Profesionales con filtros (categoría, zona) + test de no-fuga |
| **T-V6-97** | L | Convocatorias y candidaturas: `gig_calls` + `gig_applications` + Explorar > Bolos abiertos + tablero de candidaturas de la sala + "Postularnos" desde la banda con EPK + elegir → evento (I-20) + flujo e2e completo |
| **T-V6-98** | M | EPK de banda en Ajustes + página pública de banda ampliada (V5 I-16) + "Proponernos" a una sala (I-21) |
| **T-V6-99** | M | Valoraciones mutuas con relación previa (I-22), reportar, verificación de salas, límites anti-spam |
| **T-V6-100** | S | Calendario de sala (`bf-calendar` sobre convocatorias + bolos confirmados) (I-23) |

### 9.10 Orden recomendado dentro de F9

1. T-V6-90 (navegación y "una banda") — reordena todo lo demás.
2. T-V6-80 (invitación pública + compartir) — crecimiento.
3. T-V6-82 (votación de fechas) + T-V6-89 (recordatorios) — el dolor nº 1.
4. T-V6-81 (vista por miembro) + T-V6-88 (setlist inteligente) — el escenario.
5. T-V6-85 (adjuntos/PDF/grabadora) — migración de bandas con PDFs.
6. T-V6-83 + T-V6-92 + T-V6-84 (semáforo, pizarra, modo ensayo).
7. T-V6-86 (hoja del bolo), T-V6-87 (práctica), T-V6-91, T-V6-93, T-V6-94, T-V6-95.
8. **F9b (red profesional, §9.9):** T-V6-96 → T-V6-97 → T-V6-98 → T-V6-99 → T-V6-100. Puede
   arrancar en paralelo con los puntos 5–7 si hay dos IAs; necesita D-V6-27/28 cerradas y el DM
   base de la V5 (T-V5-21) hecho.

---

## 10. Hoja de ruta V6 (fases, tareas, esfuerzo, criterio de hecho)

> Orden pensado para que **cada fase deje la app mejor y desplegable**. Las tareas se abren como
> `T-V6-NN` en `harness/ROADMAP.md`/`TASKS.md` con el bucle de oro. "Hecho" = doctor verde +
> test que cubre el cambio + revisión en los dos temas y en móvil (captura en el registro).
> Esfuerzo: S ≤ ½ día · M 1–2 días · L 3–5 días.

### V6-F0 · Emergencia de seguridad y bugs críticos (≈ 1 semana)

| Tarea | Esf. | Qué | Cierra |
|---|---|---|---|
| **T-V6-01** | S | Borrar credenciales de `REGISTRO`, `TASKS`, `PENDIENTES`; `git filter-repo`; `gitleaks` en CI + pre-commit. *Requiere que Oscar haya rotado antes (§2.1)* | S-01, S-02 |
| **T-V6-02** | S | Cerrojo de `TEST_MODE` fuera de SQLite/CI; `conftest.py` fuerza `DATABASE_URL` sqlite y aborta si no | S-03, Q-01 |
| **T-V6-03** | S | `sw.js`: cache-first solo `/static/*?v=`; purga de hashes viejos; `caches.delete` en logout; test e2e de colección creada → visible tras recarga | F-01, F-21 |
| **T-V6-04** | S | Modales y toasts con tokens (`--bf-surface`, texto, borde); escala de z-index; errores de validación inline en el modal | F-02, F-04 |
| **T-V6-05** | S | `/catalog/publish` e `/import` con `require_band_member` + `_deny_guests`; tests `guest → 403` | B-01 |
| **T-V6-06** | M | Importador seguro: allowlist de hosts, bloqueo de IP privadas, tope de bytes, sin redirect cross-host, presupuesto de tiempo; rate limit básico en `/import/*` | S-04, S-05, B-20 |
| **T-V6-07** | S | `reference_url` solo `https?://` (servidor y cliente) | S-06 |
| **T-V6-08** | S | Invitaciones: caducidad 7 días / 20 usos por defecto; `DELETE /bands/{id}/invites/{iid}`; `used_count` atómico | S-07, B-16 (parte) |
| **T-V6-09** | M | **Parche móvil urgente** (CSS, antes del rediseño): filas de agenda de banda apilan acciones en < 768 px; letra del reproductor con wrap; `join.html` centrado; composer del chat de 40 px; acciones de tarjeta visibles con `hover:none` | V-01…V-04, F-08 |

### V6-F1 · Bugs altos y deuda que bloquea (≈ 1,5 semanas)

| Tarea | Esf. | Qué | Cierra |
|---|---|---|---|
| **T-V6-10** | M | Chat de banda: render diferencial por id, auto-scroll inteligente, pausa con `visibilitychange`, `?after=&limit=` en la API | F-03, B-13 |
| **T-V6-11** | S | `/songs/` con `ORDER BY updated_at` + paginación; "Cargar más" en Biblioteca | B-06 |
| **T-V6-12** | S | `selectinload(Transaction.splits)` ×3; contadores por subquery en listados; `selectinload(SetlistItem.song)` | B-02, B-15 |
| **T-V6-13** | S | `create_all` solo en SQLite; `NullPool`/pool mínimo en Vercel; `maxDuration`; `runtime.txt` 3.12 | B-12, Q-07 (parte) |
| **T-V6-14** | S | `theme.js` inline en `<head>` de las 16 páginas; `100dvh` | F-20, F-14 |
| **T-V6-15** | M | `core/api.js`: `apiJson()` + `ApiError` + mensajes en castellano; estado de error ≠ vacío en todas las listas; botones con `is-loading` y anti doble envío | F-07, F-15, F-28 |
| **T-V6-16** | S | Editor: flag `dirty` + `beforeunload`; checkbox "Compartir en Explorar" + aviso de derechos (según D-V6-3) | F-06, F-18 |
| **T-V6-17** | S | Espacio no toca el BPM con foco en +/−; metrónomo con scheduler *lookahead* | F-12, F-11 |
| **T-V6-18** | M | Contrato de fechas UTC de punta a punta (columnas tz-aware o `Z` en serialización, validador común, `toISOString()` en el front, test cruzando zonas) | B-10 |
| **T-V6-19** | M | Lote backend medio: `active_membership()` único con `Band.deleted_at`; liquidaciones a ex-miembros; `reference_url` al copiar; búsqueda por `norm_*`; `plan` fuera del PATCH; `load_dotenv(override=True)`; longitudes espejo + test en PG; `IntegrityError` en perfil; `except HTTPException: raise` en `get_db` | B-07, B-08, B-09, B-11, B-19, B-21, B-22, B-23, B-27 |

### V6-F2 · Base técnica mínima (≈ 2 semanas)

| Tarea | Esf. | Qué | Cierra |
|---|---|---|---|
| **T-V6-21** | M | CI como gate: SHA-pin, `permissions`, `concurrency`, jobs lint+unit / e2e / migraciones-PG, artefactos en fallo, branch protection con required check antes del auto-deploy | Q-03, Q-10 |
| **T-V6-22** | S | Lockfile con hashes, `requirements-dev` pineado, `pip-audit`, Dependabot, `.gitignore` `.env.*` | Q-07, Q-13 |
| **T-V6-23** | M | Migración `147a6a78da86` válida en PG; job CI con Postgres (`upgrade head` + `check` + `downgrade base`) | Q-02, Q-17 |
| **T-V6-24** | M | Estáticos servidos por Vercel con `Cache-Control: immutable`; la función solo para la API; medir cold start antes/después | Q-05 |
| **T-V6-25** | M | Tooling JS: `package.json`, ESLint, `tsc --checkJs` + JSDoc, Vitest para módulos puros; integrado en `run_checks.py`; `test_js_logic.py` deja de usar Chromium | F-25 (parte), Q-11 (parte) |
| **T-V6-26** | M | ESM `core/` y `ui/` con doble export (`window.*` shim): `api`, `session`, `dialog`, `toast`, `menu`, `format`, `labels`; import map generado por `cachebust.py` (D-V6-2) | F-23, F-24, F-26, F-36 |
| **T-V6-27** | M | Gate de aislamiento derivado de `app.routes` (+ dueño no-404) y gate de rol `guest`; `acting_as` fixture; SQLite en memoria; `pytest-randomly`; e2e herméticos (`page.route` CDN) | Q-09, Q-11 |
| **T-V6-28** | M | JWT local con JWKS (`exp`, `aud`), gracia solo ante error de red; Supabase remoto como fallback | S-09 |
| **T-V6-29** | S | `X-Request-ID`, logs JSON a stdout, Sentry back+front (DSN de Oscar), UptimeRobot a `/health`, silenciar 4xx en `get_db` | Q-06 |
| **T-V6-30** | S | README, SECURITY, CHANGELOG; `docs/archive/` para V1–V4 y `directives/`; limpiar emails/refs de docs y test; corregir contradicciones de §13.D; `CLAUDE.md` apunta a V6+V5 | §8.6, D-01…D-11, Q-16 |

### V6-F3 · Sistema de diseño 2.0 (≈ 2 semanas) — sin tocar ids de tests

| Tarea | Esf. | Qué | Cierra |
|---|---|---|---|
| **T-V6-31** | M | Tokens nuevos (§6.2), fuentes autoalojadas, escala tipográfica cerrada, quitar Inter/Roboto y los `@import` duplicados | F-32, §5.1.7 |
| **T-V6-32** | L | Componentes canónicos (§6.3): botón unificado (legacy → `bf-btn`), icon-btn, segmented, menú ⋯, fila, tarjeta, campo/input/select/textarea, buscador, pestañas, badge, chip, avatar con color estable, toast, empty/error, cabecera de página, topbar móvil con título, KPI, importe, fecha. Página de muestra `static/_components.html` (fuera de nav) para revisarlos en los dos temas | §5.1.2, §5.1.3, §5.1.9 |
| **T-V6-33** | M | `bfDialog()` único (focus trap, Escape, foco de vuelta, hoja inferior en móvil) y migración de los 9 modales; `confirm()` con foco en Cancelar; "Deshacer" en quitar de setlist | F-17, F-10, F-38 |
| **T-V6-34** | M | Barrido emoji → `bfIcon` completo (§13.A) + test "cero emoji en `<button>`, nav, `h1-h3`, placeholders" | §5.1.1 |
| **T-V6-35** | M | Tema claro completo: eliminar `#hex`/`rgba` fuera de `:root` (54 + 110 en `style.css`, 6 en JS), tokens inexistentes, `.bf-badge` sin `capitalize`; check automático en CI | F-09, F-29, F-30, F-31 |
| **T-V6-36** | S | `format.js` (`Intl` dinero/fechas) y `labels.js` únicos aplicados en todas las páginas | F-23, F-24 |
| **T-V6-37** | M | Retirar `style.css` por partes → `components.css` + `player.css` + `editor.css`; cero `style=""` inline en plantillas (utilidades `.bf-stack--*`) | §5.1.11, §8.2.2 |

### V6-F4 · Páginas (≈ 3 semanas) — orden por impacto

| Tarea | Esf. | Página | Referencia |
|---|---|---|---|
| **T-V6-40** | M | Login (dos columnas, pestañas Entrar/Crear, Google oficial, mostrar contraseña) + `reset.html` + Términos/Privacidad | §5.3, §7.1 |
| **T-V6-41** | S | Join (tarjeta centrada, estados inválida/caducada, login conservando código) | §5.3 |
| **T-V6-42a** | S | Espacio de banda: cabecera con cover, pestañas con contador + hash, onboarding una sola vez (persistido en perfil) | F-13, §5.3 |
| **T-V6-42b** | M | Agenda de banda: filas 56 px + segmented + ⋯ + panel de detalle (`bf-drawer`); Salas a Ajustes | V-01, §5.3 |
| **T-V6-42c** | M | Chat de banda: agrupación, avatar, hora, fijados colapsables, composer, editar propio | V-04, §5.3 |
| **T-V6-42d** | M | Repertorio + Setlists de banda: "Añadir canción" con menú, meta tono/BPM/capo, ⋯, orden, tarjetas de setlist con duración | §5.3 |
| **T-V6-42e** | M | Miembros + Invitaciones (lista, revocar, copiar) + Salir de la banda + transferir admin | B-29, S-07, §7.3 |
| **T-V6-42f** | M | Finanzas de banda: `Intl`, quién pagó, filtros, liquidaciones listadas/borrables, gráfico por mes | §5.3, §7.6 |
| **T-V6-42g** | S | Giras: tarjeta + timeline + editar/borrar | §5.3 |
| **T-V6-43** | M | Inicio: KPIs, "Esta semana" con asistencia in-page, actividad, "Para hoy", vacío sin banda | §5.3 |
| **T-V6-44** | M | Mis bandas: tarjetas con cover y miembros apilados; "Unirme con código"; vacío ilustrado | §5.3 |
| **T-V6-45** | M | Biblioteca + Setlists personales: chips, grid/lista, meta, ⋯ visible en móvil, orden, cargar más | §5.3 |
| **T-V6-46** | M | Editor: metadatos completos, diálogo "Importar" con 3 pestañas, barra inferior fija, Ctrl+S, preview alineada | §5.3 |
| **T-V6-47** | M | Agenda TÚ: lista agrupada por semana, crear evento eligiendo banda, filtros (calendario en F6) | §5.3 |
| **T-V6-48** | S | Finanzas TÚ: resumen global + movimientos + liquidar | §5.3 |
| **T-V6-49** | M | Chat TÚ: dos columnas + no-leídos en lateral (`.bf-nav-badge`) | §5.3 |
| **T-V6-50** | M | Perfil + Cuenta (chips de instrumentos, cambiar email/contraseña, cerrar sesiones, tema, idioma) | §7.1 |
| **T-V6-51** | S | Afinador/Metrónomo: centrado, nota en reposo, presets | §5.3 |
| **T-V6-52** | S | Explorar provisional (tarjetas, abort/debounce, paginación) + evento público (cover, .ics, compartir) | F-27, §5.3 |

### V6-F5 · Móvil y reproductor (≈ 1,5 semanas)

| Tarea | Esf. | Qué | Cierra |
|---|---|---|---|
| **T-V6-55** | M | Reproductor: toolbar compacta (popovers BPM/tono en móvil, menú ⋯), tamaño de letra A−/A+, sección actual + navegación, cuenta atrás etiquetada, tempo por usuario (D-V6-9) | §5.3, F-33 |
| **T-V6-56** | M | Modo setlist in-page ("Siguiente: …", prefetch) + parada al final con test. **Únicas excepciones al motor**, con plan en TASKS | F-19, F-34 |
| **T-V6-57** | S | `wakeLock`, offline de última canción/setlist (IndexedDB), `manifest.json` actualizado, icono coral | F-22, §7.9 |
| **T-V6-58** | M | Pasada móvil: test de overflow horizontal en las 16 páginas a 390 px, hojas inferiores, topbar con título, pestañas con desvanecido | §6.8 |
| **T-V6-59** | M | Accesibilidad: tarjetas/filas por teclado, `aria-*` en pestañas y menús, labels reales, `axe` por página en e2e | F-16, F-40, §6.9 |

### V6-F6 · Funcionalidades que faltan (≈ 2,5 semanas)

| Tarea | Esf. | Qué | Referencia |
|---|---|---|---|
| **T-V6-60** | M | Email transaccional (Edge Function + proveedor D-V6-7): invitación aceptada, evento nuevo/cambiado, recordatorio 24 h, movimiento que te afecta; preferencias por tipo | §7.8 |
| **T-V6-61** | M | Centro de notificaciones in-app (tabla + campana) y no-leídos de chat | §7.8 |
| **T-V6-62** | M | `bf-calendar` (mensual + semanal, contrato V5 §7) en Agenda TÚ, banda y Resumen; `.ics` por evento y suscripción por banda | §7.5 |
| **T-V6-63** | M | Exportar/imprimir setlist (PDF orden + notas; pack con canciones) y compartir setlist por enlace de solo lectura | §7.4 |
| **T-V6-64** | M | Onboarding: sin banda (dos caminos + canción demo), asistente de banda de 3 pasos, tour de 4 puntos | §7.2 |
| **T-V6-65** | M | Borrar cuenta (con transferencia de admin) + exportar mis datos; verificación de email; emails de auth con marca | §7.1 |
| **T-V6-66** | S | Moderación del catálogo (ocultar/retirar, borrar comentario), reportar, aviso de derechos | §7.11, B-28 |
| **T-V6-67** | S | Búsqueda global Ctrl+K y hoja de atajos `?` | §7.14 |
| **T-V6-68** | S | Landing pública en `/` y páginas 404/500 con marca (D-V6-11) | §7.12 |

### V6-F7 · Infra y operación (≈ 1,5 semanas, en paralelo con F4–F6 cuando se pueda)

| Tarea | Esf. | Qué | Cierra |
|---|---|---|---|
| **T-V6-70** | M | Staging (Supabase + env de preview en Vercel) + smoke post-deploy | Q-08 |
| **T-V6-71** | M | Migración automática en el pipeline de deploy (contra el pooler de sesión, antes de promover) | D-11, §8.3 |
| **T-V6-72** | S | Backups `pg_dump` diarios + restauración probada + runbook de rollback | Q-04 |
| **T-V6-73** | S | Dominio propio + HSTS + CSP con nonce (sin `onclick` inline) | S-08 |
| **T-V6-74** | S | Rate limiting completo (`/invites`, `/public`, `/catalog`) + cuota diaria de IA por usuario | S-05 |
| **T-V6-75** | S | Índices compuestos reales + migración de limpieza de columnas muertas | B-32, B-28 |

### V6-F9 · Producto: lo que hará que los músicos la quieran (≈ 4 semanas; se ejecuta ANTES de F8, intercalada con F6)

> Detalle, razones y orden interno en §9. Esfuerzos: 80 M · 81 M · 82 L · 83 M · 84 L · 85 L ·
> 86 M · 87 M · 88 S · 89 M · 90 M · 91 S · 92 M · 93 S · 94 S · 95 S.

| Tarea | Qué | Depende de |
|---|---|---|
| **T-V6-90** | Una banda = inicio en la banda; 7 pestañas; Giras → agrupación; Explorar tras bandera | D-V6-20, T-V6-42a |
| **T-V6-80** | Invitación con preview público + `bfShare` (WhatsApp) en invitación/evento/setlist/hoja/votación | T-V6-41 |
| **T-V6-82** | Votación de fechas sin cuenta (`date_polls`) → evento | D-V6-21, T-V6-62 (calendario, opcional) |
| **T-V6-89** | Recordatorios 24 h con respuesta por enlace | T-V6-60 |
| **T-V6-81** | Vista por miembro: mi tono / mi cejilla / mi vista / tamaño | T-V6-55 |
| **T-V6-88** | Setlist inteligente + duración | T-V6-42d |
| **T-V6-85** | Adjuntos (PDF de partitura, audio, imagen) + grabadora | Storage (ya listo) |
| **T-V6-83** | Semáforo del repertorio (`SongStatus`) + "te faltan N" | T-V6-42d |
| **T-V6-92** | Pizarra de banda (`BandNote`) | T-V6-42a |
| **T-V6-84** | Modo ensayo | T-V6-83, T-V6-85, T-V6-92 |
| **T-V6-86** | Hoja del bolo (campos + checklist + página pública imprimible) | T-V6-42b, T-V6-80 |
| **T-V6-87** | Modo práctica (referencia por sección, bucle, tempo %) | T-V6-55 |
| **T-V6-91** | Importar desde texto de WhatsApp / PDF; modo solo letra | T-V6-46 |
| **T-V6-93** | Resumen de temporada | T-V6-42f |
| **T-V6-94** | Feedback in-app + eventos de producto (`product_events`) | — |
| **T-V6-95** | Gastos recurrentes con reparto por defecto | T-V6-42f |
| **T-V6-96** | Red profesional (§9.9): perfiles de sala y profesional + fichas públicas + Explorar > Salas / Profesionales | D-V6-27, DM base V5 (T-V5-21) |
| **T-V6-97** | Convocatorias de bolos y candidaturas (I-20) → evento en la agenda | T-V6-96, T-V6-98 |
| **T-V6-98** | EPK de banda + página pública ampliada + "Proponernos" (I-21) | T-V6-96 |
| **T-V6-99** | Valoraciones mutuas, reportar, verificación, anti-spam (I-22) | T-V6-97 |
| **T-V6-100** | Calendario de sala (I-23) | T-V6-62, T-V6-97 |

### V6-F8 · Retomar la V5 (F4 → F11) sobre la base nueva

Explorar 5 pestañas, Mi material, Chat 2.0, Biblioteca por carpetas, Bandas 2.0 (pizarra,
estado de repertorio, propuestas), Conciertos, Finanzas integral — **sin cambios de alcance**,
usando los componentes de §6.3 y las reglas de §0.2. Cada sección de la V5 gana su
"criterio de hecho" visual (dos temas + móvil + axe).

### Resumen

| Fase | Semanas | Resultado visible |
|---|---|---|
| F0 | 1 | Sin secretos, sin bugs críticos, móvil usable |
| F1 | 1,5 | App estable: chat, fechas, errores, listas |
| F2 | 2 | CI gate, tooling JS, módulos, JWT local, Sentry, README |
| F3 | 2 | Un solo sistema visual; cero emoji; tema claro completo |
| F4 | 3 | Todas las páginas rediseñadas |
| F5 | 1,5 | Reproductor y móvil a nivel de app nativa |
| F6 | 2,5 | Cuenta, notificaciones, calendario, exportar, onboarding |
| F7 | 1,5 | Staging, backups, migraciones automáticas, dominio |
| F9 | 4 | Invitación pública, votación de fechas, vista por miembro, PDF/grabadora, semáforo, modo ensayo, hoja del bolo |
| F9b | 3 | Red profesional: salas, convocatorias de bolos, profesionales, EPK, valoraciones (§9.9) |
| **Total** | **≈ 22 semanas-persona** (≈ 12–14 de calendario con front y back en paralelo) | |

---

## 11. Decisiones abiertas para Oscar (D-V6-*)

> Regla 8 de §0.2: cada decisión bloquea solo lo que lista. Recomendación en negrita.

| ID | Decisión | Opciones | Bloquea exactamente |
|---|---|---|---|
| **D-V6-1** | ¿Pausar la V5 (F4+) hasta cerrar V6-F0→F5? | **Sí, pausar** (menos trabajo total) · No, intercalar | Orden del ROADMAP |
| **D-V6-2** | Módulos ES sin bundler (import map generado por `cachebust.py`) vs **Vite** | **ESM sin Vite primero**; reevaluar al llegar a T-V6-37 | T-V6-26 (cómo se versionan los imports) |
| **D-V6-3** | Publicar canciones nuevas en Explorar: ¿por defecto sí (opt-out visible) o no (opt-in)? | **Opt-out visible**: checkbox marcado + aviso de derechos (mantiene el espíritu de D9 pero informa) · Opt-in | T-V6-16 |
| **D-V6-4** | Orden de pestañas del espacio de banda | **Resumen · Repertorio · Setlists · Agenda · Finanzas · Chat · Miembros · Giras · Ajustes** · dejar el actual | T-V6-42a |
| **D-V6-5** | Color de banda | **Paleta de 8 elegible en Ajustes** (hash por defecto) · solo hash | T-V6-32 (avatar/cover) |
| **D-V6-6** | Staging | **Segundo proyecto Supabase gratuito** · Supabase Branching · sin staging | T-V6-70 |
| **D-V6-7** | Proveedor de email y remitente | **Resend** (gratis hasta 3.000/mes) con dominio propio · Postmark · Supabase SMTP | T-V6-60, T-V6-65 |
| **D-V6-8** | Dominio propio (`bandflow.es` / `.app`) | **Sí, antes de F6** (emails, HSTS, confianza) · seguir en vercel.app | T-V6-73, remitente de T-V6-60 |
| **D-V6-9** | Tempo del reproductor | **Por usuario** (localStorage; "Guardar como tempo de la banda" explícito) · compartido con confirmación | T-V6-55 |
| **D-V6-10** | Caducidad/usos por defecto de invitaciones | **7 días / 20 usos** · otros valores | T-V6-08 |
| **D-V6-11** | Landing pública en `/` | **Sí, sencilla, en F6** · después de V5-F5 | T-V6-68 |
| **D-V6-12** | Tests de estilo actuales (`test_design_system`, `test_terminologia`…) | **Sustituir por un test de reglas del sistema** · mantener | T-V6-27, T-V6-35 |
| **D-V6-13** | Nombre técnico del repo/URL (`chordflow`) | Renombrar a `bandflow` al poner dominio · dejar | T-V6-73 |
| **D-V6-20** | Navegación: "una banda = inicio en la banda", 7 pestañas (Canciones agrupa repertorio+setlists+carpetas), vistas TÚ solo con 2+ bandas | **Sí** (§9.4) · mantener 9 pestañas y vistas TÚ siempre | T-V6-90, T-V6-42a |
| **D-V6-21** | Propuestas de evento (V5 §9.5) se implementan como **votación de fechas** con 1..4 opciones y voto por enlace sin cuenta | **Sí** (una propuesta = votación de 1 opción) · mantener solo `status='proposed'` | T-V6-82 |
| **D-V6-22** | Giras pasan a ser agrupación de conciertos en Agenda (sin pestaña) | **Sí**, modelo `Tour` se conserva · mantener pestaña | T-V6-90 |
| **D-V6-23** | Explorar/catálogo oculto tras bandera hasta masa crítica; sin publicación automática | **Sí** · dejar visible | T-V6-90, T-V6-16 |
| **D-V6-24** | Afinador/Metrónomo como "Herramientas" al final del lateral (y dentro del reproductor) | **Sí** · mantener como 2º ítem | T-V6-90 |
| **D-V6-25** | Adjuntos: ¿PDF de partitura como alternativa al editor de acordes en el reproductor? | **Sí** (muchas bandas ya tienen PDFs) · solo audio/imágenes | T-V6-85 |
| **D-V6-26** | Métricas de producto propias (`product_events`) | **Sí**, sin terceros · no medir aún | T-V6-94 |
| **D-V6-27** | Red profesional (§9.9): Explorar con dos grupos (Personas y sitios: Músicos · Bandas · Salas · Profesionales · Bolos abiertos / Música y material: Canciones · Descubrir · Material) y **lanzar primero Salas + Bolos abiertos + Profesionales** como imán | **Sí** · mantener el orden V5 (Músicos primero) | T-V6-96…100, sustituye a D-V6-23 |
| **D-V6-28** | Monetización futura por el lado de salas/profesionales (destacados, plan Sala); bandas y músicos gratis | **Sí**, campos `plan` desde el inicio sin cobrar · decidir más tarde | T-V6-96 (campo `plan`) |
| **D-V6-29** | Lista de categorías de profesional (fotógrafo, vídeo, técnico de sonido, técnico de luces, estudio, local de ensayo, luthier/reparación, diseño/merch, prensa/promo, profesor, otro) | **Esta lista** · recortar/ampliar | T-V6-96 |

---

## 12. Definición de "profesional" — checklist de cierre de la V6

Se cierra la V6 cuando TODO esto es verdad:

**Seguridad y datos**
- [ ] Ningún secreto ni dato personal en el repo ni en el historial; `gitleaks` en CI.
- [ ] Repo privado; secretos solo en Vercel/Supabase; PAT revocado.
- [ ] Modo test imposible en producción; `pytest` imposible contra Postgres.
- [ ] JWT verificado localmente; rate limiting en rutas caras y públicas; importador con allowlist.
- [ ] Gate de aislamiento por `app.routes` + gate de rol verde para las 57+ rutas de banda.
- [ ] Backups diarios probados; runbook de rollback; migraciones reproducibles en PG y automáticas.

**Visual y UX**
- [ ] Cero emoji como icono; cero `#hex`/`rgba` fuera de `:root` (check en CI); un solo sistema de botones/filas/tarjetas/diálogos.
- [ ] Las 16 páginas revisadas en oscuro y claro, escritorio y 390 px, sin overflow horizontal.
- [ ] Toda lista tiene estados: cargando, vacío, error (con reintentar).
- [ ] Dinero y fechas con `Intl` es-ES; copy en castellano, *sentence case*, glosario único.
- [ ] Teclado y lector de pantalla: `axe` sin críticos; focus visible; diálogos con focus trap.
- [ ] Login con recuperar contraseña, Google oficial, legal; join impecable; onboarding de primer uso.
- [ ] Reproductor: móvil sin cortes, modo setlist sin recargas, para al final, tempo por usuario.

**Ingeniería**
- [ ] CI es gate del deploy; jobs < 5 min para lint+unit; e2e herméticos; lockfile; Dependabot.
- [ ] Módulos ES, lint y typecheck de JS, tests de JS en Node; `bands.js` troceado; `style.css` retirado.
- [ ] Sentry sin errores nuevos en 7 días; uptime > 99,5 %; cold start de la API medido y aceptable.
- [ ] README de 10 líneas con el que una IA nueva arranca la app en 5 minutos; ADRs; CHANGELOG.

**Producto**
- [ ] Gestión completa de miembros e invitaciones desde la UI; salir de banda.
- [ ] Notificaciones por email de lo importante; calendario; exportar setlist; cuenta borrable.

---

## 13. Anexos

### 13.A Mapa emoji → icono (`bfIcon`)

| Emoji | Dónde (ejemplos) | Icono Lucide |
|---|---|---|
| 🎸 / 🎵 / 🎼 | logo login/join, h1 Setlists, tipo ensayo, chips de banda | `music`, `guitar` (propio), `list-music` |
| 🎤 | tipo concierto | `mic` |
| 📌 | mensaje fijado, otro tipo | `pin` |
| 📍 | sala / lugar | `map-pin` |
| 📅 / ⏰ | temporada, "Pronto" | `calendar`, `clock` |
| 🔗 | evento compartido | `link` / `globe` |
| 💶 / 🏦 / ➕ / ➖ | caché, fondo, ingreso, gasto | `banknote`, `landmark`, `arrow-up-right` (verde), `arrow-down-right` (rojo) |
| 📞 | contacto de booking | `phone` |
| ✅ / 🤔 / ❌ | asistencia | segmented con `check`, `help-circle`, `x` + color semántico |
| 🔍 | placeholders de búsqueda | `search` dentro del input |
| 📁 | colección | `folder` |
| 👤 | "Personal" | `user` |
| 🌍 | Explorar | `globe` |
| 👋 | saludo, banner | ninguno (texto) |
| 🔎 ✨ 📷 👁 | editor | `search`, `sparkles`, `camera`, `eye` |
| 📂 💾 ✏️ 🗑️ | textos de ayuda que citan botones | reescribir el texto |

### 13.B Resumen de deuda de estilos

- `style.css`: 1.571 líneas, 54 `#hex` + 110 `rgba(` fuera de `:root`, 3 tokens inexistentes
  referenciados, 24 radios distintos, ~40 tamaños de fuente, pesos 800 no cargados.
- JS: 6 colores hex, ~150 `style=""` inline en plantillas, 240 globales.
- Páginas con `<link>` a Inter/Roboto sin uso: 11. `@import` de IBM Plex duplicado: 2 + 1 link.

### 13.C Rutas de banda sin ningún test de aislamiento (11 de 57)

`POST /bands/{bid}/members/{user_id}/reactivate` · `GET /bands/{bid}/invites` ·
`PATCH /bands/{bid}/setlists/{setlist_id}` · `PATCH /bands/{bid}/events/{event_id}` ·
`GET /bands/{bid}/transactions/{tx_id}` · `POST /bands/{bid}/settlements` ·
`DELETE /bands/{bid}/settlements/{settlement_id}` · `PATCH /bands/{bid}/messages/{message_id}` ·
`PATCH /bands/{bid}/messages/{message_id}/pin` · `DELETE /bands/{bid}/tours/{tour_id}/stops/{stop_id}` ·
`DELETE /bands/{bid}/tours/{tour_id}/budget/{line_id}`.
(Verificado que todas llevan `require_band_*`; no hay fuga hoy — pero el gate debe derivarse de
`app.routes` para que siga siendo verdad.)

### 13.D Contradicciones documentación ↔ código

| Doc | Dice | Realidad |
|---|---|---|
| `CLAUDE.md:161`, `TASKS.md:13` | Head de prod `7022a3162284` | `37fb00af7e5c` (20 migraciones) |
| `CLAUDE.md` §5.bis | "Repo GitHub privado" | **Público** |
| `ROADMAP.md:600` (T-157) | Migración pendiente en prod | Ya aplicada (`37fb00af7e5c` es posterior) |
| `test_aislamiento_parametrizado.py:4-7`, `CLAUDE.md:40-41` | "cada ruta de banda… lo caza" | 21/57 rutas |
| `GUIA_MAESTRA_V5.md:35` | e2e por ids, no por texto | 68 `:has-text` + 73 asserts de texto |
| `CLAUDE.md:61-73` | Fase no cerrada sin `REVISIONES.md` | Termina en Fase 13; `revision.py` no conoce V3/V5 |
| `REGISTRO:3143` | "is_public 0→false corregido" | Solo en `models.py`; la migración sigue con `'0'` |
| `CLAUDE.md:123`, SOP backend | Logging a `logs/app.log` | Imposible en Vercel (cae a stdout) |
| `CHECKLIST_E2E.md:9` | "401 sin token en `test_smoke`" | Está en `doctor.py` y `test_setlists.py` |
| `MOLDE.md:5-10` | T-M04/05 pendientes | Marcados hechos en ROADMAP |
| `PENDIENTES_OSCAR.md:4`, `TASKS.md:6` | Actualizado 20/21-06 | Contienen hechos del 03/05-07 |
| `directives/*_SOP.md` | Teal, Inter, hard delete, "ChordFlow", SOP de otro proyecto | Coral, IBM Plex, soft delete, BandFlow |
| `GUIA_V5:38` | Migraciones a mano "antes del push" | Ningún job las aplica; `create_all` puede adelantarse |

### 13.E Capturas de la auditoría

79 capturas (`<página>_<desk|mob>_<dark|light>.png` + pestañas `banda-<tab>_…`) generadas con
datos demo sobre el frontend real. No se han guardado en el repo (esta guía no añade nada más
que este archivo); están disponibles para incorporarlas a `harness/auditoria-2026-11-05/` si
Oscar lo pide. Para reproducirlas: servir `static/` con un backend en modo test + datos de
`harness/seed_demo.py` y recorrer las 16 páginas en 1366 px y 390 px, con `bf-theme` en
`localStorage` a `dark` y `light`.

---

*Fin del plan de la Guía Maestra V6. El estado real está en la sección siguiente.*


---

## 16. Estado de implementación (2026-11-05, rama `v6`)

> Implementado en la rama **`v6`** del repo (no en `main`: producción sigue intacta hasta que Oscar
> la fusione). CI verde: lint, ~190 tests unitarios, ~200 e2e con navegador y la cadena de
> migraciones probada contra **Postgres** (upgrade desde cero, `alembic check`, downgrade y vuelta).
> Detalle de cada entrega en `REGISTRO_DE_CAMBIOS.md` › «V6 — Registro»; checklist en
> `harness/ROADMAP.md` (bloque V6).

### 16.1 Hecho

| Bloque | Tareas | Qué ve el músico |
|---|---|---|
| F0 Seguridad | 02–09 | Modo test blindado, SW sin datos rancios, importador sin SSRF, invitaciones revocables, límites de uso |
| F1 Bugs | 10–17, 19 | Chat incremental, metrónomo preciso, editor que no pierde cambios, errores en castellano |
| F2 Calidad | 20–23, 27, 30, 22 | CI por jobs, gate de aislamiento que recorre `app.routes`, migraciones en Postgres, README/SECURITY, Dependabot, pip-audit |
| F3 Diseño | 33, 34, 36 (+31/35 parcial) | `bfDialog` accesible, iconos SVG en vez de emojis, fechas y dinero con `Intl`, una sola tipografía sin @import |
| F4 Páginas | 40–52 (42a–g parciales cerrados) | Login con recuperar contraseña y términos; invitación-escaparate; pestañas de banda enlazables; chat con hora/editar; finanzas con gráfico; giras editables; Inicio con «Para ti»; Mis bandas con fondo; biblioteca ordenable; editor con Ctrl+S; agenda por semanas y «Nuevo evento»; finanzas y chat TÚ; perfil con cuenta; metrónomo con tempos; evento público con .ics |
| F5 Reproductor | 56, 57 (+55 parcial) | «Siguiente: …» y parada al final; pantalla encendida; canción sin conexión; «Mi tono», «Solo letra», tamaño de letra, modo práctica |
| F6 Producto | 61–68 | Avisos con contador, calendario mensual y suscripción .ics, setlist imprimible y compartible, primeros pasos, borrar cuenta/exportar, moderación del catálogo, Ctrl+K, portada y 404 |
| F7 Operación | 72, 74, 75 (+24/73 parcial) | Runbook, copias (script + workflow opcional), límites de uso, índices compuestos, caché de estáticos, HSTS, CSP en solo-informe |
| F9 Funciones | 80–95 | Votación de fechas sin cuenta, recordatorios 24 h, semáforo, pizarra, hoja del bolo, modo ensayo, material y grabadora, práctica, setlist inteligente, PDF→editor, temporada, feedback, gastos fijos, una banda = menos clics |
| F9b Red profesional | 96–100 | Fichas de sala y profesional, Explorar (bolos/salas/profesionales/mensajes/mis perfiles), candidaturas con dossier → **elegir crea el concierto en la agenda**, EPK y página pública de banda, valoraciones con trato previo, reportes, calendario de sala |

### 16.2 Queda (y por qué)

| Tarea | Estado | Motivo / siguiente paso |
|---|---|---|
| T-V6-01 | Pendiente | Oscar pidió dejar las contraseñas para más adelante: rotar claves, purgar historial (`git filter-repo`) y `gitleaks` |
| T-V6-18 | Pendiente | Contrato UTC de punta a punta: cambia el significado de todas las fechas guardadas; hacerlo con una migración de datos y una tarde de pruebas en staging. Hoy todo es «hora de pared» coherente (punto único de cambio: `bfFromLocalInput`) |
| T-V6-24 | Parcial | Caché inmutable hecha; servir estáticos directamente desde Vercel (sin pasar por Python) requiere tocar `vercel.json` y medir |
| T-V6-25/26 | Parcial | ESLint en CI (informativo). Vitest y pasar el frontend a módulos ESM: refactor grande sin valor visible inmediato |
| T-V6-28 | Pendiente | Validar el JWT en local con JWKS: hay caché TTL, el beneficio es de latencia; hacerlo con PyJWT y pruebas contra el Supabase real |
| T-V6-29 | Parcial | `X-Request-ID` hecho; Sentry y UptimeRobot necesitan cuentas (DSN) de Oscar |
| T-V6-31/32/35/37 | Parcial | Sistema de diseño: tipografía e iconos hechos; unificar botones legacy → `bf-btn`, quitar colores fijos de `style.css` y trocearlo es un refactor visual largo que conviene hacer revisando pantalla a pantalla |
| T-V6-55 | Parcial | Falta la barra compacta con popovers en móvil (tamaño de letra y vistas ya están) |
| T-V6-58/59 | Parcial | Test de desborde en 15 páginas y pestañas/modales accesibles hechos; falta `axe` automático (no instalable en esta sesión) |
| T-V6-60 | Pendiente | Email transaccional: elegir proveedor (D-V6-7). El punto de enganche ya existe (`notify()` y `send_reminders()`) |
| T-V6-70/71 | Documentado | Staging y migración automática: pasos en `docs/RUNBOOK.md`; requieren un proyecto Supabase de pruebas |
| T-V6-73 | Parcial | CSP en solo-informe; activarla de verdad exige quitar los `onclick`/estilos inline |

### 16.3 Para pasar a producción (Oscar)

1. Revisar la rama `v6` en una *preview* de Vercel (cada push a una rama crea una URL).
2. Copia de seguridad de la base de datos (`docs/RUNBOOK.md`).
3. `python -m alembic upgrade head` contra el pooler de sesión (migraciones `a1b2c3d4e5f6` →
   `f6a7b8c9d0e1`, todas aditivas).
4. Variables en Vercel: `CRON_SECRET` (recordatorios). En Supabase › Auth › URL Configuration:
   añadir `/static/reset.html`. Si se quieren PDFs/audios en el material: que el bucket `media`
   admita `application/pdf` y `audio/*`.
5. Fusionar `v6` → `main` (despliega solo). Smoke: entrar, banda, agenda, reproductor, Explorar.
6. Poner el repositorio en **privado** (GitHub › Settings › Change visibility) si aún no lo está.

### 16.4 Decisiones tomadas durante la implementación

- **D-V6-31** — Los avisos (in-app) se crean en la misma transacción que la acción y nunca la
  rompen; el email llegará por el mismo punto (`notify`).
- **D-V6-32** — Votar fechas sin cuenta: el enlace es el secreto y se elige el nombre de la lista de
  miembros (como un Doodle de confianza). Confirmar convierte los votos en asistencias.
- **D-V6-33** — Red profesional: una cuenta puede tener varios perfiles; el teléfono nunca sale en
  listados ni en la ficha pública; valorar exige trato previo; 3 reportes ocultan hasta revisión.
- **D-V6-34** — «Una banda = Inicio en la banda» se resolvió sin redirecciones: con una sola banda
  sus secciones van directas en el lateral (no rompe enlaces ni la vista TÚ).
- **D-V6-35** — Explorar del lateral abre la red (`red.html`); Canciones (catálogo) queda como pestaña.
- **D-V6-36** — Cuenta borrada: se borran los datos personales y se sale de las bandas traspasando
  el admin; el usuario de Supabase Auth lo elimina Oscar (la API no usa la service key).
