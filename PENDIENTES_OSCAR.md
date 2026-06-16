# ✅ Pendientes de Oscar — acciones que solo puedes hacer tú

> Cosas que dependen de paneles/cuentas externas (Claude no tiene acceso). Marca con `[x]` al
> terminar. Última actualización: 2026-06-16.
> Leyenda: 🟢 puedes hacerlo YA (independiente) · 🟡 cuando lleguemos / decisión tuya.

---

## 🟢 Puedes ir haciendo ya

### 1. 🔴 Rotar secretos (seguridad — lo más urgente)
Se compartieron por chat la `sb_secret_` y la contraseña de Postgres **(la contraseña de la BD se
volvió a ver en el chat al hacer el despliegue del 2026-06-16 → cámbiala cuanto antes)**.
- [ ] Supabase → proyecto `fwynfifvtthtpzpejfhb` → **Settings → API** → regenerar la **secret key**.
- [ ] Supabase → **Settings → Database** → cambiar la **contraseña de Postgres**.
- [ ] Avísame con las nuevas (o actualízalas tú) en **Vercel** (`DATABASE_URL`, claves) y en
      `.env.local`. *(El `.env.local` lo actualizo yo si me pasas los valores.)*

### 2. 🔵 Login con Google (T-046)
- [ ] **Google Cloud Console** → crear proyecto → *APIs & Services → Credentials* →
      **OAuth client ID** (tipo "Web application").
- [ ] Copiar el **Redirect URI** de Supabase (*Authentication → Providers → Google*) y pegarlo en
      Google Cloud como *Authorized redirect URI*.
- [ ] Pegar *Client ID* + *Client Secret* en **Supabase → Authentication → Providers → Google** y
      **activar** el proveedor.  *(El botón de Google ya existe en el front.)*

### 3. ✉️ Emails de auth con marca (T-047)
- [ ] Supabase → **Authentication → Email Templates** → personalizar confirmación / recuperación de
      contraseña con la marca **BandFlow**.

---

## 🟡 Cuando lleguemos / decisión tuya

### 4. ✅ Despliegue del giro (Fases 7–13) a producción — HECHO (2026-06-16)
- [x] **Push a `main`** (commit `29bd505`) → Vercel desplegó (deployment READY).
- [x] **6 migraciones del giro aplicadas** a Postgres prod vía pooler 5432
      (`3684ab6335e8` → … → `7022a3162284`, head).
- [x] Verificado en vivo: `/health` ok, `manifest` = BandFlow (código nuevo sirviendo).
- [ ] **Comprobación a ojo final (tú):** entra en https://chordflow-ecru.vercel.app, **inicia sesión**
      y prueba el flujo nuevo (crear banda → Inicio/Agenda/Finanzas/Chat → reproductor). Avísame si algo falla.

### 5. Más adelante (no urgente)
- [ ] **Almacenamiento (Fase 15):** activar **Supabase Storage** (buckets + políticas por banda)
      cuando lleguemos a fotos/recibos/adjuntos reales.

---

## ✅ Decisiones ya tomadas (no requieren acción)
- **Nombre del producto:** **BandFlow** (el rebranding se aplica en la **Fase 13**).
- **Divisa:** **EUR** (una por banda; finanzas en Fase 11).
