# 🔎 ChordFlow — Revisiones por sección

> Registro de la **revisión de la app al cerrar cada sección/fase** del giro a SaaS de banda.
> Herramienta: `python harness/revision.py [sección] [--serve]` (ver integraciones reales + lanzar la app).
> Plantilla de cada entrada: `harness/templates/REVISION_TEMPLATE.md`.
>
> **Regla:** una fase no se da por cerrada hasta tener aquí su revisión con veredicto ✅
> (además del doctor verde y los tests, según CLAUDE.md).

---

## Pendientes de revisar

- _(ninguna — la Fase 7 ya tiene su revisión más abajo)_

---

## Revisiones hechas

### Revisión de sección — Fase 7 (Identidad + núcleo de banda)

- **Fecha:** 2026-06-16
- **Sección:** fase7 — Identidad + núcleo de banda (multi-tenant)
- **Comando:** `python harness/revision.py fase7 [--serve]`

#### Integraciones detectadas (automático)
- **Rutas API:** ✅ `/bands` · ✅ `/invites` · ✅ `/profile`  (membresía e invitaciones-por-banda
  bajo `/bands/{id}/members` y `/bands/{id}/invites`).
- **Páginas front:** ✅ `static/bands.html` · ✅ `static/join.html` · ✅ `static/profile.html`.
- **Estado de integración:** ✅ completa (3/3 rutas · 3/3 páginas).

#### Revisión (verificada por tests automatizados — Playwright en navegador real + unit)
- [x] Crear una banda → entro como **admin** y aparece en "Mis bandas" — *e2e
      `test_crear_banda_ver_miembro_y_generar_invitacion` + unit `test_api_bands`*.
- [x] Invitar por código → otro usuario se une (member/guest) — *unit
      `test_api_invites::test_generar_y_aceptar_invitacion`; e2e previsualiza el enlace*.
- [x] **AISLAMIENTO multi-tenant** (ajeno → 403/404) — *unit `test_band_auth` (7 casos) +
      aislamiento por ruta en `test_api_bands`/`test_api_memberships`/`test_api_invites`*.
- [x] Baja blanda: pierde acceso pero sigue en histórico — *unit
      `test_api_memberships::test_baja_blanda_corta_acceso_pero_conserva_historico`*.
- [x] El perfil muestra **nombres reales, no UUIDs** — *unit
      `test_api_profile` + e2e (la lista de miembros muestra "Oscar E2E")*.

#### Veredicto
- **Estado:** ✅ **completa**.
- **Pendiente / a corregir:** nada funcional. Falta la **revisión visual humana** opcional
  (`python harness/revision.py fase7 --serve`) y aplicar la migración a **Postgres de producción**
  (en local ya está) — ambos en `PENDIENTES_OSCAR.md`.
- **doctor + run_checks:** ✅ **TODO VERDE** (doctor 10/10 · ruff · 83 unit · 38 e2e).

---

### Revisión de sección — Fase 8 (Repertorio de banda)

- **Fecha:** 2026-06-16
- **Sección:** fase8 — Repertorio de banda (`Song.band_id`, copiar de personal)
- **Comando:** `python harness/revision.py fase8 [--serve]`

#### Integraciones detectadas (automático)
- **Rutas API:** ✅ `/bands/{band_id}/songs` (listar/crear/copiar/quitar). El reproductor reusa
  `/songs/{id}` (ahora autoriza a miembros de banda).
- **Páginas front:** ✅ `static/bands.html` (repertorio dentro de la ficha de banda).
- **Estado de integración:** ✅ completa (1/1 rutas · 1/1 páginas).

#### Revisión (verificada por tests automatizados — Playwright + unit)
- [x] Repertorio compartido (`Song.band_id`); no aparece en las personales — *unit
      `test_api_band_songs::test_crear_cancion_de_banda_y_no_aparece_en_personales`*.
- [x] Copiar personal → banda es **independiente** (editar la copia no toca la personal) — *unit
      `test_copiar_personal_a_banda_es_independiente`; e2e `test_copiar_cancion_personal_al_repertorio`*.
- [x] El **reproductor** abre canciones de banda para sus miembros (ajeno→404) — *unit
      `test_reproductor_accede_a_cancion_de_banda_segun_pertenencia`*.
