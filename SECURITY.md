# Seguridad

- **Avisar de un fallo:** escribe a Oscar (recordingmythings@gmail.com) con los pasos para
  reproducirlo. No abras un issue público con detalles explotables.
- **Multi-tenant:** toda ruta con `{band_id}` exige pertenencia (`require_band_member/editor/admin`)
  y la cubre el gate `test_toda_ruta_de_banda_aisla_al_ajeno`, que recorre `app.routes`.
- **Plano público** (`/public/*`): proyecciones seguras (sin caché, contactos, notas internas ni
  teléfonos en listados), tokens largos y aleatorios, límites por IP.
- **Secretos:** solo en variables de entorno. La `service_role` de Supabase no la usa la API.
- **Contenido de usuario:** siempre escapado al pintar (`escapeHtml`); enlaces solo `http(s)`.
