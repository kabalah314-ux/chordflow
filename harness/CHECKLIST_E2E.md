# ✅ ChordFlow — Catálogo de flujos E2E

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
| SEC1 | CORS restringe orígenes no permitidos | `test_security.py` | ✅ |
| SEC2 | Validación de token se cachea y resiste caídas de Supabase | `test_security.py` | ✅ |
| L1 | Biblioteca: estado vacío se muestra correctamente | `test_library.py` | ✅ |
| L2 | Biblioteca: una canción aparece como tarjeta | `test_library.py` | ✅ |
| L3 | Biblioteca: búsqueda en vivo filtra | `test_library.py` | ✅ |
| E1 | Editor: pegar texto genera vista previa con secciones y acordes | `test_editor.py` | ✅ |
| E2 | Editor: guardar redirige al reproductor con la canción | `test_editor.py` | ✅ |
| P1 | Reproductor: carga la canción (título + partitura) | `test_player.py` | ✅ |
| P2 | Reproductor: Play avanza el beat | `test_player.py` | ✅ |
| P3 | Reproductor: transponer cambia los acordes mostrados | `test_player.py` | ✅ |
| J1 | Lógica JS: el parser detecta acordes y secciones | `test_js_logic.py` | ✅ |
| J2 | Lógica JS: `transposeChord` sube/baja semitonos correctamente | `test_js_logic.py` | ✅ |
| J3 | Seguridad: el render escapa letra y `chord_name` maliciosos (XSS) | `test_js_logic.py` | ✅ |

> Al añadir una feature nueva, **añade aquí su fila** y crea su test antes de cerrar la tarea.