- [x] Un **guest** ve el repertorio pero no lo edita (403) — *unit `test_miembro_edita_repertorio_guest_no`*.
- [x] **AISLAMIENTO** del repertorio (ajeno→404 en listar/crear/copiar/quitar) — *unit
      `test_aislamiento_repertorio_un_ajeno_no_ve_ni_toca`*.

#### Veredicto
- **Estado:** ✅ **completa**.
- **Pendiente:** revisión visual opcional (`--serve`) + aplicar migración a Postgres prod
  (`PENDIENTES_OSCAR.md`). Diferido (no bloquea): metadatos ricos de Área 1 (status/tags/notas/
  reference_url/duration_seconds) y "crear canción nueva en banda desde el editor".
- **doctor + run_checks:** ✅ **TODO VERDE** (doctor 10/10 · ruff · 89 unit · 39 e2e).

---

### Revisión de sección — Fase 9 (Setlists de banda)

- **Fecha:** 2026-06-16
- **Sección:** fase9 — Setlists de banda (`Setlist.band_id`, `SetlistItem.note`)
- **Comando:** `python harness/revision.py fase9 [--serve]`

#### Integraciones detectadas (automático)
- **Rutas API:** ✅ `/bands/{band_id}/setlists` (CRUD). El reproductor reusa `/setlists/{id}` (ahora
  autoriza a miembros de banda).
- **Páginas front:** ✅ `static/bands.html` (sección 🎵 Setlists en la ficha de banda).
- **Estado de integración:** ✅ completa (1/1 rutas · 1/1 páginas).

#### Revisión (verificada por tests automatizados — Playwright + unit)
- [x] Crear setlist de banda desde el repertorio en orden — *unit
      `test_api_band_setlists::test_crear_setlist_de_banda_desde_el_repertorio`; e2e
      `test_crear_setlist_de_banda_desde_la_ui`*.
- [x] Solo admite canciones del repertorio de la banda (filtra las de fuera) — *unit
      `test_no_admite_canciones_fuera_del_repertorio`*.
- [x] El **reproductor** abre el setlist de banda a sus miembros (ajeno→404) — *unit
      `test_reproductor_accede_al_setlist_de_banda_segun_pertenencia`*.
- [x] Un **guest** ve pero no edita (403) — *unit `test_guest_no_edita_pero_ve`*.
- [x] Los **setlists personales se preservan** (no se mezclan con los de banda) — *unit
      `test_crear_setlist...` comprueba que el de banda no sale en `/setlists/`*.
- [x] **AISLAMIENTO** (ajeno→404 en listar/crear/ver/borrar) — *unit
      `test_aislamiento_un_ajeno_no_ve_ni_toca_setlists_de_banda`*.

#### Veredicto
- **Estado:** ✅ **completa**.
- **Pendiente:** revisión visual opcional (`--serve`) + aplicar migración a Postgres prod
  (`PENDIENTES_OSCAR.md`). Diferido: **edición de la `note` por canción** del setlist (la columna y
  la salida ya existen; falta la UI/endpoint para fijarla).
- **doctor + run_checks:** ✅ **TODO VERDE** (doctor 10/10 · ruff · 95 unit · 40 e2e).

---

### Revisión de sección — Fase 10 (Agenda — eventos) [núcleo]

- **Fecha:** 2026-06-16
- **Sección:** fase10 — Agenda (`Event` + `EventAttendance`)
- **Comando:** `python harness/revision.py fase10 [--serve]`

#### Integraciones detectadas (automático)
- **Rutas API:** ✅ `/bands/{band_id}/events` (CRUD + `/attendance`).
- **Páginas front:** ✅ `static/bands.html` (sección 📅 Agenda en la ficha de banda).
- **Estado de integración:** ✅ completa (1/1 rutas · 1/1 páginas).

#### Revisión (verificada por tests automatizados — Playwright + unit)
- [x] Crear ensayo/concierto/otro **solo admin**; miembro→403 — *unit `test_admin_crea_evento_miembro_no`;
      e2e `test_crear_evento_y_marcar_asistencia_en_la_ui`*.
- [x] Asistencia voy/no voy/quizás (incl. **guest**) — *unit `test_listar_y_marcar_asistencia`,
      `test_guest_puede_marcar_asistencia`; e2e marca "Voy" y resalta*.
- [x] Setlist solo en **conciertos** y de la **banda** (si no → 400) — *unit
      `test_setlist_solo_en_conciertos_y_de_la_banda`*.
