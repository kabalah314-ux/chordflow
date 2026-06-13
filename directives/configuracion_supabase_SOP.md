# SOP de Configuración de Supabase y Gestión de Secretos

## 1. Visión General
Este documento detalla el procedimiento para obtener credenciales críticas de Supabase (como la `service_role` key) y su correcta integración en el entorno local del proyecto.

## 2. Objetivos
- Automatizar la recuperación de la `service_role` key desde el panel de control de Supabase.
- Asegurar que el secreto se almacene exclusivamente en `.env.local` (evitando commits en git).
- Mantener el sistema sincronizado con las variables de entorno necesarias para procesos de backend.

## 3. Flujo de Trabajo (Determinista)
1. **Acceso al Dashboard:** Navegar a la URL específica de configuración de API del proyecto: `https://supabase.com/dashboard/project/nqewibtmewemlqaxriko/settings/api`.
2. **Identificación de la Clave:** Localizar la sección "Project API keys" y buscar la clave etiquetada como `service_role`.
3. **Copia de Seguridad:** Extraer el valor de la clave.
4. **Actualización Local:**
   - Se ha identificado que el proyecto correspondiente es `saas masajes a domicilio`.
   - Se ha creado/actualizado el archivo `saas masajes a domicilio/.env.local` con las variables `SUPABASE_URL`, `SUPABASE_ANON_KEY` y `SUPABASE_SERVICE_ROLE_KEY`.
   - Se ha verificado que `.env.local` esté en el `.gitignore` del proyecto.
5. **Reinicio del Servicio:** (Opcional) Si hay un servidor en ejecución, reiniciarlo para cargar las nuevas variables.

## 4. Restricciones y Advertencias
- **SEGURIDAD:** La `service_role` key salta las políticas de RLS. NUNCA debe exponerse al frontend ni subirse a repositorios públicos.
- **Formato:** Asegurarse de que el archivo `.env.local` use el formato `KEY=VALUE` sin espacios innecesarios.

## 5. Registro de Errores y Aprendizaje
- *Caso 1:* Si el login de Supabase es requerido, el agente debe pausar o intentar login si tiene credenciales (en este caso, se espera que el navegador use la sesión activa del usuario si es posible, o solicitar intervención).
