# 📌 ChordFlow — Tareas

> Una tarea activa a la vez (recomendado). Al cerrarla, moverla a "Hechas".
> Abrir tareas nuevas copiando `templates/TASK_TEMPLATE.md`.
> Backlog completo y priorizado en `ROADMAP.md`. Diseño del molde en `MOLDE.md`.
> **Última sincronización: 2026-06-21.**

---

## 🚀 EN PRODUCCIÓN — giro V2 completo (BandFlow): https://chordflow-ecru.vercel.app

**Todo el giro V2 (Fases 7–13) está EN VIVO** (desplegado 2026-06-16: commit `29bd505` → Vercel +
6 migraciones aplicadas a Postgres, head `7022a3162284`; marca **BandFlow** visible). Repo GitHub
privado `kabalah314-ux/chordflow` (rama `main`, auto-deploy en cada push). Pendiente solo de Oscar:
**rotar secretos** (`PENDIENTES_OSCAR.md`). Cuenta de prueba:
`oscarcon314@gmail.com` / `Chordflow2026!`. Detalle en REGISTRO §"Estado actual".

CLIs ya logueadas en la máquina: `gh` y `vercel` (ambas `kabalah314-ux`). Secretos en `.env.local`
(gitignored): Supabase, `DATABASE_URL` Postgres, `OPENROUTER_API_KEY`.

---

## ✅ DESPLIEGUE COMPLETADO (2026-06-23) — prod al día + pw de Postgres rotada

> **Todo el código pendiente está EN VIVO** (`shell.css?v=56a6ffa1`, head prod `91d60406fb92`). Deploy
> `559029a` READY. Las **3 migraciones** (`5481a965f5fb`, `c341c9bbb0ba`, `91d60406fb92`) aplicadas a
> Postgres prod. Verificado end-to-end (login real + `/songs/` 200 + `/collections` y `/venues` 200).
>
> 🔑 **CAUSA REAL del "BLOCKED" (no era el plan free):** Vercel Hobby bloquea builds de commits cuyo
> **autor de git** no es el dueño de la cuenta. Los commits viejos eran de `Tu Nombre <tu@email.com>`.
> `git config` ya está corregido a `kabalah314-ux <kabalah314@gmail.com>` → los commits nuevos
> construyen solos. Detalle en `REGISTRO_DE_CAMBIOS.md` (2026-06-23) y memoria `vercel-deploy-migraciones`.
>
> ⚠️ **Pendiente de Oscar (seguridad):** rotar la contraseña de Postgres (quedó en el chat:
> `Oscarnuria314!`) y demás secretos compartidos cuando se pueda. La tarea programada
> `chordflow-redeploy-check` ya no hace falta (se puede borrar).

## ✅ Sesión 2026-06-21 — cola de Oscar + Fase 14 + pulido (8 commits, todos en `origin/main`)