- [x] Próximos/pasados separados — *UI `loadAgenda` (split por `starts_at`)*.
- [x] **AISLAMIENTO** (ajeno→404 en listar/crear/ver/asistencia/borrar) — *unit
      `test_aislamiento_un_ajeno_no_ve_ni_toca_la_agenda`*.

#### Veredicto
- **Estado:** ✅ **completa (núcleo)**.
- **Pendiente:** revisión visual opcional + migración a Postgres prod (`PENDIENTES_OSCAR.md`).
  **Diferido (Áreas 2/3/4, no bloquea):** `EventSong` (orden del día), `Venue`, `BandResource`,
  checklist pre-bolo con responsable, campos de concierto (cronograma), logística; pipeline de
  booking (Fase 14).
- **doctor + run_checks:** ✅ **TODO VERDE** (doctor 10/10 · ruff · 101 unit · 41 e2e).

---

### Revisión de sección — Fase 11 (Finanzas con división)

- **Fecha:** 2026-06-16
- **Sección:** fase11 — Finanzas (`Transaction`/`Split`/`Settlement` + fondo, modelo Splitwise)
- **Comando:** `python harness/revision.py fase11 [--serve]`

#### Integraciones detectadas (automático)
- **Rutas API:** ✅ `/bands/{id}/transactions` · ✅ `/bands/{id}/balances` · ✅ `/bands/{id}/settlements`.
- **Páginas front:** ✅ `static/bands.html` (sección 💶 Finanzas en la ficha de banda).
- **Estado de integración:** ✅ completa (3/3 rutas · 1/1 páginas).

#### Revisión (verificada por tests automatizados — Playwright + unit)
- [x] Gasto/ingreso con reparto (por defecto a partes iguales; Σ partes validada) — *unit
      `test_api_finance::test_gasto_con_reparto_por_defecto_y_balances`, `test_reparto_que_no_suma_da_400`*.
- [x] **Saldo neto + fondo cuadra a cero** (ejemplo de la guía, fondo, remanente) — *unit
      `test_balances` (6 casos) + `test_api_finance` (suma == 0)*.
- [x] **Liquidar** acerca los saldos a cero — *unit `test_ingreso_y_liquidacion_acercan_a_cero`*.
- [x] Solo admin registra; cualquier miembro ve — *unit `test_solo_admin_registra_miembro_solo_ve`*.
- [x] Borrado financiero es **soft** y recalcula — *unit `test_borrar_transaccion_es_soft_y_recalcula`*.
- [x] **AISLAMIENTO** (ajeno→404 en transacciones/balances/settlements) — *unit `test_aislamiento_finanzas`*.
- [x] UI: registrar movimiento y ver saldos — *e2e `test_registrar_movimiento_y_ver_saldos_en_la_ui`*.

#### Veredicto
- **Estado:** ✅ **completa**.
- **Pendiente:** revisión visual opcional + migración a Postgres prod (`PENDIENTES_OSCAR.md`).
  **Diferido (no bloquea):** editor de reparto personalizado en la UI (el backend ya lo acepta vía
  `splits`); informes/export CSV; cuotas recurrentes; ligar movimiento a un evento desde la UI.
- **doctor + run_checks:** ✅ **TODO VERDE** (doctor 10/10 · ruff · 115 unit · 42 e2e).

---

### Revisión de sección — Fase 12 (Comunicación — chat + notas) [núcleo]

- **Fecha:** 2026-06-16
- **Sección:** fase12 — Comunicación (`Message`: chat general + hilo por evento + notas fijadas)
- **Comando:** `python harness/revision.py fase12 [--serve]`

#### Integraciones detectadas (automático)
- **Rutas API:** ✅ `/bands/{band_id}/messages` (listar/publicar/editar/borrar/fijar).
- **Páginas front:** ✅ `static/bands.html` (sección 💬 Chat en la ficha de banda).
- **Estado de integración:** ✅ completa (1/1 rutas · 1/1 páginas).

#### Revisión (verificada por tests automatizados — Playwright + unit)
- [x] Chat general (publicar/listar) con refresco periódico — *unit `test_publicar_y_listar_chat_general`;
      e2e `test_enviar_mensaje_en_el_chat_de_banda`*.
