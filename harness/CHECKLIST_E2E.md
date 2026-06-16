# ✅ BandFlow — Catálogo de flujos E2E

> Lo que **siempre** debe funcionar. Cada ítem mapea a un test en `tests/e2e/`.
> Si tocas una zona, corre su test. Antes de cerrar cualquier tarea: `run_checks.py` verde.

| # | Flujo | Test | Estado |
|---|-------|------|--------|
| S1 | La app carga sin errores de consola (login + biblioteca) | `test_smoke.py` | ✅ |
| S2 | API protegida: `/songs` sin token → 401 (modo normal) | `test_smoke.py` | ✅ |
| S3 | `/config` responde y expone `test_mode` | `test_smoke.py` | ✅ |
| S4 | `apiFetch`: un 401 redirige al login | `test_smoke.py` | ✅ |
| A1 | API: crear → leer → listar → borrar canción (CRUD) | `test_api_songs.py` | ✅ |
| A2 | API: un usuario solo ve sus propias canciones | `test_api_songs.py` | ✅ |
| A3 | API: editar (PUT) no deja filas huérfanas | `test_api_songs.py` | ✅ |
| A4 | API: PUT a id inexistente → 404 (no 400) | `test_api_songs.py` | ✅ |
| A5 | API: metadatos fuera de rango → 422 | `test_api_songs.py` | ✅ |
| A6 | API: paginación `skip`/`limit` acotada → 422 | `test_api_songs.py` | ✅ |
| A7 | API: el listado `/songs/` es ligero (sin `sections`, con `section_count`) | `test_api_songs.py` | ✅ |
| A8 | API: borrar canción cascada a nivel DB (SQL directo, sin huérfanos) | `test_api_songs.py` | ✅ |
| MIG1 | Migraciones: `alembic upgrade head` crea el esquema completo | `test_migrations.py` | ✅ |
| MIG2 | Migraciones: sin drift entre modelos y migraciones (`alembic check`) | `test_migrations.py` | ✅ |
| SEC1 | CORS restringe orígenes no permitidos | `test_security.py` | ✅ |
| SEC2 | Validación de token se cachea y resiste caídas de Supabase | `test_security.py` | ✅ |
| SEC3 | La caché de token tiene cota de tamaño (no memory leak) | `test_security.py` | ✅ |
| SEC4 | Respuestas con cabeceras de seguridad (nosniff, frame-options…) | `test_security.py` | ✅ |
| SEC5 | `_cache_set` es seguro bajo concurrencia (lock) | `test_security.py` | ✅ |
| L1 | Biblioteca: estado vacío se muestra correctamente | `test_library.py` | ✅ |
| L2 | Biblioteca: una canción aparece como tarjeta | `test_library.py` | ✅ |
| L3 | Biblioteca: búsqueda en vivo filtra | `test_library.py` | ✅ |
| E1 | Editor: pegar texto genera vista previa con secciones y acordes | `test_editor.py` | ✅ |
| E2 | Editor: guardar redirige al reproductor con la canción | `test_editor.py` | ✅ |
| P1 | Reproductor: carga la canción (título + partitura) | `test_player.py` | ✅ |
| P2 | Reproductor: Play avanza el beat | `test_player.py` | ✅ |
| P3 | Reproductor: transponer cambia los acordes mostrados | `test_player.py` | ✅ |
| P4 | Reproductor: abrir sin `?songId` carga la 1ª canción con acordes | `test_player.py` | ✅ |
| J1 | Lógica JS: el parser detecta acordes y secciones | `test_js_logic.py` | ✅ |
| J2 | Lógica JS: `transposeChord` sube/baja semitonos correctamente | `test_js_logic.py` | ✅ |
| J3 | Seguridad: el render escapa letra y `chord_name` maliciosos (XSS) | `test_js_logic.py` | ✅ |
| J4 | Seguridad: el popup de diagramas escapa el nombre (XSS 2º orden) | `test_js_logic.py` | ✅ |
| B1 | Banda: aislamiento multi-tenant (member→OK, ajeno→404, no-admin→403, baja→404) | `test_band_auth.py` | ✅ |
| B2 | Banda API: CRUD + soft delete + aislamiento por ruta | `test_api_bands.py` | ✅ |
| B3 | Membresía: baja blanda (corta acceso, conserva histórico), no dejar sin admin | `test_api_memberships.py` | ✅ |
| B4 | Invitaciones: generar/aceptar por código; caducada/agotada/ya-miembro | `test_api_invites.py` | ✅ |
| B5 | Perfil: crear/editar; el nombre real aparece en miembros (no UUID) | `test_api_profile.py` | ✅ |
| B6 | UI banda: crear banda → admin + miembro con nombre + invitación con enlace | `test_bands_ui.py` | ✅ |
| B7 | UI perfil: editar nombre/instrumentos y persiste al recargar | `test_bands_ui.py` | ✅ |
| R1 | Repertorio: canción de banda no aparece en personales; copia independiente; aislamiento | `test_api_band_songs.py` | ✅ |
| R2 | Repertorio: reproductor abre canción de banda a miembros (ajeno→404); guest no edita (403) | `test_api_band_songs.py` | ✅ |
| R3 | UI repertorio: copiar canción personal al repertorio de la banda | `test_bands_ui.py` | ✅ |
| SLB1 | Setlists de banda: crear desde repertorio, filtra ajenas, guest 403, aislamiento | `test_api_band_setlists.py` | ✅ |
| SLB2 | Setlists de banda: reproductor abre a miembros (ajeno→404); personales preservados | `test_api_band_setlists.py` | ✅ |
| SLB3 | UI setlist de banda: crear desde el repertorio y aparece en la ficha | `test_bands_ui.py` | ✅ |
| AG1 | Agenda: crear solo admin (miembro→403); asistencia voy/no voy (incl. guest); aislamiento | `test_api_events.py` | ✅ |
| AG2 | Agenda: setlist solo en conciertos y de la banda (si no→400); editar/borrar admin | `test_api_events.py` | ✅ |
| AG3 | UI agenda: crear evento (admin) y marcar asistencia "Voy" | `test_bands_ui.py` | ✅ |
| FN1 | Balances: ejemplo de la guía + fondo + liquidación + remanente cuadran a cero | `test_balances.py` | ✅ |
| FN2 | Finanzas API: reparto por defecto/validado, solo-admin, soft delete, aislamiento | `test_api_finance.py` | ✅ |
| FN3 | UI finanzas: registrar movimiento y ver saldos | `test_bands_ui.py` | ✅ |
| MSG1 | Chat: publicar/listar, hilo de evento, fijar (admin), editar/borrar propio, aislamiento | `test_api_messages.py` | ✅ |
| MSG2 | UI chat: enviar un mensaje y verlo en el chat de la banda | `test_bands_ui.py` | ✅ |
| SH1 | App shell: lateral + nav + perfil + toggle de tema (claro/oscuro) | `test_shell.py` | ✅ |
| SH2 | Shell navega entre secciones (Inicio/Biblioteca/Agenda/Finanzas/Chat/Bandas/Perfil) | `test_shell.py` | ✅ |
| HOME1 | Inicio: dashboard agrega próximos eventos + últimos mensajes de mis bandas (con etiqueta) | `test_home.py` / `test_api_dashboard.py` | ✅ |
| HOME2 | Aislamiento agregado `/me/*`: solo MIS bandas activas (`left`/borrada/ajena excluidas) | `test_api_dashboard.py` | ✅ |
| BND1 | Espacio de banda (`band.html`): banner + 8 pestañas reusando los loaders de `bands.js` | `test_band_space.py` | ✅ |
| LIBU1 | Biblioteca unificada: personal + banda con filtro Todas/Personales/[banda] + badge de fuente | `test_library.py` | ✅ |
| AGA1 | Agenda agregada: próximos/pasados de todas mis bandas + etiqueta de banda + filtro | `test_agenda.py` / `test_api_dashboard.py` | ✅ |
| FINA1 | Finanzas agregada: mi saldo por banda (verde/rojo); aislado | `test_finanzas.py` / `test_api_dashboard.py` | ✅ |
| CHTA1 | Chat agregado: una conversación por banda con último mensaje; aislado | `test_chat.py` / `test_api_dashboard.py` | ✅ |
| DS1 | Sistema de diseño BandFlow: se sirve + tokens (acento coral, IBM Plex, `*-weak`/`hover`) | `test_design_system.py` | ✅ |
| RBR1 | Rebranding: sin "ChordFlow" visible en HTML; `manifest` = BandFlow | `test_rebrand.py` | ✅ |

> Al añadir una feature nueva, **añade aquí su fila** y crea su test antes de cerrar la tarea.

✅ **Flakiness (T-042) resuelta:** se atacaron 3 carreras del harness — timeout de la fixture
`api` (httpx) 5→30 s, deadline de arranque del `live_server` 25→45 s, y el test S4 reescrito
determinista (caché de `/config` + rebote de `login.js`, comprobando la navegación vía
`framenavigated`). La suite e2e pasó 5/5 en repetición. Pendiente (no bloqueante): cobertura de
`sync_engine.js`/`chord_shapes.js` y medición de cobertura.