> `539930a` fix marco blanco (html bg) · `1cdc1e2` confirmados por evento · `92daba3` **T-114 Repertorios**
> · `a0da824` **T-115 booking (contacto+caché)** · `bee5fd2` setlist desde colección · `358e0e0`
> **T-116 Salas (Venue)**. La **cola de correcciones de Oscar (#1–#4) está CERRADA** (ver abajo).
> run_checks verde en cada tarea (192 unit · ~78 e2e). ⚠️ Aviso de entorno: si un pytest de unit se queda
> colgado/lentísimo, borra el lock stale `rm -f test_unit.db*` (lo dejó un run matado) y reintenta.

**Cómo verificar en local (Vercel bloqueado):** entorno en `./venv` (Py3.12). Sembrar + servir demo:
```
rm -f demo_bandflow.db
DATABASE_URL="sqlite:///./demo_bandflow.db" venv/bin/python harness/seed_demo.py
CHORDFLOW_TEST_MODE=1 DATABASE_URL="sqlite:///./demo_bandflow.db" venv/bin/python -m uvicorn src.main:app --host 127.0.0.1 --port 8000
```
→ http://127.0.0.1:8000 (modo test, sin login; banda demo "Los Demo Riff"). Playwright instalado para
verificar a ojo (capturas). El id de la banda demo cambia en cada seed (lo imprime `seed_demo.py`).

**Cómo verificar en local (Vercel bloqueado):** entorno en `./venv` (Py3.12). Sembrar + servir demo:
```
rm -f demo_bandflow.db
DATABASE_URL="sqlite:///./demo_bandflow.db" venv/bin/python harness/seed_demo.py
CHORDFLOW_TEST_MODE=1 DATABASE_URL="sqlite:///./demo_bandflow.db" venv/bin/python -m uvicorn src.main:app --host 127.0.0.1 --port 8000
```
→ http://127.0.0.1:8000 (modo test, sin login; banda demo "Los Demo Riff"). Playwright instalado para
verificar a ojo (capturas) qué páginas/elementos fallan.

**Correcciones a hacer (en orden) — ✅ LAS 4 HECHAS (2026-06-21):**
1. ✅ **La línea/marco lateral — INVESTIGADO Y BLINDADO (2026-06-21).** Reinvestigado con Playwright
   contra el local (todas las páginas del shell, oscuro y claro): el marco **NO se reproduce** en local
   → el `fix(shell)` previo (reset `body{margin:0}`) ya estaba bien. **Causa de que Oscar lo siguiera
   viendo: NO está desplegado** — producción sirve el `shell.css` viejo (`?v=f583ba6a`) porque **Vercel
   está BLOCKED**. Hardening añadido por si quedara una fuente residual (overscroll de macOS revela el
   blanco del `<html>`): fondo ahora en `html` Y `body`. Test reforzado + doctor verde. **➡️ Para que
   Oscar lo vea hay que DESPLEGAR** (Vercel desbloqueado → Redeploy). Detalle en REGISTRO (2026-06-21).
2. ✅ **Repertorio → "Repertorios" — HECHO (T-114, 2026-06-21).** La pestaña "Repertorio" pasa a
   "Repertorios": varias listas nombradas (colecciones temáticas) que agrupan canciones del pool. Debajo,
   "Todas las canciones" (el pool de la banda). Modelo `SongCollection`/`SongCollectionItem` (migración
   `5481a965f5fb`) + `band_collections_router` + UI. unit + e2e verdes. Detalle en REGISTRO (2026-06-21).
3. ✅ **Setlist vs Repertorios — DECIDIDO: diferenciar (2026-06-21).** *Repertorio/colección* = agrupación
   temática SIN orden; *setlist* = orden concreto de un bolo (con notas por canción T-110). Setlists
   intactos. Implementado en T-114 (punto 2). Diferido: crear un setlist directamente desde una colección.
4. ✅ **Agenda: confirmados por evento — HECHO (2026-06-21).** Cada evento muestra una línea discreta
   `✅ Ana, Luis · 🤔 2` bajo el título. Hubo que tocar backend (la **lista** de eventos devolvía
   `EventSummary` SIN asistencia; añadido `EventSummary.attendance` surtido con query agregada sin N+1)
   + frontend (`attendeesLine` en `bands.js`, escapado; `.ev-attendees` en `style.css`). unit + e2e
   verdes. Diferido: sección plegable con el detalle completo; confirmados en la agenda agregada
   (`/me/events`). Detalle en REGISTRO (2026-06-21).

---

## 🟢 En curso

### ✅ T-104 — UI de tablaturas (2026-06-20)
El editor y el reproductor ya renderizan tablaturas: parser (`isTabLine`/`parseRawText` → línea
`type:"tab"` con el ASCII en `content`, round-trip en `songToRawText`), render `<pre class="line-tab">`
(`textContent`, anti-XSS) y CSS `.line-tab` (monoespaciado, scroll-x). La joya intacta. 4 tests JS en
`test_js_logic.py`. run_checks VERDE (173 unit · 73 e2e). Diferido: tab sincronizada al beat
(`TabLine.fret_sequence`) → V3-F6.

### 🟡 Fase 14 — Booking (EN CURSO)
- ✅ **T-111 — Pipeline en la agenda** (2026-06-20): badge de estado de booking por evento + selector
  de admin para mover el funnel (lead→…→done/cancelled, PATCH `status`) + estado inicial en el alta.
  Backend ya listo (admin-only). e2e `test_booking_pipeline_cambiar_estado_de_evento`. run_checks VERDE.
- ✅ **T-112 — Recordatorios in-app** (2026-06-20): "⏰ Pronto" (próximos 7 días) + resumen "🔔 N en
  booking sin confirmar" en la agenda (cliente). e2e. run_checks VERDE.
- ✅ **T-115 — Campos de booking en el concierto** (2026-06-21): `Event.contact_name`/`contact_phone`/
  `fee` (migración `c341c9bbb0ba`) + campos en el modal (solo conciertos) + línea `💶 caché · 📇 contacto`
  en la agenda. unit + e2e. VERDE. ✅ Migración aplicada a Postgres prod (2026-06-23).
- ✅ **T-116 — Salas (Venue) reutilizables** (2026-06-21): `Venue` + `Event.venue_id` (migración
  `91d60406fb92`) + `venues_router` (CRUD admin/aislamiento) + sección "Salas" en Agenda + selector en el
  modal de concierto + `📍` en la agenda. Fix UX: modal scrollable. unit `test_api_venues` (6) + e2e.
  VERDE. ✅ Migración aplicada a Postgres prod (2026-06-23).
- ✅ **Editar sala desde la UI** (2026-06-23, completa T-116): botón ✏️ en la sección Salas → modal
  prerrellenado → `PATCH` (solo frontend `bands.js`, `newVenue` crea/edita). e2e
  `test_editar_sala_desde_la_ui`. + `fix(test)` `test_home` caducado (fecha hardcodeada → dinámica). VERDE.
- ✅ **Resumen de caché por gira** (2026-06-23): cada gira suma el `fee` de sus conciertos ligados
  (`total_fee`, 1 query agregada sin N+1; UI en detalle + fila). unit
  `test_cache_por_gira_suma_el_fee_de_los_conciertos`. Sin migración. VERDE.
- ⏳ **T-113** `EmailTemplate` (bloqueado-ish: el envío real necesita infra) · diferido: recordatorios
  por email/push reales, mapa de salas, resumen de caché por temporada.

### ✅ T-110 — Apunte por canción en el setlist (SetlistItem.note) (2026-06-20)
Los setlists de banda admiten una nota por canción ("capo 2", "acústica"). El modelo+lectura existían
(Fase 9) pero faltaba la vía de escritura. Schema `items:[{song_id,note}]` (compat con `song_ids`),
`band_setlists_router` la persiste (filtrada al repertorio), input por canción en el editor y apunte en
la barra del reproductor. unit + e2e end-to-end + revisión adversarial sin hallazgos. run_checks VERDE.
Diferido: notas en setlists personales; editar notas de un setlist existente.

### ✅ T-109 — Export CSV de finanzas (cliente) (2026-06-20)
Botón ⬇️ CSV en Finanzas: descarga los movimientos (Fecha/Tipo/Descripción/Importe/Categoría/Evento/
Pagado por) generado en el cliente (Blob + BOM UTF-8, celdas escapadas). Sin backend. e2e
`test_exportar_finanzas_csv` (descarga real). run_checks VERDE. Diferido: filtros de fecha, P&L por evento.

### ✅ T-108 — Ligar movimiento de finanzas a un evento (UI) (2026-06-20)
Selector "Evento (opcional)" en el modal de movimiento (carga los eventos de la banda, envía
`event_id`) + etiqueta 🎵 del evento en cada movimiento ligado (`loadFinance`). El backend ya
validaba `event_id` (Fase 11). e2e `test_ligar_movimiento_a_evento`. run_checks VERDE. Diferido:
P&L por evento, export CSV.

### ✅ T-107 — Hilo de discusión por evento (chat) (2026-06-20)
Botón 💬 por evento en la agenda abre un modal con el hilo de mensajes (`event_id`). Refactor
`renderMessageList` compartido (chat general + hilos, sin duplicar render). El backend ya soportaba
`?event_id=` (Fase 12). e2e `test_hilo_de_discusion_por_evento` + chat general sigue verde. Revisión
adversarial (aislamiento + XSS) sin hallazgos. run_checks VERDE. Diferido: hilo embebido (no modal),
notificaciones, encuestas.

### ✅ T-106 — Reparto personalizado de gastos en la UI (2026-06-20)
El modal "Movimiento" ofrece A partes iguales / Personalizado (fila por miembro, prerrelleno, valida
que la Σ cuadre, envía `splits`). El backend ya lo soportaba (Fase 11) pero la UI no lo exponía. e2e
`test_reparto_personalizado_en_movimiento`. + `fix(conftest)` deadline `live_server` 45→90s. run_checks
VERDE. Diferido: export CSV, ligar movimiento a evento, cuotas recurrentes.

### ✅ T-105 — Limpieza: retirado el detalle de banda legacy (openBand) (2026-06-20)
Eliminado el código muerto `openBand` (~91 líneas) + `showGrid`/`showDetail`/`elDetail` de `bands.js`,
el `#band-detail` de `bands.html` y los fallbacks legacy de `newBandSetlist` (la ficha de banda vive en
`band.html` desde T-075). Además `fix(doctor)`: deadline de arranque del server 25→45 s (la app tarda
~26 s en frío → falso negativo). run_checks VERDE. Pendiente (opcional): conversión completa de las
páginas legacy a componentes `bf-*` (refactor visual grande, aparte).

### 🌍 V3 — Red musical con plano público (arranque 2026-06-17)

Dirección aprobada en `GUIA_MAESTRA_V3.md` (D1–D8). **✅ V3-F1 (pulido de diseño) COMPLETA.**
**V3-F2 — núcleo (bolita) COMPLETO:**
- ✅ **T-088 — Bolita de posición** (client-side): barra de progreso + dot + sección actual sobre el
  timeline de beats ya existente; `app.js`+`style.css`, motor intacto. e2e `test_bolita_de_posicion_avanza`.
  run_checks VERDE (140·61). Diferido: mapa persistido + "tap para aprender" → junto a V3-F6 (sync).

**✅ V3-F4 — Quick wins de directo (COMPLETA):**
- ✅ **T-089 — Modo Directo** (escenario pantalla completa): `stage-mode` + Fullscreen API + Esc.
  e2e `test_modo_directo_alterna_y_oculta_barra`.
- ✅ **T-090 — Vídeo de referencia (YouTube)**: `Song.reference_url` (modelo+schema+migración
  `b3f1a9c2d4e5`) + input en editor + botón 🎬. e2e ×2. ✅ Migración aplicada en Postgres prod.
- ✅ **T-091 — Afinador** (`tuner.js`, autocorrelación pura `bfDetectPitch` + micro + panel). e2e.
- ✅ **T-092 — Pasapáginas/pedalera** (PageDown/PageUp/flechas → setlist o scroll). e2e.
- Diferido: loop A-B / metrónomo *lookahead* → V3-F6 (requieren seek/bucle en el motor).
- run_checks TODO VERDE (140 unit · 66 e2e).

**✅ V3-F5 — Gestión de giras (COMPLETA):**
- ✅ **T-093/094/095 — Backend**: modelos `Tour`/`TourStop`/`TourBudgetLine` + migración
  `c5d7e9f1a2b3` + schemas + `tours_router.py` (CRUD admin, paradas ligadas a conciertos, presupuesto
  con total, miembros leen). Test `test_api_tours` (5, incl. aislamiento). ✅ Migración aplicada en prod.
- ✅ **T-096 — Frontend**: pestaña Giras en `band.html` (lista/crear/detalle con ruta + presupuesto).
  e2e `test_band_space_giras`. Diferido: mapa Leaflet, ligar gasto real, co-organización. VERDE (145·67).

**V3-F9 — Biblioteca global (EL RECLAMO, D9) — backend COMPLETO + revisado:**
- ✅ **T-100/101 — Backend**: `MusicalWork`/`PublicScore`/`ScoreRating`/`ScoreComment` + migración
  `e9f1a2b3c4d5` + `catalog_router` (publicar/buscar/detalle/importar/valorar/comentar). `test_api_catalog`.
- ✅ **T-102 — Revisión ultracode aplicada** (33 agentes · 20 hallazgos): letra recortada en público
  (D2), round-trip completo (tabs/reference_url), dedup D9 (409), try/except + carrera work, Decimal,
  banda no borrada, índice+updated_at. Diferido: XSS (frontend), rate-limit comentarios. VERDE (177·67).
  ✅ Migración aplicada en Postgres prod.
- ✅ **T-103 — Frontend**: `biblioteca-global.html`+`catalogo.js` (Explorar): buscar · "ponla aquí"
  (editor publica por defecto, D9) · preview recortado · importar · valorar/comentar (escapado). Item
  "Explorar" en el lateral. e2e `test_catalogo`. **✅ V3-F9 COMPLETA.** run_checks VERDE (177·71).

**V3-F3 — Habilitadores (parte de código COMPLETA):**
- ✅ **T-097 — Andamiaje `Band.plan`** (Free/Pro, sin cobrar): columna + migración `d7e9f1a2b3c4` +
  expuesto en API + editable por admin (inválido→422). Test `test_band_plan`. ✅ Migración aplicada en prod.
- ✅ **T-098 — Gate de aislamiento parametrizado**: 16 rutas de banda → ajeno 403/404. VERDE (163·67).
- ⛔ **T-099 — Storage (Supabase)**: BLOQUEADO, necesita que Oscar cree bucket(s) + políticas + env vars.

- ✅ **T-084 — Estados de UI base** (`design-system.css`): deshabilitado, cargando (`.bf-spinner` +
  `[data-loading]`), `.bf-skeleton`, `.bf-empty`, `:focus-visible` y `.bf-num`. Test
  `test_design_system_tiene_estados_de_ui`. run_checks TODO VERDE.
- ✅ **T-085 — Iconos SVG (Lucide)**: `static/icons.js` (`bfIcon`, auto-alojado) en el shell (nav +
  tema + ajustes + logout). e2e `test_shell_nav_usa_iconos_svg`.
- ✅ **T-086 — Teleprompter espectacular**: acorde activo con glow pulsante (`chord-pulse`) +
  contraste teleprompter, solo CSS. e2e `test_acorde_activo_tiene_glow`.
- ✅ **T-087 — Empty states + skeletons**: helper `bfEmpty` en `icons.js`; Inicio/Agenda/Finanzas/
  Chat con `.bf-empty`; skeleton de carga en Inicio. e2e `test_ui_helper_empty_state`. VERDE (140·60).

### ✅ FASE 13 COMPLETA (Shell + diseño + vistas agregadas + rebranding BandFlow)

- ✅ **Fase A — Tokens BandFlow** (actualiza T-073): `design-system.css` al look del prototipo
  (acento coral, IBM Plex, tokens `*-weak`/`hover`). Spec: `harness/diseno/BANDFLOW_SPEC.md`.
- ✅ **T-074 — App shell (contexto TÚ)**: `shell.js`+`shell.css`+`app.html` (lateral + nav + perfil
  + tema). 1ª página con `bf-*`. e2e `test_shell.py` (4). Verificado en oscuro/claro.
- ✅ **T-075 — Espacio de banda (contexto BANDA)**: `band.html`+`band.js` con banner + **8 pestañas**
  (Resumen·Miembros·Repertorio·Setlists·Agenda·Finanzas·Chat·Ajustes) reusando los loaders de
  `bands.js`. Editor de setlist desacoplado; lista → `band.html`; Ajustes admin. e2e `test_band_space`
  (3) + 6 de `bands_ui` migrados. (Legacy `openBand` se retira en T-081.)
- ✅ **T-076 — Inicio (dashboard agregado)**: `GET /me/dashboard` (`me_router.py`) + `home.js` en
  `app.html`: próximos eventos + últimos mensajes de **todas mis bandas** con etiqueta, **aislado**.
  unit `test_api_dashboard` (4, incl. aislamiento) + e2e `test_home`. (Diferido: saldo total agregado.)
- ✅ **T-077 — Biblioteca unificada**: `library.js` une personales + repertorio de banda; filtro
  Todas·Personales·[banda] + búsqueda; badge de fuente. e2e `test_library` (5, incl. unificada).
- ✅ **T-078 — Agenda agregada**: `GET /me/events` (aislado) + `agenda.html`/`agenda.js` (próximos/
  pasados + filtro por banda). Agenda ya no «Pronto». unit `test_me_events_*` + e2e `test_agenda`.
- ✅ **T-079 — Finanzas agregada**: `GET /me/balances` (aislado) + `finanzas.html`/`finanzas.js`
  (saldo por banda). + **revisión ultracode** de `/me/*` aplicada (2 bugs + tests de regresión).
- ✅ **T-080 — Chat agregado**: `GET /me/conversations` (aislado) + `chat.html`/`chat.js`. Lateral
  sin items pendientes. unit + e2e. **Vistas agregadas (T-076–080) completas.**
- ✅ **T-081 — Reskin**: `style.css` re-tematizado a BandFlow (coral + IBM Plex) → todas las legacy
  adoptan el look, joya intacta. (Reskin por tokens; `bf-*` completo + `openBand` muerto = opcional.)
- ✅ **T-082 — Rebranding**: ChordFlow→BandFlow visible (8 HTML + manifest + theme-color). Marca
  técnica diferida. Test `test_rebrand`.
- ✅ **T-083 — Cierre de Fase 13**: `revision.py fase13` ✅ completa + veredicto en `REVISIONES.md`.
  `run_checks` TODO VERDE (139 unit · 57 e2e).

**No hay tarea activa.** La Fase 13 está cerrada. Pendiente de Oscar (`PENDIENTES_OSCAR.md`):
**desplegar** el V2 (push a `main` + 6 migraciones a Postgres prod). Siguiente fase del roadmap:
Fase 14+ (booking, recursos, etc.) o pulido diferido (reskin `bf-*` profundo, hilo de evento, etc.).

**Núcleo del giro (Fases 7–12) — hecho y verde en local.** Hechas y verdes:
- **Fase 7** (Identidad + núcleo de banda) — T-048→T-056.
- **Fase 8** (Repertorio de banda) — T-057/058/059.
- **Fase 9** (Setlists de banda) — T-060/061/062.
- **Fase 10** (Agenda — eventos, núcleo) — T-063/064/065.
- **Fase 11** (Finanzas con división) — T-066/067/068/069.
- **Fase 12** (Comunicación — chat + notas, núcleo) — T-070 (migración `messages`), T-071 (backend
  `/bands/{id}/messages`), T-072 (UI 💬 Chat con refresco).

Revisión ✅ de las **seis** en `REVISIONES.md`. **122 unit + 43 e2e verdes.** ✅ Desplegado: las
**6 migraciones** del giro se aplicaron a Postgres prod y el código está en `main` (deploy 2026-06-16).

**Próxima fase (cuando se apruebe): Fase 13 — Shell nueva + perfil + pulido** — navegación nueva
(perfil → partituras/bandas → banda → secciones), dashboard, y **rebranding a BandFlow** (títulos,
manifest, marca). Cierra el reposicionamiento como SaaS de gestión.

**Diferido (no bloquea):** metadatos ricos de Área 1 (Fase 8); `note` por canción del setlist (Fase 9);
Áreas 2/3/4 de la agenda (Fase 10); reparto personalizado en UI / informes CSV / cuotas (Fase 11);
hilo por evento en UI / encuestas / notificaciones / @menciones (Fase 12); pipeline de booking (Fase 14).

---

## ▶️ Siguiente recomendado (para el próximo hilo)

> 🔴 **ANTES DE NADA: desplegar.** Ver el bloque "LO PRIMERO EN LA PRÓXIMA SESIÓN" arriba (Vercel
> `BLOCKED` + **3 migraciones pendientes** a Postgres prod: `5481a965f5fb`, `c341c9bbb0ba`,
> `91d60406fb92`). Sin eso, lo de las 2 últimas sesiones no está en vivo.

Una vez desplegado, opciones de roadmap (todas aditivas, en `ROADMAP.md`):

1. 🟢 **Pulir Fase 14 (Booking):** editar una sala desde la UI (hoy solo crear/borrar); resumen de caché
   por gira/temporada; `EmailTemplate` (T-113) **bloqueado** hasta tener infra de envío (Supabase/email).
2. 🟢 **Pulir Repertorios/Setlists:** reordenar canciones dentro de una colección; colecciones personales.
3. 🟠 **Arrancar una fase V3 grande:** V3-F6 (sala de ensayo sincronizada, Supabase Realtime) o V3-F8 (EPK
   + página pública). Necesitan **config de Oscar** (Storage/Realtime) → ver `T-099` (Storage BLOQUEADO).
4. ✉️ **T-047** emails de auth con marca (Supabase Email Templates) — pequeño, mejora percepción.

🔐 **Innegociable:** cada ruta de banda nueva exige su test de aislamiento ("ajeno → 403/404") + alta en
`tests/unit/test_aislamiento_parametrizado.py`. Cada migración: `alembic check` limpio.

> ⚠️ `run_checks` puede fallar el e2e de forma intermitente (T-042); reintentar. Si un pytest de unit se
> cuelga: `rm -f test_unit.db*` (lock stale) y reintentar.
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

**🎸→🏠 Giro V2 (SaaS de banda) — Fase 7:** T-048 migración aditiva del núcleo de identidad
(`musician_profiles`, `bands`, `band_memberships`, `band_invites`) — migración `39fbdc0fff0f` solo
aditiva, `alembic check` limpio, baja blanda + CHECK de roles/estados, doctor + 50 unit verdes.
*(✅ Aplicada a Postgres prod en el deploy 2026-06-16.)* · T-049 schemas Pydantic de las 4
entidades (Literal role/status alineados a `models`; `test_schemas_banda`, 8 casos) · **T-050 auth
multi-tenant** (`band_auth.py`: `require_band_member`/`require_band_admin`, matriz de aislamiento
en `test_band_auth`, 7 casos) · T-051 endpoints de banda (`bands_router.py`: CRUD + soft delete +
aislamiento por ruta; `test_api_bands`) · T-052 membresía (baja blanda + no-sin-admin;
`test_api_memberships`) · T-053 invitaciones por código (`invites_router.py`; `test_api_invites`) ·
T-054 perfil (`profile_router.py`; `test_api_profile`) · T-055 frontend (`bands/join/profile.html`+js,
`promptModal`/`alertModal`, SW; e2e `test_bands_ui`) · T-056 cierre (run_checks verde, revisión ✅).
**🏁 Fase 7 COMPLETA.** Decisiones: nombre **BandFlow** (Fase 13), **EUR**.

**🎸→🏠 Giro V2 — Fase 8 (Repertorio de banda):** T-057 migración `Song.band_id` (`908a0a3875b1`) ·
T-058 backend repertorio (`band_songs_router.py`; reproductor autoriza a miembros; `test_api_band_songs`)
· T-059 frontend repertorio en la ficha de banda (copiar/▶/quitar; e2e). **🏁 Fase 8 COMPLETA.**

**🎸→🏠 Giro V2 — Fase 9 (Setlists de banda):** T-060 migración `Setlist.band_id`+`SetlistItem.note`
(`95eddae092db`) · T-061 backend (`band_setlists_router.py`; desde el repertorio; `test_api_band_setlists`)
· T-062 frontend (sección 🎵 Setlists en la ficha; crear/▶/borrar; e2e). **🏁 Fase 9 COMPLETA.**

**🎸→🏠 Giro V2 — Fase 10 (Agenda — eventos, núcleo):** T-063 migración `events`+`event_attendance`
(`22c7ea96b921`) · T-064 backend (`events_router.py`; crear solo admin, asistencia voy/no voy, setlist
en conciertos; `test_api_events`) · T-065 frontend (sección 📅 Agenda; próximos/pasados, asistencia,
crear evento; e2e). **🏁 Fase 10 COMPLETA.**

**🎸→🏠 Giro V2 — Fase 11 (Finanzas con división):** T-066 migración finanzas + `Band.currency` EUR
(`84c9ca4f7b64`) · T-067 servicio único de balances (`balances.py`; cuadra a cero; `test_balances`) ·
T-068 backend (`finance_router.py`; solo admin registra; `test_api_finance`) · T-069 frontend (sección
💶 Finanzas: saldos/movimientos/liquidar; e2e). **🏁 Fase 11 COMPLETA.**

**🎸→🏠 Giro V2 — Fase 12 (Comunicación — chat + notas):** T-070 migración `messages` (`7022a3162284`)
· T-071 backend (`messages_router.py`; chat general/hilo, fijar notas admin, guest escribe;
`test_api_messages`) · T-072 frontend (sección 💬 Chat con refresco; e2e). **🏁 Fase 12 COMPLETA —
122 unit + 43 e2e verdes. NÚCLEO DEL GIRO (7–12) COMPLETO.**

**Fase 5 (producto, EN VIVO):** T-045 importar desde URL con IA (OpenRouter gratuito + Jina) ·
responsive móvil/tablet · PWA instalable · export PDF · **setlists/repertorios** (CRUD + reproducir
en orden con barra ◀▶ en el reproductor).

> Estado de calidad ChordFlow: ~49 unit + ~30 e2e en verde (algunas parametrizadas). Alembic head
> `3684ab6335e8` (local + Postgres producción). **App desplegada y verificada en vivo.**
> Pendiente: Tablaturas (🟢), Google login (🔵 acción usuario), emails con marca (✉️), pulir detalles.