- [x] Hilo por evento separado del general — *unit `test_hilo_de_evento_separado_del_chat_general`*.
- [x] **Notas fijadas** (is_pinned) por admin, aparecen arriba; miembro no fija (403) — *unit
      `test_fijar_nota_solo_admin`*.
- [x] Editar/borrar el propio; admin borra cualquiera; ajeno no — *unit
      `test_editar_y_borrar_el_propio`, `test_no_editar_ni_borrar_ajeno_salvo_admin`*.
- [x] Guest puede escribir — *unit `test_guest_puede_escribir`*.
- [x] **AISLAMIENTO** (ajeno→404) — *unit `test_aislamiento_chat`*.

#### Veredicto
- **Estado:** ✅ **completa (núcleo)**.
- **Pendiente:** revisión visual opcional + migración a Postgres prod (`PENDIENTES_OSCAR.md`).
  **Diferido (no bloquea):** UI del **hilo por evento** (el backend ya lo soporta vía `?event_id=`);
  `Poll`/encuestas, `Notification`/campana, @menciones; tiempo real (Supabase Realtime).
- **doctor + run_checks:** ✅ **TODO VERDE** (doctor 10/10 · ruff · 122 unit · 43 e2e).

---

### Revisión de sección — Fase 13 (App shell + diseño + vistas agregadas + rebranding BandFlow)

- **Fecha:** 2026-06-16
- **Sección:** fase13 — shell (TÚ/BANDA) + tokens BandFlow + Inicio/Agenda/Finanzas/Chat agregadas + reskin + marca
- **Comando:** `python harness/revision.py fase13 [--serve]`

#### Integraciones detectadas (automático)
- **Rutas API:** ✅ `/me` (`/me/dashboard`, `/me/events`, `/me/balances`, `/me/conversations` — agregados, aislados).
- **Páginas front:** ✅ `static/app.html` (Inicio) · ✅ `static/agenda.html` · ✅ `static/finanzas.html` ·
  ✅ `static/chat.html` · ✅ `static/band.html` (espacio de banda). + `shell.js`/`shell.css`/`design-system.css`.
- **Estado de integración:** ✅ completa (1/1 rutas · 5/5 páginas).

#### Revisión (verificada por tests automatizados + capturas)
- [x] **Shell**: lateral aparece, navega, marca activo, tema claro/oscuro — *e2e `test_shell` (4) + captura*.
- [x] **Inicio** agrega próximos eventos + últimos mensajes con etiqueta — *unit `test_api_dashboard`
      (agrega/excluye pasados/cancelados/hilo) + e2e `test_home`; captura "Hola, Dani Vega"*.
- [x] **Espacio de banda** (banner + 8 pestañas reusando los loaders) — *e2e `test_band_space` (3) +
      6 e2e de `bands_ui` migrados; capturas (Miembros/Repertorio/Ajustes)*.
- [x] **Agenda/Finanzas/Chat agregadas** con etiqueta + filtro — *e2e `test_agenda`/`test_finanzas`/`test_chat`*.
- [x] **AISLAMIENTO** de las vistas agregadas (solo MIS bandas; `left`/borrada fuera) — *unit
      `test_api_dashboard` (aislamiento dashboard/events/balances/conversations + baja + banda borrada)*.
- [x] **Reskin**: paleta coral BandFlow + IBM Plex; la **joya** (player) sigue funcionando — *e2e
      `test_player` + captura del reproductor en coral*.
- [x] **Rebranding**: marca visible BandFlow (sin "ChordFlow" en HTML/manifest) — *unit `test_rebrand`*.

#### Veredicto
- **Estado:** ✅ **completa**.
- **Revisión adversarial ultracode** de los endpoints `/me/*`: **sin fuga de aislamiento**; 2 bugs
  reales corregidos (normalización TZ, filtro `event_id` del dashboard) + tests de regresión.
- **Pendiente / diferido (no bloquea):** revisión visual humana opcional (`--serve`); reskin profundo
  a `bf-*`/flat de cada página legacy y retirar `openBand` muerto; saldo total agregado (`/me/balances`
  ya da por-banda); marca técnica (API title, SW key, env, repo) diferida a propósito; y **desplegar**
  (push + migraciones a Postgres prod) — `PENDIENTES_OSCAR.md`.
- **doctor + run_checks:** ✅ **TODO VERDE** (doctor 10/10 · ruff · **139 unit** · **57 e2e**).
